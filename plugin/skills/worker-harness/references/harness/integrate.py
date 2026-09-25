#!/usr/bin/env python3
"""integrate — the only path to the integration branch (plan §3.5, pipeline v4 §6.3).

    integrate.py [--repo DIR] [--config FILE] [--bundle DIR] TICKET
    integrate.py [--repo DIR] [--config FILE] --approve TICKET

Imperative shell over the pure checks in `checks/`: git, subprocesses, the
writer lock and the event ledger live here; every decision is a function in
`checks/`. Stdlib only.

Sequence for TICKET (plan §3.5, with the 2026-09-24 amendments):
 1. Refuse (`REFUSED`) unless the ticket branch's committed handoff
    (`<handoffs_dir>/<ticket>.md`) says `Status: DONE` or `DONE_WITH_CONCERNS`.
 2. Read the trusted inputs from the integration head H — the ticket file,
    the blast map (fail closed: `BLAST-MAP-MISSING` / `BLAST-MAP-INVALID`) and
    the decision ledger — never from the ticket's own tree, so a change cannot
    loosen the checks that judge it. Rebase the ticket's commits onto H in a
    throwaway detached worktree (a committed rebase, never a staged merge).
    Conflict -> abort, `CONFLICT` event naming the conflicted paths and the
    tickets that last landed them (folded from the event ledger).
 3. In the worktree, on the judged commit J: lint commands (on H and on J,
    for the ratchet), then the verify commands. A verify that modifies
    tracked files fails (`VERIFY-DIRTY`): J must be what was verified.
 4. Checks on the H..J diff: ref, Touches, blast detector, scrutiny
    evidence, attribution, style lint, megafile (`checks/hygiene.py`,
    `checks/lint.py` document each token).
 5. Green at effective B0-B2: fast-forward the integration branch to J with
    a compare-and-swap (`git update-ref <branch> J H`) — only the judged tree
    lands. If the head moved meanwhile, re-enter at step 2 (at most
    `max_reentries` times, then `HEAD-MOVED`). Green at B3: pin J at
    `refs/one-punch/awaiting/<ticket>`, write the review packet to
    `<packets_dir>/<ticket>/`, emit `AWAITING-OPERATOR`; `--approve TICKET`
    fast-forwards it by the same compare-and-swap (a moved head re-runs the
    ticket and produces a fresh packet to review).
 6. Any red -> `FAILED` (or `BLAST-ESCALATION` when effective > declared:
    re-route at the higher level, work salvaged). The ticket branch is left
    as it was; on `MERGED` it is moved to J unless a worktree has it checked
    out.
Every run appends one JSON line to `events_file`.

Single writer: the process holds an exclusive `flock` on
`<git common dir>/one-punch-writer.lock` for the whole run; a second
integrate or harness run on the same repository exits with
`INTEGRATE-LOCKED`. A caller that already holds the lock (the harness run
loop) calls `integrate_ticket()` / `approve_ticket()` directly.

Exit codes: 0 MERGED · 10 AWAITING-OPERATOR · 20 FAILED · 21 BLAST-ESCALATION
· 22 CONFLICT · 30 REFUSED · 31 INTEGRATE-LOCKED · 32 HEAD-MOVED.

Event (one JSON object per line, every key always present):
  ts, event="integrate", outcome (the exit-code names above except LOCKED,
  which writes nothing: the ledger is the lock's to guard), ticket, model,
  attempt, tokens (the launcher's result.json `usage`), worker_wall_clock_s,
  wall_clock_s (this run), tag, size, declared_blast, effective_blast,
  verify (pass|fail|not-run), verify_failures [{command, exit, tail}],
  reentries, head_moved [bases that moved under a judgement], ticket_head,
  base, judged, files (both sides of renames), hits [{zone, path, source,
  level}], checklists, checks [{name, ok, failures, warnings, exceptions}],
  warnings, exceptions, conflicted_paths, conflict_with, reason, packet,
  approved, ticket_branch_moved.

harness.toml: the `[integrate]` table, keys and defaults documented on
`checks.config.IntegrateConfig`.
"""

from __future__ import annotations

import argparse
import datetime
import fcntl
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from checks.blastmap import BlastEvaluation, BlastMapError, evaluate, load_blast_map
from checks.diff import FileEntry, parse_diff
from checks.hygiene import (
    CheckResult,
    CommandRun,
    Commit,
    attribution_check,
    blast_check,
    conflict_partners,
    count_lines,
    decide,
    handoff_check,
    megafile_check,
    ref_check,
    scrutiny_check,
    touches_check,
    verify_check,
)
from checks.config import ConfigError, IntegrateConfig, parse_config
from checks.ledger import LedgerError, active_decisions, parse_ledger
from checks.lint import LintRun, lint_check
from core import Ticket, TicketHeaderError, parse_ticket_header
from review import packet_readme

LOCK_NAME = "one-punch-writer.lock"
AWAITING_REF = "refs/one-punch/awaiting/{ticket}"
EXIT_CODES = {
    "MERGED": 0,
    "AWAITING-OPERATOR": 10,
    "FAILED": 20,
    "BLAST-ESCALATION": 21,
    "CONFLICT": 22,
    "REFUSED": 30,
    "HEAD-MOVED": 32,
}
EXIT_LOCKED = 31
VERIFY_TAIL = 4000  # characters of a failed verify command's output kept in the event
_SCRUBBED_ENV = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_COMMON_DIR")
DIFF_ARGS = ("diff", "--no-color", "--no-ext-diff", "--no-textconv", "-M", "--src-prefix=a/", "--dst-prefix=b/")


class Refused(Exception):
    """A precondition failed; nothing was judged. The message starts with its token."""


class LockHeld(Exception):
    """`INTEGRATE-LOCKED`: another writer holds the repository lock."""


@dataclass(frozen=True)
class WorkerInfo:
    """What the worker's launcher bundle says (params.json, result.json)."""

    model: str | None = None
    attempt: int | None = None
    tokens: Mapping[str, Any] | None = None
    wall_clock_s: float | None = None


@dataclass(frozen=True)
class IntegrateResult:
    outcome: str
    event: Mapping[str, Any]

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.outcome]


@dataclass(frozen=True)
class _Judgement:
    outcome: str
    base: str
    ticket: Ticket
    judged: str = ""
    entries: tuple[FileEntry, ...] = ()
    evaluation: BlastEvaluation | None = None
    results: tuple[CheckResult, ...] = ()
    conflicted: tuple[str, ...] = ()
    verify_runs: tuple[CommandRun, ...] = ()
    commits: tuple[Commit, ...] = ()


# --------------------------------------------------------------------------
# git and processes
# --------------------------------------------------------------------------


def git_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in _SCRUBBED_ENV}
    env.update(GIT_TERMINAL_PROMPT="0", GIT_EDITOR="true", GIT_SEQUENCE_EDITOR="true", LC_ALL="C")
    return env


@dataclass(frozen=True)
class Git:
    repo: Path

    def run(self, *args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            ["git", *args],
            cwd=cwd or self.repo,
            env=git_env(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if check and proc.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed ({proc.returncode}): {proc.stderr.strip()}")
        return proc

    def out(self, *args: str, cwd: Path | None = None) -> str:
        return self.run(*args, cwd=cwd).stdout

    def rev(self, ref: str) -> str | None:
        proc = self.run("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False)
        return proc.stdout.strip() or None

    def show(self, rev: str, path: str) -> str | None:
        """The file at `rev:path`, or None when it does not exist there."""
        proc = self.run("cat-file", "blob", f"{rev}:{path}", check=False)
        return proc.stdout if proc.returncode == 0 else None

    def ls(self, rev: str, directory: str) -> list[str]:
        """Repo-relative paths of every file under `directory` at `rev`."""
        listing = self.out("ls-tree", "-r", "-z", "--name-only", rev, "--", f"{directory}/")
        return [p for p in listing.split("\0") if p]

    def cas(self, ref: str, new: str, old: str) -> bool:
        """Compare-and-swap a ref; False when it no longer points at `old`."""
        return self.run("update-ref", ref, new, old, check=False).returncode == 0

    def checked_out(self) -> dict[str, str]:
        """{branch ref: worktree path} for every worktree with a branch."""
        branches: dict[str, str] = {}
        path = ""
        for line in self.out("worktree", "list", "--porcelain").splitlines():
            if line.startswith("worktree "):
                path = line[len("worktree ") :]
            elif line.startswith("branch "):
                branches[line[len("branch ") :]] = path
        return branches


def run_command(command: str, cwd: Path, timeout_s: int) -> CommandRun:
    """Run a shell command in its own process group; kill the group on timeout."""
    proc = subprocess.Popen(
        command,
        shell=True,
        cwd=cwd,
        env=git_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        start_new_session=True,
    )
    try:
        output, _ = proc.communicate(timeout=timeout_s)
        return CommandRun(command, proc.returncode, output)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        output, _ = proc.communicate()
        return CommandRun(command, None, output)


@contextmanager
def writer_lock(repo: Path) -> Iterator[Path]:
    """Hold the repository's single-writer lock (non-blocking) or raise LockHeld."""
    common = Path(Git(repo).out("rev-parse", "--git-common-dir").strip())
    path = (common if common.is_absolute() else repo / common) / LOCK_NAME
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise LockHeld(f"INTEGRATE-LOCKED {path}: another integrate or harness run is writing this repository") from None
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode())
        yield path
    finally:
        os.close(fd)


@contextmanager
def throwaway_worktree(git: Git, sha: str) -> Iterator[Path]:
    tmp = Path(tempfile.mkdtemp(prefix="integrate-"))
    try:
        git.run("worktree", "add", "--detach", "--quiet", str(tmp), sha)
        yield tmp
    finally:
        git.run("worktree", "remove", "--force", "--force", str(tmp), check=False)
        shutil.rmtree(tmp, ignore_errors=True)
        git.run("worktree", "prune", check=False)


# --------------------------------------------------------------------------
# inputs
# --------------------------------------------------------------------------


def read_bundle(bundle: Path | None) -> WorkerInfo:
    """Model and attempt from params.json; usage and timestamps from
    result.json (launcher CONTRACT.md). Missing pieces stay None."""
    if bundle is None:
        return WorkerInfo()

    def load(name: str) -> dict[str, Any]:
        try:
            data = json.loads((bundle / name).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    params, result = load("params.json"), load("result.json")
    worker = params.get("worker")
    model = worker.get("model") if isinstance(worker, dict) else None
    attempt = params.get("attempt")
    usage = result.get("usage")
    wall: float | None = None
    try:
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        start = datetime.datetime.strptime(str(result["started_at"]), fmt)
        wall = (datetime.datetime.strptime(str(result["finished_at"]), fmt) - start).total_seconds()
    except (KeyError, ValueError):
        wall = None
    return WorkerInfo(
        model=model if isinstance(model, str) else None,
        attempt=attempt if type(attempt) is int else None,
        tokens=usage if isinstance(usage, dict) and "error" not in usage else None,
        wall_clock_s=wall,
    )


def read_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return events
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def append_event(path: Path, event: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")


def _load_ticket(git: Git, cfg: IntegrateConfig, base: str, ticket_id: str) -> Ticket:
    """The ticket file `<issues_dir>/<ticket>-*.md` (or `<ticket>.md`) at H."""
    issues = cfg.expand(cfg.issues_dir)
    found = [
        p
        for p in git.ls(base, issues)
        if str(Path(p).parent) == issues
        and p.endswith(".md")
        and (Path(p).name == f"{ticket_id}.md" or Path(p).name.startswith(f"{ticket_id}-"))
    ]
    text = git.show(base, found[0]) if len(found) == 1 else None
    if text is None:
        raise Refused(f"TICKET-MISSING {ticket_id}: want one {issues}/{ticket_id}-*.md at the integration head, found {found}")
    try:
        return parse_ticket_header(text, ticket_id, cfg.ref_pattern)
    except TicketHeaderError as exc:
        raise Refused(str(exc)) from None


def checklist_sources(git: Git, cfg: IntegrateConfig, base: str, ids: frozenset[str]) -> dict[str, str | None]:
    sources: dict[str, str | None] = {}
    configured = cfg.checklists_dir
    fallback = Path(__file__).resolve().parents[3] / "blast-radius" / "references"
    for cid in sorted(ids):
        name = f"checklist-{cid}.md"
        if configured and not Path(configured).is_absolute():
            sources[cid] = git.show(base, f"{configured.rstrip('/')}/{name}")
            continue
        path = Path(configured) / name if configured else fallback / name
        sources[cid] = path.read_text(encoding="utf-8") if path.is_file() else None
    return sources


# --------------------------------------------------------------------------
# the judgement (steps 2-4)
# --------------------------------------------------------------------------


def _rebase(git: Git, worktree: Path, base: str) -> list[str]:
    """Rebase the worktree's detached HEAD onto `base`; [] when clean, the
    conflicted paths (after aborting) when not."""
    rebase = ("-c", "rebase.autoStash=false", "rebase", "--no-update-refs", "--no-autosquash", "--quiet", base)
    proc = git.run(*rebase, cwd=worktree, check=False)
    if proc.returncode == 0:
        return []
    conflicted = [p for p in git.out("diff", "--name-only", "--diff-filter=U", "-z", cwd=worktree).split("\0") if p]
    git.run("rebase", "--abort", cwd=worktree, check=False)
    if not conflicted:
        raise Refused(f"REBASE-ERROR {proc.stderr.strip()[-400:]}")
    return sorted(conflicted)


def _lint_runs(git: Git, cfg: IntegrateConfig, wt: Path, base: str, judged: str) -> list[LintRun]:
    commands = [(c, True) for c in cfg.lint_hard] + [(c, False) for c in cfg.lint_soft]
    if not commands:
        return []
    git.run("checkout", "--quiet", "--detach", base, cwd=wt)
    base_runs = [run_command(c, wt, cfg.verify_timeout_s) for c, _ in commands]
    git.run("checkout", "--quiet", "--force", "--detach", judged, cwd=wt)
    git.run("clean", "-fdq", cwd=wt)
    head_runs = [run_command(c, wt, cfg.verify_timeout_s) for c, _ in commands]
    return [
        LintRun(c, hard, b.exit_code, b.output, h.exit_code, h.output)
        for (c, hard), b, h in zip(commands, base_runs, head_runs)
    ]


def _commits(git: Git, base: str, judged: str) -> list[Commit]:
    """The rebased commits, oldest first, with the paths each one touches."""
    commits = []
    for sha in git.out("rev-list", "--reverse", f"{base}..{judged}").split():
        listing = git.out("diff-tree", "-r", "-z", "--no-commit-id", "--name-only", "--root", sha)
        commits.append(Commit(sha, tuple(p for p in listing.split("\0") if p)))
    return commits


def _judge(git: Git, cfg: IntegrateConfig, ticket_id: str, ticket_sha: str, base: str) -> _Judgement:
    """Steps 2-4 against integration head `base`."""
    ticket = _load_ticket(git, cfg, base, ticket_id)
    try:
        bmap = load_blast_map(git.show(base, cfg.blast_map_file), cfg.ref_pattern)
        ledger = parse_ledger(git.show(base, cfg.ledger_file), cfg.ref_pattern)
    except (BlastMapError, LedgerError) as exc:
        raise Refused(str(exc)) from None
    if git.run("merge-base", "--is-ancestor", ticket_sha, base, check=False).returncode == 0:
        raise Refused(f"NOTHING-TO-INTEGRATE {ticket_id}: the ticket branch is already in the integration branch")
    with throwaway_worktree(git, ticket_sha) as wt:
        conflicted = _rebase(git, wt, base)
        if conflicted:
            failures = tuple(f"CONFLICT {p}" for p in conflicted)
            return _Judgement("CONFLICT", base, ticket, results=(CheckResult("rebase", failures),), conflicted=tuple(conflicted))
        judged = git.out("rev-parse", "HEAD", cwd=wt).strip()
        entries = parse_diff(git.out(*DIFF_ARGS, "--unified=0", base, judged))
        if not entries:
            raise Refused(f"NOTHING-TO-INTEGRATE {ticket_id}: empty diff against the integration head")
        lint_runs = _lint_runs(git, cfg, wt, base, judged)
        verify_runs = tuple(run_command(c, wt, cfg.verify_timeout_s) for c in cfg.verify)
        dirty = git.out("status", "--porcelain", "--untracked-files=no", cwd=wt).splitlines()
        worktree_root = str(wt)
    head_text = {}
    for e in entries:
        text = git.show(judged, e.path) if e.status != "D" and not e.binary else None
        if text is not None:
            head_text[e.path] = text
    base_lines = {}
    for e in entries:
        before = e.old_path if e.status == "R" and e.old_path else e.path
        text = git.show(base, before)
        if text is not None:
            base_lines[before] = count_lines(text)
    review_root = cfg.review_path(ticket_id)
    artifacts = {}
    for path in git.ls(judged, review_root):
        text = git.show(judged, path)
        if text is not None:
            artifacts[path[len(review_root) + 1 :]] = text
    commits = tuple(_commits(git, base, judged))
    evaluation = evaluate(bmap, entries, ticket.blast, active_decisions(ledger))
    evidence = cfg.evidence_globs(ticket_id)
    results = (
        verify_check(verify_runs, dirty),
        ref_check(entries, ledger, cfg.ref_pattern, cfg.ref_skip_globs()),
        touches_check(entries, ticket.touches, evidence, evaluation, cfg.ref_pattern),
        blast_check(evaluation),
        scrutiny_check(
            evaluation.effective,
            ticket.tag,
            artifacts,
            commits,
            evaluation.checklists,
            checklist_sources(git, cfg, base, evaluation.checklists),
            cfg.test_globs,
            evidence,
        ),
        attribution_check(ticket.reference, git.show(judged, cfg.notices_file), cfg.allowed_licenses),
        lint_check(
            lint_runs,
            entries,
            head_text,
            ledger,
            pattern=cfg.lint_pattern,
            ok_exit=cfg.lint_ok_exit,
            root=worktree_root,
            ref_pattern=cfg.ref_pattern,
        ),
        megafile_check(entries, base_lines, head_text, cfg.megafile_threshold, cfg.megafile_skip, ledger, cfg.ref_pattern),
    )
    outcome = decide(results, evaluation)
    return _Judgement(outcome, base, ticket, judged, entries, evaluation, results, verify_runs=verify_runs, commits=commits)


# --------------------------------------------------------------------------
# events and packets
# --------------------------------------------------------------------------


def _new_event(ticket: str, worker: WorkerInfo) -> dict[str, Any]:
    return {
        "ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "integrate",
        "outcome": None,
        "ticket": ticket,
        "model": worker.model,
        "attempt": worker.attempt,
        "tokens": dict(worker.tokens) if worker.tokens is not None else None,
        "worker_wall_clock_s": worker.wall_clock_s,
        "tag": None,
        "size": None,
        "declared_blast": None,
        "effective_blast": None,
        "verify": "not-run",
        "verify_failures": [],
        "reentries": 0,
        "head_moved": [],
        "ticket_head": None,
        "base": None,
        "judged": None,
        "files": [],
        "commits": [],
        "hits": [],
        "checklists": [],
        "checks": [],
        "warnings": [],
        "exceptions": [],
        "conflicted_paths": [],
        "conflict_with": [],
        "reason": None,
        "packet": None,
        "approved": False,
        "ticket_branch_moved": False,
        "wall_clock_s": None,
    }


def _record(event: dict[str, Any], j: _Judgement, handoff: CheckResult) -> None:
    ticket, ev = j.ticket, j.evaluation
    event.update(
        outcome=j.outcome,
        base=j.base,
        judged=j.judged or None,
        tag=ticket.tag.value,
        size=ticket.size.value,
        declared_blast=ticket.blast.name,
        files=sorted({p for e in j.entries for p in e.paths()}),
        checks=[handoff.as_json(), *(r.as_json() for r in j.results)],
        warnings=[w for r in j.results for w in r.warnings],
        exceptions=[x for r in j.results for x in r.exceptions],
        conflicted_paths=list(j.conflicted),
        commits=[c.sha for c in j.commits],
        verify="not-run" if not j.verify_runs else ("pass" if j.results[0].ok else "fail"),
        verify_failures=[
            {"command": r.command, "exit": r.exit_code, "tail": r.output[-VERIFY_TAIL:]}
            for r in j.verify_runs
            if r.exit_code != 0
        ],
    )
    if ev is not None:
        event["effective_blast"] = ev.effective.name
        event["hits"] = [{"zone": h.zone, "path": h.path, "source": h.source, "level": h.level.name} for h in ev.hits]
        event["checklists"] = sorted(ev.checklists)


def _write_packet(git: Git, cfg: IntegrateConfig, ticket: str, event: Mapping[str, Any]) -> Path:
    root = git.repo / cfg.expand(cfg.packets_dir) / ticket
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    base, judged = str(event["base"]), str(event["judged"])
    (root / "diff.patch").write_text(git.out(*DIFF_ARGS, "--stat", "--patch", base, judged), encoding="utf-8")
    review_root = cfg.review_path(ticket)
    reviews: dict[str, str] = {}
    for path in [cfg.handoff_path(ticket), *git.ls(judged, review_root)]:
        text = git.show(judged, path)
        if text is not None:
            (root / Path(path).name).write_text(text, encoding="utf-8")
            if path.startswith(review_root + "/"):
                reviews[Path(path).name] = text
    readme = packet_readme(
        ticket=ticket,
        event=event,
        reviews=reviews,
        commits=_commits(git, base, judged),
        test_globs=cfg.test_globs,
        evidence_globs=cfg.evidence_globs(ticket),
        awaiting_ref=AWAITING_REF.format(ticket=ticket),
    )
    (root / "README.md").write_text(readme, encoding="utf-8")
    (root / "packet.json").write_text(json.dumps(event, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return root


def _move_ticket_branch(git: Git, ticket_ref: str, judged: str, old: str) -> bool:
    if ticket_ref in git.checked_out():
        return False
    return git.cas(ticket_ref, judged, old)


def _refs(cfg: IntegrateConfig, ticket: str) -> tuple[str, str]:
    return (
        f"refs/heads/{cfg.expand(cfg.integration_branch)}",
        f"refs/heads/{cfg.expand(cfg.ticket_branch, ticket)}",
    )


def _refuse_checked_out(git: Git, integ_ref: str) -> None:
    where = git.checked_out().get(integ_ref)
    if where is not None:
        raise Refused(f"INTEGRATION-BRANCH-CHECKED-OUT {integ_ref} in {where}: switch that worktree away first")


# --------------------------------------------------------------------------
# entry points (the caller holds the writer lock)
# --------------------------------------------------------------------------


def integrate_ticket(repo: Path, cfg: IntegrateConfig, ticket: str, worker: WorkerInfo = WorkerInfo()) -> IntegrateResult:
    """Judge TICKET and land it (B0-B2) or park it (B3). Appends one event."""
    started = time.monotonic()
    git = Git(repo)
    events_path = repo / cfg.expand(cfg.events_file)
    event = _new_event(ticket, worker)
    try:
        _integrate(git, cfg, ticket, event, events_path)
    except Refused as exc:
        event["outcome"], event["reason"] = "REFUSED", str(exc)
    event["wall_clock_s"] = round(time.monotonic() - started, 3)
    append_event(events_path, event)
    return IntegrateResult(str(event["outcome"]), event)


def _integrate(git: Git, cfg: IntegrateConfig, ticket: str, event: dict[str, Any], events_path: Path) -> None:
    integ_ref, ticket_ref = _refs(cfg, ticket)
    ticket_sha = git.rev(ticket_ref)
    if ticket_sha is None:
        raise Refused(f"TICKET-BRANCH-MISSING {ticket_ref}")
    event["ticket_head"] = ticket_sha
    handoff = handoff_check(git.show(ticket_sha, cfg.handoff_path(ticket)))
    event["checks"] = [handoff.as_json()]
    if not handoff.ok:
        raise Refused(f"{handoff.failures[0]} ({cfg.handoff_path(ticket)} on {ticket_ref})")
    _refuse_checked_out(git, integ_ref)
    for reentry in range(cfg.max_reentries + 1):
        event["reentries"] = reentry
        base = git.rev(integ_ref)
        if base is None:
            raise Refused(f"INTEGRATION-BRANCH-MISSING {integ_ref}")
        j = _judge(git, cfg, ticket, ticket_sha, base)
        _record(event, j, handoff)
        if j.outcome == "CONFLICT":
            event["conflict_with"] = list(conflict_partners(read_events(events_path), set(j.conflicted), ticket))
            return
        if j.outcome == "AWAITING-OPERATOR":
            git.run("update-ref", AWAITING_REF.format(ticket=ticket), j.judged)
            event["packet"] = str(_write_packet(git, cfg, ticket, event))
            return
        if j.outcome != "MERGED":
            return
        if git.cas(integ_ref, j.judged, base):
            event["ticket_branch_moved"] = _move_ticket_branch(git, ticket_ref, j.judged, ticket_sha)
            return
        event["head_moved"].append(base)
    event["outcome"] = "HEAD-MOVED"
    event["reason"] = f"HEAD-MOVED {integ_ref} moved during {cfg.max_reentries + 1} judgements; nothing landed"


def approve_ticket(repo: Path, cfg: IntegrateConfig, ticket: str) -> IntegrateResult:
    """Land a B3 ticket the operator approved: fast-forward to the packet's
    judged commit iff the integration head is still the packet's base;
    otherwise drop the stale approval and re-judge (a fresh packet)."""
    git = Git(repo)
    integ_ref, ticket_ref = _refs(cfg, ticket)
    awaiting_ref = AWAITING_REF.format(ticket=ticket)
    events_path = repo / cfg.expand(cfg.events_file)
    event = _new_event(ticket, WorkerInfo())
    awaiting = git.rev(awaiting_ref)
    try:
        packet = json.loads((repo / cfg.expand(cfg.packets_dir) / ticket / "packet.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        packet = None
    try:
        if awaiting is None or not isinstance(packet, dict) or packet.get("judged") != awaiting:
            raise Refused(f"APPROVE-NOTHING-AWAITING {ticket}: no packet matching {awaiting_ref}")
        _refuse_checked_out(git, integ_ref)
    except Refused as exc:
        event.update(outcome="REFUSED", reason=str(exc))
        append_event(events_path, event)
        return IntegrateResult("REFUSED", event)
    if not git.cas(integ_ref, awaiting, str(packet["base"])):
        git.run("update-ref", "-d", awaiting_ref, awaiting)
        return integrate_ticket(repo, cfg, ticket)
    event = {**packet, "ts": event["ts"], "outcome": "MERGED", "approved": True, "reason": "operator approved the packet"}
    event["ticket_branch_moved"] = _move_ticket_branch(git, ticket_ref, awaiting, str(packet["ticket_head"]))
    git.run("update-ref", "-d", awaiting_ref, awaiting)
    append_event(events_path, event)
    return IntegrateResult("MERGED", event)


def load_config(path: Path) -> IntegrateConfig:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"CONFIG-INVALID: {path} not found") from None
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"CONFIG-INVALID: {path}: {exc}") from None
    return parse_config(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Land one ticket on the integration branch (plan §3.5).")
    parser.add_argument("ticket")
    parser.add_argument("--repo", default=".", help="the repository (default: cwd)")
    parser.add_argument("--config", default="harness.toml", help="harness.toml path, relative to the repo root")
    parser.add_argument("--bundle", help="the worker's launcher bundle dir (params.json, result.json)")
    parser.add_argument("--approve", action="store_true", help="operator approval of an AWAITING-OPERATOR ticket")
    args = parser.parse_args(argv)
    repo = Path(Git(Path(args.repo).resolve()).out("rev-parse", "--show-toplevel").strip())
    try:
        cfg = load_config(repo / args.config)
    except ConfigError as exc:
        print(f"REFUSED {exc}", file=sys.stderr)
        return EXIT_CODES["REFUSED"]
    try:
        with writer_lock(repo):
            if args.approve:
                result = approve_ticket(repo, cfg, args.ticket)
            else:
                result = integrate_ticket(repo, cfg, args.ticket, read_bundle(Path(args.bundle) if args.bundle else None))
    except LockHeld as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_LOCKED
    event = result.event
    print(f"{result.outcome} ticket {args.ticket}" + (f": {event['reason']}" if event.get("reason") else ""))
    for check in event.get("checks", []):
        for line in check.get("failures", []):
            print(f"  {line}")
    for line in event.get("warnings", []):
        print(f"  warning: {line}")
    if event.get("packet"):
        print(f"  review packet: {event['packet']}")
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())

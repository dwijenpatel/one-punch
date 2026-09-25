#!/usr/bin/env python3
"""run — the parallel build loop (plan §3.4, pipeline v4 §6.2).

    run.py [--repo DIR] [--config harness.toml] run [--parallel N]
    run.py [--repo DIR] [--config harness.toml] resume [--json]
    run.py [--repo DIR] [--config harness.toml] answer TICKET --note TEXT
    run.py [--repo DIR] [--config harness.toml] relaunch TICKET [--note TEXT]
    run.py [--repo DIR] [--config harness.toml] closure

`run` holds the repository's single-writer lock (integrate's) for its whole
life and loops, deterministically: derive state from git and the event
ledger -> reconcile -> frontier -> route (core.route) -> batch
(core.select_batch, also disjoint from every in-flight ticket) -> create
worktrees `.worktrees/<t>` on `t/<t>` serially -> launch the workers
concurrently -> as each exits, gate its handoff and call
`integrate_ticket` -> refill. Every decision is `core.py` or a pure
function in `runcore.py`; this file executes them.

State has no file of its own: ticket `Status:` at the integration head H,
the `t/<t>` branches and the append-only JSONL ledger (`[integrate]
events_file`, shared with integrate) are folded on every iteration.
- A `launch` with no `worker-exit` was interrupted (a killed run): its
  worktree is torn down, its branch reset to where the launch found it,
  and the attempt redone. Interruptions and usage-limit exits are not
  failed attempts.
- A worker that exits cleanly is gated on its committed handoff:
  BLOCKED/NEEDS_CONTEXT parks it (`blocked`); a `Decisions needed` item not
  marked reversible parks it (`decision`) without integrating; else
  integrate. MERGED: worktree removed, `t/<t>` moved to the judged commit,
  `Status: done` committed onto the integration branch (planner-direct,
  plan §9). AWAITING-OPERATOR: worktree removed; approve with
  `integrate.py --approve` between runs (this run holds the lock).
  FAILED, worker failure, missing handoff: a failed attempt; the worktree
  is kept and the retry routes one tier up with a root-cause note
  (core.route; a second failure parks, `escalation`). BLAST-ESCALATION:
  the raised level is committed to the ticket's `Blast:` line and the work
  is retried in place; to B3 it parks (`blast-b3`) for the B3 path.
  CONFLICT parks (`conflict`) for the merge agent. HEAD-MOVED twice parks.
- The ledger is committed: every planner-direct commit carries a snapshot
  of the on-disk ledger at `[run] ledger_snapshot`, and so does the run's
  stop. A clone without the on-disk ledger (bare or fresh) reads the
  snapshot; writers seed the disk file from it first. Review packets stay
  on disk (regenerable; the AWAITING-OPERATOR state itself is in the
  ledger).

Stops (the run drains in-flight workers first, then exits with the code):
0 FRONTIER-EMPTY · 3 ALL-PARKED (nothing launchable; some ticket parked or
awaiting the operator) · 4 DECISIONS-NEEDED (`park_k` tickets parked on
non-reversible decisions) · 5 ALL-COOLING · 6 STOPPED (SIGINT/SIGTERM or
the stop file) · 7 KILLED (a second signal: launchers get SIGTERM, their
launches stay unmatched and are redone next run) · 30 REFUSED · 31 LOCKED.
The usage governor: a worker exit whose summary matches `limit_patterns`
cools that candidate for `cooldown_s` and lowers N by one for this run.

Operator interventions (the headline metric's denominator) are ledgered:
`answer` (a parked decision answered), `relaunch` (a parked ticket
relaunched; resets its escalation), and `integrate.py --approve`.
`closure` re-runs every done ticket's acceptance commands against H: the
indented lines under an `Acceptance:` line and the lines of fenced blocks
in an `Acceptance` section.

harness.toml `[run]` (ladder required; the rest default):
  ladder            {T0 = [{tool, model, effort?}], ...}; no Fable model
  launchers         {tool = path}; relative paths from this directory;
                    defaults: claude, codex, grok, mini (`<tool>_p.py`), mock
  parallel 4 · park_k 2 · worker_timeout_s 3600 · poll_s 2.0 ·
  cooldown_s 3600 · closure_timeout_s 600 · worktrees_dir ".worktrees" ·
  bundles_dir ".worktrees/.bundles" · stop_file ".worktrees/STOP" ·
  ledger_snapshot ".scratch/{effort}/ledger/events.jsonl" ·
  field_guide "docs/field-guide/index.md" · field_guide_budget 150 ·
  limit_patterns (rate limit, usage limit, 429, overloaded, quota, ...)
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import core
from checks.blastmap import BlastMapError, extract_blast_map, load_blast_map
from checks.config import ConfigError, IntegrateConfig, parse_config
from checks.ledger import LedgerError, handoff_status, parse_ledger
from core import Blast, Candidate, Routed, Ticket, TicketHeaderError
from integrate import (
    Git,
    LockHeld,
    _checklist_sources,
    _env,
    append_event,
    integrate_ticket,
    read_bundle,
    read_events,
    run_command,
    throwaway_worktree,
    writer_lock,
)
from runcore import (
    BUSY,
    Ledger,
    RunConfig,
    TicketState,
    acceptance_commands,
    build_instructions,
    decision_items,
    depends_rows,
    fold_ledger,
    is_limit,
    parse_run_config,
    plan_round,
    set_header,
)

HERE = Path(__file__).resolve().parent
STOP_CODES = {"FRONTIER-EMPTY": 0, "ALL-PARKED": 3, "DECISIONS-NEEDED": 4, "ALL-COOLING": 5, "STOPPED": 6, "KILLED": 7}
EXIT_REFUSED, EXIT_LOCKED = 30, 31


class RunRefused(Exception):
    """A precondition failed before anything ran."""


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append(path: Path, event: str, **fields: Any) -> None:
    append_event(path, {"event": event, "ts": _now_iso(), "t": time.time(), **fields})


def _git_env(git: Git, env: Mapping[str, str], *args: str, text_in: str | None = None) -> str:
    proc = subprocess.run(["git", *args], cwd=git.repo, env=dict(env), input=text_in, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def planner_commit(git: Git, ref: str, edit: Callable[[str], Mapping[str, str]], message: str) -> str | None:
    """A planner-direct commit (plan §9) onto `ref` without checking it out:
    temp index -> commit-tree -> compare-and-swap; re-read on a lost race.
    `edit(base)` maps paths to new text; None when nothing changes."""
    env = _env()
    if git.run("var", "GIT_COMMITTER_IDENT", check=False).returncode != 0:
        env.update(GIT_AUTHOR_NAME="one-punch harness", GIT_AUTHOR_EMAIL="harness@localhost")
        env.update(GIT_COMMITTER_NAME="one-punch harness", GIT_COMMITTER_EMAIL="harness@localhost")
    for _ in range(5):
        base = git.rev(ref)
        if base is None:
            raise RunRefused(f"INTEGRATION-BRANCH-MISSING {ref}")
        changes = {p: t for p, t in edit(base).items() if git.show(base, p) != t}
        if not changes:
            return None
        with tempfile.TemporaryDirectory() as tmp:
            idx = {**env, "GIT_INDEX_FILE": str(Path(tmp) / "index")}
            _git_env(git, idx, "read-tree", base)
            for path, text in changes.items():
                blob = _git_env(git, idx, "hash-object", "-w", "--stdin", text_in=text)
                _git_env(git, idx, "update-index", "--add", "--cacheinfo", f"100644,{blob},{path}")
            commit = _git_env(git, idx, "commit-tree", _git_env(git, idx, "write-tree"), "-p", base, "-m", message)
        if git.cas(ref, commit, base):
            return commit
    raise RuntimeError(f"PLANNER-COMMIT-LOST {ref} kept moving")


@dataclass
class Effort:
    """The repository, its configs, and paths every command needs."""

    git: Git
    cfg: IntegrateConfig
    rc: RunConfig
    integ_ref: str
    events: Path

    def branch(self, tid: str) -> str:
        return self.cfg.expand(self.cfg.ticket_branch, tid)

    def worktree(self, tid: str) -> Path:
        return self.git.repo / self.rc.worktrees_dir / tid

    def read_events(self) -> list[dict[str, Any]]:
        """The on-disk ledger, else (a clone) the snapshot committed at H."""
        if self.events.is_file():
            return read_events(self.events)
        head = self.git.rev(self.integ_ref)
        text = self.git.show(head, self.rc.ledger_snapshot) if head else None
        return [json.loads(line) for line in (text or "").splitlines() if line.strip()]

    def seed_events(self) -> None:
        """Writers first bring the on-disk ledger up to the committed snapshot."""
        head = self.git.rev(self.integ_ref)
        snap = self.git.show(head, self.rc.ledger_snapshot) if head else None
        disk = self.events.read_text(encoding="utf-8") if self.events.is_file() else ""
        if snap and len(snap) > len(disk) and snap.startswith(disk):
            self.events.parent.mkdir(parents=True, exist_ok=True)
            self.events.write_text(snap, encoding="utf-8")

    def commit(self, message: str, edits: Callable[[str], Mapping[str, str]] = lambda _: {}) -> str | None:
        snapshot = self.events.read_text(encoding="utf-8") if self.events.is_file() else ""
        return planner_commit(self.git, self.integ_ref, lambda b: {**edits(b), self.rc.ledger_snapshot: snapshot}, message)


def open_effort(repo_arg: str, config: str, *, write: bool) -> Effort:
    """The effort at `repo_arg`. harness.toml comes from disk (operator-owned),
    else from HEAD (a bare clone). A clone without the local integration
    branch reads origin's; writers create the local branch from it."""
    probe = Git(Path(repo_arg).resolve())
    top = probe.run("rev-parse", "--show-toplevel", check=False).stdout.strip()
    if not top:
        if write:
            raise RunRefused("BARE-REPOSITORY: run, answer, relaunch and closure need a working checkout")
        top = probe.out("rev-parse", "--absolute-git-dir").strip()
    git = Git(Path(top))
    path = git.repo / config
    text = path.read_text(encoding="utf-8") if path.is_file() else git.show("HEAD", config)
    if text is None:
        raise RunRefused(f"CONFIG-INVALID: {config} is neither on disk nor at HEAD")
    try:
        data = tomllib.loads(text)
        cfg = parse_config(data)
        rc = parse_run_config(data, cfg.effort)
    except (ConfigError, tomllib.TOMLDecodeError) as exc:
        raise RunRefused(str(exc)) from None
    name = cfg.expand(cfg.integration_branch)
    integ_ref = f"refs/heads/{name}"
    if git.rev(integ_ref) is None and git.rev(f"refs/remotes/origin/{name}") is not None:
        if write:
            git.run("branch", name, f"origin/{name}")
        else:
            integ_ref = f"refs/remotes/origin/{name}"
    if git.rev(integ_ref) is None:
        raise RunRefused(f"INTEGRATION-BRANCH-MISSING {name}")
    return Effort(git, cfg, rc, integ_ref, git.repo / cfg.expand(cfg.events_file))


@dataclass(frozen=True)
class View:
    head: str
    tickets: tuple[Ticket, ...]  # attempts folded in
    paths: Mapping[str, str]
    texts: Mapping[str, str]
    invalid: Mapping[str, str]
    ledger: Ledger
    tree: tuple[str, ...]
    blast_map: core.BlastMap


def derive(e: Effort) -> View:
    """All state, from the integration head and the ledger."""
    git, cfg = e.git, e.cfg
    head = git.rev(e.integ_ref) or ""
    ledger = fold_ledger(e.read_events())
    issues = cfg.expand(cfg.issues_dir)
    tickets: dict[str, Ticket] = {}
    paths: dict[str, str] = {}
    texts: dict[str, str] = {}
    invalid: dict[str, str] = {}
    for path in git.ls(head, issues):
        if str(Path(path).parent) != issues or not path.endswith(".md"):
            continue
        tid, text = Path(path).stem.split("-", 1)[0], git.show(head, path) or ""
        try:
            ticket = core.parse_ticket_header(text, tid, cfg.ref_pattern)
        except TicketHeaderError as exc:
            invalid[tid] = str(exc)
            continue
        if tid in tickets:
            invalid[tid] = f"TICKET-INVALID {tid}: two ticket files ({paths[tid]}, {path})"
            continue
        state = ledger.states.get(tid)
        tickets[tid] = dataclasses.replace(ticket, attempts=state.failures if state else 0)
        paths[tid], texts[tid] = path, text
    for tid in invalid:
        tickets.pop(tid, None)
    tree = tuple(p for p in git.out("ls-tree", "-r", "-z", "--name-only", head).split("\0") if p)
    try:
        bmap = core.blast_map_from_data(extract_blast_map(git.show(head, cfg.blast_map_file) or ""))
    except ValueError:  # run's preflight refuses an invalid map; resume still reports
        bmap = core.BlastMap(zones=())
    return View(head, tuple(tickets[t] for t in sorted(tickets)), paths, texts, invalid, ledger, tree, bmap)


def preflight(e: Effort) -> None:
    git, cfg, head = e.git, e.cfg, e.git.rev(e.integ_ref) or ""
    where = git.checked_out().get(e.integ_ref)
    if where is not None:
        raise RunRefused(f"INTEGRATION-BRANCH-CHECKED-OUT {e.integ_ref} in {where}: integrate would refuse every ticket")
    try:
        load_blast_map(git.show(head, cfg.blast_map_file), cfg.ref_pattern)
        parse_ledger(git.show(head, cfg.ledger_file), cfg.ref_pattern)
    except (BlastMapError, LedgerError) as exc:
        raise RunRefused(str(exc)) from None
    try:
        core.critical_path(derive(e).tickets)
    except ValueError as exc:
        raise RunRefused(f"TICKET-GRAPH-INVALID {exc}") from None
    guide = git.show(head, e.rc.field_guide)
    if guide is not None and guide.count("\n") > e.rc.field_guide_budget:
        raise RunRefused(f"FIELD-GUIDE-OVER-BUDGET {e.rc.field_guide}: over {e.rc.field_guide_budget} lines")


def remove_worktree(git: Git, path: Path) -> None:
    git.run("worktree", "remove", "--force", "--force", str(path), check=False)
    shutil.rmtree(path, ignore_errors=True)
    git.run("worktree", "prune", check=False)


def ensure_worktree(e: Effort, tid: str, head: str) -> Path:
    """Reuse the kept worktree; else check out the ticket branch (local, then
    origin's), else cut it from the integration head."""
    git, path, branch = e.git, e.worktree(tid), e.branch(tid)
    where = git.checked_out().get(f"refs/heads/{branch}")
    if where is not None and os.path.realpath(where) == os.path.realpath(path):
        return path
    if where is not None:
        raise RunRefused(f"WORKTREE-BUSY {branch} is checked out at {where}")
    remove_worktree(git, path)
    if git.rev(f"refs/heads/{branch}"):
        git.run("worktree", "add", "--quiet", str(path), branch)
    elif git.rev(f"refs/remotes/origin/{branch}"):
        git.run("worktree", "add", "--quiet", "-b", branch, str(path), f"origin/{branch}")
    else:
        git.run("worktree", "add", "--quiet", "-b", branch, str(path), head)
    return path


def checklists_for(e: Effort, view: View, ticket: Ticket) -> dict[str, str]:
    if ticket.blast.value < Blast.B2.value:
        return {}
    valid = load_blast_map(e.git.show(view.head, e.cfg.blast_map_file), e.cfg.ref_pattern)
    names = core.ticket_zones(ticket.touches, view.blast_map, view.tree)
    ids = frozenset(z.checklist for z in valid.zones if z.name in names and z.checklist)
    return {cid: text for cid, text in _checklist_sources(e.git, e.cfg, view.head, ids).items() if text}


@dataclass
class Worker:
    proc: subprocess.Popen[bytes]
    bundle: Path
    candidate: Candidate


def launch(e: Effort, view: View, ticket: Ticket, routed: Routed) -> Worker:
    git, cfg, rc = e.git, e.cfg, e.rc
    state = view.ledger.states.get(ticket.id, TicketState())
    number = state.launches + 1
    worktree = ensure_worktree(e, ticket.id, view.head)
    start = git.rev(f"refs/heads/{e.branch(ticket.id)}") or view.head
    bundle = git.repo / rc.bundles_dir / ticket.id / f"launch-{number}"
    shutil.rmtree(bundle, ignore_errors=True)
    bundle.mkdir(parents=True)
    instructions = build_instructions(
        ticket=ticket,
        ticket_text=view.texts[ticket.id],
        branch=e.branch(ticket.id),
        base=view.head,
        handoff_path=cfg.handoff_path(ticket.id),
        verify=cfg.verify,
        agents_md=git.show(view.head, "AGENTS.md") is not None,
        field_guide=git.show(view.head, rc.field_guide),
        depends_rows=depends_rows(git.show(view.head, cfg.ledger_file) or "", ticket.depends_on),
        checklists=checklists_for(e, view, ticket),
        state=state,
    )
    (bundle / "instructions.md").write_text(instructions, encoding="utf-8")
    c = routed.candidate
    worker: dict[str, str] = {"tool": c.tool, "model": c.model, **({"effort": c.effort} if c.effort else {})}
    params = {"contract": 1, "role": "author", "worker": worker, "isolation": {}, "cwd": str(worktree), "timeout_s": rc.worker_timeout_s, "attempt": number}
    (bundle / "params.json").write_text(json.dumps(params, indent=2) + "\n", encoding="utf-8")
    with open(bundle / "launcher.out", "wb") as out, open(bundle / "launcher.err", "wb") as err:
        proc = subprocess.Popen([sys.executable, str(rc.launchers[c.tool]), str(bundle)], cwd=bundle, stdout=out, stderr=err, start_new_session=True)
    _append(e.events, "launch", ticket=ticket.id, launch=number, tool=c.tool, model=c.model, effort=c.effort, tier=routed.tier.name,
            explored=routed.explored, escalated=routed.escalated, failures=ticket.attempts, start=start, base=view.head, bundle=str(bundle))
    return Worker(proc, bundle, c)


def record_exit(e: Effort, tid: str, w: Worker) -> bool:
    """Append the worker-exit event; True when it hit a usage limit."""
    try:
        result = json.loads((w.bundle / "result.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        result = {}
    ok = result.get("ok") is True and w.proc.returncode == 0
    summary = str(result.get("error_summary") or result.get("refused_reason") or "")
    if not ok and not summary:
        summary = f"launcher exit {w.proc.returncode}, no result.json summary; see {w.bundle}/launcher.err"
    limit = not ok and is_limit(summary, e.rc.limit_patterns)
    _append(e.events, "worker-exit", ticket=tid, ok=ok, exit=result.get("exit"), launcher_exit=w.proc.returncode, summary=summary,
            limit=limit, retry_at=time.time() + e.rc.cooldown_s if limit else None, tokens=result.get("usage"),
            tool=w.candidate.tool, model=w.candidate.model, effort=w.candidate.effort)
    return limit


def settle(e: Effort, view: View, tid: str, state: TicketState) -> None:
    """Gate a cleanly exited worker's handoff, then integrate it."""
    git, cfg = e.git, e.cfg
    tip = git.rev(f"refs/heads/{e.branch(tid)}")
    handoff = git.show(tip, cfg.handoff_path(tid)) if tip else None
    status = handoff_status(handoff)
    if handoff is not None and status in ("BLOCKED", "NEEDS_CONTEXT"):
        _append(e.events, "park", ticket=tid, kind="blocked", reason=f"handoff Status: {status} ({cfg.handoff_path(tid)})")
        return
    one_way = [text for text, reversible in decision_items(handoff or "") if not reversible]
    if one_way:
        _append(e.events, "park", ticket=tid, kind="decision", reason=" | ".join(one_way)[:2000])
        return
    result = integrate_ticket(git.repo, cfg, tid, read_bundle(Path(state.bundle) if state.bundle else None))
    if result.outcome in ("MERGED", "AWAITING-OPERATOR"):
        finish(e, tid, result.event)


def finish(e: Effort, tid: str, event: Mapping[str, Any]) -> None:
    """After MERGED or AWAITING-OPERATOR: remove the worktree; after MERGED,
    point the ticket branch at the judged commit and commit `Status: done`."""
    remove_worktree(e.git, e.worktree(tid))
    if event.get("outcome") != "MERGED":
        return
    branch = f"refs/heads/{e.branch(tid)}"
    if event.get("judged") and e.git.rev(branch) == event.get("ticket_head"):
        e.git.cas(branch, str(event["judged"]), str(event["ticket_head"]))
    path = derive_path(e, tid)
    if path is None:
        return
    commit = e.commit(f"harness: ticket {tid} Status: done (MERGED)", lambda b: {path: set_header(e.git.show(b, path) or "", "Status", "done")})
    _append(e.events, "status-flip", ticket=tid, status="done", commit=commit)


def derive_path(e: Effort, tid: str) -> str | None:
    issues = e.cfg.expand(e.cfg.issues_dir)
    found = [p for p in e.git.ls(e.git.rev(e.integ_ref) or "", issues) if Path(p).stem.split("-", 1)[0] == tid]
    return found[0] if len(found) == 1 else None


def reconcile(e: Effort, view: View, inflight: Collection[str]) -> bool:
    """Bring git in line with the ledger; True when anything changed."""
    changed = False
    by_id = {t.id: t for t in view.tickets}
    for tid, s in sorted(view.ledger.states.items()):
        if tid in inflight:
            continue
        ticket = by_id.get(tid)
        if s.phase == "running":  # interrupted: tear down, reset the branch, redo
            remove_worktree(e.git, e.worktree(tid))
            branch = f"refs/heads/{e.branch(tid)}"
            if s.start and e.git.rev(branch) and e.git.rev(branch) != s.start:
                e.git.run("update-ref", branch, s.start)
            _append(e.events, "teardown", ticket=tid, launch=s.launches)
        elif s.phase == "exited":
            if e.git.checked_out().get(e.integ_ref) is not None:
                continue  # integrate would refuse; wait until the operator switches away
            settle(e, view, tid, s)
        elif s.phase == "merged" and ticket is not None and ticket.status != "done":
            finish(e, tid, {"outcome": "MERGED", "judged": s.judged, "ticket_head": s.ticket_head})
        elif s.phase == "awaiting" and e.worktree(tid).exists():
            remove_worktree(e.git, e.worktree(tid))
        elif s.escalated_to in Blast.__members__ and ticket is not None and Blast[s.escalated_to].value > ticket.blast.value:
            raised = f"{s.escalated_to} — raised from {ticket.blast.name} by the integrate blast detector (declared: {ticket.blast_reason or 'no reason'})"
            path = view.paths[tid]
            e.commit(f"harness: ticket {tid} Blast raised to {s.escalated_to} (BLAST-ESCALATION)", lambda b: {path: set_header(e.git.show(b, path) or "", "Blast", raised)})
            _append(e.events, "blast-raise", ticket=tid, to=s.escalated_to)
        else:
            continue
        changed = True
    return changed


class Stop:
    def __init__(self) -> None:
        self.requested = False
        self.hard = False

    def __call__(self, signum: int, frame: object) -> None:
        self.hard = self.requested
        self.requested = True


def terminate(workers: Collection[Worker]) -> None:
    """SIGTERM each launcher's process group (a launcher forwards it to its
    worker); SIGKILL what is still alive after 15 s."""
    for w in workers:
        if w.proc.poll() is None:
            os.killpg(w.proc.pid, signal.SIGTERM)
    for w in workers:
        try:
            w.proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(w.proc.pid, signal.SIGKILL)


def run(e: Effort, n: int) -> str:
    """The loop; the caller holds the writer lock. Returns the stop reason."""
    preflight(e)
    e.seed_events()
    stop_file = e.git.repo / e.rc.stop_file
    stop_file.unlink(missing_ok=True)
    stop = Stop()
    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGINT, signal.SIGTERM)}
    inflight: dict[str, Worker] = {}
    limits = 0
    draining = ""
    _append(e.events, "run-start", parallel=n, park_k=e.rc.park_k, pid=os.getpid())
    try:
        while True:
            for tid, w in list(inflight.items()):
                if w.proc.poll() is not None:
                    limits += record_exit(e, tid, w)
                    del inflight[tid]
            if stop.hard:
                terminate(inflight.values())
                reason = "KILLED"
                break
            if stop.requested or stop_file.exists():
                draining = draining or "STOPPED"
            view = derive(e)
            for _ in range(50):  # each pass settles at least one ticket; bounded against a stuck edit
                if not reconcile(e, view, inflight):
                    break
                view = derive(e)
            rnd = plan_round(view.tickets, view.ledger, inflight, max(1, n - limits), e.rc.park_k, e.rc.ladder, time.time(), view.blast_map, view.tree)
            for tid, kind, why in rnd.park:
                _append(e.events, "park", ticket=tid, kind=kind, reason=why)
            if rnd.stop == "DECISIONS-NEEDED":
                draining = draining or rnd.stop
            if draining:
                if not inflight:
                    reason = draining
                    break
            else:
                for ticket, routed in rnd.launch:
                    try:
                        inflight[ticket.id] = launch(e, view, ticket, routed)
                    except (RunRefused, RuntimeError) as exc:
                        _append(e.events, "park", ticket=ticket.id, kind="refused", reason=f"LAUNCH-FAILED {exc}")
                if rnd.stop and not inflight and not rnd.launch:
                    reason = rnd.stop
                    break
            time.sleep(e.rc.poll_s)
    except BaseException:
        terminate(inflight.values())  # never leave workers running unledgered
        raise
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    _append(e.events, "run-stop", reason=reason)
    e.commit(f"harness: ledger snapshot (run stopped: {reason})")
    return reason


# ==========================================================================
# resume, interventions, closure, CLI
# ==========================================================================


def report(e: Effort, view: View, run_active: bool, now: float) -> dict[str, Any]:
    states = view.ledger.states
    live = [t for t in view.tickets if t.status != "done"]
    phase = {t.id: states.get(t.id, TicketState()).phase for t in live}
    _, governor = core.fold(view.ledger.core_events)
    merged, interventions = view.ledger.merged, view.ledger.interventions
    return {
        "effort": e.cfg.effort,
        "integration_branch": e.integ_ref,
        "head": view.head,
        "tickets": len(view.tickets),
        "done": [t.id for t in view.tickets if t.status == "done"],
        "frontier": [t.id for t in core.frontier(view.tickets) if phase[t.id] not in BUSY],
        "in_flight": [{"ticket": t, "model": getattr(states[t].candidate, "model", None),
                       "state": "worker exited; integrates on the next pass" if p == "exited" else
                       "running" if run_active else "interrupted (the next run tears it down and redoes it)"}
                      for t, p in phase.items() if p in ("running", "exited")],
        "awaiting_operator": [{"ticket": t, "packet": states[t].packet} for t, p in phase.items() if p == "awaiting"],
        "parked": [{"ticket": t, "kind": states[t].park_kind, "reason": states[t].park_reason} for t, p in phase.items() if p == "parked"],
        "cooling": [{"tool": c.tool, "model": c.model, "until": datetime.datetime.fromtimestamp(u, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
                    for c, u in sorted(governor.cooling.items(), key=lambda kv: kv[1]) if u > now],
        "invalid": dict(view.invalid),
        "merged": merged,
        "interventions": interventions,
        "merged_per_intervention": round(merged / interventions, 2) if interventions else None,
        "last_stop": view.ledger.last_stop or None,
    }


def format_report(r: Mapping[str, Any]) -> str:
    lines = [f"effort {r['effort']} — {r['integration_branch']} @ {r['head'][:12]} — {len(r['done'])}/{r['tickets']} tickets done"]
    lines.append(f"frontier: {', '.join(r['frontier']) or '—'}")
    lines += [f"in flight: {x['ticket']} ({x['model']}) {x['state']}" for x in r["in_flight"]]
    lines += [f"AWAITING-OPERATOR: {x['ticket']} — packet {x['packet']}; approve: integrate.py --approve {x['ticket']}" for x in r["awaiting_operator"]]
    lines += [f"parked: {x['ticket']} [{x['kind']}] {x['reason']}" for x in r["parked"]]
    lines += [f"cooling: {x['tool']}/{x['model']} until {x['until']}" for x in r["cooling"]]
    lines += [f"invalid: {reason}" for reason in r["invalid"].values()]
    lines.append(f"merged {r['merged']} · operator interventions {r['interventions']} · merged per intervention {r['merged_per_intervention']}")
    lines.append(f"last stop: {r['last_stop'] or '—'}")
    return "\n".join(lines)


def run_active(e: Effort) -> bool:
    try:
        with writer_lock(e.git.repo):
            return False
    except LockHeld:
        return True


def intervene(e: Effort, tid: str, kind: str, note: str) -> str:
    """Ledger an operator intervention and commit the snapshot, so any
    clone's next run sees it. The caller holds the writer lock: between runs."""
    e.seed_events()
    state = fold_ledger(e.read_events()).states.get(tid)
    if state is None or state.phase in ("running", "exited", "merged"):
        raise RunRefused(f"NOT-PARKED {tid}: {state.phase if state else 'never launched'}")
    if kind == "decision-answered" and state.phase != "parked":
        raise RunRefused(f"NOT-PARKED {tid}: {state.phase}")
    _append(e.events, "intervention", ticket=tid, kind=kind, note=note, was=state.phase, park_kind=state.park_kind)
    e.commit(f"harness: ticket {tid} {kind} (operator intervention)")
    return f"{kind} {tid}: the next run relaunches it with your note"


def closure(e: Effort) -> tuple[bool, list[str]]:
    """Re-run every done ticket's acceptance commands against H."""
    view = derive(e)
    results: list[dict[str, Any]] = []
    lines: list[str] = []
    with throwaway_worktree(e.git, view.head) as wt:
        for t in view.tickets:
            if t.status != "done":
                continue
            commands = acceptance_commands(view.texts[t.id])
            if not commands:
                lines.append(f"{t.id}: no acceptance commands")
            for command in commands:
                ran = run_command(command, wt, e.rc.closure_timeout_s)
                results.append({"ticket": t.id, "command": command, "exit": ran.exit_code, "tail": ran.output[-1500:]})
                lines.append(f"{t.id}: {'ok ' if ran.exit_code == 0 else 'FAIL'} {command}")
    ok = all(r["exit"] == 0 for r in results)
    _append(e.events, "closure", head=view.head, ok=ok, results=results)
    return ok, lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="The parallel build loop (plan §3.4).")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--config", default="harness.toml", help="relative to the repo root")
    sub = parser.add_subparsers(dest="command", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("--parallel", type=int)
    sub.add_parser("resume").add_argument("--json", action="store_true")
    for name in ("answer", "relaunch"):
        p = sub.add_parser(name)
        p.add_argument("ticket")
        p.add_argument("--note", required=name == "answer", default="")
    sub.add_parser("closure")
    args = parser.parse_args(argv)
    try:
        e = open_effort(args.repo, args.config, write=args.command != "resume")
        if args.command == "resume":
            r = report(e, derive(e), run_active(e), time.time())
            print(json.dumps(r, indent=2) if args.json else format_report(r))
            return 0
        with writer_lock(e.git.repo):
            if args.command in ("answer", "relaunch"):
                print(intervene(e, args.ticket, "decision-answered" if args.command == "answer" else "relaunch", args.note))
                return 0
            if args.command == "closure":
                ok, lines = closure(e)
                print("\n".join(lines) + f"\nclosure {'GREEN' if ok else 'RED'}")
                return 0 if ok else 1
            reason = run(e, args.parallel or e.rc.parallel)
            print(f"{reason}\n" + format_report(report(e, derive(e), False, time.time())))
            return STOP_CODES[reason]
    except RunRefused as exc:
        print(f"REFUSED {exc}", file=sys.stderr)
        return EXIT_REFUSED
    except LockHeld as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_LOCKED


if __name__ == "__main__":
    sys.exit(main())

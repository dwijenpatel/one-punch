"""stages — the imperative shell of the non-author dispatches (plan §3.1,
§3.5 step 2, §3.9, §2b); `review.py` is their pure core, `run.py` the loop
that schedules them.

Every stage runs in its own detached worktree `<worktrees_dir>/<t>.<role>`
cut from the ticket branch (the test author's from the integration head),
never in the implementer's: a reviewer sees the committed change only, and
a rejected dispatch is discarded with its worktree. The implementer's
worktree is removed first — stages move the ticket branch, and git must not
have it checked out elsewhere.

Acceptance (`accept_stage`, after the launcher exits):
- `test_author`, `spec_verdict`, `lens`: the files the dispatch left are
  classified (review.keep): anything committed or modified outside what the
  role may write rejects it. The harness then commits exactly the kept files
  (reviewers are read-only; a sandboxed Codex lens cannot commit anyway),
  checks them (review.stage_problems) and moves `t/<t>` by compare-and-swap.
- `merge`: HEAD must be a linear rebase onto the integration head the agent
  was given, with nothing uncommitted; the branch moves to it and the ticket
  re-enters integrate (a B3 ticket re-enters spec verdict and lens first).
A rejection is a `stage` event with ok false: the same role runs again; the
second rejection parks the ticket (`stage`).

The B3 test author on a branch that already holds work (an escalation to
B3, or an interrupted older attempt) keeps that work at
`refs/one-punch/salvage/<t>` and starts the branch over from the
integration head, so the tests commit is first; the implementer is told
where the earlier work is.
"""

from __future__ import annotations

import datetime
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import core
import review
from checks.blastmap import BlastMapError, evaluate, load_blast_map
from checks.diff import parse_diff
from checks.ledger import LedgerError, active_decisions, parse_ledger
from core import Blast, Candidate, Routed, Ticket
from integrate import DIFF_ARGS, Git, append_event, checklist_sources, git_env, run_command
from review import LENS, MERGE, SPEC, TEST_AUTHOR, Scope, Side
from runcore import TicketState, depends_rows

if TYPE_CHECKING:  # run imports this module; the types only
    from run import Effort, View

SALVAGE_REF = "refs/one-punch/salvage/{ticket}"
SMOKE_TIMEOUT_S = 300


@dataclass
class Worker:
    proc: subprocess.Popen[bytes]
    bundle: Path
    candidate: Candidate
    role: str = review.AUTHOR


def remove_worktree(git: Git, path: Path) -> None:
    git.run("worktree", "remove", "--force", "--force", str(path), check=False)
    shutil.rmtree(path, ignore_errors=True)
    git.run("worktree", "prune", check=False)


def stage_worktree(e: Effort, tid: str, role: str) -> Path:
    return e.git.repo / e.rc.worktrees_dir / f"{tid}.{role}"


def ident_env(git: Git) -> dict[str, str]:
    """git's environment, with the harness's identity when none is configured."""
    env = git_env()
    if git.run("var", "GIT_COMMITTER_IDENT", check=False).returncode != 0:
        env.update(GIT_AUTHOR_NAME="one-punch harness", GIT_AUTHOR_EMAIL="harness@localhost")
        env.update(GIT_COMMITTER_NAME="one-punch harness", GIT_COMMITTER_EMAIL="harness@localhost")
    return env


def spawn(e: Effort, bundle: Path, instructions: str, candidate: Candidate, role: str, cwd: Path, attempt: int) -> Worker:
    """Write the bundle (instructions.md, params.json naming the model) and
    start its launcher in its own session."""
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "instructions.md").write_text(instructions, encoding="utf-8")
    worker: dict[str, str] = {"tool": candidate.tool, "model": candidate.model, **({"effort": candidate.effort} if candidate.effort else {})}
    params = {"contract": 1, "role": role, "worker": worker, "isolation": review.isolation_for(candidate), "cwd": str(cwd),
              "timeout_s": e.rc.worker_timeout_s, "attempt": attempt}
    (bundle / "params.json").write_text(json.dumps(params, indent=2) + "\n", encoding="utf-8")
    with open(bundle / "launcher.out", "wb") as out, open(bundle / "launcher.err", "wb") as err:
        proc = subprocess.Popen([sys.executable, str(e.rc.launchers[candidate.tool]), str(bundle)], cwd=bundle,
                                stdout=out, stderr=err, start_new_session=True)
    return Worker(proc, bundle, candidate, role)


def zone_checklists(e: Effort, view: View, ticket: Ticket) -> dict[str, str | None]:
    """The domain checklists of the blast-map zones the ticket's Touches
    overlap (B2+), with their sources (None when a source is missing)."""
    if ticket.blast.value < Blast.B2.value:
        return {}
    valid = load_blast_map(e.git.show(view.head, e.cfg.blast_map_file), e.cfg.ref_pattern)
    names = core.ticket_zones(ticket.touches, view.blast_map, view.tree)
    ids = frozenset(z.checklist for z in valid.zones if z.name in names and z.checklist)
    return checklist_sources(e.git, e.cfg, view.head, ids)


def diff_checklists(e: Effort, view: View, ticket: Ticket, base: str, tip: str) -> frozenset[str]:
    """The checklists integrate will require of this diff (its blast
    evaluation includes pattern hits outside the Touches zones)."""
    git, cfg = e.git, e.cfg
    try:
        bmap = load_blast_map(git.show(view.head, cfg.blast_map_file), cfg.ref_pattern)
        ledger = parse_ledger(git.show(view.head, cfg.ledger_file), cfg.ref_pattern)
    except (BlastMapError, LedgerError):
        return frozenset()
    entries = parse_diff(git.out(*DIFF_ARGS, "--unified=0", base, tip))
    return frozenset(evaluate(bmap, entries, ticket.blast, active_decisions(ledger)).checklists)


def lens_candidate(e: Effort) -> Candidate | None:
    """The decorrelated lens for this run: `[run] lens` when its
    `lens_smoke` command exits 0 (ledgered), else None (the lens falls back
    to the top ladder rung, a fresh session that sees no transcript)."""
    if e.rc.lens is None:
        return None
    ran = run_command(e.rc.lens_smoke, e.git.repo, SMOKE_TIMEOUT_S)
    ok = ran.exit_code == 0
    append_event(e.events, {"event": "lens-smoke", "ts": _now(), "tool": e.rc.lens.tool, "model": e.rc.lens.model,
                            "command": e.rc.lens_smoke, "ok": ok, "exit": ran.exit_code, "tail": ran.output[-1000:]})
    return e.rc.lens if ok else None


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _event(e: Effort, event: str, **fields: object) -> None:
    append_event(e.events, {"event": event, "ts": _now(), "t": time.time(), **fields})


def launch_stage(e: Effort, view: View, ticket: Ticket, routed: Routed, role: str) -> Worker:
    """Cut the stage's worktree, write its bundle, launch it, ledger it."""
    git, cfg, tid = e.git, e.cfg, ticket.id
    state = view.ledger.states.get(tid, TicketState())
    ref = f"refs/heads/{e.branch(tid)}"
    tip = git.rev(ref)
    remove_worktree(git, e.worktree(tid))
    wt = stage_worktree(e, tid, role)
    remove_worktree(git, wt)
    salvage = ""
    if role == TEST_AUTHOR:
        cut = view.head
        if tip and git.run("merge-base", "--is-ancestor", tip, view.head, check=False).returncode != 0:
            salvage = tip
            git.run("update-ref", SALVAGE_REF.format(ticket=tid), tip)
    elif tip is None:
        raise RuntimeError(f"STAGE-NO-BRANCH {ref} is missing for the {role} dispatch")
    else:
        cut = tip
    git.run("worktree", "add", "--detach", "--quiet", str(wt), cut)
    base = git.out("merge-base", view.head, cut).strip()
    files = sorted({p for f in parse_diff(git.out(*DIFF_ARGS, "--unified=0", base, cut)) for p in f.paths()})
    review_root = cfg.review_path(tid)
    text = view.texts[tid]
    agents_md = git.show(view.head, "AGENTS.md") is not None
    checklists: dict[str, str | None] = {}
    if role == TEST_AUTHOR:
        checklists = zone_checklists(e, view, ticket)
        instructions = review.build_test_author_instructions(ticket=ticket, ticket_text=text, test_globs=cfg.test_globs,
                                                             verify=cfg.verify, checklists=checklists, agents_md=agents_md)
    elif role == SPEC:
        instructions = review.build_spec_instructions(ticket=ticket, ticket_text=text, base=base, files=files,
                                                      handoff_path=cfg.handoff_path(tid), review_root=review_root)
    elif role == LENS:
        ids = frozenset(zone_checklists(e, view, ticket)) | diff_checklists(e, view, ticket, base, cut)
        checklists = checklist_sources(git, cfg, view.head, ids)
        instructions = review.build_lens_instructions(ticket=ticket, ticket_text=text, base=base, files=files,
                                                      review_root=review_root, checklists=checklists)
    elif role == MERGE:
        partners = [p for p in state.conflict_with if p in view.texts]
        by_id = {t.id: t for t in view.tickets}
        depends = sorted({*ticket.depends_on, *(d for p in partners if p in by_id for d in by_id[p].depends_on)})
        instructions = review.build_merge_instructions(
            ticket=ticket,
            this=Side(tid, text, git.show(cut, cfg.handoff_path(tid))),
            partners=[Side(p, view.texts[p], git.show(view.head, cfg.handoff_path(p))) for p in partners],
            onto=view.head,
            conflicted=state.conflict_paths,
            depends_rows=depends_rows(git.show(view.head, cfg.ledger_file) or "", depends),
            verify=cfg.verify,
        )
    else:
        raise RuntimeError(f"STAGE-UNKNOWN role {role!r}")
    number = state.dispatches + 1
    bundle = git.repo / e.rc.bundles_dir / tid / f"{role}-{number}"
    worker = spawn(e, bundle, instructions, routed.candidate, role, wt, number)
    c = routed.candidate
    _event(e, "launch", ticket=tid, role=role, launch=state.launches, dispatch=number, tool=c.tool, model=c.model, effort=c.effort,
           tier=routed.tier.name, explored=False, escalated=False, failures=ticket.attempts, start=tip or "", cut=cut,
           base=view.head, bundle=str(bundle), checklists=sorted(checklists), salvage=salvage)
    return worker


def _lines(git: Git, wt: Path, *args: str) -> tuple[str, ...]:
    return tuple(p for p in git.out(*args, cwd=wt).split("\0") if p)


def accept_stage(e: Effort, view: View, tid: str, state: TicketState) -> None:
    """Judge a stage that exited cleanly; commit and move the branch, or
    reject it. Appends one `stage` event and removes the stage worktree."""
    git, cfg, role = e.git, e.cfg, state.role
    wt = stage_worktree(e, tid, role)
    ref = f"refs/heads/{e.branch(tid)}"
    ticket = next((t for t in view.tickets if t.id == tid), None)

    def done(ok: bool, reason: str = "", **fields: object) -> None:
        _event(e, "stage", ticket=tid, role=role, ok=ok, reason=reason, model=state.model, **fields)
        remove_worktree(git, wt)

    if ticket is None or not wt.is_dir():
        return done(False, "the stage worktree or the ticket is gone")
    head = git.out("rev-parse", "HEAD", cwd=wt).strip()
    if role == MERGE:
        in_rebase = any((wt / git.out("rev-parse", "--git-path", d, cwd=wt).strip()).exists() for d in ("rebase-merge", "rebase-apply"))
        if in_rebase:
            git.run("rebase", "--abort", cwd=wt, check=False)
            return done(False, "the merge agent left the rebase unfinished")
        if git.run("merge-base", "--is-ancestor", state.base, head, check=False).returncode != 0:
            return done(False, f"HEAD {head[:12]} is not rebased onto the integration head {state.base[:12]}")
        if git.out("rev-list", "--merges", f"{state.base}..{head}").strip():
            return done(False, "the result has merge commits; rebase only")
        if git.out("status", "--porcelain", "--untracked-files=no", cwd=wt).strip():
            return done(False, "the merge agent left uncommitted changes")
        if not git.cas(ref, head, state.start):
            return done(False, f"{ref} moved during the merge")
        return done(True, commit=head, rereview=list(review.rereview_after_merge(ticket)))
    scope = Scope(
        committed=_lines(git, wt, "diff", "--name-only", "-z", state.cut, "HEAD") if head != state.cut else (),
        modified=_lines(git, wt, "diff", "--name-only", "-z", "HEAD"),
        untracked=_lines(git, wt, "ls-files", "--others", "--exclude-standard", "-z"),
    )
    review_root = cfg.review_path(tid)
    kept, violations = review.keep(role, scope, review_root, state.checklists, cfg.test_globs, ticket.touches)
    if violations:
        return done(False, "; ".join(violations))
    files = {p: (wt / p).read_text(encoding="utf-8", errors="replace") for p in kept if (wt / p).is_file()}
    problems = review.stage_problems(role, files, review_root, checklist_sources(git, cfg, view.head, frozenset(state.checklists)))
    if problems:
        return done(False, "; ".join(problems))
    if git.out("status", "--porcelain", "--untracked-files=all", "--", *kept, cwd=wt).strip():
        env = ident_env(git)
        c = state.model
        for args in (("add", "--", *kept), ("commit", "--quiet", "--no-verify", "-m", f"{role}: ticket {tid} ({c})", "--", *kept)):
            proc = subprocess.run(["git", *args], cwd=wt, env=env, capture_output=True, text=True)
            if proc.returncode != 0:
                return done(False, f"git {args[0]} failed: {proc.stderr.strip()[-300:]}")
        head = git.out("rev-parse", "HEAD", cwd=wt).strip()
    moved = git.cas(ref, head, state.start) if state.start else git.run("update-ref", ref, head, "", check=False).returncode == 0
    if not moved:
        return done(False, f"{ref} moved during the {role} dispatch")
    verdict = review.read_verdict(files.get(f"{review_root}/{review.SPEC_FILE if role == SPEC else review.LENS_FILE}"))
    return done(True, commit=head, verdict=verdict if role in (SPEC, LENS) else None, files=list(kept))


def teardown_path(e: Effort, tid: str, role: str) -> Path:
    return e.worktree(tid) if role == review.AUTHOR else stage_worktree(e, tid, role)


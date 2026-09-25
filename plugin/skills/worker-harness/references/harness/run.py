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
function in the first half of this file; the second half executes them.

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
import random
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import core
from checks.blastmap import BlastMapError, extract_blast_map, load_blast_map
from checks.config import ConfigError, IntegrateConfig, parse_config
from checks.ledger import LedgerError, handoff_status, parse_ledger
from core import Blast, Candidate, Routed, Ticket, TicketHeaderError, Tier
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

HERE = Path(__file__).resolve().parent
STOP_CODES = {"FRONTIER-EMPTY": 0, "ALL-PARKED": 3, "DECISIONS-NEEDED": 4, "ALL-COOLING": 5, "STOPPED": 6, "KILLED": 7}
EXIT_REFUSED, EXIT_LOCKED = 30, 31
DEFAULT_LAUNCHERS = {"claude": "claude_p.py", "codex": "codex_p.py", "grok": "grok_p.py", "mini": "mini_p.py", "mock": "mock.py"}
DEFAULT_LIMIT_PATTERNS = ("rate limit", "rate_limit", "usage limit", "limit reached", "429", "overloaded", "quota")
BUSY = frozenset({"running", "exited", "awaiting", "merged", "parked"})


# ==========================================================================
# Pure core of the loop
# ==========================================================================


@dataclass(frozen=True)
class RunConfig:
    ladder: Mapping[Tier, tuple[Candidate, ...]]
    launchers: Mapping[str, Path]
    parallel: int = 4
    park_k: int = 2
    worker_timeout_s: int = 3600
    poll_s: float = 2.0
    cooldown_s: int = 3600
    closure_timeout_s: int = 600
    worktrees_dir: str = ".worktrees"
    bundles_dir: str = ".worktrees/.bundles"
    stop_file: str = ".worktrees/STOP"
    ledger_snapshot: str = ".scratch/{effort}/ledger/events.jsonl"
    field_guide: str = "docs/field-guide/index.md"
    field_guide_budget: int = 150
    limit_patterns: tuple[str, ...] = DEFAULT_LIMIT_PATTERNS


def parse_run_config(data: Mapping[str, Any], effort: str) -> RunConfig:
    """The `[run]` table -> RunConfig; CONFIG-INVALID on anything unknown,
    a missing ladder, a model-less or Fable candidate, or a tool without a
    launcher file."""

    def fail(reason: str) -> ConfigError:
        return ConfigError(f"CONFIG-INVALID: [run] {reason}")

    table = data.get("run")
    if not isinstance(table, dict):
        raise fail("table missing (the tier ladder is operator-owned data; no default)")
    ints = {"parallel", "park_k", "worker_timeout_s", "cooldown_s", "closure_timeout_s", "field_guide_budget"}
    strs = {"worktrees_dir", "bundles_dir", "stop_file", "ledger_snapshot", "field_guide"}
    unknown = sorted(set(table) - ints - strs - {"ladder", "launchers", "poll_s", "limit_patterns"})
    if unknown:
        raise fail(f"unknown key(s) {unknown}")
    values: dict[str, Any] = {}
    for key in ints & set(table):
        if type(table[key]) is not int or table[key] < 1:
            raise fail(f"{key} must be a positive integer")
        values[key] = table[key]
    for key in strs & set(table):
        if not isinstance(table[key], str) or not table[key]:
            raise fail(f"{key} must be a non-empty string")
        values[key] = table[key].format(effort=effort)
    values.setdefault("ledger_snapshot", RunConfig.ledger_snapshot.format(effort=effort))
    if "poll_s" in table:
        if not isinstance(table["poll_s"], (int, float)) or table["poll_s"] <= 0:
            raise fail("poll_s must be a positive number")
        values["poll_s"] = float(table["poll_s"])
    if "limit_patterns" in table:
        pats = table["limit_patterns"]
        if not isinstance(pats, list) or not all(isinstance(p, str) and p for p in pats):
            raise fail("limit_patterns must be an array of non-empty strings")
        values["limit_patterns"] = tuple(pats)
    launchers = {tool: HERE / "launchers" / name for tool, name in DEFAULT_LAUNCHERS.items()}
    raw_launchers = table.get("launchers", {})
    if not isinstance(raw_launchers, dict) or not all(isinstance(v, str) for v in raw_launchers.values()):
        raise fail("launchers must be a table of tool = path")
    launchers.update({tool: HERE / path for tool, path in raw_launchers.items()})  # absolute paths stay absolute
    raw_ladder = table.get("ladder")
    if not isinstance(raw_ladder, dict) or not raw_ladder:
        raise fail("ladder missing: {T0 = [{tool, model, effort?}], ...}")
    ladder: dict[Tier, tuple[Candidate, ...]] = {}
    for tier_name, rungs in raw_ladder.items():
        if tier_name not in Tier.__members__ or not isinstance(rungs, list) or not rungs:
            raise fail(f"ladder.{tier_name}: want T0..T5 = a non-empty array of candidates")
        cands = []
        for rung in rungs:
            if not isinstance(rung, dict) or set(rung) - {"tool", "model", "effort"}:
                raise fail(f"ladder.{tier_name}: a candidate is {{tool, model, effort?}}")
            tool, model, effort_ = rung.get("tool"), rung.get("model"), rung.get("effort", "")
            if not isinstance(tool, str) or not isinstance(model, str) or not model or not isinstance(effort_, str):
                raise fail(f"ladder.{tier_name}: every candidate names its tool and model")
            if "fable" in model.lower():
                raise fail(f"ladder.{tier_name}: {model!r} — no Fable model is ever routed headless")
            if not launchers.get(tool, Path("/nonexistent")).is_file():
                raise fail(f"ladder.{tier_name}: no launcher file for tool {tool!r}")
            cands.append(Candidate(tool, model, effort_))
        ladder[Tier[tier_name]] = tuple(cands)
    return RunConfig(ladder=ladder, launchers=launchers, **values)


_DECISIONS = re.compile(r"^Decisions needed\b[^:\n]*:(?P<rest>.*)$")
_FIELD = re.compile(r"^[A-Z][A-Za-z /_-]*(?:\([^)\n]*\))?:")
_ITEM = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(?P<text>.*)$")
_NOT_REVERSIBLE = re.compile(r"\b(?:not|non|ir)[\s-]?reversible\b|\bone[\s-]way\b", re.I)
_NONE = frozenset({"", "none", "none.", "—", "-", "n/a", "no", "…"})


def decision_items(handoff: str) -> list[tuple[str, bool]]:
    """`Decisions needed` items of a handoff as (text, reversible). An item
    is reversible only when it says so ("reversible") and nothing negates
    it (not/non/ir-reversible, one-way); an unmarked item fails closed."""
    items: list[str] = []
    inside = False
    for line in handoff.splitlines():
        match = _DECISIONS.match(line)
        if match is not None:
            inside, rest = True, match.group("rest").strip()
            if rest:
                items.append(rest)
            continue
        if not inside:
            continue
        if _FIELD.match(line) and not _ITEM.match(line):
            break
        item = _ITEM.match(line)
        if item is not None:
            items.append(item.group("text").strip())
        elif line.strip() and items:
            items[-1] += " " + line.strip()
    kept = [i for i in items if i.strip().lower() not in _NONE]
    return [(i, "reversible" in i.lower() and not _NOT_REVERSIBLE.search(i)) for i in kept]


def acceptance_commands(text: str) -> list[str]:
    """The machine checks of a ticket: indented lines directly under an
    `Acceptance:` line, and every line of a fenced block inside an
    `Acceptance` section (`Acceptance:` up to the next heading, or a
    `## Acceptance` heading up to the next heading). Comments skipped."""
    commands: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        heading = re.match(r"^#+\s*Acceptance\b", line)
        if not (heading or line.startswith("Acceptance:")):
            i += 1
            continue
        i += 1
        in_fence = False
        while i < len(lines) and (in_fence or not lines[i].startswith("#")):
            cur = lines[i]
            if cur.lstrip().startswith("```"):
                in_fence = not in_fence
            elif in_fence or cur[:1] in (" ", "\t"):
                if cur.strip() and not cur.strip().startswith("#"):
                    commands.append(cur.strip())
            elif cur.strip() and not heading:
                break
            i += 1
    return commands


def set_header(text: str, key: str, value: str) -> str:
    """Replace the first `Key: …` header line's value; a missing key goes
    right after the `Status:` line."""
    line = f"{key}: {value}"
    new, count = re.subn(rf"^{re.escape(key)}:[^\n]*$", lambda _: line, text, count=1, flags=re.M)
    if count:
        return new
    return re.sub(r"^(Status:[^\n]*)$", lambda m: f"{m.group(1)}\n{line}", text, count=1, flags=re.M)


def is_limit(summary: str, patterns: Sequence[str]) -> bool:
    low = summary.lower()
    return any(p.lower() in low for p in patterns)


def _t(event: Mapping[str, Any]) -> float:
    if isinstance(event.get("t"), (int, float)):
        return float(event["t"])
    try:
        return datetime.datetime.strptime(str(event.get("ts")), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()
    except ValueError:
        return 0.0


def failure_note(event: Mapping[str, Any]) -> str:
    """The root-cause note a retry carries: integrate's failures and verify tails."""
    lines = [f"integrate {event.get('outcome')}" + (f": {event['reason']}" if event.get("reason") else "")]
    for check in event.get("checks") or []:
        lines += [str(f) for f in check.get("failures", [])]
    for run in event.get("verify_failures") or []:
        lines.append(f"verify `{run.get('command')}` exited {run.get('exit')}:\n{str(run.get('tail', ''))[-1500:]}")
    return "\n".join(lines)[:6000]


@dataclass
class TicketState:
    phase: str = "idle"  # idle | running | exited | awaiting | merged | parked
    failures: int = 0  # failed attempts since the last `relaunch` (core.route's attempts)
    launches: int = 0
    park_kind: str = ""
    park_reason: str = ""
    notes: list[str] = field(default_factory=list)
    last_failure: str = ""
    escalated_to: str = ""
    head_moved: int = 0
    start: str = ""  # the branch tip the running launch started from
    bundle: str = ""
    candidate: Candidate | None = None
    packet: str = ""
    judged: str = ""
    ticket_head: str = ""


@dataclass(frozen=True)
class Ledger:
    states: Mapping[str, TicketState]
    core_events: tuple[core.Event, ...]
    merged: int
    interventions: int
    last_stop: str


def _candidate(event: Mapping[str, Any]) -> Candidate:
    return Candidate(str(event.get("tool")), str(event.get("model")), str(event.get("effort") or ""))


def _cost(usage: Any) -> tuple[float, int]:
    usage = usage if isinstance(usage, dict) else {}
    cost, turns = usage.get("cost_usd"), usage.get("num_turns")
    return (float(cost) if isinstance(cost, (int, float)) else 0.0, turns if type(turns) is int else 0)


def fold_ledger(events: Sequence[Mapping[str, Any]]) -> Ledger:
    """Every ticket's state, and the routing inputs, from the event ledger."""
    states: dict[str, TicketState] = {}
    outcomes: list[core.Event] = []
    merged: set[str] = set()
    interventions = 0
    last_stop = ""

    def park(s: TicketState, kind: str, reason: str) -> None:
        s.phase, s.park_kind, s.park_reason = "parked", kind, reason

    def outcome(s: TicketState, tid: str, ev: Mapping[str, Any], ok: bool, usage: Any) -> None:
        if s.candidate is not None:
            cost, turns = _cost(usage)
            outcomes.append(core.Outcome(_t(ev), tid, s.candidate, ok, cost, turns))

    def fail(s: TicketState, tid: str, ev: Mapping[str, Any], note: str, usage: Any) -> None:
        s.failures, s.phase, s.last_failure = s.failures + 1, "idle", note
        outcome(s, tid, ev, False, usage)

    for ev in events:
        kind, tid = ev.get("event"), ev.get("ticket")
        if kind == "run-stop":
            last_stop = str(ev.get("reason"))
        if not isinstance(tid, str):
            continue
        s = states.setdefault(tid, TicketState())
        if kind == "launch":
            s.phase, s.launches, s.head_moved = "running", s.launches + 1, 0
            s.start, s.bundle, s.candidate = str(ev.get("start")), str(ev.get("bundle")), _candidate(ev)
        elif kind == "worker-exit":
            if ev.get("limit"):
                s.phase = "idle"
                outcomes.append(core.LimitHit(_t(ev), _candidate(ev), float(ev.get("retry_at") or 0.0)))
            elif not ev.get("ok"):
                fail(s, tid, ev, f"the worker session failed: {ev.get('summary')}", ev.get("tokens"))
            else:
                s.phase = "exited"
        elif kind == "park":
            park(s, str(ev.get("kind")), str(ev.get("reason")))
        elif kind == "teardown":
            s.phase = "idle"
        elif kind == "intervention":
            interventions += 1
            s.phase, s.park_kind, s.park_reason = "idle", "", ""
            s.notes.append(str(ev.get("note") or ""))
            if ev.get("kind") == "relaunch":
                s.failures = 0
        elif kind == "integrate":
            result = ev.get("outcome")
            if result == "MERGED":
                if ev.get("approved"):
                    interventions += 1
                elif s.phase in ("exited", "running"):
                    outcome(s, tid, ev, True, ev.get("tokens"))
                s.phase, s.judged, s.ticket_head = "merged", str(ev.get("judged")), str(ev.get("ticket_head"))
                merged.add(tid)
            elif result == "AWAITING-OPERATOR":
                outcome(s, tid, ev, True, ev.get("tokens"))
                s.phase, s.packet = "awaiting", str(ev.get("packet"))
            elif result == "FAILED":
                fail(s, tid, ev, failure_note(ev), ev.get("tokens"))
            elif result == "BLAST-ESCALATION":
                s.escalated_to, s.phase = str(ev.get("effective_blast")), "idle"
                s.last_failure = failure_note(ev)
                if s.escalated_to == "B3":
                    park(s, "blast-b3", "escalated to B3: needs the B3 path (tests first, lens, operator review)")
            elif result == "CONFLICT":
                park(s, "conflict", f"rebase conflict on {ev.get('conflicted_paths')} with tickets {ev.get('conflict_with')}: merge agent")
            elif result == "HEAD-MOVED":
                s.head_moved += 1
                if s.head_moved >= 2:
                    park(s, "head-moved", str(ev.get("reason")))
                else:
                    s.phase = "exited"
            elif result == "REFUSED":
                reason = str(ev.get("reason"))
                if reason.startswith(("HANDOFF-MISSING", "NOTHING-TO-INTEGRATE")):
                    fail(s, tid, ev, failure_note(ev), ev.get("tokens"))
                elif reason.startswith("HANDOFF-STATUS"):
                    park(s, "blocked", reason)
                elif not reason.startswith("APPROVE-NOTHING-AWAITING"):
                    park(s, "refused", reason)
    return Ledger(states, tuple(outcomes), len(merged), interventions, last_stop)


def compatible(a: Ticket, b: Ticket, blast_map: core.BlastMap, tree: Collection[str]) -> bool:
    """select_batch's pairwise rule, for a candidate against an in-flight ticket."""
    if core.touches_overlap(a.touches, b.touches, tree):
        return False
    if Blast.B3 in (a.blast, b.blast):
        return not (core.ticket_zones(a.touches, blast_map, tree) & core.ticket_zones(b.touches, blast_map, tree))
    return True


@dataclass(frozen=True)
class Round:
    launch: tuple[tuple[Ticket, Routed], ...] = ()
    park: tuple[tuple[str, str], ...] = ()
    stop: str | None = None


def plan_round(
    tickets: Sequence[Ticket],
    ledger: Ledger,
    inflight: Collection[str],
    n: int,
    k: int,
    ladder: Mapping[Tier, tuple[Candidate, ...]],
    now: float,
    blast_map: core.BlastMap,
    tree: Collection[str],
) -> Round:
    """One scheduling round: what to launch, what to park, whether to stop.
    `tickets` carry their failed-attempt counts; a stop other than
    DECISIONS-NEEDED is returned only when nothing is in flight."""
    states = ledger.states
    live = {t.id: states.get(t.id, TicketState()) for t in tickets if t.status != "done"}
    if sum(1 for s in live.values() if s.phase == "parked" and s.park_kind == "decision") >= k:
        return Round(stop="DECISIONS-NEEDED")
    stats, governor = core.fold(ledger.core_events)
    running = [t for t in tickets if t.id in inflight]
    routes: dict[str, Routed] = {}
    parks: list[tuple[str, str]] = []
    cooling = False
    for t in core.frontier(tickets):
        if t.id in inflight or live[t.id].phase in BUSY or not all(compatible(t, r, blast_map, tree) for r in running):
            continue
        decision = core.route(t, ladder, stats, governor, now, random.Random(f"{t.id}:{live[t.id].launches}").random())
        if isinstance(decision, Routed):
            routes[t.id] = decision
        elif t.attempts > core.MAX_ESCALATIONS:
            parks.append((t.id, decision.reason))
        else:
            cooling = True
    batch = core.select_batch(
        [t for t in tickets if t.id in routes],
        max(0, n - len(inflight)),
        blast_map,
        tree,
        critical_path=core.critical_path(tickets),
    )
    launch = tuple((t, routes[t.id]) for t in batch)
    stop = None
    if not inflight and not launch and not parks:
        held = any(s.phase in ("parked", "awaiting") for s in live.values())
        stop = "ALL-COOLING" if cooling else "ALL-PARKED" if held else "FRONTIER-EMPTY"
    return Round(launch, tuple(parks), stop)


LEVEL_STEPS = {
    Blast.B0: ["The project's verify commands pass. Nothing further is required."],
    Blast.B1: ["Test-driven at the ticket's seams (the red → green rule below)."],
    Blast.B2: [
        "Test the edge and error paths at the public seam, not only the happy path; coverage on the files you touch must not drop.",
        "Keep decision logic in the pure core, side effects in a thin shell. A spec-verdict review against the ticket follows.",
    ],
    Blast.B3: [
        "Acceptance tests written first by an independent agent are already committed on your branch: make them pass; never weaken, skip or delete them.",
        "Add adversarial and negative tests for every checklist item below that applies to your change.",
        "Decision logic pure and property-tested on its own; the effectful shell thin enough to review line by line.",
        "Prefer a vetted library or the ticket's Reference over hand-rolling. A decorrelated lens reviews the diff and the operator reads it before it merges.",
    ],
}
TDD_RULE = (
    "Red → green: before each behavior change, write a test for it, run it and watch it fail for the reason you "
    "expect; then write the smallest code that makes it pass; refactor only while the tests are green. Never write "
    "implementation ahead of a failing test, and never weaken a test to get green."
)
HANDOFF_SCHEMA = """Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
Commits: <sha list>
Done: …
Deviations: … (incl. any BREAKING)
Decisions needed: …
Findings / concerns: …
Field-guide proposals: …"""


def build_instructions(
    *,
    ticket: Ticket,
    ticket_text: str,
    branch: str,
    base: str,
    handoff_path: str,
    verify: Sequence[str],
    agents_md: bool,
    field_guide: str | None,
    depends_rows: Sequence[str],
    checklists: Mapping[str, str],
    state: TicketState,
) -> str:
    """The worker preamble (plan §3.8) plus the ticket text. Skill loading in
    headless workers is unreliable (spike 02), so the TDD rule, the level's
    steps and the domain checklists travel inline."""
    level = ticket.blast
    out = [
        f"# Worker instructions — ticket {ticket.id}",
        "",
        f"You are a worker executing exactly this one ticket, in a git worktree (your current directory) on branch "
        f"`{branch}`, cut from the integration head {base[:12]}. You never plan across tickets, never talk to other "
        "workers, and never decide a decision-ledger question.",
        "",
        "## Rules",
        "",
        *(["- Read `AGENTS.md` at the repository root first; its rules and its code-style section bind you."] if agents_md else []),
        f"- Change only paths matching your Touches: {', '.join(f'`{g}`' for g in ticket.touches)}. A change outside them "
        "is allowed only when the ticket genuinely requires a core change: leave `BREAKING(D-NNN): <why>` at the "
        "change site, propose the ledger row in your handoff if none exists, and list it under Deviations.",
        "- Stage files by explicit path (`git add -- <path>`), only files within your Touches plus your handoff. "
        "Never `git add -A` or `git add .`; never commit build artifacts (`__pycache__`, `node_modules`, caches).",
        "- Commit on your branch only. Never merge, rebase, push or switch branches; never edit your ticket file, "
        "other tickets, the decision ledger, the blast map, `AGENTS.md` or `harness.toml`.",
        "- If you meet an undecided cross-ticket question, take the local, reversible option and report it under "
        "Decisions needed. No TODOs, no placeholders, no partial implementations.",
        f"- {TDD_RULE}",
        "- Before you finish, run the project's verify commands and make them pass: "
        + "; ".join(f"`{c}`" for c in verify)
        + ". The harness re-runs them; your word is never the evidence.",
        "",
        f"## Blast level {level.name}" + (f" — {ticket.blast_reason}" if ticket.blast_reason else ""),
        "",
        *(f"- {step}" for lvl in Blast if lvl.value <= level.value for step in LEVEL_STEPS[lvl]),
    ]
    if level.value >= Blast.B2.value:
        out += ["", "## Domain checklists", ""]
        out += [f"### {cid}\n\n{text.strip()}\n" for cid, text in sorted(checklists.items())] or [
            "No domain-checklist zone overlaps your Touches."
        ]
    if depends_rows:
        out += ["", "## Decisions you must honor (Depends-on)", "", *depends_rows]
    if field_guide:
        out += ["", "## Field guide", "", field_guide.strip()]
    if state.notes or state.last_failure or state.launches:
        out += ["", "## Previous attempts", ""]
        if state.launches:
            out.append("Your worktree and branch hold the earlier attempts' work (commits, and any uncommitted changes): salvage it, do not start over blindly.")
        if state.last_failure:
            out += ["", "The last attempt failed. Root cause as the harness recorded it — fix this first:", "", "```", state.last_failure, "```"]
        for note in state.notes:
            out += ["", f"Operator note (decided; apply it, and do not list it under Decisions needed): {note}"]
    out += [
        "",
        "## Handoff (required)",
        "",
        f"Write `{handoff_path}` (overwrite any earlier one) and commit it on your branch as your last commit. Schema:",
        "",
        "```",
        HANDOFF_SCHEMA,
        "```",
        "",
        "Under `Decisions needed:` write `none`, or one bullet per question: `- <question> — local option: <what you did> "
        "— reversible` or `— NOT reversible`. An item not marked reversible parks this ticket for the operator instead of merging it.",
        "",
        "## Ticket",
        "",
        ticket_text.strip(),
        "",
    ]
    return "\n".join(out)


def depends_rows(ledger_text: str, ids: Sequence[str]) -> list[str]:
    """The ledger table's header and the rows of `ids` (plan §3.8 Depends-on)."""
    rows = [line for line in ledger_text.splitlines() if line.startswith("|")]
    picked = [r for r in rows if r.split("|")[1].strip().strip("*`") in ids]
    return rows[:2] + picked if picked else []


# ==========================================================================
# Imperative shell
# ==========================================================================


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
            for tid, why in rnd.park:
                _append(e.events, "park", ticket=tid, kind="escalation", reason=why)
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
                       "state": "running" if run_active else "interrupted (the next run tears it down and redoes it)"}
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
    e.seed_events()
    state = fold_ledger(e.read_events()).states.get(tid)
    if state is None or state.phase in ("running", "exited", "merged"):
        raise RunRefused(f"NOT-PARKED {tid}: {state.phase if state else 'never launched'}")
    if kind == "decision-answered" and state.phase != "parked":
        raise RunRefused(f"NOT-PARKED {tid}: {state.phase}")
    _append(e.events, "intervention", ticket=tid, kind=kind, note=note, was=state.phase, park_kind=state.park_kind)
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
        if args.command in ("answer", "relaunch"):
            print(intervene(e, args.ticket, "decision-answered" if args.command == "answer" else "relaunch", args.note))
            return 0
        with writer_lock(e.git.repo):
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

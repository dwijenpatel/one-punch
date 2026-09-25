"""runcore — the pure core of the build loop (`run.py` is its shell).

No I/O, no clock, no randomness beyond a seeded draw: events, ticket text,
the tree listing and `now` arrive as arguments, so every scheduling decision
is a unit test (test_run.py). Split from run.py so neither crosses the
800-line megafile threshold; routing, frontier, batch selection and the
floors stay in core.py.

- `parse_run_config`: the `[run]` table of harness.toml.
- `fold_ledger`: every ticket's state from the JSONL event ledger.
- `plan_round`: one scheduling round: launch, park, or stop.
- `decision_items`, `acceptance_commands`, `set_header`, `is_limit`,
  `failure_note`: the grammars the loop reads and writes.
- `build_instructions`, `depends_rows`: the worker preamble (plan §3.8).
"""

from __future__ import annotations

import datetime
import random
import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import core
from checks.config import ConfigError
from core import Blast, Candidate, Routed, Ticket, Tier

HERE = Path(__file__).resolve().parent
DEFAULT_LAUNCHERS = {"claude": "claude_p.py", "codex": "codex_p.py", "grok": "grok_p.py", "mini": "mini_p.py", "mock": "mock.py"}
DEFAULT_LIMIT_PATTERNS = ("rate limit", "rate_limit", "usage limit", "limit reached", "429", "overloaded", "quota")
BUSY = frozenset({"running", "exited", "awaiting", "merged", "parked"})
# Until the B3 path exists (ticket 10: tests-first author before the
# implementer, lens), a declared-B3 ticket cannot pass integrate's scrutiny
# check; launching it would burn two top-tier attempts. An operator
# `relaunch` (a note) lifts the hold once the tests-first commit is on the branch.
B3_HOLD = "B3 path: independent tests-first commit and lens are not dispatched by this harness yet; relaunch once they are on the branch"


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
_NOT_REVERSIBLE = re.compile(r"\bnot\b(?:\s+\w+){0,2}?\s+reversible\b|\b(?:non|ir)[\s-]?reversible\b|\bone[\s-]way\b", re.I)
_NONE = frozenset({"", "none", "none.", "—", "-", "n/a", "no", "…"})


def decision_items(handoff: str) -> list[tuple[str, bool]]:
    """`Decisions needed` items of a handoff as (text, reversible). An item
    is reversible only when it says so ("reversible") and nothing negates
    it ("not [locally] reversible", non-/irreversible, one-way); an unmarked
    item fails closed."""
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
                elif reason.startswith("INTEGRATION-BRANCH-CHECKED-OUT"):
                    s.phase = "exited"  # transient: integrate again once it is switched away
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
    park: tuple[tuple[str, str, str], ...] = ()  # (ticket, kind, reason)
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
    parks: list[tuple[str, str, str]] = []
    cooling = False
    for t in core.frontier(tickets):
        if t.id in inflight or live[t.id].phase in BUSY or not all(compatible(t, r, blast_map, tree) for r in running):
            continue
        if t.blast is Blast.B3 and not live[t.id].notes:
            parks.append((t.id, "b3-path", B3_HOLD))
            continue
        decision = core.route(t, ladder, stats, governor, now, random.Random(f"{t.id}:{live[t.id].launches}").random())
        target = max(core.tier_floor(t.tag, t.size, t.blast).value - t.attempts, 0)
        if isinstance(decision, Routed):
            routes[t.id] = decision
        elif t.attempts > core.MAX_ESCALATIONS:
            parks.append((t.id, "escalation", decision.reason))
        elif not any(ladder.get(Tier(v)) for v in range(target, -1, -1)):
            parks.append((t.id, "unroutable", f"no ladder rung at or above T{target}: add one to [run.ladder]"))
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
        held = any(s.phase in ("parked", "awaiting", "exited") for s in live.values())  # exited: integrate pending
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
        for note in filter(None, state.notes):
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

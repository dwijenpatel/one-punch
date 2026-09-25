"""review — the pure side of the non-author dispatches (plan §3.1, §3.5
step 2, §3.9, §2b "Tests", "Automated review" and "Merge conflicts" rows).

No I/O: the shell (`stages.py`) creates the worktrees, launches, reads
files and commits; everything it decides with comes from here.

Roles beside the implementer (`author`):
- `test_author` (B3): writes the acceptance tests FIRST, from the ticket and
  the domain checklists, before any implementer launch. A separate agent in
  a separate worktree is what makes the tests independent; git cannot prove
  it, so this dispatch order is the guarantee (integrate checks the order).
- `spec_verdict` (B1 `contract`, B2, B3): Missing / Extra / Misunderstood
  against the ticket; writes `<review_dir>/<ticket>/spec-verdict.md` with a
  `Verdict: pass|concerns|fail` line.
- `lens` (B3): the decorrelated review — a different model family (the
  `[run] lens` candidate, used only while its `lens_smoke` passes) else a
  fresh top-tier reviewer; sees the codebase, the ticket and the diff, never
  the implementer's transcript or handoff. Writes `lens.md` and one
  `checklist-<id>.md` per domain checklist in blast-map-format §7 grammar.
- `merge` (integrate CONFLICT): rebases the ticket onto the integration
  head under the `resolving-merge-conflicts` discipline; Sonnet tier, top
  tier when either ticket is B3. A B3 ticket's merged result re-enters
  spec verdict and lens.

Reviewers are read-only: they write only their review files; the harness
commits exactly those (it also commits the test author's test files), and a
change anywhere else rejects the dispatch. Every dispatch names its model;
the ladder refuses Fable models (runcore.parse_run_config).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass

import core
from checks.hygiene import Commit, checklist_items, checklist_problems, compile_globs
from core import Blast, Candidate, Routed, Tag, Ticket, Tier

AUTHOR, TEST_AUTHOR, SPEC, LENS, MERGE = "author", "test_author", "spec_verdict", "lens", "merge"
STAGES = (TEST_AUTHOR, SPEC, LENS, MERGE)
# The phase a ticket returns to when a dispatch of that role is torn down or
# rejected, so the same step runs again (runcore.fold_ledger).
RESTING = {AUTHOR: "idle", TEST_AUTHOR: "idle", SPEC: "exited", LENS: "exited", MERGE: "conflict"}
MAX_STAGE_FAILURES = 2  # rejected dispatches of one role before the ticket parks (`stage`)
MAX_CONFLICTS = 3  # CONFLICT outcomes per implementer attempt before it parks (`conflict`)
SPEC_FILE, LENS_FILE = "spec-verdict.md", "lens.md"
# integrate's grammar (checks.hygiene._VERDICT), read here to reject a
# review that integrate could not read instead of failing the implementer.
_VERDICT = re.compile(r"^Verdict:\s*(?P<verdict>pass|concerns|fail)\b", re.MULTILINE | re.IGNORECASE)
_ANSWER_ID = re.compile(r"^(?P<id>[A-Z]{2}-\d{2}) (?P<verdict>pass|fail|n/a): ")


def required_reviews(ticket: Ticket) -> tuple[str, ...]:
    """The ladder's "Automated review" row at the declared level; integrate
    requires the same at the effective level (checks.hygiene.scrutiny_check)."""
    if ticket.blast is Blast.B3:
        return (SPEC, LENS)
    if ticket.blast is Blast.B2 or (ticket.blast is Blast.B1 and ticket.tag is Tag.CONTRACT):
        return (SPEC,)
    return ()


def next_role(ticket: Ticket, phase: str, tests: bool, reviewed: Mapping[str, str]) -> str | None:
    """The next dispatch for a ticket in `phase`, or None: for `exited`,
    None means integrate now; other phases have no dispatch. `tests` is
    whether the tests-first commit exists; `reviewed` maps each review done
    since the last implementer (or B3 merge) to its verdict. A failed spec
    verdict skips the lens: integrate fails the attempt either way."""
    if phase == "conflict":
        return MERGE
    if phase == "idle":
        return TEST_AUTHOR if ticket.blast is Blast.B3 and not tests else AUTHOR
    if phase != "exited":
        return None
    for role in required_reviews(ticket):
        if role in reviewed:
            continue
        if role == LENS and reviewed.get(SPEC) == "fail":
            return None
        return role
    return None


def rereview_after_merge(ticket: Ticket) -> tuple[str, ...]:
    """Reviews a merged result must repeat: all of B3's (plan §2b), none below."""
    return (SPEC, LENS) if ticket.blast is Blast.B3 else ()


def stage_tier(role: str, ticket: Ticket, partners: Sequence[Ticket]) -> Tier:
    """Tier of a non-author dispatch. Merge: Sonnet (T2), Opus (T0) when
    either side is B3 (plan §3.1). Test author and lens fallback: Opus (the
    B3 floor). Spec verdict: the ticket's own routing floor."""
    if role == MERGE:
        return Tier.T0 if Blast.B3 in (ticket.blast, *(p.blast for p in partners)) else Tier.T2
    if role in (TEST_AUTHOR, LENS):
        return Tier.T0
    return core.tier_floor(ticket.tag, ticket.size, ticket.blast)


def stage_candidate(
    role: str,
    ticket: Ticket,
    partners: Sequence[Ticket],
    ladder: Mapping[Tier, tuple[Candidate, ...]],
    lens: Candidate | None,
    usable: Callable[[Candidate], bool],
) -> Routed | None:
    """The named model for a dispatch: the first `usable` (not cooling)
    candidate at the role's tier, climbing toward T0 as core.route does; for
    the lens, the decorrelated candidate when the caller passes one (its
    smoke passed) and it is usable. None when no candidate qualifies."""
    if role == LENS and lens is not None and usable(lens):
        return Routed(lens, Tier.T0, explored=False, escalated=False)
    for value in range(stage_tier(role, ticket, partners).value, -1, -1):
        for candidate in ladder.get(Tier(value), ()):
            if usable(candidate):
                return Routed(candidate, Tier(value), explored=False, escalated=False)
    return None


def isolation_for(candidate: Candidate) -> dict[str, bool]:
    """Launcher isolation intent. Codex runs in its workspace profile, the
    shape spike 02 (P3) confirmed for a reviewer; every other launcher gets
    the empty intent (plan §9: no walls; integrate guards what lands)."""
    return {"sandbox": True, "network": True} if candidate.tool == "codex" else {}


# --------------------------------------------------------------------------
# Result readers
# --------------------------------------------------------------------------


def read_verdict(text: str | None) -> str | None:
    match = _VERDICT.search(text) if text is not None else None
    return match.group("verdict").lower() if match else None


def outputs(role: str, review_root: str, checklists: Collection[str]) -> tuple[str, ...]:
    """The exact files a reviewer writes (repo-relative)."""
    if role == SPEC:
        return (f"{review_root}/{SPEC_FILE}",)
    if role == LENS:
        return (f"{review_root}/{LENS_FILE}", *(f"{review_root}/checklist-{c}.md" for c in sorted(checklists)))
    return ()


@dataclass(frozen=True)
class Scope:
    """What a dispatch left behind, relative to where it started."""

    committed: tuple[str, ...]  # paths its own commits touched
    modified: tuple[str, ...]  # tracked paths changed, uncommitted
    untracked: tuple[str, ...]


def keep(
    role: str, scope: Scope, review_root: str, checklists: Collection[str], test_globs: Sequence[str], touches: Sequence[str]
) -> tuple[tuple[str, ...], list[str]]:
    """(paths the harness commits, violations). Reviewers may write only
    their `outputs`; the test author only `test_globs` files inside the
    ticket's Touches (integrate's Touches check exempts no test). A committed or
    modified path outside that is a violation (the dispatch is rejected and
    its worktree discarded); untracked files outside it (caches, scratch)
    are left behind with the worktree."""
    if role in (SPEC, LENS):
        allowed = set(outputs(role, review_root, checklists))

        def ok(path: str) -> bool:
            return path in allowed
    else:
        tests, scope_globs = compile_globs(test_globs), compile_globs(touches)

        def ok(path: str) -> bool:
            return any(r.fullmatch(path) for r in tests) and any(r.fullmatch(path) for r in scope_globs)

    violations = [f"{role} changed {p} (outside what it may write)" for p in sorted({*scope.committed, *scope.modified}) if not ok(p)]
    kept = tuple(sorted({p for p in (*scope.committed, *scope.modified, *scope.untracked) if ok(p)}))
    return kept, violations


def stage_problems(role: str, files: Mapping[str, str], review_root: str, checklists: Mapping[str, str | None]) -> list[str]:
    """Why a finished dispatch's output cannot be used (empty when it can).
    `files` maps repo paths to the kept files' text; `checklists` maps each
    checklist id the lens had to answer to its source. A `fail` answer is a
    finding, not a problem: integrate fails the implementer's attempt on it."""
    if role == TEST_AUTHOR:
        return [] if files else ["test_author wrote no test file matching test_globs"]
    problems: list[str] = []
    if role == SPEC and read_verdict(files.get(f"{review_root}/{SPEC_FILE}")) is None:
        problems.append(f"{SPEC_FILE} missing or without a 'Verdict: pass|concerns|fail' line")
    if role == LENS:
        if read_verdict(files.get(f"{review_root}/{LENS_FILE}")) is None:
            problems.append(f"{LENS_FILE} missing or without a 'Verdict: pass|concerns|fail' line")
        for cid, source in sorted(checklists.items()):
            answer = files.get(f"{review_root}/checklist-{cid}.md")
            if answer is None:
                problems.append(f"checklist-{cid}.md missing")
            elif source is not None:
                bad = [p for p in checklist_problems(answer, checklist_items(source)) if not p.endswith(" fail")]
                problems += [f"checklist-{cid}.md: {p}" for p in bad]
    return problems


# --------------------------------------------------------------------------
# Instructions (tool-neutral prose; skills do not load reliably in headless
# workers — spike 02 — so each role's discipline travels inline)
# --------------------------------------------------------------------------

_READ_ONLY = (
    "You are read-only. Do not edit, create, delete, stage or commit any file except the output file(s) named "
    "below; do not run formatters or code generators. The harness commits your output file(s) for you and rejects "
    "this review if anything else changed."
)
VERDICT_RULE = "Begin the file with exactly one line `Verdict: pass`, `Verdict: concerns` or `Verdict: fail`."


def _checklist_section(checklists: Mapping[str, str | None]) -> list[str]:
    out: list[str] = []
    for cid, text in sorted(checklists.items()):
        body = text.strip() if text else "(this checklist's source file is missing; answer from its id's domain)"
        out += [f"### {cid}", "", body, ""]
    return out


def build_test_author_instructions(
    *, ticket: Ticket, ticket_text: str, test_globs: Sequence[str], verify: Sequence[str], checklists: Mapping[str, str | None], agents_md: bool
) -> str:
    """The independent acceptance-test author (plan §2b B3 "Tests"; the
    oracle seat). It never sees an implementation: none exists yet."""
    out = [
        f"# Acceptance-test author — ticket {ticket.id} (blast B3)",
        "",
        "You write the acceptance tests for this ticket BEFORE anyone implements it. A different agent implements it "
        "afterwards and must make your tests pass without weakening them, so your tests are the specification it is held to.",
        "",
        "## Rules",
        "",
        *(["- Read `AGENTS.md` at the repository root first; its rules and code style bind you."] if agents_md else []),
        f"- Write only test files: paths matching {', '.join(f'`{g}`' for g in test_globs)} that are also inside the "
        f"ticket's Touches ({', '.join(f'`{g}`' for g in ticket.touches)}). Never write implementation code or "
        "anything else. Do not commit: the harness commits your test files as the first commit.",
        "- Test the behavior the ticket promises at its public seam, with exact values from the ticket where it gives them.",
        "- For every checklist item below that applies, add the adversarial or negative test that catches it (authz denial "
        "on every path, replay, injection; rollback, concurrent writers, crash mid-transaction, idempotent retry; migration "
        "up/down/up), and a property test where an invariant exists. Name the item id (e.g. `AS-01`) in the test name or a comment.",
        "- The tests fail now (nothing is implemented) but must load and run: import the module path the ticket names, so "
        "they fail on the missing behavior, not on a syntax error in the test.",
        f"- The project's verify commands, for reference: {'; '.join(f'`{c}`' for c in verify)}.",
        "",
        "## Domain checklists",
        "",
        *(_checklist_section(checklists) or ["No domain-checklist zone overlaps the ticket's Touches.", ""]),
        "## Ticket",
        "",
        ticket_text.strip(),
        "",
    ]
    return "\n".join(out)


def _diff_lines(base: str, files: Sequence[str]) -> list[str]:
    return [
        f"The change is `git diff {base}...HEAD` in your current directory (the ticket branch, checked out detached). Files:",
        "",
        *(f"- `{f}`" for f in files),
        "",
    ]


def build_spec_instructions(*, ticket: Ticket, ticket_text: str, base: str, files: Sequence[str], handoff_path: str, review_root: str) -> str:
    """Spec verdict (plan §3.9): Missing / Extra / Misunderstood vs. the ticket."""
    out = [
        f"# Spec-verdict review — ticket {ticket.id} (blast {ticket.blast.name}, {ticket.tag.value})",
        "",
        "You judge whether the change does what the ticket asks: no more, no less. " + _READ_ONLY,
        "",
        *_diff_lines(base, files),
        f"The implementer's own account is in `{handoff_path}`: a claim to check, never evidence.",
        "",
        "## What to write",
        "",
        f"Write `{review_root}/{SPEC_FILE}`. {VERDICT_RULE} Then three sections, each a list of findings with file:line "
        "(or `none`):",
        "",
        "- **Missing** — what the ticket requires that the change does not do (including its acceptance checks and constraints).",
        "- **Extra** — what the change does that the ticket did not ask for (scope creep, drive-by edits, new dependencies).",
        "- **Misunderstood** — where the change does something the ticket asked for, but not the way the ticket means it.",
        "",
        "`fail`: a Missing or Misunderstood finding the ticket's acceptance depends on. `concerns`: findings the operator "
        "should see that do not break acceptance. `pass`: none. Run the project's tests if that settles a question.",
        "",
        "## Ticket",
        "",
        ticket_text.strip(),
        "",
    ]
    return "\n".join(out)


def build_lens_instructions(*, ticket: Ticket, ticket_text: str, base: str, files: Sequence[str], review_root: str, checklists: Mapping[str, str | None]) -> str:
    """The decorrelated lens (plan §3.9): codebase + ticket + diff only."""
    out = [
        f"# Lens review — ticket {ticket.id} (blast B3)",
        "",
        "You are an independent reviewer of a change in a severe blast-radius zone: a wrong change here fails silently "
        "and cannot be undone. Look for what passes the happy-path tests and is still wrong. " + _READ_ONLY,
        "",
        *_diff_lines(base, files),
        "## What to write",
        "",
        f"1. `{review_root}/{LENS_FILE}`. {VERDICT_RULE} Then each finding as "
        "`- [high|medium|low] file:line — problem — failure scenario`. `fail`: any high finding.",
    ]
    for cid in sorted(checklists):
        out.append(
            f"2. `{review_root}/checklist-{cid}.md`: one line per item id of the `{cid}` checklist below, exactly "
            "`<ID> pass: <the test that proves it>`, `<ID> n/a: <why it does not apply>` or `<ID> fail: <the finding>`. "
            "Every item exactly once; no other lines. `pass` needs a test in this change or the codebase that proves "
            "it; if there is none, the item is `fail`."
        )
    out += ["", "## Domain checklists", "", *(_checklist_section(checklists) or ["None applies to this change.", ""])]
    out += ["## Ticket", "", ticket_text.strip(), ""]
    return "\n".join(out)


@dataclass(frozen=True)
class Side:
    """One ticket of a conflict: its id, ticket text and committed handoff."""

    id: str
    text: str
    handoff: str | None


def build_merge_instructions(
    *, ticket: Ticket, this: Side, partners: Sequence[Side], onto: str, conflicted: Sequence[str], depends_rows: Sequence[str], verify: Sequence[str]
) -> str:
    """The neutral merge agent (plan §3.5 step 2). Its discipline is the
    `resolving-merge-conflicts` skill, carried inline in its essentials."""
    out = [
        f"# Merge agent — ticket {ticket.id} onto the integration head",
        "",
        f"Ticket {ticket.id}'s commits (your current directory, detached HEAD) conflict with the integration head "
        f"`{onto}` on: {', '.join(f'`{p}`' for p in conflicted) or '(see git status)'}. "
        + (f"The other side last landed from ticket(s) {', '.join(p.id for p in partners)}. " if partners else "The other side is a planner edit on the integration branch. ")
        + "You are neutral: you favor neither side.",
        "",
        "## Discipline (the `resolving-merge-conflicts` skill, in its essentials)",
        "",
        f"1. Start the rebase: `git rebase {onto}`. See the state: `git status`, the conflicted files, `git log` of both sides.",
        "2. Find why each side made its change: the tickets, handoffs and decisions below, and the commit messages.",
        "3. Resolve each hunk, preserving both intents. Where they are incompatible, keep the one the ledger decisions and "
        "tickets below support and say so in the commit message. Invent no new behavior. Always resolve; never `git rebase --abort`.",
        f"4. Run the project's checks and fix only what the merge broke: {'; '.join(f'`{c}`' for c in verify)}.",
        "5. Finish: `git add` the resolved paths, `GIT_EDITOR=true git rebase --continue`, and repeat until every commit is rebased.",
        "",
        "## Harness constraints",
        "",
        "- Rebase only: never `git merge`, never squash or reorder commits (the tests-first commit must stay first), never "
        "push, never switch or create branches. Leave HEAD at the rebased result; the harness moves the ticket branch.",
        "- Change nothing beyond resolving the conflict between these tickets. Keep both handoffs' meaning; do not rewrite review files.",
        "",
        f"## This ticket ({this.id})",
        "",
        this.text.strip(),
        "",
        f"### Handoff of {this.id}",
        "",
        (this.handoff or "(none committed)").strip(),
        "",
    ]
    for side in partners:
        out += [f"## The other ticket ({side.id})", "", side.text.strip() or "(ticket file not found at the integration head)", "",
                f"### Handoff of {side.id}", "", (side.handoff or "(none committed)").strip(), ""]
    if depends_rows:
        out += ["## Decisions both tickets depend on (Depends-on)", "", *depends_rows, ""]
    return "\n".join(out)


# --------------------------------------------------------------------------
# The AWAITING-OPERATOR review packet (integrate writes it; this renders it)
# --------------------------------------------------------------------------


def packet_readme(
    *,
    ticket: str,
    event: Mapping[str, object],
    reviews: Mapping[str, str],
    commits: Sequence[Commit],
    test_globs: Sequence[str],
    evidence_globs: Sequence[str],
    awaiting_ref: str,
) -> str:
    """README.md of a B3 review packet: what the operator reads before
    `--approve`. `reviews` maps review-file names to their text; each commit
    is tagged `tests`, `evidence` (handoff, reviews) or `work`."""
    tests, evidence = compile_globs(test_globs), compile_globs(evidence_globs)

    def kind(files: Sequence[str]) -> str:
        if files and all(any(r.fullmatch(f) for r in evidence) for f in files):
            return "evidence"
        if files and all(any(r.fullmatch(f) for r in tests) for f in files):
            return "tests"
        return "work"

    hits, checklists = event.get("hits"), event.get("checklists")
    lines = [
        f"# Review packet — ticket {ticket} (AWAITING-OPERATOR)",
        "",
        f"Integration base {event.get('base')}; judged commit {event.get('judged')} (pinned at {awaiting_ref}).",
        f"Declared {event.get('declared_blast')}, effective {event.get('effective_blast')}; "
        f"checklists: {', '.join(str(c) for c in checklists) if isinstance(checklists, list) and checklists else 'none'}.",
        "",
        "Automated review:",
        f"- spec verdict: {read_verdict(reviews.get(SPEC_FILE)) or 'missing'}",
        f"- lens: {read_verdict(reviews.get(LENS_FILE)) or 'missing'}",
    ]
    for name, text in sorted(reviews.items()):
        if name.startswith("checklist-"):
            counts: dict[str, int] = {}
            for line in text.splitlines():
                m = _ANSWER_ID.match(line)
                if m:
                    counts[m.group("verdict")] = counts.get(m.group("verdict"), 0) + 1
            lines.append(f"- {name}: " + (", ".join(f"{n} {v}" for v, n in sorted(counts.items())) or "no answers"))
    lines += ["", "Commit order (the first commit is the independent acceptance tests):"]
    lines += [f"- {c.sha[:12]} [{kind(c.files)}] {', '.join(c.files)}" for c in commits]
    lines += ["", "Blast hits:"]
    if isinstance(hits, list):
        lines += [f"- {h.get('zone')} {h.get('path')} ({h.get('source')}, {h.get('level')})" for h in hits if isinstance(h, dict)]
    warnings = event.get("warnings")
    lines += ["", "Warnings:", *(f"- {w}" for w in (warnings if isinstance(warnings, list) else []))]
    lines += [
        "",
        "Read diff.patch, the lens report and the checklist answers here, then approve with",
        f"`integrate.py --approve {ticket}` or leave it parked.",
    ]
    return "\n".join(lines) + "\n"

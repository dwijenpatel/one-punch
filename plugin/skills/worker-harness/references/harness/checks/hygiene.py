"""The integrate checks (plan §3.5 steps 1, 3, 4) and the outcome decision.

Each check is a pure function returning a `CheckResult`; a check is green
when it has no failures. Warnings never fail (soft caps, licensed breakage
listed for the planner, inactive lowerings); exceptions record every honored
`allow(<rule>): D-NNN` so retro can count them per rule.

Failure tokens (pinned by substring in the tests):
`HANDOFF-MISSING`, `HANDOFF-STATUS`, `VERIFY-FAILED`, `VERIFY-DIRTY`, `REF-UNRESOLVED`,
`TOUCHES-OUTSIDE`, `TOUCHES-B3`, `BLAST-ESCALATION`, `SCRUTINY-MISSING`,
`SCRUTINY-FAILED`, `TESTS-NOT-FIRST`, `CHECKLIST-UNANSWERED`,
`ATTRIBUTION-MISSING`, `ATTRIBUTION-LICENSE`, `MEGAFILE`.

Scrutiny evidence convention (the artifacts ticket 10's reviewers write,
committed on the ticket branch under `<review_dir>/<ticket>/`):
- `spec-verdict.md`, `lens.md`: a line `Verdict: pass|concerns|fail`;
  `fail` fails the check.
- `checklist-<id>.md`: the answer grammar of blast-map-format §7, one line
  per non-retired item; blank lines and `#` lines are ignored.
- Independent acceptance tests: in the ticket's commit order (base..judged,
  oldest first, ignoring commits that touch only the ticket's evidence
  files), the first commit touches test files only (`test_globs`).
  Independence of its author is the dispatcher's guarantee, not provable
  from git.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from checks.blastmap import BlastEvaluation
from checks.diff import FileEntry
from checks.ledger import HANDOFF_ACCEPTED, handoff_status, ref_scanner
from core import Blast, Reference, ReuseMode, Tag, glob_to_regex

_VERDICT = re.compile(r"^Verdict:\s*(?P<verdict>pass|concerns|fail)\b", re.MULTILINE | re.IGNORECASE)
_BREAKING = re.compile(r"BREAKING\((?P<ref>[^()\s]+)\):")
_ALLOW = re.compile(r"allow\((?P<rule>[^()\s]+)\):\s*")
_ITEM = re.compile(r"^- \*\*(?P<id>[A-Z]{2}-\d{2})\*\* ")
_RETIRED = re.compile(r"^- \*\*[A-Z]{2}-\d{2}\*\* Retired\.$")
_ANSWER = re.compile(r"^(?P<id>[A-Z]{2}-\d{2}) (?P<verdict>pass|fail|n/a): (?P<evidence>\S.*)$")
_SOURCE_REV = re.compile(r"(?P<source>[^\s@]+)@(?P<rev>[0-9A-Za-z._-]+)")
_LICENSE = re.compile(r"(?i:license):\s*(?P<license>[A-Za-z0-9.+-]+)")


@dataclass(frozen=True)
class CheckResult:
    name: str
    failures: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    exceptions: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.failures

    def as_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "failures": list(self.failures),
            "warnings": list(self.warnings),
            "exceptions": list(self.exceptions),
        }


@dataclass(frozen=True)
class CommandRun:
    command: str
    exit_code: int | None  # None: timed out
    output: str = ""


@dataclass(frozen=True)
class Commit:
    sha: str
    files: tuple[str, ...]


def compile_globs(globs: Sequence[str]) -> tuple[re.Pattern[str], ...]:
    return tuple(glob_to_regex(g) for g in globs)


def _hit(regexes: Sequence[re.Pattern[str]], path: str) -> bool:
    return any(r.fullmatch(path) for r in regexes)


def allowance(text: str, rule: str, ledger: Mapping[str, str], ref_pattern: str) -> str | None:
    """The active decision an `allow(<rule>): D-NNN` in `text` cites, or
    None. Rules compare case-insensitively; an inactive citation is no
    allowance (the ref check reports it)."""
    scanner = ref_scanner(ref_pattern)
    for match in _ALLOW.finditer(text):
        if match.group("rule").lower() != rule.lower():
            continue
        ref = scanner.match(text, match.end())
        if ref is not None and ledger.get(ref.group(0)) == "active":
            return ref.group(0)
    return None


def count_lines(text: str) -> int:
    return text.count("\n") + (1 if text and not text.endswith("\n") else 0)


# --------------------------------------------------------------------------
# Step 1 and step 3
# --------------------------------------------------------------------------


def handoff_check(text: str | None) -> CheckResult:
    """Step 1: refuse unless the handoff exists with DONE or DONE_WITH_CONCERNS."""
    if text is None:
        return CheckResult("handoff", failures=("HANDOFF-MISSING",))
    status = handoff_status(text)
    if status not in HANDOFF_ACCEPTED:
        return CheckResult("handoff", failures=(f"HANDOFF-STATUS {status or '(no Status line)'}",))
    return CheckResult("handoff")


def verify_check(runs: Sequence[CommandRun], dirty: Sequence[str] = ()) -> CheckResult:
    """Step 3: every verify command exits 0 on the judged tree, and leaves
    its tracked files as committed (`dirty`: `git status --porcelain` lines
    after the run), so what lands is exactly what was verified."""
    failures = [
        f"VERIFY-FAILED {run.command!r} ({'timed out' if run.exit_code is None else f'exit {run.exit_code}'})"
        for run in runs
        if run.exit_code != 0
    ]
    if dirty:
        failures.append(f"VERIFY-DIRTY verify modified tracked files: {'; '.join(line.strip() for line in dirty)}")
    return CheckResult("verify", failures=tuple(failures))


# --------------------------------------------------------------------------
# Step 4 hygiene checks
# --------------------------------------------------------------------------


def ref_check(
    entries: Sequence[FileEntry], ledger: Mapping[str, str], ref_pattern: str, skip_globs: Sequence[str]
) -> CheckResult:
    """Plan §3.3: every ledger ref on an added line resolves to an active
    row. Covers `BREAKING(D-NNN)` and `allow(<rule>): D-NNN` too, so a
    proposed decision cannot merge before the planner activates it."""
    scanner = ref_scanner(ref_pattern)
    skip = compile_globs(skip_globs)
    failures: list[str] = []
    for entry in entries:
        if _hit(skip, entry.path):
            continue
        for lineno, text in entry.added:
            for match in scanner.finditer(text):
                status = ledger.get(match.group(0))
                if status != "active":
                    why = f"status {status}" if status else "no ledger row"
                    failures.append(f"REF-UNRESOLVED {match.group(0)} {entry.path}:{lineno} ({why})")
    return CheckResult("ref", failures=tuple(failures))


def touches_check(
    entries: Sequence[FileEntry],
    touches: Sequence[str],
    exempt_globs: Sequence[str],
    evaluation: BlastEvaluation,
    ref_pattern: str,
) -> CheckResult:
    """Plan §3.5/§3.6: a file outside `Touches` needs a `BREAKING(D-NNN):`
    marker on an added line (licensed breakage, listed as a warning); a file
    outside `Touches` that hits a B3 zone fails even with the marker. Both
    sides of a rename count."""
    inside = compile_globs(touches)
    exempt = compile_globs(exempt_globs)
    ref = re.compile(ref_pattern)
    failures: list[str] = []
    warnings: list[str] = []
    for entry in entries:
        outside = [p for p in entry.paths() if not _hit(inside, p) and not _hit(exempt, p)]
        if not outside:
            continue
        for path in outside:
            if evaluation.path_level(path) is Blast.B3:
                failures.append(f"TOUCHES-B3 {path} (breakage into a B3 zone is never licensed; cut its own B3 ticket)")
        markers = sorted(
            {m.group("ref") for _, text in entry.added for m in _BREAKING.finditer(text) if ref.fullmatch(m.group("ref"))}
        )
        for path in outside:
            if markers:
                warnings.append(f"BREAKING {path} ({', '.join(markers)})")
            else:
                failures.append(f"TOUCHES-OUTSIDE {path} (no BREAKING(<ref>): marker on an added line)")
    return CheckResult("touches", failures=tuple(failures), warnings=tuple(warnings))


def blast_check(evaluation: BlastEvaluation) -> CheckResult:
    """Plan §2b: effective above declared is `BLAST-ESCALATION`, naming
    every hit above the declared level."""
    failures: tuple[str, ...] = ()
    if evaluation.escalation:
        fired = "; ".join(
            f"{h.zone} {h.path} ({h.source}, {h.level.name})"
            for h in evaluation.hits
            if h.level.value > evaluation.declared.value
        )
        failures = (
            f"BLAST-ESCALATION declared {evaluation.declared.name} effective {evaluation.effective.name}: {fired}",
        )
    return CheckResult("blast", failures=failures, warnings=evaluation.inactive_lowerings)


def checklist_items(text: str) -> frozenset[str]:
    """Non-retired item ids of a domain checklist file (format §7)."""
    return frozenset(
        m.group("id") for line in text.splitlines() if (m := _ITEM.match(line)) and not _RETIRED.match(line)
    )


def checklist_problems(answer: str, items: Collection[str]) -> list[str]:
    """Why an answer file does not answer the checklist; empty when it does."""
    seen: dict[str, int] = {}
    problems: list[str] = []
    for line in answer.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        match = _ANSWER.match(line)
        if match is None:
            problems.append(f"malformed line {line!r}")
            continue
        item = match.group("id")
        seen[item] = seen.get(item, 0) + 1
        if item not in items:
            problems.append(f"unknown item {item}")
        if match.group("verdict") == "fail":
            problems.append(f"{item} fail")
    problems += [f"{i} unanswered" for i in sorted(items) if i not in seen]
    problems += [f"{i} answered {n} times" for i, n in sorted(seen.items()) if n > 1]
    return problems


def _verdict(name: str, artifacts: Mapping[str, str]) -> list[str]:
    text = artifacts.get(name)
    match = _VERDICT.search(text) if text is not None else None
    if match is None:
        return [f"SCRUTINY-MISSING {name} (want a 'Verdict: pass|concerns|fail' line)"]
    if match.group("verdict").lower() == "fail":
        return [f"SCRUTINY-FAILED {name} (Verdict: fail)"]
    return []


def scrutiny_check(
    effective: Blast,
    tag: Tag,
    artifacts: Mapping[str, str],
    commits: Sequence[Commit],
    checklists: Collection[str],
    checklist_sources: Mapping[str, str | None],
    test_globs: Sequence[str],
    evidence_globs: Sequence[str],
) -> CheckResult:
    """Plan §2b ladder, "Automated review" and "Tests" rows, at the
    effective level: spec verdict at B2+ and at B1 for `contract`; at B3
    also tests-first commit order, a lens report, and every checklist of
    the evaluation answered (vacuous when the set is empty, format §5)."""
    failures: list[str] = []
    if effective.value >= Blast.B2.value or (effective is Blast.B1 and tag is Tag.CONTRACT):
        failures += _verdict("spec-verdict.md", artifacts)
    if effective is not Blast.B3:
        return CheckResult("scrutiny", failures=tuple(failures))
    failures += _verdict("lens.md", artifacts)
    tests, evidence = compile_globs(test_globs), compile_globs(evidence_globs)
    work = [c for c in commits if not all(_hit(evidence, f) for f in c.files)]
    if not work or not all(_hit(tests, f) for f in work[0].files):
        first = work[0].sha[:12] if work else "(none)"
        failures.append(f"TESTS-NOT-FIRST first commit {first} is not an acceptance-tests-only commit")
    for cid in sorted(checklists):
        source = checklist_sources.get(cid)
        if source is None:
            failures.append(f"SCRUTINY-MISSING checklist source for {cid} (set checklists_dir)")
            continue
        answer = artifacts.get(f"checklist-{cid}.md")
        if answer is None:
            failures.append(f"CHECKLIST-UNANSWERED {cid} (no checklist-{cid}.md)")
            continue
        problems = checklist_problems(answer, checklist_items(source))
        if problems:
            failures.append(f"CHECKLIST-UNANSWERED {cid}: {'; '.join(problems)}")
    return CheckResult("scrutiny", failures=tuple(failures))


def _revs_agree(a: str, b: str) -> bool:
    return a == b or (min(len(a), len(b)) >= 7 and (a.startswith(b) or b.startswith(a)))


def attribution_check(reference: Reference | None, notices: str | None, allowed: Collection[str]) -> CheckResult:
    """A `port`/`fork` reference needs a notices line naming its
    `<source>@<rev>` (revs agree on a common prefix of 7+) and a
    `license: <SPDX-id>` on the same line, with the license on the allowed
    list. `dependency` and `pattern` need nothing here."""
    if reference is None or reference.mode not in (ReuseMode.PORT, ReuseMode.FORK):
        return CheckResult("attribution")
    head = _SOURCE_REV.fullmatch(reference.target.split(":", 1)[0])
    if head is None:
        return CheckResult("attribution", failures=(f"ATTRIBUTION-MISSING target {reference.target!r} has no <source>@<rev>",))
    source, rev = head.group("source"), head.group("rev")
    licenses: list[str] = []
    for line in (notices or "").splitlines():
        named = any(m.group("source") == source and _revs_agree(m.group("rev"), rev) for m in _SOURCE_REV.finditer(line))
        license_match = _LICENSE.search(line)
        if named and license_match is not None:
            licenses.append(license_match.group("license"))
    if not licenses:
        return CheckResult("attribution", failures=(f"ATTRIBUTION-MISSING {source}@{rev} (no notices line with a license)",))
    if not any(lic in allowed for lic in licenses):
        return CheckResult("attribution", failures=(f"ATTRIBUTION-LICENSE {', '.join(licenses)} not in allowed_licenses",))
    return CheckResult("attribution")


def megafile_check(
    entries: Sequence[FileEntry],
    base_lines: Mapping[str, int],
    head_text: Mapping[str, str],
    threshold: int,
    skip_globs: Sequence[str],
    ledger: Mapping[str, str],
    ref_pattern: str,
) -> CheckResult:
    """A changed file that crossed `threshold` lines in this change (before
    <= threshold < after; a new file counts from 0) fails with `MEGAFILE
    <path>`. A file already above the threshold at the base passes: only the
    crossing counts. `allow(megafile): D-NNN` anywhere in the file, citing
    an active row, waives it."""
    skip = compile_globs(skip_globs)
    failures: list[str] = []
    exceptions: list[str] = []
    for entry in entries:
        if entry.status == "D" or entry.binary or entry.path not in head_text or _hit(skip, entry.path):
            continue
        before_path = entry.old_path if entry.status == "R" and entry.old_path else entry.path
        before, after = base_lines.get(before_path, 0), count_lines(head_text[entry.path])
        if not before <= threshold < after:
            continue
        waiver = allowance(head_text[entry.path], "megafile", ledger, ref_pattern)
        if waiver is not None:
            exceptions.append(f"allow(megafile): {waiver} {entry.path}")
        else:
            failures.append(f"MEGAFILE {entry.path} ({before} -> {after} lines, threshold {threshold})")
    return CheckResult("megafile", failures=tuple(failures), exceptions=tuple(exceptions))


# --------------------------------------------------------------------------
# Outcome
# --------------------------------------------------------------------------


def decide(results: Sequence[CheckResult], evaluation: BlastEvaluation) -> str:
    """Escalation re-routes (work salvaged) whatever else failed; any other
    red is a failed attempt; green B3 waits for the operator; green B0-B2
    lands."""
    if evaluation.escalation:
        return "BLAST-ESCALATION"
    if any(not r.ok for r in results):
        return "FAILED"
    if evaluation.effective is Blast.B3:
        return "AWAITING-OPERATOR"
    return "MERGED"


def conflict_partners(events: Sequence[Mapping[str, Any]], paths: Collection[str], ticket: str) -> tuple[str, ...]:
    """The tickets that last landed each conflicted path, folded from the
    integrate events (`outcome == "MERGED"`, `files`)."""
    last: dict[str, str] = {}
    for event in events:
        if event.get("event") != "integrate" or event.get("outcome") != "MERGED":
            continue
        other = event.get("ticket")
        files = event.get("files")
        if not isinstance(other, str) or other == ticket or not isinstance(files, list):
            continue
        for path in files:
            if path in paths:
                last[path] = other
    return tuple(sorted(set(last.values())))

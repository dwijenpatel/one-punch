"""Style lint severities (plan §3.11 Layer 2): hard-fail vs soft-cap, the
brownfield ratchet, and `allow(<rule>): D-NNN` exceptions.

The shell runs every `lint_hard` and `lint_soft` command twice in the
throwaway worktree — on the base (the integration head) and on the judged
tree — and hands both outputs here. Output lines are parsed with the
configured `lint_pattern` (named groups `path`, and optionally `line`,
`code`, `message`; default: ruff's concise format
`path:line:col: CODE message`). A command exiting outside `lint_ok_exit`
is `LINT-ERROR` (a failure for a hard command, a warning for a soft one).

Ratchet: only files the change adds, modifies, renames or copies count, and
within them a violation is new when the judged tree has more violations with
the same (path, code, message) than the base had (a renamed file is compared
with its old path). When a key has more occurrences than are new, the ones on
added lines are reported first. New hard violations fail (`LINT <code>
<path>:<line>`) unless the violation's line or the line above carries
`allow(<code>): D-NNN` citing an active ledger row; new soft violations are
warnings (`LINT-WARN ...`) for the integration log.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass

from checks.diff import FileEntry
from checks.hygiene import CheckResult, allowance


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    code: str
    message: str


@dataclass(frozen=True)
class LintRun:
    command: str
    hard: bool
    base_exit: int | None  # None: timed out
    base_output: str
    head_exit: int | None
    head_output: str


def parse_lint_output(text: str, pattern: str, root: str) -> tuple[Violation, ...]:
    """Lint output -> violations with repo-relative paths (`root` is the
    worktree the command ran in; absolute paths under it are relativized)."""
    regex = re.compile(pattern)
    groups = regex.groupindex
    prefix = root.rstrip("/") + "/"
    out: list[Violation] = []
    for raw in text.splitlines():
        match = regex.match(raw)
        if match is None:
            continue
        path = match.group("path").strip()
        path = path[len(prefix) :] if path.startswith(prefix) else path
        while path.startswith("./"):
            path = path[2:]
        line = int(match.group("line")) if "line" in groups and match.group("line") else 0
        code = match.group("code") if "code" in groups and match.group("code") else "lint"
        message = match.group("message").strip() if "message" in groups and match.group("message") else ""
        out.append(Violation(path=path, line=line, code=code, message=message))
    return tuple(out)


def ratchet(base: Sequence[Violation], head: Sequence[Violation], entries: Sequence[FileEntry]) -> tuple[Violation, ...]:
    """The judged tree's violations that are new relative to the base, in
    changed files only (module docstring)."""
    changed = {e.path for e in entries if e.status != "D"}
    renamed = {e.old_path: e.path for e in entries if e.status == "R" and e.old_path is not None}
    added = {e.path: {n for n, _ in e.added} for e in entries}
    base_counts = Counter((renamed.get(v.path, v.path), v.code, v.message) for v in base)
    by_key: defaultdict[tuple[str, str, str], list[Violation]] = defaultdict(list)
    for v in head:
        if v.path in changed:
            by_key[(v.path, v.code, v.message)].append(v)
    new: list[Violation] = []
    for key, found in by_key.items():
        excess = len(found) - base_counts.get(key, 0)
        if excess > 0:
            found.sort(key=lambda v: (v.line not in added.get(v.path, ()), v.line))
            new.extend(found[:excess])
    return tuple(sorted(new, key=lambda v: (v.path, v.line, v.code, v.message)))


def _waiver(v: Violation, head_text: Mapping[str, str], ledger: Mapping[str, str], ref_pattern: str) -> str | None:
    lines = head_text.get(v.path, "").splitlines()
    for index in (v.line - 1, v.line - 2):
        if 0 <= index < len(lines):
            ref = allowance(lines[index], v.code, ledger, ref_pattern)
            if ref is not None:
                return ref
    return None


def lint_check(
    runs: Sequence[LintRun],
    entries: Sequence[FileEntry],
    head_text: Mapping[str, str],
    ledger: Mapping[str, str],
    *,
    pattern: str,
    ok_exit: Collection[int],
    root: str,
    ref_pattern: str,
) -> CheckResult:
    failures: list[str] = []
    warnings: list[str] = []
    exceptions: list[str] = []
    for run in runs:
        bad = [code for code in (run.base_exit, run.head_exit) if code not in ok_exit]
        if bad:
            message = f"LINT-ERROR {run.command!r} (exit {', '.join('timeout' if c is None else str(c) for c in bad)})"
            (failures if run.hard else warnings).append(message)
            continue
        base = parse_lint_output(run.base_output, pattern, root)
        head = parse_lint_output(run.head_output, pattern, root)
        for v in ratchet(base, head, entries):
            where = f"{v.code} {v.path}:{v.line} {v.message}".rstrip()
            if not run.hard:
                warnings.append(f"LINT-WARN {where}")
                continue
            ref = _waiver(v, head_text, ledger, ref_pattern)
            if ref is not None:
                exceptions.append(f"allow({v.code}): {ref} {v.path}:{v.line}")
            else:
                failures.append(f"LINT {where}")
    return CheckResult("lint", failures=tuple(failures), warnings=tuple(warnings), exceptions=tuple(exceptions))

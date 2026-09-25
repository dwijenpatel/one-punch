"""Decision ledger, ledger references, handoff status, and the integrate
config (`harness.toml` `[integrate]`).

Ledger (plan §3.3): `docs/decisions.md` holds one markdown table, one row
per decision: `ID · decision · rationale · owner · status · ADR link`. Any
table whose header has an `ID` column and a `Status` column is read; a row
whose ID cell (bold/backticks stripped) fullmatches the ref pattern is a
decision, and its status is the status cell's first word, lowercased
(`active`, `superseded`, `inferred`, ...). Only `active` resolves a
reference. A repeated ID is `LEDGER-INVALID`.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from core import DEFAULT_REF_PATTERN, glob_to_regex

HANDOFF_ACCEPTED = frozenset({"DONE", "DONE_WITH_CONCERNS"})
_CELL_SPLIT = re.compile(r"(?<!\\)\|")
_HANDOFF_STATUS = re.compile(r"^Status:\s*(?P<status>\S+)")


class LedgerError(ValueError):
    """`LEDGER-INVALID: <reason>`."""


class ConfigError(ValueError):
    """`CONFIG-INVALID: <reason>`."""


def _cells(row: str) -> list[str]:
    inner = row.strip()
    inner = inner[1:] if inner.startswith("|") else inner
    inner = inner[:-1] if inner.endswith("|") and not inner.endswith("\\|") else inner
    return [c.strip() for c in _CELL_SPLIT.split(inner)]


def parse_ledger(text: str | None, ref_pattern: str = DEFAULT_REF_PATTERN) -> dict[str, str]:
    """Ledger text (None when the file is absent: an empty ledger) ->
    {decision id: status}."""
    if text is None:
        return {}
    ref = re.compile(ref_pattern)
    rows: dict[str, str] = {}
    id_col: int | None = None
    status_col: int | None = None
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            id_col = status_col = None
            continue
        cells = _cells(line)
        lowered = [c.lower() for c in cells]
        if "id" in lowered and "status" in lowered:
            id_col, status_col = lowered.index("id"), lowered.index("status")
            continue
        if id_col is None or status_col is None or max(id_col, status_col) >= len(cells):
            continue
        decision = cells[id_col].strip("*` ")
        if not ref.fullmatch(decision):
            continue
        if decision in rows:
            raise LedgerError(f"LEDGER-INVALID: duplicate decision {decision}")
        words = cells[status_col].strip("*` ").split()
        rows[decision] = words[0].strip(".,;:()").lower() if words else ""
    return rows


def active_decisions(ledger: Mapping[str, str]) -> frozenset[str]:
    return frozenset(d for d, status in ledger.items() if status == "active")


def ref_scanner(ref_pattern: str = DEFAULT_REF_PATTERN) -> re.Pattern[str]:
    """The configured ref pattern is anchored (it fullmatches an ID); the
    scanner strips `^`/`$` and requires a non-word character (or the line
    edge) on both sides, so `D-0123` is one ref and `PROD-001` is none."""
    body = ref_pattern
    body = body[1:] if body.startswith("^") else body
    body = body[:-1] if body.endswith("$") and not body.endswith("\\$") else body
    return re.compile(rf"(?<!\w)(?:{body})(?!\w)")


def handoff_status(text: str | None) -> str | None:
    """The first `Status:` line's value, or None when absent."""
    if text is None:
        return None
    for line in text.splitlines():
        match = _HANDOFF_STATUS.match(line)
        if match is not None:
            return match.group("status")
    return None


# --------------------------------------------------------------------------
# harness.toml [integrate]
# --------------------------------------------------------------------------

DEFAULT_TEST_GLOBS = (
    "**/test_*.py",
    "**/*_test.py",
    "**/tests/**",
    "**/test/**",
    "**/__tests__/**",
    "**/*.test.*",
    "**/*.spec.*",
    "**/*_test.go",
)
DEFAULT_MEGAFILE_SKIP = (
    "**/*.lock",
    "**/package-lock.json",
    "**/pnpm-lock.yaml",
    "**/go.sum",
)
# ruff `--output-format=concise` (also flake8/pylint-parseable-like):
# `path:line[:col]: CODE message`.
DEFAULT_LINT_PATTERN = r"^(?P<path>[^:\n]+):(?P<line>\d+):(?:\d+:)?\s+(?P<code>[A-Z]+[0-9]+)\s+(?P<message>.*)$"


@dataclass(frozen=True)
class IntegrateConfig:
    """The `[integrate]` table of `harness.toml`. Every key is documented in
    `integrate.py`'s module docstring; `{effort}` and `{ticket}` expand."""

    effort: str
    verify: tuple[str, ...]
    integration_branch: str = "integrate/{effort}"
    ticket_branch: str = "t/{ticket}"
    issues_dir: str = ".scratch/{effort}/issues"
    handoffs_dir: str = ".scratch/{effort}/handoffs"
    review_dir: str = ".scratch/{effort}/reviews"
    packets_dir: str = ".scratch/{effort}/review-packets"
    events_file: str = ".scratch/{effort}/events.jsonl"
    ledger_file: str = "docs/decisions.md"
    blast_map_file: str = "docs/blast-map.md"
    ref_pattern: str = DEFAULT_REF_PATTERN
    ref_skip: tuple[str, ...] = ()
    test_globs: tuple[str, ...] = DEFAULT_TEST_GLOBS
    verify_timeout_s: int = 1800
    lint_hard: tuple[str, ...] = ()
    lint_soft: tuple[str, ...] = ()
    lint_pattern: str = DEFAULT_LINT_PATTERN
    lint_ok_exit: tuple[int, ...] = (0, 1)
    megafile_threshold: int = 800
    megafile_skip: tuple[str, ...] = DEFAULT_MEGAFILE_SKIP
    notices_file: str = "THIRD_PARTY_NOTICES.md"
    allowed_licenses: tuple[str, ...] = ()
    checklists_dir: str = ""
    max_reentries: int = 3

    def expand(self, template: str, ticket: str = "") -> str:
        return template.format(effort=self.effort, ticket=ticket)

    def handoff_path(self, ticket: str) -> str:
        return f"{self.expand(self.handoffs_dir)}/{ticket}.md"

    def review_path(self, ticket: str) -> str:
        return f"{self.expand(self.review_dir)}/{ticket}"

    def evidence_globs(self, ticket: str) -> tuple[str, ...]:
        """The ticket's own handoff and review artifacts: exempt from
        Touches, ignored by the tests-first commit order."""
        return (self.handoff_path(ticket), f"{self.review_path(ticket)}/**")

    def ref_skip_globs(self) -> tuple[str, ...]:
        """Files the ref check never scans: the ledger itself, handoffs,
        reviews and tickets (they propose and discuss decisions), tests
        (plan §8: refs in tests are encouraged, not checked), `ref_skip`."""
        return (
            self.ledger_file,
            f"{self.expand(self.handoffs_dir)}/**",
            f"{self.expand(self.review_dir)}/**",
            f"{self.expand(self.issues_dir)}/**",
            *self.test_globs,
            *self.ref_skip,
        )


_STR_KEYS = frozenset(
    {
        "integration_branch", "ticket_branch", "issues_dir", "handoffs_dir", "review_dir", "packets_dir",
        "events_file", "ledger_file", "blast_map_file", "ref_pattern", "lint_pattern", "notices_file",
        "checklists_dir",
    }
)
_STR_LIST_KEYS = frozenset(
    {"verify", "ref_skip", "test_globs", "lint_hard", "lint_soft", "megafile_skip", "allowed_licenses"}
)
_GLOB_LIST_KEYS = frozenset({"ref_skip", "test_globs", "megafile_skip"})
_INT_KEYS = frozenset({"verify_timeout_s", "megafile_threshold", "max_reentries"})


def parse_config(data: Mapping[str, Any]) -> IntegrateConfig:
    """`tomllib.loads(harness.toml)` -> config. Unknown keys in `[integrate]`
    are errors (a typo must not silently disable a check)."""

    def fail(reason: str) -> ConfigError:
        return ConfigError(f"CONFIG-INVALID: {reason}")

    table = data.get("integrate")
    if not isinstance(table, dict):
        raise fail("harness.toml has no [integrate] table")
    known = _STR_KEYS | _STR_LIST_KEYS | _INT_KEYS | {"effort", "lint_ok_exit"}
    unknown = sorted(set(table) - known)
    if unknown:
        raise fail(f"unknown [integrate] key(s) {unknown}")
    effort = table.get("effort")
    if not isinstance(effort, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", effort):
        raise fail("[integrate].effort must be a name ([A-Za-z0-9_.-])")
    values: dict[str, Any] = {"effort": effort}
    for key, value in table.items():
        if key in _STR_KEYS:
            if not isinstance(value, str):
                raise fail(f"{key} must be a string")
            values[key] = value
        elif key in _STR_LIST_KEYS:
            if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
                raise fail(f"{key} must be an array of non-empty strings")
            values[key] = tuple(value)
        elif key in _INT_KEYS:
            if type(value) is not int or value < 0:
                raise fail(f"{key} must be a non-negative integer")
            values[key] = value
        elif key == "lint_ok_exit":
            if not isinstance(value, list) or not all(type(v) is int for v in value):
                raise fail("lint_ok_exit must be an array of integers")
            values[key] = tuple(value)
    config = IntegrateConfig(**values)
    if not config.verify:
        raise fail("verify must name at least one command (completion is granted by artifacts)")
    for key in _GLOB_LIST_KEYS:
        for glob in getattr(config, key):
            try:
                glob_to_regex(glob)
            except ValueError:
                raise fail(f"{key}: bad glob {glob!r}") from None
    for key in ("ref_pattern", "lint_pattern"):
        try:
            re.compile(getattr(config, key))
        except re.error as exc:
            raise fail(f"{key} does not compile ({exc})") from None
    groups = re.compile(config.lint_pattern).groupindex
    if "path" not in groups:
        raise fail("lint_pattern needs a (?P<path>...) group")
    for template in (config.integration_branch, config.ticket_branch, config.handoffs_dir):
        try:
            config.expand(template, "x")
        except (KeyError, IndexError, ValueError):
            raise fail(f"bad placeholder in {template!r} (use {{effort}} / {{ticket}})") from None
    return config


def matches_any(globs: Sequence[str], path: str) -> bool:
    return any(glob_to_regex(g).fullmatch(path) for g in globs)

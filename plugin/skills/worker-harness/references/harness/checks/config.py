"""The integrate config: the `[integrate]` table of `harness.toml`."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from core import DEFAULT_REF_PATTERN, glob_to_regex


class ConfigError(ValueError):
    """`CONFIG-INVALID: <reason>`."""


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
    """The `[integrate]` table of `harness.toml`. Unknown keys are
    CONFIG-INVALID; `{effort}` and `{ticket}` expand; paths are
    repo-relative. Keys and defaults:

    effort              required; the effort name
    verify              required, non-empty; shell commands run in the judged
                        worktree, each must exit 0
    verify_timeout_s    1800; per command, also for lint commands
    integration_branch  "integrate/{effort}"
    ticket_branch       "t/{ticket}"
    issues_dir          ".scratch/{effort}/issues"; ticket file `<ticket>-*.md`
                        (or `<ticket>.md`), read from H
    handoffs_dir        ".scratch/{effort}/handoffs"; handoff `<ticket>.md`,
                        read from the ticket branch
    review_dir          ".scratch/{effort}/reviews"; scrutiny evidence under
                        `<review_dir>/<ticket>/` in J: spec-verdict.md,
                        lens.md, checklist-<id>.md
    packets_dir         ".scratch/{effort}/review-packets" (on disk, uncommitted)
    events_file         ".scratch/{effort}/events.jsonl" (on disk; the
                        integration log)
    ledger_file         "docs/decisions.md", read from H
    blast_map_file      "docs/blast-map.md", read from H
    ref_pattern         '^D-\\d{3,}$'; anchored ledger-ID pattern (also the
                        lowering decision pattern)
    ref_skip            []; extra globs the ref check skips (it always skips
                        the ledger, handoffs, reviews, tickets and test_globs)
    test_globs          test_*.py, *_test.py, tests/, test/, __tests__/,
                        *.test.*, *.spec.*, *_test.go (any depth)
    lint_hard           []; commands whose new violations fail
    lint_soft           []; commands whose new violations are warnings
    lint_pattern        ruff concise: `path:line[:col]: CODE message`
                        (named groups path, line, code, message)
    lint_ok_exit        [0, 1]; lint exit codes that mean "ran"
    megafile_threshold  800
    megafile_skip       lockfiles (**/*.lock, package-lock.json, pnpm-lock.yaml,
                        go.sum)
    notices_file        "THIRD_PARTY_NOTICES.md"; attribution lines
                        `- <source>@<rev> license: <SPDX-id> ...`, read from J
    allowed_licenses    []; SPDX ids a port/fork may carry (empty: none)
    checklists_dir      ""; where checklist-<id>.md live (repo-relative: read
                        from H; absolute: from disk); empty: the blast-radius
                        skill's references next to this harness, if present
    max_reentries       3
    """

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

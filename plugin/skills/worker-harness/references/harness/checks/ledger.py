"""Decision ledger, ledger references, and handoff status.

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
from collections.abc import Mapping

from core import DEFAULT_REF_PATTERN

HANDOFF_ACCEPTED = frozenset({"DONE", "DONE_WITH_CONCERNS"})
_CELL_SPLIT = re.compile(r"(?<!\\)\|")
_HANDOFF_STATUS = re.compile(r"^Status:\s*(?P<status>\S+)")


class LedgerError(ValueError):
    """`LEDGER-INVALID: <reason>`."""


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

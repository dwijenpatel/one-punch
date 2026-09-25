"""Blast map: extraction (format §1), validation (§3), the detector (§5).

Normative source: the blast-radius skill, references/blast-map-format.md,
schema 1. The glob dialect, `Blast` and the default ledger ref pattern come
from `core.py`; the scheduling projection (`core.blast_map_from_data`) stays
there. This module builds the full validated model the detector needs —
patterns, lowerings, checklists, protection — and fails closed with the
format's tokens: `BLAST-MAP-INVALID: <reason>` (as `BlastMapError`) and
`LOWERING-INACTIVE <decision>` (reported, never raised).
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from checks.diff import FileEntry
from core import DEFAULT_REF_PATTERN, Blast, glob_to_regex

CHECKLIST_IDS = frozenset(
    {
        "auth-sessions",
        "authz-tenancy",
        "secrets-crypto",
        "transactions-concurrency",
        "migrations-destructive",
        "money",
        "untrusted-input",
    }
)
_ZONE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_TOP_KEYS = frozenset({"schema", "pack", "pattern_skip", "zone", "lowering"})
_ZONE_KEYS = frozenset({"name", "level", "why", "paths", "pattern", "checklist", "protected"})
_PATTERN_KEYS = frozenset({"regex", "files", "match", "nomatch"})
_LOWERING_KEYS = frozenset({"zone", "paths", "level", "decision"})


class BlastMapError(ValueError):
    """`BLAST-MAP-MISSING` or `BLAST-MAP-INVALID: <reason>`."""


# Copied verbatim from the blast-radius skill, references/blast-map-format.md
# §1 ("Reference extraction"), schema 1, only type-annotated. Do not edit here
# without editing the format document.
FENCE_OPEN = re.compile(r"^```toml blast-map[ \t]*$")
FENCE_CLOSE = re.compile(r"^```[ \t]*$")


def extract_blast_map(markdown: str) -> dict[str, Any]:
    lines = markdown.splitlines()
    opens = [i for i, line in enumerate(lines) if FENCE_OPEN.match(line)]
    if len(opens) != 1:
        raise ValueError(f"BLAST-MAP-INVALID: expected 1 blast-map block, found {len(opens)}")
    start = opens[0] + 1
    for end in range(start, len(lines)):
        if FENCE_CLOSE.match(lines[end]):
            return tomllib.loads("\n".join(lines[start:end]))
    raise ValueError("BLAST-MAP-INVALID: blast-map block is not closed")


@dataclass(frozen=True)
class Pattern:
    regex: re.Pattern[str]
    files: tuple[re.Pattern[str], ...]


@dataclass(frozen=True)
class MapZone:
    name: str
    level: Blast
    why: str
    paths: tuple[re.Pattern[str], ...]
    patterns: tuple[Pattern, ...]
    checklist: str | None
    protected: bool


@dataclass(frozen=True)
class Lowering:
    zone: str
    paths: tuple[re.Pattern[str], ...]
    level: Blast
    decision: str


@dataclass(frozen=True)
class ValidBlastMap:
    zones: tuple[MapZone, ...]
    lowerings: tuple[Lowering, ...]
    pattern_skip: tuple[re.Pattern[str], ...]


@dataclass(frozen=True)
class Hit:
    zone: str
    path: str
    source: str  # "path" | "pattern"
    level: Blast


@dataclass(frozen=True)
class BlastEvaluation:
    declared: Blast
    hits: tuple[Hit, ...]
    map_level: Blast
    effective: Blast
    checklists: frozenset[str]
    inactive_lowerings: tuple[str, ...]

    @property
    def escalation(self) -> bool:
        return self.effective.value > self.declared.value

    def path_level(self, path: str) -> Blast:
        """Highest hit level recorded against `path` (B0 when none)."""
        return max((h.level for h in self.hits if h.path == path), key=lambda b: b.value, default=Blast.B0)


def _invalid(reason: str) -> BlastMapError:
    return BlastMapError(f"BLAST-MAP-INVALID: {reason}")


def _table(value: object, where: str, allowed: frozenset[str]) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise _invalid(f"{where} must be a table")
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise _invalid(f"{where}: unknown key(s) {unknown}")
    return value


def _str(value: object, where: str) -> str:
    if not isinstance(value, str):
        raise _invalid(f"{where} must be a string")
    return value


def _strs(value: object, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise _invalid(f"{where} must be an array of strings")
    return tuple(str(v) for v in value)


def _globs(value: object, where: str) -> tuple[re.Pattern[str], ...]:
    out: list[re.Pattern[str]] = []
    for glob in _strs(value, where):
        try:
            out.append(glob_to_regex(glob))
        except ValueError:
            raise _invalid(f"{where}: bad glob {glob!r}") from None
    return tuple(out)


def _level(value: object, where: str) -> Blast:
    if not isinstance(value, str) or value not in Blast.__members__:
        raise _invalid(f"{where} must be one of B0, B1, B2, B3")
    return Blast[value]


def _pattern(raw: object, where: str) -> Pattern:
    table = _table(raw, where, _PATTERN_KEYS)
    source = _str(table.get("regex"), f"{where}.regex")
    try:
        regex = re.compile(source)
    except re.error as exc:
        raise _invalid(f"{where}: regex {source!r} does not compile ({exc})") from None
    for example in _strs(table.get("match", []), f"{where}.match"):
        if not regex.search(example):
            raise _invalid(f"{where}: regex {source!r} does not find match example {example!r}")
    for example in _strs(table.get("nomatch", []), f"{where}.nomatch"):
        if regex.search(example):
            raise _invalid(f"{where}: regex {source!r} finds nomatch example {example!r}")
    return Pattern(regex=regex, files=_globs(table.get("files", ["**"]), f"{where}.files"))


def _zone(raw: object, index: int) -> MapZone:
    table = _table(raw, f"zone[{index}]", _ZONE_KEYS)
    name = _str(table.get("name"), f"zone[{index}].name")
    if not _ZONE_NAME.match(name):
        raise _invalid(f"zone name {name!r} is not lowercase-hyphenated")
    where = f"zone {name!r}"
    why = _str(table.get("why"), f"{where}.why")
    if not why.strip() or "\n" in why:
        raise _invalid(f"{where}.why must be one non-empty line")
    raw_patterns = table.get("pattern", [])
    if not isinstance(raw_patterns, list):
        raise _invalid(f"{where}.pattern must be an array of tables")
    checklist = table.get("checklist")
    if checklist is not None and checklist not in CHECKLIST_IDS:
        raise _invalid(f"{where}: unknown checklist {checklist!r}")
    protected = table.get("protected", False)
    if not isinstance(protected, bool):
        raise _invalid(f"{where}.protected must be a boolean")
    zone = MapZone(
        name=name,
        level=_level(table.get("level"), f"{where}.level"),
        why=why,
        paths=_globs(table.get("paths", []), f"{where}.paths"),
        patterns=tuple(_pattern(p, f"{where}.pattern[{i}]") for i, p in enumerate(raw_patterns)),
        checklist=str(checklist) if checklist is not None else None,
        protected=protected,
    )
    if not zone.paths and not zone.patterns:
        raise _invalid(f"{where} has neither paths nor patterns")
    return zone


def validate_blast_map(data: Mapping[str, Any], ref_pattern: str = DEFAULT_REF_PATTERN) -> ValidBlastMap:
    """Format §3, all six rules. Raises `BlastMapError` on the first failure."""
    top = _table(dict(data), "the map", _TOP_KEYS)
    schema = top.get("schema")
    if type(schema) is not int or schema != 1:
        raise _invalid(f"schema must be the integer 1, got {schema!r}")
    if "pack" in top:
        _str(top["pack"], "pack")
    raw_zones = top.get("zone")
    if not isinstance(raw_zones, list) or not raw_zones:
        raise _invalid("`zone` must be a non-empty array of tables")
    zones = tuple(_zone(z, i) for i, z in enumerate(raw_zones))
    by_name: dict[str, MapZone] = {}
    for zone in zones:
        if zone.name in by_name:
            raise _invalid(f"duplicate zone name {zone.name!r}")
        by_name[zone.name] = zone
    raw_lowerings = top.get("lowering", [])
    if not isinstance(raw_lowerings, list):
        raise _invalid("`lowering` must be an array of tables")
    ref = re.compile(ref_pattern)
    lowerings: list[Lowering] = []
    for i, raw in enumerate(raw_lowerings):
        where = f"lowering[{i}]"
        table = _table(raw, where, _LOWERING_KEYS)
        zone_name = _str(table.get("zone"), f"{where}.zone")
        target = by_name.get(zone_name)
        if target is None:
            raise _invalid(f"{where} names unknown zone {zone_name!r}")
        if target.protected:
            raise _invalid(f"{where} names protected zone {zone_name!r}")
        paths = _globs(table.get("paths"), f"{where}.paths")
        if not paths:
            raise _invalid(f"{where}.paths must name at least one glob")
        level = _level(table.get("level"), f"{where}.level")
        if level.value >= target.level.value:
            raise _invalid(f"{where} level {level.name} is not below zone {zone_name!r} level {target.level.name}")
        decision = _str(table.get("decision"), f"{where}.decision")
        if not ref.fullmatch(decision):
            raise _invalid(f"{where} decision {decision!r} does not match {ref_pattern!r}")
        lowerings.append(Lowering(zone=zone_name, paths=paths, level=level, decision=decision))
    return ValidBlastMap(
        zones=zones,
        lowerings=tuple(lowerings),
        pattern_skip=_globs(top.get("pattern_skip", []), "pattern_skip"),
    )


def load_blast_map(markdown: str | None, ref_pattern: str = DEFAULT_REF_PATTERN) -> ValidBlastMap:
    """`docs/blast-map.md` text (None when the file is absent) -> validated
    map. Fails closed: `BLAST-MAP-MISSING` or `BLAST-MAP-INVALID: <reason>`."""
    if markdown is None:
        raise BlastMapError("BLAST-MAP-MISSING")
    try:
        data = extract_blast_map(markdown)
    except tomllib.TOMLDecodeError as exc:
        raise _invalid(f"TOML syntax error ({exc})") from None
    except ValueError as exc:
        raise BlastMapError(str(exc)) from None
    return validate_blast_map(data, ref_pattern)


def _any_match(regexes: Sequence[re.Pattern[str]], path: str) -> bool:
    return any(r.fullmatch(path) for r in regexes)


def evaluate(
    bmap: ValidBlastMap, entries: Sequence[FileEntry], declared: Blast, active: Collection[str]
) -> BlastEvaluation:
    """Format §5: hits over both sides of renames and over added and removed
    lines; lowerings apply only with an active decision (max of the
    applicable ones); effective = max(declared, map level)."""
    raw_hits: set[tuple[str, str, str]] = set()
    for zone in bmap.zones:
        for entry in entries:
            for path in entry.paths():
                if _any_match(zone.paths, path):
                    raw_hits.add((zone.name, path, "path"))
            if _any_match(bmap.pattern_skip, entry.path):
                continue
            for pattern in zone.patterns:
                if _any_match(pattern.files, entry.path) and any(pattern.regex.search(line) for line in entry.lines):
                    raw_hits.add((zone.name, entry.path, "pattern"))

    levels = {z.name: z.level for z in bmap.zones}
    inactive: set[str] = set()
    hits: list[Hit] = []
    for zone_name, path, source in sorted(raw_hits):
        applicable: list[Blast] = []
        for lowering in bmap.lowerings:
            if lowering.zone != zone_name or not _any_match(lowering.paths, path):
                continue
            if lowering.decision in active:
                applicable.append(lowering.level)
            else:
                inactive.add(lowering.decision)
        level = max(applicable, key=lambda b: b.value) if applicable else levels[zone_name]
        hits.append(Hit(zone=zone_name, path=path, source=source, level=level))

    map_level = max((h.level for h in hits), key=lambda b: b.value, default=Blast.B0)
    effective = map_level if map_level.value > declared.value else declared
    checklist_of = {z.name: z.checklist for z in bmap.zones}
    checklists = frozenset(
        cid for h in hits if h.level.value >= Blast.B2.value and (cid := checklist_of[h.zone]) is not None
    )
    return BlastEvaluation(
        declared=declared,
        hits=tuple(hits),
        map_level=map_level,
        effective=effective,
        checklists=checklists,
        inactive_lowerings=tuple(f"LOWERING-INACTIVE {d}" for d in sorted(inactive)),
    )

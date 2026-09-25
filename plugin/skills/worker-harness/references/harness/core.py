"""Pure routing and scheduling core for the one-punch worker harness.

Functional core / imperative shell: nothing in this module performs I/O, reads
a clock, lists a directory, or draws randomness. Time (`now`), randomness
(`rand`), the ledger (event values), the tier ladder, ticket text, the parsed
blast map and the repository tree listing all arrive as arguments. Every
decision is a deterministic function of its inputs, so every invariant is a
plain unit test (see test_core.py) and resumability is a fold over the event
log.

Normative sources:
- one-punch pipeline.md v3 §8: tag x size -> tier floors, epsilon-greedy
  within a tier, governor cooldowns, one-tier escalation.
- v4 plan (docs/design/2026-09-24-v4-steer-then-swarm-plan.md) §2b: blast
  levels and the scrutiny ladder's "Implementer floor" row; §3.2: ticket
  header fields and the v3 tag split; §3.4: batch selection.
- blast-radius skill, references/blast-map-format.md: the glob dialect (§4,
  copied below verbatim) and zone membership for scheduling (§6).

Tier mapping of the blast floors (§2b "Implementer floor" row). Floors are
ranks on the operator-owned ladder, not vendor names. In the ratified v3
ladder T0 carries Opus, T1 and T2 carry Sonnet (at max and medium effort),
T3 GPT-Luna, T4 Haiku, T5 mini and local models. So:

    B0  per tag x size (Haiku allowed)  -> T5, i.e. no blast constraint
    B1  Sonnet tier                     -> T2, the weakest rung carrying Sonnet
    B2  Sonnet; Opus for `contract`     -> T2; T0 when the tag is `contract`
    B3  Opus                            -> T0

The routing floor is the stronger of the tag x size floor and the blast floor
(on `Tier.value`, stronger means smaller, so "max floor" is `min` on value).
"""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Collection, Mapping, Sequence, Union

EPSILON = 0.12
RECENCY_DECAY = 0.85  # weight ratio between consecutive samples, newest first
UNSEEN_PRIOR = 0.5    # score for a candidate with no ledger history
MAX_ESCALATIONS = 1   # one tier up per pipeline v3; beyond that -> park
DEFAULT_REF_PATTERN = r"^D-\d{3,}$"  # plan §3.3; configurable per repo
READY_STATUSES = frozenset({"ready", "ready-for-agent"})


class Tag(Enum):
    """Determinacy tag. v4 keeps `code-complete` and `contract`; `critical`
    and `trivial` are v3 values, accepted in ticket text only to be migrated
    (plan §3.2) and kept here so v3 tables stay total."""

    CRITICAL = "critical"
    CONTRACT = "contract"
    CODE_COMPLETE = "code-complete"
    TRIVIAL = "trivial"


V4_TAGS = frozenset({Tag.CONTRACT, Tag.CODE_COMPLETE})


class Size(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very-high"


_SIZE_RANK: Mapping[Size, int] = {Size.LOW: 0, Size.MEDIUM: 1, Size.HIGH: 2, Size.VERY_HIGH: 3}


class Tier(Enum):
    """Quality ladder; smaller value = stronger tier."""

    T0 = 0
    T1 = 1
    T2 = 2
    T3 = 3
    T4 = 4
    T5 = 5


class Blast(Enum):
    """Blast radius (plan §2b); larger value = more severe."""

    B0 = 0
    B1 = 1
    B2 = 2
    B3 = 3


class ReuseMode(Enum):
    DEPENDENCY = "dependency"
    FORK = "fork"
    PORT = "port"
    PATTERN = "pattern"


@dataclass(frozen=True)
class Reference:
    """`Reference: <target> (<mode>)` or `(<mode> — <note>)`. The target is
    kept opaque (`repo@sha:path` by convention)."""

    target: str
    mode: ReuseMode
    note: str = ""


@dataclass(frozen=True)
class Candidate:
    tool: str
    model: str
    effort: str


@dataclass(frozen=True)
class Ticket:
    id: str
    title: str
    tag: Tag
    size: Size
    blocked_by: tuple[str, ...]
    status: str  # ready | ready-for-agent | done | parked | ...
    attempts: int  # failed attempts so far
    # v4 fields. The defaults describe an in-memory v3 ticket; the header
    # parser always sets them, and select_batch refuses an empty `touches`.
    blast: Blast = Blast.B0
    touches: tuple[str, ...] = ()
    blast_reason: str = ""
    decides: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    reference: Reference | None = None
    migrated_from: Tag | None = None  # the v3 tag the header carried, if any


@dataclass(frozen=True)
class Outcome:
    ts: float
    ticket_id: str
    candidate: Candidate
    ok: bool
    cost: float
    turns: int


@dataclass(frozen=True)
class LimitHit:
    ts: float
    candidate: Candidate
    retry_at: float


Event = Union[Outcome, LimitHit]


@dataclass(frozen=True)
class CandidateStats:
    samples: int
    score: float  # recency-weighted success rate in [0, 1]


@dataclass(frozen=True)
class GovernorState:
    cooling: Mapping[Candidate, float] = field(default_factory=dict)

    def cooling_until(self, candidate: Candidate) -> float:
        return self.cooling.get(candidate, 0.0)

    def is_cooling(self, candidate: Candidate, now: float) -> bool:
        return self.cooling_until(candidate) > now


@dataclass(frozen=True)
class Routed:
    candidate: Candidate
    tier: Tier
    explored: bool
    escalated: bool


@dataclass(frozen=True)
class Parked:
    reason: str


RouteDecision = Union[Routed, Parked]


@dataclass(frozen=True)
class Zone:
    """The scheduling view of one `[[zone]]`: identity, level, path globs.
    Patterns and lowerings play no part in scheduling (format §6)."""

    name: str
    level: Blast
    paths: tuple[str, ...]


@dataclass(frozen=True)
class BlastMap:
    zones: tuple[Zone, ...]


# --------------------------------------------------------------------------
# Floors
# --------------------------------------------------------------------------

_FLOORS: Mapping[tuple[Tag, Size], Tier] = {
    **{(Tag.CRITICAL, s): Tier.T0 for s in Size},
    (Tag.CONTRACT, Size.HIGH): Tier.T1,
    (Tag.CONTRACT, Size.VERY_HIGH): Tier.T1,
    (Tag.CONTRACT, Size.LOW): Tier.T2,
    (Tag.CONTRACT, Size.MEDIUM): Tier.T2,
    (Tag.CODE_COMPLETE, Size.HIGH): Tier.T3,
    (Tag.CODE_COMPLETE, Size.VERY_HIGH): Tier.T3,
    (Tag.CODE_COMPLETE, Size.LOW): Tier.T4,
    (Tag.CODE_COMPLETE, Size.MEDIUM): Tier.T4,
    **{(Tag.TRIVIAL, s): Tier.T5 for s in Size},
}


def default_floor(tag: Tag, size: Size) -> Tier:
    """The v3 tag x size floor (pipeline v3 §8)."""
    return _FLOORS[(tag, size)]


def blast_floor(blast: Blast, tag: Tag) -> Tier:
    """The blast floor; tier mapping in the module docstring."""
    if blast is Blast.B3:
        return Tier.T0
    if blast is Blast.B2:
        return Tier.T0 if tag is Tag.CONTRACT else Tier.T2
    if blast is Blast.B1:
        return Tier.T2
    return Tier.T5


def tier_floor(tag: Tag, size: Size, blast: Blast) -> Tier:
    """Routing floor = the stronger of the tag x size floor and the blast floor."""
    return Tier(min(default_floor(tag, size).value, blast_floor(blast, tag).value))


def migrate_v3_tag(tag: Tag, size: Size, blast: Blast | None) -> tuple[Tag, Size, Blast]:
    """Plan §3.2 v3 tag split: `critical` -> B3, `trivial` -> B0 + Size low.

    Risk moves to `Blast`, so the determinacy tag must become a v4 tag:
    `critical` -> `contract` (the stricter determinacy, whose spec-verdict
    review B3 requires anyway), `trivial` -> `code-complete`. A declared
    `Blast` is never lowered by migration: the result is the max of the
    declared and the implied level. v4 tags need a declared `Blast`.
    """
    if tag is Tag.CRITICAL:
        return Tag.CONTRACT, size, Blast.B3
    if tag is Tag.TRIVIAL:
        return Tag.CODE_COMPLETE, Size.LOW, blast if blast is not None else Blast.B0
    if blast is None:
        raise ValueError(f"tag {tag.value!r} needs a declared Blast level")
    return tag, size, blast


# --------------------------------------------------------------------------
# Ledger fold, frontier, routing (pipeline v3 §8)
# --------------------------------------------------------------------------


def fold(events: Sequence[Event]) -> tuple[Mapping[Candidate, CandidateStats], GovernorState]:
    """Current state is always a fold over the append-only event log."""
    outcomes: dict[Candidate, list[Outcome]] = {}
    cooling: dict[Candidate, float] = {}
    for event in events:
        if isinstance(event, Outcome):
            outcomes.setdefault(event.candidate, []).append(event)
        else:
            cooling[event.candidate] = max(cooling.get(event.candidate, 0.0), event.retry_at)
    stats: dict[Candidate, CandidateStats] = {}
    for candidate, history in outcomes.items():
        ordered = sorted(history, key=lambda o: o.ts, reverse=True)  # newest first
        weights = [RECENCY_DECAY**i for i in range(len(ordered))]
        score = sum(w * (1.0 if o.ok else 0.0) for w, o in zip(weights, ordered)) / sum(weights)
        stats[candidate] = CandidateStats(samples=len(ordered), score=score)
    return stats, GovernorState(cooling=cooling)


def frontier(tickets: Sequence[Ticket]) -> tuple[Ticket, ...]:
    """Ready tickets whose blockers are all done, in id order."""
    done = {t.id for t in tickets if t.status == "done"}
    ready = [
        t
        for t in tickets
        if t.status in READY_STATUSES and all(b in done for b in t.blocked_by)
    ]
    return tuple(sorted(ready, key=lambda t: t.id))


def _available(
    ladder: Mapping[Tier, tuple[Candidate, ...]],
    tier: Tier,
    governor: GovernorState,
    now: float,
) -> tuple[Candidate, ...]:
    return tuple(c for c in ladder.get(tier, ()) if not governor.is_cooling(c, now))


def route(
    ticket: Ticket,
    ladder: Mapping[Tier, tuple[Candidate, ...]],
    stats: Mapping[Candidate, CandidateStats],
    governor: GovernorState,
    now: float,
    rand: float,
) -> RouteDecision:
    """One routing decision. Floors are hard: fallback climbs toward T0, never
    descends. Escalation (from prior failed attempts) is one tier, then park.
    `critical` and B3 (its v4 successor) never explore."""
    if ticket.attempts > MAX_ESCALATIONS:
        return Parked(
            f"ticket {ticket.id}: {ticket.attempts} failed attempts (escalation exhausted) — parked for operator"
        )
    floor = tier_floor(ticket.tag, ticket.size, ticket.blast)
    target = Tier(max(floor.value - ticket.attempts, 0))
    for value in range(target.value, -1, -1):  # target, then upward to T0
        tier = Tier(value)
        available = _available(ladder, tier, governor, now)
        if not available:
            continue
        may_explore = (
            ticket.tag is not Tag.CRITICAL
            and ticket.blast is not Blast.B3
            and ticket.size in (Size.LOW, Size.MEDIUM)
            and len(available) > 1
        )
        if may_explore and rand < EPSILON:
            chosen = min(available, key=lambda c: (stats[c].samples if c in stats else 0, available.index(c)))
            return Routed(chosen, tier, explored=True, escalated=ticket.attempts > 0)
        chosen = max(
            available,
            key=lambda c: (
                stats[c].score if c in stats else UNSEEN_PRIOR,
                -available.index(c),
            ),
        )
        return Routed(chosen, tier, explored=False, escalated=ticket.attempts > 0)
    return Parked(
        f"ticket {ticket.id}: no candidate available at or above {floor.name} (all cooling) — parked; take other frontier work"
    )


# --------------------------------------------------------------------------
# Ticket header (plan §3.2)
# --------------------------------------------------------------------------

_HEADER_LINE = re.compile(r"^(?P<key>[A-Z][A-Za-z]*(?:[- ][A-Za-z]+)*): (?P<value>.*)$")
_ANNOTATION = re.compile(r"\s+\([^()]*\)")  # " (note)" after whitespace; `app/(auth)/x` survives
_NONE_VALUES = frozenset({"", "—", "–", "-", "none"})
_TICKET_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_BLAST_VALUE = re.compile(r"^(?P<level>B[0-3])(?:\s+[—–-]\s*(?P<reason>\S.*))?$")
_REFERENCE_VALUE = re.compile(
    r"^(?P<target>\S+)\s+\((?P<mode>dependency|fork|port|pattern)(?:\s+[—–-]\s*(?P<note>[^()]*\S))?\)$"
)
_KNOWN_KEYS = frozenset(
    {"Status", "Blocked by", "Tag", "Blast", "Size", "Touches", "Decides", "Depends-on", "Reference"}
)


class TicketHeaderError(ValueError):
    pass


def _list_value(value: str) -> list[str]:
    stripped = _ANNOTATION.sub("", value).strip()
    if stripped in _NONE_VALUES:
        return []
    return [item.strip() for item in stripped.split(",")]


def parse_ticket_header(text: str, ticket_id: str, ref_pattern: str = DEFAULT_REF_PATTERN) -> Ticket:
    """Parse a v4 (or v3) ticket's header block into a Ticket.

    The header is the run of `Key: value` lines after the `# ` title line,
    ending at the first blank line or `##` heading. Unknown keys (`Type:`,
    `Authority:`, ...) are ignored; a repeated known key is an error. A
    whitespace-preceded `(note)` is an annotation and is stripped from list
    values, so globs cannot contain whitespace. v3 tags are migrated
    (`migrate_v3_tag`); every Touches glob is validated against the blast-map
    glob dialect. `attempts` starts at 0 — the shell folds it from the ledger.
    """

    def fail(reason: str) -> TicketHeaderError:
        return TicketHeaderError(f"TICKET-INVALID {ticket_id}: {reason}")

    title = ""
    fields: dict[str, str] = {}
    started = False
    for line in text.splitlines():
        if not started and line.startswith("# "):
            title = line[2:].strip()
            continue
        if line.startswith("##") or (started and not line.strip()):
            break
        if not line.strip():
            continue
        match = _HEADER_LINE.match(line)
        if match is None:
            if started:
                break
            continue
        started = True
        key, value = match.group("key"), match.group("value").strip()
        if key in _KNOWN_KEYS:
            if key in fields:
                raise fail(f"duplicate header {key!r}")
            fields[key] = value

    for required in ("Status", "Tag", "Size", "Touches"):
        if required not in fields:
            raise fail(f"missing header {required!r}")

    status_words = _ANNOTATION.sub("", fields["Status"]).split()
    if not status_words:
        raise fail("empty Status")
    status = status_words[0]

    try:
        tag = Tag(fields["Tag"])
    except ValueError:
        raise fail(f"unknown Tag {fields['Tag']!r}") from None
    try:
        size = Size(fields["Size"])
    except ValueError:
        raise fail(f"unknown Size {fields['Size']!r}") from None

    declared: Blast | None = None
    reason = ""
    if "Blast" in fields:
        blast_match = _BLAST_VALUE.match(fields["Blast"])
        if blast_match is None:
            raise fail(f"malformed Blast {fields['Blast']!r} (want 'B0'..'B3' [— reason])")
        declared = Blast[blast_match.group("level")]
        reason = blast_match.group("reason") or ""
    try:
        new_tag, new_size, blast = migrate_v3_tag(tag, size, declared)
    except ValueError as exc:
        raise fail(str(exc)) from None
    migrated_from = tag if tag not in V4_TAGS else None
    if migrated_from is not None and not reason:
        reason = f"migrated from v3 Tag: {tag.value}"

    blocked_by = _list_value(fields.get("Blocked by", ""))
    for blocker in blocked_by:
        if not _TICKET_ID.match(blocker):
            raise fail(f"malformed blocker id {blocker!r}")

    touches = _list_value(fields["Touches"])
    if not touches:
        raise fail("empty Touches")
    for glob in touches:
        if not glob or any(c.isspace() for c in glob):
            raise fail(f"malformed Touches item {glob!r}")
        try:
            glob_to_regex(glob)
        except ValueError:
            raise fail(f"bad Touches glob {glob!r}") from None

    ref = re.compile(ref_pattern)
    decides = _list_value(fields.get("Decides", ""))
    depends_on = _list_value(fields.get("Depends-on", ""))
    for key, ids in (("Decides", decides), ("Depends-on", depends_on)):
        for ledger_id in ids:
            if not ref.fullmatch(ledger_id):
                raise fail(f"{key} id {ledger_id!r} does not match {ref_pattern!r}")

    reference: Reference | None = None
    if "Reference" in fields:
        ref_match = _REFERENCE_VALUE.match(fields["Reference"])
        if ref_match is None:
            raise fail(f"malformed Reference {fields['Reference']!r} (want '<target> (<mode>[ — note])')")
        reference = Reference(
            target=ref_match.group("target"),
            mode=ReuseMode(ref_match.group("mode")),
            note=ref_match.group("note") or "",
        )

    return Ticket(
        id=ticket_id,
        title=title,
        tag=new_tag,
        size=new_size,
        blocked_by=tuple(blocked_by),
        status=status,
        attempts=0,
        blast=blast,
        touches=tuple(touches),
        blast_reason=reason,
        decides=tuple(decides),
        depends_on=tuple(depends_on),
        reference=reference,
        migrated_from=migrated_from,
    )


# --------------------------------------------------------------------------
# Glob dialect
# --------------------------------------------------------------------------

# Copied verbatim from the blast-radius skill, references/blast-map-format.md
# §4 ("Normative translation to a Python regex"), schema 1, only type-annotated
# (`out: list[str]`). One dialect for blast-map paths and ticket Touches; do
# not edit here without editing the format document. Its test vectors run in
# test_core.py.
def glob_to_regex(glob: str) -> re.Pattern[str]:
    segments = glob.split("/")
    if glob.startswith("./") or any(s == "" for s in segments):
        raise ValueError(f"BLAST-MAP-INVALID: bad glob {glob!r}")
    out: list[str] = []
    for i, seg in enumerate(segments):
        last = i == len(segments) - 1
        if seg == "**":
            out.append(".+" if last else "(?:[^/]+/)*")
            continue
        if "**" in seg:
            raise ValueError(f"BLAST-MAP-INVALID: bad glob {glob!r}")
        body = "".join("[^/]*" if c == "*" else "[^/]" if c == "?" else re.escape(c) for c in seg)
        out.append(body if last else body + "/")
    return re.compile("".join(out))


def _segment_witness(p: str, q: str) -> str | None:
    """A non-empty string that both single-segment patterns (`*`, `?`,
    literals; no `/`) match, or None. Product-automaton search."""
    start = (0, 0)
    parent: dict[tuple[int, int], tuple[tuple[int, int], str] | None] = {start: None}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        i, j = state
        if i == len(p) and j == len(q):
            chars: list[str] = []
            cursor: tuple[int, int] | None = state
            while cursor is not None:
                step = parent[cursor]
                if step is None:
                    break
                chars.append(step[1])
                cursor = step[0]
            witness = "".join(reversed(chars))
            # Only `*` vs `*` can accept the empty string; segments are non-empty.
            return witness if witness else "x"
        moves: list[tuple[tuple[int, int], str]] = []
        if i < len(p) and p[i] == "*":
            moves.append(((i + 1, j), ""))
        if j < len(q) and q[j] == "*":
            moves.append(((i, j + 1), ""))
        if i < len(p) and j < len(q):
            a, b = p[i], q[j]
            ni = i if a == "*" else i + 1
            nj = j if b == "*" else j + 1
            a_any, b_any = a in "*?", b in "*?"
            if a_any and b_any:
                moves.append(((ni, nj), "x"))
            elif a_any:
                moves.append(((ni, nj), b))
            elif b_any or a == b:
                moves.append(((ni, nj), a))
        for nxt, char in moves:
            if nxt not in parent:
                parent[nxt] = (state, char)
                queue.append(nxt)
    return None


_ZSTAR = None  # token: zero or more whole segments


def _glob_tokens(glob: str) -> tuple[str | None, ...]:
    """Segment tokens: a segment pattern, or _ZSTAR. A last `**` (one or
    more segments) becomes `*` followed by _ZSTAR."""
    glob_to_regex(glob)  # validate
    segments = glob.split("/")
    tokens: list[str | None] = []
    for i, seg in enumerate(segments):
        if seg == "**":
            if i == len(segments) - 1:
                tokens.extend(["*", _ZSTAR])
            else:
                tokens.append(_ZSTAR)
        else:
            tokens.append(seg)
    return tuple(tokens)


def glob_intersection(g: str, h: str) -> str | None:
    """A path both globs match (a witness), or None when no path can match
    both. Exact for the §4 dialect: a product search over segment tokens,
    with segment pairs intersected by `_segment_witness`."""
    gt, ht = _glob_tokens(g), _glob_tokens(h)
    start = (0, 0)
    parent: dict[tuple[int, int], tuple[tuple[int, int], str | None] | None] = {start: None}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        i, j = state
        if i == len(gt) and j == len(ht):
            segs: list[str] = []
            cursor: tuple[int, int] | None = state
            while cursor is not None:
                step = parent[cursor]
                if step is None:
                    break
                if step[1] is not None:
                    segs.append(step[1])
                cursor = step[0]
            return "/".join(reversed(segs))
        moves: list[tuple[tuple[int, int], str | None]] = []
        if i < len(gt) and gt[i] is _ZSTAR:
            moves.append(((i + 1, j), None))
        if j < len(ht) and ht[j] is _ZSTAR:
            moves.append(((i, j + 1), None))
        if i < len(gt) and j < len(ht):
            a, b = gt[i], ht[j]
            ni = i if a is _ZSTAR else i + 1
            nj = j if b is _ZSTAR else j + 1
            segment = _segment_witness(a if a is not None else "*", b if b is not None else "*")
            if segment is not None:
                moves.append(((ni, nj), segment))
        for nxt, seg in moves:
            if nxt not in parent:
                parent[nxt] = (state, seg)
                queue.append(nxt)
    return None


def literal_prefix(glob: str) -> str:
    """The glob's leading wildcard-free segments; the whole glob when it has
    no wildcard; "" (the root) when its first segment has one."""
    lit: list[str] = []
    for seg in glob.split("/"):
        if "*" in seg or "?" in seg:
            break
        lit.append(seg)
    return "/".join(lit)


# --------------------------------------------------------------------------
# Overlap and batch selection (plan §3.4; blast-map format §6)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class _Tree:
    paths: tuple[str, ...]
    prefixes: frozenset[str]  # every existing file and directory path; "" when non-empty


def _index_tree(tree: Collection[str]) -> _Tree:
    prefixes: set[str] = set()
    for path in tree:
        segments = path.split("/")
        if path.startswith("./") or any(s == "" for s in segments):
            raise ValueError(f"bad tree path {path!r} (repo-relative, '/'-separated, no empty segments)")
        prefixes.add("")
        for k in range(1, len(segments) + 1):
            prefixes.add("/".join(segments[:k]))
    return _Tree(paths=tuple(sorted(set(tree))), prefixes=frozenset(prefixes))


@dataclass(frozen=True)
class _Footprint:
    globs: tuple[str, ...]
    files: frozenset[str]  # existing files the globs match


def _footprint(globs: Sequence[str], tree: _Tree) -> _Footprint:
    regexes = [glob_to_regex(g) for g in globs]
    files = frozenset(p for p in tree.paths if any(r.fullmatch(p) for r in regexes))
    return _Footprint(globs=tuple(globs), files=files)


def _globs_overlap(g: str, h: str, tree: _Tree) -> bool:
    if glob_intersection(g, h) is None:
        return False
    lg, lh = literal_prefix(g), literal_prefix(h)
    shallower, deeper = (lg, lh) if len(lg) <= len(lh) else (lh, lg)
    # Under-approximated only when a root wildcard meets an existing non-root prefix.
    return shallower != "" or deeper == "" or deeper not in tree.prefixes


def _footprints_overlap(a: _Footprint, b: _Footprint, tree: _Tree) -> bool:
    if a.files & b.files:
        return True
    return any(_globs_overlap(g, h, tree) for g in a.globs for h in b.globs)


def touches_overlap(a: Sequence[str], b: Sequence[str], tree: Collection[str]) -> bool:
    """Whether two glob sets may touch the same file (plan §3.4).

    Two sets overlap when some pair of globs g in `a`, h in `b` can name the
    same path (`glob_intersection`) and at least one holds:
      1. an existing file in `tree` matches both;
      2. the deeper of their literal prefixes does not exist in `tree` (as a
         file or directory) — "the same not-yet-existing path prefix";
      3. both literal prefixes are non-root, or both are the root: the globs
         share an anchor (conservative: `src/api/*.py` and
         `src/api/*_test.py` may both create `src/api/x_test.py`; two
         `**/*.md` tickets may both create `README.md`).
    Deliberate under-approximation, the one remaining case: a root-anchored
    wildcard glob (`**/AGENTS.md`) meets a glob whose non-root literal prefix
    exists only through existing files — otherwise every ticket would sit in
    every `**/`-zone (format §8 pins `src/api/**` outside `**/AGENTS.md`).
    The integrate step's Touches and B3-zone checks backstop the gap on the
    actual diff.
    """
    index = _index_tree(tree)
    return _footprints_overlap(_footprint(a, index), _footprint(b, index), index)


def ticket_zones(touches: Sequence[str], blast_map: BlastMap, tree: Collection[str]) -> frozenset[str]:
    """Names of the scheduling zones a Touches set is in (format §6): zones
    with at least one path glob that overlaps it. Pattern-only zones never
    count; lowerings play no part."""
    index = _index_tree(tree)
    mine = _footprint(touches, index)
    return frozenset(
        z.name for z in blast_map.zones if z.paths and _footprints_overlap(mine, _footprint(z.paths, index), index)
    )


def blast_map_from_data(data: Mapping[str, object]) -> BlastMap:
    """Project a parsed blast map (the `tomllib.loads` result of the fenced
    block) onto what scheduling reads: each zone's name, level and paths.

    This is not the format's §3 validation — the caller runs that first and
    fails closed on BLAST-MAP-MISSING / BLAST-MAP-INVALID. It raises
    ValueError only when the fields it reads are malformed.
    """
    raw_zones = data.get("zone")
    if not isinstance(raw_zones, list) or not raw_zones:
        raise ValueError("BLAST-MAP-INVALID: `zone` must be a non-empty array of tables")
    zones: list[Zone] = []
    for raw in raw_zones:
        if not isinstance(raw, dict):
            raise ValueError("BLAST-MAP-INVALID: every zone must be a table")
        name, level, paths = raw.get("name"), raw.get("level"), raw.get("paths", [])
        if not isinstance(name, str) or not isinstance(level, str) or level not in Blast.__members__:
            raise ValueError(f"BLAST-MAP-INVALID: zone {name!r} needs a string name and a level B0..B3")
        if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
            raise ValueError(f"BLAST-MAP-INVALID: zone {name!r} paths must be an array of globs")
        globs = tuple(str(p) for p in paths)
        for glob in globs:
            glob_to_regex(glob)
        zones.append(Zone(name=name, level=Blast[level], paths=globs))
    names = [z.name for z in zones]
    if len(set(names)) != len(names):
        raise ValueError("BLAST-MAP-INVALID: zone names must be unique")
    return BlastMap(zones=tuple(zones))


def critical_path(tickets: Sequence[Ticket]) -> dict[str, int]:
    """For every not-done ticket: the length of the longest chain of not-done
    tickets that starts at it and follows `Blocked by` edges to dependents
    (a ticket nothing waits on has length 1). Raises on a dependency cycle."""
    live = {t.id: t for t in tickets if t.status != "done"}
    dependents: dict[str, list[str]] = {tid: [] for tid in live}
    for t in live.values():
        for blocker in t.blocked_by:
            if blocker in live:
                dependents[blocker].append(t.id)
    lengths: dict[str, int] = {}
    for root in sorted(live):
        if root in lengths:
            continue
        # Iterative post-order DFS; `on_path` detects cycles.
        stack: list[tuple[str, int]] = [(root, 0)]
        on_path = {root}
        while stack:
            node, child_index = stack[-1]
            children = dependents[node]
            if child_index < len(children):
                stack[-1] = (node, child_index + 1)
                child = children[child_index]
                if child in on_path:
                    raise ValueError(f"dependency cycle through tickets {node!r} and {child!r}")
                if child not in lengths:
                    stack.append((child, 0))
                    on_path.add(child)
                continue
            lengths[node] = 1 + max((lengths[c] for c in children), default=0)
            on_path.discard(node)
            stack.pop()
    return lengths


def select_batch(
    frontier: Sequence[Ticket],
    n: int,
    blast_map: BlastMap,
    tree: Collection[str],
    *,
    critical_path: Mapping[str, int] | None = None,
) -> tuple[Ticket, ...]:
    """Up to `n` frontier tickets to launch together (plan §3.4).

    Greedy in priority order — longer critical path first, then larger Size,
    then ticket id — a ticket joins when it is compatible with every ticket
    already chosen: `Touches` do not overlap (`touches_overlap`), and when
    either ticket is B3, the two share no scheduling zone (`ticket_zones`).
    The result is maximal: every frontier ticket left out conflicts with a
    chosen one, or the batch is full. B3 means the ticket's declared (and
    migrated) Blast; the diff detector at integrate catches under-declaration.

    `critical_path` comes from `critical_path(all tickets)`; it must cover
    every frontier ticket. Without it every ticket counts as length 1 and
    Size decides.
    """
    if n < 0:
        raise ValueError(f"batch size must be >= 0, got {n}")
    ids = [t.id for t in frontier]
    if len(set(ids)) != len(ids):
        raise ValueError("frontier has duplicate ticket ids")
    for t in frontier:
        if not t.touches:
            raise ValueError(f"SCHEDULE-INVALID {t.id}: empty Touches (a ticket must promise its footprint)")
    if critical_path is not None:
        missing = [tid for tid in ids if tid not in critical_path]
        if missing:
            raise ValueError(f"critical_path lacks frontier tickets {missing}")
    lengths: Mapping[str, int] = critical_path if critical_path is not None else {}

    index = _index_tree(tree)
    zone_prints = [(z.name, _footprint(z.paths, index)) for z in blast_map.zones if z.paths]
    prints = {t.id: _footprint(t.touches, index) for t in frontier}
    zones_of = {
        tid: frozenset(name for name, zp in zone_prints if _footprints_overlap(fp, zp, index))
        for tid, fp in prints.items()
    }

    def compatible(a: Ticket, b: Ticket) -> bool:
        if _footprints_overlap(prints[a.id], prints[b.id], index):
            return False
        if Blast.B3 in (a.blast, b.blast) and zones_of[a.id] & zones_of[b.id]:
            return False
        return True

    ordered = sorted(frontier, key=lambda t: (-lengths.get(t.id, 1), -_SIZE_RANK[t.size], t.id))
    chosen: list[Ticket] = []
    for ticket in ordered:
        if len(chosen) >= n:
            break
        if all(compatible(ticket, c) for c in chosen):
            chosen.append(ticket)
    return tuple(chosen)

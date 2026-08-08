"""Pure routing core for the one-punch worker harness.

Functional core / imperative shell: nothing in this module performs I/O, reads
a clock, or draws randomness — time (`now`), randomness (`rand`), the ledger
(event values), and the tier ladder all arrive as arguments. Every decision is
a deterministic function of its inputs, so every invariant is a plain unit
test (see test_core.py) and resumability is a fold over the event log.

Normative source: one-punch pipeline.md v3 §8 (tag x size -> tier floors,
epsilon-greedy within tier, governor cooldowns, one-tier escalation).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence, Union

EPSILON = 0.12
RECENCY_DECAY = 0.85  # weight ratio between consecutive samples, newest first
UNSEEN_PRIOR = 0.5    # score for a candidate with no ledger history
MAX_ESCALATIONS = 1   # one tier up per pipeline v3; beyond that -> park


class Tag(Enum):
    CRITICAL = "critical"
    CONTRACT = "contract"
    CODE_COMPLETE = "code-complete"
    TRIVIAL = "trivial"


class Size(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very-high"


class Tier(Enum):
    """Quality ladder; smaller value = stronger tier."""

    T0 = 0
    T1 = 1
    T2 = 2
    T3 = 3
    T4 = 4
    T5 = 5


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
    status: str  # ready | done | parked | ...
    attempts: int  # failed attempts so far


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
    return _FLOORS[(tag, size)]


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
        if t.status == "ready" and all(b in done for b in t.blocked_by)
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
    descends. Escalation (from prior failed attempts) is one tier, then park."""
    if ticket.attempts > MAX_ESCALATIONS:
        return Parked(
            f"ticket {ticket.id}: {ticket.attempts} failed attempts (escalation exhausted) — parked for operator"
        )
    floor = default_floor(ticket.tag, ticket.size)
    target = Tier(max(floor.value - ticket.attempts, 0))
    for value in range(target.value, -1, -1):  # target, then upward to T0
        tier = Tier(value)
        available = _available(ladder, tier, governor, now)
        if not available:
            continue
        may_explore = (
            ticket.tag is not Tag.CRITICAL
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

"""Property-style tests for the pure routing core. No mocks anywhere —
everything the core needs (time, randomness, ledger) is passed in as values.
Run: uv run --with pytest pytest -q test_core.py
"""

from __future__ import annotations

import itertools

from core import (
    Candidate,
    CandidateStats,
    Event,
    GovernorState,
    LimitHit,
    Outcome,
    Parked,
    RouteDecision,
    Routed,
    Size,
    Tag,
    Ticket,
    Tier,
    default_floor,
    fold,
    frontier,
    route,
)

LADDER: dict[Tier, tuple[Candidate, ...]] = {
    Tier.T0: (Candidate("claude_p", "opus", "high"), Candidate("codex_p", "gpt-sol", "high")),
    Tier.T1: (
        Candidate("claude_p", "sonnet", "max"),
        Candidate("grok", "grok-4.5", "max"),
        Candidate("codex_p", "gpt-terra", "max"),
    ),
    Tier.T2: (
        Candidate("claude_p", "sonnet", "medium"),
        Candidate("grok", "grok-4.5", "medium"),
        Candidate("codex_p", "gpt-terra", "medium"),
    ),
    Tier.T3: (Candidate("codex_p", "gpt-luna", "max"),),
    Tier.T4: (Candidate("claude_p", "haiku", "high"),),
    Tier.T5: (Candidate("mini", "qwen3.6", "high"),),
}


def tk(tag: Tag, size: Size, attempts: int = 0) -> Ticket:
    return Ticket(
        id="07",
        title="x",
        tag=tag,
        size=size,
        blocked_by=(),
        status="ready",
        attempts=attempts,
    )


def all_tag_sizes() -> list[tuple[Tag, Size]]:
    return list(itertools.product(Tag, Size))


def test_floor_table_is_total() -> None:
    for tag, size in all_tag_sizes():
        assert default_floor(tag, size) in Tier


def test_floors_match_the_ratified_mapping() -> None:
    assert default_floor(Tag.CRITICAL, Size.LOW) is Tier.T0
    assert default_floor(Tag.CRITICAL, Size.VERY_HIGH) is Tier.T0
    assert default_floor(Tag.CONTRACT, Size.HIGH) is Tier.T1
    assert default_floor(Tag.CONTRACT, Size.VERY_HIGH) is Tier.T1
    assert default_floor(Tag.CONTRACT, Size.LOW) is Tier.T2
    assert default_floor(Tag.CONTRACT, Size.MEDIUM) is Tier.T2
    assert default_floor(Tag.CODE_COMPLETE, Size.HIGH) is Tier.T3
    assert default_floor(Tag.CODE_COMPLETE, Size.LOW) is Tier.T4
    assert default_floor(Tag.TRIVIAL, Size.MEDIUM) is Tier.T5


def test_floor_is_never_violated_for_any_rand() -> None:
    gov = GovernorState()
    for tag, size in all_tag_sizes():
        floor = default_floor(tag, size)
        for rand in (0.0, 0.05, 0.5, 0.99):
            d = route(tk(tag, size), LADDER, {}, gov, now=0.0, rand=rand)
            assert isinstance(d, Routed)
            assert d.tier.value <= floor.value, (tag, size, rand, d)


def test_critical_never_explores() -> None:
    stats: dict[Candidate, CandidateStats] = {}
    for rand in (0.0, 0.001, 0.5, 0.999):
        d = route(tk(Tag.CRITICAL, Size.LOW), LADDER, stats, GovernorState(), 0.0, rand)
        assert isinstance(d, Routed) and d.explored is False


def test_exploration_only_on_low_and_medium_sizes() -> None:
    for size in (Size.HIGH, Size.VERY_HIGH):
        d = route(tk(Tag.CONTRACT, size), LADDER, {}, GovernorState(), 0.0, rand=0.0)
        assert isinstance(d, Routed) and d.explored is False
    d = route(tk(Tag.CONTRACT, Size.LOW), LADDER, {}, GovernorState(), 0.0, rand=0.0)
    assert isinstance(d, Routed) and d.explored is True  # rand < epsilon


def test_cooling_provider_is_skipped_and_full_floor_cooling_parks() -> None:
    t = tk(Tag.CONTRACT, Size.HIGH)  # floor T1
    until = 100.0
    gov = fold(
        [LimitHit(ts=0.0, candidate=c, retry_at=until) for c in LADDER[Tier.T1]]
        + [LimitHit(ts=0.0, candidate=c, retry_at=until) for c in LADDER[Tier.T0]]
    )[1]
    d = route(t, LADDER, {}, gov, now=50.0, rand=0.9)
    assert isinstance(d, Parked)
    d2 = route(t, LADDER, {}, gov, now=until + 1, rand=0.9)
    assert isinstance(d2, Routed)


def test_fallback_goes_up_never_down() -> None:
    t = tk(Tag.CONTRACT, Size.HIGH)  # floor T1
    gov = fold([LimitHit(ts=0.0, candidate=c, retry_at=99.0) for c in LADDER[Tier.T1]])[1]
    d = route(t, LADDER, {}, gov, now=1.0, rand=0.9)
    assert isinstance(d, Routed) and d.tier is Tier.T0


def test_escalation_is_one_tier_up_and_two_failures_park() -> None:
    d1 = route(tk(Tag.CODE_COMPLETE, Size.LOW, attempts=1), LADDER, {}, GovernorState(), 0.0, 0.9)
    assert isinstance(d1, Routed) and d1.tier is Tier.T3  # floor T4, one failure -> T3
    d2 = route(tk(Tag.CODE_COMPLETE, Size.LOW, attempts=2), LADDER, {}, GovernorState(), 0.0, 0.9)
    assert isinstance(d2, Parked) and "operator" in d2.reason


def test_exploit_picks_best_recency_weighted_and_explore_picks_least_sampled() -> None:
    # Exploit at T1 (contract/high floors there; T1 never explores — its only
    # traffic is high/very-high sizes, a structural consequence of the mapping).
    a1, b1, _ = LADDER[Tier.T1]
    events: list[Outcome] = [
        Outcome(ts=float(i), ticket_id=str(i), candidate=a1, ok=True, cost=1.0, turns=10) for i in range(4)
    ]
    events += [Outcome(ts=4.0, ticket_id="x", candidate=b1, ok=False, cost=1.0, turns=10)]
    stats, gov = fold(events)
    exploit = route(tk(Tag.CONTRACT, Size.HIGH), LADDER, stats, gov, 5.0, rand=0.9)
    assert isinstance(exploit, Routed) and exploit.candidate == a1

    # Explore at T2 (contract/low floors there): least-sampled wins under rand < epsilon.
    a2, b2, c2 = LADDER[Tier.T2]
    events2 = [Outcome(ts=float(i), ticket_id=str(i), candidate=a2, ok=True, cost=1.0, turns=10) for i in range(3)]
    events2 += [Outcome(ts=3.0, ticket_id="y", candidate=b2, ok=True, cost=1.0, turns=10)]
    stats2, gov2 = fold(events2)
    explore = route(tk(Tag.CONTRACT, Size.LOW), LADDER, stats2, gov2, 5.0, rand=0.0)
    assert isinstance(explore, Routed) and explore.explored is True and explore.candidate == c2


def test_fold_is_deterministic_and_pure() -> None:
    a = LADDER[Tier.T1][0]
    events: list[Event] = [
        Outcome(ts=1.0, ticket_id="1", candidate=a, ok=True, cost=2.0, turns=5),
        LimitHit(ts=2.0, candidate=a, retry_at=9.0),
    ]
    s1, g1 = fold(events)
    s2, g2 = fold(list(events))
    assert s1 == s2 and g1 == g2
    assert g1.cooling_until(a) == 9.0


def test_frontier_respects_blockers_and_status() -> None:
    t1 = Ticket("01", "a", Tag.TRIVIAL, Size.LOW, (), "done", 0)
    t2 = Ticket("02", "b", Tag.CONTRACT, Size.LOW, ("01",), "ready", 0)
    t3 = Ticket("03", "c", Tag.CONTRACT, Size.LOW, ("02",), "ready", 0)
    t4 = Ticket("04", "d", Tag.CONTRACT, Size.LOW, (), "parked", 0)
    assert [t.id for t in frontier((t1, t2, t3, t4))] == ["02"]

"""Property-style tests for the pure routing and scheduling core. No mocks
anywhere — everything the core needs (time, randomness, ledger, ticket text,
blast map, tree listing) is passed in as values. Property tests draw from
hand-rolled generators over a seeded `random.Random` (the glob and tree
generators live in test_core_globs.py, beside the glob and overlap tests).
Run: python -m unittest -v   (or: uv run --with pytest pytest -q test_core.py)
"""

from __future__ import annotations

import itertools
import random
import tomllib
import unittest

from core import (
    Blast,
    BlastMap,
    Candidate,
    CandidateStats,
    Event,
    GovernorState,
    LimitHit,
    Outcome,
    Parked,
    Reference,
    ReuseMode,
    Routed,
    Size,
    Tag,
    Ticket,
    TicketHeaderError,
    Tier,
    V4_TAGS,
    Zone,
    blast_floor,
    blast_map_from_data,
    critical_path,
    default_floor,
    fold,
    frontier,
    migrate_v3_tag,
    parse_ticket_header,
    route,
    select_batch,
    ticket_zones,
    tier_floor,
    touches_overlap,
)
from test_core_globs import GLOB_POOL, random_glob, random_tree

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


def test_frontier_accepts_the_v4_ready_status() -> None:
    t1 = Ticket("01", "a", Tag.CONTRACT, Size.LOW, (), "ready-for-agent", 0)
    t2 = Ticket("02", "b", Tag.CONTRACT, Size.LOW, ("01",), "ready-for-agent", 0)
    assert [t.id for t in frontier((t1, t2))] == ["01"]


# ---------------------------------------------------------------------------
# v4: floors (plan §2b "Implementer floor" row, §3.2)
# ---------------------------------------------------------------------------


def test_blast_floor_mapping_is_the_documented_one() -> None:
    for tag in Tag:
        assert blast_floor(Blast.B0, tag) is Tier.T5
        assert blast_floor(Blast.B1, tag) is Tier.T2
        assert blast_floor(Blast.B3, tag) is Tier.T0
        assert blast_floor(Blast.B2, tag) is (Tier.T0 if tag is Tag.CONTRACT else Tier.T2)


def test_floor_is_never_below_either_input_and_is_the_stronger_of_the_two() -> None:
    for tag, size, blast in itertools.product(Tag, Size, Blast):
        floor = tier_floor(tag, size, blast)
        assert floor.value <= default_floor(tag, size).value, (tag, size, blast)
        assert floor.value <= blast_floor(blast, tag).value, (tag, size, blast)
        assert floor.value in (default_floor(tag, size).value, blast_floor(blast, tag).value)


def test_floor_is_monotone_in_blast_and_size() -> None:
    blasts = list(Blast)
    sizes = list(Size)
    for tag, size in itertools.product(Tag, Size):
        values = [tier_floor(tag, size, b).value for b in blasts]
        assert values == sorted(values, reverse=True), (tag, size, values)  # higher blast, stronger floor
    for tag, blast in itertools.product(Tag, Blast):
        values = [tier_floor(tag, s, blast).value for s in sizes]
        assert values == sorted(values, reverse=True), (tag, blast, values)


def test_b0_floor_is_the_v3_floor_and_b3_is_always_the_top_tier() -> None:
    for tag, size in itertools.product(Tag, Size):
        assert tier_floor(tag, size, Blast.B0) is default_floor(tag, size)
        assert tier_floor(tag, size, Blast.B3) is Tier.T0


def test_route_honours_the_blast_floor_and_b3_never_explores() -> None:
    gov = GovernorState()
    for tag, size, blast in itertools.product(V4_TAGS, Size, Blast):
        t = Ticket("09", "x", tag, size, (), "ready", 0, blast=blast, touches=("src/**",))
        floor = tier_floor(tag, size, blast)
        for rand in (0.0, 0.05, 0.5, 0.99):
            d = route(t, LADDER, {}, gov, now=0.0, rand=rand)
            assert isinstance(d, Routed)
            assert d.tier.value <= floor.value, (tag, size, blast, rand, d)
            if blast is Blast.B3:
                assert d.explored is False and d.tier is Tier.T0


# ---------------------------------------------------------------------------
# v4: v3 tag migration (plan §3.2)
# ---------------------------------------------------------------------------


def test_v3_migration_properties_over_every_input() -> None:
    for tag, size, declared in itertools.product(Tag, Size, [None, *Blast]):
        if tag in V4_TAGS and declared is None:
            try:
                migrate_v3_tag(tag, size, declared)
            except ValueError as exc:
                assert "Blast" in str(exc)
                continue
            raise AssertionError(f"{tag} without Blast must be refused")
        new_tag, new_size, blast = migrate_v3_tag(tag, size, declared)
        assert new_tag in V4_TAGS
        if declared is not None:
            assert blast.value >= declared.value  # migration never lowers a declared level
        if tag is Tag.CRITICAL:
            assert (new_tag, new_size, blast) == (Tag.CONTRACT, size, Blast.B3)
        elif tag is Tag.TRIVIAL:
            assert (new_tag, new_size) == (Tag.CODE_COMPLETE, Size.LOW)
            assert blast is (declared if declared is not None else Blast.B0)
        else:
            assert (new_tag, new_size, blast) == (tag, size, declared)
        # The migrated routing floor is never weaker than the v3 floor.
        assert tier_floor(new_tag, new_size, blast).value <= default_floor(tag, size).value


def test_v3_critical_keeps_t0_and_trivial_rises_from_t5_to_t4() -> None:
    for size in Size:
        assert tier_floor(*migrate_v3_tag(Tag.CRITICAL, size, None)) is Tier.T0
        assert tier_floor(*migrate_v3_tag(Tag.TRIVIAL, size, None)) is Tier.T4


# ---------------------------------------------------------------------------
# v4: ticket header parsing (plan §3.2)
# ---------------------------------------------------------------------------

# Verbatim header of this repo's v4 ticket 02: parenthetical Status, "—" for
# no blockers, an annotation containing a comma inside Touches, and a
# Reference with a note.
TICKET_02 = """# 02 — spike headless workers

Type: spike
Status: ready-for-agent (quota-spending runs are operator-triggered, per run)
Blocked by: —
Tag: contract
Blast: B1 — throwaway probes; findings gate B2 tickets 08/09/10
Size: low
Touches: .scratch/v4-execution/spikes/**, plugin/skills/code-style/references/lint-packs/** (P4 verification markers, per ticket 04 handoff), plugin/skills/worker-harness/references/harness/smoke_workers.sh, plugin/skills/worker-harness/references/harness/launchers/claude_p.py, plugin/skills/worker-harness/references/harness/launchers/codex_p.py, docs/vendor-smoke.md
Reference: outrigger@9fa7023:tools/exec-loop/SMOKE.md (pattern — prior smoke ledger; only its non-wall facts apply)
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md §8.1, §9

## What

Touches: this/line/is/body/text/**
"""


def test_parse_real_ticket_02_header() -> None:
    t = parse_ticket_header(TICKET_02, "02")
    assert t.title == "02 — spike headless workers"
    assert t.status == "ready-for-agent"
    assert t.blocked_by == ()
    assert (t.tag, t.size, t.blast) == (Tag.CONTRACT, Size.LOW, Blast.B1)
    assert t.blast_reason == "throwaway probes; findings gate B2 tickets 08/09/10"
    assert t.touches == (
        ".scratch/v4-execution/spikes/**",
        "plugin/skills/code-style/references/lint-packs/**",
        "plugin/skills/worker-harness/references/harness/smoke_workers.sh",
        "plugin/skills/worker-harness/references/harness/launchers/claude_p.py",
        "plugin/skills/worker-harness/references/harness/launchers/codex_p.py",
        "docs/vendor-smoke.md",
    )
    assert t.reference == Reference(
        target="outrigger@9fa7023:tools/exec-loop/SMOKE.md",
        mode=ReuseMode.PATTERN,
        note="prior smoke ledger; only its non-wall facts apply",
    )
    assert t.migrated_from is None and t.attempts == 0


def test_parse_plan_example_header() -> None:
    text = """# 21 — store layer

Status: ready-for-agent
Blocked by: 03, 05
Tag: code-complete
Blast: B3 — changes session token validation
Size: medium
Touches: src/store/**, tests/store/**, app/(auth)/page.tsx
Decides: D-014
Depends-on: D-003, D-007
Reference: tokio-rs/axum@3f2c1e9:examples/jwt/src/main.rs (pattern)
"""
    t = parse_ticket_header(text, "21")
    assert t.blocked_by == ("03", "05")
    assert t.blast is Blast.B3 and t.blast_reason == "changes session token validation"
    assert t.touches == ("src/store/**", "tests/store/**", "app/(auth)/page.tsx")
    assert t.decides == ("D-014",) and t.depends_on == ("D-003", "D-007")
    assert t.reference == Reference("tokio-rs/axum@3f2c1e9:examples/jwt/src/main.rs", ReuseMode.PATTERN)


def test_parse_migrates_v3_headers() -> None:
    critical = "Status: ready\nTag: critical\nSize: high\nTouches: src/auth/**\n"
    t = parse_ticket_header(critical, "31")
    assert (t.tag, t.size, t.blast, t.migrated_from) == (Tag.CONTRACT, Size.HIGH, Blast.B3, Tag.CRITICAL)
    assert t.blast_reason == "migrated from v3 Tag: critical"
    trivial = "Status: ready\nTag: trivial\nSize: very-high\nTouches: README.md\n"
    t = parse_ticket_header(trivial, "32")
    assert (t.tag, t.size, t.blast, t.migrated_from) == (Tag.CODE_COMPLETE, Size.LOW, Blast.B0, Tag.TRIVIAL)
    raised = "Status: ready\nTag: trivial\nBlast: B2 — shared config\nSize: low\nTouches: README.md\n"
    assert parse_ticket_header(raised, "33").blast is Blast.B2  # declared level survives migration


def test_parse_refuses_malformed_headers() -> None:
    base = {
        "Status": "ready-for-agent",
        "Tag": "contract",
        "Blast": "B1",
        "Size": "low",
        "Touches": "src/**",
    }
    bad: list[tuple[dict[str, str | None], str]] = [
        ({"Blast": None}, "needs a declared Blast"),
        ({"Touches": None}, "missing header 'Touches'"),
        ({"Touches": "—"}, "empty Touches"),
        ({"Touches": "src/"}, "bad Touches glob"),
        ({"Touches": "src/a**"}, "bad Touches glob"),
        ({"Tag": "critcal"}, "unknown Tag"),
        ({"Size": "huge"}, "unknown Size"),
        ({"Blast": "B4"}, "malformed Blast"),
        ({"Blast": "B2 —"}, "malformed Blast"),
        ({"Reference": "repo@abc:x.py (borrow)"}, "malformed Reference"),
        ({"Decides": "ADR-7"}, "Decides id"),
        ({"Depends-on": "D-1"}, "Depends-on id"),
        ({"Blocked by": "03; 04"}, "malformed blocker"),
    ]
    for overrides, needle in bad:
        fields: dict[str, str | None] = {**base, **overrides}
        text = "# 40 — x\n\n" + "".join(f"{k}: {v}\n" for k, v in fields.items() if v is not None)
        try:
            parse_ticket_header(text, "40")
        except TicketHeaderError as exc:
            assert "TICKET-INVALID 40" in str(exc) and needle in str(exc), (overrides, str(exc))
            continue
        raise AssertionError(f"accepted malformed header {overrides}")
    duplicate = "Status: ready\nTag: contract\nTag: contract\nBlast: B0\nSize: low\nTouches: a\n"
    try:
        parse_ticket_header(duplicate, "41")
    except TicketHeaderError as exc:
        assert "duplicate header 'Tag'" in str(exc)
    else:
        raise AssertionError("accepted a duplicate header")


def test_parse_accepts_a_configured_ref_pattern() -> None:
    text = "Status: ready\nTag: contract\nBlast: B1\nSize: low\nTouches: a\nDepends-on: ADR-0007\n"
    assert parse_ticket_header(text, "42", ref_pattern=r"^ADR-\d{4}$").depends_on == ("ADR-0007",)


def test_parse_round_trips_random_headers() -> None:
    rng = random.Random(7)
    for _ in range(300):
        tag = rng.choice(list(Tag))
        size = rng.choice(list(Size))
        declared = rng.choice([None, *Blast]) if tag not in V4_TAGS else rng.choice(list(Blast))
        blockers = rng.sample(["01", "02", "03", "L-01"], rng.randint(0, 3))
        touches = rng.sample(GLOB_POOL, rng.randint(1, 4))
        reason = rng.choice(["", "why it matters"])
        lines = [f"# {rng.randint(1, 99):02d} — title", "", "Type: task", "Status: ready-for-agent"]
        lines.append(f"Blocked by: {', '.join(blockers) if blockers else '—'}")
        lines.append(f"Tag: {tag.value}")
        if declared is not None:
            lines.append(f"Blast: {declared.name}" + (f" — {reason}" if reason else ""))
        lines.append(f"Size: {size.value}")
        lines.append("Touches: " + ", ".join(g + rng.choice(["", " (note, with comma)"]) for g in touches))
        lines += ["", "## What", "Blast: B0"]
        t = parse_ticket_header("\n".join(lines) + "\n", "77")
        expected = migrate_v3_tag(tag, size, declared)
        assert (t.tag, t.size, t.blast) == expected
        assert t.blocked_by == tuple(blockers)
        assert t.touches == tuple(touches)
        assert t.migrated_from == (None if tag in V4_TAGS else tag)
        if declared is not None and reason:
            assert t.blast_reason == reason


# ---------------------------------------------------------------------------
# Blast map: format §8 worked example (normative scheduling vector)
# ---------------------------------------------------------------------------

WORKED_MAP_TOML = """
schema = 1
pack = "one-punch-default/1"
pattern_skip = ["**/*.md"]

[[zone]]
name = "auth-sessions"
level = "B3"
checklist = "auth-sessions"
why = "Authentication and sessions fail open silently."
paths = ["src/auth/**"]

  [[zone.pattern]]
  regex = '(?i)\\bjwt\\b'
  match = ["claims = jwt.decode(raw, key)"]
  nomatch = ["jwtish = 1"]

[[zone]]
name = "process-rules"
level = "B3"
protected = true
why = "Rule surfaces steer every later change."
paths = ["**/AGENTS.md", "docs/blast-map.md", "docs/decisions.md"]

[[zone]]
name = "dependency-manifests"
level = "B2"
why = "Dependency changes are wide."
paths = ["**/pyproject.toml"]

[[zone]]
name = "request-input"
level = "B2"
checklist = "untrusted-input"
why = "Request parsing sits on a trust boundary."

  [[zone.pattern]]
  regex = '\\brequest\\.(json|form|args)\\b'
  match = ["rows = request.json"]

[[lowering]]
zone = "request-input"
paths = ["src/admin/**"]
level = "B1"
decision = "D-014"
"""
WORKED_TREE = ["src/auth/login.py", "src/api/users.py", "AGENTS.md", "pyproject.toml"]


def worked_map() -> BlastMap:
    return blast_map_from_data(tomllib.loads(WORKED_MAP_TOML))


def st(tid: str, touches: tuple[str, ...], blast: Blast = Blast.B1, size: Size = Size.MEDIUM) -> Ticket:
    return Ticket(tid, tid, Tag.CONTRACT, size, (), "ready-for-agent", 0, blast=blast, touches=touches)


def test_blast_map_projection_keeps_only_scheduling_fields() -> None:
    m = worked_map()
    assert [z.name for z in m.zones] == ["auth-sessions", "process-rules", "dependency-manifests", "request-input"]
    assert m.zones[0] == Zone("auth-sessions", Blast.B3, ("src/auth/**",))
    assert m.zones[3].paths == ()  # pattern-only
    broken_maps: list[dict[str, object]] = [
        {},
        {"zone": []},
        {"zone": [{"name": "z", "level": "B9"}]},
        {"zone": [{"name": "z", "level": "B1", "paths": ["src/"]}]},
        {"zone": [{"name": "z", "level": "B1"}, {"name": "z", "level": "B2"}]},
    ]
    for broken in broken_maps:
        try:
            blast_map_from_data(broken)
        except ValueError as exc:
            assert "BLAST-MAP-INVALID" in str(exc)
            continue
        raise AssertionError(f"accepted {broken}")


def test_format_worked_example_zones() -> None:
    m = worked_map()
    assert ticket_zones(["src/auth/**"], m, WORKED_TREE) == {"auth-sessions"}
    assert ticket_zones(["src/api/**"], m, WORKED_TREE) == frozenset()
    assert ticket_zones(["src/**"], m, WORKED_TREE) == {"auth-sessions"}
    assert ticket_zones(["AGENTS.md"], m, WORKED_TREE) == {"process-rules"}


def test_format_worked_example_batching() -> None:
    m = worked_map()
    a = st("A", ("src/auth/**",), Blast.B3)
    b = st("B", ("src/api/**",))
    c = st("C", ("src/**",))
    d = st("D", ("AGENTS.md",))
    assert {t.id for t in select_batch([a, b, d], 4, m, WORKED_TREE)} == {"A", "B", "D"}
    assert {t.id for t in select_batch([a, c], 4, m, WORKED_TREE)} == {"A"}


def test_b3_zone_exclusion_is_separate_from_touches_disjointness() -> None:
    m = worked_map()
    tree = WORKED_TREE + ["src/auth/logout.py"]
    login = st("01", ("src/auth/login.py",), Blast.B3)
    logout = st("02", ("src/auth/logout.py",), Blast.B1)
    assert not touches_overlap(login.touches, logout.touches, tree)
    assert [t.id for t in select_batch([login, logout], 4, m, tree)] == ["01"]  # same zone, one is B3
    calm = st("01", ("src/auth/login.py",), Blast.B2)
    assert [t.id for t in select_batch([calm, logout], 4, m, tree)] == ["01", "02"]
    # A pattern-only zone never excludes: request-input has no paths.
    api = st("03", ("src/api/users.py",), Blast.B3)
    admin = st("04", ("src/admin/**",), Blast.B1)
    assert len(select_batch([api, admin], 4, m, tree)) == 2


# ---------------------------------------------------------------------------
# Critical path and select_batch
# ---------------------------------------------------------------------------


def test_critical_path_lengths() -> None:
    t = [
        Ticket("01", "a", Tag.CONTRACT, Size.LOW, (), "done", 0),
        Ticket("02", "b", Tag.CONTRACT, Size.LOW, ("01",), "ready", 0),
        Ticket("03", "c", Tag.CONTRACT, Size.LOW, ("02",), "ready", 0),
        Ticket("04", "d", Tag.CONTRACT, Size.LOW, ("03", "02"), "ready", 0),
        Ticket("05", "e", Tag.CONTRACT, Size.LOW, ("L-01",), "ready", 0),
    ]
    assert critical_path(t) == {"02": 3, "03": 2, "04": 1, "05": 1}
    cyclic = [
        Ticket("01", "a", Tag.CONTRACT, Size.LOW, ("02",), "ready", 0),
        Ticket("02", "b", Tag.CONTRACT, Size.LOW, ("01",), "ready", 0),
    ]
    try:
        critical_path(cyclic)
    except ValueError as exc:
        assert "cycle" in str(exc)
    else:
        raise AssertionError("cycle not detected")


def test_ties_break_by_critical_path_then_size_then_id() -> None:
    m = BlastMap(zones=())
    small = st("01", ("x/**",), size=Size.LOW)
    big = st("02", ("x/**",), size=Size.VERY_HIGH)
    assert select_batch([small, big], 1, m, []) == (big,)
    assert select_batch([small, big], 1, m, [], critical_path={"01": 3, "02": 1}) == (small,)
    twin = st("03", ("x/**",), size=Size.VERY_HIGH)
    assert select_batch([twin, big], 1, m, []) == (big,)


def test_select_batch_refuses_bad_input() -> None:
    m = BlastMap(zones=())
    cases: list[tuple[list[Ticket], int, dict[str, int] | None, str]] = [
        ([st("01", ())], 2, None, "empty Touches"),
        ([st("01", ("a",)), st("01", ("b",))], 2, None, "duplicate"),
        ([st("01", ("a",))], -1, None, ">= 0"),
        ([st("01", ("a",))], 2, {}, "lacks frontier"),
    ]
    for tickets, n, cp, needle in cases:
        try:
            select_batch(tickets, n, m, [], critical_path=cp)
        except ValueError as exc:
            assert needle in str(exc), (needle, str(exc))
            continue
        raise AssertionError(f"accepted {needle}")


SCHED_MAP = BlastMap(
    zones=(
        Zone("auth", Blast.B3, ("src/auth/**",)),
        Zone("rules", Blast.B3, ("**/AGENTS.md",)),
        Zone("api", Blast.B2, ("src/api/*.py",)),
        Zone("patterns-only", Blast.B2, ()),
    )
)


def random_frontier(rng: random.Random) -> list[Ticket]:
    tickets = []
    for i in range(rng.randint(1, 8)):
        touches = tuple(dict.fromkeys(random_glob(rng) for _ in range(rng.randint(1, 2))))
        blast = rng.choice([Blast.B0, Blast.B1, Blast.B2, Blast.B3, Blast.B3])
        tickets.append(st(f"{i:02d}", touches, blast, rng.choice(list(Size))))
    return tickets


def test_select_batch_properties() -> None:
    rng = random.Random(23)
    for _ in range(250):
        tree = random_tree(rng)
        tickets = random_frontier(rng)
        n = rng.randint(0, 5)
        cp = {t.id: rng.randint(1, 4) for t in tickets}
        batch = select_batch(tickets, n, SCHED_MAP, tree, critical_path=cp)
        ids = [t.id for t in batch]
        assert len(ids) == len(set(ids)) and len(batch) <= n
        assert all(t in tickets for t in batch)
        zones = {t.id: ticket_zones(t.touches, SCHED_MAP, tree) for t in tickets}

        def conflict(x: Ticket, y: Ticket) -> bool:
            if touches_overlap(x.touches, y.touches, tree):
                return True
            return Blast.B3 in (x.blast, y.blast) and bool(zones[x.id] & zones[y.id])

        for x, y in itertools.combinations(batch, 2):
            assert not touches_overlap(x.touches, y.touches, tree), (x, y, tree)  # disjoint Touches
            if Blast.B3 in (x.blast, y.blast):
                assert not zones[x.id] & zones[y.id], (x, y, tree)  # B3 zone exclusion
        if len(batch) < n:  # maximal: everything left out conflicts with a chosen ticket
            for t in tickets:
                if t not in batch:
                    assert any(conflict(t, c) for c in batch), (t, batch, tree)
        if n >= 1:  # the top-priority ticket always runs
            top = min(tickets, key=lambda t: (-cp[t.id], -["low", "medium", "high", "very-high"].index(t.size.value), t.id))
            assert batch[0] == top
        shuffled = tickets[:]
        rng.shuffle(shuffled)
        assert select_batch(shuffled, n, SCHED_MAP, list(reversed(tree)), critical_path=cp) == batch


# ---------------------------------------------------------------------------
# `python -m unittest` collects the module-level test functions too.
# ---------------------------------------------------------------------------


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None) -> unittest.TestSuite:
    suite = unittest.TestSuite(tests)
    for name, obj in sorted(globals().items()):
        if name.startswith("test_") and callable(obj) and not isinstance(obj, type):
            suite.addTest(unittest.FunctionTestCase(obj, description=name))
    return suite

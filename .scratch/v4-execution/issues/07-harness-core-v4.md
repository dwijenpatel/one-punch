# 07 — harness core v4

Type: task
Status: done
Blocked by: 03
Tag: contract
Blast: B2 — routing and batching every build depends on
Size: high
Touches: plugin/skills/worker-harness/references/harness/core.py, plugin/skills/worker-harness/references/harness/test_core.py
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md

## What

Extend the pure core (plan §3.2, §3.4, §2b): parse v4 ticket headers (`Tag`, `Blast` + reason, `Touches`, `Decides`, `Depends-on`, `Reference` + mode); migrate v3 tags (`critical` → B3, `trivial` → B0 + low); tier floor = max(tag × size floor, blast floor); `select_batch(frontier, n, blast_map, tree)` — pairwise-disjoint `Touches` (overlap: any existing file matches both, or same not-yet-existing prefix), B3 never co-batched with a ticket in the same blast-map zone, ties by critical path then size.

Constraints: stays functional-core — no I/O, time/randomness injected, stdlib only, `mypy --strict` clean, zero mocks. Tree listing is an argument, not a filesystem call.

Acceptance: property tests for disjointness, B3 zone exclusion, floor monotonicity (floor never below either input), v3 migration; `python -m unittest` green; `mypy --strict core.py` clean.

## Comments

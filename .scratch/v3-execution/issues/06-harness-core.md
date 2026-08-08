# 06 — Harness python core (pure, typed)

Type: task
Status: done
Blocked by: 05
Tag: contract
Size: very-high

## Question

Functional-core/imperative-shell, stdlib-only, mypy --strict: frozen dataclass domain, route() pure function (floors, epsilon-bandit, escalation), JSONL event-log folds, tier table as data. Property-style tests on routing invariants; zero mocks in core.

## Comments

Completed 2026-08-08, test-first (red: ModuleNotFound; green: 11/11, mypy
--strict clean). core.py: frozen dataclass domain, route() pure (floors hard,
upward-only fallback, one-tier escalation then park, epsilon-greedy w/
least-sampled explore + recency-weighted exploit, unseen prior 0.5), fold()
over Outcome|LimitHit events, frontier(). Zero mocks; time/randomness injected.

DESIGN OBSERVATION (flag for retro): under the ratified constraints
(exploration only on low/medium sizes; critical never explores), T0 and T1
structurally NEVER explore — their only traffic is critical and
high/very-high-contract tickets. Bandit calibration therefore happens only in
T2-T5 and via escalated arrivals; T1 placements (e.g. grok @ max) gather
evidence only through exploitation wins, fallback, or operator-approved
auditions. Surfaced by the test suite itself (the original explore test was
impossible as written).

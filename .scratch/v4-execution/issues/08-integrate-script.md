# 08 — integrate script

Type: task
Status: ready-for-agent
Blocked by: 02, 03, 04, 07
Tag: contract
Blast: B2 — the only path to the integration branch
Size: very-high
Touches: plugin/skills/worker-harness/references/harness/integrate.py, plugin/skills/worker-harness/references/harness/test_integrate.py, plugin/skills/worker-harness/references/harness/checks/**
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md

## What

Plan §3.5 end to end: refuse without a DONE/DONE_WITH_CONCERNS handoff; rebase onto `integrate/<effort>` (conflict → abort + `CONFLICT` event); run verify commands from `harness.toml`; checks — ref (`D-NNN` resolve to active rows; pattern configurable), Touches (outside without `BREAKING(D-NNN)` → fail; into B3 zone from non-B3 → fail), blast detector (effective > declared → `BLAST-ESCALATION`), scrutiny evidence (B2 spec verdict; B3 independent tests committed before implementation commits + lens report + checklist), attribution (`port`/`fork` references need a notices entry + allowed license), style lint severities (hard fail vs soft-cap warnings to log/handoff; brownfield ratchet), megafile (crossed threshold in this change), `allow(<rule>): D-NNN` exceptions honored; then fast-forward (B0–B2) or `AWAITING-OPERATOR` with review packet (B3); JSONL event with declared/effective blast.

Constraints: functional core / imperative shell — each check is a pure function over (diff, tree, ledger, config) and unit-tested; git calls live in a thin shell. Error messages pinned by substring (v3 §7.3).

Acceptance: one test per check (pass + fail case); an end-to-end test on a temp repo (clean ff, conflict, escalation, B3 hold); `mypy --strict` clean.

## Comments

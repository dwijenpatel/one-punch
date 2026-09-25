# 10 — harness merge and lens

Type: task
Status: ready-for-agent
Blocked by: 09
Tag: contract
Blast: B2
Size: high
Touches: plugin/skills/worker-harness/references/harness/review.py, plugin/skills/worker-harness/references/harness/test_review.py
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md

## What

The agent paths the loop invokes (plan §3.1, §3.5 step 2, §3.9, §2b): merge agent on `CONFLICT` (Sonnet; Opus if either ticket is B3; both tickets + handoffs + Depends-on rows; result re-enters integrate; B3 merges re-enter B3 review); spec-verdict reviewer (B2, `contract`); B3 path — independent acceptance-test author dispatched *before* the implementer, decorrelated lens via `codex_p` when its smoke passes else fresh Opus (codebase + ticket + diff only), review packet assembly for AWAITING-OPERATOR. Reviewers read-only; every dispatch names its model; never Fable.

Acceptance: mock-launcher tests: conflict → merge agent → re-integrate; B3 ticket produces tests-first commit order, lens report, packet; lens falls back to Opus when codex smoke is absent.

## Comments

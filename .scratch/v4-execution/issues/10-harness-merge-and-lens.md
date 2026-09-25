# 10 — harness merge and lens

Type: task
Status: done
Blocked by: 09
Tag: contract
Blast: B2
Size: high
Touches: plugin/skills/worker-harness/references/harness/review.py, plugin/skills/worker-harness/references/harness/test_review.py, plugin/skills/worker-harness/references/harness/run.py, plugin/skills/worker-harness/references/harness/runcore.py, plugin/skills/worker-harness/references/harness/test_run.py, plugin/skills/worker-harness/references/harness/integrate.py
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md

## What

The agent paths the loop invokes (plan §3.1, §3.5 step 2, §3.9, §2b): merge agent on `CONFLICT` (Sonnet; Opus if either ticket is B3; both tickets + handoffs + Depends-on rows; result re-enters integrate; B3 merges re-enter B3 review); spec-verdict reviewer (B2, `contract`); B3 path — independent acceptance-test author dispatched *before* the implementer, decorrelated lens via `codex_p` when its smoke passes else fresh Opus (codebase + ticket + diff only), review packet assembly for AWAITING-OPERATOR. Reviewers read-only; every dispatch names its model; never Fable.

Acceptance: mock-launcher tests: conflict → merge agent → re-integrate; B3 ticket produces tests-first commit order, lens report, packet; lens falls back to Opus when codex smoke is absent.

## Comments
2026-09-25 — from ticket 08, the scrutiny-evidence convention integrate checks:
reviewers commit under `<review_dir>/<ticket>/` on the ticket branch
`spec-verdict.md` and `lens.md` (each with a `Verdict: pass|concerns|fail`
line; fail fails), and `checklist-<id>.md` in blast-map-format §7 answer
grammar. Tests-first: the first commit touching anything beyond the handoff
and review files may touch only `test_globs` files. Git cannot prove the test
author was independent, so this ticket's dispatch must guarantee it (a separate
agent, dispatched before the implementer).
2026-09-25 — from ticket 09 (run.py merged; read `handoffs/09.md`): remove
run's temporary B3 plan-time hold (`b3-path` park) once this ticket's B3 path
exists. Make integrate's `_checklist_sources` and `_env` public (run.py
imports them). CONFLICT currently parks the ticket; wire the merge agent into
that branch of run.py.

# 09 — harness run parallel

Type: task
Status: ready-for-agent
Blocked by: 02, 07, 08
Tag: contract
Blast: B2
Size: very-high
Touches: plugin/skills/worker-harness/references/harness/run.py, plugin/skills/worker-harness/references/harness/test_run.py, plugin/skills/worker-harness/references/harness/launchers/claude_p.py
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md

## What

Supersedes v3 ticket 13. Plan §3.4: `harness run --parallel N` — frontier → `select_batch` → `git worktree add .worktrees/<t>` on `t/<t>` from the integration head → route (tier router + governor) → launch via launcher with preamble (§3.8: AGENTS.md pointer, field guide inline, Depends-on rows, blast level + required steps + checklist for B2/B3, handoff contract) → on exit run `integrate` → keep the pipe full → salvage/escalate per v3. Stop conditions: frontier empty · all parked/blocked · K (default 2) parked on non-reversible `Decisions needed` · all candidates cooling · operator stop. `resume` reports frontier / in-flight / AWAITING-OPERATOR / parked / cooling from the ledger. Worktrees removed after integrate, kept on failure. N lowered to the ceiling ticket 02 measured.

Constraints: the loop is deterministic — no LLM decides scheduling; all decisions in core.py. `claude_p` updated per ticket 02 findings.

Acceptance: integration tests against the mock launcher: 4-wide batch with disjoint Touches; overlap serialized; stop on K decisions-needed; resume from a bare clone; kill -INT mid-run leaves a resumable ledger.

## Comments

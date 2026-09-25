# 02 — spike headless workers

Type: spike
Status: ready-for-agent
Blocked by: —
Tag: contract
Blast: B1 — throwaway probes; findings gate B2 tickets
Size: medium
Touches: .scratch/v4-execution/spikes/**
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md

## What

Settle plan §8.1 by execution (one-punch `spike`; transcript = command · trimmed output · versions · date, recorded here and under `spikes/`):
1. `claude -p` launched with cwd inside `.worktrees/<ticket>` (branch `t/<ticket>` from an integration head) commits to that branch only.
2. Four concurrent headless sessions on the operator's subscription: where limits bite, and the exact error shape (feeds the usage governor).
3. Permission mode + tool allowlist for edit/test/commit without prompts; whether `claude_p`'s isolation intent (deny-read walls) is expressible on the current CLI build.
4. Whether a headless worker loads the operator's plugins/skills (`tdd`); if not, what the preamble must carry.
5. `codex_p` smoke on the current Codex CLI build (lens path).
6. Lint rule names for the §3.11 language packs outside ruff (eslint, pylint, clippy, Go) — verified against installed tool output.

Acceptance: one transcript per item; each item ends with a verdict line `CONFIRMED | REFUTED | CEILING=<n>`; any REFUTED names the fallback taken (plan §8.1) and amends the plan's deviations log.

## Comments

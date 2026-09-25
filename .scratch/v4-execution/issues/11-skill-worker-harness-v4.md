# 11 — skill worker harness v4

Type: task
Status: ready-for-agent
Blocked by: 08, 09, 10
Tag: contract
Blast: B1
Size: medium
Touches: plugin/skills/worker-harness/SKILL.md, plugin/skills/worker-harness/references/*.md, plugin/skills/worker-harness/references/harness/launchers/**
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md

## What

Rewrite the worker-harness SKILL.md for v4: `run --parallel N` launched from the planner session, stop conditions and the between-run steering loop, `integrate` and its checks, handoff schema (plan §3.8), B3 AWAITING-OPERATOR flow, `resume`. Harness-neutral wording; real requirements in `compatibility`. **Remove the unused isolation-wall code** from `claude_p.py`/`codex_p.py`/`CONTRACT.md` and the wall cases in `test_codex_p.py` (walls are out of v4 by operator decision; plan §9).

Acceptance: `rg -q 'parallel' plugin/skills/worker-harness/SKILL.md` · handoff schema in references/ · `skills-ref validate` if available.

## Comments

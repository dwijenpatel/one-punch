# 15 — packaging v4

Type: task
Status: ready-for-agent
Blocked by: 01, 11, 13, 14
Tag: contract
Blast: B1
Size: medium
Touches: plugin/skills/start/**, plugin/skills/learning-gates/SKILL.md, README.md, .claude-plugin/**, plugin/.claude-plugin/**
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md

## What

Remove `start` (steer replaces it; history keeps it). learning-gates: opt-in wording (proposed when INTENT.md names a learning goal). README: v4 shape (steer-then-swarm, blast radius, three-layer standards). Plugin manifest → 0.4.0. Conformance audit of every skill (frontmatter, name↔dir, limits, harness-neutral wording, no repo paths inside SKILL.md).

Acceptance: `test ! -d plugin/skills/start` · manifest version 0.4.0 · audit table in Comments with every skill PASS.

## Comments
2026-09-25 — added by planner from ticket 01's handoff: **pipeline.md trim
pass.** v4 pipeline.md (683 lines) restates contracts that the plan and, after
ticket 11, the worker-harness skill also hold (ticket header §7.1, stop
conditions §6.2, tier ladder §8). Once 11 lands, replace those with pointers
to the skill (compose, don't paraphrase — three copies drift). Also: the
README may still describe v3 stages; update it here.

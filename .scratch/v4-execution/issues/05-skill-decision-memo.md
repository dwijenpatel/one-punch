# 05 — skill decision memo

Type: task
Status: ready-for-agent
Blocked by: —
Tag: contract
Blast: B1
Size: medium
Touches: plugin/skills/decision-memo/**
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md

## What

New skill per plan §1.2 + H2/H3: memo format (demo · risk-register update · forks with evidence link + tier + what it forecloses · reuse fork · blast map ratification · B3 decisions always forks · recorded defaults `D-NNN — decision — rationale` with B2 flagged · not-yet-specified list), the altitude rule, follow-up rounds in the same sitting, adversarial-evidence trigger for one-way doors on external claims, absence claims operator-confirmed, H3 mini-memo variant.

Constraints: compose mattpocock `grilling` (rounds over a frontier) — invoke, don't restate. Conversational surface, never a pasted wall (v3 `cdae9ad`).

Acceptance: `test -f plugin/skills/decision-memo/SKILL.md` · a template in references/ with every memo section · `skills-ref validate` if available.

## Comments

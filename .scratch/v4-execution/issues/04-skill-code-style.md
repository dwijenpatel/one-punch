# 04 — skill code style

Type: task
Status: ready-for-agent
Blocked by: —
Tag: code-complete
Blast: B1
Size: medium
Touches: plugin/skills/code-style/**
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md

## What

New skill per plan §3.11 + Appendix A: the 14-rule template with repo slots, the three layers, hard-fail vs soft-cap lint packs per language (python/ruff verified; others marked `UNVERIFIED` until ticket 02 item 6 lands), the `allow(<rule>): D-NNN` exception convention, the Layer 3 review rubric (incl. "flag only violations and correctness/requirement gaps"), and the rule lifecycle.

Constraints: Appendix A text is transcribed verbatim (code-complete). Evidence citations point at the two research memos; no restating the research.

Acceptance: `rg -q 'Pure core, thin shell' plugin/skills/code-style` · 14 numbered rules in the template reference · lint-pack files per language exist · `skills-ref validate` if available.

## Comments

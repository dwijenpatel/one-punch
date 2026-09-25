# 01 — pipeline v4 amendments

Type: task
Status: done
Blocked by: —
Tag: contract
Blast: B2 — process authority every effort loads
Size: medium
Touches: docs/design/pipeline.md, AGENTS.md
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md

## What

Amend `pipeline.md` to v4 from the ratified plan (docs/design/2026-09-24-v4-steer-then-swarm-plan.md): principles §1 (supersede v3 §1.2 serialization and §4 touchpoint policy), the H1/A1/H2/A2/H3 stage table replacing the v3 stage table, blast radius (§2b) as the scrutiny axis, build loop (§3), code standards (§3.11), evidence in the front half, the v3 tag split. Keep v2/v3 provenance sections; state what v4 superseded and why (cite the evidence memos). AGENTS.md: authority pointer v3 → v4.

Constraints: compose, don't paraphrase — pipeline.md names the skills that carry mechanism instead of restating their rules. No new rules beyond the plan.

Acceptance: `rg -q 'v4' docs/design/pipeline.md` · `rg -q 'blast radius' -i docs/design/pipeline.md` · `rg -q 'pipeline.md.*v4|v4.*pipeline.md' AGENTS.md` · every § cited in the plan's §5 table has a home in pipeline.md (checklist in Comments).

## Comments

Plan §5 → pipeline.md home (acceptance checklist):
- [x] `steer` → §2.1 (H1/A1/H2/A2/H3 rows), §2.2, §5 (lane briefs, dossier format, evidence lane); replaces `start` (§0, §2.2)
- [x] `decision-memo` → §2.1 (H2, H3 mini-memo), §2.2, §4
- [x] `field-guide` → §2.1 (A2), §2.2, §6.6 (plan §3.7)
- [x] `code-style` → §2.1 (A2), §2.2, §9 (plan §3.11), §6.8 (Standards axis)
- [x] `blast-radius` → §2.1 (A1/H2/A2), §2.2, §3 (plan §2b)
- [x] `worker-harness` → §2.1 (Build), §2.2, §6 (plan §3.4 → §6.2; §3.5 → §6.3; §3.9 → §6.8; §8.1 gate → §6 intro), §8
- [x] `intent` → §2.1 (H1), §2.2, §1 principle 0a
- [x] `retro` → §2.2, §11 (plan §6 metrics, headline metric, kill/revise)
- [x] `learning-gates` → §2.2, §12 (opt-in)
- [x] `spike`, `contract-review` → §2.2 (unchanged; re-earn clause stands), §1 principle 1
- [x] `start` → §0, §2.2 (front door until `steer` lands, then removed)
- [x] Merge agent (no skill) → §2.2, §6.1, §6.3
- [x] Composed list (mattpocock skills, superpowers discipline) and harness-neutral wording → §2.2, §13

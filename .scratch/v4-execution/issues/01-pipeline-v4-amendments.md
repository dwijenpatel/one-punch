# 01 — pipeline v4 amendments

Type: task
Status: ready-for-agent
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

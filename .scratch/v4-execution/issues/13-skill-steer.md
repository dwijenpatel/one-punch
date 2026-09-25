# 13 — skill steer

Type: task
Status: ready-for-agent
Blocked by: 03, 04, 05, 06, 12
Tag: contract
Blast: B2 — front door every effort passes
Size: very-high
Touches: plugin/skills/steer/**
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md

## What

New front door per plan §2 + §5: H1 (invokes `intent`) → A1 lanes with briefs in references/ (risk spikes; shape: skeleton/prototype or brownfield survey + blast-map proposal; safety net; prior art with the reference-dossier template and reuse modes; evidence lane composing evidence-kit lake-first at retrieval grade, questions tied to forks/risks) under the ≤4 cap and priority order → H2 (invokes `decision-memo`) → A2 (ledger, optional `to-spec`, `to-tickets` + v4 fields, isolate-the-blast, installs `code-style` template + blast map, ticket-graph veto window) → build handoff to `worker-harness` → H3 (milestone report, fast-decay recheck). `resume` reports effort state. Absorbs `start`'s dependency freshness checks.

Constraints: compose — invoke intent, decision-memo, blast-radius, code-style, field-guide, spike, mattpocock skills, evidence-kit; never restate them. SKILL.md < 500 lines.

Acceptance: `test -f plugin/skills/steer/SKILL.md` · dossier template + lane briefs in references/ · every stage names its invoked skill (`rg` list in Comments) · `skills-ref validate` if available.

## Comments

# 13 — skill steer

Type: task
Status: done
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

2026-09-24 — acceptance (worker):
- `test -f plugin/skills/steer/SKILL.md` → pass (301 lines).
- references/: reference-dossier.md, lane-risk.md, lane-shape.md,
  lane-safety-net.md, lane-prior-art.md, lane-evidence.md, ticket-header.md,
  ticket-graph-summary.md, milestone-report.md, prerequisites.md → pass.
- Stage → invoked skill, from
  `rg -n '^## (H1|A1|H2|A2|Build|H3|`steer resume`)|`(intent|decision-memo|blast-radius|code-style|field-guide|spike|retro|worker-harness|wayfinder|prototype|research|to-spec|to-tickets|grilling|code-review)`|evidence-kit' plugin/skills/steer/SKILL.md`:
  - H1 (106): `intent` (108)
  - A1 (115): `spike` (123), `prototype` (124), evidence-kit (127), `blast-radius` (147), `field-guide` (150), `wayfinder` (154); `research` via lane-prior-art.md / lane-evidence.md
  - H2 (161): `decision-memo` (163, 170, 172), `grilling` (171)
  - A2 (177): `to-spec` (184), `to-tickets` (186, 214), `blast-radius` (194, 203), `code-style` (204), `field-guide` (207), `worker-harness` (208)
  - Build (220): `worker-harness` (223), `decision-memo` (233), `field-guide` (243), `retro` (249)
  - H3 (251): `code-review` (259), `code-style` (261), evidence-kit (264), `decision-memo` (270), `retro` (273)
  - resume (278): `worker-harness` `resume` (293)
- `skills-ref validate` not installed; manual yaml.safe_load: name steer ==
  dir, description 966/1024, compatibility 425/500, license MIT → pass.

# 15 — packaging v4

Type: task
Status: done
Blocked by: 01, 11, 13, 14
Tag: contract
Blast: B2 — pipeline.md trim (process authority) + removal of start
Size: medium
Touches: plugin/**, README.md, AGENTS.md, docs/design/pipeline.md, .claude-plugin/**, docs/vendor-smoke.md
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
2026-09-25 — from ticket 08: one-punch's own harness source
(`plugin/skills/worker-harness/references/harness/**`) lands as B3 under the
default pack, because it names auth/money/destructive domains in code and
fixtures. The pack's `.scratch/**/harness/**` zone doesn't cover it. When
one-punch dogfoods v4, its blast map needs a repo zone or a lowering for it.
Record this in the packaging README / dogfood notes.
2026-09-25 — from ticket 09: `closure` runs only machine-readable acceptance
(indented command lines under `Acceptance:`, or fenced blocks in an Acceptance
section). Update `steer`'s ticket-header reference so v4 tickets are cut in
that form. `steer`'s A2 install must ensure `.worktrees/` is git-ignored.
2026-09-25 — from ticket 10: `steer`'s ticket-header reference must require
B3 tickets' `Touches` to include their test paths (the independent test
author may write only test files inside Touches; otherwise the ticket parks
as `stage`). Also document `[run] lens` + `lens_smoke` in harness.toml setup
at A2 (lens model used only while its smoke passes).
2026-09-25 — from ticket 11: launcher tests (`launchers/test_codex_p.py`,
`launchers/test_launchers.py`) are not collected by `python -m unittest`;
make one repo-level verify command that runs the harness suite AND both
launcher suites AND `mypy --strict` on all harness .py (tickets 07–10 checked
subsets and missed 127 errors). Document it in AGENTS.md as the repo's verify.
Touches widened by planner: plugin/**, README.md, AGENTS.md,
docs/design/pipeline.md, .claude-plugin/**, docs/vendor-smoke.md. Blast B2
(pipeline.md trim is the process authority).

2026-09-25 — done (worker). Conformance audit, every skill (script: frontmatter parsed with PyYAML; name == dir and `^[a-z0-9]+(-[a-z0-9]+)*$` ≤64; description ≤1024; compatibility ≤500; SKILL.md <500 lines; every relative link resolves and is one hop, `references/<file>`; no project names, machine/repo paths, plan pointers, SHAs or pipeline-version pointers anywhere in SKILL.md; no vendor tool or product names outside `compatibility:`, where the standard puts real requirements such as a required CLI):

| skill | name==dir | name ok | desc | compat | lines | links (exist, 1 level) | SKILL.md leaks | result |
|---|---|---|---|---|---|---|---|---|
| blast-radius | True | True | 840 | 337 | 183 | 9 True | none | PASS |
| code-style | True | True | 724 | 310 | 132 | 5 True | none | PASS |
| contract-review | True | True | 642 | 156 | 79 | 0 True | none | PASS |
| decision-memo | True | True | 815 | 301 | 158 | 1 True | none | PASS |
| field-guide | True | True | 908 | 155 | 128 | 1 True | none | PASS |
| intent | True | True | 560 | 174 | 133 | 2 True | none | PASS |
| learning-gates | True | True | 572 | 224 | 88 | 2 True | none | PASS |
| retro | True | True | 540 | 146 | 89 | 2 True | none | PASS |
| spike | True | True | 659 | 69 | 52 | 0 True | none | PASS |
| steer | True | True | 966 | 425 | 312 | 10 True | none | PASS |
| worker-harness | True | True | 959 | 408 | 337 | 14 True | none | PASS |

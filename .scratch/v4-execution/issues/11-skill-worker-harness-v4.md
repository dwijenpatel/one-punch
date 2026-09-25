# 11 — skill worker harness v4

Type: task
Status: done
Blocked by: 08, 09, 10
Tag: contract
Blast: B2 — harness core split + launcher changes
Size: medium
Touches: plugin/skills/worker-harness/SKILL.md, plugin/skills/worker-harness/references/*.md, plugin/skills/worker-harness/references/harness/launchers/**, plugin/skills/worker-harness/references/harness/core.py, plugin/skills/worker-harness/references/harness/test_core.py, plugin/skills/worker-harness/references/harness/core_*.py, plugin/skills/worker-harness/references/harness/CONTRACT.md
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md

## What

Rewrite the worker-harness SKILL.md for v4: `run --parallel N` launched from the planner session, stop conditions and the between-run steering loop, `integrate` and its checks, handoff schema (plan §3.8), B3 AWAITING-OPERATOR flow, `resume`. Harness-neutral wording; real requirements in `compatibility`. **Remove the unused isolation-wall code** from `claude_p.py`/`codex_p.py`/`CONTRACT.md` and the wall cases in `test_codex_p.py` (walls are out of v4 by operator decision; plan §9).

Acceptance: `rg -q 'parallel' plugin/skills/worker-harness/SKILL.md` · handoff schema in references/ · `skills-ref validate` if available.

## Comments
2026-09-25 — from tickets 08/09:
- Split `core.py` (852 lines — already past the 800-line megafile threshold)
  and keep `integrate.py` (753), `run.py` (692) and `runcore.py` (533) under it.
- Port `claude_p.py`'s SIGTERM/SIGINT forwarding into `mock.py` and `codex_p.py`.
- Document in the skill: run's exit codes (0/3/4/5/6/7/30/31), integrate's
  exit codes (0/10/20/21/22/30/31/32), `answer` / `relaunch` / `--approve` /
  `closure` / `resume`, stop via `kill -INT <pid>` or the stop file (not
  terminal ^C), the reversibility grammar for `Decisions needed`, and
  "commit the handoff last, on the branch".
2026-09-25 — from ticket 10: also document the dispatch roles (test_author,
spec_verdict, lens, merge), their models, the file-scope rule, B3 salvage,
`[run] lens` / `lens_smoke`, and park states (`stage`, `conflict`,
`blast-b3`). Remove the unused `RouteDecision` import in test_core.py.
Touches widened by planner: this ticket now also owns `core.py` and
`test_core.py` (the split) — Blast raised to B2 (harness core).

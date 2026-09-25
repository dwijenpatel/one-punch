# Evidence memo — 2026-09-25 — v4 bootstrap build (one-punch built with v4-shaped tickets)

**Scope:** the 15 v4 execution tickets (`.scratch/v4-execution/`), 2026-09-24 →
2026-09-25. **Not** a v4 trial: the front half (H1 → H2) was the design
conversation itself, and the harness being built could not run its own build.

## What was measured

| Measure | Value | Source |
|---|---|---|
| Tickets merged | 15 / 15 | ticket `Status:` lines |
| Rebase conflicts at merge | 0 (all disjoint `Touches`; one ticket at a time on the critical path 07 → 08 → 09 → 10 → 11 → 15) | planner merges |
| Defects found by planner review before merge | 3: code-style SKILL.md named the project (portability rule); integrate's megafile rule contradicted the plan ("pass until they grow"); retro's headline denominator counted designed oversight as interventions | review diffs, commits `v4 ticket 04/08/14` |
| Defects found by later workers in earlier tickets' claims | 1 class: tickets 07–10 reported `mypy --strict` clean on file subsets; ticket 11 found 127 errors across launchers and their tests. Fixed; `verify.sh` now checks everything | handoff 11 |
| Worker agent tokens (quota proxy, not money) | ≈2.86M total: Opus ≈2.24M (9 tickets), Sonnet ≈0.61M (5 tickets) | task notifications |
| Spike quota runs | 7 short Claude sessions + 1 Codex session, ≈3 min wall-clock | `spikes/01-p1-p2-p3.md` |
| Operator rulings during build | ≈6: redirect ticket 02 to outrigger prior art; reject isolation walls; sequencing; user-only upstream gates (glad-I-was-asked); T5 unrouted; "you run the probes" | this session |
| Planner process slips | 1: a status commit made directly on `main` (AGENTS.md forbids it); corrected for all later tickets | git history `a7bb3ed` |

## What it confirms / contradicts

- **Confirms:** planner review of worker diffs catches plan-contradicting
  choices that the worker's own acceptance checks pass (megafile, denominator).
  Handoffs with a "Decisions needed — local option — reversibility" section
  surfaced 25+ calls, all resolvable by the planner in one line each: the
  altitude rule working as intended.
- **Confirms:** subset verification silently hides defects (127 mypy errors).
  One repo-wide verify command is the fix; enforce "never check a subset".
- **Contradicts nothing measured yet.** The headline metric (unattended tickets
  per unplanned intervention) is not computable: the build ran on in-session
  subagents, not `harness run`.

## Honesty lines (how this build deviated from v4)

- Merges were planner-reviewed fast-forwards, **not** `integrate`: no blast
  detector, no Touches check, no scrutiny-evidence check ran on these diffs.
- Workers edited their own ticket `Status:` lines, which v4's integrate would
  fail as TOUCHES-B3.
- Tickets 01 and 15 touched process surfaces (`AGENTS.md`, `pipeline.md`,
  manifests, harness) at declared B2; under the default pack they are B3, so
  under v4 the operator would have reviewed those diffs.
- The launchers were changed (ticket 11) **after** the spike's live runs;
  live P1/P3 on the current launcher code is owed.

## Proposed amendments

1. Trial 1 (greenfield, operator-run) is the real test of the front half and
   of `steer` → `harness.toml` → `run` → `integrate` end to end. Watch-for:
   no `harness.toml` example ships; A2 composes one from worker-harness's
   configuration reference.
2. Dogfooding one-punch on itself needs a deliberate blast-map decision for
   the harness source (README note). The default pack's own logic argues for
   B3 on harness self-edits.

## Considered and left unchanged

Tier floors, lane timeboxes, K=2 decisions-needed stop, megafile 800. Nothing
in this build measured them.

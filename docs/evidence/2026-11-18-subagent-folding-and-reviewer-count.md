# Subagent folding and reviewer count (2026-11-18)

**Inputs:**
- Anthropic, "Building agents: When to fold subagents into your main agent
  loop" (claude.com, 2026-10-22).
- The agent-time retro of one effort
  ([2026-11-18-resonance-agent-time-retro.md](2026-11-18-resonance-agent-time-retro.md)):
  635 subagent transcripts.

## The article's test

Keep a separate agent when at least one of these holds:
1. one loop degrades measurably from context bloat;
2. the work runs in parallel in fresh, discardable contexts;
3. tool choice or instructions conflict in one loop;
4. it gives black-box verification.

Fold agents that are split by problem type and chain on each other's output:
each handoff loses fidelity.

Method: an end-to-end eval before the first fold, one change at a time, and a
comparison of which tasks flipped, not only the score. Run every task more
than once.

## one-punch against it

| Role | Condition met | Decision |
|---|---|---|
| Parallel implementers; A1 lanes | 2 | keep |
| Independent B3 test author | 4 | keep |
| Planner that never implements | 1 (the planner compacted repeatedly) | keep |
| Inline worker preambles instead of skill loading | 3 (spike 02); also launcher isolation by design (F4) | keep |
| Spec verdict + lens of the same model family | none | **fold (F1)** |
| A new implementer agent per fix round | none | **fold (F2)** |
| A new reviewer per re-review | partly 4 | **deferred (F3)** |

## Measured

- **The lens ran on the implementers' model family in 180 of 182 runs.** The
  effort's ledger named a codex lens. Its `lens_smoke` was the template's
  `test -f <marker>`, and nothing ever wrote the marker. In light mode,
  nothing routed the lens to codex. No ledger row recorded the fallback.
- **Agents per ticket:** mean 7.0, median 6, max 17.
- **Re-review rounds:** 105 lens runs (23.5h) and 83 spec verdicts (12.3h).
- **Fix rounds:** 48 new implementer agents (16.6h).
- **Re-orientation is cheap:** median time to first edit is 5.8 min for a
  fix-round implementer and 5.2 min for a first-pass one, 4.7h in total. F2's
  case is fidelity, not time.
- **Vendor drift:** on codex-cli 0.156.1, three listed models returned
  `model_not_found` for a subscription login. After an update to 0.170.0,
  `gpt-6.2-astra` passed the lens smoke in 52s and wrote only its review file.
  A smoke record must therefore be pinned to the build.

## Changes (v4.11)

- **F1.** Without a decorrelated lens, B3 gets one T0 `review` dispatch that
  writes both review files (harness role `review`). integrate's scrutiny
  check is unchanged.
- **F2.** A fix round resumes the implementer that wrote the ticket. A new
  agent is used only after an escalation, or when that session is gone.
- **Lens smoke:**
  - `smoke_workers.sh --record` writes `codex <model> <version>`, and
    `lens_smoke` compares that record with the configured model and the
    installed build;
  - a Build-start lens gate puts a failure to the operator: fix it, or
    proceed on a fallback recorded in the ledger;
  - light mode dispatches the lens through `codex_p.py`.
- **Deferred:**
  - **F3, delta-only re-review.** The risk is delayed discovery. It waits for
    reviewer-yield data: medium-or-higher findings per review role that a
    regression test confirmed.
  - **F4, headless skill loading: kept inline, now by decision.** A smoke on
    2026-11-18 (claude 2.1.327, sonnet) passed in 12s and committed its
    work, but reported `skill tdd => unavailable`. That is by design:
    `claude_p` passes `--setting-sources ""` and `--disable-slash-commands` to
    keep ambient configuration away from workers. Progressive disclosure
    would mean reopening that isolation. Inline preambles also stay
    model-neutral for a lens on another model family, so the preamble rule
    stands.
  - **F5, prompt audit of the skills.** It runs separately.

## F1 trial protocol (operator design, 2026-11-18)

F1 is adopted on structural grounds: a same-family pair adds no
independence. Its effect on findings is still to be measured:

1. **Corpus.** A frozen set of past B3 diffs. Each diff carries its confirmed
   medium-or-higher findings, plus planted defects that no arm has seen.
2. **Arms.**
   - A: the spec verdict, then the lens, as two agents.
   - B: one `review` agent.
   - Both on the same model and effort.
3. **Isolation.** Each run gets its own worktree and session. No run sees
   another run's files, findings or transcript, and the arms share nothing
   but the input diff.
4. **Repeats.** At least 3 runs per arm per diff.
5. **Measure.**
   - Recall per defect: which defects each arm catches, and which flip
     between the arms.
   - Overlap between independent runs of the same arm.
6. **Reading overlap.** Overlap between two independent runs of the same arm
   prices a second reviewer of that arm.
   - **Low overlap:** reviewer output varies a lot from run to run, so
     another run adds findings.
   - **High overlap:** a second same-model reviewer adds little.
7. **Revert bar.** Arm B misses a defect class that arm A catches
   consistently.

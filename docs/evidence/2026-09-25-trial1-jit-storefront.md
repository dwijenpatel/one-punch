# Trial 1 (greenfield-on-external-codebase) — adjudication, 2026-09-25

**Evidence:** the trial's full retro memo (operator interaction log, timings, metrics, nine proposed amendments). It is kept in the effort's own repository and is not published here; amendment numbers below refer to it.

**Operator adjudication:** all amendments adopted as the planner recommended.

| # | Amendment | Disposition | Lands in |
|---|---|---|---|
| 1 | Visual closure for UI tickets (browser walk at desktop + 375px asserting each variant's defining behaviour; H3 desktop screenshots) | adopted | steer ticket-header + H3; pipeline.md |
| 2 | Never hand the operator a labelled link that no executed check verified | adopted | steer H2 demo / H3 |
| 3 | Polish as a named stage after H3 (ledger row; failing e2e case before the fix; full suite + neighbouring variants). Planner addition: a fix touching >1 file or ~30 lines goes to a worker (planners don't implement) | adopted + extended | steer; pipeline.md stage table |
| 4 | Defaults ratification merged into the veto window when the milestone is all ≤B1 | adopted | decision-memo + steer A2 |
| 5 | Batch ≤3 forks per turn when every fork is ≤B1; one-at-a-time for B2+ and one-way doors | adopted | decision-memo |
| 6 | Prior-art brief: brand terms, badges, program names are do-not-copy | adopted | steer lane-prior-art |
| 7 | Classifier wording changes need a both-polarity regression set | **field-guide candidate**; promote to a rule on a second occurrence | this memo (tracked) |
| 8 | Retro compiles timing from the session transcript when the harness exposes one | adopted | retro |
| 9 | H1 restates scope from the repo's README/brief before framing questions | adopted | intent |
| 10 | (planner) Light mode is a sanctioned degrade path (in-session workers), but every ticket still lands through `integrate` run by hand; ship an example `harness.toml` so setup is minutes | adopted | worker-harness, steer, pipeline.md |
| 11 | (planner) A2 installs (blast map, code-style section, field guide, harness config) are one automatic template step, not optional ceremony | adopted | steer A2 |

**Planner observations not in the operator's retro:**
- The v4 build path (`harness run` + `integrate`) still has never run on a
  real project: D-011 skipped it for the 2h budget. Trial 2 should use the full
  path on a larger effort.
- Front-half result against v3: first runnable artifact in 44 min, 3 sittings,
  no fork reopened. The ckb baseline was 8 days, 16 decision tickets, zero code.
  This is the strongest evidence yet for the v4 front half.
- Operator time dominated wall clock (58%). H1 ran 35 min against the 15-min
  target, but the retro judges each answer load-bearing, so no amendment is made.

# Milestone report — H3

Written to `milestones/<m>/report.md` after closure (visual closure included,
for UI efforts), milestone review and the fast-decay recheck, and walked with
the operator at the H3 sitting. Every
row links its evidence; a missing artifact is written `not recorded`, never
filled from memory. Forks unlocked by building are not decided here — they go
to the `decision-memo` H3 mini-memo, linked below.

```
# Milestone report — <effort> · <milestone m> · <date>

Integration head: <full SHA> on integrate/<effort> · main at: <full SHA>
Tickets merged: <n> · parked: <n> · still open: <n>

## Demo
<what runs and the exact command to run it>

Links to try (each verified by an executed check; unverified links are not listed):
| Link | Label | Check that verified it | Result |
|---|---|---|---|

## Closure — every merged ticket's acceptance checks, re-run on the integration head
| Ticket | Acceptance command | Result on head | If failed: fixer ticket |
|---|---|---|---|
Closure: green | red (H3 waits; fixer tickets cut: <…>)

## Visual closure (UI efforts; otherwise "not a UI effort")
| Variant | URL | Defining behaviour | Browser walk, desktop / ~375px | Desktop screenshot | Planner inspection |
|---|---|---|---|---|---|
| <label> | <url> | <one sentence> | pass / pass | closure/<variant>.png | fit | defect → fixer ticket <NN> |
Screenshots inspected by the planner before this report: yes

## B2 and B3 changes
| Ticket | Declared → effective blast | Evidence |
|---|---|---|
| <NN> | B3 → B3 | tests: <path>; spec verdict: <link>; lens report: <link>; checklist answers: <link>; operator sign-off: <date> |
| <NN> | B2 → B2 | tests: <path>; spec verdict: <link> |

## Blast escalations caught by the detector
| Ticket | Declared → effective | Cause (path or pattern) | Outcome |
|---|---|---|---|
Recurring pattern: <none | proposal to extend the blast map: …>

## Milestone review
code-review (Standards + Spec) over main..integrate/<effort>: <link>
Lint warnings accumulated this milestone: <count by rule>
Findings → fixer ticket: <NN> · B3-zone findings → own B3 tickets: <NN, …>

## Fast-decay recheck (evidence-kit recheck)
| Fact the build rests on | Decay class | Source | Recheck result | Impact |
|---|---|---|---|---|
| <API price / vendor behavior / library version> | <class> | <holding> | current | changed → <fork or ticket> | struck |

## Steering since the last milestone
Operator interventions: <n> (B3 reviews <n>, parked-ticket steers <n>, manual relaunches <n>)
Ledger rows added / superseded: <D-… list>
Field-guide entries curated: <added n, promoted n, pruned n>

## For the operator
Mini-memo (forks unlocked by building): <link to h3-memo.md | none>
Decision: accept | redirect — <notes>
Merge integrate/<effort> → main: yes (<date>) | no — <why>
Polish log: <link to polish.md>
Retro memo: <link — filled after polish closes and retro runs>
```

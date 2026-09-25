# Evidence memo — <effort> · <date>

Reporter: operator · Compiled by: <agent/session>
Cadence: <milestone N | effort end | outcome report arrival | tier-promotion proposal | validation-trial check>

Every cell below names its source. `not recorded` is an honest value when a
source doesn't exist for this effort (no ledger event, no integrate log, no
evidence corpus); a guessed number is not — leave it `not recorded` instead.

## Headline

**Unattended tickets merged per operator intervention** — the delete-or-keep
signal for whether the build half is pulling its weight.

- Numerator: tickets that reached the integration branch this milestone.
  Source: ledger event.
- Denominator: **unplanned** operator interventions this milestone — answers
  to a parked "decisions needed" item, relaunches after a stalled or failed
  run, and any manual fix the operator made directly. Source: operator report
  + ledger event (park/relaunch events).
- Reported beside it, not in the ratio: **designed oversight**, meaning
  scheduled sittings and highest-blast-level diff reviews. Those are scrutiny
  spent on purpose, not babysitting; count them, and their minutes, so their
  load stays visible without penalizing a milestone for doing its reviews.
- Value this milestone: <n> merged / <n> interventions = <ratio>. Prior
  milestone: <ratio>. Trend: <rising | flat | falling>.

Falling across milestones means the build half is not earning its keep — treat
that as a required finding, not a number to bury in the table below.

## Operator interaction log

Source: session transcript, when the harness or agent environment exposes
one with timestamps; else this whole section is `not recorded` — do not
reconstruct it from memory. One row per operator turn, in order. Class: **D**
designed oversight (a scheduled sitting or review the process asks for) ·
**U** unplanned intervention (the operator found a defect the process didn't
catch) · **S** operator-initiated scope or request · **C** correction of an
agent framing error.

| Turn | Time | Stage | Gist | Class | What prompted it | Avoidable? |
|---|---|---|---|---|---|---|
| | | | | | | |

## Timing

Source: session transcript; else `not recorded`. "Agent active" includes
time waiting on background workers; "Operator" is the gap from the agent's
last action to the next operator message (reading, testing, or away).

| Stage | Wall clock | Duration | Agent active | Operator | Notes |
|---|---|---|---|---|---|
| | | | | | |

## Metrics

| Metric | This milestone | Bar | Source |
|---|---|---|---|
| Operator turns, effort kickoff → first build dispatch | | ≤3 sittings; exceeding it before first dispatch on a trial with a pre-registered bar means the front half needs revision before the next trial | operator report |
| Wall-clock, effort start → first runnable artifact | | <1 day; missing it on a trial with a pre-registered bar means the front half needs revision before the next trial | git (first artifact commit) + operator report (effort-start time) |
| Wall-clock, effort kickoff → first merged ticket | | recorded (no prior baseline until an effort sets one) | git (merge commit time) + operator report (kickoff time) |
| Merge conflicts per merged ticket | | > 0.3 triggers a Touches-granularity review | integrate log (conflict records) ÷ ledger event (merged-ticket count) |
| Integrate verify-fail rate, by tag × blast × model | | recorded; feeds the routing ledger's tier calibration | ledger event |
| Decisions reopened after build started, and the rework they caused | | recorded; a reopened fork that a steering sitting should have asked = an altitude-rule defect | git (decision ledger diffs) + handoffs (deviations, decisions needed) |
| Token share, planner vs. workers (a quota proxy) | | recorded; compare against this pipeline's own prior-milestone baseline — majority share is expected to sit with workers | ledger event (tokens field, tagged planner vs. worker) |
| Escaped defects (found after merge), by blast level | | recorded; any escaped B3 defect triggers a retro of the B3 scrutiny ladder itself | operator report |
| BLAST-ESCALATIONs (planner under-classified the blast level) | | recorded; a recurring pattern means extend the blast map / pattern pack | integrate log |
| Share of tickets at B3, and operator minutes per B3 review | | recorded; B3 share > 20% means the isolate-the-blast rule at ticket-cutting time is failing | ledger event (blast field) + operator report (review minutes) |
| Static-analysis warnings and complexity per merged KLOC; clone-level duplication % | | recorded per milestone; a rising trend across milestones triggers a review of the enforced (linter) rule set | integrate log (soft-cap warnings) |
| Layer 3 rubric findings per milestone, by rule | | recorded; feeds the rule lifecycle below | git (milestone review findings committed to the branch) |
| Verify-fail rate and rework: tickets with a `Reference:` field vs. without | | recorded; tests whether a proven reference implementation pays for itself | ledger event + git (ticket header field) |
| Forks reopened after build, by evidence tier at ratification | | recorded; low-confidence tiers reopening often means escalate the evidence grade earlier next time | git (decision ledger) + handoffs |
| Field-guide entries a later worker actually cited | | recorded; zero after a milestone means question the skill, or the guide's curation | handoffs (field-guide proposals) + git (field-guide commit history / citation greps) |

**Kill/revise clause — concurrency.** Average concurrency per milestone
(tickets batched together under disjoint `Touches`): <value>. Bar: below 2
over a milestone means revisit ticket granularity before adding more merge
machinery. Source: ledger event (batch/worktree launch events).

## Stated-rules on/off comparison (only if this effort is running it)

Some efforts run tickets that alternate with and without the stated
(Layer 1) style section by ticket number, Layers 2–3 unchanged, to measure
what the stated prose itself buys. When active, compile the comparison split
by arm, same sources throughout:

| Quantity | With Layer 1 | Without Layer 1 | Source |
|---|---|---|---|
| Lint warnings per ticket | | | integrate log |
| Layer 3 findings per ticket | | | git (milestone review findings) |
| Verify-fail rate | | | ledger event |
| Tokens per ticket | | | ledger event |

## Rule lifecycle review

- **Pruning candidates**: a stated rule with no Layer 3 finding and no lint
  hit across two milestones. Source: git (Layer 3 findings) + integrate log
  (lint hits).
- **Promote to enforced**: a stated rule a linter can now decide — moves
  into the enforced layer and leaves the prose. Source: operator report /
  planner proposal.
- **Redraft signal**: many `allow(<rule>): D-NNN` exceptions logged against
  one rule — the rule is mis-drawn, not the workers undisciplined. Source:
  git (`allow(` occurrences, grep) + decision ledger.
- **New rule candidates**: only after a repeated mistake; cite the handoffs
  that show the pattern, promoted from the field guide into the stated
  section. Source: handoffs (field-guide proposals) + git (field-guide and
  style-section commit history).

## What was measured

<summary of the metrics above, in prose>

## What it confirms or contradicts in the current process

<one paragraph per notable metric or trend>

## Proposed amendments

Each amendment cites the metric row or finding that motivates it, and its
class (tier change, gate recalibration, rule lifecycle, pipeline amendment).

1. <amendment> — evidence: <metric/row> — class: <class>

## Considered and left unchanged

<what looked like a candidate amendment but wasn't, and why>

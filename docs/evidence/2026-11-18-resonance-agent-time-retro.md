# Evidence memo — resonance · 2026-11-18

Reporter: operator · Compiled by: a forked planner session (Opus 5.5), from the effort's own
session and subagent transcripts and its integration-branch git history.
Cadence: outcome report arrival. Mid-milestone, the operator reported that the effort is taking
far longer than its complexity suggests, with much of it unbuilt.

**Scope and altitude.** This repository is public. The memo carries metrics and process findings
only; the full memo, including per-ticket and per-surface detail, stays in the effort's
repository. **Adjudication:** the operator agreed with every amendment and both hypotheses on
2026-11-18. The amendments land as v4.10 on the commit that cites this file.

## Headline

**Unattended tickets merged per operator intervention:** `not recorded`. The milestone is still
open, and the ledger was not compiled for this memo, which is about where agent time goes.

**Designed oversight:** in this effort the operator chose to approve every B3 merge. With 96% of
tickets at B3, that is one packet read per ticket.

## Method

- **Active time** is the sum of gaps of 10 minutes or less between consecutive messages in each
  transcript. Longer gaps count as idle.
- Two reviewer stalls of 8 hours each were waits on a background job, and are excluded.
- **Roles** come from each agent's launch description.
- **Rework** is every agent after the first one of its role on a ticket. Rounds resumed inside
  one agent count as first pass, so rework is a lower bound.
- Not recorded: the background verify runs for packets and landing.

## Metrics

| Metric | Value | Source |
|---|---|---|
| Span | 10.9 days | transcripts |
| Subagents / active agent-hours | 635 / 146h (88h model, 21h test runs) | subagent transcripts |
| Planner active hours (concurrent) | 54h | main transcripts |
| Implementer and fix rounds | 34% | transcripts, by role |
| Lens review | 28% | transcripts, by role |
| Spec-verdict review | 16% | transcripts, by role |
| Independent test author | 12% | transcripts, by role |
| Eval content (questions, labels, bench) | 3.5% | transcripts, by role |
| Tickets: planned at A2 / at retro | 26 → 76 (one track); 8 → 22 (second track) | git, ticket graph |
| Ticket hours on tickets added after A2 | 63% (first pass 38%, rework 25%) | transcripts × ticket graph |
| Ticket hours in rework rounds, all tickets | 40% | transcripts |
| B3 share of tickets | 73 / 76 = 96% (cap: ~20%) | git, ticket headers |
| Lens findings: high / medium / low / info | 11 / 45 / 148 / 155 (84% low or info) | git, review files |
| Spec-verdict findings: high / medium / low / info | 1 / 11 / 78 / 221 | git, review files |
| Tickets with 3 or more lens runs | 28 of 78 | transcripts |
| Hours on the project's own verify tooling | 19.3h, more than the gate core, the diff gate and the test fixture together (11.7h) | transcripts × tickets |
| Test lines : source lines | 48.4k : 10.6k | git |
| Full verify duration | ~25 min, per round, per packet and per landing re-judge | handoffs |

## What it confirms or contradicts

1. **Contradicts:** the 2026-11-10 amendment's "A2 keeps B3 under ~20%". The ticket graph reported
   the high share, and the build went ahead anyway. Every follow-up was also cut at B3, so a
   calibration rule that is only advisory did not hold.
2. **Contradicts:** "scrutiny concentrates where damage lives". With B3 everywhere, the full ladder
   (independent tests, two reviews, an operator packet) ran on fixture code, refactors and lint
   tooling. Review roles took 56% of agent time.
3. **New finding:** an adversarial lens has no stopping rule. 84% of its findings were low or
   info. Turning lows into tickets at the parent's B3 level made a loop that doesn't converge:
   each follow-up's lens found new lows, and chains ran 5 to 9 tickets deep on one surface.
4. **New finding:** the process-surface rule (B3) covered tooling the project builds for itself.
   One guard test was re-ticketed five times for precision.
5. **Hypothesis, operator agreed:** a host-level OS sandbox around the candidate code is an
   open-ended surface. The effort's threat model treats its own implementer's output as a
   hostile adversary, which made that surface the largest single chain. v4.9, filed one day
   earlier, covers the pattern; it arrived after the chains had run.
6. **Hypothesis, operator agreed:** the project's own gate grew into a product. Its suite was
   4.6× the source, and its 25-minute verify ran on every round.

## Amendments (v4.10, operator-agreed 2026-11-18)

1. **The B3 share cap binds** at A2 and for later tickets. Above ~20%, the graph names the
   concrete damage per B3 ticket, and the operator ratifies the share explicitly before the build
   starts. Evidence: items 1 and 2.
2. **Review findings: severity decides what moves.** High and medium findings route fixes. Low
   and info findings are accepted residuals by default, batched into at most one follow-up per
   surface per milestone, cut at the blast level of its own diff. Evidence: item 3.
3. **Checks a project builds for itself are B1** unless they decide a gate. Loosening the verify
   command list stays B3. Evidence: item 4.
4. **Verify budget:** a full verify over ~10 minutes is split into a fast tier for every round
   and a full tier at `integrate`. Evidence: item 6.
5. **Critical path first:** hardening and follow-ups wait behind the milestone's demo path,
   unless a high finding names a realistic threat. Evidence: the metrics as a whole.

The threat-model re-rating (item 5) is a project decision, recorded in the effort's own ledger.

## Considered and left unchanged

- Independent tests-first and a decorrelated lens for the real B3 core.
- Landing only through `integrate`.
- The decision ledger.
- v4.9's patch-class check. It is complementary: v4.9 catches recurring classes, and v4.10 stops
  low findings from feeding them.

---
name: retro
description: Compile an effort's measured evidence — led by the headline metric of unattended tickets merged per operator intervention, plus routing/usage ledgers, gate outcomes and waivers, size-estimate audits, and operator outcome reports — into an evidence memo with proposed process amendments, filed in the process-authority repo. Use at milestones, at effort end, or whenever outside evidence arrives (an interview, an incident, a model release); also the required path for promoting a model tier or for reviewing a stated-vs-enforced style rule.
compatibility: Works in any agent harness. Needs read access to the effort repo's ledgers and, to file memos, the process-authority repo the operator designates.
license: MIT
---

# retro — the process is under the same regime as the code

Measured, ledgered, amended on evidence. Nothing about the pipeline is
tenured; nothing about it changes on vibes either. The retro is the one
sanctioned channel from "we observed X" to "the process now does Y."

## When

- Milestone boundaries and effort end.
- **Any time an outcome report arrives** — external evidence has no schedule:
  a job interview probing a learning goal, a production incident, a vendor
  model release, a benchmark superseded. File it when it happens
  ([references/outcome-report-template.md](references/outcome-report-template.md)).
- When anyone proposes a tier promotion (this is the only path).
- When a validation trial has pre-registered bars: check every measured
  value against its bar and call out any breach explicitly — a breach is
  itself a valid, expected finding, never an omission to paper over.

## Inputs (compile, don't recollect)

Every input names the source it was pulled from, so a retro is compiled from
artifacts, not recollected from memory. Six source kinds recur across the
metrics below:

- **Ledger event** — the harness's per-ticket event log (one JSONL record
  appended per attempt): model, tag, size, declared and effective blast,
  attempts, verify result, tokens (when known), wall-clock, batch/worktree
  launches. Feeds per-(tool, model, tag, size) verify pass rates.
- **Integrate log** — the integration script's per-attempt output: style-lint
  warnings, blast escalations, megafile flags, conflict records,
  operator-hold events.
- **Handoffs** — each worker's completion report: deviations, decisions
  needed, findings, field-guide proposals.
- **Git** — commit and branch history: merge commits, the decision ledger's
  diffs (reopened or superseded rows), rule-exception annotations (grep for
  them), field-guide and style-rule commit history, ticket header fields.
- **Operator report** — sittings and turns, review minutes, escaped defects
  found after merge, and outcome reports filed since the last retro.
- **Polish log** — the milestone's post-demo fix log: each operator-reported
  symptom, its regression case, whether it landed planner-direct or as a
  ticket, and any fix that broke a neighbouring variant. Every polish entry is
  an escaped defect and an unplanned intervention.
- **Session transcript** — when the harness or agent environment exposes a
  timestamped record of the operator/agent session (a steering sitting, a
  light-mode build), compile the per-stage timing table and the operator
  interaction log (below) from it **by default**, not by estimate: for each
  stage, its wall-clock span, the time the agent was actively working
  (including waiting on background workers) vs. the time spent waiting on
  the operator, and one row per operator turn (time, stage, gist, class,
  what prompted it, whether it was avoidable). A milestone with no exposed
  transcript — no session log, a harness that doesn't record one, a gap the
  operator worked outside any logged session — leaves the timing table and
  interaction log `not recorded`, same as any other missing source; do not
  reconstruct either from memory.

Also compile: gate outcomes and every waiver, named always (git: decision
ledger rows; handoffs); size audits, estimated vs. actual per ticket (git:
ticket header; ledger event: actual wall-clock/attempts); evidence-corpus
recheck results due this cadence, warrant × decay (the effort's evidence
corpus, when one exists).

A source that doesn't exist for this effort — no ledger, no integrate log,
no evidence corpus — leaves that cell `not recorded`, never a value
estimated from memory. An empty cell is honest input; a guessed one defeats
the point of compiling.

## Output — the evidence memo

Fill [references/evidence-memo-template.md](references/evidence-memo-template.md)
and file it in the process-authority repo's `docs/evidence/` (dated,
effort-named) — one memo per retro. It opens with the **headline metric**
(unattended tickets merged per operator intervention — the delete-or-keep
signal for whether the build half is pulling its weight), carries the full
metrics table with a bar and a source per row so a later reader can
re-derive every number, and then states: what was measured · what it
contradicts or confirms in the current process · **proposed amendments,
each citing its evidence** · what was explicitly considered and left
unchanged. When a session transcript is available, the memo also carries
the per-stage timing table and the operator interaction log, both compiled
from it, not estimated; when none is available both are `not recorded`.

Amendment classes and their rules:
- **Tier changes**: the ledger auto-DEMOTES during an effort; PROMOTIONS are
  proposed here with the measured record and land only on operator sign-off.
  Cross-tier auditions (N tickets one tier up to gather promotion evidence)
  are proposed here too — never bandit-driven.
- **Gate recalibration**: a passed gate that didn't transfer (per an outcome
  report) is evidence about the GATE; propose the redesign, cite the report.
- **Rule lifecycle**: a stated style rule with no reviewed finding and no
  lint hit across two milestones is a pruning candidate. A rule a linter can
  now decide moves into the enforced layer and leaves the prose. Many
  logged exceptions against one rule says the rule is mis-drawn, not that
  workers are undisciplined — propose a redraft, citing the exception
  count. A new stated rule enters only after a repeated mistake surfaces in
  the field guide — cite the handoffs that show the pattern.
- **Pipeline amendments**: land as commits to the authority doc citing the
  memo. The repo's history is the ledger.

The memo is a proposal document. The operator adjudicates; the agent never
amends the process unilaterally.

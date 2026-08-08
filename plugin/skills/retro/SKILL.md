---
name: retro
description: Compile an effort's measured evidence — routing/usage ledgers, gate outcomes and waivers, size-estimate audits, and operator outcome reports — into an evidence memo with proposed process amendments, filed in the process-authority repo. Use at milestones, at effort end, or whenever outside evidence arrives (an interview, an incident, a model release); also the required path for promoting a model tier.
compatibility: Works in any agent harness. Needs read access to the effort repo's ledgers and, to file memos, the process-authority repo (one-punch or the operator's equivalent).
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

## Inputs (compile, don't recollect)

- The effort's routing/usage ledger: per-(tool, model, tag, size) verify pass
  rates, spec-verdict findings, costs, turns, escalations.
- Gate outcomes: passes, fails, retests, and every waiver (named, always).
- Size audits: estimated vs. actual per ticket.
- Evidence-corpus recheck results due this cadence (warrant × decay).
- Operator outcome reports since the last retro.

## Output — the evidence memo

One memo per retro, filed in the process-authority repo's `docs/evidence/`
(dated, effort-named), containing: what was measured · what it contradicts or
confirms in the current process · **proposed amendments, each citing its
evidence** · what was explicitly considered and left unchanged.

Amendment classes and their rules:
- **Tier changes**: the ledger auto-DEMOTES during an effort; PROMOTIONS are
  proposed here with the measured record and land only on operator sign-off.
  Cross-tier auditions (N tickets one tier up to gather promotion evidence)
  are proposed here too — never bandit-driven.
- **Gate recalibration**: a passed gate that didn't transfer (per an outcome
  report) is evidence about the GATE; propose the redesign, cite the report.
- **Pipeline amendments**: land as commits to the authority doc citing the
  memo. The repo's history is the ledger.

The memo is a proposal document. The operator adjudicates; the agent never
amends the process unilaterally.

---
name: learning-gates
description: Gate implementation progress on the operator's measured, verified learning. Types each learning goal (conceptual understanding, tradeoff mastery, skill acquisition, gap-closing), attaches the right assessment mechanism, and enforces gates as tracker-native blocker tickets that resolve only via committed assessment artifacts. Use when INTENT.md declares learning goals, when cutting tickets in a learning-tagged domain, or when running any assessment, drill, or waiver.
compatibility: Works in any agent harness. Blind grading requires the ability to start a fresh session or context without the coaching history; where unavailable, note the limitation on the assessment artifact. Voice mocks degrade to text.
license: MIT
---

# learning-gates — understanding is granted by artifacts

The failure this skill exists to prevent: the operator watches competent
decisions happen, feels the learning, and learns ~10% of it. "I feel like I
learned X" is a completion claim, and completion claims are worthless without
artifacts — the same rule the pipeline applies to agents, applied to the human.

## Conversation surface

Tables and taxonomies in this file are YOUR reference, never pasted at the
operator. Goal-typing and gate-setting happen conversationally: one question
at a time, threading from answers; menus and mechanics surface only when a
concrete choice needs them.

## Goals are typed; the mechanism follows the type

| Type | Primary mechanism | Gate |
|---|---|---|
| **Conceptual understanding** | Build against it + write the explainer (when intent includes publishing, the article section IS the artifact) | Blind-graded draft + short spoken/written Q&A |
| **Tradeoff mastery** | Operator OWNS the project's relevant harness (e.g. an eval matrix): designs it, predicts results before each run, interprets divergence — reality is the answer key | Defend the tradeoff writeup to a blind grader; capstone artifact per intent |
| **Skill acquisition (near-zero start)** | Operator-implements tickets on a difficulty gradient (start low/medium code-complete, climb), agent as reviewer/pair | TREND gate: N merged tickets with review findings-per-ticket declining |
| **Gap-closing against a bar** | Baseline mock → gap map → drill blocks → transfer re-measure | Re-measure at/above the pre-registered bar, blind-graded, on a DIFFERENT problem class |

**Prediction-first** is the unifying primitive wherever the project supplies
an answer key (eval runs, game days, incident behavior): the operator writes
the expected outcome before observing; the delta is the curriculum. Cheap,
project-native, ungameable.

## The gating model

- **Assessment tickets (`L-NN`)** are ordinary tracker tickets; implementation
  tickets in learning-tagged domains carry `Blocked by: L-NN` like any other
  edge. The frontier does not move past an unresolved gate.
- An L-ticket resolves ONLY via a **committed assessment artifact**: the
  pre-registered rubric and bar ([references/rubric-template.md](references/rubric-template.md)),
  the transcript or work product, and a grade at/above bar.
- **Bars**: the TARGET is set at intent time and is binding; the RUBRIC is
  written per milestone, always before the assessment. **Budget**: N
  operator-implements tickets per effort, tracker-visible.
- **Grader separation**: the assessment is graded by a fresh session blind to
  the coaching history. Coach and examiner are never the same context.
- **Transfer-only**: never assess on the drilled material itself.
- **Load-bearing forms are strongest** — gates that ARE work the project
  needs: operator-authored test suites verified by seeded-defect mutation
  (agent plants N known violations; the suite must catch ≥ k), prediction-first
  game days, operator runbooks verified by literal execution, operator tickets
  on the tagged domain's critical path (circumvention then cannot produce a
  finished implementation at all).
- **Socratic inversion** in decision sessions for tradeoff-mastery domains:
  ask the operator's position before showing the recommendation — a drill
  disguised as work. (This deliberately un-compresses those domains.)

## The honest limit — waivers, never fakes

The operator owns the machine; no gate survives a determined file edit. The
guarantee is therefore: **the agent never fakes a pass** — no artifact, no
resolution — and bypass exists only as a loud, recorded waiver: a committed
`WAIVED WITHOUT PASSING` entry in LEARNING.md
([references/LEARNING-template.md](references/LEARNING-template.md)), which the
agent names in every subsequent milestone summary. Silent drift becomes
explicit self-override.

## Anti-death-spiral

Fail → targeted drills → retest on a DIFFERENT task (never the same test).
Two fails → forced explicit choice: waive on the record, or descope the
milestone. Gates are sized to what the milestone actually exercised — a gate
demanding mastery the work hasn't yet touched teaches only resentment.

Outcome reports (an interview months later, a real incident) are retro input:
they calibrate the gate designs themselves. A passed gate that didn't transfer
is evidence about the gate, and it gets ledgered like everything else.

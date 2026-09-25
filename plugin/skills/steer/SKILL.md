---
name: steer
description: "Front door for every effort. Steers a project from intent to merged milestones: H1 intent sitting; A1 parallel agent lanes (risk spikes, a walking skeleton or prototype — or, brownfield, a code survey with a blast-map proposal and characterization tests — prior-art reference dossiers with reuse modes, and a lake-first retrieval-grade evidence pass tied to open forks and risks); H2 decision memo; A2 compile (decision ledger, tickets with blast levels, isolate-the-blast, code-style and blast-map install, ticket-graph veto window); build handoff to the parallel worker harness; H3 milestone closure, report, fast-decay recheck and merge. `steer resume` reports where an effort stands from its on-disk artifacts. Use when beginning any new project-sized effort or milestone, and when returning to an effort after any gap (\"where were we?\"). The agent may propose steer when the operator describes project-sized work, but never enters it without the operator's yes."
compatibility: "Requires git and shell access. Composes the intent, decision-memo, blast-radius, code-style, field-guide, spike, retro and worker-harness skills, the mattpocock-skills plugin (wayfinder, prototype, research, grilling, to-spec, to-tickets, code-review) and evidence-kit; detects each and prints install guidance when missing. Runs A1 lanes as concurrent background agents where the harness offers them, sequentially otherwise."
license: MIT
---

# steer — agents run ahead, the operator ratifies

Agents do discovery in parallel before the operator is asked anything
evidence could inform; the operator spends attention in a few dense sittings
on forks only; a planner that never implements turns ratified decisions into
explicit tickets; a harness builds them; scrutiny at every stage follows
blast radius.

This skill owns the **sequence and the artifacts between stages**. Each stage
invokes the skill that owns its content — never restate that skill's rules
here or in a brief; name it and invoke it.

| Stage | Who | Invokes | Leaves on disk |
|---|---|---|---|
| Preflight | agent | — (this skill) | prerequisites report |
| **H1** intent | operator sitting | `intent` | `INTENT.md` |
| **A1** fan-out | ≤4 agents | `spike`, `prototype`, `blast-radius`, `field-guide`, `research`, evidence-kit, `wayfinder` (planner's private map) | lane briefs, findings, dossiers |
| **H2** decisions | operator sitting | `decision-memo` (+ `grilling` through it) | memo, ledger rows, ratified blast map |
| **A2** compile | planner | `to-spec` (optional), `to-tickets`, `blast-radius`, `code-style`, `field-guide` | tickets, blast map, style section, ticket graph, integration branch |
| **Build** | harness + workers | `worker-harness` | merges, handoffs, harness ledger |
| **H3** milestone | operator sitting | `code-review`, evidence-kit, `decision-memo`, `retro` | milestone report, mini-memo, retro memo |

## Entry and ceremony

- New effort or new milestone → `steer`. Returning after any gap → `steer
  resume` (below). That is the whole entry surface.
- **Ceremony is model-proposable, never model-enterable.** `steer` itself is a
  ceremony: propose it ("this looks like a project-sized effort — run
  steer?") and wait for the operator's yes. The same holds for every opt-in
  it may surface: the private overlay (only when an intent answer signals a
  private motive — `intent` decides when to offer it), a per-effort evidence
  corpus (evidence-kit scaffold; only when the effort has a lasting stake in
  the answers), `learning-gates` (only when INTENT.md names a learning goal),
  and `contract-review` (only when the operator points it at a contract).
  Propose with a one-line reason; enter only on a yes.
- Some harnesses reserve certain composed skills for operator invocation.
  When a stage reaches one, ask the operator to invoke it by name at that
  point; never substitute a paraphrase of its steps.
- Name the model on every agent dispatch — lanes, reviewers, workers. A
  dispatch that silently inherits the session's model is a defect.

## Effort layout

Artifacts are the memory; stages read them, never transcripts. Defaults
(an effort may relocate any of them once, in its planner scratchpad):

```
INTENT.md                          intent
docs/decisions.md                  decision ledger (decision-memo filing)
docs/blast-map.md                  blast map (blast-radius install)
docs/field-guide/index.md          field guide (field-guide)
AGENTS.md → "Code style" section   code-style Layer 1
.scratch/<effort>/
  planner-scratchpad.md            planner state — rewritten, never appended
  issues/NN-slug.md                tickets (to-tickets, local tracker)
  handoffs/NN.md                   worker handoffs
  milestones/<m>/
    a1/<lane>-brief.md             lane brief (filled from references/)
    a1/<lane>-findings.md          lane output (risk lane: one pair per R-n)
    a1/dossiers/<ref>.md           prior-art dossiers
    memo.md                        H2 decision memo (decision-memo template)
    ticket-graph.md                A2 veto-window summary
    report.md                      H3 milestone report
    h3-memo.md                     H3 mini-memo (decision-memo, when forks arose)
```

Milestones are named `m1`, `m2`, …; the first milestone's memo is the H2
memo. Worker-harness keeps its own ledger and configuration where that skill
puts them; evidence holdings go where evidence-kit puts them.

## Preflight — prerequisites and freshness

Detect, don't assume. For each item, report present / missing / stale /
unchecked, and print exact remediation for anything not present and current —
never fail silently or degrade without saying so. Example commands per
harness: [references/prerequisites.md](references/prerequisites.md).

1. **git repo** on `main`. If absent, offer `git init` (default branch
   `main`).
2. **Composed skills present:** every sibling skill the stage table names,
   the mattpocock-skills plugin (probe for `wayfinder`, `to-tickets`,
   `grilling`), and evidence-kit (needed at A1; its absence degrades the
   evidence lane, see its brief). Missing → print the harness's install
   command.
3. **Tracker configured:** the mattpocock skills expect a configured issue
   tracker. If the repo has none, run `setup-matt-pocock-skills`; the
   local-markdown tracker is the default, so the repo stays self-contained.
4. **Freshness, not just presence.** Where the harness exposes installed
   plugin or skill versions and the source or marketplace is reachable,
   compare them for this plugin and every composed dependency. Anything stale
   → say so now, print the exact update commands, and remind the operator
   that updates apply at session start — restart at minute zero, not
   mid-sitting. A version check that cannot be performed in this harness is
   reported as **unchecked**, never assumed current.
5. **Worker harness runnable** (checked now, needed at Build): the
   `worker-harness` skill's own requirements. Missing → note it; the build
   degrades to sequential tickets in the session.

## H1 — intent sitting

Invoke `intent`. It runs the one sitting and writes `INTENT.md`; steer adds
nothing to its questions. Decide greenfield vs brownfield from the answers:
brownfield when the effort changes an existing codebase. Steer consumes two
of its sections downstream — **Catastrophes** (seed of the blast map) and the
**Risk register** (what A1 spikes) — plus the operator's known prior art
(A1's first research targets).

## A1 — parallel fan-out

Before launching, write one brief per lane from its reference into
`milestones/<m>/a1/`. A brief is the whole instruction set for a fresh agent:
question(s), inputs, the skill it invokes, timebox, output path, stop rule.

| Lane | Greenfield | Brownfield | Brief |
|---|---|---|---|
| **Risk** | one `spike` per top-ranked `R-n`, cheapest first | same | [lane-risk.md](references/lane-risk.md) |
| **Shape** | walking skeleton or `prototype` for the biggest does-this-feel-right question | code survey of the touched area + blast-map proposal | [lane-shape.md](references/lane-shape.md) |
| **Safety net** | — | characterization tests at the seams to be changed | [lane-safety-net.md](references/lane-safety-net.md) |
| **Prior art** | reference dossiers, reuse mode each | same + how comparable codebases structured the changed area; the repo's own history counts | [lane-prior-art.md](references/lane-prior-art.md), [reference-dossier.md](references/reference-dossier.md) |
| **Evidence** | evidence-kit retrieval-grade pass, lake-first, questions tied to forks and risks | same + upstream and issue history for the touched area | [lane-evidence.md](references/lane-evidence.md) |

**Lane budget.** At most four agents run at once, every lane timeboxed.
Slots are filled in this order: risk spikes (any risk whose failure would
land in a B3 zone first — those are spiked now, never deferred to build),
then the shape lane (the H2 demo depends on it), then prior art, then
evidence; the brownfield safety net starts once the survey has named the
seams. A lane that finishes frees its slot for the next in order. Without
background agents, run the lanes one after another in the same order.

**Rules.**
- **A kill stops the fan-out.** A spike or lane that hits its kill criterion
  surfaces immediately: stop launching lanes, let running ones write what
  they have, and go to H2 now with the dead assumption first. It is never a
  memo footnote.
- **Files, not messages.** Lanes write findings to their output path and
  never message each other or the operator; the planner reads files.
- **Every research question names the fork or `R-n` it serves**, or it is
  dropped. No open-ended surveys.
- **Blast map draft.** Greenfield: the planner drafts zones from INTENT.md's
  Catastrophes and the skeleton's architecture, per `blast-radius`'s propose
  step. Brownfield: the shape lane's survey proposes it.
- **Field guide seed.** Brownfield: fold the survey's fragile areas and
  working commands into a new field guide via `field-guide`'s seeding
  section. Greenfield: it starts empty.

**Meanwhile, the planner** drafts the decision map privately with
`wayfinder` as its own tool (not one operator session per ticket), resolving
craft decisions on the record as lane results land, and rewrites
`planner-scratchpad.md` with current state after each landing.

A1 ends when every launched lane has written its findings or hit its
timebox (a timed-out lane records what it has and what it would do next).

## H2 — decision sitting

Invoke `decision-memo` for the H2 sitting. Steer's part is the inputs and the
filing around it:

1. Draft the memo at `milestones/<m>/memo.md` from the decision-memo
   template, linking every lane output: skeleton or survey (demo), spike
   transcripts (risk register), dossiers (reuse forks), holdings (evidence
   tiers), the blast-map draft (ratification).
2. Run the sitting as `decision-memo` directs (its altitude rule, its
   adversarial-evidence trigger, its follow-up rounds through `grilling`).
3. After the sitting: the ledger is filed per `decision-memo`; update each
   `R-n`'s Status in INTENT.md's risk register with a link to its evidence;
   record the ratified reuse mode per problem area in the planner scratchpad
   (A2 turns it into `Reference:` fields).

## A2 — compile

The planner turns ratified decisions into an explicit build. In order:

1. **Ledger complete.** Every fork answer and default is a row in
   `docs/decisions.md`. Brownfield: add discovered de-facto decisions
   (status `inferred`) only where a ticket will depend on them.
2. **Spec** via `to-spec` only when the effort is handoff-sized; otherwise
   the ledger plus INTENT.md are the contract.
3. **Tickets** via `to-tickets`, each carrying the header block in
   [references/ticket-header.md](references/ticket-header.md). Tickets are
   explicit enough for a mid-tier worker to transcribe: constraints, numeric
   ranges, acceptance checks as shell commands, worked examples.
4. **Isolate the blast.** Declare every ticket's level and cut B3 cores into
   their own small tickets behind narrow seams, per `blast-radius`'s
   declaring steps; B3 core and its B1 surroundings are always separate
   tickets. Each B3 ticket is a diff the operator will read — keep them few
   and small.
5. **Milestones.** A destination larger than one build batch (rule of thumb:
   more than 15 tickets or more than a day of worker time) splits into
   milestones; cut tickets for the current milestone only.
6. **Install the standing artifacts** (each is a process surface the
   operator owns):
   - the ratified blast map, per `blast-radius`'s install step;
   - the `Code style` section in `AGENTS.md`, per `code-style` Layer 1 —
     brownfield adapts it to existing idioms with lint ratcheted; the first
     tickets wire Layer 2 into the project's verify commands;
   - the field guide file from `field-guide`'s template (seeded or empty);
   - the worker harness and its configuration, per `worker-harness`.
7. **Cut the integration branch** `integrate/<effort>` from `main`. `main`
   changes only at H3.
8. **Ticket-graph summary — a veto window, not a gate.** Write
   `milestones/<m>/ticket-graph.md` per
   [references/ticket-graph-summary.md](references/ticket-graph-summary.md)
   and show it; it is also the breakdown review `to-tickets` asks for.
   Building starts unless the operator objects: in an attended session, on
   the operator's next reply unless it raises an objection; when the
   operator has said they are stepping away, immediately — operator stop
   stays available throughout.

## Build — hand off to the harness

Start the harness's parallel run as a background process from the planner
session (`worker-harness`: `run --parallel N`, default 4) and let it notify
the session when it stops. Scheduling, integration checks, blast escalation,
salvage and stop conditions are the harness's; the planner never schedules
by hand. Without background processes, run it in the foreground; without the
harness, work tickets one at a time in dependency order.

**Between runs** — steering happens here, never mid-run. When the run stops:

1. Read the handoffs as files. Worker transcripts never enter the planner's
   context.
2. `Decisions needed:` — decide at the `decision-memo` altitude: a craft
   question becomes a ledger row and the parked ticket is unparked; a fork
   waits for the operator (now if it blocks the frontier, else the H3
   mini-memo).
3. Licensed breakage (`BREAKING(D-NNN)`) — accept (ledger row goes active,
   dependents become follow-up tickets) or reject (the attempt fails with a
   note).
4. B3 changes held for the operator — surface each review packet; the
   operator reads the diff and approves or rejects; the harness merges on
   approval.
5. Field-guide proposals — curate via `field-guide`.
6. Recut, split or add tickets the handoffs call for (a megafile flag
   becomes a decompose ticket that blocks further work on that file).
7. Rewrite `planner-scratchpad.md`, then relaunch.

Operator actions here are interventions; the harness ledgers them so
`retro` can compute the headline metric.

## H3 — milestone closure, report, merge

When the run stops with the milestone's frontier empty:

1. **Closure.** Re-run every merged ticket's acceptance checks against the
   integration head (per-merge verify runs the suite, but ticket-specific
   checks ran only once). Any failure → a fixer ticket and back to Build;
   H3 waits until closure is green.
2. **Milestone review.** mattpocock `code-review` over the milestone diff
   (integration head against `main`), its Standards axis carrying
   `code-style`'s Layer 3 rubric and the milestone's accumulated lint
   warnings; every B2 and B3 diff reviewed individually. Findings batch into
   one fixer ticket; a finding inside a B3 zone becomes its own B3 ticket.
3. **Fast-decay recheck.** Run evidence-kit's recheck over the fast-decaying
   facts the build rests on (API pricing, vendor behavior, library versions).
   A changed fact becomes a fork or a ticket before acceptance.
4. **Milestone report** at `milestones/<m>/report.md` from
   [references/milestone-report.md](references/milestone-report.md).
5. **The sitting.** Demo the milestone running; walk the report; forks
   unlocked by building go through `decision-memo`'s H3 mini-memo. The
   operator accepts or redirects and decides the merge to `main`; perform
   the merge only on that decision.
6. **Retro.** Invoke `retro` for the milestone.
7. **Next milestone.** A1 again with only lanes for new risks → H2 with only
   newly visible forks → A2 → Build → H3. A new planner session per
   milestone is normal; `steer resume` rebuilds state from disk.

## `steer resume` — where is this effort?

Read `planner-scratchpad.md` first, then derive the stage from what exists —
the latest milestone directory decides. Report the stage, the evidence for
it, and the next action; never guess from memory.

| On disk (latest milestone) | Stage | Next action |
|---|---|---|
| no `INTENT.md` | not started | propose `steer` |
| `INTENT.md`, no `a1/` briefs | H1 done | A1 |
| briefs with missing findings | A1 in flight | check which lanes finished; relaunch the rest in slot order |
| a findings file reports a kill | A1 stopped | H2 now, dead assumption first |
| findings complete, `memo.md` absent or unratified | H2 due | compile memo, sitting |
| memo ratified, tickets for this milestone absent | A2 | compile |
| `ticket-graph.md`, no harness ledger events for its tickets | veto window | start the run unless objected |
| harness ledger has events | Build | invoke `worker-harness` `resume` and relay its report |
| frontier empty, no `report.md` | H3 due | closure, review, report |
| `report.md` without an operator decision | H3 sitting pending | the sitting |
| `report.md` with merge decision | milestone closed | next milestone, or effort done |

Alongside the stage, list: risk-register rows still open, forks awaiting the
operator, parked tickets with their `Decisions needed:`, B3 diffs awaiting
review, prerequisites last reported stale or unchecked, and evidence due for
recheck.

# one-punch v2 — decisions by execution, contracts by compilation

**Status:** LIVING copy — this document is one-punch's design authority.
**Date:** 2026-07-27. **Supersedes:** the v1 pipeline (`one-liner → PRD → tech-plan →
plan-review → runner → verification`), preserved in git history at `762edda` and
summarized in the provenance section below. v1's frozen capstone remains at
`outrigger docs/design/one-liner-to-code-complete.md@3ebe595`; outrigger is untouched
by this redesign and its runner references are historical.

## 0. Why v2 (the evidence that forced it)

v1 was built for **headless fleet execution by cheap, context-free implementers**. That
premise demanded total specs — plans that need no judgment — which relocated
implementation-grade debugging into prose, the one medium with no interpreter. The
retrieval-fetcher plan (evidence-kit, 2026-07-25→27) measured the consequence: **four
adversarial review rounds, 79 confirmed findings applied, five amendments — and every
amendment minted new defects at ~0.5–0.8× the rate it fixed them**, because fixes were
new unverified claims about an external system, written in English. The blockers each
round sat in the previous round's fixes. Two skill retrofits mid-flight (probe ledgers,
fence execution) each arrived exactly one round after the defect class they would have
caught. Root cause, compressed: *correctness of executable behavior was being
established through prose review instead of through execution.* Full analysis: the
5-whys in the evidence-kit session records; the four review reports in
`evidence-kit docs/plans/2026-07-25-retrieval-fetcher/plan-review-report-round{1..4}.md`.

Two premise changes, both operator-ratified 2026-07-27:

1. **The AFK-fleet goal is dead.** one-punch designs for a HITL operator.
2. **Prototypes beat specs.** A question about how anything external behaves is
   answered by code that runs, never by prose that asserts.

v2 therefore composes the **mattpocock-skills** plugin (installed from
`github.com/mattpocock/skills`; local clone `~/repos/skills`) — wayfinder, grilling,
domain-modeling, prototype, research, to-spec, to-tickets, tdd, code-review — and adds
only two small deltas of its own. We compose rather than paraphrase: paraphrases drift.

## 1. Principles (v2)

1. **Mechanism truth comes from execution, never prose.** A claim about an external
   system enters a contract only via a spike transcript. (v1's probe apparatus,
   collapsed to its useful residue.)
2. **Decisions are serialized, one at a time, with the human.** No batch ratification
   of documents that resolve twenty interacting questions at once — that is where v1's
   amendment churn lived.
3. **Contracts are compiled, not interviewed.** A spec is the synthesis of decisions
   already resolved (and spike-verified where behavioral) — written at the end of
   deciding, not the start.
4. **Fog of war.** Don't pin what can't be seen yet. The retrieval-fetcher plan pinned
   robots-failure semantics before any code existed to say what was pinnable; three
   rounds paid for it.
5. **Verification cost scales with the change, not the artifact.** Per-slice TDD and
   two-axis diff review, never whole-artifact re-review rounds. Prose artifacts get at
   most one adversarial pass, ever.
6. **Instruments hold their seats on current evidence.** Anything carried over from v1
   is provisional and carries an explicit re-earn test in its own file. v1's measured
   wins do not transfer across a medium change.

## 2. The pipeline

All stages HITL unless marked. Tracker-backed (run `/setup-matt-pocock-skills` once per
repo — tracker, triage labels, docs location).

| Stage | Instrument | Notes |
|---|---|---|
| **Destination** | `/grilling` (+ `/domain-modeling`) | Name what *done* looks like — a working tool, a decision, a corpus change, a spec-for-handoff. Minutes, not hours. Scope is fixed here. |
| **Decision map** | `/wayfinder` | Decisions as tickets, one resolved per session. Fog stays in Not-yet-specified. Out-of-scope is a ledger, not a fence built upfront. |
| **— resolve: product judgment** | `/grilling` | The human's decisions, one question at a time, recommendation attached. |
| **— resolve: behavior/substrate** | **`/one-punch:spike`** or `/prototype` | Executed code answers it. Spike = AFK fact-finding (what is true); prototype = HITL reaction (does this feel right). |
| **— resolve: external facts** | `/research` (subagent) | Primary sources, findings as a cited file. |
| **Contract** (only when the effort is big enough to hand off or gate) | `/to-spec` | Compiled from Decisions-so-far. Decisions and seams, **no mechanism**: no file paths, no code except spike/prototype-born snippets trimmed to the decision-rich parts. Small efforts skip straight to tickets. |
| **Contract review** (optional, on-demand) | **`/one-punch:contract-review`** | Demoted from v1's plan-review. One round, contract surfaces only; mechanism-shaped findings convert to spike tickets, never prose amendments. Carries its own delete-if re-earn test. |
| **Tickets** | `/to-tickets` | Tracer-bullet vertical slices, blocking edges, quiz-the-human approval. Wide refactors go expand–contract. |
| **Build** (per ticket, frontier order) | `/implement` + `/tdd` | Seams pre-agreed with the human; red→green; typecheck often; full suite once at the end. |
| **Review** (per ticket or branch) | `/code-review` | Two axes — Standards and Spec — parallel subagents, reported side by side. The human takes the merge decision. |

**What replaced what:** brainstorm+PRD interview → destination + decision map (the PRD
is now `/to-spec` output, compiled late, optional). tech-plan → decision map + spikes +
to-tickets. plan-review → contract-review (demoted). The runner, tasks.json contract,
status files, determinacy-tier routing, oracle stage, mock suite → tickets + TDD + diff
review + the human. Per-ticket acceptance criteria absorb the role machine checks
played; where shell-runnable checks already exist (the retrieval-fetcher plan's 140)
they paste into tickets nearly verbatim.

## 3. one-punch's own two skills

- **`spike`** — settle a substrate or design question by executing throwaway code;
  output is a probe transcript (command · trimmed output · versions · date) recorded on
  the decision ticket. The one hard rule inherited from v1's measurements: *a claim
  about how an external system behaves enters a contract only via a spike transcript.*
- **`contract-review`** — adversarial divergence-pair review of a *compiled contract*,
  scoped to contract surfaces (schemas, one-way doors, error models, invariants, stated
  deviations). Explicitly not a pipeline stage; the operator points it at an artifact,
  once. Its file carries the re-earn clause: two consecutive invocations with zero
  findings the operator judges worth fixing → delete the skill.

## 4. Human-touchpoint policy

The human appears at: destination naming; every grilling answer; prototype reactions;
seam agreement before TDD; ticket-breakdown approval; contract ratification when a
contract exists; merge decisions. This is more touchpoints than v1's four gates and
that is the point — v1 concentrated human attention into rare, heavyweight batch
ratifications of large prose artifacts, which is exactly where its defects pooled.
Frequent, small, one-question decisions are cheaper per unit of attention and leave no
25KB artifact to re-review.

## 5. Provenance (v1, and what its evidence still supports)

v1's outrigger arc measured real things that remain true and are inherited: spec
ambiguity survives every downstream instrument (hence grilling one question at a time,
and contracts that record decisions rather than prose that invites readings);
completion claims are worthless without artifacts (hence TDD red/green evidence and
diff review); conventions live in CLAUDE.md or they are enforced on no one. What v1's
evidence does **not** support is total-spec authoring: its one end-to-end success
(goodhart-sim, 2026-07-17, $31.32) was a small greenfield build; the first
framework-coupled plan produced the four-round record above. The v1 pipeline text,
runner, and evidence appendix: git history `762edda` and earlier.

## 6. First trial — completed 2026-07-27, successful

The retrieval-fetcher (evidence-kit) ran through v2 end to end: 9 tickets
(local-markdown tracker, `.scratch/`), every one red→green TDD, **104 tests, zero
review rounds during the build**, ending in a live run committed to the private lake
(4 hosts, 8 attempts, all 200 first try, politeness verified from the manifest and
logs rather than asserted). Tickets 03–09 landed in a single session.

What the trial establishes, and what it does not:

- **Confirmed:** execution is the only competent reviewer of mechanism. The build
  surfaced two substrate facts no prose round could have found — a graceful SIGINT
  drains scrapy's downloader slot queue (so a small-seed interrupt leaves nothing to
  resume), and scrapy's exact-`3.0s` pacing makes a `>= 3.0` wall-clock assert a coin
  flip (measured 2.9992s). Both were found and fixed inside one red/green cycle.
- **Confirmed:** the `contract`-tier annotation does real work. The one ticket so
  tagged (the robots seam) required reading the installed source, exactly as the tag
  warned; the code-complete tickets transcribed with zero divergence.
- **Caveat, stated plainly:** the trial ran on a pre-paid spec — the v1 plan at its
  final amended state, i.e. ~40 spikes' worth of probed facts and worked examples.
  It validates the back half (tickets → TDD → review). The front half (destination →
  decision map → compiled contract, from a cold start) is untested until the next
  fresh effort.
- **Untriggered:** `contract-review` was never invoked — nothing new was
  contract-shaped. Its re-earn clause stands at zero invocations, neither passed nor
  failed.

## 7. Ticket craft inherited from v1 (earned in the trial)

These v1 spec conventions were used ticket-by-ticket in the trial and pulled their
weight; they are v2's house style for ticket bodies, applied by whoever writes tickets
(they are deltas *on top of* `/to-tickets`, not a replacement for it):

1. **Determinacy annotation.** Tag a ticket `code-complete` (the spec contains the
   code; implementation is transcription + testing) or `contract` (pinned behavior,
   the seam must be read from the installed substrate at build time). The tag is
   advice to the implementer, not routing — v1's model-routing use is dead.
2. **Acceptance fences that cannot rot.** Every test promised in prose is gated by a
   name-grep in the ticket's checks; every negative grep is paired with a `test -f`
   on its target so it can never pass vacuously against a path that stopped existing.
3. **Error models pin message *substrings*, never whole sentences** — exact-message
   asserts reject correct rephrasings; substring pins keep oracle and implementation
   from diverging.
4. **Worked examples carry exact values** and are written to be lifted into tests
   verbatim. A placeholder that matches two structurally different values is a
   defect in the ticket.
5. **Repo conventions are numbered and quotable** (the repo's CLAUDE.md); a
   convention that lives only in a ticket is requested of one implementer and
   enforced on none.

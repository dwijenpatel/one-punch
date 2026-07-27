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

## 6. First trial

The retrieval-fetcher (evidence-kit) runs through v2 end to end as its first live
trial: destination → decision map (most decisions already resolved and spike-verified
by the v1 rounds — the map imports them as closed tickets rather than re-litigating) →
tickets → TDD build → two-axis review. The trial's honest question is whether the back
half (tickets/TDD/review) reaches merged, oracle-quality code at a fraction of v1's
review spend.

# one-punch

**Decisions by execution, contracts by compilation.** A thin, HITL pipeline layer over
the [mattpocock-skills](https://github.com/mattpocock/skills) plugin: decisions are
resolved one at a time (grilling · spike · prototype · research), contracts are
compiled from resolved decisions rather than interviewed into existence, and builds are
tracer-bullet tickets under TDD with two-axis diff review.

```
destination → decision map → [contract] → tickets → TDD build → two-axis review
 (grilling)   (wayfinder;     (to-spec,    (to-tickets) (implement   (code-review;
               grill/spike/    optional)                 + tdd)       human merges)
               prototype/
               research)
```

Authority: [docs/design/pipeline.md](docs/design/pipeline.md). v1 — the total-spec,
AFK-fleet pipeline with its runner and plan-review rounds — is superseded; its record
and the evidence that retired it (four review rounds, 79 findings, one plan) live in
git history at `762edda` and in the pipeline doc's provenance section.

## Install

```sh
claude plugin marketplace add mattpocock/skills
claude plugin install mattpocock-skills@mattpocock
claude plugin marketplace add ~/repos/one-punch
claude plugin install one-punch@one-punch
```

Then `/setup-matt-pocock-skills` once per repo (tracker, triage labels, docs location).

## one-punch's own skills (the deltas)

- **`/one-punch:spike`** — settle how an external system actually behaves by executing
  throwaway code; the probe transcript (command · output · versions · date) is the
  deliverable, recorded on the decision ticket. The rule: external-behavior claims
  enter contracts only via spike transcripts.
- **`/one-punch:contract-review`** — one adversarial divergence-pair pass over a
  compiled contract's surfaces (schemas, one-way doors, error models). On-demand, never
  a stage; one round ever; mechanism-shaped findings convert to spike tickets.
  Provisional — carries a delete-if re-earn test in its own file.

## Status (v0.2)

- ✅ Pipeline v2 ratified 2026-07-27; composes mattpocock-skills 1.2.0.
- ✅ Removed: runner, mock suite, tasks.json contract, tech-plan, plan-review (→
  demoted to contract-review), determinacy-tier routing, oracle stage.
- ✅ First live trial completed 2026-07-27: the evidence-kit retrieval fetcher, 9
  tickets, all TDD, 104 tests, zero review rounds, live run committed. Validates
  the back half (tickets → TDD → review); the front half from a cold start is the
  next trial. Earned v1 ticket craft recorded in pipeline.md §7; contract-review's
  re-earn clause untriggered (no contract was compiled).

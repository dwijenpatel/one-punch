---
name: contract-review
description: "On-demand adversarial review of a COMPILED CONTRACT — a spec, schema, or decision record assembled from already-resolved decisions. Finds sentences on contract surfaces (schemas, one-way doors, error models, invariants, stated deviations) that admit two defensible readings, verifies each finding adversarially, and reports with proposed rewrites. Mechanism-shaped candidates (claims about how an external system behaves, test-harness details, framework internals) are never findings here — they convert to spike tickets. One round per artifact, ever. Use only when the operator explicitly points it at a contract; it is not a pipeline stage."
compatibility: Works in any agent harness; verification passes benefit from parallel or fresh sessions where available, and degrade to sequential fresh contexts otherwise.
license: MIT
---

# contract-review — one adversarial pass over a compiled contract

`/contract-review <contract artifact> [design/decision references…]`

**Provisional — re-earn clause.** This skill is demoted from an earlier pipeline's instrument
whose measured value came from reviewing total-spec plans, a medium the current pipeline no
longer produces. Its seat is not tenured: **if its next two invocations each confirm
zero findings the operator judges worth fixing, delete this skill.** Record each
invocation's outcome (artifact, confirmed count, operator-kept count) in the ledger at
the bottom of this file.

## Scope — contract surfaces only

In scope: schemas and wire shapes; one-way doors (formats on disk, public interfaces,
irreversible layouts); error models and exit contracts; invariants and counting rules;
stated deviations from an upstream authority; worked examples on any of these.

Out of scope, structurally: **anything mechanism-shaped.** A sentence asserting how an
external system behaves, a test-harness recipe, a framework-internal ordering — these
are not reviewable here even when wrong, because prose review is the wrong instrument
for them (measured: four consecutive rounds on one plan, every blocker an executable
falsehood). When a candidate is mechanism-shaped, the finding is **"unexecuted claim on
a contract surface"** and its remedy is a **spike ticket** (see the `spike` skill): the
claim leaves the contract until a spike transcript backs it. Never verify such a claim
by review, and never fix it by rewording.

## The finding contract

Every finding carries a **concrete divergence pair**: two readings of one location,
each stated as executable-style behavior — input → exact output — both defensible,
with no sentence in the contract or its cited decisions resolving them. No divergence
pair, no finding. False positives are the #1 product risk: every surfaced finding
spends operator attention.

## Shape (one round, always lean)

1. **Two independent translators** (identical prompt, no shared context): translate
   the contract surfaces into concrete assertions keyed by (section, contract point),
   choosing the reading they would implement, never flagging ambiguity. Diff the two
   key-by-key; structural disagreements are candidates, and the disagreeing
   translations are their divergence pairs.
2. **One merged finder**: seams between rules (two universal statements that collide on
   a composed case), under-determined observables, worked examples that contradict the
   rule beside them, and unexecuted mechanism claims (→ spike conversion).
3. **Grouped adversarial verification**: one verifier per section group, instructed to
   REFUTE each candidate by quoting the sentence that pins one reading. "The obvious
   reading" refutes nothing; a refutation without a quote is invalid. Keep CONFIRMED;
   keep PLAUSIBLE only when it would flip an acceptance criterion.

## Report, then stop

Write `contract-review-report.md` beside the artifact. Open with a ranked executive
tier (one line per finding, most severe first; flag any needing an OPERATOR DECISION
rather than an editor). Then every confirmed finding in full — location, both readings,
what was checked, a minimal proposed rewrite with a negative example ("this does NOT
mean …") — no cap. End with the negative space: candidates refuted, and by which quote.

**One round is the whole budget.** The operator adjudicates; prose fixes are applied
once by whoever owns the artifact; mechanism findings become spike tickets. There is no
re-review loop — wanting a second adversarial pass is the signal the content is
mechanism and belongs in code, not that the contract needs round two.

## Invocation ledger

<!-- artifact · date · confirmed · operator-kept -->
- a knowledge-base effort's compiled spec · 2026-08-02 · 10 confirmed
  (+1 plausible dropped, 4 spike conversions) · 10 kept and applied. First real
  invocation; re-earn clause: passed round one (kept > 0).
- 2026-07-27 status note (not an invocation): the pipeline's first
  trial (a retrieval-fetcher build) compiled no new contract — its spec was inherited — so this
  skill was never pointed at anything. Clause untriggered; the two-invocation
  count starts at the first real compiled contract.

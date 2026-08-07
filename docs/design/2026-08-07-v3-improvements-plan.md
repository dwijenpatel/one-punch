# one-punch v3 improvements — planning document

**Status: DRAFT — under active review in the 2026-08-07 operator session.**
Nothing here is ratified; the operator finalizes this document explicitly before
any change to one-punch executes. First test case for every change: the "ckb"
restart of the cerebras-knowledge-base effort (which does not begin until this
document is final).

**Evidence base:** the cerebras-knowledge-base effort end to end (design map,
contract review, Qwen/Sonnet build experiments, run-agent.sh harness);
outrigger's frozen capstone (`docs/design/one-liner-to-code-complete.md`) and
exec-loop smoke ledger; mattpocock-skills v1.2.3 upstream.

---

## 1. Intent elicitation (new opening move, before destination)

**Problem observed:** the entire kb effort ran without the operator's actual
goal-stack (portfolio artifact → article series → hiring visibility → possible
buzz adoption). Post-hoc counterfactual: six ratified decisions flip and one P0
vertical (the eval harness) was left in fog. No existing posture asks this
layer: grilling interrogates decisions inside the presented frame; outrigger's
compression optimizes question count and would delete these questions.

**The rule that unifies compression and elicitation — fan-out ordering:**

> A question's value is its fan-out — the number of downstream decisions its
> answer changes. Ask in descending fan-out order; batch-ratify everything with
> fan-out ≈ 1.

**Mechanism:**
- A distinct opening move before destination-naming: a handful of open,
  generative questions — the why behind the why, audiences, success scenarios
  one and two levels up, happy paths, futures not to foreclose.
- Output is a durable artifact (`INTENT.md`, see §2) loaded by every subsequent
  decision session, like the domain glossary.
- New legal move in decision sessions: a recommendation that cannot be grounded
  in recorded intent triggers an intent question, not a preference question.
- Intent is revisited at stage boundaries (map-complete, contract, pre-build).
- Intent licenses out-of-frame proposals (upstream contributions, publication
  timing, article outlines) — always proposed, never executed unilaterally.

**Honest limit, stated in the skill:** elicitation works only with candor; some
intents are private. Intent shared is design leverage; intent withheld is
priced-in risk, not failure. Hence §2.

## 2. Intent privacy (structural, fails closed)

- **Private overlay repo:** `.private/` in the main repo, gitignored in the
  same first commit that creates it, itself a separate git repository with its
  own private origin. Private artifacts (INTENT.md, sensitive research) are
  structurally unpublishable — not tracked by the main repo at all. Both repos
  push to remotes: no laptop SPOF. The main repo is publishable by construction
  (public release = flip visibility; full history intact).
- **Ordering guarantee:** the skill writes the `.gitignore` entry before
  creating any private file. Preflights assert `git check-ignore .private/`.
- **No public remote until publish day** on the main repo.
- **Sanitized derivation rule:** decisions informed by private intent are
  recorded publicly at engineering altitude ("eval promoted to P0"), never
  quoting or paraphrasing `.private/` content into tracked files, commit
  messages, or upstream issues.
- **Three privacy tiers per intent item:** Tier 0 spoken-only (agent project
  memory, never any repo) · Tier 1 `.private/` overlay (default) · Tier 2
  public record.
- If the project itself indexes repos (ckb does), `.private/` goes on the
  deny-glob list.

## 3. Question compression in decision-map resolution ("decision memos")

**Evidence:** outrigger's measured interview compression (14/10 baseline turns
→ 2, zero escapes across 11 ratified specs). kb session audit: ~20 one-at-a-
time "agree?" gates; operator changed course exactly twice.

**Mechanism:** a resolution session produces a decision memo: craft decisions
derived on the record (recommendation applied, one-line rationale each) plus
only the genuine forks — one-way doors and product boundaries — as individual
questions with recommendations. The operator answers forks, batch-ratifies the
memo, and may reopen any memo item by naming it. Learning-mode exception: §7
deliberately un-compresses tagged domains.

## 4. Worker harness (one-punch delta skill; portable)

**Evidence:** the kb build re-derived outrigger's principle 3 ("completion is
granted by artifacts, never claimed by agents") from scratch across three
nights of runner debugging. The lessons are general and belong in one-punch.

Contents: harness-verified done (project verify commands re-run by the harness;
the agent's word is never the evidence) · blocker gating from ticket metadata ·
fresh session per ticket, file handoffs · failure-debris salvage and
restore-on-retry (partial work accumulates across attempts) · context
compaction guidance for local models · two launcher recipes: mini-swe-agent
(local models) and hardened `claude -p` (outrigger's claude_p.py pattern with
the 2026-08 build corrections: OS-level denyRead walls + Read-tool deny,
acceptEdits never bypassPermissions, failIfUnavailable, setting-source
exclusion, network allowlists, unix-socket DB bridging, env-prefix
approval-gating workaround via config files) · per-ticket cost/usage ledger.
Verify commands parameterized per repo. Composes with, never replaces,
`/to-tickets` ticket bodies.

## 5. Verification & routing by determinacy/risk tags

**Evidence:** outrigger routing table (prose-spec implementers below mid-tier
churned 2/2); kb experiment (local Qwen: 3 attempts, spec-narrowing, test
theater; Sonnet 5 high: one pass, ~zero findings, $3.03); outrigger's
disjoint-instruments result (the shared defect shipped at every tier and only
the blind oracle caught it).

**Mechanism — the same tags drive implementer routing and verification depth:**
- `code-complete` + strong implementer → harness verify only; review amortized
  at branch milestones.
- `contract` → per-ticket spec-verdict pass (Missing / Extra / Misunderstood
  against the ticket checklist — minutes, not ceremony).
- `critical` (ACL/leak-tests, money paths, fusion math) → top-tier implementer
  AND a blind oracle authoring acceptance tests from the contract, because
  "the tests that should exist" is what neither the implementer nor
  harness-verify can self-certify.
- Primary defect-prevention lever is implementer tier, not review (operator
  position, evidence-backed); review concentrates where its defect class lives.
- Plan-probe → trap-notes loop: before dispatching a cheap implementer at a
  hard ticket, ask it for its implementation plan; a strong model converts the
  plan's wrong turns into ticket trap notes. Measured effect in kb: changed
  what the implementer built.

## 6. Orchestrator invocation (skills-repo split, reconciled)

User-invoked-vs-model-invoked split is preserved in effect but reframed:
**orchestrator skills become model-proposable, never model-enterable.** The
agent may propose entering a ceremony (wayfinder, grilling, to-spec…) when the
work looks ceremony-shaped; the human's yes is the invocation. Fixes the recall
failure (kb never ran grill-with-docs — nobody remembered it existed) while
preserving process sovereignty. Discipline skills remain freely model-invoked.

## 7. Operator learning mode (brainstorm — OPEN, under discussion)

**Problem:** agentic coding lets the operator watch competent decisions happen
without building any expertise. For many projects, building domain expertise
hands-on IS a goal — it just isn't stated, so no process serves it.

**INTENT.md captures it:** learning goals as first-class intent — domain(s),
current level, target, preferred modes. Learning mode is an overlay on existing
stages, driven by intent tags, default OFF (vibe-coding stays vibe-coding).

**Candidate mechanisms (to refine):**
- **Socratic inversion at decision points** (tagged domains only): the agent
  presents the decision and asks the operator to reason first, then critiques —
  deliberately un-compressing §3 where the tedium is the product.
- **Teach-back gates:** before ratifying a contract section in a tagged
  domain, the operator explains it back (voice fine); gaps become drills.
- **Operator-implements tickets:** some tickets tagged for human
  implementation with the agent as reviewer/pair; chosen for learning density
  and low schedule risk.
- **Measure → gap-map → drill blocks → re-measure (the proven loop):** baseline
  mock exercise in the project domain (mock design review, "defend this
  architecture," "the relay is down — go"); prioritized gap report; drills
  generated FROM the project's own artifacts (spike numbers, contract
  sections, live incidents); re-measure on a transfer task, not the original.
  Modeled on the operator's system-design coaching session (measured: works).
- **Game-day drills on the running system:** kill a dependency mid-operation;
  operator predicts behavior before observing. Builds the operational-maturity
  layer that reading never does.
- **Inverted review:** operator reviews the agent's PR first; agent grades the
  review against defects it knows are present.
- **LEARNING.md ledger** (Tier 1 private by default): gaps, drills completed,
  re-measure dates; the agent schedules re-measures.
- **Composition note:** upstream `productivity/teach` already does multi-
  session stateful teaching; one-punch composes (invokes it with
  project-sourced material) rather than paraphrasing it. The deltas one-punch
  owns: intent tagging, stage hooks, project-sourced drills, operator-
  implements routing, the measure/re-measure protocol.

## 8. Out of scope for v3 (recorded to keep the fence honest)

- Reviving the v1 total-spec runner (dead; the harness in §4 is deliberately
  minimal).
- Building generic teaching content (compose upstream `teach`).
- Any change executing before this document is finalized by the operator.

## Open questions (running list)

1. §5: does the blind-oracle instrument for `critical` tickets earn its seat in
   v3, or does ckb's first ACL ticket generate the evidence first? (Operator
   leaning: evidence first.)
2. §7: which candidate mechanisms make the cut for v3 vs. stay listed as
   options? Socratic inversion and measure/drill/re-measure look strongest.
3. §1: exact question set for intent elicitation (draft when finalizing).
4. §6: propose-consent UX — how loud should ceremony proposals be?
5. Packaging: which items become skills vs. pipeline.md amendments vs. harness
   templates?

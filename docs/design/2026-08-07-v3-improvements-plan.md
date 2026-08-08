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

**Draft question set (Q3 resolved — refine at finalization):**
1. Why this project, and why now? What happens if it never ships?
2. Who, besides you, will see or use the result — users, readers, employers,
   communities, specific companies?
3. Describe the best realistic month-after-success. What changed?
4. Any second-order happy paths worth designing for? Longshots welcome.
5. What adjacent futures must we not foreclose? What outcome would make this
   effort a regret?
6. Which domains here do you want to build real expertise in, versus delegate
   entirely? (feeds §7 tags, budget, and gates)
Each answer gets a privacy tier (§2) at capture time. Follow-up rule: pull the
thread wherever an answer implies undeclared goals; stop when a new answer
changes no decision you can foresee.

**Honest limit, stated in the skill:** elicitation works only with candor; some
intents are private. Intent shared is design leverage; intent withheld is
priced-in risk, not failure. Hence §2.

## 1b. Evidence pass (evidence-kit, early and eager)

**Operator direction 2026-08-08:** high upfront research investment has
repeatedly shown very high ROI — whole projects avoided by forking prior art,
core decisions changed by compelling evidence. v3 makes this explicit:

- **An evidence pass runs at the front of every non-trivial effort**, between
  intent and the decision map: prior art and FORK-OR-BUILD scan (must be
  answered before the map is charted — the kb effort never explicitly asked
  it), benchmarks, domain evidence, related-domain survey.
- **Research routes through the evidence-kit method** (repos/evidence-kit:
  graded holdings with warrant x decay per claim, Tier-A-only load-bearing,
  separate promotion pass, corrections ledger, pinned mirrors) instead of
  ad-hoc docs/research/*.md files. Evidence from kb: the NIP-34 mis-claim and
  buzz's stale rate-limit doc were both warrant/decay failures the kit
  catches by construction.
- **Unification**: one-punch's spike rule ("mechanism claims enter contracts
  only via spike transcripts") is the execution-warrant special case of
  evidence-kit's warrant system; spike transcripts file into the corpus as
  directly-verified holdings. One rule, all claim types.
- **Privacy**: the distilled corpus lives in the `.private/` overlay (like
  INTENT); publishable extracts are promoted deliberately via the sanitized-
  derivation rule. Decision-map tickets cite corpus claims by tier.
- **Recheck schedules feed the retro loop** (§8): facts that rot get re-
  verified or struck on the same cadence retros run.

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

**Architecture (ratified in direction 2026-08-08):** outrigger's tool-neutral
launcher contract is the spine — one bundle shape (params.json: worker
{tool, model, effort}; isolation intent; cwd; timeout; instructions.md),
per-tool launchers that translate intent into vendor mechanisms and refuse
fail-closed anything inexpressible. Adding a tool = adding a launcher; the
runner never changes.

**Tool-agnostic core (what made the kb runner work):** harness-verified done
(commit + harness re-runs project verify; the agent's word is never the
evidence) · blocker gating from ticket metadata · fresh session per ticket,
file handoffs · failure-debris salvage and restore-on-retry · per-ticket
cost/usage ledger. Verify commands parameterized per repo. Composes with,
never replaces, `/to-tickets` ticket bodies.

**Launchers (v3 roster):**
- `claude_p` — outrigger pattern + the 2026-08 build-2.1.220 corrections
  (OS denyRead walls + Read-tool deny, acceptEdits never bypassPermissions,
  failIfUnavailable, setting-source exclusion, network allowlists,
  unix-socket DB bridging, env-prefix approval-gating workaround via config
  files, stream-json usage capture).
- `codex_p` — port of outrigger's smoke-verified launcher (codex exec,
  generated per-spawn --profile, permissions-table walls, network deny
  verified; Browser-plugin network breach documented -> plugins excluded in
  worker profiles).
- `grok` — NEW; no launcher, no probed facts. Smoke-first before any real
  ticket: headless invocation, usage reporting, native sandbox or absence.
  Isolation: container-wrapped launcher as the wall (ratified); interim until
  built: low-sensitivity tickets in isolated clones only. Fail-closed rule
  inherited.
- `mini` (mini-swe-agent + local models) — RETAINED at the lowest tier only
  (operator decision 2026-08-08: local model quality may improve; keep the
  lane open). Only routed truly simple, straightforward tickets. Its
  compaction machinery is kept as a mini-specific reference.

**Routing & usage governor (forks resolved 2026-08-08):**
- Tag -> hard quality floor -> ordered candidate chain of (tool, model,
  effort); router substitutes freely across tools at/above the floor; nothing
  available at floor -> park the ticket and take other frontier work; never
  silently downgrade.
- Remaining-usage is INFERRED: per-provider spend ledger + observed limit
  errors with parsed-or-default cooldowns; optional operator hint command.
  No dashboard scraping.
- Quality is measured, not asserted: per-(tool, model, tag) outcome ledger
  (verify pass rate, spec-verdict findings, cost, turns) continuously updates
  the routing table. Seeded from existing evidence: outrigger's routing
  anchors + the kb Qwen/Sonnet experiment. Ledger stats are recency-weighted
  so old evidence fades as vendors ship new versions.
- **Within-tier exploration (operator direction 2026-08-08): epsilon-greedy
  bandit.** Default: exploit the tier's best-by-ledger candidate; with
  probability epsilon (~0.10-0.15), route to the tier's least-sampled
  candidate so no model goes unexercised and calibration drift is caught.
  Constraints: critical/T0 tickets NEVER explore (always best-known);
  exploration only on low/medium-size tickets; the usage governor filters
  first; every outcome is ledgered. Cross-tier "auditions" (trialing a model
  one tier up to gather promotion evidence) are not bandit-driven — the retro
  proposes them and the operator approves, consistent with the
  demote/promote asymmetry.

**Quality tiers (operator-ratified 2026-08-08, except T2 pending):**

Fable 5 is EXCLUDED from headless execution permanently — operator-interaction
sessions only (cost; and it is the ceiling, reserved for judgment).

| Tier | Candidates (operator-ratified 2026-08-08) |
|---|---|
| T0 | Opus 5 @ high (claude_p) · GPT-5.6-Sol @ high (codex_p) |
| T1 | Sonnet 5 @ max · grok 4.5 @ max · GPT-5.6-Terra @ max |
| T2 | Sonnet 5 @ medium · grok 4.5 @ medium · GPT-5.6-Terra @ medium |
| T3 | GPT-5.6-Luna @ max |
| T4 | Haiku 4.5 |
| T5 | mini + local qwen 3.6 |

Tag x size -> floor mapping (operator-directed 2026-08-08): tickets carry a
Size estimate (low / medium / high / very-high), set at ticket-cutting time by
/to-tickets alongside the determinacy tag.

| Tag | Size | Floor |
|---|---|---|
| critical | any | T0 |
| contract | high, very-high | T1 |
| contract | low, medium | T2 |
| code-complete | high, very-high | T3 |
| code-complete | low, medium | T4 |
| trivial/mechanical | any | T5 |

Supporting rules:
- **Failure-driven escalation** (outrigger's BLOCKED-reasoning pattern): a
  failed attempt retries ONE tier up, with restored debris and a root-cause /
  trap note — so an underestimated Size self-corrects instead of burning
  retries at the wrong tier. Two escalated failures -> park for operator.
- **Size audit in the ledger**: actual turns/cost per ticket are recorded
  against the Size estimate; systematic underestimation is a visible,
  correctable pattern, not a vibe.
- T2/T4 remain landing spots for demotions and operator overrides in addition
  to their floor roles; floors stay hard, fallback goes up freely, down never.

Ledger asymmetry (ratified): measured outcomes auto-DEMOTE a model from a
tier; only the operator PROMOTES. A lucky streak cannot lift a model without
sign-off.

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

**Proposal UX (Q4 resolved):** one line, at natural pauses only ("this looks
map-sized — enter wayfinder?"); at most one ceremony proposal per turn; never
mid-ceremony; a declined proposal is not re-raised until circumstances
materially change.

## 7. Operator learning mode (brainstorm — OPEN, under discussion)

**Problem:** agentic coding lets the operator watch competent decisions happen
without building any expertise. For many projects, building domain expertise
hands-on IS a goal — it just isn't stated, so no process serves it.

**INTENT.md captures it:** learning goals as first-class intent — domain(s),
current level, target, preferred modes. Learning mode is an overlay on existing
stages, driven by intent tags, default OFF (vibe-coding stays vibe-coding).

**Learning goals are TYPED; the mechanism menu differs by type (refined
2026-08-08 against the operator's real ckb goals — the one-loop-fits-all
framing over-indexed on the interview-prep example):**

| Goal type | Primary mechanism | Assessment / gate |
|---|---|---|
| Conceptual understanding (e.g. buzz architecture, what makes it agent-first) | Build against it + write the explainer (the intended article section IS the artifact — load-bearing by construction) | Blind-graded draft + short spoken Q&A |
| Tradeoff mastery (e.g. vector search vs KG vs organized docs; embedding options; code-vs-prose) | Operator OWNS the project's eval harness: designs the experiment matrix, interprets results. Prediction-first: write down expected winner + why before each run; divergence is the curriculum, reality is the answer key | Defend the tradeoff writeup to a blind grader; article as capstone |
| Skill acquisition from near-zero (e.g. Rust basics) | Operator-implements tickets on a difficulty gradient (start low/med code-complete — ideal newbie material — climb toward contract), agent as reviewer/pair | TREND gate: N merged tickets with agent-review findings-per-ticket declining; measured by existing review machinery |
| Gap-closing against a bar (e.g. interview prep) | Baseline mock -> gap map -> drill blocks -> transfer re-measure (the full loop; this is where it applies, not the default) | Re-measure at/above pre-registered bar, blind-graded |

Prediction-first is the unifying assessment primitive wherever the project can
supply an answer key (eval runs, game days, incident behavior): cheap,
project-native, ungameable.

**Candidate mechanisms (menu; select per goal type):**
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
  re-measure dates, waivers; the agent schedules re-measures.

**Gating model (operator-ratified direction, 2026-08-07): implementation
progress is GATED on measured, verified learning.** "Understanding is granted
by artifacts, never claimed by the operator" — the outrigger principle applied
to the human. Mechanism:

- **Assessment tickets (`L-NN`) as tracker-native blockers**: implementation
  tickets in learning-tagged domains carry `Blocked by: L-NN`; the harness and
  the agent already refuse blocked tickets. An L-ticket resolves ONLY via a
  committed assessment artifact: pre-registered rubric + bar, transcript,
  grade at/above bar.
- **Grader separation**: rubric and bar written before the mock; grading by a
  fresh session blind to the coaching history. Coach and examiner are never
  the same context.
- **Transfer-only testing**: never assessed on the drilled material itself.
- **Load-bearing assessment (strongest form)**: gates that ARE work the
  project needs — mutation-tested operator-authored test suites (agent seeds
  N known defects; operator's suite must catch >= k), prediction-first game
  days (the system's behavior is the answer key), operator-authored runbooks
  verified by literal execution. In tagged domains, operator-implements
  tickets sit on the critical path: circumvention then cannot produce a
  finished implementation at all.
- **Waiver protocol (the honest limit)**: the agent never fakes a pass; bypass
  exists only as a loud recorded waiver (committed WAIVED WITHOUT PASSING
  ledger entry, named in every subsequent milestone summary). Converts silent
  drift into explicit self-override.
- **Anti-death-spiral**: fail -> targeted drills -> retest on a DIFFERENT
  task; two fails -> forced explicit choice (waive on the record, or descope
  the milestone). Gates sized to what the milestone actually exercised.
- **Bar-setting (ratified 2026-08-07)**: the TARGET is set once at intent time
  (binding; cannot be quietly lowered); the RUBRIC is written per-milestone as
  gates are cut, pre-registered before each assessment.
- **Learning budget (ratified 2026-08-07)**: expressed as N operator-implements
  tickets per effort — tracker-visible and self-enforcing, not self-reported
  hours.
- **Mechanism cut for v3 (proposed)**: IN — Socratic inversion,
  measure/drill/re-measure, game days, the gating model. Options available but
  not built as machinery — inverted review, teach-back gates (both usable
  ad hoc without new tooling). Nothing else.
- **Composition note:** upstream `productivity/teach` already does multi-
  session stateful teaching; one-punch composes (invokes it with
  project-sourced material) rather than paraphrasing it. The deltas one-punch
  owns: intent tagging, stage hooks, project-sourced drills, operator-
  implements routing, the measure/re-measure protocol.

## 8. Packaging plan (Q5 — proposed)

**Effort lifecycle requirements (operator, 2026-08-08), mapped into this
section:**
- **Self-contained repo**: the local-markdown tracker becomes the DEFAULT
  posture, not an option — task definitions, decision record, and effort state
  live in-repo; no external ticketing. Run state is committed or derivable
  from committed artifacts (ticket Status lines are the source of truth);
  only transient logs/trajectories are gitignored (and archived).
- **Resumability first-class**: every stage's output is an on-disk artifact;
  sessions are file-contract based; the harness gains a `resume` entry point
  (read the repo -> report frontier, in-flight debris, pending gates, parked
  tickets -> continue). Nothing lives only in a conversation.
- **Retro loop**: at milestones, effort-end, or any later date, a retro
  compiles the routing/usage ledger, gate outcomes + waivers, size-estimate
  audits, and operator OUTCOME REPORTS (external results, e.g. an interview
  probing a learning goal) into an evidence memo filed in one-punch, with
  proposed amendments. Retro is the promotion front door (ledger auto-demotes
  in-effort; promotions ride retro evidence + operator sign-off) and the
  calibration channel for §7 gate design.

| Item | Ships as |
|---|---|
| §1 intent elicitation + §2 privacy overlay | New one-punch skill `intent` (effort-opening ceremony; INTENT.md + overlay setup templates in references/) |
| §3 decision memos | pipeline.md amendment (usage discipline over /grilling inside wayfinder resolution) |
| §4 worker harness | New one-punch skill `worker-harness` (runner skeleton, mini + hardened claude -p launcher recipes as reference templates; portable, no machine paths) |
| §5 tags, routing, verification, plan-probe/trap-notes | pipeline.md amendment extending the §7 ticket-craft list; harness skill references the routing table |
| §6 orchestrator proposals | pipeline.md note (one paragraph); consider upstreaming to mattpocock-skills later — out of v3 scope |
| §7 learning mode + gates | New one-punch skill `learning-gates` (L-ticket conventions, rubric + LEARNING.md templates, waiver protocol; composes upstream `teach`, never paraphrases it) |
| §1b evidence pass | pipeline.md stage amendment + composition note in the `intent` skill; evidence-kit itself stays external (composed, not vendored); spike skill amended to file transcripts as execution-warrant holdings |
| Effort lifecycle: tracker default + committed state + `resume` | pipeline.md amendment + harness skill `resume` entry point |
| `start` front-door skill | New one-punch skill `start`: single entry point for a new effort — prerequisite check (runs setup if missing) -> scaffold (repo + .private overlay, remotes) -> intent ceremony -> evidence pass w/ fork-or-build gate -> hand-off to wayfinder. Model-proposable per §6. Paired with the harness `resume` entry point as the only two things a newcomer must know; the README's Getting Started is these two commands |
| Standalone README rewrite | one-punch README rewritten to stand alone (a newcomer needs no other repo to understand what it is, why, and how to start), modeled on the skills repo README's shape: the problems it fixes, 30-second install for EACH supported harness, the pipeline at a glance, reference section per skill/stage. Composition with mattpocock-skills and evidence-kit stated as an implementation detail ("pulls these in under the hood"), never as required reading |
| §8b harness agnosticism | AGENTS.md canonicalization + CLAUDE.md shim; skill-by-skill standard-conformance audit; per-vendor smoke checklist doc; dual-path install docs in README |
| `retro` loop | New one-punch skill `retro` (evidence-memo template, outcome-report format, amendment-proposal protocol; files memos in one-punch docs/evidence/) |
| Blind oracle for `critical` tickets | NOT built in v3 (Q1 resolved: evidence-first). ckb's first critical ticket runs top-tier implementer + spec-verdict review; if a defect ships through that, the oracle earns its seat with evidence. Revisit clause recorded here. |

## 8b. Harness agnosticism (operator requirement, 2026-08-08)

one-punch must be usable with any interactive agent — Claude Code, Codex,
grok — not only Claude Code. Outrigger already made this migration; adopt its
pattern:

- **AGENTS.md is canonical**; CLAUDE.md becomes an `@AGENTS.md` import shim
  plus a short Claude-specific section (the outrigger layout, verbatim
  pattern). Vendor-specific guidance lives only in the vendor shim.
- **Every one-punch skill conforms to the Agent Skills open standard**
  (agentskills.io): no hardcoded Claude Code tool names, graceful degradation
  ("if the harness offers a structured question UI, use it; else ask in plain
  text"), background-agent dispatch phrased harness-neutrally (upstream
  skills' 1.2.1-1.2.3 diffs are the template), real requirements in
  `compatibility:` frontmatter.
- **Distribution dual-path**: Claude Code plugin AND skills.sh-style
  file-copy install for Codex/grok/others.
- **The harness reference implementation is already agnostic by
  construction** (stdlib Python core; per-tool launchers behind the JSON
  bundle contract; the interactive agent driving it is irrelevant to it).
- **Per-vendor compatibility smoke** (outrigger's discipline): a checklist
  table in one-punch — instructions loaded, skills invocable, tracker ops,
  harness runnable — each row passing PER VENDOR before that vendor is
  claimed supported; re-run on vendor releases. A green Claude row says
  nothing about Codex.
- **Install flows (README source material, ratified direction):**
  Claude Code: `claude plugin marketplace add <gh-slug>/one-punch` +
  `claude plugin install one-punch@one-punch`, then `/one-punch:start` in the
  project dir; `start`'s prereq check detects missing composed dependencies
  (mattpocock-skills, evidence-kit) and prints their install commands rather
  than requiring foreknowledge. Codex (post-§8b, post-smoke only):
  `npx skills@latest add <gh-slug>/one-punch` (+ mattpocock/skills) via the
  skills.sh file-copy path; AGENTS.md read natively; skills invoked by name in
  prose, no slash commands assumed.
- Capability-degradation notes where features assume a harness capability
  (e.g. voice mocks in learning gates degrade to text; subagent model-routing
  names differ per harness and live in the vendor shim, never in skill
  bodies).

## 9. Out of scope for v3 (recorded to keep the fence honest)

- Reviving the v1 total-spec runner (dead; the harness in §4 is deliberately
  minimal).
- Building generic teaching content (compose upstream `teach`).
- Any change executing before this document is finalized by the operator.

## Open questions (running list)

1. ~~Blind oracle~~ — resolved (evidence-first; see §8 revisit clause).
2. §7 mechanism cut — proposed in §7; awaiting operator ratification.
3. ~~Intent question set~~ — drafted in §1; refine at finalization.
4. ~~Proposal UX~~ — resolved in §6.
5. §8 packaging table — proposed; awaiting operator ratification.
6. Finalization checklist: operator reads the full doc top to bottom, ratifies
   §7 cut + §8 table + §1 question set, then v3 execution begins (skills
   authored on this branch, pipeline.md amended, ledgered).

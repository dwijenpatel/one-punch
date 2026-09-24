# one-punch v4 — steer-then-swarm — planning document

**Status: DRAFT — design approved in session 2026-09-24 (principles, half A,
half B with the interactive session as planner, skill inventory); this written
spec awaits operator review.** On ratification it becomes the execution
authority for v4, and `pipeline.md` is amended to v4 by the first ticket.

**Evidence base:** [../evidence/2026-09-24-v4-outside-evidence.md](../evidence/2026-09-24-v4-outside-evidence.md)
— the ckb cold-start stall, Cursor's three swarm posts, superpowers 5.0.6–6.4.1
measured corrections, mattpocock-skills 1.2.3, slipstream's build record,
idea-gen D26. Section references below cite that memo as `E§n`. Code-style
evidence: [canon](../evidence/2026-09-24-code-style-research-canon.md) (`C`)
and [critiques + agent evidence](../evidence/2026-09-24-code-style-research-critiques-and-agents.md) (`K`).

**One-line shape:** agents run ahead of the human in parallel; the human
ratifies forks against evidence in few, dense sittings; a planner that never
implements turns ratified decisions into explicit tickets; up to four workers
execute them in isolated worktrees; a script — not an agent's word — decides
what merges; and **scrutiny at every stage is set by blast radius** — how much
damage a wrong change could do if it shipped unnoticed.

---

## 1. Principles (v4 deltas; v3 principles not listed here stand)

1. **Agents run ahead of the human.** Research, spikes, prototypes and code
   survey run in parallel *before* the operator is asked anything that
   evidence can inform. The operator ratifies forks; they do not drive
   discovery. *Supersedes v3 §1.2 (serialized one at a time).* (E§1.1, E§1.4)
2. **Question altitude.** The operator is asked only about one-way doors,
   product boundaries, and conflicts with recorded intent. Everything else is
   decided by the agent, recorded with a one-line rationale, and reopenable by
   ID. Fan-out ordering (v3 §0a) still orders what is asked. (E§1.1)
3. **Planners decide, workers execute.** Every design decision has one owner
   (the planner) and one ledger entry. No two tickets decide the same
   question. A worker that meets an undecided cross-ticket question takes the
   local, reversible option and flags it in its handoff; it never decides
   silently. (E§1.2 split-brain, contention)
4. **Avoid conflicts structurally, resolve them neutrally.** Tickets declare
   what they touch; the scheduler never co-runs overlapping tickets; residual
   conflicts go to a neutral merge agent, never to either worker. (E§1.2)
5. **Scrutiny scales with blast radius.** The damage a wrong change could do
   if it shipped unnoticed — irreversibility, security exposure, breadth,
   silence — sets every scrutiny dial: who decides the design, which model
   implements, who writes the tests, which lenses review, whether a spike is
   mandatory, and whether the operator reads the diff. Classification is the
   maximum of the plan, a ratified blast map, and a diff detector; agents can
   raise it, never lower it. Contained work takes the lightest path so the
   scrutiny budget concentrates where damage lives (§2b). Execution-based
   verification stays primary at every level; concurrency × run length only
   raises the milestone-review floor. (Operator principle 2026-09-24; E§1.7,
   E§3, D26.)
6. **Ceremony is opt-in.** Private overlay, evidence corpus, learning gates and
   contract review are off by default and proposed only when the effort shows
   the need (v3 §9 "model-proposable, never model-enterable" stands). (E§1.1)
7. **Code standards are enforced, not just stated.** A short, repo-specific
   style section says only what a linter cannot decide; linters and import
   boundaries enforce what they can; review checks the rest. Each
   decomposition rule carries its counterweight, because the listed failure of
   agent code is over-abstraction, not under-abstraction. (§3.11; C, K)
8. **The environment carries the memory.** Decisions, negative results and
   surprises are written where the next agent reads them first (decision
   ledger, field guide), not left in transcripts. (E§1.2 Field Guide, E§1.5)

## 2. Half A — steering

Three human touchpoints per milestone (H1 once per effort), three agent stages.

### H1 — intent + destination sitting (one sitting, ≤15 min target)

One round of questions, fan-out ordered, asked conversationally (never a
pasted wall — v3 lesson `cdae9ad`). The agent's checklist:

1. What are we building, and why now? What does *done* look like — describe
   the demo.
2. Who uses or sees it?
3. Constraints: stack, deadline, budget, hard non-goals, things that must not
   be foreclosed.
4. **What would be catastrophic if wrong?** Data loss or corruption, a
   security or privacy breach, money moved wrongly, users locked out,
   anything irreversible or silent. Seeds the blast map (§2b).
5. **Brownfield only:** which area of the code; what must not break; what the
   operator already knows is fragile.
6. **Risky assumptions:** the agent proposes a list drawn from answers 1–5;
   the operator ranks and adds. Each gets a kill/pivot criterion.

Follow-ups only where an answer changes a foreseeable decision. The private
overlay is offered only if the operator signals private motives.

**Output:** `INTENT.md` (≤1 page) with sections Goal · Done looks like ·
Audience · Constraints · Non-goals · Must-not-foreclose · **Catastrophes**
(seed for the blast map) · **Risk register**
(table: ID `R-n`, assumption, why risky, cheapest test, kill/pivot criterion,
status).

### A1 — parallel fan-out (agents, ≤4 concurrent)

The planner launches up to four background agents at once, each with a
file-based brief and a timebox:

| Lane | Greenfield | Brownfield |
|---|---|---|
| **Risk** | one `spike` per top-ranked `R-n`, cheapest first; transcript recorded against the risk | same |
| **Shape** | walking skeleton or `prototype` answering the biggest *does-this-feel-right* question | code survey of the touched area: module map, seams, test coverage, hot/mega files, **blast-map proposal** (auth, transactions, migrations, money, trust boundaries found in the code) |
| **Safety net** | — | characterization tests pinning current behavior at the seams to be changed |
| **Facts** | `research` on open external questions; fork-or-build only if genuinely open | same, plus upstream/issue history for the touched area |

Meanwhile the planner drafts the **decision map** privately (wayfinder used as
the planner's own tool, not as one human session per ticket), resolving craft
decisions on the record as spike and research results land.

Rules:
- A spike or lane that hits its kill criterion **stops the fan-out** and
  surfaces immediately — a dead assumption is an H2-now event, not a memo
  footnote.
- Research and spikes write findings to files; lanes never message each
  other.
- Brownfield seeds the field guide (§3.7) from the survey.
- Greenfield: the planner drafts the blast map from INTENT.md's catastrophes
  and the skeleton's architecture.
- Any risk whose failure would land in a B3 zone is spiked in A1, not
  deferred to build.

### H2 — decision memo + demo (one sitting; follow-up rounds allowed)

Produced by the new `decision-memo` skill. Format:

1. **Demo:** the skeleton/prototype running, or the survey's module map.
2. **Risk register update:** each `R-n` → confirmed / killed / pivoted, with
   transcript links.
3. **Forks** (the only questions), fan-out ordered, each with: the question,
   options, recommendation, evidence link, what it forecloses.
4. **Blast map** (§2b) for ratification — a fork by definition, since it
   encodes the operator's risk tolerance. Every design decision inside a B3
   zone (auth scheme, session model, transaction/isolation model, migration
   strategy, trust boundaries) is listed as a **fork**, never as a default.
5. **Recorded defaults:** every craft decision as `D-NNN — decision — one-line
   rationale`, batch-ratified; the operator reopens any by ID. B2 defaults are
   flagged as such.

Forks newly unlocked by the answers come as a short follow-up round in the
same sitting (mattpocock `grilling` rounds over a frontier), never as new
sessions. Fog stays fog: undecidable-now items are listed as "not yet
specified", with the milestone that will reveal them.

### A2 — compile (planner)

- **Decision ledger** `docs/decisions.md` (§3.3) populated from the memo.
- **Spec** via `to-spec` only when the effort is handoff-sized; otherwise the
  ledger + INTENT.md are the contract.
- **Tickets** via `to-tickets`, plus the v4 fields (§3.2).
- **Isolate the blast.** Tickets are cut so B3 code sits behind narrow seams
  (deep modules) and is touched by as few, as small tickets as possible;
  B3 core and its B1 surroundings are separate tickets.
- A one-screen **ticket-graph summary** (ticket, Touches, blockers, tag, size,
  **blast**) is shown to the operator, with the count of B3 tickets — each is
  a diff the operator will read. It is a veto window, not a gate: building starts
  unless the operator objects.

### H3 — milestone demo + merge (recurs)

The operator sees the milestone running, accepts or redirects, and decides the
merge to `main`. Forks unlocked by building arrive here as a mini-memo (same
format as H2, forks + defaults only). The milestone report lists every B2/B3
change with its evidence (tests, lens report, operator sign-off for B3) and
every blast escalation the detector caught.

**Milestones:** destinations larger than one build batch (rule of thumb: >15
tickets or >1 day of worker time) split into milestones. Each milestone runs
A1 (only lanes with new risks) → H2 (only newly visible forks) → A2 → build →
H3.

## 2b. Blast radius — the scrutiny axis

**Definition.** A change's blast radius is the worst plausible damage if it is
wrong and the error ships unnoticed. Four factors:

- **Irreversibility** — data lost or corrupted, money moved, messages sent,
  state that cannot be rolled back.
- **Exposure** — crosses a security or privacy boundary: authentication,
  authorization, sessions, secrets, crypto, PII, parsing untrusted input.
- **Breadth** — fan-in: how many modules, users, or later tickets depend on
  it (shared core, public interfaces, schema, build/CI/deploy).
- **Silence** — fails quietly rather than loudly. A wrong isolation level or
  a missing authz check passes every happy-path test.

**Levels** (silent + irreversible ⇒ B3 regardless of size):

| Level | Typical code |
|---|---|
| **B0 contained** | tests only, docs, dev scripts, prototypes, internal tooling, copy |
| **B1 local** | feature code behind a seam, one module; failures loud and reversible |
| **B2 wide** | shared core modules, public APIs/interfaces, additive schema changes, concurrency, caching, performance-critical paths, build/CI config, dependency upgrades |
| **B3 severe** | authn/authz, sessions, crypto, secrets; payments/money; database transactions and isolation; destructive or irreversible data operations (migrations that drop or transform, deletes, backfills); PII; tenant/permission boundaries; untrusted-input parsing at a trust boundary; deploy/infra |

**Assignment — the maximum of three sources; never lowered by an agent:**

1. **Blast map** (`docs/blast-map.md`, with a machine-readable block the
   harness reads): path globs and content patterns → minimum level. A default
   pattern pack ships with the `blast-radius` skill (auth/session/password/
   token identifiers and crypto imports; SQL DDL, `DELETE`, transaction and
   isolation keywords; migration directories; payment SDKs; role/permission
   checks; deserialization of external input; CI/deploy files); repos extend
   it. Proposed in A1, ratified at H2.
2. **Planner declaration** per ticket at A2: `Blast: B3 — changes session
   token validation` (level + one-line reason).
3. **Diff detector** in `integrate` (§3.5): effective blast = max(declared,
   blast-map level of every path in the actual diff, pattern matches in the
   diff). Effective > declared → `BLAST-ESCALATION`: not merged; the ticket
   re-routes at the higher level with its work salvaged, and the retry adds
   that level's scrutiny steps. Planner under-classification is caught
   mechanically and counted.

Only the operator lowers a level, recorded as a ledger row (`D-NNN: path X is
B1 despite pattern Y because …`). Detector false positives cost one extra
review; accepted, because the costs are asymmetric.

**Scrutiny ladder** (each level includes everything in the levels below it):

| Dial | B0 | B1 | B2 | B3 |
|---|---|---|---|---|
| Design decisions (H2) | craft default | craft default | default, flagged | **always an operator fork** |
| Spikes | — | external-behavior claims (v3 §1.1) | same | **mandatory** for every security/consistency semantic relied on (the isolation level the DB actually provides, a token library's validation defaults, the framework's CSRF behavior) |
| Implementer floor | per tag × size (Haiku allowed) | Sonnet | Sonnet (Opus for `contract`) | **Opus** |
| Tests | verify passes | TDD red→green at the seams | + edge and error paths at the public seam; coverage on touched files not reduced | + **acceptance tests written first by an independent agent** from the ticket and the domain checklist (oracle seat, v3 §8); + adversarial/negative tests (authz denial on every path, replay, injection; rollback, concurrent writers, crash mid-transaction, idempotent retry; migration up→down→up on prod-shaped data); property tests where an invariant exists |
| Automated review | — | spec verdict if `contract` | spec verdict | spec verdict + **decorrelated lens** (Codex else Opus, no transcript) against the domain checklist |
| Operator review | milestone sample | milestone | milestone; each B2 diff listed | **reads the diff before it merges** — `integrate` holds it `AWAITING-OPERATOR`; the run continues with other tickets |
| Scheduling | any batch | any | any | never co-scheduled with a ticket in the same blast-map zone; licensed breakage *into* a B3 zone is forbidden (it must be its own B3 ticket) |
| Merge conflicts | merge agent | merge agent | merge agent | merge agent on Opus, and the merged result re-enters B3 review |
| Structure (§3.11) | style lint | style lint | + decision logic in the pure core | + **decision logic pure and property-tested on its own; the effectful shell kept thin enough to review line by line** |

**Domain checklists** (`blast-radius` skill references; used by the oracle
test author and the lens): authentication & sessions · authorization &
tenancy · secrets & crypto · transactions & concurrency · migrations &
destructive operations · money · untrusted input. Each is a short list of
the failure modes that pass happy-path tests (for transactions: boundaries
match the invariant; isolation level stated and justified; no
read-modify-write outside a transaction; retries idempotent; lock order
fixed; a failure leaves no partial state).

**Why the operator reads B3 diffs.** LLM judges caught 5% of real bugs in
D26's exp-01; at B3 the failure is silent and irreversible, so model review
alone is not an adequate last line. This deliberately reinstates one
per-ticket human touchpoint, and only here. v4 moves the operator's attention
from craft questions, which it removes, to the few diffs where damage lives.
A2's "isolate the blast" rule keeps that load small.

## 3. Half B — build

### 3.1 Roles and models

| Role | Who | Model | Never |
|---|---|---|---|
| **Planner** | the operator's interactive session (default); headless T0 is a later option | Opus (session model) | implements; routes itself headless |
| **Worker** | fresh headless session per ticket, launched by `harness run` into its own worktree via a v3 launcher (`claude_p` default) | floor = max(tag × size floor, blast floor §2b): Haiku only at B0; Sonnet default; Opus at B3 | plans across tickets; talks to other workers; decides a ledger question |
| **Merge agent** | fresh agent, invoked only on conflict | Sonnet (Opus if either ticket is B3) | favors either side; changes behavior beyond the two tickets |
| **Lens reviewer** | fresh agent, B3 tickets + milestones | a model different from the implementer's | edits code; sees the implementer's transcript (codebase + ticket + diff only) |

Every dispatch names its model explicitly (operator policy; superpowers
v6.0.0 failure). No Fable model on any subagent.

**Planner context discipline:** all planner state lives on disk — ledger,
tickets, handoffs, `planner-scratchpad.md` (rewritten, never appended —
Cursor freshness rule) and the integration log. A new session per milestone
is normal; `resume` rebuilds state from files.

### 3.2 Ticket format (v4 fields on top of `to-tickets` + v3 §7)

Local-markdown default (`.scratch/<effort>/issues/NN-slug.md`). Header lines:

```
Status: ready-for-agent
Blocked by: 03, 05
Tag: code-complete | contract
Blast: B0 | B1 | B2 | B3 — <one-line reason>
Size: low | medium | high | very-high
Touches: src/store/**, tests/store/**
Decides: D-014            (only if the planner delegates a local decision)
Depends-on: D-003, D-007
```

Body: intent in a few sentences; **constraints** ("no TODOs, no partial
implementations, no new dependencies without a ledger entry") rather than a
step checklist; numeric ranges where scope is quantitative; acceptance checks
as shell commands (v3 §7 rot-proof fences); worked examples with exact values.

`Touches` is a promise the harness checks (§3.5): a diff outside `Touches` is
allowed only as licensed breakage (§3.6).

**v3 tag split.** v3's `Tag` mixed two axes. v4 keeps `Tag` for determinacy
only (`code-complete` / `contract`) and moves risk to `Blast`: v3 `critical`
→ B3, v3 `trivial` → B0 + `Size: low`. Routing floor = max(v3 tag × size
floor, blast floor); fallback goes up freely, down never (v3 §8).

### 3.3 Decision ledger

`docs/decisions.md` — one table, one row per decision:
`ID · decision · rationale (one line) · owner · status (active/superseded by
D-x) · ADR link (if any)`. Decisions meeting mattpocock `domain-modeling`'s ADR
criteria (hard to reverse, surprising, real trade-off) also get an ADR; the
ledger row links it.

Code that exists *because of* a non-obvious decision carries a reference
comment `D-NNN`. The harness's **ref check** (§3.5) fails if any `D-NNN` in
the diff has no active ledger row — the portable analog of Cursor's
compile-checked references and slipstream's drift test. The ref pattern is configurable in `harness.toml` for repos where `D-NNN` collides with existing identifiers. Superseding a
decision makes every reference to it a visible grep target for a follow-up
ticket.

### 3.4 Scheduling — `harness run --parallel N` (ratified 2026-09-24, option C)

The build loop is a deterministic program, not an LLM. The planner session
cuts tickets, then starts `harness run --parallel 4` as a background process
and is notified when it stops. The loop:

1. Frontier = tickets whose blockers are merged (v3 `frontier()`).
2. **Batch selection:** from the frontier, pick up to N (default 4) tickets
   with pairwise-disjoint `Touches`; ties broken by critical path, then size.
   B3 tickets are never batched with a ticket in the same blast-map zone.
   Pure function `select_batch()` in `core.py`, property-tested. Overlap is
   defined on the current tree: two tickets overlap if any existing file
   matches both `Touches` sets, or both sets match the same not-yet-existing
   path prefix.
3. Each selected ticket → `git worktree add .worktrees/<ticket>` on a branch
   `t/<ticket>` cut from the current integration head; the tier router (v3
   §8) picks the launcher + model; the worker gets the preamble (§3.8) +
   ticket text.
4. **Keep the pipe full:** as each worker exits, run `integrate` (§3.5) on its
   branch, recompute the frontier, and launch the next disjoint ticket. No
   waiting for the slowest worker (Cursor's rigid-executor failure).
5. Failures follow v3 salvage/escalation; conflicts launch the merge agent
   headless (§3.5 step 2).

**Stop conditions** (the run exits and the planner session is notified):
frontier empty (milestone done) · every frontier ticket parked or blocked ·
**K tickets (default 2) parked on `Decisions needed`** — a worker handoff whose
decision-needed item is not locally reversible parks that ticket and its
dependents · usage governor reports all candidates cooling · operator stop.
The planner then reads handoffs, updates the ledger/tickets (steering happens
here, between runs), and relaunches. `harness run` is equally usable
walk-away or overnight; `resume` reports state from the event ledger.

### 3.5 Integration — `integrate` script (the only path to the integration branch)

Deterministic, stdlib-only, invoked by `harness run` after each worker exits (and runnable by hand):

1. Refuse unless the worker's handoff file exists with status DONE or
   DONE_WITH_CONCERNS.
2. Rebase the ticket branch onto the integration head.
   - Clean → continue.
   - Conflict → abort the rebase, emit `CONFLICT` with both tickets' IDs;
     the harness launches the merge agent headless (mattpocock
     `resolving-merge-conflicts` discipline) with both tickets, both
     handoffs, and their `Depends-on` rows; the merge agent's result re-enters
     at step 2.
3. Run the project's verify commands (from `harness.toml`) on the rebased tree.
4. Run the hygiene checks:
   - **ref check** (§3.3);
   - **Touches check** — files changed outside `Touches` without a
     `BREAKING(D-NNN):` comment → fail;
   - **blast check** (§2b) — compute effective blast from the actual diff;
     above declared → `BLAST-ESCALATION` (not merged; re-route at the higher
     level, work salvaged); a diff reaching into a B3 zone from a non-B3
     ticket → fail;
   - **scrutiny evidence check** — the steps the effective level requires
     exist as artifacts (B2: spec verdict; B3: independent acceptance tests
     committed before the implementation commits, lens report, domain
     checklist answered) → else fail;
   - **style lint** (§3.11) — hard-fail rules fail; soft-cap warnings are
     written to the integration log and the handoff, not failed; brownfield
     is ratcheted (only new violations in changed code count);
   - **megafile check** — any changed file that crossed the threshold (default
     800 lines, configurable) *in this change* → fail with
     `MEGAFILE <path>`; the planner cuts a decompose ticket that blocks further
     tickets touching that file (pre-existing brownfield megafiles pass until
     they grow).
5. All green → B0–B2: fast-forward the integration branch. B3: park as
   `AWAITING-OPERATOR` with a review packet (diff, tests, lens report,
   checklist) and continue other tickets; the planner session surfaces it,
   and it fast-forwards only on operator approval. Append an event to the
   JSONL ledger (ticket, model, tag, size, declared and effective blast,
   attempts, verify result, tokens if known, wall-clock).
6. Any red → FAILED attempt (v3 salvage/escalation rules unchanged: retry one
   tier up with a root-cause note; two escalated failures park the ticket).

The integration branch (`integrate/<effort>`, cut from `main` at A2) is always green. `main` changes only at H3.

### 3.6 Licensed breakage

A worker may change code outside its `Touches` when its ticket genuinely
requires a core change. It must leave `BREAKING(D-NNN): <why>` at the change
site (creating a *proposed* ledger row in its handoff if no decision exists)
and list it under Deviations. The planner accepts (ledger row goes active; the
compiler/tests surface every dependent site as follow-up work) or rejects (the
attempt fails with a note). Prevents ossification without licensing drive-by
edits. (E§1.2) Blast limits: breakage into a B2 zone needs the planner's
acceptance before merge; breakage into a B3 zone is never licensed and must
become its own B3 ticket.

### 3.7 Field guide

`docs/field-guide/index.md`, hard budget 150 lines (checked by the harness),
injected into every worker preamble. Content: surprises, traps, negative
results ("tried X, rejected because Y — see D-NNN / transcript"), commands that
actually work. Workers **propose** entries in their handoff; the planner
curates and commits them (single writer, no contention; also keeps the
budget). Distinct from `AGENTS.md`, which stays operator-owned rules.

### 3.8 Worker preamble and handoff

**Preamble** (short; don't instruct what the model knows): the repo's
`AGENTS.md` pointer, `field-guide/index.md` inline, the relevant ledger rows
(`Depends-on`), constraints (stay within `Touches`; licensed-breakage rule;
TDD red→green at the ticket's seams; never decide a ledger question), the
ticket's blast level with that level's required steps — and for B2/B3 the
relevant domain checklist inline — and the handoff contract.

**Handoff** (`.scratch/<effort>/handoffs/NN.md`):

```
Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
Commits: <sha list>
Done: …
Deviations: … (incl. any BREAKING)
Decisions needed: … (question, local option taken, reversibility)
Findings / concerns: …
Field-guide proposals: …
```

The planner reads handoffs as files; worker transcripts are never loaded into
the planner's context.

### 3.9 Review by blast radius

Per-ticket review follows the §2b ladder: nothing extra at B0; spec verdict
(Missing / Extra / Misunderstood vs. the ticket) for `contract` at B1 and for
every B2; spec verdict + decorrelated lens + operator diff review at B3. The
decorrelated lens is a different model *family* via `codex_p` when available,
else a fresh Opus reviewer that sees codebase + ticket + diff only, never the
transcript.

**Milestone:** mattpocock `code-review` (Standards + Spec axes, parallel) over
the milestone diff, with every B2/B3 diff reviewed individually, then H3. The
Standards axis reads the repo's `AGENTS.md` style section natively and adds the
§3.11 review rubric; it also receives the milestone's accumulated lint
warnings.

Reviewers are read-only (superpowers v6.0.0). Milestone findings are batched
to one fixer ticket, not one fixer per finding; a finding in a B3 zone
becomes its own B3 ticket.

### 3.10 Economics

- Ticket explicitness is the cost lever (E§1.2): `code-complete` tickets let
  Sonnet/Haiku workers transcribe; vague tickets cost more worker tokens than
  a planner saves.
- Turn count beats token price (superpowers): don't route prose-heavy
  tickets below Sonnet.
- Scrutiny spend is concentrated by design: the bulk of tickets (B0/B1) take
  the cheap path; Opus implementers, independent test authors, lenses and
  operator attention are spent on the few B3 tickets.
- Spend is a quota proxy on a fixed subscription; the v3 usage governor stays
  as the throttle. N=4 is a default, lowered automatically when limit errors
  are observed.

### 3.11 Code standards (three layers)

**Evidence in brief.** Agent-adopting repos showed +30% static-analysis
warnings and +42% complexity that persisted (K: He et al., MSR'26,
difference-in-differences). Prompting with more detail did not reduce smells
(K: Zhu et al., p>0.8). Context files are followed but cost steps, and their
value is in *non-standard, repo-specific* practice (K: Gloaguen et al.,
preprint; style rules were never ablated separately — whether prose style rules
improve quality is unmeasured). Vendors converge: short, positive, reasoned
rules; linters over prose; add a rule after a repeated mistake. The canon (C)
strongly supports the operator's five principles, with two refinements: the
DB/shared-object exception becomes *injected and confined to the shell*, and
granularity is split by abstraction level, never by line count, paired with
Ousterhout's counterweights (no pass-through layers, no shallow modules).
Inference, not measured: with four parallel fresh workers, stated conventions
reduce style split-brain, and consistent layered code lowers the operator's
B3 review cost.

**Layer 1 — stated.** A `Code style` section in the repo's `AGENTS.md`,
installed at A2 from the one-punch default (Appendix A) with repo-specific
slots filled (which directories are the pure core, which are the shell, a
reference file showing the pattern). Budget ≈ 30 lines. Positive phrasing,
one-clause why, no MUST/CRITICAL. Operator-owned; the planner proposes edits.

**Layer 2 — enforced** (the project's verify commands, run by `integrate`):

| Hard fail | Soft cap (warn, never fail) |
|---|---|
| import boundary: core modules may not import I/O, DB, network, clock or randomness modules (import-linter / dependency-cruiser / crate boundaries) | function length ~40–60 lines (target ~25; K: Chowdhury et al., MSR'22) |
| swallowed errors (bare/blind except, empty catch, unchecked errors) | cyclomatic/cognitive complexity above the repo's cap |
| unused imports/variables, commented-out code, unused exports | clone-level duplication above threshold |
| boolean flag parameters; > N parameters | inheritance depth > framework + 1 |
| new mutable globals; mutable default arguments | — |
| formatter drift | — |

Language packs ship with the skill (ruff codes verified in C; eslint, pylint,
clippy and Go rule names from recall — verified when a repo is wired, as a
spike item). Brownfield ratchet: existing violations are grandfathered;
changed code must not add new ones.

**Layer 3 — reviewed** (only what tools cannot decide). Rubric for the
milestone Standards axis and the B2/B3 spec verdict:
- Over-abstraction: single-use helpers without a standalone contract,
  pass-through functions, interfaces with one implementation, speculative
  parameters/config, new modules before a second real use.
- Mixed abstraction levels in one body; names that don't cover what the
  function does.
- Defensive code for states the types or boundary parsing already rule out.
- Observable-behavior drift in a refactor: outputs, error types/messages,
  ordering (Hyrum's law).
- Knowledge duplicated (a rule that must change in lockstep in two places);
  shared helpers that grew per-caller flags.
- Scope beyond the ticket, or PR size out of proportion to the ticket.

Reviewers flag rule violations and correctness- or requirement-relevant gaps
only. They are told not to request extra abstraction or hardening, since
review itself can push code toward over-engineering (K: Anthropic guidance).

**Rule lifecycle.** A new rule enters only after a repeated mistake (field
guide → promoted to `AGENTS.md`, citing the handoffs). A stated rule with no
review findings and no lint hits across two milestones is a pruning candidate
at retro. A rule a linter can decide moves to Layer 2 and leaves the prose.

## 4. Greenfield vs brownfield (one pipeline, two lane sets)

| Aspect | Greenfield | Brownfield |
|---|---|---|
| A1 shape lane | walking skeleton / prototype | code survey + characterization tests |
| First tickets | skeleton hardening, then tracer bullets | prefactors at the seams ("make the change easy"), then slices |
| Field guide | starts empty, grows | seeded from survey (fragile areas, real commands) |
| Code standards | template installed at A2; lint from ticket 1 | template adapted to existing idioms; lint ratcheted (new violations only); moving old code toward the rules only via planned prefactor tickets |
| Megafile check | from ticket 1 | only on files that grow past threshold in the change |
| Blast map | drafted from INTENT.md catastrophes + skeleton architecture | proposed by the survey from existing code; B3 zones usually already exist |
| Ledger | starts empty | seeded with discovered de-facto decisions (`status: inferred`) only where tickets depend on them |

## 5. Skill inventory (one-punch plugin)

| Skill | Change |
|---|---|
| **`steer`** (new) | Front door. Runs H1 → A1 → H2 → A2, and H3 per milestone; `resume` reports where the effort is. Replaces `start` (whose dependency-freshness checks move here). |
| **`decision-memo`** (new) | Memo format and the altitude rule; used at H2 and H3. |
| **`field-guide`** (new) | Format, budget, curation rules. Small. |
| **`code-style`** (new) | Appendix A template with repo slots, lint packs per language (hard-fail vs soft-cap), the Layer 3 review rubric, and the rule lifecycle. Used by `steer` (A2) and reviewers. |
| **`blast-radius`** (new) | Level definitions, blast-map format, default pattern pack, the scrutiny ladder, domain checklists (references/). Used by `steer` (A1/H2/A2), the harness (detector, evidence check), the oracle test author and the lens. |
| **`worker-harness`** (changed) | Builds the imperative shell v3 cut (ticket 13): `run --parallel N` (§3.4) with worktree-per-ticket, stop conditions, and `resume`. `core.py`: `select_batch()` (disjoint `Touches`), v4 ticket-header parsing. New `integrate` script (§3.5) with ref/Touches/**blast/scrutiny-evidence**/megafile checks, the B3 `AWAITING-OPERATOR` hold, and ledger events. Handoff schema. Launchers kept: `claude_p` for workers, `codex_p` for cross-vendor lenses (§3.9). **Blocked by the §8.1 spike.** |
| **`intent`** (changed) | One sitting, H1 question set (incl. catastrophes), risk register; overlay offered, not default. |
| **`retro`** (changed) | Adds v4 metrics (§6). |
| **`learning-gates`** | Unchanged content; opt-in only (proposed when INTENT.md names a learning goal). |
| `spike`, `contract-review` | Unchanged (re-earn clause stands). |
| **`start`** | Removed after `steer` lands (history keeps it). |
| Merge agent | No new skill: the harness launches it headless with mattpocock `resolving-merge-conflicts` discipline. Revisit if conflicts prove frequent. |

Composed, never copied: mattpocock `grilling`, `wayfinder`, `prototype`,
`research`, `to-spec`, `to-tickets`, `tdd`, `code-review`,
`resolving-merge-conflicts`; superpowers worktree and verification discipline.
All skills stay Agent-Skills-standard and harness-neutral ("if the harness
offers isolated background subagents…, else run tickets sequentially").

## 6. Validation — how v4 earns its seat

**Trial 1 (greenfield):** the next fresh effort. **Trial 2 (brownfield):** one
real change in an existing repo (candidate: a slipstream or evidence-kit
feature). Each trial's retro reports:

| Metric | Bar (pre-registered) |
|---|---|
| Operator turns, H1 → first build dispatch | ≤ 3 sittings; turn count recorded |
| Wall-clock, effort start → first runnable artifact | < 1 day (ckb: 8 days, none) |
| Wall-clock, H1 → first merged ticket | recorded (no prior baseline) |
| Merge conflicts per merged ticket | recorded; > 0.3 triggers a Touches-granularity review |
| Integrate verify-fail rate by tag × blast × model | recorded; feeds tier ledger |
| Decisions reopened after build started, and rework they caused | recorded; any reopened fork that H2 should have asked = altitude-rule defect |
| Token share planner vs workers (quota proxy) | recorded; compare to Cursor's ≥69% worker share |
| Escaped defects (found after merge) by blast level | recorded; **any escaped B3 defect triggers a retro of the B3 ladder** |
| `BLAST-ESCALATION`s (planner under-classification) | recorded; recurring pattern → extend the blast map / pattern pack |
| Share of tickets at B3, and operator minutes per B3 review | recorded; B3 share > 20% → A2's isolate-the-blast rule is failing |
| Static-analysis warnings and complexity per merged KLOC; clone-level duplication % | recorded per milestone; a rising trend across milestones (the He et al. pattern) triggers a Layer 2 review |
| Layer 3 rubric findings per milestone, by rule | recorded; feeds the rule lifecycle |
| Field-guide entries that a later worker cited | recorded; zero after a milestone → question the skill |

**Kill/revise clauses:** if Trial 1 exceeds 3 operator sittings before first
dispatch, or produces no runnable artifact inside a day, the front half is
revised before Trial 2. If disjoint-`Touches` batching leaves average
concurrency < 2 over a milestone, revisit ticket granularity before adding
merge machinery.

## 7. Out of scope for v4

Custom VCS or shared CoW workspaces; recursive subplanners; accepted error
rate on the integration branch; a headless *planner* (workers are headless,
the planner stays the operator's session); per-ticket mid-run steering
(steering is between runs); peer-to-peer worker coordination; a standing
integrator agent; N > 4 tuning.

## 8. Resolved choices and the gating spike

Resolved by the operator 2026-09-24:

- **Build loop:** option C — `harness run --parallel N` launched from the
  planner session (§3.4). Rejected: A (session dispatches native subagents —
  Opus does bookkeeping, session must stay open, Claude-only workers, relies
  on unverified subagent-worktree behavior); B (standalone only — loses the
  planner session's between-batch steering loop).
- **Critical-ticket lens:** a different vendor via `codex_p` when available,
  else a fresh Opus reviewer with codebase + ticket + diff only (§3.9).
- **Scrutiny is a function of blast radius** (operator principle): §2b, applied
  at H1, A1, H2, A2, H3, routing, scheduling, integrate, licensed breakage,
  review, metrics. Proposed specifics awaiting ratification: the four levels,
  the ladder values, operator diff review at B3, and the v3 tag split.
- **Code standards in three layers** (§3.11): approved 2026-09-24; the
  Appendix A rule text awaits operator review. Optional experiment for Trial
  2: run a ticket subset with the Layer 1 section removed (Layers 2–3
  unchanged) to measure what the prose itself buys (K open gap).
- **Megafile threshold:** 800 lines default, per-repo in `harness.toml`.
- **`D-NNN` refs in tests:** encouraged, not checked.
- **Worktrees:** `.worktrees/<ticket>`, git-ignored, created and removed by
  the harness (removed after integrate; kept on failure for salvage).

### 8.1 SPIKE FIRST — blocks every `run`/`integrate` ticket

Claims the loop depends on that no transcript has verified (v3 §1.1: they
enter the contract only via a `spike` transcript):

1. `claude -p` (headless) launched with its working directory inside a
   `.worktrees/<ticket>` worktree commits to that worktree's branch and
   nothing else.
2. Four concurrent headless sessions on the operator's subscription: rate /
   concurrency limits hit, and the error shape when they are (feeds the usage
   governor).
3. The permission mode and tool allowlist a headless worker needs to edit,
   test and commit without prompting, and that `claude_p`'s isolation intent
   (deny-read walls) is still expressible on the current CLI build.
4. A headless worker can load the operator's plugins/skills (`tdd`) or,
   if not, what the preamble must carry instead.
5. `codex_p` smoke on the current Codex CLI build (lens path).

Fallback if (2) caps below 4: lower the default N to the measured ceiling;
the design is unchanged.

## Appendix A — default `Code style` section (one-punch template; slots in `<…>`)

```markdown
## Code style

1. **Pure core, thin shell.** Decision logic lives in `<core dirs>` and is pure:
   its result depends only on its arguments, with no I/O, clock, randomness, or
   mutation of inputs. DB, network, filesystem and time live in `<shell dirs>`,
   which receive their handles as parameters, never through imported
   singletons. Logging is fine anywhere. Why: pure code tests without mocks.
   Pattern: `<reference file>`.
2. **Each layer changes the abstraction.** Top-level functions sequence named
   steps, mid-level functions compose leaves, and leaves do one concrete job.
   Keep each body at one level. Inline a function that only forwards, and a
   single-use helper that can't be understood without its caller.
3. **One responsibility, fully named.** A module or function does one thing
   you can state without "and", and its name covers all of it. Modules stay
   deep: few public functions over substantial behavior. Split instead of
   adding a boolean flag parameter.
4. **Compose; inherit only to implement an interface** or where the framework
   requires it.
5. **Write for the next reader.** Plain constructs, early returns, names sized
   to their scope. Comments state contracts and why, never what the code does
   or how it changed.
6. **Fail loudly.** Never swallow an error or fall back to a silent default.
   First design error cases away (idempotent operations, clamps); handle the
   rest where something can act on them.
7. **Parse at the boundary.** Turn external input into precise types once, at
   the edge; inside, trust the types and skip re-validation.
8. **Explicit and immutable.** Pass collaborators in; add no mutable globals,
   singletons or module caches; don't mutate arguments.
9. **Build what the ticket asks.** No speculative parameters, flags, config or
   one-implementation interfaces. Tests and clarity refactors within `Touches`
   are always in scope.
10. **Delete what you replace:** no dead code, commented-out code or compat
    shims unless the ticket asks for them.
11. **Deduplicate knowledge, not text.** A rule that must change in lockstep
    lives in one place; look-alike code stays separate until a third copy that
    changes for the same reason.
12. **Observable behavior is the interface.** Refactors keep outputs, error
    types and messages, and ordering unless the ticket says otherwise.
13. **Match the repo.** Reuse existing helpers and conventions before adding
    new ones; the formatter and linter config are authoritative.
14. **Hot paths may trade these for speed** when profiled and marked
    `PERF: <why>`.
```

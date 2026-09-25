# one-punch v4 — steer then swarm, scrutiny by blast radius

**Status:** LIVING copy. This document is one-punch's design authority.
**Date:** 2026-09-24 (v4). **v4 provenance:** the ratified plan
([2026-09-24-v4-steer-then-swarm-plan.md](2026-09-24-v4-steer-then-swarm-plan.md),
including its §9 execution deviations), which holds the detail this document
compresses. Evidence:
[v4 outside evidence](../evidence/2026-09-24-v4-outside-evidence.md) (the ckb
cold-start stall, Cursor's swarm posts, superpowers and mattpocock-skills
practice, slipstream, idea-gen D26; cited as `E§n`),
[code-style canon](../evidence/2026-09-24-code-style-research-canon.md) and
[code-style critiques + agent evidence](../evidence/2026-09-24-code-style-research-critiques-and-agents.md).
**Supersedes:** v3 (2026-08-08), preserved in git at `f08a27a`; v3's own
provenance is §14. v2 (2026-07-27) and v1 provenance are §§15–17.

This document states policy and names instruments. Mechanism lives in the
skills it names, and every mechanism contract has exactly one home, named
where this document uses it: the ticket header (`steer`), the full scrutiny
ladder and the domain checklists (`blast-radius`; §3 states the levels and
the B3 row as policy), stop conditions, exit codes, routing floors,
configuration and the handoff schema (`worker-harness`). Rationale and
detail live in the plan. Three copies of a contract drift; one plus
pointers does not.

**Section map.** The harness code and the plan cite v3 section numbers; they
resolve here as: v3 §0 → §15 · §1 → §1 · §2 → §2 · §3 → §2.2 · §4 → §4 ·
§5 → §16 · §6 → §17 · §7 → §7.3 · §8 → §8 · §9 → §10 · §10 → §11 · §11 → §12
· §12 → §13. The plan's "principle n" is v4.n in §1.

## 0. Why v4

v3's front half was tried from a cold start on ckb (2026-08-08 → 2026-08-16):
`start` → intent with the private overlay → evidence pass with fork-or-build
→ a learning file → a wayfinder map of 16 decision tickets and 2 learning
gates → 4 decisions resolved → a pivot that sent 5 tickets back to fog → 11
build tickets cut. **Zero code was built; the effort was abandoned** (E§1.1).
The operator's attribution: too many human turns; ceremony before value, with
days of setup and no early runnable artifact; serial decisions, one per
session, with agents idle while the operator was the bottleneck; and the
wrong altitude, asking about craft the agent should have decided.

The operator's report (2026-09-24): the v3 front half was "too onerous". The
operator wants more steering than a headless swarm and far fewer touchpoints
than v3, and a back half that runs about four agents in parallel on a
subscription budget. Cursor's swarm posts supplied a working shape for that
back half (planners that never implement, workers that never plan, a neutral
merge agent, a field guide) and superpowers supplied its measured limits
(E§1.2–1.3). E§2 tabulates which v3 elements the evidence contradicts,
confirms, or leaves as gaps.

**What replaced what.** Serialized decisions (v3 principle 2) and wayfinder
as one human session per ticket → a parallel agent fan-out (A1) and one
decision memo sitting (H2); wayfinder is now the planner's private tool. v3's
many small touchpoints (v3 §4) → three sittings per milestone plus B3 diff
reads (§4). Intent, evidence pass and learning gates as default openers → one
≤15-minute intent sitting, evidence as parallel lanes, and the overlay,
per-effort corpus and learning gates made opt-in. The four-value `Tag` → a
determinacy `Tag` plus a `Blast` level (§7.2). The sequential frontier
harness → `harness run --parallel N` with an `integrate` script as the only
path to the integration branch (§6). Fail-closed isolation → no isolation
walls; `integrate` guards what lands (§6.9). Per-ticket review for everyone
→ review set by blast radius (§6.8). `start` → `steer`.

## 1. Principles

**v4 deltas** (v4.n; rationale and evidence in the plan §1):

- **v4.1 Agents run ahead of the human.** Research, spikes, prototypes and
  code survey run in parallel before the operator is asked anything evidence
  can inform. The operator ratifies forks; they do not drive discovery.
- **v4.2 Question altitude.** Governing test (operator, 2026-09-24): ask only
  what the operator, in hindsight, is glad to have been asked. In practice
  that means one-way doors, product boundaries, and conflicts with recorded
  intent. Upstream "operator-invoked only" gates on composed skills are
  advisory, judged by their purpose: where v4 already serves it or the ask
  would fail the test, the planner follows the skill itself (composing by
  loading its instructions, never paraphrasing). Everything else is
  decided by the agent, recorded with a one-line rationale, and reopenable by
  ID. Fan-out ordering (0a) still orders what is asked.
- **v4.3 Planners decide, workers execute.** Every design decision has one
  owner, the planner, and one ledger row. No two tickets decide the same
  question. A worker that meets an undecided cross-ticket question takes the
  local, reversible option and flags it in its handoff.
- **v4.4 Avoid conflicts structurally, resolve them neutrally.** Tickets
  declare what they touch; the scheduler never co-runs overlapping tickets;
  residual conflicts go to a neutral merge agent, never to either worker.
- **v4.5 Scrutiny scales with blast radius** (§3). The damage a wrong change
  could do if it shipped unnoticed sets every scrutiny dial. Agents can raise
  a level, never lower it. Execution-based verification stays primary at
  every level.
- **v4.6 Ceremony is opt-in; evidence is not.** The private overlay, a
  per-effort corpus, learning gates and contract review are off by default.
  Evidence is always gathered, lightly and in parallel (§5).
- **v4.7 Code standards are enforced, not just stated** (§9).
- **v4.8 The environment carries the memory.** Decisions, negative results
  and surprises are written where the next agent reads them first (decision
  ledger, field guide), not left in transcripts.

**Standing from v2/v3** (numbering kept so v3 citations resolve):

- **0a. Goals before frames.** Every effort opens by eliciting the operator's
  intent-stack into a durable INTENT.md that every later session loads, in one
  sitting (H1). A question's value is its fan-out (how many downstream
  decisions its answer changes): ask in descending fan-out order and
  batch-ratify everything with fan-out ≈ 1. (kb evidence: one intent paragraph
  flipped six ratified decisions and surfaced a missing P0.) *Amended v4: one
  sitting; the private overlay is offered only when the operator signals
  private motives.*
- **0b. Load-bearing claims carry warrants.** The spike rule is the
  execution-warrant special case of evidence-kit's warrant × decay system.
  *Amended v4:* research runs lake-first at retrieval grade, scoped to open
  forks and risks; a per-effort graded corpus is opt-in; v3's fork-or-build
  gate is now the H2 reuse fork (§5).
- **1. Mechanism truth comes from execution, never prose.** A claim about an
  external system enters a contract only via a spike transcript.
- **2.** *Superseded by v4.1* ("decisions are serialized, one at a time, with
  the human"): ckb stalled on it (§0), and mattpocock `grilling` itself moved
  to rounds over a decision frontier (E§1.4).
- **3. Contracts are compiled, not interviewed.** A spec is the synthesis of
  decisions already resolved (and spike-verified where behavioral), written at
  the end of deciding, not the start.
- **4. Fog of war.** Don't pin what can't be seen yet. Undecidable-now items
  are listed as "not yet specified" with the milestone that will reveal them.
- **5. Verification cost scales with the change, not the artifact** — and,
  since v4, with the change's blast radius. Per-slice TDD and diff review,
  never whole-artifact re-review rounds. Prose artifacts get at most one
  adversarial pass, ever.
- **6. Instruments hold their seats on current evidence.** Anything carried
  over is provisional and carries an explicit re-earn test in its own file.

## 2. The pipeline

### 2.1 Stages

Three human sittings per milestone (H1 once per effort) alternate with three
agent stages. The planner is the operator's interactive session.

| Stage | Who | Instrument | Output | Operator |
|---|---|---|---|---|
| **H1 — intent + destination** (once per effort, one sitting, ≤15 min target) | operator + planner | `intent`, invoked by `steer` | `INTENT.md` (≤1 page) including **Catastrophes** (seed of the blast map) and a **risk register** (`R-n`, each with a kill/pivot criterion) | answers one fan-out-ordered round, conversationally |
| **A1 — parallel fan-out** (≤4 concurrent agents, timeboxed) | background agents; planner drafts the decision map privately (mattpocock `wayfinder` as its own tool) | `steer` lane briefs: **risk** lane — `spike` per top `R-n`; **shape** lane — mattpocock `prototype` / walking skeleton, or a brownfield code survey with a blast-map proposal (`blast-radius`); **safety net** (brownfield) — characterization tests; **prior art** — reference dossiers; **evidence** — evidence-kit retrieval-grade pass (§5) | findings on disk; blast-map proposal; brownfield field-guide seed | none, unless a lane hits a kill criterion: that stops the fan-out and is an H2-now event |
| **H2 — decision memo + demo** (one sitting; follow-up rounds in the same sitting) | operator + planner | `decision-memo`; mattpocock `grilling` rounds for newly unlocked forks; `blast-radius` for the map | ratified forks (reuse fork included), updated risk register, ratified blast map, batch-ratified defaults `D-NNN` | decides forks only; reopens any default by ID |
| **A2 — compile** | planner | decision ledger `docs/decisions.md`; mattpocock `to-spec` only when handoff-sized (otherwise the ledger + INTENT.md are the contract); mattpocock `to-tickets` plus the v4 fields (§7.1); `code-style` installs Layer 1; `field-guide` index; `Blast:` per ticket (`blast-radius`) | ledger, tickets cut to isolate the blast, integration branch `integrate/<effort>` cut from `main`, one-screen ticket-graph summary with the B3 count | veto window, not a gate: building starts unless the operator objects |
| **Build** | headless workers, ≤4 at once | `worker-harness`: `harness run --parallel N` and `integrate` (§6); workers use mattpocock `tdd` at the ticket's seams; conflicts go to a merge agent with mattpocock `resolving-merge-conflicts` discipline | merged tickets on an always-green integration branch; handoffs; JSONL event ledger | reads B3 diffs before they merge; steers between runs when the run stops |
| **H3 — milestone demo + merge** (recurs) | operator + planner | mattpocock `code-review` over the milestone diff; `decision-memo` mini-memo for forks unlocked by building; evidence-kit decay recheck; `retro` at milestones | milestone report (every B2/B3 change with its evidence, every blast escalation) | sees it running, accepts or redirects, decides the merge to `main` |

Plan §2 holds the H1 question set, the A1 lane table, the memo format and the
A2 rules; the named skills carry them.

### 2.2 Instruments

one-punch's own skills (roster per plan §5):

- **`steer`** — the front door: runs H1 → A1 → H2 → A2, and H3 per milestone;
  owns the A1 lane briefs, the prior-art dossier format and the evidence lane;
  `resume` reports where the effort is. Replaced `start`, removed in v4
  (git history keeps it).
- **`intent`** — H1: one sitting, catastrophes, risk register; overlay
  offered, not default.
- **`decision-memo`** — the altitude rule and the memo format, at H2 and as
  the H3 mini-memo.
- **`blast-radius`** — levels, blast-map format, default pattern pack,
  scrutiny ladder, domain checklists. Used by `steer`, the harness, the
  oracle test author and the lens (§3).
- **`code-style`** — the three-layer standards system (§9).
- **`field-guide`** — format, budget and curation of the field guide (§6.6).
- **`worker-harness`** — routing, `harness run --parallel N`, `integrate`,
  salvage, the event ledger and `resume` (§6, §8).
- **`spike`** — settles how an external system behaves by executing
  throwaway code; the output is a probe transcript (command · trimmed output ·
  versions · date) recorded on the decision or risk that asked. Carries
  principle 1.
- **`contract-review`** — one adversarial round over a compiled contract, on
  the operator's explicit request only; not a stage. Re-earn clause in its own
  file: two consecutive invocations with zero findings the operator judges
  worth fixing → delete it. Zero invocations so far; the clause stands.
- **`retro`** — evidence memos and amendments (§11).
- **`learning-gates`** — opt-in, proposed when INTENT.md names a learning
  goal (§12).

Composed, never copied: mattpocock `grilling`, `wayfinder`, `prototype`,
`research`, `domain-modeling`, `to-spec`, `to-tickets`, `tdd`, `code-review`,
`resolving-merge-conflicts`; the evidence-kit method; superpowers worktree and
verification discipline. The merge agent has no skill of its own; the harness
launches it headless (revisit if conflicts prove frequent).

### 2.3 Milestones, greenfield and brownfield

A destination larger than one build batch (rule of thumb: >15 tickets or >1
day of worker time) splits into milestones. Each milestone runs A1 (only
lanes with new risks) → H2 (only newly visible forks) → A2 → build → H3.

Greenfield and brownfield run one pipeline with two A1 lane sets: greenfield
builds a walking skeleton and drafts the blast map from INTENT.md's
catastrophes; brownfield surveys the code, pins current behavior with
characterization tests, seeds the field guide and the ledger (`status:
inferred`, only where tickets depend on it), ratchets lint to new violations,
and starts with prefactor tickets at the seams. Full comparison: plan §4.

## 3. Blast radius — the scrutiny axis

A change's **blast radius** is the worst plausible damage if it is wrong and
the error ships unnoticed. Four factors: **irreversibility** (data lost or
corrupted, money moved, messages sent), **exposure** (crosses a security or
privacy boundary), **breadth** (fan-in: modules, users, later tickets that
depend on it), **silence** (fails quietly; passes every happy-path test).

| Level | Typical code |
|---|---|
| **B0 contained** | tests, docs, dev scripts, prototypes, internal tooling, copy |
| **B1 local** | feature code behind a seam, one module; failures loud and reversible |
| **B2 wide** | shared core, public interfaces, additive schema, concurrency, caching, hot paths, build/CI config, dependency upgrades |
| **B3 severe** | authn/authz, sessions, crypto, secrets; money; transactions and isolation; destructive or irreversible data operations; PII; tenant/permission boundaries; untrusted-input parsing at a trust boundary; deploy/infra; **process and rule files** |

Silent + irreversible ⇒ B3 regardless of size. **Process and rule files**
(`AGENTS.md`, `.claude/`, the blast map, the decision ledger, the field guide,
`harness.toml`, lint/formatter config, verify commands, the harness itself)
are B3 in the default blast map. This is gate integrity: agents loosen their
own checks to reach green (plan §9, imported from outrigger).

**Assignment** is the maximum of three sources and is never lowered by an
agent: the **blast map** (`docs/blast-map.md`, path globs and content
patterns, proposed in A1 and ratified at H2); the **planner's declaration**
per ticket at A2 (`Blast: B3 — <reason>`); and the **diff detector** in
`integrate`, which recomputes blast from the actual diff and emits
`BLAST-ESCALATION` (not merged, re-routed at the higher level, work salvaged)
when it exceeds the declaration. Only the operator lowers a level, as a
ledger row. Detector false positives cost one extra review; accepted.

**The scrutiny ladder** sets, per level, who decides the design, whether a
spike is mandatory, the implementer floor, who writes the tests, which
automated review runs, whether the operator reads the diff, scheduling,
merge-conflict handling, build-vs-reuse default, and structure. Each level
includes everything below it. The `blast-radius` skill owns the ladder and
the domain checklists. Load-bearing points:

- **B0–B1** take the lightest path, so the scrutiny budget concentrates where
  damage lives.
- **B2** design decisions are flagged defaults; review adds a spec verdict;
  every B2 diff is listed at H3; a proven reference is preferred.
- **B3** design decisions are always operator forks; every security or
  consistency semantic relied on is spiked; the implementer is Opus;
  acceptance tests are written first by an independent agent from the ticket
  and the domain checklist; a decorrelated lens reviews; decision logic is
  pure and property-tested with a shell thin enough to read line by line; the
  default is a vetted library or reference, and hand-rolling is an operator
  fork; **the operator reads the diff before it merges.**

A2 **isolates the blast**: B3 code sits behind narrow seams and is touched by
as few, as small tickets as possible, with B3 core and its B1 surroundings in
separate tickets.

## 4. Human-touchpoint policy

*Supersedes v3 §4*, which held that more, smaller touchpoints were "the
point". ckb measured the cost of that count (§0; E§2). v4 moves the
operator's attention from craft questions, which it removes, to forks and to
the few diffs where damage lives.

The operator appears at:

1. **H1**, once per effort: one sitting, ≤15 minutes target.
2. **H2**, per milestone: one sitting; forks only; follow-up rounds happen in
   the same sitting, never as new sessions. An A1 lane that hits a kill
   criterion brings H2 forward.
3. **A2 ticket-graph summary**: a veto window, not a gate.
4. **B3 diffs**: read before merge. `integrate` holds the ticket
   `AWAITING-OPERATOR` with a review packet; the run continues with other
   tickets. This deliberately reinstates one per-ticket touchpoint, and only
   here: LLM judges caught 5% of real bugs in D26 exp-01, and at B3 the
   failure is silent and irreversible.
5. **Between runs**, when `harness run` stops (§6.2): the planner session
   surfaces parked decisions and the operator steers. There is no mid-run
   steering.
6. **H3**, per milestone: demo, accept or redirect, merge to `main`.

Reserved to the operator: every fork (one-way doors, product boundaries,
conflicts with intent, every B3 design decision, the reuse fork, the blast
map); lowering a blast level; confirming absence claims; promoting a model
tier (via retro); owning `AGENTS.md`. Everything else is agent-decided,
recorded, and reopenable by ID. **Bar:** ≤3 operator sittings from H1 to the
first build dispatch (§11).

## 5. Evidence in the front half

Evidence is gathered in every effort, lightly and in parallel; heavier
evidence is proposed only when the effort shows the need. Method: evidence-kit,
composed; lane briefs and the dossier format: `steer`. Detail: plan §2 A1/H2,
§2b, §3.2, §3.5.

- **A1 prior-art lane.** Codebases that already solve the problem (operator
  seeds from H1 first), each cloned at a pinned SHA with one reference
  dossier: what it solves and how, evidence it works (stars are not
  evidence), license, and a recommended reuse mode — `dependency` / `fork` /
  `port` / `pattern`.
- **A1 evidence lane.** An evidence-kit retrieval-grade pass into the
  evidence lake, lake-first: reuse existing holdings, write new ones back. A
  question that cannot name the fork or `R-n` it could change is dropped. A
  per-effort corpus is opt-in.
- **Lane budget.** All lanes share the ≤4-agent cap; risk spikes first, then
  prior art, then evidence. Any risk that would land in a B3 zone is spiked
  in A1, not deferred.
- **H2.** The reuse fork is always asked when prior art exists (a one-way
  door by definition). Every fork cites its evidence and its evidence-kit
  tier. A one-way-door fork resting on external claims triggers an
  adversarial-grade pass before ratification; this is the only automatic
  escalation of evidence weight. Absence claims are never asserted from the
  corpus alone; the operator confirms them.
- **Build.** A ticket's `Reference:` field points the worker at a proven
  implementation with its ratified reuse mode; `integrate`'s attribution check
  requires third-party notices and an allowed license for `port` and `fork`.
  B2 prefers a proven reference; B3 defaults to a vetted library or reference.
- **H3.** Fast-decaying facts the build rests on (pricing, vendor behavior,
  library versions) are rechecked on evidence-kit's decay schedule before the
  milestone is accepted.

## 6. Build loop

Detail: plan §3; mechanism: `worker-harness`. The plan's §8.1 gating spike
ran on 2026-09-25: headless workers commit unattended in their own
worktrees under `bypassPermissions`, the concurrency ceiling is ≥4, and the
`codex_p` lens runs read-only (rows in [vendor-smoke.md](../vendor-smoke.md)).
Workers' skill-availability self-reports proved unreliable, so worker
guidance goes inline in the preamble (§6.7). If a re-smoke measures a
ceiling below 4, the default N drops to it; the design is unchanged.

### 6.1 Roles and models

| Role | Who | Model | Never |
|---|---|---|---|
| **Planner** | the operator's interactive session | session model (Opus) | implements; routes itself headless |
| **Worker** | fresh headless session per ticket, in its own worktree, via a launcher (`claude_p` default) | floor = max(tag × size floor, blast floor) (§8) | plans across tickets; talks to other workers; decides a ledger question |
| **Merge agent** | fresh agent, only on conflict | Sonnet; Opus if either ticket is B3 | favors either side; changes behavior beyond the two tickets |
| **Lens reviewer** | fresh agent, B3 tickets and milestones | a model different from the implementer's | edits code; sees the implementer's transcript |

Every dispatch names its model explicitly; no Fable model on any subagent.
All planner state lives on disk (ledger, tickets, handoffs, a rewritten
`planner-scratchpad.md`, the integration log); a new planner session per
milestone is normal.

### 6.2 Scheduling

The build loop is a deterministic program, not an LLM. The planner starts
`harness run --parallel N` (default 4) in the background and is notified when
it stops. It takes the frontier (tickets whose blockers are merged), selects
up to N tickets with pairwise-disjoint `Touches` (B3 never batched with a
ticket in the same blast-map zone), gives each its own worktree and branch
cut from the integration head, runs `integrate` as each worker exits, and
refills the pipe without waiting for the slowest worker. It stops when
nothing more can run unattended — decisions the planner or operator must
take, exhausted usage, or an operator stop; the stop conditions, their exit
codes and the next step for each are `worker-harness`'s. The planner then
reads handoffs, updates ledger and tickets, and relaunches. Usable
walk-away or overnight.

### 6.3 Integration

`integrate` is the only path to the integration branch: deterministic,
stdlib-only, runnable by hand. It refuses without a DONE or
DONE_WITH_CONCERNS handoff; rebases onto the integration head (a conflict
launches the merge agent, whose result re-enters at rebase); runs the
project's verify commands; then runs the hygiene checks — **ref**, **Touches**,
**blast** (§3), **scrutiny evidence** (the artifacts the effective level
requires), **attribution** (§5), **style lint** (§9), **megafile** (a changed
file crossing the threshold, default 800 lines, in this change). All green:
B0–B2 fast-forward the integration branch; B3 parks `AWAITING-OPERATOR`
(§4). It fast-forwards only the exact tree its checks ran on and re-enters at
rebase if the head moved; one writer per repository holds a `flock`. Any red
is a failed attempt under the salvage and escalation rules (§8); outcomes,
exit codes and failure tokens are `worker-harness`'s. The integration branch
is always green; `main` changes only at H3.

### 6.4 Licensed breakage

A worker may change code outside `Touches` when its ticket genuinely requires
a core change, leaving `BREAKING(D-NNN): <why>` at the site (a proposed
ledger row in its handoff if none exists) and listing it under Deviations.
The planner accepts or rejects. Breakage into a B2 zone needs planner
acceptance before merge; breakage into a B3 zone is never licensed and
becomes its own B3 ticket.

### 6.5 Decision ledger

`docs/decisions.md`, one row per decision, planner-owned (v4.3); decisions
meeting mattpocock `domain-modeling`'s ADR criteria also get an ADR. Code
that exists because of a non-obvious decision carries a `D-NNN` reference,
kept honest by `integrate`'s ref check. Row format: `decision-memo`
(filing).

### 6.6 Field guide

`docs/field-guide/index.md`, hard budget 150 lines, injected into every
worker preamble: surprises, traps, negative results, commands that actually
work. Workers propose entries; the planner is the single writer. Mechanism:
`field-guide`. `AGENTS.md` stays operator-owned rules.

### 6.7 Preamble and handoff

The preamble is short and carries only what the model doesn't know: the
`AGENTS.md` pointer, the field guide, the `Depends-on` ledger rows, the
constraints, the ticket's blast level with its required steps (and the domain
checklist for B2/B3), and the handoff contract. Workers report in a
committed handoff file; the planner reads handoffs, never worker
transcripts. The handoff schema and the reversibility grammar for
`Decisions needed` are `worker-harness`'s.

### 6.8 Review by blast radius

Per ticket, the §3 ladder: nothing extra at B0; a spec verdict (Missing /
Extra / Misunderstood vs. the ticket) for `contract` at B1 and for every B2;
spec verdict, a decorrelated lens (a different model family via `codex_p`
when available, else a fresh Opus reviewer that sees codebase + ticket + diff
only) and the operator's diff read at B3. **Milestone closure:** before H3,
re-run every merged ticket's acceptance checks against the integration head;
then mattpocock `code-review` over the milestone diff, with every B2/B3 diff
reviewed individually and the `code-style` rubric on the Standards axis.
Reviewers are read-only. Milestone findings batch into one fixer ticket; a
finding in a B3 zone becomes its own B3 ticket.

### 6.9 Worker environment (plan §9, operator 2026-09-24)

No isolation walls. Outrigger measured wall-escape prevention (deny-read,
sandbox walls, escape and boundary probes, sealed held-out suites) as not
worth its cost, and v4 has nothing to hide from workers. Workers run with
`bypassPermissions` inside their worktree; `integrate` guards what lands.
Launcher hygiene flags (no ambient hooks, MCP servers or memory) stay.

## 7. Tickets

### 7.1 Ticket format

Local markdown by default, cut via mattpocock `to-tickets` plus the v4
header block (`Status`, `Blocked by`, `Tag`, `Blast`, `Size`, `Touches`,
optional `Decides`, `Depends-on`, `Reference`). The block, its key
semantics, the body conventions and a worked example are `steer`'s
ticket-header reference; the harness parses exactly that form. Policy that
holds here:

- `Touches` is a promise `integrate` checks; a B3 ticket's `Touches` include
  its test paths, because the independent test author writes only there.
- Acceptance is machine-readable commands, because milestone closure re-runs
  them and runs nothing else.
- Constraints, not step checklists; worked examples with exact values.
  Ticket explicitness is the cost lever: vague tickets cost more worker
  tokens than a planner saves (E§1.2).

### 7.2 The v3 tag split

v3's `Tag` mixed two axes. v4 keeps `Tag` for determinacy only
(`code-complete` / `contract`) and moves risk to `Blast`: v3 `critical` → B3;
v3 `trivial` → B0 + `Size: low`. Routing floor = max(tag × size floor, blast
floor); fallback goes up freely, down never.

### 7.3 Ticket craft inherited from v1 (earned in the v2 trial)

These v1 spec conventions were used ticket-by-ticket in the trial and pulled their
weight; they are house style for ticket bodies, applied by whoever writes tickets
(they are deltas *on top of* `/to-tickets`, not a replacement for it):

1. **Determinacy annotation.** Tag a ticket `code-complete` (the spec contains the
   code; implementation is transcription + testing) or `contract` (pinned behavior,
   the seam must be read from the installed substrate at build time). *Amended
   v3/v4:* the tag feeds the routing floor together with `Size` and `Blast` (§8).
2. **Acceptance fences that cannot rot.** Every test promised in prose is gated by a
   name-grep in the ticket's checks; every negative grep is paired with a `test -f`
   on its target so it can never pass vacuously against a path that stopped existing.
3. **Error models pin message *substrings*, never whole sentences** — exact-message
   asserts reject correct rephrasings; substring pins keep oracle and implementation
   from diverging.
4. **Worked examples carry exact values** and are written to be lifted into tests
   verbatim. A placeholder that matches two structurally different values is a
   defect in the ticket.
5. **Repo conventions are numbered and quotable** (the repo's AGENTS.md); a
   convention that lives only in a ticket is requested of one implementer and
   enforced on none.

## 8. Routing and verification (v3, amended)

Tickets carry `Tag` (§7.2), `Size` (low / medium / high / very-high), `Blast`
(§3), and any learning tags (§12).

**Floors.** Each ticket has a tag × size floor and a blast floor; the
effective floor is the stronger of the two. Floors are hard: fallback goes
up freely, down never. Blast floors put B3 on the top tier and keep the
cheapest tier to B0. Both tables are `worker-harness`'s (routing floors).
**The tier ladder** (T0 strongest … T5) is operator-owned and configured per
effort (`[run] ladder`); the ledger auto-DEMOTES, only the operator PROMOTES,
and promotions ride retro evidence. T5 carries no traffic in v4 until a retro
reopens it (plan §9). The interactive operator-session model is NEVER routed
headless.

**Selection within a tier:** ε-greedy bandit (ε≈0.10–0.15; exploit
best-by-ledger, explore least-sampled) so no candidate goes unexercised; B3
(v3 `critical`) never explores; exploration only on low/med sizes; the usage
governor (per-provider spend ledger + observed limit errors + inferred
cooldowns) filters first and lowers N when limit errors are observed; ledger
stats are recency-weighted. A failed attempt retries ONE tier up with
restored debris and a root-cause note; two escalated failures park the
ticket for the operator.

**Verification depth follows blast radius** (§3, §6.8), replacing v3's
verification by tag. Completion is granted by artifacts, never claimed by
agents: `integrate` re-runs the project's verify commands after every claimed
done. Traps a cheap implementer would hit on a hard ticket reach it through
the field guide and the ticket body. Turn count beats token price: prose-heavy tickets are not routed
below Sonnet (E§1.3).

Mechanism: `worker-harness` — launchers (hygiene flags, no isolation walls,
§6.9), `harness run`, `integrate`, salvage, the JSONL event ledger (all state
a pure fold) and `resume`.

## 9. Code standards

Three layers, because agent-adopting repos showed +30% static-analysis
warnings and +42% complexity that persisted, more detailed prompting did not
reduce smells, and context files earn their cost only on repo-specific
practice (evidence: the two code-style memos; summary in plan §3.11).
Mechanism: `code-style`.

- **Layer 1 — stated.** A short `Code style` section in the effort repo's
  `AGENTS.md`, installed at A2 from `code-style`'s 14-rule template with
  repo-specific slots filled. Operator-owned; the planner
  proposes edits.
- **Layer 2 — enforced.** The project's verify commands, run by `integrate`:
  hard-fail rules fail, soft caps warn into the integration log and handoff,
  brownfield is ratcheted to new violations. Every hard-fail rule has a
  sanctioned exception, and **the exception is a decision**:
  `allow(<rule>): D-NNN` pointing at an active ledger row the planner owns,
  so a worker can't grant itself one. Retro counts exceptions per rule.
- **Layer 3 — reviewed.** A rubric for what tools cannot decide, applied on
  the milestone Standards axis and in B2/B3 spec verdicts. Reviewers flag
  violations and correctness- or requirement-relevant gaps only, never ask
  for extra abstraction or hardening.

Each decomposition rule carries its counterweight, because the listed
failure of agent code is over-abstraction. **Rule lifecycle:** a rule enters
only after a repeated mistake (field guide → `AGENTS.md`, citing handoffs); a
stated rule with no findings and no lint hits across two milestones is a
pruning candidate at retro; a rule a linter can decide moves to Layer 2.
Trial 2 alternates tickets with and without the Layer 1 section to measure
what the prose buys.

## 10. Effort lifecycle

Local-markdown tracker is the DEFAULT: the repo is fully self-contained (task
definitions, decision ledger, effort state committed or derivable from
committed artifacts; only transient logs and trajectories gitignored and
archived). Every stage's output is an on-disk artifact, so an effort can stop
and resume anytime, in any session, with `resume`. Ceremony (private
overlay, per-effort corpus, learning gates, contract review) is
model-PROPOSABLE, never model-enterable: one-line proposals at natural
pauses, at most one per turn, declined proposals not re-raised absent
material change.

## 11. Retro and validation

At milestones, effort-end, or whenever outside evidence arrives, `retro`
compiles the routing/usage ledger, gate outcomes and waivers, size audits,
and operator OUTCOME REPORTS into an evidence memo filed in one-punch
`docs/evidence/`, with proposed amendments (tier promotions, gate
recalibrations, pipeline changes). Retro is the promotion front door and the
calibration channel for §12 gates. The process is under the same regime as
the code: measured, ledgered, amended on evidence. Spend figures are quota
proxies on a fixed subscription.

v4 earns its seat in two trials: **Trial 1** greenfield (the next fresh
effort), **Trial 2** brownfield (one real change in an existing repo). The
**headline metric** is unattended tickets merged per operator intervention,
recorded per milestone; a falling trend means the build half is not earning
its keep. The full pre-registered metric table is plan §6. **Kill/revise:**
more than 3 operator sittings before first dispatch, or no runnable artifact
inside a day, in Trial 1 → revise the front half before Trial 2; average
concurrency < 2 over a milestone → revisit ticket granularity before adding
merge machinery; any escaped B3 defect → retro of the B3 ladder.

Out of scope for v4: plan §7.

## 12. Operator learning mode

Opt-in since v4: proposed when INTENT.md names a learning goal, never a
default opener. When enabled, learning goals are typed and implementation
progress gates on measured, verified learning: assessment tickets (`L-NN`)
block implementation tickets like any other edge and resolve only via
committed artifacts. Bypass exists only as a loud recorded waiver; the agent
never fakes a pass. Mechanism (goal types, assessments, bars, budget,
anti-death-spiral): `learning-gates`.

## 13. Harness agnosticism

AGENTS.md is the only agent-instructions file and stays vendor-neutral;
Claude Code reads it natively (v2.1.277+), so there is no CLAUDE.md shim.
Every skill conforms to the Agent Skills open standard (harness-neutral
wording, graceful degradation, compatibility frontmatter; e.g. "if the
harness offers isolated background subagents, run lanes in parallel, else
sequentially"). Distribution: Claude Code plugin AND skills.sh file-copy. A
vendor is claimed supported only when its dated, build-pinned smoke checklist
row passes — a green Claude row says nothing about Codex.

---

## 14. Provenance: v3 (2026-08-08)

v3 ("decisions by execution, contracts by compilation, goals before frames")
came from the ratified improvements plan
([2026-08-07-v3-improvements-plan.md](2026-08-07-v3-improvements-plan.md);
evidence: the cerebras-knowledge-base effort end to end, outrigger's frozen
capstone and smoke ledger, upstream skills v1.2.3). It added intent-stack
elicitation, the evidence pass with fork-or-build, decision memos,
tag × size routing with harness-granted completion, the effort lifecycle,
retro, learning gates and harness agnosticism. v4 keeps its routing,
completion-by-artifact, lifecycle, retro, learning-gate and agnosticism
sections (amended in place) and supersedes its serialized decisions,
touchpoint policy, default openers and four-value tag (§0). Full v3 text:
`git show f08a27a:docs/design/pipeline.md`.

## 15. Why v2 (the evidence that forced it)

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

*v4 note:* premise 1 is refined, not reversed. The operator stays in the loop
as the ratifier of forks and the reader of B3 diffs; what runs unattended is
execution of explicit tickets, gated by a script and by blast radius, not
headless design.

## 16. Provenance: v1, and what its evidence still supports

v1's outrigger arc measured real things that remain true and are inherited: spec
ambiguity survives every downstream instrument (hence grilling one question at a time,
and contracts that record decisions rather than prose that invites readings);
completion claims are worthless without artifacts (hence TDD red/green evidence and
diff review); conventions live in AGENTS.md or they are enforced on no one. What v1's
evidence does **not** support is total-spec authoring: its one end-to-end success
(goodhart-sim, 2026-07-17, $31.32) was a small greenfield build; the first
framework-coupled plan produced the four-round record above. The v1 pipeline text,
runner, and evidence appendix: git history `762edda` and earlier. v1's frozen capstone
remains at `outrigger docs/design/one-liner-to-code-complete.md@3ebe595`.

## 17. First trial (v2) — completed 2026-07-27, successful

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
  *v4 note:* ckb was that fresh effort, and the front half stalled (§0).
- **Untriggered:** `contract-review` was never invoked — nothing new was
  contract-shaped. Its re-earn clause stands at zero invocations, neither passed nor
  failed.

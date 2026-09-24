# one-punch v4 — steer-then-swarm — planning document

**Status: DRAFT — design approved in session 2026-09-24 (principles, half A,
half B with the interactive session as planner, skill inventory); this written
spec awaits operator review.** On ratification it becomes the execution
authority for v4, and `pipeline.md` is amended to v4 by the first ticket.

**Evidence base:** [../evidence/2026-09-24-v4-outside-evidence.md](../evidence/2026-09-24-v4-outside-evidence.md)
— the ckb cold-start stall, Cursor's three swarm posts, superpowers 5.0.6–6.4.1
measured corrections, mattpocock-skills 1.2.3, slipstream's build record,
idea-gen D26. Section references below cite that memo as `E§n`.

**One-line shape:** agents run ahead of the human in parallel; the human
ratifies forks against evidence in few, dense sittings; a planner that never
implements turns ratified decisions into explicit tickets; up to four workers
execute them in isolated worktrees; a script — not an agent's word — decides
what merges.

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
5. **Review scales with risk × concurrency × run length.** Execution-based
   verification is primary. Decorrelated review lenses are spent on `critical`
   tickets and milestone boundaries only. (E§3)
6. **Ceremony is opt-in.** Private overlay, evidence corpus, learning gates and
   contract review are off by default and proposed only when the effort shows
   the need (v3 §9 "model-proposable, never model-enterable" stands). (E§1.1)
7. **The environment carries the memory.** Decisions, negative results and
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
4. **Brownfield only:** which area of the code; what must not break; what the
   operator already knows is fragile.
5. **Risky assumptions:** the agent proposes a list drawn from answers 1–4;
   the operator ranks and adds. Each gets a kill/pivot criterion.

Follow-ups only where an answer changes a foreseeable decision. The private
overlay is offered only if the operator signals private motives.

**Output:** `INTENT.md` (≤1 page) with sections Goal · Done looks like ·
Audience · Constraints · Non-goals · Must-not-foreclose · **Risk register**
(table: ID `R-n`, assumption, why risky, cheapest test, kill/pivot criterion,
status).

### A1 — parallel fan-out (agents, ≤4 concurrent)

The planner launches up to four background agents at once, each with a
file-based brief and a timebox:

| Lane | Greenfield | Brownfield |
|---|---|---|
| **Risk** | one `spike` per top-ranked `R-n`, cheapest first; transcript recorded against the risk | same |
| **Shape** | walking skeleton or `prototype` answering the biggest *does-this-feel-right* question | code survey of the touched area: module map, seams, test coverage, hot/mega files |
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

### H2 — decision memo + demo (one sitting; follow-up rounds allowed)

Produced by the new `decision-memo` skill. Format:

1. **Demo:** the skeleton/prototype running, or the survey's module map.
2. **Risk register update:** each `R-n` → confirmed / killed / pivoted, with
   transcript links.
3. **Forks** (the only questions), fan-out ordered, each with: the question,
   options, recommendation, evidence link, what it forecloses.
4. **Recorded defaults:** every craft decision as `D-NNN — decision — one-line
   rationale`, batch-ratified; the operator reopens any by ID.

Forks newly unlocked by the answers come as a short follow-up round in the
same sitting (mattpocock `grilling` rounds over a frontier), never as new
sessions. Fog stays fog: undecidable-now items are listed as "not yet
specified", with the milestone that will reveal them.

### A2 — compile (planner)

- **Decision ledger** `docs/decisions.md` (§3.3) populated from the memo.
- **Spec** via `to-spec` only when the effort is handoff-sized; otherwise the
  ledger + INTENT.md are the contract.
- **Tickets** via `to-tickets`, plus the v4 fields (§3.2).
- A one-screen **ticket-graph summary** (ticket, Touches, blockers, tag, size)
  is shown to the operator. It is a veto window, not a gate: building starts
  unless the operator objects.

### H3 — milestone demo + merge (recurs)

The operator sees the milestone running, accepts or redirects, and decides the
merge to `main`. Forks unlocked by building arrive here as a mini-memo (same
format as H2, forks + defaults only).

**Milestones:** destinations larger than one build batch (rule of thumb: >15
tickets or >1 day of worker time) split into milestones. Each milestone runs
A1 (only lanes with new risks) → H2 (only newly visible forks) → A2 → build →
H3.

## 3. Half B — build

### 3.1 Roles and models

| Role | Who | Model | Never |
|---|---|---|---|
| **Planner** | the operator's interactive session (default); headless T0 is a later option | Opus (session model) | implements; routes itself headless |
| **Worker** | fresh background agent per ticket, own worktree | Sonnet default; Haiku for `trivial`; Opus for `critical` | plans across tickets; talks to other workers; decides a ledger question |
| **Merge agent** | fresh agent, invoked only on conflict | Sonnet (Opus if either ticket is `critical`) | favors either side; changes behavior beyond the two tickets |
| **Lens reviewer** | fresh agent, `critical` tickets + milestones | a model different from the implementer's | edits code; sees the implementer's transcript (codebase + ticket + diff only) |

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
Tag: code-complete | contract | critical | trivial
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

### 3.4 Scheduling (planner + harness core)

- Frontier = tickets whose blockers are merged (v3 `frontier()`).
- **Batch selection:** from the frontier, pick up to N (default 4) tickets
  with pairwise-disjoint `Touches`; ties broken by critical path, then size.
  Pure function in `core.py`, property-tested. Overlap is defined on the
  current tree: two tickets overlap if any existing file matches both
  `Touches` sets, or both sets match the same not-yet-existing path prefix.
- Each selected ticket → a worker in its own worktree branched from the
  current integration head, with the preamble (§3.8) + ticket text.
- The planner keeps the pipe full: as each ticket integrates, recompute the
  frontier and dispatch the next disjoint ticket. No waiting for the slowest
  worker (Cursor's rigid-executor failure).

### 3.5 Integration — `integrate` script (the only path to the integration branch)

Deterministic, stdlib-only, invoked by the planner per claimed-done ticket:

1. Refuse unless the worker's handoff file exists with status DONE or
   DONE_WITH_CONCERNS.
2. Rebase the ticket branch onto the integration head.
   - Clean → continue.
   - Conflict → abort the rebase, emit `CONFLICT` with both tickets' IDs;
     the planner dispatches the merge agent (mattpocock
     `resolving-merge-conflicts` discipline) with both tickets, both
     handoffs, and their `Depends-on` rows; the merge agent's result re-enters
     at step 2.
3. Run the project's verify commands (from `harness.toml`) on the rebased tree.
4. Run the hygiene checks:
   - **ref check** (§3.3);
   - **Touches check** — files changed outside `Touches` without a
     `BREAKING(D-NNN):` comment → fail;
   - **megafile check** — any changed file that crossed the threshold (default
     800 lines, configurable) *in this change* → fail with
     `MEGAFILE <path>`; the planner cuts a decompose ticket that blocks further
     tickets touching that file (pre-existing brownfield megafiles pass until
     they grow).
5. All green → fast-forward the integration branch; append an event to the
   JSONL ledger (ticket, model, tag, size, attempts, verify result, tokens
   if known, wall-clock).
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
edits. (E§1.2)

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
TDD red→green at the ticket's seams; never decide a ledger question), and
the handoff contract.

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

### 3.9 Review by tag

| Tag | Per ticket | Extra |
|---|---|---|
| `trivial`, `code-complete` | `integrate` verify only | — |
| `contract` | spec verdict (Missing / Extra / Misunderstood vs. ticket) by a fresh reviewer | — |
| `critical` | spec verdict + one **decorrelated lens**: a different model *family* from the implementer via a v3 launcher (e.g. `codex_p`) when available, else a fresh Opus reviewer with a different context (codebase + ticket + diff only, never the transcript); independent acceptance-test authorship stays per v3 §8 | — |
| **Milestone** | — | mattpocock `code-review` (Standards + Spec axes, parallel) over the milestone diff, then H3 |

Reviewers are read-only (superpowers v6.0.0). Findings are batched to one
fixer ticket per milestone, not one fixer per finding.

### 3.10 Economics

- Ticket explicitness is the cost lever (E§1.2): `code-complete` tickets let
  Sonnet/Haiku workers transcribe; vague tickets cost more worker tokens than
  a planner saves.
- Turn count beats token price (superpowers): don't route prose-heavy
  tickets below Sonnet.
- Spend is a quota proxy on a fixed subscription; the v3 usage governor stays
  as the throttle. N=4 is a default, lowered automatically when limit errors
  are observed.

## 4. Greenfield vs brownfield (one pipeline, two lane sets)

| Aspect | Greenfield | Brownfield |
|---|---|---|
| A1 shape lane | walking skeleton / prototype | code survey + characterization tests |
| First tickets | skeleton hardening, then tracer bullets | prefactors at the seams ("make the change easy"), then slices |
| Field guide | starts empty, grows | seeded from survey (fragile areas, real commands) |
| Megafile check | from ticket 1 | only on files that grow past threshold in the change |
| Ledger | starts empty | seeded with discovered de-facto decisions (`status: inferred`) only where tickets depend on them |

## 5. Skill inventory (one-punch plugin)

| Skill | Change |
|---|---|
| **`steer`** (new) | Front door. Runs H1 → A1 → H2 → A2, and H3 per milestone; `resume` reports where the effort is. Replaces `start` (whose dependency-freshness checks move here). |
| **`decision-memo`** (new) | Memo format and the altitude rule; used at H2 and H3. |
| **`field-guide`** (new) | Format, budget, curation rules. Small. |
| **`worker-harness`** (changed) | `core.py`: `select_batch()` (disjoint `Touches`), ticket-header parsing for v4 fields. New `integrate` script (§3.5) with ref/Touches/megafile checks and ledger events. Handoff schema. Dispatch stays with the planner via the harness's native isolated background subagents; the headless `run` shell remains deferred (v3 ticket 13 stays cut). v3 launchers are kept, used for cross-vendor lenses (§3.9) and as the future headless path. **Blocked by the §8.4 spike.** |
| **`intent`** (changed) | One sitting, H1 question set, risk register; overlay offered, not default. |
| **`retro`** (changed) | Adds v4 metrics (§6). |
| **`learning-gates`** | Unchanged content; opt-in only (proposed when INTENT.md names a learning goal). |
| `spike`, `contract-review` | Unchanged (re-earn clause stands). |
| **`start`** | Removed after `steer` lands (history keeps it). |
| Merge agent | No new skill: the planner dispatches with mattpocock `resolving-merge-conflicts`. Revisit if conflicts prove frequent. |

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
| Integrate verify-fail rate by tag × model | recorded; feeds tier ledger |
| Decisions reopened after build started, and rework they caused | recorded; any reopened fork that H2 should have asked = altitude-rule defect |
| Token share planner vs workers (quota proxy) | recorded; compare to Cursor's ≥69% worker share |
| Field-guide entries that a later worker cited | recorded; zero after a milestone → question the skill |

**Kill/revise clauses:** if Trial 1 exceeds 3 operator sittings before first
dispatch, or produces no runnable artifact inside a day, the front half is
revised before Trial 2. If disjoint-`Touches` batching leaves average
concurrency < 2 over a milestone, revisit ticket granularity before adding
merge machinery.

## 7. Out of scope for v4

Custom VCS or shared CoW workspaces; recursive subplanners; accepted error
rate on the integration branch; headless planner (later option, not v4);
peer-to-peer worker coordination; a standing integrator agent; N > 4 tuning.

## 8. Open questions

1. Megafile default threshold (800 lines) — language-dependent; set per repo
   in `harness.toml`? (Proposed: yes, 800 default.)
2. Should `D-NNN` refs also be required in tests that pin a decision's
   behavior? (Proposed: encouraged, not checked.)
3. Worktree location and cleanup — defer to the harness's native worktree
   tool when present (superpowers `using-git-worktrees` discipline), else
   `.worktrees/` git-ignored.
4. **SPIKE FIRST — blocks every `integrate`/dispatch ticket.** The in-session
   dispatch path (§3.4, §3.5, §5) assumes behavior of the harness's native
   isolated background subagents that no transcript has verified: does a
   worktree subagent that committed leave a named branch, where, and does it
   persist; can the parent repo rebase and fast-forward from it; is a
   worktree cut from the current integration head or from `HEAD`; can a
   background subagent invoke plugin skills (`tdd`, `spike`); how many run
   concurrently before limits bite. Per principle v3 §1.1 these enter the
   contract only via a `spike` transcript. Fallback if the spike fails:
   planner-created `git worktree add` per ticket, worker launched into it.
5. **Change from the design as presented in chat, for ratification:** chat
   §4 said "worker-harness gains `--parallel N`". Because the planner is the
   interactive session, this spec instead keeps dispatch with the planner
   (native subagents) and limits the harness to pure `select_batch()` + the
   `integrate` script; the headless multi-worker `run` shell stays deferred.

# Evidence memo — 2026-09-24 — outside evidence for v4 (Cursor swarm posts, ckb stall, superpowers/mattpocock/slipstream practice)

**Trigger:** outside evidence arrived (retro skill, "any time an outcome report
arrives"): Cursor's *Agent swarms and the new model economics* (Wilson Lin,
2026-09), read together with its two predecessors (*Scaling agents*,
*Towards self-driving codebases*, 2026-02-05). Operator outcome report the same
day: the v3 front half was "too onerous" and was abandoned; the operator wants
more steering than a headless swarm but far fewer touchpoints than v3, and a
back half that runs ~4 agents in parallel on a subscription budget.

**Proposed amendments:** [../design/2026-09-24-v4-steer-then-swarm-plan.md](../design/2026-09-24-v4-steer-then-swarm-plan.md).

---

## 1. What was measured (by source)

### 1.1 ckb — the v3 front half from a cold start (the §6 open question, now answered)

- 2026-08-08 → 2026-08-16: `start` → intent (+ private overlay) → evidence pass
  (+ FORK-OR-BUILD) → LEARNING.md → wayfinder map of 16 decision tickets + 2
  learning-gate tickets → 4 decisions resolved → pivot (buzz out, POC-first,
  5 tickets back to fog) → 11 M0 build tickets cut. **Zero code built. Effort
  abandoned.**
- Operator attribution (2026-09-24, all four selected): too many human turns;
  ceremony before value (days of setup, no early runnable artifact); serial
  decisions (one per session, agents idle while the operator was the
  bottleneck); wrong altitude (asked about craft the agent should have decided).
- **Contradicts** pipeline v3 §1.2 ("decisions are serialized, one at a time")
  and §4 ("more touchpoints than v1 … that is the point"). **Confirms** v3's
  own §3 decision-memo mechanism was the right direction but was not applied
  to the map as a whole: wayfinder still resolved one ticket per session.

### 1.2 Cursor — swarm architecture (the three posts)

Facts as stated by the source (single-vendor, self-reported, one task family;
grade: vendor research blog, not independently replicated):

- **Roles.** Planners (frontier models) decompose and delegate, never
  implement; workers (cheaper models) execute, never plan, never talk to
  other agents, write one handoff (done + notes, concerns, deviations,
  findings, feedback) to the requesting planner. Recursive subplanners at
  scale. Cursor attributes the gain to **context efficiency more than
  parallelism** — "present in the swarm at every scale … helps agent
  performance even on moderately sized tasks."
- **Failed designs (self-driving-codebases post):** peer agents
  self-coordinating via a shared locked state file (lock misuse, 20 agents →
  throughput of 1–3, agents avoided big tasks); a single continuous executor
  with all roles (slept, did work itself, claimed premature completion — "too
  many roles"); a central integrator gate (bottleneck at hundreds of workers;
  removed); requiring 100% correctness per commit at hundreds of agents
  (serialized everything; they accepted a small stable error rate plus a final
  green pass).
- **Failure modes at scale → fixes:** split-brain (planners decide design
  themselves; no two delegated subtrees decide the same question); planner
  contention (decisions in shared design docs, code carries compile-checked
  references to them, a reconciler merges contradicting docs); merge
  conflicts (neutral third-party merge agent — workers "either overwrite the
  other change or abandon their own"); megafiles (workers flag, commits
  block, an outside agent decomposes); ossification (licensed intentional
  breakage with an explanatory comment; the compiler propagates).
- **Review lenses:** decorrelated lenses (transcript vs output vs codebase
  only; different models/personalities) stack; "review is much cheaper than
  the work it audits."
- **Field Guide:** agent-owned folder, `index.md` injected at every agent
  start, line budget the only constraint; captures surprises so the next
  trajectory is shorter. Early, "promising"; expected to help more on
  codebases agents don't fully own.
- **Results (SQLite from docs, Rust, 4h):** new harness beat old in every
  model mix; conflicts <1,000 vs >70,000; hottest file 47 vs 7,771 conflicts;
  9 crates vs 54 (three duplicate SQL packages = split-brain); 9,908 vs
  64,305 LOC and 4,645 vs 19,013 LOC for equal-or-better grades.
- **Economics:** workers carry ≥69% (mostly >90%) of tokens; planner tokens
  carry most dollars. Cost $1,339 (Opus planner + Composer workers) to
  $10,565 (GPT-5.5 solo) at similar quality. A terser, pricier planner (Fable 5)
  cost less itself but its workers burned several× the tokens → larger total
  bill. **Lever: how completely the planner collapses ambiguity into explicit
  instructions.**
- **Prompting:** don't instruct what the model knows; constraints beat
  instructions ("No TODOs, no partial implementations"); avoid checkbox
  lists for deep tasks (unlisted things get deprioritized); give numeric
  ranges for scope ("20–100 tasks", not "many"); poor intent specification
  showed up directly as poor output ("converged on an architecture unfit to
  evolve … a failure of the initial specification").
- **Not applicable at our scale:** the custom VCS (1,000 commits/s), shared
  copy-on-write workspaces, recursive subplanners.

### 1.3 superpowers (installed 6.4.1; clone at 6.1.1) — measured corrections

- v5.0.6: subagent review loops in brainstorming/writing-plans **doubled
  execution time (~25 min) with no measured quality gain** (5 versions × 5
  trials); replaced by inline self-review.
- v6.0.0: merging per-task spec + quality reviewers into one reviewer with
  two verdicts, file-based handoffs, and one final whole-branch review →
  "~2× faster, ~50% fewer tokens." Unnamed subagent model silently inherited
  the top tier ("all 26 reviewers on the top tier") → model named on every
  dispatch. Controllers were caught coaching reviewers to suppress findings →
  banned. A reviewer ran `git checkout` and orphaned commits → reviewers
  read-only. A durable progress ledger added after controllers lost their
  place post-compaction ("the single most expensive failure observed").
- SDD dispatches implementers **one at a time**; parallel implementers are a
  listed red flag (conflicts). True parallelism only for independent domains.
- "Turn count beats token price": cheap models take 2–3× turns; mid-tier is
  the floor for prose-based implementers.

### 1.4 mattpocock-skills v1.2.3 — direction of travel

- `grilling` moved from one-question-at-a-time to **round-based over a
  decision frontier** (every question whose prerequisites are settled, per
  round). Facts go to subagents; decisions always to the human.
- `to-tickets`: tracer-bullet slices with blocking edges; expand–contract for
  wide refactors. `wayfinder`: HITL/AFK typing per ticket; research tickets
  parallelized via subagents; "claim by assignment" to avoid collisions.
- `code-review`: two axes as isolated parallel subagents; Fowler baseline.

### 1.5 slipstream — a large codebase built fast by agents (process evidence)

- Parallel agents in worktrees (`worktree-agent-*` branches) merged into a
  feature branch **in dependency order** via scoped integration merges; a
  pinned baseline worktree kept for A/B.
- All discipline in plain `AGENTS.md` + tests, no harness hooks:
  single-source-of-truth defaults with a **drift test** (born from an incident:
  a default hardcoded in six places, a change updated two, build stayed green);
  measurement protocol with drift control; exactness gates; **"keep negative
  results"** (103-experiment inventory with dispositions incl. reversed
  rejections; README "Measured and left out").
- Claims-audit review docs (`docs/REVIEW-*.md`) that double as forward plans.

### 1.6 Internal prior (idea-gen D26, exp-01)

- LLM judge caught 5% of real bugs vs 72% of LLM-planted ones
  (PROVISIONAL-FINAL). Bears on how much weight review lenses can carry
  relative to execution-based verification.

## 2. What it contradicts / confirms in the current process

| v3 element | Verdict | Evidence |
|---|---|---|
| §1.2 decisions serialized one at a time with the human | **Contradicted** | ckb stall; mattpocock grilling's own move to rounds |
| §4 many small touchpoints | **Contradicted** at the count v3 produced | ckb; operator report |
| §3 decision memo (craft on record, forks only) | **Confirmed**, under-applied | ckb audit; outrigger 14/10 → 2 turns |
| §1.1 mechanism truth by execution | **Confirmed** | Cursor's compiler errors as the propagation channel; v2 trial; D26 |
| Completion granted by artifacts | **Confirmed** | superpowers v6.0.0 failure list; Cursor judge/handoff history |
| §8 tag × size routing, frontier planner / cheap worker | **Confirmed** | Cursor economics; superpowers turn-count caveat bounds how cheap |
| worker-harness sequential frontier, headless shell unbuilt | **Gap** | operator wants 4-wide; ticket 13 still cut |
| Intent, evidence pass, learning gates as default openers | **Contradicted as defaults** | ckb "ceremony before value" |
| `contract-review` | Unchanged; 0 invocations, re-earn clause stands | — |

## 3. Evidence conflict, resolved rather than averaged

**Stacked review (Cursor: high ROI) vs per-task double review (superpowers:
measured overhead, no gain).** Discriminator: error *accumulation*, which
scales with concurrency × run length × blast radius. Cursor runs hundreds of
agents for hours with no human; superpowers runs one implementer at a time
with a human nearby. At 4 workers with a human planner and per-merge
re-verification, accumulation is low → execution checks stay primary, and
decorrelated lenses are reserved for `critical` tickets and milestone
boundaries. D26's 5% real-bug catch rate is a further reason not to buy
reliability with more LLM review.

## 4. Considered and left unchanged / rejected

- Custom VCS, CoW workspaces, recursive subplanners — scale-specific.
- Accepting an error rate on the integration branch — a hundreds-of-agents
  tradeoff; at 4 workers, per-merge re-verify is cheap.
- Peer self-coordination via shared state files — Cursor measured failure.
- A standing integrator *agent* gate — Cursor removed it; v4 integrates by
  script and invokes an agent only on conflict.
- Fully headless planner by default — operator chose the interactive
  session as planner (2026-09-24).

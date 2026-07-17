# One-liner → code-complete: the pipeline design

**Status:** LIVING copy — this document is one-punch's design authority and evolves
with the repo. The frozen capstone record lives at
`outrigger docs/design/one-liner-to-code-complete.md@3ebe595`. **Date:** 2026-07-17.
**Provenance:** closes the outrigger/eaitl experiment arc. Every stage below either
carries a measured number from that arc ([evidence appendix](#appendix-evidence-anchors))
or names the practice corpus it adopts (Claude Code built-ins, superpowers v6.1.1, the
cowork plugins — surveys in outrigger `docs/research/internal/longhorizon-value/`:
`plugin-corpus-survey.md`, `claude-code-artifacts.md`).

## 0. Principles (each one paid for)

1. **Determinacy at the source beats detection downstream.** The experiment's only
   shipped defect — in all three arms and the oracle — was spec ambiguity; every
   downstream instrument (gate $131, review probes ×2) missed it. Money spent making
   plans unambiguous outperforms money spent catching ambiguity's consequences.
2. **Instruments own disjoint defect classes.** PRD/interview catches operator-intent
   gaps; plan-review catches spec incoherence; per-task review catches implementation
   defects + spec drift; the independent oracle catches what review can't execute;
   whole-branch review catches cross-task issues. No instrument substitutes for another
   — this is measured, not aesthetic.
3. **Completion is granted by artifacts, never claimed by agents.** Exit 0 lies
   (permission-denied planner: $1.65, 16 turns, zero files, "grant write access");
   "agent reports success" is insufficient (superpowers' verification table, our earned
   banners). Control flow reads git state and file existence only.
4. **Humans appear only at high-leverage ambiguity.** Four gates (below). Everything
   else runs walk-away; a pipeline that pings its operator between tasks has failed.
5. **Token economics = tiering + cache-stable file contracts + fresh short sessions.**
   The cheapest correct model per role; briefs as files (not pasted history — a measured
   42k-char dispatch was 99% paste); stable prompt prefixes so caches hit; fresh
   per-task sessions keep contexts small and error-compounding bounded.
6. **Every stage is standalone and composable** (file contracts in, file contracts out,
   exit codes). Any stage can run alone; no stage requires another's existence.

## 1. Stage map

| # | Stage | Instrument | Attended? | Cost anchor |
|---|-------|-----------|-----------|-------------|
| S0 | Divergent brainstorm (optional) | `product-management:product-brainstorming` (as-is) | yes | interactive |
| S1 | PRD | `product-management:write-spec` (as-is) + blocking-Q gate | **yes — Gate G1** | interactive |
| S2 | Technical plan | **`tech-plan` (new skill — the one big authoring item)** | **yes — Gate G2a** (≤3 consolidated questions + ratification) | ~$3–6 |
| S3 | Adversarial plan review | `/plan-review` (ours, as-is; lean/full tiers) | **G2b** only if findings | $10–24 full / ~half lean |
| S4 | Execution loop | **pipeline runner (evolve ours)** driving per-task implement → two-verdict review → simplify | no — halt doors only (**G3**) | ~$3–9/task |
| S5 | End-state verification | independent test-authored oracle + `/code-review` whole-branch + arbitration | **G4**: merge decision (+ arbitration if disputes) | oracle ~$4–6/task-family; review $4–7 |

Scope rule (superpowers' decompose lesson + our 15-task surprise): if the PRD phases the
work, **one pipeline instance per phase** — S2 plans only the phase in front of it.

## 2. Stage specs

### S0 — Brainstorm (optional, attended)
Run only when the one-liner is genuinely open ("do something about onboarding"). The
skill's discipline: 5–7 distinct approaches before evaluating any, one do-the-opposite,
one remove-something, anti-early-convergence. Output feeds S1 as context. Skip freely.

### S1 — PRD (attended; Gate G1)
`write-spec` as shipped: conversational elicitation, goals-as-outcomes, **non-goals with
rationale** (the scope fence), P0/P1/P2 with P2s as architectural insurance, success
metrics with measurement methods, **open questions tagged owner + blocking/non-blocking**.
**Gate G1 (mechanical convention, no machinery):** every *blocking* open question is
answered or explicitly waived by the human, in the PRD text, before S2 starts. The PRD
is the product authority for everything downstream.

### S2 — Technical plan (`tech-plan`, the new skill; Gate G2a)
Synthesizes the three planning corpora into one skill. Inputs: PRD (authority), repo
conventions, any prior design docs (reference; conflicts → ask, don't pick).

- **Question policy** (our measured protocol: 14/10 baseline turns → 2): derive all
  craft decisions on the record; ask the human only product-boundary and one-way-door
  questions, **consolidated into ≤3 early exchanges**; >3 genuine questions = the PRD
  wasn't ready, bounce to S1.
- **Conventions → root CLAUDE.md**, numbered and quotable — the only surface review
  passes enforce (measured: conventions in specs are requested, never enforced).
- **Plan format** (superpowers `writing-plans`, adopted nearly whole): Global
  Constraints header with exact values copied verbatim; per-task **Interfaces:
  Consumes/Produces** blocks with exact signatures; **No Placeholders** (named
  plan-failures: "TBD", "handle edge cases", "similar to task N"); exact file paths;
  worked examples with exact values; task sizing = one reviewable diff, "smallest unit
  worth a fresh reviewer's gate".
- **Hybrid determinacy tiers, tagged per task** (the synthesis' core economic move):
  - `code-complete` — the plan embeds the actual test + implementation code
    (superpowers style). Kills the divergent-readings class for that task; implementer
    is transcription+testing on the **cheapest** model tier.
  - `contract` — pinned interfaces + worked examples + error model, implementation
    freedom inside (our spec style). Mid-tier implementer + review carries more weight.
  Mechanical/leaf tasks default `code-complete`; judgment/integration tasks `contract`.
  The tag drives S4's model routing.
- **Self-review** (authoring-time, free): spec coverage, placeholder scan, cross-task
  type consistency, and the **ambiguity self-check** — "could any sentence be read two
  ways? pick one and write it down" (pull-idea #7).
- **Gate G2a:** human ratifies the plan (approve-before-effect; ratification voids on
  any post-hoc edit).

### S3 — Plan review (ours; Gate G2b only when findings exist)
`/plan-review` as built and measured (first firing: 10 confirmed findings blind,
including a worked-example oracle the plan's own algorithm could not reach; one known
recall miss — it is a net, not a guarantee). Attended mode: report-only, human ratifies
rewrites (that IS Gate G2b — skipped when the report is clean). Unattended mode:
`--fix` with recorded pin precedence. Tier by stakes: `lean` for small plans/re-reviews,
full when the plan gates real build spend. Findings that survive verification void G2a's
ratification: re-ratify after amendments (cheap — a diff read, not a re-interview).

### S4 — Execution loop (machinery; halt doors = Gate G3)
The pipeline runner — our nocode runner evolved (already live-hardened: permission
bypass, ledger git-exclusion, closure-base-from-ledger, silent-no-op guards, spend
telemetry per session). Per task, all fresh headless sessions:

1. **Implement** at the tier the task's determinacy tag names. The worker prompt
   carries the superpowers implementer contract: the task brief as a file
   ("your requirements — exact values verbatim"); TDD iron law with **RED/GREEN
   evidence in the report file** (command + output both phases); focused tests while
   iterating, full suite once pre-commit; self-review before reporting; "never
   silently produce work you're unsure about"; escalation is penalty-free.
   **Status contract as a file** (`.status.json`: DONE | DONE_WITH_CONCERNS |
   NEEDS_CONTEXT | BLOCKED + concerns) — the runner parses structure, never prose.
   Routing: NEEDS_CONTEXT → re-dispatch with the missing context; BLOCKED-reasoning →
   escalate one model tier; BLOCKED-plan-wrong → **halt (G3)**.
2. **Two-verdict task review** (pull-idea #2; adapted from superpowers'
   task-reviewer template): reviewer gets brief + report + diff-package **as files**;
   verdict 1 = spec compliance (**Missing / Extra / Misunderstood** — catches both
   under-building and the unrequested `--json` flag class); verdict 2 = code quality
   (Critical/Important/Minor). "Do Not Trust the Report" stance; **⚠️
   cannot-verify-from-diff** items route to the runner, which holds cross-task context
   (pull-idea #5). Dispatch hygiene: constraints copied verbatim as the attention lens;
   **never pre-judge findings** in the dispatch — class-level FP suppression lives in
   the reviewer's own instructions, instance-level suppression is forbidden
   (pull-idea #6). Fixes: churn meter as measured, budget 3 passes (our 2-pass rule
   false-alarmed on a converging 93→8-line series), dirty-pass diff sizes recorded so
   convergence is visible; churn → fresh re-implement at escalated tier **with a
   root-cause note** (systematic-debugging: no fixes without root cause), churn again →
   halt (G3).
3. **Simplify** (built-in `/simplify`), trust-but-verify: checks re-run by the runner,
   red → mechanical revert, noted on the ledger.
4. Ledger append (resume-correct; the superpowers-convergent design), next task.

Closure: every task's checks; findings from the whole-branch review dispatched as **one
fix wave with the complete list** — never one fixer per finding (pull-idea #4; their
measured: a per-finding fix wave cost more than all tasks combined).

### S5 — End-state verification (Gate G4)
- **Independent oracle**: blind test author writes an executable suite from the specs +
  PRD acceptance criteria (machinery exists; measured: the only instrument that caught
  the shared defect — and also measured: oracle authors misread ambiguous specs, which
  S2/S3 determinacy directly mitigates). Disagreements → per-test **arbitration**
  (measured protocol); genuine spec-level disputes go to the human.
- **Whole-branch `/code-review`** at high effort (measured: complementary to the
  oracle over disjoint classes; spec-blind and spec-fed cells both add value).
- **Finishing gate (G4)**: verify-tests-before-presenting-options
  (finishing-a-development-branch), then the human takes the merge/PR decision with
  the oracle report, review findings, and spend rollup in hand. Completion is this
  gate's grant — nothing upstream may declare success.

## 3. Worker & reviewer contracts (the enforcement layer)

- Status file contract (above) — machine-parsed, prose-free control flow.
- TDD evidence contract: RED/GREEN command+output in the report file; reviewers do not
  re-run suites on trust; a fix dispatch re-runs the covering tests and appends results.
- Verification iron law in every worker prompt: no completion claims without fresh
  command evidence; pristine test output (warnings are findings).
- Review-reception rule for fix workers: if ANY finding is unclear, fix NOTHING until
  clarified — partial understanding produces wrong fixes; push back with technical
  reasoning rather than performative agreement.
- File handoffs everywhere: briefs, reports, diff packages, findings lists. Nothing
  bulk is ever pasted into a prompt; nothing bulk returns in a final message.

## 4. Model routing & token economics

| Role | Default tier | Rationale / measured anchor |
|---|---|---|
| Brainstorm / PRD / tech-plan | top tier | judgment-dense, attended, once per pipeline (~$3–6 plan) |
| plan-review | top tier, `lean` unless build-gating | $23.87 full / est. ~half lean at 15-spec scale |
| Implement, `code-complete` tasks | cheapest tier | transcription+testing; "turn count beats token price" — floor rises if turns balloon |
| Implement, `contract` tasks | mid tier | measured: prose-spec implementers below mid-tier churned 2/2 |
| Task reviewer | mid tier, scale to diff risk | $1.3–1.6/pass measured at top tier — routing cuts this |
| Escalation implementer | +1 tier from current | with root-cause note |
| Simplify | mid/top | ~$1/task measured |
| Oracle author | top tier | $4.07/suite measured; blind |
| Whole-branch review / arbitration | top tier | $4–7 measured; the "most capable model for final review" rule |

Cache rules: per-stage prompt templates are byte-stable (same prefix every session);
all variable content arrives via `Read` of files (briefs/reports/diffs) so repeated
context is cache-served; sessions are fresh-per-task and end when the task ends —
long-lived contexts pay quadratic re-read costs and compound errors. Telemetry ledger
records cost/turns/cache tokens per session (built) — the pipeline's own economics stay
measured, per-run, by default.

## 5. Human-gate policy (exhaustive)

| Gate | When | Human does |
|---|---|---|
| G1 | PRD blocking questions | answer or waive, in the PRD |
| G2a/G2b | plan ratification / confirmed plan-review findings | ratify; adjudicate rewrites |
| G3 | halt doors: post-escalation churn; BLOCKED-plan-wrong; adjudication of oracle-defect stops | judge; amend plan via recorded channel; resume |
| G4 | finish: merge/PR decision (+ arbitration disputes) | decide, with evidence in hand |

Everything else is walk-away by construction. Any new human touchpoint added later must
name the outcome-impact that justifies it (this list is the budget, not a floor).

## 6. Build list (ordered; each item small and standalone)

1. **`tech-plan` skill** — WRITTEN v0 (`plugin/skills/tech-plan/SKILL.md`); needs its
   first live trial. Adapts: spec-interview (routing), superpowers writing-plans
   (format), feature-dev (architecture options pattern).
2. **Runner evolution** (each a small mechanical delta to the existing runner):
   status-file contract + routing; two-verdict reviewer stage (adapted template, file
   handoffs); determinacy-tag model routing; churn budget 3 + diff-size trajectory on
   the ledger; root-cause note required on escalation; fix-wave closure dispatch.
3. **Oracle-stage adaptation**: author prompt consumes PRD acceptance criteria alongside
   specs (machinery exists from the experiment).
4. **Skill packaging** — DONE: this repo is the marketplace; plan-review + tech-plan
   ship as the `one-punch` plugin (install: README).
5. Nothing else. Preflight/ratification tooling, walls, and the blind merge gate stay
   available in outrigger for high-stakes profiles but are **not** in this pipeline's
   default path (measured: the gate caught 0 real defects at 5.9× cost on well-specified
   work; it returns only under weak-spec/high-stakes conditions, by explicit choice).

## Appendix: evidence anchors

- Three-arm experiment (gate 0-catch at 5.9×; 1=1=1 spec-seam defect; oracle-author
  misreads): outrigger repo: `docs/research/internal/longhorizon-value/runs/` + `runs/CORRECTIONS.md`.
- Review-probe (code review misses spec-level defects, both cells): outrigger repo: `runs/review-probe/PROBE.md`.
- plan-review first firing (10 confirmed blind incl. unreachable worked-oracle; recall
  miss; $23.87/31.6 min): `eaitl-nocode-B/plan-review-report.md` + nocode-trial README.
- Runner live incidents (headless deny-by-default exit-0; ledger `git add -A`/`clean`
  hazard; churn false-alarm on converging 93→8; 2/2 Sonnet prose-spec escalations):
  nocode-trial README + runner.py comments + arm-A ledger.
- Interview compression (14/10 → 2 turns, 0 escapes across 11 ratified specs): spec
  cascade records, outrigger repo: `docs/design/evidence-based-harness.md` D7.
- Practice corpora: outrigger repo: `plugin-corpus-survey.md` (superpowers §§2–4, 7; cowork plugins §6;
  pull-ideas 1–7), claude-code-artifacts.md (built-ins, headless facts, probe numbers).

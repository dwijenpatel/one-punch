---
name: tech-plan
description: Turn a ratified PRD into a ratifiable technical plan — conventions written to CLAUDE.md, tasks with per-task determinacy tiers (code-complete vs contract), exact interfaces restated at point of use, no placeholders, and a runner-compatible tasks.json manifest. Asks the operator only consolidated product-boundary and one-way-door questions (≤3 exchanges). Use after a PRD exists and before any implementation, or when invoked as /tech-plan [PRD path] [reference docs…].
---

# tech-plan — PRD → ratifiable technical plan

`/tech-plan <PRD file> [reference docs…]`

You are the tech lead turning a product document into an implementation plan a fleet of
fresh, context-free sessions can execute. The deliverable is a ratified plan, not code.
Two measured facts shape everything here: spec ambiguity is the defect class that
survives every downstream instrument (implementers, reviewers, and test authors all
inherit it), and operator attention is the scarcest resource in the loop (baseline
interviews burned 14 and 10 turns; the compressed protocol needs ≤3).

## Inputs and authority

- **The PRD is the product authority.** Its non-goals are a fence you never cross; its
  P0 acceptance criteria are the contract your plan must discharge; its *blocking* open
  questions must be answered or explicitly waived in the PRD text — if any are not,
  stop and send the operator back to the PRD stage rather than planning around a hole.
- **Reference docs** (prior design drafts, architecture notes) inform but never
  override. Where a reference conflicts with the PRD, ask the operator — never pick
  silently.
- **The repo** answers craft questions before the operator does: read existing
  conventions, patterns, and any prior ratified plans first. Never ask what the
  codebase already answers.
- **Scope rule:** if the PRD phases the work, plan exactly one phase. If the phase
  still spans multiple independent subsystems, propose the decomposition and plan the
  first sub-project.

## Question policy (Gate G2a's front half)

Derive every craft decision yourself — stack, layout, libraries, test framework —
under the license: recorded conventions → ratified precedent → general engineering
principles. Record each derived decision with its rationale in the plan's decision log;
the operator approves them at ratification, not by questionnaire.

Ask the operator only: product-boundary questions the PRD leaves genuinely open,
one-way doors (hard-to-reverse choices: data formats on disk, public API shapes,
distribution channels), and PRD-vs-reference conflicts. **Consolidate into at most 3
exchanges, asked early**, each option carrying pros, cons, and a recommendation whose
costs are stated. More than 3 genuine questions means the PRD is not ready — say so and
bounce to the PRD stage; a plan built on guesses is worse than no plan.

## Conventions → root `CLAUDE.md`

Before writing tasks, write (or extend — never overwrite silently) the repo's root
`CLAUDE.md` with the project-wide engineering conventions as **numbered, quotable
rules** (language/runtime, dependency policy, type-checking, test framework and layout,
error-model house rules, style). This is load-bearing: review passes enforce only what
CLAUDE.md states — a convention living in a task spec is requested of one implementer,
never enforced on any. Derive the rules from the PRD plus the repo; keep each rule one
testable sentence.

## The plan format

Write the plan under `docs/plans/<date>-<name>/`: one `plan.md` (header + decision log)
plus one spec file per task, and a `tasks.json` manifest at the repo root.

**plan.md header:**

```markdown
# <Name> — implementation plan
**PRD:** <path> (authority) | **References:** <paths>
**Goal:** one sentence.
**Architecture:** 2–4 sentences.
## Global Constraints
[Project-wide requirements copied VERBATIM from the PRD and CLAUDE.md — exact values,
version floors, dependency limits, naming rules. Every task implicitly includes these.]
## Decision log
[Each derived decision: what · rejected alternative · why · cost of changing later.]
```

**Every task spec is self-contained** — a fresh implementer sees only their own spec:

- Exact file paths to create/modify and each file's single responsibility.
- **Interfaces:** `Consumes:` (exact signatures from earlier tasks, restated here — the
  implementer learns neighboring names and types from this block alone) and
  `Provides:` (exact names, parameter and return types later tasks rely on).
- A worked example with exact input → exact output values wherever behavior could be
  read two ways. Placeholders that match two structurally different values (`<the
  digest>`) are defects — show the real shape.
- Error model: which failures throw what, with the required message *substrings* (never
  full-sentence pins — exact-message asserts reject correct rephrasings).
- `checks`: shell commands with exit codes, runnable from the repo root.

**Determinacy tier — tag every task, it drives the runner's model routing:**

- `code-complete` — the spec contains the actual code: each step shows the failing
  test to write, the command and expected failure, the implementation, the passing
  command. Implementation becomes transcription + testing on the cheapest model tier,
  and divergent readings are impossible. Default for mechanical, well-understood leaf
  tasks (parsers with pinned grammars, format emitters, CRUD plumbing, config).
- `contract` — pinned interfaces, worked examples, and error model; implementation
  freedom inside. For judgment and integration tasks where prescribing code would be
  guessing. These route to a mid-tier-or-better implementer and lean harder on review.

When unsure, prefer `code-complete` — writing the code in the plan surfaces the
ambiguity NOW, while the author who can resolve it is present.

**No placeholders — these are plan failures, never write them:** "TBD", "add
appropriate error handling", "handle edge cases", "write tests for the above" (without
the tests), "similar to task N" (repeat it — tasks are read alone), any reference to a
type or function no task defines.

**Task sizing:** the smallest unit that carries its own test cycle and is worth a fresh
reviewer's gate — one human-reviewable diff (a few hundred changed lines at most).
Fold scaffolding into the task whose deliverable needs it.

**tasks.json** (the runner's contract): ordered array of
`{"id": "<kebab-id>", "spec": "docs/plans/<…>/<file>.md", "tier": "code-complete" |
"contract", "checks": ["<shell command>", …]}`.

## Self-review (run it yourself, then fix inline)

1. **PRD coverage:** every P0 requirement and acceptance criterion points at a task;
   every task points back at a requirement (orphan tasks are scope creep).
2. **Placeholder scan** against the list above.
3. **Cross-task consistency:** names, signatures, and types used in later tasks match
   where earlier tasks define them; every `Consumes` has a matching `Provides`.
4. **Ambiguity check:** for each normative sentence — could a careful reader take it
   two ways? Pick one reading and write it down, with a negative example ("this does
   NOT mean …") where the rejected reading is tempting.
5. **Tier check:** would a cheap model mis-implement this task from its spec alone? If
   yes and the task is mechanical, upgrade the spec to `code-complete` rather than the
   model to expensive.

## Ratify, then hand off

Present for ratification (Gate G2a): the plan summary, the decision log, your ≤3
question outcomes, and the task list with tiers. On an explicit yes, record
`ratified-by` and the date in plan.md. Any later edit voids ratification.

Recommend — do not run — the next stage: `/plan-review` (report-only) over the plan
before build spend; its confirmed findings amend the plan and re-ratification is a diff
read, not a re-interview. Never assert your own plan is unambiguous; the adversarial
pass exists because authors cannot see their own trap sentences.

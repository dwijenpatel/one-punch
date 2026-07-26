---
name: tech-plan
description: Turn a ratified PRD into a ratifiable technical plan — conventions written to CLAUDE.md, tasks with per-task determinacy tiers (code-complete earned by executing the spec's own code, vs contract), exact interfaces restated at point of use, a probe ledger recording every claim about external system behavior with its command and version, checks that name the wrong implementation they reject, no placeholders, and a tasks.json manifest generated from the specs. Asks the operator only consolidated product-boundary and one-way-door questions (≤3 exchanges). Use after a PRD exists and before any implementation, or when invoked as /tech-plan [PRD path] [reference docs…].
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
- `checks`: shell commands with exit codes, runnable from the repo root. **Each check
  names the wrong implementation it rejects** — one clause suffices ("fails when the
  delay is never applied"). A check whose false you cannot name is asserting that text
  exists, not that behavior holds, and belongs as a test instead. Two shapes recur and
  both are traps: an unanchored substring match (`grep -qF 'X = 1'` passes on `X = 16`),
  and a negative check whose target file is absent (grep exits 2, `!` inverts it to 0) —
  pair every negative check with a `test -f` on the same path.

**Determinacy tier — tag every task, it drives the runner's model routing:**

- `code-complete` — the spec contains the actual code, **and you executed it while
  authoring**: each step shows the failing test to write, the command and expected
  failure, the implementation, the passing command. Implementation becomes transcription
  + testing on the cheapest model tier, and divergent readings are impossible. Default
  for mechanical, well-understood leaf tasks (parsers with pinned grammars, format
  emitters, CRUD plumbing, config).
- `contract` — pinned interfaces, worked examples, and error model; implementation
  freedom inside. For judgment and integration tasks where prescribing code would be
  guessing. These route to a mid-tier-or-better implementer and lean harder on review.

**The tier is earned by execution, not by ambition.** `code-complete` claims divergent
readings are impossible — true, but it says nothing about *wrong* readings, and unexecuted
verbatim code ships false confidence with no reader able to see it. So: extract the fences,
run them, record the result. If the code cannot run standalone at authoring time, the task
is `contract` — no exceptions, and no "code-complete apart from the integration bits".
Prescribed-but-unrun code is worse than an honest contract, because the contract at least
tells the implementer to check.

When unsure, prefer `code-complete` *and then run it* — writing the code in the plan
surfaces the ambiguity NOW, while the author who can resolve it is present; running it
surfaces the falsehood.

**No placeholders — these are plan failures, never write them:** "TBD", "add
appropriate error handling", "handle edge cases", "write tests for the above" (without
the tests), "similar to task N" (repeat it — tasks are read alone), any reference to a
type or function no task defines.

**Task sizing:** the smallest unit that carries its own test cycle and is worth a fresh
reviewer's gate — one human-reviewable diff (a few hundred changed lines at most).
Fold scaffolding into the task whose deliverable needs it.

**tasks.json** (the runner's contract): ordered array of
`{"id": "<kebab-id>", "spec": "docs/plans/<…>/<file>.md", "tier": "code-complete" |
"contract", "checks": ["<shell command>", …]}`. **Generate it from the specs' `## Checks`
fences — never maintain two hand-written copies.** They drift, the drift is invisible to
count-based review (measured: two lists differing in three tasks, both summing to the same
total), and the runner executes only one of them, so a check living in the other is a
check that never runs.

## Substrate claims — probe them or label them

A **substrate claim** is any sentence asserting how something *outside this plan* behaves:
a framework's defaults or middleware ordering, a library's call semantics, a tool's exit
codes and pattern syntax, a platform's path resolution. These carry the highest defect
density in a plan, and they are **invisible to every ambiguity instrument downstream** — a
false claim is perfectly unambiguous, so translators, adversarial readers, and reviewers
all pass it through unchallenged. It reaches the implementer as fact and fails at runtime.

Every substrate claim is one of exactly two things:

1. **Probed.** You ran it. Record the command, the trimmed output, and the version in
   plan.md's **probe ledger**; cite the row wherever the claim appears.
2. **Delegated and labeled.** The spec instructs the implementer to read the installed
   source and states what they are looking for. A delegated claim may not *also* be
   asserted as fact — "read the installed version" plus a confident restatement is the
   worst of both, because the restatement is what gets transcribed.

There is no third option. "It almost certainly does X" is the sentence that ships defects.

**Probe ledger** — a table in plan.md, one row per probed claim:

```markdown
| Claim | Probe | Result | Version | as_of |
|---|---|---|---|---|
| the retry middleware ignores `Retry-After` | `python -c "import inspect,…; print('Retry-After' in src)"` | `False` | lib 2.17.0 | 2026-07-26 |
```

Version and date are load-bearing, not bookkeeping: a probe is true of one version at one
moment, and a dependency bump silently invalidates every row. When a version floor moves,
the ledger is **re-run, not re-read**.

**Two failure modes worth naming, both measured.** First, *settings interact*: values that
are individually correct can defeat each other, so probe the combination the plan actually
ships, not each constant alone. Second, *a fix is itself a substrate claim* — an amendment
asserting "setting this flag makes the framework do X" is exactly as likely to be wrong as
the sentence it replaces, and arrives with less scrutiny because it reads as a correction.

## Self-review (run it yourself, then fix inline)

**Every item is an execution or a diff. Do not count things.** A count is what lets two
different check-lists both total 61 and read as agreement, and what lets "4 negative checks
are paired" stand when the true number is 1. Counting is the failure mode this list exists
to replace; if a step can be satisfied by arithmetic, it is written wrong.

1. **PRD coverage:** every P0 requirement and acceptance criterion points at a task;
   every task points back at a requirement (orphan tasks are scope creep).
2. **Placeholder scan** against the list above.
3. **Cross-task consistency:** diff each `Consumes` block against the `Provides` it
   names — parameter order, defaults, types, and 0-vs-1 basing. A restatement that drifts
   is worse than an absent one, because it looks authoritative.
4. **Ambiguity check:** for each normative sentence — could a careful reader take it
   two ways? Pick one reading and write it down, with a negative example ("this does
   NOT mean …") where the rejected reading is tempting.
5. **Tier check:** would a cheap model mis-implement this task from its spec alone? If
   yes and the task is mechanical, upgrade the spec to `code-complete` rather than the
   model to expensive.
6. **Run every check against the current tree** and classify each result: passes because
   the artifact already exists, fails because the task is unimplemented, or **passes
   vacuously** (a negative check whose target is absent). Vacuous passes are the ones to
   fix now — they will still be vacuous on the day they were meant to catch something.
7. **Extract and execute every verbatim code fence.** A `code-complete` task whose code
   you did not run is a `contract` task wearing a better label.
8. **Diff each spec's `## Checks` fence against `tasks.json`** command-for-command — or
   generate the manifest and make the diff impossible.
9. **Mutation-test a sample of checks:** introduce the exact violation each check claims
   to reject and confirm it goes red. A check that stays green under its own violation is
   decoration, and you will not discover that later — nothing downstream tests the tests.
10. **Probe-ledger sweep:** every substrate claim in the plan appears in the ledger or is
    labeled delegated. Grep your own prose for confident verbs about external systems
    ("returns", "defaults to", "drops", "is keyed by") and check each one lands in a row.

## Ratify, then hand off

Present for ratification (Gate G2a): the plan summary, the decision log, your ≤3
question outcomes, and the task list with tiers. On an explicit yes, record
`ratified-by` and the date in plan.md. Any later edit voids ratification.

**Every review request ships the command that performs it.** A gate that says "review
the plan", names a bare commit SHA, or points at a directory has handed the operator your
job — locating the material — at the exact moment their attention is the scarce resource
the whole protocol is built to conserve. So a ratification request carries a runnable
command *and* the exact file paths, never one or the other:

```
sed -n '/^## Decision log/,/^## Tasks/p' docs/plans/<date>-<name>/plan.md   # what to approve
cat tasks.json                                                             # what will run
```

At **re**-ratification the diff is the artifact, so lead with what changed and only then
offer the full text:

```
git show <sha> --stat                                                      # files touched
sed -n '/^## Amendments/,/^## Ratification/p' docs/plans/<date>-<name>/plan.md
git show <sha>                                                             # full text
```

Write the amendment summary into plan.md as a table — was / now / why it mattered — so the
second command answers the question without the operator reading a prose diff. A diff shows
what changed; only the table shows why it was wrong.

Recommend — do not run — the next stage: `/plan-review` (report-only) over the plan
before build spend. Never assert your own plan is unambiguous; the adversarial pass exists
because authors cannot see their own trap sentences.

**Amendments are not safe edits.** The instinct that re-ratification is "a diff read, not a
re-interview" holds only for the ratifier's *attention* — it never held for correctness.
Amendment prose is written under fix pressure, skips the self-review the original passed,
and reads as a correction, which buys it less scrutiny exactly when it deserves more.
Measured across two rounds on one plan: an amendment round introduced three new blockers,
including a fix that set a flag the framework never reads. So:

- Every amended substrate claim gets a probe row before the amendment is presented.
- Every fix ships a **regression check that fails against the defect it repairs** —
  demonstrate the red, not just the green.
- An amendment round that adds or changes mechanism prose earns a `lean` re-review, and the
  cost is small against what it catches (measured: 13 confirmed findings at roughly half
  the full tier's spend, nearly all of them in the amendment prose itself).

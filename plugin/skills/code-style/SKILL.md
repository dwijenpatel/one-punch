---
name: code-style
description: "Install and maintain a repo's three-layer code-standards system for agent-written code — a short, positive Layer-1 `Code style` section for AGENTS.md (the default 14-rule template with repo-specific slots), Layer-2 lint-pack mappings to hard-fail-vs-soft-cap enforcement plus the `allow(<rule>): D-NNN` exception convention, and the Layer-3 review rubric for what only a reviewer can decide. Use when compiling or updating a repo's AGENTS.md at plan-compile time, when wiring or auditing a project's lint/format verify commands, when a reviewer needs the Standards-axis rubric for a milestone or a spec verdict, or when deciding whether a stated rule should be promoted, pruned, or moved to Layer 2 under the rule lifecycle."
compatibility: No runtime dependency of its own. Layer 2 assumes the target repo's language has (or a wiring ticket adds) a lint/format toolchain; only the Python/ruff mappings in references/lint-pack-python.md are verified against vendor docs, the rest are recall-sourced and UNVERIFIED until checked against a real install.
license: MIT
---

# code-style — enforced, not just stated

Code standards for agent-written repos work in three layers, because linters and
review are cheap and reliable where they apply, and prose is the leftover for what
neither can decide. A worker's job is to satisfy Layer 2 as written, or take the
ticket's local, reversible option and flag the gap — never to grant itself an
exception by inventing a ledger entry (see the exception convention below).

Evidence for the shape of this skill lives in the process-authority repo's
`docs/evidence/` — the 2026-09-24 code-style canon memo and the companion
critiques-and-agents memo. Cite them from a decision or a rule change; don't
re-derive or restate their content here.

## Layer 1 — stated

At plan-compile time (A2), install [references/template.md](references/template.md)
— the default `Code style` section — into the repo's `AGENTS.md`,
filling the `<…>` slots (which directories are the pure core, which are the
shell, a reference file that shows the pattern). Keep all 14 rules; the section
runs to roughly 40 lines. Positive phrasing, one clause of *why* per rule, no
MUST/CRITICAL. The section is operator-owned once installed — the planner may
propose edits, but does not unilaterally rewrite it. A controlled trial run on
real tickets and the rule lifecycle (below) are what decide later cuts, not a
worker's preference.

## Layer 2 — enforced

The project's verify commands (run by `integrate`) enforce what a tool can
decide. Split by consequence, not by rule number:

| Hard fail | Soft cap (warn, never fail) |
|---|---|
| import boundary: core modules may not import I/O, DB, network, clock or randomness modules (import-linter / dependency-cruiser / crate boundaries) | function length ~40–60 lines (target ~25) |
| swallowed errors (bare/blind except, empty catch, unchecked errors) | cyclomatic/cognitive complexity above the repo's cap |
| unused imports/variables, commented-out code, unused exports | clone-level duplication above threshold |
| boolean flag parameters; > N parameters | inheritance depth > framework + 1 |
| mutable global state without a `D-NNN` reference; mutable default arguments | — |
| formatter drift | — |

Language lint packs map each row to concrete linter codes:
[lint-pack-python.md](references/lint-pack-python.md) (ruff, verified against
vendor docs), [lint-pack-javascript-typescript.md](references/lint-pack-javascript-typescript.md),
[lint-pack-rust.md](references/lint-pack-rust.md) and
[lint-pack-go.md](references/lint-pack-go.md) (eslint, pylint's supplementary
codes, clippy and Go tool names — all `UNVERIFIED`, recall-sourced).
Don't upgrade an `UNVERIFIED` mapping to load-bearing in a verify command
without first running the `spike` skill against the repo's actual installed
toolchain — that probe transcript *is* the verification, not this skill.

Brownfield ratchet: existing violations at the point a rule goes live are
grandfathered; changed code must not add new ones.

### The `allow(<rule>): D-NNN` exception convention

Every hard-fail rule gets a sanctioned escape hatch, because a rule applied
absolutely by every worker on every ticket hardens into "never" — including at
the site where it's wrong. A worker (or the planner, writing the ticket) marks
a specific site `allow(<rule>): D-NNN`, where `D-NNN` names an **active** row
in the decision ledger (`docs/decisions.md` by default) that says why this
site is the exception.

- **The planner owns the ledger rows.** A worker cannot grant itself an
  exception by writing an `allow(...)` comment and inventing the `D-NNN` it
  points at — that is deciding a cross-ticket question silently, and no
  worker decides a question that belongs to another ticket or to the design
  ledger. A worker that needs an exception the ledger doesn't yet have takes
  the local, reversible option (leave the hard fail red, or take the
  least-bad compliant shape) and flags the need in its handoff; the planner
  cuts the ledger row and, if warranted, a follow-up ticket.
- **The harness's ref check keeps pointers honest:** an `allow(...)` in the
  diff whose `D-NNN` has no active ledger row fails the same way a dangling
  `D-NNN` code comment does. Superseding a decision turns every site that
  cited it into a visible grep target for a follow-up.
- **Retro counts exceptions per rule.** Many exceptions clustered on one rule
  is a signal the rule is mis-drawn, not that workers are undisciplined — feed
  that into the rule lifecycle below, not into more exceptions.

## Layer 3 — reviewed

What no tool can decide is a review rubric, not a checklist a worker
self-certifies against. It feeds the `code-review` skill's Standards axis and
the milestone/spec-verdict review at any blast-radius tier that reads the
diff:

- **Over-abstraction:** single-use helpers without a standalone contract,
  pass-through functions, interfaces with one implementation, speculative
  parameters/config, new modules before a second real use.
- **Mixed abstraction levels** in one function body; names that don't cover
  what the function does.
- **Defensive code** for states the types or boundary parsing already rule
  out.
- **Observable-behavior drift** in a refactor: outputs, error types/messages,
  ordering (Hyrum's law).
- **Knowledge duplicated** — a rule that must change in lockstep in two
  places; shared helpers that grew per-caller flags.
- **Scope beyond the ticket**, or PR size out of proportion to the ticket.

Reviewers flag rule violations and correctness- or requirement-relevant gaps
**only**. Do not request extra abstraction or hardening — review pressure is
itself a documented path to over-engineered code.

## Rule lifecycle

A rule's home moves as evidence about it accumulates:

1. **Enters:** a new rule is added only after a repeated mistake — the field
   guide records the mistake and the handoffs it came from, and the planner
   promotes it into `AGENTS.md`'s `Code style` section.
2. **Prunes:** a stated rule with no Layer 3 review findings and no Layer 2
   lint hits across two milestones is a pruning candidate at retro.
3. **Migrates:** a rule a linter can decide moves to Layer 2 (a lint-pack
   entry and, if it should block, the hard-fail table) and leaves the prose.

## Using this skill

- **Planner, at plan-compile time:** install/update Layer 1 from
  `references/template.md`.
- **Whoever wires a repo's verify commands:** spike the `UNVERIFIED` entries
  in the `references/lint-pack-*.md` files against the repo's actual toolchain before a
  verify command depends on them; update the file's verification note in
  place with the probe transcript.
- **Reviewer, at any blast-radius tier that reads the diff or at a milestone:**
  apply the Layer 3 rubric above via the `code-review` skill's Standards axis;
  check any `allow(<rule>): D-NNN` in the diff against an active ledger row.
- **Retro:** apply the rule lifecycle to every stated and enforced rule.

---
name: field-guide
description: "Maintain the field guide — a short, environment-specific memory file of surprises, traps, negative results (each citing a decision ID or transcript), and working commands, held to a hard 150-line budget. Workers propose entries only through their handoff's Field-guide proposals field; this skill is for the single curator who reviews those proposals, dedupes them, cuts to stay under budget, and commits the result — never for a worker writing directly to the file. It also governs the promotion path: an entry that recurs across two or more tickets graduates into the team's stated-rules file, citing the handoffs that show the repeat, and is then removed from here. Use when curating field-guide proposals from worker handoffs, when the file is approaching its line budget, when deciding whether a recurring entry should be promoted, or when seeding a new environment's field guide from a codebase survey."
compatibility: Works in any harness with local read/write access to a plain-text file and a way to count its lines (e.g. a `wc -l` equivalent); no other tooling required.
license: MIT
---

# field-guide — the environment's memory

Decisions, negative results, and surprises belong where the next agent reads
them first, not buried in a transcript nobody replays. The field guide is
that place for anything too fast-moving, too provisional, or too
session-specific to earn a stated rule outright: it is read by every worker
before it starts, proposed to by every worker when it finishes, and written
by exactly one curator.

## What it is, and what it isn't

The field guide (a single file, conventionally named `index.md`, living
wherever this project keeps its working docs) is **fast-moving and curated**:
short entries, added provisionally, pruned or promoted as evidence
accumulates. It is not the stated-rules file (an `AGENTS.md`-equivalent, or
whatever this project calls its operator-owned conventions doc). That file
is **slow-moving and owned by the operator** — the planner may propose edits
to it, but a new rule lands there only via the promotion path below, never
directly from a worker's proposal. If you're unsure which one a fact belongs
in, ask: would this still be true and useful three milestones from now, with
no further evidence? If yes, it's a rule candidate, not a field-guide entry.

**Single writer.** Workers never edit the field guide file directly. A
worker that hits something worth recording writes it under the
`Field-guide proposals:` field of its own handoff (per this project's
worker-handoff format) and stops there. Only the curator — normally the
planner, or whoever plays that role in a smaller setup — reads proposals
across handoffs and commits changes to the file itself. This is what keeps
the budget enforceable and avoids concurrent-write contention: one owner,
one commit, no merge conflicts on a file every worker touches.

## Entry kinds

Every entry is one of four kinds, and says which kind it is (by section or
tag — see the template):

- **Surprise** — something about this environment that didn't match
  expectation and would trip up the next agent too (an implicit dependency,
  an undocumented default, a naming mismatch between two layers).
- **Trap** — something that looks safe or idiomatic but isn't here, plus the
  safe alternative. A trap without its safe alternative is half an entry;
  don't file one without the other.
- **Negative result** — an approach that was tried and rejected, with the
  reason, and a citation: a decision-ledger ID (`D-NNN`, or whatever this
  project's ID scheme is) or a link/path to the transcript that settled it.
  A negative result with no citation is a complaint, not an entry — cite it
  or drop it.
- **Working command** — a command (build, test, lint, repro, debug) that
  actually works in this environment, especially where the obvious or
  documented form doesn't. Include the command verbatim and a one-line note
  on why it's the one that works.

## Curating: from proposals to the file

1. **Collect.** Read the `Field-guide proposals:` field of every handoff
   since the last curation pass. Never read worker transcripts for this —
   if it mattered, it's in the proposal; if it isn't, it doesn't belong in
   the file.
2. **Dedupe and merge.** Two proposals describing the same surprise or trap
   become one entry. Prefer the sharper phrasing; keep both citations if
   they point to different evidence.
3. **Check the promotion path first.** Before adding or re-adding an entry,
   check whether it (or something close to it) has now shown up across two
   or more tickets. If so, it doesn't go in the field guide at all —
   propose it as a stated rule instead (see below).
4. **Enforce the budget.** The file has a hard cap — 150 lines is the
   reference budget; use whatever this project has actually configured if
   different. Count before committing (a plain line count is enough; a
   harness-side check, if one is wired up, is the backstop, not the
   primary check). Over budget, cut in this order before dropping anything
   with an open citation: (a) entries superseded by a promoted rule — they
   just graduated, remove them; (b) entries no later ticket has cited or
   restated since they were added; (c) the least specific working commands,
   if duplicated by a sharper one. Never silently drop a negative result
   that's still the only record of why an approach was rejected — promote
   it or fold its citation into a shorter line before cutting it.
5. **Commit.** One curator, one commit, ideally at the same cadence as
   milestone or integration work so the file never drifts far from what
   workers actually hit.

## Promotion path

A field-guide entry is provisional by design — that's what makes it cheap to
add. A stated rule is not: it's read by every future worker on every future
ticket, so it earns its place only after a repeated mistake, not a single
observation. Concretely:

- An entry that has recurred across **two or more tickets** — the same
  surprise tripping different workers, the same trap being walked into again
  — is promoted: propose it as a new line in the stated-rules file, citing
  the handoffs that show the repeat, then remove the field-guide entry it
  replaces.
- An entry with no repeat and no citation from later work after a few
  milestones is a pruning candidate — drop it rather than let the file grow
  without bound.
- If a later tool (a linter, a formatter, a type check) starts deciding
  something a field-guide entry used to warn about by hand, that entry is
  obsolete the moment the tool is wired in — drop it; the enforcement layer
  replaced the memory.

The direction only runs one way in the ordinary case: field guide, then
(sometimes) promoted out to a stated rule. A stated rule is not
re-demoted into the field guide — if a rule stops earning its keep, that's a
rule-retirement decision for whoever owns that file, not a field-guide
curation call.

## Seeding a field guide from scratch

A brand-new field guide starts empty and grows from real handoffs. The one
exception is a codebase survey run before any tickets exist: fold its
findings — fragile areas, non-obvious build steps, commands that actually
reproduce a build or test run — directly into the initial file using the
same entry kinds and the same budget, so day-one workers aren't the first to
discover what the survey already found.

## Template

Use [references/index-template.md](references/index-template.md) as the
starting file for a new field guide. It carries the section-per-kind
structure and the single-writer note as an inline comment, so a worker who
opens it by mistake sees the rule before it can be violated.

# Worker handoff, review evidence and acceptance commands

These are the files workers and reviewers leave for the harness and the
planner. The harness puts the handoff schema and the reversibility rule in
every implementer's preamble verbatim; this page is the planner's copy.

## The handoff

Path: `<handoffs_dir>/<ticket>.md` (default `.scratch/<effort>/handoffs/<ticket>.md`).
The worker writes it (overwriting any earlier attempt's) and **commits it on
its ticket branch as the last commit**. Integrate reads it from the branch as
committed, never from the worktree: an uncommitted handoff is a missing one.

```
Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
Commits: <sha list>
Done: …
Deviations: … (incl. any BREAKING)
Decisions needed: …
Findings / concerns: …
Field-guide proposals: …
```

| Status | What the harness does |
|---|---|
| DONE, DONE_WITH_CONCERNS | Gate `Decisions needed`, then reviews (if the level requires them), then integrate |
| BLOCKED, NEEDS_CONTEXT | Park `blocked`; nothing is integrated |
| missing or unreadable | A failed attempt (`HANDOFF-MISSING`), retried one tier up |

`Deviations` lists every licensed breakage (`BREAKING(D-NNN): <why>` at the
change site, with a proposed ledger row if none exists) and every departure
from the ticket's `Reference`. `Field-guide proposals` are curated by the
planner through the field-guide skill; workers never edit the field guide.

## `Decisions needed` — the reversibility grammar

The field is `none`, or one item per question:

```
Decisions needed:
- <question> — local option: <what you did> — reversible
- <question> — local option: <what you did> — NOT reversible
```

Items are the text after the colon on the `Decisions needed` line and each
following `-`, `*` or `1.`/`1)` bullet (continuation lines join the item), up
to the next `Field:` line. `none`, `n/a`, `no`, `-` and `—` mean no items.

An item is **reversible only when it contains the word "reversible" and no
negation**. Negations, case-insensitive: `not`, then at most two words, then
`reversible` ("not reversible", "not locally reversible"); `non-reversible`
(also `nonreversible`, `non reversible`); `irreversible`; `one-way` or
`one way`. **An item with no marker
fails closed**: it counts as not reversible.

Any not-reversible item parks the ticket (`decision`) without integrating it;
its dependents wait. `park_k` such tickets (default 2) stop the run with
DECISIONS-NEEDED. Reversible items integrate normally and are the planner's to
review between runs.

## Review evidence

Committed on the ticket branch under `<review_dir>/<ticket>/` (default
`.scratch/<effort>/reviews/<ticket>/`). Reviewers write these files; the
harness commits exactly them and rejects a review that changes anything else.
They, and the handoff, are exempt from the Touches check.

| File | Written by | Required at | Content |
|---|---|---|---|
| `spec-verdict.md` | spec-verdict reviewer | B1 `contract`, B2, B3 | Missing / Extra / Misunderstood against the ticket; a line `Verdict: pass\|concerns\|fail` |
| `lens.md` | lens reviewer | B3 | The decorrelated review; a line `Verdict: pass\|concerns\|fail` |
| `checklist-<id>.md` | lens reviewer | B3, one per domain checklist of the B2+ zones the diff hits | One answer line per checklist item, `<ID> pass\|fail\|n/a: <evidence>`, per the blast-radius skill's checklist answer grammar |

`Verdict: fail` fails the attempt (`SCRUTINY-FAILED`); `concerns` passes and is
carried into the B3 review packet. A checklist `fail` answer is a finding for
the operator, not a rejection of the review.

**Tests first (B3).** The first commit on the ticket branch that touches
anything besides the handoff and review files may touch only `test_globs`
files: the independent acceptance tests. The harness guarantees it by
dispatch order (a separate test author, before any implementer); integrate
checks the order (`TESTS-NOT-FIRST`).

## Acceptance commands (read by `closure`)

`closure` re-runs every done ticket's machine checks against the integration
head. A ticket's checks are:

- the indented lines directly under an `Acceptance:` line, and
- every line of a fenced block inside an Acceptance section (from
  `Acceptance:` or a `## Acceptance` heading to the next heading).

`#` comment lines are skipped. Prose acceptance is reported as "no acceptance
commands", so write the checks as commands:

```
Acceptance:
  python -m pytest tests/store -q
  test -f docs/store.md
```

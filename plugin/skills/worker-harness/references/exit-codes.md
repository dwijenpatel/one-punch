# Exit codes, stop reasons, park states and failure tokens

## `run.py run` — why the run stopped

The run drains in-flight workers before every stop except KILLED. The reason is
printed, recorded as a `run-stop` event, and committed with a ledger snapshot.

| Exit | Reason | Meaning | Next step |
|---|---|---|---|
| 0 | FRONTIER-EMPTY | Nothing launchable and nothing parked, awaiting or pending integrate | Milestone build done: `closure`, then milestone review |
| 3 | ALL-PARKED | Nothing launchable; some ticket is parked, awaiting the operator, or exited with its integrate pending | `resume`; clear parks (below), approve packets, relaunch |
| 4 | DECISIONS-NEEDED | `park_k` tickets parked on non-reversible `Decisions needed` | Decide, `answer` each, relaunch |
| 5 | ALL-COOLING | Every candidate that could take the remaining work is cooling after usage-limit errors | Relaunch after the cooldown (`resume` shows until when) |
| 6 | STOPPED | One SIGINT/SIGTERM, or the stop file appeared | Steer, then relaunch |
| 7 | KILLED | A second signal: every launcher's group got SIGTERM; their launches stay unmatched | Relaunch: interrupted work is torn down and redone, not counted as failed |
| 30 | REFUSED | A precondition failed before anything ran (below) | Fix the named cause |
| 31 | LOCKED | Another run or integrate holds the repository's writer lock | Wait for it, or stop it |

`answer` and `relaunch` exit 0 on success, 30 on refusal (`NOT-PARKED
<ticket>`: never launched, running, exited or merged; `answer` needs a parked
ticket) and 31 while a run holds the lock — interventions happen between runs.
`closure` also takes the lock; it exits 0 when every acceptance command passed
(GREEN), 1 otherwise (RED). `resume` takes no lock and works during a run.

Run refusals: `CONFIG-INVALID`, `INTEGRATION-BRANCH-MISSING`,
`INTEGRATION-BRANCH-CHECKED-OUT` (switch that worktree away first),
`BARE-REPOSITORY` (every command but `resume` needs a working checkout),
`BLAST-MAP-MISSING`/`BLAST-MAP-INVALID`, `LEDGER-INVALID`,
`TICKET-GRAPH-INVALID` (a dependency cycle), `FIELD-GUIDE-OVER-BUDGET`.
`LAUNCH-FAILED` and `WORKTREE-BUSY` park the one ticket (`refused`) instead.

## Park states

A parked ticket holds its dependents; the rest of the frontier keeps going.
`resume` lists each with its kind and reason.

| Kind | Cause | Clear it with |
|---|---|---|
| `decision` | Its handoff has a `Decisions needed` item not marked reversible | Decide (ledger row or ticket edit), then `answer T --note "<decision>"` |
| `blocked` | Its handoff says BLOCKED or NEEDS_CONTEXT | Supply what it asks for (ticket edit, ledger row), then `relaunch T --note …` |
| `escalation` | Two failed attempts (the second one tier up) | Read the root cause in `resume`/the ledger; recut or clarify the ticket; `relaunch T` resets the counter |
| `blast-b3` | Its diff escalated to B3; the work predates an independent tests-first commit | `relaunch T`: the B3 path runs, the old work kept as salvage |
| `stage` | A test-author, spec-verdict, lens or merge dispatch was rejected twice | Read the rejection reasons; fix the cause (e.g. B3 Touches without a test path); `relaunch T` retries the same stage |
| `conflict` | Three rebase conflicts in one implementer attempt | Resolve or re-sequence the overlapping tickets; `relaunch T` returns it to the merge agent |
| `head-moved` | The integration head moved under two judgements in a row | `relaunch T` |
| `refused` | Integrate refused for a reason a retry cannot fix (missing ticket, bad config), or the launch failed | Fix the named cause; `relaunch T` |
| `unroutable` | No ladder rung at or above the ticket's (or stage's) tier | Add a rung to `[run].ladder`; the next run routes it |

AWAITING-OPERATOR is not a park: the ticket passed every check at B3 and waits
for `integrate.py --approve T`.

## `integrate.py` — one ticket's judgement

| Exit | Outcome | Meaning |
|---|---|---|
| 0 | MERGED | The integration branch fast-forwarded to the judged commit |
| 10 | AWAITING-OPERATOR | Green at effective B3: judged commit pinned, review packet written |
| 20 | FAILED | A check or verify failed: a failed attempt |
| 21 | BLAST-ESCALATION | Effective blast above declared: re-route at the higher level, work kept |
| 22 | CONFLICT | The rebase onto the integration head conflicted; the merge agent runs next |
| 30 | REFUSED | A precondition failed (below) |
| 31 | INTEGRATE-LOCKED | Another writer holds the lock; no event is written |
| 32 | HEAD-MOVED | The head moved under `max_reentries` judgements in a row |

Refusal tokens: `HANDOFF-MISSING`, `HANDOFF-STATUS`, `TICKET-MISSING`,
`TICKET-BRANCH-MISSING`, `INTEGRATION-BRANCH-MISSING`,
`INTEGRATION-BRANCH-CHECKED-OUT`, `NOTHING-TO-INTEGRATE`, `REBASE-ERROR`,
`CONFIG-INVALID`, `BLAST-MAP-MISSING`, `BLAST-MAP-INVALID`, `LEDGER-INVALID`,
`APPROVE-NOTHING-AWAITING`.

## Check failure tokens (in the event's `checks[].failures`)

| Token | Check | Fails when |
|---|---|---|
| `VERIFY-FAILED` | verify | A verify command exits nonzero (its output tail is in `verify_failures`) |
| `VERIFY-DIRTY` | verify | A verify command modified tracked files |
| `REF-UNRESOLVED` | ref | A `D-NNN` in the diff (incl. `BREAKING(…)`, `allow(…)`) has no active ledger row |
| `TOUCHES-OUTSIDE` | Touches | A file outside Touches changed without a `BREAKING(D-NNN):` marker |
| `TOUCHES-B3` | Touches | A change outside Touches reaches a B3 zone (never licensed) |
| `BLAST-ESCALATION` | blast | The diff's effective level exceeds the declared `Blast:` |
| `LOWERING-INACTIVE` | blast | A zone lowering cites a decision that is not active |
| `SCRUTINY-MISSING` | scrutiny | A required review file (spec verdict, lens) is absent or has no `Verdict:` line, or a checklist source is missing |
| `SCRUTINY-FAILED` | scrutiny | A review says `Verdict: fail` |
| `TESTS-NOT-FIRST` | scrutiny | At B3, the first non-evidence commit touches more than test files |
| `CHECKLIST-UNANSWERED` | scrutiny | A required domain checklist lacks an answer line per item |
| `ATTRIBUTION-MISSING` | attribution | A `port`/`fork` reference has no notices entry |
| `ATTRIBUTION-LICENSE` | attribution | Its license is not in `allowed_licenses` |
| `LINT` | lint | A hard lint command reports a violation new in the changed code |
| `LINT-WARN` | lint | Same for a soft command (warning, not failure) |
| `LINT-ERROR` | lint | A lint command exited outside `lint_ok_exit` |
| `MEGAFILE` | megafile | A changed file ends over the threshold and grew in this change |

Waivers: `allow(<rule>): D-NNN` in the file, citing an active ledger row, waives
that lint rule or `megafile` for the file.

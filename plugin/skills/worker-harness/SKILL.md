---
name: worker-harness
description: "Build a milestone's tickets unattended with headless worker agents running in parallel. A deterministic loop (`run --parallel N`, started from the planner session) picks tickets whose Touches do not overlap, routes each to a model tier by tag, size and blast radius, and runs each worker in its own git worktree. It dispatches the reviews each blast level requires: an independent tests-first author, a spec verdict, a decorrelated lens, a merge agent. Work lands only through `integrate`, which re-runs the project's verify commands and hygiene checks on the exact tree it fast-forwards; an agent's word is never the evidence. The loop stops on an empty frontier, all parked, K decisions needed, all cooling, or an operator stop, and it ledgers every event. Use when an effort's tickets are cut and the operator wants walk-away or overnight execution; between runs to answer, relaunch or approve parked work; and for `resume` (\"where were we?\") on any clone."
compatibility: "Requires git and Python 3.12+ (stdlib only, nothing to install) on a Unix host (process groups, signals). Each launcher needs its worker CLI: claude (Claude Code) for implementers and reviewers, codex (Codex CLI) for the optional decorrelated lens, mini-swe-agent for local models; a launcher whose CLI is missing refuses fail-closed. Vendor CLI behavior decays: re-run a launcher's smoke after tool updates."
license: MIT
---

# worker-harness: completion is granted by artifacts

The build loop is a program, not an agent. It picks which tickets run
together, which model runs each one, which reviews each needs, and what may
land. Workers are fresh headless sessions that see one ticket each. The
planner (the operator's interactive session) cuts the tickets, starts a run,
and steers between runs. The planner never schedules by hand and never reads
worker transcripts.

## Where it lives

The harness is [references/harness/](references/harness/): stdlib-only Python,
strictly typed, split into a pure functional core and a thin imperative
shell. Run it in place and point it at the project:

```
python3 <this skill>/references/harness/run.py --repo <project> run --parallel 4
python3 <this skill>/references/harness/integrate.py --repo <project> <ticket>
```

Before the first run, the project needs:

- `harness.toml` at the repository root, with an `[integrate]` table (effort
  name and verify commands) and a `[run]` table (the tier ladder). Every key
  is in [references/configuration.md](references/configuration.md).
- The integration branch (`integrate/<effort>` by default), cut from `main`
  and not checked out in any worktree.
- On that branch: the tickets (`Status`, `Blocked by`, `Tag`, `Blast`,
  `Size`, `Touches`, and optionally `Decides`, `Depends-on`, `Reference`), the
  decision ledger, the blast map (see the blast-radius skill), and the field
  guide (see the field-guide skill).
- `.worktrees/` git-ignored.
- The CLI of every launcher the ladder names.

## The contract

1. **`integrate` is the only path to the integration branch.** Worker
   changes land nowhere else, so the branch is always green. `main` changes
   only at milestone closure.
2. **Done means the harness verified it.** Integrate rebases the ticket onto
   the integration head in a throwaway worktree, re-runs the project's verify
   commands and the hygiene checks there, and fast-forwards only that exact
   judged commit, by compare-and-swap. If the head moved meanwhile, it judges
   again.
3. **The judge reads trusted inputs.** The ticket, decision ledger and blast
   map are read from the integration head, never from the ticket's branch, so
   a change cannot loosen the checks that judge it.
4. **One writer per repository.** A `flock` is held for a whole run, or for
   one hand-run integrate.
5. **Fresh session per dispatch; files, not memory.** A worker gets a
   preamble and its ticket, and it reports in a committed handoff file. The
   preamble carries inline everything the worker needs: the rules, the
   field guide, the `Depends-on` ledger rows, the blast level's steps and
   domain checklists, any previous attempt's root cause and operator notes,
   and the handoff schema. Headless workers cannot be relied on to load
   skills.
6. **Everything is ledgered.** Every launch, exit, stage, park, judgement,
   intervention and stop is appended to a JSONL event ledger. All state is a
   fold over that ledger plus ticket `Status:` lines and `t/<ticket>`
   branches, which is why `resume` works from a bare clone
   ([references/events.md](references/events.md)).

## Launching a run

Start the run from the planner session as a background process: the shell's
`&`, or the harness's background-task facility if it has one, so the session
is notified when the run exits. Without background processes, run it in the
foreground. The same command serves attended, walk-away and overnight use:

```
python3 <harness>/run.py --repo . run --parallel 4 > run.log 2>&1 &
```

The run's pid is in its `run-start` event. The exit code names the stop
reason, and the run prints it with a `resume` report on exit.

## What a run does

Each loop iteration:

1. **Derive** state from the integration head, the ticket branches and the
   ledger. Reconcile leftovers: an interrupted dispatch is torn down and
   redone, a clean exit that has not been integrated is integrated, and a
   merge made outside the run is flipped to `Status: done`.
2. **Frontier**: tickets whose `Status` is ready and whose blockers are all
   done.
3. **Route** each ticket to a named model on the tier ladder (see
   [Routing](#routing-and-escalation)).
4. **Batch**: fill the free slots with tickets whose Touches overlap neither
   each other nor any in-flight ticket. Two tickets overlap if an existing
   file matches both, or if both may create the same new path. A B3 ticket
   never runs beside another ticket in the same blast-map zone. Ties break by
   critical path, then size, then id. Review stages of tickets already
   started take slots first.
5. **Launch** in `.worktrees/<ticket>` on `t/<ticket>`, cut from the
   integration head. Worktrees are created serially; workers run
   concurrently.
6. **As each worker exits**, gate its handoff, dispatch the reviews its level
   requires, run `integrate`, and refill the slot at once. The loop never
   waits for the slowest worker.

## Dispatch roles and models

Every dispatch names its model from the ladder; the ladder refuses unnamed
models. Tiers run from T0 (strongest) to T5.

| Role | When | Model | May write |
|---|---|---|---|
| `author` (implementer) | Every ticket | The ticket's routing floor, one tier up per failed attempt | Its Touches, plus licensed breakage and its handoff |
| `test_author` | B3, before any implementer | T0 | Only `test_globs` files inside the ticket's Touches, as the first commit |
| `spec_verdict` | After a clean exit, at B1 `contract`, B2 and B3 | The ticket's routing floor | Only `<review_dir>/<ticket>/spec-verdict.md` |
| `lens` | B3, after the spec verdict (skipped when the verdict is `fail`) | `[run] lens` (another model family) while `lens_smoke` passes; else T0 in a fresh session | Only `lens.md` and `checklist-<id>.md` in the review dir |
| `merge` | After a CONFLICT | T2; T0 when either ticket is B3 | Only a rebase of `t/<ticket>` onto the integration head, with no merge commits |

The implementer and the merge agent commit their own work. For the test
author and the reviewers, the harness commits exactly the files that role may
write. A dispatch that changes anything else is rejected and retried once; a
second rejection parks the ticket as `stage`. Reviewers see the codebase,
the ticket and the diff. The lens also gets the domain checklists, and never
the implementer's handoff or transcript. The merge agent follows the
`resolving-merge-conflicts` skill, whose steps are carried inline, and a B3
ticket's merged result goes through the spec verdict and the lens again.

## File-scope rule

- **Implementers stay inside Touches.** A change outside Touches is allowed
  only when the ticket genuinely requires it: `BREAKING(D-NNN): <why>` at the
  change site, a proposed ledger row in the handoff if none exists, and an
  entry under Deviations. Breakage into a B2 zone needs the planner's
  acceptance before it merges, and breakage into a B3 zone is never licensed.
  Integrate enforces all of this on the actual diff (`TOUCHES-OUTSIDE`,
  `TOUCHES-B3`, `REF-UNRESOLVED`).
- **Stage files by explicit path.** Never `git add -A`, never build
  artifacts. Commit on the ticket branch only; never merge, rebase, push or
  switch branches.
- **Some files are never a worker's to edit:** its own ticket, other tickets,
  the decision ledger, the blast map, `AGENTS.md` and `harness.toml`. These
  are planner or operator surfaces, and the default blast map treats them as
  B3.
- **Reviewers are read-only**, as the table above says.

## The B3 path and salvage

A declared B3 ticket runs in this order:

1. An independent test author writes the acceptance tests first.
2. The implementer makes them pass without weakening them.
3. The spec verdict runs, then the decorrelated lens, which answers every
   domain checklist the diff's zones require.
4. Integrate re-checks all of it. On green it does not merge: it pins the
   judged commit, writes a review packet to `<packets_dir>/<ticket>/`
   (README, `diff.patch`, handoff, verdicts, checklist answers,
   `packet.json`), and reports AWAITING-OPERATOR.
5. The operator reads the packet and approves the ticket between runs with
   `integrate.py --approve <ticket>`. To reject, `relaunch <ticket> --note
   "<what to change>"` instead.

**Salvage.** A lower-level ticket whose diff reaches a B3 zone escalates
(BLAST-ESCALATION to B3) and parks as `blast-b3`: its work predates any
independent tests. `relaunch` runs the B3 path. The old tip is kept under a
salvage ref, the branch restarts from the integration head with the tests
commit, and the implementer's preamble names the salvage commit to reuse.
Below B3, a failed attempt keeps its worktree and branch. The retry salvages
that work in place and carries integrate's root-cause note.

## Routing and escalation

The floor is the stronger of the tag × size floor and the blast floor. B3
always routes at T0. Fallback climbs toward T0 and never descends. Within a
tier the router exploits the best-by-ledger candidate and sometimes explores
the least-sampled one (never at B3). A failed attempt (FAILED, a failed
session, or a missing handoff) retries one tier up with a root-cause note,
and a second failure parks the ticket as `escalation`. A BLAST-ESCALATION
below B3 commits the raised `Blast:` line and retries in place, which is not
counted as a failure. The usage governor watches for usage-limit errors: an
exit whose summary matches `limit_patterns` cools that candidate for
`cooldown_s` and lowers N by one for the rest of the run. That exit is not a
failed attempt. The floor tables are in
[references/configuration.md](references/configuration.md).

## Stopping a run

- **Draining stop:** `kill -INT <pid>`, or create the stop file
  (`.worktrees/STOP` by default). In-flight workers finish and are
  integrated, nothing new launches, and the run exits STOPPED.
- **Hard stop:** send a second signal. Every launcher forwards SIGTERM to its
  worker's process group, and the run exits KILLED. Those launches stay
  unmatched in the ledger, so the next run tears them down and redoes them.
  Nothing counts as a failed attempt.
- **Never stop with a terminal ^C.** It sends SIGINT to the whole foreground
  group, including integrate's git subprocesses in the middle of a
  judgement. Signal the pid instead.

## Stop conditions

| Stop | Next step between runs |
|---|---|
| FRONTIER-EMPTY | The milestone's build is done: `closure`, then milestone review |
| ALL-PARKED | Clear each park, approve or reject each awaiting packet, then relaunch |
| DECISIONS-NEEDED | `park_k` tickets (default 2) are parked on non-reversible decisions. Decide them, `answer` each, relaunch |
| ALL-COOLING | Relaunch after the cooldown; `resume` shows when it ends |
| STOPPED / KILLED | Steer, then relaunch |
| REFUSED / LOCKED | Fix the named precondition, or wait for the other writer |

Exit codes, refusal tokens and every check's failure token are in
[references/exit-codes.md](references/exit-codes.md).

## Between runs: the steering loop

Steering happens between runs, never mid-run. The steer skill owns what to
decide; these are the mechanics:

1. `run.py resume` shows done, frontier, in flight, awaiting the operator,
   parked (kind and reason), cooling, and merged per intervention.
2. Read the handoffs as files: `<handoffs_dir>/<ticket>.md` on each ticket
   branch.
3. Make planner edits: ledger rows, ticket recuts, new tickets, accepted
   breakage. Commit them directly onto the integration branch, for example in
   a temporary worktree removed before the next run; a run refuses while the
   integration branch is checked out anywhere. The planner, not a worker,
   writes these. Blast-map edits need the operator's OK.
4. Clear parks and approve work:

   ```
   run.py answer <ticket> --note "<the decision>"   # a `decision` park
   run.py relaunch <ticket> [--note "<guidance>"]   # any other park; resets escalation
   integrate.py --approve <ticket>                  # an AWAITING-OPERATOR packet
   ```

   Each is ledgered as an operator intervention and committed with a ledger
   snapshot. While a run holds the lock, each exits LOCKED. The note is
   inlined into the ticket's next preamble.
5. Relaunch the run.

| Park | Meaning |
|---|---|
| `decision` | Its handoff has a `Decisions needed` item not marked reversible |
| `blocked` | Its handoff says BLOCKED or NEEDS_CONTEXT |
| `escalation` | Two failed attempts |
| `blast-b3` | Its diff escalated to B3; relaunch runs the B3 path with salvage |
| `stage` | A test-author, spec, lens or merge dispatch was rejected twice |
| `conflict` | Three rebase conflicts in one implementer attempt |
| `head-moved` | The integration head moved under two judgements in a row |
| `refused` | Integrate refused for a cause a retry cannot fix, or the launch failed |
| `unroutable` | No ladder rung at or above the needed tier |

Causes and remedies per park kind are in
[references/exit-codes.md](references/exit-codes.md).

## integrate by hand

```
integrate.py [--repo DIR] [--config harness.toml] [--bundle DIR] <ticket>
integrate.py [--repo DIR] [--config harness.toml] --approve <ticket>
```

The run calls integrate in-process. Run it by hand to re-judge a ticket, or
with `--approve` for a B3 packet. The sequence:

1. Refuse without a committed DONE or DONE_WITH_CONCERNS handoff.
2. Rebase onto the integration head. A conflict reports CONFLICT with the
   conflicted paths and the tickets that last landed them.
3. Run the lint commands (on the head and on the judged commit, for the
   ratchet), then the verify commands.
4. Run the checks: ref, Touches, blast, scrutiny evidence, attribution, style
   lint, megafile.
5. Fast-forward at B0–B2, or produce the AWAITING-OPERATOR packet at B3.

`--approve` fast-forwards the pinned commit by the same compare-and-swap. If
the head has moved since, the ticket is re-judged and a fresh packet is
produced. The outcome tokens and exit codes (0, 10, 20, 21, 22, 30, 31, 32)
are in [references/exit-codes.md](references/exit-codes.md). Integrate never
writes to the handoff: soft-lint warnings go to the event and stdout.

## Light mode

For a small or timeboxed effort, tickets may run as in-session background
workers instead of a scheduled `run --parallel N` loop — but every finished
ticket branch still lands through `integrate.py <ticket>` run by hand, so the
gate that decides what merges never changes. Lost: automatic dispatch,
salvage/escalation, the stop conditions, and a ledger-sourced headline metric
(the retro records it `not recorded` instead of estimating). Kept: every
`integrate` check, and the events ledger for every integrate outcome. Details
and the exact by-hand commands: [references/light-mode.md](references/light-mode.md).

## resume and closure

- `run.py resume [--json]` answers "where were we?" after any gap, on any
  machine. It takes no lock, so it works during a run. It also works on a
  bare clone, from the committed ledger snapshot.
- `run.py closure` runs before the milestone review. It re-runs every done
  ticket's acceptance commands against the integration head in a throwaway
  worktree, prints GREEN or RED, and ledgers the result. It reads only
  command-form acceptance checks
  ([references/handoff.md](references/handoff.md#acceptance-commands-read-by-closure)).

## Launchers

Each launcher (`launchers/` in the harness directory) is a self-contained
file with one bundle contract, specified in `launchers/CONTRACT.md` there:
`params.json` and `instructions.md` go in, `result.json` (with binary
provenance and usage) and a transcript come out. Each launcher refuses
fail-closed, enforces its timeout, and forwards an operator stop to its
worker's process group.

There are no isolation walls. Workers run with their tool's permission
prompts bypassed, inside their own worktree, and integrate guards what lands.
Launchers keep ambient configuration away from workers: settings hooks, MCP
servers, slash commands, memory and session persistence. Vendor CLIs are the
fastest-decaying dependency. Before first use, and after every tool update,
run the harness's `smoke_workers.sh claude|codex … --rehearse` (free,
`--dry-run` only). Then run it with `--i-understand-this-spends-quota`, and
record the dated, build-pinned result.

## Worker handoff

A worker writes `<handoffs_dir>/<ticket>.md` and commits it on its branch as
its **last** commit; integrate reads it from the branch, never from the
worktree. The schema is `Status`, `Commits`, `Done`, `Deviations`, `Decisions
needed`, `Findings / concerns` and `Field-guide proposals`. Every `Decisions
needed` item ends `— reversible` or `— NOT reversible`. An unmarked item
counts as not reversible and parks the ticket. The full schema, the
reversibility grammar, the review-evidence files and the acceptance-command
grammar are in [references/handoff.md](references/handoff.md).

## References

- [references/configuration.md](references/configuration.md): `harness.toml`
  (`[integrate]`, `[run]` including `lens` and `lens_smoke`), the routing
  floors, and the repository layout.
- [references/harness-example.toml](references/harness-example.toml): a
  complete, commented `harness.toml` for a typical web repo, loader-tested so
  it can never silently drift from what `parse_config` / `parse_run_config`
  accept.
- [references/light-mode.md](references/light-mode.md): running tickets as
  in-session workers instead of a scheduled run, with `integrate` still the
  only path to the integration branch.
- [references/exit-codes.md](references/exit-codes.md): run and integrate
  exit codes, stop reasons, park states, and refusal and check tokens.
- [references/handoff.md](references/handoff.md): the handoff schema, the
  reversibility grammar, review evidence, and acceptance commands.
- [references/events.md](references/events.md): the event ledger schema.
- [references/harness/](references/harness/): the code. `run.py` and
  `integrate.py` are the entry points, and their module docstrings are the
  authoritative sequence descriptions. `verify.sh` there checks the harness
  itself: every test suite, including the launcher tests that unittest
  discovery does not collect, plus `mypy --strict` over every file
  (development only; it needs uv).

# The event ledger

One JSON object per line, append-only, in `[integrate] events_file`; the run
and integrate share it. All harness state — every ticket's phase, attempts,
parks, the routing statistics, the usage governor's cooldowns, the
interventions count — is a pure fold over it, recomputed on every loop
iteration; there is no other state file. Every planner-direct commit and
every run stop commits a snapshot of it to the integration branch at
`[run] ledger_snapshot`, so `resume` works from a bare or fresh clone.

Every event has `event` and `ts` (UTC, `YYYY-MM-DDTHH:MM:SSZ`); run-loop events
also carry `t` (epoch seconds). `role` is one of `author`, `test_author`,
`spec_verdict`, `lens`, `merge`; absent means `author`.

| Event | Written when | Fields |
|---|---|---|
| `run-start` | A run begins | `parallel`, `park_k`, `pid` (signal this pid to stop the run) |
| `lens-smoke` | Once per run, when `[run] lens` is set | `tool`, `model`, `command`, `ok`, `exit`, `tail` |
| `launch` | A dispatch starts | `ticket`, `role`, `launch` (implementer launch number), `dispatch` (stages), `tool`, `model`, `effort`, `tier`, `explored`, `escalated`, `failures`, `start` (branch tip it started from), `cut` (stages), `base` (integration head), `bundle`, `checklists` and `salvage` (stages) |
| `worker-exit` | A dispatch's launcher exits | `ticket`, `role`, `ok`, `exit`, `launcher_exit`, `summary`, `limit` (a usage-limit exit), `retry_at`, `tokens` (the launcher's `usage`), `tool`, `model`, `effort` |
| `stage` | The harness accepts or rejects a stage's output | `ticket`, `role`, `ok`, `reason`, `model`, and on success `commit`, `verdict` (spec/lens), `files`, `rereview` (merge) |
| `park` | A ticket parks | `ticket`, `kind`, `reason` |
| `teardown` | An interrupted dispatch's worktree is removed and its branch reset | `ticket`, `role`, `launch` |
| `integrate` | One judgement (by the run or by hand) | see below |
| `status-flip` | `Status: done` is committed after MERGED | `ticket`, `status`, `commit` |
| `blast-raise` | A BLAST-ESCALATION's level is committed to the ticket's `Blast:` line | `ticket`, `to` |
| `intervention` | `answer` or `relaunch` | `ticket`, `kind` (`decision-answered` or `relaunch`), `note`, `was` (phase), `park_kind` |
| `closure` | `closure` ran | `head`, `ok`, `results` [`ticket`, `command`, `exit`, `tail`] |
| `run-stop` | A run ends | `reason` (the stop reason) |

## The `integrate` event

Every key is always present: `ts`, `event`, `outcome` (MERGED,
AWAITING-OPERATOR, FAILED, BLAST-ESCALATION, CONFLICT, REFUSED, HEAD-MOVED;
INTEGRATE-LOCKED writes no event), `ticket`, `model`, `attempt` (from the
bundle's `params.json`), `tokens` (the launcher's `usage`),
`worker_wall_clock_s`, `wall_clock_s`, `tag`, `size`, `declared_blast`,
`effective_blast`, `verify` (`pass`, `fail` or `not-run`), `verify_failures`
[`command`, `exit`, `tail`], `reentries`, `head_moved` (bases that moved under
a judgement), `ticket_head`, `base`, `judged`, `files` (both sides of
renames), `commits`, `hits` [`zone`, `path`, `source`, `level`], `checklists`,
`checks` [`name`, `ok`, `failures`, `warnings`, `exceptions`], `warnings`,
`exceptions`, `conflicted_paths`, `conflict_with` (the tickets that last
landed those paths), `reason`, `packet`, `approved`, `ticket_branch_moved`.

## Reading it

- `resume` (or `resume --json`) is the fold, rendered: done, frontier, in
  flight (with role, model and state), awaiting the operator (with packet
  path), parked (kind and reason), cooling candidates, invalid tickets,
  merged, interventions, merged per intervention, and the last stop.
- A `launch` with no matching `worker-exit` is an interrupted dispatch; the
  next run tears it down and redoes it without counting a failure.
- The headline metric is merged tickets per operator intervention
  (`answer`, `relaunch`, and each `--approve`, counted from `approved: true`).

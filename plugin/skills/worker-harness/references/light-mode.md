# Light mode: in-session workers, `integrate` still the gate

For a small or timeboxed effort, a full `harness run --parallel N` loop can
cost more to stand up than it saves. Light mode is the sanctioned degrade
path: tickets run as in-session background workers instead — dispatched by
the planner's own session, each in its own git worktree, the way any
subagent-driven build works — and every finished ticket branch still lands
by running `integrate.py` on it **by hand**. The gate that decides what
reaches the integration branch never changes; only who schedules the
dispatch does.

Record the choice as a decision-ledger row naming light mode and why: light
mode is a documented degrade, not a silent default.

## What stays exactly the same

- **`integrate` is still the only path to the integration branch.** Every
  ticket, however it was dispatched, is judged by the same rebase, lint,
  verify and check sequence against `harness.toml` — see
  [SKILL.md](../SKILL.md#the-contract) and
  [configuration.md](configuration.md). A worked, loader-tested config to
  copy is [harness-example.toml](harness-example.toml).
- **The events ledger records every integrate outcome.** Each hand-run
  `integrate.py` call appends the same JSONL event a scheduled run would
  have appended (MERGED, CONFLICT, the check failures, AWAITING-OPERATOR for
  a B3 ticket). `run.py resume` still folds a true picture of what merged,
  because it reads the ledger and the ticket branches, not a live scheduler
  — but `resume` (like every `run.py` subcommand) still needs a valid `[run]`
  table to start, so keep `harness.toml` complete even in light mode.
- **The B3 path, salvage semantics on a rejected attempt, and every check
  token** (`TOUCHES-OUTSIDE`, `BLAST-ESCALATION`, `VERIFY-FAILED`, …) are
  unchanged — they live in `integrate`, which light mode still calls.

## What is lost

- **Automatic dispatch.** Nothing picks the frontier, routes a ticket to a
  tier, or batches disjoint `Touches` for you; the planner decides what runs
  next and starts each worker itself.
- **Salvage and escalation as an automatic sequence.** A failed attempt does
  not automatically retry one tier up, and a diff that reaches a B3 zone
  does not automatically escalate and restart with a test-author commit —
  the planner notices and redispatches by hand.
- **Stop conditions.** There is no `FRONTIER-EMPTY`, `ALL-PARKED`,
  `DECISIONS-NEEDED`, `ALL-COOLING` or governor cooldown; nothing pauses the
  effort for the operator automatically when work runs out or piles up.
- **A ledger-sourced headline metric.** Unattended tickets merged per
  operator intervention is normally computed from a run's own dispatch and
  intervention events; light mode has no run, so the retro cannot source it
  that way. It compiles the same ratio from other artifacts instead — git
  (tickets that reached the integration branch) and, when the harness
  exposes one, the session transcript (each unplanned intervention, as an
  interaction-log row) — naming those sources in the memo. With no
  transcript, the denominator is `not recorded` rather than estimated (see
  the retro skill).

## Running `integrate` by hand

Exactly as its CLI accepts (`integrate.py --help`):

```
python3 <this skill>/references/harness/integrate.py [--repo DIR] [--config harness.toml] [--bundle DIR] <ticket>
python3 <this skill>/references/harness/integrate.py [--repo DIR] [--config harness.toml] --approve <ticket>
```

- `<ticket>` is required: the ticket id whose branch (`ticket_branch` in
  `harness.toml`, default `t/<ticket>`) has a committed DONE or
  DONE_WITH_CONCERNS handoff.
- `--repo` defaults to the current directory.
- `--config` defaults to `harness.toml` at the repo root.
- `--bundle` is only for a scheduled run's own launcher bundle; a hand-run
  call omits it.
- `--approve` fast-forwards a B3 ticket's pinned `AWAITING-OPERATOR` packet
  once the operator has read it; every other ticket omits it.

Run one `integrate.py` call per finished ticket, in whatever order the
planner judges ready. Nothing else changes: a CONFLICT, a check failure or
an AWAITING-OPERATOR packet reads and resolves the same way `harness run`
would have produced it.

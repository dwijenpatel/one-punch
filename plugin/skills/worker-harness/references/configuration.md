# harness.toml and repository layout

`harness.toml` lives at the repository root (override with `--config`). It is
operator-owned: the harness reads it from disk (a bare clone falls back to the
committed copy at `HEAD`), workers are told never to edit it, and a blast map
that follows the default pattern pack treats it as a B3 process surface.
Unknown keys in either table are `CONFIG-INVALID` — a typo must never silently
disable a check. `{effort}` and `{ticket}` expand in path and branch values.

## Example

```toml
[integrate]
effort = "m1"
verify = ["make fmt-check", "make lint", "make test"]
lint_hard = ["ruff check --output-format=concise ."]

[run]
parallel = 4
ladder = { T0 = [{ tool = "claude", model = "opus", effort = "high" }],
           T2 = [{ tool = "claude", model = "sonnet", effort = "medium" }],
           T4 = [{ tool = "claude", model = "haiku" }] }
lens = { tool = "codex", model = "<codex model id>" }
lens_smoke = "test -f .scratch/m1/lens-smoke-ok"
```

## `[integrate]`

| Key | Default | Meaning |
|---|---|---|
| `effort` | required | The effort name (`[A-Za-z0-9_.-]`); expands `{effort}` everywhere |
| `verify` | required, non-empty | Shell commands run in the judged worktree; each must exit 0 and leave tracked files unchanged |
| `verify_timeout_s` | 1800 | Per command; also bounds lint commands |
| `integration_branch` | `integrate/{effort}` | The always-green branch; cut from `main` before the first run |
| `ticket_branch` | `t/{ticket}` | One branch per ticket |
| `issues_dir` | `.scratch/{effort}/issues` | Ticket files `<id>-*.md` (or `<id>.md`), read from the integration head |
| `handoffs_dir` | `.scratch/{effort}/handoffs` | Handoff `<ticket>.md`, read from the ticket branch as committed |
| `review_dir` | `.scratch/{effort}/reviews` | Scrutiny evidence under `<review_dir>/<ticket>/` |
| `packets_dir` | `.scratch/{effort}/review-packets` | B3 review packets (on disk, uncommitted, regenerable) |
| `events_file` | `.scratch/{effort}/events.jsonl` | The live event ledger (on disk) |
| `ledger_file` | `docs/decisions.md` | Decision ledger, read from the integration head |
| `blast_map_file` | `docs/blast-map.md` | Blast map, read from the integration head; missing or invalid refuses every ticket |
| `ref_pattern` | `^D-\d{3,}$` | Anchored ledger-ID pattern for the ref check and lowerings |
| `ref_skip` | `[]` | Extra globs the ref check skips (ledger, handoffs, reviews, tickets and `test_globs` are always skipped) |
| `test_globs` | `test_*.py`, `*_test.py`, `tests/`, `test/`, `__tests__/`, `*.test.*`, `*.spec.*`, `*_test.go`, at any depth | What counts as a test file (tests-first order, the test author's scope) |
| `lint_hard` | `[]` | Lint commands whose new violations fail |
| `lint_soft` | `[]` | Lint commands whose new violations are warnings |
| `lint_pattern` | ruff concise, `path:line[:col]: CODE message` | Named groups `path` (required), `line`, `code`, `message` |
| `lint_ok_exit` | `[0, 1]` | Lint exit codes that mean "ran" |
| `megafile_threshold` | 800 | A changed file crossing it, or a file already over it growing, fails |
| `megafile_skip` | lockfiles | Globs the megafile check ignores |
| `notices_file` | `THIRD_PARTY_NOTICES.md` | Attribution lines `- <source>@<rev> license: <SPDX-id> …` |
| `allowed_licenses` | `[]` | SPDX ids a `port`/`fork` reference may carry; empty admits none |
| `checklists_dir` | `""` | Domain checklists `checklist-<id>.md`: repo-relative (read from the integration head) or absolute; empty uses the blast-radius skill installed beside this skill |
| `max_reentries` | 3 | Head-moved re-judgements before `HEAD-MOVED` |

Lint commands run on clean checkouts before verify, so each must be
self-sufficient (install what it needs). Brownfield lint is ratcheted: only
violations new in the changed code count.

## `[run]`

| Key | Default | Meaning |
|---|---|---|
| `ladder` | required | `{T0 = [{tool, model, effort?}], …, T5 = […]}`; T0 is the strongest tier. Every candidate names its model; a model whose name contains `fable` is refused; every tool needs a launcher file |
| `launchers` | `claude`, `codex`, `grok`, `mini` (`<tool>_p.py`), `mock` | `{tool = path}`, relative to the harness directory |
| `parallel` | 4 | Worker slots (`run --parallel N` overrides) |
| `park_k` | 2 | Tickets parked on non-reversible decisions that stop the run |
| `worker_timeout_s` | 3600 | Per dispatch |
| `poll_s` | 2.0 | Loop poll interval |
| `cooldown_s` | 3600 | How long a candidate cools after a usage-limit exit |
| `limit_patterns` | rate limit, usage limit, limit reached, 429, overloaded, quota | Substrings of a failed session's summary that mean "usage limit", not "failed attempt" |
| `closure_timeout_s` | 600 | Per acceptance command in `closure` |
| `worktrees_dir` | `.worktrees` | Worker worktrees `<dir>/<ticket>`, stage worktrees `<dir>/<ticket>.<role>` |
| `bundles_dir` | `.worktrees/.bundles` | Launcher bundles `<dir>/<ticket>/<role>-<n>` |
| `stop_file` | `.worktrees/STOP` | Its existence requests a draining stop; removed at run start |
| `ledger_snapshot` | `.scratch/{effort}/ledger/events.jsonl` | Where the ledger is committed on the integration branch |
| `field_guide` | `docs/field-guide/index.md` | Inlined into every worker preamble |
| `field_guide_budget` | 150 | Lines; over budget refuses the run |
| `lens` | unset | `{tool, model, effort?}`: the decorrelated B3 lens, a model family other than the implementers'; needs `lens_smoke` |
| `lens_smoke` | `""` | Shell command run once per run; exit 0 means the lens launcher's smoke passes and the lens is used, else the lens falls back to the top ladder rung |

## Routing floors

A ticket's floor is the stronger of its tag × size floor and its blast floor;
fallback climbs toward T0, never descends.

| Tag × Size | Floor |
|---|---|
| `contract` high / very-high | T1 |
| `contract` low / medium | T2 |
| `code-complete` high / very-high | T3 |
| `code-complete` low / medium | T4 |

| Blast | Floor |
|---|---|
| B0 | none (tag × size decides) |
| B1 | T2 |
| B2 | T2; T0 for `contract` |
| B3 | T0 |

v3 tags migrate on read: `critical` → `contract` + B3, `trivial` →
`code-complete` + B0 + Size low. Within a tier the router exploits the
best-by-ledger candidate and explores the least-sampled one about 12% of the
time (never at B3, never at high sizes).

## Repository layout the harness expects

- The integration branch exists (local, or `origin/<name>` in a fresh clone)
  and is never checked out in any worktree while the harness writes to it.
- The ticket files, decision ledger, blast map and field guide are committed
  on the integration branch; the harness reads them from its head, never from
  a ticket branch, so a change cannot loosen the checks that judge it.
- `.worktrees/` (or your `worktrees_dir`) is git-ignored; the harness does not
  check this.
- The events file and review packets are uncommitted; the ledger reaches git
  through `ledger_snapshot`.

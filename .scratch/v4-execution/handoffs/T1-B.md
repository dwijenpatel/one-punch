Status: DONE
Commits: 0938e63, d674a5b

Done:
- Item 1 (#10 example harness.toml): `plugin/skills/worker-harness/references/harness-example.toml`
  — complete, commented `[integrate]`/`[run]` config for a typical web repo,
  keys read from `checks/config.py` (`IntegrateConfig`/`parse_config`) and
  `runcore.py` (`parse_run_config`). Placeholders (`<EFFORT_NAME>`,
  `<TEST_COMMAND>`, `<BROWSER_WALK_COMMAND>`, `<LINT_HARD_COMMAND>`,
  `<LINT_SOFT_COMMAND>`) for what the planner fills in; a working no-Fable
  ladder (`claude`/opus·sonnet·haiku across T0/T2/T4); `[run.ladder]`
  sub-table form (see Findings — inline-table bug); `lens`/`lens_smoke`
  shown commented out, ordered before `[run.ladder]` so uncommenting stays
  valid TOML.
  Test: `plugin/skills/worker-harness/references/harness/test_example_config.py`
  (new, 5 tests) — loads the example through both real parsers
  (`checks.config.parse_config`, `runcore.parse_run_config`) after
  substituting placeholders; separately proves the unsubstituted `effort`
  placeholder is load-bearing (fails `CONFIG-INVALID` as shipped, so a
  planner who forgets to fill it in gets a loud refusal, not a silent bad
  name); separately uncomments and parses the `lens`/`lens_smoke` block so
  a rename there can't drift silently either. Picked up automatically by
  `python -m unittest` discovery (`test_*.py` in the harness dir) — no
  `verify.sh` change needed; confirmed with an explicit discovery count
  (126 total tests, up from the 121 baseline; 5 new).
- Item 2 (#10 light mode doc): short "## Light mode" section in
  `plugin/skills/worker-harness/SKILL.md` (before `## resume and closure`)
  + full doc `plugin/skills/worker-harness/references/light-mode.md`. States
  in-session workers replace `run --parallel N` for small/timeboxed efforts,
  every finished ticket branch still lands via `integrate.py <ticket>` run
  by hand (exact CLI, read from `integrate.py`'s argparse: `<ticket>`,
  `--repo`, `--config`, `--bundle`, `--approve`), lost vs kept exactly as
  the ticket specified. `SKILL.md`'s References list gained entries for both
  new files.
- Item 3 (#8 retro): `plugin/skills/retro/SKILL.md` — "Session transcript"
  added as a sixth Inputs source kind (per-stage wall clock, agent-active
  vs operator time, operator turn log, compiled by default when the harness
  exposes a timestamped transcript; `not recorded` when it doesn't), plus a
  line in the Output section pointing at the new template tables.
  `plugin/skills/retro/references/evidence-memo-template.md` — new
  "Operator interaction log" table (Turn, Time, Stage, Gist, Class D/U/S/C,
  What prompted it, Avoidable?) with the class legend, and a new "Timing"
  table (Stage, Wall clock, Duration, Agent active, Operator, Notes), both
  sourced from the session transcript, both `not recorded` when unavailable.

Deviations:
- Fixed a pre-existing bug in `plugin/skills/worker-harness/references/configuration.md`'s
  own `[run]` example while adding the cross-reference to the new example
  file: its `ladder = { T0 = [...], T2 = [...], T4 = [...] }` spanned
  multiple lines inside one inline table, which TOML forbids (confirmed by
  running it through `tomllib.loads` directly — it raised
  `TOMLDecodeError: Invalid initial character for a key part`). Rewrote it
  as `[run.ladder]` sub-table form (the same form the new example uses) and
  added a short note explaining why, plus a pointer to
  `harness-example.toml`. This is a docs-only fix inside my Touches
  (`configuration.md` is under `plugin/skills/worker-harness/**`); no
  behaviour change to any `.py` file.
- Blast: B1 for docs, but the ticket also required the example config to
  "parse under the real loaders" — verified by the new test, which is the
  strongest form of that check available (loader-tested, not just
  eyeballed).

Decisions needed: none — no one-way doors or product-boundary questions
arose; the one ambiguity (does the shipped example need to be valid TOML as
placeholders, or does "loads through the loaders after substitution" allow
placeholder tokens that are invalid TOML keys/syntax) I resolved locally and
reversibly: placeholders are valid TOML string values (so the file is
inspectable/copyable as-is) but `<EFFORT_NAME>` specifically is designed to
fail `parse_config`'s name regex unless substituted, so an operator who
forgets to fill it in gets a loud `CONFIG-INVALID` rather than a silently
wrong effort name. Reversible: changing the placeholder convention is a
one-file edit with no other consumers.

Findings / concerns:
- `configuration.md`'s own worked example never actually parsed (see
  Deviations) before this change — worth noting in case another doc or a
  ticket template copied the same broken multi-line-inline-table pattern
  elsewhere; I did not find another occurrence in `plugin/skills/worker-harness/**`.
- Advisor review (called before writing this handoff) caught two factual
  errors in my first draft that I want on record since they're the kind of
  claim a planner would act on directly: (1) I originally wrote "light mode
  never needs `[run]`" — false, `run.py resume`/`closure`/`answer`/
  `relaunch` all parse `[run]` via `open_effort` and refuse without it; only
  `integrate.py` skips it. (2) I originally wrote light mode's retro
  headline is always `not recorded` — too strong; it's the *ledger-sourced*
  computation that's lost, and the retro's new session-transcript source
  (this same ticket's item 3) can still compile the same ratio from git +
  transcript. Both fixed in the second commit, along with adding the
  lens-block test that the first draft's coverage missed.

Field-guide proposals: none.

Acceptance:
- `bash plugin/skills/worker-harness/references/harness/verify.sh` — green.
  126 unittest tests (up from 121 baseline; 5 new in
  `test_example_config.py`), both launcher suites
  (`launchers/test_codex_p.py` 12 tests, `launchers/test_launchers.py` 4
  tests), `mypy --strict` clean over 28 harness `.py` files.
- `python -m unittest -v` discovery count for the new file confirmed
  explicitly: `uv run --no-project python -m unittest -v 2>&1 | rg -c
  "test_example"` → 10 (5 tests × 2 matching lines each in `-v` output) —
  confirms automatic discovery, so `verify.sh` needed no changes.
- Frontmatter self-validation (parsed the YAML block, checked name==dir,
  description length, total line count) for both touched skills:
  - `worker-harness`: name `worker-harness` == dir `worker-harness`;
    description 963/1024 chars; SKILL.md 356/500 lines.
  - `retro`: name `retro` == dir `retro`; description 540/1024 chars;
    SKILL.md 104/500 lines.
- Portability grep (`§`, `/Users/`, 7-40 char hex SHAs, `one-punch\b`) over
  both `SKILL.md` files: no hits.
- `harness-example.toml` and the `[run]` example in `configuration.md` both
  independently confirmed to parse via `tomllib.loads` + `parse_config` +
  `parse_run_config` (the latter via the new test; the former via an
  ad-hoc check during the fix, superseded by the test's coverage of the
  canonical example).
- Touches respected: only `plugin/skills/worker-harness/**` and
  `plugin/skills/retro/**` files changed, plus this handoff. No ticket file
  edited (none exists for this ticket — this brief is T1-B). No changes to
  `run.py`, `runcore.py`, `core.py`, `integrate.py`, `checks/*.py`, or any
  other behavioural harness code.

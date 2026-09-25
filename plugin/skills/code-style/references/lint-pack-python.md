# Lint pack — Python

Ruff codes below are **verified**: checked against docs.astral.sh 2026-09-24
(process-authority repo's `docs/evidence/`, 2026-09-24 code-style canon memo,
header note and row citations). The pylint-only rows are recall-sourced and
**UNVERIFIED** — ruff does not implement them, so a repo that wants that check
runs pylint alongside ruff. Spike (see the `spike` skill) any `UNVERIFIED`
entry against an installed pylint before it gates a verify command.

## Hard fail

| Layer 2 rule | Tool / code | Status |
|---|---|---|
| Import boundary (core ↛ I/O, DB, network, clock, randomness) | `import-linter` (contracts config, not a ruff rule) | UNVERIFIED — confirm contract syntax against an installed version |
| Swallowed errors (bare/blind except, empty catch) | ruff `E722` (bare except), `BLE001` (blind except), `S110` (try-except-pass) | Verified |
| Unused imports/variables | ruff `F401`, `F841` | Verified |
| Commented-out code | ruff `ERA001` | Verified |
| Boolean flag parameters | ruff `FBT001`–`FBT003` | Verified |
| Too many parameters | ruff `PLR0913` | Verified |
| Mutable global state (no `D-NNN`) | ruff `PLW0603` (`global` statement) — flags the statement, not the missing ledger reference; the missing-reference check is the harness's ref check, not a lint rule | Verified (the lint half only) |
| Mutable default arguments | ruff `B006` | Verified |
| Formatter drift | `ruff format` (or `black`, if the repo predates the ruff formatter) | Verified 2026-09-25 (ruff 0.16.9: subcommand exists); which formatter a repo standardizes on stays a per-repo choice |

## Soft cap

| Layer 2 rule | Tool / code | Status |
|---|---|---|
| Function length ~40–60 lines (target ~25) | ruff `PLR0915` (too-many-statements — a proxy for length, not a line count) | Verified |
| Cyclomatic/cognitive complexity | ruff `C901` | Verified |
| Clone-level duplication | pylint `R0801` (`duplicate-code`); no ruff equivalent | Verified 2026-09-25 (pylint 4.0.9) |
| Inheritance depth > framework + 1 | pylint `R0901` (`too-many-ancestors`); no ruff equivalent | Verified 2026-09-25 (pylint 4.0.9) |

## Also useful, not in the hard-fail/soft-cap table

- Docstrings on public API: ruff `D` (pydocstyle rules) — Verified, opt-in
  subset recommended (the full `D` set is stricter than this skill's Layer 1
  rule 5 asks for).
- Naming: ruff `N8xx` (pep8-naming) — Verified.

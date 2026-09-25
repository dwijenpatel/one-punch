# Lint pack — JavaScript / TypeScript

Every rule name below is recall-sourced, **not** checked against an installed
eslint/typescript-eslint config (process-authority repo's `docs/evidence/`,
2026-09-24 code-style canon memo, header note: "eslint, pylint, clippy,
typescript-eslint... from recall, so check them before wiring into CI").
Treat this file as a starting point for the `spike` skill to verify against a
real repo, not as ready to gate a verify command.

## Hard fail

| Layer 2 rule | Tool / rule name | Status |
|---|---|---|
| Import boundary (core ↛ I/O, DB, network, clock, randomness) | `dependency-cruiser` (rule config, not an eslint rule) | UNVERIFIED |
| Swallowed errors (empty catch) | eslint `no-empty` (catch clauses), `no-empty-function` | Verified 2026-09-25 (eslint 9.39.5 core) |
| Unused imports/variables | eslint `no-unused-vars` | Verified 2026-09-25 (eslint 9.39.5 core) |
| Unused exports | `knip` | UNVERIFIED |
| Commented-out code | no standard eslint rule found; review only until one is confirmed | UNVERIFIED |
| Boolean flag parameters | no standard eslint core rule found; a custom rule or `eslint-plugin-boolean-trap`-style plugin would be needed | UNVERIFIED |
| Too many parameters | eslint `max-params` | Verified 2026-09-25 (eslint 9.39.5 core) |
| Mutable global state (no `D-NNN`) | eslint `no-restricted-globals` — the missing-reference check is the harness's ref check, not a lint rule | Verified 2026-09-25 (eslint 9.39.5 core) |
| Mutable default arguments / argument mutation | eslint `no-param-reassign` | Verified 2026-09-25 (eslint 9.39.5 core) |
| Formatter drift | `prettier` (via `eslint-config-prettier` or standalone) | UNVERIFIED |

## Soft cap

| Layer 2 rule | Tool / rule name | Status |
|---|---|---|
| Function length ~40–60 lines (target ~25) | eslint `max-lines-per-function` | Verified 2026-09-25 (eslint 9.39.5 core) |
| Cyclomatic/cognitive complexity | eslint `complexity` | Verified 2026-09-25 (eslint 9.39.5 core) |
| Clone-level duplication | `jscpd` | UNVERIFIED |
| Inheritance depth > framework + 1 | no standard eslint rule found (JS/TS inheritance depth is a review item more than a lint one); review only | UNVERIFIED |

## Also useful, not in the hard-fail/soft-cap table

- Immutability: TypeScript `readonly` (typescript-eslint `prefer-readonly`), eslint `prefer-const` — Verified 2026-09-25 (typescript-eslint 8.70.1, eslint 9.39.5).

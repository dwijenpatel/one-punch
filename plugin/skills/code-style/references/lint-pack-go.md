# Lint pack — Go

Every tool name below is recall-sourced, **not** checked against an installed
Go toolchain (process-authority repo's `docs/evidence/`, 2026-09-24 code-style
canon memo, header note: linter names beyond ruff are "from recall, so check
them before wiring into CI" — the canon memo's own Go citations are for the
*style guidance* itself, e.g. Go-CRC "Contexts" and "Handle Errors", not for
these tool names). Treat this file as a starting point for the `spike` skill
to verify against a real repo, not as ready to gate a verify command.

## Hard fail

| Layer 2 rule | Tool / check | Status |
|---|---|---|
| Import boundary (core ↛ I/O, DB, network, clock, randomness) | internal package layout (`internal/`) + `go vet` import checks; no single named boundary tool confirmed | UNVERIFIED |
| Swallowed errors (unchecked errors) | `errcheck` | UNVERIFIED |
| Unused imports/variables | `go vet`, `staticcheck` (`U1000`) | UNVERIFIED |
| Commented-out code | no standard tool found; review only until one is confirmed | UNVERIFIED |
| Boolean flag parameters | no standard tool found; review only | UNVERIFIED |
| Too many parameters | no standard tool found; review only | UNVERIFIED |
| Mutable global state (no `D-NNN`) | no standard tool found; the missing-reference check is the harness's ref check, not a lint | UNVERIFIED |
| Mutable default arguments | not applicable — Go has no default arguments | N/A |
| Formatter drift | `gofmt` / `goimports` | UNVERIFIED |

## Soft cap

| Layer 2 rule | Tool / check | Status |
|---|---|---|
| Function length ~40–60 lines (target ~25) | `gocyclo`-adjacent length checks (no dedicated length tool confirmed) | UNVERIFIED |
| Cyclomatic/cognitive complexity | `gocyclo` | UNVERIFIED |
| Clone-level duplication | no idiomatic Go tool confirmed; review only | UNVERIFIED |
| Inheritance depth > framework + 1 | not applicable — Go has no implementation inheritance (embedding + interfaces only) | N/A |

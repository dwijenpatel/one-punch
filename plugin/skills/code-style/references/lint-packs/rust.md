# Lint pack — Rust

Every rule name below is recall-sourced, **not** checked against an installed
clippy version (process-authority repo's `docs/evidence/`, 2026-09-24
code-style canon memo, header note). Treat this file as a starting point for
the `spike` skill to verify against a real repo, not as ready to gate a
verify command.

## Hard fail

| Layer 2 rule | Tool / lint name | Status |
|---|---|---|
| Import boundary (core ↛ I/O, DB, network, clock, randomness) | crate/module boundaries (workspace layout + `pub(crate)` visibility, not a single named tool) | UNVERIFIED |
| Swallowed errors (unchecked `Result`) | `#[must_use]` on `Result`/`Option` (compiler lint, not clippy); clippy `unused_must_use` | UNVERIFIED |
| Unused imports/variables | rustc `unused_imports`, `unused_variables` (compiler warnings, not clippy) | UNVERIFIED |
| Commented-out code | no standard clippy lint found; review only until one is confirmed | UNVERIFIED |
| Boolean flag parameters | clippy `fn_params_excessive_bools` | UNVERIFIED |
| Too many parameters | clippy `too_many_arguments` | UNVERIFIED |
| Mutable global state (no `D-NNN`) | `static mut` is itself a hard signal (compiler discourages it directly); the missing-reference check is the harness's ref check, not a lint | UNVERIFIED |
| Mutable default arguments | not applicable — Rust has no default arguments | N/A |
| Formatter drift | `rustfmt` | UNVERIFIED |

## Soft cap

| Layer 2 rule | Tool / lint name | Status |
|---|---|---|
| Function length ~40–60 lines (target ~25) | no standard clippy lint found; review only | UNVERIFIED |
| Cyclomatic/cognitive complexity | clippy `cognitive_complexity` (nightly-gated in some clippy versions) | UNVERIFIED |
| Clone-level duplication | no idiomatic Rust tool confirmed; review only | UNVERIFIED |
| Inheritance depth > framework + 1 | not applicable — Rust has no implementation inheritance (traits only); rule 4 (compose; inherit only to implement an interface) is already the Rust default | N/A |

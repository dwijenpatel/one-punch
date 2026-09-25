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
| Swallowed errors (unchecked `Result`) | rustc `unused_must_use` (a **compiler** lint, not clippy — corrected) on `#[must_use]` types incl. `Result` | Verified 2026-09-25 (rustc lint list) |
| Unused imports/variables | rustc `unused_imports`, `unused_variables` (compiler warnings, not clippy) | Verified 2026-09-25 (rustc lint list) |
| Commented-out code | no standard clippy lint found; review only until one is confirmed | UNVERIFIED |
| Boolean flag parameters | clippy `fn_params_excessive_bools` | Verified 2026-09-25 (clippy 0.1.97) |
| Too many parameters | clippy `too_many_arguments` | Verified 2026-09-25 (clippy 0.1.97) |
| Mutable global state (no `D-NNN`) | `static mut` is itself a hard signal (compiler discourages it directly); the missing-reference check is the harness's ref check, not a lint | UNVERIFIED |
| Mutable default arguments | not applicable — Rust has no default arguments | N/A |
| Formatter drift | `rustfmt` | UNVERIFIED |

## Soft cap

| Layer 2 rule | Tool / lint name | Status |
|---|---|---|
| Function length ~40–60 lines (target ~25) | clippy `too_many_lines` (pedantic group; set the threshold in `clippy.toml`) — corrected, the lint exists | Verified 2026-09-25 (clippy 0.1.97) |
| Cyclomatic/cognitive complexity | **do not use** clippy `cognitive_complexity`: it exists but sits in `restriction`, and clippy's own docs say it does not measure cognitive complexity; treat complexity as review-only in Rust | Verified 2026-09-25 (clippy 0.1.97) |
| Clone-level duplication | no idiomatic Rust tool confirmed; review only | UNVERIFIED |
| Inheritance depth > framework + 1 | not applicable — Rust has no implementation inheritance (traits only); rule 4 (compose; inherit only to implement an interface) is already the Rust default | N/A |

# 02 spike — P4 lint rule names — 2026-09-25

Method: installed tools' own rule listings, not docs.

```
$ uvx ruff rule <code>        # ruff 0.16.9
E722 bare-except · BLE001 blind-except · S110 try-except-pass · F401 unused-import · F841 unused-variable
ERA001 commented-out-code · FBT001/2/3 boolean-* · PLR0913 too-many-arguments · PLW0603 global-statement
B006 mutable-argument-default · PLR0915 too-many-statements · C901 complex-structure · D100 · N801
$ uvx ruff format --help      # exists
$ uvx pylint --help-msg=R0801|R0901      # pylint 4.0.9
duplicate-code (R0801) · too-many-ancestors (R0901)
$ node -e "require('eslint/use-at-your-own-risk').builtinRules.has(r)"   # eslint 9.39.5
no-empty, no-empty-function, no-unused-vars, max-params, no-restricted-globals, no-param-reassign,
max-lines-per-function, complexity, prefer-const: all exist
@typescript-eslint/eslint-plugin 8.70.1: prefer-readonly exists
$ cargo clippy --explain <lint>          # clippy 0.1.97
fn_params_excessive_bools ✓ · too_many_arguments ✓ · too_many_lines ✓ (pack said none — corrected)
cognitive_complexity: exists, group `restriction`; clippy docs: "We used to think it measured how hard
  a method is to understand" → pack now says do not use
$ rustc -W help | rg unused-
unused-imports, unused-variables, unused-must-use (rustc lints; pack attributed unused_must_use to clippy — corrected)
```

Not verified: Go (toolchain not installed on this host; go.md stays UNVERIFIED);
tool-level entries that are configuration systems rather than rule names
(import-linter, dependency-cruiser, knip, jscpd, prettier) — verify when a repo wires them.

Verdict: CONFIRMED for ruff/pylint/eslint/typescript-eslint/clippy/rustc entries, with 3 corrections
(rust: unused_must_use is rustc; too_many_lines exists; cognitive_complexity not fit for purpose).
Go: OPEN.

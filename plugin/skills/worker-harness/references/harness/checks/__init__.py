"""Pure check core for `integrate.py` (plan §3.5 step 4).

Nothing in this package performs I/O, reads a clock, runs a process or draws
randomness: the shell (`integrate.py`) gathers the diff, file contents, the
ledger text, command outputs and the config, and each check is a function of
those values returning a `CheckResult`. Modules:

- `diff`      — unified-diff text -> file entries (format §5 "File entry").
- `blastmap`  — blast-map extraction (format §1), validation (§3), the
                detector (§5).
- `ledger`    — decision-ledger table, ledger-ref scanning, handoff status,
                config (`harness.toml` `[integrate]`).
- `hygiene`   — every check and the outcome decision.
- `lint`      — lint-output parsing, the brownfield ratchet, `allow(...)`
                exceptions.
"""

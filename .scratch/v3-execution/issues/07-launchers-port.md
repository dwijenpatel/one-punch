# 07 — Launchers: port + smoke

Type: task
Status: done
Blocked by: 06
Tag: contract
Size: high

## Question

Port outrigger claude_p.py (+2.1.220 corrections from the kb memory facts) and codex_p.py; wrap mini as lowest-tier launcher; grok launcher smoke-first w/ container wall; mock launcher for tests. Re-smoke claude + codex on current builds; record in smoke checklist (ticket 12).

## Comments

Completed 2026-08-08. Ported from outrigger @ 3a95273 with provenance headers:
claude_p.py (+2.1.220 corrections: network allowlist w/ strictAllowlist,
unix_sockets isolation key, env-prefix/pipe gating documented; dry-run
verified the settings translation), codex_p.py + CONTRACT.md + mock.py
verbatim. New: mini_p.py (contract-conformant wrapper, refuses any isolation
intent — mini has no walls; zero-cost usage), grok_p.py (fail-closed
placeholder with the smoke-first procedure in its docstring; container-wall
plan per the ratified direction). All launchers py_compile clean.
NOTE: codex_p re-smoke on the current codex build + the claude live smoke row
are ticket 12's job — port ≠ proof; the launchers carry their smoke procedures.

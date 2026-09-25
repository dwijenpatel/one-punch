# 02 spike — P1 + P3 re-run on post-ticket-11 launchers — 2026-09-25T07:31Z

Why: ticket 11 rewrote `claude_p.py` (always bypassPermissions, isolation
fields refused, `--settings` removed) and `codex_p.py` (lens-only profile)
after the first live runs. Operator go-ahead: "do it". Plugin 0.4.0 at
`3634fa7`. Raw: `probes-rerun-2026-09-25.log`.

| Probe | Result |
|---|---|
| P1 claude, n=1 | ok, exit 0, 23 s; commit on `t/w1` only; main unchanged; `-c`/pipe/env-prefix ran; usage + provenance (2.1.281) captured |
| P3 codex lens | ok, exit 0, 27 s; only `?? review.md`; same correct finding; tokens parsed, cost not exposed (0.156.1) |

Verdict: **CONFIRMED** for both on the current launcher code. P2 not re-run:
concurrency is a property of the CLI/subscription, not of launcher code.

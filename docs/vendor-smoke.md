# Per-vendor compatibility smoke

A vendor is claimed supported only when every row below passes FOR THAT VENDOR,
dated and build-pinned. A green Claude row says nothing about Codex. Re-run a
vendor's rows after its tool updates — vendor builds are the fastest-decaying
dependency in the system.

Rows (per vendor):
1. **Instructions loaded** — AGENTS.md (or the vendor shim) is read in a real
   session; a canary line is echoed back.
2. **Skills invocable** — the `start` and `intent` skills run to completion in
   that harness (structured-question UI or plain text).
3. **Tracker ops** — the local-markdown tracker conventions (claim, resolve,
   blocking, frontier) execute correctly from that harness.
4. **Worker launcher smoke** — the vendor's launcher probe passes: walls DENIED
   where intended, workspace writable, commit runs unattended, usage captured.
   (Each launcher file carries its own probe procedure.)

## Ledger

| Vendor | Row | Status | Build | Date | Evidence |
|---|---|---|---|---|---|
| Claude Code | 4 (launcher, v4: unattended commit + telemetry, no walls) | **PASS** | 2.1.281 | 2026-09-25 | one-punch v4 spike 02 P1/P2: bypassPermissions in own worktree, commit on own branch only, usage + provenance captured, `-c`/pipe/env-prefix run; 4 concurrent workers in one repo, no limit or lock errors (ceiling ≥4). Walls out of scope by operator decision. |
| Codex | 4 (launcher, v4: read-only lens) | **PASS** | codex 0.156.1 | 2026-09-25 | one-punch v4 spike 02 P3: headless review, read-only respected, report written, token usage parsed (cost/api-ms not exposed). |
| Claude Code | 4 (launcher) | **PASS** | 2.1.220 | 2026-08-07 | rustwork-8317 experiment: denyRead walls DENIED (repo + user config dir), cwd writable, headless commit, stream-json usage captured; network default-deny + unix-socket bridge probed. Corrections folded into claude_p.py. |
| Claude Code | 1–3 | **PASS (in-effort evidence)** | 2.1.2xx | 2026-07→08 | The kb effort end-to-end: instructions, all skills, tracker ops exercised across ~30 sessions. Formal canary re-run due at next CLI major. |
| Codex | 4 (launcher) | **PASS (stale — re-run due)** | codex 0.144.3 | 2026-07-13 | outrigger smoke ledger: profile walls (reads/writes/network) + full commit cycle; Browser-plugin network breach documented → plugins excluded. Port unchanged; re-smoke on current build before first real ticket. |
| Codex | 1–3 | OPEN | — | — | Not yet run. |
| grok | 1–4 | OPEN (launcher refuses until smoked) | — | — | grok_p.py is a fail-closed placeholder; smoke procedure in its docstring. |
| mini (local) | 4 (launcher) | **PASS (no walls by design)** | mini 2.4.6 | 2026-08-05→07 | kb overnight runs: bundle-shape behavior, step accounting, compaction; refuses isolation intent. T5 tickets in throwaway clones only. |

# Per-vendor compatibility smoke

A vendor is claimed supported only when every row below passes FOR THAT VENDOR,
dated and build-pinned. A green Claude row says nothing about Codex. Re-run a
vendor's rows after its tool updates — vendor builds are the fastest-decaying
dependency in the system.

Rows (per vendor):
1. **Instructions loaded** — AGENTS.md (or the vendor shim) is read in a real
   session; a canary line is echoed back.
2. **Skills invocable** — the `steer` (preflight through H1) and `intent`
   skills run to completion in that harness (structured-question UI or plain
   text).
3. **Tracker ops** — the local-markdown tracker conventions (claim, resolve,
   blocking, frontier) execute correctly from that harness.
4. **Worker launcher smoke** (v4) — the vendor's launcher runs headless and
   unattended in its own worktree: an implementer launcher commits on its own
   branch only, with usage and binary provenance captured in `result.json`; a
   read-only lens launcher writes its report without touching the worktree,
   with usage captured. v4 runs no isolation walls, so this row makes no wall
   claims. Procedure: the harness's `smoke_workers.sh` and each launcher
   file's own probe notes.

Rows marked **HISTORICAL** were measured against the v3 row 4, which also
required isolation walls to be DENIED where intended. They stay as the record
of what was measured; they are not v4 evidence.

## Ledger

| Vendor | Row | Status | Build | Date | Evidence |
|---|---|---|---|---|---|
| Claude Code | 4 (launcher, v4: unattended commit + telemetry) | **PASS** | 2.1.281 | 2026-09-25 | one-punch v4 spike 02 P1/P2: bypassPermissions in own worktree, commit on own branch only, usage + provenance captured, `-c`/pipe/env-prefix run; 4 concurrent workers in one repo, no limit or lock errors (ceiling ≥4). |
| Codex | 4 (launcher, v4: read-only lens) | **PASS** | codex 0.156.1 | 2026-09-25 | one-punch v4 spike 02 P3: headless review, read-only respected, report written, token usage parsed (cost/api-ms not exposed). |
| Claude Code | 2 (v4 skills: `steer`, `intent`) | OPEN | — | — | `steer` replaced `start` in v4 and has not yet run in a real effort. The first v4 trial is the smoke. |
| Claude Code | 1–3 | **PASS (in-effort evidence, v3 skills)** | 2.1.2xx | 2026-07→08 | The kb effort end-to-end: instructions, all v3 skills (incl. `start`), tracker ops exercised across ~30 sessions. Formal canary re-run due at next CLI major. |
| Codex | 1–3 | OPEN | — | — | Not yet run. |
| grok | 1–4 | OPEN (launcher refuses until smoked) | — | — | grok_p.py is a fail-closed placeholder; smoke procedure in its docstring. |
| Claude Code | 4 (launcher, v3 walls) | HISTORICAL | 2.1.220 | 2026-08-07 | rustwork-8317 experiment: denyRead walls DENIED (repo + user config dir), cwd writable, headless commit, stream-json usage captured; network default-deny + unix-socket bridge probed. The wall code was removed in v4. |
| Codex | 4 (launcher, v3 walls) | HISTORICAL | codex 0.144.3 | 2026-07-13 | outrigger smoke ledger: profile walls (reads/writes/network) + full commit cycle; Browser-plugin network breach documented → plugins excluded. Superseded for the lens role by the 0.156.1 row. |
| mini (local) | 4 (launcher, v3) | HISTORICAL | mini 2.4.6 | 2026-08-05→07 | kb overnight runs: bundle-shape behavior, step accounting, compaction; refuses isolation intent. T5 tickets in throwaway clones only. T5 is unrouted in v4 until a retro reopens it; re-smoke under the v4 row before routing to it. |

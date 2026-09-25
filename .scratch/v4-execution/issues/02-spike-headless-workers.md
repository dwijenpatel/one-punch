# 02 — spike headless workers

Type: spike
Status: done
Blocked by: —
Tag: contract
Blast: B1 — throwaway probes; findings gate B2 tickets 08/09/10
Size: low
Touches: .scratch/v4-execution/spikes/**, plugin/skills/code-style/references/lint-packs/** (P4 verification markers, per ticket 04 handoff), plugin/skills/worker-harness/references/harness/smoke_workers.sh, plugin/skills/worker-harness/references/harness/launchers/claude_p.py, plugin/skills/worker-harness/references/harness/launchers/codex_p.py, docs/vendor-smoke.md
Reference: outrigger@9fa7023:tools/exec-loop/SMOKE.md (pattern — prior smoke ledger; only its non-wall facts apply)
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md §8.1, §9

## What

Confirm by execution (one-punch `spike`; each transcript = command · trimmed
output · versions · date, filed under `spikes/`) that headless workers run v4's
build loop on the current builds: **Claude Code 2.1.281** and **codex-cli
0.156.1**.

**Out of scope, by operator decision (2026-09-24):** isolation walls of any
kind: `deny_read`, sandboxes as walls, escape or boundary probes, network
policy. Outrigger measured them as not worth their cost, and v4 has nothing to
hide from workers (B3 tests are written first and visible). Workers run
**`bypassPermissions` inside their worktree**. The `integrate` script, not
containment, guards what lands.

Kept launcher hygiene (not walls): `--setting-sources ""`,
`--strict-mcp-config`, `--disable-slash-commands`, `--no-session-persistence`,
`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`. Without these, the operator's own hooks,
MCP servers and memory load into every worker (outrigger run 5 showed the
flags work and auth survives).

### Probes

| P | Question | Expectation | Method | Cost |
|---|---|---|---|---|
| **P1** | One Claude worker, `bypassPermissions`, cwd = `.worktrees/t-a` on branch `t/a`: edits, runs tests, commits unattended; the commit lands on `t/a` only; `result.json` has usage + binary provenance | runs unattended with no approval stops; `python3 -c`, pipes and env-prefixed commands also run (their gating was a sandbox quirk); `/tdd` unavailable (hygiene flags) | new `smoke_workers.sh claude --n 1` | 1 short Sonnet session |
| **P2** | Parallel: N workers, N worktrees, one repo | N=2 and N=4 all commit; no lock errors from concurrent commits (worktree *creation* serialized by the harness); ceiling ≥ 4 | `smoke_workers.sh claude --n 2`, then `--n 4`; record per-worker wall-clock and exit, plus any limit error **verbatim** (exit code, stderr, stream event) | 6 short Sonnet sessions |
| **P3** | Codex as the B3 lens: headless, read-only review of a diff, report written, usage parsed | runs unattended; report file produced; `result.json` usage populated | `smoke_workers.sh codex --n 1 --review` | 1 Codex session |
| **P4** | Lint rule names for §3.11 packs outside ruff (eslint, pylint, clippy, Go) | recall-grade names partly wrong | installed tools' rule listings | free |

### Launcher changes (this ticket's Touches)

- `claude_p.py`: when the bundle requests no isolation (v4 always), use
  `--permission-mode bypassPermissions` with no sandbox settings. Keep the
  hygiene flags.
- `codex_p.py`: the simplest unattended mode; read-only for the lens.
- The unused wall code in both launchers (and `test_codex_p.py`'s wall cases)
  is **removed in ticket 11**, not here, so this spike stays small.

### Outputs feeding later tickets

- Measured ceiling → default N; limit-error shape → usage governor (09).
- Any command form that still stops unattended runs → preamble rule (09).
- `docs/vendor-smoke.md` row 4 for Claude 2.1.281 and Codex 0.156.1, redefined
  as "unattended commit + telemetry", with no wall claims.

## Acceptance

- One transcript per probe under `.scratch/v4-execution/spikes/`, each ending
  `CONFIRMED | REFUTED | CEILING=<n>`; any REFUTED names the fallback taken
  and is recorded in plan §9.
- `smoke_workers.sh` passes `--rehearse` (free, builds bundles + scratch repo,
  launchers `--dry-run`) before any quota run; quota runs need
  `--i-understand-this-spends-quota` and are triggered by the operator, per run.
- `vendor-smoke.md` updated for both vendors.

## Comments

2026-09-24 — v1 of this rewrite ported outrigger's wall-probing smoke
apparatus. The operator rejected wall-escape prevention (measured
not worth the cost), so it was removed. The copied `smoke_codex_escape.sh` was
deleted; `smoke_codex.sh` was deleted too (its purpose was the read-wall probe),
replaced by `smoke_workers.sh`. `test_codex_p.py` stays until ticket 11 strips
the wall code it tests.

2026-09-25 — done. P1 CONFIRMED · P2 CEILING ≥ 4 · P3 CONFIRMED · P4
CONFIRMED (3 Rust corrections; Go open). Transcripts in `spikes/`. Outputs:
default N = 4 stands; preamble rule "never `git add -A`, stage only your
Touches" (ticket 09); skill-availability self-reports are unreliable, so
guidance goes inline (09); no limit-error shape observed yet.

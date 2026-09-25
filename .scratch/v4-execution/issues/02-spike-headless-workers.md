# 02 — spike headless workers

Type: spike
Status: ready-for-agent (quota-spending probes are operator-triggered, per run)
Blocked by: —
Tag: contract
Blast: B1 — throwaway probes; findings gate B2 tickets 08/09/10
Size: medium
Touches: .scratch/v4-execution/spikes/**, plugin/skills/worker-harness/references/harness/smoke_*.sh, plugin/skills/worker-harness/references/harness/launchers/claude_p.py, docs/vendor-smoke.md
Reference: outrigger@9fa7023:tools/exec-loop/SMOKE.md (pattern — prior smoke ledger, 5 Claude runs + 4 Codex attempts)
Reference: outrigger@9fa7023:tools/exec-loop/smoke_codex.sh (port — done, see Prep)
Reference: outrigger@9fa7023:tools/exec-loop/loop.py#L440-577 (pattern — worktree-per-attempt, teardown/redo, ff-only land)
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md §8.1

## What

Settle plan §8.1 by execution (one-punch `spike`; each transcript = command ·
trimmed output · versions · date, filed under `spikes/`). **Start from the
prior art; don't rediscover it.** Outrigger's exec-loop already ran headless
`claude -p` / `codex exec` workers in `git worktree`s, one at a time, across 5
Claude runs and 4 Codex attempts. The facts below are the baseline and
**pre-registered expectations**. Each probe re-verifies them on the current
builds and adds what v4 needs that the serial loop never tested: concurrency.

### Prep — done 2026-09-24 (free)

- Copied from outrigger @9fa7023 into the harness (provenance headers
  added): `launchers/test_codex_p.py` (16 tests, stub binary; **16/16 OK**
  against one-punch's `codex_p.py`, which is byte-identical to outrigger's),
  `smoke_codex.sh`, `smoke_codex_escape.sh` (**both `--rehearse` OK**).
- Not copied: `smoke.sh`, `smoke_codex_loop.sh` (they drive outrigger's
  `loop.py`, held-out suite CLI and preflight — none exist in one-punch;
  replaced by P1/P3 scripts below). `claude_p.py`: one-punch's copy is
  already newer (2.1.220 network corrections); outrigger's is not carried back.
- Current builds: **Claude Code 2.1.281** (last PASS 2.1.220, 2026-08-07) ·
  **codex-cli 0.156.1** (last PASS 0.144.3, 2026-07-13). Both are stale
  → re-smoke required (standing per-build rule).

### Baseline (prior art — build-specific facts to re-verify)

| # | Fact | Build · date | Source |
|---|---|---|---|
| F1 | `bypassPermissions` drops the permission-layer Read deny → wall must be OS-layer: `sandbox.filesystem.denyRead` + `autoAllowBashIfSandboxed` + `--permission-mode acceptEdits` | 2.1.205–2.1.207 · 07-11/12 | SMOKE runs 1–3 |
| F2 | Unattended `git commit` from a `git worktree` under sandbox auto-allow AND denyRead holding — simultaneously | 2.1.202 · 07-12 | run 3 (serial only) |
| F3 | `sandbox.failIfUnavailable: true` accepted; vendor default otherwise = warn and run unsandboxed | 2.1.202 · 07-12 | run 3 |
| F4 | Ambient isolation: `--setting-sources ""`, `--strict-mcp-config`, `--disable-slash-commands`, `--no-session-persistence`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` → no hooks, no MCP, auth still works. Residual: account email injected (accepted) | 2.1.207 · 07-13 | run 5 |
| F5 | `python3 -c`, env-prefixed commands (`VAR=x cmd`, `export …;`) and pipes are approval-gated even under auto-allow; script files run fine | 2.1.207 / 2.1.220 | run 5; claude_p comments |
| F6 | Network: sandbox default pre-allows nothing; loopback TCP blocked and not allowlistable; listen/bind blocked; local services only via unix sockets + host bridge | 2.1.220 · 08-07 | vendor-smoke.md |
| F7 | `--output-format json` usage/cost parse into `result.json` is correct | 2.1.207 · 07-12 | run 4 |
| F8 | Codex: permission-profile walls (read/write/network) hold; profile via `--profile` file (quoted `-c` keys falsified); `--ignore-user-config` suppresses profiles; Browser plugin breaches network → plugins excluded | 0.144.3 · 07-13 | SMOKE codex attempts 1–4, escape probe |
| F9 | Gate environment: checks that read git state fail in a `--no-commit` staged merge — commit the merge in a throwaway worktree before running checks | machinery · 07-12 | run 4 |

### Probes

| P | Question | Pre-registered expectation | Method | Cost |
|---|---|---|---|---|
| **P1** | Single Claude worker on 2.1.281: wall + unattended commit + telemetry + ambient isolation | F1–F4, F7 hold; `/tdd` unavailable (F4 disables skills) | **new `smoke_claude.sh`**, launcher-level (no loop), modelled on `smoke_codex.sh`: sentinel read via Read tool and shell → `DENIED`; write outside cwd → blocked; trivial commit; `result.json` usage + binary provenance | 1 Sonnet session |
| **P2** | Worktree commit confinement: worker in `.worktrees/t-a` on `t/a` commits there only; main checkout and other branches untouched; sandbox permits the writes git needs in the common dir | F2 holds on 2.1.281 | P1 script, `--worktree` variant: bundle cwd = a fresh worktree; afterwards `git log` every branch + `git status` main | shares P1's session |
| **P3** | **Parallel:** 4 concurrent workers, 4 worktrees, one repo | all 4 commit; no lock errors from concurrent commits (worktree *creation* is serialized by the harness); ceiling ≥ 4 on the subscription | **new `smoke_parallel.sh`**: harness-style `git worktree add` ×N serial, then N launchers concurrent; run N=2, then N=4; record per-worker wall-clock, exit, any limit error **verbatim** (exit code, stderr, stream event) | 2 + 4 short Sonnet sessions |
| **P4** | Approval-gated command forms on 2.1.281 | F5, F6 unchanged | one worker bundle attempts each form (`python3 -c`, `VAR=x cmd`, pipe, loopback TCP) and records outcome per form | 1 short session |
| **P5** | Skills in headless workers | **Decision, not probe:** F4's isolation deliberately disables skills; keep it. Workers get TDD, code-style and blast-checklist content inline via the preamble (ticket 09). P1 confirms `/tdd` is unavailable | P1 transcript line | — |
| **P6** | Codex on 0.156.1 | F8 holds | ported `smoke_codex.sh` (+ `network-deny` variant) and `smoke_codex_escape.sh` | 3 Codex sessions (OpenAI quota) |
| **P7** | Lint rule names for §3.11 packs outside ruff (eslint, pylint, clippy, Go) | recall-grade names partly wrong | installed tools' rule listings | free |

**Deferred, with a trigger:** outrigger's named upgrade, the *adversarial
boundary matrix*. Per launcher, it deliberately attempts Read-tool reads,
shell reads, glob/search, credential paths (`~/.claude`, keychain) and
outbound network. Outrigger triggered it "before the first plan on a
repository whose secrets matter". v4 translation: **before the first B3
ticket runs headless**. Recorded as a prerequisite in ticket 10, not in
this spike's scope.

### Outputs feeding later tickets

- `claude_p.py` corrections for 2.1.281, if any (this ticket's Touches).
- Preamble rules from P4/F5/F6 (plain commands, env in config files, script
  files not `-c`) → ticket 09. `harness.toml` verify commands must avoid the
  gated forms → ticket 08.
- Limit-error shape from P3 → the usage governor (ticket 09). Measured
  ceiling → default N.
- F9 → ticket 08: `integrate` runs checks on a committed rebase in its own
  worktree, never on a staged merge.
- `docs/vendor-smoke.md` ledger rows: Claude 2.1.281 row 4, Codex 0.156.1
  row 4, dated and build-pinned.

## Acceptance

- One transcript per probe P1–P4, P6, P7 under `.scratch/v4-execution/spikes/`.
  Each ends with a verdict line `CONFIRMED | REFUTED | CEILING=<n>` and names
  the baseline facts it re-verified.
- Any REFUTED names the fallback taken and is recorded in the plan's
  execution-deviations log.
- `smoke_claude.sh` and `smoke_parallel.sh` both pass `--rehearse` (free)
  before any quota run. Quota runs require `--i-understand-this-spends-quota`
  and are triggered by the operator, per run.
- `vendor-smoke.md` updated for both vendors.

## Comments

2026-09-24 — rewritten from outrigger prior art at the operator's direction.
The original 6-item draft asked questions that 5 Claude runs and 4 Codex
attempts had already answered on older builds. It now re-verifies those
answers as expectations and spends new quota only on concurrency (P3) and
the build deltas.

# The launcher contract (v1)

A **launcher** is the executable that starts one headless AI worker. It is the harness's only
seam to any AI tool: the harness never calls a vendor CLI directly, and a new tool is a new
launcher file honoring this contract — never loop surgery.

## Invocation

```
<launcher> <bundle-dir>            # run the worker
<launcher> --dry-run <bundle-dir>  # print what WOULD run (argv, env, generated config); execute nothing
```

## The bundle directory

The caller (the harness) prepares it with exactly:

- `instructions.md` — the role prompt the worker must follow. Tool-neutral prose.
- `params.json` — tool-neutral parameters:

```json
{
  "contract": 1,
  "role": "author",
  "attempt": 1,
  "worker": {"tool": "claude", "model": "<model id>", "effort": "high"},
  "isolation": {},
  "cwd": "/abs/working-dir",
  "timeout_s": 3600
}
```

`contract` is the bundle's major version: a launcher refuses an unknown major fail-closed;
absence means major 1. `result.json` carries the same field back. `role` is one of `author`,
`test_author`, `spec_verdict`, `lens`, `merge`; `attempt` is informational (it lets launchers
and transcripts distinguish retries). `worker.effort` is optional and tool-interpreted.

## Isolation: there are no walls

Workers run unattended in their own git worktree with the tool's permission prompts
bypassed; the integrate step, not containment, guards what lands on the integration branch.
`isolation` is therefore empty for every launcher except Codex, where
`{"sandbox": true, "network": true}` names the workspace profile its lens dispatch runs in
(a Codex worker without an explicit profile would inherit the user's own config).

## Fail-closed (the load-bearing clause)

**A launcher that cannot honor any part of the bundle — an unknown params or isolation
field, an unsupported value, a wrong `worker.tool`, a missing `instructions.md` — must refuse
to launch**: exit nonzero, `result.json` written with `ok: false` and `refused_reason` naming
the part. Never launch on a guess.

## What the launcher must produce (in the bundle dir)

- `result.json` — `{contract, ok, exit, started_at, finished_at, duration_s, timed_out,
  interrupted, refused_reason?, error_summary?, binary?, usage?}`.
  - `ok: true` means the worker session ran to completion with exit 0. **Task success is not
    the launcher's judgment** — the harness judges results; the launcher only reports that
    the session ran.
  - `error_summary` (on `ok: false`) carries the tool's own words, so the caller can classify
    the failure (a usage limit is a cooldown, not a failed attempt).
  - `binary` (recommended) records the tool binary's resolved path and version actually used
    for this spawn. Vendor builds are the fastest-decaying dependency; provenance makes every
    result self-describing.
  - `usage` (recommended) records the session's own accounting: `{input_tokens,
    output_tokens, cache_read_tokens, cache_creation_tokens, cost_usd, num_turns,
    api_duration_ms}` (nulls where the tool does not expose a field), or `{error: <reason>}`
    when the output could not be parsed. Best-effort — an accounting miss never fails an
    otherwise-good launch.
- `transcript.txt` — the worker session's captured output.

Launcher exit code: `0` = worker session ran to completion · nonzero = launch failure,
refusal, timeout or stop (see `result.json` for which).

## Timeout

The launcher enforces `timeout_s`: on expiry it kills the worker's whole process group and
reports `ok: false, timed_out: true`. A hung worker is a failure, not a wait.

## Stop

The worker runs in its own session, so a signal to the launcher's process group never reaches
it. On SIGTERM or SIGINT the launcher forwards SIGTERM to the worker's process group (SIGKILL
after 10 s), writes `result.json` with `ok: false, interrupted: true`, and exits 1. The
harness's operator stop relies on this: a killed launcher must never leave a live session
spending quota and committing.

## Hygiene

A worker must be reproducible, not shaped by whoever's machine it runs on: each launcher
keeps ambient user configuration — settings hooks, MCP servers, slash commands, memory,
session persistence, notify hooks — away from the worker, by whatever flags its tool offers.
Flag semantics are vendor-build behavior, verified only by the launcher's operator-run smoke
(`../smoke_workers.sh`); `--dry-run` shows what would be attempted, the smoke proves what
actually happens.

## Shipped launchers

- `claude_p.py` — Claude Code headless (`claude -p`). `--permission-mode
  bypassPermissions`, `--output-format json` (usage parsed from it), `--setting-sources ""`,
  `--strict-mcp-config`, `--disable-slash-commands`, `--no-session-persistence`, and
  `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`. Refuses any isolation field. **Documented residual:**
  on subscription auth the logged-in account's identity is injected into the session
  regardless of flags (only `--bare` suppresses it, and `--bare` breaks subscription auth).
  Spike 02 (2026-09-25, 2.1.281): unattended edits, tests, pipes, env-prefixed commands and
  commits ran; 4 concurrent workers in 4 worktrees of one repository ran without lock errors.
- `codex_p.py` — Codex CLI headless (`codex exec`), the decorrelated lens. Requires
  `isolation.sandbox: true` and takes a boolean `network`; expresses them as a generated
  per-spawn permission profile (`extends = ":workspace"`, `network.enabled`, `notify = []`)
  in `$CODEX_HOME`, loaded via `--profile` and activated by `-c default_permissions=…` so a
  failed load aborts loudly; removed after the run. `--ignore-rules`, `--strict-config`,
  `--ephemeral`; prompt via stdin; usage parsed best-effort from `--json` events. Spike 02
  (2026-09-25, codex-cli 0.156.1): a read-only review ran unattended and wrote only its
  review file.
- `mini_p.py` — mini-swe-agent on local models (lowest tier). Offers no isolation mechanism;
  takes the empty intent only.
- `grok_p.py` — smoke-first placeholder: refuses every launch until its probe procedure (in
  its docstring) has been run and recorded.
- `mock.py` — the test substrate: executes a scripted scenario (`MOCK_SCRIPT`, or the more
  specific `MOCK_SCRIPT_<ROLE>` / `MOCK_SCRIPT_<ROLE>_A<attempt>`) in `cwd` as the "worker";
  honors a `#MOCK_REFUSE <reason>` first-line directive to simulate a fail-closed refusal.

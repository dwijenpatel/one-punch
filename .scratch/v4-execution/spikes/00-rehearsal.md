# 02 spike — rehearsal (free) — 2026-09-25T03:23Z

Builds: 2.1.281 (Claude Code) · codex-cli 0.156.1

```
$ sh plugin/skills/worker-harness/references/harness/smoke_workers.sh claude --n 4 --rehearse
    "--permission-mode",
    "bypassPermissions",
  "cwd": "/var/folders/5p/cpth8gqn2319mbr1b745wq4w0000gn/T//smoke-workers.ka88Pq/repo/.worktrees/w1",
    "--permission-mode",
    "bypassPermissions",
  "cwd": "/var/folders/5p/cpth8gqn2319mbr1b745wq4w0000gn/T//smoke-workers.ka88Pq/repo/.worktrees/w2",
    "--permission-mode",
    "bypassPermissions",
  "cwd": "/var/folders/5p/cpth8gqn2319mbr1b745wq4w0000gn/T//smoke-workers.ka88Pq/repo/.worktrees/w3",
    "--permission-mode",
    "bypassPermissions",
  "cwd": "/var/folders/5p/cpth8gqn2319mbr1b745wq4w0000gn/T//smoke-workers.ka88Pq/repo/.worktrees/w4",
rehearsal OK (claude, n=4). The real run: plugin/skills/worker-harness/references/harness/smoke_workers.sh claude --n 4  --i-understand-this-spends-quota
$ sh .../smoke_workers.sh codex --review --rehearse
    "--model",
rehearsal OK (codex, n=1). The real run: plugin/skills/worker-harness/references/harness/smoke_workers.sh codex --n 1 --review --i-understand-this-spends-quota
```

Verdict: REHEARSAL OK — bundles, serial worktree creation, claude_p empty-intent → bypassPermissions, codex_p review bundle all dry-run clean. Quota runs P1–P3 pending operator trigger.

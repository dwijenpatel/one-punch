---
name: worker-harness
description: Run a ticketed build unattended with headless worker agents — routing each ticket to a model tier by its tag and size, enforcing completion by artifacts (the harness re-runs the project's verify commands; an agent's word is never the evidence), salvaging failed attempts, and ledgering every outcome. Use when an effort's tickets are cut and the operator wants overnight or walk-away execution, and for resuming any effort (`resume`).
compatibility: Requires git and Python 3.12+ (stdlib only). Worker tools (claude, codex, grok CLIs, mini-swe-agent) are optional per launcher; each launcher refuses fail-closed when its tool or isolation intent is unavailable. Vendor mechanics decay — re-run each launcher's smoke after tool updates.
license: MIT
---

# worker-harness — completion is granted by artifacts

The reference implementation lives in [references/harness/](references/harness/)
— copy it into the project (conventionally `.scratch/<effort>-build/harness/`)
and parameterize via `harness.toml`. It is stdlib-only, strictly typed, and
split functional-core / imperative-shell: every routing decision is a pure
function you can test without mocks; every side effect lives in a thin shell.

## The contract (what makes overnight runs trustworthy)

1. **Done = commit + harness-verified.** After a worker claims a ticket, the
   harness re-runs the project's verify commands (from `harness.toml`, e.g.
   fmt/lint/tests) itself. A red commit is a FAILED attempt, whatever the
   worker said.
2. **Blocker gating** from ticket metadata (`Blocked by:`); the frontier is
   computed, never assumed. Learning gates (`L-NN`) block like any other edge.
3. **Fresh session per ticket, file handoffs** — prompt = preamble + ticket
   text (+ restore note); no conversation state between tickets.
4. **Salvage**: a failed attempt's work is stashed per-ticket and restored on
   retry — attempts accumulate; nothing is thrown away. Failed attempts retry
   ONE tier up with a root-cause note; two escalated failures park the ticket.
5. **Ledger**: every dispatch, outcome, limit-hit, and cost lands in an
   append-only JSONL event log. All state is a pure fold over it — which is
   also why `resume` works from a bare clone.

## Routing (pipeline v3 §8, implemented in `core.py`)

Tag × Size → hard tier floor; ε-greedy bandit within the tier (exploit
best-by-recency-weighted-ledger, explore least-sampled; critical never
explores; exploration only on low/medium sizes); usage governor (spend +
observed limit errors → cooldowns) filters candidates first; nothing at/above
floor → park, take other frontier work. The tier ladder and floor table are
DATA in `harness.toml`, owned by the operator; the ledger auto-demotes, only
the operator promotes (via retro).

## Launchers ([references/harness/launchers/](references/harness/launchers/))

One bundle contract (params.json + instructions.md in → result.json +
transcript out; fail-closed `validate()`; binary provenance; killpg timeouts).
Launchers are deliberately self-contained per vendor — vendor CLIs are the
fastest-decaying dependency; one vendor's breakage stays one file's problem.
Isolation intent (deny-read walls, network policy) is translated per vendor
and REFUSED when inexpressible — never launched unwalled. Each launcher
carries a smoke procedure; run it before first real use and after tool
updates, and record dated, build-pinned results.

## Entry points

- `run` — work the frontier until done or nothing progresses (multi-pass).
- `resume` — report effort state (frontier, in-flight debris, pending gates,
  parked tickets, cooling providers) and continue. The answer to "where were
  we?" after any gap, on any machine.
- `plan-probe <ticket>` — ask a cheap model for its implementation plan so a
  strong reviewer can seed trap notes into the ticket before dispatch.

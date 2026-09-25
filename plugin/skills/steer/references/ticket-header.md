# Ticket header block

Every ticket `to-tickets` writes at A2 opens with these plain header lines,
one per line, directly under the title — the worker harness parses them, so
keep the exact keys and spelling. Local tracker default:
`.scratch/<effort>/issues/NN-slug.md`.

```
# NN — <ticket title>

Status: ready-for-agent
Blocked by: 03, 05
Tag: code-complete | contract
Blast: B0 | B1 | B2 | B3 — <one-line reason>
Size: low | medium | high | very-high
Touches: src/store/**, tests/store/**
Decides: D-014
Depends-on: D-003, D-007
Reference: <owner>/<repo>@<full SHA>:<path> (<dependency | fork | port | pattern>)
```

| Key | Required | Meaning |
|---|---|---|
| `Status` | yes | `ready-for-agent` when cut; the harness and planner move it on |
| `Blocked by` | yes | ticket numbers that must merge first, or `—` |
| `Tag` | yes | determinacy only: `code-complete` (the ticket fully specifies the code) or `contract` (the worker designs within a stated contract). Risk never goes here |
| `Blast` | yes | level plus the reason, naming the factor that set it — declared per the `blast-radius` skill; never below the highest blast-map zone the `Touches` globs overlap |
| `Size` | yes | the planner's estimate; retro audits it against actuals |
| `Touches` | yes | comma-separated globs of every path the ticket may change, in the blast map's glob dialect. A promise the harness checks: a diff outside it merges only as licensed breakage |
| `Decides` | no | only when the planner delegates one local decision to this ticket; the worker records the choice in its handoff and the planner files the ledger row |
| `Depends-on` | no | ledger rows the worker must honor; the harness injects them into the worker's instructions |
| `Reference` | no | a file from a reference dossier at its pinned SHA, with the reuse mode ratified at H2. The worker follows it unless the ticket says otherwise and reports deviations. `port` and `fork` carry an attribution obligation (third-party notices entry) |

Two tickets never decide the same question: a ledger ID appears in at most
one `Decides` line across the effort.

## Body

After the header, in this order:

1. **Intent** — a few sentences: what this ticket makes true, and why.
2. **Constraints**, not a step checklist — e.g. "no TODOs, no partial
   implementations, no new dependencies without a ledger entry", plus any
   ledger decisions that bind it.
3. **Numeric ranges** wherever scope is quantitative (limits, sizes,
   timeouts, counts).
4. **Acceptance checks as shell commands** that pass only when the ticket is
   done, written to survive later tickets (assert behavior, not line
   numbers). The milestone closure re-runs every one of them against the
   integration head, so each must be runnable from the repo root without
   setup the ticket doesn't state.
5. **Worked examples with exact values** — input, expected output.

Explicitness is the cost lever: a `code-complete` ticket a mid-tier worker
can transcribe is cheaper than a vague one a top-tier worker must interpret.

## Worked example

```
# 07 — reject expired session tokens

Status: ready-for-agent
Blocked by: 04
Tag: code-complete
Blast: B3 — changes session token validation (exposure, silent)
Size: low
Touches: src/auth/session_check.py, tests/auth/test_session_check.py
Depends-on: D-009

A session token past its expiry must be rejected at the one validation seam
(`check_session`), with the rejection indistinguishable from a bad signature.

Constraints: no new dependencies; decision logic stays pure (clock passed in);
no change to the token format (D-009).

Clock skew allowance: 30 seconds, not configurable.

Acceptance:
  python -m pytest tests/auth/test_session_check.py -q
  python -m pytest tests/auth/test_session_check.py -q -k "expired and skew"

Example: token issued at 1700000000 with ttl 1 expires at 1700000001; with
the 30-second skew it is valid at now=1700000031 and rejected at
now=1700000032.
```

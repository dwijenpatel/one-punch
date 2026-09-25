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
| `Touches` | yes | comma-separated globs of every path the ticket may change, in the blast map's glob dialect. A promise the harness checks: a diff outside it merges only as licensed breakage. **A B3 ticket's `Touches` include its test paths**: the independent test author may write only test files inside `Touches`, so a B3 ticket without them cannot get its tests-first commit and parks |
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
   setup the ticket doesn't state. Closure reads only machine-readable
   acceptance, in the grammar the `worker-harness` skill's handoff reference
   defines: command lines indented directly under an `Acceptance:` line (as
   in the worked example below), or a fenced block inside an Acceptance
   section. Prose acceptance is reported as "no acceptance commands" and is
   never re-run.
5. **Worked examples with exact values** — input, expected output.

## Tickets that touch rendered UI

Acceptance that asserts presence — a marker class, an element, a string in
the served HTML — passes on a page that renders wrong. A ticket that touches
rendered UI therefore carries, among its acceptance commands, a **browser
walk**: a Playwright script or an equivalent headless-browser check,
invoked as a command so closure re-runs it.

- **Variants.** The walk covers every one of the effort's example URLs and
  variants. The planner lists them once at A2 — each a URL (or route plus
  state), a label, and its defining behaviour in one sentence — in the first
  UI ticket, which creates the walk; later UI tickets extend it and put its
  path in their `Touches`. The same list, with its passing results, is what
  links handed to the operator are generated from.
- **Two widths.** Every variant is walked at desktop width (about 1280px) and
  at phone width (about 375px).
- **Defining behaviour, not presence.** Each variant's assertion checks what
  makes it that variant: a comparison view lays the compared items out side
  by side with aligned attributes; a strip spans the width of the grid below
  it; no image overflows its card at either width; a filter changes which
  items render. Asserting that the element exists is not acceptance.
- **Boundary cases are variants.** Where a layout depends on a count, the
  walk includes the zero, one and many cases.

```
Acceptance:
  npx playwright test e2e/variants.spec.ts
```

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

Example: token issued at t=100 with ttl 1 expires at t=101; with the
30-second skew it is valid at now=131 and rejected at now=132.
```

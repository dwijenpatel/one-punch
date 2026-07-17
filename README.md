# one-punch

**One-liner in, code-complete out.** A pipeline that takes a product idea from a
sentence to reviewed, tested, independently-verified code — with the human appearing at
exactly four gates and everything else running walk-away.

```
one-liner → [brainstorm] → PRD → tech-plan → plan-review → execution loop → verification
              (S0, opt)    (G1)   (G2a)       (G2b)         (G3 halt doors)  (G4 merge)
```

The authority for every design decision here: [docs/design/pipeline.md](docs/design/pipeline.md).

## Lineage

Built from the measured evidence of the **outrigger** lab (`~/repos/outrigger`) — a
three-arm gated-vs-ungated build experiment, live review-instrument probes, a blind
plan-review firing that caught a build-breaking spec defect pre-implementation, and the
adopted practice corpora (Claude Code built-ins, superpowers, the Anthropic cowork
plugins). Outrigger remains the lab: future behavior changes to this pipeline earn
their numbers there and port here. The frozen capstone of that arc is
`outrigger docs/design/one-liner-to-code-complete.md@3ebe595`; this repo carries the
living copy.

## Install

```sh
claude plugin marketplace add ~/repos/one-punch
claude plugin install one-punch@one-punch
```

Gives every repo `/one-punch:tech-plan` and `/one-punch:plan-review`. Stage skills used
as-is from elsewhere: `product-management:write-spec` and `product-brainstorming`
(cowork mirror), built-in `/code-review` and `/simplify`.

## Run the pipeline

1. **PRD** (attended): `/product-management:write-spec <one-liner>` — answer its
   questions; every *blocking* open question gets answered or waived in the doc (G1).
2. **Plan** (attended, ≤3 exchanges): `/one-punch:tech-plan <prd.md>` → CLAUDE.md
   conventions + `docs/plans/…` + `tasks.json` with per-task determinacy tiers;
   ratify (G2a).
3. **Plan review**: `/one-punch:plan-review` (report-only) — ratify confirmed rewrites
   (G2b, skipped when clean).
4. **Build** (walk-away): `python3 runner/runner.py --repo <repo> --skip-plan --yes` —
   fresh session per task: implement → review → simplify, halting only at genuine
   operator doors (G3).
5. **Verify**: independent test-authored oracle + whole-branch `/code-review`; the
   merge decision is yours, made with evidence in hand (G4).

## Status (v0.1)

- ✅ Skills: `tech-plan` (written, needs first live trial), `plan-review` (live-fired:
  10 confirmed findings blind, $23.87 full tier / lean tier available).
- ✅ Runner: migrated from the outrigger nocode trial, live-hardened (headless
  permission bypass, ledger git-exclusion, resume-correct closure base, silent-no-op
  guards, per-session spend telemetry). Mock suite: `zsh runner/tests/mock_suite.zsh`.
- ⬜ Runner deltas (design §6.2, in order): status-file worker contract; two-verdict
  task review; determinacy-tier model routing; churn budget 3 + diff-size trajectory;
  root-cause note on escalation; fix-wave closure dispatch.
- ⬜ Oracle stage: adapt the outrigger author machinery to consume PRD acceptance
  criteria.
- ⬜ First end-to-end run (a real one-liner, all six stages).

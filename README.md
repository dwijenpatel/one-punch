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

- ✅ Skills: `tech-plan` (first live trial 2026-07-17: goodhart-sim, 0 operator
  questions), `plan-review` (live-fired full tier: 10 confirmed blind, $23.87; lean
  tier live-fired: 2 raised → 0 confirmed, clean).
- ✅ Runner: migrated from the outrigger nocode trial, live-hardened (headless
  permission bypass, ledger git-exclusion, resume-correct closure base incl.
  `--skip-plan` run-base, silent-no-op guards, per-session spend telemetry, pid-unique
  rundirs). Mock suite (15 scenarios): `zsh runner/tests/mock_suite.zsh`.
- ✅ Status-file worker contract (schema'd done|blocked; blocked = penalty-free halt
  with the worker's reason; done+no-commit = contradiction halt).
- ✅ Oracle stage: blind-by-construction — author session in a clone at the
  pre-implementation sha, authors from `--oracle-source` (default `docs/prd.md`);
  suite runs against the built tree; red → exit 3 (merge evidence, not a halt).
- ✅ **First end-to-end run — 2026-07-17, goodhart-sim** (a Goodhart's-Law visual
  simulator, one-liner → merged main): PRD ratified → tech-plan (4 tasks, 0
  questions) → lean plan-review (0 confirmed) → walk-away build (4/4 tasks, one
  escalation self-recovered, zero halts) → closure review (2 real findings, 0
  critical) → blind oracle **40/40 green** → operator merge. Build spend $31.32 /
  105 min / 19 sessions (sonnet implement $3.43, opus review+verify $27.90).
  Notable: the oracle missed a behavior-neutral contract narrowing the closure
  review caught (`/simplify` removed a spec-mandated attr the tests never pinned) —
  layered instruments earning their seats, and a live datum that **simplify is
  spec-blind** (candidate delta: pass the task spec into the simplify prompt).
- ⬜ Runner deltas remaining (design §6.2): two-verdict task review; determinacy-tier
  model routing (live datum: code-complete implement 68s/$0.45 + clean review vs the
  fussiest contract task churning to escalation); churn budget 3 + diff-size
  trajectory; root-cause note on escalation; fix-wave closure dispatch.

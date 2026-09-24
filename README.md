# one-punch

**A pipeline for building real software with agents — where decisions are made
by execution, contracts are compiled from decisions, workers are routed by
measured quality, and the human appears only where judgment lives.**

You bring a project idea and an agent (Claude Code today; Codex support is
smoke-gated, in progress). one-punch turns "loose idea" into "shipped,
reviewed, resumable effort" through a fixed set of stages with named human
gates — and it treats itself the way it treats your code: measured, ledgered,
amended on evidence.

## The problems it exists to fix

- **The agent built the wrong thing** — because nobody asked about the goals
  *behind* the goal. one-punch opens every effort by eliciting your
  intent-stack (audiences, success scenarios, learning goals) into a private,
  durable INTENT.md that every later decision cites. Questions are asked in
  descending fan-out order; low-impact craft decisions are derived on the
  record and batch-ratified, not dripped at you one "agree?" at a time.
- **The plan was confidently wrong about reality** — because prose asserted
  how external systems behave. Here, mechanism claims enter contracts only via
  executed probe transcripts (spikes), and research lives in a graded evidence
  corpus with warrants and decay, behind a mandatory fork-or-build gate.
- **The overnight agent "finished" and it was garbage** — because its own
  report was the evidence. The worker harness re-runs your project's verify
  commands itself; completion is granted by artifacts, never claimed by
  agents. Failed attempts are salvaged and retried one model tier up.
- **You paid top-tier prices for transcription work** — routing sends each
  ticket to a model tier by its determinacy tag and size, explores
  alternatives with a small bandit so calibration stays honest, and backs off
  providers whose usage windows are exhausted.
- **You shipped the project and learned nothing** — when you declare learning
  goals, implementation literally gates on measured, verified learning:
  assessment tickets block the frontier, graded blind, waivable only loudly.

## Install (Claude Code)

```bash
claude plugin marketplace add <your-gh-user>/one-punch
claude plugin install one-punch@one-punch
```

Developing one-punch itself: pass your local clone's path to
`claude plugin marketplace add` instead of `<your-gh-user>/one-punch`.

Then, in your project directory, one command:

```
/one-punch:start
```

`start` checks its own prerequisites and prints install commands for anything
missing (it composes the mattpocock-skills plugin and the evidence-kit method
under the hood — you don't need to know that in advance; the front door
teaches you). Returning to an effort later — any session, any machine:
`resume`.

Other harnesses: skills are written to the
[Agent Skills open standard](https://agentskills.io) and install via
`npx skills@latest add <your-gh-user>/one-punch`. A vendor is *supported* only
when its [smoke checklist](docs/vendor-smoke.md) rows pass — currently green:
Claude Code. In progress: Codex. Placeholder: grok.

## The pipeline at a glance

```
intent → evidence pass → destination → decision map → [contract → review]
 (INTENT.md,  (fork-or-build   (grilling)   (wayfinder;      (to-spec; one
  private      gate; graded                  decision memos,   adversarial
  overlay)     corpus)                       spikes)           round)
        → tickets → build → retro
          (tag+size)  (worker harness: routed tiers,   (evidence memos;
                       verify-as-authority, salvage,    the process amends
                       learning gates)                  itself here)
```

Authority: [docs/design/pipeline.md](docs/design/pipeline.md). Everything in
it is either measured or carries a named re-earn test.

## Reference

**Skills** (in [plugin/skills/](plugin/skills/)):

- **start** — the front door: prereqs → scaffold (+ private overlay) → intent
  → evidence pass → hand-off to the decision map.
- **intent** — elicit the goal-stack into a privacy-tiered INTENT.md; the
  fan-out rule for all questioning.
- **spike** — settle external-behavior questions by executing throwaway code;
  transcripts are execution warrants.
- **contract-review** — one adversarial divergence-pair pass over a compiled
  contract. Provisional; carries its own re-earn clause.
- **worker-harness** — unattended ticket execution: routing, verification,
  salvage, ledger, `resume`. Reference implementation (typed, stdlib-only
  Python + per-vendor launchers) in its references/.
- **learning-gates** — typed learning goals, assessment tickets as blockers,
  blind grading, loud waivers.
- **retro** — compile ledgers + outcome reports into evidence memos; the only
  path to tier promotions and process amendments.

**Composed, not vendored** (installed separately; `start` detects and guides):
[mattpocock-skills](https://github.com/mattpocock/skills) — wayfinder,
grilling, to-spec, to-tickets, tdd, code-review — and
[evidence-kit](https://github.com/dwijen/evidence-kit) — the graded-corpus
research method. one-punch is deliberately a thin layer: deltas only,
composition over paraphrase.

## Lineage

v1 (total-spec AFK fleets) was retired by measurement — four review rounds, 79
findings, amendments minting defects as fast as they fixed them. v2 (HITL,
decisions by execution) was validated on a live build. v3 (this) adds intent,
evidence, routing, learning gates, and retro — every addition carrying the
session, measurement, or trial that earned it, in the repo history and
[docs/evidence/](docs/evidence/). MIT.

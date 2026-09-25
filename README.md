# one-punch

**Steer, then swarm. Agents run ahead of you, you decide the forks, a
parallel harness builds explicit tickets, and scrutiny goes where the damage
would be.**

You bring a project idea and an agent harness (Claude Code today; Codex runs
as the cross-vendor reviewer). one-punch turns a loose idea into a shipped,
reviewed, resumable effort. The human appears in a few dense sittings and at
the diffs that could really hurt, and nowhere else. It treats itself the way
it treats your code: measured, ledgered, amended on evidence.

## The problems it exists to fix

- **The agent built the wrong thing**, because nobody asked about the goals
  *behind* the goal. Every effort opens with one short intent sitting
  (≤15 minutes) that records the goal, the audience, the catastrophes and
  the riskiest assumptions in an `INTENT.md` every later stage reads.
- **Setup ate the week and nothing ran.** Before you are asked anything
  evidence could answer, agents fan out in parallel: spikes on the top risks,
  a walking skeleton (or, in an existing codebase, a survey plus
  characterization tests), prior-art dossiers with a reuse recommendation,
  and a light evidence pass. You then sit once for a decision memo that asks
  only the forks you would be glad to have been asked. Everything else is
  decided on the record and reopenable by ID.
- **The overnight agent "finished" and it was garbage**, because its own
  report was the evidence. Work lands only through `integrate`, a script
  that re-runs your verify commands and hygiene checks on the exact tree it
  fast-forwards. An agent's word is never the evidence.
- **Review effort went everywhere except where it mattered.** Every ticket
  carries a **blast radius** (B0 contained … B3 severe: auth, money,
  destructive data, trust boundaries, and the process files that judge the
  work). Scrutiny scales with it. At B3 an independent agent writes the tests
  first, a model from another family reviews, and you read the diff before
  it merges. B0–B1 take the light path. The harness recomputes blast from
  the actual diff and escalates when a ticket under-declared.
- **Agent code rotted the codebase.** Code standards come in three layers:
  a short stated `Code style` section in `AGENTS.md`, lint enforced by the
  verify commands (exceptions are ledgered decisions, not self-granted), and
  a review rubric for what tools can't decide.
- **You paid top-tier prices for transcription work.** Each ticket routes to
  a model tier by its determinacy, size and blast radius. Failed attempts are
  salvaged and retried one tier up. Providers whose usage windows are
  exhausted are backed off.

## Install (Claude Code)

```bash
claude plugin marketplace add dwijenpatel/one-punch
claude plugin install one-punch@one-punch
```

Update:

```bash
claude plugin marketplace update one-punch
claude plugin update one-punch@one-punch
```

Plugin updates load at session start, so restart the session after updating.

one-punch composes the [mattpocock-skills](https://github.com/mattpocock/skills)
plugin and the [evidence-kit](https://github.com/dwijenpatel/evidence-kit)
research method. You don't need to install them first: `steer`'s preflight
detects each one, checks that it is current, and prints the exact install or
update command for anything missing or stale.

Other harnesses: the skills follow the
[Agent Skills open standard](https://agentskills.io) and install with
`npx skills@latest add dwijenpatel/one-punch`. A vendor counts as
*supported* only when its [smoke checklist](docs/vendor-smoke.md) rows pass.
Claude Code is green. Codex passes as the read-only B3 lens, and its skill
rows are open.

## First run

In your project directory (new or existing):

```
/one-punch:steer <your idea, in a sentence or a paragraph>
```

`steer` runs a preflight, then the intent sitting, then launches the agent
lanes and comes back with a decision memo. After you ratify the forks, it
compiles tickets and shows a one-screen ticket graph. That is a veto window,
not a gate: the build starts unless you object. Coming back to an effort
later, in any session or on any clone:

```
/one-punch:steer resume
```

## The pipeline at a glance

```
H1 intent ─► A1 parallel lanes ─► H2 decision memo ─► A2 compile ─► Build ─► H3 milestone
(you, once   (≤4 agents: risk      (you: forks only;   (ledger,       (run --parallel N:   (you: demo,
 per effort)  spikes, skeleton or   reuse fork; blast   tickets with   worktree per ticket, closure, review,
              survey, prior art,    map ratified)       Blast +        integrate is the     accept, merge
              evidence)                                 Touches)       only path; you read  to main; retro)
                                                                       B3 diffs)
```

H = a human sitting, A = agents only. A1 → H2 → A2 → Build → H3 repeats per
milestone. The harness stops on an empty frontier, parked decisions or an
operator stop; you steer between runs, never mid-run.

Authority: [docs/design/pipeline.md](docs/design/pipeline.md). Everything in
it is either measured or carries a named re-earn test.

## Skills

In [plugin/skills/](plugin/skills/):

- **steer**: the front door. Preflight, H1 → A1 → H2 → A2 → build hand-off
  → H3 per milestone, plus `steer resume`. Owns the lane briefs, the
  prior-art dossier format and the ticket header.
- **intent**: the one intent sitting. Catastrophes seed the blast map; the
  risk register drives the A1 spikes. The private overlay is offered only on
  signal.
- **decision-memo**: the altitude rule (fork only on one-way doors, product
  boundaries and conflicts with intent) and the memo format, at H2 and H3.
- **blast-radius**: levels B0–B3, the blast-map format and default pattern
  pack, the scrutiny ladder, and the domain checklists.
- **code-style**: the three-layer standards system, per-language lint packs,
  and the review rubric.
- **field-guide**: the short, planner-curated file of surprises, traps and
  commands that work, injected into every worker's instructions.
- **worker-harness**: `run --parallel N`, `integrate`, routing, the B3
  review path, salvage, the event ledger, `resume` and `closure`. The
  reference implementation (stdlib-only, strictly typed Python plus
  per-vendor launchers) lives in its references/.
- **spike**: settles how an external system behaves by running throwaway
  code; the transcript is the warrant.
- **retro**: compiles ledgers and outcome reports into evidence memos, led by
  the headline metric (unattended tickets merged per operator intervention).
  It is the only path to tier promotions and process amendments.
- **contract-review**: one adversarial pass over a compiled contract, on
  request only. Provisional; it carries its own re-earn clause.
- **learning-gates**: opt-in, proposed only when `INTENT.md` names a
  learning goal. Implementation then gates on measured, verified learning.

**Composed, not vendored:** mattpocock-skills (wayfinder, grilling,
prototype, research, to-spec, to-tickets, tdd, code-review,
resolving-merge-conflicts) and evidence-kit. one-punch is deliberately a
thin layer: deltas only, composition over paraphrase.

## Developing one-punch

Working rules: [AGENTS.md](AGENTS.md). To try a local clone, pass its path
to `claude plugin marketplace add` instead of `dwijenpatel/one-punch`.

Verify (every harness suite, both launcher suites, `mypy --strict` over all
harness code; needs [uv](https://docs.astral.sh/uv/)):

```bash
bash plugin/skills/worker-harness/references/harness/verify.sh
```

**Dogfooding one-punch on itself.** The harness source
(`plugin/skills/worker-harness/references/harness/**`) evaluates as **B3**
under the default blast-map pack. Its code and test fixtures name the auth,
money and destructive-data domains the pack's content patterns look for.
The pack's own harness zone (`.scratch/**/harness/**`) matches only an
installed copy, not this source path. The raw `default-pattern-pack.toml`
also trips its own patterns through its match examples. So a one-punch
effort run on this repo must settle it at A2 in its blast map. One option
is a repo zone for that path at a deliberate level: B3 means every harness
ticket takes the tests-first, lens and operator-diff-read path. The other is
an operator lowering recorded as a decision-ledger row. Without either,
every harness ticket escalates to B3 through the diff detector.

## Lineage

v1 (total-spec AFK fleets) was retired by measurement: four review rounds,
79 findings, amendments minting defects as fast as they fixed them. v2 (HITL,
decisions by execution) was validated on a live build. v3 added intent,
evidence, routing, learning gates and retro, but its front half stalled a
real effort before any code was built: too many touchpoints, ceremony before
value, decisions serialized through the human. v4 (this) keeps v3's back
half and replaces the front with steer-then-swarm: parallel agent lanes, one
decision sitting, blast-radius scrutiny and a parallel harness. Every change
carries the session, measurement or trial that earned it, in the repo
history and [docs/evidence/](docs/evidence/). MIT.

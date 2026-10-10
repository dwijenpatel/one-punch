# one-punch

**Build software with AI agents while making only the decisions that need you.**

The third version of this tool spent eight days asking me questions, one per
session, and wrote no code. The fourth had a clickable skeleton of the
project running 44 minutes after I typed the first prompt. Most of the
difference comes from one rule:

> Only stop for the human when, looking back, they'd be glad they were asked.

The agent workflows I'd tried before failed in one of two ways. Some asked me
about everything, and I became a full-time reviewer of questions I didn't
need to see. Others asked me nothing, ran overnight, and handed back
confident work built on a wrong guess.

one-punch is a set of skills for coding agents (Claude Code today) that tries
to avoid both. You make the few decisions that change the outcome. The agents
do the rest in parallel, and a script, not an agent's own report, decides
which of their changes merge.

## A project, start to finish

Say you want an online store for a small coffee roaster: product pages, a
cart, checkout, order emails. I haven't built this store. The example shows
the sequence, and the measured results from real projects are under
[How it got here](#how-it-got-here).

```mermaid
flowchart LR
    A["You: one short<br/>conversation"] --> B["Agents: research,<br/>test risks, build<br/>a running skeleton"]
    B --> C["You: decide<br/>a few forks"]
    C --> D["Agents: build in<br/>parallel; a script<br/>checks each merge"]
    D --> E["You: read the<br/>high-risk diffs"]
    E --> F["You: see it running,<br/>accept, merge"]
    F -. next milestone .-> B
```

*The sequence of one milestone. This diagrams the process; it isn't a
measurement.*

### 1. You describe it and answer a short round of questions

```
/one-punch:steer an online store for a small coffee roaster
```

The agent reads the repo, then asks a handful of questions one at a time. It
starts with the ones whose answers change the most later decisions.

**Agent:** What does "done" look like? Describe the demo you'd show someone.

**You:** A customer finds a coffee, adds two bags, pays, and gets an order
email. I can see the order.

**Agent:** What would be catastrophic if we got it wrong?

**You:** Charging someone the wrong amount. Leaking customer addresses.
Losing an order after taking payment.

**Agent:** Here are the assumptions I think are riskiest. Rank them. First,
the payment provider's hosted checkout can handle subscriptions later.
Second, order emails will send reliably from the host you want. Third,
product data can live in files for now, with no admin screen.

The questions should take about fifteen minutes. The agent writes your
answers into a one-page statement of intent. It lists the catastrophes and
the assumptions that could end the project.

### 2. You leave, and the agents get to work

Up to four agents work at once, each on a different job.

- **One tests the risky assumptions by running code.** It runs a real
  test-mode checkout against the payment provider and saves the transcript.
- **One builds a walking skeleton:** a bare store you can click through,
  running on your machine.
- **One finds prior art.** It reads existing store starters and the payment
  provider's own sample code. For each it notes the license, the evidence
  that it works, and whether to depend on it, copy from it, or only borrow
  its structure.
- **One gathers evidence** on the open questions, such as how small stores
  usually handle guest checkout.

In an existing codebase this step changes. The agents survey the code you're
about to modify, and they write tests that pin down its current behavior
before anyone touches it.

### 3. You come back to a short list of decisions

First you see the skeleton running. Then the agent brings you the decisions
that pass the rule at the top of this page.

| You're asked | Why it's yours |
|---|---|
| Take payment on the site in version one, or only collect orders? | It changes the product itself. |
| A hosted checkout page, or card fields embedded in your site? | It's hard to reverse, and it sets how much card-handling risk you own. |
| Start from an open-source store starter, or build fresh? | Adopting a dependency is expensive to undo. |
| Is this the right list of high-risk areas: payments, customer data, order records? | It decides which code you'll review yourself. |

The agent settles the rest without asking, and writes each decision down.

| You're not asked | The agent does this instead |
|---|---|
| CSS framework, folder layout, test runner, naming | It decides and records a one-line reason. |
| Products per page, image sizes, date formats | It decides and records. |
| Linter rules, how config loads | It installs tested defaults. |

Every recorded decision gets an ID. If you disagree with one later, name it
and the agent reopens it. Each question you do get comes with a
recommendation, the evidence behind it, and the options it rules out.

### 4. The build runs without you

The agent splits the work into small tickets. Each ticket declares the files
it will touch and how risky it is. Then the workers start.

- Up to four workers build at once. Each has its own copy of the repo and a
  ticket that shares no files with the others.
- A script decides which changes merge. It re-runs your tests and a set of
  checks on the exact code about to land. An agent saying "I'm done and it
  works" merges nothing.
- Cheaper models take the routine tickets, and stronger models take the hard
  and risky ones.
- A worker that hits a question it shouldn't answer alone takes the safe,
  reversible option and flags it. If no option is reversible, that ticket
  waits for you and the others carry on.

### 5. You read only the diffs that could hurt

Most tickets merge on their own: the product grid, the cart, the styling.

The checkout, the payment webhook, and any code that touches customer records
go through more. A separate agent writes the acceptance tests before the code
exists. A reviewer from a different model family checks the result against a
list of the ways that kind of code fails quietly. Then the change waits for
you to read it.

That's the one place the workflow spends your attention on purpose. It's why
the agent asked about catastrophes on day one.

### 6. You see it running and report problems

At the end of a milestone you get the store running. The agent has checked
that every link it hands you matches its label. For every screen, it has
walked the pages at desktop and phone width and looked at the screenshots
itself before showing you.

You'll still spot things. Each one you report becomes a failing test first,
then a fix. The agent then re-checks the neighboring pages, because a fix for
one page can break the page beside it.

Then the next milestone starts, and you're asked only about decisions that
have newly come into view.

## When it stops for you, and when it doesn't

The same rule sorts every possible interruption into one of two columns.

| It stops for | It doesn't stop for |
|---|---|
| Your intent, once, at the start | Craft decisions an experienced engineer would make without asking |
| Decisions that are expensive to reverse | Questions the evidence already answered |
| The product's scope | Questions it can settle by running code |
| Conflicts between your stated intent and the evidence | Permission to proceed, when you've already seen the plan |
| High-risk diffs, before they merge | Routine diffs |
| A decision a worker couldn't safely make alone | Progress updates |
| The running result, at each milestone | |

Two details keep the left column short. The agent batches small, low-risk
questions into one turn. And "go ahead and build" is a window in which you
can object, not a gate you have to open.

## How it got here

I've rebuilt one-punch four times. Each time, a real project showed me where
the previous version wasted effort or attention. The records are in
[docs/evidence/](docs/evidence/) and the commit history.

**Version 1: write a complete spec, then let cheap agents build it
unattended.** One plan went through four rounds of adversarial review and
collected 79 confirmed defects. Every fix added between five and eight new
defects for each ten it removed. The spec made claims in English about how
outside systems behave, and English has no interpreter. I stopped
establishing facts in prose. A claim about how a system behaves now needs
code that ran.

**Version 2: keep a human in the loop, settle behavior by running throwaway
code, build in small test-first tickets.** The same project then built
cleanly: 9 tickets, 104 tests, no review rounds. Running the code surfaced
two facts about the framework that four rounds of review had missed. This
version is still the back half of the current one.

**Version 3: add intent-gathering, a graded evidence pass, model routing, and
a retro after each effort.** The front half stalled a real project. Over
eight days it produced 16 decision tickets, each resolved in its own session
with me, and no code. It asked too often, it did setup before producing
anything I could see, and it asked about things it should have decided. I
replaced the front half.

**Version 4: agents work in parallel before asking anything, one decision
sitting, scrutiny by risk, a script that decides merges.** The build half
borrows from Cursor's published work on
[agent swarms](https://cursor.com/blog/agent-swarm-model-economics). In the
first trial, on an existing web codebase, the skeleton ran after 44 minutes.
I sat down three times before the build started. Two parallel workers then
built 5 tickets in 14 minutes with no merge conflicts and no input from me.

That trial also failed in a specific way. Four visible defects reached me
while every automated check was green. I could see each one in a single
screenshot. The checks had confirmed that elements existed on the page, and
nothing more. That result drove the most recent changes.

- **Checks on anything visual now walk the real pages** at two widths and
  assert each page's purpose. The agent looks at screenshots before I do.
- **The agent verifies every link before handing it to me.** Two of the four
  defects were links whose labels promised something the page didn't do.
- **The fixes I report after a demo now have their own stage, with rules.**
  In the trial I took ten turns in 25 minutes there, my densest stretch of
  the run, and one fix broke the case next to it.
- **I removed two stops.** "Ratify the defaults" and "go ahead" came back to
  back with nothing new between them, so they're one turn now. Small
  low-risk decisions arrive together.
- **A lighter mode is official** for small or time-boxed work, on one
  condition: every change still lands through the checking script.

I also dropped things. An earlier version put headless workers behind sandbox
walls and probed for escapes. Establishing those walls took nine live test
runs and they weren't worth it. Workers now run freely inside their own copy
of the repo, and the merge script guards the branch. I left out a routine
second-agent review of every plan as well. The
[superpowers](https://github.com/obra/superpowers/blob/main/RELEASE-NOTES.md)
project measured its own plan-review loop and reported that it doubled run
time while quality scores stayed the same. Extra review goes where the risk
is.

## The checks behind the output

- **Risk sets the scrutiny.** Every change gets a level, from contained
  (docs, tests) to severe (auth, money, destructive data operations, and the
  files that define the checks themselves). The level sets which model builds
  the change, who writes its tests, who reviews it, and whether you read the
  diff. A check on the actual diff catches a ticket labeled lower than the
  code it touched. The docs call this blast radius.
- **Facts come from running code.** Anything the plan assumes about an
  outside system gets a short experiment with a saved transcript.
- **Code standards have three layers.** The agents read a short list of
  rules. The merge script enforces lint checks. A reviewer applies a
  checklist for the judgment calls no tool can make. An exception to a rule
  has to be a recorded decision, so an agent can't grant itself one.
- **Each decision has one owner.** The planning agent makes design decisions
  and records them, and the workers build. Two workers never decide the same
  question two different ways.
- **The process measures itself.** Each milestone ends with a retro. Its
  headline number is tickets merged unattended, divided by the times you had
  to step in unplanned.

## Where it stands

As of October 2026, version 0.4.3:

- It works in Claude Code. It uses OpenAI's Codex as the second-opinion
  reviewer for high-risk changes. I claim support for another agent tool only
  when its row in the [smoke checklist](docs/vendor-smoke.md) passes.
- The front half has run on one real codebase, with the results above.
- The unattended parallel build loop is tested, but new. It passes its own
  suite of 126 tests and strict type checks, and it has run live with four
  concurrent workers. The first trial used the lighter mode, so the full loop
  hasn't yet built a whole real project. That's the next trial.
- I built it for the way I work. Take the parts that help.

## Install

Claude Code:

```bash
claude plugin marketplace add dwijenpatel/one-punch
claude plugin install one-punch@one-punch
```

To update, run these and start a new session:

```bash
claude plugin marketplace update one-punch
claude plugin update one-punch@one-punch
```

one-punch builds on two other projects: the
[mattpocock-skills](https://github.com/mattpocock/skills) plugin and my
[evidence-kit](https://github.com/dwijenpatel/evidence-kit) research method.
You don't need to install them first. The first step of every run checks for
each one and prints the exact command for anything missing or out of date.

For other agent tools, the skills follow the
[Agent Skills open standard](https://agentskills.io) and install with
`npx skills@latest add dwijenpatel/one-punch`.

## First run

In your project directory, new or existing:

```
/one-punch:steer <your idea, in a sentence or a paragraph>
```

To come back later, in any session or on any clone:

```
/one-punch:steer resume
```

## Skills

The skills live in [plugin/skills/](plugin/skills/). Each row gives one
skill's job.

| Skill | Job |
|---|---|
| **steer** | The front door. It runs the whole sequence above and reports where an effort stands. |
| **intent** | It runs the opening conversation. |
| **decision-memo** | It sorts decisions into "ask" and "record", and runs the decision sitting. |
| **blast-radius** | It defines the risk levels, the per-repo risk map, and checklists of how risky code fails quietly. |
| **code-style** | It holds the three-layer code standards. |
| **field-guide** | It keeps a short file of surprises and traps that the agents write for each other. |
| **worker-harness** | It contains the parallel build loop and the script that decides merges. |
| **spike** | It settles a factual question by running code. |
| **retro** | It turns a milestone's records into measured findings and proposed changes. |
| **contract-review** | It makes one adversarial pass over a written spec, on request. |
| **learning-gates** | Optional. It gates progress on your own measured learning, if learning is a goal. |

The full process is in [docs/design/pipeline.md](docs/design/pipeline.md),
which also defines the stage names the skills use.

## Developing one-punch

The working rules are in [AGENTS.md](AGENTS.md). To try a local clone, pass
its path to `claude plugin marketplace add` in place of
`dwijenpatel/one-punch`.

One command runs every test suite and the strict type checks. It needs
[uv](https://docs.astral.sh/uv/).

```bash
bash plugin/skills/worker-harness/references/harness/verify.sh
```

Running one-punch on its own repo needs one decision first. The default risk
map classes the build loop's source as severe, because that code names the
payment, auth, and data-deletion patterns the map looks for. Either accept
that and review every change to it, or record a deliberate lower level for
that path.

MIT licensed.

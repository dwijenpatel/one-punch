---
name: decision-memo
description: "Compile and run the H2/H3 decision sitting: demo, risk-register update, the few forks the operator owns (each asked as one plain question with a recommendation, an evidence tier, and what it forecloses), a decided-for-you list of high-blast decisions that were independently checked instead of asked, the blast map as one question about what will wait for the operator's read, and recorded defaults announced by ID (never voted). Applies the owner test — ask only what the operator, in hindsight, is glad they were asked — including at B3. Checks the memo before the sitting. Use at H2, once parallel research (spikes, prototypes, code survey, prior-art dossiers, evidence lane) has landed and the operator needs to ratify what it changed; use the H3 mini-memo variant when building unlocks new forks at a milestone."
compatibility: Works in any agent harness that can hold a multi-turn conversation. Composes the mattpocock `grilling` skill for follow-up rounds over the decision frontier and evidence-kit for evidence grading and tier citation — degrades to a plain-text threaded Q&A and self-stated tiers if either isn't available.
license: MIT
---

# decision-memo — the owner-gated decision sitting

Upstream agents (spikes, a prototype or skeleton, a code survey, prior-art
dossiers, a retrieval-grade evidence pass) have already produced findings.
This skill turns those findings into the one sitting where the operator
spends attention: it separates what genuinely needs a human from what an
agent can decide, check and record, presents the former as a short
conversation, and files both into the decision ledger. It is invoked at
**H2** (after the parallel fan-out) and, in a smaller form, at **H3** (per
milestone, when building surfaces new forks).

## The owner test — the heart of this skill

**The governing test:** ask only what the operator, in hindsight, is glad
they were asked. Nothing overrides it — not a blast level, not a category
below.

The measured failure this rule exists for: on one effort with a
high-blast-heavy map, a sitting asked 22 questions in an hour; the operator
picked the recommendation on 15 of 16, answering ~400-word asks in under a
minute. The questions were technical-correctness calls (statistics,
isolation mechanics, cache keys) where the operator held no information the
planner lacked. They were rubber-stamped, which is worse than not asked: the
ledger records an oversight that did not happen.

**Ask (a fork) only when the operator owns the consequence or the
knowledge:**
- **their resources** — money, subscription quota, their own time (review
  load, manual steps they must do);
- **their accounts, repos and data** — credentials, another repository they
  own, its history, personal data, production;
- **a rule they wrote** — a conflict with recorded intent (INTENT.md's
  goals, audiences, non-goals, must-not-foreclose) or with a rule or
  runbook the operator authored;
- **a product boundary** — what the thing is or does, who it's for, what it
  refuses to do;
- **taste or a stated preference the evidence can't settle** — and the
  operator has signalled they care about it.

**Everything else is decided for them,** at every blast level:
- **B0–B2:** a recorded default (`D-NNN`, one line of rationale), B2
  flagged. Reopenable by ID; never voted on (see Recorded defaults).
- **B3:** decided by the planner, **independently checked before the
  sitting** (a spike for any external-behavior claim, a second model's
  review of the decision, or both — the evidence-kit adversarial grade when
  it rests on an outside claim), and listed in the sitting's
  **decided-for-you** block. B3 raises the *checking*, not the *asking*.
  A B3 decision that also passes the owner test is a fork like any other.

If you catch yourself drafting a fork whose honest answer is "the
recommended option; the operator has nothing to add," it is not a fork. The
failure mode this rule does not excuse is the opposite: a decision that
spends the operator's money, quota, time or accounts slipping through as a
default.

Fan-out ordering carries over from the intent sitting: the `intent` skill
asks by descending fan-out, and this skill asks its forks in the same order
— highest fan-out first — subject to dependencies (below).

## Before the sitting — check the memo

A memo presented with a wrong citation or a false choice makes the operator
rule on something that then changes under them. Before the first fork is
asked:

1. **Citations.** Every fork's evidence link and every claim about the spec,
   intent or a prior ruling is checked against its source — by a fresh
   reviewer (a different model when the harness can launch one) that sees
   the memo and the sources, not the drafting transcript.
2. **Options.** Each fork's options are real alternatives (not one test
   described two ways), and the recommendation states what it forecloses.
3. **Dependencies.** For every pair of forks, ask: does ruling one change
   the other's options? Order dependents after their inputs. A fork whose
   options depend on an unruled fork is never asked before it.
4. **Owner test, again.** Re-run the owner test on every fork after the
   checks. Forks that fail it move to decided-for-you.

Record the check (who ran it, what it changed) in the memo header.

## How a question reads

Each fork is one message the operator can answer from a phone without
scrolling back:

- **First line: the question in plain words** — what is being decided and
  why it is theirs ("This spends your subscription overnight: …").
- **Second line: "If you don't mind either way, I'll do X."** Always present.
- **≤ ~120 words in the body.** Options, the recommendation, what it
  forecloses, the evidence tier. Detail lives behind a link to the memo.
- **No internal IDs in the ask** (fork numbers, decision IDs, section
  references, lane names). They belong in the memo and the ledger, not in
  the question.
- **Answer choices describe outcomes**, not option letters: "Runner may
  start graders", not "A: amend runbook". Always include a **"your call"**
  choice that delegates to the recommendation; its use is recorded and is
  itself evidence the fork failed the owner test.
- If the harness offers clickable choices, use them with the labels above;
  otherwise list the choices in plain text.
- One fork per message. Never ask a choice in the same message as a status
  report; the status goes first, alone, or into the memo.

## H2 — the decision memo (one sitting)

Compile and walk the operator through, in order:

1. **Demo.** The skeleton or prototype running, or — brownfield — the
   survey's module map. Show it before asking anything.
2. **Risk register update.** Each `R-n` from INTENT.md's risk register →
   confirmed / killed / pivoted, each with a link to what settled it. A
   statement, not a question.
3. **Forks** — the only questions in the sitting, ordered as above. Each
   carries the question, the options, a recommendation, an **evidence link
   and its evidence-kit tier** (a fork resting on Tier B or C evidence says
   so), and **what it forecloses**.
   - **Reuse decisions** — for every problem area with a prior-art dossier,
     choose the reuse mode (`dependency` / `fork` / `port` / `pattern` /
     build fresh). A fork only when the owner test passes: a license the
     operator must accept, a paid or account-bound service, or code the
     operator owns elsewhere whose maintenance they'd carry. Otherwise
     decided-for-you, with the dossier linked.
   - **Adversarial-evidence trigger** — a one-way-door decision (fork or
     decided-for-you) resting on an *external* claim gets an evidence-kit
     **adversarial-grade** pass first.
   - **Absence claims** — "nobody has built this" is never asserted from the
     corpus alone. State it as one line in decided-for-you ("Searched N
     sources, found none; tell me if you know one"), not as a question that
     blocks the sitting.
4. **Decided for you.** One line per checked B3 decision and per non-fork
   reuse decision: `decision — why — how it was checked — what would
   reopen it`. The operator vetoes by replying with the line; silence is
   not a vote, it is the default holding. Keep it to one screen; link the
   rest.
5. **Blast map — one question.** The map encodes risk tolerance, and its
   cost lands on the operator's time, so it is theirs — but as one question,
   not a zone-by-zone ratification:
   - which zones will **wait for the operator's diff read** (B3 zones with
     `operator_review` true, per the `blast-radius` skill), with the
     estimated share of tickets that will hold;
   - which B3 zones are **checked without a read**, and how;
   - the projected **B3 share of tickets** (warn above ~20%).

   Ask: "These N areas will wait for your read; these are checked without
   you. Change any?" A zone the operator moves is recorded as a ledger row.
6. **Recorded defaults — announced, never voted.** Every remaining craft
   decision, one line each: `D-NNN — decision — one-line rationale`, B2
   flagged inline. Post the list (or link it) and say how to reopen one:
   by ID, at any time. There is no "ratify the batch" question — a 22-line
   vote answered in seconds is not oversight. When the milestone will be
   all B0/B1 and the pipeline ends compilation with a ticket-graph veto
   window, the list rides with the ticket graph instead.

Close with a **not-yet-specified list**: items that are genuinely undecidable
now, each with the milestone that will make it decidable. A statement, not a
question.

### Follow-up rounds, same sitting

An answer often unlocks a fork nobody could have posed before it. Run these
as a short additional round in the **same sitting**: compose the mattpocock
`grilling` skill for this — invoke it by name when the frontier moves. Each
new fork passes the owner test and the pre-sitting check first.

## H3 — the milestone mini-memo

Same instrument, smaller: forks, decided-for-you and recorded defaults only
(skip demo and the risk-register update — those belong to the milestone
report; re-ask the blast-map question only if the milestone's work proposes
a change to it). The owner test and the pre-sitting check apply
identically. A decision an earlier sitting classified as a default or
decided-for-you gets reopened here if building proved it needed the
operator — reopen by ID and note the reclassification as its own ledger row.

## Conversational surface, never a pasted wall

Run H2/H3 the way the `intent` skill runs its opening: one fork at a time,
threaded from the answer before it. Never enumerate the full fork list up
front. Lists that are not questions (decided-for-you, defaults,
not-yet-specified) are posted once, skimmable, and never turned into a vote.

**Low-blast forks may share a message** (up to three) when each passes the
owner test, none is a one-way door, and none depends on another's answer.

## Measuring the sitting

Record per fork, for the retro: whether the answer matched the
recommendation, whether "your call" was used, the ask's length, and the
reply time. A fork answered with the recommendation within about a minute
of a long ask is a **quick-agree** — evidence that it failed the owner test.
The `retro` skill compiles these.

## Filing

Every fork's outcome, every decided-for-you line and every recorded default
becomes a row in `docs/decisions.md` (or wherever this effort records
decisions): `ID · decision · one-line rationale · owner · status
(active / superseded by D-x) · ADR link (if any)`. Owner is `operator` for
forks and `planner` for decided-for-you and defaults; decided-for-you rows
also name how they were checked. A decision that meets the mattpocock
`domain-modeling` skill's ADR criteria also gets an ADR. Superseding a
decision leaves every `D-NNN` reference a visible grep target — mark the
row, never delete it.

Use [references/decision-memo-template.md](references/decision-memo-template.md)
as the working document while compiling the memo; its shape mirrors the H2
format above section for section.

---
name: decision-memo
description: "Compile and run the H2/H3 decision sitting: demo, risk-register update, forks (each with options, a recommendation, an evidence link and its evidence-kit tier, and what it forecloses), the reuse fork, blast-map ratification, and recorded defaults (D-NNN, B2 flagged). Applies the altitude rule — the operator is asked only about one-way doors, product boundaries, and conflicts with recorded intent; everything else is decided and recorded as a reopenable default. Presents as a concise, threaded conversation, never a pasted wall, with follow-up rounds in the same sitting. Use at H2, once parallel research (spikes, prototypes, code survey, prior-art dossiers, evidence lane) has landed and the operator needs to ratify what it changed; use the H3 mini-memo variant when building unlocks new forks at a milestone."
compatibility: Works in any agent harness that can hold a multi-turn conversation. Composes the mattpocock `grilling` skill for follow-up rounds over the decision frontier and evidence-kit for evidence grading and tier citation — degrades to a plain-text threaded Q&A and self-stated tiers if either isn't available.
license: MIT
---

# decision-memo — the altitude-gated decision sitting

Upstream agents (spikes, a prototype or skeleton, a code survey, prior-art
dossiers, a retrieval-grade evidence pass) have already produced findings.
This skill turns those findings into the one sitting where the operator
spends attention: it separates what genuinely needs a human from what an
agent can decide and record, presents the former as a short conversation, and
files both into the decision ledger. It is invoked at **H2** (after the
parallel fan-out) and, in a smaller form, at **H3** (per milestone, when
building surfaces new forks).

## The altitude rule — the heart of this skill

**The governing test:** ask only what the operator, in hindsight, is glad
they were asked. The categories below are where that test usually lands; when
a category and the test disagree, the test wins.

Every design decision the upstream work surfaced gets classified before it
reaches the operator:

**Ask (a fork) only when the decision is at least one of:**
- a **one-way door** — expensive or impossible to reverse once shipped (a
  wire format, a public interface, a data layout, an adopted dependency,
  anything the reuse fork touches);
- a **product boundary** — what the thing is or does, who it's for, what it
  refuses to do;
- a **conflict with recorded intent** — INTENT.md's goals, audiences,
  non-goals, or must-not-foreclose list point one way and the evidence
  points another.

**Everything else is a default:** decide it, write one line of rationale, log
it as `D-NNN` in the ledger, and move on. A default is never silent — it's
recorded and reopenable by ID — but it is not asked. This is the rule the
whole memo enforces; if you catch yourself drafting a fork whose answer is
"the obviously better option and nobody would pick otherwise," it's a
default, not a fork. The failure mode this rule targets is a pasted wall of
craft questions that burns the operator's attention on things an agent
should just decide; the failure mode it does not excuse is asking too little
and letting a real one-way door slide through as a default.

**Blast radius overrides the classifier, never softens it:** per the
`blast-radius` skill's scrutiny ladder — **B3 is always a fork**, no matter
how settled the decision looks, no exceptions; **B2 may be recorded as a
default but is flagged** in the batch so the operator can spot-check it;
**B0/B1 are craft defaults**, no flag. What falls into which level is the
`blast-radius` skill's own pattern pack and level definitions — consult it
and the ratified blast map rather than re-deriving a decision's severity
here.

Fan-out ordering carries over from the intent sitting: the `intent` skill
asks by descending fan-out, and this skill asks its forks in the same order
— highest fan-out first.

## H2 — the decision memo (one sitting)

Compile and walk the operator through, in order:

1. **Demo.** The skeleton or prototype running, or — brownfield — the
   survey's module map. Show it before asking anything; forks read
   differently once the operator has seen what exists.
2. **Risk register update.** Each `R-n` from INTENT.md's risk register →
   confirmed / killed / pivoted, each with a link to the transcript (spike,
   prototype session, survey finding) that settled it.
3. **Forks** — the only questions in the sitting, fan-out ordered. Each
   carries: the question, the options, a recommendation, an **evidence link
   and its evidence-kit tier** (a fork resting on Tier B or C evidence says
   so out loud — the operator is ratifying under that uncertainty, not
   blind to it), and **what it forecloses** if decided this way.
   - **Reuse fork** — asked for every problem area where a prior-art
     dossier exists: adopt the reference as `dependency` / `fork` / `port` /
     `pattern`, or build fresh, with the dossier as the evidence. A one-way
     door by definition — it always gets a fork, never a default.
   - **Adversarial-evidence trigger** — a one-way-door fork resting on an
     *external* claim (a vendor's stated behavior, a library's documented
     guarantee, another codebase's claimed properties) is not ratified on
     retrieval-grade evidence alone. Run an evidence-kit **adversarial-grade**
     pass on that claim first; this is the one place evidence weight escalates
     automatically, without the operator asking for it.
   - **Absence claims** — "nobody has built this," "no library does X," and
     similar negative claims are never asserted from the corpus by
     themselves; a corpus that didn't find something is not proof nothing
     exists. Put the claim to the operator here and let them confirm or
     contradict it from what they know.
4. **Blast map — for ratification.** The blast map itself is a fork, always
   asked, because it encodes the operator's risk tolerance: which paths and
   patterns count as B0/B1/B2/B3 (per the `blast-radius` skill's levels and
   default pattern pack). As part of ratifying it, list every design
   decision that falls inside a **B3** zone as its own fork per the rule
   above — never bundle a B3 decision into the defaults batch.
5. **Recorded defaults.** Every remaining craft decision, one line each:
   `D-NNN — decision — one-line rationale`. Present the whole batch for
   ratification at once (the operator reopens any single one by ID rather
   than approving them one at a time); defaults that touch a **B2** zone are
   flagged inline so they don't scroll past unnoticed.
   **Hold the batch for the build veto window** when the milestone will
   likely be all B0/B1 — no default is B2-flagged and no fork this sitting
   was B2 or higher — and the orchestrating pipeline ends compilation with a
   ticket-graph veto window: the batch is then shown with the ticket graph
   in one turn, and one reply both ratifies it and releases the build. If
   any ticket comes out B2 or higher, the held batch is presented as its own
   turn first. Tell the operator at the end of the sitting that the
   defaults will arrive with the ticket graph.

Close with a **not-yet-specified list**: items that are genuinely undecidable
now. Name the milestone that will make each one decidable. Fog stays fog —
don't force a premature answer just to close out the sitting.

### Follow-up rounds, same sitting

An answer often unlocks a fork nobody could have posed before it (a chosen
reuse mode implies a new integration question; a killed risk removes an
option from another fork's list). Run these as a short additional round in
the **same sitting**, never a new session: compose the mattpocock `grilling`
skill for this — invoke it by name when the frontier moves.

## H3 — the milestone mini-memo

Same instrument, smaller: per milestone, once building has surfaced new
forks, run the same conversational format restricted to **forks and
recorded defaults only** (skip demo and the risk-register update — those
belong to the milestone report, not the mini-memo; re-ratify the blast map
only if the milestone's work proposes a change to it). The altitude rule and
the B3-is-always-a-fork rule apply identically. This is also where a
decision an earlier sitting classified as a default gets reopened, if
building proved it was actually a one-way door — reopen by ID, add the new
fork, and note the reclassification as its own ledger row rather than
silently editing the old one.

## Conversational surface, never a pasted wall

Measured on first live use: a full question list dumped in one message reads
as a form, not a conversation, and the operator either disengages or answers
shallowly. Run H2/H3 the way the `intent` skill runs its opening: one fork at
a time, threaded from the answer before it, with enough framing that the
operator knows why they're being asked. Batch only
the parts that are inherently a batch — the recorded-defaults review and the
not-yet-specified list are meant to be skimmed as a list, not asked
question-by-question, since neither is a question. Never enumerate the full
fork list up front; the operator sees fork *n+1* after answering fork *n*,
and sees the whole defaults batch at once only when it's time to ratify it.

**Low-blast forks may share a turn.** Up to three forks go in one turn when
every fork in that batch is B0 or B1 and none is a one-way door — so a reuse
fork never qualifies. Take them consecutively in fan-out order, and never
batch a fork whose options depend on another answer in the same batch. B2
and B3 forks and every one-way door stay one per turn. The governing test
still applies to each fork in a batch: every one must be a question the
operator is glad they were asked.

## Filing

Every fork's outcome and every recorded default becomes a row in
`docs/decisions.md` (or wherever this effort records decisions): `ID ·
decision · one-line rationale · owner · status
(active / superseded by D-x) · ADR link (if any)`. A decision that meets the
mattpocock `domain-modeling` skill's ADR criteria (hard to reverse,
surprising, a real trade-off) also gets an ADR; the ledger row links it.
Superseding a decision leaves every `D-NNN` reference to it a visible grep
target — don't delete a superseded row, mark it.

Use [references/decision-memo-template.md](references/decision-memo-template.md)
as the working document while compiling the memo (draft it there section by
section as findings land, then walk the operator through it live); its
output — the forks' ratified answers and the defaults batch — is what gets
transcribed into `docs/decisions.md` afterward. The template's shape mirrors
the H2 format above exactly, section for section, so nothing said here needs
restating there.

---
name: intent
description: Open an effort in one sitting (~15 minutes) by eliciting the operator's intent-stack — the goal behind the engineering goal, audience, constraints, catastrophic failure modes, known prior art, brownfield risk areas, and risky assumptions with kill/pivot criteria — into a durable INTENT.md whose Catastrophes section seeds the effort's blast map and whose risk register carries the kill/pivot criteria. Use at the start of any non-trivial effort (normally invoked by the effort's front-door skill), or whenever a decision cannot be grounded in recorded intent.
compatibility: Works in any agent harness. Uses a structured-question UI if the harness offers one, plain conversational text otherwise. Voice input is fine where supported; never required.
license: MIT
---

# intent — goals before frames

Every planning posture interrogates decisions inside the frame the operator
presents. This skill interrogates the frame. Its output changes more downstream
decisions per question asked than any other instrument in the pipeline.

**The fan-out rule** (governs all questioning in this pipeline): a question's
value is its fan-out — the number of downstream decisions its answer changes.
Ask in descending fan-out order. Intent questions have fan-out 10+; craft
questions have fan-out ≈ 1 and are batch-ratified elsewhere, never asked here.

## When

One sitting, once per effort, target ≤15 minutes: the effort's front-door
skill invokes this first, before any research or fan-out work. Ask the
checklist below in order; stop early once another answer would
change no decision you can foresee — don't pad a 15-minute sitting into a
longer one for its own sake.

If, later in the effort, some decision can't be grounded in recorded intent,
that gap is itself an intent question — but answer it as a short, dated
addendum appended to the existing `INTENT.md` (one or two targeted follow-ups),
never as a full re-run of this checklist. H1 happens once; a gap found later
is a small patch to its output, not a new sitting.

## The opening — concise, conversational

The question list below is YOUR checklist, never a pasted wall of text. Open
in three lines or fewer: what this is, that candor is safe, then question 1
alone. Example shape:

> Before we plan: a few open questions, one at a time, about fifteen minutes
> total. Be as candid as you can — embarrassing or self-interested reasons are
> exactly the useful ones, and if anything feels too exposed to write down,
> say so and it stays out of the file. First: what are we building, why now,
> and what does *done* look like?

One question per turn, threading from answers. Never enumerate the full list
upfront, and never open with the privacy tier menu — that surfaces later,
only if an answer needs it (see Privacy below).

## The questions (agent checklist)

Ask openly and generatively — these are conversation starters, not a form.
Pull the thread wherever an answer implies an undeclared goal or a missed
catastrophe; stop when a new answer changes no decision you can foresee.

1. What are we building, and why now? What does *done* look like — describe
   the demo you'd show to prove it shipped.
2. Who uses or sees it — users, readers, employers, communities, specific
   organizations?
3. Constraints: stack, deadline, budget, hard non-goals, anything that must
   not be foreclosed even though this effort won't build it.
4. **What would be catastrophic if this went wrong?** Data loss or
   corruption, a security or privacy breach, money moved wrongly, users
   locked out, anything irreversible or silent. This seeds the effort's blast
   map — hand these answers to whatever skill drafts it.
5. **What do you already know about?** Prior art, competitors, reference
   codebases, articles, people. The operator seeds research targets here;
   later research starts from these seeds, never from a blank search.
6. **Brownfield only** (skip on a greenfield effort): which area of the code,
   what must not break, what you already know is fragile. Record "must not
   break" under Constraints and known-fragile areas under Catastrophes.
7. **Risky assumptions.** Propose a list drawn from answers 1–6; the operator
   ranks it and adds their own. Each assumption gets a kill/pivot criterion —
   the cheapest test whose result would tell you to stop or change course.

Follow-ups only where an answer changes a foreseeable decision.

## Privacy — structural, fails closed, offered not forced

State the limit honestly before asking: elicitation works only with candor,
and some intents are private. ACTIVELY ENCOURAGE candor: the goals people
hesitate to state — career positioning, impressing a specific company, proving
a point, money — are usually the highest-fan-out answers in the whole
elicitation. Never react to a motive with judgment; mine it for design
consequences. Intent shared is design leverage; intent withheld is priced-in
risk, not failure.

Default: everything goes straight into the tracked `INTENT.md` — Tier 2,
public record, no tier menu, no ceremony. Offer the other tiers only when an
answer itself signals a private motive (a specific employer, a competitive
angle, money, anything the operator wouldn't want a stranger reading in this
repo's history) — never proactively for a neutral answer, and never as an
upfront menu:

- **Tier 0 — spoken only**: lives in agent memory if the harness has any;
  never written to any repo.
- **Tier 1 — private overlay**: `.private/` in the project repo — gitignored
  in the SAME commit that creates it, itself a separate git repository with
  its own private remote. Structurally unpublishable: not tracked by the main
  repo at all. Off by default — ceremony is opt-in, set it up only once an
  item actually needs it. Setup steps:
  [references/private-overlay.md](references/private-overlay.md).
- **Tier 2 — public record (default)**: goals the operator is happy to state
  in `INTENT.md` or the map notes.

**Ordering guarantee:** if Tier 1 is invoked, write the `.gitignore` entry
BEFORE creating any private file. Assert `git check-ignore .private/` in any
later preflight.

**Sanitized derivation rule:** decisions informed by a private item are
recorded publicly at engineering altitude ("eval promoted to P0"), never
quoting or paraphrasing `.private/` content into tracked files, commit
messages, or upstream issues. If the project indexes its own repos, `.private/`
goes on the deny list.

## Output

Write [references/INTENT-template.md](references/INTENT-template.md) filled
in — `INTENT.md` at the effort root by default, or `.private/INTENT.md` if
Tier 1 was invoked for the whole file, plus a Tier-2 sanitized echo wherever
the effort keeps map notes. Keep it to one page: this is a steering artifact
loaded at the top of every planning session, not an archive, so cut prose
that a table or a pointer says more compactly.

If the operator raises a learning goal unprompted — a domain they want to
build real expertise in rather than delegate — don't turn this into an eighth
checklist question. Note it in one line under Constraints (e.g. "operator
wants hands-on ownership of X") and propose the `learning-gates` skill to
type it, attach its assessment mechanism, and gate tickets on it. Learning
goals are an opt-in follow-up, never a default question here.

Intent licenses out-of-frame proposals (upstream contributions, publication
timing, article outlines) — always proposed to the operator, never executed
unilaterally.

---
name: intent
description: Open an effort by eliciting the operator's intent-stack — the goals behind the engineering goal, audiences, success scenarios, futures not to foreclose, and learning goals — into a durable, privacy-tiered INTENT.md that every later planning session loads. Use at the start of any non-trivial effort (normally via the start skill), or whenever a decision cannot be grounded in recorded intent.
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

- At effort start (the `start` skill invokes this first).
- Mid-effort, whenever a recommendation cannot be grounded in recorded intent —
  that gap is an intent question, not a preference question.
- At stage boundaries (map complete, contract ratified, pre-build): re-read
  INTENT.md aloud in one paragraph and ask what changed.

## The opening — concise, conversational (operator feedback, first live use)

The question list below is YOUR checklist, never a pasted wall of text. Open
in three lines or fewer: one sentence of what this is, one clause on privacy,
then question 1 alone. Example shape:

> Before we plan: a few open questions, one at a time. Answers can stay
> private (they live in `.private/`, never published — or say "off the
> record" for memory-only). First: why this project, and why now?

One question per turn, threading from answers. The tier menu surfaces only
when FILING answers ("I'll record that as private — object if you want it
public or memory-only"), not upfront. Never enumerate the full list or the
tier taxonomy in the opening.

## The questions (agent checklist)

Ask openly and generatively — these are conversation starters, not a form.
Pull the thread wherever an answer implies undeclared goals; stop when a new
answer changes no decision you can foresee.

1. Why this project, and why now? What happens if it never ships?
2. Who, besides you, will see or use the result — users, readers, employers,
   communities, specific organizations?
3. Describe the best realistic month-after-success. What changed?
4. Any second-order happy paths worth designing for? Longshots welcome.
5. What adjacent futures must we not foreclose? What outcome would make this
   effort a regret?
6. Which domains here do you want to build real expertise in, versus delegate
   entirely? (Learning goals are TYPED — see the learning-gates skill — and
   their targets set here are binding.)

## Privacy — structural, fails closed

State the limit honestly before asking: elicitation works only with candor,
and some intents are private. Intent shared is design leverage; intent
withheld is priced-in risk, not failure. Then offer three tiers PER ITEM:

- **Tier 0 — spoken only**: lives in agent memory if the harness has any;
  never written to any repo.
- **Tier 1 — private overlay (default)**: `.private/` in the project repo —
  gitignored in the SAME commit that creates it, itself a separate git
  repository with its own private remote. Structurally unpublishable: not
  tracked by the main repo at all. Setup steps: [references/private-overlay.md](references/private-overlay.md).
- **Tier 2 — public record**: goals the operator is happy to state in the
  README or map notes.

**Ordering guarantee:** write the `.gitignore` entry BEFORE creating any
private file. Assert `git check-ignore .private/` in any later preflight.

**Sanitized derivation rule:** decisions informed by private intent are
recorded publicly at engineering altitude ("eval promoted to P0"), never
quoting or paraphrasing `.private/` content into tracked files, commit
messages, or upstream issues. If the project indexes its own repos, `.private/`
goes on the deny list.

## Output

Write [references/INTENT-template.md](references/INTENT-template.md) filled in,
at the tier the operator chose (default `.private/INTENT.md`), plus a Tier-2
sanitized echo in the effort map's Notes. Learning goals hand off to the
learning-gates skill for typing, targets, and budget.

Intent licenses out-of-frame proposals (upstream contributions, publication
timing, article outlines) — always proposed to the operator, never executed
unilaterally.

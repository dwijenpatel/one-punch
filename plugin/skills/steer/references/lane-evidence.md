# Lane brief — Evidence

Copy to `milestones/<m>/a1/evidence-brief.md`, fill every `<…>`, hand the
filled file to a fresh agent.

---

**Lane:** Evidence · **Effort:** <name> · **Milestone:** <m>
**Model:** <named explicitly>
**Timebox:** <wall-clock; default 2 hours>
**Grade:** retrieval — fixed. Adversarial grade is never run from this lane;
it is triggered only through the `decision-memo` skill at H2, for a
one-way-door fork resting on an external claim.

## Questions

Each question could rule a product direction in or out. A question that
cannot name the fork or risk it serves is dropped before the pass starts.

| # | Question | Serves (fork or R-n) | What answer would change the decision |
|---|---|---|---|
| Q1 | <…> | <F-n or R-n> | <…> |

Brownfield additions: upstream and issue-tracker history for the touched
area (<area>) — known bugs, reverted fixes, maintainer statements about
intended behavior.

## Your job

Invoke evidence-kit's **pass** operation at **retrieval grade**:

1. **Lake first.** Read the evidence lake for existing holdings on each
   question and reuse them; a question the lake already answers at adequate
   tier and within its decay window costs nothing new. Lake location:
   <path, or "none — see fallback">.
2. Run the pass for what remains, writing new holdings **back into the
   lake** so evidence compounds across efforts.
3. Per-effort corpus: <"none" by default; a corpus path only if the operator
   accepted one>.

**Fallback if evidence-kit is unavailable:** use the mattpocock `research`
skill for each question, write its findings file into this lane's folder,
and mark every claim **ungraded** — the H2 memo then states that the forks
resting on them have no tier.

## Output

Write `milestones/<m>/a1/evidence-findings.md`:

```
Grade: retrieval · Lake: <path or none> · Fallback used: yes | no
| Q# | Serves | Answer (one line) | Holding link | Tier | Decay class | Reused from lake? |
Fast-decaying facts the build may rest on: <fact — decay class — recheck trigger>
Absence findings: <"no source found for X" — sample searched, date>
Dropped questions: <question — why no fork or risk>
Kill criterion hit: yes | no
```

The fast-decaying list feeds the H3 recheck; keep it even when short.

## Stop rules

- An answer that meets an INTENT.md kill criterion → write the findings with
  `Kill criterion hit: yes` and stop.
- Timebox reached → write what is answered and what remains.
- Never message other lanes or the operator.

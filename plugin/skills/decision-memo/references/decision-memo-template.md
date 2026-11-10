# Decision memo — <effort name> — <H2 | H3 milestone: name>

Sitting date: <date> · Compiled from: <spike transcripts, prototype/skeleton,
code survey, prior-art dossiers, evidence-lake holdings — link each>
Pre-sitting check: <who checked it (fresh reviewer / model), what it changed:
citations fixed, forks reordered, forks moved to decided-for-you>

## 1. Demo

<What the operator is shown before anything is asked.>

*(H3 mini-memo: omit this section.)*

## 2. Risk register update

| R-n | Assumption | Outcome | Evidence |
|---|---|---|---|
| R-1 | <from INTENT.md> | confirmed / killed / pivoted | <link> |

*(H3 mini-memo: omit unless a milestone spike touched a still-open risk.)*

## 3. Forks (the only questions)

Only decisions that pass the owner test: the operator's resources (money,
quota, time), their accounts / repos / data, a rule they wrote or recorded
intent, a product boundary, or a stated taste. Ordered by fan-out, dependents
after their inputs. Asked one at a time.

### Fork F-<n> (memo only — the ask never shows the ID)

- **Why it's theirs:** <which owner category>
- **The ask, as sent** (≤ ~120 words):
  > <plain question> · If you don't mind either way, I'll do <X>. · <options,
  > recommendation, what it forecloses, evidence tier>
- **Answer choices:** <outcome-describing labels> / your call
- **Evidence:** <link> — tier <A|B|C>
- **Depends on:** <fork IDs, or none>
- **Operator answer:** <recorded> · matched recommendation: <yes/no> ·
  reply time: <s> · "your call" used: <yes/no>

### Reuse fork (only when it passes the owner test)

- **Dossier:** <link> — what it solves, evidence it works, license
- **Why it's theirs:** <license to accept / paid service / changes or couples to a repo they own>
- **The ask, as sent:** <…>
- **Operator answer:** <…>

### Adversarial-evidence check (only when triggered)

<The external claim, the adversarial-grade pass run before the fork or
decided-for-you line, and its verdict.>

## 4. Decided for you

High-blast decisions checked instead of asked, and reuse decisions that
didn't pass the owner test. One line each; the operator vetoes by replying
with the line. Silence means the decision holds.

| ID | Decision | Why | How it was checked | What would reopen it |
|---|---|---|---|---|
| D-<NNN> | <…> | <one line> | <spike / second-model review / adversarial pass> | <…> |

Absence claims: <"Searched N sources (list), found none; tell me if you know one.">

## 5. Blast map — one question

| Zone | Paths / patterns | Level | Waits for your read? | Reason |
|---|---|---|---|---|
| <zone> | <globs> | B3 | yes (operator_review) | <owner category> |
| <zone> | <globs> | B3 | no — checked by <tests-first / lens / spike> | <one line> |

Projected B3 share of tickets: <n / N> (warn above ~20%). Content patterns
anchored (no bare common words): <yes / list fixes>.

**The ask:** "These N areas will wait for your read; these are checked
without you. Change any?" **Operator answer:** <…>

## 6. Recorded defaults (announced, not voted)

Reopen any row by ID at any time. B2 rows flagged.

| ID | Decision | Rationale | Flag |
|---|---|---|---|
| D-<NNN> | <craft decision> | <one line> | — |
| D-<NNN> | <touching a B2 zone> | <one line> | **B2** |

**Posted:** <in this sitting / with the ticket-graph veto window>

## 7. Not yet specified

| Item | Why it can't be decided yet | Milestone that reveals it |
|---|---|---|
| <…> | <…> | <…> |

---

## Filing checklist (after the sitting)

- [ ] Every fork → a ledger row (owner: operator), with its measurement
      (matched recommendation, reply time, "your call").
- [ ] Every decided-for-you line → a ledger row (owner: planner) naming how
      it was checked.
- [ ] Every recorded default → a ledger row, B2 flag carried over.
- [ ] Blast map, with `operator_review` per B3 zone and any operator change →
      `docs/blast-map.md`.
- [ ] Not-yet-specified items → carried forward, not dropped.

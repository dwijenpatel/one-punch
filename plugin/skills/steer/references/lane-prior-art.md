# Lane brief — Prior art

Copy to `milestones/<m>/a1/prior-art-brief.md`, fill every `<…>`, hand the
filled file to a fresh agent.

---

**Lane:** Prior art · **Effort:** <name> · **Milestone:** <m>
**Model:** <named explicitly>
**Timebox:** <wall-clock; default 2 hours>

## Purpose

Find codebases that already solve our problem, so H2 can decide per problem
area whether to adopt one or build fresh. Every dossier is evidence for a
**reuse fork**, which the operator decides.

## Problem areas

<one line each; for each, the fork or R-n it serves. A candidate that serves
none of these is out of scope.>

## Seeds (start here)

<the operator's known prior art from INTENT.md, verbatim — references,
competitors, articles, people. Exhaust these before searching.>

Brownfield additions:
- How comparable codebases structured the area being changed.
- The repo's own history and past approaches to this area count as prior art
  (earlier attempts, reverted changes, dead branches).

## Your job

For each candidate worth a dossier:
1. Clone it and pin the exact commit (full SHA); every file reference in the
   dossier is at that SHA.
2. Fill [reference-dossier.md](reference-dossier.md) — one dossier per
   reference, written to `milestones/<m>/a1/dossiers/<owner>-<repo>.md`.
3. Run its test suite if one exists and record the result; "has tests" is a
   claim, a passing run is evidence.

When a candidate is ruled out early (wrong license, abandoned, solves a
different problem), record it in one line in the findings with the reason —
negative results save the next search.

Use the mattpocock `research` skill's primary-source discipline for any
claim about a candidate that the code itself doesn't show (production users,
maintenance status); cite the source.

## Output

Write `milestones/<m>/a1/prior-art-findings.md`:

```
| Problem area | Serves | Candidates with dossiers | Recommended reuse mode | Dossier |
Ruled out: <candidate — one-line reason>
Absence claims: <"found nothing for X" — with the searches run and the date;
                 the operator confirms or contradicts these at H2>
Kill criterion hit: yes | no
```

## Stop rules

- A finding that makes the effort unnecessary (a reference already delivers
  the destination) meets the kill/pivot bar by definition → write the
  findings with `Kill criterion hit: yes` and stop.
- Timebox reached → write the dossiers finished and the candidates left.
- Never message other lanes or the operator.

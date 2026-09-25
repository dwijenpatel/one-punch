# Lane brief — Risk

Copy to `milestones/<m>/a1/risk-<R-n>-brief.md`, one brief per risk, fill
every `<…>`, hand the filled file to a fresh agent. The brief is its whole
instruction set.

---

**Lane:** Risk · **Effort:** <name> · **Milestone:** <m>
**Model:** <named explicitly>
**Timebox:** <wall-clock; default 1 hour per risk>

## The risk

- **R-n:** <id from INTENT.md's risk register>
- **Assumption:** <verbatim from the register>
- **Why risky:** <verbatim>
- **Kill/pivot criterion:** <verbatim — the result that means stop or change course>
- **Blast zone it would land in if wrong:** <level, from the blast-map draft or "unknown">

## Your job

Invoke the `spike` skill on this assumption. Name the competing readings
before writing any code; run the smallest program that discriminates them
against the installed reality. If the question is "does this feel right?"
rather than "what is true?", stop and say so in your findings — it belongs
to the shape lane's prototype, not a spike.

## Inputs

- `INTENT.md` (Constraints, Catastrophes, Risk register)
- <operator-seeded pointers bearing on this risk, if any>

## Output

Write `milestones/<m>/a1/risk-<R-n>-findings.md`:

```
Verdict: confirmed | killed | pivoted | undecided (timebox)
Kill criterion hit: yes | no
Reading that survived: <one line>
Transcript: <path to the spike transcript, or inline>
Versions and date: <pinned versions, date run>
Implication for forks: <which decision this changes, one line each>
If undecided: <what the next probe would be>
```

## Stop rules

- **Kill criterion hit → write the findings file first, with `Kill criterion
  hit: yes` on its own line, then stop.** The planner halts the fan-out on
  reading it.
- Timebox reached → write `undecided` with what you have.
- Never message other lanes or the operator; your findings file is your
  only output channel.

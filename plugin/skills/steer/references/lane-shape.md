# Lane brief — Shape

Copy to `milestones/<m>/a1/shape-brief.md`, keep the variant that applies
(greenfield or brownfield), fill every `<…>`, hand the filled file to a fresh
agent. Its output is the H2 demo, so the planner schedules it right after the
risk spikes.

---

**Lane:** Shape · **Effort:** <name> · **Milestone:** <m>
**Model:** <named explicitly>
**Timebox:** <wall-clock; default 3 hours>

## Inputs

- `INTENT.md` — Goal, Done looks like, Constraints, Catastrophes
- <risk findings already landed, if any>

## Greenfield variant — make it run

**Question:** <the biggest does-this-feel-right question, one line — e.g.
"is the state model for X coherent once a user does Y and Z?">

Pick one, per the question:
- **Walking skeleton** — the thinnest end-to-end path through every layer the
  destination needs, runnable with one command. Hard-coded values are fine;
  missing layers are not.
- **Prototype** — invoke the mattpocock `prototype` skill when the question is
  about feel (a state model, a UI) rather than end-to-end plumbing.

Also record the architecture the skeleton implies (components, data stores,
trust boundaries, external services) — the planner drafts the blast map from
it.

## Brownfield variant — survey the touched area

**Area:** <directories/modules from INTENT.md's brownfield answer>

Produce:
1. **Module map** of the area: modules, their responsibilities, who calls
   whom (fan-in counts for shared modules).
2. **Seams** where the change can attach without rewriting callers.
3. **Test coverage** of the area: which seams have tests, which don't, and the
   command that runs them.
4. **Hot and mega files:** files changed most often recently, and files over
   the effort's megafile threshold (default 800 lines).
5. **Blast-map proposal** — invoke the `blast-radius` skill's propose step
   against the code: every auth, session, transaction, migration, money,
   personal-data and trust-boundary site found, as zones with path globs and
   patterns in its format, each with the file evidence that justified it.
6. **Field-guide seeds:** fragile areas, non-obvious build/test steps, and
   commands that actually reproduce a build or test run here — in the
   `field-guide` skill's entry kinds, so the planner can fold them in as-is.

## Output

Write `milestones/<m>/a1/shape-findings.md`:

```
Variant: skeleton | prototype | survey
Demo: <command that runs it, or path to the module map>
Answer to the question: <one paragraph> (greenfield)
Architecture / module map: <section>
Blast-map draft or proposal: <section, blast-radius format>
Field-guide seeds: <section> (brownfield)
Surprises: <anything that changes a fork or an R-n — name it>
Kill criterion hit: yes | no
```

Skeleton or prototype code lives on a scratch branch named in the findings;
the planner decides at A2 whether hardening it is the first ticket.

## Stop rules

- Anything that meets an INTENT.md kill criterion → write the findings with
  `Kill criterion hit: yes` and stop.
- Timebox reached → write what exists and the next step.
- Never message other lanes or the operator.

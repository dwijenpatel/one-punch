# Lane brief — Safety net (brownfield only)

Copy to `milestones/<m>/a1/safety-net-brief.md`, fill every `<…>`, hand the
filled file to a fresh agent. Launch it once the shape lane's survey has
named the seams to be changed.

---

**Lane:** Safety net · **Effort:** <name> · **Milestone:** <m>
**Model:** <named explicitly>
**Timebox:** <wall-clock; default 2 hours>

## Purpose

Pin the code's **current** behavior at the seams the effort will change, so
any later ticket that alters it by accident fails loudly. These are
characterization tests: they assert what the code does today, not what it
should do. A surprising current behavior is recorded, not fixed.

## Inputs

- `milestones/<m>/a1/shape-findings.md` — the seams and test coverage
- `INTENT.md` — Constraints (what must not break), Catastrophes
- Seams to pin: <list from the survey, highest blast first>

## Your job

For each seam, highest blast level first:
1. Drive it with representative inputs, including the edge and error paths
   the survey flagged, and record the actual outputs, errors and side
   effects.
2. Commit tests that assert exactly those, on the branch named below, using
   the project's existing test framework and the command the survey found.
3. Run them twice on an unchanged tree; a test that is not deterministic is
   removed and reported, never committed flaky.

Branch: <scratch branch name>; the planner decides at A2 whether these land
as the first ticket.

## Output

Write `milestones/<m>/a1/safety-net-findings.md`:

```
Branch: <name> · Test command: <exact>
| Seam | Tests added | Behaviors pinned | Surprises (current behavior that looks wrong) |
Nondeterminism found: <tests removed and why>
Seams left unpinned: <which, and why — timebox, no harness, needs fixtures>
Kill criterion hit: yes | no
```

## Stop rules

- A pinned behavior that contradicts an INTENT.md assumption and meets its
  kill criterion → write the findings with `Kill criterion hit: yes` and
  stop.
- Never change production code to make it testable; record the seam as
  unpinned with the reason.
- Never message other lanes or the operator.

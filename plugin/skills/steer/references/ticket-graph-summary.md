# Ticket-graph summary — the A2 veto window

Written to `milestones/<m>/ticket-graph.md` and shown to the operator at the
end of A2. **One screen.** It is a veto window, not a gate: building starts
unless the operator objects. It also serves as the breakdown review
`to-tickets` asks for.

Fill every `<…>`; the table carries every ticket in the milestone, in
dependency order (blockers first).

```
# Ticket graph — <effort> · <milestone m> · <date>

<N> tickets · B3: <k> (<k/N>%) — <h> wait for your read before they merge
(zones you marked for your review); the other <k−h> are checked by
independent tests-first and a second-model review, and listed at the
milestone. B2: <j> — listed individually at the milestone review.
Build: <parallel N> workers from integrate/<effort>; starts <on your next
reply unless you object | now — you said you are stepping away>.

| #  | Title | Touches | Blocked by | Tag | Size | Blast |
|----|-------|---------|------------|-----|------|-------|
| 01 | <…>   | <globs> | —          | code-complete | low | B1 — <reason> |

Critical path: <01 → 04 → 07> (<n> tickets)
First batch (disjoint Touches): <01, 02, 03, 05>

Installed this A2 (operator-owned surfaces — always installed; object to
any content, e.g. a blast-map level):
- blast map: <new | changed zones: …>
- Code style section in AGENTS.md: <installed | unchanged | adapted: …>
- field guide: <empty | seeded with n entries from the survey>
- harness configuration: <installed from the example | unchanged | changed: …>
- worktree directory git-ignored: <yes>
- build mode: <harness run | light mode — ledger row D-NNN>

Recorded defaults — only when the H2 sitting held the list for this
window; otherwise omit this block. Announced, not voted:
- D-NNN — <decision> — <one-line rationale>
Reopen any by ID (that holds the build until it is resettled).

Not in this milestone: <what the next milestone will take, one line>
```

Checks before showing it:

- Every ticket's `Blast` is at least the highest blast-map zone its
  `Touches` overlaps.
- No B3 ticket also carries B1 surroundings — isolate-the-blast held.
- B3 share ≤ ~20% of the milestone's tickets; above it, recut the seams,
  anchor over-broad content patterns, or reclassify zones before the
  operator sees the graph — and name what you did in one line.
- No ledger ID appears in two `Decides` lines.
- A recorded-defaults block is a list, never a question.
- Every ticket touching rendered UI has a browser walk among its acceptance
  commands; every ticket following a design or prior-art reference carries
  the do-not-copy list.

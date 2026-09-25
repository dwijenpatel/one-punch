# Ticket-graph summary — the A2 veto window

Written to `milestones/<m>/ticket-graph.md` and shown to the operator at the
end of A2. **One screen.** It is a veto window, not a gate: building starts
unless the operator objects. It also serves as the breakdown review
`to-tickets` asks for.

Fill every `<…>`; the table carries every ticket in the milestone, in
dependency order (blockers first).

```
# Ticket graph — <effort> · <milestone m> · <date>

<N> tickets · B3: <k> — each B3 ticket is a diff you will read before it merges.
B2: <j> — listed individually at the milestone review.
Build: <parallel N> workers from integrate/<effort>; starts <on your next
reply unless you object | now — you said you are stepping away>.

| #  | Title | Touches | Blocked by | Tag | Size | Blast |
|----|-------|---------|------------|-----|------|-------|
| 01 | <…>   | <globs> | —          | code-complete | low | B1 — <reason> |

Critical path: <01 → 04 → 07> (<n> tickets)
First batch (disjoint Touches): <01, 02, 03, 05>

Installed this A2 (operator-owned surfaces — object to any):
- blast map: <new | changed zones: …>
- Code style section in AGENTS.md: <installed | unchanged | adapted: …>
- field guide: <empty | seeded with n entries from the survey>

Not in this milestone: <what the next milestone will take, one line>
```

Checks before showing it:

- Every ticket's `Blast` is at least the highest blast-map zone its
  `Touches` overlaps.
- No B3 ticket also carries B1 surroundings — isolate-the-blast held.
- B3 count is small relative to the milestone; a high share means the
  seams need recutting before the operator sees it.
- No ledger ID appears in two `Decides` lines.

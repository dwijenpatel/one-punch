# Decision memo — <effort name> — <H2 | H3 milestone: name>

Sitting date: <date> · Compiled from: <spike transcripts, prototype/skeleton,
code survey, prior-art dossiers, evidence-lake holdings — link each>

## 1. Demo

<What the operator is shown before anything is asked: the skeleton/prototype
running (command to launch it, or a recording), or — brownfield — the
survey's module map. H3: link the milestone build instead.>

*(H3 mini-memo: omit this section.)*

## 2. Risk register update

| R-n | Assumption | Outcome | Evidence |
|---|---|---|---|
| R-1 | <from INTENT.md> | confirmed / killed / pivoted | <spike or session transcript link> |

*(H3 mini-memo: omit this section unless a milestone spike touched a
still-open risk.)*

## 3. Forks (the only questions)

Fan-out ordered, highest first. One entry per fork; walk these one at a time
in the live sitting, never all at once.

### Fork F-<n>: <question>

- **Options:** <A> / <B> / <…>
- **Recommendation:** <option, and why in one line>
- **Evidence:** <link> — tier <A|B|C> (evidence-kit grading)
- **Forecloses:** <what choosing this option rules out later>
- **Operator answer:** <recorded after the sitting>

### Reuse fork: <problem area>

- **Prior-art dossier:** <link> — what it solves, evidence it works
  (production users, test suite, maintenance — not stars), license
- **Reuse mode options:** `dependency` / `fork` / `port` / `pattern` / build
  fresh
- **Recommendation:** <mode, and why>
- **Forecloses:** <license/coupling/maintenance consequences>
- **Operator answer:** <recorded after the sitting>

*(One-way door by definition — always a fork, never a default, whenever a
dossier exists for the area.)*

### Adversarial-evidence check (only when triggered)

<Only present when a one-way-door fork above rests on an external claim —
vendor behavior, a library's documented guarantee, another codebase's
claimed property. Name the claim, link the adversarial-grade evidence-kit
pass that was run before this fork was presented, and its verdict. If this
section is empty for every fork above, no one-way-door fork here rested on
an unverified external claim.>

### Absence claims (only when raised)

<Any "nobody has built this" / "no library does X" claim implied by a fork
above. State it plainly and let the operator confirm or contradict it — do
not treat a corpus miss as proof. Record the operator's answer here, not as
a default.>

- **Claim:** <…>
- **Operator confirms / contradicts:** <recorded after the sitting>

## 4. Blast map — for ratification

<Proposed blast map: path globs and content patterns → B0/B1/B2/B3, per the
`blast-radius` skill's default pattern pack plus anything the survey or
skeleton found. Always a fork — the operator ratifies or edits it.>

| Zone | Paths / patterns | Level | Reason |
|---|---|---|---|
| <e.g. auth/session> | <globs> | B3 | <one line> |

**Design decisions inside a B3 zone** (listed as forks here, never bundled
into the recorded-defaults section below):

### Fork B3-<n>: <B3 design decision, e.g. session model>

- **Options:** <A> / <B>
- **Recommendation:** <…>
- **Evidence:** <link> — tier <A|B|C>
- **Forecloses:** <…>
- **Operator answer:** <recorded after the sitting>

**Operator ratification of the map itself:** <accepted as-is / edits, recorded
as `D-NNN: path X is <level> despite pattern Y because …` for any operator
override>

## 5. Recorded defaults

Batch-ratified as a whole; the operator reopens any single row by ID rather
than approving them one at a time. Rows touching a B2 zone are flagged.

| ID | Decision | Rationale | Flag |
|---|---|---|---|
| D-<NNN> | <craft decision> | <one line> | — |
| D-<NNN> | <craft decision touching a B2 zone> | <one line> | **B2** |

**Operator response to the batch:** <ratified as-is / reopened: D-<NNN> —
new answer and why>

## 6. Not yet specified

Genuinely undecidable now — don't force an answer to close out the sitting.

| Item | Why it can't be decided yet | Milestone that reveals it |
|---|---|---|
| <…> | <…> | <…> |

---

## Filing checklist (after the sitting)

- [ ] Every fork's operator answer → a row in `docs/decisions.md` (ID,
      decision, rationale, owner, status, ADR link if it meets the
      `domain-modeling` ADR criteria).
- [ ] Every recorded default → a row in `docs/decisions.md`, B2 flag carried
      over.
- [ ] Blast map ratified (with any operator override) → `docs/blast-map.md`.
- [ ] Not-yet-specified items → carried into the ticket graph or the next
      milestone's INTENT/risk register, not dropped.

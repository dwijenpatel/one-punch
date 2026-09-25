# Reference dossier — <owner>/<repo>

One per reference, written by the prior-art lane to
`milestones/<m>/a1/dossiers/<owner>-<repo>.md`. It is the evidence for a
reuse fork at H2, and `Reference:` fields in tickets point into it.

```
Source:        <clone URL>
Pinned at:     <full commit SHA> (cloned <date>)
Seeded by:     operator | lane search
Problem areas: <which of our problem areas; the fork or R-n each serves>
```

## What it solves, and how

- **Problem it solves:** <one paragraph, in our terms — how close is it to
  our problem, and where does it stop?>
- **Architecture:** <components and data flow, a few lines>
- **Key files** (at the pinned SHA): <path — what it shows>, one per line.
  These are what a ticket's `Reference:` field points at.

## Evidence it works

Stars, forks and download counts are not evidence: popularity is not
correctness. Each line below cites its source.

- **Production users:** <named users or deployments, each with a link; or
  "none found" with the search and date>
- **Test suite:** <exists? what it covers; the command; ran it at the pinned
  SHA? result>
- **Maintenance:** <last release and date; commit cadence over the last year;
  how issues and security reports get answered; number of active
  maintainers>
- **Known defects:** <open issues or advisories that bear on our use>
- **Evidence tier:** <per evidence-kit grading, where the claim was graded;
  otherwise "ungraded">

## License

- **License:** <SPDX identifier, from the license file at the pinned SHA>
- **Compatible with ours:** <yes / no / only as dependency — why>
- **Obligations:** <attribution, notice, source-disclosure duties that each
  reuse mode would trigger>

## Fit

- **Matches INTENT.md:** <constraints and non-goals it respects>
- **Conflicts:** <stack, deadline, non-goal, must-not-foreclose items it
  collides with>
- **Blast zones it would touch:** <levels, from the blast-map draft — B2/B3
  reuse prefers a vetted reference; say whether this one qualifies>
- **Borrowable:** <design tokens and structure we may take from it>
- **Do not copy:** <its brand terms, badges, program names and marketing
  copy, one per line — carried into the findings' do-not-copy list; "none
  seen" if none>

## Recommended reuse mode

One of:

| Mode | Meaning | What it costs later |
|---|---|---|
| `dependency` | take it as a versioned dependency, unmodified | upgrades, their release cadence, supply-chain exposure |
| `fork` | own a diverging copy of the whole project | we carry its maintenance; attribution kept |
| `port` | copy specific code into our tree, adapted, with attribution | we own the copied code; notices entry required |
| `pattern` | read only; follow its design, copy no code | nothing beyond the design choice |
| none | not recommended | — |

- **Recommendation:** <mode> — <one-line why>
- **Forecloses:** <what adopting it this way rules out later>
- **Risks:** <what would make this recommendation wrong>

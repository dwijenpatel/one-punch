Status: DONE_WITH_CONCERNS
Commits: 3fc2fc7 (skills), fc5626c (handoff), plus the commit adding lane-shape demo links and this handoff update
Done: Trial 1 amendments 1, 2, 3, 4, 5, 6, 9, 10 (steer part), 11 in steer, decision-memo, intent.

Amendment → file:section
- #1 visual closure
  - steer/references/ticket-header.md "Tickets that touch rendered UI" (browser walk, Playwright or equivalent, run as an acceptance command; variants list set at A2 in the first UI ticket; desktop about 1280px + about 375px; defining behaviour, not presence; zero/one/many boundary cases count as variants)
  - steer/SKILL.md A2 step 3 (UI tickets carry the walk); H3 step 1 "Visual closure (UI efforts)" (desktop screenshots to `milestones/<m>/closure/`, planner inspects every one before the report, a visible defect gets a fixer ticket); Effort layout (`closure/<variant>.png`)
  - steer/references/milestone-report.md "Visual closure" table + "Screenshots inspected by the planner" line
  - steer/references/ticket-graph-summary.md checks (UI tickets have a walk)
- #2 verified links
  - steer/SKILL.md "Entry and ceremony" bullet "Links handed to the operator are verified links" (one rule for H2 demo, H3, polish, ad-hoc); H2 step 1 and H3 step 5 point to it
  - steer/references/milestone-report.md Demo "Links to try" table (link, label, check, result)
  - steer/references/lane-shape.md Output "Demo links:" (the skeleton's URLs ship with the checks that exhibit their labels, which is where the H2 links come from)
  - steer/references/ticket-header.md Variants bullet (the links list is generated from the walk's variant list and its passing results)
- #3 polish stage
  - steer/SKILL.md stage table (Polish and Retro rows; retro removed from H3's Invokes); new "## Polish — operator-reported fixes after H3" (≤1 file and about 30 lines, in no B2/B3 zone → planner-direct; else a worker ticket through integrate; failing regression case before the fix via `tdd`; full suite + full walk over every variant at both widths; ledger row + polish-log row; where fixes land; new scope is not polish); "## Retro and the next milestone"; `resume` table (polish due / Polish / retro due / milestone closed rows); intro line 12 (the polish exception to "never implements"); A2 step 7 (`main` changes on the H3 merge decision, again when polish closes)
  - steer/references/polish-log.md (new; `Status: open|closed` is the marker `resume` reads)
  - steer/references/milestone-report.md "Polish log:" line; "Retro memo:" is filled after polish
- #4 defaults + veto in one turn
  - decision-memo/SKILL.md H2 step 5 "Hold the batch for the build veto window"
  - decision-memo/references/decision-memo-template.md §5 "Presented:" field
  - steer/SKILL.md A2 step 8 "All-≤B1 milestone: one turn"
  - steer/references/ticket-graph-summary.md "Recorded defaults" block (conditional) + check
- #5 fork batching
  - decision-memo/SKILL.md "Conversational surface" → "Low-blast forks may share a turn" (≤3 per turn; all B0/B1; no one-way door, so a reuse fork never qualifies; consecutive in fan-out order; no intra-batch dependency; B2/B3 and one-way doors one per turn; the glad-I-was-asked test applies to each fork)
- #6 do-not-copy
  - steer/references/lane-prior-art.md "Borrowed style: tokens and structure only" + Output block (`Design references:` table, `Do not copy:` list)
  - steer/references/reference-dossier.md Fit ("Borrowable", "Do not copy")
  - steer/SKILL.md A2 step 3 (the do-not-copy list goes verbatim into Constraints of any ticket that follows a reference)
  - steer/references/ticket-graph-summary.md check
- #9 scope restatement
  - intent/SKILL.md "The opening" → "Restate the scope before asking" (read README/brief/kickoff first, restate in one or two lines naming every in-scope surface, ask only what's left open; with no brief, say so); example opening updated (generic CLI + HTTP API example)
- #10 light mode (steer part)
  - steer/SKILL.md Build "Light mode — the sanctioned degrade" (in-session background workers in their own worktrees; every ticket lands through `worker-harness`'s `integrate` run by hand, pointing to that skill's "integrate by hand" section and not restating it; the script decides what lands; a ledger row records entering light mode); Preflight step 5 (a missing launcher degrades to light mode, which still needs integrate to run); description
  - steer/references/ticket-graph-summary.md "build mode" line
- #11 A2 installs automatic
  - steer/SKILL.md A2 step 6 "Install the standing artifacts — one automatic template step" (blast map from the default pack, code-style Layer 1, field guide, harness configuration started from worker-harness's example, `.worktrees/` ignored; never proposed, never skipped; the operator ratifies blast-map levels at H2 or the veto window; skipping them removes integrate's checks because it cannot run without its configuration and fails closed without a blast map); "Entry and ceremony" (installs are not ceremony); stage table A2 row
  - steer/references/ticket-graph-summary.md "Installed this A2" (always installed; lists harness config and the ignored worktree directory)

Deviations:
- The brief's evidence docs are not on this branch; they are in main's commit 415fd74. I read them there with `git show` and did not touch the main checkout.
- Added one new file, steer/references/polish-log.md, inside Touches. It holds the polish log format so SKILL.md stays short and `resume` has an on-disk marker.
- Also edited decision-memo/references/decision-memo-template.md, one field, inside Touches.

Decisions needed (for each: the local option I took, and whether it can be undone):
1. Where polish fixes land, given that "`main` changes only at H3". I took: fixes land on the integration branch, and `main` is fast-forwarded once when polish closes, under the H3 merge decision. Can be undone: yes.
2. Amendment #4's condition (every ticket ≤B1) can only be checked at A2, but the defaults batch belongs to H2. I took: at H2, hold the batch when no default is B2-flagged and no fork was B2 or higher. If A2 then produces a ticket at B2 or higher, the held batch goes out as its own turn before the graph. A reply that reopens a default holds the whole build, which is the safe choice over holding only the dependent tickets. Can be undone: yes.
3. Planner-direct polish fixes. Besides ≤1 file and about 30 lines, I added "in no B2 or B3 zone". Planner-direct fixes are committed straight onto the integration branch, following worker-harness's planner-edit precedent, not through integrate. Integrate needs a ticket and a handoff. Can be undone: yes.
4. For the red-before-fix rule, the failing run is recorded in the polish log. The integration branch receives the case and the fix together, green, so the always-green invariant holds. Can be undone: yes.
5. A design reference (a site or product with no code) gets no clone or dossier. It goes in a design-references table in the prior-art findings. Can be undone: yes.
6. Operator-requested new behaviour during polish counts as new scope (a ticket regardless of size, or the next milestone), not a polish fix. Can be undone: yes.

Findings / concerns:
- steer refers to "`worker-harness`'s example configuration" by role, not by path. That example `harness.toml` does not exist on this branch yet (amendment #10's worker-harness part, another ticket). If that ticket names it differently, the wording still holds; if it never lands, A2 step 6 points at nothing.
- steer says "`retro` reads the log" and lists the polish log among retro's inputs. retro is out of my Touches and its inputs list does not name a polish log yet. It needs a polish-log input line, and amendment #8's retro ticket is the natural home.
- pipeline.md's stage table (amendments #1, #3, #10) is out of my Touches and not updated. steer now has Polish and Retro stages that pipeline.md does not.
- steer/SKILL.md is now 405 lines, up from 312. The limit is 500, so headroom is shrinking.
- The ticket-graph summary is billed as "one screen". With the installs list and the conditional defaults block it may run past one screen on larger milestones.

Field-guide proposals: none.

Acceptance:
- Frontmatter parsed with PyYAML. steer: name==dir, description 982/1024, compatibility 430/500, 405 lines. decision-memo: name==dir, description 815, compatibility 301, 174 lines. intent: name==dir, description 560, compatibility 174, 143 lines. All pass.
- Portability grep `rg -i '\b[0-9a-f]{7,40}\b|§|docs/design|one-punch|/Users/|\bprime\b|\btrial\b|v4-steer|plan\.md'` over steer, decision-memo and intent returns no matches (exit 1). Pass.
- Every `references/…` link in the three SKILL.md files resolves to an existing file. Pass.
- `bash plugin/skills/worker-harness/references/harness/verify.sh` ends with "verify: OK", exit 0. Pass.

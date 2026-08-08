---
name: start
description: The one-punch front door — open a new effort in a fresh or existing repo. Checks prerequisites (printing exact install commands for anything missing), scaffolds the repo with the private overlay, runs intent elicitation, runs the evidence pass with the mandatory fork-or-build gate, then hands off to the decision map. Use when beginning any new project or effort; may be proposed by the agent when the operator describes new project-sized work.
compatibility: Works in any agent harness with shell access. Requires git. Composes the mattpocock-skills plugin and (for the evidence pass) the evidence-kit method; detects absence and prints install guidance rather than failing.
license: MIT
---

# start — the front door

New effort → `start`. Returning to an existing effort → the worker-harness
skill's `resume`. Those two commands are the complete entry surface; nobody
should need to memorize the pipeline to begin.

This is a CEREMONY: the agent may propose it ("this looks like a new
project-sized effort — run one-punch start?") but never enters it without the
operator's yes.

## 1. Prerequisite check (detect, don't assume)

Check, in order, and print exact remediation for anything missing rather than
failing or silently degrading:

- **git repo**: if absent, offer `git init` (default branch `main`).
- **mattpocock-skills**: probe for its skills (is `wayfinder`/`grilling`
  available in this harness?). If missing, print the harness-appropriate
  install (Claude Code: `claude plugin install mattpocock-skills@mattpocock`;
  file-copy harnesses: `npx skills@latest add mattpocock/skills`).
- **Repo skill config**: if `docs/agents/issue-tracker.md` is absent, run
  `setup-matt-pocock-skills` (local-markdown tracker is the one-punch DEFAULT —
  the repo stays self-contained; external trackers are the exception).
- **evidence-kit**: needed at step 4; detect and note now, install guidance
  only when reached.
- **Freshness, not just presence** (added after two stale-cache incidents on
  day one of first use): where the harness exposes installed plugin versions
  and the local source/marketplace is reachable, compare them for one-punch
  and its composed dependencies. If anything is stale, say so NOW and print
  the exact update commands (e.g. for Claude Code:
  `claude plugin marketplace update <name> && claude plugin update <plugin>@<name>`),
  and remind the operator that updates apply at session start — better to
  restart at minute zero than mid-ceremony. A version check that cannot be
  performed in this harness is reported as unchecked, never assumed current.

## 2. Scaffold

- First commit carries `.gitignore` with `/.private/` (ignore-before-create).
- Set up the `.private/` overlay per the intent skill's
  `references/private-overlay.md` (its own repo + private remote when the
  operator has one ready; otherwise note the TODO on the map).
- No public remote on the main repo — publishing is a deliberate later act.

## 3. Intent

Invoke the `intent` skill. Its INTENT.md (at the operator's chosen tier) and
the Tier-2 echo are the first artifacts of the effort. Learning goals hand off
to `learning-gates` for typing, binding targets, and budget.

## 4. Evidence pass

Research routes through the evidence-kit method (graded holdings, warrant ×
decay, corrections ledger) into `.private/evidence/`. Non-negotiable
deliverable before any map is charted: **the fork-or-build memo** — does prior
art make this effort unnecessary, smaller, or differently shaped? The operator
reads and rules on it. Scale the rest of the pass to the effort; a small
effort may stop at fork-or-build plus one benchmark sweep.

If evidence-kit is unavailable: print its install guidance; if the operator
declines, fall back to plain research files but keep the fork-or-build memo
mandatory, and mark every load-bearing claim with an explicit TODO-warrant.

## 5. Hand off

Enter the decision map (`wayfinder`) with INTENT.md and the corpus loaded.
Resolution sessions follow the decision-memo discipline (pipeline v3 §2):
derive craft decisions on the record, ask only genuine forks, batch-ratify.

Then stop — charting is the next session's work. Report what was created:
intent location and tier, corpus location, fork-or-build ruling, map location.

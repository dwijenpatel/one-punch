# Evidence memo — resonance · 2026-11-10

Reporter: operator · Compiled by: a separate Claude Code session (Opus 5.5), from an
export of the effort's own planner session
Cadence: outcome report arrival. The operator reported approving asks "without
clarity on what the ask was" mid-milestone (m1, build in progress).

**Scope and altitude.** resonance is the operator's private eval-automation
project. This repository is public, so this memo stays at engineering altitude:
it names the effort but carries none of its spec content. The retro skill puts
the full memo in the effort's repo, but that session was mid-build and
`integrate` checks for a dirty tree, so nothing was written there. The per-turn
detail lives in the exported session transcript (operator-held).

**Adjudication.** The operator ruled in the same conversation (2026-11-10): "file
the retro memo and implement the fixes". So this memo is ratified, not just a
proposal. The amendments land as one-punch 0.5.0 on the commits that cite this
file.

## Headline

**Unattended tickets merged per operator intervention:** `not recorded`. The
build is in progress, so the milestone isn't closed. Ledger and integrate-log
values exist but weren't compiled. This memo is about the asks, not the build
half.

Designed oversight is reported beside the ratio, as the template requires:

- three sittings (H1, H2 and an A2 continuation);
- 47 operator inputs in all (counting rule below);
- three approval turns covering five B3 review packets.

The inputs split as follows:

- 44 answered the agent's asks: 35 turns plus 9 structured questions.
- 3 were operator-initiated turns: `steer resume` and two requests (S).

**Which count, and where:** the quick-agree asks defined below are reported
here, beside the ratio. They are not added to the denominator, which counts
only unplanned interventions. Moving designed oversight into the ratio would
reverse the bootstrap retro's fix, and that retro's reasoning still holds.

## Operator interaction log

**Source:** the exported session transcript (main thread; subagents excluded).

**Counting rule:**
- One row per operator message that answers or initiates. Context-continuation
  summaries are not operator messages, so the 41 user-role messages give 38
  turns.
- Each question inside a structured choice prompt counts as one answer. There
  were 8 prompts holding 9 questions.

The rows are grouped by phase; the per-turn rows are in the export.

| Turns | Time (UTC) | Stage | Gist | Class | What prompted it | Avoidable? |
|---|---|---|---|---|---|---|
| 1 | 11-09 07:46 | resume | `steer resume` | S | operator | no |
| 2 | 07:47 | preflight | "start H1" | D | stage gate | no |
| 2 structured | 07:47 | preflight | tracker triage labels; AGENTS.md vs CLAUDE.md | D | upstream setup skill | **yes**: a convention or recorded preference already answered both |
| 6 | 07:50–08:00 | H1 | goal, audience, constraints, catastrophes, prior art, risk register | D | intent sitting | no: substantive free-text answers |
| 1 | 08:03 | A1 | "Launch A1" | D | stage gate (spends quota) | no |
| 13 | 20:36–21:29 | H2 | the main forks, one per turn | D | altitude rule: "B3 is always a fork" | **8 of 13 yes** (see Findings) |
| 3 | 21:30–21:35 | H2 | reuse forks (port a launcher, a stats dependency, pattern-only reuse) | D | reuse fork | **yes**: every answer matched the recommendation; none touched anything the operator owns |
| 1 | 21:35 | H2 | absence claim | D | rule: operator confirms absence claims | partly: the operator had no new information |
| 1 | 21:36 | H2 | blast map, 12 B3 zones, one button | D | rule: every B3 zone is an explicit yes | the read was not possible in 22 s |
| 1 | 21:37 | H2 | 22-item defaults batch, one button | D | rule: present the batch for ratification | **yes**: approved in 5 s |
| 3 | 21:37–11-10 02:50 | H2 | learning-gates opt-in, goal type, target bar | D | learning-gates | no |
| 2 | 02:56–03:45 | A2 | "Continue A2"; "Commit and cut" | D | stage gates | **yes**: neither is a decision the operator owns |
| 1 structured | 03:01 | A2 | how the target project's tickets get built | D | planner | yes |
| 6 structured | 03:46–03:48 | A2 | 3 eval questions, each asked twice: operator position first, then hold or switch | D | learning-gates Socratic inversion | **yes**: 6–14 s each; 2 of 3 flipped to the recommendation |
| 1 structured | 03:49 | A2 | merge an existing branch in the operator's other repo | D | planner | no: it's the operator's repo history |
| 3 | 05:35–07:12 | build | approve B3 packets (02; 03 + 08 + 22; 09) | D | rule: the operator reads every B3 diff | see Findings |
| 2 | 06:29–06:30 | build | "why Python 3.9?"; "add mypy strict" | S | operator read a status message | no: operator-initiated and substantive |

## Timing

**Source:** the transcript's timestamps.

"Reply latency" is the gap from the agent's last message to the operator's
next one. It is not operator effort. Gaps where the operator was evidently
away (12 h before the first H2 fork, 5 h before "Accept target", 1.5 h before
the first packet approval) are excluded from medians.

| Stage | Wall clock (UTC) | Duration | Agent active | Operator | Notes |
|---|---|---|---|---|---|
| Preflight + H1 | 11-09 07:46–08:03 | 17 min | not recorded | 9 asks | substantive answers |
| A1 | 08:03–08:33 | 30 min | ≈30 min | 0 asks | then away ~12 h |
| H2 sitting | 20:36–21:40 | 64 min | short turns | 22 asks | median reply ≈45 s on ≈420-word asks |
| A2 | 21:40–11-10 03:45 | with a ~5 h away gap | not recorded | 10 asks | 6 of the 10 were Socratic doubles |
| Build (in progress) | 03:45–07:31 | ongoing | — | 3 approvals + 2 requests | 19 of 21 tickets B3 |

## Metrics

| Metric | Value | Bar | Source |
|---|---|---|---|
| Asks answered, kickoff → first build dispatch | 41 | ≤3 sittings: met as sittings, but the bar never limited asks per sitting | transcript, counting rule above |
| Recommendation agreement, H2 forks and reuse forks | 15 / 16 | none existed; proposed below | transcript (option chosen vs option marked recommended) |
| Recommendation agreement, structured prompts with a marked recommendation | 4 / 4 | — | transcript |
| Socratic doubles: first position matched the recommendation / final ruling = recommendation | 1 / 3 · 3 / 3 | — | transcript |
| **Quick-agree asks**: reply ≤60 s to an ask over 200 words, answer = the recommended option | **11**: start H1 (8 s, 332 w); launch A1 (11 s, 321 w); 3 forks (19–36 s, 343–499 w); 2 reuse forks (19–24 s); blast map (22 s, 438 w); defaults batch (5 s, 528 w); continue A2 (60 s, 589 w); commit and cut (17 s, 784 w) | proposed: >25% of a sitting's asks means the sitting asked below altitude | transcript |
| Batch sizes ratified in one reply | 22 defaults; 12 B3 zones | — | transcript |
| Share of tickets at B3 | 19 / 21 (90%) | >20% means isolate-the-blast is failing | ticket headers |
| B3 tickets that were B3 only because a bare common word matched a content pattern | 2 (planner's own report) | — | transcript |
| B3 packets approved per approval turn, and time | 3 packets in one turn, 140 s after a ~700-word message | the ladder assumes a read | transcript |
| Fork framing errors corrected mid-sitting | 1 rewritten (wrong spec citation; a false choice); 3 forks reframed or added by earlier rulings | 0 | transcript |
| Other template rows (conflicts, verify-fail, escalations, tokens…) | not recorded | — | milestone open |

## What was measured

The operator answered 44 asks over two days. In the H2 sitting they answered
22 asks in 64 minutes, picked the recommended option on 15 of 16 forks, and
replied in a median of about 45 seconds to messages averaging about 420 words.
Eleven asks were answered with the recommendation in a minute or less, on
messages long enough that they couldn't have been read. Two batch items, a
22-line defaults list and a 12-zone blast map, took 5 and 22 seconds.

Under learning-gates' Socratic inversion, position-first answers took 6–14
seconds. Two of three flipped to the recommendation 7 seconds after seeing it.
In the build, 19 of 21 tickets were B3, and the operator approved three B3
review packets in one click.

## What it confirms or contradicts in the current process

**The decision-memo skill contradicts itself, and the rule that lost was the
governing one.**
- [decision-memo](../../plugin/skills/decision-memo/SKILL.md) says the
  glad-I-was-asked test wins whenever a category disagrees with it.
- It also says "B3 is always a fork… no exceptions".
- On an effort whose blast map put 12 zones at B3, the second rule turned
  technical-correctness questions (statistics, isolation mechanics, cache
  keys) into operator forks.
- The operator had no information the planner lacked, and ratified the
  recommendation without reading it.

That is the v3 failure (many small touchpoints the operator rubber-stamps)
returning through the blast axis.

**The B3 diff read did not happen as designed.**
- pipeline.md §4 item 4 justifies the one per-ticket touchpoint: LLM judges
  caught 5% of real bugs in D26 exp-01, and at B3 failures are silent.
- That argument assumes the operator actually reads. At 19 B3 tickets per
  milestone, they didn't: three packets went through in one click.
- A designed check that doesn't run is worse than none, because the ledger
  records it as done.
- The read has to be scarce enough to be real. It belongs where the operator
  holds knowledge or consequences that the agents don't: their credentials,
  money, personal data, their own repos, their own rules, production.
  Elsewhere the B3 machinery already does the checking: independent
  tests-first, a decorrelated lens, mandatory spikes, execution-based verify.

**Ask format raised the cost of each ask.**
- Internal IDs (F-14, D-026, §12.7, "gap 7") filled the messages.
- Answer buttons named options by letter ("A: margin + label").
- No ask said what happens if the operator doesn't care.
- The operator was on Remote Control, often on a phone.

**Batches converted reading into clicking.**
- Ratifying 22 defaults in 5 seconds is no oversight. The defaults were
  already recorded and reopenable, so the vote added nothing but an ask.

**Socratic inversion through choice buttons measured guessing, not
understanding.**
- The operator's first picks were the "as ruled / keep" options. That is a
  status-quo default, not a position.

**The memo was presented before it was checked.**
- One fork carried a wrong spec citation and a false choice.
- Three forks changed because of earlier rulings in the same sitting.

**Confirmed working:**
- H1's five questions, pre-filled from the spec, drew substantive answers.
- The operator engaged sharply when content was concrete and theirs (the
  Python 3.9 question, the mypy request).
- The one fork the operator overrode (container network egress) was a
  genuine preference: it's the kind of fork the test is for.

## Proposed amendments

All were adjudicated by the operator on 2026-11-10 and land in 0.5.0.

1. **B3 means checked, not asked.** — evidence: the 15/16 agreement and
   quick-agree rows. Class: pipeline amendment (decision-memo, blast-radius,
   pipeline §3–§4).
   - A B3 design decision is decided by the planner and independently checked
     (a spike, a second-model review or a tests-first author).
   - It's listed in the sitting's **decided-for-you** block, one line each,
     with a veto by reply.
   - It becomes a fork only when it passes the owner test: the operator's
     money, quota or time; their accounts or repos; a rule they wrote; a
     product boundary; or genuine taste.
2. **Operator diff reads only in operator-owned zones.** — evidence: the
   approval rows and the B3 share. Class: pipeline amendment plus harness.
   - A new blast-map zone key, `operator_review`. It's absent on a B3 zone, so
     the zone holds (fail-closed, and existing maps behave unchanged).
   - `false` on a non-protected B3 zone lets a green ticket merge after the
     full B3 machinery. Protected zones can't be set false.
   - At ratification each project B3 zone states the flag with a reason.
3. **Ask format.**
   - One plain sentence first.
   - "If you don't mind, I'll do X."
   - About 120 words, with no internal IDs.
   - Buttons that describe outcomes, plus a "your call" option.

   Evidence: the latency and agreement rows. Class: pipeline amendment
   (decision-memo, steer).
4. **No batch votes.** Defaults are announced and reopenable by ID; nothing is
   voted. Evidence: the batch row. Class: pipeline amendment.
5. **B3-share and pattern hygiene at ticket cut.**
   - Over ~20% B3 is a warning, with a plan to narrow before dispatch.
   - Content patterns that match bare common words get anchored.

   Evidence: the B3-share and bare-word rows. Class: pipeline amendment
   (blast-radius, steer).
6. **Learning-gates: position-first becomes written prediction.** It goes in
   the learning log, never blocks a fork, and isn't asked by button.
   Evidence: the Socratic row. Class: gate recalibration.
7. **Pre-sitting memo check.** Citations are verified, dependencies between
   forks ordered, and dependent forks asked after their inputs. Evidence: the
   framing-error row. Class: pipeline amendment.
8. **Retro measures ask efficiency.** Asks, recommendation agreement and the
   quick-agree count become standing rows. Evidence: this memo had to derive
   them by hand. Class: pipeline amendment (retro).
9. **Setup questions answered by convention.** Upstream setup prompts whose
   answers a recorded preference or default already settles are answered and
   recorded, not asked. Evidence: the two preflight structured questions.
   Class: pipeline amendment (steer).

## Considered and left unchanged

- **H1's intent sitting.** It worked: five asks, substantive answers.
- **Stage gates that spend quota** ("launch A1"). Kept as one-line gates; they
  pass the owner test (quota).
- **The headline ratio's denominator.** Quick-agree asks stay beside it, not
  in it.
- **B3's automated machinery** (tests-first author, decorrelated lens,
  mandatory spikes, top-tier implementer). Unchanged. Amendment 2 leans on it
  harder, so any escaped B3 defect in a zone flagged `operator_review = false`
  triggers a retro of that zone's flag.
- **Lowering levels.** Still operator-only. The new flag doesn't lower a
  level; it changes who reads.

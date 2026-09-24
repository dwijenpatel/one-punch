# Evidence memo — 2026-09-24 — code-style guidance: critiques of the canon, and evidence for agent-facing conventions

**Trigger:** operator is adding a short coding-standards section to AGENTS.md in
agent-written repos (principles: minimize side effects / prefer pure functions;
composition over inheritance; readability; layered function granularity; Unix
"do one thing well"). Question: which of these fail when over-applied, and what
does 2024–2026 evidence say about phrasing and enforcing conventions for agents?

**Grades:** PR = peer-reviewed; WS = workshop paper; PP = preprint; VB = vendor
doc/blog; OP = practitioner opinion. All Part A sources are OP (one PR anchor).

---

## Part A — contested rules and refined wording

| Rule | Critique | Source | Failure condition | Refined wording |
|---|---|---|---|---|
| Small functions; "do one thing" (Martin: 2–4 lines) | Ousterhout: over-decomposition yields *entangled* methods, where understanding one requires reading the other. Martin conceded 1st-ed. *Clean Code* gave no guidance on spotting over-decomposition. Empirical anchor (**PR**): across ~785k Java methods, maintenance effort rises with length. Authors suggest ≤24 SLOC; data supports ~24, not 2–4. | https://github.com/johnousterhout/aposd-vs-clean-code (2024–25); https://arxiv.org/abs/2205.01842 (Chowdhury, Uddin, Holmes, MSR 2022) | Extracted pieces have no standalone contract, so the reader flips between call sites to rebuild the algorithm. | Target ~25 lines. Linter *warning* at ~40–60, never a hard fail. Extract a piece only if its name + signature can be understood without reading its caller. |
| Extract helpers for readability | Carmack: consider inlining single-call functions; bugs come from execution state not being what you think. His 2014 preface says the real enemy is unexpected dependency and mutation of state. | http://number-none.com/blow/john_carmack_on_inlined_code.html (2007 email, 2014 preface) | Helpers hide ordering and state preconditions; can be called out of sequence. | Inline a single-call helper unless it is pure or has a contract worth naming. Keep sequential steps visible in one body. |
| Layered granularity (top → mid → low) | Ousterhout: pass-through methods and shallow modules add interface cost without hiding anything. | aposd-vs-clean-code (above); *A Philosophy of Software Design* | Layers exist for their own sake. A mid function's body is one call down with the same arguments. | Each layer must change the level of abstraction or hide a decision. A function whose body only forwards to one call is a smell. |
| DRY | Metz: "duplication is far cheaper than the wrong abstraction." Wrong abstractions accrete parameters and conditionals. Abramov's reverted dedup traded changeability for less duplication. | https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction (2016); https://overreacted.io/goodbye-clean-code/ (2020) | Callers diverge or special cases arrive later. The shared function grows per-caller flags. | Deduplicate *knowledge* (a rule that must change in lockstep), not similar-looking text. If a shared helper takes a per-caller flag, inline it back. Out-of-scope refactors get their own ticket. |
| Rule of three (Roberts via Fowler, *Refactoring*) | This is itself the refinement of DRY: tolerate two copies and refactor at the third. | https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming) (secondary; primary is *Refactoring*) | Applied as a count instead of a judgment. Three copies that change for different reasons should stay separate. | Extract at the third copy only if all copies change for the same reason. |
| Polymorphism over switch; small functions (perf) | Muratori measured the same shape code: switch 1.5× faster than virtual dispatch, table-driven 10×, ~15× after adding one property, 20–25× with AVX. | https://www.computerenhance.com/p/clean-code-horrible-performance (2023) | Hot loops over many small objects, and data-oriented code. | Style rules apply outside profiled hot paths. In a hot path, prefer data layout + switch/table, and document why. |
| Minimize side effects / pure functions | Carmack is a supporter with caveats: purity is a continuum, and not everything can be pure. Purity implies more copying, which is sometimes the wrong strategy. | https://www.gamedeveloper.com/programming/in-depth-functional-programming-in-c- (2012) | Threading state through every signature. Copying large structures. Forcing purity onto inherently effectful code. | Keep I/O and mutation at the edges. Make core logic pure when convenient, and when it isn't, make the mutation explicit and local. No hidden globals. |
| Complexity / premature factoring | Grug: don't factor early, because good cut points emerge from code. Repeating code often beats complex DRY. | https://grugbrain.dev/ | Abstractions and modules are cut before usage reveals the seams. | Don't introduce a module, interface, or config knob until a second real use exists. |
| YAGNI | Fowler: YAGNI covers presumptive *features*. It does **not** cover effort that makes code easier to modify (refactoring, tests). | https://martinfowler.com/bliki/Yagni.html (2015) | Used as an excuse to skip tests or refactoring, or conversely to over-build "just in case". | No speculative parameters, hooks, or config. Tests and refactoring toward clarity are always in scope. |
| Unix "do one thing well" at module/service scale | Ousterhout: prefer *deep* modules (small interface, lots of behavior). Grug: microservices add a network call to the hardest problem. | aposd-vs-clean-code; grugbrain.dev | Many tiny modules or services whose interfaces are nearly as complex as their bodies. | Apply "one thing" to *responsibility*, not size. A module should hide substantial behavior behind a small interface. |
| "Refactor freely behind the interface" | Hyrum's law: with enough users, every observable behavior gets depended on. | https://www.hyrumslaw.com/ | Output order, error text, timing, or default values change during a "pure refactor". | Treat observable behavior as the interface. Refactors must not change outputs, error types or messages, or ordering unless the task says so. |
| Composition over inheritance | **No primary critique gathered.** | — | — | Keep the rule as stated. |

---

## Part B — evidence on conventions for LLM coding agents

### B1. Do repository context files help?

- **Gloaguen, Mündler, Müller, Raychev, Vechev (ETH Zurich / LogicStar), arXiv 2602.11988 v2, 2026-06-23 — PP.** Verified from the PDF.
  - Setup: 4 agent/model pairs (Claude Code/Sonnet-4.5, Codex/GPT-5.2, GPT-5.1 mini, Qwen Code/Qwen3-30B). Benchmarks: SWE-bench Lite (300 tasks) and CTXbench (138 tasks, 12 niche repos with developer-committed context files).
  - LLM-generated files: success −0.5 pts (SWE-bench, p=0.87) and −2 pts (CTXbench, p=0.37). Steps +2.45 / +3.92 per task. Cost +20% / +23% (p<0.001%).
  - Developer-written files: success +2.4 pts (p=0.21, not significant), steps +3.34, cost up to +19%. They helped every agent except Claude Code.
  - Behavior: agents follow the instructions. When a tool is mentioned, its usage rises (e.g., uv 1.6×). Repository overviews did not speed up finding the relevant files. Success rate showed no correlation with context-file length (Fig. 13).
  - Category ablation (GPT-5.2, Table 7): removing *testing* instructions cut cost significantly (CTXbench $0.47 → $0.37, p=0.023; SWE-bench p=0.0035). No category moved accuracy significantly. Style/convention rules were **not** ablated separately.
  - Authors' conclusion: context files are useful "for specifying non-standard coding practices."
  - **Correction:** the widely repeated "−3% / +4%" figures come from secondary coverage and do not match v2.
  - Gap: the paper measures task success and cost only, **not code quality**.
- **Lulla et al. (incl. Baltes, Treude), arXiv 2601.20404 (ICSE'26 JAWs) — WS, 5 pp.** 10 repos, 124 PRs, with vs without AGENTS.md. Median runtime −28.64%, output tokens −16.58%, "comparable" completion. It measures output tokens and wall time, not Gloaguen's total inference cost, on different tasks at small scale. The two results don't cancel.
- **Shepard & Albrecht, arXiv 2606.20512 — PP.** SWE-bench Verified, one model (Qwen3.5-35B-A3B), 4 trials. Resolve rate 33.0% with probe-refined guidance, 28.3% with a static knowledge base, 25.5% with none (p<0.001). The gain came from reaching the right files (+14.5 pts); per-patch precision stayed flat (~59%). The guidance covered navigation, not style, and extrapolation to frontier models is unverified.
- **Chatlatanagulchai et al., "Agent READMEs," arXiv 2511.12884 (v2 Aug 2026) — PP, descriptive only.** 2,303 files from 1,925 repos. Testing 75.9%, architecture 68.1%, security 14.8%, performance 14.5% (v1 figures differ slightly). Files grow by small additions. No outcome measure.

### B2. Characteristic quality problems in LLM/agent code

- **He, Miller, Agarwal, Kästner, Vasilescu, arXiv 2511.04427 (MSR'26) — PR.**
  - Difference-in-differences design: 806 Cursor-adopting repos vs 1,380 matched controls, measured with SonarQube.
  - Static-analysis warnings +30.26% (±6.66). Code complexity +41.64% (±7.62). Both persistent.
  - Lines added rose +281% in month 1 and +48% in month 2, then returned to baseline.
  - Accumulated debt later reduced velocity. This is the strongest causal evidence found.
- **GitClear, "AI Copilot Code Quality 2025" — VB, correlational over time, no control group, proprietary metric definitions.**
  - 211M changed lines, 2020–2024.
  - Moved/refactored lines fell from 25% (2021) to <10% (2024). Copy/pasted lines rose from 8.3% to 12.3%, overtaking moved lines for the first time.
  - The report headline claims "4x growth in code clones".
- **Zhu, Tsantalis, Rigby, "AI-Generated Smells," arXiv 2605.02741 — PP, small n.**
  - 90 CodeContest problems and 20 MetaGPT projects.
  - Total LOC correlates with architectural smells at ρ=0.94 (p<0.001).
  - LLMs produce more Long Method smells than the human baseline.
  - Few-shot and more specific requirements did **not** reduce smells (p>0.8).
  - Multi-agent systems scatter functionality across files, which the authors call a "modular mirage".
- **Paul, Zhu, Bayley, arXiv 2510.03029 — PP** (conference version at ICCBDCS'25, a minor venue; Java, older models). Smells +63.34% vs reference solutions: implementation +73.35%, design +21.42%.
- **Cynthia, Muttakin, Roy, arXiv 2601.20109 — PP.** 1,210 merged agent bug-fix PRs, SonarQube. Code smells dominate the new issues. Differences between agents vanish once normalized for PR size.
- **Sawada et al., arXiv 2605.06464 (EASE'26) — PR.** 1,000+ agent-written files in 100 repos. They are maintained less often than human code, mostly for feature extensions, and mostly by humans.
- **Anthropic prompting docs — VB, vendor self-report.**
  - Opus 4.5/4.6 "overengineer": extra files, unnecessary abstractions, unrequested flexibility.
  - The docs ship a snippet against this covering scope, comments, defensive code ("only validate at system boundaries"), and one-off helpers.
- **Not verified:** no empirical source with numbers was found for *dead code* or *excessive defensive code* in LLM output. The only evidence for defensive code is vendor statements.

### B3. Linters and static analysis in the loop

- **SWE-agent (Yang et al., NeurIPS'24) — PR.**
  - An edit command that rejects syntax-breaking edits: 18.0% vs 15.0% without it (SWE-bench Lite, GPT-4 Turbo).
  - Agents recovered from failed edits more often than not.
  - This is a *syntax guardrail*, not a style linter.
- **Blyth, Licorish, Treude, Wagner, arXiv 2508.14419 — PP.** An IEEE Xplore listing exists; the venue was not verified.
  - GPT-4o on PythonSecurityEval, feeding Bandit and Pylint output back into the prompt for up to 10 rounds.
  - Security issues >40% → 13%, readability violations >80% → 11%, reliability warnings >50% → 11%.
  - It optimizes the same metric it reports, and uses single functions. No maintainability outcome.
- **Net:** edit-time guardrails help task success, and warning-driven loops reduce warnings. **No study found shows that style linters in an agent loop improve long-term maintainability.** Zhu et al. suggest prose instructions won't do it either.

### B4. Vendor phrasing guidance (all VB)

- **Anthropic, Claude Code best practices** (code.claude.com/docs/en/best-practices):
  - Keep the file short, prune per line, and include only style rules that differ from defaults.
  - Exclude "self-evident practices like 'write clean code'". A bloated file makes the agent ignore rules.
  - Emphasize one line at most. Hooks are deterministic; instructions are advisory.
  - Reviewers chasing every finding push code into over-engineering.
- **Anthropic, prompting best practices:** say what to do, not what not to do. Give the reason. Dial back "CRITICAL/MUST", because newer models over-trigger.
- **OpenAI Codex best practices:** a short, accurate AGENTS.md beats a long vague one. Add a rule after a repeated mistake. Include lint/test commands.
- **Cursor rules docs:** keep rules under 500 lines. Don't reproduce style guides, because linters handle them. Reference files, don't copy code. Add rules only for repeated mistakes.
- **GitHub Copilot:** repository instructions ≤2 pages, as short self-contained statements, with no conflicts.

---

## Implications for an agent-facing style section

1. **Only non-default rules earn a line.** Gloaguen's conclusion and Anthropic's exclude list agree. "Readability", "prefer pure functions", and "do one thing" are generic defaults the model already knows, so they likely add little signal. This is inference: Gloaguen attributes the measured cost to testing and tooling instructions and never isolated style rules. Replace each with the *repo-specific* form: which directory is the pure core, where I/O is allowed, which import directions are forbidden.
2. **Length budget: ≤ ~25 lines for the style section**, inside a short AGENTS.md. This is inference, not a measured optimum. No study measured one, and Gloaguen found no length–success correlation. The cost of instructions is real, though: agents comply, and compliance costs 2–4 extra steps per task.
3. **Phrase rules as constraints on the diff, not workflow.** Workflow instructions are the measured cost driver (Table 7).
   - State the positive form, give a one-clause *why*, and name a reference file (e.g. "see `core/pricing.py` for the pattern").
   - Use no CRITICAL/MUST, or at most one.
   - Add a rule only after the agent repeats a mistake, and log which mistake it fixes.
4. **Enforce mechanically** whatever a tool can decide:
   - import boundaries, including I/O-in-core bans;
   - a complexity budget;
   - a function-length *warning* (~40–60 lines, never a hard fail);
   - dead code and unused symbols;
   - a clone-level duplication threshold.

   Reasons: vendors say linters beat prose, Zhu found prompting doesn't reduce smells, and He et al. show warnings accumulate otherwise.
5. **State in prose only what a linter can't decide:**
   - when to inline vs extract (the Part A "nameable contract" test);
   - dedupe knowledge, not text (the flag-parameter smell);
   - no speculative configuration;
   - observable behavior is the interface (Hyrum).
6. **Review for the agent-specific failure modes:**
   - over-abstraction: single-use helpers, pass-through layers, interfaces with one implementation;
   - defensive code for impossible states;
   - scope creep and PR size. Size drives issue count (Cynthia) and architectural smells (Zhu).

   Adapt Anthropic's over-engineering snippet as the review rubric. Tell reviewers to flag only correctness- or requirement-relevant gaps, so review itself doesn't push code toward over-engineering.
7. **Pitfall: the operator's own list can cause the damage it targets.** Read strictly, "layered granularity" plus "do one thing" invites the shallow, entangled decomposition Ousterhout describes, and LLMs already lean that way (Anthropic self-report; Zhu). Pair each decomposition rule with its counterweight in the same line, e.g. "split by responsibility; inline single-use helpers without a standalone contract."
8. **Open gap:** no study measures whether style rules in context files change code quality. To find out, A/B the section on real tickets and score the results with the linters above.

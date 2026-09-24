# Evidence memo — 2026-09-24 — code-style canon for agent-written repos

**Trigger:** operator wants a ≤15-rule, language-agnostic coding-standards section
for repos where LLM agents write most code. Operator's five held principles are
tested against the canon here as inputs, not conclusions.

**Grading:** `P` = primary source fetched 2026-09-24; `B` = book, cited by chapter
from the text (not fetched); `2°` = secondary summary only. Source keys expand in §4.
Ruff codes verified against docs.astral.sh 2026-09-24. Other linters' rule names
(eslint, pylint, clippy, typescript-eslint) are from recall, so check them before wiring into CI.

---

## 1. Consensus table

| # | Principle | Statement | Sources | Consensus | Checkable? |
|---|---|---|---|---|---|
| 1 | Clarity over cleverness | Plain construct wins when one works. | EPS 1, 5, 41; Raymond R2; Beck-4 rule 2; Google-review "Complexity"; APoSD ch18 | strong | Partial: cyclomatic lint (ruff `C901`, eslint `complexity`); rest review |
| 2 | Simplicity / YAGNI | Solve today's known problem; no speculative hooks. | Google-review "Over-engineering"; Raymond R5; Beck-4 rule 4; Refactoring ch3 "Speculative Generality" | strong | Partial: unused-param/export finders (vulture, knip); review |
| 3 | Deep modules, information hiding | Small interface, much functionality; one design decision lives in one module. | APoSD ch4–5; TPOP ch4; Raymond R1; PragProg #14 | strong | Import-boundary contracts (import-linter, dependency-cruiser, ArchUnit); public-export count |
| 4 | One abstraction level per function | Orchestrators call named steps; leaves do work; no mixing. | Clean Code ch3 (stepdown); Beck *Smalltalk Best Practice Patterns* "Composed Method"; APoSD ch7; qntm accepts it | moderate | Review only |
| 5 | Short functions (line caps) | Martin: rarely 20 lines. Google: ~40 is a prompt, not a cap. | Clean Code ch3; Google-py 3.18; opposed: APoSD ch9 + debate; McConnell CC2 ch7 | **contested** | Soft signal only (`PLR0915`, `max-lines-per-function`) |
| 6 | Cohesion ("one thing") | A unit is describable in one sentence without "and". | McIlroy (i); CC2 ch7 (functional cohesion); Hevery flaw 4; Refactoring ch3 "Divergent Change" | strong at module level; vague at function level (APoSD debate) | Review only |
| 7 | Separate effects from logic | Pure core, thin imperative shell; commands vs queries. | Bernhardt FC/IS; Raymond R4; PragProg #17; CQS (Meyer, via Fowler) | strong (CQS: moderate, `pop` exception) | Import boundary: core may not import I/O packages; core tests need no mocks |
| 8 | Explicit dependencies | Pass collaborators in; no mutable globals, singletons, service locators. | Hevery flaws 1–3; PragProg #47–48; Google-py 2.5; Refactoring 2e "Global Data"; Go-CRC "Contexts" | strong | `PLW0603` (global stmt); eslint `no-restricted-globals`; review for locators |
| 9 | Immutability by default | Mutate only where needed; never mutate inputs. | Effective Java 17 (2°); Refactoring 2e "Mutable Data"; Google-py 2.12 | strong | `B006`; frozen dataclasses; TS `readonly`/`prefer-const`; `no-param-reassign` |
| 10 | Composition over inheritance | Reuse by holding, not extending. | GoF ch1; Effective Java 18 (2°); PragProg #51–53 | strong | pylint `R0901` (ancestors); review |
| 11 | Parse, don't validate; illegal states unrepresentable | Convert raw input to precise types at the boundary; types carry the proof. | King; Minsky; PragProg #37; EPS 19 | moderate-strong (strong in typed-FP) | Strict type checker; exhaustiveness (`assert_never`, `switch-exhaustiveness-check`); NewType/branded types |
| 12 | Fail fast, never swallow | Detect early, surface loudly, no silent defaults. | Raymond R12; Shore 2004; PragProg #38–39; Go-CRC "Handle Errors"; Google-py 2.4; Effective Java 77 (2°) | strong | `E722`, `BLE001`, `S110`; Go `errcheck`; eslint `no-empty` |
| 13 | Define errors out of existence | Shrink the error surface by redefining semantics (idempotent delete, clamp). | APoSD ch10; Ousterhout CS190 lecture | moderate (one author, compatible with 12) | Review only |
| 14 | Handle errors where action is possible | Detect low, handle high; collapse error kinds into few handlers. | TPOP ch4 (B); Ousterhout CS190 ("aggregate"); Clean Code ch7 | moderate | Review only |
| 15 | DRY means knowledge, not text | One authoritative home per fact; tolerate textual repeats until the third. | PragProg #15; Beck-4 rule 3; Refactoring ch2 (Rule of Three); tension: Metz, Abramov, EPS 44 | moderate (tension) | Signal only: duplicate detectors (jscpd, pylint `R0801`) |
| 16 | No boolean flag parameters; few params | Split into named functions; group params into types. | Fowler FlagArgument; Clean Code ch3; Refactoring ch3 "Long Parameter List" | moderate | `FBT001–003`; clippy `fn_params_excessive_bools`; `PLR0913`/`max-params` |
| 17 | Law of Demeter / tell, don't ask | Don't reach through collaborators. | Holland 1987; PragProg #45–46; Hevery flaw 2; Refactoring ch3 "Message Chains" | moderate (exempt: data structures, fluent APIs) | Review only; chain-length heuristics noisy |
| 18 | Comments carry contracts and "why" | Interface comments required; never restate code. | APoSD ch12–13; Google-review "Comments"; EPS 49–50, 56; opposed: Clean Code ch4 | strong on this synthesis; extremes contested | Docstring lint on public API (ruff `D`); `ERA001` (commented-out code) |
| 19 | Intent-revealing names | Name says what it is/does; length scales with scope. | CC2 ch11; PragProg #74; Google-py 3.16; Go-CRC "Variable Names"; APoSD ch14 | strong | Partial: naming lint (`N8xx`); banned-name lists; review |
| 20 | Consistency with existing code | Follow the local convention over personal preference. | Google-review "Consistency"; APoSD ch17; Raymond R10 | strong | Committed formatter + linter config in CI |
| 21 | Delete dead code | No unused code, commented-out code, or parallel old paths. | Refactoring ch3 "Dead Code"; Tidy First (2°); EPS 16 | strong | `F401`/`F841`, vulture, knip, `ERA001` |

**Key tensions resolved:**
- **Length vs depth (rows 4–5).** SLAP survives both sides. qntm and Ousterhout accept it while rejecting line caps. The debate splits on depth (APoSD), not line count. Ousterhout's red flags: pass-through method, shallow module, conjoined methods (APoSD; red-flag list 2°). In the debate Martin concedes over-decomposition is possible.
- **Comments.** Martin calls comments "always failures" (debate). Ousterhout: "without comments there is no way to have abstraction" (debate). Google, K&P and Ousterhout agree on the middle ground: contract/why comments are in, what-comments are out.
- **DRY vs wrong abstraction.** Metz: "Duplication is far cheaper than the wrong abstraction." PragProg DRY is about knowledge, so the two agree. Deduplicate facts and rules immediately; leave similar-looking code alone until the third instance.
- **Clean Code, split.** Contested: line caps, preference for zero/one arguments, "comments are failures", example quality (qntm, debate). Broadly accepted: names (ch2), SLAP/stepdown, no flag args, CQS, exceptions over error codes (ch7).
- **Fail fast vs define errors out.** These are not opposed. Design-time: remove error cases that need not exist (APoSD ch10). Run-time: any error that remains is surfaced, never swallowed (Raymond R12). Ousterhout's test before throwing: can you see how the caller will handle it (CS190)?

---

## 2. Operator's five principles vs the canon

**(a) Minimize side effects / prefer pure functions.** Supported by Bernhardt FC/IS, Raymond R4, PragProg #17 and #47, Hevery, CQS, and Refactoring 2e's new "Global Data"/"Mutable Data" smells. *Refinement:* the canon doesn't carve out an exception for DB/shared objects. It says to **inject** them (Hevery) and **confine their use to the shell** (Bernhardt). Logging is the one exception nobody disputes.
> **Rule:** Domain logic is pure: output depends only on arguments, with no I/O, clock, randomness, or mutation of inputs/globals. Effects (DB, network, filesystem, time) happen only in orchestrating shell functions, and those receive their handles as parameters, never through imported singletons. Logging is exempt. *Check:* import contract "core ↛ io packages"; core tests use no mocks.

**(b) Composition over inheritance.** Strong and uncontested (GoF, Effective Java 18, PragProg #51–53; Go has no inheritance). *Refinement:* implementing an interface/protocol is fine (PragProg #52). Reusing implementation through inheritance is the thing to avoid.
> **Rule:** Never subclass to reuse implementation. Subclass only to implement an interface/abstract protocol or where a framework requires it. At most one level of concrete inheritance. *Check:* `R0901` ≤ framework depth + 1.

**(c) Optimize for readability.** Strong (EPS, Raymond R2, Beck rule 2, Google, APoSD ch18 "code should be obvious"). *Refinement:* the canon makes it operational. Google counts code as complex when it "can't be understood quickly by code readers". APoSD defines complexity as change amplification, cognitive load, and unknown unknowns.
> **Rule:** Optimize for the next reader. Use the plain construct wherever it works. A reviewer must understand each function from its body plus its callees' names and contracts, without reading their implementations.

**(d) Clear granularity levels.** Supported by Beck's Composed Method (origin), Martin's stepdown/SLAP, and APoSD ch7 "different layer, different abstraction". *Refinement:* the length-driven version is **contested**. APoSD adds the opposing guardrails: no pass-through layers, no shallow wrappers, and no conjoined siblings. McConnell (CC2 ch7) also declines to cap routine length.
> **Rule:** Each function body stays at one abstraction level: orchestrators sequence named steps and leaf functions do one concrete job. Split on abstraction level and independent understandability, never on line count. A function whose body only forwards to another function is a defect.

**(e) Do one thing well.** McIlroy (i), McConnell functional cohesion, Hevery's "and" test, Fowler's Divergent Change. *Refinement:* Ousterhout calls "one thing" vague at function level (debate). Its strongest form is at module/program level. McConnell gives the checkable test: the name describes everything the routine does.
> **Rule:** Each module and function has one responsibility statable in one sentence without "and", and its name covers everything it does. Names that need `And`/`Or`/`Manager`/`Utils`/`Helper` signal a split.

---

## 3. Additions the canon implies, ranked (consensus × agent-code impact)

| Rank | Rule | Consensus | Agent failure mode it targets |
|---|---|---|---|
| 1 | Never swallow errors; fail loudly at the earliest point (row 12) | strong | `except: pass`, silent fallback defaults |
| 2 | No speculative generality: no unused params, flags, config knobs, or single-implementation interfaces (row 2) | strong | Gold-plated "extensibility" |
| 3 | Delete what you replace: no dead code, commented-out code, or compat shims unless asked (row 21) | strong | Old path left beside new |
| 4 | Match existing conventions and reuse existing helpers (row 20) | strong | Imports its own style; re-implements utilities |
| 5 | Explicit dependencies; no new mutable globals, singletons, or module caches (row 8) | strong | Hidden module-level state |
| 6 | Parse at the boundary into precise types; internals trust types; exhaustive matches (row 11) | moderate-strong | Re-validation everywhere (shotgun parsing), stringly/dict typing |
| 7 | Comments state contracts and why; never narrate code or the change history (row 18) | strong | "# increment i", "# now uses X" |
| 8 | Intent-revealing names; banned: `data`, `result`, `tmp`, `helper`, `utils` at wide scope (row 19) | strong | Generic names |
| 9 | No boolean flag params; >4 params → a parameter type (row 16) | moderate | `force=True`, `skip_x=False` accretion |
| 10 | Immutable by default; never mutate arguments (row 9) | strong | In-place edits of caller data |
| 11 | DRY on knowledge; rule of three on text (row 15) | moderate | Both copy-paste across files and premature shared abstractions |
| 12 | Shrink the error surface (idempotent ops, sane clamps) before adding exceptions; handle errors where action is possible (rows 13–14) | moderate | Exceptions for benign cases; catch-log-rethrow at every level |
| 13 | Law of Demeter (row 17) | moderate | `a.b().c().d` coupling |
| 14 | CQS (row 7) | moderate | Getters with side effects |

Not in scope but adjacent: Google-review "Tests" asks for tests that fail when the code breaks. Agents write tautological, over-mocked tests, so this belongs in the testing section.

**Fit to ≤15:** operator's five (a–e) plus ranks 1–10 = 15. Ranks 11–14 go in as refinements: 11 folds into 3/§2(e), 12 into rank 1, and 13–14 into §2(a).

---

## 4. Sources

- **APoSD**: Ousterhout, *A Philosophy of Software Design* 2e (2021), ch2, 4–7, 9–10, 12–14, 17 (B); book page https://web.stanford.edu/~ouster/cgi-bin/aposd.php (P); red-flag list via https://notes.portebois.net/2021/03/04/13.html (2°)
- **Debate**: https://github.com/johnousterhout/aposd-vs-clean-code (P)
- **Ousterhout CS190**: https://web.stanford.edu/~ouster/cgi-bin/cs190-spring16/lecture.php?topic=exceptions (P)
- **Clean Code**: Martin (2008), ch2–4, 7 (B)
- **qntm**: https://qntm.org/clean (2020; 403 on fetch, gist via search, 2°)
- **Abramov**: https://overreacted.io/goodbye-clean-code/ (2020, P); **Muratori**: https://www.computerenhance.com/p/clean-code-horrible-performance (2023, 2°; performance critique, not used for rules)
- **EPS**: Kernighan & Plauger, *Elements of Programming Style* 2e; rule list https://en.wikipedia.org/wiki/The_Elements_of_Programming_Style (2°)
- **TPOP**: Kernighan & Pike, *The Practice of Programming* (1999), ch1 Style, ch4 Interfaces (B; appendix not retrieved)
- **PragProg**: Hunt & Thomas, *The Pragmatic Programmer* 20th anniv. ed.; tips https://pragprog.com/tips/ (P)
- **Refactoring**: Fowler (with Beck), *Refactoring* 2e (2018), ch2, ch3 "Bad Smells in Code" (B); catalog mirror https://refactoring.guru/refactoring/smells (2°)
- **Beck-4**: https://martinfowler.com/bliki/BeckDesignRules.html (P); **Composed Method**: Beck, *Smalltalk Best Practice Patterns* (1997) (B)
- **Tidy First**: Beck (2023); https://henrikwarne.com/2024/01/10/tidy-first/ (2°)
- **FlagArgument**: https://martinfowler.com/bliki/FlagArgument.html (P); **CQS**: https://martinfowler.com/bliki/CommandQuerySeparation.html (P)
- **CC2**: McConnell, *Code Complete* 2e (2004), ch5, 7, 8, 11 (B); checklist summary https://github.com/mgp/book-notes/blob/master/code-complete.markdown (2°)
- **Raymond / McIlroy / Pike**: *The Art of Unix Programming* ch1 §6, mirror https://cscie2x.dce.harvard.edu/hw/ch01s06.html (P; catb.org TLS broken); https://en.wikipedia.org/wiki/Unix_philosophy (2°)
- **Bernhardt**: https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell (P; page is mostly diagram)
- **King**: https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/ (P)
- **Minsky**: https://blog.janestreet.com/effective-ml-revisited/ (2011, P)
- **Google-review**: https://google.github.io/eng-practices/review/reviewer/looking-for.html (P)
- **Google-py**: https://google.github.io/styleguide/pyguide.html (P)
- **Go-CRC**: https://go.dev/wiki/CodeReviewComments (P)
- **Hevery**: https://github.com/mhevery/guide-to-testable-code (P)
- **Shore**: "Fail Fast", IEEE Software 2004, https://www.martinfowler.com/ieeeSoftware/failFast.pdf (P)
- **Metz**: https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction (P)
- **LoD**: Holland/Lieberherr 1987; https://en.wikipedia.org/wiki/Law_of_Demeter (2°)
- **Effective Java**: Bloch 3e, items 17, 18, 77 (B; summaries 2°)
- **GoF**: Gamma et al., *Design Patterns* (1994), ch1 (B)

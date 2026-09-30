# Evidence memo — 2026-09-30 — code guidance: twelve-factor and a terse constraints list

**Trigger:** operator supplied two outside resources and asked for a
comparison against the `code-style` guidance with proposed changes.
**Operator adjudication:** all proposed changes adopted (2026-09-30).

## Sources

1. **Twelve-factor manifesto, update in progress** —
   github.com/twelve-factor/twelve-factor, branch `next` @ `3ad5a5f`
   (2025-07-09; repo last pushed 2025-08-21). CC BY 4.0. Grade: community
   standard (the original 2011 text is widely adopted); the update is
   incomplete — factors restated as numbered requirements, many examples still
   2011-era.
2. **"Timeless constraints (not a checklist)"** — operator-pasted, 10
   principles plus 4 honorable mentions and three meta-rules. Grade:
   practitioner synthesis; every principle traces to the canon memo's sources.

## Findings

**Twelve-factor is not code style.** Its own FAQ says DRY/YAGNI/KISS "will
never be explicit factors". It is the app-platform contract: config, backing
services, processes, logs, shutdown, build/release/run. The existing guidance
covered none of it. It applies to efforts that deploy a long-running service,
so it lands conditionally:
- Code-level factors (III config, IV backing services, VI stateless processes,
  IX disposability, XI logs, II dependencies incl. system tools) → template
  rules 1 and 8 amended, plus a conditional service-rules block (15–17).
- III's litmus test ("could be open-sourced at any moment without leaking
  credentials") → Layer 2 hard fail: secret scan, no brownfield ratchet.
- Architecture factors (V, VII, VIII, X, XII) → recorded A2 defaults for
  service efforts (`steer` references/service-defaults.md), reopenable by ID;
  never questions under the altitude rule.

**The terse list's 10 principles are mostly already covered, and more
operationally** (SoC/SRP/encapsulation → rules 1, 3; DRY-knowledge → 11;
KISS → 5; YAGNI → 9; composition → 4; fail fast/illegal states → 6, 7; OCP
with discipline → 11's rule of three). Restating known principles adds little
(K: Gloaguen et al.; vendor guidance). Two real gaps:
- **Cohesion: change-together lives together.** It was implied, never stated.
  Multi-agent output scatters functionality across files (K: Zhu et al.,
  "modular mirage"). Added to rule 3, with "optimize for deletion" folded in.
- **Depend on abstractions** vs rule 9 (no one-implementation interfaces):
  resolved by making it explicit in rule 1. The pure core depends on data and
  contracts it defines, so the dependency-inversion goal is met without
  speculative interfaces.

**The list's value is its three meta-rules, which the guidance lacked:**
1. A tie-break: when two principles collide, pick the one that cuts future
   cost in this codebase (the worker names the pick in its handoff).
2. Structure first, behavior second (Beck, *Tidy First*): a refactor lands as
   its own commit(s) with tests unchanged and green. This also makes B3 diff
   review cheaper, because a structure-only commit is checkable as "tests
   unchanged and still pass".
3. Constraints, not a checklist. This matches the Cursor and vendor findings
   against checkbox prompting. `allow()` covered exceptions for lint rules
   only.

## Changes landed

- `code-style` template: new preamble (3 meta-rules). Rules 1, 3 and 8
  amended. Conditional service-rules block. About 40 → 46 lines, plus 6
  conditional.
- `code-style` Layer 2: secret scan hard fail, no ratchet, tool invocation
  `UNVERIFIED` until spiked. Layer 3 rubric: structure mixed with behavior;
  scattered change; service-rule violations.
- `steer` A2: installs the service-rules block and records the service
  defaults for service efforts.

## Considered and left unchanged

- OCP, Law of Demeter as stated rules: covered by rule 11's rule of three and
  by the review rubric.
- Twelve-factor's grouped-environments rule (no `staging`/`prod` config
  bundles): kept in the service defaults, not the style rules.
- Length budget: the Trial 2 with/without-prose comparison still decides
  whether the stated layer earns its length.

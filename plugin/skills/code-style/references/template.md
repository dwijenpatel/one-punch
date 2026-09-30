# Default `Code style` section (one-punch template)

Source: the process authority's code-standards evidence memos (canon,
critiques and agent evidence; twelve-factor and terse-constraints comparison).
Install it verbatim, including the preamble and rule 8's wording; do not
paraphrase or "clean up" this block. Fill the `<…>` slots with the repo's own directories and reference file
before committing it into `AGENTS.md`; everything outside the slots stays as
written.

```markdown
## Code style

These are constraints, not a checklist. When two collide, pick the one that
cuts future cost in this codebase, and say which you picked in your handoff.
**Structure first, behavior second:** when a change needs a refactor, land the
refactor as its own commit(s) with tests unchanged and green, then the behavior
change.

1. **Pure core, thin shell.** Decision logic lives in `<core dirs>` and is pure:
   its result depends only on its arguments, with no I/O, clock, randomness, or
   mutation of inputs. DB, network, filesystem and time live in `<shell dirs>`,
   which receive their handles as parameters, never through imported
   singletons. The core depends on data and contracts it defines, never on
   details. Logging is fine anywhere: structured events to stdout; the app
   never routes or stores its own logs. Why: pure code tests without mocks.
   Pattern: `<reference file>`.
2. **Each layer changes the abstraction.** Top-level functions sequence named
   steps, mid-level functions compose leaves, and leaves do one concrete job.
   Keep each body at one level. Inline a function that only forwards, and a
   single-use helper that can't be understood without its caller.
3. **One responsibility, fully named.** A module or function does one thing
   you can state without "and", and its name covers all of it. Modules stay
   deep: few public functions over substantial behavior. Split instead of
   adding a boolean flag parameter. Code that changes together lives
   together; independent parts talk through narrow interfaces. Aim for a
   feature that can be deleted by removing its folder, not by editing ten
   files.
4. **Compose; inherit only to implement an interface** or where the framework
   requires it.
5. **Write for the next reader.** Plain constructs, early returns, names sized
   to their scope. Comments state contracts and why, never what the code does
   or how it changed.
6. **Fail loudly.** Never swallow an error or fall back to a silent default.
   First design error cases away (idempotent operations, clamps); handle the
   rest where something can act on them.
7. **Parse at the boundary.** Turn external input into precise types once, at
   the edge; inside, trust the types and skip re-validation.
8. **Explicit dependencies, immutable data.** Functions get collaborators as
   parameters rather than reaching for them. Module-level constants are
   fine. Configuration that varies between deploys comes from the
   environment, parsed once at startup into a typed object; no credentials or
   per-deploy values in code. Process-wide resources (connection pools, HTTP
   clients, metrics registries) are created once at startup and passed down.
   A genuinely global mutable object is a design decision: it needs a
   `D-NNN` entry. Don't mutate arguments.
9. **Build what the ticket asks.** No speculative parameters, flags, config or
   one-implementation interfaces. Tests and clarity refactors within `Touches`
   are always in scope.
10. **Delete what you replace:** no dead code, commented-out code or compat
    shims unless the ticket asks for them.
11. **Deduplicate knowledge, not text.** A rule that must change in lockstep
    lives in one place; look-alike code stays separate until a third copy that
    changes for the same reason.
12. **Observable behavior is the interface.** Refactors keep outputs, error
    types and messages, and ordering unless the ticket says otherwise.
13. **Match the repo.** Reuse existing helpers and conventions before adding
    new ones; the formatter and linter config are authoritative.
14. **Hot paths may trade these for speed** when profiled and marked
    `PERF: <why>`.
```

### Conditional block — service rules

Install this block after the main section **only when the effort deploys a
long-running service** (a web app, an API, a worker consuming a queue).
CLIs, libraries and local-only tools skip it.

```markdown
### Service rules

15. **Backing services are attached resources.** Databases, queues, caches
    and third-party APIs are reached through a URL or credential from config;
    code never distinguishes a local service from a third-party one.
16. **Processes are stateless and disposable.** Nothing kept in memory or on
    local disk is relied on by the next request; durable state lives in a
    backing service. Start in seconds; on SIGTERM stop accepting work, then
    finish or return in-flight work.
17. **Declare every dependency**, including system tools the code shells out
    to. Nothing is assumed installed globally.
```

## Slots

- `<core dirs>` / `<shell dirs>` — the repo's actual pure-core and thin-shell
  directories. Name them, don't leave the angle brackets in.
- `<reference file>` — one file in the repo that already shows the pure-core /
  thin-shell split, for a worker to pattern-match against instead of inferring
  the rule from prose alone.

## Rule 8's `D-NNN` and the ledger

Rule 8 is the one rule in this template that names the exception mechanism
inline (the decision ledger, `docs/decisions.md` by default). That is
deliberate and part of the verbatim text — do not strip the `D-NNN` clause
when trimming the section for a smaller repo. The same convention
(`allow(<rule>): D-NNN`) extends to every other hard-fail rule in Layer 2; see
the skill's top-level `SKILL.md` for how the exception is granted, checked,
and counted at retro.

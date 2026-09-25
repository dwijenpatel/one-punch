# Default `Code style` section (one-punch template)

Source: one-punch v4 plan, Appendix A. Transcribed verbatim, including rule 8's
current wording — do not paraphrase or "clean up" this block when installing
it. Fill the `<…>` slots with the repo's own directories and reference file
before committing it into `AGENTS.md`; everything outside the slots stays as
written.

```markdown
## Code style

1. **Pure core, thin shell.** Decision logic lives in `<core dirs>` and is pure:
   its result depends only on its arguments, with no I/O, clock, randomness, or
   mutation of inputs. DB, network, filesystem and time live in `<shell dirs>`,
   which receive their handles as parameters, never through imported
   singletons. Logging is fine anywhere. Why: pure code tests without mocks.
   Pattern: `<reference file>`.
2. **Each layer changes the abstraction.** Top-level functions sequence named
   steps, mid-level functions compose leaves, and leaves do one concrete job.
   Keep each body at one level. Inline a function that only forwards, and a
   single-use helper that can't be understood without its caller.
3. **One responsibility, fully named.** A module or function does one thing
   you can state without "and", and its name covers all of it. Modules stay
   deep: few public functions over substantial behavior. Split instead of
   adding a boolean flag parameter.
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
   parameters rather than reaching for them. Module-level constants and
   read-once config are fine. Process-wide resources (connection pools, HTTP
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

---
name: blast-radius
description: "Classify every change by blast radius — the worst damage it could do if it were wrong and shipped unnoticed (irreversibility, exposure, breadth, silence) — into levels B0–B3, and set every scrutiny dial from that level: who decides the design, implementer tier, who writes the tests, which review lenses run, whether a spike is mandatory, whether the operator reads the diff. Ships the blast-map format (a machine-readable block of path globs and content patterns → minimum level), a default pattern pack, the scrutiny ladder, and seven domain checklists of failure modes that pass happy-path tests. Use when proposing or ratifying a project's blast map, declaring a ticket's Blast level, writing independent acceptance tests or a review lens for a high-blast change, or implementing a detector that computes a diff's effective blast level."
compatibility: Harness-neutral. Mechanical consumers of the blast map need a TOML 1.0 parser and a Python-compatible regex engine (Python 3.11+ standard library suffices). The decorrelated review lens is stronger when the harness can launch a model from a different family; it degrades to a fresh top-tier reviewer without the implementer's transcript.
license: MIT
---

# blast-radius — scrutiny goes where damage lives

**Blast radius** is the worst plausible damage a change could do if it is wrong
and the error ships unnoticed. It sets every scrutiny dial in the pipeline, so
the cheap path stays cheap for contained work and the expensive steps —
top-tier implementers, independent test authors, decorrelated lenses, operator
attention — concentrate on the few changes that can hurt.

The one rule that gives this skill its authority: **a level is the maximum of
its sources, and agents can raise it but never lower it.** Only the operator
lowers a level, and only with a recorded decision.

## Four factors

- **Irreversibility** — data lost or corrupted, money moved, messages sent,
  state that cannot be rolled back.
- **Exposure** — crosses a security or privacy boundary: authentication,
  authorization, sessions, secrets, crypto, personal data, parsing untrusted
  input.
- **Breadth** — fan-in: how many modules, users or later tickets depend on it
  (shared core, public interfaces, schema, build, CI, deploy).
- **Silence** — fails quietly rather than loudly. A wrong isolation level or a
  missing authorization check passes every happy-path test.

## Levels

**Silent + irreversible ⇒ B3, regardless of size.**

| Level | Typical code |
|---|---|
| **B0 contained** | tests only, docs, dev scripts, prototypes, internal tooling, copy |
| **B1 local** | feature code behind a seam, one module; failures loud and reversible |
| **B2 wide** | shared core modules, public APIs and interfaces, additive schema changes, concurrency, caching, performance-critical paths, build config, dependency upgrades |
| **B3 severe** | authentication and authorization, sessions, crypto, secrets; payments and money; database transactions and isolation; destructive or irreversible data operations (migrations that drop or transform, deletes, backfills); personal data; tenant and permission boundaries; untrusted-input parsing at a trust boundary; deploy and infrastructure; **process and rule surfaces** (below) |

**Process and rule surfaces are B3** — agent instruction files, the decision
ledger, the blast map itself, the field guide, harness configuration and the
harness, tickets, lint/formatter/type-check configuration, CI workflows and
verify targets. This is gate integrity, not adversarial containment: agents
loosen their own checks to reach green, and a worker that edits the
instruction surfaces steers every later spawn. Such a diff never merges
without the operator.

## Assignment — maximum of three sources

1. **Blast map** — the project's `docs/blast-map.md`: prose plus one
   machine-readable block of **zones**, each a minimum level with path globs
   and content patterns. The format is a contract that schedulers and
   detectors parse: [references/blast-map-format.md](references/blast-map-format.md).
2. **Planner declaration** per ticket: `Blast: B3 — changes session token
   validation` (level plus a one-line reason).
3. **Diff detector** at integration: effective level = max(declared, the
   map's level for every path and changed line in the actual diff). Effective
   above declared is a **blast escalation**: the change does not merge; the
   ticket re-routes at the higher level with its work salvaged, and the retry
   adds that level's scrutiny steps.

Lowering: the operator records a ledger decision (`D-NNN: path X is B1
despite zone Y because …`) and adds a `[[lowering]]` entry citing it.
Protected zones (the process and rule surfaces) cannot be lowered this way.
Detector false positives cost one extra review; accepted, because the costs
are asymmetric.

## Declaring a ticket's level (planner)

1. Walk the four factors for what the ticket changes, not for how big it is.
   Ask: if this is subtly wrong, who finds out, when, and can it be undone?
2. Check the blast map: which zones do the ticket's `Touches` globs overlap?
   The declaration is at least the highest of those zones' levels.
3. Write `Blast: Bn — <reason>` naming the factor that set the level.
4. **Isolate the blast.** When a feature has a B3 core (a token check, a
   migration, a balance update), cut that core into its own small ticket so
   the operator reads a short diff and the rest of the feature takes the
   cheap path. Never let a B1 ticket drift into a B3 zone; that is a
   separate B3 ticket.

## The blast map (propose → ratify → install)

- **Propose** during the parallel discovery phase. Greenfield: draft zones
  from the intent document's catastrophes and the skeleton's architecture.
  Brownfield: the code survey proposes zones from existing code; B3 zones
  usually already exist and have names.
- **Ratify** at the operator's decision sitting: zones and levels are a
  ratification item; every B3 zone is an explicit yes.
- **Install** when tickets are cut: create `docs/blast-map.md` with a short
  prose header (what the map is, who owns it, the ratification date) and one
  ```` ```toml blast-map ```` block containing the whole of
  [references/default-pattern-pack.toml](references/default-pattern-pack.toml)
  followed by the project's own zones. The installed copy is self-contained:
  the harness reads only it, and pack updates reach a project only by an
  operator-reviewed edit.
- **Extend** by adding zones or raising levels; tighten a regex by editing it
  together with its `match`/`nomatch` examples. Validate after every edit
  (the format reference lists the checks); an invalid or missing map fails
  closed.

The default pack covers: process and rule surfaces, lint config, CI verify
targets (B3, protected); build config and dependency manifests (B2); deploy
and infrastructure (B3); authentication and session identifiers,
authorization and tenancy checks, secrets and crypto imports, personal data
(B3); SQL transaction and isolation keywords, destructive SQL and ORM
operations, migration directories (B3); concurrency and caching primitives,
additive schema, destructive filesystem operations (B2); payment SDKs and
money identifiers (B3); unsafe deserialization, eval, command and query
string building (B3); request-input accessors (B2).

## Scrutiny ladder

Each level includes everything in the levels below it.

| Dial | B0 | B1 | B2 | B3 |
|---|---|---|---|---|
| Design decisions | craft default | craft default | default, flagged to the operator | **always an operator fork** |
| Spikes | — | external-behavior claims | same | **mandatory** for every security or consistency semantic relied on (the isolation level the database actually provides, a token library's validation defaults, the framework's CSRF behavior) |
| Implementer tier floor | per task shape and size (cheapest tier allowed) | mid tier | mid tier (top tier for contract-shaped tickets) | **top tier** |
| Tests | verify passes | test-first red→green at the ticket's seams | + edge and error paths at the public seam; coverage on touched files not reduced | + **acceptance tests written first by an independent agent** from the ticket and the domain checklist; + adversarial and negative tests (authorization denial on every path, replay, injection; rollback, concurrent writers, crash mid-transaction, idempotent retry; migration up→down→up on production-shaped data); property tests where an invariant exists |
| Automated review | — | spec verdict if contract-shaped | spec verdict | spec verdict + **decorrelated lens** against the domain checklist |
| Operator review | milestone sample | milestone | milestone; each B2 diff listed | **reads the diff before it merges**; the change waits while other work continues |
| Scheduling | any batch | any | any | never co-scheduled with a ticket sharing a blast-map zone; licensed breakage *into* a B3 zone is forbidden (it becomes its own B3 ticket) |
| Merge conflicts | merge agent | merge agent | merge agent | merge agent on the top tier; the merged result re-enters B3 review |
| Build vs reuse | any | any | prefer a proven reference implementation | **default is a vetted library or reference implementation; hand-rolling auth, crypto, transactions or migrations is an operator fork** |
| Structure | style lint | style lint | + decision logic in the pure core | + **decision logic pure and property-tested on its own; the effectful shell thin enough to review line by line** |

Execution-based verification stays primary at every level. Model review
alone is not an adequate last line at B3: judged review catches few real
bugs, and B3 failures are silent and irreversible — hence the operator's
diff read, and only there.

Mandatory spikes run through the `spike` skill; test-first work through a TDD
skill (e.g. mattpocock `tdd`); milestone review through a code-review skill
(e.g. mattpocock `code-review`). This skill sets *which* of them a change
needs, never how they run.

## Domain checklists

Each is a short list of failure modes that pass happy-path tests, with the
test that exposes each. The independent acceptance-test author turns items
into negative tests; the decorrelated lens answers every item; workers on
B2/B3 tickets get the relevant checklist in their instructions.

- [Authentication & sessions](references/checklist-auth-sessions.md)
- [Authorization & tenancy](references/checklist-authz-tenancy.md)
- [Secrets, crypto & sensitive data](references/checklist-secrets-crypto.md)
- [Transactions & concurrency](references/checklist-transactions-concurrency.md)
- [Migrations & destructive operations](references/checklist-migrations-destructive.md)
- [Money](references/checklist-money.md)
- [Untrusted input](references/checklist-untrusted-input.md)

Which checklists apply is computed, not chosen: every zone names its
checklist, and the detector reports the checklists of every zone the diff
hits at B2 or above. A B3 change whose hits name no checklist (a declared
B3, deploy or process surfaces) gets a lens review against the ticket; the
lens names the closest checklist if one fits.

**Answering** is one line per item: `TC-03 pass: tests/test_ledger.py::test_concurrent_increment`,
`MD-04 n/a: no table rewrite; additive nullable column`, or
`AS-02 fail: audience not checked`. A checklist is answered when every item
has a line and none says `fail` (exact grammar in the format reference).

## Roles

- **Planner** — declares levels, isolates the blast, proposes zones, never
  lowers a level.
- **Worker** — follows its level's steps; if the work turns out to reach a
  higher zone, says so in its handoff rather than waiting for the detector.
- **Independent acceptance-test author (B3)** — sees the ticket and the
  checklists, never the implementation; commits tests before the
  implementation commits exist.
- **Decorrelated lens (B3)** — a different model family when the harness can
  launch one, else a fresh top-tier reviewer that sees code, ticket and diff
  but never the implementer's transcript; answers every checklist item.
- **Operator** — ratifies the map, owns every lowering, reads every B3 diff.
- **Harness** — computes zones for scheduling and the effective level of each
  diff exactly as the format reference specifies; fails closed on a missing
  or invalid map.

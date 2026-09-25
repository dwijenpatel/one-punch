# Blast-map format — schema 1 (machine contract)

The blast map is `docs/blast-map.md` in the project repository. It is prose
for humans plus exactly one machine-readable block that the scheduler (zone
exclusion) and the integration detector (effective blast of a diff) parse.
This file is normative: consumers implement exactly what is written here,
using only a language's standard library (Python: `tomllib`, `re`).

## 1. Extraction

- The block is a fenced code block whose opening line is exactly
  ```` ```toml blast-map ```` (three backticks, `toml`, one space,
  `blast-map`; trailing whitespace allowed) and whose closing line is the
  next line consisting of exactly three backticks (trailing whitespace
  allowed).
- The text between those lines is a TOML 1.0 document (Python:
  `tomllib.loads`).
- Zero such blocks, two or more, an unclosed block, a TOML syntax error, or
  any validation failure in §3 makes the map **invalid**.
- A missing `docs/blast-map.md` or an invalid map **fails closed**: the
  scheduler does not start and the integration step merges nothing,
  reporting `BLAST-MAP-MISSING` or `BLAST-MAP-INVALID: <reason>`. It never
  falls back to "no zones".

Reference extraction (Python 3.11+ standard library):

```python
import re, tomllib

FENCE_OPEN = re.compile(r"^```toml blast-map[ \t]*$")
FENCE_CLOSE = re.compile(r"^```[ \t]*$")

def extract_blast_map(markdown: str) -> dict:
    lines = markdown.splitlines()
    opens = [i for i, line in enumerate(lines) if FENCE_OPEN.match(line)]
    if len(opens) != 1:
        raise ValueError(f"BLAST-MAP-INVALID: expected 1 blast-map block, found {len(opens)}")
    start = opens[0] + 1
    for end in range(start, len(lines)):
        if FENCE_CLOSE.match(lines[end]):
            return tomllib.loads("\n".join(lines[start:end]))
    raise ValueError("BLAST-MAP-INVALID: blast-map block is not closed")
```

## 2. Schema

TOML types are exact; an unknown key at any level makes the map invalid
(typos such as `glob` for `paths` must not silently match nothing).

### Top level

| Key | Type | Required | Meaning |
|---|---|---|---|
| `schema` | integer | yes | Must be `1`. Consumers refuse any other value. |
| `pack` | string | no | Provenance of the copied default pack, e.g. `"one-punch-default/1"`. Informational. |
| `pattern_skip` | array of globs | no, default `[]` | Paths whose lines no pattern ever scans (prose files). Path rules still apply to them. |
| `zone` | array of tables | yes, ≥ 1 | The zones, below. |
| `lowering` | array of tables | no, default `[]` | Operator-owned lowerings, below. |

### `[[zone]]`

| Key | Type | Required | Meaning |
|---|---|---|---|
| `name` | string | yes | Unique; matches `^[a-z0-9]+(-[a-z0-9]+)*$`. The zone identity used by scheduling and lowerings. |
| `level` | string | yes | One of `"B0"`, `"B1"`, `"B2"`, `"B3"`. Minimum level of any change the zone hits. |
| `why` | string | yes | One line, non-empty. Printed in escalation messages. |
| `paths` | array of globs | no, default `[]` | Files in the zone (§4 glob dialect). Used by **both** the scheduler and the detector. |
| `pattern` | array of tables | no, default `[]` | Content patterns, below. Used by the **detector only** — no diff exists at scheduling time. |
| `checklist` | string | no | Domain checklist id (§7). |
| `protected` | boolean | no, default `false` | `true` ⇒ no `[[lowering]]` may name this zone. |

A zone must have at least one path or one pattern.

### `[[zone.pattern]]`

| Key | Type | Required | Meaning |
|---|---|---|---|
| `regex` | string | yes | Python `re` syntax, compiled with `re.compile(regex)` and no flags argument. Case-insensitivity and other flags are written inline at the start, e.g. `(?i)`. Must compile. |
| `files` | array of globs | no, default `["**"]` | The pattern scans only files whose path matches one of these. |
| `match` | array of strings | no, default `[]` | Lines the regex must find (`re.search` truthy). |
| `nomatch` | array of strings | no, default `[]` | Lines the regex must not find. |

`match`/`nomatch` are executable examples: validation runs them, so a repo
that edits a regex learns immediately when it stops matching what it was
written for. TOML literal strings (`'...'`, or `'''...'''` when the regex
contains `'`) keep backslashes verbatim; prefer them for regexes.

### `[[lowering]]`

| Key | Type | Required | Meaning |
|---|---|---|---|
| `zone` | string | yes | Name of an existing, non-protected zone. |
| `paths` | array of globs | yes, ≥ 1 | Paths the lowering covers. |
| `level` | string | yes | Strictly lower than the zone's `level`. |
| `decision` | string | yes | Ledger ID of the operator decision (`D-NNN` by default; the repo's configured ledger ref pattern if it overrides that). |

Only the operator adds lowerings. The map file is itself in a protected
zone, so an agent's edit to it never merges without the operator.

## 3. Validation (all must hold, else `BLAST-MAP-INVALID`)

1. Extraction succeeds (§1); `schema == 1`; no unknown keys; types as in §2.
2. Zone names unique and well-formed; every level in `B0`–`B3`.
3. Every glob is valid under §4.
4. Every regex compiles; every `match` example is found; no `nomatch`
   example is found.
5. Every `checklist` is one of the seven ids in §7.
6. Every lowering names an existing non-protected zone, has a level
   strictly below that zone's level, and a decision ID matching the ledger
   ref pattern (default `^D-\d{3,}$`).

Whether a lowering's decision is *active* is checked at evaluation time
(§5), not here: a superseded decision disables its lowering without
invalidating the map.

## 4. Glob dialect (shared with ticket `Touches`)

Paths are repo-root-relative, `/`-separated, with no leading `./` or `/`.
Globs are anchored at the repo root and must match the **whole** path.
Matching is case-sensitive.

- A glob is split on `/` into segments; empty segments (leading, trailing,
  or doubled `/`) and a leading `./` are invalid.
- A segment that is exactly `**` matches zero or more whole segments; as
  the **last** segment it matches one or more (so `src/**` matches every
  file under `src/` but not a file named `src`). A segment that contains
  `**` together with other characters is invalid.
- In any other segment, `*` matches zero or more characters other than `/`,
  `?` matches exactly one character other than `/`, and every other
  character is literal (`[`, `]`, `{`, `}`, `!` have no special meaning).
- A glob without `/` matches only at the root: `AGENTS.md` is the root file;
  write `**/AGENTS.md` for any depth.

Normative translation to a Python regex (`fullmatch` against the path):

```python
import re

def glob_to_regex(glob: str) -> re.Pattern[str]:
    segments = glob.split("/")
    if glob.startswith("./") or any(s == "" for s in segments):
        raise ValueError(f"BLAST-MAP-INVALID: bad glob {glob!r}")
    out = []
    for i, seg in enumerate(segments):
        last = i == len(segments) - 1
        if seg == "**":
            out.append(".+" if last else "(?:[^/]+/)*")
            continue
        if "**" in seg:
            raise ValueError(f"BLAST-MAP-INVALID: bad glob {glob!r}")
        body = "".join("[^/]*" if c == "*" else "[^/]" if c == "?" else re.escape(c) for c in seg)
        out.append(body if last else body + "/")
    return re.compile("".join(out))
```

Test vectors (glob, path, matches):

| Glob | Path | Match |
|---|---|---|
| `**/AGENTS.md` | `AGENTS.md` | yes |
| `**/AGENTS.md` | `pkg/sub/AGENTS.md` | yes |
| `**/AGENTS.md` | `pkg/AGENTS.md.bak` | no |
| `AGENTS.md` | `pkg/AGENTS.md` | no |
| `src/**` | `src/a.py` | yes |
| `src/**` | `src/a/b/c.py` | yes |
| `src/**` | `src` | no |
| `src/*` | `src/a/b.py` | no |
| `src/*.py` | `src/app.py` | yes |
| `**/migrations/**` | `migrations/0001_init.py` | yes |
| `**/migrations/**` | `app/db/migrations/0002.sql` | yes |
| `**/migrations/**` | `app/migrations_old/x.py` | no |
| `a/**/b.txt` | `a/b.txt` | yes |
| `a/**/b.txt` | `a/x/y/b.txt` | yes |
| `**/.env.*` | `svc/.env.local` | yes |
| `**/tsconfig*.json` | `tsconfig.json` | yes |
| `**/tsconfig*.json` | `web/tsconfig.build.json` | yes |
| `file?.txt` | `file1.txt` | yes |
| `file?.txt` | `file10.txt` | no |
| `**` | `any/path/at/all.c` | yes |
| `Src/**` | `src/a.py` | no |
| `docs/[x].md` | `docs/[x].md` | yes |

Invalid globs: `src/`, `/src/**`, `./src/**`, `src//a`, `src/a**`, `**.py`.

## 5. Evaluation (the detector)

Input: the change's file entries and the ledger.

- **File entry** — for each file the diff adds, modifies, deletes, renames
  or copies: `path` (the post-image path; for a deletion, the deleted
  path), `old_path` (renames and copies only), and `lines` — the changed
  lines: every hunk line beginning with `+` or `-`, excluding the
  `+++ `/`--- ` file headers, with that first character removed. Context
  lines are not changed lines. Binary files have no lines. Running the
  diff with or without rename detection both conform; without it, a moved
  file's every line counts as changed, which can only raise the level.
- **Path hit** — for every zone and every path `p` in {`path`, `old_path`}
  of every entry: if `p` matches any glob in the zone's `paths`, record hit
  (zone, `p`).
- **Pattern hit** — for every zone pattern and every entry whose `path`
  matches the pattern's `files` and matches no `pattern_skip` glob: if
  `re.search(regex, line)` is truthy for any line in `lines`, record hit
  (zone, `path`).
- **Hit level** — the zone's `level`, unless one or more lowerings apply to
  the hit: a lowering applies when its `zone` equals the hit's zone, the
  hit's path matches one of its `paths`, and its `decision` is an
  **active** row in the decision ledger. When lowerings apply, the hit
  level is the **maximum** of their levels (the conservative choice when
  two overlap). A lowering whose decision is missing or not active is
  ignored and reported as `LOWERING-INACTIVE <decision>`.
- **Map level** — the maximum hit level over all hits; `B0` if there are
  no hits. Order: `B0 < B1 < B2 < B3`.
- **Effective level** — `max(declared, map level)`, where `declared` is the
  ticket's `Blast:` level. Effective above declared is a
  `BLAST-ESCALATION`.
- **Checklists** — the set of `checklist` ids of zones with at least one
  hit whose hit level is `B2` or `B3`. These are the domain checklists the
  worker preamble inlines and, at effective `B3`, the ones that must be
  answered (§7).

Report every hit as (zone, path, source `path`|`pattern`, hit level) so an
escalation message can name what fired.

## 6. Zones for scheduling

A ticket is **in** zone Z when its `Touches` globs overlap Z's `paths`
under the same overlap predicate the scheduler uses between two tickets'
`Touches` sets (a file in the current tree matches both, or both match the
same not-yet-existing path prefix). Patterns play no part: scheduling
happens before any diff exists. A B3 ticket is never co-scheduled with a
ticket that shares any zone with it.

## 7. Checklist ids and answers

The seven ids, each a file in this skill's references:

| Id | File | Item prefix |
|---|---|---|
| `auth-sessions` | [checklist-auth-sessions.md](checklist-auth-sessions.md) | `AS` |
| `authz-tenancy` | [checklist-authz-tenancy.md](checklist-authz-tenancy.md) | `AZ` |
| `secrets-crypto` | [checklist-secrets-crypto.md](checklist-secrets-crypto.md) | `SC` |
| `transactions-concurrency` | [checklist-transactions-concurrency.md](checklist-transactions-concurrency.md) | `TC` |
| `migrations-destructive` | [checklist-migrations-destructive.md](checklist-migrations-destructive.md) | `MD` |
| `money` | [checklist-money.md](checklist-money.md) | `MN` |
| `untrusted-input` | [checklist-untrusted-input.md](checklist-untrusted-input.md) | `UI` |

**Items.** Every checklist item is one line matching
`^- \*\*(?P<id>[A-Z]{2}-\d{2})\*\* ` — the item id in bold, then the
failure mode and the test that catches it. Ids are stable: an item is
never renumbered; a retired item keeps its id with the text `Retired.`

**Answers.** An answered checklist is a text file with one line per item,
each matching
`^(?P<id>[A-Z]{2}-\d{2}) (?P<verdict>pass|fail|n/a): (?P<evidence>\S.*)$`
— evidence is the test that proves `pass` (test id or path), the reason
for `n/a`, or the finding for `fail`. A checklist is **answered** when
every non-retired item id appears exactly once and no verdict is `fail`.
Where the answer file lives is the harness's convention.

## 8. Worked example (exact values)

`docs/blast-map.md` (the fence as it appears in the file):

````markdown
# Blast map

Floors for this repo's blast radius; ratified at H2. Lowerings cite D-NNN.

```toml blast-map
schema = 1
pack = "one-punch-default/1"
pattern_skip = ["**/*.md"]

[[zone]]
name = "auth-sessions"
level = "B3"
checklist = "auth-sessions"
why = "Authentication and sessions fail open silently."
paths = ["src/auth/**"]

  [[zone.pattern]]
  regex = '(?i)\bjwt\b'
  match = ["claims = jwt.decode(raw, key)"]
  nomatch = ["jwtish = 1"]

[[zone]]
name = "process-rules"
level = "B3"
protected = true
why = "Rule surfaces steer every later change."
paths = ["**/AGENTS.md", "docs/blast-map.md", "docs/decisions.md"]

[[zone]]
name = "dependency-manifests"
level = "B2"
why = "Dependency changes are wide."
paths = ["**/pyproject.toml"]

[[zone]]
name = "request-input"
level = "B2"
checklist = "untrusted-input"
why = "Request parsing sits on a trust boundary."

  [[zone.pattern]]
  regex = '\brequest\.(json|form|args)\b'
  match = ["rows = request.json"]

[[lowering]]
zone = "request-input"
paths = ["src/admin/**"]
level = "B1"
decision = "D-014"
```
````

Ledger: `D-014` is an active row ("admin export endpoint is behind the VPN
and validated by the schema layer; B1 despite request-input").

Ticket declares `Blast: B1 — admin export columns`. Its diff has four file
entries:

| Entry | `path` | Changed lines |
|---|---|---|
| 1 | `src/admin/export.py` | `+    rows = request.json["rows"]` |
| 2 | `src/api/session_view.py` | `-    claims = jwt.decode(raw, key, algorithms=["HS256"])` |
| 3 | `docs/notes.md` | `+jwt rotation plan` |
| 4 | `pyproject.toml` | `+    "httpx>=0.28",` |

Hits:

| Zone | Path | Source | Hit level | Why |
|---|---|---|---|---|
| `request-input` | `src/admin/export.py` | pattern | `B1` | zone level B2, lowered by active `D-014` |
| `auth-sessions` | `src/api/session_view.py` | pattern | `B3` | removed lines count; the path is outside `src/auth/**` but the pattern fires |
| `dependency-manifests` | `pyproject.toml` | path | `B2` | path glob |

Entry 3 produces no hit: `docs/notes.md` matches `pattern_skip`, and no
zone's `paths` match it.

Result: map level `B3`; effective level `max(B1, B3) = B3`;
`BLAST-ESCALATION` (declared `B1`, effective `B3`); checklists
`{"auth-sessions"}` (`request-input` is excluded because its only hit was
lowered to `B1`).

Variant: if `D-014` is superseded, the lowering is ignored and reported as
`LOWERING-INACTIVE D-014`; the `request-input` hit is `B2`; map level stays
`B3`; checklists become `{"auth-sessions", "untrusted-input"}`.

Scheduling with the same map, tree `["src/auth/login.py",
"src/api/users.py", "AGENTS.md", "pyproject.toml"]`:

| Ticket | `Touches` | Zones |
|---|---|---|
| A | `src/auth/**` | `{auth-sessions}` |
| B | `src/api/**` | `{}` |
| C | `src/**` | `{auth-sessions}` |
| D | `AGENTS.md` | `{process-rules}` |

If A is B3, A may be batched with B or D but not with C.

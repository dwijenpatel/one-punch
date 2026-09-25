# 03 — skill blast radius

Type: task
Status: done
Blocked by: —
Tag: contract
Blast: B1
Size: high
Touches: plugin/skills/blast-radius/**
Authority: docs/design/2026-09-24-v4-steer-then-swarm-plan.md

## What

New skill per plan §2b: level definitions (B0–B3, four factors), blast-map format (`docs/blast-map.md` with a machine-readable block: path globs + content patterns → min level; operator-owned lowering via `D-NNN`), default pattern pack (auth/session/token identifiers, crypto imports, SQL DDL/DELETE/transaction/isolation keywords, migration dirs, payment SDKs, role/permission checks, external deserialization, CI/deploy files), the scrutiny ladder, and domain checklists as references (auth & sessions, authz & tenancy, secrets & crypto, transactions & concurrency, migrations & destructive ops, money, untrusted input).

Constraints: Agent Skills standard (name = dir, description says what + when, harness-neutral, SKILL.md < 500 lines, detail in references/). The machine-readable block's schema is the contract ticket 07/08 parse — document it with one worked example with exact values.

Acceptance: `test -f plugin/skills/blast-radius/SKILL.md` · 7 checklist files under references/ · schema example parses (a doctest-style snippet or `python -c` in Comments) · `skills-ref validate` if available.

## Comments
2026-09-24 — ACCEPTED amendment (operator, 2026-09-24), from outrigger
exec-loop's protected-paths interlock, reframed as gate integrity rather than
adversarial containment: agents loosen their own checks to reach green, and a
worker that edits the instruction/process surfaces steers every later spawn. Default pattern pack classifies these as **B3**: `AGENTS.md`,
`CLAUDE.md`, `.claude/`, `.agents/`, `.codex/`, `docs/blast-map.md`,
`docs/decisions.md`, `docs/field-guide/`, `harness.toml`, lint/formatter
config, verify commands, and the harness itself. Effect: such a diff never auto-merges; it goes through the operator.

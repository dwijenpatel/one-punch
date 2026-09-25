# one-punch — working rules (canonical, all agents)

- **Authority:** [docs/design/pipeline.md](docs/design/pipeline.md) (v4). Changes cite
  what prompted them — a session, a measurement, a trial, a retro memo — in the
  commit message. The repo's history is the ledger; retro evidence memos live in
  `docs/evidence/`.
- **Compose, don't paraphrase.** one-punch is a thin layer over the
  `mattpocock-skills` plugin (wayfinder, grilling, prototype, to-spec, to-tickets,
  tdd, code-review, …) and composes the evidence-kit method for research. Never
  copy or restate those projects' content into this repo — deltas only, as
  one-punch's own skills. Paraphrases drift.
- **Git:** never commit directly to `main` — feature branch → commit → ff-only
  merge → delete branch.
- **Skills stay self-contained, portable, and harness-agnostic:** no repo-relative
  references, machine paths, or project names inside `plugin/skills/*/SKILL.md`;
  conform to the Agent Skills open standard (agentskills.io) — no hardcoded
  vendor tool names, graceful degradation when a harness lacks a capability,
  real requirements in `compatibility:` frontmatter.
- **Provisional skills carry their re-earn test in their own file** (currently:
  `contract-review`). When the test says delete, delete — don't renegotiate in
  the moment.
- **Operator host notes:** shell is zsh (no bare `=`-prefixed words; explicit
  arrays in loops; macOS lacks `realpath -m`).

# one-punch — working rules

- **Authority:** [docs/design/pipeline.md](docs/design/pipeline.md) (v2). Changes cite
  what prompted them — a session, a measurement, a trial — in the commit message. No
  heavier evidence gate: at this maturity, big corrections beat small ones, and the
  repo's history is the ledger.
- **Compose, don't paraphrase.** one-punch is a thin layer over the
  `mattpocock-skills` plugin (wayfinder, grilling, prototype, to-spec, to-tickets, tdd,
  code-review, …). Never copy or restate those skills' content into this repo — deltas
  only, as one-punch's own skills. Paraphrases drift.
- **Git:** never commit directly to `main` — feature branch → commit → `--ff-only`
  merge → delete branch.
- **Skills stay self-contained and portable:** no repo-relative references, machine
  paths, or project names inside `plugin/skills/*/SKILL.md` — they get installed into
  arbitrary repos.
- **Provisional skills carry their re-earn test in their own file** (currently:
  `contract-review`). When the test says delete, delete — don't renegotiate in the
  moment.
- **Operator shell is zsh:** no bare `=`-prefixed words; explicit arrays for loops;
  macOS lacks `realpath -m`.

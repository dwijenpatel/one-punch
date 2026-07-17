# one-punch — working rules

- **Authority:** [docs/design/pipeline.md](docs/design/pipeline.md). Changes to pipeline
  *behavior* (runner control flow, gate semantics, skill contracts) require either
  evidence measured in the outrigger lab (`~/repos/outrigger` — the evidence base this
  design cites) or a named trial in this repo's records. Refactors and fixes with
  mock-suite coverage need no new evidence.
- **Git:** never commit directly to `main` — feature branch → commit → `--ff-only`
  merge → delete branch. (Initial scaffold excepted.)
- **After any runner change:** `python3 -m py_compile runner/runner.py` and
  `zsh runner/tests/mock_suite.zsh` — all scenarios must pass. The mock suite's claude
  shim mimics headless deny-by-default; keep it faithful when adding stages.
- **Runner control flow reads git state and file existence only** — never model prose.
  Telemetry parses structured JSON fields; a parse failure must never affect control
  flow.
- **Skills stay self-contained and portable:** no repo-relative references inside
  `plugin/skills/*/SKILL.md` — they get installed into arbitrary repos.
- **Operator shell is zsh:** no bare `=`-prefixed words; explicit arrays for loops;
  macOS lacks `realpath -m`.
- Sessions spending real quota (live pipeline runs) are operator-directed only — never
  wired into tests or CI.

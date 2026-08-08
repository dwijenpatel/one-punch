@AGENTS.md

## Claude Code-specific guidance

- Plugin install for local development: `claude plugin marketplace add <this repo path>`
  then `claude plugin install one-punch@one-punch`.
- Subagent model policy comes from the operator's global CLAUDE.md (never spawn
  subagents on the session's top model; set `model` explicitly on every spawn).

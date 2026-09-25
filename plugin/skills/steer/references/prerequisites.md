# Preflight — report format and example commands

## Report

Print one line per item before H1; nothing is assumed current.

```
Preflight — <date>
git repo on main ............ present | missing → git init -b main
<skill or plugin> ........... present <version> | missing → <install command> | stale <installed> < <available> → <update command> | unchecked (<why>)
issue tracker ............... configured (<kind>) | missing → setup-matt-pocock-skills
worker harness .............. runnable | missing <requirement> → build degrades to sequential tickets
```

End with one line: `Restart needed before H1: yes | no`. Updates to skills and
plugins usually load only at session start, so any `stale` line makes it
`yes`.

## Example commands by harness

These are examples for two harness families; use the current harness's own
equivalents, and print the exact command rather than describing it.

**Plugin-marketplace harnesses** (for example, Claude Code):

```
claude plugin install mattpocock-skills@mattpocock
claude plugin marketplace update <marketplace>
claude plugin update <plugin>@<marketplace>
```

Installed versions are listed by the harness's plugin listing command;
compare them against the marketplace or local source version.

**File-copy harnesses** (skills are directories copied into the agent's skill
path):

```
npx skills@latest add mattpocock/skills
```

Freshness here means comparing the copied directory against its source
(a commit or version file); if the source is not reachable, report
`unchecked`.

**evidence-kit** installs as a skill directory from its own repository; follow
that repository's README for the current harness. Its absence is not fatal:
the evidence lane falls back to mattpocock `research` with every claim marked
ungraded.

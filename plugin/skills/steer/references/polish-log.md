# Polish log

Written to `milestones/<m>/polish.md` when the H3 sitting ends, one row per
operator-reported fix, closed when the operator says polish is done. `steer
resume` reads its `Status:` line; `retro` reads its rows as unplanned
operator interventions. Every row links its evidence; a missing artifact is
written `not recorded`.

```
# Polish — <effort> · <milestone m>

Status: open | closed <date>

| # | Reported symptom (operator's words, trimmed) | Regression case | Failing run before the fix | Fix | Path | Suite + full walk after | Ledger row |
|---|---|---|---|---|---|---|---|
| P-1 | <…> | <test path :: case> | <command — failed, date> | <commit or ticket NN> | planner-direct (1 file, <n> lines) | worker ticket | green | D-NNN |

New scope raised during polish (not fixed here): <request — ticket NN | next milestone>
main fast-forwarded to the integration head at close: <full SHA> | no — <why>
```

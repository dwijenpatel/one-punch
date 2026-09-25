# 13 — Harness imperative shell (run / resume / plan-probe)

Type: task
Status: superseded (by v4-execution 09)
Blocked by: 06, 07
Tag: contract
Size: high

## Question

The thin imperative shell connecting the pure core to the world: parse tickets
(markdown -> Ticket), harness.toml (ladder/floors/verify commands/epsilon),
bundle creation + launcher dispatch, verify execution (the authority), salvage
stash/restore, JSONL ledger append, and the three entry points (run: multi-pass
frontier loop; resume: state report from a bare clone; plan-probe). Shell stays
thin: every decision already lives in core.py; the shell executes RouteDecisions
and appends events. Integration-test against the mock launcher.

Honest status: cores and launchers are done and verified (tickets 06-07); this
shell is the remaining piece before an effort's BUILD phase can run unattended.
The ckb front half (start -> intent -> evidence -> map -> contract -> tickets)
needs nothing from it.

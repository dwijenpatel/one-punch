# Checklist — migrations & destructive operations (`migrations-destructive`)

Failure modes that pass happy-path tests. Each item: what goes wrong
silently, then the test or check that exposes it. The oracle test author
writes the negative tests; the lens answers every item (answer format in
[blast-map-format.md](blast-map-format.md) §7).

- **MD-01** Down migration missing or lossy; up→down→up never run on data shaped like production. *Test:* up→down→up on a fixture with realistic volume, nulls, duplicates, unicode and boundary values; row counts and checksums match.
- **MD-02** A NOT NULL, unique or foreign-key constraint added without a backfill that handles the values production actually holds. *Test:* run the migration on a fixture containing nulls, duplicates and orphans → it succeeds or fails loudly before changing anything.
- **MD-03** A destructive step (drop, rename, type narrowing) ships in the same release as the code that stops using it, so old code running during rollout breaks. *Check:* expand/contract ordering; the drop lands a release after the last reader is gone.
- **MD-04** The migration takes a long lock or rewrites a large table (non-concurrent index build, column type change) — fine on a test database, an outage in production. *Check:* locking behavior for the production database version is pinned by a spike transcript.
- **MD-05** Backfill or update with a missing or wrong WHERE clause, or a batch loop that skips or double-processes rows at batch edges; not resumable. *Test:* exact affected-row counts on a fixture; interrupt and resume → the same final state.
- **MD-06** Data transform not idempotent: re-running applies it twice (cents multiplied by 100 twice). *Test:* run the transform twice → identical result.
- **MD-07** A delete removes more than intended through cascades, triggers or ignored soft-delete filters. *Test:* delete one parent in a fixture → assert exactly the expected rows are gone, and no others.
- **MD-08** Migration ordering conflicts with parallel branches (duplicate ids, two heads). *Test:* the migration graph has a single head after rebase.
- **MD-09** Irreversible operation without a recovery path: no backup, snapshot, soft-delete window or archived copy. *Check:* the recovery path is stated in the ticket and exercised once.
- **MD-10** Type conversion changes precision, encoding or time zone (float to decimal, timestamp to timestamptz, text encoding). *Test:* round-trip boundary values through the conversion.
- **MD-11** Destructive filesystem or history operation driven by a variable that can be empty or attacker-influenced (`rm -rf "$DIR/"`, force-push). *Test:* empty or root-like path → refuses; the path is contained under an expected root.

# Checklist — transactions & concurrency (`transactions-concurrency`)

Failure modes that pass happy-path tests. Each item: what goes wrong
silently, then the test or check that exposes it. The oracle test author
writes the negative tests; the lens answers every item (answer format in
[blast-map-format.md](blast-map-format.md) §7).

- **TC-01** Transaction boundaries do not match the invariant: writes that must agree run in separate transactions or in autocommit. *Test:* inject a failure between the writes → neither is persisted.
- **TC-02** Isolation level unstated, or the code relies on a guarantee the database does not provide at that level (write skew under snapshot isolation, phantom reads). *Test:* two concurrent transactions that would violate the invariant; the level the database actually provides is pinned by a spike transcript.
- **TC-03** Read-modify-write outside a transaction, or without a row lock or conditional update (lost update). *Test:* two concurrent increments of the same row → both applied.
- **TC-04** Retries are not idempotent: a retried transaction, request or message duplicates its effect. *Test:* deliver the same request or idempotency key twice → exactly one effect.
- **TC-05** External side effects (HTTP calls, messages, emails, file writes) inside a transaction that can roll back, or fired after commit with no outbox or reconciliation. *Test:* force a rollback → no message sent; crash after commit → the effect is still delivered.
- **TC-06** Lock order not fixed, or a lock held across I/O or an await (deadlock, convoy). *Test:* concurrent operations acquiring the same resources in opposite request order complete within a timeout.
- **TC-07** A failure leaves partial state: an exception handler swallows the error and commits, or nested transaction or savepoint semantics differ from the assumption. *Test:* fail at each step → database state equals the state before the call.
- **TC-08** Serialization failures and deadlock errors are not retried, or retried without a bound or backoff. *Test:* an injected serialization error → retried, and gives up after the configured bound.
- **TC-09** Uniqueness enforced by check-then-insert without a database constraint. *Test:* concurrent creates of the same key → exactly one row; the constraint exists in the schema.
- **TC-10** Cache or in-memory state updated before commit, or not invalidated on rollback. *Test:* roll back → the cache agrees with the database.
- **TC-11** A connection or session shared across threads or tasks, or returned to the pool mid-transaction. *Test:* concurrent requests do not observe each other's uncommitted writes.
- **TC-12** State read before an await or yield point and acted on after it (time-of-check to time-of-use). *Test:* interleave a concurrent write at the await point → the action re-checks or fails.

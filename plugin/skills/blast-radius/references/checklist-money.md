# Checklist — money (`money`)

Failure modes that pass happy-path tests. Each item: what goes wrong
silently, then the test or check that exposes it. The oracle test author
writes the negative tests; the lens answers every item (answer format in
[blast-map-format.md](blast-map-format.md) §7).

- **MN-01** Money held in binary floating point, or rounding mode and rounding step unstated (per line versus on the total). *Test:* line items that round differently per line and on the total → the documented rule holds and lines sum to the total.
- **MN-02** Amount carried without its currency, currencies mixed, or two minor-unit digits assumed for every currency. *Test:* JPY (0 digits) and KWD (3 digits) amounts round-trip exactly; mixing currencies raises.
- **MN-03** Charge, transfer or payout not idempotent: a retry or double submit moves money twice; the idempotency key is not passed to the provider. *Test:* the same request and key twice → one provider call, one ledger entry.
- **MN-04** Provider webhooks accepted without signature verification, or replayed and out-of-order events applied twice or in the wrong order. *Test:* unsigned webhook → rejected; duplicate event → one effect; out-of-order events → final state correct.
- **MN-05** Payment state machine allows an invalid transition: marked paid before capture is confirmed, refund above the captured amount, refund of a failed charge. *Test:* each invalid transition → rejected.
- **MN-06** Balance changed without a matching ledger entry, or computed by read-modify-write under concurrency. *Test:* after concurrent operations, the sum of ledger entries equals the stored balance.
- **MN-07** Price, amount or discount taken from the client; negative, zero or overflowing amounts accepted. *Test:* a tampered client price is ignored; negative, zero and maximal amounts are rejected or handled as specified.
- **MN-08** Provider sandbox behavior assumed to match live (decline codes, 3-D Secure, settlement timing). *Check:* each provider behavior relied on is pinned by a spike transcript against the provider's documented test mode.
- **MN-09** Crash between the provider's success and the local commit leaves money moved with no record. *Test:* simulate the crash → the reconciliation path finds and records the charge.
- **MN-10** Tax, fee and discount application order unspecified; discounts stack or apply after tax contrary to the rule. *Test:* a worked example with exact values per rule, asserted to the minor unit.

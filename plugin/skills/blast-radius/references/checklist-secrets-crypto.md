# Checklist — secrets, crypto & sensitive data (`secrets-crypto`)

Failure modes that pass happy-path tests. Each item: what goes wrong
silently, then the test or check that exposes it. Also used for personal
data. The oracle test author writes the negative tests; the lens answers
every item (answer format in [blast-map-format.md](blast-map-format.md) §7).

- **SC-01** A secret lands in source, fixtures, logs, error messages, crash reports or a client bundle. *Test:* a secret scanner over the diff is clean; a log-capture test asserts the secret is absent from output on success and error paths.
- **SC-02** Hand-rolled construction or low-level primitive used where a vetted high-level API exists (ECB mode, raw RSA, homemade MAC, encrypt-without-authenticate). *Check:* only the vetted library's high-level API is called; hand-rolling was an operator decision with a ledger row.
- **SC-03** Tokens, nonces, salts or identifiers drawn from a non-cryptographic generator. *Check:* every security-relevant random value comes from the platform CSPRNG.
- **SC-04** Nonce or IV reused under the same key (static IV, counter reset on restart). *Test:* encrypting the same plaintext twice yields different ciphertexts; nonce generation is not derived from process-local state.
- **SC-05** Signature or MAC verified with a non-constant-time compare, or data used before verification completes. *Check:* verify-then-use ordering; constant-time compare.
- **SC-06** TLS certificate or hostname verification disabled, including "temporarily" or in a code path reachable in production. *Test:* a connection to a self-signed endpoint fails.
- **SC-07** Key rotation breaks: data under the previous key no longer decrypts, or retired keys stay accepted forever. *Test:* decrypt a fixture encrypted under the previous key id; a retired key id is rejected.
- **SC-08** A deprecated algorithm or parameter used for a security purpose (MD5 or SHA-1 for integrity, RSA below 2048 bits, low PBKDF2 iterations). *Check:* algorithms and parameters are pinned and current.
- **SC-09** Personal data written to logs, analytics, error trackers or caches without redaction, or returned in responses beyond what the caller needs. *Test:* a request carrying personal data → captured logs and events contain only redacted forms; response fields match an allowlist.
- **SC-10** Encryption or key lookup fails open: plaintext stored or sent when the key is unavailable. *Test:* key unavailable → the operation errors and nothing is persisted.
- **SC-11** A secret read from configuration with a silent default (`getenv("SECRET", "dev")`), so production runs with the default. *Test:* start with the secret unset → startup fails.

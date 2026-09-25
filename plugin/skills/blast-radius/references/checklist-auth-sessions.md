# Checklist — authentication & sessions (`auth-sessions`)

Failure modes that pass happy-path tests. Each item: what goes wrong
silently, then the test or check that exposes it. The oracle test author
writes the negative tests; the lens answers every item (answer format in
[blast-map-format.md](blast-map-format.md) §7).

- **AS-01** Token signature accepted with an algorithm outside a pinned allowlist (`alg: none`, HS256 verified with an RS256 public key). *Test:* forged tokens with `alg: none` and with HS256 signed by the public key → 401.
- **AS-02** Expiry, not-before, audience or issuer not enforced because the library's defaults differ from the assumption. *Test:* expired, future-`nbf`, wrong-`aud`, wrong-`iss` tokens each → 401; the defaults relied on are pinned by a spike transcript.
- **AS-03** Session identifier not rotated on login or privilege change (session fixation). *Test:* session id before login ≠ session id after login and after role elevation.
- **AS-04** Logout, password change or account disable leaves existing sessions and refresh tokens valid. *Test:* the pre-logout session and refresh token → 401 after each of those events.
- **AS-05** Secrets, tokens or password hashes compared with ordinary equality instead of a constant-time comparison. *Check:* every comparison of secret material uses the platform's constant-time compare.
- **AS-06** Passwords stored with a fast hash, without per-user salt, or with a work factor below current guidance. *Test:* the stored value carries the expected algorithm and cost prefix (e.g. `$argon2id$` with pinned parameters).
- **AS-07** Unknown user and wrong password are distinguishable by status, body or timing (account enumeration), including on reset and signup. *Test:* both cases return byte-identical status and body; the unknown-user path still runs a hash.
- **AS-08** Session cookie missing `HttpOnly`, `Secure` or `SameSite`, or scoped to a broader domain or path than needed. *Test:* assert the exact `Set-Cookie` attributes.
- **AS-09** CSRF protection absent or bypassed on a new state-changing route (JSON endpoints, method override, GET that mutates). *Test:* cross-origin POST without the token → 403 on every new mutating route.
- **AS-10** No rate limit or lockout on login, password reset, OTP or MFA verification. *Test:* the attempt after the configured limit is rejected, per account and per source.
- **AS-11** Reset, invite or magic-link tokens reusable, non-expiring, not bound to one user, or written to logs. *Test:* second use → rejected; expired → rejected; token absent from captured logs.
- **AS-12** Verification fails open: an exception, timeout or missing key in the verifier lets the request continue as authenticated or as a default user. *Test:* force the verifier to raise → the request is denied, never 200.

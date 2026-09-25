# Checklist — untrusted input (`untrusted-input`)

Failure modes that pass happy-path tests. Each item: what goes wrong
silently, then the test or check that exposes it. The oracle test author
writes the negative tests; the lens answers every item (answer format in
[blast-map-format.md](blast-map-format.md) §7).

- **UI-01** Query, shell, template or path strings built by concatenating input (SQL, shell, LDAP, NoSQL, template injection). *Test:* payloads such as `' OR 1=1 --`, `; id`, `{{7*7}}`, `$where` are stored or echoed literally, never executed.
- **UI-02** External data deserialized with a code-executing format (pickle, unsafe YAML load, native object streams) or passed to eval. *Test:* a crafted payload does not execute; only the safe loader is reachable.
- **UI-03** XML parsed with external entities or unbounded entity expansion enabled. *Test:* an XXE payload and a billion-laughs payload → rejected without file or network access.
- **UI-04** File path taken from input without normalization and containment (`../`, absolute paths, symlinks, encoded `%2e%2e`). *Test:* each traversal form → rejected; the resolved path stays under the allowed root.
- **UI-05** Server fetches a URL from input without an allowlist (redirects, IPv6 literals, link-local metadata addresses, DNS rebinding). *Test:* URLs resolving to internal and metadata addresses, directly and via redirect → refused.
- **UI-06** No limit on body size, nesting depth, element count, decompressed size or regex cost. *Test:* oversized body, deeply nested JSON, a zip bomb and a catastrophic-backtracking input → rejected promptly.
- **UI-07** Validation on one entry path only: the HTTP API validates, the CLI, queue consumer, webhook or import job does not. *Test:* the same malformed input through every entry path → rejected.
- **UI-08** Unicode and encoding tricks: normalization or case-folding differences in identifiers, null bytes, CRLF injection into headers or logs. *Test:* confusable and differently normalized identifiers do not collide with or impersonate existing ones; CR/LF and NUL are rejected or escaped.
- **UI-09** Input rendered without output encoding (HTML, attributes, URLs, JavaScript), including through a "safe" or raw-HTML escape hatch. *Test:* a stored XSS payload renders inert in every view that shows it.
- **UI-10** Two components parse the same input differently (URL parsers, duplicate JSON keys, content-type confusion, header folding). *Test:* ambiguous inputs are rejected at the boundary, not reinterpreted downstream.
- **UI-11** Error responses echo the input, stack traces or internal identifiers. *Test:* a malformed request's response contains none of them.

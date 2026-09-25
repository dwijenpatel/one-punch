# Checklist — authorization & tenancy (`authz-tenancy`)

Failure modes that pass happy-path tests. Each item: what goes wrong
silently, then the test or check that exposes it. The oracle test author
writes the negative tests; the lens answers every item (answer format in
[blast-map-format.md](blast-map-format.md) §7).

- **AZ-01** A new route, handler, RPC method or GraphQL field ships without the authorization check the others have. *Test:* enumerate every route the change adds or touches; each has an unauthenticated-denied and a wrong-role-denied test.
- **AZ-02** Object fetched by identifier without an owner or tenant filter (insecure direct object reference). *Test:* user A requests user B's object id → 404 or 403, never B's data.
- **AZ-03** Tenant scoping applied on read but missing on update, delete, list, count, search, export or bulk endpoints. *Test:* a cross-tenant request for every verb the resource exposes → denied or empty.
- **AZ-04** The check guards a different path than the effect: the list is filtered but the mutation endpoint, bulk endpoint or background job is not; or the check lives only in the UI. *Test:* call each effectful endpoint directly, bypassing the UI → denied.
- **AZ-05** Role logic is a deny-list or string match that a new or unknown role bypasses; the default role grants more than read. *Test:* an unknown role and a newly created role → denied.
- **AZ-06** Mass assignment: the payload can set `role`, `tenant_id`, `owner_id`, `is_admin` or similar protected fields. *Test:* submit each protected field → ignored or rejected, stored value unchanged.
- **AZ-07** Revocation not effective: cached permissions, long-lived tokens or check-then-act races keep access after a role is removed. *Test:* revoke, then act → denied within the stated window.
- **AZ-08** Background jobs, webhooks, admin scripts and queue consumers run without tenant context and touch every tenant's rows. *Test:* a job scheduled for tenant A cannot read or write tenant B's data.
- **AZ-09** A denial leaks existence or data: 403 versus 404 where policy says indistinguishable, or the error message echoes the object. *Test:* nonexistent and forbidden ids return identical responses where the policy requires it.
- **AZ-10** A refactor removes an authorization line without replacing it; the diff shows it only as a deleted line. *Check:* every removed line containing a permission, role or tenant check is accounted for in the diff; the pre-existing denial tests still run and pass.

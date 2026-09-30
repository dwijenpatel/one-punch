# Service defaults (recorded at A2 for service efforts)

For an effort that deploys a long-running service, the planner records each
line below as a default `D-NNN` row in the decision ledger. These are
defaults, not questions: each is reopenable by ID, and a line that doesn't fit
the project is recorded as a deviation with its reason rather than dropped
silently. Anything here that turns out to be a one-way door for this project
(for example a hosting platform that forbids one of these) becomes an H2 fork
instead.

| Default | What it means in the project |
|---|---|
| Config in the environment | Deploy-varying values (hosts, credentials, feature toggles per deploy) come from environment variables, parsed once at startup into a typed object. Each variable is its own control, never grouped into named environments such as `staging` or `prod` bundles. |
| Backing services are attached resources | Every database, queue, cache and third-party API is addressed by a URL or credential in config, so it can be swapped without a code change. |
| Build, release, run are separate | A build produces an artifact. A release is that artifact plus config, and is immutable and identifiable. Run executes a release. No code changes at run time. |
| Stateless processes | No sticky sessions and no reliance on local memory or disk between requests. Session and job state live in a backing service. |
| Port binding | The service exports itself by binding a port that config supplies. It does not rely on a server injected at run time. |
| Scale out by process type | Scale by running more processes of a type (web, worker, scheduler), not by growing one process. |
| Disposability | Starts in seconds. On SIGTERM, stops accepting work, then finishes or returns in-flight work. Survives sudden termination without corrupting data. |
| Dev/prod parity | Development uses the same kinds of backing services as production (not an in-memory or file database standing in for a server database), at versions close to production. |
| Logs are an event stream | Structured events go to stdout. The platform, not the app, routes and stores them. |
| Admin tasks are one-off processes | Migrations and maintenance scripts run as one-off commands against the same release and config as the app, and are committed with it. |

Blast-radius note: deploy configuration, migrations and credentials handling
are already high-blast zones in the default pattern pack. These defaults
decide *how* such code is shaped, not how much scrutiny it gets.

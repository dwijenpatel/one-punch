# Private overlay setup (fails closed)

Goal: a `.private/` directory whose contents are structurally unpublishable
from the main repo, while both repos replicate to remotes (no laptop SPOF).

Order matters — ignore before create:

```bash
# in the project repo, ideally in its first commit
echo '/.private/' >> .gitignore
git add .gitignore && git commit -m "chore: ignore .private overlay"

mkdir .private && cd .private
git init                     # its OWN repository
git remote add origin <private remote URL>   # always-private remote
cd ..
git check-ignore -q .private/ && echo "overlay ignored: OK"
```

Rules:
- The main repo gets NO public remote until publish day; publishing = flipping
  the main repo's visibility (its history is publishable by construction).
- Never `git add -f` anything under `.private/`.
- Filtered-export and encrypted-in-repo approaches are rejected alternatives:
  both fail open (a forgotten filter entry publishes; encrypted blobs leak
  names and look odd in a public portfolio repo). The overlay fails closed.
- Preflights in any runner/harness assert `git check-ignore .private/`.

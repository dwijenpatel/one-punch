#!/usr/bin/env python3
"""reviewer_yield — high and medium review findings raised vs. confirmed, per review file.

Raised: `- [high]` / `- [medium]` finding lines in every committed version of
each review file under --reviews (spec-verdict.md, lens.md), across all refs,
each distinct file version counted once.
Confirmed: handoff `Evidence:` lines of the form
`fixed <review file> <file:line> — test <id> (red on <sha>, green on head)`
in every committed version of the handoffs under --handoffs, each distinct
line counted once.

Usage: reviewer_yield.py --repo DIR --reviews .scratch/<effort>/reviews --handoffs .scratch/<effort>/handoffs
"""

import argparse
import re
import subprocess
import sys
from collections import Counter

FINDING = re.compile(r"^\s*-\s*\[(high|medium)\]", re.MULTILINE | re.IGNORECASE)
CONFIRMED = re.compile(r"\bfixed\s+(spec-verdict\.md|lens\.md)\s+\S+.*\bred on\b.*\bgreen on\b", re.IGNORECASE)
ROLES = ("spec-verdict.md", "lens.md")


def git(repo: str, *args: str) -> str:
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout


def blobs(repo: str, path: str) -> dict[str, str]:
    """Every distinct blob ever committed under `path` (any ref), mapped to its file path."""
    found: dict[str, str] = {}
    for commit in git(repo, "log", "--all", "--format=%H", "--", path).split():
        for line in git(repo, "ls-tree", "-r", commit, "--", path).splitlines():
            meta, name = line.split("\t", 1)
            found.setdefault(meta.split()[2], name)
    return found


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--reviews", required=True)
    ap.add_argument("--handoffs", required=True)
    a = ap.parse_args(argv)
    raised: Counter[tuple[str, str]] = Counter()
    for blob, name in blobs(a.repo, a.reviews).items():
        role = name.rsplit("/", 1)[-1]
        if role in ROLES:
            for sev in FINDING.findall(git(a.repo, "cat-file", "-p", blob)):
                raised[(role, sev.lower())] += 1
    confirmed: Counter[str] = Counter()
    lines: set[str] = set()
    for blob in blobs(a.repo, a.handoffs):
        lines |= {ln.strip() for ln in git(a.repo, "cat-file", "-p", blob).splitlines() if CONFIRMED.search(ln)}
    for ln in lines:
        match = CONFIRMED.search(ln)
        assert match is not None
        confirmed[match.group(1).lower()] += 1
    print("review file | high raised | medium raised | confirmed | yield")
    for role in ROLES:
        total = raised[(role, "high")] + raised[(role, "medium")]
        share = f"{confirmed[role] / total:.0%}" if total else "n/a"
        print(f"{role} | {raised[(role, 'high')]} | {raised[(role, 'medium')]} | {confirmed[role]} | {share}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

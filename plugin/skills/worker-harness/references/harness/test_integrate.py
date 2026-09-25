"""End-to-end tests for integrate.py on throwaway git repositories: clean
fast-forward, rebase conflict, BLAST-ESCALATION, B3 hold and approval,
head moved mid-check, the single-writer lock, and refusals. The pure checks
have their own unit tests in checks/test_checks.py.
Run from the harness directory: python -m unittest -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest import mock

import integrate

HERE = Path(__file__).resolve().parent
EFFORT = "demo"
INTEG = f"integrate/{EFFORT}"

BLAST_MAP = """# Blast map

```toml blast-map
schema = 1
pattern_skip = ["**/*.md"]

[[zone]]
name = "auth-sessions"
level = "B3"
checklist = "auth-sessions"
why = "Authentication fails open silently."
paths = ["src/auth/**"]

[[zone]]
name = "process-rules"
level = "B3"
protected = true
why = "Rule surfaces steer every later change."
paths = ["**/AGENTS.md", "docs/blast-map.md", "docs/decisions.md", "harness.toml"]
```
"""

LEDGER = """| ID | Decision | Rationale | Owner | Status | ADR |
|---|---|---|---|---|---|
| D-001 | KV store is in-memory | Trial scope | planner | active | |
"""

CHECKLIST = "# Auth\n\n- **AS-01** Token not verified. Test: forged token.\n- **AS-02** Session fixation. Test: rotate.\n"

HARNESS_TOML = """[integrate]
effort = "demo"
verify = ["test -f src/app.py"]
checklists_dir = "docs/checklists"
"""

TICKET = """# {id} — {title}

Status: ready-for-agent
Tag: {tag}
Blast: {blast} — {title}
Size: low
Touches: {touches}
"""


@contextmanager
def isolated_git() -> Iterator[None]:
    """No operator git config (hooks, signing, rebase defaults) leaks in."""
    env = {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }
    with mock.patch.dict(os.environ, env):
        yield


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.pending: list[str] = []
        self.git("init", "-q", "-b", "main")
        self.git("config", "commit.gpgsign", "false")
        self.write("src/app.py", "print('app')\n")
        self.write("docs/blast-map.md", BLAST_MAP)
        self.write("docs/decisions.md", LEDGER)
        self.write("docs/checklists/checklist-auth-sessions.md", CHECKLIST)
        self.write("harness.toml", HARNESS_TOML)
        self.commit("base")
        self.git("branch", INTEG)

    def git(self, *args: str) -> str:
        proc = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=True)
        return proc.stdout.strip()

    def write(self, path: str, text: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        self.pending.append(path)

    def commit(self, message: str) -> str:
        """Commit exactly the files written since the last commit (never the
        untracked event ledger or review packets)."""
        self.git("add", "--", *self.pending)
        self.pending = []
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def rev(self, ref: str) -> str:
        return self.git("rev-parse", ref)

    def add_ticket(self, tid: str, *, touches: str, blast: str = "B1", tag: str = "code-complete") -> None:
        """Commit the ticket file onto the integration branch (tickets are read from H)."""
        self.git("checkout", "-q", INTEG)
        self.write(f".scratch/{EFFORT}/issues/{tid}-t.md", TICKET.format(id=tid, title=f"ticket {tid}", tag=tag, blast=blast, touches=touches))
        self.commit(f"planner: ticket {tid}")
        self.git("checkout", "-q", "main")

    def work(self, tid: str, commits: list[dict[str, str]], status: str = "DONE") -> None:
        """Cut t/<tid> from the integration head and commit the worker's work plus its handoff."""
        self.git("checkout", "-q", "-b", f"t/{tid}", INTEG)
        for files in commits:
            for path, text in files.items():
                self.write(path, text)
            self.commit(f"ticket {tid}: {', '.join(files)}")
        if status:
            self.write(f".scratch/{EFFORT}/handoffs/{tid}.md", f"Status: {status}\nCommits: …\n")
            self.commit(f"ticket {tid}: handoff")
        self.git("checkout", "-q", "main")

    def land(self, tid: str) -> integrate.IntegrateResult:
        with integrate.writer_lock(self.root):
            return integrate.integrate_ticket(self.root, integrate.load_config(self.root / "harness.toml"), tid)

    def events(self) -> list[dict[str, Any]]:
        return integrate.read_events(self.root / f".scratch/{EFFORT}/events.jsonl")


@contextmanager
def repo() -> Iterator[Repo]:
    with isolated_git(), tempfile.TemporaryDirectory(prefix="integrate-e2e-") as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        yield Repo(root.resolve())


def _failures(result: integrate.IntegrateResult) -> list[str]:
    return [f for check in result.event["checks"] for f in check["failures"]]


def test_clean_fast_forward_lands_the_judged_commit() -> None:
    with repo() as r:
        r.add_ticket("01", touches="src/store/**")
        r.work("01", [{"src/store/kv.py": "STORE = {}  # D-001\n"}])
        head = r.rev("t/01")
        result = r.land("01")
        assert result.outcome == "MERGED" and result.exit_code == 0, _failures(result)
        assert r.rev(INTEG) == head == result.event["judged"]
        event = r.events()[-1]
        assert (event["declared_blast"], event["effective_blast"], event["verify"]) == ("B1", "B1", "pass")
        assert event["files"] == [".scratch/demo/handoffs/01.md", "src/store/kv.py"]
        assert event["ticket_branch_moved"] is True
        assert r.git("worktree", "list").count("\n") == 0  # the throwaway worktree is gone


def test_rebase_conflict_emits_conflict_naming_the_other_ticket() -> None:
    with repo() as r:
        r.add_ticket("02", touches="src/**")
        r.add_ticket("03", touches="src/**")
        r.work("02", [{"src/app.py": "print('two')\n"}])
        r.work("03", [{"src/app.py": "print('three')\n"}])
        assert r.land("03").outcome == "MERGED"
        before = r.rev(INTEG)
        result = r.land("02")
        assert result.outcome == "CONFLICT" and result.exit_code == 22
        assert result.event["conflicted_paths"] == ["src/app.py"]
        assert result.event["conflict_with"] == ["03"]
        assert r.rev(INTEG) == before
        assert "rebase" not in r.git("status")


def test_under_declared_blast_escalates_and_does_not_merge() -> None:
    with repo() as r:
        r.add_ticket("04", touches="src/auth/**", blast="B1")
        r.work("04", [{"src/auth/login.py": "def login(token): return True\n"}])
        before = r.rev(INTEG)
        result = r.land("04")
        assert result.outcome == "BLAST-ESCALATION" and result.exit_code == 21
        assert any("BLAST-ESCALATION declared B1 effective B3: auth-sessions src/auth/login.py" in f for f in _failures(result))
        assert r.rev(INTEG) == before


def _b3_work(r: Repo, tid: str) -> None:
    review = f".scratch/{EFFORT}/reviews/{tid}"
    r.work(
        tid,
        [
            {"tests/test_login.py": "def test_forged_token_rejected(): ...\n"},
            {"src/auth/login.py": "def login(token): return verify(token)\n"},
            {
                f"{review}/spec-verdict.md": "Missing: none\nVerdict: pass\n",
                f"{review}/lens.md": "Reviewer: other family\nVerdict: pass\n",
                f"{review}/checklist-auth-sessions.md": "AS-01 pass: tests/test_login.py\nAS-02 n/a: no sessions here\n",
            },
        ],
    )


def test_b3_waits_for_the_operator_with_a_review_packet_then_approval_lands_it() -> None:
    with repo() as r:
        r.add_ticket("05", touches="src/auth/**, tests/**", blast="B3", tag="contract")
        _b3_work(r, "05")
        before = r.rev(INTEG)
        result = r.land("05")
        assert result.outcome == "AWAITING-OPERATOR" and result.exit_code == 10, _failures(result)
        assert r.rev(INTEG) == before
        judged = str(result.event["judged"])
        assert r.rev("refs/one-punch/awaiting/05") == judged
        packet = Path(str(result.event["packet"]))
        assert {"README.md", "diff.patch", "lens.md", "checklist-auth-sessions.md", "packet.json", "05.md"} <= {
            p.name for p in packet.iterdir()
        }
        assert "src/auth/login.py" in (packet / "diff.patch").read_text()
        cfg = integrate.load_config(r.root / "harness.toml")
        with integrate.writer_lock(r.root):
            approved = integrate.approve_ticket(r.root, cfg, "05")
        assert approved.outcome == "MERGED" and approved.event["approved"] is True
        assert r.rev(INTEG) == judged
        assert subprocess.run(["git", "rev-parse", "--verify", "--quiet", "refs/one-punch/awaiting/05"], cwd=r.root).returncode != 0


def test_b3_without_tests_first_fails() -> None:
    with repo() as r:
        r.add_ticket("06", touches="src/auth/**, tests/**", blast="B3", tag="contract")
        r.work("06", [{"src/auth/login.py": "x = 1\n", "tests/test_login.py": "def test_x(): ...\n"}])
        result = r.land("06")
        assert result.outcome == "FAILED"
        tokens = {f.split(" ")[0] for f in _failures(result)}
        assert {"SCRUTINY-MISSING", "TESTS-NOT-FIRST", "CHECKLIST-UNANSWERED"} <= tokens


def test_head_moved_mid_check_re_enters_at_rebase() -> None:
    with repo() as r:
        r.add_ticket("07", touches="src/store/**")
        r.work("07", [{"src/store/kv.py": "STORE = {}\n"}])
        r.git("checkout", "-q", INTEG)
        r.write("notes/planner.md", "a planner commit landing mid-check\n")
        moved_to = r.commit("planner: notes")
        r.git("reset", "-q", "--hard", "HEAD~1")
        r.git("checkout", "-q", "main")
        marker = r.root.parent / "moved-once"
        mover = f"test -f {marker} || (touch {marker} && git -C {r.root} update-ref refs/heads/{INTEG} {moved_to})"
        config = HARNESS_TOML.replace('verify = ["test -f src/app.py"]', f"verify = [{json.dumps(mover)}]")
        (r.root / "harness.toml").write_text(config, encoding="utf-8")
        result = r.land("07")
        assert result.outcome == "MERGED", _failures(result)
        assert result.event["reentries"] == 1 and len(result.event["head_moved"]) == 1
        assert r.rev(f"{INTEG}~2") == moved_to  # rebased onto the moved head, then landed
        assert r.git("diff", "--name-only", moved_to, INTEG).split() == [".scratch/demo/handoffs/07.md", "src/store/kv.py"]


def test_writer_lock_refuses_a_second_writer() -> None:
    with repo() as r:
        r.add_ticket("08", touches="src/store/**")
        r.work("08", [{"src/store/kv.py": "STORE = {}\n"}])
        with integrate.writer_lock(r.root):
            proc = subprocess.run(
                [sys.executable, str(HERE / "integrate.py"), "--repo", str(r.root), "08"],
                capture_output=True,
                text=True,
                env=os.environ.copy(),
            )
        assert proc.returncode == integrate.EXIT_LOCKED, proc.stderr
        assert "INTEGRATE-LOCKED" in proc.stderr
        assert r.events() == []
        released = subprocess.run(
            [sys.executable, str(HERE / "integrate.py"), "--repo", str(r.root), "08"], capture_output=True, text=True
        )
        assert released.returncode == 0, released.stdout + released.stderr
        assert released.stdout.startswith("MERGED ticket 08")


LINTER = """import pathlib, sys
code = sys.argv[1]
for path in sorted(pathlib.Path("src").rglob("*.py")):
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if code in line and "allow(" not in line:
            print(f"{path}:{n}:1: {code} marker {code} found")
"""


def test_lint_ratchet_allow_and_soft_warnings_on_real_runs() -> None:
    with repo() as r:
        linter = r.root.parent / "linter.py"
        linter.write_text(LINTER, encoding="utf-8")
        lint = f"{sys.executable} {linter}"
        r.git("checkout", "-q", INTEG)
        r.write("src/legacy.py", "x = 1  # HARD1 grandfathered\n")
        r.commit("brownfield violation")
        r.git("checkout", "-q", "main")
        r.add_ticket("11", touches="src/**")
        r.work("11", [{"src/legacy.py": "x = 1  # HARD1 grandfathered\ny = 2\n", "src/new.py": "a = 1  # HARD1\nb = 2  # SOFT1\n"}])
        config = HARNESS_TOML + f"lint_hard = [{json.dumps(lint + ' HARD1')}]\nlint_soft = [{json.dumps(lint + ' SOFT1')}]\n"
        (r.root / "harness.toml").write_text(config, encoding="utf-8")  # on disk only: the operator's config
        failed = r.land("11")
        assert failed.outcome == "FAILED", (failed.outcome, failed.event["reason"], _failures(failed))
        assert [f for f in _failures(failed) if f.startswith("LINT")] == ["LINT HARD1 src/new.py:1 marker HARD1 found"]
        assert failed.event["warnings"] == ["LINT-WARN SOFT1 src/new.py:2 marker SOFT1 found"]
        r.add_ticket("12", touches="src/**")
        r.work("12", [{"src/new.py": "# allow(HARD1): D-001\na = 1  # HARD1\n"}])
        landed = r.land("12")
        assert landed.outcome == "MERGED", _failures(landed)
        assert landed.event["exceptions"] == ["allow(HARD1): D-001 src/new.py:2"]


def test_refusals_and_failed_hygiene() -> None:
    with repo() as r:
        r.add_ticket("09", touches="src/store/**")
        r.work("09", [{"src/store/kv.py": "x = 1\n"}], status="BLOCKED")
        blocked = r.land("09")
        assert blocked.outcome == "REFUSED" and "HANDOFF-STATUS BLOCKED" in str(blocked.event["reason"])
        r.add_ticket("10", touches="src/store/**")
        r.work("10", [{"src/store/kv.py": "x = 1  # D-777\n", "src/app.py": "print('drive-by')\n"}])
        failed = r.land("10")
        assert failed.outcome == "FAILED" and failed.exit_code == 20
        tokens = {f.split(" ")[0] for f in _failures(failed)}
        assert tokens == {"REF-UNRESOLVED", "TOUCHES-OUTSIDE"}, _failures(failed)
        r.git("checkout", "-q", INTEG)
        r.git("rm", "-q", "docs/blast-map.md")
        r.git("commit", "-q", "-m", "planner: drop map")
        r.git("checkout", "-q", "main")
        missing = r.land("10")
        assert missing.outcome == "REFUSED" and str(missing.event["reason"]).startswith("BLAST-MAP-MISSING")


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None) -> unittest.TestSuite:
    suite = unittest.TestSuite(tests)
    for name, obj in sorted(globals().items()):
        if name.startswith("test_") and callable(obj) and not isinstance(obj, type):
            suite.addTest(unittest.FunctionTestCase(obj, description=name))
    return suite

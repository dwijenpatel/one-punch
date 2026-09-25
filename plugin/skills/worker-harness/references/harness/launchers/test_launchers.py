"""Launcher contract tests for mock.py, mini_p.py and claude_p.py beyond what
test_run.py covers: mock and mini_p forward an operator stop to the worker's
process group, and claude_p and mini_p express no isolation (no walls) — they
refuse any isolation field. codex_p has its own file.

Run: python3 launchers/test_launchers.py   (launchers/ is not a package, so
`python -m unittest` from the harness directory does not collect this file.)
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent

TRAPPING_SCENARIO = """\
trap 'echo term > "$MARK"; exit 143' TERM
echo started > "$MARK.started"
sleep 30 &
wait
"""


def bundle(root: Path, tool: str, isolation: dict[str, Any]) -> Path:
    b = root / "bundle"
    b.mkdir()
    (b / "instructions.md").write_text("do it\n")
    params = {"contract": 1, "role": "author", "worker": {"tool": tool, "model": f"{tool}-model"},
              "isolation": isolation, "cwd": str(root), "timeout_s": 60}
    (b / "params.json").write_text(json.dumps(params))
    return b


class MockLauncher(unittest.TestCase):
    def test_sigterm_is_forwarded_to_the_scenario_group_and_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenario = root / "scenario.sh"
            scenario.write_text(TRAPPING_SCENARIO)
            b = bundle(root, "mock", {})
            env = {**os.environ, "MOCK_SCRIPT": str(scenario), "MARK": str(root / "mark")}
            proc = subprocess.Popen([sys.executable, str(HERE / "mock.py"), str(b)], env=env, start_new_session=True)
            deadline = time.monotonic() + 20
            while not (root / "mark.started").exists():
                self.assertLess(time.monotonic(), deadline)
                time.sleep(0.05)
            os.killpg(proc.pid, signal.SIGTERM)
            self.assertEqual(proc.wait(timeout=20), 1)
            self.assertEqual((root / "mark").read_text().strip(), "term", "the scenario's own group got SIGTERM")
            result = json.loads((b / "result.json").read_text())
            self.assertEqual((result["ok"], result["interrupted"]), (False, True))
            self.assertIn("interrupted by signal", result["error_summary"])


class MiniLauncher(unittest.TestCase):
    def test_isolation_is_refused_and_sigterm_is_forwarded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            walled = bundle(root, "mini", {"sandbox": True})
            refused = subprocess.run([sys.executable, str(HERE / "mini_p.py"), str(walled)], capture_output=True, text=True)
            self.assertEqual(refused.returncode, 2)
            self.assertIn("no isolation", json.loads((walled / "result.json").read_text())["refused_reason"])
            shutil.rmtree(walled)
            fake = root / "bin" / "mini"
            fake.parent.mkdir()
            fake.write_text("#!/bin/sh\n" + TRAPPING_SCENARIO)
            fake.chmod(0o755)
            b = bundle(root, "mini", {})
            env = {**os.environ, "PATH": f"{fake.parent}:{os.environ['PATH']}", "MARK": str(root / "mark")}
            proc = subprocess.Popen([sys.executable, str(HERE / "mini_p.py"), str(b)], env=env, start_new_session=True)
            deadline = time.monotonic() + 20
            while not (root / "mark.started").exists():
                self.assertLess(time.monotonic(), deadline)
                time.sleep(0.05)
            os.killpg(proc.pid, signal.SIGTERM)
            self.assertEqual(proc.wait(timeout=20), 1)
            self.assertEqual((root / "mark").read_text().strip(), "term", "the worker's own group got SIGTERM")
            result = json.loads((b / "result.json").read_text())
            self.assertEqual((result["ok"], result["interrupted"]), (False, True))


class ClaudeLauncherHasNoWalls(unittest.TestCase):
    def run_claude(self, isolation: dict[str, Any]) -> tuple[subprocess.CompletedProcess[str], Path]:
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        b = bundle(Path(tmp), "claude", isolation)
        proc = subprocess.run([sys.executable, str(HERE / "claude_p.py"), "--dry-run", str(b)],
                              capture_output=True, text=True)
        return proc, b

    def test_any_isolation_field_is_refused(self) -> None:
        for isolation in ({"sandbox": True}, {"deny_read": ["/x"]}, {"network": False}):
            proc, b = self.run_claude(isolation)
            self.assertEqual(proc.returncode, 2, isolation)
            reason = json.loads((b / "result.json").read_text())["refused_reason"]
            self.assertIn("does not express", reason)

    def test_empty_isolation_runs_bypass_permissions_with_hygiene_flags_and_no_settings(self) -> None:
        proc, b = self.run_claude({})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        plan = json.loads(proc.stdout)
        argv = plan["argv"]
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "bypassPermissions")
        for flag in ("--strict-mcp-config", "--disable-slash-commands", "--no-session-persistence"):
            self.assertIn(flag, argv)
        self.assertEqual(argv[argv.index("--setting-sources") + 1], "")
        self.assertNotIn("--settings", argv)
        self.assertNotIn("generated_settings", plan)
        self.assertFalse((b / "generated-settings.json").exists())
        self.assertEqual(plan["env_extra"], {"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"})


if __name__ == "__main__":
    unittest.main(verbosity=2)

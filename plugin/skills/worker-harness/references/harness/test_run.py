"""Tests for run.py: the pure loop logic (fold, round planning, handoff and
acceptance grammars, preamble, config), and end-to-end runs against the
mock launcher on throwaway git repositories — a 4-wide batch, overlap
serialized, the K decisions-needed stop, resume from a bare clone and
continuation in a fresh clone, operator stop, and SIGINT mid-run.
Run from the harness directory: python -m unittest -v
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from collections.abc import Iterator
from contextlib import contextmanager, redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any
from unittest import mock

import core
import run
import runcore
from checks.config import ConfigError
from core import Blast, Candidate, Size, Tag, Ticket, Tier
from integrate import Git, integrate_ticket, load_config
from test_integrate import BLAST_MAP, EFFORT, INTEG, Repo, isolated_git

HERE = Path(__file__).resolve().parent
EVENTS = f".scratch/{EFFORT}/events.jsonl"
SNAPSHOT = f".scratch/{EFFORT}/ledger/events.jsonl"

HARNESS_TOML = """[integrate]
effort = "demo"
verify = ["test -f src/app.py"]
checklists_dir = "docs/checklists"

[run]
parallel = {parallel}
park_k = 2
poll_s = 0.05
worker_timeout_s = 120
ladder = {{ T4 = [{{ tool = "mock", model = "mock-small" }}], T3 = [{{ tool = "mock", model = "mock-large" }}], T2 = [{{ tool = "mock", model = "mock-mid" }}] }}
"""

TICKET = """# {id} — ticket {id}

Status: ready-for-agent
Blocked by: {blocked}
Tag: code-complete
Blast: B0 — test ticket
Size: low
Touches: {touches}

Intent: ticket {id}.

Acceptance:
  test -f src/{id}/x.py
"""

# The mock launcher runs this in the worker's worktree. It finds the ticket
# from the branch and the attempt from params.json, then sources the
# scenario `$SCEN/<ticket>-a<attempt>.sh` or `$SCEN/<ticket>.sh`.
DISPATCH = r"""set -e
T=$(git rev-parse --abbrev-ref HEAD); T=${T#t/}
A=$(sed -n 's/.*"attempt": \([0-9]*\).*/\1/p' "$MOCK_BUNDLE/params.json")
work() { mkdir -p "$(dirname "$1")"; printf '%s\n' "$2" > "$1"; git add -- "$1"; git commit -q --allow-empty -m "$T: $1"; }
handoff() {
  mkdir -p .scratch/demo/handoffs
  printf 'Status: %s\nCommits: attempt '"$A"'\nDone: x\nDeviations: none\nDecisions needed: %s\nFindings / concerns: none\n' "$1" "${2:-none}" > .scratch/demo/handoffs/$T.md
  git add -- .scratch/demo/handoffs/$T.md; git commit -qm "$T: handoff"
}
stamp() { python3 -c 'import time; print(time.time())' > "$OUT/$T.$1"; }
S="$SCEN/$T-a$A.sh"; [ -f "$S" ] || S="$SCEN/$T.sh"
. "$S"
"""
DEFAULT_SCENARIO = 'stamp start; work "src/$T/x.py" "x = 1"; handoff DONE; stamp end\n'


class Effort:
    """A throwaway repository with an integration branch, tickets, and mock scenarios."""

    def __init__(self, root: Path, parallel: int = 4) -> None:
        self.root = root
        (root / "repo").mkdir()
        self.repo = Repo(root / "repo")
        self.scen, self.out = root / "scen", root / "out"
        self.scen.mkdir()
        self.out.mkdir()
        (root / "dispatch.sh").write_text(DISPATCH, encoding="utf-8")
        self.repo.git("checkout", "-q", "main")
        self.repo.write("harness.toml", HARNESS_TOML.format(parallel=parallel))
        self.repo.commit("harness: [run] table")
        self.env = {"MOCK_SCRIPT": str(root / "dispatch.sh"), "SCEN": str(self.scen), "OUT": str(self.out)}

    def ticket(self, tid: str, touches: str = "", blocked: str = "—", scenario: str = DEFAULT_SCENARIO) -> None:
        self.repo.git("checkout", "-q", INTEG)
        self.repo.write(f".scratch/{EFFORT}/issues/{tid}-t.md", TICKET.format(id=tid, touches=touches or f"src/{tid}/**", blocked=blocked))
        self.repo.commit(f"planner: ticket {tid}")
        self.repo.git("checkout", "-q", "main")
        self.scenario(tid, scenario)

    def scenario(self, name: str, text: str) -> None:
        (self.scen / f"{name}.sh").write_text(text, encoding="utf-8")

    def main(self, *args: str, repo: Path | None = None) -> tuple[int, str]:
        buf = StringIO()
        with mock.patch.dict(os.environ, self.env), redirect_stdout(buf):
            code = run.main(["--repo", str(repo or self.repo.root), *args])
        return code, buf.getvalue()

    def events(self, repo: Path | None = None) -> list[dict[str, Any]]:
        return [json.loads(line) for line in ((repo or self.repo.root) / EVENTS).read_text().splitlines()]

    def status(self, tid: str, repo: Path | None = None) -> str:
        text = subprocess.run(["git", "show", f"{INTEG}:.scratch/{EFFORT}/issues/{tid}-t.md"], cwd=repo or self.repo.root,
                              capture_output=True, text=True, check=True).stdout
        return core.parse_ticket_header(text, tid).status

    def stamp(self, tid: str, which: str) -> float:
        return float((self.out / f"{tid}.{which}").read_text())


@contextmanager
def effort(parallel: int = 4) -> Iterator[Effort]:
    with tempfile.TemporaryDirectory() as tmp, isolated_git():
        yield Effort(Path(tmp).resolve(), parallel)


def launches(events: list[dict[str, Any]], tid: str) -> list[dict[str, Any]]:
    return [e for e in events if e["event"] == "launch" and e["ticket"] == tid]


# --------------------------------------------------------------------------
# End to end, against the mock launcher
# --------------------------------------------------------------------------


class RunEndToEnd(unittest.TestCase):
    def test_four_wide_batch_with_disjoint_touches(self) -> None:
        barrier = (
            'touch "$OUT/barrier.$T"; i=0\n'
            'while [ "$(ls "$OUT"/barrier.* | wc -l)" -lt 4 ] && [ $i -lt 150 ]; do sleep 0.1; i=$((i+1)); done\n'
            'ls "$OUT"/barrier.* | wc -l | tr -d " " > "$OUT/$T.seen"\n'
        )
        with effort() as fx:
            for tid in ("01", "02", "03", "04"):
                fx.ticket(tid, scenario=barrier + DEFAULT_SCENARIO)
            code, out = fx.main("run")
            self.assertEqual(code, 0, out)
            self.assertIn("FRONTIER-EMPTY", out)
            events = fx.events()
            for tid in ("01", "02", "03", "04"):
                self.assertEqual((fx.out / f"{tid}.seen").read_text().strip(), "4", "all four workers ran at once")
                self.assertEqual(fx.status(tid), "done")
                (launch,) = launches(events, tid)
                self.assertEqual((launch["tool"], launch["model"], launch["tier"]), ("mock", "mock-small", "T4"))
            merges = [e for e in events if e["event"] == "integrate"]
            self.assertEqual([e["outcome"] for e in merges], ["MERGED"] * 4)
            self.assertFalse(any((fx.repo.root / ".worktrees" / t).exists() for t in ("01", "02", "03", "04")))
            snapshot = fx.repo.git("show", f"{INTEG}:{SNAPSHOT}")
            self.assertIn('"reason": "FRONTIER-EMPTY"', snapshot, "the stop commits the ledger")
            params = json.loads(Path(launches(events, "01")[0]["bundle"], "params.json").read_text())
            self.assertEqual(params["worker"], {"tool": "mock", "model": "mock-small"})
            self.assertEqual(params["isolation"], {})

            code, out = fx.main("closure")
            self.assertEqual(code, 0, out)
            self.assertIn("01: ok  test -f src/01/x.py", out)
            fx.repo.git("checkout", "-q", INTEG)
            fx.repo.git("rm", "-q", "src/01/x.py")
            fx.repo.git("commit", "-q", "-m", "a later change breaks ticket 01's promise")
            fx.repo.git("checkout", "-q", "main")
            code, out = fx.main("closure")
            self.assertEqual(code, 1, out)
            self.assertIn("01: FAIL test -f src/01/x.py", out)
            self.assertIn("closure RED", out)

    def test_overlapping_touches_are_serialized(self) -> None:
        slow = 'stamp start; sleep 0.8; work "src/shared/$T.py" "x = 1"; handoff DONE; stamp end\n'
        with effort() as fx:
            fx.ticket("01", touches="src/shared/**", scenario=slow)
            fx.ticket("02", touches="src/shared/**", scenario=slow)
            fx.ticket("03", scenario='stamp start; sleep 0.8; work "src/03/x.py" "x = 1"; handoff DONE; stamp end\n')
            code, out = fx.main("run")
            self.assertEqual(code, 0, out)
            first, second = sorted(("01", "02"), key=lambda t: fx.stamp(t, "start"))
            self.assertGreater(fx.stamp(second, "start"), fx.stamp(first, "end"), "overlapping tickets never co-run")
            self.assertLess(fx.stamp("03", "start"), fx.stamp(first, "end"), "a disjoint ticket runs alongside")
            self.assertEqual([fx.status(t) for t in ("01", "02", "03")], ["done"] * 3)

    def test_stops_on_k_decisions_needed_and_answer_is_an_intervention(self) -> None:
        one_way = 'work "src/$T/x.py" "x = 1"; handoff DONE "- schema key naming — local option: snake_case — NOT reversible"\n'
        with effort() as fx:
            fx.ticket("01", scenario=one_way)
            fx.ticket("02", scenario=one_way)
            fx.ticket("03")
            fx.ticket("04", blocked="01")
            code, out = fx.main("run")
            self.assertEqual(code, 4, out)
            self.assertIn("DECISIONS-NEEDED", out)
            events = fx.events()
            parks = {e["ticket"]: e for e in events if e["event"] == "park"}
            self.assertEqual(sorted(parks), ["01", "02"])
            self.assertTrue(all(p["kind"] == "decision" and "schema key naming" in p["reason"] for p in parks.values()))
            self.assertEqual(fx.status("03"), "done")
            self.assertEqual(launches(events, "04"), [], "a parked ticket's dependents wait")
            self.assertNotIn("src/01/x.py", fx.repo.git("ls-tree", "-r", "--name-only", INTEG), "a parked decision is not merged")
            self.assertTrue((fx.repo.root / ".worktrees" / "01").is_dir(), "the parked ticket's worktree is kept")
            code, out = fx.main("answer", "01", "--note", "snake_case is right; keep it")
            self.assertEqual(code, 0, out)
            report = json.loads(fx.main("resume", "--json")[1])
            self.assertEqual(report["interventions"], 1)
            self.assertEqual([p["ticket"] for p in report["parked"]], ["02"])
            self.assertIn("01", report["frontier"])

    def test_escalation_then_resume_from_a_bare_clone_and_continue_in_a_fresh_clone(self) -> None:
        outside = 'work "docs/stray.md" "stray"; work "src/$T/x.py" "x = 1"; handoff DONE\n'
        with effort() as fx:
            fx.ticket("01")
            fx.ticket("02", scenario=outside)
            fx.ticket("03", blocked="02")
            code, out = fx.main("run")
            self.assertEqual(code, 3, out)
            self.assertIn("ALL-PARKED", out)
            events = fx.events()
            tries = launches(events, "02")
            self.assertEqual([(t["model"], t["tier"]) for t in tries], [("mock-small", "T4"), ("mock-large", "T3")], "a failed attempt retries one tier up")
            retry = Path(tries[1]["bundle"], "instructions.md").read_text()
            self.assertIn("TOUCHES-OUTSIDE", retry, "the retry carries the root-cause note")
            self.assertEqual([e["kind"] for e in events if e["event"] == "park"], ["escalation"])

            bare = fx.root / "clone.git"
            subprocess.run(["git", "clone", "-q", "--bare", str(fx.repo.root), str(bare)], check=True)
            original = json.loads(fx.main("resume", "--json")[1])
            cloned = json.loads(fx.main("resume", "--json", repo=bare)[1])
            for key in ("done", "frontier", "parked", "merged", "interventions"):
                self.assertEqual(cloned[key], original[key], key)
            self.assertEqual(cloned["done"], ["01"])
            self.assertEqual([p["kind"] for p in cloned["parked"]], ["escalation"])

            clone = fx.root / "clone"
            subprocess.run(["git", "clone", "-q", str(fx.repo.root), str(clone)], check=True)
            fx.scenario("02-a3", 'git rm -q docs/stray.md; git commit -qm "$T: drop stray"; work "src/$T/y.py" "y = 1"; handoff DONE\n')
            code, out = fx.main("relaunch", "02", "--note", "stay inside Touches", repo=clone)
            self.assertEqual(code, 0, out)
            code, out = fx.main("run", repo=clone)
            self.assertEqual(code, 0, out)
            self.assertEqual([fx.status(t, clone) for t in ("01", "02", "03")], ["done"] * 3)
            relaunched = launches(fx.events(clone), "02")[-1]
            self.assertEqual((relaunched["launch"], relaunched["model"], relaunched["failures"]), (3, "mock-small", 0))
            self.assertIn("stay inside Touches", Path(relaunched["bundle"], "instructions.md").read_text())

    def test_blast_escalation_raises_the_ticket_and_retries_in_place(self) -> None:
        core_zone = '\n[[zone]]\nname = "shared-core"\nlevel = "B2"\nwhy = "Shared core."\npaths = ["src/core/**"]\n'
        with effort() as fx:
            fx.repo.git("checkout", "-q", INTEG)
            fx.repo.write("docs/blast-map.md", BLAST_MAP.replace('paths = ["src/auth/**"]\n', 'paths = ["src/auth/**"]\n' + core_zone))
            fx.repo.commit("planner: shared-core zone (operator OK)")
            fx.repo.git("checkout", "-q", "main")
            fx.ticket("01", touches="src/core/**", scenario='work "src/core/x.py" "x = 1"; handoff DONE\n')
            fx.scenario("01-a2", 'mkdir -p .scratch/demo/reviews/01; work .scratch/demo/reviews/01/spec-verdict.md "Verdict: pass"; handoff DONE\n')
            code, out = fx.main("run")
            self.assertEqual(code, 0, out)
            events = fx.events()
            self.assertEqual([e["outcome"] for e in events if e["event"] == "integrate"], ["BLAST-ESCALATION", "MERGED"])
            ticket = fx.repo.git("show", f"{INTEG}:.scratch/{EFFORT}/issues/01-t.md")
            self.assertIn("Blast: B2 — raised from B0 by the integrate blast detector", ticket)
            self.assertEqual([(t["tier"], t["failures"]) for t in launches(events, "01")], [("T4", 0), ("T2", 0)], "re-routed at the raised floor; not a failure")
            self.assertEqual(fx.status("01"), "done")

    def test_stop_file_drains_and_stops(self) -> None:
        with effort(parallel=1) as fx:
            fx.ticket("01", scenario='touch ../STOP; ' + DEFAULT_SCENARIO)
            fx.ticket("02")
            code, out = fx.main("run")
            self.assertEqual(code, 6, out)
            self.assertEqual(fx.status("01"), "done", "the in-flight worker drains and lands")
            self.assertEqual(launches(fx.events(), "02"), [])

    def start_run(self, fx: Effort, tid: str) -> subprocess.Popen[str]:
        """`run.py run` as a process, returned once it has launched `tid`."""
        proc = subprocess.Popen([sys.executable, str(HERE / "run.py"), "--repo", str(fx.repo.root), "run"], env={**os.environ, **fx.env},
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        deadline = time.monotonic() + 20
        while not ((fx.repo.root / EVENTS).is_file() and launches(fx.events(), tid)):
            self.assertLess(time.monotonic(), deadline, f"the run never launched {tid}")
            time.sleep(0.05)
        return proc

    def test_one_sigint_drains_in_flight_work_and_stops(self) -> None:
        with effort(parallel=1) as fx:
            fx.ticket("01", scenario="sleep 1.5; " + DEFAULT_SCENARIO)
            fx.ticket("02")
            proc = self.start_run(fx, "01")
            proc.send_signal(signal.SIGINT)
            out, err = proc.communicate(timeout=60)
            self.assertEqual(proc.returncode, 6, out + err)
            self.assertEqual(fx.status("01"), "done", "the in-flight worker finishes and lands")
            self.assertEqual(launches(fx.events(), "02"), [], "nothing new launches after the stop")
            self.assertEqual(fx.events()[-1]["reason"], "STOPPED")

    def test_a_merge_landed_outside_the_run_is_flipped_done(self) -> None:
        with effort() as fx:
            fx.ticket("01")
            fx.repo.work("01", [{"src/01/x.py": "x = 1\n"}])
            cfg = load_config(fx.repo.root / "harness.toml")
            self.assertEqual(integrate_ticket(fx.repo.root, cfg, "01").outcome, "MERGED")
            self.assertEqual(fx.status("01"), "ready-for-agent")
            code, out = fx.main("run")
            self.assertEqual(code, 0, out)
            self.assertEqual(fx.status("01"), "done")
            self.assertEqual(launches(fx.events(), "01"), [])

    def test_sigint_mid_run_leaves_a_resumable_ledger(self) -> None:
        with effort(parallel=1) as fx:
            fx.ticket("01", scenario="sleep 4; exit 1\n")
            fx.ticket("02")
            proc = self.start_run(fx, "01")
            proc.send_signal(signal.SIGINT)
            time.sleep(0.3)
            proc.send_signal(signal.SIGINT)
            out, err = proc.communicate(timeout=30)
            self.assertEqual(proc.returncode, 7, out + err)
            events = fx.events()
            self.assertEqual([e["event"] for e in events if e.get("ticket") == "01"], ["launch"], "the launch stays unmatched")
            self.assertEqual(events[-1]["reason"], "KILLED")
            report = json.loads(fx.main("resume", "--json")[1])
            self.assertEqual([x["ticket"] for x in report["in_flight"]], ["01"])
            self.assertIn("interrupted", report["in_flight"][0]["state"])

            fx.scenario("01", DEFAULT_SCENARIO)
            code, out = fx.main("run")
            self.assertEqual(code, 0, out)
            events = fx.events()
            self.assertIn({"ticket": "01", "launch": 1}, [{"ticket": e["ticket"], "launch": e["launch"]} for e in events if e["event"] == "teardown"])
            self.assertEqual([t["failures"] for t in launches(events, "01")], [0, 0], "an interruption is not a failed attempt")
            self.assertEqual([fx.status(t) for t in ("01", "02")], ["done", "done"])


# --------------------------------------------------------------------------
# Pure logic
# --------------------------------------------------------------------------


def T(tid: str, touches: str = "", *, blast: Blast = Blast.B0, attempts: int = 0, blocked: tuple[str, ...] = (), status: str = "ready-for-agent") -> Ticket:
    return Ticket(tid, tid, Tag.CODE_COMPLETE, Size.LOW, blocked, status, attempts, blast=blast, touches=(touches or f"src/{tid}/**",))


SMALL, LARGE = Candidate("mock", "mock-small", ""), Candidate("mock", "mock-large", "")
LADDER = {Tier.T4: (SMALL,), Tier.T3: (LARGE,)}
EMPTY_MAP = core.BlastMap(zones=())


def ev(event: str, tid: str, **fields: Any) -> dict[str, Any]:
    return {"event": event, "ticket": tid, "t": 1.0, "tool": "mock", "model": "mock-small", "effort": "", **fields}


class Grammars(unittest.TestCase):
    def test_decision_items(self) -> None:
        self.assertEqual(runcore.decision_items("Status: DONE\nDecisions needed: none\nFindings / concerns: x\n"), [])
        items = runcore.decision_items(
            "Decisions needed (question → local option → reversibility):\n"
            "1. Tag mapping? I chose contract.\n   Reversible with one line.\n"
            "2. Schema key — local option: snake — NOT reversible\n"
            "- Wire format — one-way door\n"
            "- Retry count — local option: 3\n"
            "Findings / concerns:\n- irrelevant reversible\n"
        )
        self.assertEqual([r for _, r in items], [True, False, False, False], "unmarked fails closed")
        self.assertIn("Reversible with one line", items[0][0])
        self.assertEqual(runcore.decision_items("Decisions needed: pick X — reversible\n"), [("pick X — reversible", True)])
        self.assertEqual(runcore.decision_items("Decisions needed: it is irreversible\n")[0][1], False)
        self.assertEqual(runcore.decision_items("Decisions needed: key names — not locally reversible\n")[0][1], False)
        self.assertEqual(runcore.decision_items("Decisions needed: X — NOT reversible\n")[0][1], False)

    def test_acceptance_commands(self) -> None:
        ticket = "# 07\n\nStatus: done\n\nAcceptance:\n  python -m pytest a -q\n  # comment\n  test -f b\n\nExample: prose\n"
        self.assertEqual(runcore.acceptance_commands(ticket), ["python -m pytest a -q", "test -f b"])
        fenced = "## Acceptance\n\nRun these:\n\n```sh\nrg -q x f\ntest -f g\n```\n\n## Comments\n```\nnot me\n```\n"
        self.assertEqual(runcore.acceptance_commands(fenced), ["rg -q x f", "test -f g"])
        self.assertEqual(runcore.acceptance_commands("Acceptance: integration tests pass.\n\nMore prose.\n"), [])

    def test_set_header_replaces_or_inserts(self) -> None:
        text = "# 01\n\nStatus: ready-for-agent\nTag: contract\n\nStatus: body line\n"
        self.assertEqual(runcore.set_header(text, "Status", "done"), text.replace("ready-for-agent", "done"))
        self.assertIn("Status: ready-for-agent\nBlast: B2 — raised\nTag", runcore.set_header(text, "Blast", "B2 — raised"))

    def test_is_limit(self) -> None:
        self.assertTrue(runcore.is_limit("Claude AI usage limit reached|1759", runcore.DEFAULT_LIMIT_PATTERNS))
        self.assertFalse(runcore.is_limit("AssertionError: 2 != 3", runcore.DEFAULT_LIMIT_PATTERNS))


class Fold(unittest.TestCase):
    def test_failures_escalate_and_relaunch_resets(self) -> None:
        events = [
            ev("launch", "01", start="s1", bundle="b1"),
            ev("worker-exit", "01", ok=False, summary="boom"),
            ev("launch", "01", start="s1", bundle="b2"),
            ev("worker-exit", "01", ok=True),
            {"event": "integrate", "ticket": "01", "outcome": "FAILED", "checks": [{"failures": ["TOUCHES-OUTSIDE docs/x"]}], "ts": "2026-09-25T00:00:00Z"},
        ]
        s = runcore.fold_ledger(events).states["01"]
        self.assertEqual((s.phase, s.failures, s.launches), ("idle", 2, 2))
        self.assertIn("TOUCHES-OUTSIDE", s.last_failure)
        s = runcore.fold_ledger([*events, ev("intervention", "01", kind="relaunch", note="n")]).states["01"]
        self.assertEqual((s.phase, s.failures, s.notes), ("idle", 0, ["n"]))
        self.assertEqual([o.ok for o in runcore.fold_ledger(events).core_events if isinstance(o, core.Outcome)], [False, False])

    def test_limit_exit_cools_without_failing(self) -> None:
        ledger = runcore.fold_ledger([ev("launch", "01"), ev("worker-exit", "01", ok=False, limit=True, retry_at=99.0)])
        self.assertEqual((ledger.states["01"].phase, ledger.states["01"].failures), ("idle", 0))
        self.assertEqual(core.fold(ledger.core_events)[1].cooling_until(SMALL), 99.0)

    def test_integrate_outcomes(self) -> None:
        def after(outcome: str, **extra: Any) -> runcore.TicketState:
            return runcore.fold_ledger([ev("launch", "01"), ev("worker-exit", "01", ok=True), {"event": "integrate", "ticket": "01", "outcome": outcome, **extra}]).states["01"]

        self.assertEqual(after("CONFLICT").park_kind, "conflict")
        self.assertEqual(after("HEAD-MOVED").phase, "exited")
        self.assertEqual(after("BLAST-ESCALATION", effective_blast="B2").escalated_to, "B2")
        self.assertEqual(after("BLAST-ESCALATION", effective_blast="B3").park_kind, "blast-b3")
        self.assertEqual(after("REFUSED", reason="HANDOFF-STATUS BLOCKED (x)").park_kind, "blocked")
        self.assertEqual(after("REFUSED", reason="HANDOFF-MISSING (x)").failures, 1)
        self.assertEqual(after("AWAITING-OPERATOR", packet="p").phase, "awaiting")
        twice = runcore.fold_ledger([ev("launch", "01"), ev("worker-exit", "01", ok=True)] + [{"event": "integrate", "ticket": "01", "outcome": "HEAD-MOVED"}] * 2)
        self.assertEqual(twice.states["01"].park_kind, "head-moved")
        approved = runcore.fold_ledger([{"event": "integrate", "ticket": "01", "outcome": "MERGED", "approved": True, "judged": "j"}])
        self.assertEqual((approved.merged, approved.interventions, approved.states["01"].phase), (1, 1, "merged"))
        self.assertEqual(runcore.fold_ledger([ev("launch", "01")]).states["01"].phase, "running")


class PlanRound(unittest.TestCase):
    def plan(self, tickets: list[Ticket], events: list[dict[str, Any]] = [], inflight: tuple[str, ...] = (), n: int = 4, now: float = 0.0) -> runcore.Round:
        return runcore.plan_round(tickets, runcore.fold_ledger(events), inflight, n, 2, LADDER, now, EMPTY_MAP, ())

    def test_candidates_disjoint_from_in_flight_tickets(self) -> None:
        tickets = [T("01", "src/a/**"), T("02", "src/a/**"), T("03", "src/b/**")]
        rnd = self.plan(tickets, [ev("launch", "01")], inflight=("01",))
        self.assertEqual([t.id for t, _ in rnd.launch], ["03"])
        self.assertIsNone(rnd.stop)

    def test_slots_and_routing(self) -> None:
        rnd = self.plan([T(f"0{i}") for i in range(1, 6)], n=3)
        self.assertEqual(len(rnd.launch), 3)
        self.assertEqual({r.candidate for _, r in rnd.launch}, {SMALL})
        self.assertEqual(self.plan([T("01", attempts=1)]).launch[0][1].candidate, LARGE)

    def test_stops(self) -> None:
        decision = [ev("launch", t) for t in ("01", "02")] + [ev("park", t, kind="decision", reason="r") for t in ("01", "02")]
        self.assertEqual(self.plan([T("01"), T("02"), T("03")], decision).stop, "DECISIONS-NEEDED")
        self.assertEqual(self.plan([T("01", attempts=2)]).park[0][0], "01")
        self.assertEqual(self.plan([T("01", status="done")]).stop, "FRONTIER-EMPTY")
        parked = [ev("launch", "01"), ev("park", "01", kind="blocked", reason="r")]
        self.assertEqual(self.plan([T("01"), T("02", blocked=("01",))], parked).stop, "ALL-PARKED")
        cooling = [ev("launch", "01"), ev("worker-exit", "01", ok=False, limit=True, retry_at=50.0)]
        cold = runcore.plan_round([T("01")], runcore.fold_ledger(cooling), (), 4, 2, {Tier.T4: (SMALL,)}, 10.0, EMPTY_MAP, ())
        self.assertEqual(cold.stop, "ALL-COOLING")
        self.assertIsNone(self.plan([T("01")], [ev("launch", "01")], inflight=("01",)).stop)
        exited = [ev("launch", "01"), ev("worker-exit", "01", ok=True)]
        self.assertEqual(self.plan([T("01")], exited).stop, "ALL-PARKED", "a pending integrate is never 'milestone done'")

    def test_holds_b3_until_relaunched_and_parks_unroutable(self) -> None:
        self.assertEqual(self.plan([T("01", blast=Blast.B3)]).park, (("01", "b3-path", runcore.B3_HOLD),))
        relaunched = [ev("intervention", "01", kind="relaunch", note="")]
        self.assertEqual(self.plan([T("01", blast=Blast.B3)], relaunched).park[0][1], "unroutable", "the ladder has no T0 rung")
        top = runcore.plan_round([T("01", blast=Blast.B3)], runcore.fold_ledger(relaunched), (), 4, 2, {Tier.T0: (LARGE,)}, 0.0, EMPTY_MAP, ())
        self.assertEqual([r.tier for _, r in top.launch], [Tier.T0])
        self.assertEqual(self.plan([T("01", blast=Blast.B1)]).park[0][1], "unroutable")


class Preamble(unittest.TestCase):
    def build(self, ticket: Ticket, **kw: Any) -> str:
        args: dict[str, Any] = dict(ticket=ticket, ticket_text="# 01 — t\n\nStatus: ready-for-agent\n", branch="t/01", base="a" * 40,
                                    handoff_path=".scratch/demo/handoffs/01.md", verify=["make test"], agents_md=True, field_guide="- trap: X",
                                    depends_rows=[], checklists={}, state=runcore.TicketState())
        return runcore.build_instructions(**{**args, **kw})

    def test_contract_surfaces(self) -> None:
        text = self.build(T("01", "src/a/**", blast=Blast.B1))
        for needle in ("`src/a/**`", "never `git add -A`", "Red → green", "`make test`", "AGENTS.md", "- trap: X",
                       ".scratch/demo/handoffs/01.md", "Decisions needed:", "NOT reversible", "BREAKING(D-NNN)", "never edit your ticket file"):
            self.assertIn(needle.lower(), text.lower(), needle)
        self.assertNotIn("Domain checklists", text)

    def test_b2_carries_checklists_and_depends_on_rows(self) -> None:
        text = self.build(T("01", blast=Blast.B2), checklists={"money": "- **MO-01** rounding"}, depends_rows=["| ID |", "| D-003 | x |"])
        self.assertIn("### money", text)
        self.assertIn("MO-01", text)
        self.assertIn("| D-003 | x |", text)
        self.assertIn("edge and error paths", text)
        b3 = self.build(T("01", blast=Blast.B3))
        self.assertIn("independent agent", b3)
        self.assertIn("No domain-checklist zone", b3)

    def test_retry_note(self) -> None:
        state = runcore.TicketState(launches=1, last_failure="VERIFY-FAILED make test", notes=["use B"])
        text = self.build(T("01"), state=state)
        self.assertIn("VERIFY-FAILED make test", text)
        self.assertIn("Operator note (decided", text)

    def test_depends_rows(self) -> None:
        ledger = "| ID | Decision |\n|---|---|\n| D-001 | a |\n| **D-002** | b |\n"
        self.assertEqual(runcore.depends_rows(ledger, ["D-002"]), ["| ID | Decision |", "|---|---|", "| **D-002** | b |"])
        self.assertEqual(runcore.depends_rows(ledger, []), [])


class Config(unittest.TestCase):
    def parse(self, run_table: dict[str, Any]) -> runcore.RunConfig:
        return runcore.parse_run_config({"run": run_table}, "demo")

    def test_valid_and_defaults(self) -> None:
        rc = self.parse({"ladder": {"T0": [{"tool": "claude", "model": "claude-opus-4-8", "effort": "high"}]}})
        self.assertEqual(rc.ladder, {Tier.T0: (Candidate("claude", "claude-opus-4-8", "high"),)})
        self.assertEqual((rc.parallel, rc.park_k, rc.ledger_snapshot), (4, 2, ".scratch/demo/ledger/events.jsonl"))

    def test_refusals(self) -> None:
        bad: list[dict[str, Any]] = [
            {},
            {"ladder": {"T0": [{"tool": "claude", "model": "claude-fable-5"}]}},
            {"ladder": {"T0": [{"tool": "claude", "model": "FABLE-5.1"}]}},
            {"ladder": {"T0": [{"tool": "claude"}]}},
            {"ladder": {"T0": [{"tool": "nope", "model": "m"}]}},
            {"ladder": {"T9": [{"tool": "claude", "model": "m"}]}},
            {"ladder": {"T0": [{"tool": "claude", "model": "m"}]}, "paralel": 4},
            {"ladder": {"T0": [{"tool": "claude", "model": "m"}]}, "parallel": 0},
        ]
        for table in bad:
            with self.assertRaises(ConfigError, msg=str(table)):
                self.parse(table)


FAKE_CLAUDE = """#!/bin/sh
if [ "$1" = "--version" ]; then echo "fake 0.0"; exit 0; fi
trap 'echo term > "$MARK"; exit 143' TERM
echo started > "$MARK.started"
sleep 30 &
wait
"""


class ClaudeLauncher(unittest.TestCase):
    def bundle(self, root: Path) -> Path:
        bundle = root / "bundle"
        bundle.mkdir()
        (bundle / "instructions.md").write_text("do it\n")
        params = {"contract": 1, "role": "author", "worker": {"tool": "claude", "model": "claude-sonnet-5"}, "isolation": {}, "cwd": str(root), "timeout_s": 60}
        (bundle / "params.json").write_text(json.dumps(params))
        return bundle

    def test_empty_isolation_is_bypass_permissions_with_the_model_named(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = subprocess.run([sys.executable, str(HERE / "launchers" / "claude_p.py"), "--dry-run", str(self.bundle(Path(tmp)))],
                                 capture_output=True, text=True, check=True).stdout
            argv = json.loads(out)["argv"]
            self.assertEqual(argv[argv.index("--permission-mode") + 1], "bypassPermissions")
            self.assertEqual(argv[argv.index("--model") + 1], "claude-sonnet-5")

    def test_sigterm_reaches_the_worker_and_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = root / "bin" / "claude"
            fake.parent.mkdir()
            fake.write_text(FAKE_CLAUDE)
            fake.chmod(0o755)
            bundle = self.bundle(root)
            env = {**os.environ, "PATH": f"{fake.parent}:{os.environ['PATH']}", "MARK": str(root / "mark")}
            proc = subprocess.Popen([sys.executable, str(HERE / "launchers" / "claude_p.py"), str(bundle)], env=env, start_new_session=True)
            deadline = time.monotonic() + 20
            while not (root / "mark.started").exists():
                self.assertLess(time.monotonic(), deadline)
                time.sleep(0.05)
            os.killpg(proc.pid, signal.SIGTERM)
            self.assertEqual(proc.wait(timeout=20), 1)
            self.assertEqual((root / "mark").read_text().strip(), "term", "the worker's own group got SIGTERM")
            result = json.loads((bundle / "result.json").read_text())
            self.assertEqual((result["ok"], result["interrupted"]), (False, True))
            self.assertIn("interrupted by signal", result["error_summary"])


class PlannerCommit(unittest.TestCase):
    def test_commits_without_checkout_and_retries_a_lost_race(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, isolated_git():
            repo = Repo(Path(tmp))
            git = Git(repo.root)
            moved: list[str] = []

            def edit(base: str) -> dict[str, str]:
                if not moved:  # a planner edit lands between our read and our swap
                    repo.git("checkout", "-q", INTEG)
                    repo.write("docs/other.md", "x\n")
                    moved.append(repo.commit("planner: other"))
                    repo.git("checkout", "-q", "main")
                return {"docs/note.md": "note\n"}

            commit = run.planner_commit(git, f"refs/heads/{INTEG}", edit, "harness: note")
            self.assertEqual(repo.rev(INTEG), commit)
            self.assertEqual(repo.git("rev-parse", f"{commit}^"), moved[0])
            self.assertEqual(repo.git("show", f"{INTEG}:docs/note.md"), "note")
            self.assertEqual(repo.git("rev-parse", "--abbrev-ref", "HEAD"), "main", "nothing was checked out")
            self.assertIsNone(run.planner_commit(git, f"refs/heads/{INTEG}", lambda _: {"docs/note.md": "note\n"}, "noop"))


if __name__ == "__main__":
    unittest.main()

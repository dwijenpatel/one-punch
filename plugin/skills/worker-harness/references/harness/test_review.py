"""Tests for the non-author dispatches: review.py's pure core (roles,
models, scopes, readers, instructions, packet), their sequencing in
runcore's fold and round, and end-to-end runs against the mock launcher —
conflict -> merge agent -> re-integrate; a B3 ticket's tests-first commit,
spec verdict, lens and review packet (the lens on the decorrelated
candidate while its smoke passes, on the top rung otherwise); a reviewer
that writes outside its file is rejected; a B3 escalation salvaged into
the B3 path.
Run from the harness directory: python -m unittest -v
"""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from typing import Any

import core
import review
import runcore
from checks.config import ConfigError
from checks.hygiene import Commit
from core import Blast, Candidate, Routed, Size, Tag, Ticket, Tier
from review import LENS, MERGE, SPEC, TEST_AUTHOR, Scope, Side
from test_integrate import CHECKLIST, EFFORT, INTEG
from test_run import Effort, effort, launches

SMALL, MID, OPUS, CODEX = (Candidate("mock", m, "") for m in ("mock-small", "mock-mid", "mock-opus", "codex-mock"))
LADDER = {Tier.T4: (SMALL,), Tier.T2: (MID,), Tier.T0: (OPUS,)}
ROOT = f".scratch/{EFFORT}/reviews/01"
LENS_OK = f"""put {ROOT}/lens.md "Verdict: pass"
printf 'AS-01 pass: src/auth/test_login.py::test_forged\\nAS-02 n/a: no sessions in this change\\n' > {ROOT}/checklist-auth-sessions.md
"""
SPEC_OK = f'put {ROOT}/spec-verdict.md "Verdict: pass"\n'
TESTS_OK = 'put src/auth/test_login.py "def test_forged(): assert False"\n'
AUTH_WORK = 'work src/auth/login.py "def login(): return True"; handoff DONE\n'


def T(tid: str = "01", *, blast: Blast = Blast.B0, tag: Tag = Tag.CODE_COMPLETE, touches: str = "src/auth/**") -> Ticket:
    return Ticket(tid, tid, tag, Size.LOW, (), "ready-for-agent", 0, blast=blast, touches=(touches,))


def ev(event: str, tid: str = "01", **fields: Any) -> dict[str, Any]:
    return {"event": event, "ticket": tid, "t": 1.0, "tool": "mock", "model": "mock-opus", "effort": "", **fields}


def usable(_: Candidate) -> bool:
    return True


# --------------------------------------------------------------------------
# Pure core
# --------------------------------------------------------------------------


class Roles(unittest.TestCase):
    def test_next_role_follows_the_ladder(self) -> None:
        b3, b2, contract, b1, b0 = T(blast=Blast.B3), T(blast=Blast.B2), T(blast=Blast.B1, tag=Tag.CONTRACT), T(blast=Blast.B1), T()
        self.assertEqual(review.next_role(b3, "idle", False, {}), TEST_AUTHOR, "B3: tests before the implementer")
        self.assertEqual(review.next_role(b3, "idle", True, {}), "author")
        self.assertEqual(review.next_role(b3, "exited", True, {}), SPEC)
        self.assertEqual(review.next_role(b3, "exited", True, {SPEC: "pass"}), LENS)
        self.assertIsNone(review.next_role(b3, "exited", True, {SPEC: "concerns", LENS: "pass"}), "integrate next")
        self.assertIsNone(review.next_role(b3, "exited", True, {SPEC: "fail"}), "a failed spec verdict skips the lens")
        self.assertEqual(review.next_role(b2, "exited", False, {}), SPEC)
        self.assertEqual(review.next_role(contract, "exited", False, {}), SPEC)
        self.assertIsNone(review.next_role(b1, "exited", False, {}))
        self.assertEqual(review.next_role(b0, "idle", False, {}), "author")
        self.assertEqual(review.next_role(b0, "conflict", False, {}), MERGE)
        self.assertIsNone(review.next_role(b0, "parked", False, {}))
        self.assertEqual(review.rereview_after_merge(b3), (SPEC, LENS))
        self.assertEqual(review.rereview_after_merge(b2), ())

    def test_every_dispatch_names_its_model(self) -> None:
        b0, b3 = T(), T("02", blast=Blast.B3)
        self.assertEqual(review.stage_candidate(MERGE, b0, [], LADDER, None, usable), Routed(MID, Tier.T2, False, False))
        self.assertEqual(review.stage_candidate(MERGE, b0, [b3], LADDER, None, usable).candidate, OPUS, "Opus if either side is B3")  # type: ignore[union-attr]
        self.assertEqual(review.stage_candidate(MERGE, b3, [], LADDER, None, usable).candidate, OPUS)  # type: ignore[union-attr]
        self.assertEqual(review.stage_candidate(TEST_AUTHOR, b3, [], LADDER, None, usable).candidate, OPUS)  # type: ignore[union-attr]
        self.assertEqual(review.stage_candidate(LENS, b3, [], LADDER, CODEX, usable).candidate, CODEX)  # type: ignore[union-attr]
        self.assertEqual(review.stage_candidate(LENS, b3, [], LADDER, None, usable).candidate, OPUS, "fallback: a fresh top-rung reviewer")  # type: ignore[union-attr]
        self.assertEqual(review.stage_candidate(LENS, b3, [], LADDER, CODEX, lambda c: c != CODEX).candidate, OPUS, "a cooling lens falls back")  # type: ignore[union-attr]
        self.assertEqual(review.stage_candidate(SPEC, T(blast=Blast.B2), [], LADDER, None, usable).candidate, MID)  # type: ignore[union-attr]
        self.assertEqual(review.stage_candidate(MERGE, b0, [], {Tier.T0: (OPUS,)}, None, usable).candidate, OPUS, "climbs toward T0")  # type: ignore[union-attr]
        self.assertIsNone(review.stage_candidate(MERGE, b0, [], {Tier.T4: (SMALL,)}, None, usable), "never descends")
        self.assertIsNone(review.stage_candidate(MERGE, b0, [], LADDER, None, lambda _: False))

    def test_isolation(self) -> None:
        self.assertEqual(review.isolation_for(Candidate("codex", "gpt-5.6-sol", "")), {"sandbox": True, "network": True})
        self.assertEqual(review.isolation_for(OPUS), {})


class Readers(unittest.TestCase):
    def test_keep_scopes_each_role(self) -> None:
        spec = Scope(committed=(), modified=(), untracked=(f"{ROOT}/spec-verdict.md", "notes.txt", "__pycache__/x.pyc"))
        self.assertEqual(review.keep(SPEC, spec, ROOT, (), (), ("src/**",)), ((f"{ROOT}/spec-verdict.md",), []), "untracked junk is left behind")
        edited = Scope(committed=(), modified=("src/auth/login.py",), untracked=(f"{ROOT}/spec-verdict.md",))
        kept, bad = review.keep(SPEC, edited, ROOT, (), (), ("src/**",))
        self.assertEqual(bad, ["spec_verdict changed src/auth/login.py (outside what it may write)"])
        lens = Scope(committed=(f"{ROOT}/lens.md",), modified=(), untracked=(f"{ROOT}/checklist-money.md", f"{ROOT}/checklist-other.md"))
        self.assertEqual(review.keep(LENS, lens, ROOT, ("money",), (), ())[0], (f"{ROOT}/checklist-money.md", f"{ROOT}/lens.md"))
        tests = Scope(committed=(), modified=(), untracked=("src/auth/test_login.py", "tests/test_elsewhere.py", "src/auth/login.py"))
        kept, bad = review.keep(TEST_AUTHOR, tests, ROOT, (), ("**/test_*.py",), ("src/auth/**",))
        self.assertEqual((kept, bad), (("src/auth/test_login.py",), []), "only test files inside Touches are committed")
        kept, bad = review.keep(TEST_AUTHOR, Scope(("src/auth/login.py",), (), ()), ROOT, (), ("**/test_*.py",), ("src/auth/**",))
        self.assertEqual(len(bad), 1, "an implementation committed by the test author rejects it")

    def test_stage_problems(self) -> None:
        self.assertEqual(review.stage_problems(TEST_AUTHOR, {}, ROOT, {}), ["test_author wrote no test file matching test_globs"])
        self.assertIn("spec-verdict.md missing", review.stage_problems(SPEC, {f"{ROOT}/spec-verdict.md": "looks fine"}, ROOT, {})[0])
        self.assertEqual(review.stage_problems(SPEC, {f"{ROOT}/spec-verdict.md": "Verdict: FAIL\n"}, ROOT, {}), [])
        lens = {f"{ROOT}/lens.md": "Verdict: concerns\n", f"{ROOT}/checklist-auth-sessions.md": "AS-01 fail: forged token accepted\nAS-02 n/a: none\n"}
        self.assertEqual(review.stage_problems(LENS, lens, ROOT, {"auth-sessions": CHECKLIST}), [], "a fail answer is a finding, not a bad review")
        lens[f"{ROOT}/checklist-auth-sessions.md"] = "AS-01 pass: t\n"
        self.assertEqual(review.stage_problems(LENS, lens, ROOT, {"auth-sessions": CHECKLIST}), ["checklist-auth-sessions.md: AS-02 unanswered"])
        self.assertEqual(review.stage_problems(LENS, {f"{ROOT}/lens.md": "Verdict: pass"}, ROOT, {"money": None}), ["checklist-money.md missing"])
        self.assertEqual(review.read_verdict("# Lens\nVerdict: Concerns — two"), "concerns")
        self.assertIsNone(review.read_verdict(None))


class Instructions(unittest.TestCase):
    def test_lens_sees_codebase_ticket_and_diff_only(self) -> None:
        text = review.build_lens_instructions(ticket=T(blast=Blast.B3), ticket_text="# 01\n\nIntent: sessions.", base="b" * 40,
                                              files=["src/auth/login.py"], review_root=ROOT, checklists={"auth-sessions": CHECKLIST})
        for needle in (f"git diff {'b' * 40}...HEAD", "`src/auth/login.py`", f"{ROOT}/lens.md", f"{ROOT}/checklist-auth-sessions.md",
                       "**AS-01**", "`<ID> pass:", "Verdict: pass", "read-only", "Intent: sessions."):
            self.assertIn(needle, text)
        self.assertNotIn("handoff", text.lower(), "never the implementer's account or transcript")

    def test_spec_asks_missing_extra_misunderstood(self) -> None:
        text = review.build_spec_instructions(ticket=T(blast=Blast.B2), ticket_text="# 01", base="b" * 40, files=["a.py"],
                                              handoff_path=".scratch/demo/handoffs/01.md", review_root=ROOT)
        for needle in ("**Missing**", "**Extra**", "**Misunderstood**", f"{ROOT}/spec-verdict.md", "Verdict: fail", "never evidence"):
            self.assertIn(needle, text)

    def test_test_author_writes_tests_only_from_ticket_and_checklist(self) -> None:
        text = review.build_test_author_instructions(ticket=T(blast=Blast.B3), ticket_text="# 01\n\nIntent: x.", test_globs=["**/test_*.py"],
                                                     verify=["make test"], checklists={"auth-sessions": CHECKLIST}, agents_md=True)
        for needle in ("BEFORE anyone implements", "`**/test_*.py`", "`src/auth/**`", "Never write implementation", "**AS-02**",
                       "Do not commit", "Intent: x.", "AGENTS.md"):
            self.assertIn(needle, text)

    def test_merge_carries_the_discipline_both_tickets_and_the_rebase(self) -> None:
        text = review.build_merge_instructions(
            ticket=T(), this=Side("01", "# 01 — mine", "Status: DONE\nDone: a"), partners=[Side("03", "# 03 — theirs", "Status: DONE\nDone: b")],
            onto="c" * 40, conflicted=["src/x.py"], depends_rows=["| ID |", "| D-004 | y |"], verify=["make test"])
        for needle in ("resolving-merge-conflicts", f"git rebase {'c' * 40}", "never `git rebase --abort`", "GIT_EDITOR=true git rebase --continue",
                       "never `git merge`", "favor neither side", "# 01 — mine", "# 03 — theirs", "Done: b", "| D-004 | y |", "`src/x.py`", "`make test`"):
            self.assertIn(needle, text)

    def test_packet_readme_tags_the_commit_order(self) -> None:
        commits = [Commit("a" * 40, ("src/auth/test_login.py",)), Commit("b" * 40, ("src/auth/login.py",)), Commit("c" * 40, (f"{ROOT}/lens.md",))]
        text = review.packet_readme(ticket="01", event={"base": "h", "judged": "j", "declared_blast": "B3", "effective_blast": "B3",
                                                        "checklists": ["auth-sessions"], "hits": [], "warnings": []},
                                    reviews={"spec-verdict.md": "Verdict: pass", "lens.md": "Verdict: concerns",
                                             "checklist-auth-sessions.md": "AS-01 pass: t\nAS-02 n/a: none\n"},
                                    commits=commits, test_globs=["**/test_*.py"], evidence_globs=[f"{ROOT}/**"], awaiting_ref="refs/x")
        self.assertIn(f"- {'a' * 12} [tests] src/auth/test_login.py\n- {'b' * 12} [work] src/auth/login.py\n- {'c' * 12} [evidence]", text)
        for needle in ("- spec verdict: pass", "- lens: concerns", "- checklist-auth-sessions.md: 1 n/a, 1 pass", "integrate.py --approve 01"):
            self.assertIn(needle, text)


class Sequencing(unittest.TestCase):
    """The fold and the round drive the stages (runcore)."""

    def test_fold_through_the_b3_path(self) -> None:
        events = [ev("launch", role=TEST_AUTHOR, salvage="s0"), ev("worker-exit", role=TEST_AUTHOR, ok=True)]
        self.assertEqual(runcore.fold_ledger(events).states["01"].phase, "pending", "the harness accepts it next")
        events.append(ev("stage", role=TEST_AUTHOR, ok=True, commit="t1"))
        s = runcore.fold_ledger(events).states["01"]
        self.assertEqual((s.phase, s.tests, s.salvage, s.launches), ("idle", "t1", "s0", 0), "a stage is not an implementer launch")
        events += [ev("launch", bundle="a1"), ev("worker-exit", ok=True), ev("launch", role=SPEC), ev("worker-exit", role=SPEC, ok=True),
                   ev("stage", role=SPEC, ok=True, verdict="pass"), ev("launch", role=LENS, checklists=["money"])]
        s = runcore.fold_ledger(events).states["01"]
        self.assertEqual((s.phase, s.role, s.reviewed, s.checklists, s.author_bundle, s.launches), ("running", LENS, {SPEC: "pass"}, ("money",), "a1", 1))
        torn = runcore.fold_ledger([*events, ev("teardown", role=LENS)]).states["01"]
        self.assertEqual(torn.phase, "exited", "an interrupted lens runs again, not the implementer")

    def test_rejections_retry_then_park_and_relaunch_resumes_the_stage(self) -> None:
        events = [ev("launch"), ev("worker-exit", ok=True)]
        for _ in range(2):
            events += [ev("launch", role=SPEC), ev("worker-exit", role=SPEC, ok=True), ev("stage", role=SPEC, ok=False, reason="edited src")]
            if len(events) == 5:
                self.assertEqual(runcore.fold_ledger(events).states["01"].phase, "exited")
        s = runcore.fold_ledger(events).states["01"]
        self.assertEqual((s.phase, s.park_kind), ("parked", "stage"))
        self.assertIn("edited src", s.park_reason)
        s = runcore.fold_ledger([*events, ev("intervention", kind="relaunch", note="")]).states["01"]
        self.assertEqual((s.phase, s.stage_failures), ("exited", {}))

    def test_merge_reenters_integrate_and_b3_review(self) -> None:
        events = [ev("launch"), ev("worker-exit", ok=True), ev("stage", role=SPEC, ok=True, verdict="pass"), ev("stage", role=LENS, ok=True, verdict="pass"),
                  {"event": "integrate", "ticket": "01", "outcome": "CONFLICT", "conflicted_paths": ["a"], "conflict_with": ["02"]},
                  ev("launch", role=MERGE), ev("worker-exit", role=MERGE, ok=True)]
        events.append(ev("stage", role=MERGE, ok=True, rereview=[SPEC, LENS]))
        s = runcore.fold_ledger(events).states["01"]
        self.assertEqual((s.phase, s.reviewed, s.conflicts), ("exited", {}, 1))
        failed = runcore.fold_ledger([*events[:-1], ev("stage", role=MERGE, ok=False, reason="left a rebase")]).states["01"]
        self.assertEqual(failed.phase, "conflict", "a rejected merge runs again")

    def test_round_finishes_started_tickets_first(self) -> None:
        tickets = [T("01", blast=Blast.B2, touches="src/a/**"), T("02", touches="src/a/**"), T("03", touches="src/b/**"), T("04", touches="src/c/**")]
        ledger = runcore.fold_ledger([ev("launch"), ev("worker-exit", ok=True)])
        rnd = runcore.plan_round(tickets, ledger, (), 2, 2, LADDER, 0.0, core.BlastMap(zones=()), ())
        self.assertEqual([(t.id, role, r.candidate.model) for t, r, role in rnd.launch], [("01", SPEC, "mock-mid"), ("03", "author", "mock-small")],
                         "the review takes a slot first; 02 overlaps 01, which still holds its Touches")
        idle = runcore.plan_round(tickets[:1], runcore.fold_ledger([]), (), 2, 2, {Tier.T4: (SMALL,)}, 0.0, core.BlastMap(zones=()), ())
        self.assertEqual(idle.park[0][1], "unroutable")
        exited_b3 = runcore.fold_ledger([ev("launch"), ev("worker-exit", ok=True)])
        rnd = runcore.plan_round([T(blast=Blast.B3)], exited_b3, (), 4, 2, LADDER, 0.0, core.BlastMap(zones=()), (), CODEX)
        self.assertEqual([role for _, _, role in rnd.launch], [SPEC])

    def test_lens_config(self) -> None:
        table: dict[str, Any] = {"ladder": {"T0": [{"tool": "claude", "model": "claude-opus-5"}]}}
        rc = runcore.parse_run_config({"run": {**table, "lens": {"tool": "codex", "model": "gpt-5.6-sol"}, "lens_smoke": "true"}}, "demo")
        self.assertEqual((rc.lens, rc.lens_smoke), (Candidate("codex", "gpt-5.6-sol", ""), "true"))
        self.assertIsNone(runcore.parse_run_config({"run": table}, "demo").lens)
        for bad in ({"lens": {"tool": "codex", "model": "gpt-5.6-sol"}}, {"lens": {"tool": "claude", "model": "claude-fable-5"}, "lens_smoke": "true"}):
            with self.assertRaises(ConfigError, msg=str(bad)):
                runcore.parse_run_config({"run": {**table, **bad}}, "demo")


# --------------------------------------------------------------------------
# End to end, against the mock launcher
# --------------------------------------------------------------------------

PLANNER_EDIT = r"""B=$(git rev-parse refs/heads/integrate/demo)
blob=$(printf 'x = 2\n' | git hash-object -w --stdin)
GIT_INDEX_FILE="$OUT/idx" git read-tree "$B"
GIT_INDEX_FILE="$OUT/idx" git update-index --add --cacheinfo "100644,$blob,src/01/x.py"
tree=$(GIT_INDEX_FILE="$OUT/idx" git write-tree)
git update-ref refs/heads/integrate/demo "$(git commit-tree "$tree" -p "$B" -m 'planner: a conflicting edit')" "$B"
"""
MERGE_AGENT = r"""H=$(sed -n 's/.*`git rebase \([0-9a-f]\{40\}\)`.*/\1/p' "$MOCK_BUNDLE/instructions.md" | head -n 1)
git rebase "$H" >/dev/null 2>&1 || true
printf 'x = 1\nx2 = 2\n' > src/01/x.py; git add src/01/x.py
GIT_EDITOR=true git rebase --continue >/dev/null
"""


def roles(fx: Effort, tid: str = "01") -> list[tuple[str, str]]:
    return [(e["role"], e["model"]) for e in launches(fx.events(), tid)]


class StagesEndToEnd(unittest.TestCase):
    def test_conflict_runs_the_merge_agent_and_reintegrates(self) -> None:
        with effort() as fx:
            fx.ticket("01", scenario=PLANNER_EDIT + 'work src/01/x.py "x = 1"; handoff DONE\n')
            fx.scenario("01-merge", MERGE_AGENT)
            code, out = fx.main("run")
            self.assertEqual(code, 0, out)
            events = fx.events()
            outcomes = [e for e in events if e["event"] == "integrate"]
            self.assertEqual([e["outcome"] for e in outcomes], ["CONFLICT", "MERGED"])
            self.assertEqual(outcomes[0]["conflicted_paths"], ["src/01/x.py"])
            self.assertEqual(roles(fx), [("author", "mock-small"), (MERGE, "mock-mid")], "the merge agent is Sonnet-tier and named")
            bundle = Path(launches(events, "01")[1]["bundle"])
            self.assertIn("resolving-merge-conflicts", (bundle / "instructions.md").read_text())
            self.assertEqual(json.loads((bundle / "params.json").read_text())["role"], MERGE)
            self.assertEqual(fx.repo.git("show", f"{INTEG}:src/01/x.py"), "x = 1\nx2 = 2")
            self.assertEqual(fx.status("01"), "done")
            self.assertFalse((fx.repo.root / ".worktrees" / "01.merge").exists())

    def test_a_merge_agent_that_does_not_rebase_is_rejected_then_parks(self) -> None:
        with effort() as fx:
            fx.ticket("01", scenario=PLANNER_EDIT + 'work src/01/x.py "x = 1"; handoff DONE\n')
            fx.scenario("01-merge-a2", "true\n")
            fx.scenario("01-merge", 'git merge -q --no-edit -s ours refs/heads/integrate/demo\n')
            code, out = fx.main("run")
            self.assertEqual(code, 3, out)
            self.assertIn("[stage] the merge dispatch failed 2 times", out)
            reasons = [e["reason"] for e in fx.events() if e["event"] == "stage"]
            self.assertEqual(len(reasons), 2)
            self.assertIn("is not rebased onto the integration head", reasons[0])
            self.assertIn("merge commits; rebase only", reasons[1])
            self.assertEqual(fx.repo.git("show", f"{INTEG}:src/01/x.py"), "x = 2", "nothing landed")

    def run_b3(self, extra: str) -> tuple[Effort, str]:
        fx = self.enter(extra)
        fx.ticket("01", touches="src/auth/**", blast="B3", scenario=AUTH_WORK)
        for name, text in (("01-test_author", TESTS_OK), ("01-spec_verdict", SPEC_OK), ("01-lens", LENS_OK)):
            fx.scenario(name, text)
        code, out = fx.main("run")
        self.assertEqual(code, 3, out)
        self.assertIn("AWAITING-OPERATOR: 01", out)
        return fx, out

    def enter(self, extra: str = "") -> Effort:
        ctx = effort(extra=extra)
        fx = ctx.__enter__()
        self.addCleanup(ctx.__exit__, None, None, None)
        return fx

    def assert_b3_packet(self, fx: Effort) -> None:
        (awaiting,) = [e for e in fx.events() if e["event"] == "integrate"]
        self.assertEqual(awaiting["outcome"], "AWAITING-OPERATOR", awaiting)
        order = fx.repo.git("log", "--reverse", "--format=%s", f"{awaiting['base']}..{awaiting['judged']}").splitlines()
        self.assertEqual(order[0], "test_author: ticket 01 (mock-opus)", "the independent tests are the first commit")
        self.assertEqual(fx.repo.git("show", "--name-only", "--format=", f"{awaiting['judged']}~{len(order) - 1}"), "src/auth/test_login.py")
        packet = Path(awaiting["packet"])
        self.assertEqual((packet / "lens.md").read_text().strip(), "Verdict: pass")
        readme = (packet / "README.md").read_text()
        for needle in ("[tests] src/auth/test_login.py", "- spec verdict: pass", "- lens: pass", "checklist-auth-sessions.md: 1 n/a, 1 pass"):
            self.assertIn(needle, readme)

    def test_b3_tests_first_then_implementer_spec_lens_and_packet(self) -> None:
        fx, _ = self.run_b3('lens = { tool = "mock", model = "codex-mock" }\nlens_smoke = "true"\n')
        self.assertEqual(roles(fx), [(TEST_AUTHOR, "mock-opus"), ("author", "mock-opus"), (SPEC, "mock-opus"), (LENS, "codex-mock")])
        self.assert_b3_packet(fx)
        (smoke,) = [e for e in fx.events() if e["event"] == "lens-smoke"]
        self.assertEqual((smoke["ok"], smoke["model"]), (True, "codex-mock"))
        lens_bundle = Path(launches(fx.events(), "01")[3]["bundle"])
        self.assertIn("checklist-auth-sessions.md", (lens_bundle / "instructions.md").read_text())
        self.assertNotIn("Status: DONE", (lens_bundle / "instructions.md").read_text(), "the lens never sees the handoff")

    def test_lens_falls_back_to_opus_when_the_codex_smoke_fails_or_is_absent(self) -> None:
        fx, _ = self.run_b3('lens = { tool = "mock", model = "codex-mock" }\nlens_smoke = "exit 3"\n')
        self.assertEqual(roles(fx)[-1], (LENS, "mock-opus"))
        self.assertEqual([e["ok"] for e in fx.events() if e["event"] == "lens-smoke"], [False])
        self.assert_b3_packet(fx)
        fx, _ = self.run_b3("")
        self.assertEqual(roles(fx)[-1], (LENS, "mock-opus"))
        self.assertEqual([e for e in fx.events() if e["event"] == "lens-smoke"], [])

    def test_a_reviewer_that_edits_code_is_rejected_and_rerun(self) -> None:
        fx = self.enter()
        fx.ticket("02", blast="B2", scenario='work src/02/x.py "x = 1"; handoff DONE\n')
        fx.scenario("02-spec_verdict-a2", 'put src/02/x.py "x = 666"; put .scratch/demo/reviews/02/spec-verdict.md "Verdict: pass"\n')
        fx.scenario("02-spec_verdict", 'put .scratch/demo/reviews/02/spec-verdict.md "Verdict: pass"\n')
        code, out = fx.main("run")
        self.assertEqual(code, 0, out)
        stages = [e for e in fx.events() if e["event"] == "stage"]
        self.assertEqual([s["ok"] for s in stages], [False, True])
        self.assertIn("spec_verdict changed src/02/x.py", stages[0]["reason"])
        self.assertEqual(fx.repo.git("show", f"{INTEG}:src/02/x.py"), "x = 1", "nothing a reviewer changed outside its file lands")
        self.assertEqual(fx.repo.git("show", f"{INTEG}:.scratch/demo/reviews/02/spec-verdict.md"), "Verdict: pass")
        self.assertEqual(roles(fx, "02"), [("author", "mock-mid"), (SPEC, "mock-mid"), (SPEC, "mock-mid")])

    def test_escalation_to_b3_is_salvaged_into_the_b3_path(self) -> None:
        fx = self.enter()
        fx.ticket("01", touches="src/auth/**", scenario=AUTH_WORK)
        code, out = fx.main("run")
        self.assertEqual(code, 3, out)
        self.assertIn("[blast-b3]", out)
        old_tip = fx.repo.rev("t/01")
        self.assertIn("Blast: B3 — raised from B0", fx.repo.git("show", f"{INTEG}:.scratch/{EFFORT}/issues/01-t.md"))
        for name, text in (("01-test_author", TESTS_OK), ("01-a2", 'work src/auth/login.py "def login(): return False"; handoff DONE\n'),
                           ("01-spec_verdict", SPEC_OK), ("01-lens", LENS_OK)):
            fx.scenario(name, text)
        self.assertEqual(fx.main("relaunch", "01")[0], 0)
        code, out = fx.main("run")
        self.assertEqual(code, 3, out)
        self.assertEqual(fx.repo.rev("refs/one-punch/salvage/01"), old_tip, "the pre-tests work is kept aside")
        author = launches(fx.events(), "01")[-3]
        self.assertEqual((author["role"], author["model"]), ("author", "mock-opus"))
        self.assertIn(f"kept at {old_tip[:12]}", Path(author["bundle"], "instructions.md").read_text())
        self.assert_b3_packet_after_salvage(fx)

    def assert_b3_packet_after_salvage(self, fx: Effort) -> None:
        awaiting = [e for e in fx.events() if e["event"] == "integrate"][-1]
        self.assertEqual(awaiting["outcome"], "AWAITING-OPERATOR", awaiting)
        first = fx.repo.git("log", "--reverse", "--format=%s", f"{awaiting['base']}..{awaiting['judged']}").splitlines()[0]
        self.assertEqual(first, "test_author: ticket 01 (mock-opus)")
        subprocess.run(["git", "cat-file", "-e", f"{awaiting['judged']}:src/auth/login.py"], cwd=fx.repo.root, check=True)


if __name__ == "__main__":
    unittest.main()

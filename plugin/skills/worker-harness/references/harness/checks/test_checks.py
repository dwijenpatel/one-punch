"""Unit tests for the pure integrate checks: one pass and one fail case per
check, the blast-map format's worked example with exact values, and a real
`git diff` fixture. No git, no processes, no filesystem (except the optional
default-pack test, skipped when the skill's pack file is not next door).
Run from the harness directory: python -m unittest -v
"""

from __future__ import annotations

import pathlib
import unittest

from checks.blastmap import BlastEvaluation, BlastMapError, Hit, evaluate, load_blast_map
from checks.diff import FileEntry, parse_diff
from checks.hygiene import (
    CheckResult,
    CommandRun,
    Commit,
    attribution_check,
    blast_check,
    checklist_items,
    checklist_problems,
    conflict_partners,
    decide,
    handoff_check,
    megafile_check,
    ref_check,
    scrutiny_check,
    touches_check,
    verify_check,
)
from checks.config import ConfigError, parse_config
from checks.ledger import LedgerError, parse_ledger, ref_scanner
from checks.lint import LintRun, lint_check, parse_lint_output, ratchet
from core import DEFAULT_REF_PATTERN, Blast, Reference, ReuseMode, Tag

REF = DEFAULT_REF_PATTERN

# The worked example of blast-map-format.md §8, verbatim.
EXAMPLE_MAP = '''# Blast map

Floors for this repo's blast radius; ratified at H2. Lowerings cite D-NNN.

```toml blast-map
schema = 1
pack = "one-punch-default/1"
pattern_skip = ["**/*.md"]

[[zone]]
name = "auth-sessions"
level = "B3"
checklist = "auth-sessions"
why = "Authentication and sessions fail open silently."
paths = ["src/auth/**"]

  [[zone.pattern]]
  regex = '(?i)\\bjwt\\b'
  match = ["claims = jwt.decode(raw, key)"]
  nomatch = ["jwtish = 1"]

[[zone]]
name = "process-rules"
level = "B3"
protected = true
why = "Rule surfaces steer every later change."
paths = ["**/AGENTS.md", "docs/blast-map.md", "docs/decisions.md"]

[[zone]]
name = "dependency-manifests"
level = "B2"
why = "Dependency changes are wide."
paths = ["**/pyproject.toml"]

[[zone]]
name = "request-input"
level = "B2"
checklist = "untrusted-input"
why = "Request parsing sits on a trust boundary."

  [[zone.pattern]]
  regex = '\\brequest\\.(json|form|args)\\b'
  match = ["rows = request.json"]

[[lowering]]
zone = "request-input"
paths = ["src/admin/**"]
level = "B1"
decision = "D-014"
```
'''

EXAMPLE_ENTRIES = (
    FileEntry("src/admin/export.py", "M", lines=('    rows = request.json["rows"]',), added=((3, '    rows = request.json["rows"]'),)),
    FileEntry("src/api/session_view.py", "M", lines=('    claims = jwt.decode(raw, key, algorithms=["HS256"])',)),
    FileEntry("docs/notes.md", "M", lines=("jwt rotation plan",), added=((1, "jwt rotation plan"),)),
    FileEntry("pyproject.toml", "M", lines=('    "httpx>=0.28",',), added=((9, '    "httpx>=0.28",'),)),
)

REAL_DIFF = (
    "diff --git a/added.md b/added.md\nnew file mode 100644\nindex 0000000..92d5444\n--- /dev/null\n+++ b/added.md\n"
    "@@ -0,0 +1 @@\n+fresh\n"
    "diff --git a/bin.dat b/bin.dat\nindex bdc955b..8835708 100644\nBinary files a/bin.dat and b/bin.dat differ\n"
    'diff --git "a/caf\\303\\251.txt" "b/caf\\303\\251.txt"\nindex bca70f3..4286f42 100644\n'
    '--- "a/caf\\303\\251.txt"\n+++ "b/caf\\303\\251.txt"\n@@ -1 +1 @@\n-q\n+r\n'
    "diff --git a/del.txt b/del.txt\ndeleted file mode 100644\nindex 286c5f5..0000000\n--- a/del.txt\n+++ /dev/null\n"
    "@@ -1 +0,0 @@\n-gone\n"
    "diff --git a/mod.txt b/mod.txt\nold mode 100644\nnew mode 100755\nindex e32e7f2..3b24b46\n--- a/mod.txt\n+++ b/mod.txt\n"
    "@@ -2 +1,0 @@ a\n--- b\n@@ -3,0 +3 @@ c\n++ new\n"
    "diff --git a/old.py b/new.py\nsimilarity index 79%\nrename from old.py\nrename to new.py\nindex b2f931a..17eb8c9 100644\n"
    "--- a/old.py\n+++ b/new.py\n@@ -5 +5 @@ four\n-five\n+FIVE\n"
    "diff --git a/sp ace.txt b/sp ace.txt\nindex 587be6b..975fbec 100644\n--- a/sp ace.txt\t\n+++ b/sp ace.txt\t\n"
    "@@ -1 +1 @@\n-x\n+y\n"
)

LEDGER = """# Decisions

| ID | Decision | Rationale | Owner | Status | ADR |
|---|---|---|---|---|---|
| D-001 | Pure core | Tests without mocks | planner | active | |
| D-002 | Old way | Replaced | planner | superseded by D-003 | |
| **D-003** | New way | Better | planner | Active | [ADR](adr/3.md) |
| D-004 | Brownfield habit | Found in code | planner | inferred | |
"""
LEDGER_ROWS = parse_ledger(LEDGER)


def _evaluation(declared: Blast, hits: tuple[Hit, ...] = ()) -> BlastEvaluation:
    map_level = max((h.level for h in hits), key=lambda b: b.value, default=Blast.B0)
    effective = map_level if map_level.value > declared.value else declared
    return BlastEvaluation(declared, hits, map_level, effective, frozenset(), ())


def _added(path: str, *lines: str, status: str = "M", old_path: str | None = None) -> FileEntry:
    added = tuple((i + 1, text) for i, text in enumerate(lines))
    return FileEntry(path, status, old_path, tuple(lines), added)


# --------------------------------------------------------------------------
# Blast map
# --------------------------------------------------------------------------


def test_worked_example_hits_levels_and_checklists() -> None:
    bmap = load_blast_map(EXAMPLE_MAP)
    result = evaluate(bmap, EXAMPLE_ENTRIES, Blast.B1, active={"D-014"})
    got = sorted((h.zone, h.path, h.source, h.level.name) for h in result.hits)
    assert got == [
        ("auth-sessions", "src/api/session_view.py", "pattern", "B3"),
        ("dependency-manifests", "pyproject.toml", "path", "B2"),
        ("request-input", "src/admin/export.py", "pattern", "B1"),
    ]
    assert (result.map_level, result.effective, result.escalation) == (Blast.B3, Blast.B3, True)
    assert result.checklists == {"auth-sessions"}
    assert result.inactive_lowerings == ()


def test_worked_example_variant_superseded_lowering() -> None:
    result = evaluate(load_blast_map(EXAMPLE_MAP), EXAMPLE_ENTRIES, Blast.B1, active=set())
    assert result.inactive_lowerings == ("LOWERING-INACTIVE D-014",)
    assert [h.level for h in result.hits if h.zone == "request-input"] == [Blast.B2]
    assert result.checklists == {"auth-sessions", "untrusted-input"}


def test_rename_hits_both_sides_and_clean_diff_is_b0() -> None:
    bmap = load_blast_map(EXAMPLE_MAP)
    moved = FileEntry("src/session.py", "R", old_path="src/auth/session.py")
    assert evaluate(bmap, (moved,), Blast.B1, set()).effective is Blast.B3
    plain = _added("src/app.py", "print('hi')")
    result = evaluate(bmap, (plain,), Blast.B1, set())
    assert (result.hits, result.effective, result.escalation) == ((), Blast.B1, False)


def test_blast_map_missing_and_invalid_fail_closed() -> None:
    def invalid(markdown: str | None, token: str) -> None:
        try:
            load_blast_map(markdown)
        except BlastMapError as exc:
            assert token in str(exc), (token, str(exc))
        else:
            raise AssertionError(f"accepted: {markdown!r}")

    invalid(None, "BLAST-MAP-MISSING")
    invalid("no fence here", "BLAST-MAP-INVALID")
    invalid(EXAMPLE_MAP + EXAMPLE_MAP, "BLAST-MAP-INVALID")
    invalid("```toml blast-map\nschema = 1\n", "not closed")
    body = EXAMPLE_MAP.split("```toml blast-map\n")[1].split("```")[0]
    variants = {
        "schema = 1": "schema = 2",
        'name = "auth-sessions"': 'name = "Auth"',
        'paths = ["src/auth/**"]': 'paths = ["src/auth/"]',
        "match = [\"claims = jwt.decode(raw, key)\"]": "match = [\"no token here\"]",
        'decision = "D-014"': 'decision = "DX-14"',
        'level = "B1"': 'level = "B2"',
        'zone = "request-input"': 'zone = "process-rules"',
        'checklist = "untrusted-input"': 'checklist = "web"',
        'why = "Dependency changes are wide."': 'why = "Dependency changes are wide."\nglob = ["x"]',
        "[[lowering]]": 'unknown = 1\n[[lowering]]',
        "regex = '\\brequest": "regex = '(\\brequest",
    }
    for old, new in variants.items():
        assert old in body, old
        invalid(f"```toml blast-map\n{body.replace(old, new, 1)}```\n", "BLAST-MAP-INVALID")
    invalid("```toml blast-map\nschema = [\n```\n", "TOML syntax")


def test_default_pattern_pack_validates_when_available() -> None:
    pack = pathlib.Path(__file__).resolve().parents[4] / "blast-radius/references/default-pattern-pack.toml"
    if not pack.exists():
        raise unittest.SkipTest("blast-radius skill not next to this harness copy")
    bmap = load_blast_map(f"```toml blast-map\n{pack.read_text()}```\n")
    protected = {z.name for z in bmap.zones if z.protected}
    assert {"process-rules", "lint-config", "ci-verify"} <= protected
    agents = evaluate(bmap, (_added("AGENTS.md", "rule"),), Blast.B0, set())
    assert agents.effective is Blast.B3


# --------------------------------------------------------------------------
# Diff, ledger, config
# --------------------------------------------------------------------------


def test_parse_real_git_diff() -> None:
    entries = {e.path: e for e in parse_diff(REAL_DIFF)}
    assert set(entries) == {"added.md", "bin.dat", "café.txt", "del.txt", "mod.txt", "new.py", "sp ace.txt"}
    assert (entries["added.md"].status, entries["added.md"].added) == ("A", ((1, "fresh"),))
    assert entries["bin.dat"].binary and entries["bin.dat"].status == "M"
    assert entries["café.txt"].lines == ("q", "r")
    assert (entries["del.txt"].status, entries["del.txt"].lines, entries["del.txt"].added) == ("D", ("gone",), ())
    assert entries["mod.txt"].lines == ("-- b", "+ new")
    assert entries["mod.txt"].added == ((3, "+ new"),)
    renamed = entries["new.py"]
    assert (renamed.status, renamed.old_path, renamed.paths()) == ("R", "old.py", ("new.py", "old.py"))
    assert renamed.added == ((5, "FIVE"),)
    assert entries["sp ace.txt"].added == ((1, "y"),)


def test_ledger_parse_and_duplicates() -> None:
    assert LEDGER_ROWS == {"D-001": "active", "D-002": "superseded", "D-003": "active", "D-004": "inferred"}
    assert parse_ledger(None) == {}
    try:
        parse_ledger(LEDGER + "| D-001 | again | x | planner | active | |\n")
    except LedgerError as exc:
        assert "LEDGER-INVALID" in str(exc)
    else:
        raise AssertionError("duplicate accepted")


def test_ref_scanner_word_boundaries() -> None:
    scan = ref_scanner(REF)
    assert [m.group(0) for m in scan.finditer("see D-001, BREAKING(D-0123): x; PROD-001 D-01 D-001x")] == [
        "D-001",
        "D-0123",
    ]


def test_config_defaults_and_rejections() -> None:
    config = parse_config({"integrate": {"effort": "demo", "verify": ["make test"]}})
    assert config.expand(config.integration_branch) == "integrate/demo"
    assert config.handoff_path("07") == ".scratch/demo/handoffs/07.md"
    assert config.megafile_threshold == 800
    for bad in (
        {},
        {"integrate": {"effort": "demo", "verify": []}},
        {"integrate": {"effort": "demo", "verify": ["x"], "megafile": 900}},
        {"integrate": {"effort": "demo", "verify": ["x"], "test_globs": ["tests/"]}},
        {"integrate": {"effort": "de mo", "verify": ["x"]}},
    ):
        try:
            parse_config(bad)
        except ConfigError as exc:
            assert "CONFIG-INVALID" in str(exc)
        else:
            raise AssertionError(f"accepted {bad}")


# --------------------------------------------------------------------------
# Checks: one pass and one fail case each
# --------------------------------------------------------------------------


def test_handoff_check() -> None:
    assert handoff_check("Status: DONE_WITH_CONCERNS\nCommits: abc\n").ok
    assert handoff_check("Status: DONE\n").ok
    assert handoff_check(None).failures == ("HANDOFF-MISSING",)
    assert "HANDOFF-STATUS BLOCKED" in handoff_check("Status: BLOCKED\n").failures[0]


def test_verify_check() -> None:
    assert verify_check([CommandRun("make test", 0)]).ok
    failures = verify_check([CommandRun("make test", 2), CommandRun("make lint", None)]).failures
    assert "VERIFY-FAILED 'make test' (exit 2)" in failures[0] and "timed out" in failures[1]
    assert verify_check([CommandRun("ruff format", 0)], [" M src/a.py"]).failures[0].startswith("VERIFY-DIRTY")


def test_ref_check() -> None:
    skip = ("docs/decisions.md", "**/test_*.py")
    ok = ref_check([_added("src/a.py", "# D-001: pure core"), _added("src/test_a.py", "# D-999")], LEDGER_ROWS, REF, skip)
    assert ok.ok
    bad = ref_check([_added("src/a.py", "x = 1  # D-002", "y  # BREAKING(D-042): core")], LEDGER_ROWS, REF, skip)
    assert bad.failures == (
        "REF-UNRESOLVED D-002 src/a.py:1 (status superseded)",
        "REF-UNRESOLVED D-042 src/a.py:2 (no ledger row)",
    )


def test_touches_check() -> None:
    touches, exempt = ("src/store/**",), (".scratch/e/handoffs/07.md",)
    inside = [_added("src/store/a.py", "x"), _added(".scratch/e/handoffs/07.md", "Status: DONE")]
    assert touches_check(inside, touches, exempt, _evaluation(Blast.B1), REF).ok
    licensed = touches_check([_added("src/core.py", "# BREAKING(D-001): widen API")], touches, exempt, _evaluation(Blast.B1), REF)
    assert licensed.ok and licensed.warnings == ("BREAKING src/core.py (D-001)",)
    outside = touches_check([_added("src/core.py", "x")], touches, exempt, _evaluation(Blast.B1), REF)
    assert outside.failures[0].startswith("TOUCHES-OUTSIDE src/core.py")
    moved = FileEntry("src/store/b.py", "R", old_path="src/core.py")
    assert touches_check([moved], touches, exempt, _evaluation(Blast.B1), REF).failures[0].startswith("TOUCHES-OUTSIDE src/core.py")
    b3 = _evaluation(Blast.B1, (Hit("auth-sessions", "src/auth/x.py", "path", Blast.B3),))
    into_b3 = touches_check([_added("src/auth/x.py", "# BREAKING(D-001): x")], touches, exempt, b3, REF)
    assert into_b3.failures[0].startswith("TOUCHES-B3 src/auth/x.py")


def test_blast_check() -> None:
    assert blast_check(_evaluation(Blast.B2, (Hit("deps", "pyproject.toml", "path", Blast.B2),))).ok
    escalated = blast_check(_evaluation(Blast.B1, (Hit("deps", "pyproject.toml", "path", Blast.B2),)))
    assert escalated.failures == ("BLAST-ESCALATION declared B1 effective B2: deps pyproject.toml (path, B2)",)


CHECKLIST = "# Money\n\n- **MN-01** Rounding drift. Test: sum.\n- **MN-02** Retired.\n- **MN-03** Double spend. Test: replay.\n"
EVIDENCE = (".scratch/e/handoffs/07.md", ".scratch/e/reviews/07/**")
TESTS = ("**/test_*.py",)


def _b3_commits() -> list[Commit]:
    return [
        Commit("a" * 40, ("tests/test_pay.py",)),
        Commit("b" * 40, ("src/pay.py", "tests/test_pay.py")),
        Commit("c" * 40, (".scratch/e/reviews/07/lens.md",)),
    ]


def test_scrutiny_check_levels() -> None:
    assert scrutiny_check(Blast.B1, Tag.CODE_COMPLETE, {}, [], (), {}, TESTS, EVIDENCE).ok
    missing = scrutiny_check(Blast.B1, Tag.CONTRACT, {}, [], (), {}, TESTS, EVIDENCE)
    assert missing.failures[0].startswith("SCRUTINY-MISSING spec-verdict.md")
    verdict = {"spec-verdict.md": "Missing: none\nVerdict: pass\n"}
    assert scrutiny_check(Blast.B2, Tag.CODE_COMPLETE, verdict, [], (), {}, TESTS, EVIDENCE).ok
    rejected = scrutiny_check(Blast.B2, Tag.CODE_COMPLETE, {"spec-verdict.md": "Verdict: fail"}, [], (), {}, TESTS, EVIDENCE)
    assert rejected.failures[0].startswith("SCRUTINY-FAILED spec-verdict.md")


def test_scrutiny_check_b3() -> None:
    answers = "MN-01 pass: tests/test_pay.py::test_sum\nMN-03 n/a: no retries in this path\n"
    artifacts = {"spec-verdict.md": "Verdict: concerns", "lens.md": "Verdict: pass", "checklist-money.md": answers}
    green = scrutiny_check(Blast.B3, Tag.CONTRACT, artifacts, _b3_commits(), {"money"}, {"money": CHECKLIST}, TESTS, EVIDENCE)
    assert green.ok, green.failures
    impl_first = [_b3_commits()[1], _b3_commits()[0]]
    red = scrutiny_check(Blast.B3, Tag.CONTRACT, {}, impl_first, {"money"}, {"money": CHECKLIST}, TESTS, EVIDENCE)
    tokens = [f.split(" ")[0] for f in red.failures]
    assert tokens == ["SCRUTINY-MISSING", "SCRUTINY-MISSING", "TESTS-NOT-FIRST", "CHECKLIST-UNANSWERED"], red.failures


def test_checklist_grammar() -> None:
    assert checklist_items(CHECKLIST) == {"MN-01", "MN-03"}
    assert checklist_problems("MN-01 pass: t1\nMN-03 pass: t2\n", {"MN-01", "MN-03"}) == []
    problems = checklist_problems("MN-01 fail: rounding\nMN-01 pass: t\nbogus\nMN-09 n/a: x\n", {"MN-01", "MN-03"})
    assert problems == [
        "MN-01 fail",
        "malformed line 'bogus'",
        "unknown item MN-09",
        "MN-03 unanswered",
        "MN-01 answered 2 times",
    ]


def test_attribution_check() -> None:
    port = Reference("outrigger@9fa7023:tools/exec-loop/loop.py", ReuseMode.PORT)
    notices = "# Third-party notices\n\n- outrigger@9fa7023e81 license: MIT — exec loop\n"
    assert attribution_check(port, notices, {"MIT"}).ok
    assert attribution_check(Reference("x@1234567:y", ReuseMode.PATTERN), None, ()).ok
    assert attribution_check(port, None, {"MIT"}).failures[0].startswith("ATTRIBUTION-MISSING outrigger@9fa7023")
    assert attribution_check(port, notices, {"Apache-2.0"}).failures[0].startswith("ATTRIBUTION-LICENSE MIT")


def test_megafile_check() -> None:
    grown = _added("src/big.py", "x")
    head = {"src/big.py": "x\n" * 801, "src/old.py": "y\n" * 900, "src/shrunk.py": "s\n" * 880, "uv.lock": "z\n" * 5000}
    base = {"src/big.py": 790, "src/old.py": 850, "src/shrunk.py": 900}
    others = [_added("src/shrunk.py", "s"), _added("uv.lock", "z", status="A")]
    assert megafile_check(others, base, head, 800, ("**/*.lock",), LEDGER_ROWS, REF).ok
    grew_above = megafile_check([_added("src/old.py", "y")], base, head, 800, (), LEDGER_ROWS, REF)
    assert grew_above.failures == ("MEGAFILE src/old.py (850 -> 900 lines, threshold 800)",)
    red = megafile_check([grown], base, head, 800, (), LEDGER_ROWS, REF)
    assert red.failures == ("MEGAFILE src/big.py (790 -> 801 lines, threshold 800)",)
    waived = {"src/big.py": "# allow(megafile): D-001 generated table\n" + "x\n" * 800}
    ok = megafile_check([grown], base, waived, 800, (), LEDGER_ROWS, REF)
    assert ok.ok and ok.exceptions == ("allow(megafile): D-001 src/big.py",)


def _lint_run(hard: bool, base: str, head: str, exit_code: int = 1) -> LintRun:
    return LintRun("ruff check .", hard, 0 if not base else 1, base, exit_code, head)


def _lint(runs: list[LintRun], entries: list[FileEntry], head_text: dict[str, str], ledger: dict[str, str]) -> CheckResult:
    pattern = parse_config({"integrate": {"effort": "e", "verify": ["x"]}}).lint_pattern
    return lint_check(runs, entries, head_text, ledger, pattern=pattern, ok_exit=(0, 1), root="/wt", ref_pattern=REF)


def test_lint_check_ratchet_and_allow() -> None:
    entry = FileEntry("src/a.py", "M", lines=("import os", "except:"), added=((1, "import os"), (5, "except:")))
    old = "src/a.py:9:1: E722 Do not use bare `except`\n"
    head_out = "/wt/src/a.py:1:8: F401 `os` imported but unused\n" + old.replace(":9:", ":10:") + "src/b.py:2:1: F401 x\n"
    head_text = {"src/a.py": "import os  # allow(F401): D-001\n"}
    waived = _lint([_lint_run(True, old, head_out)], [entry], head_text, LEDGER_ROWS)
    assert waived.ok and waived.exceptions == ("allow(F401): D-001 src/a.py:1",)
    red = _lint([_lint_run(True, old, head_out)], [entry], {"src/a.py": "import os\n"}, LEDGER_ROWS)
    assert red.failures == ("LINT F401 src/a.py:1 `os` imported but unused",)
    superseded = _lint([_lint_run(True, old, head_out)], [entry], {"src/a.py": "import os  # allow(F401): D-002\n"}, LEDGER_ROWS)
    assert superseded.failures == red.failures and superseded.exceptions == ()
    soft = _lint([_lint_run(False, old, head_out)], [entry], {}, LEDGER_ROWS)
    assert soft.ok and soft.warnings == ("LINT-WARN F401 src/a.py:1 `os` imported but unused",)
    crashed = _lint([_lint_run(True, "", "", exit_code=2)], [entry], {}, LEDGER_ROWS)
    assert crashed.failures[0].startswith("LINT-ERROR 'ruff check .' (exit 2)")


def test_ratchet_counts_and_renames() -> None:
    pattern = parse_config({"integrate": {"effort": "e", "verify": ["x"]}}).lint_pattern
    base = parse_lint_output("old.py:3:1: E501 Line too long\n", pattern, "/wt")
    head = parse_lint_output("new.py:3:1: E501 Line too long\nnew.py:7:1: E501 Line too long\n", pattern, "/wt")
    entry = FileEntry("new.py", "R", old_path="old.py", lines=("long",), added=((7, "long"),))
    assert [(v.path, v.line) for v in ratchet(base, head, [entry])] == [("new.py", 7)]


def test_decide_and_conflict_partners() -> None:
    green = [CheckResult("ref")]
    red = [CheckResult("ref", failures=("REF-UNRESOLVED D-9",))]
    assert decide(green, _evaluation(Blast.B1)) == "MERGED"
    assert decide(green, _evaluation(Blast.B3)) == "AWAITING-OPERATOR"
    assert decide(red, _evaluation(Blast.B1)) == "FAILED"
    escalated = _evaluation(Blast.B1, (Hit("z", "p", "path", Blast.B2),))
    assert decide(red, escalated) == "BLAST-ESCALATION"
    events = [
        {"event": "integrate", "outcome": "MERGED", "ticket": "03", "files": ["src/a.py"]},
        {"event": "integrate", "outcome": "FAILED", "ticket": "04", "files": ["src/a.py"]},
        {"event": "integrate", "outcome": "MERGED", "ticket": "05", "files": ["src/b.py"]},
    ]
    assert conflict_partners(events, {"src/a.py"}, "07") == ("03",)


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None) -> unittest.TestSuite:
    suite = unittest.TestSuite(tests)
    for name, obj in sorted(globals().items()):
        if name.startswith("test_") and callable(obj) and not isinstance(obj, type):
            suite.addTest(unittest.FunctionTestCase(obj, description=name))
    return suite

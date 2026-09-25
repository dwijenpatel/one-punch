"""The shipped example config (../harness-example.toml) must always parse
through the real loaders. It is the example a planner copies for a fresh
effort (#10, light mode), so it can never silently drift from what
`checks.config.parse_config` and `runcore.parse_run_config` actually accept:
a renamed or newly-required key here would break every effort that copied
the example, so this test fails loudly first. Run from the harness
directory: python -m unittest -v
"""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

from checks.config import ConfigError, parse_config
from runcore import parse_run_config

EXAMPLE_PATH = Path(__file__).resolve().parent.parent / "harness-example.toml"

# What the planner would fill in for a real effort. Only the placeholders
# that appear as literal TOML values need substituting; commented-out lines
# (lens, lens_smoke) are never parsed either way.
SUBSTITUTIONS = {
    "<EFFORT_NAME>": "m1",
    "<TEST_COMMAND>": "npm test -- --run",
    "<BROWSER_WALK_COMMAND>": "npx playwright test e2e/",
    "<LINT_HARD_COMMAND>": "npx eslint . --max-warnings=0",
    "<LINT_SOFT_COMMAND>": "npx tsc --noEmit",
}


def _filled_text() -> str:
    text = EXAMPLE_PATH.read_text(encoding="utf-8")
    for placeholder, value in SUBSTITUTIONS.items():
        text = text.replace(placeholder, value)
    return text


def test_example_file_exists() -> None:
    assert EXAMPLE_PATH.is_file(), f"missing {EXAMPLE_PATH}"


def test_example_has_no_unfilled_placeholders_after_substitution() -> None:
    text = _filled_text()
    for placeholder in SUBSTITUTIONS:
        assert placeholder not in text, f"{placeholder} left unsubstituted"


def test_example_parses_through_both_real_loaders() -> None:
    data = tomllib.loads(_filled_text())

    cfg = parse_config(data)
    assert cfg.effort == "m1"
    assert cfg.verify == ("npm test -- --run", "npx playwright test e2e/")
    assert cfg.lint_hard == ("npx eslint . --max-warnings=0",)
    assert cfg.lint_soft == ("npx tsc --noEmit",)

    rc = parse_run_config(data, cfg.effort)
    assert rc.parallel == 4
    got_tools_models = {(tier.name, c.tool, c.model) for tier, cands in rc.ladder.items() for c in cands}
    assert got_tools_models == {
        ("T0", "claude", "opus"),
        ("T2", "claude", "sonnet"),
        ("T4", "claude", "haiku"),
    }
    # The commented-out lens block must stay commented: no lens configured
    # by default, and no candidate anywhere names a Fable model (the parser
    # itself refuses one; this just documents the example ships clean).
    assert rc.lens is None
    assert rc.lens_smoke == ""
    for candidates in rc.ladder.values():
        for candidate in candidates:
            assert "fable" not in candidate.model.lower()


def test_example_effort_placeholder_is_load_bearing() -> None:
    """The example is not accidentally valid TOML config as shipped: the
    effort placeholder must fail parse_config's name pattern, so a planner
    who forgets to fill it in gets CONFIG-INVALID, not a silent bad effort
    name."""
    raw = EXAMPLE_PATH.read_text(encoding="utf-8")
    data = tomllib.loads(raw)
    try:
        parse_config(data)
    except ConfigError as exc:
        assert "CONFIG-INVALID" in str(exc)
    else:
        raise AssertionError("unsubstituted example unexpectedly parsed")


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None) -> unittest.TestSuite:
    suite = unittest.TestSuite(tests)
    for name, obj in sorted(globals().items()):
        if name.startswith("test_") and callable(obj) and not isinstance(obj, type):
            suite.addTest(unittest.FunctionTestCase(obj, description=name))
    return suite

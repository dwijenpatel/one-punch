"""Property-style tests for the glob dialect and the Touches overlap
predicate (core_globs.py, imported through core's re-exports). No mocks:
the tree listing is a value, and property tests draw from hand-rolled
generators over a seeded `random.Random` (test_core.py reuses them).
Run: python -m unittest -v   (or: uv run --with pytest pytest -q test_core_globs.py)
"""

from __future__ import annotations

import itertools
import random
import unittest

from core import glob_intersection, glob_to_regex, literal_prefix, touches_overlap


# ---------------------------------------------------------------------------
# Glob dialect: blast-map-format.md §4 vectors, run against the copied code
# ---------------------------------------------------------------------------

GLOB_VECTORS: list[tuple[str, str, bool]] = [
    ("**/AGENTS.md", "AGENTS.md", True),
    ("**/AGENTS.md", "pkg/sub/AGENTS.md", True),
    ("**/AGENTS.md", "pkg/AGENTS.md.bak", False),
    ("AGENTS.md", "pkg/AGENTS.md", False),
    ("src/**", "src/a.py", True),
    ("src/**", "src/a/b/c.py", True),
    ("src/**", "src", False),
    ("src/*", "src/a/b.py", False),
    ("src/*.py", "src/app.py", True),
    ("**/migrations/**", "migrations/0001_init.py", True),
    ("**/migrations/**", "app/db/migrations/0002.sql", True),
    ("**/migrations/**", "app/migrations_old/x.py", False),
    ("a/**/b.txt", "a/b.txt", True),
    ("a/**/b.txt", "a/x/y/b.txt", True),
    ("**/.env.*", "svc/.env.local", True),
    ("**/tsconfig*.json", "tsconfig.json", True),
    ("**/tsconfig*.json", "web/tsconfig.build.json", True),
    ("file?.txt", "file1.txt", True),
    ("file?.txt", "file10.txt", False),
    ("**", "any/path/at/all.c", True),
    ("Src/**", "src/a.py", False),
    ("docs/[x].md", "docs/[x].md", True),
]
INVALID_GLOBS = ["src/", "/src/**", "./src/**", "src//a", "src/a**", "**.py"]


def test_glob_dialect_vectors_from_the_format_document() -> None:
    assert len(GLOB_VECTORS) == 22
    for glob, path, expected in GLOB_VECTORS:
        assert (glob_to_regex(glob).fullmatch(path) is not None) is expected, (glob, path)


def test_invalid_globs_are_rejected_everywhere() -> None:
    for glob in INVALID_GLOBS:
        for check in (glob_to_regex, lambda g: glob_intersection(g, "**"), literal_prefix_checked):
            try:
                check(glob)
            except ValueError:
                continue
            raise AssertionError(f"accepted invalid glob {glob!r}")


def literal_prefix_checked(glob: str) -> str:
    glob_to_regex(glob)
    return literal_prefix(glob)


def test_literal_prefix() -> None:
    assert literal_prefix("src/store/**") == "src/store"
    assert literal_prefix("src/*.py") == "src"
    assert literal_prefix("docs/new.md") == "docs/new.md"
    assert literal_prefix("**/AGENTS.md") == ""
    assert literal_prefix("file?.txt") == ""


# ---------------------------------------------------------------------------
# Generators (seeded; no hypothesis dependency)
# ---------------------------------------------------------------------------

DIRS = ["src", "api", "auth", "new"]
FILES = ["a.py", "b.md", "AGENTS.md", "x_test.py", "ab.py"]
UNIVERSE = [
    "/".join((*dirs, f))
    for depth in range(0, 3)
    for dirs in itertools.product(DIRS, repeat=depth)
    for f in FILES
]
GLOB_POOL = [
    "**",
    "src/**",
    "src/api/**",
    "src/auth/**",
    "src/new/**",
    "new/**",
    "src/*.py",
    "src/api/*.py",
    "src/api/*_test.py",
    "src/**/x_test.py",
    "**/AGENTS.md",
    "**/*.md",
    "src/api/a.py",
    "src/auth/a.py",
    "src/new/a.py",
    "AGENTS.md",
    "*/a.py",
    "src/?.py",
    "api/**/b.md",
    "auth/*",
]


def random_glob(rng: random.Random) -> str:
    shape = rng.randrange(6)
    d = "/".join(rng.choice(DIRS) for _ in range(rng.randint(1, 2)))
    if shape == 0:
        return rng.choice(GLOB_POOL)
    if shape == 1:
        return f"{d}/**"
    if shape == 2:
        return f"{d}/{rng.choice(['*.py', '*_test.py', '?.py', 'a*', '*'])}"
    if shape == 3:
        return f"**/{rng.choice(FILES + ['*.md', 'x_*'])}"
    if shape == 4:
        return f"{d}/**/{rng.choice(FILES)}"
    return rng.choice(UNIVERSE)


def random_tree(rng: random.Random) -> list[str]:
    return rng.sample(UNIVERSE, rng.randint(0, 25))


def random_segment_pattern(rng: random.Random) -> str:
    while True:
        p = "".join(rng.choice("ab*?") for _ in range(rng.randint(1, 4)))
        if "**" not in p:
            return p


# ---------------------------------------------------------------------------
# Glob intersection and overlap
# ---------------------------------------------------------------------------


def test_segment_intersection_is_exact_against_brute_force() -> None:
    rng = random.Random(11)
    strings = ["".join(s) for n in range(1, 6) for s in itertools.product("ab", repeat=n)]
    for _ in range(600):
        p, q = random_segment_pattern(rng), random_segment_pattern(rng)
        witness = glob_intersection(p, q)
        rp, rq = glob_to_regex(p), glob_to_regex(q)
        brute = any(rp.fullmatch(s) and rq.fullmatch(s) for s in strings)
        if witness is None:
            assert not brute, (p, q)
        else:
            assert rp.fullmatch(witness) and rq.fullmatch(witness), (p, q, witness)


def test_glob_intersection_witness_is_sound_and_none_is_complete() -> None:
    rng = random.Random(13)
    for _ in range(800):
        g, h = random_glob(rng), random_glob(rng)
        witness = glob_intersection(g, h)
        rg, rh = glob_to_regex(g), glob_to_regex(h)
        if witness is None:
            assert not any(rg.fullmatch(p) and rh.fullmatch(p) for p in UNIVERSE), (g, h)
        else:
            assert rg.fullmatch(witness) and rh.fullmatch(witness), (g, h, witness)
            assert glob_intersection(h, g) is not None


def test_overlap_properties() -> None:
    rng = random.Random(17)
    for _ in range(500):
        tree = random_tree(rng)
        prefixes = {"/".join(p.split("/")[:k]) for p in tree for k in range(1, p.count("/") + 2)}
        a = [random_glob(rng) for _ in range(rng.randint(1, 2))]
        b = [random_glob(rng) for _ in range(rng.randint(1, 2))]
        result = touches_overlap(a, b, tree)
        assert result == touches_overlap(b, a, tree)  # symmetric
        ra, rb = [glob_to_regex(g) for g in a], [glob_to_regex(g) for g in b]
        shared_file = any(any(r.fullmatch(p) for r in ra) and any(r.fullmatch(p) for r in rb) for p in tree)
        if shared_file:
            assert result, (a, b, tree)  # clause 1: an existing file matches both
        for g, h in itertools.product(a, b):
            deeper = max(literal_prefix(g), literal_prefix(h), key=len)
            nonexistent = deeper not in prefixes and not (deeper == "" and tree)
            if glob_intersection(g, h) is not None and nonexistent:
                assert result, (g, h, tree)  # clause 2: same not-yet-existing prefix
            same_anchor_kind = (literal_prefix(g) == "") == (literal_prefix(h) == "")
            if glob_intersection(g, h) is not None and same_anchor_kind:
                assert result, (g, h, tree)  # clause 3: shared anchor
        if all(glob_intersection(g, h) is None for g, h in itertools.product(a, b)):
            assert not result, (a, b)  # never overlap when no path can match both
        assert touches_overlap(a, a, tree)  # reflexive


def test_overlap_worked_cases() -> None:
    tree = ["src/store/a.py", "src/api/users.py", "AGENTS.md"]
    assert touches_overlap(["src/store/**"], ["src/store/new.py"], tree)  # new file in a touched dir
    assert touches_overlap(["src/**"], ["src/newmod/**"], tree)  # new dir under a touched dir
    assert touches_overlap(["src/newmod/x.py"], ["src/newmod/x.py"], tree)  # same new file
    assert touches_overlap(["src/api/*.py"], ["src/api/*_test.py"], tree)  # shared non-root anchor
    assert not touches_overlap(["src/api/*.py"], ["src/api/*.ts"], tree)  # no common path
    assert not touches_overlap(["src/*.py"], ["src/api/**"], tree)  # depth differs
    assert not touches_overlap(["src/store/**"], ["src/api/**"], tree)
    assert not touches_overlap(["**/AGENTS.md"], ["src/api/**"], tree)  # format §8 vector
    assert touches_overlap(["**/AGENTS.md"], ["newpkg/**"], tree)  # newpkg/AGENTS.md, new territory
    assert touches_overlap(["**/*.md"], ["**/b.md"], [])  # empty tree: everything is new
    assert touches_overlap(["**/*.md"], ["**/README.md"], tree)  # both root-anchored: same new README.md


# ---------------------------------------------------------------------------
# `python -m unittest` collects the module-level test functions too.
# ---------------------------------------------------------------------------


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None) -> unittest.TestSuite:
    suite = unittest.TestSuite(tests)
    for name, obj in sorted(globals().items()):
        if name.startswith("test_") and callable(obj) and not isinstance(obj, type):
            suite.addTest(unittest.FunctionTestCase(obj, description=name))
    return suite

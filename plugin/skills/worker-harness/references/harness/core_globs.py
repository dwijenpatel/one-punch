"""Glob dialect and Touches overlap for the one-punch worker harness core.

Pure, stdlib only, no I/O: the repository tree listing arrives as an
argument. Split from core.py (which re-exports every public name here) so
neither file crosses the 800-line megafile threshold; this module depends on
nothing in core.py.

- `glob_to_regex`: the blast-map glob dialect (blast-radius skill,
  references/blast-map-format.md §4), shared by blast-map paths and ticket
  Touches.
- `glob_intersection`, `literal_prefix`: exact intersection of two globs
  (with a witness path) and a glob's wildcard-free prefix.
- `touches_overlap` and the footprint helpers core.py's scheduling uses
  (`index_tree`, `footprint`, `footprints_overlap`): whether two glob sets
  may touch the same file (plan §3.4; blast-map format §6).
"""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass
from typing import Collection, Sequence


# --------------------------------------------------------------------------
# Glob dialect
# --------------------------------------------------------------------------

# Copied verbatim from the blast-radius skill, references/blast-map-format.md
# §4 ("Normative translation to a Python regex"), schema 1, only type-annotated
# (`out: list[str]`). One dialect for blast-map paths and ticket Touches; do
# not edit here without editing the format document. Its test vectors run in
# test_core_globs.py.
def glob_to_regex(glob: str) -> re.Pattern[str]:
    segments = glob.split("/")
    if glob.startswith("./") or any(s == "" for s in segments):
        raise ValueError(f"BLAST-MAP-INVALID: bad glob {glob!r}")
    out: list[str] = []
    for i, seg in enumerate(segments):
        last = i == len(segments) - 1
        if seg == "**":
            out.append(".+" if last else "(?:[^/]+/)*")
            continue
        if "**" in seg:
            raise ValueError(f"BLAST-MAP-INVALID: bad glob {glob!r}")
        body = "".join("[^/]*" if c == "*" else "[^/]" if c == "?" else re.escape(c) for c in seg)
        out.append(body if last else body + "/")
    return re.compile("".join(out))


def _segment_witness(p: str, q: str) -> str | None:
    """A non-empty string that both single-segment patterns (`*`, `?`,
    literals; no `/`) match, or None. Product-automaton search."""
    start = (0, 0)
    parent: dict[tuple[int, int], tuple[tuple[int, int], str] | None] = {start: None}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        i, j = state
        if i == len(p) and j == len(q):
            chars: list[str] = []
            cursor: tuple[int, int] | None = state
            while cursor is not None:
                step = parent[cursor]
                if step is None:
                    break
                chars.append(step[1])
                cursor = step[0]
            witness = "".join(reversed(chars))
            # Only `*` vs `*` can accept the empty string; segments are non-empty.
            return witness if witness else "x"
        moves: list[tuple[tuple[int, int], str]] = []
        if i < len(p) and p[i] == "*":
            moves.append(((i + 1, j), ""))
        if j < len(q) and q[j] == "*":
            moves.append(((i, j + 1), ""))
        if i < len(p) and j < len(q):
            a, b = p[i], q[j]
            ni = i if a == "*" else i + 1
            nj = j if b == "*" else j + 1
            a_any, b_any = a in "*?", b in "*?"
            if a_any and b_any:
                moves.append(((ni, nj), "x"))
            elif a_any:
                moves.append(((ni, nj), b))
            elif b_any or a == b:
                moves.append(((ni, nj), a))
        for nxt, char in moves:
            if nxt not in parent:
                parent[nxt] = (state, char)
                queue.append(nxt)
    return None


_ZSTAR = None  # token: zero or more whole segments


def _glob_tokens(glob: str) -> tuple[str | None, ...]:
    """Segment tokens: a segment pattern, or _ZSTAR. A last `**` (one or
    more segments) becomes `*` followed by _ZSTAR."""
    glob_to_regex(glob)  # validate
    segments = glob.split("/")
    tokens: list[str | None] = []
    for i, seg in enumerate(segments):
        if seg == "**":
            if i == len(segments) - 1:
                tokens.extend(["*", _ZSTAR])
            else:
                tokens.append(_ZSTAR)
        else:
            tokens.append(seg)
    return tuple(tokens)


def glob_intersection(g: str, h: str) -> str | None:
    """A path both globs match (a witness), or None when no path can match
    both. Exact for the §4 dialect: a product search over segment tokens,
    with segment pairs intersected by `_segment_witness`."""
    gt, ht = _glob_tokens(g), _glob_tokens(h)
    start = (0, 0)
    parent: dict[tuple[int, int], tuple[tuple[int, int], str | None] | None] = {start: None}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        i, j = state
        if i == len(gt) and j == len(ht):
            segs: list[str] = []
            cursor: tuple[int, int] | None = state
            while cursor is not None:
                step = parent[cursor]
                if step is None:
                    break
                if step[1] is not None:
                    segs.append(step[1])
                cursor = step[0]
            return "/".join(reversed(segs))
        moves: list[tuple[tuple[int, int], str | None]] = []
        if i < len(gt) and gt[i] is _ZSTAR:
            moves.append(((i + 1, j), None))
        if j < len(ht) and ht[j] is _ZSTAR:
            moves.append(((i, j + 1), None))
        if i < len(gt) and j < len(ht):
            a, b = gt[i], ht[j]
            ni = i if a is _ZSTAR else i + 1
            nj = j if b is _ZSTAR else j + 1
            segment = _segment_witness(a if a is not None else "*", b if b is not None else "*")
            if segment is not None:
                moves.append(((ni, nj), segment))
        for nxt, seg in moves:
            if nxt not in parent:
                parent[nxt] = (state, seg)
                queue.append(nxt)
    return None


def literal_prefix(glob: str) -> str:
    """The glob's leading wildcard-free segments; the whole glob when it has
    no wildcard; "" (the root) when its first segment has one."""
    lit: list[str] = []
    for seg in glob.split("/"):
        if "*" in seg or "?" in seg:
            break
        lit.append(seg)
    return "/".join(lit)

# --------------------------------------------------------------------------
# Overlap (plan §3.4; blast-map format §6)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Tree:
    paths: tuple[str, ...]
    prefixes: frozenset[str]  # every existing file and directory path; "" when non-empty


def index_tree(tree: Collection[str]) -> Tree:
    prefixes: set[str] = set()
    for path in tree:
        segments = path.split("/")
        if path.startswith("./") or any(s == "" for s in segments):
            raise ValueError(f"bad tree path {path!r} (repo-relative, '/'-separated, no empty segments)")
        prefixes.add("")
        for k in range(1, len(segments) + 1):
            prefixes.add("/".join(segments[:k]))
    return Tree(paths=tuple(sorted(set(tree))), prefixes=frozenset(prefixes))


@dataclass(frozen=True)
class Footprint:
    globs: tuple[str, ...]
    files: frozenset[str]  # existing files the globs match


def footprint(globs: Sequence[str], tree: Tree) -> Footprint:
    regexes = [glob_to_regex(g) for g in globs]
    files = frozenset(p for p in tree.paths if any(r.fullmatch(p) for r in regexes))
    return Footprint(globs=tuple(globs), files=files)


def _globs_overlap(g: str, h: str, tree: Tree) -> bool:
    if glob_intersection(g, h) is None:
        return False
    lg, lh = literal_prefix(g), literal_prefix(h)
    shallower, deeper = (lg, lh) if len(lg) <= len(lh) else (lh, lg)
    # Under-approximated only when a root wildcard meets an existing non-root prefix.
    return shallower != "" or deeper == "" or deeper not in tree.prefixes


def footprints_overlap(a: Footprint, b: Footprint, tree: Tree) -> bool:
    if a.files & b.files:
        return True
    return any(_globs_overlap(g, h, tree) for g in a.globs for h in b.globs)


def touches_overlap(a: Sequence[str], b: Sequence[str], tree: Collection[str]) -> bool:
    """Whether two glob sets may touch the same file (plan §3.4).

    Two sets overlap when some pair of globs g in `a`, h in `b` can name the
    same path (`glob_intersection`) and at least one holds:
      1. an existing file in `tree` matches both;
      2. the deeper of their literal prefixes does not exist in `tree` (as a
         file or directory) — "the same not-yet-existing path prefix";
      3. both literal prefixes are non-root, or both are the root: the globs
         share an anchor (conservative: `src/api/*.py` and
         `src/api/*_test.py` may both create `src/api/x_test.py`; two
         `**/*.md` tickets may both create `README.md`).
    Deliberate under-approximation, the one remaining case: a root-anchored
    wildcard glob (`**/AGENTS.md`) meets a glob whose non-root literal prefix
    exists only through existing files — otherwise every ticket would sit in
    every `**/`-zone (format §8 pins `src/api/**` outside `**/AGENTS.md`).
    The integrate step's Touches and B3-zone checks backstop the gap on the
    actual diff.
    """
    index = index_tree(tree)
    return footprints_overlap(footprint(a, index), footprint(b, index), index)

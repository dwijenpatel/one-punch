"""Unified diff -> file entries (blast-map format §5 "File entry").

Input is the text of `git diff --no-color --no-ext-diff --no-textconv
--unified=0 -M --src-prefix=a/ --dst-prefix=b/ <base> <judged>` (any
`--unified` value parses; context lines are not changed lines). Hunk bodies
are consumed by the counts in their `@@` header, so a removed line whose text
starts with `-- ` is never mistaken for a file header.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_HUNK = re.compile(r"^@@ -\d+(?:,(?P<old>\d+))? \+(?P<new_start>\d+)(?:,(?P<new>\d+))? @@")
_ESCAPES = {"a": 7, "b": 8, "t": 9, "n": 10, "v": 11, "f": 12, "r": 13, '"': 34, "\\": 92}


@dataclass(frozen=True)
class FileEntry:
    """One file the diff adds (`A`), modifies (`M`), deletes (`D`), renames
    (`R`) or copies (`C`). `path` is the post-image path (the deleted path
    for `D`); `old_path` is set for `R`/`C` only. `lines` holds every changed
    line, added and removed, without its `+`/`-`; `added` holds the added
    lines with their post-image line numbers."""

    path: str
    status: str
    old_path: str | None = None
    lines: tuple[str, ...] = ()
    added: tuple[tuple[int, str], ...] = ()
    binary: bool = False

    def paths(self) -> tuple[str, ...]:
        """Both sides of a rename or copy; the one path otherwise."""
        return (self.path,) if self.old_path is None else (self.path, self.old_path)


def unquote_path(token: str) -> str:
    """Undo git's C-style path quoting (`"a/sp\\303\\244ce"`); unquoted
    tokens pass through."""
    if not (len(token) >= 2 and token.startswith('"') and token.endswith('"')):
        return token
    body, out, i = token[1:-1], bytearray(), 0
    while i < len(body):
        c = body[i]
        if c != "\\":
            out += c.encode("utf-8")
            i += 1
            continue
        nxt = body[i + 1]
        if nxt in _ESCAPES:
            out.append(_ESCAPES[nxt])
            i += 2
        else:
            out.append(int(body[i + 1 : i + 4], 8))
            i += 4
    return out.decode("utf-8", errors="surrogateescape")


def _strip_prefix(path: str, prefix: str) -> str:
    return path[len(prefix) :] if path.startswith(prefix) else path


def _file_header_path(rest: str) -> str | None:
    """Path from the rest of a `--- ` / `+++ ` line; None for /dev/null. Git
    appends a tab after a path that contains a space."""
    token = rest[:-1] if rest.endswith("\t") else rest
    if token == "/dev/null":
        return None
    return _strip_prefix(_strip_prefix(unquote_path(token), "a/"), "b/")


def _git_header_paths(rest: str) -> tuple[str, str]:
    """Paths from `diff --git <rest>`: two quoted tokens, or `a/P b/P` split
    in the middle (the only unquoted form used as a fallback: mode-only and
    binary changes, where both sides are the same path)."""
    if rest.startswith('"'):
        end = 1
        while rest[end] != '"':
            end += 2 if rest[end] == "\\" else 1
        first, second = rest[: end + 1], rest[end + 2 :]
        return _strip_prefix(unquote_path(first), "a/"), _strip_prefix(unquote_path(second), "b/")
    if rest.endswith('"'):
        start = rest.index(' "b/')
        return _strip_prefix(rest[:start], "a/"), _strip_prefix(unquote_path(rest[start + 1 :]), "b/")
    half = (len(rest) - 1) // 2
    return _strip_prefix(rest[:half], "a/"), _strip_prefix(rest[half + 1 :], "b/")


@dataclass
class _Block:
    header_old: str
    header_new: str
    status: str = "M"
    old: str | None = None
    new: str | None = None
    minus: str | None = None
    plus: str | None = None
    saw_minus: bool = False
    saw_plus: bool = False
    binary: bool = False

    def entry(self, lines: list[str], added: list[tuple[int, str]]) -> FileEntry:
        if self.status in ("R", "C"):
            path, old_path = self.new or self.header_new, self.old or self.header_old
            return FileEntry(path, self.status, old_path, tuple(lines), tuple(added), self.binary)
        status = self.status
        if self.saw_minus and self.minus is None:
            status = "A"
        elif self.saw_plus and self.plus is None:
            status = "D"
        if status == "D":
            path = self.minus or self.header_old
        else:
            path = self.plus or self.header_new
        return FileEntry(path, status, None, tuple(lines), tuple(added), self.binary)


def parse_diff(text: str) -> tuple[FileEntry, ...]:
    """Parse `git diff` output into one entry per file, in diff order."""
    rows = text.split("\n")
    entries: list[FileEntry] = []
    i = 0
    while i < len(rows):
        row = rows[i]
        if not row.startswith("diff --git "):
            i += 1
            continue
        old, new = _git_header_paths(row[len("diff --git ") :])
        block = _Block(header_old=old, header_new=new)
        lines: list[str] = []
        added: list[tuple[int, str]] = []
        i += 1
        while i < len(rows) and not rows[i].startswith("diff --git "):
            row = rows[i]
            hunk = _HUNK.match(row)
            if hunk is not None:
                old_left = int(hunk.group("old") or "1")
                new_left = int(hunk.group("new") or "1")
                new_no = int(hunk.group("new_start"))
                i += 1
                while i < len(rows) and (old_left > 0 or new_left > 0):
                    body = rows[i]
                    if body.startswith("+"):
                        lines.append(body[1:])
                        added.append((new_no, body[1:]))
                        new_no += 1
                        new_left -= 1
                    elif body.startswith("-"):
                        lines.append(body[1:])
                        old_left -= 1
                    elif body.startswith("\\"):
                        pass
                    else:
                        new_no += 1
                        old_left -= 1
                        new_left -= 1
                    i += 1
                continue
            if row.startswith("new file mode"):
                block.status = "A"
            elif row.startswith("deleted file mode"):
                block.status = "D"
            elif row.startswith("rename from "):
                block.status, block.old = "R", unquote_path(row[len("rename from ") :])
            elif row.startswith("rename to "):
                block.new = unquote_path(row[len("rename to ") :])
            elif row.startswith("copy from "):
                block.status, block.old = "C", unquote_path(row[len("copy from ") :])
            elif row.startswith("copy to "):
                block.new = unquote_path(row[len("copy to ") :])
            elif row.startswith("--- "):
                block.saw_minus, block.minus = True, _file_header_path(row[4:])
            elif row.startswith("+++ "):
                block.saw_plus, block.plus = True, _file_header_path(row[4:])
            elif row.startswith("Binary files ") or row == "GIT binary patch":
                block.binary = True
            i += 1
        entries.append(block.entry(lines, added))
    return tuple(entries)

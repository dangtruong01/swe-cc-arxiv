"""Unified diff -> {path: FileChange}.

Layer A: no repository-specific knowledge. The only thing this module decides is which
post-patch line numbers the agent authored, which is what every ownership question
reduces to.
"""

from __future__ import annotations

import re

from compliance.core.models import FileChange, Hunk

_DIFF_GIT = re.compile(r"^diff --git a/(?P<a>.+?) b/(?P<b>.+)$")
_HUNK = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<start>\d+)(?:,(?P<count>\d+))? @@"
)
_BINARY = re.compile(r"^(?:Binary files|GIT binary patch)")


class _Acc:
    __slots__ = ("path", "old_path", "added", "removed", "is_new", "is_deleted",
                 "is_binary", "hunks", "anchors", "_hunk")

    def __init__(self, path: str, old_path: str | None) -> None:
        self.path = path
        self.old_path = old_path
        self.added: list[tuple[int, str]] = []
        self.removed: list[str] = []
        self.is_new = False
        self.is_deleted = False
        self.is_binary = False
        self.hunks: list[Hunk] = []
        self.anchors: set[int] = set()
        self._hunk: dict | None = None

    def open_hunk(self, old_start, old_count, new_start, new_count) -> None:
        self.close_hunk()
        self._hunk = {"old_start": old_start, "old_count": old_count,
                      "new_start": new_start, "new_count": new_count, "lines": []}

    def close_hunk(self) -> None:
        if self._hunk:
            hunk = Hunk(self._hunk["old_start"], self._hunk["old_count"],
                        self._hunk["new_start"], self._hunk["new_count"],
                        tuple(self._hunk["lines"]))
            self.hunks.append(hunk)
            self.anchors.update(deletion_anchors(hunk))
            self._hunk = None

    def finish(self) -> FileChange:
        self.close_hunk()
        return FileChange(
            path=self.path,
            authored_lines=frozenset(n for n, _ in self.added),
            added_lines=tuple(self.added),
            removed_lines=tuple(self.removed),
            deletion_anchors=frozenset(self.anchors),
            is_new=self.is_new,
            is_deleted=self.is_deleted,
            is_binary=self.is_binary,
            old_path=self.old_path if self.old_path != self.path else None,
            hunks=tuple(self.hunks),
        )


def deletion_anchors(hunk: Hunk) -> set[int]:
    """Post-patch lines where this hunk removes code.

    A removed line has no post-patch number of its own, so it is anchored to the line
    that ends up in its place: the running post-patch counter, which has advanced past
    every context and added line before it and not past any removal. Consecutive removals
    therefore share one anchor, which is right -- one removal site, one edit.

    Clamped to at least 1 so a removal at the very top of a file, where the new side of
    the header can start at 0, still anchors onto a real line.
    """
    anchors: set[int] = set()
    line_no = hunk.new_start
    for raw in hunk.lines:
        marker = raw[:1]
        if marker == "+":
            line_no += 1
        elif marker == "-":
            anchors.add(max(1, line_no))
        else:
            line_no += 1
    return anchors


def parse_unified_diff(text: str) -> dict[str, FileChange]:
    """Return one FileChange per path touched by ``text``.

    Line numbers are post-patch, so they index the file as the agent left it. A rename
    with no content change still yields a FileChange, with no authored lines.
    """
    changes: dict[str, FileChange] = {}
    acc: _Acc | None = None
    new_lineno = 0
    in_hunk = False

    for line in (text or "").splitlines():
        if match := _DIFF_GIT.match(line):
            if acc is not None:
                changes[acc.path] = acc.finish()
            acc = _Acc(match.group("b"), match.group("a"))
            in_hunk = False
            continue
        if acc is None:
            continue

        if line.startswith("new file mode"):
            acc.is_new = True
        elif line.startswith("deleted file mode"):
            acc.is_deleted = True
        elif _BINARY.match(line):
            acc.is_binary = True
        elif line.startswith("rename to "):
            acc.path = line[len("rename to ") :].strip()
        elif match := _HUNK.match(line):
            new_lineno = int(match.group("start"))
            acc.open_hunk(
                int(match.group("old_start")),
                int(match.group("old_count") or 1),
                new_lineno,
                int(match.group("count") or 1),
            )
            in_hunk = True
        elif in_hunk:
            if line.startswith("+++") or line.startswith("---"):
                continue
            if acc._hunk is not None and line[:1] in (" ", "+", "-", ""):
                acc._hunk["lines"].append(line)
            if line.startswith("+"):
                acc.added.append((new_lineno, line[1:]))
                new_lineno += 1
            elif line.startswith("-"):
                acc.removed.append(line[1:])
            elif line.startswith("\\"):  # "\ No newline at end of file"
                continue
            else:  # context line (leading space, or an empty line git emitted bare)
                new_lineno += 1

    if acc is not None:
        changes[acc.path] = acc.finish()
    return changes


def authored_line_count(changes: dict[str, FileChange]) -> int:
    return sum(len(c.authored_lines) for c in changes.values())

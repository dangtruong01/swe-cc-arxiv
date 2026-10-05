"""psf (requests): helpers shared across the rule modules. Not a rule module.

Layer C, and deliberately thin. Anything a second project would want belongs in
`compliance/extractors/`; what is left is Requests' own vocabulary -- where its package,
tests and documentation live -- which `docs/checker-authoring.md` §3 keeps local.

**Two layouts, one project.** Requests moved its package from ``requests/`` to
``src/requests/`` and its tests from a top-level ``test_requests.py`` to ``tests/``. The
SWE-bench instances sit on both sides of those moves while the contributing guide the
corpus was extracted from describes the current tree, so ``is_test_path`` and
``SOURCE_ROOTS`` name both spellings rather than the one that happens to be current.

**The command-log helpers are the heuristic half of this pack.** Four rules
(C003/C005/C006 here, C024 in git_conventions) turn on *when* something was run relative
to *when* the change was made, and the bundle records commands but not edits. ``edits``
below recognises an edit by the shape of the command that performed it, which over- and
under-fires; every rule built on it declares ``heuristic=True`` and says so.
"""

from __future__ import annotations

import re
from typing import Optional

from compliance.core import ownership as own
from compliance.core.models import Command, EvidenceBundle, Target

#: Both package layouts. `src/` came with the 2.31 restructuring; the SWE-bench base
#: commits predate it.
SOURCE_ROOTS = ("requests/", "src/requests/")
TEST_ROOTS = ("tests/",)
DOC_ROOT = "docs/"
DOC_SUFFIXES = (".rst", ".md", ".markdown")
RST_SUFFIXES = (".rst", ".rest")

#: Project metadata that is written in a documentation markup but is not documentation:
#: the changelog, the readme, the licence notice, the contributing guide, the issue
#: templates. Excluded so C013 does not read "documentation changes live under docs/" as
#: a prohibition on editing HISTORY.md -- see the documentation module's docstring.
META_PREFIXES = (".github/",)


def is_test_path(path: str) -> bool:
    """Requests' tests, in either layout.

    A basename test is included deliberately: the older base commits keep the whole suite
    in a top-level ``test_requests.py``, and a rule that only knew ``tests/`` would report
    those contributions as testless.
    """
    if path.startswith(TEST_ROOTS):
        return True
    name = path.rsplit("/", 1)[-1]
    return name.startswith("test_") and name.endswith(".py")


def is_source_path(path: str) -> bool:
    return path.startswith(SOURCE_ROOTS) and not is_test_path(path)


def is_meta_path(path: str) -> bool:
    """Repository metadata rather than documentation: anything at the top level, and the
    `.github/` tree."""
    return "/" not in path or path.startswith(META_PREFIXES)


def target(key: str, path: Optional[str] = None,
           span: Optional[tuple[int, int]] = None,
           payload=None, snippet: str = "", source: str = "patch") -> Target:
    return Target(key=key, file=path, line_span=span, source=source,
                  payload=payload, snippet=snippet[:200])


def ran(bundle: EvidenceBundle, pattern: re.Pattern) -> list[Command]:
    return [c for c in bundle.commands if pattern.search(c.command)]


def contribution_target(bundle: EvidenceBundle, prefix: str,
                        snippet: str = "") -> list[Target]:
    """The antecedent shared by whole-contribution rules (spec §4.4).

    Fires on having submitted something, never on having run the tool the rule is about
    (§7.1): triggering on the tool lets a contribution that ran nothing collect
    ``not_applicable`` instead of a violation. One target, payload the bundle, ownership
    ``touched``.
    """
    if not bundle.files:
        return []
    return [target(f"{prefix}:{bundle.instance_id}", None, None, bundle,
                   snippet or f"{len(bundle.files)} file(s) in the contribution")]


def python_files(bundle: EvidenceBundle, *, mode: str = "touched",
                 tests: Optional[bool] = None) -> list[str]:
    out = []
    for path in sorted(bundle.files):
        if not path.endswith(".py") or not own.owns_file(bundle, path, mode):
            continue
        if tests is not None and is_test_path(path) is not tests:
            continue
        out.append(path)
    return out


def changed_under(bundle: EvidenceBundle, prefix: str,
                  suffixes: tuple[str, ...] = ()) -> list[str]:
    return [p for p in sorted(bundle.files)
            if p.startswith(prefix) and (not suffixes or p.endswith(suffixes))]


def documentation_files(bundle: EvidenceBundle) -> list[str]:
    """Every documentation source the contribution changes, wherever it sits.

    Not scoped to ``docs/``: C013 is about files that are documentation and are in the
    wrong place, so scoping the selection to the right place would leave it unable to
    fire.
    """
    return [p for p in sorted(bundle.files)
            if p.endswith(DOC_SUFFIXES) and not is_meta_path(p)]


def test_files(bundle: EvidenceBundle) -> list[str]:
    return [p for p in sorted(bundle.files) if is_test_path(p)]


def added_lines(bundle: EvidenceBundle, path: str) -> tuple[tuple[int, str], ...]:
    change = bundle.files.get(path)
    return change.added_lines if change else ()


def added_text(bundle: EvidenceBundle, path: str) -> str:
    return "\n".join(text for _, text in added_lines(bundle, path))


# --- the command log, and where the change sits in it ---------------------------------

#: Every runner the guide's "run the tests" could mean, plus the wrappers Requests ships.
TEST_RUN = re.compile(
    r"\bpytest\b|\bpy\.test\b|\bpython\s+-m\s+unittest\b|\bnox\b|\btox\b"
    r"|\bmake\s+test\b")
#: A run that names particular tests rather than the suite: a node id, a `-k` filter, a
#: rerun of last failures, or a single file argument.
SELECTIVE_RUN = re.compile(r"::|(?:^|\s)-k(?:\s|=)|--last-failed|(?:^|\s)--lf\b|\S+\.py\b")
#: What a failing pytest/unittest run prints. Positive detection of failure only --
#: searching for success matches unrelated output constantly.
RUN_FAILED = re.compile(
    r"=+\s*(FAILURES|ERRORS)\s*=+|^FAILED\b|^ERROR\b|\b\d+\s+failed\b|\b\d+\s+error"
    r"|^FAILED \(|\bTraceback \(most recent call last\)", re.M)

#: Shell shapes that write to a file, and the editor tool calls the OpenHands adapter
#: renders as `str_replace_editor {"command": "create", ...}`. Read-only forms of the
#: same tool (`view`) are deliberately not matched.
_EDIT = re.compile(
    r"\bsed\s+-i\b|\bpatch\s+-p\d\b|\bgit\s+apply\b|\bapply_patch\b|\bedit_file\b"
    r"|>>?\s*[\w./-]+\.(?:py|rst|md|txt|cfg|toml|ini|yaml|yml)\b"
    r"|\bstr_replace_editor\b[^\n]*[\"']command[\"']\s*:\s*[\"'](?:create|insert|str_replace)[\"']")
#: A path inside the command that says the edit landed on a test.
_TEST_PATH_IN_COMMAND = re.compile(r"(?:^|[\s\"'/])tests?/|\btest_\w+\.py\b|\b\w+_test\.py\b")


def edits(bundle: EvidenceBundle) -> list[Command]:
    """Commands that changed a file, as far as their text can say."""
    return [c for c in bundle.commands if _EDIT.search(c.command)]


def first_edit_index(bundle: EvidenceBundle) -> Optional[int]:
    """Where the agent stopped looking and started changing things. ``None`` when no
    command in the log looks like an edit at all."""
    return next((c.index for c in edits(bundle)), None)


def first_source_edit_index(bundle: EvidenceBundle) -> Optional[int]:
    """The first edit that did not name a test path -- the change itself, as opposed to
    the tests written before it."""
    return next((c.index for c in edits(bundle)
                 if not _TEST_PATH_IN_COMMAND.search(c.command)), None)


def last_edit_index(bundle: EvidenceBundle) -> Optional[int]:
    indexes = [c.index for c in edits(bundle)]
    return indexes[-1] if indexes else None


def test_runs(bundle: EvidenceBundle, *, before: Optional[int] = None,
              after: Optional[int] = None, whole_suite: bool = False) -> list[Command]:
    """Test-runner invocations in the log, optionally windowed against an edit index."""
    out = []
    for command in bundle.commands:
        if not TEST_RUN.search(command.command):
            continue
        if before is not None and command.index >= before:
            continue
        if after is not None and command.index <= after:
            continue
        if whole_suite and SELECTIVE_RUN.search(command.command):
            continue
        out.append(command)
    return out


def reported_failure(command: Command) -> bool:
    """Whether a run said it failed, from its exit status when one was captured and from
    its output otherwise."""
    if command.returncode is not None and command.returncode != 0:
        return True
    return bool(RUN_FAILED.search(command.output or ""))


# --- Python code samples inside reStructuredText --------------------------------------

_DOCTEST = re.compile(r"^(?P<indent>\s*)(?:>>>|\.\.\.)\s?(?P<code>.*)$")
_PYTHON_BLOCK = re.compile(
    r"^(?P<indent>\s*)\.\.\s+(?:code-block|sourcecode|code)::\s*(?:python|py|python3)\s*$",
    re.I)
_SINGLE_QUOTED = re.compile(r"'[^'\n]*'")
_DOUBLE_QUOTED = re.compile(r'"[^"\n]*"')


def python_sample_lines(text: str) -> list[tuple[int, str]]:
    """(line number, code) for every line of Python sample in a reStructuredText file.

    Two shapes only: a doctest prompt, and the body of a `.. code-block:: python`
    directive. Untagged literal blocks (`::`) are deliberately excluded -- they carry
    shell transcripts and HTTP headers as often as Python, and quoting those as
    double-quote violations would manufacture findings the rule does not make.
    """
    out: list[tuple[int, str]] = []
    lines = text.split("\n")
    block_indent: Optional[int] = None
    for number, line in enumerate(lines, 1):
        if match := _PYTHON_BLOCK.match(line):
            block_indent = len(match.group("indent"))
            continue
        if match := _DOCTEST.match(line):
            out.append((number, match.group("code")))
            continue
        if block_indent is None:
            continue
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= block_indent:
            block_indent = None
            continue
        out.append((number, line.strip()))
    return out


def double_quoted_strings(code: str) -> list[str]:
    """Double-quoted literals in one line of Python, with single-quoted ones removed
    first so `'he said "no"'` does not read as a violation."""
    return _DOUBLE_QUOTED.findall(_SINGLE_QUOTED.sub("", code))

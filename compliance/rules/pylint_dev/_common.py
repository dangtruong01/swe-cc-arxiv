"""pylint-dev: helpers shared across the rule modules. Not a rule module.

Layer C, and deliberately thin. Anything a second project would want belongs in
`compliance/extractors/`; what is left is pylint's own vocabulary -- where its checkers,
tests and news fragments live, and the two little grammars its functional-test framework
legislates -- which `docs/checker-authoring.md` §3 keeps local.

**The docs and the tree spell the test directory differently.** The contributor guide
writes ``/pylint/test`` on one page and ``pylint/tests`` on its overview, while the
checkout has ``tests/``; the workbook records the discrepancy on C037 as
``low_confidence``. The corpus is the specification and is not edited (§0), so the path
matchers below accept every spelling the sources use -- ``tests/``, ``test/`` and either
under a leading ``pylint/`` -- and the rules that turn on a directory name say in their
docstring that the tolerance is why they are heuristic.

**Two grammars are pylint's own and are matched here rather than in each rule.** A
functional test's expectation is carried in two places: ``# [symbol]`` annotations in the
``.py`` and ``symbol:line:...`` records in the companion ``.txt``. ``ANNOTATION`` and
``EXPECTED_LINE`` are the readings of those, shared by C041, C042, C043, C047, C048, C049
and C050 so that seven rules cannot disagree about what an annotation is.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Optional

from compliance.core import ownership as own
from compliance.core.models import Command, EvidenceBundle, Target

PACKAGE = "pylint/"
CHECKERS_ROOT = "pylint/checkers/"
EXTENSIONS_ROOT = "pylint/extensions/"

#: towncrier's fragment directory and the twelve types `towncrier.toml` declares. Both
#: are read off the project's own configuration, so C007 grades against a published list
#: rather than a guess.
FRAGMENTS_ROOT = "doc/whatsnew/fragments/"
FRAGMENT_TYPES = (
    "breaking", "user_action", "feature", "new_check", "removed_check", "extension",
    "false_positive", "false_negative", "bugfix", "other", "internal", "performance",
)
#: `1234.bugfix` as `towncrier create <IssueNumber>.<type>` writes it. The `.rst` suffix
#: is tolerated because the pre-commit hook's own exclude pattern is written against
#: `.rst` fragment files.
FRAGMENT_NAME = re.compile(r"^(?P<issue>\d+)\.(?P<type>[a-z_]+)(?:\.rst)?$")

#: Every spelling of the test tree the sources use -- see the module docstring.
_TESTS = r"(?:pylint/)?tests?/"
TESTS_RE = re.compile(rf"^{_TESTS}")
FUNCTIONAL_RE = re.compile(rf"^{_TESTS}functional/")
CONFIG_TEST_RE = re.compile(rf"^{_TESTS}config/")
REGRTEST_DATA_RE = re.compile(rf"^{_TESTS}regrtest_data/")
#: The two directories the guide names for regression tests, relative to `functional/`.
REGRESSION_DIRS = ("r/regression/", "r/regression_02/")
REGRESSION_PREFIX = "regression_"
#: `tests/functional/ext/<extension name>/`.
EXT_FUNCTIONAL = "ext/"

#: A message id: one of the five category letters and exactly four digits.
MESSAGE_ID = re.compile(r"^[CWEFR]\d{4}$")

#: The six keys the functional runner's `[testoptions]` section accepts, as the guide
#: enumerates them.
TESTOPTIONS_SECTION = "testoptions"
TESTOPTIONS_KEYS = ("min_pyver", "max_pyver", "min_pyver_end_position", "requires",
                    "except_implementations", "exclude_platforms")

#: One `# [symbol]` expectation, with the two optional prefixes the framework allows: a
#: line offset (`# +1:`) and a version condition (`# <3.12:`). Written to find *every*
#: annotation on a line, because C043 is about how many of them there are.
ANNOTATION = re.compile(
    r"#\s*(?:(?P<offset>[+-]?\d+)\s*:)?\s*"
    r"(?:(?P<op>[<>=!]+)\s*(?P<version>\d+\.\d+(?:\.\d+)?)\s*:)?\s*"
    r"\[(?P<msgs>[^\]]*)\]"
)
#: One record of a functional test's expected output: `symbol:line:...`.
EXPECTED_LINE = re.compile(r"^(?P<symbol>[a-z][a-z0-9-]*):(?P<line>\d+):")
#: `<stem>.314.txt` -- the expected output that applies from Python 3.14 onwards.
VERSIONED_TXT = re.compile(r"^(?P<stem>.+)\.(?P<version>\d{2,4})\.txt$")
#: `<test name>.<exit code>.out`.
OUT_NAME = re.compile(r"^(?P<stem>.+)\.(?P<code>\d+)\.out$")

#: Configuration formats and the directory name that carries each, as
#: `tests/config/functional/` is laid out.
CONFIG_FORMATS = {
    ".toml": ("toml",),
    ".ini": ("ini", "tox", "setup_cfg"),
    ".cfg": ("setup_cfg", "ini"),
    ".rc": ("ini",),
}
CONFIG_INPUT_SUFFIXES = tuple(CONFIG_FORMATS)


# --- targets and command log ----------------------------------------------------------


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
    (§7.1): triggering on the tool lets a contribution that checked nothing collect
    ``not_applicable`` instead of a violation.
    """
    if not bundle.files:
        return []
    return [target(f"{prefix}:{bundle.instance_id}", None, None, bundle,
                   snippet or f"{len(bundle.files)} file(s) in the contribution")]


# --- paths ----------------------------------------------------------------------------


def stem_of(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    return name.rsplit(".", 1)[0] if "." in name else name


def directory_of(path: str) -> str:
    return path.rsplit("/", 1)[0] + "/" if "/" in path else ""


def suffix_of(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    return "." + name.rsplit(".", 1)[-1] if "." in name else ""


def changed_under(bundle: EvidenceBundle, prefix: str,
                  suffixes: tuple[str, ...] = ()) -> list[str]:
    return [p for p in sorted(bundle.files)
            if p.startswith(prefix) and (not suffixes or p.endswith(suffixes))]


def matching(bundle: EvidenceBundle, pattern: re.Pattern, *, mode: str = "touched",
             suffixes: tuple[str, ...] = ()) -> list[str]:
    """Owned changed paths matching one of the tree patterns above."""
    return [p for p in sorted(bundle.files)
            if pattern.match(p) and own.owns_file(bundle, p, mode)
            and (not suffixes or p.endswith(suffixes))]


def is_functional_test(path: str) -> bool:
    """A functional test *case*: the `.py` the framework pairs with a `.txt`."""
    return bool(FUNCTIONAL_RE.match(path)) and path.endswith(".py") \
        and not path.endswith("__init__.py")


def functional_relpath(path: str) -> str:
    """The part of a functional test path below `functional/` -- `u/use/use_foo.py`."""
    match = FUNCTIONAL_RE.match(path)
    return path[match.end():] if match else path


def functional_tests(bundle: EvidenceBundle, *, mode: str = "created") -> list[str]:
    return [p for p in sorted(bundle.files)
            if is_functional_test(p) and own.owns_file(bundle, p, mode)]


def companion(bundle: EvidenceBundle, path: str, suffix: str) -> Optional[str]:
    """`<stem><suffix>` beside ``path``, when the contribution carries it."""
    candidate = f"{directory_of(path)}{stem_of(path)}{suffix}"
    return candidate if candidate in bundle.files else None


def versioned_companions(bundle: EvidenceBundle, path: str) -> list[str]:
    """Every `<stem>.<version>.txt` beside ``path`` in the contribution."""
    directory, stem = directory_of(path), stem_of(path)
    out = []
    for candidate in sorted(bundle.files):
        if directory_of(candidate) != directory:
            continue
        match = VERSIONED_TXT.match(candidate.rsplit("/", 1)[-1])
        if match and match.group("stem") == stem:
            out.append(candidate)
    return out


def python_files(bundle: EvidenceBundle, *, mode: str = "touched",
                 tests: Optional[bool] = None) -> list[str]:
    out = []
    for path in sorted(bundle.files):
        if not path.endswith(".py") or not own.owns_file(bundle, path, mode):
            continue
        if tests is not None and bool(TESTS_RE.match(path)) is not tests:
            continue
        out.append(path)
    return out


# --- file text ------------------------------------------------------------------------


def added_text(bundle: EvidenceBundle, path: str) -> str:
    change = bundle.files.get(path)
    if change is None:
        return ""
    return "\n".join(text for _, text in change.added_lines)


def removed_text(bundle: EvidenceBundle, path: str) -> str:
    change = bundle.files.get(path)
    return "\n".join(change.removed_lines) if change else ""


def head_text(bundle: EvidenceBundle, path: str) -> Optional[str]:
    change = bundle.files.get(path)
    return change.head_text if change else None


def modules(bundle: EvidenceBundle, *, mode: str = "touched",
            tests: Optional[bool] = None):
    """(path, PyModule) for each owned Python file whose head text parses."""
    from compliance.extractors import python_ast as pa

    out = []
    for path in python_files(bundle, mode=mode, tests=tests):
        text = head_text(bundle, path)
        if text is None:
            continue
        module = pa.parse_module(text, path)
        if module.ok:
            out.append((path, module))
    return out


# --- pylint's two functional-test grammars --------------------------------------------


@dataclass(frozen=True)
class Annotation:
    """One `# [symbol]` expectation in a functional test file."""

    lineno: int
    """File line the comment sits on."""
    expected_line: int
    """Line the messages are expected on -- the comment's line plus its offset."""
    symbols: tuple[str, ...]
    op: str = ""
    version: str = ""
    text: str = ""


def annotations_of(source: str) -> list[Annotation]:
    out: list[Annotation] = []
    for lineno, line in enumerate(source.split("\n"), start=1):
        for match in ANNOTATION.finditer(line):
            offset = int(match.group("offset") or 0)
            symbols = tuple(s.strip() for s in match.group("msgs").split(",") if s.strip())
            out.append(Annotation(
                lineno=lineno, expected_line=lineno + offset, symbols=symbols,
                op=match.group("op") or "", version=match.group("version") or "",
                text=match.group(0)))
    return out


def annotation_count(line: str) -> int:
    """How many separate bracket comments one source line carries (C043)."""
    return len(ANNOTATION.findall(line))


def expected_messages(source: str) -> list[tuple[str, int]]:
    """(symbol, line) for each record of a functional test's expected output."""
    out = []
    for line in source.split("\n"):
        if match := EXPECTED_LINE.match(line.strip()):
            out.append((match.group("symbol"), int(match.group("line"))))
    return out


def ini_sections(source: str) -> dict[str, dict[str, str]]:
    """A very small ini reader: `configparser` would raise on a malformed `.rc`, and a
    malformed file is a verdict this pack has to be able to report rather than crash on."""
    sections: dict[str, dict[str, str]] = {"": {}}
    current = ""
    for raw in source.split("\n"):
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip().lower()
            sections.setdefault(current, {})
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            sections[current][key.strip().lower()] = value.strip()
    return sections


def version_tuple(text: str) -> Optional[tuple[int, ...]]:
    if not re.match(r"^\d+\.\d+(\.\d+)?$", text.strip()):
        return None
    return tuple(int(part) for part in text.strip().split("."))


# --- pylint's checker vocabulary ------------------------------------------------------


@dataclass(frozen=True)
class MessageEntry:
    """One entry of a checker's `msgs` dictionary."""

    msgid: str
    symbol: str
    lineno: int
    end_lineno: int
    shared: bool = False

    def span(self) -> tuple[int, int]:
        return (self.lineno, self.end_lineno)


def checker_classes(module) -> list[ast.ClassDef]:
    """Every class in the module that inherits from something named `*Checker`."""
    out = []
    for node in ast.walk(module.tree) if module.tree is not None else []:
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            name = base.attr if isinstance(base, ast.Attribute) else getattr(base, "id", "")
            if name.endswith("Checker"):
                out.append(node)
                break
    return out


def message_entries(classdef: ast.ClassDef) -> list[MessageEntry]:
    """The `msgs` dictionary of one checker class, read as entries."""
    out: list[MessageEntry] = []
    for node in classdef.body:
        value = None
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "msgs" for t in node.targets):
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and node.target.id == "msgs":
            value = node.value
        if not isinstance(value, ast.Dict):
            continue
        for key, entry in zip(value.keys, value.values):
            if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                continue
            symbol, shared = "", False
            if isinstance(entry, (ast.Tuple, ast.List)):
                if len(entry.elts) > 1 and isinstance(entry.elts[1], ast.Constant):
                    symbol = str(entry.elts[1].value)
                for element in entry.elts[2:]:
                    if not isinstance(element, ast.Dict):
                        continue
                    for option, setting in zip(element.keys, element.values):
                        if isinstance(option, ast.Constant) and option.value == "shared":
                            shared = bool(getattr(setting, "value", False))
            start = key.lineno
            end = getattr(entry, "end_lineno", None) or start
            out.append(MessageEntry(key.value, symbol, start, end, shared))
    return out


def class_attribute(classdef: ast.ClassDef, name: str) -> Optional[ast.AST]:
    for node in classdef.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return node.value
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and node.target.id == name:
            return node.value if node.value is not None else node
    return None


def class_methods(classdef: ast.ClassDef) -> list[ast.FunctionDef]:
    return [node for node in classdef.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def added_message_entries(bundle: EvidenceBundle) -> list[tuple[str, ast.ClassDef,
                                                                MessageEntry]]:
    """(path, checker class, entry) for every `msgs` entry the agent wrote itself.

    Spec §4.1: the entry is the target, and an entry every line of which the agent
    authored is one it brought into existence -- which is what `created` means for a
    construct added to a file that already existed.
    """
    out = []
    for path, module in modules(bundle, tests=False):
        for classdef in checker_classes(module):
            for entry in message_entries(classdef):
                if own.owns_span(bundle, path, entry.span(), "created"):
                    out.append((path, classdef, entry))
    return out

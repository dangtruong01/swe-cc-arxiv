"""Import statements: which group each belongs to, what order they are in, how they read.

Layer B -- shared across Python projects, and it names none of them. Which package names
count as first party, and which order the groups should appear in, are supplied by the
caller as a `GroupPolicy`; nothing here has an opinion about any particular project's
declared import-group order.

Like the RST extractor, this is deliberately **not** a formatter and does not pretend to
be one. A formatter's job is to rewrite the text; a rule's job is to say *which line* is
wrong, and the two want opposite things. Normalising a wrapped import into a canonical
form throws away the continuation indent, the trailing comma and the marker comment --
the very details the rules exist to check. So every construct is recognised where it sits
and every result carries a line number.

Two inputs, on purpose. `ast` gives the structure -- what is imported, from where, at
what relative depth, inside which `try` -- and discards everything about how the source
was *typed*. Indentation, parentheses, trailing commas, blank lines and end-of-line
markers survive only in the raw text. Functions here take both, and a caller that already
parsed the file can pass the `PyModule` in to avoid a second parse.

**A file that does not parse is not a violation.** Every entry point returns an empty
tuple (or `None`) for source that will not parse, matching `python_ast.parse_module`,
which records a syntax error rather than raising it.

Built on `python_ast.ImportSite` rather than beside it: `ImportLine` is one import
*statement* as written, and carries the `ImportSite`s for the names it binds.
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional, Sequence

from compliance.extractors.python_ast import ImportSite, PyModule, parse_module

# --- groups -------------------------------------------------------------------------

FUTURE = "future"
STDLIB = "stdlib"
THIRD_PARTY = "third_party"
FIRST_PARTY = "first_party"
LOCAL = "local"

#: The conventional ordering, and only a default -- `GroupPolicy.order` overrides it.
DEFAULT_GROUP_ORDER: tuple[str, ...] = (FUTURE, STDLIB, THIRD_PARTY, FIRST_PARTY, LOCAL)

# Taken from the running interpreter rather than hand-listed. A hand-list is wrong the
# day the interpreter changes, and it would also encode *our* Python version into a
# judgement about somebody else's file. The caller can extend it via `GroupPolicy`.
_STDLIB_NAMES = frozenset(sys.stdlib_module_names)

# --- problem kinds ------------------------------------------------------------------

GROUP_OUT_OF_ORDER = "group_out_of_order"
GROUP_SPLIT = "group_split"
IMPORT_AFTER_FROM = "import_after_from"
NAMES_UNSORTED = "names_unsorted"
NO_PARENTHESES = "no_parentheses"
BACKSLASH_CONTINUATION = "backslash_continuation"
CONTINUATION_INDENT = "continuation_indent"
NO_TRAILING_COMMA = "no_trailing_comma"

# `# noqa`, `# NOQA: F401`, `# noqa:F401,E501`. Case-insensitive because both spellings
# are in wide use, and the codes are captured separately so a rule can ask whether the
# marker actually covers the thing it is excusing.
_MARKER = re.compile(
    r"#\s*noqa(?P<sep>\s*:\s*(?P<codes>[A-Za-z]+[0-9]+(?:\s*,\s*[A-Za-z]+[0-9]+)*))?",
    re.I,
)
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

_CONTEXTS: dict[type, str] = {
    ast.FunctionDef: "function",
    ast.AsyncFunctionDef: "function",
    ast.ClassDef: "class",
    ast.Try: "try",
    ast.If: "conditional",
}
if hasattr(ast, "TryStar"):  # 3.11+
    _CONTEXTS[ast.TryStar] = "try"

_DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


@dataclass(frozen=True)
class GroupPolicy:
    """Which names belong to which group, and the order the groups should appear in.

    Answers: *given this project's configuration, what group is this import in?* The
    caller passes its own first-party package names; there is no built-in list, because
    a built-in list would be one project's answer wearing a generic label.

    `first_party` is consulted before the stdlib, so a project that ships a package
    shadowing a stdlib name is classified the way it declares itself rather than the way
    the interpreter happens to be built.
    """

    first_party: frozenset[str] = frozenset()
    third_party: frozenset[str] = frozenset()
    stdlib: frozenset[str] = frozenset()
    """Additions to the interpreter's own stdlib list, not a replacement for it."""
    order: tuple[str, ...] = DEFAULT_GROUP_ORDER
    default: str = THIRD_PARTY
    """Where an unrecognised top-level name lands. Third party is the safe guess: a
    first-party package is declared, and the stdlib is known, so what is left is
    somebody else's."""

    def __post_init__(self) -> None:
        for name in ("first_party", "third_party", "stdlib"):
            object.__setattr__(self, name, frozenset(getattr(self, name)))
        object.__setattr__(self, "order", tuple(self.order))

    def group_of(self, module: str, level: int = 0) -> str:
        """The group one import belongs to. `level` is the leading-dot count."""
        if level:
            return LOCAL
        root = module.split(".")[0]
        if not root:
            return self.default
        if root == "__future__":
            return FUTURE
        if root in self.first_party:
            return FIRST_PARTY
        if root in self.third_party:
            return THIRD_PARTY
        if root in self.stdlib or root in _STDLIB_NAMES:
            return STDLIB
        return self.default

    def rank(self, group: str) -> int:
        """Position of a group in the declared order; unlisted groups sort last."""
        return self.order.index(group) if group in self.order else len(self.order)


DEFAULT_POLICY = GroupPolicy()


# --- the shapes rules judge ---------------------------------------------------------


@dataclass(frozen=True)
class Problem:
    """One thing that is wrong, and the line it is wrong on.

    A single shape for every check here, because a rule's job is the same in all of
    them: point at a line and say what it found. `other_lineno` is the line that makes
    this one a problem -- the earlier group, the `from` that should have come after.
    """

    kind: str
    lineno: int
    detail: str = ""
    other_lineno: int = 0


@dataclass(frozen=True)
class Wrapping:
    """How a statement was physically typed across one or more lines."""

    lineno: int
    end_lineno: int
    base_indent: int
    """Column the statement itself starts at, so continuation is measured relative."""
    uses_parentheses: bool
    uses_backslash: bool
    trailing_comma: bool
    continuation_indents: tuple[tuple[int, int], ...] = ()
    """(line number, indent column) for each continued line, closing bracket excluded."""
    closing_indent: Optional[int] = None

    @property
    def is_wrapped(self) -> bool:
        return self.end_lineno > self.lineno

    def misindented(self, width: int = 4) -> tuple[tuple[int, int], ...]:
        """Continuation lines that are not `width` columns past the statement."""
        return tuple(
            (lineno, indent)
            for lineno, indent in self.continuation_indents
            if indent != self.base_indent + width
        )

    def indented_by(self, width: int = 4) -> bool:
        return not self.misindented(width)


@dataclass(frozen=True)
class ImportLine:
    """One import *statement* as written: its structure and its formatting."""

    lineno: int
    end_lineno: int
    is_from: bool
    level: int
    """Leading-dot count. 0 for an absolute import."""
    modules: tuple[str, ...]
    """`from a.b import c` -> ('a.b',); `import a, b` -> ('a', 'b')."""
    names: tuple[str, ...]
    """Names as imported, before any `as`."""
    bindings: tuple[str, ...]
    """What the rest of the module calls them, aligned with `names`."""
    aliased: tuple[bool, ...]
    """Whether each name carried an `as`, aligned with `names`."""
    group: str
    groups: tuple[str, ...]
    """Group per module, so a rule can spot one statement that mixes two groups."""
    raw: str
    wrapping: Wrapping
    context: str = "module"
    """`module`, `function`, `class`, `try` or `conditional` -- innermost wins."""
    context_lineno: int = 0
    in_leading_block: bool = False
    """Part of the run of imports at the top of the file, before any other statement."""
    noqa: str = ""
    """The end-of-line suppression comment as written, '' when there is none."""
    noqa_codes: tuple[str, ...] = ()
    noqa_lineno: int = 0
    has_star: bool = False
    sites: tuple[ImportSite, ...] = ()
    node: ast.AST = field(repr=False, default=None)

    @property
    def module(self) -> str:
        """The module imported from; '' for a purely relative `from . import x`."""
        return self.modules[0] if self.modules else ""

    @property
    def is_relative(self) -> bool:
        return self.level > 0

    @property
    def is_absolute(self) -> bool:
        return self.level == 0

    @property
    def dot_depth(self) -> int:
        """How far up the package the import reaches; 0 when absolute."""
        return self.level

    @property
    def is_plain(self) -> bool:
        """`import x` rather than `from x import y`."""
        return not self.is_from

    @property
    def is_top_level(self) -> bool:
        return self.context == "module"

    @property
    def has_noqa(self) -> bool:
        return bool(self.noqa)

    def span(self) -> tuple[int, int]:
        return (self.lineno, self.end_lineno)


@dataclass(frozen=True)
class GroupRun:
    """A maximal run of consecutive imports that all fall in the same group."""

    group: str
    first_lineno: int
    last_lineno: int
    count: int


@dataclass(frozen=True)
class BlankLineReport:
    """Blank-line counts around the leading import block."""

    last_import_lineno: Optional[int] = None
    """Last line of the last statement in the leading import block."""
    next_statement_lineno: Optional[int] = None
    blank_after_imports: Optional[int] = None
    """Blank lines immediately *after* the import block. Measured from the imports, not
    from what follows, so an intervening comment does not silently change the count."""
    first_definition_lineno: Optional[int] = None
    """First line of the first top-level def/class -- its first decorator, if any, since
    that is the line the blank run actually sits above."""
    first_definition_kind: str = ""
    blank_before_first_definition: Optional[int] = None


@dataclass(frozen=True)
class UnusedName:
    """A name an import binds that nothing in the module body appears to use."""

    name: str
    origin: str
    lineno: int
    group: str = ""
    noqa: str = ""
    """The suppression comment on the import line, '' when there is none."""


# --- extraction ---------------------------------------------------------------------


def _module_of(source: Optional[str], module: Optional[PyModule], path: str) -> Optional[PyModule]:
    if module is not None:
        return module
    return parse_module(source, path)


def _walk(node: ast.AST, context: str, context_lineno: int) -> Iterator[tuple[ast.AST, str, int]]:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.Import, ast.ImportFrom)):
            yield child, context, context_lineno
        elif isinstance(child, (ast.stmt, ast.excepthandler)) or type(child).__name__ == "match_case":
            label = _CONTEXTS.get(type(child))
            if label:
                yield from _walk(child, label, getattr(child, "lineno", context_lineno))
            else:
                yield from _walk(child, context, context_lineno)


def _leading_block_lines(tree: ast.AST) -> frozenset[int]:
    """Line numbers of the imports in the run at the top of the module.

    A docstring does not end the block; anything else does. The block is what the
    blank-line and group-order questions are usually about, and a caller that wants
    every import in the file simply ignores this.
    """
    out: set[int] = set()
    body = list(getattr(tree, "body", []))
    start = 1 if body and _is_docstring(body[0]) else 0
    for node in body[start:]:
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            break
        out.add(node.lineno)
    return frozenset(out)


def _is_docstring(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _strip_comment(text: str) -> str:
    """Drop an end-of-line comment. Safe here: an import statement holds no strings."""
    return text.split("#", 1)[0]


def _indent_of(text: str) -> int:
    expanded = text.expandtabs()
    return len(expanded) - len(expanded.lstrip(" "))


def _wrapping(node: ast.AST, text_lines: Sequence[str], is_from: bool) -> Wrapping:
    first, last = node.lineno, getattr(node, "end_lineno", node.lineno)
    physical = list(text_lines[first - 1:last])
    raw = "\n".join(physical)
    body = raw.split("import", 1)[1] if "import" in raw else raw
    uses_parentheses = is_from and "(" in body
    uses_backslash = any(line.rstrip().endswith("\\") for line in physical[:-1])

    continuation: list[tuple[int, int]] = []
    closing: Optional[int] = None
    for offset, line in enumerate(physical[1:], start=1):
        if not line.strip():
            continue
        if line.strip().startswith(")"):
            closing = _indent_of(line)
            continue
        continuation.append((first + offset, _indent_of(line)))

    trailing_comma = False
    if uses_parentheses and ")" in raw:
        inner = raw[raw.index("(") + 1:raw.rindex(")")]
        cleaned = "".join(_strip_comment(line) for line in inner.split("\n"))
        trailing_comma = cleaned.rstrip().endswith(",")

    return Wrapping(
        lineno=first,
        end_lineno=last,
        base_indent=_indent_of(physical[0]) if physical else 0,
        uses_parentheses=uses_parentheses,
        uses_backslash=uses_backslash,
        trailing_comma=trailing_comma,
        continuation_indents=tuple(continuation),
        closing_indent=closing,
    )


def _suppression_on(physical: Sequence[tuple[int, str]]) -> tuple[str, tuple[str, ...], int]:
    for lineno, text in physical:
        if match := _MARKER.search(text):
            codes = match.group("codes") or ""
            return (
                match.group(0).strip(),
                tuple(code.strip() for code in codes.split(",") if code.strip()),
                lineno,
            )
    return ("", (), 0)


def import_lines(
    source: Optional[str] = None,
    policy: Optional[GroupPolicy] = None,
    module: Optional[PyModule] = None,
    path: str = "",
) -> tuple[ImportLine, ...]:
    """Every import statement in the file, in line order, classified and measured.

    Answers: *what does this file import, from where, in what group, written how?* --
    the one call the other functions here build on. Imports nested in functions, classes
    and `try` blocks are included, tagged by `context`, because a rule about where an
    import may appear needs to see the ones in the wrong place.

    Source that does not parse yields an empty tuple, never an exception.
    """
    parsed = _module_of(source, module, path)
    if parsed is None or not parsed.ok:
        return ()
    policy = policy or DEFAULT_POLICY
    text = parsed.source if parsed.source else (source or "")
    text_lines = text.split("\n")
    tree = parsed.tree
    if tree is None:
        return ()

    sites_by_line: dict[int, list[ImportSite]] = {}
    for site in parsed.import_sites:
        sites_by_line.setdefault(site.lineno, []).append(site)
    leading = _leading_block_lines(tree)

    out: list[ImportLine] = []
    for node, context, context_lineno in _walk(tree, "module", 0):
        end = getattr(node, "end_lineno", node.lineno)
        physical = [(n, text_lines[n - 1]) for n in range(node.lineno, end + 1)
                    if 0 < n <= len(text_lines)]
        is_from = isinstance(node, ast.ImportFrom)
        level = getattr(node, "level", 0) or 0
        if is_from:
            modules = (node.module or "",)
        else:
            modules = tuple(alias.name for alias in node.names)
        names = tuple(alias.name for alias in node.names)
        bindings = tuple(
            alias.asname or (alias.name if is_from else alias.name.split(".")[0])
            for alias in node.names
        )
        aliased = tuple(alias.asname is not None for alias in node.names)
        groups = tuple(policy.group_of(name, level) for name in modules)
        noqa, codes, noqa_lineno = _suppression_on(physical)
        out.append(
            ImportLine(
                lineno=node.lineno,
                end_lineno=end,
                is_from=is_from,
                level=level,
                modules=modules,
                names=names,
                bindings=bindings,
                aliased=aliased,
                group=groups[0] if groups else policy.default,
                groups=groups,
                raw="\n".join(line for _, line in physical),
                wrapping=_wrapping(node, text_lines, is_from),
                context=context,
                context_lineno=context_lineno,
                in_leading_block=node.lineno in leading,
                noqa=noqa,
                noqa_codes=codes,
                noqa_lineno=noqa_lineno,
                has_star=any(name == "*" for name in names),
                sites=tuple(sites_by_line.get(node.lineno, ())),
                node=node,
            )
        )
    return tuple(sorted(out, key=lambda line: line.lineno))


def leading_block(lines: Iterable[ImportLine]) -> tuple[ImportLine, ...]:
    """The imports at the top of the file, before any other statement."""
    return tuple(line for line in lines if line.in_leading_block)


def top_level(lines: Iterable[ImportLine]) -> tuple[ImportLine, ...]:
    """Imports in the module body -- not in a function, class, `try` or `if`."""
    return tuple(line for line in lines if line.is_top_level)


# --- group order --------------------------------------------------------------------


def group_runs(lines: Sequence[ImportLine]) -> tuple[GroupRun, ...]:
    """The groups as they actually appear, as consecutive runs.

    Runs rather than a set, because a group appearing twice with something else between
    is a different fault from a group in the wrong place, and only runs preserve it.
    """
    out: list[GroupRun] = []
    for line in lines:
        if out and out[-1].group == line.group:
            previous = out[-1]
            out[-1] = GroupRun(previous.group, previous.first_lineno,
                               max(previous.last_lineno, line.end_lineno),
                               previous.count + 1)
        else:
            out.append(GroupRun(line.group, line.lineno, line.end_lineno, 1))
    return tuple(out)


def group_order_problems(
    lines: Sequence[ImportLine],
    policy: Optional[GroupPolicy] = None,
    order: Optional[Sequence[str]] = None,
) -> list[Problem]:
    """Answers: *do the groups appear in the order this project declares?*

    Two faults, reported separately: a group that follows one it should precede, and a
    group split into two runs. The second is not a mis-ordering -- both runs can be in
    the right place relative to their neighbours -- so folding them together would leave
    a rule unable to say which happened.
    """
    policy = policy or DEFAULT_POLICY
    if order is not None:
        policy = GroupPolicy(
            first_party=policy.first_party, third_party=policy.third_party,
            stdlib=policy.stdlib, order=tuple(order), default=policy.default,
        )
    problems: list[Problem] = []
    runs = group_runs(lines)
    seen: dict[str, int] = {}
    for index, run in enumerate(runs):
        if run.group in seen:
            problems.append(Problem(
                GROUP_SPLIT, run.first_lineno,
                f"{run.group} appears again after another group",
                seen[run.group],
            ))
        else:
            seen[run.group] = run.first_lineno
        if index:
            previous = runs[index - 1]
            if policy.rank(run.group) < policy.rank(previous.group):
                problems.append(Problem(
                    GROUP_OUT_OF_ORDER, run.first_lineno,
                    f"{run.group} follows {previous.group}",
                    previous.first_lineno,
                ))
    return problems


def statement_order_problems(lines: Sequence[ImportLine]) -> list[Problem]:
    """Answers: *within each group, does every `import x` precede every `from x import y`?*

    Judged per run of consecutive same-group imports, so a group that legitimately
    appears once does not inherit the ordering of a different group above it.
    """
    problems: list[Problem] = []
    first_from = 0
    current = None
    for line in lines:
        if line.group != current:
            current, first_from = line.group, 0
        if line.is_from:
            first_from = first_from or line.lineno
        elif first_from:
            problems.append(Problem(
                IMPORT_AFTER_FROM, line.lineno,
                f"plain import follows a from-import in the {line.group} group",
                first_from,
            ))
    return problems


# --- names on one line --------------------------------------------------------------


def name_sort_key(name: str) -> tuple[int, str]:
    """Sort key for the names on one `from x import a, b, C` line.

    The convention is that uppercase-initial names -- constants and classes -- come
    before lowercase ones, and alphabetical within each band. Case-insensitive inside a
    band on purpose: a plain byte-order sort would put `_helper` and `aardvark` in an
    order nobody reading the line would predict.
    """
    return (0 if name[:1].isupper() else 1, name.lower())


def names_are_sorted(names: Sequence[str]) -> bool:
    """Whether these names are already in the order `name_sort_key` describes."""
    return list(names) == sorted(names, key=name_sort_key)


def name_order_problems(lines: Sequence[ImportLine]) -> list[Problem]:
    """Answers: *are the names on each from-import line alphabetised?*

    Sorted on the name as imported, not on the local binding: `from x import b as a, c`
    reads in the order the names are written, which is what someone scanning it sees.
    Star imports and single-name lines are skipped -- there is nothing to order.
    """
    problems: list[Problem] = []
    for line in lines:
        if not line.is_from or line.has_star or len(line.names) < 2:
            continue
        if not names_are_sorted(line.names):
            expected = ", ".join(sorted(line.names, key=name_sort_key))
            problems.append(Problem(NAMES_UNSORTED, line.lineno, f"expected: {expected}"))
    return problems


# --- how a wrapped import is written ------------------------------------------------


def wrapping_problems(
    lines: Sequence[ImportLine],
    indent: int = 4,
    require_parentheses: bool = True,
    require_trailing_comma: bool = True,
) -> list[Problem]:
    """Answers: *is this multi-line import wrapped the way the project asks?*

    Only statements that actually span lines are judged. Each mis-indented continuation
    line gets its own problem at its own line number; the other faults are reported at
    the line the statement opens on, which is where the fix goes.
    """
    problems: list[Problem] = []
    for line in lines:
        wrap = line.wrapping
        if not wrap.is_wrapped:
            continue
        if wrap.uses_backslash:
            problems.append(Problem(BACKSLASH_CONTINUATION, line.lineno,
                                    "continued with a backslash"))
        if require_parentheses and not wrap.uses_parentheses:
            problems.append(Problem(NO_PARENTHESES, line.lineno,
                                    "wrapped without parentheses"))
        for lineno, found in wrap.misindented(indent):
            problems.append(Problem(
                CONTINUATION_INDENT, lineno,
                f"indented {found}, expected {wrap.base_indent + indent}",
                line.lineno,
            ))
        if require_trailing_comma and wrap.uses_parentheses and not wrap.trailing_comma:
            problems.append(Problem(NO_TRAILING_COMMA, line.lineno,
                                    "last name has no trailing comma"))
    return problems


# --- blank lines --------------------------------------------------------------------


def _blank_run_below(text_lines: Sequence[str], lineno: int) -> int:
    count = 0
    index = lineno  # 0-based index of the line after `lineno`
    while index < len(text_lines) and not text_lines[index].strip():
        count += 1
        index += 1
    return count


def _blank_run_above(text_lines: Sequence[str], lineno: int) -> int:
    count = 0
    index = lineno - 2  # 0-based index of the line before `lineno`
    while index >= 0 and not text_lines[index].strip():
        count += 1
        index -= 1
    return count


def _definition_start(node: ast.AST) -> int:
    """First line of a definition, counting decorators -- the line a blank run sits above."""
    decorators = getattr(node, "decorator_list", []) or []
    return min([node.lineno] + [d.lineno for d in decorators])


def blank_line_report(
    source: Optional[str] = None,
    module: Optional[PyModule] = None,
    path: str = "",
) -> Optional[BlankLineReport]:
    """Answers: *how many blank lines separate the imports from what follows?*

    Two measures, because rules ask two different questions: the run directly after the
    import block, and the run directly before the first top-level def/class. They differ
    whenever a constant or a comment sits between the two, which is common enough that
    conflating them would misjudge those files.

    `None` for source that does not parse.
    """
    parsed = _module_of(source, module, path)
    if parsed is None or not parsed.ok or parsed.tree is None:
        return None
    text_lines = (parsed.source if parsed.source else (source or "")).split("\n")
    body = list(parsed.tree.body)
    index = 1 if body and _is_docstring(body[0]) else 0

    last_import: Optional[ast.AST] = None
    while index < len(body) and isinstance(body[index], (ast.Import, ast.ImportFrom)):
        last_import = body[index]
        index += 1
    following = body[index] if index < len(body) else None

    definition = next((node for node in body if isinstance(node, _DEFINITIONS)), None)

    last_lineno = getattr(last_import, "end_lineno", None) if last_import is not None else None
    return BlankLineReport(
        last_import_lineno=last_lineno,
        next_statement_lineno=None if following is None else _definition_start(following),
        blank_after_imports=(None if last_lineno is None
                             else _blank_run_below(text_lines, last_lineno)),
        first_definition_lineno=None if definition is None else _definition_start(definition),
        first_definition_kind=("" if definition is None else
                               "class" if isinstance(definition, ast.ClassDef) else "def"),
        blank_before_first_definition=(
            None if definition is None
            else _blank_run_above(text_lines, _definition_start(definition))
        ),
    )


# --- names nothing uses -------------------------------------------------------------


def _annotation_strings(tree: ast.AST) -> set[str]:
    """Identifiers mentioned inside quoted annotations.

    A forward reference is a string to `ast`, so a name used only in `def f() -> "Thing"`
    would otherwise look unused. Scanned with a plain identifier regex and only inside
    annotation positions -- scanning every string in the file would let a docstring
    mentioning a name mark it used, which is the opposite failure.
    """
    found: set[str] = set()
    for node in ast.walk(tree):
        annotations = []
        for attribute in ("annotation", "returns"):
            value = getattr(node, attribute, None)
            if value is not None:
                annotations.append(value)
        for annotation in annotations:
            for inner in ast.walk(annotation):
                if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                    found.update(_IDENTIFIER.findall(inner.value))
    return found


def _exported(tree: ast.AST) -> set[str]:
    """Names listed in a module-level `__all__`, which are used by being re-exported."""
    out: set[str] = set()
    for node in getattr(tree, "body", []):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        if not any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets):
            continue
        value = getattr(node, "value", None)
        if isinstance(value, (ast.List, ast.Tuple)):
            out.update(item.value for item in value.elts
                       if isinstance(item, ast.Constant) and isinstance(item.value, str))
    return out


def unused_names(
    source: Optional[str] = None,
    policy: Optional[GroupPolicy] = None,
    module: Optional[PyModule] = None,
    path: str = "",
    ignore: Sequence[str] = (),
) -> tuple[UnusedName, ...]:
    """Answers: *which imported names does nothing in this module appear to use?*

    Deliberately under-reports rather than over-reports. Every binding is checked against
    every name used anywhere in the file, ignoring scope, so an import inside one
    function is counted as used when a different function uses that name. Scope-accurate
    analysis is a type checker's job; a rule that accuses an author of an unused import
    had better be right, and a false accusation costs more than a miss.

    Four things are never reported: star imports (nothing can be known about them),
    `__future__` imports (they bind nothing to use), `from x import y as y` (the
    conventional spelling of a deliberate re-export), and anything named in `__all__`.
    Whether an import line carries a suppression comment is reported, not acted on --
    that judgement belongs to the rule.
    """
    parsed = _module_of(source, module, path)
    if parsed is None or not parsed.ok or parsed.tree is None:
        return ()
    tree = parsed.tree
    used: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            used.update(node.names)
    used |= _annotation_strings(tree)
    used |= _exported(tree)
    skip = set(ignore)

    out: list[UnusedName] = []
    for line in import_lines(policy=policy, module=parsed, path=path):
        if line.group == FUTURE:
            continue
        for index, binding in enumerate(line.bindings):
            if line.names[index] == "*":
                continue
            if line.is_from and line.aliased[index] and line.names[index] == binding:
                continue
            if binding in used or binding in skip:
                continue
            origin = (f"{line.module}.{line.names[index]}" if line.is_from and line.module
                      else line.names[index])
            out.append(UnusedName(
                name=binding, origin=origin, lineno=line.lineno,
                group=line.group, noqa=line.noqa,
            ))
    return tuple(out)

"""Python source -> the structures the test and docstring rules judge.

Layer B: shared across Python repositories. Nothing here knows which helper a
particular project wants you to call; rules supply those names.

Everything is derived from ``ast`` plus ``doctest``, both stdlib, so this stays a pure
function of the text it is given.

**A file that does not parse is not a violation.** Three pilot runs produced invalid
Python -- one wrote ``ssert`` for ``assert`` -- and that is missing evidence, not
non-compliance (invariant 6). ``PyModule.ok`` is False and ``error`` carries the reason;
rules must report ``tool_missing``/``parse_error`` rather than fail the agent.

**Line numbers are real file lines**, including inside docstrings. Ownership is decided
by line number (invariant 5), so a doctest example reported one line off can be credited
to the wrong author. ``Docstring.lineno`` is resolved to the file line of the docstring's
first *cleaned* line, which is what ``doctest`` counts from.
"""

from __future__ import annotations

import ast
import doctest
import re
import warnings
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

TEST_PREFIX = "test_"
_TEST_PATH = re.compile(r"(^|/)tests?/|(^|/)test_[^/]+\.py$|_test\.py$")


def is_test_path(path: str) -> bool:
    """Whether a path is a test module by the usual Python conventions."""
    return bool(_TEST_PATH.search(path))


def dotted_name(node: ast.AST) -> str:
    """`pkg.mod.func` from an Attribute/Name chain; '' if the node is neither."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return ""


def span_of(node: ast.AST) -> tuple[int, int]:
    """(first, last) file line of any node with position info."""
    start = getattr(node, "lineno", 0)
    return (start, getattr(node, "end_lineno", None) or start)


@dataclass(frozen=True)
class Decorator:
    name: str
    lineno: int
    keywords: dict[str, Optional[str]] = field(default_factory=dict)
    node: ast.AST = field(repr=False, default=None)


@dataclass(frozen=True)
class ImportSite:
    """One name bound by an import statement, with where it came from."""

    name: str
    """The local binding, i.e. what the rest of the module calls it."""
    origin: str
    """Full dotted path of the thing bound, e.g. `pkg.testing.helpers.raises`."""
    module: str
    """The `from <module> import ...` part, '' for a plain `import`."""
    lineno: int
    is_from: bool
    is_star: bool = False


@dataclass(frozen=True)
class FunctionDef:
    name: str
    lineno: int
    end_lineno: int
    decorators: tuple[Decorator, ...]
    docstring: Optional[str]
    qualname: str = ""
    node: ast.AST = field(repr=False, default=None)

    @property
    def is_test(self) -> bool:
        return self.name.startswith(TEST_PREFIX)

    def has_decorator(self, *names: str) -> bool:
        wanted = {n.lstrip("@") for n in names}
        return any(d.name in wanted or d.name.split(".")[-1] in wanted for d in self.decorators)

    def decorator(self, *names: str) -> Optional[Decorator]:
        wanted = {n.lstrip("@") for n in names}
        for d in self.decorators:
            if d.name in wanted or d.name.split(".")[-1] in wanted:
                return d
        return None

    def span(self) -> tuple[int, int]:
        return (self.lineno, self.end_lineno)


@dataclass(frozen=True)
class CallSite:
    func: str
    """Dotted name as written, e.g. `raises` or `pkg.testing.helpers.raises`."""
    lineno: int
    end_lineno: int = 0
    args: tuple[ast.AST, ...] = field(repr=False, default=())
    keywords: dict[str, ast.AST] = field(repr=False, default_factory=dict)
    enclosing: Optional[str] = None
    node: ast.AST = field(repr=False, default=None)

    @property
    def short(self) -> str:
        return self.func.split(".")[-1]

    def span(self) -> tuple[int, int]:
        return (self.lineno, self.end_lineno or self.lineno)


@dataclass(frozen=True)
class DoctestExample:
    source: str
    want: str
    lineno: int
    """File line of the `>>>` that opens the example."""
    owner: str
    """Qualified name of the function or module whose docstring holds it."""
    end_lineno: int = 0
    indent: int = 0

    def span(self) -> tuple[int, int]:
        return (self.lineno, self.end_lineno or self.lineno)


@dataclass(frozen=True)
class Docstring:
    """One docstring, its position in the file, and the doctest examples inside it."""

    owner: str
    kind: str
    """`module`, `class` or `function`."""
    lineno: int
    """File line of the first line of the *cleaned* text -- what doctest counts from."""
    end_lineno: int
    text: str
    raw: str
    def_span: tuple[int, int]
    """Span of the definition the docstring documents; (1, 1) for a module docstring."""
    def_own_lines: frozenset[int] = frozenset()
    """Lines of that definition minus every nested `def`/`class` inside it.

    This is what ``enclosing`` ownership has to be decided on. A class spans its whole
    body, so editing one method of a 900-line class would otherwise make the agent the
    owner of the class docstring's doctests, which it plainly is not.
    """
    examples: tuple[DoctestExample, ...] = ()
    indent: int = 0

    def span(self) -> tuple[int, int]:
        return (self.lineno, self.end_lineno)

    def lines(self) -> tuple[tuple[int, str], ...]:
        """(file line number, text) for each line of the cleaned docstring."""
        return tuple(
            (self.lineno + offset, line) for offset, line in enumerate(self.text.split("\n"))
        )


@dataclass(frozen=True)
class PyModule:
    path: str
    ok: bool = True
    error: str = ""
    functions: tuple[FunctionDef, ...] = ()
    calls: tuple[CallSite, ...] = ()
    asserts: tuple[ast.Assert, ...] = field(repr=False, default=())
    imports: tuple[str, ...] = ()
    import_sites: tuple[ImportSite, ...] = ()
    import_map: dict[str, str] = field(default_factory=dict)
    tries: tuple[ast.Try, ...] = field(repr=False, default=())
    docstrings: tuple[Docstring, ...] = ()
    doctests: tuple[DoctestExample, ...] = ()
    source: str = field(repr=False, default="")
    tree: ast.AST = field(repr=False, default=None)

    def tests(self) -> tuple[FunctionDef, ...]:
        return tuple(f for f in self.functions if f.is_test)

    def calls_within(self, span: tuple[int, int]) -> tuple[CallSite, ...]:
        lo, hi = span
        return tuple(c for c in self.calls if lo <= c.lineno <= hi)

    def asserts_within(self, span: tuple[int, int]) -> tuple[ast.Assert, ...]:
        lo, hi = span
        return tuple(a for a in self.asserts if lo <= a.lineno <= hi)

    def enclosing_function(self, lineno: int) -> Optional[FunctionDef]:
        """Innermost function whose body spans ``lineno``."""
        best = None
        for f in self.functions:
            if f.lineno <= lineno <= f.end_lineno:
                if best is None or f.lineno > best.lineno:
                    best = f
        return best

    def origin(self, dotted: str) -> str:
        """Resolve a written name through the import table.

        `raises` -> `pkg.testing.helpers.raises` when it was imported from there.
        Names that were never imported come back unchanged, so a rule can still match
        on the short form when the module defines the helper itself.
        """
        if not dotted:
            return dotted
        head, _, rest = dotted.partition(".")
        base = self.import_map.get(head)
        if base is None:
            return dotted
        return f"{base}.{rest}" if rest else base

    def star_imports(self) -> tuple[str, ...]:
        return tuple(s.module for s in self.import_sites if s.is_star)


# --- docstring / doctest position resolution ---------------------------------------


def _cleandoc_offset(raw: str) -> tuple[int, int]:
    """(leading lines ``inspect.cleandoc`` drops, common indent it strips).

    Reimplemented rather than inferred, because the count is what maps a doctest
    example's offset back onto a real file line.
    """
    lines = raw.expandtabs().split("\n")
    margins = [
        len(line) - len(line.lstrip(" ")) for line in lines[1:] if line.strip()
    ]
    margin = min(margins) if margins else 0
    dedented = [lines[0].lstrip(" ")] + [line[margin:] for line in lines[1:]]
    dropped = 0
    while dropped < len(dedented) and not dedented[dropped].strip():
        dropped += 1
    return dropped, margin


def _docstring_node(node: ast.AST) -> Optional[ast.Constant]:
    body = getattr(node, "body", None)
    if not body:
        return None
    first = body[0]
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return first.value
    return None


def _examples_of(text: str, owner: str, first_line: int, indent: int) -> tuple[DoctestExample, ...]:
    if ">>>" not in text:
        return ()
    try:
        parsed = doctest.DocTestParser().get_examples(text)
    except ValueError:
        return ()
    out = []
    for example in parsed:
        start = first_line + example.lineno
        n_source = example.source.count("\n") or 1
        n_want = example.want.count("\n")
        out.append(
            DoctestExample(
                source=example.source,
                want=example.want,
                lineno=start,
                owner=owner,
                end_lineno=start + n_source - 1 + n_want,
                indent=indent + example.indent,
            )
        )
    return tuple(out)


def _own_lines(node: ast.AST, def_span: tuple[int, int]) -> frozenset[int]:
    """Lines of a definition that belong to it directly, not to something nested in it."""
    lines = set(range(def_span[0], def_span[1] + 1))
    for child in ast.walk(node):
        if child is node or not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                                   ast.ClassDef)):
            continue
        start, end = span_of(child)
        lines -= set(range(start, end + 1))
    return frozenset(lines)


def _docstring_of(node: ast.AST, owner: str, kind: str) -> Optional[Docstring]:
    const = _docstring_node(node)
    if const is None:
        return None
    raw = const.value
    text = ast.get_docstring(node, clean=True) or ""
    dropped, margin = _cleandoc_offset(raw)
    first_line = const.lineno + dropped
    def_span = (1, 1) if kind == "module" else span_of(node)
    own = frozenset({1}) if kind == "module" else _own_lines(node, def_span)
    return Docstring(
        owner=owner,
        kind=kind,
        lineno=first_line,
        end_lineno=first_line + max(text.count("\n"), 0),
        text=text,
        raw=raw,
        def_span=def_span,
        def_own_lines=own,
        examples=_examples_of(text, owner, first_line, margin),
        indent=margin,
    )


# --- parsing ------------------------------------------------------------------------


# Two very different failures both leave `ok=False`, and Layer C has to tell them apart:
# the source was never reconstructed (our gap -- withhold), versus the source is in hand and
# is not valid Python (the agent's contribution -- a violation). The discriminator is whether
# `source` survived on the module, and this sentinel names the first case so the test for it
# is not a substring search over an error message that could be reworded.
NO_SOURCE = "no source available"


def parse_module(source: Optional[str], path: str = "") -> PyModule:
    """Parse one Python file. A SyntaxError is recorded, never raised."""
    if source is None:
        return PyModule(path=path, ok=False, error=NO_SOURCE)
    return _parse_cached(source, path)


@lru_cache(maxsize=128)
def _parse_cached(source: str, path: str) -> PyModule:
    """Memoised because every rule re-reads the same handful of files.

    Keyed on the text itself, so it stays a pure function: identical source always
    yields the identical module, whichever rule asked first.
    """
    try:
        # The source belongs to the project under test, not to us. Its invalid escape
        # sequences and other lint are its business; surfacing them as our warnings would
        # bury real output under someone else's noise. Errors are still raised, so a file
        # that does not parse is still reported as such.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            warnings.simplefilter("ignore", DeprecationWarning)
            tree = ast.parse(source)
    except SyntaxError as exc:
        return PyModule(path=path, ok=False,
                        error=f"{exc.msg} (line {exc.lineno})", source=source)

    functions: list[FunctionDef] = []
    calls: list[CallSite] = []
    asserts: list[ast.Assert] = []
    tries: list[ast.Try] = []
    imports: list[str] = []
    import_sites: list[ImportSite] = []
    import_map: dict[str, str] = {}
    docstrings: list[Docstring] = []

    if (module_doc := _docstring_of(tree, path, "module")) is not None:
        docstrings.append(module_doc)

    scope: list[str] = []

    def _bind(site: ImportSite) -> None:
        import_sites.append(site)
        if not site.is_star:
            import_map.setdefault(site.name, site.origin)

    class Visitor(ast.NodeVisitor):
        def _function(self, node):
            scope.append(node.name)
            qualname = ".".join(scope)
            if (doc := _docstring_of(node, qualname, "function")) is not None:
                docstrings.append(doc)
            functions.append(
                FunctionDef(
                    name=node.name,
                    lineno=node.lineno,
                    end_lineno=getattr(node, "end_lineno", node.lineno),
                    decorators=_decorators(node),
                    docstring=ast.get_docstring(node),
                    qualname=qualname,
                    node=node,
                )
            )
            self.generic_visit(node)
            scope.pop()

        visit_FunctionDef = _function
        visit_AsyncFunctionDef = _function

        def visit_ClassDef(self, node):
            scope.append(node.name)
            if (doc := _docstring_of(node, ".".join(scope), "class")) is not None:
                docstrings.append(doc)
            self.generic_visit(node)
            scope.pop()

        def visit_Call(self, node):
            name = dotted_name(node.func)
            if name:
                calls.append(
                    CallSite(
                        func=name,
                        lineno=node.lineno,
                        end_lineno=getattr(node, "end_lineno", node.lineno),
                        args=tuple(node.args),
                        keywords={k.arg: k.value for k in node.keywords if k.arg},
                        enclosing=scope[-1] if scope else None,
                        node=node,
                    )
                )
            self.generic_visit(node)

        def visit_Assert(self, node):
            asserts.append(node)
            self.generic_visit(node)

        def visit_Try(self, node):
            tries.append(node)
            self.generic_visit(node)

        def visit_Import(self, node):
            for alias in node.names:
                imports.append(alias.name)
                _bind(ImportSite(
                    name=alias.asname or alias.name.split(".")[0],
                    origin=alias.name,
                    module="",
                    lineno=node.lineno,
                    is_from=False,
                ))
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            module = node.module or ""
            for alias in node.names:
                full = f"{module}.{alias.name}" if module else alias.name
                imports.append(full)
                _bind(ImportSite(
                    name=alias.asname or alias.name,
                    origin=full,
                    module=module,
                    lineno=node.lineno,
                    is_from=True,
                    is_star=alias.name == "*",
                ))
            self.generic_visit(node)

    Visitor().visit(tree)
    doctests = tuple(e for d in docstrings for e in d.examples)
    return PyModule(
        path=path,
        ok=True,
        functions=tuple(functions),
        calls=tuple(calls),
        asserts=tuple(asserts),
        imports=tuple(imports),
        import_sites=tuple(import_sites),
        import_map=import_map,
        tries=tuple(tries),
        docstrings=tuple(docstrings),
        doctests=doctests,
        source=source,
        tree=tree,
    )


def _decorators(node) -> tuple[Decorator, ...]:
    out = []
    for dec in node.decorator_list:
        if isinstance(dec, ast.Call):
            name = dotted_name(dec.func)
            kw = {k.arg: _literal(k.value) for k in dec.keywords if k.arg}
        else:
            name, kw = dotted_name(dec), {}
        if name:
            out.append(Decorator(name, getattr(dec, "lineno", node.lineno), kw, dec))
    return tuple(out)


def _literal(node: ast.AST) -> Optional[str]:
    try:
        return repr(ast.literal_eval(node))
    except (ValueError, SyntaxError):
        return None


def parse_changed_files(bundle, only_python: bool = True) -> dict[str, PyModule]:
    """Parse every file in the contribution, keyed by path.

    Reads ``head_text``, which the builder populates by reconstruction. Files with no
    reconstructed text come back with ``ok=False`` so rules can distinguish "the agent
    wrote something wrong" from "we could not read what the agent wrote".
    """
    out: dict[str, PyModule] = {}
    for path, change in sorted(bundle.files.items()):
        if only_python and not path.endswith(".py"):
            continue
        out[path] = parse_module(change.head_text, path)
    return out

"""scikit-learn: helpers shared across the rule modules. Not a rule module.

Layer C, and deliberately thin. Anything a second project would want belongs in
`compliance/extractors/`; what is left is scikit-learn's own vocabulary -- where its
package, tests, gallery, user guide and changelog fragments live -- which
`docs/checker-authoring.md` §3 keeps local.

Two things here are *nearly* general and are kept local on purpose:

* the Cython reader (`cython_text`, `cython_defs`, `memoryview_names`). Cython is not
  Python and `ast` cannot parse it, so the `.pyx`/`.pxd` rules read text. No other pack
  legislates Cython, so §7.4's bar for a shared extractor -- "the project legislates
  something no previous one did, *and* it can be parameterised" -- is met only halfway:
  it is new, but a text scanner tuned to one dialect is not yet a parameterised extractor.
* `classes()`, which walks the AST for class definitions. `extractors/python_ast.py`
  exposes functions, docstrings, imports and call sites but not classes, and more than
  fifty of this pack's rules are about an estimator class. Adding `classes` to the shared
  extractor is the right move and is reported as a shared-layer request rather than made
  here.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Optional

from compliance.core import ownership as own
from compliance.core.models import Command, EvidenceBundle, Target
from compliance.extractors import docstrings as ds
from compliance.extractors import python_ast as pa

# --- where things live --------------------------------------------------------------

PACKAGE = "sklearn/"
DOC_ROOT = "doc/"
USER_GUIDE_ROOT = "doc/modules/"
EXAMPLES_ROOT = "examples/"
API_REFERENCE_FILE = "doc/api_reference.py"
CHANGELOG_DIR = "doc/whats_new/upcoming_changes/"

#: The seven fragment types the upcoming_changes README publishes, verbatim (C269).
FRAGMENT_TYPES = ("major-feature", "feature", "efficiency", "enhancement", "fix", "api",
                  "other")

#: Topic folders the same README names beside the `sklearn.<module>` ones (C270).
FRAGMENT_TOPIC_FOLDERS = ("array-api", "metadata-routing", "security", "custom-top-level",
                          "many-modules", "sklearn")

CYTHON_SUFFIXES = (".pyx", ".pxd", ".pyx.tp", ".pxd.tp", ".pxi")
COMPILED_SUFFIXES = CYTHON_SUFFIXES + (".c", ".cpp", ".cc", ".h", ".hpp")
DOC_SUFFIXES = (".rst", ".md")

#: Configuration the pull-request CI reads. Used by C235, which is about that file set.
CI_PATHS = (".github/workflows/", "build_tools/", "azure-pipelines.yml",
            ".circleci/config.yml", ".github/actions/")

#: `sklearn.utils._testing` is private but is the location the project's own testing
#: rules point at (C197), so C184 must not read an import from it as a private-location
#: import. Named here so the exemption is one constant rather than a repeated literal.
SANCTIONED_PRIVATE_TEST_MODULES = ("sklearn.utils._testing", "sklearn.conftest",
                                   "sklearn.utils.fixes")


# --- target construction ------------------------------------------------------------


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

    Fires on having submitted something, never on having done the thing the rule is
    about (§7.1). One target, payload the bundle, ownership ``touched``.
    """
    if not bundle.files:
        return []
    return [target(f"{prefix}:{bundle.instance_id}", None, None, bundle,
                   snippet or f"{len(bundle.files)} file(s) in the contribution")]


# --- path vocabulary ----------------------------------------------------------------


def is_test_path(path: str) -> bool:
    """A pytest-discoverable module in one of the package's `tests/` subdirectories."""
    return "/tests/" in path and path.rsplit("/", 1)[-1].startswith("test_")


def in_package(path: str) -> bool:
    return path.startswith(PACKAGE)


def is_cython(path: str) -> bool:
    return path.endswith(CYTHON_SUFFIXES)


def changed_under(bundle: EvidenceBundle, prefix: str,
                  suffixes: tuple[str, ...] = ()) -> list[str]:
    return [p for p in sorted(bundle.files)
            if p.startswith(prefix) and (not suffixes or p.endswith(suffixes))]


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


def cython_files(bundle: EvidenceBundle, *, mode: str = "touched") -> list[str]:
    return [p for p in sorted(bundle.files)
            if is_cython(p) and own.owns_file(bundle, p, mode)]


def source_files(bundle: EvidenceBundle, *, mode: str = "touched") -> list[str]:
    """Package code that is not a test -- what "a change to scikit-learn" means."""
    return [p for p in python_files(bundle, mode=mode, tests=False) if in_package(p)]


def doc_files(bundle: EvidenceBundle) -> list[str]:
    return [p for p in changed_under(bundle, DOC_ROOT) if p.endswith(DOC_SUFFIXES)]


def rst_files(bundle: EvidenceBundle, *, mode: str = "touched") -> list[str]:
    return [p for p in sorted(bundle.files)
            if p.endswith(".rst") and own.owns_file(bundle, p, mode)]


def user_guide_files(bundle: EvidenceBundle, *, mode: str = "touched") -> list[str]:
    """Narrative documentation: the user-guide tree, plus any other `doc/` reST page.

    `doc/whats_new/` is excluded because a changelog is not documentation -- the same
    narrowing sphinx-doc needed between its C005 and C030 (spec §7.5). Without it a
    changelog fragment would be graded by every user-guide rule in this module.
    """
    return [p for p in rst_files(bundle, mode=mode)
            if p.startswith(DOC_ROOT) and not p.startswith("doc/whats_new/")]


def example_files(bundle: EvidenceBundle, *, mode: str = "touched") -> list[str]:
    return [p for p in sorted(bundle.files)
            if p.startswith(EXAMPLES_ROOT) and p.endswith(".py")
            and own.owns_file(bundle, p, mode)]


def changelog_fragments(bundle: EvidenceBundle, *, mode: str = "created") -> list[str]:
    """Files added under `doc/whats_new/upcoming_changes/`, README and .gitkeep aside."""
    out = []
    for path in changed_under(bundle, CHANGELOG_DIR):
        name = path.rsplit("/", 1)[-1]
        if name in ("README.md", ".gitkeep") or not own.owns_file(bundle, path, mode):
            continue
        out.append(path)
    return out


def ci_files(bundle: EvidenceBundle, *, mode: str = "touched") -> list[str]:
    return [p for p in sorted(bundle.files)
            if p.startswith(CI_PATHS) and own.owns_file(bundle, p, mode)]


# --- file text ----------------------------------------------------------------------


def added_text(bundle: EvidenceBundle, path: str) -> str:
    change = bundle.files.get(path)
    if change is None:
        return ""
    return "\n".join(text for _, text in change.added_lines)


def added_lines(bundle: EvidenceBundle, path: str) -> tuple[tuple[int, str], ...]:
    change = bundle.files.get(path)
    return change.added_lines if change else ()


def file_text(bundle: EvidenceBundle, path: str) -> str:
    """The post-patch text when it was reconstructed, else the lines the agent wrote."""
    change = bundle.files.get(path)
    if change is None:
        return ""
    return change.head_text if change.head_text is not None else added_text(bundle, path)


def numbered_lines(text: str) -> tuple[tuple[int, str], ...]:
    return tuple(enumerate(text.split("\n"), start=1))


def head_lines(bundle: EvidenceBundle, path: str) -> tuple[tuple[int, str], ...]:
    change = bundle.files.get(path)
    if change is None:
        return ()
    if change.head_text is not None:
        return numbered_lines(change.head_text)
    return change.added_lines


def modules(bundle: EvidenceBundle, *, mode: str = "touched",
            tests: Optional[bool] = None) -> list[tuple[str, pa.PyModule]]:
    """(path, PyModule) for each owned Python file that parses."""
    out = []
    for path in python_files(bundle, mode=mode, tests=tests):
        text = bundle.files[path].head_text
        if text is None:
            continue
        module = pa.parse_module(text, path)
        if module.ok:
            out.append((path, module))
    return out


def base_module(bundle: EvidenceBundle, path: str) -> Optional[pa.PyModule]:
    """The same file as it stood at the base commit, when the tree was available."""
    change = bundle.files.get(path)
    if change is None or change.base_text is None:
        return None
    module = pa.parse_module(change.base_text, path)
    return module if module.ok else None


# --- docstrings ---------------------------------------------------------------------


def owned_docstrings(bundle: EvidenceBundle, *, mode: str = "touched",
                     tests: Optional[bool] = None,
                     kinds: tuple[str, ...] = ("function", "class", "module"),
                     ) -> list[tuple[str, pa.PyModule, pa.Docstring]]:
    """Docstrings the agent wrote or edited (spec §4.3)."""
    out = []
    for path, module in modules(bundle, tests=tests):
        for doc in module.docstrings:
            if doc.kind not in kinds or not doc.text.strip():
                continue
            if own.owns_span(bundle, path, doc.span(), mode):
                out.append((path, module, doc))
    return out


def numpydoc(doc: pa.Docstring) -> ds.Doc:
    return ds.parse(doc.lines())


@dataclass(frozen=True)
class ParamEntry:
    """One `name : type` line of a numpydoc Parameters/Attributes section."""

    names: str
    type_text: str
    lineno: int
    description: tuple[tuple[int, str], ...] = ()

    def description_text(self) -> str:
        return " ".join(t.strip() for _, t in self.description).strip()


#: `name : type, default=...`, at the section's own indentation. numpydoc's own shape.
_PARAM_LINE = re.compile(r"^(?P<indent>\s*)(?P<names>[*\w][\w, *]*?)\s+:\s?(?P<type>.*)$")


def parameter_entries(section: ds.Section) -> list[ParamEntry]:
    """The `name : type` entries of a numpydoc section, with their description lines."""
    body = list(section.body)
    entries: list[tuple[int, str, str, int]] = []
    for index, (lineno, text) in enumerate(body):
        match = _PARAM_LINE.match(text)
        if match and match.group("type").strip():
            entries.append((index, match.group("names").strip(),
                            match.group("type").strip(), lineno))
    out = []
    for order, (index, names, type_text, lineno) in enumerate(entries):
        end = entries[order + 1][0] if order + 1 < len(entries) else len(body)
        out.append(ParamEntry(names=names, type_text=type_text, lineno=lineno,
                              description=tuple(body[index + 1:end])))
    return out


# --- classes ------------------------------------------------------------------------


@dataclass(frozen=True)
class ClassInfo:
    name: str
    lineno: int
    end_lineno: int
    bases: tuple[str, ...]
    decorators: tuple[str, ...]
    docstring: Optional[str]
    node: ast.ClassDef = field(repr=False, default=None)
    methods: dict[str, ast.AST] = field(repr=False, default_factory=dict)

    def span(self) -> tuple[int, int]:
        return (self.lineno, self.end_lineno)

    def method(self, name: str) -> Optional[ast.AST]:
        return self.methods.get(name)

    def inherits(self, *names: str) -> bool:
        wanted = set(names)
        return any(b in wanted or b.split(".")[-1] in wanted for b in self.bases)


def classes(module: pa.PyModule) -> list[ClassInfo]:
    """Every class definition in a parsed module, nested ones included."""
    if module.tree is None:
        return []
    out = []
    for node in ast.walk(module.tree):
        if not isinstance(node, ast.ClassDef):
            continue
        methods = {child.name: child for child in node.body
                   if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))}
        out.append(ClassInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=getattr(node, "end_lineno", node.lineno),
            bases=tuple(pa.dotted_name(b) for b in node.bases),
            decorators=tuple(pa.dotted_name(d.func if isinstance(d, ast.Call) else d)
                             for d in node.decorator_list),
            docstring=ast.get_docstring(node),
            node=node,
            methods=methods,
        ))
    return out


def owned_classes(bundle: EvidenceBundle, *, mode: str = "touched",
                  tests: Optional[bool] = None,
                  ) -> list[tuple[str, pa.PyModule, ClassInfo]]:
    out = []
    for path, module in modules(bundle, tests=tests):
        for info in classes(module):
            if own.owns_span(bundle, path, info.span(), mode):
                out.append((path, module, info))
    return out


ESTIMATOR_BASES = ("BaseEstimator", "TransformerMixin", "ClassifierMixin",
                   "RegressorMixin", "ClusterMixin", "BiclusterMixin", "OutlierMixin",
                   "DensityMixin", "MetaEstimatorMixin", "MultiOutputMixin")


def is_estimator(info: ClassInfo) -> bool:
    """An estimator by the project's own definition: it fits, or it claims the base.

    A proxy -- the corpus says "estimator" and scikit-learn has no marker a checker can
    read -- so every rule selecting on it declares ``heuristic=True`` (§6.3).
    """
    return "fit" in info.methods or info.inherits(*ESTIMATOR_BASES)


def decorator_names(node: ast.AST) -> tuple[str, ...]:
    return tuple(pa.dotted_name(d.func if isinstance(d, ast.Call) else d)
                 for d in getattr(node, "decorator_list", ()))


def parameters(node: ast.AST) -> list[str]:
    """Positional-or-keyword parameter names of a function, `self` included."""
    args = getattr(node, "args", None)
    if args is None:
        return []
    return [a.arg for a in list(args.posonlyargs) + list(args.args)]


def keyword_defaults(node: ast.AST) -> dict[str, ast.AST]:
    """Parameters that carry a default, mapped to the default expression."""
    args = getattr(node, "args", None)
    if args is None:
        return {}
    positional = list(args.posonlyargs) + list(args.args)
    out: dict[str, ast.AST] = {}
    for arg, default in zip(positional[len(positional) - len(args.defaults):],
                            args.defaults):
        out[arg.arg] = default
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        if default is not None:
            out[arg.arg] = default
    return out


def self_assignments(node: ast.AST) -> dict[str, ast.AST]:
    """`self.<name> = <value>` inside a method, mapped to the assigned expression."""
    out: dict[str, ast.AST] = {}
    for child in ast.walk(node):
        targets = []
        if isinstance(child, ast.Assign):
            targets = child.targets
        elif isinstance(child, (ast.AnnAssign, ast.AugAssign)):
            targets = [child.target]
        for element in targets:
            for leaf in ast.walk(element):
                if (isinstance(leaf, ast.Attribute)
                        and isinstance(leaf.value, ast.Name)
                        and leaf.value.id == "self"):
                    out.setdefault(leaf.attr, getattr(child, "value", child))
    return out


def returns_self(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if (isinstance(child, ast.Return) and isinstance(child.value, ast.Name)
                and child.value.id == "self"):
            return True
    return False


def calls_in(node: ast.AST) -> list[str]:
    return [pa.dotted_name(child.func) for child in ast.walk(node)
            if isinstance(child, ast.Call)]


# --- deprecations -------------------------------------------------------------------

_DEPRECATED_DIRECTIVE = re.compile(r"^\s*\.\.\s+deprecated::", re.M)
_VERSIONCHANGED = re.compile(r"^\s*\.\.\s+versionchanged::", re.M)


def deprecation_decorators(module: pa.PyModule) -> list[pa.FunctionDef]:
    """Functions and methods carrying `@deprecated(...)`."""
    return [f for f in module.functions if f.has_decorator("deprecated")]


def deprecated_names(bundle: EvidenceBundle) -> dict[str, str]:
    """Names this contribution deprecates -> the path that deprecates them.

    Read from `@deprecated` decorators and `@deprecated` classes in the agent's own
    Python files. A proxy for "a deprecation was introduced": a deprecation announced
    only in prose, or only by a hand-rolled ``FutureWarning``, is not seen here.
    """
    found: dict[str, str] = {}
    for path, module in modules(bundle, tests=False):
        for function in deprecation_decorators(module):
            found.setdefault(function.name, path)
        for info in classes(module):
            if any(d.split(".")[-1] == "deprecated" for d in info.decorators):
                found.setdefault(info.name, path)
    return found


def raises_future_warning(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and pa.dotted_name(child.func).endswith("warn"):
            for arg in list(child.args) + [k.value for k in child.keywords]:
                if isinstance(arg, ast.Name) and arg.id == "FutureWarning":
                    return True
                if isinstance(arg, ast.Attribute) and arg.attr == "FutureWarning":
                    return True
    return False


def has_deprecated_directive(text: str) -> bool:
    return bool(_DEPRECATED_DIRECTIVE.search(text or ""))


def has_versionchanged_directive(text: str) -> bool:
    return bool(_VERSIONCHANGED.search(text or ""))


# --- Cython -------------------------------------------------------------------------

_CY_COMMENT = re.compile(r"#.*$")
#: `cdef`/`cpdef`/`def` at any indentation, with the name that follows.
_CY_DEF = re.compile(r"^(?P<indent>\s*)(?P<kind>cpdef|cdef|def)\s+(?P<rest>.*)$")
_CY_FUNC_NAME = re.compile(r"(?P<name>\w+)\s*\((?P<params>.*)$")
#: A memoryview declaration: a type followed by `[...]` with a colon inside the brackets.
_CY_MEMORYVIEW = re.compile(r"(?P<type>[\w.]+)\s*\[(?P<dims>[^\]]*:[^\]]*)\]\s+(?P<name>\w+)")
_CY_CLASS = re.compile(r"^(?P<indent>\s*)cdef\s+class\s+(?P<name>\w+)\s*(\((?P<bases>[^)]*)\))?\s*:")


def cython_text(bundle: EvidenceBundle, path: str) -> str:
    return file_text(bundle, path)


def code_lines(text: str) -> list[tuple[int, str]]:
    """Numbered lines with comments stripped -- enough for the text-level Cython rules."""
    return [(n, _CY_COMMENT.sub("", line))
            for n, line in enumerate(text.split("\n"), start=1)]


@dataclass(frozen=True)
class CyDef:
    kind: str
    name: str
    params: str
    lineno: int
    indent: int
    line: str


def _balanced(text: str) -> str:
    """The parameter list between a `(` already consumed and its matching `)`.

    Written out rather than stripped off the end of the line, because a Cython signature
    carries qualifiers after the closing parenthesis -- `) noexcept nogil:` -- and taking
    the whole tail read those qualifiers as a parameter.
    """
    depth, out = 0, []
    for char in text:
        if char == ")" and depth == 0:
            break
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        out.append(char)
    return "".join(out)


def cython_defs(text: str) -> list[CyDef]:
    """`def`/`cdef`/`cpdef` function definitions in Cython source, read textually."""
    out = []
    for lineno, line in code_lines(text):
        match = _CY_DEF.match(line)
        if not match or match.group("rest").startswith(("class ", "extern", "packed")):
            continue
        name_match = _CY_FUNC_NAME.search(match.group("rest"))
        if not name_match:
            continue
        out.append(CyDef(kind=match.group("kind"), name=name_match.group("name"),
                         params=_balanced(name_match.group("params")),
                         lineno=lineno, indent=len(match.group("indent")), line=line))
    return out


@dataclass(frozen=True)
class CyClass:
    name: str
    bases: tuple[str, ...]
    lineno: int
    decorators: tuple[str, ...]


def cython_classes(text: str) -> list[CyClass]:
    lines = code_lines(text)
    out = []
    for index, (lineno, line) in enumerate(lines):
        match = _CY_CLASS.match(line)
        if not match:
            continue
        decorators = []
        back = index - 1
        while back >= 0 and lines[back][1].strip().startswith("@"):
            decorators.append(lines[back][1].strip().lstrip("@").split("(")[0])
            back -= 1
        bases = tuple(b.strip() for b in (match.group("bases") or "").split(",")
                      if b.strip())
        out.append(CyClass(name=match.group("name"), bases=bases, lineno=lineno,
                           decorators=tuple(decorators)))
    return out


def memoryview_names(text: str) -> dict[str, int]:
    """Variables declared as a typed memoryview -> the line declaring them."""
    out: dict[str, int] = {}
    for lineno, line in code_lines(text):
        for match in _CY_MEMORYVIEW.finditer(line):
            out.setdefault(match.group("name"), lineno)
    return out

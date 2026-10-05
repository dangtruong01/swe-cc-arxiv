"""matplotlib: helpers shared across the rule modules. Not a rule module.

Layer C, and deliberately thin. Anything a second project would want belongs in
`compliance/extractors/`; what is left is Matplotlib's own vocabulary -- where its
package, tests, galleries, baseline images and release notes live -- which
`docs/checker-authoring.md` §3 keeps local.

**Two corpus/repository mismatches are recorded here rather than corrected (§0).**

* The corpus names :file:`doc/release/next_whats_new/` as the What's new directory
  (C220, C230). Every SWE-bench matplotlib instance predates that move and uses
  :file:`doc/users/next_whats_new/`. Both spellings are accepted, and the rules that
  depend on it declare ``heuristic=True`` for accepting the alternative form (§6.2).
* The corpus writes the gallery sources as :file:`doc/gallery`, :file:`doc/tutorials`
  and so on (C001). The tree carries the *sources* under :file:`galleries/` and only the
  *generated* pages under :file:`doc/`. C001 is about the generated pages, so it is coded
  against the paths its own sentence names; ``GALLERY_SOURCE_ROOTS`` below is what the
  other gallery rules select on.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional

from compliance.core import ownership as own
from compliance.core.models import Command, EvidenceBundle, Target

# --- where things live ----------------------------------------------------------------

PACKAGE_ROOTS = ("lib/matplotlib/", "lib/mpl_toolkits/")
TEST_ROOT = "lib/matplotlib/tests/"
BASELINE_DIR = "baseline_images"
DOC_ROOT = "doc/"
#: Gallery, tutorial and plot-types *sources*: executable ``.py`` under `galleries/`,
#: with the pre-3.8 layout kept because the SWE-bench instances are older than the move.
GALLERY_SOURCE_ROOTS = ("galleries/examples/", "galleries/tutorials/",
                        "galleries/plot_types/", "galleries/users_explain/",
                        "examples/", "tutorials/", "plot_types/")
PLOT_TYPES_ROOTS = ("galleries/plot_types/", "plot_types/")
EXTERN_ROOT = "extern/"
LICENSE_ROOT = "LICENSE/"

RCSETUP = "lib/matplotlib/rcsetup.py"
MATPLOTLIBRC = "lib/matplotlib/mpl-data/matplotlibrc"
TYPING_STUB = "lib/matplotlib/typing.py"
PYPLOT = "lib/matplotlib/pyplot.py"
BOILERPLATE = "tools/boilerplate.py"

#: Release-note trees. The first What's new spelling is the corpus's, the second the
#: one every instance in the benchmark actually has -- see the module docstring.
WHATS_NEW_DIRS = ("doc/release/next_whats_new/", "doc/users/next_whats_new/")
API_CHANGE_ROOT = "doc/api/next_api_changes/"
API_CHANGE_KINDS = ("deprecations", "removals", "behavior", "development")
#: Aggregated release notes: an entry written straight into one of these is an entry
#: that was not filed as its own note.
RELEASE_AGGREGATES = ("doc/users/whats_new.rst", "doc/api/api_changes.rst")
RELEASE_AGGREGATE_PREFIXES = ("doc/users/prev_whats_new/", "doc/api/prev_api_changes/")

DOC_SUFFIXES = (".rst",)
C_SUFFIXES = (".c", ".cpp", ".cc", ".h", ".hpp", ".m", ".mm")

# --- vocabulary -----------------------------------------------------------------------

#: The ``_api`` deprecation helpers, by the kind of API each is for (C207).
DEPRECATION_HELPERS = ("deprecated", "warn_deprecated", "deprecate_privatize_attribute",
                       "rename_parameter", "delete_parameter", "make_keyword_only")
_DEPRECATION_RE = re.compile(r"\b(?:_api\.)?(" + "|".join(DEPRECATION_HELPERS) + r")\s*\(")
_PENDING_RE = re.compile(r"\bpending\s*=\s*True\b")

#: A reST cross-reference: an explicit role, or a trailing-underscore hyperlink.
XREF = re.compile(r":[a-z+:-]+:`[^`]+`|(?<![`\w])`[^`]+`_")
#: ``literal`` -- double backticks, which is what a code object in a title must use.
DOUBLE_BACKTICK = re.compile(r"``[^`]+``")

_UNDERLINE = re.compile(r'^\s*([*=\-^"~+#`\'_:.])\1{1,}\s*$')


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

    Fires on having submitted something, never on having produced the artefact the rule
    is about (§7.1). One target, payload the bundle, ownership ``touched``.
    """
    if not bundle.files:
        return []
    return [target(f"{prefix}:{bundle.instance_id}", None, None, bundle,
                   snippet or f"{len(bundle.files)} file(s) in the contribution")]


# --- path predicates ------------------------------------------------------------------


def is_package_path(path: str) -> bool:
    return path.startswith(PACKAGE_ROOTS)


def is_test_path(path: str) -> bool:
    return "/tests/" in path and path.endswith(".py")


def is_gallery_path(path: str) -> bool:
    return path.startswith(GALLERY_SOURCE_ROOTS) and path.endswith(".py")


def is_plot_types_path(path: str) -> bool:
    return path.startswith(PLOT_TYPES_ROOTS) and path.endswith(".py")


def is_baseline_image(path: str) -> bool:
    return f"/{BASELINE_DIR}/" in path


def is_release_note(path: str) -> bool:
    return path.startswith(WHATS_NEW_DIRS) or path.startswith(API_CHANGE_ROOT)


def is_whats_new(path: str) -> bool:
    return path.startswith(WHATS_NEW_DIRS)


def is_c_source(path: str) -> bool:
    return path.endswith(C_SUFFIXES)


def is_prose_path(path: str) -> bool:
    """A page of narrative documentation: reST under `doc/`, or a gallery narrative."""
    return (path.startswith(DOC_ROOT) and path.endswith(DOC_SUFFIXES)) or is_gallery_path(path)


# --- file access ----------------------------------------------------------------------


def changed(bundle: EvidenceBundle, predicate) -> list[str]:
    return [p for p in sorted(bundle.files) if predicate(p)]


def owned(bundle: EvidenceBundle, predicate, mode: str = "touched") -> list[str]:
    return [p for p in sorted(bundle.files)
            if predicate(p) and own.owns_file(bundle, p, mode)]


def added_lines(bundle: EvidenceBundle, path: str) -> tuple[tuple[int, str], ...]:
    change = bundle.files.get(path)
    return change.added_lines if change else ()


def added_text(bundle: EvidenceBundle, path: str) -> str:
    return "\n".join(text for _, text in added_lines(bundle, path))


def removed_text(bundle: EvidenceBundle, path: str) -> str:
    change = bundle.files.get(path)
    return "\n".join(change.removed_lines) if change else ""


def head_lines(bundle: EvidenceBundle, path: str) -> tuple[tuple[int, str], ...]:
    """(line number, text) for the whole post-patch file, or () if unreconstructed."""
    change = bundle.files.get(path)
    if change is None or change.head_text is None:
        return ()
    return tuple(enumerate(change.head_text.split("\n"), start=1))


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


def modules(bundle: EvidenceBundle, *, mode: str = "touched",
            tests: Optional[bool] = None):
    """(path, PyModule) for each owned Python file that parses."""
    from compliance.extractors import python_ast as pa

    out = []
    for path in python_files(bundle, mode=mode, tests=tests):
        module = pa.parse_module(bundle.files[path].head_text, path)
        if module.ok:
            out.append((path, module))
    return out


def classes(module) -> list:
    """ClassDef nodes of a parsed module. `python_ast` exposes functions, not classes."""
    import ast

    if module.tree is None:
        return []
    return [n for n in ast.walk(module.tree) if isinstance(n, ast.ClassDef)]


# --- release notes --------------------------------------------------------------------


def release_notes_added(bundle: EvidenceBundle) -> list[str]:
    """New files in either release-note tree -- the entries this contribution filed."""
    return [p for p in sorted(bundle.files)
            if is_release_note(p) and bundle.files[p].is_new]


def api_change_notes_added(bundle: EvidenceBundle) -> list[str]:
    return [p for p in release_notes_added(bundle) if p.startswith(API_CHANGE_ROOT)]


def whats_new_added(bundle: EvidenceBundle) -> list[str]:
    return [p for p in release_notes_added(bundle) if is_whats_new(p)]


def note_kind(path: str) -> str:
    """The `next_api_changes` subdirectory a note sits in, '' when it sits in none."""
    if not path.startswith(API_CHANGE_ROOT):
        return ""
    rest = path[len(API_CHANGE_ROOT):].split("/")
    return rest[0] if len(rest) > 1 else ""


def titles_of(lines: Iterable[tuple[int, str]]) -> list[tuple[int, str]]:
    """(line number, title text) for each reST section title in ``lines``.

    A title is a line followed by an underline of repeated punctuation at least as
    long as it is; an overline above it is skipped rather than reported twice.
    """
    rows = list(lines)
    out: list[tuple[int, str]] = []
    for index, (number, text) in enumerate(rows):
        if index + 1 >= len(rows):
            continue
        below = rows[index + 1][1]
        if not text.strip() or _UNDERLINE.match(text):
            continue
        if _UNDERLINE.match(below) and len(below.strip()) >= len(text.strip()) - 1:
            out.append((number, text.strip()))
    return out


# --- deprecation vocabulary -----------------------------------------------------------


def deprecation_sites(text: str) -> list[str]:
    """Every `_api` deprecation helper named in ``text``, in order of appearance."""
    return _DEPRECATION_RE.findall(text)


def introduces_deprecation(bundle: EvidenceBundle) -> list[str]:
    """Package files where the agent *added* a deprecation helper call."""
    return [p for p in python_files(bundle)
            if is_package_path(p) and deprecation_sites(added_text(bundle, p))]


def expires_deprecation(bundle: EvidenceBundle) -> list[str]:
    """Package files where the agent *removed* a deprecation helper call.

    Expiring a deprecation is deleting the deprecated API together with its helper, so
    the evidence is on the minus side of the diff (`removed_lines`).
    """
    return [p for p in python_files(bundle)
            if is_package_path(p) and deprecation_sites(removed_text(bundle, p))]


def introduces_pending_deprecation(bundle: EvidenceBundle) -> list[str]:
    return [p for p in introduces_deprecation(bundle)
            if _PENDING_RE.search(added_text(bundle, p))]


# --- minimum supported versions -------------------------------------------------------

#: The six files C286 names for a Python bump. The CI entry is a group rather than a
#: path -- the sentence says "CI configuration files (circle, GHA, azure)" -- so it is
#: matched by prefix.
MIN_PYTHON_FILES = ("pyproject.toml", "environment.yml", "doc/install/dependencies.rst",
                    "doc/devel/min_dep_policy.rst", "<ci>", "tox.ini")
#: The six C287 names for a NumPy bump. A different list: `minver.txt` and
#: `_check_versions()` appear here and nowhere else.
MIN_NUMPY_FILES = ("pyproject.toml", "environment.yml", "doc/install/dependencies.rst",
                   "doc/devel/min_dep_policy.rst", "requirements/testing/minver.txt",
                   "lib/matplotlib/__init__.py")

_CI_CONFIG = re.compile(r"^\.circleci/|^\.github/workflows/|^azure-pipelines\.yml$")

_PYTHON_MIN = re.compile(r"requires-python|python_requires|target-version"
                         r"|Programming Language :: Python :: 3", re.I)
_NUMPY_MIN = re.compile(r"numpy\s*[><=~!]{1,2}\s*[\d.]|_check_versions|\bnumpy\b.*\bmin",
                        re.I)


def satisfies_min_file(bundle: EvidenceBundle, entry: str) -> bool:
    """Whether the contribution touches the file (or file group) ``entry`` names."""
    if entry == "<ci>":
        return any(_CI_CONFIG.search(p) for p in bundle.files)
    return entry in bundle.files


def raises_min_python(bundle: EvidenceBundle) -> bool:
    """Whether the contribution moves the minimum Python version.

    A proxy: the fields the policy page names are matched in the added lines of the
    files that carry them. A bump written some other way is not seen.
    """
    for path in ("pyproject.toml", "environment.yml", "tox.ini",
                 "doc/devel/min_dep_policy.rst"):
        if path in bundle.files and _PYTHON_MIN.search(added_text(bundle, path)):
            return True
    return False


def raises_min_numpy(bundle: EvidenceBundle) -> bool:
    """Whether the contribution moves the minimum NumPy version. Same proxy as above."""
    for path in ("pyproject.toml", "environment.yml", "requirements/testing/minver.txt",
                 "lib/matplotlib/__init__.py", "doc/devel/min_dep_policy.rst"):
        if path in bundle.files and _NUMPY_MIN.search(added_text(bundle, path)):
            return True
    return False


# --- new public API -------------------------------------------------------------------


def new_public_defs(bundle: EvidenceBundle) -> list[tuple[str, str, int]]:
    """(path, name, line) for each public function or class the agent added to the
    package.

    "Added" means the whole definition header is on a line the agent wrote, which is what
    distinguishes a new definition from an edit inside an existing one. Private names --
    a leading underscore -- are excluded because the rules that use this are about
    *public* API.
    """
    out = []
    for path, module in modules(bundle, tests=False):
        if not is_package_path(path):
            continue
        authored = bundle.files[path].authored_lines
        for function in module.functions:
            if function.lineno in authored and not function.name.startswith("_"):
                out.append((path, function.qualname or function.name, function.lineno))
        for node in classes(module):
            if node.lineno in authored and not node.name.startswith("_"):
                out.append((path, node.name, node.lineno))
    return out


def new_rcparams(bundle: EvidenceBundle) -> list[str]:
    """rcParam keys the agent added to the `_validators` table in `rcsetup.py`."""
    if RCSETUP not in bundle.files:
        return []
    keys = []
    for _, text in added_lines(bundle, RCSETUP):
        if match := re.match(r"""\s*["']([a-z0-9_]+(?:\.[a-z0-9_]+)+)["']\s*:""", text):
            keys.append(match.group(1))
    return keys


# --- decorators -----------------------------------------------------------------------

IMAGE_COMPARISON = "image_comparison"
CHECK_FIGURES_EQUAL = "check_figures_equal"


def decorator_argument(dec, index: int, name: str):
    """The AST node of a decorator argument, by keyword name or positional index.

    `python_ast.Decorator` keeps keyword *literals* and the call node; positional
    arguments -- which is how ``@image_comparison(['x.png'])`` names its baselines --
    are only on the node, so both are read from there.
    """
    import ast

    node = dec.node
    if not isinstance(node, ast.Call):
        return None
    for keyword in node.keywords:
        if keyword.arg == name:
            return keyword.value
    if index is not None and len(node.args) > index:
        return node.args[index]
    return None


def literal_of(node):
    """`ast.literal_eval` on a node, or None when it is not a literal."""
    import ast

    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError, TypeError):
        return None


def baseline_images(dec) -> Optional[list]:
    """The baseline image names an ``image_comparison`` decorator declares."""
    value = literal_of(decorator_argument(dec, 0, "baseline_images"))
    if isinstance(value, (list, tuple)):
        return list(value)
    return None


def function_source(module, function) -> str:
    """The source text of one function definition."""
    lines = module.source.split("\n")
    return "\n".join(lines[function.lineno - 1:function.end_lineno])


def parameter_names(function) -> list[str]:
    """Every parameter name of a FunctionDef, positional and keyword-only."""
    import ast

    node = function.node
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []
    args = node.args
    names = [a.arg for a in list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs)]
    return names


# --- parse failures --------------------------------------------------------------------


def unparseable(bundle: EvidenceBundle) -> list[str]:
    """Submitted Python files that do not parse. Only the agent's own files count.

    A module the agent ships that will not compile provably fails every lint hook, which
    is what lets a rule graded off a tool report still record one side without the tool.
    """
    from compliance.extractors import python_ast as pa

    broken = []
    for path in python_files(bundle):
        text = bundle.files[path].head_text
        if text is None:
            continue
        module = pa.parse_module(text, path)
        if not module.ok and module.error != pa.NO_SOURCE:
            broken.append(f"{path} ({module.error})")
    return broken


# --- functions, tests and call sites ----------------------------------------------------

TEST_PREFIX = "test_"
TEST_CLASS_PREFIX = "Test"


def owned_functions(bundle: EvidenceBundle, *, mode: str = "touched",
                    tests: Optional[bool] = None):
    """(path, PyModule, FunctionDef) for each function the agent's edit reaches."""
    out = []
    for path, module in modules(bundle, mode=mode, tests=tests):
        for function in module.functions:
            if own.owns_span(bundle, path, function.span(), mode):
                out.append((path, module, function))
    return out


def test_functions(bundle: EvidenceBundle, *, mode: str = "touched"):
    """Functions in test modules the agent wrote that pytest would collect."""
    return [(p, m, f) for p, m, f in owned_functions(bundle, mode=mode, tests=True)
            if f.name.startswith(TEST_PREFIX)]


def calls_in(node) -> list[str]:
    """Dotted names of every call inside an AST node, in source order."""
    import ast

    from compliance.extractors import python_ast as pa

    return [pa.dotted_name(child.func) for child in ast.walk(node)
            if isinstance(child, ast.Call)]


def call_nodes_in(node):
    """Every ``ast.Call`` inside an AST node, paired with its dotted name."""
    import ast

    from compliance.extractors import python_ast as pa

    return [(pa.dotted_name(child.func), child) for child in ast.walk(node)
            if isinstance(child, ast.Call)]


def decorator_names(node) -> tuple[str, ...]:
    import ast

    from compliance.extractors import python_ast as pa

    return tuple(pa.dotted_name(d.func if isinstance(d, ast.Call) else d)
                 for d in getattr(node, "decorator_list", ()))


def source_files(bundle: EvidenceBundle, *, mode: str = "touched") -> list[str]:
    """Library modules the agent edited: package Python that is not a test."""
    return [p for p in python_files(bundle, mode=mode, tests=False)
            if is_package_path(p)]


# --- prose ------------------------------------------------------------------------------

#: reST inline markup that is *code*, not prose: an explicit role, a literal, a
#: hyperlink target, a URL. The terminology rules must not read a class name as a word.
_MARKUP = re.compile(r"``[^`]*``|:[a-z+:-]+:`[^`]*`|`[^`]*`_+|https?://\S+"
                     r"|\|[A-Za-z]+\|")
#: A line that carries no prose at all: a directive, an option, an underline, a comment
#: marker, or a doctest prompt.
_NON_PROSE = re.compile(r"^\s*(\.\.\s|:[\w-]+:|>>>|\.\.\.\s|#\s*%%|\|)")


def strip_markup(text: str) -> str:
    """``text`` with reST code markup blanked out, so only prose words remain."""
    return _MARKUP.sub(" ", text)


def prose_lines(bundle: EvidenceBundle) -> list[tuple[str, int, str]]:
    """(path, line number, text) for each line of prose the agent wrote.

    Prose is narrative the reader reads: an added line of a reST page, and a docstring
    line inside a Python file the agent authored. Code markup is left in place here and
    removed by ``strip_markup`` at the point of use, so a rule that wants the raw line
    still has it.
    """
    from compliance.extractors import python_ast as pa

    out: list[tuple[str, int, str]] = []
    for path in sorted(bundle.files):
        change = bundle.files[path]
        if path.endswith(DOC_SUFFIXES):
            for number, text in added_lines(bundle, path):
                if text.strip() and not _NON_PROSE.match(text):
                    out.append((path, number, text))
        elif path.endswith(".py"):
            module = pa.parse_module(change.head_text, path)
            if not module.ok:
                continue
            for doc in module.docstrings:
                for number, text in doc.lines():
                    if (number in change.authored_lines and text.strip()
                            and not _NON_PROSE.match(text)):
                        out.append((path, number, text))
    return out


# --- documentation surfaces ---------------------------------------------------------------

from dataclasses import dataclass  # noqa: E402  (used only by the docstring helpers)


def doc_pages(bundle: EvidenceBundle, *, mode: str = "touched") -> list[str]:
    """reST pages under `doc/` the agent's edit reaches."""
    return owned(bundle, lambda p: p.startswith(DOC_ROOT) and p.endswith(DOC_SUFFIXES),
                 mode)


def gallery_examples(bundle: EvidenceBundle, *, mode: str = "touched") -> list[str]:
    """Executable gallery, tutorial and plot-types sources the agent's edit reaches."""
    return owned(bundle, is_gallery_path, mode)


def page_lines(bundle: EvidenceBundle, path: str):
    """Whole-file lines when the patch reconstructs the file, else the added ones."""
    return head_lines(bundle, path) or added_lines(bundle, path)


def owned_docstrings(bundle: EvidenceBundle, *, mode: str = "touched",
                     tests: Optional[bool] = None):
    """(path, PyModule, Docstring, FunctionDef|None) for docstrings the agent's edit
    reaches.

    The fourth element is the function a function docstring documents, so a rule about a
    parameter can reach the signature without re-walking the tree. It is ``None`` for
    module and class docstrings.
    """
    out = []
    for path, module in modules(bundle, mode=mode, tests=tests):
        by_line = {f.lineno: f for f in module.functions}
        for doc in module.docstrings:
            if not own.owns_span(bundle, path, doc.span(), mode):
                continue
            out.append((path, module, doc, by_line.get(doc.def_span[0])))
    return out


def numpydoc(doc):
    from compliance.extractors import docstrings as ds

    return ds.parse(doc.lines())


@dataclass(frozen=True)
class ParamEntry:
    """One ``name : type`` line of a numpydoc Parameters or Returns section."""

    names: str
    type_text: str
    lineno: int
    description: tuple[tuple[int, str], ...] = ()

    def description_text(self) -> str:
        return " ".join(text.strip() for _, text in self.description).strip()


_PARAM_LINE = re.compile(r"^(?P<indent>\s*)(?P<names>[*\w][\w, *]*?)\s+:\s?(?P<type>.*)$")


def parameter_entries(section) -> list[ParamEntry]:
    """The ``name : type`` entries of a numpydoc section, with their description lines."""
    body = list(section.body)
    found: list[tuple[int, str, str, int]] = []
    for index, (number, text) in enumerate(body):
        match = _PARAM_LINE.match(text)
        if match and match.group("type").strip():
            found.append((index, match.group("names").strip(),
                          match.group("type").strip(), number))
    out = []
    for order, (index, names, type_text, number) in enumerate(found):
        end = found[order + 1][0] if order + 1 < len(found) else len(body)
        out.append(ParamEntry(names=names, type_text=type_text, lineno=number,
                              description=tuple(body[index + 1:end])))
    return out

"""astropy: Tests and test style -- 30 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

The largest category in this corpus, and three things shape it.

**Half of these rules name a marker, a flag or a directive, and the trap is identical in
every one.** *"Mark a test that retrieves remote data with ``@pytest.mark.remote_data``"*
is not a rule about that decorator: a pre-condition selecting decorated tests would record
a pass for every target and could never find the omission the rule exists to catch, and one
selecting undecorated tests could only ever fail (§7.1). So each of these fires on the
*situation* -- a test that fetches over the network, a doctest whose output is a float, an
example that cannot run -- and the grading asks whether the marker is there. Those
situations are proxies, which is why most of this module is ``heuristic=True``.

**The doctest rules read a single scanner.** ``_examples`` walks docstring and narrative
prompt blocks alike and yields the same view of each: source, expected output and the
``# doctest:`` flags on the prompt line. astropy legislates doctests in both places and its
sentences do not distinguish them, so neither does this module.

**Three rules are ``differential`` and none of them pretends otherwise.** C025 fails on a
doctest that is not valid Python -- decidable, and conclusive -- and withholds on the rest,
declaring ``doctest_run``. C037 fails a contribution that ships no test at all, because no
run is needed to know that no test went from failing to passing, and withholds where one
exists. C205 reads the harness's own before-and-after report: a regression there is
conclusive, and a clean report is reported as a pass with the caveat -- declared
``heuristic`` -- that the harness ran the instance's subset rather than the whole suite. It
is the one of the three that grades both ways, because a real execution is what it reads.

**Corpus mismatch, recorded rather than corrected (§0, §5).** C036 is filed ``trajectory``
and reads ``commands``, which agrees. C001 is filed ``differential`` -- an unhandled
``ResourceWarning`` really is a runtime fact -- and is graded from the patch by a proxy,
declared ``heuristic`` rather than withheld, because an unclosed file in a test is visible
in the source and failing to say so would cost the rule its whole fail path.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from compliance.core import ownership as own
from compliance.core.models import (EvidenceBundle, Satisfied, Target, Undetermined,
                                    Violated)
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.astropy._common import (PACKAGE, SHARED_TEST_DIR, added_lines,
                                              is_doc_path, is_source_path, modules,
                                              owned_files, python_files, ran,
                                              subpackage_of, target)

CATEGORY = "Tests and test style"

# --- astropy's test vocabulary ---------------------------------------------------------

TEST_DIR = "/tests/"
TEST_MODULE_NAME = re.compile(r"^(test_.+|.+_test)\.py$")
NOT_A_TEST_MODULE = ("__init__.py", "conftest.py", "setup_package.py")

REMOTE_DATA_MARK = ("pytest.mark.remote_data", "remote_data")
FIGURE_TEST = ("figure_test", "astropy.tests.figures.figure_test")
MPL_IMAGE_COMPARE = ("pytest.mark.mpl_image_compare", "mpl_image_compare")
SKIPIF = ("pytest.mark.skipif", "skipif")

#: Calls that reach the network, which is what "retrieves remote data" looks like in code.
REMOTE_CALLS = ("download_file", "get_readable_fileobj", "urlopen", "urlretrieve",
                "get_file_contents", "requests.get", "get", "conf.download_cache")
_URL_LITERAL = re.compile(r"https?://|ftp://")

#: Calls that write a file from inside a test.
WRITE_CALLS = ("writeto", "to_file", "savetxt", "savefig", "save", "write", "dump",
               "write_text", "write_bytes", "mkdir", "touch")
TMP_FIXTURES = ("tmp_path", "tmp_path_factory", "tmpdir", "tmpdir_factory", "tmp_dir")

OPTIONAL_PACKAGES = ("scipy", "matplotlib", "h5py", "yaml", "bs4", "beautifulsoup4",
                     "asdf", "dask", "pandas", "pyarrow", "jplephem", "sortedcontainers",
                     "html5lib", "bleach", "mpmath", "skyfield")
HAS_FLAG = re.compile(r"\bHAS_[A-Z0-9_]+\b")
OPTIONAL_DEPS_MODULE = "astropy.utils.compat.optional_deps"

WARNING_ASSERTIONS = ("pytest.warns", "warnings.catch_warnings", "assert_warns",
                      "catch_warnings", "warns")
EXCEPTION_ASSERTIONS = ("pytest.raises", "assertRaises", "assertRaisesRegex",
                        "assert_raises", "raises")

PRAGMA = re.compile(r"#\s*pragma\s*:?(?P<body>[^\n]*)")
NO_COVER = re.compile(r"^\s*:?\s*no cover\s*$")

DOCTEST_SKIP_DIRECTIVE = re.compile(r"^\s*\.\.\s+doctest-skip(-all)?::?")
DOCTEST_REQUIRES_DIRECTIVE = re.compile(r"^\s*\.\.\s+doctest-requires::")
DOCTEST_FLAG = re.compile(r"#\s*doctest:\s*(?P<flags>[^\n]+)")
FLOAT_LITERAL = re.compile(r"(?<![\w.])[-+]?\d+\.\d+(?:[eE][-+]?\d+)?(?![\w.])")
PLACEHOLDER = re.compile(r"path/to|/path/|your[_ ]|<[a-zA-Z][^>]*>|\.\.\.\s*$|filename\.")

DOCTEST_SKIP_VARIABLE = "__doctest_skip__"
DOCTEST_REQUIRES_VARIABLE = "__doctest_requires__"

REMOTE_DATA_FLAG = "REMOTE_DATA"
SKIP_FLAG = "SKIP"
IGNORE_OUTPUT_FLAG = "IGNORE_OUTPUT"
FLOAT_CMP_FLAG = "FLOAT_CMP"

PYTEST_REMOTE_DATA = re.compile(r"\bpytest\b[^\n]*--remote-data\b|\btox\b[^\n]*--remote-data\b")

_PROMPT = re.compile(r"^(?P<indent>\s*)>>> ?(?P<code>.*)$")
_CONTINUATION = re.compile(r"^\s*\.\.\. ?(?P<code>.*)$")


# --- shared selection ---------------------------------------------------------------


def _authored(bundle: EvidenceBundle, path: str) -> frozenset[int]:
    change = bundle.files.get(path)
    return change.authored_lines if change else frozenset()


def _in_test_directory(path: str) -> bool:
    return TEST_DIR in path or path.startswith("tests/")


def _is_test_module(path: str) -> bool:
    """A module pytest collects, by location or by name."""
    name = path.rsplit("/", 1)[-1]
    if name in NOT_A_TEST_MODULE:
        return False
    return path.endswith(".py") and (_in_test_directory(path)
                                     or bool(TEST_MODULE_NAME.match(name)))


def _test_modules(bundle: EvidenceBundle, *, mode: str = "touched"):
    for path, module in modules(bundle, mode=mode):
        if _is_test_module(path):
            yield path, module


def _library_modules(bundle: EvidenceBundle):
    return [(p, m) for p, m in modules(bundle) if is_source_path(p)]


def _looks_like_a_test(function: pa.FunctionDef, module: pa.PyModule) -> bool:
    """A function that asserts something, whatever it is called.

    The pre-condition for C003 cannot be "its name starts with ``test_``" -- that is the
    compliant form -- so what makes a function a test here is that it makes an assertion
    or carries a pytest marker.
    """
    if function.name.startswith("test") or function.decorators:
        return True
    return bool(module.asserts_within(function.span()))


def _written_tests(bundle: EvidenceBundle, *, mode: str = "touched"):
    """(path, module, function) for each test the agent wrote."""
    for path, module in _test_modules(bundle, mode=mode):
        for function in module.functions:
            if not _looks_like_a_test(function, module):
                continue
            if own.owns_span(bundle, path, function.span(), mode):
                yield path, module, function


def _decorator_names(function: pa.FunctionDef) -> list[str]:
    return [d.name for d in function.decorators]


def _has_mark(function: pa.FunctionDef, names: tuple[str, ...]) -> bool:
    return any(name.split(".")[-1] == wanted.split(".")[-1]
               for name in _decorator_names(function) for wanted in names)


@dataclass(frozen=True)
class Example:
    """One doctest prompt block, from a docstring or from a narrative page."""

    path: str
    lineno: int
    source: str
    want: str
    prompt: str

    def flags(self) -> str:
        match = DOCTEST_FLAG.search(self.prompt)
        return match.group("flags") if match else ""

    def has_flag(self, name: str) -> bool:
        return f"+{name}" in self.flags()


def _scan_examples(path: str, lines: list[tuple[int, str]],
                   authored: frozenset[int]) -> list[Example]:
    out: list[Example] = []
    index = 0
    while index < len(lines):
        lineno, text = lines[index]
        prompt = _PROMPT.match(text)
        index += 1
        if not prompt:
            continue
        source = [prompt.group("code")]
        while index < len(lines):
            continuation = _CONTINUATION.match(lines[index][1])
            # A bare `...` carrying no code is expected *output* elided wholesale, not a
            # continuation of the statement. Reading it as a continuation is what hid
            # C032's whole antecedent, so the two are separated here rather than in the
            # rule.
            if not continuation or not continuation.group("code").strip():
                break
            source.append(continuation.group("code"))
            index += 1
        want: list[str] = []
        while index < len(lines):
            following = lines[index][1]
            if not following.strip() or _PROMPT.match(following):
                break
            want.append(following.strip())
            index += 1
        if lineno in authored:
            out.append(Example(path, lineno, "\n".join(source), "\n".join(want), text))
    return out


def _examples(bundle: EvidenceBundle) -> list[Example]:
    """Every doctest example the agent wrote, in docstrings and in narrative pages."""
    out: list[Example] = []
    for path, module in modules(bundle):
        authored = _authored(bundle, path)
        for doc in module.docstrings:
            out.extend(_scan_examples(path, list(doc.lines()), authored))
    for path, change in owned_files(bundle, is_doc_path):
        if change.head_text is None:
            continue
        lines = [(n, line) for n, line in enumerate(change.head_text.split("\n"), start=1)]
        out.extend(_scan_examples(path, lines, change.authored_lines))
    return out


def _calls_in(module: pa.PyModule, function: pa.FunctionDef) -> tuple[pa.CallSite, ...]:
    return module.calls_within(function.span())


def _short_calls(module: pa.PyModule, function: pa.FunctionDef) -> list[str]:
    return [c.func.split(".")[-1] for c in _calls_in(module, function)]


def _function_source(module: pa.PyModule, function: pa.FunctionDef) -> str:
    return ast.dump(function.node) if function.node is not None else ""


def _parameters(function: pa.FunctionDef) -> list[str]:
    node = function.node
    if node is None:
        return []
    args = node.args
    return [a.arg for a in list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs)]


# =========================================================================== placement


@rule(
    id="ASTROPY-C002",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "name test modules" is a decision taken on creation
    reads=("files",),  # spec §5: the path is the whole question
)
class TestModulesAreNamedForDiscovery:
    """Pre-condition: each Python module the agent added inside a ``tests`` directory.
    Pass condition: its name is ``test_*.py`` or ``*_test.py``.

    Not heuristic: pytest's two discovery patterns are quoted in the corpus sentence and
    compared against exactly. Selecting on *location* rather than on the name is what makes
    the rule able to fail -- a pre-condition keyed on the name would select only modules
    that already comply (§7.1). ``__init__.py`` and ``conftest.py`` are excluded because
    pytest never collects them as test modules.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b, mode="created"):
            name = path.rsplit("/", 1)[-1]
            if _in_test_directory(path) and name not in NOT_A_TEST_MODULE:
                out.append(target(f"test-name:{path}", path, None, path, path))
        return out

    def pass_condition(self, t: Target):
        path = t.payload
        name = path.rsplit("/", 1)[-1]
        if TEST_MODULE_NAME.match(name):
            return Satisfied(f"{name} matches pytest's discovery patterns")
        return Violated(f"{name} is neither test_*.py nor *_test.py, so pytest collects "
                        f"nothing from it")


@rule(
    id="ASTROPY-C003",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a function the agent wrote
    reads=("files",),  # spec §5
    heuristic=True,
)
class TestFunctionsArePrefixed:
    """Pre-condition: each function the agent added to a test module that asserts something
    or carries a pytest marker.
    Pass condition: its name starts with ``test_``.

    Heuristic on the **pre-condition** (§6.3): *a test function* is approximated by one that
    makes an assertion or is decorated, because keying on the name would select only the
    compliant form and the rule could never fail (§7.1). A helper that happens to assert is
    selected here and is not a test.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"test-prefix:{path}:{function.lineno}", path, function.span(),
                       (path, function), function.name)
                for path, module, function in _written_tests(b, mode="created")]

    def pass_condition(self, t: Target):
        path, function = t.payload
        if function.name.startswith("test_"):
            return Satisfied(f"{path}:{function.lineno} `{function.name}` is prefixed")
        return Violated(f"{path}:{function.lineno} `{function.name}` asserts but is not "
                        f"prefixed `test_`, so pytest never runs it")


@rule(
    id="ASTROPY-C004",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class TestClassesArePrefixedAndHaveNoInit:
    """Pre-condition: each class the agent added to a test module that holds test methods.
    Pass condition: its name starts with ``Test`` and it defines no ``__init__``.

    Heuristic on the **pre-condition** (§6.3): *a test class* is approximated by one whose
    methods assert or are named for tests, because keying on the ``Test`` prefix would
    select only the compliant form (§7.1). A fixture-holding base class whose methods
    assert is selected here and is not itself collected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _test_modules(b, mode="created"):
            for node in ast.walk(module.tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                methods = [c for c in node.body
                           if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef))]
                holds_tests = any(m.name.startswith("test")
                                  or module.asserts_within(pa.span_of(m)) for m in methods)
                if not holds_tests:
                    continue
                if own.owns_span(b, path, pa.span_of(node), "created"):
                    out.append(target(f"test-class:{path}:{node.lineno}", path,
                                      pa.span_of(node),
                                      (path, node.name, node.lineno,
                                       [m.name for m in methods]), node.name))
        return out

    def pass_condition(self, t: Target):
        path, name, lineno, methods = t.payload
        if not name.startswith("Test"):
            return Violated(f"{path}:{lineno} test class `{name}` has no `Test` prefix, so "
                            f"pytest never collects it")
        if "__init__" in methods:
            return Violated(f"{path}:{lineno} test class `{name}` defines __init__, which "
                            f"stops pytest collecting it")
        return Satisfied(f"{path}:{lineno} `{name}` is prefixed and has no __init__")


@rule(
    id="ASTROPY-C006",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- where a test module goes is decided when it is added
    reads=("files",),  # spec §5
)
class SubPackageTestsLiveInItsTestsDirectory:
    """Pre-condition: each test module the agent added inside ``astropy/``.
    Pass condition: it sits in a ``tests`` directory.

    Not heuristic: both halves are read off the path. Selecting on the module being a test
    -- by name or by location -- rather than on its directory is what lets a correctly
    placed module record a pass (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"test-location:{path}", path, None, path, path)
                for path in python_files(b, mode="created")
                if path.startswith(PACKAGE) and _is_test_module(path)]

    def pass_condition(self, t: Target):
        path = t.payload
        if TEST_DIR in path:
            return Satisfied(f"{path} is inside a tests directory")
        return Violated(f"{path} is a test module outside any tests directory")


@rule(
    id="ASTROPY-C007",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the directory is one the agent is populating
    reads=("files",),  # spec §5
    heuristic=True,
)
class TestsDirectoriesCarryAnInitFile:
    """Pre-condition: each ``tests`` directory the agent added a file to.
    Pass condition: an ``__init__.py`` for it is in the contribution, or the contribution
    also edits a file that was already there.

    Heuristic on the **pass condition** (§6.2): the tree outside the patch is not visible,
    so "the directory has an ``__init__.py``" is inferred -- either the contribution adds
    one, or it edits a pre-existing file in the same directory, which shows the directory
    already existed and therefore already has one. A brand-new tests directory with no
    ``__init__.py`` is the case this really catches.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        directories: dict[str, list[str]] = {}
        for path in python_files(b, mode="created"):
            if not _in_test_directory(path):
                continue
            directories.setdefault(path.rsplit("/", 1)[0], []).append(path)
        return [target(f"tests-init:{directory}", directory + "/", None, (directory, b),
                       f"{len(paths)} new file(s) in {directory}")
                for directory, paths in sorted(directories.items())]

    def pass_condition(self, t: Target):
        directory, bundle = t.payload
        init = f"{directory}/__init__.py"
        if init in bundle.files:
            return Satisfied(f"{init} is in the contribution")
        for path, change in bundle.files.items():
            if path.rsplit("/", 1)[0] == directory and not change.is_new:
                return Satisfied(f"{directory} already existed; {path} is edited, not added")
        return Violated(f"{directory} is a new tests directory with no __init__.py, so its "
                        f"tests cannot be imported")


@rule(
    id="ASTROPY-C008",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class CrossSubPackageTestsLiveInAstropyTests:
    """Pre-condition: each test module the agent added that imports from two or more
    astropy sub-packages.
    Pass condition: it sits in ``astropy/tests/``.

    Heuristic on the **pre-condition** (§6.3): *involving two or more sub-packages* is
    approximated by what the module imports, which over-fires on a test that imports a
    second sub-package only for a helper, and under-fires on one that reaches another
    sub-package through the object it is given.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _test_modules(b, mode="created"):
            packages = set()
            for site in module.import_sites:
                parts = site.origin.split(".")
                if parts[0] == "astropy" and len(parts) > 1:
                    packages.add(parts[1])
            if len(packages) >= 2:
                out.append(target(f"cross-package:{path}", path, None,
                                  (path, sorted(packages)),
                                  f"imports {', '.join(sorted(packages))}"))
        return out

    def pass_condition(self, t: Target):
        path, packages = t.payload
        if path.startswith(SHARED_TEST_DIR):
            return Satisfied(f"{path} is in {SHARED_TEST_DIR}")
        return Violated(f"{path} spans {', '.join(packages)} and is not in "
                        f"{SHARED_TEST_DIR}")


# =========================================================================== test bodies


@rule(
    id="ASTROPY-C010",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the regression test is what the agent wrote
    reads=("files",),  # spec §5
    heuristic=True,
)
class RegressionTestsCiteTheIssueUrl:
    """Pre-condition: each test the agent added alongside a change to library code, which
    is what a regression test looks like.
    Pass condition: the test carries the URL of the report.

    Heuristic on **both layers** (§6.1). *A regression test* is approximated by a test
    added in the same contribution as a source change, so a test added with a new feature
    is selected too. And the URL is looked for anywhere in the test's text, so a bare issue
    number -- which is not what the sentence asks for -- reads as missing.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not [p for p, _ in _library_modules(b)]:
            return []
        out = []
        for path, module, function in _written_tests(b, mode="created"):
            text = "\n".join(line for n, line in added_lines(b, path)
                             if function.lineno <= n <= function.end_lineno)
            out.append(target(f"issue-url:{path}:{function.lineno}", path, function.span(),
                              (path, function, text), function.name))
        return out

    def pass_condition(self, t: Target):
        path, function, text = t.payload
        body = text + "\n" + (function.docstring or "")
        if match := _URL_LITERAL.search(body):
            return Satisfied(f"{path}:{function.lineno} cites the report at "
                             f"{body[match.start():match.start() + 60].split()[0]}")
        return Violated(f"{path}:{function.lineno} `{function.name}` is a regression test "
                        f"citing no report URL")


@rule(
    id="ASTROPY-C012",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier; an edited test is in scope
    reads=("files",),  # spec §5
    heuristic=True,
)
class RemoteDataTestsAreMarked:
    """Pre-condition: each test the agent wrote or edited that reaches the network.
    Pass condition: it carries ``@pytest.mark.remote_data``.

    Heuristic on the **pre-condition** (§6.3): *may retrieve remote data* is approximated by
    the download helpers astropy tests use and by a URL literal in the body. A test that
    fetches through a helper of its own is missed, and one that merely mentions a URL in a
    comment is over-selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in _written_tests(b):
            source = _function_source(module, function)
            calls = _short_calls(module, function)
            if any(c in REMOTE_CALLS for c in calls) or _URL_LITERAL.search(source):
                out.append(target(f"remote-data:{path}:{function.lineno}", path,
                                  function.span(), (path, function), function.name))
        return out

    def pass_condition(self, t: Target):
        path, function = t.payload
        if _has_mark(function, REMOTE_DATA_MARK):
            return Satisfied(f"{path}:{function.lineno} is marked remote_data")
        return Violated(f"{path}:{function.lineno} `{function.name}` retrieves remote data "
                        f"without @pytest.mark.remote_data")


@rule(
    id="ASTROPY-C014",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class TestsWriteIntoTmpPath:
    """Pre-condition: each test the agent wrote or edited that creates a file.
    Pass condition: it takes a temporary-directory fixture and uses it.

    Heuristic on **both layers** (§6.1). *Writing a file* is approximated by the call names
    that do it -- ``open`` in a writing mode, ``writeto``, ``savefig``, ``write_text`` --
    so a test writing through something else is missed. And using the fixture is
    approximated by requesting it as a parameter, which does not prove the path written to
    was derived from it.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in _written_tests(b):
            writes = False
            for call in _calls_in(module, function):
                short = call.func.split(".")[-1]
                if short == "open":
                    modes = [a.value for a in call.args
                             if isinstance(a, ast.Constant) and isinstance(a.value, str)]
                    writes = writes or any("w" in m or "a" in m or "x" in m for m in modes)
                elif short in WRITE_CALLS:
                    writes = True
            if writes:
                out.append(target(f"tmp-path:{path}:{function.lineno}", path,
                                  function.span(), (path, function), function.name))
        return out

    def pass_condition(self, t: Target):
        path, function = t.payload
        fixtures = [p for p in _parameters(function) if p in TMP_FIXTURES]
        if fixtures:
            return Satisfied(f"{path}:{function.lineno} writes into the `{fixtures[0]}` "
                             f"fixture directory")
        return Violated(f"{path}:{function.lineno} `{function.name}` creates a file without "
                        f"taking a tmp_path fixture, so the file is not cleaned up")


@rule(
    id="ASTROPY-C016",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class OptionalDependencyTestsAreSkippable:
    """Pre-condition: each test the agent wrote or edited that uses an optional dependency.
    Pass condition: it is skipped when the dependency is absent -- a ``skipif`` marker or
    an ``importorskip`` call.

    Heuristic on the **pre-condition** (§6.3): *requires an optional dependency* is
    approximated by a list of the packages astropy treats as optional, appearing in the
    test's own text or among the module's imports. A dependency outside the list is missed.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in _written_tests(b):
            source = _function_source(module, function)
            used = [name for name in OPTIONAL_PACKAGES
                    if name in source or any(site.origin.split(".")[0] == name
                                             for site in module.import_sites)]
            if used:
                out.append(target(f"optional-skip:{path}:{function.lineno}", path,
                                  function.span(), (path, module, function, used[0]),
                                  function.name))
        return out

    def pass_condition(self, t: Target):
        path, module, function, package = t.payload
        if _has_mark(function, SKIPIF):
            return Satisfied(f"{path}:{function.lineno} is skipped when `{package}` is "
                             f"absent")
        for call in module.calls:
            if call.func.split(".")[-1] == "importorskip":
                return Satisfied(f"{path} guards `{package}` with importorskip")
        if any(d.name.split(".")[-1] == "skipif" for d in function.decorators):
            return Satisfied(f"{path}:{function.lineno} carries a skipif marker")
        return Violated(f"{path}:{function.lineno} `{function.name}` uses the optional "
                        f"dependency `{package}` and is not skipped when it is absent")


@rule(
    id="ASTROPY-C017",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class SkipConditionsComeFromTheHasFlags:
    """Pre-condition: each skip condition the agent wrote on a test.
    Pass condition: it is one of the ``HAS_*`` flags from
    ``astropy.utils.compat.optional_deps``.

    Selecting every skip condition, rather than the ones already using a flag, is what lets
    a correct one record a pass (§7.1).

    Heuristic on the **pass condition** (§6.2): a name matching ``HAS_*`` is accepted even
    when the import table does not resolve it to ``optional_deps``, because the flag may be
    re-exported. A locally defined ``HAS_THING`` therefore passes.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in _written_tests(b):
            for decorator in function.decorators:
                if decorator.name.split(".")[-1] != "skipif":
                    continue
                condition = ast.dump(decorator.node) if decorator.node is not None else ""
                out.append(target(f"skip-flag:{path}:{decorator.lineno}", path,
                                  (decorator.lineno, decorator.lineno),
                                  (path, decorator.lineno, condition, module),
                                  f"@{decorator.name}"))
        return out

    def pass_condition(self, t: Target):
        path, lineno, condition, module = t.payload
        if match := HAS_FLAG.search(condition):
            flag = match.group(0)
            if module.origin(flag).startswith(OPTIONAL_DEPS_MODULE):
                return Satisfied(f"{path}:{lineno} skips on {flag} from optional_deps")
            return Satisfied(f"{path}:{lineno} skips on {flag}")
        return Violated(f"{path}:{lineno} builds its skip condition without a HAS_* flag "
                        f"from {OPTIONAL_DEPS_MODULE}")


@rule(
    id="ASTROPY-C020",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class WarningsAreAssertedWithPytestWarns:
    """Pre-condition: each place a test the agent wrote checks that a warning is raised.
    Pass condition: it uses the ``pytest.warns`` context manager.

    Heuristic on the **pre-condition** (§6.3): *testing that a warning is triggered* is
    approximated by the ways of doing it -- ``pytest.warns``, ``catch_warnings``, the
    ``recwarn`` fixture, numpy's ``assert_warns``. A test that inspects warnings some other
    way is not selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in _written_tests(b):
            for call in _calls_in(module, function):
                short = call.func.split(".")[-1]
                if short in [name.split(".")[-1] for name in WARNING_ASSERTIONS]:
                    out.append(target(f"warns:{path}:{call.lineno}", path,
                                      (call.lineno, call.lineno),
                                      (path, call.lineno, module.origin(call.func),
                                       call.func), call.func))
            if "recwarn" in _parameters(function):
                out.append(target(f"warns:{path}:{function.lineno}", path,
                                  function.span(),
                                  (path, function.lineno, "recwarn", "recwarn"), "recwarn"))
        return out

    def pass_condition(self, t: Target):
        path, lineno, resolved, written = t.payload
        if resolved.endswith("pytest.warns") or written.split(".")[-1] == "warns":
            return Satisfied(f"{path}:{lineno} asserts the warning with pytest.warns")
        return Violated(f"{path}:{lineno} checks a warning with `{written}` rather than the "
                        f"pytest.warns context manager")


@rule(
    id="ASTROPY-C021",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ExceptionsAreAssertedWithPytestRaises:
    """Pre-condition: each place a test the agent wrote checks that an exception is raised.
    Pass condition: it uses the ``pytest.raises`` context manager.

    Heuristic on the **pre-condition** (§6.3): *designed to trigger an error* is
    approximated by the assertion helpers a test uses -- ``pytest.raises``, unittest's
    ``assertRaises``, numpy's ``assert_raises``. A test that catches the exception by hand
    and asserts on it is not selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in _written_tests(b):
            for call in _calls_in(module, function):
                short = call.func.split(".")[-1]
                if short in [name.split(".")[-1] for name in EXCEPTION_ASSERTIONS]:
                    out.append(target(f"raises:{path}:{call.lineno}", path,
                                      (call.lineno, call.lineno),
                                      (path, call.lineno, module.origin(call.func),
                                       call.func), call.func))
        return out

    def pass_condition(self, t: Target):
        path, lineno, resolved, written = t.payload
        if resolved.endswith("pytest.raises") or written.split(".")[-1] == "raises":
            return Satisfied(f"{path}:{lineno} asserts the exception with pytest.raises")
        return Violated(f"{path}:{lineno} checks an exception with `{written}` rather than "
                        f"the pytest.raises context manager")


@rule(
    id="ASTROPY-C023",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a comment the agent wrote
    reads=("files",),  # spec §5
    heuristic=True,
)
class CoveragePragmasAreSpelledCorrectly:
    """Pre-condition: each ``# pragma`` comment the agent wrote in Python.
    Pass condition: it reads ``pragma: no cover`` and sits on the line that opens the block
    it excludes.

    Selecting every pragma, rather than the correctly spelled ones, is what makes the rule
    able to fail: a misspelled pragma excludes nothing and is exactly the mistake worth
    catching (§7.1).

    Heuristic on the **pass condition** (§6.2): "at the start of the block" is approximated
    by the pragma sitting on a line that opens a block, or on the first line of one. A
    pragma placed correctly in a shape this does not recognise reads as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b):
            written = added_lines(b, path)
            for index, (lineno, text) in enumerate(written):
                if not PRAGMA.search(text):
                    continue
                previous = written[index - 1][1] if index else ""
                out.append(target(f"pragma:{path}:{lineno}", path, (lineno, lineno),
                                  (path, lineno, text, previous), text.strip()))
        return out

    def pass_condition(self, t: Target):
        path, lineno, text, previous = t.payload
        match = PRAGMA.search(text)
        if not NO_COVER.match(match.group("body")):
            return Violated(f"{path}:{lineno} reads `#{match.group(0)[1:]}` rather than "
                            f"`# pragma: no cover`")
        code = text[:match.start()].rstrip()
        if code.endswith(":") or previous.rstrip().endswith(":") or not code:
            return Satisfied(f"{path}:{lineno} excludes the block it opens")
        return Violated(f"{path}:{lineno} carries `# pragma: no cover` in the middle of a "
                        f"block rather than at its start")


@rule(
    id="ASTROPY-C024",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier
    reads=("files",),  # spec §5
)
class FigureTestsUseTheConvenienceDecorator:
    """Pre-condition: each figure test the agent wrote or edited, in either form.
    Pass condition: it is decorated with ``@figure_test``.

    Not heuristic: the sentence names both decorators, so *a figure test* is a category the
    rule itself defines and the pre-condition selects on it exactly. Selecting only the
    ``mpl_image_compare`` form would make every target a violation (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in _written_tests(b):
            if _has_mark(function, FIGURE_TEST) or _has_mark(function, MPL_IMAGE_COMPARE):
                out.append(target(f"figure:{path}:{function.lineno}", path, function.span(),
                                  (path, function), function.name))
        return out

    def pass_condition(self, t: Target):
        path, function = t.payload
        if _has_mark(function, FIGURE_TEST):
            return Satisfied(f"{path}:{function.lineno} uses @figure_test")
        return Violated(f"{path}:{function.lineno} `{function.name}` uses "
                        f"@pytest.mark.mpl_image_compare directly rather than @figure_test")


# =========================================================================== doctests


@rule(
    id="ASTROPY-C013",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is an example the agent wrote
    reads=("files",),  # spec §5
    heuristic=True,
)
class RemoteDoctestsCarryTheRemoteDataFlag:
    """Pre-condition: each doctest example the agent wrote that retrieves remote data.
    Pass condition: its prompt line carries ``# doctest: +REMOTE_DATA``.

    Heuristic on the **pre-condition** (§6.3), the same approximation C012 makes for test
    functions: remote retrieval is recognised by a URL literal or by one of astropy's
    download helpers appearing in the example's source.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for example in _examples(b):
            fetches = (_URL_LITERAL.search(example.source)
                       or any(f"{name}(" in example.source for name in REMOTE_CALLS))
            if fetches:
                out.append(target(f"remote-doctest:{example.path}:{example.lineno}",
                                  example.path, (example.lineno, example.lineno), example,
                                  example.source[:80]))
        return out

    def pass_condition(self, t: Target):
        example: Example = t.payload
        if example.has_flag(REMOTE_DATA_FLAG):
            return Satisfied(f"{example.path}:{example.lineno} carries +{REMOTE_DATA_FLAG}")
        return Violated(f"{example.path}:{example.lineno} retrieves remote data without "
                        f"`# doctest: +{REMOTE_DATA_FLAG}`")


@rule(
    id="ASTROPY-C025",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier; an edited example must run
    reads=("files", "doctest_run"),  # spec §5: running them is what decides this
)
class DoctestExamplesRunCorrectly:
    """Pre-condition: each doctest example the agent wrote or edited.
    Pass condition: it runs, and its output matches what the example claims.

    Graded **one-sidedly**. An example whose source is not valid Python cannot run, and
    that is decidable from the patch and conclusive -- so the rule fails on it. Whether a
    syntactically valid example produces the output it claims is exactly what executing the
    doctests answers and nothing static does, so the rule declares ``doctest_run`` and
    withholds. It never passes vacuously.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"doctest:{e.path}:{e.lineno}", e.path, (e.lineno, e.lineno), e,
                       e.source[:80])
                for e in _examples(b)]

    def pass_condition(self, t: Target):
        example: Example = t.payload
        if not example.has_flag(SKIP_FLAG):
            try:
                compile(example.source + "\n", "<doctest>", "exec")
            except SyntaxError as exc:
                return Violated(f"{example.path}:{example.lineno} is not valid Python, so "
                                f"it cannot run as a doctest: {exc.msg}")
        return Undetermined(
            "tool_missing",
            f"whether {example.path}:{example.lineno} produces the output it claims is "
            f"decided by executing the doctests; this bundle carries no such run")


@rule(
    id="ASTROPY-C026",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class NonExecutableExamplesAreSkipped:
    """Pre-condition: each doctest example the agent wrote that looks non-executable, and
    each one already marked skipped.
    Pass condition: its prompt line carries ``# doctest: +SKIP``.

    The already-marked examples are in the pre-condition deliberately: without them it
    would select only examples that fail, and the rule could never record a compliant one
    (§7.1).

    Heuristic on the **pre-condition** (§6.3): *looks like a doctest but is not executable
    verbatim* is approximated by placeholder text -- ``path/to``, ``your_file``, an
    angle-bracket stand-in. An example that cannot run for a subtler reason is not
    selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for example in _examples(b):
            if PLACEHOLDER.search(example.source) or example.has_flag(SKIP_FLAG):
                out.append(target(f"doctest-skip:{example.path}:{example.lineno}",
                                  example.path, (example.lineno, example.lineno), example,
                                  example.source[:80]))
        return out

    def pass_condition(self, t: Target):
        example: Example = t.payload
        if example.has_flag(SKIP_FLAG):
            return Satisfied(f"{example.path}:{example.lineno} carries +{SKIP_FLAG}")
        return Violated(f"{example.path}:{example.lineno} cannot run verbatim and carries "
                        f"no `# doctest: +{SKIP_FLAG}`")


@rule(
    id="ASTROPY-C027",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier
    reads=("files",),  # spec §5
)
class DoctestSkipIsAModuleLevelListOfPatterns:
    """Pre-condition: each ``__doctest_skip__`` assignment the agent wrote.
    Pass condition: it is at module level and its value is a list of wildcard patterns.

    Not heuristic: the variable name, its position and the shape of its value are all read
    off the syntax tree, and the sentence states each of them. A dict, a bare string or an
    assignment inside a function is a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _variable_targets(b, DOCTEST_SKIP_VARIABLE, "doctest-skip-var")

    def pass_condition(self, t: Target):
        path, lineno, node, module_level = t.payload
        if not module_level:
            return Violated(f"{path}:{lineno} {DOCTEST_SKIP_VARIABLE} is not at module "
                            f"level, where the test framework looks for it")
        if not isinstance(node.value, (ast.List, ast.Tuple)):
            return Violated(f"{path}:{lineno} {DOCTEST_SKIP_VARIABLE} is a "
                            f"{type(node.value).__name__.lower()}, not a list of wildcard "
                            f"patterns")
        return Satisfied(f"{path}:{lineno} {DOCTEST_SKIP_VARIABLE} is a module-level list")


@rule(
    id="ASTROPY-C028",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class DoctestRequiresIsAModuleLevelDictionary:
    """Pre-condition: each ``__doctest_requires__`` assignment the agent wrote.
    Pass condition: it is at module level and its value is a dictionary.

    Not heuristic, for the same reasons as C027: the name, the position and the type of the
    value are all stated in the sentence and all read off the syntax tree.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _variable_targets(b, DOCTEST_REQUIRES_VARIABLE, "doctest-requires-var")

    def pass_condition(self, t: Target):
        path, lineno, node, module_level = t.payload
        if not module_level:
            return Violated(f"{path}:{lineno} {DOCTEST_REQUIRES_VARIABLE} is not at module "
                            f"level, where the test framework looks for it")
        if not isinstance(node.value, ast.Dict):
            return Violated(f"{path}:{lineno} {DOCTEST_REQUIRES_VARIABLE} is a "
                            f"{type(node.value).__name__.lower()}, not a dictionary of "
                            f"patterns to modules")
        return Satisfied(f"{path}:{lineno} {DOCTEST_REQUIRES_VARIABLE} is a module-level "
                         f"dictionary")


def _variable_targets(bundle: EvidenceBundle, name: str, prefix: str) -> list[Target]:
    out = []
    for path, module in modules(bundle):
        authored = _authored(bundle, path)
        module_level_lines = {n.lineno for n in module.tree.body}
        for node in ast.walk(module.tree):
            if not isinstance(node, ast.Assign) or node.lineno not in authored:
                continue
            names = [pa.dotted_name(t) for t in node.targets]
            if name not in names:
                continue
            out.append(target(f"{prefix}:{path}:{node.lineno}", path,
                              (node.lineno, node.lineno),
                              (path, node.lineno, node, node.lineno in module_level_lines),
                              name))
    return out


@rule(
    id="ASTROPY-C029",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a line the agent wrote
    reads=("files",),  # spec §5
    heuristic=True,
)
class NarrativeDoctestsAreSkippedWithTheDirective:
    """Pre-condition: each attempt in narrative documentation to stop a doctest block
    running, in either form.
    Pass condition: it is the ``.. doctest-skip::`` directive, or ``doctest-skip-all``.

    Heuristic on the **pre-condition** (§6.3): the alternative form is recognised as a
    ``# doctest: +SKIP`` comment inside a ``.rst`` page, which is how someone reaches for
    the docstring mechanism in narrative text. A third way of trying to skip is not
    selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, change in owned_files(b, is_doc_path):
            for lineno, text in change.added_lines:
                directive = bool(DOCTEST_SKIP_DIRECTIVE.match(text))
                inline = f"+{SKIP_FLAG}" in text
                if directive or inline:
                    out.append(target(f"doctest-skip-rst:{path}:{lineno}", path,
                                      (lineno, lineno), (path, lineno, directive, text),
                                      text.strip()))
        return out

    def pass_condition(self, t: Target):
        path, lineno, directive, text = t.payload
        if directive:
            return Satisfied(f"{path}:{lineno} uses the doctest-skip directive")
        return Violated(f"{path}:{lineno} skips a narrative doctest with an inline flag "
                        f"rather than the `.. doctest-skip::` directive")


@rule(
    id="ASTROPY-C030",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class NarrativeDoctestsAreGatedWithTheDirective:
    """Pre-condition: each attempt in narrative documentation to gate a doctest block on a
    dependency, in either form.
    Pass condition: it is the ``.. doctest-requires::`` directive.

    Heuristic on the **pre-condition** (§6.3), the mirror of C029: the alternative form is
    recognised as the module-level ``__doctest_requires__`` name appearing inside a
    ``.rst`` page, which is the mechanism for docstrings rather than for narrative text.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, change in owned_files(b, is_doc_path):
            for lineno, text in change.added_lines:
                directive = bool(DOCTEST_REQUIRES_DIRECTIVE.match(text))
                alternative = DOCTEST_REQUIRES_VARIABLE in text
                if directive or alternative:
                    out.append(target(f"doctest-requires-rst:{path}:{lineno}", path,
                                      (lineno, lineno), (path, lineno, directive, text),
                                      text.strip()))
        return out

    def pass_condition(self, t: Target):
        path, lineno, directive, text = t.payload
        if directive:
            return Satisfied(f"{path}:{lineno} uses the doctest-requires directive")
        return Violated(f"{path}:{lineno} gates a narrative doctest with "
                        f"{DOCTEST_REQUIRES_VARIABLE} rather than the "
                        f"`.. doctest-requires::` directive")


@rule(
    id="ASTROPY-C032",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class IgnoredOutputUsesTheIgnoreOutputFlag:
    """Pre-condition: each doctest example the agent wrote whose expected output is elided
    wholesale, in either form.
    Pass condition: its prompt line carries ``# doctest: +IGNORE_OUTPUT``.

    Heuristic on the **pre-condition** (§6.3): *ignoring the output entirely* is recognised
    either by the flag itself or by the expected output being nothing but an ellipsis,
    which is the other way people write it. An example that elides output some third way is
    not selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for example in _examples(b):
            elided = example.want.strip() == "..."
            if elided or example.has_flag(IGNORE_OUTPUT_FLAG):
                out.append(target(f"ignore-output:{example.path}:{example.lineno}",
                                  example.path, (example.lineno, example.lineno), example,
                                  example.source[:80]))
        return out

    def pass_condition(self, t: Target):
        example: Example = t.payload
        if example.has_flag(IGNORE_OUTPUT_FLAG):
            return Satisfied(f"{example.path}:{example.lineno} carries "
                             f"+{IGNORE_OUTPUT_FLAG}")
        return Violated(f"{example.path}:{example.lineno} elides its whole output with an "
                        f"ellipsis rather than `# doctest: +{IGNORE_OUTPUT_FLAG}`")


@rule(
    id="ASTROPY-C033",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class FloatingPointOutputUsesFloatCmp:
    """Pre-condition: each doctest example the agent wrote whose expected output contains a
    floating-point number.
    Pass condition: its prompt line carries ``# doctest: +FLOAT_CMP``.

    Heuristic on the **pre-condition** (§6.3): *output that needs a float comparison* is
    approximated by a decimal number appearing in the expected output, which over-fires on
    a value that is exact in every environment -- a version string, a count written with a
    decimal point.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for example in _examples(b):
            if FLOAT_LITERAL.search(example.want):
                out.append(target(f"float-cmp:{example.path}:{example.lineno}",
                                  example.path, (example.lineno, example.lineno), example,
                                  example.want[:80]))
        return out

    def pass_condition(self, t: Target):
        example: Example = t.payload
        if example.has_flag(FLOAT_CMP_FLAG) or example.has_flag(IGNORE_OUTPUT_FLAG):
            return Satisfied(f"{example.path}:{example.lineno} compares its float output "
                             f"with a flag")
        return Violated(f"{example.path}:{example.lineno} claims floating-point output "
                        f"without `# doctest: +{FLOAT_CMP_FLAG}`")


# =========================================================================== the suite


@rule(
    id="ASTROPY-C001",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier
    reads=("files",),  # spec §5: the open and its close are both in the patch
    heuristic=True,
)
class TestsCloseTheFilesTheyOpen:
    """Pre-condition: each test the agent wrote or edited that opens a file.
    Pass condition: every open is closed -- a ``with`` statement, or a ``close`` call.

    Heuristic on the **pass condition** (§6.2), and the corpus files this rule
    ``differential`` for a good reason: what the rule is really about is a
    ``ResourceWarning`` at run time. It is graded statically all the same, because an open
    with no ``with`` and no ``close`` is visible in the source and withholding would cost
    the rule its entire fail path. A file handed to a helper that closes it reads as a
    violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in _written_tests(b):
            opens = [c for c in _calls_in(module, function)
                     if c.func.split(".")[-1] in ("open", "fits_open")
                     or module.origin(c.func).endswith("fits.open")]
            if opens:
                out.append(target(f"close:{path}:{function.lineno}", path, function.span(),
                                  (path, module, function, opens), function.name))
        return out

    def pass_condition(self, t: Target):
        path, module, function, opens = t.payload
        managed = set()
        for node in ast.walk(function.node):
            if isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    for child in ast.walk(item.context_expr):
                        if isinstance(child, ast.Call):
                            managed.add(child.lineno)
        closes = any(c.func.split(".")[-1] == "close" for c in _calls_in(module, function))
        unmanaged = [c for c in opens if c.lineno not in managed]
        if not unmanaged or closes:
            return Satisfied(f"{path}:{function.lineno} closes the file(s) it opens")
        return Violated(f"{path}:{unmanaged[0].lineno} opens a file with neither a `with` "
                        f"statement nor a close(), so the test can raise a ResourceWarning")


@rule(
    id="ASTROPY-C036",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- running the suite is part of making the contribution
    reads=("files", "commands"),  # spec §5: CheckTier=trajectory, and running is an act
    heuristic=True,
)
class RemoteDataTestsAreRunWithTheFlag:
    """Pre-condition: the contribution touches remote data access, which is when the flag
    is needed.
    Pass condition: a test run with ``--remote-data`` appears in the command log.

    The pre-condition fires on the **bug involving remote data**, not on the invocation
    (§7.1, §7.2): firing on the flag would find only agents that already complied.

    Heuristic on the **pre-condition** (§6.3): *the bug involves remote data access* is
    approximated by the contribution touching a remote-data marker or one of astropy's
    download helpers, which is what such work looks like in a patch.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        evidence = []
        for path in python_files(b):
            text = "\n".join(line for _, line in added_lines(b, path))
            if "remote_data" in text or any(f"{name}(" in text for name in REMOTE_CALLS):
                evidence.append(path)
        if not evidence:
            return []
        return [target(f"remote-run:{b.instance_id}", evidence[0], None, (b, evidence),
                       f"remote data touched in {evidence[0]}", source="trajectory")]

    def pass_condition(self, t: Target):
        bundle, evidence = t.payload
        if runs := ran(bundle, PYTEST_REMOTE_DATA):
            return Satisfied(f"ran `{runs[0].command.strip()[:60]}`")
        return Violated(f"{evidence[0]} touches remote data access and no test run with "
                        f"--remote-data appears in the command log")


@rule(
    id="ASTROPY-C037",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- the contribution as a whole is the subject
    reads=("files", "full_suite_run"),  # spec §5: before-and-after is what decides it
    heuristic=True,
)
class ATestFailsBeforeAndPassesAfter:
    """Pre-condition: the contribution changes library code, which is what a fix does.
    Pass condition: it also ships a test, and that test fails before the change and passes
    after it.

    Graded **one-and-a-half-sidedly**, and deliberately. A fix with no test at all is
    failed here, because no run is needed to establish that no test can have gone from
    failing to passing -- there is none. Where a test *is* present, whether it fails on the
    pre-fix code is exactly what a before-and-after run answers. The harness's own
    ``FAIL_TO_PASS`` bucket cannot stand in: it is computed from the benchmark's reference
    test patch, not from the test the agent wrote, so reading it would grade somebody
    else's test. The rule declares ``full_suite_run`` and withholds instead.

    Heuristic on the **pre-condition** (§6.3): "changes library code" is what a fix looks
    like in a patch, and so does a refactor.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        source = [p for p, _ in _library_modules(b)]
        if not source:
            return []
        return [target(f"regression:{b.instance_id}", source[0], None, (b, source),
                       f"{len(source)} library file(s) changed", source="rerun")]

    def pass_condition(self, t: Target):
        bundle, source = t.payload
        tests = [p for p in python_files(bundle) if _is_test_module(p)]
        if not tests:
            return Violated("the contribution changes library code and adds no test, so no "
                            "test can fail before the change and pass after it")
        return Undetermined(
            "tool_missing",
            f"whether {tests[0]} fails on the pre-fix code is decided by running it on both "
            f"revisions; this bundle carries no such run")


@rule(
    id="ASTROPY-C056",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- one target for the whole contribution
    reads=("files",),  # spec §5
    heuristic=True,
)
class NewCodeComesWithTests:
    """Pre-condition: the contribution changes library code, which is the case the
    checklist's exemption -- "some changes, e.g. to documentation, do not need tests" --
    leaves in.
    Pass condition: it also adds or changes a test module in the same sub-package.

    Heuristic on the **pass condition** (§6.2): *covering* the new code is a coverage
    measurement, approximated here by a test module changed in the same sub-package as the
    source. A test added in the right place that exercises none of the new code passes, and
    that is the flag's whole meaning. What the check does establish exactly is the case
    invariant 2 cares about: a contribution that ships **no** test fails.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        source = [p for p, _ in _library_modules(b)]
        if not source:
            return []
        return [target(f"tests-for-code:{b.instance_id}", source[0], None, (b, source),
                       f"{len(source)} library file(s) changed")]

    def pass_condition(self, t: Target):
        bundle, source = t.payload
        tests = [p for p in python_files(bundle) if _is_test_module(p)]
        if not tests:
            return Violated(f"{source[0]} changes library code and the contribution adds "
                            f"no test")
        packages = {subpackage_of(p) for p in source}
        matching = [p for p in tests if subpackage_of(p) in packages]
        if matching:
            return Satisfied(f"{matching[0]} tests the sub-package the change is in")
        return Violated(f"the contribution changes {source[0]} and its tests ({tests[0]}) "
                        f"are in a different sub-package")


@rule(
    id="ASTROPY-C201",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- the raise the agent wrote is the antecedent
    reads=("files",),  # spec §5
    heuristic=True,
)
class EveryRaisedExceptionHasATest:
    """Pre-condition: each exception class the agent's written library code raises.
    Pass condition: a test in the contribution asserts that it is raised.

    Heuristic on the **pass condition** (§6.2): the test is matched by the exception's name
    appearing in a test module's text, which does not establish that the test exercises
    *this* raise. Matching more tightly is not possible from a patch, and matching less
    tightly -- any test at all -- would make the rule meaningless.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        raised: dict[str, tuple[str, int]] = {}
        for path, module in _library_modules(b):
            authored = _authored(b, path)
            for node in ast.walk(module.tree):
                if not isinstance(node, ast.Raise) or node.lineno not in authored:
                    continue
                exc = node.exc
                if exc is None:
                    continue
                name = pa.dotted_name(exc.func if isinstance(exc, ast.Call) else exc)
                if name:
                    raised.setdefault(name.split(".")[-1], (path, node.lineno))
        return [target(f"exception-test:{name}", path, (lineno, lineno),
                       (name, path, lineno, b), f"raises {name}")
                for name, (path, lineno) in sorted(raised.items())]

    def pass_condition(self, t: Target):
        name, path, lineno, bundle = t.payload
        for test_path in python_files(bundle):
            if not _is_test_module(test_path):
                continue
            text = (bundle.files[test_path].head_text or "") + "\n".join(
                line for _, line in added_lines(bundle, test_path))
            if re.search(rf"\b{re.escape(name)}\b", text):
                return Satisfied(f"{test_path} tests for `{name}`")
        return Violated(f"{path}:{lineno} raises `{name}` and no test in the contribution "
                        f"asserts that it is raised")


@rule(
    id="ASTROPY-C205",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- the contribution is what has to pass
    reads=("files", "evaluation"),  # spec §5: the harness's own run is what decides this
    heuristic=True,
)
class ToxTestEnvironmentPasses:
    """Pre-condition: the agent submitted Python, which is what gets run.
    Pass condition: the harness's own before-and-after run reports no test that passed
    before the change and fails after it.

    Graded from a real execution rather than from a stand-in for one, which is what the
    ``differential`` tier asks for: a submitted module that will not parse fails without any
    run, and beyond that the verdict is the harness's report.

    Heuristic on the **pass condition** (§6.2), and this is where the check is weaker than
    the sentence. The harness executes the subset of the suite the benchmark instance names,
    so a clean report is evidence that *those* tests pass and not that ``tox -e test``
    passes entire. Reported as a pass with that stated, rather than withheld: a rule that
    declines to grade on every run measures nothing, while the failing direction -- a
    regression -- is exact.

    ``EvalReport.regressions()`` is the single place the reading of ``tests_status`` is
    written down; ``PASS_TO_FAIL`` merely looks like it means that.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        files = python_files(b)
        if not files:
            return []
        return [target(f"tox:{b.instance_id}", None, None, b,
                       f"{len(files)} Python file(s) submitted", source="rerun")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        for path in python_files(bundle):
            text = bundle.files[path].head_text
            if text is None:
                continue
            module = pa.parse_module(text, path)
            if not module.ok and module.error != pa.NO_SOURCE:
                return Violated(f"`tox -e test` cannot pass: {path} is not valid Python "
                                f"({module.error})")
        report = bundle.evaluation
        if report is None or not report.usable:
            return Undetermined("tool_missing", "this run carries no functional result, so "
                                                "whether the suite passes is unknown")
        if regressions := report.regressions():
            return Violated(f"{len(regressions)} test(s) that passed before the change now "
                            f"fail: {sorted(regressions)[:5]}")
        return Satisfied(f"the harness reported no regression across "
                         f"{report.n_outcomes} test outcome(s); it ran the instance's "
                         f"subset rather than the whole suite")

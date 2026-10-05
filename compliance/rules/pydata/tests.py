"""pydata (xarray): Tests and test style -- 13 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

The largest category in this pack, and the one where ownership splits most sharply. Rules
that say *new* -- where a test goes, how a test module is named, functions rather than
classes -- are `created` (§4.3): a pre-existing test in the wrong place is not the agent's
doing. Rules that state a property with no newness qualifier -- which helper to compare
with, how to gate on an optional dependency -- are `touched`, because editing a test makes
the agent answerable for its shape.

Four of the thirteen come from `xarray/tests/CLAUDE.md` rather than the contributing guide
(C132-C135). They are instructions written *for an agent*, which is why they are unusually
mechanical: each names one construct and its replacement.
"""

from __future__ import annotations

import ast
import re

from compliance.core import ownership as own
from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.pydata._common import (TEST_ROOTS, is_test_path, modules,
                                             python_files, target)

CATEGORY = "Tests and test style"

XARRAY_TESTING = ("assert_equal", "assert_identical", "assert_allclose",
                  "assert_duckarray_equal")
_XARRAY_OBJECT = re.compile(r"\b(DataArray|Dataset|Variable|DataTree)\s*\(")
_REQUIRES = re.compile(r"^requires_\w+$")


def _owned_tests(bundle: EvidenceBundle, mode: str = "touched"):
    """(path, module, function) for each test function the agent owns under ``mode``."""
    out = []
    for path, module in modules(bundle, tests=True):
        for function in module.tests():
            if own.owns_span(bundle, path, function.span(), mode):
                out.append((path, module, function))
    return out


def _source_of(module: pa.PyModule, function) -> str:
    lines = (module.source or "").split("\n")
    lo, hi = function.span()
    return "\n".join(lines[lo - 1:hi])


def _parametrize_calls(module: pa.PyModule):
    return [c for c in module.calls if c.short == "parametrize"]


def _marked_directly(element: ast.AST) -> str:
    """`pytest.mark.slow(3)` used as an argvalue -- the form the guide replaces."""
    if isinstance(element, ast.Call) and isinstance(element.func, ast.Attribute):
        dotted = pa.dotted_name(element.func)
        if "mark" in dotted.split(".") and not dotted.endswith("param"):
            return dotted
    return ""


def _param_marks(element: ast.AST) -> list[str]:
    """Mark names passed as `pytest.param(..., marks=...)`."""
    if not (isinstance(element, ast.Call) and pa.dotted_name(element.func).endswith("param")):
        return []
    out = []
    for keyword in element.keywords:
        if keyword.arg != "marks":
            continue
        values = (keyword.value.elts if isinstance(keyword.value, (ast.List, ast.Tuple))
                  else [keyword.value])
        for value in values:
            node = value.func if isinstance(value, ast.Call) else value
            out.append(pa.dotted_name(node))
    return out


# --- where tests live and what shape they take ----------------------------------------


@rule(
    id="PYDATA-C049",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the sentence says "new tests"
    reads=("files",),  # spec §5: the path is the whole question
)
class NewTestsLiveInTheTestsSubdirectory:
    """Pre-condition: each test function the agent added.
    Pass condition: the file it was added to is under `xarray/tests/`.

    Selects only tests the agent created: a pre-existing test in an unusual place is not
    this contribution's doing, and grading it would attribute somebody else's choice.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=None):
            for function in module.tests():
                if function.qualname != function.name:
                    continue
                if own.owns_span(b, path, function.span(), "created"):
                    out.append(target(f"testloc:{path}:{function.name}", path,
                                      function.span(), path, f"def {function.name}"))
        return out

    def pass_condition(self, t: Target):
        path: str = t.payload
        if is_test_path(path):
            return Satisfied(f"{path} is under {TEST_ROOTS[0]}")
        return Violated(f"new test added in {path}, outside {TEST_ROOTS[0]}")


@rule(
    id="PYDATA-C060",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- naming a module is a thing you do once
    reads=("files",),  # spec §5
)
class TestModulesAreNamedForTheirFeature:
    """Pre-condition: each test module the agent created.
    Pass condition: its filename is `test_<feature>.py`.

    A module the agent merely edited keeps whatever name it already had, so only new files
    are selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b, mode="created", tests=None):
            name = path.rsplit("/", 1)[-1]
            if is_test_path(path) or name.startswith("test_"):
                out.append(target(f"testmod:{path}", path, None, (path, name), name))
        return out

    def pass_condition(self, t: Target):
        path, name = t.payload
        if re.match(r"^test_\w+\.py$", name):
            return Satisfied(f"{name} is test_<feature>.py")
        return Violated(f"{name} is not named test_<feature>.py")


@rule(
    id="PYDATA-C052",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the sentence says "new tests"
    reads=("files",),  # spec §5
)
class NewTestsAreFunctionsNotClasses:
    """Pre-condition: each test function the agent added.
    Pass condition: it is defined at module level rather than inside a test class.

    `qualname != name` is exactly "nested in something", which for a test function means a
    class. Existing class-based tests are left alone: the rule governs what the agent
    writes, not what it found.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=True):
            for function in module.tests():
                if own.owns_span(b, path, function.span(), "created"):
                    out.append(target(f"testshape:{path}:{function.qualname}", path,
                                      function.span(), (path, function),
                                      f"def {function.qualname}"))
        return out

    def pass_condition(self, t: Target):
        path, function = t.payload
        if function.qualname == function.name:
            return Satisfied(f"{path}:{function.name} is a module-level function")
        return Violated(f"{path}:{function.qualname} is a method of a test class")


@rule(
    id="PYDATA-C053",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- naming is fixed when the test is written
    reads=("files",),  # spec §5
    heuristic=True,
)
class TestNamingAndArguments:
    """Pre-condition: each test function the agent added.
    Pass condition: its name begins with `test_` and every argument is a parametrize name
    or a fixture defined in the same module.

    Heuristic on the **pass condition** (§6.2). Fixtures reach a test from `conftest.py`
    and from plugins as well as from its own module, and neither is in the patch, so an
    argument this cannot account for is reported as unaccounted rather than as wrong --
    which will over-report on tests using shared fixtures. The naming half is exact.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in _owned_tests(b, "created"):
            fixtures = {f.name for f in module.functions if f.has_decorator("fixture")}
            names: set[str] = set()
            for decorator in function.decorators:
                if "parametrize" not in decorator.name:
                    continue
                node = decorator.node
                call = node if isinstance(node, ast.Call) else getattr(node, "value", None)
                argnames = (call.args[0] if isinstance(call, ast.Call) and call.args
                            else None)
                if isinstance(argnames, ast.Constant) and isinstance(argnames.value, str):
                    names |= set(re.findall(r"[A-Za-z_]\w*", argnames.value))
                elif isinstance(argnames, (ast.List, ast.Tuple)):
                    names |= {e.value for e in argnames.elts
                              if isinstance(e, ast.Constant) and isinstance(e.value, str)}
            out.append(target(f"testname:{path}:{function.name}", path, function.span(),
                              (path, function, fixtures | names), f"def {function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function, known = t.payload
        if not function.name.startswith("test_"):
            return Violated(f"{path}: `{function.name}` does not begin with test_")
        args = {a.arg for a in function.node.args.args} - {"self", "cls"}
        unaccounted = sorted(args - known)
        if unaccounted:
            return Violated(f"{path}:{function.name} takes {', '.join(unaccounted)}, "
                            f"which is neither a parametrize name nor a fixture defined "
                            f"in this module")
        return Satisfied(f"{path}:{function.name} is named and parameterised as required")


# --- what a test asserts with ---------------------------------------------------------


@rule(
    id="PYDATA-C048",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier
    reads=("files",),  # spec §5
    heuristic=True,
)
class TestsAreWrittenWithPytest:
    """Pre-condition: each test module the contribution changes.
    Pass condition: it defines no `unittest.TestCase` subclass.

    Heuristic on the **pass condition** (§6.2), graded one-sidedly. "Written with pytest,
    using the numpy.testing extensions where they apply" cannot be confirmed -- a plain
    function with a bare assert is a pytest test and looks like nothing in particular. What
    is decidable is the alternative the sentence rules out, and a `TestCase` subclass is
    positive evidence of it.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"pytest-style:{path}", path, None, (path, module), path)
                for path, module in modules(b, tests=True)]

    def pass_condition(self, t: Target):
        path, module = t.payload
        for node in ast.walk(module.tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for base in node.bases:
                if pa.dotted_name(base).endswith("TestCase"):
                    return Violated(f"{path}:{node.lineno} defines `{node.name}`, a "
                                    f"unittest.TestCase subclass, not a pytest test")
        return Satisfied(f"{path} defines no unittest.TestCase subclass")


@rule(
    id="PYDATA-C051",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier
    reads=("files",),  # spec §5
    heuristic=True,
)
class XarrayObjectsComparedWithXarrayTesting:
    """Pre-condition: each test function the agent wrote or edited that constructs an
    xarray object.
    Pass condition: it compares with `assert_equal`, `assert_identical` or a sibling from
    `xarray.testing`.

    Heuristic on the **pre-condition** (§6.3): *compares xarray objects* is approximated by
    the test constructing a `DataArray`, `Dataset`, `Variable` or `DataTree`, which
    over-fires on a test that builds one and asserts something scalar about it. That
    direction is deliberate -- the alternative, selecting only tests that already use the
    helpers, could never record a violation (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in _owned_tests(b):
            body = _source_of(module, function)
            if _XARRAY_OBJECT.search(body):
                out.append(target(f"xr-assert:{path}:{function.qualname}", path,
                                  function.span(), (path, function, body),
                                  f"def {function.qualname}"))
        return out

    def pass_condition(self, t: Target):
        path, function, body = t.payload
        for helper in XARRAY_TESTING:
            if re.search(rf"\b{helper}\s*\(", body):
                return Satisfied(f"{path}:{function.qualname} compares with `{helper}`")
        return Violated(f"{path}:{function.qualname} builds an xarray object and compares "
                        f"it without {' or '.join(XARRAY_TESTING[:2])}")


@rule(
    id="PYDATA-C058",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ScalarsAssertedBare:
    """Pre-condition: each test function the agent wrote or edited that asserts a scalar or
    a truth value through a helper call.
    Pass condition: it uses a bare `assert` statement instead.

    Heuristic on the **pre-condition** (§6.3): *a scalar or truth value* is recognised by a
    literal number, string or boolean passed to an `assert_*` helper, which misses a scalar
    held in a variable. Graded one-sidedly for that reason -- it finds the case the guide
    names and says nothing about the rest.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in _owned_tests(b):
            for call in module.calls_within(function.span()):
                if not call.short.startswith("assert_"):
                    continue
                literal = next((a for a in call.args if isinstance(a, ast.Constant)), None)
                if literal is not None:
                    out.append(target(f"bare-assert:{path}:{call.lineno}", path,
                                      call.span(), (path, call, literal),
                                      f"{call.func}(...)"))
        return out

    def pass_condition(self, t: Target):
        path, call, literal = t.payload
        return Violated(f"{path}:{call.lineno} asserts the literal {literal.value!r} "
                        f"through `{call.func}` -- the guide asks for a bare assert")


# --- parametrize -----------------------------------------------------------------------


@rule(
    id="PYDATA-C055",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class IndividualParametersMarkedWithPytestParam:
    """Pre-condition: each `parametrize` call the agent wrote or edited whose values carry
    a mark.
    Pass condition: the mark is applied through `pytest.param(..., marks=...)`.

    Not heuristic: both forms are exact syntax. A mark applied directly to a value reads as
    `pytest.mark.slow(3)` in the value list; the sanctioned form wraps the value in
    `pytest.param`. Deciding which of the two appeared is a structural question the AST
    answers, not a proxy.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=True):
            for call in _parametrize_calls(module):
                if not own.owns_span(b, path, call.span(), "touched"):
                    continue
                values = next((a for a in call.args
                               if isinstance(a, (ast.List, ast.Tuple))), None)
                if values is None:
                    continue
                marked = [e for e in values.elts if _marked_directly(e) or _param_marks(e)]
                if marked:
                    out.append(target(f"param-marks:{path}:{call.lineno}", path,
                                      call.span(), (path, call, marked),
                                      "parametrize(...)"))
        return out

    def pass_condition(self, t: Target):
        path, call, marked = t.payload
        for element in marked:
            if direct := _marked_directly(element):
                return Violated(f"{path}:{call.lineno} applies `{direct}` to a value "
                                f"directly instead of pytest.param(..., marks=...)")
        return Satisfied(f"{path}:{call.lineno} marks its parameters through pytest.param")


@rule(
    id="PYDATA-C134",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class NoSkipifOnAParametrizeParam:
    """Pre-condition: each `parametrize` call the agent wrote or edited.
    Pass condition: none of its parameters carries a `skipif` mark.

    A prohibition, so the pre-condition selects the permitted act -- writing a parametrize
    -- and the pass condition checks it was not the prohibited one (§7.1). Selecting
    parametrizes that already carry `skipif` would find nothing but violations.

    Distinct from C055, which is about *how* a mark is attached. This one is about *which*
    mark, and a `pytest.param(..., marks=pytest.mark.skipif(...))` satisfies C055 and
    violates this.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=True):
            for call in _parametrize_calls(module):
                if own.owns_span(b, path, call.span(), "touched"):
                    out.append(target(f"skipif-param:{path}:{call.lineno}", path,
                                      call.span(), (path, call), "parametrize(...)"))
        return out

    def pass_condition(self, t: Target):
        path, call = t.payload
        values = next((a for a in call.args if isinstance(a, (ast.List, ast.Tuple))), None)
        for element in (values.elts if values is not None else []):
            for mark in _param_marks(element) + [_marked_directly(element)]:
                if mark and mark.split(".")[-1] == "skipif":
                    return Violated(f"{path}:{call.lineno} attaches `skipif` to a "
                                    f"parametrize parameter")
        return Satisfied(f"{path}:{call.lineno} attaches no skipif to a parameter")


# --- optional dependencies -------------------------------------------------------------


@rule(
    id="PYDATA-C132",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class OptionalDependenciesGatedWithRequiresDecorator:
    """Pre-condition: each test function the agent wrote or edited in a module that guards
    an import behind `try`/`except ImportError`.
    Pass condition: the test carries a `@requires_*` decorator.

    Heuristic on the **pre-condition** (§6.3): a guarded import in the module is evidence
    that the module deals with an optional dependency, not proof that *this* test depends
    on it. Every test in such a module is selected, which over-fires on the ones that do
    not touch the optional path.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in _owned_tests(b):
            guarded = any(
                any(isinstance(h.type, ast.Name) and h.type.id == "ImportError"
                    or (isinstance(h.type, ast.Tuple) and
                        any(isinstance(e, ast.Name) and e.id == "ImportError"
                            for e in h.type.elts))
                    for h in node.handlers)
                for node in module.tries)
            if guarded:
                out.append(target(f"requires:{path}:{function.qualname}", path,
                                  function.span(), (path, function),
                                  f"def {function.qualname}"))
        return out

    def pass_condition(self, t: Target):
        path, function = t.payload
        for decorator in function.decorators:
            if _REQUIRES.match(decorator.name.split(".")[-1]):
                return Satisfied(f"{path}:{function.qualname} is gated with "
                                 f"@{decorator.name}")
        return Violated(f"{path}:{function.qualname} sits in a module with a conditional "
                        f"import and carries no @requires_* decorator")


@rule(
    id="PYDATA-C133",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class DaskHelpersImportedFromXarrayTests:
    """Pre-condition: each test module the contribution changes that imports dask at all.
    Pass condition: it does not import `dask.array` directly.

    Not heuristic: both halves are import statements the AST reports exactly. A module that
    imports dask through `xarray.tests` satisfies this; one that reaches for `dask.array`
    itself does not, whatever else it also imports.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=True):
            if any(name.split(".")[0] == "dask" for name in module.imports):
                out.append(target(f"dask-import:{path}", path, None, (path, module), path))
        return out

    def pass_condition(self, t: Target):
        path, module = t.payload
        direct = [n for n in module.imports if n == "dask.array" or n.startswith("dask.array.")]
        if direct:
            return Violated(f"{path} imports `{direct[0]}` directly instead of taking the "
                            f"helpers from xarray.tests")
        return Satisfied(f"{path} imports dask without reaching for dask.array")


@rule(
    id="PYDATA-C135",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class InFunctionImportsUseImportorskip:
    """Pre-condition: each test function the agent wrote or edited that imports a module
    inside its body.
    Pass condition: the import goes through `pytest.importorskip`.

    Not heuristic: an `import` statement inside a function body is exactly what the rule
    forbids, and `pytest.importorskip` is exactly what it asks for. Module-level imports
    are not selected -- the rule is about imports inside a test.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in _owned_tests(b):
            inner = [n for n in ast.walk(function.node)
                     if isinstance(n, (ast.Import, ast.ImportFrom))]
            if inner:
                out.append(target(f"importorskip:{path}:{function.qualname}", path,
                                  function.span(), (path, function, inner),
                                  f"def {function.qualname}"))
        return out

    def pass_condition(self, t: Target):
        path, function, inner = t.payload
        names = []
        for node in inner:
            if isinstance(node, ast.Import):
                names += [a.name for a in node.names]
            else:
                names.append(node.module or "")
        return Violated(f"{path}:{function.qualname} imports {names[0]} with a plain "
                        f"import statement -- the guide asks for pytest.importorskip")


# --- the change carries tests -----------------------------------------------------------


@rule(
    id="PYDATA-C112",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- one target for the whole contribution
    reads=("files",),  # DEPARTURE from CheckTier=differential -- both halves are in the patch
    heuristic=True,
)
class TestsAddedForTheChange:
    """Pre-condition: the contribution changes non-test Python source.
    Pass condition: it also changes or adds a file under `xarray/tests/`.

    Heuristic on the **pass condition** (§6.2): a changed test file is evidence that tests
    accompany the change, not proof that they test *it*. A documentation-only or
    changelog-only contribution finds no target rather than being graded.

    The corpus files this `differential` and both halves are in the patch, so no tool run is
    needed. Recorded rather than corrected, per the spec §5.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        source = python_files(b, tests=False)
        if not source:
            return []
        return [target(f"tests-added:{b.instance_id}", None, None, b,
                       f"{len(source)} source file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        tests = [p for p in sorted(bundle.files) if is_test_path(p)]
        if tests:
            return Satisfied(f"{len(tests)} test file(s) changed alongside the code: "
                             f"{tests[0]}")
        return Violated("source changed with nothing under xarray/tests/ in the "
                        "contribution")

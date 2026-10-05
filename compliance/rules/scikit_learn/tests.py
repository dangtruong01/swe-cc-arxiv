"""scikit-learn: Tests and test style -- 16 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects
on the rule's ANTECEDENT, ``pass_condition`` grades.

Three groups. The first is the pull-request checklist -- a test was added (C029), it fails
before and passes after (C030), the suite passes (C033) -- and the last two are graded
from ``bundle.evaluation``, the SWE-bench harness's own before-and-after comparison, which
is what the corpus means by ``CheckTier=differential``. The second group is deprecation
hygiene (C127, C128, C129), which fires only when the contribution actually deprecates
something. The third is test style: where tests live, what they import, how they assert,
and how they seed.

**C233 is graded one-sidedly** and says so in its own docstring: the contract is "passes
for every seed from 0 to 99", the bundle carries one run at one seed, so a failure is
conclusive and a success is not. It declares ``repeated_runs`` -- the Phase 5 source that
would settle it -- so the withhold is a named missing input and stops being permitted the
day that evidence is collected.
"""

from __future__ import annotations

import ast
import re

from compliance.core import ownership as own
from compliance.core.models import (EvidenceBundle, Satisfied, Target, Undetermined,
                                    Violated)
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.scikit_learn._common import (COMPILED_SUFFIXES, PACKAGE,
                                                   SANCTIONED_PRIVATE_TEST_MODULES,
                                                   calls_in, contribution_target,
                                                   cython_files, decorator_names,
                                                   deprecated_names, example_files,
                                                   file_text, is_test_path, modules,
                                                   parameters, ran, source_files, target)

CATEGORY = "Tests and test style"

#: pytest discovers a test by this prefix; the corpus Notes name pytest's rules as what
#: "appropriately named" means.
TEST_PREFIX = "test_"

#: The fixtures the project's conftest supplies.
PYPLOT_FIXTURE = "pyplot"
GLOBAL_SEED_FIXTURE = "global_random_seed"

#: Assertions that compare arrays for approximate equality (C197).
APPROX_ASSERTIONS = ("assert_allclose", "assert_almost_equal",
                     "assert_array_almost_equal", "assert_approx_equal",
                     "assert_allclose_dense_sparse")
#: The one the guide names.
SANCTIONED_ALLCLOSE = "sklearn.utils._testing.assert_allclose"

#: Module-level RNG routines: using one makes a test depend on execution order (C232).
_GLOBAL_RNG_CALL = re.compile(
    r"^(np|numpy)\.random\.(?!RandomState|Generator|default_rng|SeedSequence)\w+$"
    r"|^random\.\w+$")
#: Building an independent generator, which is what the rule asks for instead.
_OWN_RNG_CALL = ("np.random.RandomState", "numpy.random.RandomState",
                 "np.random.default_rng", "numpy.random.default_rng",
                 "check_random_state", "sklearn.utils.check_random_state")

_MATPLOTLIB = re.compile(r"\bmatplotlib\b|\bpyplot\b|\bplt\.")
_SEED_ALL_RUN = re.compile(r"SKLEARN_TESTS_GLOBAL_RANDOM_SEED\s*=\s*[\"']?all[\"']?", re.I)
_PYTEST_RUN = re.compile(r"\bpytest\b")
_WERROR_FUTURE = re.compile(r"-W\s*error::FutureWarning")


def owned_functions(bundle: EvidenceBundle, *, mode: str = "touched",
                    tests: bool = True) -> list[tuple[str, pa.PyModule, pa.FunctionDef]]:
    out = []
    for path, module in modules(bundle, tests=tests):
        for function in module.functions:
            if own.owns_span(bundle, path, function.span(), mode):
                out.append((path, module, function))
    return out


def test_functions(bundle: EvidenceBundle, *, mode: str = "touched"):
    """Functions the agent wrote that pytest would collect as tests."""
    return [(p, m, f) for p, m, f in owned_functions(bundle, mode=mode, tests=True)
            if f.name.startswith(TEST_PREFIX)]


def fixture_names(function: pa.FunctionDef) -> list[str]:
    return [p for p in parameters(function.node) if p not in ("self", "cls")]


def source_of(node) -> str:
    try:
        return ast.unparse(node)
    except Exception:  # noqa: BLE001 -- an unparseable node is missing evidence
        return ""


def calls_named(module: pa.PyModule, span: tuple[int, int], names: tuple[str, ...]):
    return [c for c in module.calls_within(span) if c.short in names]


def _report(bundle: EvidenceBundle):
    report = bundle.evaluation
    return report if report is not None and report.usable else None


def _mentions(names: tuple[str, ...], text: str) -> str:
    for name in names:
        if re.search(rf"\b{re.escape(name)}\b", text):
            return name
    return ""


# --- the pull-request checklist ------------------------------------------------------


@rule(
    id="SCIKIT-LEARN-C029",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the bug fix or feature, code
                          # that already existed; the test it demands is the artefact
    reads=("files",),  # spec §5: both halves are in the patch
    heuristic=True,
)
class NewTestsAccompanyTheChange:
    """Pre-condition: a contribution that changes package code outside the tests.
    Pass condition: it also adds at least one test function.

    Heuristic on the **pre-condition** (§6.3): "the bug-fixes or new features the PR
    contributes" is approximated by *package source changed*, a superset that also
    catches refactors nobody would ask for a test about. Fires on the change rather than
    on the test, so a contribution that adds nothing is a recorded failure rather than an
    absent row -- the worked case for docs/checker-authoring.md §7.1.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        changed = source_files(b) + cython_files(b)
        if not changed:
            return []
        return [target(f"new-tests:{b.instance_id}", None, None, b,
                       f"{len(changed)} package source file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        added = test_functions(bundle, mode="created")
        if added:
            path, _module, function = added[0]
            return Satisfied(f"{len(added)} test(s) added, e.g. {path}::{function.name}")
        return Violated("package code changed but the contribution adds no test function")


@rule(
    id="SCIKIT-LEARN-C030",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the bug fix
    reads=("files", "evaluation"),  # spec §5: CheckTier=differential, and the harness's
                                    # before/after report is that comparison
    heuristic=True,
)
class NewTestsFailBeforeAndPassAfter:
    """Pre-condition: a contribution that changes package code and adds a test.
    Pass condition: the harness reports at least one test that failed on the base commit
    and passes with the patch.

    Heuristic on the **pre-condition** (§6.3), which approximates *bug fix* by
    source-plus-test -- the spec's own worked example of a rule flagged on its selecting
    layer while its grading layer is a tool's exact verdict. Withholds when the run was
    never graded, which is a named missing input (``evaluation``), not a judgement.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not source_files(b) and not cython_files(b):
            return []
        if not test_functions(b, mode="created"):
            return []
        return [target(f"regression-test:{b.instance_id}", None, None, b,
                       "package source and a new test in one contribution")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        report = _report(bundle)
        if report is None:
            return Undetermined("tool_missing",
                                "the run carries no per-test evaluation report, so "
                                "before-and-after outcomes cannot be compared")
        if newly := report.newly_passing():
            return Satisfied(f"{len(newly)} test(s) fail on main and pass with the "
                             f"patch, e.g. {newly[0]}")
        return Violated("no test in this contribution fails on the unpatched main branch "
                        "and passes with the patch applied")


@rule(
    id="SCIKIT-LEARN-C033",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- one target for the whole contribution
    reads=("files", "evaluation"),  # spec §5: the suite's outcome, as the harness ran it
)
class TheSuitePassesBeforeOpeningThePr:
    """Pre-condition: the agent submitted a contribution.
    Pass condition: the harness reports no test broken by it and none of the tests it was
    meant to fix still failing.

    Deliberately not "the agent ran the suite": the checklist item is that the tests
    *pass*, so a contribution that never ran them is judged rather than excused. Not
    heuristic -- the verdict is a tool's own report (§6.2) -- and it withholds, rather
    than passing, when the run was never graded.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return contribution_target(b, "suite-passes")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        report = _report(bundle)
        if report is None:
            return Undetermined("tool_missing",
                                "the run carries no per-test evaluation report, so the "
                                "suite's outcome is not recorded")
        if regressions := report.regressions():
            return Violated(f"{len(regressions)} test(s) that passed before this change "
                            f"now fail, e.g. {regressions[0]}")
        if still_failing := report.bucket("FAIL_TO_PASS", "failure"):
            return Violated(f"{len(still_failing)} test(s) the change was meant to fix "
                            f"still fail, e.g. {still_failing[0]}")
        return Satisfied(f"the harness reports no failing test over "
                         f"{report.n_outcomes} outcome(s)")


# --- where tests live ----------------------------------------------------------------


@rule(
    id="SCIKIT-LEARN-C106",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "put tests in" is about tests being placed, and
                          # a pre-existing test in the wrong directory is not the agent's
                          # doing; only tests it added are judged
    reads=("files",),  # spec §5
    heuristic=True,
)
class TestsLiveInTheModulesTestsSubdirectory:
    """Pre-condition: each test function the agent added, named `test_*` or `*_test`.
    Pass condition: it sits in a `sklearn/<module>/tests/test_*.py` module and its own
    name carries the `test_` prefix pytest collects on.

    Heuristic on the **pre-condition** (§6.3): "a test" is recognised by the two naming
    conventions pytest publishes, so a test written under a third name is invisible here
    exactly as it is to the test runner. Both halves of the sentence are graded -- the
    `*_test` spelling is selected precisely so the naming half can fail on something.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=None):
            for function in module.functions:
                looks_like_a_test = (function.name.startswith(TEST_PREFIX)
                                     or function.name.endswith("_test"))
                if not looks_like_a_test or "." in function.qualname:
                    continue
                if not own.owns_span(b, path, function.span(), "created"):
                    continue
                out.append(target(f"test-location:{path}:{function.name}", path,
                                  function.span(), (path, function),
                                  f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function = t.payload
        name = path.rsplit("/", 1)[-1]
        if not (path.startswith(PACKAGE) and is_test_path(path)):
            return Violated(f"{path}::{function.name} is not in a `tests/` subdirectory "
                            f"of {PACKAGE}, so pytest's published layout does not find it")
        if not function.name.startswith(TEST_PREFIX):
            return Violated(f"{path}::{function.name} is not named `test_*`, so pytest "
                            f"does not collect it")
        return Satisfied(f"{name}::{function.name} is a `test_`-named function in a "
                         f"`tests/` subdirectory")


# --- deprecation hygiene -------------------------------------------------------------


@rule(
    id="SCIKIT-LEARN-C127",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the deprecation, a change to
                          # code that already existed
    reads=("files",),  # spec §5
    heuristic=True,
)
class ADeprecationCarriesAWarningTest:
    """Pre-condition: a contribution that deprecates a name.
    Pass condition: one of the tests it adds or edits asserts the deprecation warning is
    raised, with `pytest.warns`.

    Heuristic on **both layers** (§6.3, §6.2). The pre-condition recognises a deprecation
    by the `@deprecated` decorator, so one announced only in prose is missed. The pass
    condition is narrower than the sentence: it confirms the warning is asserted and does
    **not** confirm the second half -- *and not in other cases* -- because a test that
    demonstrates the warning's absence has no single recognisable shape. Stated here
    rather than left for a reader to discover.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        deprecated = deprecated_names(b)
        if not deprecated:
            return []
        return [target(f"warning-test:{b.instance_id}", None, None, (b, deprecated),
                       f"deprecates {', '.join(sorted(deprecated))[:80]}")]

    def pass_condition(self, t: Target):
        bundle, deprecated = t.payload
        for path, module, function in owned_functions(bundle, tests=True):
            for call in calls_named(module, function.span(), ("warns",)):
                arguments = " ".join(source_of(a) for a in call.args)
                if "Warning" in arguments:
                    return Satisfied(f"{path}::{function.name} asserts the deprecation "
                                     f"warning with pytest.warns({arguments[:40]})")
        return Violated(f"the contribution deprecates "
                        f"{', '.join(sorted(deprecated))[:60]} but no test asserts that "
                        f"the warning is raised")


@rule(
    id="SCIKIT-LEARN-C128",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- every other test is answerable for catching the
                          # warning, whether the agent wrote it or edited it
    reads=("files",),  # spec §5
    heuristic=True,
)
class OtherTestsCatchTheDeprecationWarning:
    """Pre-condition: in a contribution that deprecates a name, each test the agent wrote
    or edited that uses that name without asserting the warning.
    Pass condition: it catches the warning -- `@pytest.mark.filterwarnings`,
    `warnings.catch_warnings`, or an explicit filter.

    Heuristic on **both layers** (§6.3, §6.2): the deprecated name is recognised from the
    `@deprecated` decorator and its use from the test's source text, and "caught" is
    accepted in the forms the project's own tests use, the marker being the one the
    sentence names by example. The warning test itself is excluded, because that one is
    C127's target and grading it here would report one artefact under two rules (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        deprecated = deprecated_names(b)
        if not deprecated:
            return []
        out = []
        for path, module, function in owned_functions(b, tests=True):
            if not function.name.startswith(TEST_PREFIX):
                continue
            used = _mentions(tuple(deprecated), source_of(function.node))
            if not used:
                continue
            if calls_named(module, function.span(), ("warns",)):
                continue  # this is the warning test itself -- C127's target
            out.append(target(f"catch-warning:{path}:{function.name}", path,
                              function.span(), (path, module, function, used),
                              f"{path}::{function.name} uses {used}"))
        return out

    def pass_condition(self, t: Target):
        path, module, function, used = t.payload
        for decorator in decorator_names(function.node):
            if "filterwarnings" in decorator:
                return Satisfied(f"{path}::{function.name} carries @{decorator} for the "
                                 f"deprecation warning")
        if calls_named(module, function.span(), ("catch_warnings", "simplefilter")):
            return Satisfied(f"{path}::{function.name} catches warnings explicitly")
        return Violated(f"{path}::{function.name} uses the deprecated `{used}` without "
                        f"catching its warning (e.g. @pytest.mark.filterwarnings)")


@rule(
    id="SCIKIT-LEARN-C129",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the deprecation
    reads=("files",),  # spec §5
    heuristic=True,
)
class GalleryExamplesAreFreeOfTheDeprecationWarning:
    """Pre-condition: in a contribution that deprecates a name, each gallery example
    under `examples/` the contribution touches.
    Pass condition: the example does not use the deprecated name.

    Narrowed to examples *in the patch* on purpose: the documentation build checks the
    whole gallery, and the bundle carries only what the contribution changed, so the
    pre-condition fires on the examples the agent is answerable for. Heuristic on **both
    layers** (§6.3, §6.2) -- the deprecation is recognised by decorator, the use by name
    -- and the narrowing means a warning left in an untouched example is out of scope
    rather than silently passed.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        deprecated = deprecated_names(b)
        if not deprecated:
            return []
        return [target(f"example-warning:{path}", path, None, (path, b, deprecated), path)
                for path in example_files(b)]

    def pass_condition(self, t: Target):
        path, bundle, deprecated = t.payload
        used = _mentions(tuple(deprecated), file_text(bundle, path))
        if used:
            return Violated(f"{path} uses the deprecated `{used}`, so the gallery build "
                            f"raises its warning")
        return Satisfied(f"{path} uses none of the names this contribution deprecates")


# --- test style ----------------------------------------------------------------------


@rule(
    id="SCIKIT-LEARN-C184",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- states a property of unit tests, no newness
                          # qualifier
    reads=("files",),  # spec §5
    heuristic=True,
)
class TestsImportFromThePublicLocation:
    """Pre-condition: each `from sklearn...` import in a test module the agent edited.
    Pass condition: the module it names carries no private component.

    Heuristic on the **pass condition** (§6.2): "as client code would" means importing
    from the module that *exports* the object, which no checker can know without the
    package's own `__init__` files, so a leading-underscore component stands in for it --
    the guide's worked case, `sklearn.foo.bar.baz`, is private in exactly this way.
    `sklearn.utils._testing` and its siblings are exempted by name because the project's
    own testing rule C197 points tests at them; without that exemption the two rules
    would contradict each other (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=True):
            for site in module.import_sites:
                base = site.module or site.origin
                if not base.startswith("sklearn"):
                    continue
                if not own.owns_span(b, path, (site.lineno, site.lineno), "touched"):
                    continue
                out.append(target(f"public-import:{path}:{site.lineno}", path,
                                  (site.lineno, site.lineno), (path, site, base),
                                  f"{base} ({site.name})"))
        return out

    def pass_condition(self, t: Target):
        path, site, base = t.payload
        if base in SANCTIONED_PRIVATE_TEST_MODULES:
            return Satisfied(f"{base} is the project's own test helper module")
        private = [part for part in base.split(".") if part.startswith("_")]
        if private:
            return Violated(f"{path}:{site.lineno} imports `{site.name}` from the "
                            f"private `{base}` rather than from its public location")
        return Satisfied(f"{path}:{site.lineno} imports `{site.name}` from the public "
                         f"`{base}`")


@rule(
    id="SCIKIT-LEARN-C197",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class QuasiEqualityUsesTheProjectsAssertAllclose:
    """Pre-condition: each approximate-array-equality assertion in a test the agent wrote
    or edited.
    Pass condition: the helper called is `sklearn.utils._testing.assert_allclose`.

    Heuristic on the **pre-condition** (§6.3): "asserting the quasi-equality of arrays of
    continuous values" is approximated by the family of near-equality assertions --
    numpy's `assert_almost_equal` and friends alongside `assert_allclose` -- so an
    equality asserted through a bare `assert` is not selected. The pass condition resolves
    the written name through the module's import table, so `assert_allclose` imported from
    numpy is told apart from the project's own.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=True):
            for call in module.calls:
                if call.short not in APPROX_ASSERTIONS:
                    continue
                if not own.owns_span(b, path, call.span(), "touched"):
                    continue
                out.append(target(f"allclose:{path}:{call.lineno}", path, call.span(),
                                  (path, call, module.origin(call.func)),
                                  f"{call.func} at {path}:{call.lineno}"))
        return out

    def pass_condition(self, t: Target):
        path, call, origin = t.payload
        if origin == SANCTIONED_ALLCLOSE:
            return Satisfied(f"{path}:{call.lineno} uses {SANCTIONED_ALLCLOSE}")
        return Violated(f"{path}:{call.lineno} asserts quasi-equality with "
                        f"`{origin or call.func}` rather than {SANCTIONED_ALLCLOSE}")


@rule(
    id="SCIKIT-LEARN-C198",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ZeroComparisonsPassAnAbsoluteTolerance:
    """Pre-condition: each `assert_allclose` call the agent wrote or edited whose
    arguments contain a zero.
    Pass condition: it passes a non-zero `atol`.

    Heuristic on the **pre-condition** (§6.3): "arrays of zero-elements" is approximated
    by a literal `0`, `0.0` or a `np.zeros(...)` call among the arguments, so an array of
    zeros arriving through a variable is not selected. The pass condition is exact --
    relative tolerance alone is meaningless against zero, and `atol` either appears with
    a non-zero value or does not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=True):
            for call in module.calls:
                if call.short != "assert_allclose":
                    continue
                if not own.owns_span(b, path, call.span(), "touched"):
                    continue
                arguments = " ".join(source_of(a) for a in call.args)
                if not re.search(r"\bzeros\b|(?<![\w.])0(\.0*)?(?![\w.])", arguments):
                    continue
                out.append(target(f"atol:{path}:{call.lineno}", path, call.span(),
                                  (path, call, arguments),
                                  f"{path}:{call.lineno} {arguments[:60]}"))
        return out

    def pass_condition(self, t: Target):
        path, call, arguments = t.payload
        atol = call.keywords.get("atol")
        if atol is None:
            return Violated(f"{path}:{call.lineno} compares against zero without an "
                            f"`atol`, so only the relative tolerance applies")
        written = source_of(atol)
        if written.strip() in ("0", "0.0", "0."):
            return Violated(f"{path}:{call.lineno} passes atol={written}, which is the "
                            f"same as passing none")
        return Satisfied(f"{path}:{call.lineno} passes atol={written}")


@rule(
    id="SCIKIT-LEARN-C208",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- "every test that needs matplotlib", with no
                          # newness qualifier
    reads=("files",),  # spec §5
    heuristic=True,
)
class MatplotlibTestsTakePyplotFirst:
    """Pre-condition: each test the agent wrote or edited whose module uses matplotlib.
    Pass condition: `pyplot` is its first parameter.

    Heuristic on the **pre-condition** (§6.3): "every test that requires it" is
    approximated by the test module importing or naming matplotlib, which is a superset --
    a test in such a module that never plots is still selected. The pass condition is
    exact: a position in a parameter list, which is stricter than the contributing
    guide's version of the same sentence and is what the plotting page says.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in owned_functions(b, tests=True):
            if not function.name.startswith(TEST_PREFIX):
                continue
            if not _MATPLOTLIB.search(module.source):
                continue
            out.append(target(f"pyplot:{path}:{function.name}", path, function.span(),
                              (path, function), f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function = t.payload
        names = fixture_names(function)
        if names and names[0] == PYPLOT_FIXTURE:
            return Satisfied(f"{path}::{function.name} takes `pyplot` first")
        if PYPLOT_FIXTURE in names:
            return Violated(f"{path}::{function.name} takes `pyplot` at position "
                            f"{names.index(PYPLOT_FIXTURE) + 1}, not first")
        return Violated(f"{path}::{function.name} is in a matplotlib test module but "
                        f"does not take the `pyplot` fixture at all")


@rule(
    id="SCIKIT-LEARN-C232",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class TestsSeedTheirOwnRngInstance:
    """Pre-condition: each test the agent wrote or edited that draws random numbers.
    Pass condition: it does so through its own generator, not a module-level RNG routine.

    A prohibition read as the guide states it, so the antecedent is *using randomness* and
    the graded question is which RNG (§7.1). Heuristic on the **pre-condition** (§6.3):
    randomness is recognised from the call names in the test body, so a helper that draws
    numbers on the test's behalf is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in owned_functions(b, tests=True):
            if not function.name.startswith(TEST_PREFIX):
                continue
            called = calls_in(function.node)
            if not any(_GLOBAL_RNG_CALL.match(c) or c in _OWN_RNG_CALL for c in called):
                continue
            out.append(target(f"rng:{path}:{function.name}", path, function.span(),
                              (path, function, called), f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function, called = t.payload
        offending = [c for c in called if _GLOBAL_RNG_CALL.match(c)]
        if offending:
            return Violated(f"{path}::{function.name} draws from the global RNG "
                            f"singleton with `{offending[0]}`, so its result depends on "
                            f"test execution order")
        own_rng = [c for c in called if c in _OWN_RNG_CALL]
        return Satisfied(f"{path}::{function.name} seeds its own generator with "
                         f"`{own_rng[0]}`")


@rule(
    id="SCIKIT-LEARN-C233",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- the contract binds every test using the fixture
    reads=("files", "evaluation", "repeated_runs"),  # spec §5: the contract is a
                                                     # repeated run; `evaluation` carries
                                                     # the single seed actually executed
)
class GlobalRandomSeedTestsPassForEverySeed:
    """Pre-condition: each test the agent wrote or edited that takes the
    `global_random_seed` fixture.
    Pass condition: it passes for every seed in the range, which the bundle can only
    contradict.

    **Graded one-sidedly, and that is the honest shape.** The bundle carries one run at
    one seed: a failure recorded by the harness disproves "passes for every seed from 0 to
    99" outright, while a success establishes nothing about the other ninety-nine. So this
    fails on evidence and withholds otherwise, never passing vacuously. ``repeated_runs``
    is declared as the Phase 5 source that would settle it, which is what makes the
    withhold a named missing input rather than a judgement call (§5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in owned_functions(b, tests=True):
            if GLOBAL_SEED_FIXTURE not in fixture_names(function):
                continue
            out.append(target(f"seed-contract:{path}:{function.name}", path,
                              function.span(), (path, function, b),
                              f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function, bundle = t.payload
        report = _report(bundle)
        if report is None:
            return Undetermined("tool_missing",
                                f"no evaluation report, so nothing is known about "
                                f"{function.name} at any seed")
        reported = tuple(report.regressions()) + tuple(report.bucket("FAIL_TO_PASS",
                                                                     "failure"))
        failing = [name for name in reported
                   if name.endswith(f"::{function.name}")
                   or f"::{function.name}[" in name]
        if failing:
            return Violated(f"{path}::{function.name} takes the global_random_seed "
                            f"fixture and already fails at the seed the harness ran: "
                            f"{failing[0]}")
        return Undetermined("tool_missing",
                            f"{function.name} was exercised at one seed only; the "
                            f"0-99 contract needs a repeated run")


@rule(
    id="SCIKIT-LEARN-C234",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the sentence says "when writing a NEW test
                          # function that uses this fixture"
    reads=("files", "commands"),  # spec §5: CheckTier=trajectory; the file says the rule
                                  # fires, the command log says whether the run happened
)
class NewSeedTestsAreRunOverAllSeeds:
    """Pre-condition: each test the agent *added* that takes the `global_random_seed`
    fixture.
    Pass condition: a command in the log runs pytest with
    `SKLEARN_TESTS_GLOBAL_RANDOM_SEED="all"`.

    Fires on writing the test, never on having run the command (§7.1) -- selecting the
    invocation would find only agents that already complied. Not heuristic: the sentence
    supplies one environment variable and one invocation, and the command log either
    contains them or does not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, function in owned_functions(b, mode="created", tests=True):
            if GLOBAL_SEED_FIXTURE not in fixture_names(function):
                continue
            out.append(target(f"seed-run:{path}:{function.name}", path, function.span(),
                              (path, function, b), f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function, bundle = t.payload
        for command in ran(bundle, _SEED_ALL_RUN):
            if _PYTEST_RUN.search(command.command):
                return Satisfied(f"the run exercises every admissible seed: "
                                 f"{command.command.strip()[:80]}")
        return Violated(f"{path}::{function.name} is a new global_random_seed test but "
                        f"pytest was never run with "
                        f"SKLEARN_TESTS_GLOBAL_RANDOM_SEED=\"all\"")


@rule(
    id="SCIKIT-LEARN-C243",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the function being replaced by
                          # a compiled extension, code that already existed
    reads=("files",),  # spec §5
    heuristic=True,
)
class ThePythonReferenceImplementationMovesToTheTests:
    """Pre-condition: a contribution that adds a compiled extension source file.
    Pass condition: it also adds a non-test helper function to a test module -- the gold
    standard Python version the extension is asserted against.

    Heuristic on **both layers** (§6.3, §6.2). The pre-condition approximates *a Python
    function was replaced by a compiled extension* by the extension appearing. The pass
    condition approximates *the Python version was moved into the tests* by a plain
    function being added to a test module, which is the structure the step describes; a
    reference implementation kept in a fixture file the contribution does not touch would
    be missed.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        added = [p for p in sorted(b.files)
                 if b.files[p].is_new and p.endswith(COMPILED_SUFFIXES)]
        if not added:
            return []
        return [target(f"reference-impl:{b.instance_id}", None, None, (b, added),
                       f"{len(added)} compiled extension source file(s) added")]

    def pass_condition(self, t: Target):
        bundle, added = t.payload
        for path, module, function in owned_functions(bundle, mode="created", tests=True):
            if function.name.startswith(TEST_PREFIX) or "." in function.qualname:
                continue
            return Satisfied(f"{path}::{function.name} is the Python reference "
                             f"implementation kept beside the tests")
        return Violated(f"{added[0]} is a new compiled extension but no Python reference "
                        f"implementation was added to the tests to check it against")


@rule(
    id="SCIKIT-LEARN-C245",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- a whole-contribution rule about an act, and §4.4
                          # settles those as `touched`
    reads=("commands",),  # spec §5: CheckTier=trajectory, and running pytest is recorded
                          # in the command log
)
class PytestRunsWithFutureWarningsAsErrors:
    """Pre-condition: the agent ran pytest at least once.
    Pass condition: at least one of those runs carries `-Werror::FutureWarning`.

    Fires on running the tests -- the act the rule qualifies -- never on the flag (§7.1).
    A run that never invoked pytest finds no target, which is right: the sentence
    qualifies how the suite is run, and C033 is the rule about it passing. Not heuristic:
    the flag is a literal string in a command line.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        runs = ran(b, _PYTEST_RUN)
        if not runs:
            return []
        return [target(f"werror:{b.instance_id}", None, None, runs,
                       f"{len(runs)} pytest invocation(s)")]

    def pass_condition(self, t: Target):
        runs = t.payload
        for command in runs:
            if _WERROR_FUTURE.search(command.command):
                return Satisfied(f"pytest ran with -Werror::FutureWarning: "
                                 f"{command.command.strip()[:80]}")
        return Violated(f"none of the {len(runs)} pytest invocation(s) used "
                        f"-Werror::FutureWarning, so an uncaught FutureWarning would "
                        f"only surface in CI")

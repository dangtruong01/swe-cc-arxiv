"""pallets (flask): Tests and test style -- 10 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

The naming rules split on what they grade. Where the *name* is not the question -- C072,
C076, C077 -- the pre-condition uses pytest's own collection criterion, a `test_` prefix,
which is exact and published. Where the name **is** the question -- C070 and C071 -- that
criterion cannot be used without inverting the rule (§7.1): selecting `test_*` functions
and then asking whether they are called `test_*` could only ever record a pass. Those two
select on shape instead -- a function that asserts something -- and say so as a declared
heuristic.

**Corpus note (spec §5).** C067 and C084 are filed ``static`` and ``differential``
respectively and neither is decidable from the patch: one needs the suite run, the other
needs the added tests run against the reverted source. Both declare a Phase 5 source and
grade one-sidedly rather than passing on a proxy. ``repeated_runs`` is the nearest
registered source for C084 -- a `revert_run` would name what is actually absent, and is
reported rather than added here, since ``EVIDENCE_SOURCES`` is shared machinery.
"""

from __future__ import annotations

import ast
import re

from compliance.core import ownership as own
from compliance.core.models import (EvidenceBundle, Satisfied, Target, Undetermined,
                                    Violated)
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.pallets._common import (PACKAGE, TEST_ROOTS, UNITTEST_ASSERT,
                                              contribution_target, is_test_path, modules,
                                              named_tests, python_files, shipped_source,
                                              target, test_shaped)

CATEGORY = "Tests and test style"

#: pytest's own collection pattern for modules, which is also what the guide prints.
TEST_MODULE_NAME = re.compile(r"^test_[A-Za-z0-9_]+\.py$|^[A-Za-z0-9_]+_test\.py$")
#: `test_{topic}.py` exactly as the guide writes it.
TOPIC_NAME = re.compile(r"^test_[A-Za-z0-9_]+\.py$")
#: `test_{specific}` -- the prefix plus something specific after it.
SPECIFIC_NAME = re.compile(r"^test_[A-Za-z0-9_]+$")
#: Support modules that live under `tests/` and are not themselves tests.
NOT_A_TEST_MODULE = ("conftest.py", "__init__.py")

_MIN_CASES = 3


def _basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def _test_modules(bundle: EvidenceBundle, *, mode: str = "touched"):
    """(path, PyModule) for each owned module under `tests/` that is not a support file."""
    return [(path, module) for path, module in modules(bundle, mode=mode, tests=True)
            if _basename(path) not in NOT_A_TEST_MODULE]


def _owns(bundle: EvidenceBundle, path: str, func) -> bool:
    return own.owns_span(bundle, path, func.span(), "touched")


def _added_tests(bundle: EvidenceBundle) -> list[tuple[str, object]]:
    """Collected tests whose definition the agent wrote, across the test files."""
    out = []
    for path, module in _test_modules(bundle):
        for func in named_tests(module):
            if bundle.files[path].is_new or _owns(bundle, path, func):
                out.append((path, func))
    return out


def _iterates_a_literal(func) -> bool:
    """`for case in [...]` -- a hand-rolled parametrisation, and the shape C077 is about."""
    if func.node is None:
        return False
    for node in ast.walk(func.node):
        if isinstance(node, (ast.For, ast.comprehension)):
            iterated = node.iter
            if isinstance(iterated, (ast.List, ast.Tuple, ast.Set)) and len(iterated.elts) > 1:
                return True
    return False


@rule(
    id="PALLETS-C066",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- one target for the whole contribution
    reads=("files",),  # spec §5: both halves of the sentence are in the patch
    heuristic=True,
)
class TestsDemonstrateTheChange:
    """Pre-condition: the contribution changes shipped source under `src/flask/`.
    Pass condition: it also adds or changes a file under `tests/`.

    Heuristic on **both** layers (§6.3, §6.2). The antecedent is *your code*, approximated
    by a change to the shipped package, so a documentation-only or tooling-only
    contribution finds no target instead of being graded. And *demonstrate that your code
    works* is graded as the presence of a test change: whether the test actually exercises
    the changed behaviour is exactly what C084 needs a tool run to answer, and is not
    decidable here.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        source = shipped_source(b)
        if not source:
            return []
        return [target(f"tests-added:{b.instance_id}", None, None, b,
                       f"{len(source)} shipped source file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        tests = [p for p in sorted(bundle.files) if is_test_path(p)]
        if tests:
            return Satisfied(f"{len(tests)} file(s) under tests/ changed alongside the "
                             f"code: {tests[0]}")
        return Violated("shipped source changed with nothing under tests/ in the "
                        "contribution")


@rule(
    id="PALLETS-C067",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- the obligation is on the contribution as a whole
    reads=("files", "full_suite_run"),  # spec §5: the suite's result, which nothing runs yet
)
class WholeSuitePassesBeforeSubmitting:
    """Pre-condition: the contribution submits Python.
    Pass condition: the whole test suite passes over it.

    Graded **one-sidedly**. A submitted module that will not parse cannot be collected, so
    the suite provably fails and that is decidable from the patch. Nothing else is: the
    harness runs the benchmark's subset, not the whole suite, and inferring a passing suite
    from source text would be a silent 100%. So this fails on evidence and withholds
    otherwise -- never a vacuous pass.

    Not heuristic: the failing branch is a fact about the file, and the other branch does
    not grade at all.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not python_files(b):
            return []
        return contribution_target(b, "suite-passes",
                                   f"{len(python_files(b))} Python file(s) submitted")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        for path in python_files(bundle):
            text = bundle.files[path].head_text
            if text is None:
                continue
            module = pa.parse_module(text, path)
            if not module.ok and module.error != pa.NO_SOURCE:
                return Violated(f"the suite cannot pass: {path} is not valid Python "
                                f"({module.error})")
        return Undetermined("tool_missing",
                            "no run of the whole test suite is recorded for this "
                            "contribution")


@rule(
    id="PALLETS-C069",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the corpus trigger reads "adds a new test file";
                          # a misplaced test the agent merely edited is not its doing
    reads=("files",),  # spec §5: a path in the patch
)
class NewTestFilesLiveUnderTests:
    """Pre-condition: each test module the agent added, recognised by pytest's own
    collection pattern.
    Pass condition: its path is under `tests/`.

    Not heuristic. The pre-condition selects on the published `test_*.py` / `*_test.py`
    pattern, which is an exact observable fact (§6.3), and the pass condition is a path
    prefix (§6.2). A newly added test module named neither way is not selected, which
    under-reports rather than manufacturing a violation (§4.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            if not path.endswith(".py") or not own.owns_file(b, path, "created"):
                continue
            if TEST_MODULE_NAME.match(_basename(path)):
                out.append(target(f"test-location:{path}", path, None, path, path))
        return out

    def pass_condition(self, t: Target):
        path = t.payload
        if is_test_path(path):
            return Satisfied(f"{path} is under {TEST_ROOTS[0]}")
        return Violated(f"{path} is a test module outside {TEST_ROOTS[0]}, where pytest's "
                        f"configured testpaths will not collect it")


@rule(
    id="PALLETS-C070",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- the sentence states a property with no newness
                          # qualifier, so a test file the agent edited is in scope
    reads=("files",),  # spec §5
    heuristic=True,
)
class TestFilesNamedByTopic:
    """Pre-condition: each module under `tests/` the agent added or edited that defines a
    function which asserts something.
    Pass condition: its filename matches `test_{topic}.py`.

    Heuristic on the **pre-condition** (§6.3). *A test file* is approximated by content --
    a module that contains an asserting function -- because selecting on the filename
    pattern would be §7.1 inverted: every selected file would already comply. `conftest.py`
    and `__init__.py` are excluded by name, being the two support modules the layout
    requires; another helper module under `tests/` that happens to assert would be
    reported, and that is the cost of the approximation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _test_modules(b):
            if test_shaped(module):
                out.append(target(f"test-filename:{path}", path, None, path,
                                  _basename(path)))
        return out

    def pass_condition(self, t: Target):
        path = t.payload
        name = _basename(path)
        if TOPIC_NAME.match(name):
            return Satisfied(f"{name} matches test_{{topic}}.py")
        return Violated(f"{name} does not match test_{{topic}}.py")


@rule(
    id="PALLETS-C071",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property with no newness qualifier
    reads=("files",),  # spec §5
    heuristic=True,
)
class TestFunctionsNamedBySpecific:
    """Pre-condition: each function under `tests/` the agent wrote or edited that asserts
    something.
    Pass condition: its name matches `test_{specific}`.

    Heuristic on the **pre-condition** (§6.3), and for the same reason as C070: the name is
    what is graded, so the name cannot also be what selects. *A test* is approximated by a
    non-private, non-fixture function that asserts -- which admits the unittest family as
    well as a bare `assert`, so a badly named test is still visible. A local helper that
    asserts an invariant inside a test module is selected too, and would be reported; that
    over-fires rather than exempting the tests the rule is about.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _test_modules(b):
            for func in test_shaped(module):
                if b.files[path].is_new or _owns(b, path, func):
                    out.append(target(f"test-name:{path}:{func.lineno}", path,
                                      func.span(), func.name, f"def {func.name}"))
        return out

    def pass_condition(self, t: Target):
        name = t.payload
        if SPECIFIC_NAME.match(name):
            return Satisfied(f"`{name}` matches test_{{specific}}")
        return Violated(f"`{name}` does not match test_{{specific}}, so pytest will not "
                        f"collect it")


@rule(
    id="PALLETS-C072",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- the module the names live in already existed
    reads=("files",),  # spec §5
)
class TestFunctionNamesAreUnique:
    """Pre-condition: each test module the agent added or edited that defines a collected
    test.
    Pass condition: no test name the agent wrote is defined twice in that module.

    Not heuristic: both layers are exact (§6.2, §6.3). Selection is pytest's own `test_`
    prefix, and uniqueness is decided by collecting the names in the module. Scoped to the
    module, because that is where a duplicate does its damage -- the second definition
    shadows the first and the first is silently never run -- and scoped to names the agent
    wrote, so a collision that was already in the file is not charged to the run.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _test_modules(b):
            tests = named_tests(module)
            if tests:
                out.append(target(f"unique-name:{path}", path, None, (b, path, module),
                                  f"{len(tests)} test(s) in {_basename(path)}"))
        return out

    def pass_condition(self, t: Target):
        bundle, path, module = t.payload
        names = [f.name for f in named_tests(module)]
        for func in named_tests(module):
            if not (bundle.files[path].is_new or _owns(bundle, path, func)):
                continue
            if names.count(func.name) > 1:
                return Violated(f"{path} defines `{func.name}` {names.count(func.name)} "
                                f"times; the earlier definition is shadowed and never run")
        return Satisfied(f"{len(names)} test name(s) in {_basename(path)} are unique")


@rule(
    id="PALLETS-C074",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- one target for the whole contribution
    reads=("files",),  # spec §5: the diff carries both the fix and where the tests went
    heuristic=True,
)
class BugFixExtendsAnExistingTestFile:
    """Pre-condition: a contribution read as a single bug fix that adds tests -- it
    changes shipped source without adding a public API, and it adds test functions.
    Pass condition: those tests went into a test file that already existed.

    Heuristic on the **pre-condition** (§6.3). *A single bug fix* is not observable: the
    task's provenance is a fact about the benchmark, not about the contribution, and the
    corpus does not license reading it. The stand-in is a change to existing shipped source
    that adds no new module -- a contribution that adds a new source file is taken to be a
    feature and finds no target, which is the direction that under-reports.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        source = shipped_source(b)
        if not source or any(b.files[p].is_new for p in source):
            return []
        if not _added_tests(b):
            return []
        return [target(f"extend-tests:{b.instance_id}", None, None, b,
                       f"{len(source)} source file(s) changed, tests added")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        new_files = sorted({path for path, _ in _added_tests(bundle)
                            if bundle.files[path].is_new})
        if new_files:
            return Violated(f"a bug fix adds the new test file {new_files[0]} instead of "
                            f"extending an existing related one")
        touched = sorted({path for path, _ in _added_tests(bundle)})
        return Satisfied(f"the added tests extend the existing file {touched[0]}")


@rule(
    id="PALLETS-C076",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property with no newness qualifier
    reads=("files",),  # spec §5
    heuristic=True,
)
class TestsUsePlainAssert:
    """Pre-condition: each collected test under `tests/` the agent wrote or edited.
    Pass condition: it checks its expectations with `assert`, not with the unittest
    assertion family.

    Heuristic on the **pass condition** (§6.2), graded one-sidedly. A `self.assertEqual`
    or `assertRaises` call is positive evidence of the form the guide does not use; the
    absence of one is not proof that the test asserts anything at all, so a test with no
    checks is recorded as satisfying. Where a bare `assert` is present that is reported as
    the satisfying evidence, which is stronger than mere absence.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _test_modules(b):
            for func in named_tests(module):
                if not (b.files[path].is_new or _owns(b, path, func)):
                    continue
                span = func.span()
                body = "\n".join(module.source.split("\n")[span[0] - 1:span[1]])
                out.append(target(f"plain-assert:{path}:{func.lineno}", path, span,
                                  (path, func, module, body), f"def {func.name}"))
        return out

    def pass_condition(self, t: Target):
        path, func, module, body = t.payload
        if match := UNITTEST_ASSERT.search(body):
            return Violated(f"{path}:{func.lineno} `{func.name}` checks with "
                            f"`{match.group(0).strip()}` instead of a plain assert")
        if module.asserts_within(func.span()):
            return Satisfied(f"{path}:{func.lineno} `{func.name}` uses plain assert "
                             f"statements")
        return Satisfied(f"{path}:{func.lineno} `{func.name}` carries no non-assert "
                         f"assertion form")


@rule(
    id="PALLETS-C077",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property with no newness qualifier
    reads=("files",),  # spec §5
    heuristic=True,
)
class MultipleCasesAreParametrized:
    """Pre-condition: each collected test the agent wrote or edited that covers more than
    one input case.
    Pass condition: it carries `@pytest.mark.parametrize`.

    Heuristic on the **pre-condition** (§6.3). *Multiple test cases* is an intent, and the
    stand-in is three observable shapes: the decorator itself, a loop over a literal
    sequence of more than one element, and three or more assert statements. The decorator
    is deliberately one of them -- leaving it out would select only tests written the wrong
    way, so the rule could record a violation and never a compliant test (§7.1). Three
    asserts is the loose one: a single-case test that checks three properties of one result
    is selected and reported, which over-fires.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _test_modules(b):
            for func in named_tests(module):
                if not (b.files[path].is_new or _owns(b, path, func)):
                    continue
                n_asserts = len(module.asserts_within(func.span()))
                multiple = (func.has_decorator("parametrize", "pytest.mark.parametrize")
                            or _iterates_a_literal(func) or n_asserts >= _MIN_CASES)
                if multiple:
                    out.append(target(f"parametrize:{path}:{func.lineno}", path,
                                      func.span(), (path, func, n_asserts),
                                      f"def {func.name}"))
        return out

    def pass_condition(self, t: Target):
        path, func, n_asserts = t.payload
        if func.has_decorator("parametrize", "pytest.mark.parametrize"):
            return Satisfied(f"{path}:{func.lineno} `{func.name}` is parametrized")
        return Violated(f"{path}:{func.lineno} `{func.name}` covers several cases "
                        f"({n_asserts} assert(s), or a loop over a literal) without "
                        f"@pytest.mark.parametrize")


@rule(
    id="PALLETS-C084",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- the contribution as a whole is what is reverted
    reads=("files", "repeated_runs"),  # spec §5: the added tests, run against the
                                       # reverted source -- a run nothing collects yet
)
class AddedTestsFailWithoutTheChange:
    """Pre-condition: the contribution adds test functions.
    Pass condition: those tests fail when the change is reverted.

    Graded **one-sidedly**. One branch is decidable from the patch and conclusive: tests
    added by a contribution that changes no shipped source cannot behave differently with
    the change reverted, because there is nothing to revert. Beyond that the verdict needs
    the added tests executed against the base tree, which no source in the bundle carries,
    so the rule withholds rather than passing on a proxy.

    Not heuristic: the failing branch is a fact about the diff, and the other branch does
    not grade.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        added = _added_tests(b)
        if not added:
            return []
        return [target(f"fails-when-reverted:{b.instance_id}", None, None, (b, added),
                       f"{len(added)} test(s) added")]

    def pass_condition(self, t: Target):
        bundle, added = t.payload
        if not shipped_source(bundle):
            return Violated(f"{len(added)} test(s) were added but nothing under "
                            f"{PACKAGE} changed, so reverting the change cannot make "
                            f"them fail")
        return Undetermined("tool_missing",
                            f"the {len(added)} added test(s) were never run against the "
                            f"reverted source")

"""sphinx-doc: Tests and test style -- 4 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

The guide treats code and tests as one deliverable and grants no exception for either bug
fixes or features, which is why C004 fires on any source change rather than on the presence
of a test.

**C026 is the only rule in this corpus that a static reading cannot answer.** It asks for a
test that *fails before the patch and passes after it*, which is a before-and-after fact
about executing the suite, so it is graded from the harness's own report.
"""

from __future__ import annotations

import re

from compliance.core import ownership as own
from compliance.core.models import EvidenceBundle, Satisfied, Target, Undetermined, Violated
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.sphinx_doc._common import python_files, ran, target

CATEGORY = "Tests and test style"

TEST_ROOT = "tests/"

#: `npm run test` and `npm test` are the two forms the contributing guide gives.
_NPM_TEST = re.compile(r"\bnpm\s+(run\s+)?test\b")
_JS_SUFFIX = ".js"


def _test_functions_created(bundle: EvidenceBundle) -> list[tuple[str, str, int]]:
    """Test functions the agent brought into existence, wherever they were put."""
    out: list[tuple[str, str, int]] = []
    for path in python_files(bundle, tests=None):
        text = bundle.files[path].head_text
        if text is None:
            continue
        module = pa.parse_module(text, path)
        if not module.ok:
            continue
        for function in module.tests():
            if function.qualname != function.name:
                continue
            if own.owns_span(bundle, path, function.span(), "created"):
                out.append((path, function.name, function.lineno))
    return out


@rule(
    id="SPHINX-DOC-C004",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- the antecedent is the code change
    reads=("files",),  # spec §5: both halves are in the patch
    heuristic=True,
)
class TestsAccompanyTheCodeChange:
    """Pre-condition: the contribution changes non-test Python source.
    Pass condition: it also changes or adds a test file.

    Heuristic because *demonstrating that the bug was fixed* is not settled by a test
    existing. A test that accompanies the change is the strongest signal the patch itself
    carries; whether it demonstrates anything is what C026 asks of the harness instead.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        source = python_files(b, tests=False)
        if not source:
            return []
        return [target(f"tests-alongside:{b.instance_id}", None, None, b,
                       f"{len(source)} source file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        tests = [p for p in sorted(bundle.files) if pa.is_test_path(p)]
        if tests:
            return Satisfied(f"{len(tests)} test file(s) changed alongside the code: "
                             f"{tests[0]}")
        return Violated("source changed with no test file in the contribution")


@rule(
    id="SPHINX-DOC-C024",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched
    reads=("files", "commands"),  # spec §5: CheckTier=trajectory, running is an act
)
class JavaScriptSuiteRunWithNpm:
    """Pre-condition: the contribution changes a JavaScript file.
    Pass condition: an `npm test` or `npm run test` invocation appears in the command log.

    The Firefox requirement the guide notes in a tip conditions the environment, not the
    obligation, so it is not part of the pass condition.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        js = [p for p in sorted(b.files)
              if p.endswith(_JS_SUFFIX) and own.owns_file(b, p, "touched")]
        if not js:
            return []
        return [target(f"npm:{b.instance_id}", None, None, b,
                       f"{len(js)} JavaScript file(s) changed: {js[0]}")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if runs := ran(bundle, _NPM_TEST):
            return Satisfied(f"JavaScript suite run: {runs[0].command.strip()[:80]}")
        return Violated("JavaScript changed but the npm test suite was never run")


@rule(
    id="SPHINX-DOC-C025",
    category=CATEGORY,
    ownership="created",  # spec §4 created -- the test did not exist before the run
    reads=("files",),  # spec §5: the path is the whole question
)
class NewTestsLiveUnderTests:
    """Pre-condition: each test function the agent added.
    Pass condition: the file it was added to is under `tests/`.

    "Where necessary" in the source sentence governs whether a test is needed, not where it
    goes, so it does not soften this. A test the agent did not create is not selected: the
    rule is about placing new tests, not about relocating the project's existing ones.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"testloc:{path}:{name}", path, (lineno, lineno), path,
                       f"def {name}")
                for path, name, lineno in _test_functions_created(b)]

    def pass_condition(self, t: Target):
        path: str = t.payload
        if path.startswith(TEST_ROOT):
            return Satisfied(f"{path} is under {TEST_ROOT}")
        return Violated(f"new test added in {path}, outside {TEST_ROOT}")


@rule(
    id="SPHINX-DOC-C026",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- the antecedent is the fix
    reads=("files", "evaluation"),  # spec §5: CheckTier=differential, before and after
    heuristic=True,
)
class TestFailsBeforeAndPassesAfter:
    """Pre-condition: the contribution changes non-test Python source and also changes a
    test file.
    Pass condition: the harness reports at least one test that failed before the patch and
    passes after it.

    Heuristic for a reason worth stating: the tests the harness flips are the *benchmark's*
    tests, not necessarily the ones the agent wrote. A contribution can therefore be
    credited for a transition its own test did not cause. The alternative -- executing the
    agent's test against the base commit -- needs a runner this instrument does not have,
    so the proxy is declared rather than avoided.

    Withheld, never failed, when the run carries no functional result: absence of a report
    is not absence of a passing test.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not python_files(b, tests=False):
            return []
        if not [p for p in sorted(b.files) if pa.is_test_path(p)]:
            return []
        return [target(f"failfirst:{b.instance_id}", None, None, b,
                       "source and tests changed together")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        report = bundle.evaluation
        if report is None or not report.usable:
            note = report.note if report is not None else "no functional result"
            return Undetermined("tool_missing",
                                f"cannot tell whether a test changed state: {note}")
        if flipped := report.newly_passing():
            return Satisfied(f"{len(flipped)} test(s) failed before the patch and pass "
                             f"after it, e.g. {flipped[0]}")
        return Violated(f"no test among the {report.n_outcomes} the harness ran failed "
                        f"before the patch and passes after it")

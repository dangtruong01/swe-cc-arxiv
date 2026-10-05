"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

**C233 has no satisfying case, and that is not an omission.** Its contract -- passes for
every seed from 0 to 99 -- can only be contradicted by the single seed the harness ran,
so its three cases are violated, withheld (asserting the row is `not_applicable` with a
non-`ok` status, never a silent pass), and no target (§9's alternative triple for a
one-sidedly graded rule).

C128 and C129 take *a deprecation was introduced* as their antecedent, so a contribution
that deprecates nothing finds no target in either.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.evaluation import EvalReport
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.scikit_learn.tests  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("sklearn/svm/_base.py", [(1, "x = 1")])
DOC = make_file("doc/modules/svm.rst", [(1, "Support vector machines")])


@pytest.fixture(scope="module")
def corpus():
    """scikit-learn's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("scikit-learn"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def module(text, path="sklearn/svm/tests/test_svm.py", new=True):
    lines = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text, is_new=new)


def report(**buckets) -> EvalReport:
    return EvalReport(shape="instance", instance_id="test__test-1",
                      tests_status=dict(buckets))


PASSING = report(PASS_TO_PASS={"success": ("test_a",)})

DEPRECATION = module(
    "from sklearn.utils import deprecated\n"
    "\n"
    "@deprecated('use predict_proba instead')\n"
    "def predict_probability(self, X):\n"
    "    return None\n",
    path="sklearn/svm/_classes.py")


# --- C029 new tests accompany the change ----------------------------------------------


def test_c029_passes_when_a_test_is_added(corpus):
    bundle = make_bundle(files=[SOURCE, module("def test_kernel():\n    assert True\n")])
    assert verdict("SCIKIT-LEARN-C029", bundle, corpus).verdict == "pass"


def test_c029_fails_when_only_source_changed(corpus):
    assert verdict("SCIKIT-LEARN-C029", make_bundle(files=[SOURCE]),
                   corpus).verdict == "fail"


def test_c029_finds_no_target_for_a_documentation_change(corpus):
    row = verdict("SCIKIT-LEARN-C029", make_bundle(files=[DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C030 the new tests fail before and pass after ------------------------------------


def test_c030_passes_when_the_harness_reports_a_newly_passing_test(corpus):
    bundle = make_bundle(files=[SOURCE, module("def test_kernel():\n    assert True\n")],
                         evaluation=report(FAIL_TO_PASS={"success": ("test_kernel",)}))
    assert verdict("SCIKIT-LEARN-C030", bundle, corpus).verdict == "pass"


def test_c030_fails_when_nothing_changed_state(corpus):
    bundle = make_bundle(files=[SOURCE, module("def test_kernel():\n    assert True\n")],
                         evaluation=PASSING)
    assert verdict("SCIKIT-LEARN-C030", bundle, corpus).verdict == "fail"


def test_c030_finds_no_target_when_the_change_adds_no_test(corpus):
    row = verdict("SCIKIT-LEARN-C030", make_bundle(files=[SOURCE], evaluation=PASSING),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C033 the suite passes ------------------------------------------------------------


def test_c033_passes_when_the_harness_reports_no_failure(corpus):
    bundle = make_bundle(files=[SOURCE], evaluation=PASSING)
    assert verdict("SCIKIT-LEARN-C033", bundle, corpus).verdict == "pass"


def test_c033_fails_on_a_regression(corpus):
    bundle = make_bundle(files=[SOURCE],
                         evaluation=report(PASS_TO_PASS={"failure": ("test_b",)}))
    assert verdict("SCIKIT-LEARN-C033", bundle, corpus).verdict == "fail"


def test_c033_finds_no_target_for_an_empty_contribution(corpus):
    row = verdict("SCIKIT-LEARN-C033", make_bundle(files=[], evaluation=PASSING), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C106 tests live in the module's tests/ subdirectory ------------------------------


def test_c106_passes_for_a_test_in_the_tests_subdirectory(corpus):
    bundle = make_bundle(files=[module("def test_kernel():\n    assert True\n")])
    assert verdict("SCIKIT-LEARN-C106", bundle, corpus).verdict == "pass"


def test_c106_fails_for_a_test_outside_it(corpus):
    bundle = make_bundle(files=[module("def test_kernel():\n    assert True\n",
                                       path="sklearn/svm/test_svm.py")])
    assert verdict("SCIKIT-LEARN-C106", bundle, corpus).verdict == "fail"


def test_c106_fails_on_a_test_named_the_wrong_way_round(corpus):
    bundle = make_bundle(files=[module("def kernel_test():\n    assert True\n")])
    assert verdict("SCIKIT-LEARN-C106", bundle, corpus).verdict == "fail"


def test_c106_finds_no_target_when_no_test_was_added(corpus):
    row = verdict("SCIKIT-LEARN-C106",
                  make_bundle(files=[module("def helper():\n    return 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C127 a deprecation carries a warning test ----------------------------------------


def test_c127_passes_when_a_test_asserts_the_warning(corpus):
    tests = module("import pytest\n"
                   "def test_deprecated():\n"
                   "    with pytest.warns(FutureWarning):\n"
                   "        pass\n")
    bundle = make_bundle(files=[DEPRECATION, tests])
    assert verdict("SCIKIT-LEARN-C127", bundle, corpus).verdict == "pass"


def test_c127_fails_when_no_test_asserts_it(corpus):
    tests = module("def test_predict():\n    assert True\n")
    bundle = make_bundle(files=[DEPRECATION, tests])
    assert verdict("SCIKIT-LEARN-C127", bundle, corpus).verdict == "fail"


def test_c127_finds_no_target_without_a_deprecation(corpus):
    row = verdict("SCIKIT-LEARN-C127", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C128 other tests catch the deprecation warning -----------------------------------


def test_c128_passes_when_the_other_test_filters_the_warning(corpus):
    tests = module("import pytest\n"
                   "@pytest.mark.filterwarnings('ignore::FutureWarning')\n"
                   "def test_still_works():\n"
                   "    predict_probability(None, None)\n")
    bundle = make_bundle(files=[DEPRECATION, tests])
    assert verdict("SCIKIT-LEARN-C128", bundle, corpus).verdict == "pass"


def test_c128_fails_when_it_does_not(corpus):
    tests = module("def test_still_works():\n"
                   "    predict_probability(None, None)\n")
    bundle = make_bundle(files=[DEPRECATION, tests])
    assert verdict("SCIKIT-LEARN-C128", bundle, corpus).verdict == "fail"


def test_c128_finds_no_target_when_no_other_test_uses_the_name(corpus):
    tests = module("def test_predict():\n    assert True\n")
    row = verdict("SCIKIT-LEARN-C128", make_bundle(files=[DEPRECATION, tests]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C129 gallery examples are free of the warning ------------------------------------


def test_c129_passes_when_the_touched_example_avoids_the_name(corpus):
    example = module("from sklearn.svm import SVC\nSVC().fit(X, y)\n",
                     path="examples/svm/plot_svm.py")
    bundle = make_bundle(files=[DEPRECATION, example])
    assert verdict("SCIKIT-LEARN-C129", bundle, corpus).verdict == "pass"


def test_c129_fails_when_the_example_uses_the_deprecated_name(corpus):
    example = module("clf.predict_probability(X)\n", path="examples/svm/plot_svm.py")
    bundle = make_bundle(files=[DEPRECATION, example])
    assert verdict("SCIKIT-LEARN-C129", bundle, corpus).verdict == "fail"


def test_c129_finds_no_target_when_no_example_is_touched(corpus):
    row = verdict("SCIKIT-LEARN-C129", make_bundle(files=[DEPRECATION]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C184 tests import from the public location ---------------------------------------


def test_c184_passes_on_a_public_import(corpus):
    bundle = make_bundle(files=[module("from sklearn.svm import SVC\n"
                                       "def test_svc():\n    assert SVC\n")])
    assert verdict("SCIKIT-LEARN-C184", bundle, corpus).verdict == "pass"


def test_c184_fails_on_a_private_submodule_import(corpus):
    bundle = make_bundle(files=[module("from sklearn.svm._base import BaseLibSVM\n"
                                       "def test_svc():\n    assert BaseLibSVM\n")])
    assert verdict("SCIKIT-LEARN-C184", bundle, corpus).verdict == "fail"


def test_c184_allows_the_projects_own_test_helpers(corpus):
    """C197 sends tests to `sklearn.utils._testing`; this rule must not contradict it."""
    bundle = make_bundle(files=[module(
        "from sklearn.utils._testing import assert_allclose\n"
        "def test_svc():\n    assert assert_allclose\n")])
    assert verdict("SCIKIT-LEARN-C184", bundle, corpus).verdict == "pass"


def test_c184_finds_no_target_without_a_sklearn_import(corpus):
    bundle = make_bundle(files=[module("def test_svc():\n    assert True\n")])
    row = verdict("SCIKIT-LEARN-C184", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C197 quasi-equality uses the project's assert_allclose ---------------------------


def test_c197_passes_on_the_projects_helper(corpus):
    bundle = make_bundle(files=[module(
        "from sklearn.utils._testing import assert_allclose\n"
        "def test_close():\n    assert_allclose(a, b)\n")])
    assert verdict("SCIKIT-LEARN-C197", bundle, corpus).verdict == "pass"


def test_c197_fails_on_numpys_own_assertion(corpus):
    bundle = make_bundle(files=[module(
        "from numpy.testing import assert_array_almost_equal\n"
        "def test_close():\n    assert_array_almost_equal(a, b)\n")])
    assert verdict("SCIKIT-LEARN-C197", bundle, corpus).verdict == "fail"


def test_c197_finds_no_target_without_an_approximate_assertion(corpus):
    bundle = make_bundle(files=[module("def test_close():\n    assert a == b\n")])
    row = verdict("SCIKIT-LEARN-C197", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C198 zero comparisons pass an absolute tolerance ---------------------------------


def test_c198_passes_when_atol_is_given(corpus):
    bundle = make_bundle(files=[module(
        "from sklearn.utils._testing import assert_allclose\n"
        "def test_zero():\n    assert_allclose(out, np.zeros(3), atol=1e-9)\n")])
    assert verdict("SCIKIT-LEARN-C198", bundle, corpus).verdict == "pass"


def test_c198_fails_without_atol(corpus):
    bundle = make_bundle(files=[module(
        "from sklearn.utils._testing import assert_allclose\n"
        "def test_zero():\n    assert_allclose(out, np.zeros(3))\n")])
    assert verdict("SCIKIT-LEARN-C198", bundle, corpus).verdict == "fail"


def test_c198_finds_no_target_when_no_zero_is_compared(corpus):
    bundle = make_bundle(files=[module(
        "from sklearn.utils._testing import assert_allclose\n"
        "def test_close():\n    assert_allclose(out, expected)\n")])
    row = verdict("SCIKIT-LEARN-C198", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C208 matplotlib tests take pyplot first ------------------------------------------


def test_c208_passes_when_pyplot_comes_first(corpus):
    bundle = make_bundle(files=[module(
        "import matplotlib\n"
        "def test_plot(pyplot, data):\n    assert data is not None\n")])
    assert verdict("SCIKIT-LEARN-C208", bundle, corpus).verdict == "pass"


def test_c208_fails_when_pyplot_comes_second(corpus):
    bundle = make_bundle(files=[module(
        "import matplotlib\n"
        "def test_plot(data, pyplot):\n    assert data is not None\n")])
    assert verdict("SCIKIT-LEARN-C208", bundle, corpus).verdict == "fail"


def test_c208_finds_no_target_in_a_module_that_never_plots(corpus):
    bundle = make_bundle(files=[module("def test_kernel():\n    assert True\n")])
    row = verdict("SCIKIT-LEARN-C208", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C232 tests seed their own RNG instance -------------------------------------------


def test_c232_passes_on_an_independent_generator(corpus):
    bundle = make_bundle(files=[module(
        "def test_noise():\n"
        "    rng = np.random.RandomState(0)\n"
        "    assert rng is not None\n")])
    assert verdict("SCIKIT-LEARN-C232", bundle, corpus).verdict == "pass"


def test_c232_fails_on_the_global_singleton(corpus):
    bundle = make_bundle(files=[module(
        "def test_noise():\n    values = np.random.rand(10)\n    assert values.size\n")])
    assert verdict("SCIKIT-LEARN-C232", bundle, corpus).verdict == "fail"


def test_c232_finds_no_target_in_a_deterministic_test(corpus):
    bundle = make_bundle(files=[module("def test_kernel():\n    assert True\n")])
    row = verdict("SCIKIT-LEARN-C232", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C233 the global_random_seed contract (one-sidedly graded) ------------------------


SEED_TEST = module("def test_kernel(global_random_seed):\n"
                   "    assert global_random_seed >= 0\n")


def test_c233_fails_when_the_harness_already_saw_it_fail(corpus):
    bundle = make_bundle(files=[SEED_TEST], evaluation=report(
        PASS_TO_PASS={"failure": ("sklearn/svm/tests/test_svm.py::test_kernel",)}))
    assert verdict("SCIKIT-LEARN-C233", bundle, corpus).verdict == "fail"


def test_c233_withholds_when_only_one_seed_was_run(corpus):
    row = verdict("SCIKIT-LEARN-C233",
                  make_bundle(files=[SEED_TEST], evaluation=PASSING), corpus)
    assert row.verdict == "not_applicable" and row.status != "ok"


def test_c233_finds_no_target_without_the_fixture(corpus):
    bundle = make_bundle(files=[module("def test_kernel():\n    assert True\n")])
    row = verdict("SCIKIT-LEARN-C233", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C234 a new seed test is run over all seeds ---------------------------------------


def test_c234_passes_when_the_all_seeds_run_appears(corpus):
    bundle = make_bundle(files=[SEED_TEST], commands=[
        'SKLEARN_TESTS_GLOBAL_RANDOM_SEED="all" pytest -v -k test_kernel'])
    assert verdict("SCIKIT-LEARN-C234", bundle, corpus).verdict == "pass"


def test_c234_fails_when_the_tests_were_run_at_one_seed(corpus):
    bundle = make_bundle(files=[SEED_TEST], commands=["pytest -v -k test_kernel"])
    assert verdict("SCIKIT-LEARN-C234", bundle, corpus).verdict == "fail"


def test_c234_finds_no_target_for_a_test_without_the_fixture(corpus):
    bundle = make_bundle(files=[module("def test_kernel():\n    assert True\n")],
                         commands=["pytest"])
    row = verdict("SCIKIT-LEARN-C234", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C243 the Python reference implementation moves to the tests ----------------------


EXTENSION = make_file("sklearn/svm/_fast.pyx", [(1, "cdef double f(double x):"),
                                                (2, "    return x")],
                      head_text="cdef double f(double x):\n    return x\n", is_new=True)


def test_c243_passes_when_the_tests_keep_a_python_version(corpus):
    tests = module("def _slow_f(x):\n    return x\n\n"
                   "def test_fast_matches():\n    assert True\n")
    assert verdict("SCIKIT-LEARN-C243", make_bundle(files=[EXTENSION, tests]),
                   corpus).verdict == "pass"


def test_c243_fails_when_only_tests_were_added(corpus):
    tests = module("def test_fast():\n    assert True\n")
    assert verdict("SCIKIT-LEARN-C243", make_bundle(files=[EXTENSION, tests]),
                   corpus).verdict == "fail"


def test_c243_finds_no_target_without_a_compiled_extension(corpus):
    row = verdict("SCIKIT-LEARN-C243", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C245 pytest runs with FutureWarnings as errors -----------------------------------


def test_c245_passes_when_the_flag_is_used(corpus):
    bundle = make_bundle(files=[SOURCE],
                         commands=["pytest -Werror::FutureWarning sklearn/svm"])
    assert verdict("SCIKIT-LEARN-C245", bundle, corpus).verdict == "pass"


def test_c245_fails_when_pytest_ran_without_it(corpus):
    bundle = make_bundle(files=[SOURCE], commands=["pytest sklearn/svm"])
    assert verdict("SCIKIT-LEARN-C245", bundle, corpus).verdict == "fail"


def test_c245_finds_no_target_when_the_tests_were_never_run(corpus):
    bundle = make_bundle(files=[SOURCE], commands=["git status"])
    row = verdict("SCIKIT-LEARN-C245", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

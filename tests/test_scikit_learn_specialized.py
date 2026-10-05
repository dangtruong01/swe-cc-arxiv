"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

Every no-target case here is Cython source that does not raise the question: a file with
no memoryview, no `cdef class`, no `nogil` declaration, no OpenMP call, no f-string. That
is what stops these rules firing on Cython in general and reporting a violation wherever
the construct they are about happens to be absent.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.scikit_learn.specialized  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


@pytest.fixture(scope="module")
def corpus():
    """scikit-learn's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("scikit-learn"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def pyx(text, path="sklearn/metrics/_pairwise_fast.pyx"):
    lines = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text)


def workflow(*lines, path=".github/workflows/tests.yml"):
    return make_file(path, [(n, t) for n, t in enumerate(lines, 1)])


# --- C210 memoryviews are not sliced --------------------------------------------------


def test_c210_passes_when_the_memoryview_is_only_indexed(corpus):
    text = ("cdef void _sum(double[::1] values) noexcept nogil:\n"
            "    cdef int i\n"
            "    for i in range(values.shape[0]):\n"
            "        values[i] = 0.0\n")
    assert verdict("SCIKIT-LEARN-C210", make_bundle(files=[pyx(text)]),
                   corpus).verdict == "pass"


def test_c210_fails_on_a_memoryview_slice(corpus):
    text = ("cdef void _sum(double[::1] values) noexcept nogil:\n"
            "    head = values[0:4]\n")
    assert verdict("SCIKIT-LEARN-C210", make_bundle(files=[pyx(text)]),
                   corpus).verdict == "fail"


def test_c210_finds_no_target_without_a_memoryview(corpus):
    text = "cdef double _square(double x) noexcept nogil:\n    return x * x\n"
    row = verdict("SCIKIT-LEARN-C210", make_bundle(files=[pyx(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C211 final Cython classes carry @final -------------------------------------------


def test_c211_passes_on_a_final_decorated_class(corpus):
    text = "@final\ncdef class DistanceMetric:\n    cdef double dist(self):\n        return 0.0\n"
    assert verdict("SCIKIT-LEARN-C211", make_bundle(files=[pyx(text)]),
                   corpus).verdict == "pass"


def test_c211_fails_when_an_unsubclassed_class_is_not_final(corpus):
    text = "cdef class DistanceMetric:\n    cdef double dist(self):\n        return 0.0\n"
    assert verdict("SCIKIT-LEARN-C211", make_bundle(files=[pyx(text)]),
                   corpus).verdict == "fail"


def test_c211_leaves_a_subclassed_base_out_of_the_selection(corpus):
    """A base class is not final, so the rule does not ask it for the decorator."""
    text = "cdef class Base:\n    pass\n\n@final\ncdef class Euclidean(Base):\n    pass\n"
    row = verdict("SCIKIT-LEARN-C211", make_bundle(files=[pyx(text)]), corpus)
    assert row.n_targets == 1 and row.verdict == "pass"


def test_c211_finds_no_target_without_a_cdef_class(corpus):
    text = "cdef double _square(double x) noexcept nogil:\n    return x * x\n"
    row = verdict("SCIKIT-LEARN-C211", make_bundle(files=[pyx(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C214 the GIL is released explicitly ----------------------------------------------


def test_c214_passes_on_an_explicit_with_nogil_block(corpus):
    text = ("cdef double _work(double x) noexcept nogil:\n    return x\n\n"
            "def run(double x):\n    with nogil:\n        _work(x)\n")
    assert verdict("SCIKIT-LEARN-C214", make_bundle(files=[pyx(text)]),
                   corpus).verdict == "pass"


def test_c214_fails_when_nogil_is_only_declared(corpus):
    text = "cdef double _work(double x) noexcept nogil:\n    return x\n"
    assert verdict("SCIKIT-LEARN-C214", make_bundle(files=[pyx(text)]),
                   corpus).verdict == "fail"


def test_c214_finds_no_target_without_a_nogil_declaration(corpus):
    text = "cdef double _square(double x):\n    return x * x\n"
    row = verdict("SCIKIT-LEARN-C214", make_bundle(files=[pyx(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C216 direct OpenMP calls are protected -------------------------------------------


def test_c216_passes_when_the_helpers_module_supplies_the_routine(corpus):
    text = ("from sklearn.utils._openmp_helpers cimport omp_get_max_threads\n\n"
            "def threads():\n    return omp_get_max_threads()\n")
    assert verdict("SCIKIT-LEARN-C216", make_bundle(files=[pyx(text)]),
                   corpus).verdict == "pass"


def test_c216_fails_on_an_unguarded_call(corpus):
    text = "def threads():\n    return omp_get_max_threads()\n"
    assert verdict("SCIKIT-LEARN-C216", make_bundle(files=[pyx(text)]),
                   corpus).verdict == "fail"


def test_c216_finds_no_target_without_an_openmp_call(corpus):
    text = "def threads():\n    return 1\n"
    row = verdict("SCIKIT-LEARN-C216", make_bundle(files=[pyx(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C217 OpenMP routines are cimported from the helpers ------------------------------


def test_c217_passes_on_the_helpers_module(corpus):
    text = "from sklearn.utils._openmp_helpers cimport omp_get_max_threads\n"
    assert verdict("SCIKIT-LEARN-C217", make_bundle(files=[pyx(text)]),
                   corpus).verdict == "pass"


def test_c217_fails_on_a_direct_library_cimport(corpus):
    text = "from openmp cimport omp_get_max_threads\n"
    assert verdict("SCIKIT-LEARN-C217", make_bundle(files=[pyx(text)]),
                   corpus).verdict == "fail"


def test_c217_finds_no_target_for_an_unrelated_cimport(corpus):
    text = "from libc.math cimport fabs\n"
    row = verdict("SCIKIT-LEARN-C217", make_bundle(files=[pyx(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C218 Cython code declares explicit types -----------------------------------------


def test_c218_passes_on_typed_parameters(corpus):
    text = "cdef double _dot(double[::1] a, double[::1] b) noexcept nogil:\n    return 0.0\n"
    assert verdict("SCIKIT-LEARN-C218", make_bundle(files=[pyx(text)]),
                   corpus).verdict == "pass"


def test_c218_fails_on_an_untyped_parameter(corpus):
    text = "def _dot(a, b):\n    return 0.0\n"
    assert verdict("SCIKIT-LEARN-C218", make_bundle(files=[pyx(text)]),
                   corpus).verdict == "fail"


def test_c218_finds_no_target_when_nothing_takes_a_parameter(corpus):
    text = "cdef double _one() noexcept nogil:\n    return 1.0\n"
    row = verdict("SCIKIT-LEARN-C218", make_bundle(files=[pyx(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C220 no {var=} f-strings in Cython -----------------------------------------------


def test_c220_passes_on_an_ordinary_fstring(corpus):
    text = 'def show(x):\n    print(f"value {x}")\n'
    assert verdict("SCIKIT-LEARN-C220", make_bundle(files=[pyx(text)]),
                   corpus).verdict == "pass"


def test_c220_fails_on_the_self_documenting_form(corpus):
    text = 'def show(x):\n    print(f"{x=}")\n'
    assert verdict("SCIKIT-LEARN-C220", make_bundle(files=[pyx(text)]),
                   corpus).verdict == "fail"


def test_c220_finds_no_target_without_an_fstring(corpus):
    text = 'def show(x):\n    print("value")\n'
    row = verdict("SCIKIT-LEARN-C220", make_bundle(files=[pyx(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C235 the PR CI does not set the global seed --------------------------------------


def test_c235_passes_when_the_workflow_sets_nothing(corpus):
    bundle = make_bundle(files=[workflow("  - name: run tests", "    run: pytest")])
    assert verdict("SCIKIT-LEARN-C235", bundle, corpus).verdict == "pass"


def test_c235_fails_when_the_workflow_sets_the_seed(corpus):
    bundle = make_bundle(files=[workflow('    SKLEARN_TESTS_GLOBAL_RANDOM_SEED: "all"')])
    assert verdict("SCIKIT-LEARN-C235", bundle, corpus).verdict == "fail"


def test_c235_finds_no_target_when_no_ci_file_changed(corpus):
    bundle = make_bundle(files=[make_file("sklearn/svm/_base.py", [(1, "x = 1")])])
    row = verdict("SCIKIT-LEARN-C235", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

C241's no-target case is a contribution that adds no compiled extension at all -- the
recipe applies to code being moved into one, and a pure-Python change never invokes it.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.scikit_learn.code_quality  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
DOC = make_file("doc/modules/svm.rst", [(3, "Support vector machines")])


@pytest.fixture(scope="module")
def corpus():
    """scikit-learn's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("scikit-learn"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def source(text, path="sklearn/svm/_base.py"):
    lines = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text)


def extension(text, path="sklearn/svm/_liblinear.pyx"):
    lines = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text, is_new=True)


# --- C180 contributed Python follows PEP8 ---------------------------------------------


def test_c180_passes_on_ordinary_lines(corpus):
    bundle = make_bundle(files=[source("def fit(self, X, y):\n    return self\n")])
    assert verdict("SCIKIT-LEARN-C180", bundle, corpus).verdict == "pass"


def test_c180_fails_on_a_line_over_the_limit(corpus):
    bundle = make_bundle(files=[source("x = " + "1 + " * 40 + "1\n")])
    assert verdict("SCIKIT-LEARN-C180", bundle, corpus).verdict == "fail"


def test_c180_fails_on_a_tab_indent(corpus):
    bundle = make_bundle(files=[source("def fit(self):\n\treturn self\n")])
    assert verdict("SCIKIT-LEARN-C180", bundle, corpus).verdict == "fail"


def test_c180_finds_no_target_when_no_python_was_written(corpus):
    row = verdict("SCIKIT-LEARN-C180", make_bundle(files=[DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C241 the bottleneck is isolated in a module-level function -----------------------


def test_c241_passes_when_the_extension_defines_a_module_level_function(corpus):
    text = ("cdef double _fast_inner(double[::1] x, double[::1] y) noexcept nogil:\n"
            "    return 0.0\n")
    assert verdict("SCIKIT-LEARN-C241", make_bundle(files=[extension(text)]),
                   corpus).verdict == "pass"


def test_c241_fails_when_everything_sits_inside_a_class(corpus):
    text = ("cdef class Solver:\n"
            "    cdef double step(self):\n"
            "        return 1.0\n")
    assert verdict("SCIKIT-LEARN-C241", make_bundle(files=[extension(text)]),
                   corpus).verdict == "fail"


def test_c241_finds_no_target_for_a_pure_python_change(corpus):
    bundle = make_bundle(files=[source("def fit(self):\n    return self\n")])
    row = verdict("SCIKIT-LEARN-C241", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

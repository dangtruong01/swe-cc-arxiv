"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

**C058 and C135 have no satisfying case.** Both grade one-sidedly: their pre-conditions
select the construct the guide replaces, so every target is a violation and a compliant test
finds no target at all. That is the correct shape for a rule whose satisfying state is the
*absence* of something, and it is why the no-target case carries the weight here.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pydata.tests  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("xarray/core/dataset.py", [(1, "x = 1")])
DOC = make_file("doc/whats-new.rst", [(4, "- prose")])
TESTS = "xarray/tests/test_merge.py"


def module(text: str, path: str = TESTS, new: bool = True):
    lines = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text, is_new=new)


@pytest.fixture(scope="module")
def corpus():
    """pydata's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pydata"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C049 new tests live in the tests subdirectory -------------------------------------


TEST_BODY = "def test_merge():\n    assert True\n"


def test_c049_passes_for_a_test_under_xarray_tests(corpus):
    assert verdict("PYDATA-C049", make_bundle(files=[module(TEST_BODY)]),
                   corpus).verdict == "pass"


def test_c049_fails_for_a_test_elsewhere(corpus):
    bundle = make_bundle(files=[module(TEST_BODY, "xarray/core/test_merge.py")])
    assert verdict("PYDATA-C049", bundle, corpus).verdict == "fail"


def test_c049_finds_no_target_when_no_test_was_added(corpus):
    row = verdict("PYDATA-C049", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C060 test module naming ----------------------------------------------------------


def test_c060_passes_on_test_feature_py(corpus):
    assert verdict("PYDATA-C060", make_bundle(files=[module(TEST_BODY)]),
                   corpus).verdict == "pass"


def test_c060_fails_on_another_name(corpus):
    bundle = make_bundle(files=[module(TEST_BODY, "xarray/tests/merge_tests.py")])
    assert verdict("PYDATA-C060", bundle, corpus).verdict == "fail"


def test_c060_finds_no_target_when_no_module_was_created(corpus):
    row = verdict("PYDATA-C060", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C052 functions rather than classes -----------------------------------------------


def test_c052_passes_on_a_module_level_test(corpus):
    assert verdict("PYDATA-C052", make_bundle(files=[module(TEST_BODY)]),
                   corpus).verdict == "pass"


def test_c052_fails_on_a_test_class_method(corpus):
    body = "class TestMerge:\n    def test_merge(self):\n        assert True\n"
    assert verdict("PYDATA-C052", make_bundle(files=[module(body)]),
                   corpus).verdict == "fail"


def test_c052_finds_no_target_without_a_new_test(corpus):
    row = verdict("PYDATA-C052", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C053 naming and arguments --------------------------------------------------------


def test_c053_passes_on_a_parametrised_test(corpus):
    body = ("import pytest\n\n\n"
            "@pytest.mark.parametrize('dim', ['x', 'y'])\n"
            "def test_merge(dim):\n    assert dim\n")
    assert verdict("PYDATA-C053", make_bundle(files=[module(body)]),
                   corpus).verdict == "pass"


def test_c053_fails_on_an_unaccounted_argument(corpus):
    body = "def test_merge(dataset):\n    assert dataset\n"
    assert verdict("PYDATA-C053", make_bundle(files=[module(body)]),
                   corpus).verdict == "fail"


def test_c053_finds_no_target_without_a_new_test(corpus):
    row = verdict("PYDATA-C053", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C048 written with pytest ---------------------------------------------------------


def test_c048_passes_on_a_plain_pytest_module(corpus):
    assert verdict("PYDATA-C048", make_bundle(files=[module(TEST_BODY)]),
                   corpus).verdict == "pass"


def test_c048_fails_on_a_unittest_testcase(corpus):
    body = ("import unittest\n\n\n"
            "class TestMerge(unittest.TestCase):\n"
            "    def test_merge(self):\n        assert True\n")
    assert verdict("PYDATA-C048", make_bundle(files=[module(body)]),
                   corpus).verdict == "fail"


def test_c048_finds_no_target_without_a_test_module(corpus):
    row = verdict("PYDATA-C048", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C051 xarray objects compared with xarray.testing ---------------------------------


def test_c051_passes_when_assert_identical_is_used(corpus):
    body = ("from xarray.testing import assert_identical\n\n\n"
            "def test_merge():\n"
            "    actual = Dataset({'a': 1})\n"
            "    assert_identical(actual, actual)\n")
    assert verdict("PYDATA-C051", make_bundle(files=[module(body)]),
                   corpus).verdict == "pass"


def test_c051_fails_on_a_bare_equality(corpus):
    body = ("def test_merge():\n"
            "    actual = Dataset({'a': 1})\n"
            "    assert actual == actual\n")
    assert verdict("PYDATA-C051", make_bundle(files=[module(body)]),
                   corpus).verdict == "fail"


def test_c051_finds_no_target_when_no_xarray_object_is_built(corpus):
    row = verdict("PYDATA-C051", make_bundle(files=[module(TEST_BODY)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C058 scalars asserted bare -------------------------------------------------------


def test_c058_fails_when_a_literal_goes_through_a_helper(corpus):
    body = ("def test_merge():\n"
            "    assert_equal(len(result), 3)\n")
    assert verdict("PYDATA-C058", make_bundle(files=[module(body)]),
                   corpus).verdict == "fail"


def test_c058_finds_no_target_on_a_bare_assert(corpus):
    """The compliant form is the absence of the construct, so it finds no target."""
    body = "def test_merge():\n    assert len(result) == 3\n"
    row = verdict("PYDATA-C058", make_bundle(files=[module(body)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c058_finds_no_target_without_a_test(corpus):
    row = verdict("PYDATA-C058", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C055 individual parameters marked with pytest.param ------------------------------


def test_c055_passes_on_pytest_param_marks(corpus):
    body = ("import pytest\n\n\n"
            "@pytest.mark.parametrize('dim', [pytest.param('x', marks=pytest.mark.slow)])\n"
            "def test_merge(dim):\n    assert dim\n")
    assert verdict("PYDATA-C055", make_bundle(files=[module(body)]),
                   corpus).verdict == "pass"


def test_c055_fails_when_a_mark_is_applied_to_the_value(corpus):
    body = ("import pytest\n\n\n"
            "@pytest.mark.parametrize('dim', [pytest.mark.slow('x')])\n"
            "def test_merge(dim):\n    assert dim\n")
    assert verdict("PYDATA-C055", make_bundle(files=[module(body)]),
                   corpus).verdict == "fail"


def test_c055_finds_no_target_on_an_unmarked_parametrize(corpus):
    body = ("import pytest\n\n\n"
            "@pytest.mark.parametrize('dim', ['x', 'y'])\n"
            "def test_merge(dim):\n    assert dim\n")
    row = verdict("PYDATA-C055", make_bundle(files=[module(body)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C134 no skipif on a parametrize param --------------------------------------------


def test_c134_passes_on_a_parametrize_without_skipif(corpus):
    body = ("import pytest\n\n\n"
            "@pytest.mark.parametrize('dim', [pytest.param('x', marks=pytest.mark.slow)])\n"
            "def test_merge(dim):\n    assert dim\n")
    assert verdict("PYDATA-C134", make_bundle(files=[module(body)]),
                   corpus).verdict == "pass"


def test_c134_fails_when_skipif_is_attached_to_a_param(corpus):
    body = ("import pytest\n\n\n"
            "@pytest.mark.parametrize('dim', "
            "[pytest.param('x', marks=pytest.mark.skipif(True, reason='no'))])\n"
            "def test_merge(dim):\n    assert dim\n")
    assert verdict("PYDATA-C134", make_bundle(files=[module(body)]),
                   corpus).verdict == "fail"


def test_c134_finds_no_target_without_a_parametrize(corpus):
    row = verdict("PYDATA-C134", make_bundle(files=[module(TEST_BODY)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C132 optional dependencies gated with @requires_* --------------------------------


GUARDED = ("try:\n    import dask\nexcept ImportError:\n    dask = None\n\n\n")


def test_c132_passes_on_a_requires_decorated_test(corpus):
    body = GUARDED + "@requires_dask\ndef test_merge():\n    assert True\n"
    assert verdict("PYDATA-C132", make_bundle(files=[module(body)]),
                   corpus).verdict == "pass"


def test_c132_fails_on_an_ungated_test_in_a_guarded_module(corpus):
    body = GUARDED + "def test_merge():\n    assert True\n"
    assert verdict("PYDATA-C132", make_bundle(files=[module(body)]),
                   corpus).verdict == "fail"


def test_c132_finds_no_target_when_the_module_guards_nothing(corpus):
    row = verdict("PYDATA-C132", make_bundle(files=[module(TEST_BODY)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C133 dask helpers from xarray.tests ----------------------------------------------


def test_c133_passes_when_dask_comes_through_xarray_tests(corpus):
    body = "from xarray.tests import dask_array_type\n\n\ndef test_merge():\n    assert True\n"
    bundle = make_bundle(files=[module(body)])
    assert verdict("PYDATA-C133", bundle, corpus).verdict == "not_applicable"


def test_c133_fails_on_a_direct_dask_array_import(corpus):
    body = "import dask.array as da\n\n\ndef test_merge():\n    assert da\n"
    assert verdict("PYDATA-C133", make_bundle(files=[module(body)]),
                   corpus).verdict == "fail"


def test_c133_passes_when_dask_is_imported_without_reaching_for_the_array_module(corpus):
    body = "import dask\n\n\ndef test_merge():\n    assert dask\n"
    assert verdict("PYDATA-C133", make_bundle(files=[module(body)]),
                   corpus).verdict == "pass"


def test_c133_finds_no_target_when_dask_is_not_imported(corpus):
    row = verdict("PYDATA-C133", make_bundle(files=[module(TEST_BODY)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C135 in-function imports use importorskip ----------------------------------------


def test_c135_fails_on_a_plain_import_inside_a_test(corpus):
    body = "def test_merge():\n    import dask\n    assert dask\n"
    assert verdict("PYDATA-C135", make_bundle(files=[module(body)]),
                   corpus).verdict == "fail"


def test_c135_finds_no_target_when_importorskip_is_used(corpus):
    """The compliant form is a call, not an import statement, so nothing is selected."""
    body = ("import pytest\n\n\n"
            "def test_merge():\n    dask = pytest.importorskip('dask')\n    assert dask\n")
    row = verdict("PYDATA-C135", make_bundle(files=[module(body)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c135_finds_no_target_without_a_test(corpus):
    row = verdict("PYDATA-C135", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C112 tests added for the change --------------------------------------------------


def test_c112_passes_when_a_test_changed_alongside_the_code(corpus):
    assert verdict("PYDATA-C112", make_bundle(files=[SOURCE, module(TEST_BODY)]),
                   corpus).verdict == "pass"


def test_c112_fails_when_source_changed_alone(corpus):
    assert verdict("PYDATA-C112", make_bundle(files=[SOURCE]), corpus).verdict == "fail"


def test_c112_finds_no_target_for_a_documentation_only_change(corpus):
    row = verdict("PYDATA-C112", make_bundle(files=[DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

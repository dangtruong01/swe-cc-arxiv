"""Three cases per rule (spec §9): satisfied, violated, and an input where the
pre-condition finds nothing.

**C067 and C084 have no satisfying case reachable from a bundle**, and §9's alternative
triple is used for both: violated, withheld, and no target. Each declares a Phase 5 source
that nothing collects yet -- the whole suite's result, and the added tests run against the
reverted source -- so the only verdict either can reach from the patch is its conclusive
failure. The withheld case asserts the row is ``not_applicable`` with a non-``ok`` status,
which is what stops a withhold being read as a silent pass.

The no-target cases are the ones worth reading twice. C069's pins that a test file the
agent merely edited is out of scope; C070's, C071's and C076's pin that the shape-based
pre-conditions do not fire on a support module.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pallets.tests  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


def py_file(path, source, *, is_new=False, owned=None):
    """A changed Python file whose post-patch text is `source`.

    By default every line is the agent's, which is what a newly written test file looks
    like; `owned` narrows that where a rule's ownership is the point of the test.
    """
    lines = source.split("\n")
    numbers = range(1, len(lines) + 1) if owned is None else owned
    return make_file(path, [(n, lines[n - 1]) for n in numbers],
                     head_text=source, is_new=is_new)


SOURCE = make_file("src/flask/app.py", [(10, "    return None")])
DOC = make_file("docs/quickstart.rst", [(9, "New prose.")])
BROKEN = make_file("src/flask/app.py", [(1, "def create_app(:")],
                   head_text="def create_app(:\n    return None\n")

A_TEST = (
    "from flask import Flask\n"
    "\n"
    "\n"
    "def test_app_is_created():\n"
    "    app = Flask(__name__)\n"
    "    assert app is not None\n"
)
A_HELPER_ONLY = (
    "import pytest\n"
    "\n"
    "\n"
    "@pytest.fixture\n"
    "def app():\n"
    "    assert True\n"
    "    return object()\n"
)


@pytest.fixture(scope="module")
def corpus():
    """pallets' corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pallets"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C066 add tests that demonstrate the change ------------------------------------------


def test_c066_passes_when_a_test_changes_alongside_the_code(corpus):
    bundle = make_bundle(files=[SOURCE, py_file("tests/test_app.py", A_TEST)])
    assert verdict("PALLETS-C066", bundle, corpus).verdict == "pass"


def test_c066_fails_when_the_code_changes_alone(corpus):
    row = verdict("PALLETS-C066", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "fail" and "nothing under tests/" in row.notes


def test_c066_finds_no_target_for_a_documentation_only_contribution(corpus):
    row = verdict("PALLETS-C066", make_bundle(files=[DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C067 the whole suite passes before submitting ----------------------------------------


def test_c067_fails_when_a_submitted_file_will_not_parse(corpus):
    row = verdict("PALLETS-C067", make_bundle(files=[BROKEN]), corpus)
    assert row.verdict == "fail" and "not valid Python" in row.notes


def test_c067_withholds_when_the_suite_was_never_run(corpus):
    bundle = make_bundle(files=[py_file("tests/test_app.py", A_TEST)])
    row = verdict("PALLETS-C067", bundle, corpus)
    assert row.verdict == "not_applicable" and row.status == "tool_missing"


def test_c067_finds_no_target_for_a_documentation_only_contribution(corpus):
    row = verdict("PALLETS-C067", make_bundle(files=[DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C069 new test files live under tests/ -------------------------------------------------


def test_c069_passes_on_a_new_test_file_under_tests(corpus):
    bundle = make_bundle(files=[py_file("tests/test_routing.py", A_TEST, is_new=True)])
    assert verdict("PALLETS-C069", bundle, corpus).verdict == "pass"


def test_c069_fails_on_a_new_test_file_outside_tests(corpus):
    bundle = make_bundle(files=[py_file("src/flask/test_routing.py", A_TEST, is_new=True)])
    row = verdict("PALLETS-C069", bundle, corpus)
    assert row.verdict == "fail" and "outside tests/" in row.notes


def test_c069_finds_no_target_for_a_test_file_the_agent_only_edited(corpus):
    """Ownership is `created`: a misplaced test that was already there is not the
    agent's doing (spec §4.3)."""
    bundle = make_bundle(files=[py_file("src/flask/test_routing.py", A_TEST)])
    row = verdict("PALLETS-C069", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C070 test files named test_{topic}.py -------------------------------------------------


def test_c070_passes_on_a_file_named_by_topic(corpus):
    bundle = make_bundle(files=[py_file("tests/test_app.py", A_TEST)])
    assert verdict("PALLETS-C070", bundle, corpus).verdict == "pass"


def test_c070_fails_on_a_test_file_named_another_way(corpus):
    bundle = make_bundle(files=[py_file("tests/app_tests.py", A_TEST)])
    row = verdict("PALLETS-C070", bundle, corpus)
    assert row.verdict == "fail" and "app_tests.py" in row.notes


def test_c070_finds_no_target_for_a_support_module(corpus):
    """`conftest.py` is excluded by name and a module with no asserting function is not
    selected at all, so neither is reported for its filename."""
    bundle = make_bundle(files=[py_file("tests/conftest.py", A_HELPER_ONLY)])
    row = verdict("PALLETS-C070", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C071 test functions named test_{specific} ---------------------------------------------


def test_c071_passes_on_a_test_named_by_what_it_checks(corpus):
    bundle = make_bundle(files=[py_file("tests/test_app.py", A_TEST)])
    assert verdict("PALLETS-C071", bundle, corpus).verdict == "pass"


def test_c071_fails_on_an_asserting_function_named_another_way(corpus):
    source = A_TEST.replace("def test_app_is_created", "def check_app_is_created")
    bundle = make_bundle(files=[py_file("tests/test_app.py", source)])
    row = verdict("PALLETS-C071", bundle, corpus)
    assert row.verdict == "fail" and "check_app_is_created" in row.notes


def test_c071_finds_no_target_when_the_module_defines_only_a_fixture(corpus):
    bundle = make_bundle(files=[py_file("tests/test_app.py", A_HELPER_ONLY)])
    row = verdict("PALLETS-C071", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C072 test function names are unique ---------------------------------------------------


def test_c072_passes_when_every_test_name_is_distinct(corpus):
    source = A_TEST + "\n\ndef test_app_has_a_name():\n    assert True\n"
    bundle = make_bundle(files=[py_file("tests/test_app.py", source)])
    assert verdict("PALLETS-C072", bundle, corpus).verdict == "pass"


def test_c072_fails_when_the_agent_shadows_an_existing_test(corpus):
    source = A_TEST + "\n\ndef test_app_is_created():\n    assert True\n"
    bundle = make_bundle(files=[py_file("tests/test_app.py", source)])
    row = verdict("PALLETS-C072", bundle, corpus)
    assert row.verdict == "fail" and "shadowed" in row.notes


def test_c072_finds_no_target_in_a_module_defining_no_collected_test(corpus):
    bundle = make_bundle(files=[py_file("tests/helpers.py", A_HELPER_ONLY)])
    row = verdict("PALLETS-C072", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C074 a bug fix extends an existing test file -------------------------------------------


def test_c074_passes_when_the_tests_extend_an_existing_file(corpus):
    bundle = make_bundle(files=[SOURCE, py_file("tests/test_app.py", A_TEST)])
    assert verdict("PALLETS-C074", bundle, corpus).verdict == "pass"


def test_c074_fails_when_the_fix_adds_a_new_test_file(corpus):
    bundle = make_bundle(files=[SOURCE,
                                py_file("tests/test_issue.py", A_TEST, is_new=True)])
    row = verdict("PALLETS-C074", bundle, corpus)
    assert row.verdict == "fail" and "tests/test_issue.py" in row.notes


def test_c074_finds_no_target_when_the_contribution_adds_no_test(corpus):
    row = verdict("PALLETS-C074", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C076 tests use plain assert statements --------------------------------------------------


def test_c076_passes_on_a_test_using_plain_assert(corpus):
    bundle = make_bundle(files=[py_file("tests/test_app.py", A_TEST)])
    assert verdict("PALLETS-C076", bundle, corpus).verdict == "pass"


def test_c076_fails_on_a_test_using_the_unittest_assertions(corpus):
    source = (
        "import unittest\n"
        "\n"
        "\n"
        "class AppTests(unittest.TestCase):\n"
        "    def test_app_is_created(self):\n"
        "        self.assertEqual(1, 1)\n"
    )
    bundle = make_bundle(files=[py_file("tests/test_app.py", source)])
    row = verdict("PALLETS-C076", bundle, corpus)
    assert row.verdict == "fail" and "assertEqual" in row.notes


def test_c076_finds_no_target_when_the_module_collects_no_test(corpus):
    bundle = make_bundle(files=[py_file("tests/test_app.py", A_HELPER_ONLY)])
    row = verdict("PALLETS-C076", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C077 multiple cases are parametrized ------------------------------------------------------


def test_c077_passes_on_a_parametrized_test(corpus):
    source = (
        "import pytest\n"
        "\n"
        "\n"
        '@pytest.mark.parametrize("path", ["/a", "/b"])\n'
        "def test_paths_start_with_a_slash(path):\n"
        '    assert path.startswith("/")\n'
    )
    bundle = make_bundle(files=[py_file("tests/test_routing.py", source)])
    assert verdict("PALLETS-C077", bundle, corpus).verdict == "pass"


def test_c077_fails_on_a_hand_rolled_loop_over_the_cases(corpus):
    source = (
        "def test_paths_start_with_a_slash():\n"
        '    for path in ["/a", "/b"]:\n'
        '        assert path.startswith("/")\n'
    )
    bundle = make_bundle(files=[py_file("tests/test_routing.py", source)])
    row = verdict("PALLETS-C077", bundle, corpus)
    assert row.verdict == "fail" and "parametrize" in row.notes


def test_c077_finds_no_target_for_a_single_case_test(corpus):
    bundle = make_bundle(files=[py_file("tests/test_app.py", A_TEST)])
    row = verdict("PALLETS-C077", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C084 the added tests fail when the change is reverted ---------------------------------------


def test_c084_fails_when_tests_are_added_with_no_change_to_revert(corpus):
    bundle = make_bundle(files=[DOC, py_file("tests/test_app.py", A_TEST)])
    row = verdict("PALLETS-C084", bundle, corpus)
    assert row.verdict == "fail" and "cannot make" in row.notes


def test_c084_withholds_when_the_tests_were_never_run_against_the_base(corpus):
    bundle = make_bundle(files=[SOURCE, py_file("tests/test_app.py", A_TEST)])
    row = verdict("PALLETS-C084", bundle, corpus)
    assert row.verdict == "not_applicable" and row.status == "tool_missing"


def test_c084_finds_no_target_when_no_test_was_added(corpus):
    row = verdict("PALLETS-C084", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

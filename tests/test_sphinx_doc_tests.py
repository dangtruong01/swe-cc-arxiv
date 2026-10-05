"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

C026 carries a fourth: withheld when the run has no functional result, because absence of a
harness report is not absence of a passing test.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.evaluation import EvalReport
from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.sphinx_doc.tests  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}

SOURCE = make_file("sphinx/util/inventory.py", [(1, "x = 1")])
TEST_FILE = make_file("tests/test_inventory.py", [(1, "def test_a():"), (2, "    pass")])


def new_module(path: str, text: str):
    lines = text.splitlines()
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text, is_new=True)


def cmds(*commands):
    return tuple(Command(index=i, command=c) for i, c in enumerate(commands))


def report(fail_to_pass=(), pass_to_pass_failures=()):
    return EvalReport(shape="instance", tests_status={
        "FAIL_TO_PASS": {"success": tuple(fail_to_pass), "failure": ()},
        "PASS_TO_PASS": {"success": ("tests/test_other.py::test_x",),
                         "failure": tuple(pass_to_pass_failures)},
    })


@pytest.fixture(scope="module")
def corpus():
    """sphinx-doc's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("sphinx-doc"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C004 tests accompany the code change ---------------------------------------------


def test_c004_passes_when_a_test_changed_alongside_the_code(corpus):
    bundle = make_bundle(files=[SOURCE, TEST_FILE])
    assert verdict("SPHINX-DOC-C004", bundle, corpus).verdict == "pass"


def test_c004_fails_when_source_changed_alone(corpus):
    assert verdict("SPHINX-DOC-C004", make_bundle(files=[SOURCE]), corpus).verdict == "fail"


def test_c004_finds_no_target_for_a_test_only_change(corpus):
    row = verdict("SPHINX-DOC-C004", make_bundle(files=[TEST_FILE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C024 the JavaScript suite is run with npm ----------------------------------------


JS = make_file("sphinx/themes/basic/static/searchtools.js", [(4, "var x = 1;")])


def test_c024_passes_when_npm_test_ran(corpus):
    bundle = make_bundle(files=[JS], commands=cmds("npm install", "npm run test"))
    assert verdict("SPHINX-DOC-C024", bundle, corpus).verdict == "pass"


def test_c024_fails_when_javascript_changed_and_npm_never_ran(corpus):
    bundle = make_bundle(files=[JS], commands=cmds("python -m pytest"))
    assert verdict("SPHINX-DOC-C024", bundle, corpus).verdict == "fail"


def test_c024_finds_no_target_without_a_javascript_change(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("python -m pytest"))
    row = verdict("SPHINX-DOC-C024", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C025 new tests live under tests/ -------------------------------------------------


TEST_BODY = "def test_inventory():\n    assert True\n"


def test_c025_passes_for_a_new_test_under_tests(corpus):
    bundle = make_bundle(files=[new_module("tests/test_inventory.py", TEST_BODY)])
    assert verdict("SPHINX-DOC-C025", bundle, corpus).verdict == "pass"


def test_c025_fails_for_a_new_test_outside_tests(corpus):
    bundle = make_bundle(files=[new_module("sphinx/util/test_inventory.py", TEST_BODY)])
    assert verdict("SPHINX-DOC-C025", bundle, corpus).verdict == "fail"


def test_c025_finds_no_target_when_no_test_was_added(corpus):
    bundle = make_bundle(files=[new_module("sphinx/util/inventory.py", "x = 1\n")])
    row = verdict("SPHINX-DOC-C025", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C026 a test fails before and passes after ----------------------------------------


def test_c026_passes_when_a_test_changed_state(corpus):
    bundle = make_bundle(files=[SOURCE, TEST_FILE],
                         evaluation=report(fail_to_pass=("tests/test_inventory.py::test_a",)))
    assert verdict("SPHINX-DOC-C026", bundle, corpus).verdict == "pass"


def test_c026_fails_when_nothing_the_harness_ran_changed_state(corpus):
    bundle = make_bundle(files=[SOURCE, TEST_FILE], evaluation=report())
    assert verdict("SPHINX-DOC-C026", bundle, corpus).verdict == "fail"


def test_c026_withholds_when_the_run_has_no_functional_result(corpus):
    row = verdict("SPHINX-DOC-C026", make_bundle(files=[SOURCE, TEST_FILE]), corpus)
    assert row.verdict == "not_applicable" and row.status != "ok"


def test_c026_finds_no_target_without_both_source_and_tests(corpus):
    row = verdict("SPHINX-DOC-C026", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

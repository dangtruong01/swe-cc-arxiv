"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pytest_dev.language_style  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


def new_module(path: str, text: str):
    lines = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text, is_new=True)


@pytest.fixture(scope="module")
def corpus():
    """pytest-dev's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pytest-dev"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C016 PEP-8 naming ----------------------------------------------------------------


def test_c016_passes_on_snake_case_and_capwords(corpus):
    body = "def collect_items():\n    pass\n\n\nclass ItemCollector:\n    pass\n"
    assert verdict("PYTEST-DEV-C016", make_bundle(files=[new_module("src/_pytest/a.py", body)]),
                   corpus).verdict == "pass"


def test_c016_fails_on_a_camel_case_function(corpus):
    body = "def collectItems():\n    pass\n"
    assert verdict("PYTEST-DEV-C016", make_bundle(files=[new_module("src/_pytest/a.py", body)]),
                   corpus).verdict == "fail"


def test_c016_fails_on_a_lowercase_class(corpus):
    body = "class itemCollector:\n    pass\n"
    assert verdict("PYTEST-DEV-C016", make_bundle(files=[new_module("src/_pytest/a.py", body)]),
                   corpus).verdict == "fail"


def test_c016_finds_no_target_when_nothing_was_defined(corpus):
    row = verdict("PYTEST-DEV-C016",
                  make_bundle(files=[new_module("src/_pytest/a.py", "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C045 the Python 3.10 floor -------------------------------------------------------


def test_c045_passes_on_code_that_predates_the_floor(corpus):
    body = "import os\n\n\ndef collect():\n    return os.getcwd()\n"
    assert verdict("PYTEST-DEV-C045", make_bundle(files=[new_module("src/_pytest/a.py", body)]),
                   corpus).verdict == "pass"


def test_c045_fails_on_a_module_added_after_310(corpus):
    body = "import tomllib\n"
    assert verdict("PYTEST-DEV-C045", make_bundle(files=[new_module("src/_pytest/a.py", body)]),
                   corpus).verdict == "fail"


def test_c045_fails_on_except_star(corpus):
    body = "try:\n    pass\nexcept* ValueError:\n    pass\n"
    change = make_file("src/_pytest/a.py",
                       [(n, line) for n, line in enumerate(body.split("\n"), 1)])
    assert verdict("PYTEST-DEV-C045", make_bundle(files=[change]), corpus).verdict == "fail"


def test_c045_finds_no_target_when_no_line_was_written(corpus):
    change = make_file("src/_pytest/a.py", [], deletion_anchors=frozenset({4}))
    row = verdict("PYTEST-DEV-C045", make_bundle(files=[change]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

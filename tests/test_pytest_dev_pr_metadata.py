"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

C021 carries a fourth: a fragment whose *name* is malformed is C020's finding, and this
rule must not select it, or one defect would depress two rates.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pytest_dev.pr_metadata  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("src/_pytest/fixtures.py", [(1, "x = 1")])


def entry(name: str, *lines: str):
    return make_file(f"changelog/{name}",
                     [(n, text) for n, text in enumerate(lines, 1)], is_new=True)


@pytest.fixture(scope="module")
def corpus():
    """pytest-dev's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pytest-dev"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C020 changelog filename grammar --------------------------------------------------


def test_c020_passes_on_the_published_grammar(corpus):
    bundle = make_bundle(files=[entry("2574.bugfix.rst", "Fixed the thing.")])
    assert verdict("PYTEST-DEV-C020", bundle, corpus).verdict == "pass"


def test_c020_fails_when_the_issue_id_is_missing(corpus):
    bundle = make_bundle(files=[entry("bugfix.rst", "Fixed the thing.")])
    assert verdict("PYTEST-DEV-C020", bundle, corpus).verdict == "fail"


def test_c020_finds_no_target_without_a_new_fragment(corpus):
    row = verdict("PYTEST-DEV-C020", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C021 changelog type from the closed list -----------------------------------------


def test_c021_passes_on_a_published_type(corpus):
    bundle = make_bundle(files=[entry("2574.improvement.rst", "Made it better.")])
    assert verdict("PYTEST-DEV-C021", bundle, corpus).verdict == "pass"


def test_c021_fails_on_a_type_outside_the_list(corpus):
    bundle = make_bundle(files=[entry("2574.refactor.rst", "Moved things around.")])
    assert verdict("PYTEST-DEV-C021", bundle, corpus).verdict == "fail"


def test_c021_does_not_select_a_malformed_filename(corpus):
    """That is C020's finding. Selecting it here would report one defect twice."""
    row = verdict("PYTEST-DEV-C021", make_bundle(files=[entry("bugfix.rst", "x.")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c021_finds_no_target_without_a_new_fragment(corpus):
    row = verdict("PYTEST-DEV-C021", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C048 changelog tense -------------------------------------------------------------


def test_c048_passes_on_a_past_tense_entry(corpus):
    bundle = make_bundle(files=[entry("2574.bugfix.rst", "Fixed a crash in the parser.")])
    assert verdict("PYTEST-DEV-C048", bundle, corpus).verdict == "pass"


def test_c048_fails_on_a_future_tense_entry(corpus):
    bundle = make_bundle(files=[entry("2574.bugfix.rst", "This will fix the parser.")])
    assert verdict("PYTEST-DEV-C048", bundle, corpus).verdict == "fail"


def test_c048_finds_no_target_for_an_empty_fragment(corpus):
    row = verdict("PYTEST-DEV-C048", make_bundle(files=[entry("2574.bugfix.rst", "")]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C049 changelog punctuation -------------------------------------------------------


def test_c049_passes_when_the_entry_ends_with_a_period(corpus):
    bundle = make_bundle(files=[entry("2574.bugfix.rst", "Fixed a crash in the parser.")])
    assert verdict("PYTEST-DEV-C049", bundle, corpus).verdict == "pass"


def test_c049_fails_when_the_entry_has_no_terminator(corpus):
    bundle = make_bundle(files=[entry("2574.bugfix.rst", "Fixed a crash in the parser")])
    assert verdict("PYTEST-DEV-C049", bundle, corpus).verdict == "fail"


def test_c049_finds_no_target_when_the_fragment_is_only_a_directive(corpus):
    row = verdict("PYTEST-DEV-C049",
                  make_bundle(files=[entry("2574.bugfix.rst", ".. note::")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

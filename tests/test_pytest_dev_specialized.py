"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pytest_dev.specialized  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("src/_pytest/fixtures.py", [(1, "x = 1")])


def entry(name: str, *lines: str):
    return make_file(f"changelog/{name}",
                     [(n, t) for n, t in enumerate(lines, 1)], is_new=True)


@pytest.fixture(scope="module")
def corpus():
    """pytest-dev's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pytest-dev"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C039 deprecations name PytestRemovedInXWarning -----------------------------------


def test_c039_passes_when_the_class_is_named(corpus):
    change = make_file("src/_pytest/fixtures.py", [
        (10, "    .. deprecated:: 8.0"),
        (11, "    warnings.warn('gone', PytestRemovedIn9Warning, stacklevel=2)"),
    ])
    assert verdict("PYTEST-DEV-C039", make_bundle(files=[change]), corpus).verdict == "pass"


def test_c039_fails_when_a_deprecation_names_no_class(corpus):
    change = make_file("src/_pytest/fixtures.py", [(10, "    .. deprecated:: 8.0")])
    assert verdict("PYTEST-DEV-C039", make_bundle(files=[change]), corpus).verdict == "fail"


def test_c039_finds_no_target_without_a_deprecation(corpus):
    row = verdict("PYTEST-DEV-C039", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C042 breaking changes ship deprecation warnings ----------------------------------


BREAKING = entry("2574.breaking.rst", "Removed the old hook.")


def test_c042_passes_when_a_warning_ships_with_the_break(corpus):
    change = make_file("src/_pytest/fixtures.py", [
        (12, "    warnings.warn('use new_hook instead', PytestRemovedIn9Warning)")])
    assert verdict("PYTEST-DEV-C042", make_bundle(files=[change, BREAKING]),
                   corpus).verdict == "pass"


def test_c042_fails_when_the_break_ships_nothing(corpus):
    assert verdict("PYTEST-DEV-C042", make_bundle(files=[SOURCE, BREAKING]),
                   corpus).verdict == "fail"


def test_c042_finds_no_target_for_a_non_breaking_change(corpus):
    bundle = make_bundle(files=[SOURCE, entry("2574.bugfix.rst", "Fixed it.")])
    row = verdict("PYTEST-DEV-C042", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

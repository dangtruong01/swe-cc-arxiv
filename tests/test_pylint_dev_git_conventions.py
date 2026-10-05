"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

Both rules are prohibitions, so the third case is what proves the pre-condition selects the
permitted act rather than the forbidden one: a contribution that never touches `.gitignore`
must find no target for C098, and an empty contribution none for C099.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pylint_dev.git_conventions  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("pylint/checkers/typecheck.py", [(1, "x = 1")], head_text="x = 1")


@pytest.fixture(scope="module")
def corpus():
    """pylint-dev's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pylint-dev"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def gitignore(*lines):
    text = "\n".join(lines)
    return make_file(".gitignore", [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text)


def new_file(path, text="x = 1"):
    return make_file(path, [(1, text)], head_text=text, is_new=True)


# --- C098 venv is not added to .gitignore ---------------------------------------------


def test_c098_passes_when_the_ignore_entries_are_unrelated(corpus):
    bundle = make_bundle(files=[SOURCE, gitignore("*.pyc", "build/")])
    assert verdict("PYLINT-DEV-C098", bundle, corpus).verdict == "pass"


def test_c098_fails_when_venv_is_added_to_the_ignore_file(corpus):
    bundle = make_bundle(files=[SOURCE, gitignore("*.pyc", "venv/")])
    row = verdict("PYLINT-DEV-C098", bundle, corpus)
    assert row.verdict == "fail" and "venv/" in row.notes


def test_c098_finds_no_target_when_the_ignore_file_is_untouched(corpus):
    row = verdict("PYLINT-DEV-C098", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C099 no virtual environment is committed -----------------------------------------


def test_c099_passes_when_the_contribution_is_source_only(corpus):
    assert verdict("PYLINT-DEV-C099", make_bundle(files=[SOURCE]),
                   corpus).verdict == "pass"


def test_c099_fails_when_an_environment_directory_is_committed(corpus):
    bundle = make_bundle(files=[SOURCE,
                                new_file(".venv/lib/python3.12/site-packages/six.py")])
    row = verdict("PYLINT-DEV-C099", bundle, corpus)
    assert row.verdict == "fail" and "virtual environment" in row.notes


def test_c099_finds_no_target_for_an_empty_contribution(corpus):
    row = verdict("PYLINT-DEV-C099", make_bundle(files=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

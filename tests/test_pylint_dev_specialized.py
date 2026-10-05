"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

The no-target case here does double duty. It pins that a functional test added *without*
an extension change is not this rule's business, and it is the other half of the exclusion
C053 makes: `tests/test_pylint_dev_tests.py` asserts that an extension test finds no target
under C053, and this module asserts that a non-extension test finds none under C054, so
neither rule can quietly claim the other's file (spec §7.5).
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pylint_dev.specialized  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
EXTENSION = make_file("pylint/extensions/docparams.py", [(1, "x = 1")], head_text="x = 1")


@pytest.fixture(scope="module")
def corpus():
    """pylint-dev's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pylint-dev"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def functional(path, text="a = 1  # [missing-param-doc]"):
    return make_file(path, [(1, text)], head_text=text, is_new=True)


# --- C054 an extension's functional test lives under its own directory ----------------


def test_c054_passes_when_the_test_is_under_the_extension_directory(corpus):
    bundle = make_bundle(files=[
        EXTENSION, functional("tests/functional/ext/docparams/missing_param_doc.py")])
    assert verdict("PYLINT-DEV-C054", bundle, corpus).verdict == "pass"


def test_c054_fails_when_the_test_is_filed_by_first_letter_instead(corpus):
    bundle = make_bundle(files=[
        EXTENSION, functional("tests/functional/m/missing_param_doc.py")])
    row = verdict("PYLINT-DEV-C054", bundle, corpus)
    assert row.verdict == "fail" and "extension" in row.notes


def test_c054_finds_no_target_when_no_extension_is_touched(corpus):
    bundle = make_bundle(files=[functional("tests/functional/m/missing_param_doc.py")])
    row = verdict("PYLINT-DEV-C054", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

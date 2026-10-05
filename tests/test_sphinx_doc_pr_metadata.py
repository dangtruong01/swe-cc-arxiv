"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

The third case is the interesting one here: a documentation-only contribution is what the
guide's own parenthesis exempts, so the rule must not fire on it at all.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.sphinx_doc.pr_metadata  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}

SOURCE = make_file("sphinx/util/inventory.py", [(1, "x = 1")])
DOC_ONLY = make_file("doc/usage/configuration.rst", [(1, "Some prose.")])


@pytest.fixture(scope="module")
def corpus():
    """sphinx-doc's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("sphinx-doc"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C005 changelog entry -------------------------------------------------------------


def test_c005_passes_when_changes_gains_a_bullet(corpus):
    changelog = make_file("CHANGES.rst", [(12, "* Fixed the inventory parser.")])
    bundle = make_bundle(files=[SOURCE, changelog])
    assert verdict("SPHINX-DOC-C005", bundle, corpus).verdict == "pass"


def test_c005_fails_when_source_changed_and_the_changelog_did_not(corpus):
    bundle = make_bundle(files=[SOURCE])
    assert verdict("SPHINX-DOC-C005", bundle, corpus).verdict == "fail"


def test_c005_fails_when_changes_was_edited_but_gained_no_bullet(corpus):
    changelog = make_file("CHANGES.rst", [(12, "Release 8.0")])
    bundle = make_bundle(files=[SOURCE, changelog])
    assert verdict("SPHINX-DOC-C005", bundle, corpus).verdict == "fail"


def test_c005_finds_no_target_for_a_documentation_only_change(corpus):
    """The exemption the guide names -- small doc updates -- must not be graded."""
    row = verdict("SPHINX-DOC-C005", make_bundle(files=[DOC_ONLY]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

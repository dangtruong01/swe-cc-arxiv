"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

C070 carries a fourth: a contribution with no whats-new entry at all is C069's finding and
must find no target here, or one defect would depress two rates.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pydata.pr_metadata  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("xarray/core/dataset.py", [(1, "x = 1")])


@pytest.fixture(scope="module")
def corpus():
    """pydata's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pydata"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def entry(*lines):
    return make_file("doc/whats-new.rst",
                     [(n, t) for n, t in enumerate(lines, start=40)])


# --- C069 a whats-new entry is added --------------------------------------------------


def test_c069_passes_when_the_changelog_gains_a_line(corpus):
    bundle = make_bundle(files=[SOURCE, entry("- Fixed the merge (:issue:`1234`).")])
    assert verdict("PYDATA-C069", bundle, corpus).verdict == "pass"


def test_c069_fails_when_the_changelog_is_untouched(corpus):
    assert verdict("PYDATA-C069", make_bundle(files=[SOURCE]), corpus).verdict == "fail"


def test_c069_finds_no_target_for_an_empty_contribution(corpus):
    row = verdict("PYDATA-C069", make_bundle(files=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C070 the entry cites the issue ---------------------------------------------------


def test_c070_passes_on_the_issue_role(corpus):
    bundle = make_bundle(files=[SOURCE, entry("- Fixed the merge (:issue:`1234`).")])
    assert verdict("PYDATA-C070", bundle, corpus).verdict == "pass"


def test_c070_fails_when_the_entry_cites_nothing(corpus):
    bundle = make_bundle(files=[SOURCE, entry("- Fixed the merge.")])
    assert verdict("PYDATA-C070", bundle, corpus).verdict == "fail"


def test_c070_finds_no_target_when_no_entry_was_added(corpus):
    """The missing entry is C069's finding, not this rule's."""
    row = verdict("PYDATA-C070", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

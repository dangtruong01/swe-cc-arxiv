"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

C073 carries a fourth: with no `git status` captured, the rule must find no target rather
than read an empty capture as a clean tree.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_commit, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pydata.git_conventions  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("xarray/core/dataset.py", [(1, "x = 1")])
DOC = make_file("doc/whats-new.rst", [(4, "- Fixed a thing.")])
CI = make_file("ci/requirements/environment.yml", [(3, "  - dask")])


@pytest.fixture(scope="module")
def corpus():
    """pydata's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pydata"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C018 every modified file is committed --------------------------------------------


def test_c018_passes_when_the_tree_matches_the_commit(corpus):
    bundle = make_bundle(files=[SOURCE], files_worktree={SOURCE.path: SOURCE})
    assert verdict("PYDATA-C018", bundle, corpus).verdict == "pass"


def test_c018_fails_when_a_modified_file_was_left_out(corpus):
    stray = make_file("xarray/core/merge.py", [(9, "y = 2")])
    bundle = make_bundle(files=[SOURCE],
                         files_worktree={SOURCE.path: SOURCE, stray.path: stray})
    assert verdict("PYDATA-C018", bundle, corpus).verdict == "fail"


def test_c018_finds_no_target_for_an_empty_run(corpus):
    row = verdict("PYDATA-C018", make_bundle(files=[], files_worktree={}), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C073 every new file is added -----------------------------------------------------


def test_c073_passes_when_nothing_is_untracked(corpus):
    bundle = make_bundle(files=[SOURCE], status_entries=(("M ", SOURCE.path),))
    assert verdict("PYDATA-C073", bundle, corpus).verdict == "pass"


def test_c073_fails_on_an_untracked_file(corpus):
    bundle = make_bundle(files=[SOURCE],
                         status_entries=(("M ", SOURCE.path), ("??", "xarray/core/new.py")))
    assert verdict("PYDATA-C073", bundle, corpus).verdict == "fail"


def test_c073_finds_no_target_when_status_was_not_captured(corpus):
    """An empty capture is missing evidence, not a clean tree."""
    row = verdict("PYDATA-C073", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C076 the commit references the issue ---------------------------------------------


def test_c076_passes_on_the_gh_form(corpus):
    bundle = make_bundle(files=[SOURCE], commits=[make_commit("Fix merge\n\nGH1234")])
    assert verdict("PYDATA-C076", bundle, corpus).verdict == "pass"


def test_c076_passes_on_the_hash_form(corpus):
    bundle = make_bundle(files=[SOURCE], commits=[make_commit("Fix merge (#1234)")])
    assert verdict("PYDATA-C076", bundle, corpus).verdict == "pass"


def test_c076_fails_without_a_reference(corpus):
    bundle = make_bundle(files=[SOURCE], commits=[make_commit("Fix merge")])
    assert verdict("PYDATA-C076", bundle, corpus).verdict == "fail"


def test_c076_finds_no_target_when_nothing_was_committed(corpus):
    row = verdict("PYDATA-C076", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C088 the upstream CI tag ---------------------------------------------------------


def test_c088_passes_when_a_ci_change_carries_the_tag(corpus):
    bundle = make_bundle(files=[CI],
                         commits=[make_commit("Bump dask [test-upstream]")])
    assert verdict("PYDATA-C088", bundle, corpus).verdict == "pass"


def test_c088_fails_when_a_ci_change_omits_it(corpus):
    bundle = make_bundle(files=[CI], commits=[make_commit("Bump dask")])
    assert verdict("PYDATA-C088", bundle, corpus).verdict == "fail"


def test_c088_finds_no_target_for_an_ordinary_change(corpus):
    """Most commits should not run the upstream CI, so most must not be graded."""
    row = verdict("PYDATA-C088", make_bundle(files=[SOURCE],
                                             commits=[make_commit("Fix merge")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C089 the skip-ci tag -------------------------------------------------------------


def test_c089_passes_on_a_documentation_only_commit_with_the_tag(corpus):
    bundle = make_bundle(files=[DOC], commits=[make_commit("Tidy the docs [skip-ci]")])
    assert verdict("PYDATA-C089", bundle, corpus).verdict == "pass"


def test_c089_fails_on_a_documentation_only_commit_without_it(corpus):
    bundle = make_bundle(files=[DOC], commits=[make_commit("Tidy the docs")])
    assert verdict("PYDATA-C089", bundle, corpus).verdict == "fail"


def test_c089_finds_no_target_when_code_changed_too(corpus):
    bundle = make_bundle(files=[DOC, SOURCE], commits=[make_commit("Fix and document")])
    row = verdict("PYDATA-C089", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

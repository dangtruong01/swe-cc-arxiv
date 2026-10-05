"""Three cases per rule (`docs/checker-authoring.md` §9): satisfied, violated, and an
input where the pre-condition finds nothing.

The third case is what catches a pre-condition written against the artefact the rule
demands instead of the antecedent that invokes it (§7.1). For the two skip-marker rules
it is the important one: a commit that does not use the marker must find *no target*,
not a violation.

C076 carries a fourth case: with no branch recorded, the rule withholds rather than
reading an unknown branch as a clean one.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_commit, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.matplotlib.git_conventions  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("lib/matplotlib/axes/_axes.py", [(10, "    pass")])
CI = make_file(".github/workflows/tests.yml", [(3, "  runs-on: ubuntu-latest")])


@pytest.fixture(scope="module")
def corpus():
    """matplotlib's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("matplotlib"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C076 do not commit to main -------------------------------------------------------


def test_c076_passes_on_a_contribution_branch(corpus):
    bundle = make_bundle(commits=[make_commit("Fix the axes", branch="fix/axes")])
    assert verdict("MATPLOTLIB-C076", bundle, corpus).verdict == "pass"


def test_c076_fails_on_main(corpus):
    bundle = make_bundle(commits=[make_commit("Fix the axes", branch="main")])
    assert verdict("MATPLOTLIB-C076", bundle, corpus).verdict == "fail"


def test_c076_withholds_when_no_branch_was_recorded(corpus):
    """An unrecorded branch is missing evidence, never a clean bill."""
    row = verdict("MATPLOTLIB-C076", make_bundle(commits=[make_commit("Fix")]), corpus)
    assert row.verdict == "not_applicable" and row.status == "tool_missing"


def test_c076_finds_no_target_when_nothing_was_committed(corpus):
    row = verdict("MATPLOTLIB-C076", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C082 every new file is under version control --------------------------------------


def test_c082_passes_when_nothing_is_untracked(corpus):
    bundle = make_bundle(files=[SOURCE], status_entries=(("M ", SOURCE.path),))
    assert verdict("MATPLOTLIB-C082", bundle, corpus).verdict == "pass"


def test_c082_fails_on_a_file_that_was_never_added(corpus):
    bundle = make_bundle(files=[SOURCE],
                         status_entries=(("M ", SOURCE.path),
                                         ("??", "lib/matplotlib/newthing.py")))
    assert verdict("MATPLOTLIB-C082", bundle, corpus).verdict == "fail"


def test_c082_finds_no_target_when_status_was_not_captured(corpus):
    row = verdict("MATPLOTLIB-C082", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C096 [skip appveyor] on the first line -------------------------------------------


def test_c096_passes_when_the_marker_is_on_the_summary(corpus):
    bundle = make_bundle(commits=[make_commit("Tweak docs [skip appveyor]")])
    assert verdict("MATPLOTLIB-C096", bundle, corpus).verdict == "pass"


def test_c096_fails_when_the_marker_is_in_the_body(corpus):
    bundle = make_bundle(commits=[make_commit("Tweak docs\n\n[skip appveyor]")])
    assert verdict("MATPLOTLIB-C096", bundle, corpus).verdict == "fail"


def test_c096_finds_no_target_when_the_marker_is_not_used(corpus):
    """The rule constrains an option; a commit that declines it is not in scope."""
    row = verdict("MATPLOTLIB-C096", make_bundle(commits=[make_commit("Tweak docs")]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C097 [skip ci] only where the checks do not apply ---------------------------------


def test_c097_passes_when_skip_ci_is_used_on_ci_configuration(corpus):
    bundle = make_bundle(files=[CI], commits=[make_commit("Bump runner [skip ci]")])
    assert verdict("MATPLOTLIB-C097", bundle, corpus).verdict == "pass"


def test_c097_fails_when_skip_ci_is_used_on_library_code(corpus):
    bundle = make_bundle(files=[SOURCE], commits=[make_commit("Fix axes [skip ci]")])
    assert verdict("MATPLOTLIB-C097", bundle, corpus).verdict == "fail"


def test_c097_finds_no_target_without_the_marker(corpus):
    row = verdict("MATPLOTLIB-C097",
                  make_bundle(files=[SOURCE], commits=[make_commit("Fix axes")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

The no-target cases here pin the boundary between the four fragment rules and C061: a
contribution with no fragment invokes C061 and none of the other four, and a fragment of a
type C240 does not speak to finds no target there.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.astropy.pr_metadata  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("astropy/io/fits/header.py", [(10, "    x = 1")])
TEST = make_file("astropy/io/fits/tests/test_header.py", [(3, "def test_x(): pass")])
DOC = make_file("docs/io/fits/index.rst", [(4, "The header is read lazily.")])


def fragment(path, *lines, new=True):
    return make_file(path, [(n, text) for n, text in enumerate(lines, start=1)],
                     is_new=new)


@pytest.fixture(scope="module")
def corpus():
    """astropy's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("astropy"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


GOOD = fragment("docs/changes/io.fits/1234.bugfix.rst",
                "Fixed lazy loading of headers.")


# --- C061 a changelog fragment is added ------------------------------------------------


def test_c061_passes_when_the_change_ships_a_fragment(corpus):
    assert verdict("ASTROPY-C061", make_bundle(files=[SOURCE, GOOD]), corpus).verdict == "pass"


def test_c061_fails_when_code_changed_and_no_fragment_was_added(corpus):
    assert verdict("ASTROPY-C061", make_bundle(files=[SOURCE]), corpus).verdict == "fail"


def test_c061_finds_no_target_for_a_documentation_and_test_only_change(corpus):
    """CONTRIBUTING exempts minor documentation and test updates."""
    row = verdict("ASTROPY-C061", make_bundle(files=[DOC, TEST]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C062 the fragment's name ----------------------------------------------------------


def test_c062_passes_on_the_published_name(corpus):
    assert verdict("ASTROPY-C062", make_bundle(files=[GOOD]), corpus).verdict == "pass"


def test_c062_fails_on_a_free_form_name(corpus):
    bad = fragment("docs/changes/io.fits/header-fix.rst", "Fixed lazy loading.")
    assert verdict("ASTROPY-C062", make_bundle(files=[bad]), corpus).verdict == "fail"


def test_c062_finds_no_target_when_an_existing_fragment_is_edited(corpus):
    """A fragment already in the tree was not named by the agent."""
    old = fragment("docs/changes/io.fits/wrong-name.rst", "Edited.", new=False)
    row = verdict("ASTROPY-C062", make_bundle(files=[old]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C063 no single backticks ----------------------------------------------------------


def test_c063_passes_when_the_reference_uses_a_role(corpus):
    ok = fragment("docs/changes/io.fits/1234.bugfix.rst",
                  "Fixed :func:`~astropy.io.fits.open` for lazy headers.")
    assert verdict("ASTROPY-C063", make_bundle(files=[ok]), corpus).verdict == "pass"


def test_c063_fails_on_a_single_backtick_reference(corpus):
    bad = fragment("docs/changes/io.fits/1234.bugfix.rst",
                   "Fixed `astropy.io.fits.open` for lazy headers.")
    assert verdict("ASTROPY-C063", make_bundle(files=[bad]), corpus).verdict == "fail"


def test_c063_finds_no_target_when_no_fragment_was_written(corpus):
    row = verdict("ASTROPY-C063", make_bundle(files=[SOURCE, DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C237 full sentences ---------------------------------------------------------------


def test_c237_passes_on_a_full_sentence(corpus):
    assert verdict("ASTROPY-C237", make_bundle(files=[GOOD]), corpus).verdict == "pass"


def test_c237_fails_on_a_lower_case_fragment_with_no_full_stop(corpus):
    bad = fragment("docs/changes/io.fits/1234.bugfix.rst", "fixed lazy loading")
    assert verdict("ASTROPY-C237", make_bundle(files=[bad]), corpus).verdict == "fail"


def test_c237_finds_no_target_when_the_fragment_has_no_written_text(corpus):
    empty = make_file("docs/changes/io.fits/1234.bugfix.rst", [], is_new=True)
    row = verdict("ASTROPY-C237", make_bundle(files=[empty]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C240 `other` fragments live in the root -------------------------------------------


def test_c240_passes_when_an_other_fragment_is_in_the_root(corpus):
    ok = fragment("docs/changes/1234.other.rst", "Rearranged the build.")
    assert verdict("ASTROPY-C240", make_bundle(files=[ok]), corpus).verdict == "pass"


def test_c240_fails_when_an_other_fragment_is_in_a_sub_directory(corpus):
    bad = fragment("docs/changes/io.fits/1234.other.rst", "Rearranged the build.")
    assert verdict("ASTROPY-C240", make_bundle(files=[bad]), corpus).verdict == "fail"


def test_c240_finds_no_target_for_a_bugfix_fragment_in_a_sub_directory(corpus):
    """Only the `other` type is placed by this rule; every other type belongs there."""
    row = verdict("ASTROPY-C240", make_bundle(files=[GOOD]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

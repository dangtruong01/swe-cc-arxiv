"""Three cases per rule (`docs/checker-authoring.md` §9): satisfied, violated, and an
input where the pre-condition finds nothing.

C220 carries a fourth: an entry written into the aggregated :file:`doc/users/whats_new.rst`
must find *no target* here, because that case belongs to C230. It is the pinned half of
the §7.5 resolution between the two rules.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.matplotlib.pr_metadata  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("lib/matplotlib/axes/_axes.py", [(10, "    pass")])


@pytest.fixture(scope="module")
def corpus():
    """matplotlib's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("matplotlib"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def note(path: str, body: str, *, is_new: bool = True):
    """A release-note file, given as its whole text."""
    lines = body.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=body, is_new=is_new)


DEPRECATES = make_file(
    "lib/matplotlib/cbook.py",
    [(20, "@_api.deprecated('3.9')"), (21, "def old_helper():")],
    head_text="import matplotlib as mpl\n",
)
EXPIRES = make_file(
    "lib/matplotlib/cbook.py", [(20, "def helper():")],
    removed_lines=("@_api.deprecated('3.7')", "def old_helper():"),
    head_text="def helper():\n    pass\n",
)
DEPRECATION_NOTE = note("doc/api/next_api_changes/deprecations/12345-AB.rst",
                        "``old_helper`` is deprecated\n"
                        "~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n"
                        "Use ``helper`` instead.\n")


# --- C205 a deprecation notice accompanies a new deprecation ---------------------------


def test_c205_passes_when_the_deprecation_is_announced(corpus):
    bundle = make_bundle(files=[DEPRECATES, DEPRECATION_NOTE])
    assert verdict("MATPLOTLIB-C205", bundle, corpus).verdict == "pass"


def test_c205_fails_when_no_note_is_filed(corpus):
    assert verdict("MATPLOTLIB-C205", make_bundle(files=[DEPRECATES]),
                   corpus).verdict == "fail"


def test_c205_finds_no_target_when_nothing_is_deprecated(corpus):
    row = verdict("MATPLOTLIB-C205", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C212 an announcement accompanies an expiry ----------------------------------------


def test_c212_passes_when_the_expiry_is_announced(corpus):
    removal = note("doc/api/next_api_changes/removals/12345-AB.rst",
                   "``old_helper`` has been removed\n"
                   "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    assert verdict("MATPLOTLIB-C212", make_bundle(files=[EXPIRES, removal]),
                   corpus).verdict == "pass"


def test_c212_fails_when_the_expiry_is_silent(corpus):
    assert verdict("MATPLOTLIB-C212", make_bundle(files=[EXPIRES]),
                   corpus).verdict == "fail"


def test_c212_finds_no_target_when_no_deprecation_expires(corpus):
    row = verdict("MATPLOTLIB-C212", make_bundle(files=[DEPRECATES]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C218 a pending deprecation says so in the title -----------------------------------


PENDING = make_file(
    "lib/matplotlib/cbook.py",
    [(20, "@_api.deprecated('3.9', pending=True)"), (21, "def old_helper():")],
    head_text="import matplotlib as mpl\n",
)


def test_c218_passes_when_the_title_says_pending_deprecation(corpus):
    titled = note("doc/api/next_api_changes/deprecations/1-AB.rst",
                  "Pending deprecation of ``old_helper``\n"
                  "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    assert verdict("MATPLOTLIB-C218", make_bundle(files=[PENDING, titled]),
                   corpus).verdict == "pass"


def test_c218_fails_when_the_title_does_not(corpus):
    assert verdict("MATPLOTLIB-C218", make_bundle(files=[PENDING, DEPRECATION_NOTE]),
                   corpus).verdict == "fail"


def test_c218_finds_no_target_for_an_ordinary_deprecation(corpus):
    row = verdict("MATPLOTLIB-C218", make_bundle(files=[DEPRECATES, DEPRECATION_NOTE]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C220 the entry goes in the folder for its kind ------------------------------------


FEATURE_NOTE = note("doc/users/next_whats_new/new_thing.rst",
                    "A new thing\n"
                    "~~~~~~~~~~~\n\n"
                    "``Axes.new_thing`` draws a new thing.\n")


def test_c220_passes_when_a_feature_note_is_under_whats_new(corpus):
    assert verdict("MATPLOTLIB-C220", make_bundle(files=[FEATURE_NOTE]),
                   corpus).verdict == "pass"


def test_c220_fails_when_a_deprecation_is_filed_as_a_feature(corpus):
    misfiled = note("doc/users/next_whats_new/gone.rst",
                    "Gone\n~~~~\n\n``old_helper`` is deprecated and will be removed.\n")
    assert verdict("MATPLOTLIB-C220", make_bundle(files=[misfiled]),
                   corpus).verdict == "fail"


def test_c220_finds_no_target_when_no_entry_was_filed(corpus):
    row = verdict("MATPLOTLIB-C220", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c220_finds_no_target_for_an_entry_in_no_per_kind_folder(corpus):
    """§7.5: an aggregate edit has no routing to grade -- that case is C230's."""
    aggregate = note("doc/users/whats_new.rst", "A new thing\n~~~~~~~~~~~\n",
                     is_new=False)
    row = verdict("MATPLOTLIB-C220", make_bundle(files=[aggregate]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C225 no cross-references in release-note titles -----------------------------------


def test_c225_passes_on_a_plain_title(corpus):
    assert verdict("MATPLOTLIB-C225", make_bundle(files=[FEATURE_NOTE]),
                   corpus).verdict == "pass"


def test_c225_fails_on_a_role_in_the_title(corpus):
    linked = note("doc/users/next_whats_new/linked.rst",
                  "New :func:`~matplotlib.pyplot.thing`\n"
                  "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\nBody.\n")
    assert verdict("MATPLOTLIB-C225", make_bundle(files=[linked]),
                   corpus).verdict == "fail"


def test_c225_finds_no_target_outside_the_release_notes(corpus):
    page = note("doc/devel/contribute.rst", "Contribute\n==========\n", is_new=False)
    row = verdict("MATPLOTLIB-C225", make_bundle(files=[page]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C226 API change notes go in a kind subdirectory -----------------------------------


def test_c226_passes_in_a_named_subdirectory(corpus):
    assert verdict("MATPLOTLIB-C226", make_bundle(files=[DEPRECATION_NOTE]),
                   corpus).verdict == "pass"


def test_c226_fails_at_the_root_of_next_api_changes(corpus):
    loose = note("doc/api/next_api_changes/12345-AB.rst", "Change\n~~~~~~\n")
    assert verdict("MATPLOTLIB-C226", make_bundle(files=[loose]),
                   corpus).verdict == "fail"


def test_c226_finds_no_target_for_a_whats_new_entry(corpus):
    row = verdict("MATPLOTLIB-C226", make_bundle(files=[FEATURE_NOTE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C228 code objects in titles use double backticks ----------------------------------


def test_c228_passes_when_the_code_object_is_marked(corpus):
    assert verdict("MATPLOTLIB-C228", make_bundle(files=[DEPRECATION_NOTE]),
                   corpus).verdict == "pass"


def test_c228_fails_on_a_bare_dotted_name(corpus):
    bare = note("doc/api/next_api_changes/behavior/1-AB.rst",
                "matplotlib.axes.Axes.plot now warns\n"
                "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    assert verdict("MATPLOTLIB-C228", make_bundle(files=[bare]),
                   corpus).verdict == "fail"


def test_c228_finds_no_target_when_no_note_was_written(corpus):
    row = verdict("MATPLOTLIB-C228", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C229 every new feature gets a What's new entry ------------------------------------


NEW_FEATURE = make_file(
    "lib/matplotlib/thing.py", [(1, "def new_thing():"), (2, "    return 1")],
    head_text="def new_thing():\n    return 1\n", is_new=True,
)


def test_c229_passes_when_the_feature_is_described(corpus):
    assert verdict("MATPLOTLIB-C229", make_bundle(files=[NEW_FEATURE, FEATURE_NOTE]),
                   corpus).verdict == "pass"


def test_c229_fails_when_it_is_not(corpus):
    assert verdict("MATPLOTLIB-C229", make_bundle(files=[NEW_FEATURE]),
                   corpus).verdict == "fail"


def test_c229_finds_no_target_for_a_bug_fix(corpus):
    row = verdict("MATPLOTLIB-C229", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C230 each What's new entry is its own file ----------------------------------------


def test_c230_passes_for_a_separate_file(corpus):
    assert verdict("MATPLOTLIB-C230", make_bundle(files=[FEATURE_NOTE]),
                   corpus).verdict == "pass"


def test_c230_fails_for_an_entry_appended_to_the_aggregate(corpus):
    aggregate = note("doc/users/whats_new.rst", "A new thing\n~~~~~~~~~~~\n",
                     is_new=False)
    assert verdict("MATPLOTLIB-C230", make_bundle(files=[aggregate]),
                   corpus).verdict == "fail"


def test_c230_finds_no_target_when_no_entry_was_written(corpus):
    row = verdict("MATPLOTLIB-C230", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C289 a minimum-version bump carries a development note ----------------------------


BUMP = make_file("pyproject.toml", [(5, 'requires-python = ">=3.11"')],
                 head_text='requires-python = ">=3.11"\n')


def test_c289_passes_with_the_template_note(corpus):
    templated = note("doc/api/next_api_changes/development/1-AB.rst",
                     "Increase to minimum supported versions of dependencies\n"
                     "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n"
                     "Python 3.11 is now required.\n")
    assert verdict("MATPLOTLIB-C289", make_bundle(files=[BUMP, templated]),
                   corpus).verdict == "pass"


def test_c289_fails_without_a_development_note(corpus):
    assert verdict("MATPLOTLIB-C289", make_bundle(files=[BUMP]),
                   corpus).verdict == "fail"


def test_c289_finds_no_target_when_no_minimum_moves(corpus):
    row = verdict("MATPLOTLIB-C289", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

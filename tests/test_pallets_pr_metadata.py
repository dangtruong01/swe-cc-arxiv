"""Three cases per rule (spec §9): satisfied, violated, and an input where the
pre-condition finds nothing.

C086's no-target case is doing extra work. C018 forbids a changelog entry for a change
that only touches documentation or tool configuration, and C086 requires one -- read
literally the two bind the same artefact in opposite directions. The resolution (§7.5) is
in C086's antecedent, and
``test_c086_finds_no_target_for_a_documentation_only_change_which_c018_forbids`` pins it
so it is enforced rather than remembered.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pallets.pr_metadata  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}

SOURCE = make_file("src/flask/app.py", [(10, "    return None")])
TEST = make_file("tests/test_app.py", [(20, "    assert app is not None")])
DOC = make_file("docs/quickstart.rst", [(9, "New prose about the application object.")])
CONFIG = make_file("pyproject.toml", [(5, 'line-length = 88')])

#: CHANGES.rst as flask writes it: version headings underlined with dashes, entries as
#: `-   ` bullets. The agent's entry is the last line of the top section.
CHANGELOG_HEAD = (
    "Version 3.1.0\n"
    "-------------\n"
    "\n"
    "Unreleased\n"
    "\n"
    "-   An entry that was already there.\n"
    "-   The entry the agent appended.\n"
    "\n"
    "\n"
    "Version 3.0.4\n"
    "-------------\n"
    "\n"
    "-   An older entry.\n"
)
#: The same file with the agent's entry inserted above the existing one instead.
CHANGELOG_HEAD_INSERTED = (
    "Version 3.1.0\n"
    "-------------\n"
    "\n"
    "Unreleased\n"
    "\n"
    "-   The entry the agent inserted.\n"
    "-   An entry that was already there.\n"
    "\n"
    "\n"
    "Version 3.0.4\n"
    "-------------\n"
    "\n"
    "-   An older entry.\n"
)
APPENDED = make_file("CHANGES.rst", [(7, "-   The entry the agent appended.")],
                     head_text=CHANGELOG_HEAD)
INSERTED = make_file("CHANGES.rst", [(6, "-   The entry the agent inserted.")],
                     head_text=CHANGELOG_HEAD_INSERTED)


@pytest.fixture(scope="module")
def corpus():
    """pallets' corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pallets"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C018 no changelog entry for a docs-only or tool-config-only change ------------------


def test_c018_passes_when_a_docs_only_change_adds_no_entry(corpus):
    bundle = make_bundle(files=[DOC, CONFIG])
    assert verdict("PALLETS-C018", bundle, corpus).verdict == "pass"


def test_c018_fails_when_a_docs_only_change_adds_an_entry(corpus):
    row = verdict("PALLETS-C018", make_bundle(files=[DOC, APPENDED]), corpus)
    assert row.verdict == "fail" and "only touches documentation" in row.notes


def test_c018_finds_no_target_when_the_change_touches_code(corpus):
    """The antecedent is the exempt kind of change, not the act of adding an entry."""
    row = verdict("PALLETS-C018", make_bundle(files=[SOURCE, APPENDED]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C021 a bug fix carries nothing unrelated -------------------------------------------


def test_c021_passes_on_a_focused_fix_with_its_test(corpus):
    assert verdict("PALLETS-C021", make_bundle(files=[SOURCE, TEST]),
                   corpus).verdict == "pass"


def test_c021_fails_when_the_fix_reorganises_a_test_file(corpus):
    moved = make_file("tests/test_routing.py", [(1, "from flask import Flask")],
                      old_path="tests/test_urls.py")
    row = verdict("PALLETS-C021", make_bundle(files=[SOURCE, moved]), corpus)
    assert row.verdict == "fail" and "test_urls.py" in row.notes


def test_c021_fails_when_the_fix_bundles_an_annotation_only_change(corpus):
    annotated = make_file("src/flask/typing.py",
                          [(1, "from typing import Any"), (2, "handler: Any")])
    row = verdict("PALLETS-C021", make_bundle(files=[SOURCE, annotated]), corpus)
    assert row.verdict == "fail" and "annotation" in row.notes


def test_c021_finds_no_target_for_a_documentation_only_contribution(corpus):
    row = verdict("PALLETS-C021", make_bundle(files=[DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C053 a new changelog entry is appended to the end of its section --------------------


def test_c053_passes_when_the_entry_is_appended_to_the_section(corpus):
    assert verdict("PALLETS-C053", make_bundle(files=[APPENDED]),
                   corpus).verdict == "pass"


def test_c053_fails_when_the_entry_is_inserted_above_an_existing_one(corpus):
    row = verdict("PALLETS-C053", make_bundle(files=[INSERTED]), corpus)
    assert row.verdict == "fail" and "not at the end of its section" in row.notes


def test_c053_finds_no_target_when_no_entry_was_added(corpus):
    row = verdict("PALLETS-C053", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C086 a CHANGES.rst entry summarising the change ------------------------------------


def test_c086_passes_when_the_change_adds_an_entry(corpus):
    assert verdict("PALLETS-C086", make_bundle(files=[SOURCE, APPENDED]),
                   corpus).verdict == "pass"


def test_c086_fails_when_a_code_change_leaves_the_changelog_untouched(corpus):
    row = verdict("PALLETS-C086", make_bundle(files=[SOURCE, TEST]), corpus)
    assert row.verdict == "fail" and "untouched" in row.notes


def test_c086_finds_no_target_for_a_documentation_only_change_which_c018_forbids(corpus):
    """The §7.5 resolution, pinned: demanding an entry here would contradict C018."""
    row = verdict("PALLETS-C086", make_bundle(files=[DOC, CONFIG]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

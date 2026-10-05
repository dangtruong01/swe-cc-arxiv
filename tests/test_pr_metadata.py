"""Phase 2 -- PR and release metadata.

Three cases per rule (docs/checker-authoring.md §9): a target that satisfies, one that
violates, and an input where the pre-condition finds nothing. The third is what catches
a pre-condition written against the artefact a rule demands rather than the antecedent
that invokes it.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_commit, make_file

from compliance.core.registry import registered
from compliance.core.runner import run_rule
from compliance.extractors import release_notes as rn

import compliance.rules.sympy.git_conventions  # noqa: F401
import compliance.rules.sympy.pr_metadata  # noqa: F401

RULES = {r.id: r for r in registered()}
CATEGORY = "PR and release metadata"
BEGIN, END = rn.BEGIN_MARKER, rn.END_MARKER

# Every bundle here carries a contribution, because that is the situation these rules
# are about: the agent has something to submit, so there is a pull request. Whether it
# also wrote a description is the graded behaviour, not the trigger.
CONTRIBUTION = dict(
    files=[make_file("sympy/geometry/point.py", [(1, "x = 1")])],
    commits=[make_commit("fix: the thing")],
)


def verdict(rule_id, pr_text, corpus):
    bundle = make_bundle(pr_text=pr_text, **CONTRIBUTION)
    return run_rule(bundle, RULES[rule_id], corpus).verdict


def block(*lines):
    return BEGIN + "\n" + "\n".join(lines) + "\n" + END


GOOD = "Fix the thing\n\nFixes #123 in the opening paragraph.\n\n" + block(
    "geometry", "- Fixed the distance calculation for mismatched dimensions."
)


# --- extractor ---------------------------------------------------------------------


def test_strips_a_whole_body_code_fence():
    """One pilot run wrapped its entire PR description in a ``` fence."""
    assert rn.parse("```\nTitle here\n```").title == "Title here"


def test_finds_the_block_whether_it_comes_first_or_last():
    first = rn.parse(block("core", "- Did a thing.") + "\n\nProse after.")
    last = rn.parse("Prose before.\n\n" + block("core", "- Did a thing."))
    for pr in (first, last):
        assert pr.release_notes.present and pr.release_notes.submodules == ("core",)


def test_headers_parse_with_and_without_a_trailing_colon():
    """Real runs produced both `geometry` and `functions:`."""
    for header in ("geometry", "geometry:"):
        pr = rn.parse(block(header, "- Did a thing."))
        assert pr.release_notes.submodules == ("geometry",), header


def test_no_entry_is_recognised():
    pr = rn.parse(block("NO ENTRY"))
    assert pr.release_notes.no_entry and not pr.release_notes.entries


def test_content_under_a_header_that_is_not_a_list_is_kept_as_stray():
    pr = rn.parse(block("core", "just a sentence, not a list item"))
    assert pr.release_notes.stray_lines and not pr.release_notes.entries[0].is_list_item


def test_autoclose_records_position_and_negation():
    pr = rn.parse("Opening para fixes #7.\n\nLater this does not fix #9.")
    by_number = {r.number: r for r in pr.autoclose}
    assert by_number[7].in_opening_paragraph and not by_number[7].negated
    assert by_number[9].negated


def test_missing_block_is_absent_not_empty():
    """Absent and empty mean different things: C052 vs C055."""
    assert rn.parse("Just prose.").release_notes.present is False
    assert rn.parse(block()).release_notes.present is True


# --- rules: the description as a whole ---------------------------------------------


# The four gatekeepers. Their obligation attaches to the pull request, so writing no
# description is a way of failing them, not a way of escaping them.
GATEKEEPERS = [
    ("SYMPY-C006", "Fixes #12.", "No issue mentioned at all."),
    ("SYMPY-C009", GOOD, "Prose only, no release notes."),
    ("SYMPY-C037", GOOD, "Prose only."),
    ("SYMPY-C052", GOOD, "Prose only, no block."),
]

# Prohibitions and conditional obligations. With no description there is no title to
# carry a file name and no claim to be unfinished, so nothing is violated.
DESCRIPTION_SCOPED = [
    ("SYMPY-C036", "Fix the thing", "[WIP] Fix the thing"),
    ("SYMPY-C039", "Fix the distance calculation", "Fix #123 in point.py"),
]


@pytest.mark.parametrize(("rule_id", "passing", "failing"), GATEKEEPERS + DESCRIPTION_SCOPED)
def test_whole_description_rules(rule_id, passing, failing, corpus):
    assert verdict(rule_id, passing, corpus) == "pass"
    assert verdict(rule_id, failing, corpus) == "fail"


@pytest.mark.parametrize(("rule_id", "passing", "failing"), GATEKEEPERS)
def test_writing_no_description_at_all_fails_the_gatekeepers(rule_id, passing, failing, corpus):
    """Invariant 2. These rules read "a pull request must ..."; the pull request exists
    the moment the agent has something to submit. Triggering on the description instead
    let an agent that wrote none collect not_applicable from all four -- and because they
    gatekeep the release-notes rules, all 19 rules in the category then fell silent with
    nothing failing."""
    assert verdict(rule_id, None, corpus) == "fail"


@pytest.mark.parametrize(("rule_id", "passing", "failing"), DESCRIPTION_SCOPED)
def test_description_scoped_rules_do_not_apply_without_one(rule_id, passing, failing, corpus):
    """The other side of the line: a prohibition with no artefact has nothing to
    violate, and must not be recorded as a vacuous pass either."""
    assert verdict(rule_id, None, corpus) == "not_applicable"


def test_the_gatekeepers_still_need_a_contribution_to_fire(corpus):
    """The trigger is the contribution, not the run. An empty bundle is not a pull
    request that forgot its description; it is not a pull request."""
    for rule_id, _, _ in GATEKEEPERS:
        row = run_rule(make_bundle(pr_text=None), RULES[rule_id], corpus)
        assert (row.verdict, row.n_targets) == ("not_applicable", 0), rule_id


def test_c007_only_applies_when_an_issue_is_referenced(corpus):
    assert verdict("SYMPY-C007", "Fixes #12.", corpus) == "pass"
    assert verdict("SYMPY-C007", "Related to #12.", corpus) == "fail"
    assert verdict("SYMPY-C007", "No issue mentioned.", corpus) == "not_applicable"


def test_c035_only_applies_when_the_agent_says_it_is_unfinished(corpus):
    """Draft state does not exist in a text-only PR, so the antecedent is textual."""
    assert verdict("SYMPY-C035", "[WIP] Fix\n\nStill work in progress.", corpus) == "pass"
    assert verdict("SYMPY-C035", "Fix\n\nStill work in progress.", corpus) == "fail"
    assert verdict("SYMPY-C035", "Fix the thing, complete.", corpus) == "not_applicable"


# --- rules: autoclose --------------------------------------------------------------


def test_c046_autoclose_must_sit_in_the_opening_paragraph(corpus):
    assert verdict("SYMPY-C046", "Fixes #7 right here.", corpus) == "pass"
    assert verdict("SYMPY-C046", "Opening prose.\n\nMore.\n\nFixes #7.", corpus) == "fail"
    assert verdict("SYMPY-C046", "No autoclose keyword anywhere.", corpus) == "not_applicable"


def test_c048_every_number_needs_its_own_keyword(corpus):
    assert verdict("SYMPY-C048", "Fixes #1 and fixes #2.", corpus) == "pass"
    assert verdict("SYMPY-C048", "Fixes #1, #2.", corpus) == "fail"
    assert verdict("SYMPY-C048", "Fixes #1 only.", corpus) == "not_applicable"


def test_c050_a_negated_sentence_still_autocloses(corpus):
    """`does not fix #12345` closes the issue anyway -- that is the whole point."""
    assert verdict("SYMPY-C050", "This does not fix #99.", corpus) == "fail"
    assert verdict("SYMPY-C050", "Fixes #99.", corpus) == "not_applicable"
    assert verdict("SYMPY-C050", "Does not address issue 99.", corpus) == "not_applicable"


# --- rules: the block --------------------------------------------------------------


def test_c053_headers_must_be_published_submodule_names(corpus):
    assert verdict("SYMPY-C053", block("geometry", "- Did a thing."), corpus) == "pass"
    assert verdict("SYMPY-C053", block("geomtry", "- Did a thing."), corpus) == "fail"
    assert verdict("SYMPY-C053", "No block at all.", corpus) == "not_applicable"


def test_c054_content_under_a_header_must_be_a_list(corpus):
    assert verdict("SYMPY-C054", block("core", "- Did a thing."), corpus) == "pass"
    assert verdict("SYMPY-C054", block("core", "Did a thing without a bullet."), corpus) == "fail"
    assert verdict("SYMPY-C054", "No block at all.", corpus) == "not_applicable"


def test_c055_an_empty_block_must_say_no_entry(corpus):
    assert verdict("SYMPY-C055", block("NO ENTRY"), corpus) == "pass"
    assert verdict("SYMPY-C055", block(""), corpus) == "fail"
    assert verdict("SYMPY-C055", block("core", "- Did a thing."), corpus) == "not_applicable"


# --- rules: individual entries -----------------------------------------------------


@pytest.mark.parametrize(
    ("rule_id", "good_entry", "bad_entry"),
    [
        ("SYMPY-C060", "Fixed the calculation.", "fixed the calculation"),
        ("SYMPY-C061", "Fixed the calculation.", "Fixed the calculation, thanks @someone."),
        ("SYMPY-C063", "Fixed the calculation.", "Fixed the calculation for #123."),
        ("SYMPY-C065", "Fixed the calculation.", "This pull request fixes the calculation."),
        ("SYMPY-C066", "Fixed the calculation.", "I have fixed the calculation."),
    ],
)
def test_per_entry_rules(rule_id, good_entry, bad_entry, corpus):
    assert verdict(rule_id, block("core", f"- {good_entry}"), corpus) == "pass"
    assert verdict(rule_id, block("core", f"- {bad_entry}"), corpus) == "fail"
    assert verdict(rule_id, "No release-notes block at all.", corpus) == "not_applicable"


# --- category-level guards ---------------------------------------------------------


def test_the_whole_pr_category_is_implemented(corpus):
    from compliance.core.registry import in_batch

    expected = {r for r in in_batch(corpus)
                if corpus[r].shared_category == "PR and release metadata"}
    assert expected <= set(RULES), sorted(expected - set(RULES))
    assert len(expected) == 19


def test_no_pr_rule_fires_without_a_description(corpus):
    """A run with no PR text must produce no PR verdicts at all -- absence of the
    artefact is not evidence of non-compliance for rules whose antecedent is the text."""
    pr_rules = [r for r in RULES.values() if r.category == "PR and release metadata"]
    for rule in pr_rules:
        row = run_rule(make_bundle(pr_text=None), rule, corpus)
        assert row.verdict == "not_applicable", f"{rule.id} fired on an empty description"


def test_header_and_change_on_one_line_is_content_not_an_empty_block():
    """Two pilot runs wrote `matrices: Fixed the thing.` on a single line. Parsed as
    neither header nor list item, that block looked EMPTY -- so C055 failed it for not
    saying NO ENTRY, and C053/C054 never judged it at all."""
    pr = rn.parse(block("matrices: Fixed incorrect evaluation of identity matrix elements."))
    notes = pr.release_notes
    assert notes.submodules == ("matrices",)
    assert len(notes.entries) == 1
    assert notes.entries[0].is_list_item is False   # so C054 can fail it
    assert notes.no_entry is False


def test_inline_header_is_judged_by_the_right_rules(corpus):
    text = block("matrices: Fixed incorrect evaluation of identity matrix elements.")
    assert verdict("SYMPY-C053", text, corpus) == "pass"          # matrices is published
    assert verdict("SYMPY-C054", text, corpus) == "fail"          # not a Markdown list
    assert verdict("SYMPY-C055", text, corpus) == "not_applicable"  # the block is NOT empty
    assert verdict("SYMPY-C009", text, corpus) == "pass"          # an entry does exist

"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

The no-target case does most of the work in this module. Twenty of these rules are lexical,
and the failure they are all one step away from is a pre-condition that selects the wrong
spelling instead of the situation -- which can record violations and never a pass (§7.1).
Each satisfied case here is a line written the right way that the rule still fires on.

Four no-target tests pin narrowings between rules rather than a property of one rule:

* a changelog fragment is not documentation prose, so C156 finds no target in one (§7.5);
* ``astropy`` is C153's word, so C152 finds no target on a line naming it;
* a number followed by a unit is C160's, so C161 finds no target on one;
* a development-version link is C221's, so C220 finds no target on one.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.astropy.documentation  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SRC = "astropy/io/fits/header.py"


def doc(*lines: str, path: str = "docs/io/fits/index.rst"):
    """A documentation page whose every line the agent wrote."""
    source = "\n".join(lines)
    return make_file(path, [(n, text) for n, text in enumerate(lines, start=1)],
                     head_text=source)


def py(source: str, path: str = SRC, *, new: bool = False):
    lines = source.split("\n")
    return make_file(path, [(n, text) for n, text in enumerate(lines, start=1)],
                     head_text=source, is_new=new)


@pytest.fixture(scope="module")
def corpus():
    """astropy's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("astropy"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def row(rule_id, files, corpus):
    return verdict(rule_id, make_bundle(files=files), corpus)


def line(rule_id, text, corpus):
    """Grade one line of narrative documentation."""
    return row(rule_id, [doc(text)], corpus)


NO_PROSE = py("x = 1\n")


# --- C085 public definitions have docstrings ---------------------------------------------


def test_c085_passes_on_a_documented_function(corpus):
    assert row("ASTROPY-C085", [py('def read(x):\n    """Read it."""\n    return x\n')],
               corpus).verdict == "pass"


def test_c085_fails_on_an_undocumented_public_function(corpus):
    assert row("ASTROPY-C085", [py("def read(x):\n    return x\n")], corpus).verdict == "fail"


def test_c085_finds_no_target_for_a_private_function(corpus):
    result = row("ASTROPY-C085", [py("def _read(x):\n    return x\n")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C219 docstrings are numpydoc ----------------------------------------------------------


def test_c219_passes_on_a_numpydoc_section(corpus):
    source = ('def read(x):\n'
              '    """Read it.\n\n    Parameters\n    ----------\n    x : int\n    """\n'
              '    return x\n')
    assert row("ASTROPY-C219", [py(source)], corpus).verdict == "pass"


def test_c219_fails_on_a_rest_field_list(corpus):
    source = ('def read(x):\n    """Read it.\n\n    :param x: the thing\n    """\n'
              '    return x\n')
    assert row("ASTROPY-C219", [py(source)], corpus).verdict == "fail"


def test_c219_finds_no_target_without_a_docstring(corpus):
    result = row("ASTROPY-C219", [py("def read(x):\n    return x\n")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C206 a full numpydoc docstring on new functions ------------------------------------------


FULL = ('def read(x):\n'
        '    """Read it.\n\n'
        '    Parameters\n    ----------\n    x : int\n\n'
        '    Returns\n    -------\n    int\n\n'
        '    Examples\n    --------\n    >>> read(1)\n    1\n    """\n'
        '    return x\n')


def test_c206_passes_on_a_complete_docstring(corpus):
    assert row("ASTROPY-C206", [py(FULL, new=True)], corpus).verdict == "pass"


def test_c206_fails_when_a_required_section_is_missing(corpus):
    source = ('def read(x):\n    """Read it.\n\n    Parameters\n    ----------\n'
              '    x : int\n    """\n    return x\n')
    row_ = row("ASTROPY-C206", [py(source, new=True)], corpus)
    assert row_.verdict == "fail" and "Examples" in row_.notes


def test_c206_finds_no_target_for_a_function_the_agent_only_edited(corpus):
    edited = make_file(SRC, [(16, "    return x")], head_text=FULL)
    result = row("ASTROPY-C206", [edited], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C190 implemented algorithms cite their source ----------------------------------------------


def test_c190_passes_when_the_docstring_cites_a_reference(corpus):
    source = ('def deproject(x):\n    """Deproject.\n\n    References\n    ----------\n'
              '    .. [1] Smith 1999, ApJ 1, 1\n    """\n    return x\n')
    assert row("ASTROPY-C190", [py(source, new=True)], corpus).verdict == "pass"


def test_c190_fails_when_no_origin_is_named(corpus):
    source = 'def deproject(x):\n    """Deproject."""\n    return x\n'
    assert row("ASTROPY-C190", [py(source, new=True)], corpus).verdict == "fail"


def test_c190_finds_no_target_when_nothing_public_was_added(corpus):
    result = row("ASTROPY-C190", [py("def _helper(x):\n    return x\n", new=True)], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C220 docstring cross-references use intersphinx --------------------------------------------


def test_c220_passes_on_a_role(corpus):
    source = 'def read(x):\n    """See :func:`~astropy.io.fits.open`."""\n    return x\n'
    assert row("ASTROPY-C220", [py(source)], corpus).verdict == "pass"


def test_c220_fails_on_a_url_into_the_documentation(corpus):
    source = ('def read(x):\n'
              '    """See https://docs.astropy.org/en/stable/io/fits/index.html."""\n'
              '    return x\n')
    assert row("ASTROPY-C220", [py(source)], corpus).verdict == "fail"


def test_c220_finds_no_target_for_a_development_version_link(corpus):
    """§7.5: C221 makes a direct URL the right form for these."""
    source = ('def read(x):\n'
              '    """See https://docs.astropy.org/en/latest/io/fits/index.html."""\n'
              '    return x\n')
    result = row("ASTROPY-C220", [py(source)], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C221 development-version links are direct URLs ----------------------------------------------


def test_c221_passes_on_a_direct_url(corpus):
    assert line("ASTROPY-C221",
                "See https://docs.astropy.org/en/latest/io/fits/index.html for details.",
                corpus).verdict == "pass"


def test_c221_fails_on_a_role(corpus):
    assert line("ASTROPY-C221", "See :doc:`astropy:dev/index` for details.",
                corpus).verdict == "fail"


def test_c221_finds_no_target_for_a_stable_link(corpus):
    result = line("ASTROPY-C221", "See https://docs.astropy.org/en/stable/index.html.",
                  corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C146 i.e. and e.g. ----------------------------------------------------------------------------


def test_c146_passes_inside_parentheses_with_a_comma(corpus):
    assert line("ASTROPY-C146", "The header is lazy (i.e., it is read on demand).",
                corpus).verdict == "pass"


def test_c146_fails_outside_parentheses(corpus):
    assert line("ASTROPY-C146", "The header is lazy, i.e. it is read on demand.",
                corpus).verdict == "fail"


def test_c146_finds_no_target_without_an_abbreviation(corpus):
    result = line("ASTROPY-C146", "The header is read on demand.", corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C151 organization acronyms are hyperlinked -------------------------------------------------------


def test_c151_passes_when_the_acronym_is_linked(corpus):
    assert line("ASTROPY-C151", "Data comes from the `NASA <https://www.nasa.gov>`_ archive.",
                corpus).verdict == "pass"


def test_c151_fails_when_it_is_not(corpus):
    assert line("ASTROPY-C151", "Data comes from the NASA archive.",
                corpus).verdict == "fail"


def test_c151_finds_no_target_for_a_format_acronym(corpus):
    result = line("ASTROPY-C151", "The FITS header is read lazily.", corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C152 code names are lowercase in double backticks --------------------------------------------------


def test_c152_passes_on_a_backticked_lowercase_name(corpus):
    assert line("ASTROPY-C152", "Arrays come from ``numpy`` and are converted.",
                corpus).verdict == "pass"


def test_c152_fails_on_a_bare_capitalised_name(corpus):
    assert line("ASTROPY-C152", "Arrays come from NumPy and are converted.",
                corpus).verdict == "fail"


def test_c152_finds_no_target_for_the_word_astropy(corpus):
    """§7.5: C153 legislates that word's two spellings."""
    result = line("ASTROPY-C152", "The Astropy Project maintains it.", corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C153 astropy against Astropy -------------------------------------------------------------------------


def test_c153_passes_on_both_sanctioned_spellings(corpus):
    assert line("ASTROPY-C153",
                "The ``astropy`` package is maintained by the Astropy Project.",
                corpus).verdict == "pass"


def test_c153_fails_on_a_bare_lowercase_mention(corpus):
    assert line("ASTROPY-C153", "The astropy package is maintained by volunteers.",
                corpus).verdict == "fail"


def test_c153_finds_no_target_when_the_word_is_absent(corpus):
    result = line("ASTROPY-C153", "The package is maintained by volunteers.", corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C156 no contractions ---------------------------------------------------------------------------------


def test_c156_passes_without_a_contraction(corpus):
    assert line("ASTROPY-C156", "The parser does not read the header eagerly.",
                corpus).verdict == "pass"


def test_c156_fails_on_a_contraction(corpus):
    assert line("ASTROPY-C156", "The parser doesn't read the header eagerly.",
                corpus).verdict == "fail"


def test_c156_finds_no_target_in_a_changelog_fragment(corpus):
    """§7.5: a changelog fragment is release metadata, graded by C063 and C237."""
    fragment = make_file("docs/changes/io.fits/1234.bugfix.rst",
                         [(1, "It doesn't leak file handles now.")], is_new=True)
    result = row("ASTROPY-C156", [fragment], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C160 numbers with units are numerals ------------------------------------------------------------------


def test_c160_passes_on_a_numeral(corpus):
    assert line("ASTROPY-C160", "The tolerance is 1 arcminute across the field.",
                corpus).verdict == "pass"


def test_c160_fails_on_a_spelled_out_number(corpus):
    assert line("ASTROPY-C160", "The tolerance is one arcminute across the field.",
                corpus).verdict == "fail"


def test_c160_finds_no_target_without_a_unit(corpus):
    result = line("ASTROPY-C160", "The tolerance is configurable.", corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C161 small numbers are spelled out ----------------------------------------------------------------------


def test_c161_passes_on_a_spelled_out_small_number(corpus):
    assert line("ASTROPY-C161", "There are three tables in the file.",
                corpus).verdict == "pass"


def test_c161_fails_on_a_numeral_below_ten(corpus):
    assert line("ASTROPY-C161", "There are 3 tables in the file.",
                corpus).verdict == "fail"


def test_c161_finds_no_target_when_a_unit_follows(corpus):
    """§7.5: C160 requires the numeral there, and this rule would require the word."""
    result = line("ASTROPY-C161", "The tolerance is 3 arcminutes across the field.", corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C164 parenthetical punctuation ----------------------------------------------------------------------------


def test_c164_passes_with_the_stop_inside(corpus):
    assert line("ASTROPY-C164", "(The header is read on demand.)",
                corpus).verdict == "pass"


def test_c164_fails_with_the_stop_outside(corpus):
    assert line("ASTROPY-C164", "(The header is read on demand).",
                corpus).verdict == "fail"


def test_c164_finds_no_target_without_a_parenthetical(corpus):
    result = line("ASTROPY-C164", "The header is read on demand.", corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C165 punctuation inside quotation marks ----------------------------------------------------------------------


def test_c165_passes_with_the_period_inside(corpus):
    assert line("ASTROPY-C165", 'The keyword is named "SIMPLE."',
                corpus).verdict == "pass"


def test_c165_fails_with_the_period_outside(corpus):
    assert line("ASTROPY-C165", 'The keyword is named "SIMPLE".',
                corpus).verdict == "fail"


def test_c165_finds_no_target_without_a_quotation(corpus):
    result = line("ASTROPY-C165", "The keyword is named SIMPLE.", corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C166 number ranges use an en dash ------------------------------------------------------------------------------


def test_c166_passes_on_an_unspaced_en_dash(corpus):
    assert line("ASTROPY-C166", "See chapters 14–18 for the details.",
                corpus).verdict == "pass"


def test_c166_fails_on_a_hyphen(corpus):
    assert line("ASTROPY-C166", "See chapters 14-18 for the details.",
                corpus).verdict == "fail"


def test_c166_finds_no_target_without_a_range(corpus):
    result = line("ASTROPY-C166", "See chapter 14 for the details.", corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C167 em dashes are spaced ------------------------------------------------------------------------------------------


def test_c167_passes_when_the_em_dash_is_spaced(corpus):
    assert line("ASTROPY-C167", "The result — a table — is returned.",
                corpus).verdict == "pass"


def test_c167_fails_when_it_is_not(corpus):
    assert line("ASTROPY-C167", "The result—a table—is returned.",
                corpus).verdict == "fail"


def test_c167_finds_no_target_without_an_em_dash(corpus):
    result = line("ASTROPY-C167", "The result is a table.", corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C168 American spelling ------------------------------------------------------------------------------------------------


def test_c168_passes_on_the_american_form(corpus):
    assert line("ASTROPY-C168", "Cross-matching catalog coordinates is supported.",
                corpus).verdict == "pass"


def test_c168_fails_on_the_british_form(corpus):
    assert line("ASTROPY-C168", "Cross-matching catalogue coordinates is supported.",
                corpus).verdict == "fail"


def test_c168_finds_no_target_when_no_word_alternates(corpus):
    result = line("ASTROPY-C168", "Cross-matching coordinates is supported.", corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C169 exact times on the 24-hour clock -----------------------------------------------------------------------------------


def test_c169_passes_on_the_twenty_four_hour_form(corpus):
    assert line("ASTROPY-C169", "The presentation starts at 15:00 in the hall.",
                corpus).verdict == "pass"


def test_c169_fails_on_the_twelve_hour_form(corpus):
    assert line("ASTROPY-C169", "The presentation starts at 3 p.m. in the hall.",
                corpus).verdict == "fail"


def test_c169_finds_no_target_without_a_time(corpus):
    result = line("ASTROPY-C169", "The presentation starts in the hall.", corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C170 ISO 8601 dates ------------------------------------------------------------------------------------------------------


def test_c170_passes_on_the_iso_form(corpus):
    assert line("ASTROPY-C170", "Data was released on 2018-04-25 by the mission.",
                corpus).verdict == "pass"


def test_c170_fails_on_a_written_out_date(corpus):
    assert line("ASTROPY-C170", "Data was released on April 25, 2018 by the mission.",
                corpus).verdict == "fail"


def test_c170_finds_no_target_without_a_date(corpus):
    result = line("ASTROPY-C170", "Data was released by the mission.", corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C172 the first-person inclusive plural -----------------------------------------------------------------------------------------


def test_c172_passes_on_the_inclusive_plural(corpus):
    assert line("ASTROPY-C172", "We did this the long way, but there is a short way.",
                corpus).verdict == "pass"


def test_c172_fails_on_the_singular(corpus):
    assert line("ASTROPY-C172", "I did this the long way, but there is a short way.",
                corpus).verdict == "fail"


def test_c172_finds_no_target_without_a_first_person_pronoun(corpus):
    result = line("ASTROPY-C172", "There is a shorter way to do this.", corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C173 the generic pronoun -----------------------------------------------------------------------------------------------------------


def test_c173_passes_on_you(corpus):
    assert line("ASTROPY-C173", "You can access any attribute on the frame.",
                corpus).verdict == "pass"


def test_c173_fails_on_one(corpus):
    assert line("ASTROPY-C173", "One can access any attribute on the frame.",
                corpus).verdict == "fail"


def test_c173_finds_no_target_without_a_generic_pronoun(corpus):
    result = line("ASTROPY-C173", "Every attribute on the frame is accessible.", corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C174 no belittling words -------------------------------------------------------------------------------------------------------------


def test_c174_passes_without_one(corpus):
    assert line("ASTROPY-C174", "Read the header before writing to the file.",
                corpus).verdict == "pass"


def test_c174_fails_on_a_belittling_word(corpus):
    assert line("ASTROPY-C174", "Simply read the header before writing to the file.",
                corpus).verdict == "fail"


def test_c174_finds_no_target_when_nothing_prose_was_written(corpus):
    result = row("ASTROPY-C174", [NO_PROSE], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C177 warnings note limitations in the code -------------------------------------------------------------------------------------------


def test_c177_passes_when_the_warning_is_about_the_code(corpus):
    page = doc(".. warning::", "", "   The parser ignores unknown keywords.")
    assert row("ASTROPY-C177", [page], corpus).verdict == "pass"


def test_c177_fails_when_the_warning_addresses_the_reader(corpus):
    page = doc(".. warning::", "", "   Be careful if you are not familiar with FITS.")
    assert row("ASTROPY-C177", [page], corpus).verdict == "fail"


def test_c177_finds_no_target_for_another_directive(corpus):
    page = doc(".. note::", "", "   The parser ignores unknown keywords.")
    result = row("ASTROPY-C177", [page], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C179 heading underlines --------------------------------------------------------------------------------------------------------------------


def test_c179_passes_when_the_underline_matches(corpus):
    page = doc("Reading FITS", "============", "", "Text follows.")
    assert row("ASTROPY-C179", [page], corpus).verdict == "pass"


def test_c179_fails_when_the_underline_is_short(corpus):
    page = doc("Reading FITS", "=====", "", "Text follows.")
    assert row("ASTROPY-C179", [page], corpus).verdict == "fail"


def test_c179_finds_no_target_in_a_page_with_no_heading(corpus):
    result = row("ASTROPY-C179", [doc("Text with no heading at all.")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C185 new functionality is described in the narrative docs --------------------------------------------------------------------------------------


def test_c185_passes_when_the_manual_changes_too(corpus):
    added = py('def deproject(x):\n    """Deproject."""\n    return x\n', new=True)
    assert row("ASTROPY-C185", [added, doc("Deprojection is now supported.")],
               corpus).verdict == "pass"


def test_c185_fails_when_nothing_under_docs_changes(corpus):
    added = py('def deproject(x):\n    """Deproject."""\n    return x\n', new=True)
    assert row("ASTROPY-C185", [added], corpus).verdict == "fail"


def test_c185_finds_no_target_for_a_bug_fix_that_adds_nothing_public(corpus):
    result = row("ASTROPY-C185", [py("def _helper(x):\n    return x\n", new=True)], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0

"""Unit tests for the docstring and RST extractors (docs/checker-authoring.md §9).

These extractors deliberately keep detail a real parser would normalise away -- underline
length, backtick count, a leading `~` in a cross-reference target -- because that detail
*is* what the documentation rules are about. So the tests are mostly about preserving
distinctions: a heading without an underline is not a section; a single backtick is not an
inline literal; valid RST that resembles Markdown is not Markdown.
"""

from __future__ import annotations

import textwrap

from compliance.extractors import docstrings as ds
from compliance.extractors import rst
from compliance.extractors.python_ast import parse_module

FULL = textwrap.dedent('''\
    def f(x):
        r"""Do a thing.

        Explanation
        ===========

        Longer prose about \\alpha.

        Examples
        ========

        >>> f(1)
        1

        >>> f(2)
        2

        Parameters
        ==========

        x : Expr
        """
        return x
    ''')


# A project whose section names deviate from numpydoc's, which is the normal case and the
# reason `parse` takes `known=` at all. These tests used to rely on the shared default
# carrying `Explanation` -- and it only carried it because one project's vocabulary had
# leaked into Layer B. Passing the vocabulary explicitly is how a caller is meant to use it.
PROJECT_SECTIONS = ("Summary", "Explanation") + ds.NUMPYDOC_SECTIONS


def doc_of(source: str, index: int = 0, known=PROJECT_SECTIONS):
    module = parse_module(source, "m.py")
    entry = module.docstrings[index]
    return entry, ds.parse(entry.lines(), known=known,
                           quote=ds.opening_quote(source, entry.lineno))


# --- docstring structure --------------------------------------------------------------


def test_sections_are_found_in_order_with_their_bodies():
    _, doc = doc_of(FULL)
    assert doc.section_order() == ("Explanation", "Examples", "Parameters")
    assert "x : Expr" in doc.section("Parameters").text()


def test_the_summary_is_what_precedes_the_first_heading():
    _, doc = doc_of(FULL)
    assert doc.summary_text() == "Do a thing."
    assert ds.summary_sentences(doc.summary) == ["Do a thing."]


def test_a_heading_without_an_underline_is_not_a_section():
    """The distinction a missing-underline rule depends on. Normalising it away would
    leave that rule with nothing to see."""
    source = 'def f():\n    """Do it.\n\n    Examples\n\n    >>> f()\n    """\n'
    _, doc = doc_of(source)
    assert doc.sections == ()
    assert "Examples" in doc.text()


def test_prose_over_a_rule_of_dashes_is_not_a_section():
    """Restricting to known names keeps a table separator from reading as a heading."""
    source = 'def f():\n    """Do it.\n\n    some prose\n    ----------\n    """\n'
    _, doc = doc_of(source)
    assert doc.sections == ()


def test_underline_length_is_preserved_not_normalised():
    source = 'def f():\n    """Do it.\n\n    Examples\n    ===\n\n    >>> f()\n    """\n'
    _, doc = doc_of(source)
    heading = doc.headings[0]
    assert (len(heading.name), heading.underline_length) == (8, 3)


def test_the_opening_quote_is_read_from_the_source():
    """The AST discards it, and two rules are about the quote itself."""
    _, doc = doc_of(FULL)
    assert doc.quote == 'r"""'
    _, plain = doc_of('def f():\n    """Do it."""\n')
    assert plain.quote == '"""'
    _, single = doc_of("def f():\n    '''Do it.'''\n")
    assert single.quote == "'''"


def test_doctest_blocks_are_split_on_blank_lines():
    """Parsed examples cannot show where one block ends, which is what the blank-line
    separation rules need."""
    entry, _ = doc_of(FULL)
    blocks = ds.doctest_blocks(entry.lines())
    assert [[t.strip() for _, t in b] for b in blocks] == [
        [">>> f(1)", "1"], [">>> f(2)", "2"]]


def test_line_numbers_are_real_file_lines():
    entry, doc = doc_of(FULL)
    source_lines = FULL.split("\n")
    for lineno, text in doc.lines:
        assert text in source_lines[lineno - 1]


# --- RST surface ----------------------------------------------------------------------


def test_a_heading_underline_must_be_long_enough():
    assert rst.headings([(1, "Title"), (2, "=====")])[0].is_consistent is True
    assert rst.headings([(1, "Long Title"), (2, "===")])[0].is_consistent is False


def test_a_mixed_underline_is_inconsistent():
    assert rst.headings([(1, "Title"), (2, "==-==")])[0].is_consistent is False


def test_roles_keep_the_tilde_and_the_custom_text_form():
    found = rst.roles([(1, "See :obj:`~.Point` and :obj:`the point <pkg.geom.Point>`.")])
    assert (found[0].has_tilde, found[0].is_abbreviated) == (True, True)
    assert found[1].custom_text is True
    assert found[1].link_target == "pkg.geom.Point"
    assert found[1].has_tilde is False


def test_a_single_backtick_is_not_an_inline_literal():
    assert rst.single_backtick_spans("use `code` here") == ["code"]
    assert rst.single_backtick_spans("use ``code`` here") == []


def test_a_role_is_not_mistaken_for_a_bare_backtick_span():
    """Roles use one backtick, so they have to be removed before looking for bare spans
    or every cross-reference would read as a formatting error."""
    assert rst.single_backtick_spans("see :obj:`~.Point` now") == []


def test_only_constructs_rst_lacks_count_as_markdown():
    """`**bold**` and `- item` are valid RST, so flagging them would fail correct RST."""
    lines = [(1, "**bold** text"), (2, "- a bullet"), (3, "## heading"),
             (4, "[text](http://x)"), (5, "```")]
    assert sorted(n for n, _ in rst.markdown_constructs(lines)) == [3, 4, 5]


def test_citations_and_dois_are_extracted():
    lines = [(1, ".. [1] A paper, doi:10.1090/S0002-9939 and https://x.org")]
    assert rst.citations(lines) == [(1, "1")]
    assert rst.dois(lines[0][1]) == ["10.1090/S0002-9939"]
    assert rst.urls(lines[0][1]) == ["https://x.org"]


def test_code_block_opener_is_detected():
    assert rst.opens_code_block("For example::") is True
    assert rst.opens_code_block("For example:") is False


def test_the_shared_section_vocabulary_is_numpydoc_and_not_one_projects_dialect():
    """Layer B's default must be the convention it is named after.

    It carried `Explanation` for months, which is not a numpydoc section — numpydoc calls
    that `Extended Summary`. So the shared default was one project's vocabulary under a
    generic label, and two tests in this file passed only because of it.

    `test_layers.py` cannot catch this: its guard looks for repository slugs and curated
    repo vocabulary, and `Explanation` is an ordinary English word. That is the stated
    limit of those guards (C4) showing up in practice, so the check has to live here,
    against the specific constant.
    """
    assert "Extended Summary" in ds.NUMPYDOC_SECTIONS
    assert "Explanation" not in ds.NUMPYDOC_SECTIONS, (
        "a project's own section name is back in the shared default; pass it via known= "
        "from that project's rule pack instead"
    )


def test_a_caller_can_add_its_own_section_names():
    """The mechanism that replaces the leak: `known=` is how a project states its dialect."""
    source = textwrap.dedent('''\
        def f():
            """Do a thing.

            Explanation
            ===========

            Prose.
            """
        ''')
    _, generic = doc_of(source, known=ds.NUMPYDOC_SECTIONS)
    assert generic.section_order() == ()
    _, dialect = doc_of(source, known=("Explanation",) + ds.NUMPYDOC_SECTIONS)
    assert dialect.section_order() == ("Explanation",)

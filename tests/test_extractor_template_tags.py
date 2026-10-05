"""Unit tests for the curly-brace template tag extractor (docs/checker-authoring.md §9).

The rules built on this one ask *where* and *how it is written*, never *what it means* --
is the extends tag first, is there one space inside the braces, is the closing tag on the
opener's line, are the arguments sorted. So these tests are mostly about detail a parser
would throw away: the column a tag starts at, the two spaces someone left inside `{%`, the
indentation of the line, the line a token sits on when the tag is broken across three.

The other half is degradation. Templates in a repository under change are frequently
half-written, and an extractor that raises on an unclosed tag takes the whole rule down
with it -- so every malformed shape here is asserted to lex what it can and report the rest.
"""

from __future__ import annotations

import textwrap

import pytest

from compliance.extractors import template_tags as tt

PAGE = textwrap.dedent('''\
    {# the page comment #}
    {% extends "base.html" %}
    {% load i18n humanize %}

    <div class="{{ css_class }}">
      {% block content %}
        {{ user.name|title }}
        {%if flag%}<b>{{count}}</b>{% endif %}
      {% endblock content %}
    </div>
    ''')


@pytest.fixture(scope="module")
def page():
    return tt.tokenize(PAGE)


# --- tokenising ------------------------------------------------------------------------

@pytest.mark.parametrize("source", ["", None])
def test_an_empty_file_has_no_nodes_and_no_complaints(source):
    assert tt.tokenize(source) == []
    assert tt.malformed_delimiters(source) == []


def test_a_file_without_tags_is_one_text_run():
    nodes = tt.tokenize("<p>hello</p>\n")
    assert [node.kind for node in nodes] == ["text"]
    assert nodes[0].raw == "<p>hello</p>\n"


def test_the_four_kinds_come_back_in_source_order(page):
    kinds = [node.kind for node in page if not node.is_blank]
    assert kinds[:4] == ["comment", "block", "block", "text"]


def test_every_tag_carries_the_line_it_sits_on(page):
    assert [(node.name, node.lineno) for node in tt.block_tags(page)] == [
        ("extends", 2), ("load", 3), ("block", 6), ("if", 8), ("endif", 8),
        ("endblock", 9),
    ]


def test_a_tag_inside_markup_carries_its_column(page):
    inline = tt.variable_expressions(page)[0]
    assert (inline.lineno, inline.col) == (5, 12)
    assert inline.raw == "{{ css_class }}"
    assert PAGE.split("\n")[inline.lineno - 1][inline.col:inline.col + 2] == "{{"


def test_the_filters_select_by_kind(page):
    assert len(tt.block_tags(page)) == 6
    assert [node.raw for node in tt.comment_nodes(page)] == ["{# the page comment #}"]
    assert len(tt.variable_expressions(page)) == 3
    assert [node.name for node in tt.tags_named(page, "block", "endblock")] == [
        "block", "endblock"]


# --- names and arguments ---------------------------------------------------------------

def test_a_tag_splits_into_a_name_and_arguments(page):
    load = tt.tags_named(page, "load")[0]
    assert load.name == "load"
    assert load.args == ("i18n", "humanize")


def test_a_quoted_argument_stays_in_one_piece():
    tag = tt.block_tags(tt.tokenize('{% include "a page.html" %}'))[0]
    assert tag.args == ('"a page.html"',)
    assert tt.unquote(tag.args[0]) == "a page.html"


def test_a_variable_expression_has_no_tag_name(page):
    assert tt.variable_expressions(page)[0].name == ""
    assert tt.variable_expressions(page)[0].args == ()


def test_a_closing_tag_knows_what_it_closes(page):
    endblock = tt.tags_named(page, "endblock")[0]
    assert endblock.is_closing and endblock.closes == "block"
    assert not tt.tags_named(page, "block")[0].is_closing


# --- placement -------------------------------------------------------------------------

def test_a_comment_and_blank_lines_do_not_count_as_the_first_thing(page):
    first = tt.first_significant(page)
    assert first.name == "extends" and first.lineno == 2
    assert tt.is_first_significant(page, first)


def test_a_tag_after_markup_is_not_the_first_thing():
    nodes = tt.tokenize("<h1>title</h1>\n{% extends 'base.html' %}\n")
    extends = tt.tags_named(nodes, "extends")[0]
    assert not tt.is_first_significant(nodes, extends)
    assert tt.first_significant(nodes).is_text


def test_a_file_of_only_comments_and_whitespace_has_no_first_thing():
    assert tt.first_significant(tt.tokenize("{# a #}\n\n  {# b #}\n")) is None


def test_indentation_is_the_leading_whitespace_of_the_tags_line(page):
    inner = tt.tags_named(page, "if")[0]
    assert inner.indent == "    " and inner.indent_width == 4
    assert tt.tags_named(page, "block")[0].indent == "  "


def test_a_tag_embedded_in_a_line_does_not_start_it(page):
    assert not tt.variable_expressions(page)[0].starts_line
    assert tt.tags_named(page, "block")[0].starts_line


# --- spacing ---------------------------------------------------------------------------

def test_inner_spacing_is_counted_on_both_sides(page):
    assert tt.tags_named(page, "block")[0].spacing == (1, 1)
    assert tt.tags_named(page, "block")[0].has_single_inner_spacing


@pytest.mark.parametrize("raw, spacing", [
    ("{%if flag%}", (0, 0)),
    ("{%  if flag %}", (2, 1)),
    ("{% if flag  %}", (1, 2)),
    ("{{name}}", (0, 0)),
    ("{{ name }}", (1, 1)),
])
def test_spacing_that_is_not_one_space_is_reported_as_written(raw, spacing):
    node = tt.tokenize(raw)[0]
    assert node.spacing == spacing
    assert node.has_single_inner_spacing == (spacing == (1, 1))


def test_an_empty_tag_reports_its_width_rather_than_raising():
    node = tt.tokenize("{%  %}")[0]
    assert node.leading_space == 2 and node.trailing_space == 2
    assert not node.has_single_inner_spacing
    assert node.name == "" and node.args == ()


def test_expression_tokens_carry_the_whitespace_around_them(page):
    tokens = tt.expression_tokens(tt.variable_expressions(page)[1])
    assert [token.text for token in tokens] == ["user", ".", "name", "|", "title"]
    assert [token.space_before for token in tokens] == [1, 0, 0, 0, 0]
    assert tokens[-1].space_after == 1


def test_attribute_access_and_filters_are_flagged_as_the_tight_ones(page):
    tokens = tt.expression_tokens(tt.variable_expressions(page)[1])
    tight = [token.text for token in tokens if token.is_tight_operator]
    assert tight == [".", "|"]
    # The judgement a rule makes: tight operators touch, everything else is single-spaced.
    assert all(token.space_before == 0 and token.space_after == 0
               for token in tokens if token.is_tight_operator)


def test_a_loose_filter_is_visible_as_spaces_around_the_pipe():
    tokens = tt.expression_tokens(tt.tokenize("{{ name | title }}")[0])
    pipe = [token for token in tokens if token.is_tight_operator][0]
    assert (pipe.space_before, pipe.space_after) == (1, 1)


def test_token_kinds_separate_strings_and_numbers_from_names():
    tokens = tt.expression_tokens(tt.tokenize('{% if n > 2 and s == "x" %}')[0])
    kinds = {token.text: token.kind for token in tokens}
    assert kinds["2"] == "number" and kinds['"x"'] == "string"
    assert kinds["n"] == "name" and kinds[">"] == "operator"


# --- tags spanning lines ---------------------------------------------------------------

def test_a_tag_broken_across_lines_keeps_both_ends_and_the_tokens_line_numbers():
    node = tt.tokenize("{% if a\n   and b %}\n")[0]
    assert node.spans_lines and node.span == (1, 2)
    assert [(token.text, token.lineno) for token in node.tokens] == [
        ("if", 1), ("a", 1), ("and", 2), ("b", 2)]
    # The break is whitespace like any other, so the spacing question stays answerable.
    assert [token.space_before for token in node.tokens] == [1, 1, 4, 1]


# --- pairing ---------------------------------------------------------------------------

def test_an_opener_pairs_with_its_closer_and_knows_the_lines_apart(page):
    pair = tt.tag_pairs(page)[0]
    assert (pair.name, pair.label) == ("block", "content")
    assert pair.is_closed and pair.span == (6, 9)
    assert not pair.same_line


def test_a_block_opened_and_closed_on_one_line_says_so(page):
    pair = [p for p in tt.tag_pairs(page) if p.name == "if"][0]
    assert pair.same_line and pair.span == (8, 8)


def test_whether_the_closer_repeats_the_block_name(page):
    named = tt.tag_pairs(page)[0]
    assert named.closer_repeats_name and named.names_agree
    bare = [p for p in tt.tag_pairs(page) if p.name == "if"][0]
    assert not bare.closer_repeats_name and not bare.names_agree


def test_a_closer_repeating_the_wrong_name_is_a_disagreement():
    pair = tt.tag_pairs(tt.tokenize("{% block a %}\n{% endblock b %}\n"))[0]
    assert pair.closer_repeats_name and not pair.names_agree


def test_nested_blocks_match_innermost_first():
    nodes = tt.tokenize(textwrap.dedent('''\
        {% block outer %}
          {% block inner %}
          {% endblock %}
        {% endblock %}
        '''))
    pairs = tt.tag_pairs(nodes)
    assert [(pair.label, pair.span) for pair in pairs] == [("outer", (1, 4)),
                                                           ("inner", (2, 3))]


def test_a_tag_that_opens_nothing_does_not_break_the_pairing():
    nodes = tt.tokenize("{% block a %}\n{% load i18n %}\n{% endblock %}\n")
    pairs = tt.tag_pairs(nodes)
    assert len(pairs) == 1 and pairs[0].span == (1, 3)


def test_an_unclosed_block_comes_back_with_no_closer():
    nodes = tt.tokenize("{% block a %}\n{% block b %}\n{% endblock %}\n")
    pairs = tt.tag_pairs(nodes)
    assert [(pair.label, pair.is_closed) for pair in pairs] == [("a", False), ("b", True)]
    assert pairs[0].span == (1, 1)


def test_a_closing_tag_with_nothing_open_is_reported_separately():
    nodes = tt.tokenize("<p>x</p>\n{% endif %}\n")
    orphans = tt.unmatched_closers(nodes)
    assert [node.lineno for node in orphans] == [2]
    assert tt.tag_pairs(nodes) == []


# --- malformed input -------------------------------------------------------------------

def test_an_unterminated_tag_is_reported_and_the_rest_still_lexes():
    source = "<p>Write {% to open a tag.</p>\n{% block b %}hi{% endblock %}\n"
    broken = tt.malformed_delimiters(source)
    assert [(item.reason, item.delimiter, item.lineno, item.col) for item in broken] == [
        ("unterminated", "{%", 1, 9)]
    assert [pair.span for pair in tt.tag_pairs(tt.tokenize(source))] == [(2, 2)]


def test_a_double_brace_in_prose_does_not_swallow_the_tags_below_it():
    source = "Type {{ to interpolate.\n{{ name }}\n"
    kinds = [node.kind for node in tt.tokenize(source)]
    assert kinds.count("variable") == 1
    assert tt.variable_expressions(tt.tokenize(source))[0].lineno == 2
    assert [item.reason for item in tt.malformed_delimiters(source)] == ["unterminated"]


def test_a_stray_closing_delimiter_is_reported_with_its_line():
    broken = tt.malformed_delimiters("<p>ok</p>\n<p>50%} off</p>\n")
    assert [(item.reason, item.delimiter, item.lineno) for item in broken] == [
        ("stray", "%}", 2)]


def test_a_comment_may_contain_what_looks_like_a_tag():
    nodes = tt.tokenize("{# {% block a %} #}\n{{ x }}\n")
    assert [node.kind for node in nodes if not node.is_text] == ["comment", "variable"]
    assert tt.malformed_delimiters("{# {% block a %} #}\n{{ x }}\n") == []


@pytest.mark.parametrize("source", [
    "{%", "{{", "{#", "%}", "}}", "{% %}{{", "{{{{}}}}", "{% block", "{%%}",
    "{# unclosed", "{% a %}{% enda %}{% enda %}", "\n\n{{\n\n",
])
def test_nothing_raises_on_garbage(source):
    nodes = tt.tokenize(source)
    tt.malformed_delimiters(source)
    tt.tag_pairs(nodes)
    tt.unmatched_closers(nodes)
    for node in nodes:
        assert node.spacing == node.spacing and node.name == node.name
        tt.expression_tokens(node)


# --- argument order and paths ----------------------------------------------------------

@pytest.mark.parametrize("values, expected", [
    (("i18n", "humanize"), False),
    (("humanize", "i18n"), True),
    ((), True),
    (("a",), True),
    (('"b"', '"a"'), False),
    (("Alpha", "beta"), True),
])
def test_alphabetical_order_of_an_argument_list(values, expected):
    assert tt.is_alphabetical(values) is expected


def test_case_folding_can_be_turned_off():
    # Byte order puts every capital ahead of every lowercase letter; a human reading the
    # list would not, which is why folding is the default.
    assert tt.is_alphabetical(("Zeta", "alpha"), fold_case=False)
    assert not tt.is_alphabetical(("Zeta", "alpha"))


@pytest.mark.parametrize("path, expected", [
    ("a/b/page.html", True), ("page.htm", True), ("page.txt", False), ("mod.py", False),
])
def test_template_paths_are_recognised_by_suffix(path, expected):
    assert tt.is_template_path(path) is expected

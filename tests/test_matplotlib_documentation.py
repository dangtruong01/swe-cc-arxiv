"""Three cases per rule (`docs/checker-authoring.md` §9): satisfied, violated, and an
input where the pre-condition finds nothing.

Many of the no-target cases here are doing double duty: they pin the §7.5 narrowings the
module docstring lists, so that a later edit which lets two rules grade one defect fails a
test rather than quietly halving a rate. They are named ``..._is_left_to_cNNN`` where that
is what they are for.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.matplotlib.documentation  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


@pytest.fixture(scope="module")
def corpus():
    """matplotlib's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("matplotlib"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def whole(path: str, body: str, **kwargs):
    """A whole file, every line of it written by the agent."""
    lines = body.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=body, **kwargs)


PAGE = "doc/devel/contribute.rst"
LIB = "lib/matplotlib/axes/_axes.py"
EXAMPLE = "galleries/examples/lines_bars/plot_simple.py"
PLOT_TYPE = "galleries/plot_types/basic/plot.py"


def page(body: str, path: str = PAGE, **kwargs):
    return whole(path, body, **kwargs)


def example(body: str, path: str = EXAMPLE, **kwargs):
    return whole(path, body, **kwargs)


def one(rule_id, files, corpus):
    return verdict(rule_id, make_bundle(files=files), corpus)


def no_target(row):
    return row.verdict == "not_applicable" and row.n_targets == 0


# --- C001 generated pages are not edited -------------------------------------------------


def test_c001_passes_for_a_hand_written_page(corpus):
    assert one("MATPLOTLIB-C001", [page("Title\n=====\n")], corpus).verdict == "pass"


def test_c001_fails_for_a_generated_gallery_page(corpus):
    assert one("MATPLOTLIB-C001",
               [page("Title\n=====\n", "doc/gallery/index.rst")],
               corpus).verdict == "fail"


def test_c001_passes_for_the_api_changes_exception(corpus):
    assert one("MATPLOTLIB-C001",
               [page("Note\n====\n", "doc/api/api_changes/note.rst")],
               corpus).verdict == "pass"


def test_c001_finds_no_target_when_no_documentation_page_changed(corpus):
    assert no_target(one("MATPLOTLIB-C001", [whole(LIB, "x = 1\n")], corpus))


# --- C002 sentence case ------------------------------------------------------------------


def test_c002_passes_for_a_sentence_case_title(corpus):
    assert one("MATPLOTLIB-C002", [page("Contribute to the docs\n"
                                        "======================\n")],
               corpus).verdict == "pass"


def test_c002_fails_for_a_title_case_title(corpus):
    assert one("MATPLOTLIB-C002", [page("Contribute To The Docs\n"
                                        "======================\n")],
               corpus).verdict == "fail"


def test_c002_finds_no_target_for_a_page_with_no_titles(corpus):
    assert no_target(one("MATPLOTLIB-C002", [page("Just a paragraph of prose.\n")],
                         corpus))


# --- C003/C004 heading adornments ---------------------------------------------------------


LEVELS = ("Chapter\n*******\n\nSection\n=======\n\nSubsection\n----------\n")
BAD_LEVELS = ("Chapter\n*******\n\nSection\n-------\n")


def test_c003_passes_for_the_listed_adornments(corpus):
    assert one("MATPLOTLIB-C003", [page(LEVELS)], corpus).verdict == "pass"


def test_c003_fails_when_a_level_uses_the_wrong_character(corpus):
    assert one("MATPLOTLIB-C003", [page(BAD_LEVELS)], corpus).verdict == "fail"


def test_c003_finds_no_target_for_a_hash_overline_which_is_left_to_c004(corpus):
    """The §7.5 half: `#` belongs to C004, so C003 must not grade it."""
    assert no_target(one("MATPLOTLIB-C003",
                         [page("Main\n####\n", "doc/index.rst")], corpus))


def test_c004_passes_when_the_hash_titles_an_index_page(corpus):
    assert one("MATPLOTLIB-C004", [page("Main\n####\n", "doc/index.rst")],
               corpus).verdict == "pass"


def test_c004_fails_when_an_ordinary_page_uses_the_hash_overline(corpus):
    assert one("MATPLOTLIB-C004", [page("Main\n####\n")], corpus).verdict == "fail"


def test_c004_finds_no_target_for_a_page_with_no_headings(corpus):
    assert no_target(one("MATPLOTLIB-C004", [page("Just prose.\n")], corpus))


# --- C006/C007/C008 marking up function arguments -----------------------------------------


def docstring_module(body: str, path: str = LIB):
    return whole(path, body)


EMPHASISED = ('def plot(x, color=None):\n'
              '    """Draw a line.\n'
              '\n'
              '    The *color* is applied to the line.\n'
              '    """\n')
BARE = ('def plot(x, color=None):\n'
        '    """Draw a line.\n'
        '\n'
        '    The color is applied to the line.\n'
        '    """\n')
DEFAULT_ROLE = ('def plot(x, color=None):\n'
                '    """Draw a line.\n'
                '\n'
                '    The `color` is applied to the line.\n'
                '    """\n')
LITERAL_ROLE = ('def plot(x, color=None):\n'
                '    """Draw a line.\n'
                '\n'
                '    The ``color`` is applied to the line.\n'
                '    """\n')
CLASS_ROLE = ('def plot(x, color=None):\n'
              '    """Draw a line.\n'
              '\n'
              '    The `Axes` owns the line.\n'
              '    """\n')


def test_c006_passes_for_an_emphasised_argument(corpus):
    assert one("MATPLOTLIB-C006", [docstring_module(EMPHASISED)], corpus).verdict == "pass"


def test_c006_fails_for_a_bare_argument_mention(corpus):
    assert one("MATPLOTLIB-C006", [docstring_module(BARE)], corpus).verdict == "fail"


def test_c006_finds_no_target_for_a_backticked_mention_left_to_c007(corpus):
    """The §7.5 half: a default-role span is C007's, so C006 must not see it."""
    assert no_target(one("MATPLOTLIB-C006", [docstring_module(DEFAULT_ROLE)], corpus))


def test_c007_passes_when_the_default_role_marks_something_else(corpus):
    assert one("MATPLOTLIB-C007", [docstring_module(CLASS_ROLE)], corpus).verdict == "pass"


def test_c007_fails_when_the_default_role_marks_an_argument(corpus):
    assert one("MATPLOTLIB-C007", [docstring_module(DEFAULT_ROLE)], corpus).verdict == "fail"


def test_c007_finds_no_target_when_nothing_uses_the_default_role(corpus):
    assert no_target(one("MATPLOTLIB-C007", [docstring_module(EMPHASISED)], corpus))


def test_c008_passes_when_the_literal_role_marks_a_value(corpus):
    body = ('def plot(x, color=None):\n'
            '    """Draw a line.\n'
            '\n'
            '    Pass ``"red"`` for a red line.\n'
            '    """\n')
    assert one("MATPLOTLIB-C008", [docstring_module(body)], corpus).verdict == "pass"


def test_c008_fails_when_the_literal_role_marks_an_argument(corpus):
    assert one("MATPLOTLIB-C008", [docstring_module(LITERAL_ROLE)], corpus).verdict == "fail"


def test_c008_finds_no_target_when_nothing_uses_the_literal_role(corpus):
    assert no_target(one("MATPLOTLIB-C008", [docstring_module(EMPHASISED)], corpus))


# --- C009/C010 mathematics -----------------------------------------------------------------


def test_c009_passes_for_the_math_role(corpus):
    assert one("MATPLOTLIB-C009",
               [page("The value :math:`\\alpha` scales the line.\n")],
               corpus).verdict == "pass"


def test_c009_fails_for_bare_inline_latex(corpus):
    assert one("MATPLOTLIB-C009", [page("The value $\\alpha$ scales the line.\n")],
               corpus).verdict == "fail"


def test_c009_finds_no_target_for_prose_with_no_mathematics(corpus):
    assert no_target(one("MATPLOTLIB-C009", [page("The value scales the line.\n")],
                         corpus))


def test_c010_passes_under_a_math_directive(corpus):
    body = ".. math::\n\n   \\begin{equation} a = b \\end{equation}\n"
    assert one("MATPLOTLIB-C010", [page(body)], corpus).verdict == "pass"


def test_c010_fails_for_a_bare_display_block(corpus):
    assert one("MATPLOTLIB-C010", [page("$$ a = b $$\n")], corpus).verdict == "fail"


def test_c010_finds_no_target_for_inline_mathematics_left_to_c009(corpus):
    assert no_target(one("MATPLOTLIB-C010", [page("The value $\\alpha$ scales it.\n")],
                         corpus))


# --- C011 page links ------------------------------------------------------------------------


def test_c011_passes_for_the_doc_role(corpus):
    assert one("MATPLOTLIB-C011", [page("See :doc:`/devel/testing` for more.\n")],
               corpus).verdict == "pass"


def test_c011_fails_for_a_raw_path_link(corpus):
    assert one("MATPLOTLIB-C011", [page("See devel/testing.rst for more.\n")],
               corpus).verdict == "fail"


def test_c011_finds_no_target_when_nothing_links_to_a_page(corpus):
    assert no_target(one("MATPLOTLIB-C011", [page("Nothing links anywhere.\n")], corpus))


# --- C013/C014/C015 reference labels ----------------------------------------------------------


LABELLED = ".. _writing-docs:\n\nWriting docs\n============\n"


def test_c013_passes_for_hyphen_separated_words(corpus):
    assert one("MATPLOTLIB-C013", [page(LABELLED)], corpus).verdict == "pass"


def test_c013_fails_for_an_underscored_label(corpus):
    body = ".. _writing_docs:\n\nWriting docs\n============\n"
    assert one("MATPLOTLIB-C013", [page(body)], corpus).verdict == "fail"


def test_c013_finds_no_target_for_a_page_with_no_labels(corpus):
    assert no_target(one("MATPLOTLIB-C013", [page("Title\n=====\n")], corpus))


def test_c014_passes_when_the_label_does_not_repeat_the_path(corpus):
    assert one("MATPLOTLIB-C014", [page(LABELLED)], corpus).verdict == "pass"


def test_c014_fails_when_the_label_repeats_a_directory(corpus):
    body = ".. _devel-writing-docs:\n\nWriting docs\n============\n"
    assert one("MATPLOTLIB-C014", [page(body)], corpus).verdict == "fail"


def test_c014_finds_no_target_for_a_malformed_label_left_to_c013(corpus):
    """The §7.5 half: an underscored label is C013's finding, not counted twice here."""
    body = ".. _devel_writing_docs:\n\nWriting docs\n============\n"
    assert no_target(one("MATPLOTLIB-C014", [page(body)], corpus))


def test_c015_passes_when_the_label_precedes_a_section(corpus):
    assert one("MATPLOTLIB-C015", [page(LABELLED)], corpus).verdict == "pass"


def test_c015_fails_when_the_label_precedes_prose(corpus):
    body = ".. _writing-docs:\n\nJust a paragraph, no section title here at all.\n"
    assert one("MATPLOTLIB-C015", [page(body)], corpus).verdict == "fail"


def test_c015_finds_no_target_for_a_page_with_no_labels(corpus):
    assert no_target(one("MATPLOTLIB-C015", [page("Title\n=====\n")], corpus))


# --- C016/C018 references to code ---------------------------------------------------------------


def test_c016_passes_for_a_back_ticked_reference(corpus):
    assert one("MATPLOTLIB-C016",
               [page("See `matplotlib.axes.Axes.plot` for details.\n")],
               corpus).verdict == "pass"


def test_c016_fails_for_a_bare_dotted_name(corpus):
    assert one("MATPLOTLIB-C016",
               [page("See matplotlib.axes.Axes.plot for details.\n")],
               corpus).verdict == "fail"


def test_c016_finds_no_target_when_no_code_element_is_named(corpus):
    assert no_target(one("MATPLOTLIB-C016", [page("Nothing is named here.\n")], corpus))


def test_c018_passes_for_a_qualified_reference(corpus):
    assert one("MATPLOTLIB-C018",
               [page("See :meth:`~matplotlib.axes.Axes.plot` for details.\n")],
               corpus).verdict == "pass"


def test_c018_fails_for_a_bare_ambiguous_name(corpus):
    assert one("MATPLOTLIB-C018", [page("See :meth:`plot` for details.\n")],
               corpus).verdict == "fail"


def test_c018_finds_no_target_for_an_unambiguous_name(corpus):
    assert no_target(one("MATPLOTLIB-C018",
                         [page("See :func:`get_backend` for details.\n")], corpus))


# --- C019 the plot directive ------------------------------------------------------------------


def test_c019_passes_when_the_directive_names_a_script(corpus):
    assert one("MATPLOTLIB-C019", [page(".. plot:: mpl_examples/simple.py\n")],
               corpus).verdict == "pass"


def test_c019_fails_when_the_directive_names_an_image(corpus):
    assert one("MATPLOTLIB-C019", [page(".. plot:: _static/simple.png\n")],
               corpus).verdict == "fail"


def test_c019_finds_no_target_for_an_inline_plot_directive(corpus):
    assert no_target(one("MATPLOTLIB-C019",
                         [page(".. plot::\n\n   plt.plot([1, 2])\n")], corpus))


# --- C020/C021 redirects -------------------------------------------------------------------------


MOVED = make_file("doc/users/old.rst", [], is_deleted=True)


def test_c020_passes_when_a_redirect_is_added(corpus):
    new = page(".. redirect-from:: /users/old\n\nNew\n===\n", "doc/users/new.rst")
    assert one("MATPLOTLIB-C020", [MOVED, new], corpus).verdict == "pass"


def test_c020_fails_when_the_old_url_goes_dead(corpus):
    new = page("New\n===\n", "doc/users/new.rst")
    assert one("MATPLOTLIB-C020", [MOVED, new], corpus).verdict == "fail"


def test_c020_finds_no_target_when_no_page_moved(corpus):
    assert no_target(one("MATPLOTLIB-C020", [page("Title\n=====\n")], corpus))


def test_c021_passes_for_a_full_path(corpus):
    assert one("MATPLOTLIB-C021", [page(".. redirect-from:: /users/old\n")],
               corpus).verdict == "pass"


def test_c021_fails_for_a_relative_path(corpus):
    assert one("MATPLOTLIB-C021", [page(".. redirect-from:: ../users/old\n")],
               corpus).verdict == "fail"


def test_c021_finds_no_target_when_no_redirect_is_written(corpus):
    assert no_target(one("MATPLOTLIB-C021", [page("Title\n=====\n")], corpus))


# --- C023 numpydoc structure -------------------------------------------------------------------


GOOD_NUMPYDOC = ('def plot(x):\n'
                 '    """Draw a line.\n'
                 '\n'
                 '    Parameters\n'
                 '    ----------\n'
                 '    x : float\n'
                 '        The value.\n'
                 '    """\n')
BAD_SECTION_NAME = ('def plot(x):\n'
                    '    """Draw a line.\n'
                    '\n'
                    '    Arguments\n'
                    '    ---------\n'
                    '    x : float\n'
                    '        The value.\n'
                    '    """\n')


def test_c023_passes_for_a_well_formed_numpydoc_docstring(corpus):
    assert one("MATPLOTLIB-C023", [whole(LIB, GOOD_NUMPYDOC)], corpus).verdict == "pass"


def test_c023_fails_for_a_section_name_numpydoc_does_not_define(corpus):
    assert one("MATPLOTLIB-C023", [whole(LIB, BAD_SECTION_NAME)], corpus).verdict == "fail"


def test_c023_finds_no_target_for_a_docstring_with_no_sections(corpus):
    assert no_target(one("MATPLOTLIB-C023",
                         [whole(LIB, 'def plot(x):\n    """Draw a line."""\n')], corpus))


# --- C025/C158 where new API documentation goes -------------------------------------------------


NEW_PUBLIC = whole(LIB, 'def draw_ribbon(x):\n    """Draw a ribbon."""\n    return x\n')
NEW_MODULE = whole("lib/matplotlib/ribbon.py", '"""Ribbons."""\n', is_new=True)
NEW_API_PAGE = page("Ribbon\n======\n", "doc/api/ribbon_api.rst", is_new=True)


def test_c025_passes_when_the_new_api_is_documented_in_docstrings(corpus):
    assert one("MATPLOTLIB-C025", [NEW_PUBLIC], corpus).verdict == "pass"


def test_c025_fails_when_a_new_doc_api_page_carries_the_reference(corpus):
    assert one("MATPLOTLIB-C025", [NEW_PUBLIC, NEW_API_PAGE], corpus).verdict == "fail"


def test_c025_finds_no_target_for_a_new_module_which_is_left_to_c158(corpus):
    """The §7.5 half: a new module needs an API page, which is C158's sentence."""
    assert no_target(one("MATPLOTLIB-C025", [NEW_MODULE, NEW_API_PAGE], corpus))


def test_c158_passes_when_a_new_module_gets_an_api_page(corpus):
    assert one("MATPLOTLIB-C158", [NEW_MODULE, NEW_API_PAGE], corpus).verdict == "pass"


def test_c158_fails_when_a_new_module_gets_none(corpus):
    assert one("MATPLOTLIB-C158", [NEW_MODULE], corpus).verdict == "fail"


def test_c158_finds_no_target_when_no_module_is_added(corpus):
    assert no_target(one("MATPLOTLIB-C158", [NEW_PUBLIC], corpus))


# --- C026/C027 quote positions -------------------------------------------------------------------


def test_c026_passes_for_a_one_line_docstring(corpus):
    assert one("MATPLOTLIB-C026", [whole(LIB, 'def f():\n    """Do it."""\n')],
               corpus).verdict == "pass"


def test_c026_fails_when_a_one_line_docstring_is_spread_over_lines(corpus):
    body = 'def f():\n    """\n    Do it.\n    """\n'
    assert one("MATPLOTLIB-C026", [whole(LIB, body)], corpus).verdict == "fail"


def test_c026_finds_no_target_for_a_multi_line_docstring(corpus):
    body = 'def f():\n    """Do it.\n\n    More.\n    """\n'
    assert no_target(one("MATPLOTLIB-C026", [whole(LIB, body)], corpus))


def test_c027_passes_when_both_quotes_are_alone(corpus):
    body = 'def f():\n    """\n    Do it.\n\n    More.\n    """\n'
    assert one("MATPLOTLIB-C027", [whole(LIB, body)], corpus).verdict == "pass"


def test_c027_fails_when_the_text_starts_on_the_opening_line(corpus):
    body = 'def f():\n    """Do it.\n\n    More.\n    """\n'
    assert one("MATPLOTLIB-C027", [whole(LIB, body)], corpus).verdict == "fail"


def test_c027_finds_no_target_for_a_single_line_docstring(corpus):
    assert no_target(one("MATPLOTLIB-C027", [whole(LIB, 'def f():\n    """Do it."""\n')],
                         corpus))


# --- C029--C042 type descriptions ------------------------------------------------------------------


def documented(*entries: str, section: str = "Parameters", signature: str = "def f(x=1):",
               raw: bool = False):
    """A function whose docstring documents ``entries`` under one numpydoc section.

    ``raw`` opens the docstring with ``r\"\"\"``, which is what a wrapped parameter list
    needs: in an ordinary docstring Python eats the trailing backslash and joins the two
    lines before the checker ever sees them.
    """
    body = [signature, ('    r"""Summary.' if raw else '    """Summary.'), '',
            f'    {section}', '    ' + "-" * len(section)]
    body += [f"    {entry}" for entry in entries]
    body += ['    """', '    return x']
    return whole(LIB, "\n".join(body) + "\n")


def test_c029_passes_for_plain_quotes(corpus):
    files = [documented("x : {'a', 'b'}", "    The mode.")]
    assert one("MATPLOTLIB-C029", files, corpus).verdict == "pass"


def test_c029_fails_for_a_literal_wrapped_string(corpus):
    files = [documented("x : ``'a'`` or ``'b'``", "    The mode.")]
    assert one("MATPLOTLIB-C029", files, corpus).verdict == "fail"


def test_c029_finds_no_target_when_no_string_value_is_given(corpus):
    assert no_target(one("MATPLOTLIB-C029", [documented("x : float", "    The value.")],
                         corpus))


def test_c030_passes_for_a_prose_type(corpus):
    assert one("MATPLOTLIB-C030", [documented("x : float", "    The value.")],
               corpus).verdict == "pass"


def test_c030_fails_for_annotation_syntax(corpus):
    assert one("MATPLOTLIB-C030", [documented("x : Optional[float]", "    The value.")],
               corpus).verdict == "fail"


def test_c030_finds_no_target_when_no_parameters_are_documented(corpus):
    assert no_target(one("MATPLOTLIB-C030",
                         [whole(LIB, 'def f():\n    """Summary."""\n')], corpus))


def test_c031_passes_when_a_number_is_described_as_float(corpus):
    assert one("MATPLOTLIB-C031", [documented("x : float", "    The value.")],
               corpus).verdict == "pass"


def test_c031_fails_when_it_is_described_as_int(corpus):
    assert one("MATPLOTLIB-C031", [documented("x : int", "    The value.")],
               corpus).verdict == "fail"


def test_c031_finds_no_target_for_a_non_numeric_type(corpus):
    assert no_target(one("MATPLOTLIB-C031", [documented("x : str", "    The label.")],
                         corpus))


def test_c032_passes_for_the_parenthesised_form(corpus):
    assert one("MATPLOTLIB-C032",
               [documented("xy : (float, float)", "    The position.")],
               corpus).verdict == "pass"


def test_c032_fails_without_the_parentheses(corpus):
    assert one("MATPLOTLIB-C032",
               [documented("xy : 2-tuple of float", "    The position.")],
               corpus).verdict == "fail"


def test_c032_finds_no_target_for_a_scalar_parameter(corpus):
    assert no_target(one("MATPLOTLIB-C032", [documented("x : float", "    The value.")],
                         corpus))


def test_c033_passes_for_array_like(corpus):
    assert one("MATPLOTLIB-C033", [documented("x : array-like", "    The values.")],
               corpus).verdict == "pass"


def test_c033_fails_for_a_bare_ndarray(corpus):
    assert one("MATPLOTLIB-C033", [documented("x : ndarray", "    The values.")],
               corpus).verdict == "fail"


def test_c033_finds_no_target_for_a_returns_entry_left_to_c034(corpus):
    """The §7.5 half: return types are C034's, and C033 reads Parameters only."""
    assert no_target(one("MATPLOTLIB-C033",
                         [documented("out : array-like", "    The values.",
                                     section="Returns")], corpus))


def test_c034_passes_when_a_returned_array_is_called_array(corpus):
    assert one("MATPLOTLIB-C034",
               [documented("out : array", "    The values.", section="Returns")],
               corpus).verdict == "pass"


def test_c034_fails_when_a_returned_array_is_called_array_like(corpus):
    assert one("MATPLOTLIB-C034",
               [documented("out : array-like", "    The values.", section="Returns")],
               corpus).verdict == "fail"


def test_c034_finds_no_target_for_a_parameters_entry(corpus):
    assert no_target(one("MATPLOTLIB-C034",
                         [documented("x : array-like", "    The values.")], corpus))


def test_c035_passes_when_the_dtype_is_spelt_out(corpus):
    assert one("MATPLOTLIB-C035",
               [documented("x : array-like of int", "    The values.")],
               corpus).verdict == "pass"


def test_c035_fails_when_the_dtype_is_not_spelt_out(corpus):
    assert one("MATPLOTLIB-C035", [documented("x : list of int", "    The values.")],
               corpus).verdict == "fail"


def test_c035_finds_no_target_for_a_float_sequence(corpus):
    assert no_target(one("MATPLOTLIB-C035",
                         [documented("x : array-like of float", "    The values.")],
                         corpus))


def test_c036_passes_for_list_of_type(corpus):
    assert one("MATPLOTLIB-C036", [documented("labels : list of str", "    The labels.")],
               corpus).verdict == "pass"


def test_c036_fails_for_another_sequence_word(corpus):
    assert one("MATPLOTLIB-C036",
               [documented("labels : sequence of str", "    The labels.")],
               corpus).verdict == "fail"


def test_c036_finds_no_target_for_a_numeric_sequence(corpus):
    assert no_target(one("MATPLOTLIB-C036",
                         [documented("x : array-like of float", "    The values.")],
                         corpus))


def test_c037_passes_for_a_full_reference_with_a_tilde(corpus):
    assert one("MATPLOTLIB-C037",
               [documented("ax : :class:`~matplotlib.axes.Axes`", "    The Axes.")],
               corpus).verdict == "pass"


def test_c037_fails_for_a_bare_reference(corpus):
    assert one("MATPLOTLIB-C037", [documented("ax : :class:`Axes`", "    The Axes.")],
               corpus).verdict == "fail"


def test_c037_finds_no_target_when_the_type_carries_no_reference(corpus):
    assert no_target(one("MATPLOTLIB-C037", [documented("x : float", "    The value.")],
                         corpus))


ABBREVIATED_IN_TEXT = ('def f(x=1):\n'
                       '    """Summary.\n'
                       '\n'
                       '    See :meth:`~.Axes.plot` for details.\n'
                       '    """\n'
                       '    return x\n')
FULL_IN_TEXT = ('def f(x=1):\n'
                '    """Summary.\n'
                '\n'
                '    See :meth:`matplotlib.axes.Axes.plot` for details.\n'
                '    """\n'
                '    return x\n')


def test_c038_passes_for_the_abbreviated_dotted_form(corpus):
    assert one("MATPLOTLIB-C038", [whole(LIB, ABBREVIATED_IN_TEXT)],
               corpus).verdict == "pass"


def test_c038_fails_for_a_full_in_text_reference(corpus):
    assert one("MATPLOTLIB-C038", [whole(LIB, FULL_IN_TEXT)], corpus).verdict == "fail"


def test_c038_finds_no_target_when_the_prose_carries_no_reference(corpus):
    assert no_target(one("MATPLOTLIB-C038",
                         [whole(LIB, 'def f():\n    """Summary."""\n')], corpus))


def test_c039_passes_for_the_stated_default_form(corpus):
    files = [documented("x : float, default: 1", "    The value.")]
    assert one("MATPLOTLIB-C039", files, corpus).verdict == "pass"


def test_c039_fails_when_the_default_is_left_out_of_the_type_line(corpus):
    assert one("MATPLOTLIB-C039", [documented("x : float", "    The value.")],
               corpus).verdict == "fail"


def test_c039_finds_no_target_for_a_none_default_left_to_c041(corpus):
    """The §7.5 half: a None default is C041's question, not this rule's."""
    files = [documented("x : float", "    The value.", signature="def f(x=None):")]
    assert no_target(one("MATPLOTLIB-C039", files, corpus))


def test_c041_passes_when_none_is_explained(corpus):
    files = [documented("x : float, default: None",
                        "    The value. None means the Axes limits are used.",
                        signature="def f(x=None):")]
    assert one("MATPLOTLIB-C041", files, corpus).verdict == "pass"


def test_c041_fails_when_none_is_only_a_sentinel(corpus):
    files = [documented("x : float, default: None", "    The value.",
                        signature="def f(x=None):")]
    assert one("MATPLOTLIB-C041", files, corpus).verdict == "fail"


def test_c041_finds_no_target_for_an_ordinary_default(corpus):
    assert no_target(one("MATPLOTLIB-C041",
                         [documented("x : float, default: 1", "    The value.")], corpus))


LONG_TYPE = "x : " + "a very long type description " * 4
WRAPPED = LONG_TYPE.rstrip() + " \\"


def test_c042_passes_for_a_backslash_continuation(corpus):
    files = [documented(WRAPPED, "or something else", "    The value.", raw=True)]
    assert one("MATPLOTLIB-C042", files, corpus).verdict == "pass"


def test_c042_fails_for_an_unwrapped_long_line(corpus):
    assert one("MATPLOTLIB-C042", [documented(LONG_TYPE, "    The value.")],
               corpus).verdict == "fail"


def test_c042_finds_no_target_for_a_short_type_line(corpus):
    assert no_target(one("MATPLOTLIB-C042", [documented("x : float", "    The value.")],
                         corpus))


# --- C043 rcParams -------------------------------------------------------------------------------


def test_c043_passes_for_the_rc_role(corpus):
    assert one("MATPLOTLIB-C043", [page("Set :rc:`lines.linewidth` to widen it.\n")],
               corpus).verdict == "pass"


def test_c043_fails_for_a_bare_key(corpus):
    assert one("MATPLOTLIB-C043", [page("Set lines.linewidth to widen it.\n")],
               corpus).verdict == "fail"


def test_c043_finds_no_target_when_no_rcparam_is_named(corpus):
    assert no_target(one("MATPLOTLIB-C043", [page("Widen the line by hand.\n")], corpus))


# --- C045/C047/C145 methods and their docstrings -------------------------------------------------


SETTER_OK = ('class Line:\n'
             '    def set_width(self, w):\n'
             '        """Set the width.\n'
             '\n'
             '        Parameters\n'
             '        ----------\n'
             '        w : float\n'
             '            The width.\n'
             '        """\n')
SETTER_BAD = ('class Line:\n'
              '    def set_width(self, w):\n'
              '        """Set the width."""\n')


def test_c045_passes_when_the_setter_documents_its_parameters(corpus):
    assert one("MATPLOTLIB-C045", [whole(LIB, SETTER_OK, is_new=True)],
               corpus).verdict == "pass"


def test_c045_fails_when_it_documents_neither_parameters_nor_accepts(corpus):
    assert one("MATPLOTLIB-C045", [whole(LIB, SETTER_BAD, is_new=True)],
               corpus).verdict == "fail"


def test_c045_finds_no_target_for_a_getter(corpus):
    body = 'class Line:\n    def get_width(self):\n        """Return the width."""\n'
    assert no_target(one("MATPLOTLIB-C045", [whole(LIB, body, is_new=True)], corpus))


INHERITED = ('class Line:\n'
             '    def draw(self, renderer):\n'
             '        # docstring inherited\n'
             '        return renderer\n')
UNDOCUMENTED = 'class Line:\n    def draw(self, renderer):\n        return renderer\n'
DOCUMENTED = ('class Line:\n'
              '    def draw(self, renderer):\n'
              '        """Draw the line onto the renderer."""\n'
              '        return renderer\n')


def test_c047_passes_for_the_inherited_marker(corpus):
    assert one("MATPLOTLIB-C047", [whole(LIB, INHERITED, is_new=True)],
               corpus).verdict == "pass"


def test_c047_fails_when_nothing_says_the_absence_is_deliberate(corpus):
    assert one("MATPLOTLIB-C047", [whole(LIB, UNDOCUMENTED, is_new=True)],
               corpus).verdict == "fail"


def test_c047_finds_no_target_for_a_documented_method(corpus):
    assert no_target(one("MATPLOTLIB-C047", [whole(LIB, DOCUMENTED, is_new=True)], corpus))


def test_c145_passes_for_a_documented_public_method(corpus):
    assert one("MATPLOTLIB-C145", [whole(LIB, DOCUMENTED, is_new=True)],
               corpus).verdict == "pass"


def test_c145_passes_for_a_deliberately_inherited_docstring(corpus):
    """The §7.5 resolution: C047's marker satisfies this rule instead of failing it."""
    assert one("MATPLOTLIB-C145", [whole(LIB, INHERITED, is_new=True)],
               corpus).verdict == "pass"


def test_c145_fails_for_an_undocumented_public_method(corpus):
    assert one("MATPLOTLIB-C145", [whole(LIB, UNDOCUMENTED, is_new=True)],
               corpus).verdict == "fail"


def test_c145_finds_no_target_for_a_private_method(corpus):
    body = 'class Line:\n    def _draw(self, renderer):\n        return renderer\n'
    assert no_target(one("MATPLOTLIB-C145", [whole(LIB, body, is_new=True)], corpus))


# --- C159 examples in plotting docstrings ----------------------------------------------------------


WITH_EXAMPLE = ('class Axes:\n'
                '    def ribbon(self, x):\n'
                '        """Draw a ribbon.\n'
                '\n'
                '        Examples\n'
                '        --------\n'
                '        >>> ax.ribbon([1, 2])\n'
                '        """\n')
WITHOUT_EXAMPLE = ('class Axes:\n'
                   '    def ribbon(self, x):\n'
                   '        """Draw a ribbon."""\n')


def test_c159_passes_when_the_docstring_carries_an_example(corpus):
    assert one("MATPLOTLIB-C159", [whole(LIB, WITH_EXAMPLE, is_new=True)],
               corpus).verdict == "pass"


def test_c159_fails_when_it_carries_none(corpus):
    assert one("MATPLOTLIB-C159", [whole(LIB, WITHOUT_EXAMPLE, is_new=True)],
               corpus).verdict == "fail"


def test_c159_finds_no_target_outside_the_plotting_modules(corpus):
    assert no_target(one("MATPLOTLIB-C159",
                         [whole("lib/matplotlib/colors.py", WITHOUT_EXAMPLE, is_new=True)],
                         corpus))


# --- C219--C224 versioning directives ----------------------------------------------------------


REMOVED_PUBLIC = make_file(LIB, [(1, "x = 1")], head_text="x = 1\n",
                           removed_lines=("def old_thing(self):", "    return 1"))
VERSIONED_PAGE = page("Changes\n=======\n\nA change.\n\n.. versionchanged:: 3.9\n")


def test_c219_passes_when_a_versioning_directive_accompanies_the_change(corpus):
    assert one("MATPLOTLIB-C219", [REMOVED_PUBLIC, VERSIONED_PAGE],
               corpus).verdict == "pass"


def test_c219_fails_when_no_directive_is_added(corpus):
    assert one("MATPLOTLIB-C219", [REMOVED_PUBLIC], corpus).verdict == "fail"


def test_c219_finds_no_target_for_a_compatible_change(corpus):
    assert no_target(one("MATPLOTLIB-C219", [whole(LIB, "x = 1\n")], corpus))


def test_c221_passes_when_the_directive_ends_its_block(corpus):
    assert one("MATPLOTLIB-C221", [VERSIONED_PAGE], corpus).verdict == "pass"


def test_c221_fails_when_prose_follows_it(corpus):
    body = "Changes\n=======\n\n.. versionchanged:: 3.9\n\nAnd more prose after it.\n"
    assert one("MATPLOTLIB-C221", [page(body)], corpus).verdict == "fail"


def test_c221_finds_no_target_for_a_docstring_directive_left_to_c222(corpus):
    """The §7.5 half: a directive inside a docstring is C222's or C223's, not C221's."""
    body = ('def f(x=1):\n'
            '    """Summary.\n'
            '\n'
            '    .. versionadded:: 3.9\n'
            '    """\n'
            '    return x\n')
    assert no_target(one("MATPLOTLIB-C221", [whole(LIB, body)], corpus))


BEFORE_PARAMS = ('def f(x=1):\n'
                 '    """Summary.\n'
                 '\n'
                 '    .. versionadded:: 3.9\n'
                 '\n'
                 '    Parameters\n'
                 '    ----------\n'
                 '    x : float\n'
                 '        The value.\n'
                 '    """\n'
                 '    return x\n')
AFTER_PARAMS = ('def f(x=1):\n'
                '    """Summary.\n'
                '\n'
                '    Parameters\n'
                '    ----------\n'
                '    x : float\n'
                '        The value.\n'
                '\n'
                '    Notes\n'
                '    -----\n'
                '    .. versionadded:: 3.9\n'
                '    """\n'
                '    return x\n')


def test_c222_passes_when_the_directive_precedes_the_parameters(corpus):
    assert one("MATPLOTLIB-C222", [whole(LIB, BEFORE_PARAMS)], corpus).verdict == "pass"


def test_c222_fails_when_it_follows_them(corpus):
    assert one("MATPLOTLIB-C222", [whole(LIB, AFTER_PARAMS)], corpus).verdict == "fail"


def test_c222_finds_no_target_for_a_docstring_with_no_parameters(corpus):
    body = 'def f():\n    """Summary.\n\n    .. versionadded:: 3.9\n    """\n'
    assert no_target(one("MATPLOTLIB-C222", [whole(LIB, body)], corpus))


PARAM_DIRECTIVE_LAST = ('def f(x=1):\n'
                        '    """Summary.\n'
                        '\n'
                        '    Parameters\n'
                        '    ----------\n'
                        '    x : float\n'
                        '        The value.\n'
                        '\n'
                        '        .. versionadded:: 3.9\n'
                        '    """\n'
                        '    return x\n')
PARAM_DIRECTIVE_EARLY = ('def f(x=1):\n'
                         '    """Summary.\n'
                         '\n'
                         '    Parameters\n'
                         '    ----------\n'
                         '    x : float\n'
                         '        .. versionadded:: 3.9\n'
                         '\n'
                         '        The value.\n'
                         '    """\n'
                         '    return x\n')


def test_c223_passes_when_the_directive_ends_the_description(corpus):
    assert one("MATPLOTLIB-C223", [whole(LIB, PARAM_DIRECTIVE_LAST)],
               corpus).verdict == "pass"


def test_c223_fails_when_description_follows_it(corpus):
    assert one("MATPLOTLIB-C223", [whole(LIB, PARAM_DIRECTIVE_EARLY)],
               corpus).verdict == "fail"


def test_c223_finds_no_target_for_a_directive_outside_the_parameters(corpus):
    assert no_target(one("MATPLOTLIB-C223", [whole(LIB, BEFORE_PARAMS)], corpus))


def test_c224_passes_for_a_two_component_version(corpus):
    assert one("MATPLOTLIB-C224", [whole(LIB, BEFORE_PARAMS)], corpus).verdict == "pass"


def test_c224_fails_when_the_micro_version_is_given(corpus):
    body = BEFORE_PARAMS.replace("3.9", "3.9.1")
    assert one("MATPLOTLIB-C224", [whole(LIB, body)], corpus).verdict == "fail"


def test_c224_fails_when_a_module_docstring_carries_one(corpus):
    body = '"""Module summary.\n\n.. versionadded:: 3.9\n"""\n'
    assert one("MATPLOTLIB-C224", [whole(LIB, body)], corpus).verdict == "fail"


def test_c224_finds_no_target_when_no_directive_is_written(corpus):
    assert no_target(one("MATPLOTLIB-C224", [whole(LIB, "x = 1\n")], corpus))


# --- C233/C234 discouraged API ---------------------------------------------------------------------


DISCOURAGED_BOTH = ('def old_way(x):\n'
                    '    """[*Discouraged*] Do it the old way.\n'
                    '\n'
                    '    .. admonition:: Discouraged\n'
                    '\n'
                    '       Use the new way instead.\n'
                    '    """\n'
                    '    return x\n')
DISCOURAGED_PROSE = ('def old_way(x):\n'
                     '    """Do it the old way.\n'
                     '\n'
                     '    This function is discouraged; use the new way.\n'
                     '    """\n'
                     '    return x\n')


def test_c233_passes_for_a_discouraged_admonition(corpus):
    assert one("MATPLOTLIB-C233", [whole(LIB, DISCOURAGED_BOTH)], corpus).verdict == "pass"


def test_c233_fails_when_only_the_prose_says_so(corpus):
    assert one("MATPLOTLIB-C233", [whole(LIB, DISCOURAGED_PROSE)], corpus).verdict == "fail"


def test_c233_finds_no_target_for_ordinary_api(corpus):
    assert no_target(one("MATPLOTLIB-C233",
                         [whole(LIB, 'def f(x):\n    """Do it."""\n    return x\n')],
                         corpus))


def test_c234_passes_for_the_summary_prefix(corpus):
    assert one("MATPLOTLIB-C234", [whole(LIB, DISCOURAGED_BOTH)], corpus).verdict == "pass"


def test_c234_fails_when_the_summary_carries_no_prefix(corpus):
    assert one("MATPLOTLIB-C234", [whole(LIB, DISCOURAGED_PROSE)], corpus).verdict == "fail"


def test_c234_finds_no_target_for_ordinary_api(corpus):
    assert no_target(one("MATPLOTLIB-C234",
                         [whole(LIB, 'def f(x):\n    """Do it."""\n    return x\n')],
                         corpus))


# --- C248 C/C++ header documentation ------------------------------------------------------------------


NUMPYDOC_HEADER = ("/*\n"
                   " * Draw a path.\n"
                   " *\n"
                   " * Parameters\n"
                   " * ----------\n"
                   " * path : the path to draw\n"
                   " */\n"
                   "void draw(void);\n")
PLAIN_HEADER = ("/*\n"
                " * Draw a path.\n"
                " * @param path the path to draw\n"
                " */\n"
                "void draw(void);\n")


def test_c248_passes_for_a_numpydoc_header_block(corpus):
    assert one("MATPLOTLIB-C248", [whole("src/_path.h", NUMPYDOC_HEADER)],
               corpus).verdict == "pass"


def test_c248_fails_for_a_doxygen_style_block(corpus):
    assert one("MATPLOTLIB-C248", [whole("src/_path.h", PLAIN_HEADER)],
               corpus).verdict == "fail"


def test_c248_finds_no_target_for_a_header_with_no_documentation(corpus):
    assert no_target(one("MATPLOTLIB-C248", [whole("src/_path.h", "void draw(void);\n")],
                         corpus))


# --- C049--C075 gallery examples and plot types ----------------------------------------------------


PLOTTING = ('"""\n'
            '===========\n'
            'Simple plot\n'
            '===========\n'
            '\n'
            'A simple line.\n'
            '"""\n'
            'import matplotlib.pyplot as plt\n'
            '\n'
            'fig, ax = plt.subplots()\n'
            'ax.plot([1, 2])\n'
            'plt.show()\n')
NO_PLOT = ('"""\n'
           '========\n'
           'Overview\n'
           '========\n'
           '\n'
           'Explains something.\n'
           '"""\n'
           'x = 1\n')


def test_c049_passes_when_a_plotless_example_is_named_sgskip(corpus):
    files = [example(NO_PLOT, "galleries/examples/misc/overview_sgskip.py", is_new=True)]
    assert one("MATPLOTLIB-C049", files, corpus).verdict == "pass"


def test_c049_fails_when_it_is_not(corpus):
    assert one("MATPLOTLIB-C049", [example(NO_PLOT, is_new=True)], corpus).verdict == "fail"


def test_c049_finds_no_target_for_an_example_that_plots_left_to_c137(corpus):
    """The §7.5 half: an example that draws is C137's, and must end with show()."""
    assert no_target(one("MATPLOTLIB-C049", [example(PLOTTING, is_new=True)], corpus))


SEPARATED = PLOTTING + "\n# %%\n# Now widen the line.\n# The width is set below.\nax.plot([2, 3])\n"
UNSEPARATED = PLOTTING + "\n# Now widen the line.\n# The width is set below.\nax.plot([2, 3])\n"


def test_c050_passes_when_narrative_blocks_open_with_the_separator(corpus):
    assert one("MATPLOTLIB-C050", [example(SEPARATED)], corpus).verdict == "pass"


def test_c050_fails_when_they_do_not(corpus):
    assert one("MATPLOTLIB-C050", [example(UNSEPARATED)], corpus).verdict == "fail"


def test_c050_finds_no_target_for_an_example_with_no_narrative_blocks(corpus):
    assert no_target(one("MATPLOTLIB-C050", [example(PLOTTING)], corpus))


CITED = PLOTTING.replace("A simple line.",
                         "A simple line. Data from https://example.org/dataset.") \
    + "data = cbook.get_sample_data('goog.npz')\n"
UNCITED = PLOTTING + "data = cbook.get_sample_data('goog.npz')\n"


def test_c051_passes_when_the_dataset_is_cited(corpus):
    assert one("MATPLOTLIB-C051", [example(CITED)], corpus).verdict == "pass"


def test_c051_fails_when_it_is_not(corpus):
    assert one("MATPLOTLIB-C051", [example(UNCITED)], corpus).verdict == "fail"


def test_c051_finds_no_target_for_an_example_that_loads_no_dataset(corpus):
    assert no_target(one("MATPLOTLIB-C051", [example(PLOTTING)], corpus))


INLINE_DATA = PLOTTING + "import numpy as np\nvalues = np.array([1, 2, 3])\n"


def test_c052_passes_when_the_data_is_written_out(corpus):
    assert one("MATPLOTLIB-C052", [example(INLINE_DATA)], corpus).verdict == "pass"


def test_c052_fails_when_it_reaches_for_get_sample_data(corpus):
    assert one("MATPLOTLIB-C052", [example(UNCITED)], corpus).verdict == "fail"


def test_c052_finds_no_target_for_an_example_that_supplies_no_data(corpus):
    assert no_target(one("MATPLOTLIB-C052", [example(PLOTTING)], corpus))


def test_c053_passes_when_large_data_goes_in_the_sample_data_directory(corpus):
    files = [whole("lib/matplotlib/mpl-data/sample_data/goog.npz", "binary\n", is_new=True)]
    assert one("MATPLOTLIB-C053", files, corpus).verdict == "pass"


def test_c053_fails_when_it_ships_beside_the_example(corpus):
    files = [whole("galleries/examples/misc/goog.npz", "binary\n", is_new=True)]
    assert one("MATPLOTLIB-C053", files, corpus).verdict == "fail"


def test_c053_finds_no_target_when_no_data_file_is_added(corpus):
    assert no_target(one("MATPLOTLIB-C053", [example(PLOTTING, is_new=True)], corpus))


REFERENCED = PLOTTING + (
    "\n# %%\n"
    "# .. admonition:: References\n"
    "#\n"
    "#    - `matplotlib.axes.Axes.plot`\n"
    "#    - `matplotlib.pyplot.plot`\n")
REFERENCED_ONE_SIDE = PLOTTING + (
    "\n# %%\n"
    "# .. admonition:: References\n"
    "#\n"
    "#    - `matplotlib.pyplot.plot`\n")


def test_c054_passes_for_a_references_admonition(corpus):
    assert one("MATPLOTLIB-C054", [example(REFERENCED, is_new=True)],
               corpus).verdict == "pass"


def test_c054_fails_when_the_example_lists_nothing(corpus):
    assert one("MATPLOTLIB-C054", [example(PLOTTING, is_new=True)], corpus).verdict == "fail"


def test_c054_finds_no_target_for_a_pre_existing_example(corpus):
    lines = PLOTTING.split("\n")
    edited = make_file(EXAMPLE, [(11, lines[10])], head_text=PLOTTING)
    assert no_target(one("MATPLOTLIB-C054", [edited], corpus))


def test_c056_passes_when_both_references_are_listed_pyplot_second(corpus):
    assert one("MATPLOTLIB-C056", [example(REFERENCED)], corpus).verdict == "pass"


def test_c056_fails_when_only_the_pyplot_reference_is_listed(corpus):
    assert one("MATPLOTLIB-C056", [example(REFERENCED_ONE_SIDE)], corpus).verdict == "fail"


def test_c056_finds_no_target_without_the_admonition_c054_asks_for(corpus):
    """The §7.5 half: a missing References block is C054's finding."""
    assert no_target(one("MATPLOTLIB-C056", [example(PLOTTING)], corpus))


ORDER_EXPLICIT = whole("galleries/examples/lines_bars/gallery_order.txt",
                       "plot_simple.py\nplot_other.py\n")
ORDER_WITH_STAR = whole("galleries/examples/lines_bars/gallery_order.txt",
                        "plot_other.py\n*\n")


def test_c057_passes_when_the_example_is_listed(corpus):
    assert one("MATPLOTLIB-C057", [example(PLOTTING, is_new=True), ORDER_EXPLICIT],
               corpus).verdict == "pass"


def test_c057_fails_when_it_is_missing_from_an_explicit_order(corpus):
    other = example(PLOTTING, "galleries/examples/lines_bars/plot_new.py", is_new=True)
    assert one("MATPLOTLIB-C057", [other, ORDER_EXPLICIT], corpus).verdict == "fail"


def test_c057_finds_no_target_when_the_order_file_has_a_placeholder(corpus):
    assert no_target(one("MATPLOTLIB-C057",
                         [example(PLOTTING, is_new=True), ORDER_WITH_STAR], corpus))


RAW_RST = whole("galleries/examples/lines_bars/notes.rst", "Notes\n=====\n", is_new=True)
TOCTREE = page(".. toctree::\n\n   notes\n", "doc/users/index.rst")


def test_c058_passes_when_a_toctree_lists_the_page(corpus):
    files = [example(PLOTTING, is_new=True), RAW_RST, TOCTREE]
    assert one("MATPLOTLIB-C058", files, corpus).verdict == "pass"


def test_c058_fails_when_nothing_lists_it(corpus):
    files = [example(PLOTTING, is_new=True), RAW_RST]
    assert one("MATPLOTLIB-C058", files, corpus).verdict == "fail"


def test_c058_finds_no_target_when_no_raw_rst_is_added(corpus):
    assert no_target(one("MATPLOTLIB-C058", [example(PLOTTING, is_new=True)], corpus))


DEMO_TITLE = PLOTTING.replace("Simple plot", "Line demo ")


def test_c062_passes_for_a_title_without_demo(corpus):
    assert one("MATPLOTLIB-C062", [example(PLOTTING)], corpus).verdict == "pass"


def test_c062_fails_for_a_title_with_demo(corpus):
    assert one("MATPLOTLIB-C062", [example(DEMO_TITLE)], corpus).verdict == "fail"


def test_c064_finds_no_target_for_a_title_that_needs_no_verb_either(corpus):
    assert no_target(one("MATPLOTLIB-C064", [example(titled("Bar chart"))], corpus))


def test_c062_finds_no_target_for_an_example_with_no_title(corpus):
    assert no_target(one("MATPLOTLIB-C062", [example("x = 1\n")], corpus))


def titled(title: str, rest: str = "A simple line."):
    """A gallery example whose reST title is ``title``, over- and underlined to match."""
    rule = "=" * len(title)
    return ('"""\n' + rule + "\n" + title + "\n" + rule + "\n\n" + rest + '\n"""\n'
            "import matplotlib.pyplot as plt\n"
            "\nfig, ax = plt.subplots()\nax.plot([1, 2])\nplt.show()\n")


def test_c064_passes_for_a_simple_present_verb(corpus):
    assert one("MATPLOTLIB-C064", [example(titled("Draw a line"))],
               corpus).verdict == "pass"


def test_c064_fails_for_a_gerund(corpus):
    assert one("MATPLOTLIB-C064", [example(titled("Drawing a line"))],
               corpus).verdict == "fail"


def test_c064_finds_no_target_for_a_title_that_needs_no_verb(corpus):
    assert no_target(one("MATPLOTLIB-C064", [example(PLOTTING)], corpus))


def test_c070_passes_for_a_figure_within_the_width_limit(corpus):
    body = PLOTTING.replace("plt.subplots()", "plt.subplots(figsize=(6, 4))")
    assert one("MATPLOTLIB-C070", [example(body)], corpus).verdict == "pass"


def test_c070_fails_for_a_figure_over_it(corpus):
    body = PLOTTING.replace("plt.subplots()", "plt.subplots(figsize=(16, 4))")
    assert one("MATPLOTLIB-C070", [example(body)], corpus).verdict == "fail"


def test_c070_finds_no_target_when_the_example_sets_no_figure_size(corpus):
    assert no_target(one("MATPLOTLIB-C070", [example(PLOTTING)], corpus))


PLOT_TYPE_ENTRY = ('"""\n'
                   '===============\n'
                   'plot(x, y)\n'
                   '===============\n'
                   '\n'
                   'See `~matplotlib.axes.Axes.plot`.\n'
                   '"""\n'
                   'import matplotlib.pyplot as plt\n'
                   "plt.style.use('_mpl-gallery')\n"
                   'fig, ax = plt.subplots()\n'
                   'ax.plot([1, 2], [3, 4])\n'
                   'plt.show()\n')


def test_c072_passes_for_a_signature_title(corpus):
    assert one("MATPLOTLIB-C072", [example(PLOT_TYPE_ENTRY, PLOT_TYPE)],
               corpus).verdict == "pass"


def test_c072_fails_for_a_prose_title(corpus):
    body = PLOT_TYPE_ENTRY.replace("plot(x, y)", "Line plots")
    assert one("MATPLOTLIB-C072", [example(body, PLOT_TYPE)], corpus).verdict == "fail"


def test_c072_finds_no_target_for_a_gallery_example(corpus):
    assert no_target(one("MATPLOTLIB-C072", [example(PLOTTING)], corpus))


def test_c073_passes_for_one_sentence_with_a_link(corpus):
    assert one("MATPLOTLIB-C073", [example(PLOT_TYPE_ENTRY, PLOT_TYPE)],
               corpus).verdict == "pass"


def test_c073_fails_for_two_sentences(corpus):
    body = PLOT_TYPE_ENTRY.replace("See `~matplotlib.axes.Axes.plot`.",
                                   "See `~matplotlib.axes.Axes.plot`. It draws lines.")
    assert one("MATPLOTLIB-C073", [example(body, PLOT_TYPE)], corpus).verdict == "fail"


def test_c073_finds_no_target_for_an_entry_with_no_description(corpus):
    body = '"""\n==========\nplot(x, y)\n==========\n"""\nx = 1\n'
    assert no_target(one("MATPLOTLIB-C073", [example(body, PLOT_TYPE)], corpus))


def test_c075_passes_when_the_gallery_stylesheet_is_used(corpus):
    assert one("MATPLOTLIB-C075", [example(PLOT_TYPE_ENTRY, PLOT_TYPE)],
               corpus).verdict == "pass"


def test_c075_fails_when_it_is_not(corpus):
    body = PLOT_TYPE_ENTRY.replace("plt.style.use('_mpl-gallery')\n", "")
    assert one("MATPLOTLIB-C075", [example(body, PLOT_TYPE)], corpus).verdict == "fail"


def test_c075_finds_no_target_for_a_gallery_example(corpus):
    assert no_target(one("MATPLOTLIB-C075", [example(PLOTTING)], corpus))


# --- C126--C142 expository language and formatting ---------------------------------------------------


def test_c126_passes_for_an_imperative_heading(corpus):
    assert one("MATPLOTLIB-C126", [page("Write documentation\n"
                                        "===================\n")],
               corpus).verdict == "pass"


def test_c126_fails_for_a_gerund_heading(corpus):
    assert one("MATPLOTLIB-C126", [page("Writing documentation\n"
                                        "=====================\n")],
               corpus).verdict == "fail"


def test_c126_finds_no_target_for_a_noun_phrase_heading(corpus):
    assert no_target(one("MATPLOTLIB-C126",
                         [page("Documentation guide\n===================\n")], corpus))


def test_c127_passes_for_an_imperative_instruction(corpus):
    assert one("MATPLOTLIB-C127",
               [page("Please run the suite before opening a pull request.\n")],
               corpus).verdict == "pass"


def test_c127_fails_when_the_instruction_names_its_subject(corpus):
    assert one("MATPLOTLIB-C127",
               [page("You should run the suite before opening a pull request.\n")],
               corpus).verdict == "fail"


def test_c127_finds_no_target_for_an_explanatory_sentence_left_to_c129(corpus):
    """The §7.5 half: explanation is C129's, instruction is C127's, never both."""
    assert no_target(one("MATPLOTLIB-C127",
                         [page("The renderer draws each Artist in turn.\n")], corpus))


def test_c129_passes_for_the_present_simple(corpus):
    assert one("MATPLOTLIB-C129", [page("The renderer draws each Artist in turn.\n")],
               corpus).verdict == "pass"


def test_c129_fails_for_the_future_tense(corpus):
    assert one("MATPLOTLIB-C129",
               [page("The renderer will draw each Artist in turn.\n")],
               corpus).verdict == "fail"


def test_c129_finds_no_target_for_an_instruction_left_to_c127(corpus):
    assert no_target(one("MATPLOTLIB-C129",
                         [page("You should run the suite first.\n")], corpus))


def test_c131_passes_for_the_active_voice(corpus):
    assert one("MATPLOTLIB-C131", [page("The renderer draws each Artist in turn.\n")],
               corpus).verdict == "pass"


def test_c131_fails_for_the_passive_voice(corpus):
    assert one("MATPLOTLIB-C131",
               [page("Each Artist is drawn by the renderer in turn.\n")],
               corpus).verdict == "fail"


def test_c131_fails_for_a_regular_past_participle(corpus):
    assert one("MATPLOTLIB-C131",
               [page("The style is applied to every new Figure.\n")],
               corpus).verdict == "fail"


def test_c131_finds_no_target_for_a_page_with_no_prose(corpus):
    assert no_target(one("MATPLOTLIB-C131", [page("Title\n=====\n")], corpus))


COMMENT_BEFORE = PLOTTING + "\n# Widen the line\nax.plot([2, 3])\n"
COMMENT_AFTER = PLOTTING + "\nax.plot([2, 3])\n# That widened the line\n"


def test_c136_passes_when_the_comment_precedes_its_code(corpus):
    assert one("MATPLOTLIB-C136", [example(COMMENT_BEFORE)], corpus).verdict == "pass"


def test_c136_fails_when_it_follows_it(corpus):
    assert one("MATPLOTLIB-C136", [example(COMMENT_AFTER)], corpus).verdict == "fail"


def test_c136_finds_no_target_for_an_example_with_no_comments(corpus):
    assert no_target(one("MATPLOTLIB-C136", [example(PLOTTING)], corpus))


def test_c137_passes_when_the_example_ends_with_show(corpus):
    assert one("MATPLOTLIB-C137", [example(PLOTTING)], corpus).verdict == "pass"


def test_c137_fails_when_it_never_calls_show(corpus):
    body = PLOTTING.replace("plt.show()\n", "")
    assert one("MATPLOTLIB-C137", [example(body)], corpus).verdict == "fail"


def test_c137_finds_no_target_for_an_example_that_draws_nothing(corpus):
    assert no_target(one("MATPLOTLIB-C137", [example(NO_PLOT)], corpus))


PROMPTED = PLOTTING + "\n# %%\n# >>> ax.get_xlim()\n# >>> ax.get_ylim()\n"
WITH_OUTPUT = PLOTTING + "\n# %%\n# >>> ax.get_xlim()\n# (0.0, 1.0)\n"


def test_c138_passes_when_only_input_is_shown(corpus):
    assert one("MATPLOTLIB-C138", [example(PROMPTED)], corpus).verdict == "pass"


def test_c138_fails_when_output_is_left_behind(corpus):
    assert one("MATPLOTLIB-C138", [example(WITH_OUTPUT)], corpus).verdict == "fail"


def test_c138_finds_no_target_for_an_example_with_no_prompts(corpus):
    assert no_target(one("MATPLOTLIB-C138", [example(PLOTTING)], corpus))


def test_c140_passes_for_a_list_of_ordered_actions(corpus):
    body = "Steps\n=====\n\n1. Install the dependencies.\n2. Run the suite.\n"
    assert one("MATPLOTLIB-C140", [page(body)], corpus).verdict == "pass"


def test_c140_fails_for_a_numbered_list_of_things(corpus):
    body = "Backends\n========\n\n1. Agg backend\n2. Cairo backend\n"
    assert one("MATPLOTLIB-C140", [page(body)], corpus).verdict == "fail"


def test_c140_finds_no_target_for_a_bulleted_list(corpus):
    body = "Backends\n========\n\n- Agg backend\n- Cairo backend\n"
    assert no_target(one("MATPLOTLIB-C140", [page(body)], corpus))


GRID_TABLE = ("Table\n=====\n\n"
              "+------+------+\n"
              "| a    | b    |\n"
              "+------+------+\n")
LIST_TABLE = "Table\n=====\n\n.. list-table::\n\n   * - a\n     - b\n"
MARKDOWN_TABLE = "Table\n=====\n\n| a | b |\n| - | - |\n"
CSV_TABLE = "Table\n=====\n\n.. csv-table::\n\n   a,b\n"


def test_c141_passes_for_an_ascii_table(corpus):
    assert one("MATPLOTLIB-C141", [page(GRID_TABLE)], corpus).verdict == "pass"


def test_c141_fails_for_a_list_table(corpus):
    assert one("MATPLOTLIB-C141", [page(LIST_TABLE)], corpus).verdict == "fail"


def test_c141_finds_no_target_for_a_markdown_table_left_to_c142(corpus):
    """The §7.5 half: Markdown and csv-table are C142's, and C141 must not repeat it."""
    assert no_target(one("MATPLOTLIB-C141", [page(MARKDOWN_TABLE)], corpus))


def test_c142_passes_for_an_ascii_table(corpus):
    assert one("MATPLOTLIB-C142", [page(GRID_TABLE)], corpus).verdict == "pass"


def test_c142_fails_for_a_markdown_table(corpus):
    assert one("MATPLOTLIB-C142", [page(MARKDOWN_TABLE)], corpus).verdict == "fail"


def test_c142_fails_for_the_csv_table_directive(corpus):
    assert one("MATPLOTLIB-C142", [page(CSV_TABLE)], corpus).verdict == "fail"


def test_c142_finds_no_target_for_a_page_with_no_tables(corpus):
    assert no_target(one("MATPLOTLIB-C142", [page("Title\n=====\n")], corpus))


# --- C272 and the tag rules -----------------------------------------------------------------------------


NEW_PLOTTING_API = whole(LIB, 'class Axes:\n    def ribbon(self, x):\n'
                              '        """Draw a ribbon."""\n        return x\n')


def test_c272_passes_when_a_gallery_example_demonstrates_the_feature(corpus):
    assert one("MATPLOTLIB-C272", [NEW_PLOTTING_API, example(PLOTTING)],
               corpus).verdict == "pass"


def test_c272_fails_when_nothing_demonstrates_it(corpus):
    assert one("MATPLOTLIB-C272", [NEW_PLOTTING_API], corpus).verdict == "fail"


def test_c272_finds_no_target_for_a_change_outside_the_plotting_modules(corpus):
    files = [whole("lib/matplotlib/colors.py",
                   'def to_ribbon(x):\n    """Convert."""\n    return x\n')]
    assert no_target(one("MATPLOTLIB-C272", files, corpus))


TAGGED = PLOTTING + "\n# %%\n# .. tags:: plot-type: line, level: beginner\n"
TAGGED_THEN_MORE = (PLOTTING + "\n# %%\n# .. tags:: plot-type: line\n"
                    "#\n# And a closing note about the example.\n")


def test_c276_passes_when_the_tags_directive_is_last(corpus):
    assert one("MATPLOTLIB-C276", [example(TAGGED)], corpus).verdict == "pass"


def test_c276_fails_when_content_follows_it(corpus):
    assert one("MATPLOTLIB-C276", [example(TAGGED_THEN_MORE)], corpus).verdict == "fail"


def test_c276_finds_no_target_for_an_untagged_page(corpus):
    assert no_target(one("MATPLOTLIB-C276", [example(PLOTTING)], corpus))


def test_c277_passes_for_a_tagged_example(corpus):
    assert one("MATPLOTLIB-C277", [example(TAGGED, is_new=True)], corpus).verdict == "pass"


def test_c277_fails_for_an_untagged_one(corpus):
    assert one("MATPLOTLIB-C277", [example(PLOTTING, is_new=True)],
               corpus).verdict == "fail"


def test_c277_finds_no_target_for_a_pre_existing_example(corpus):
    lines = TAGGED.split("\n")
    edited = make_file(EXAMPLE, [(11, lines[10])], head_text=TAGGED)
    assert no_target(one("MATPLOTLIB-C277", [edited], corpus))


def test_c280_passes_for_the_subcategory_form(corpus):
    assert one("MATPLOTLIB-C280", [example(TAGGED)], corpus).verdict == "pass"


def test_c280_fails_for_a_bare_tag(corpus):
    body = PLOTTING + "\n# %%\n# .. tags:: line\n"
    assert one("MATPLOTLIB-C280", [example(body)], corpus).verdict == "fail"


def test_c280_finds_no_target_for_an_untagged_example(corpus):
    assert no_target(one("MATPLOTLIB-C280", [example(PLOTTING)], corpus))


def test_c281_passes_for_a_two_word_tag(corpus):
    assert one("MATPLOTLIB-C281", [example(TAGGED)], corpus).verdict == "pass"


def test_c281_fails_for_a_longer_tag(corpus):
    body = PLOTTING + "\n# %%\n# .. tags:: plot-type: a line drawn simply\n"
    assert one("MATPLOTLIB-C281", [example(body)], corpus).verdict == "fail"


def test_c281_finds_no_target_for_a_tag_with_no_subcategory_left_to_c280(corpus):
    """The §7.5 half: a tag without a subcategory is C280's finding."""
    body = PLOTTING + "\n# %%\n# .. tags:: a line drawn simply\n"
    assert no_target(one("MATPLOTLIB-C281", [example(body)], corpus))


SECOND_EXAMPLE = example(TAGGED, "galleries/examples/lines_bars/plot_other.py")
SECOND_WITH_OWN_TAG = example(
    PLOTTING + "\n# %%\n# .. tags:: plot-type: bar\n",
    "galleries/examples/lines_bars/plot_other.py")


def test_c283_passes_when_the_tag_reaches_two_entries(corpus):
    assert one("MATPLOTLIB-C283", [example(TAGGED), SECOND_EXAMPLE],
               corpus).verdict == "pass"


def test_c283_fails_for_a_tag_used_by_one_entry_only(corpus):
    assert one("MATPLOTLIB-C283", [example(TAGGED), SECOND_WITH_OWN_TAG],
               corpus).verdict == "fail"


def test_c283_finds_no_target_when_only_one_entry_is_tagged(corpus):
    assert no_target(one("MATPLOTLIB-C283", [example(TAGGED)], corpus))

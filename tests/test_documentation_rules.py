"""Three cases per rule (docs/checker-authoring.md §9): a target that satisfies, one that
violates, and an input where the pre-condition finds nothing.

Two things this category needs from its tests specifically.

**The `created` versus `touched` distinction is the interesting one.** C180, C183 and C191
demand that a docstring *contain* something, and they take `created` ownership so that an
agent which edited one line of existing prose is not asked to have written an `Examples`
block someone else owed. Their "does not apply" case is therefore a docstring the agent
merely touched -- if that case ever starts returning `fail`, the rule has begun scoring
SymPy's authors (invariant 5).

**Where two rules fire on one fixture, the failure assertion names the phrase only one of
them produces.** C169 and C216 both fire on a docstring containing LaTeX, because LaTeX
contains backslashes; C194, C195 and C196 all fire on a See Also entry. Asserting on the
verdict alone would pin neither (`checker-development-issues.md` K).
"""

from __future__ import annotations

import textwrap

from conftest import make_bundle

from compliance.core.models import Command, FileChange
from compliance.core.registry import registered
from compliance.core.runner import run_rule

import compliance.rules.sympy.documentation  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
CODE = "sympy/core/thing.py"
NARRATIVE = "doc/src/guides/thing.rst"


def pyfile(path: str = CODE, source: str = "", *, authored: list[int] | None = None,
           is_new: bool = False) -> FileChange:
    """A Python file in the contribution.

    ``authored`` restricts which lines the agent wrote, which is how the `created` and
    `touched` cases are told apart; by default it wrote all of them.
    """
    source = textwrap.dedent(source)
    lines = source.split("\n")
    owned = frozenset(authored) if authored is not None else frozenset(range(1, len(lines) + 1))
    return FileChange(
        path=path,
        authored_lines=owned,
        added_lines=tuple((n, lines[n - 1]) for n in sorted(owned) if n <= len(lines)),
        head_text=source,
        is_new=is_new,
    )


def textfile(path: str, body: str, *, authored: list[int] | None = None) -> FileChange:
    body = textwrap.dedent(body)
    lines = body.split("\n")
    owned = frozenset(authored) if authored is not None else frozenset(range(1, len(lines) + 1))
    return FileChange(
        path=path,
        authored_lines=owned,
        added_lines=tuple((n, lines[n - 1]) for n in sorted(owned) if n <= len(lines)),
        head_text=body,
    )


def bundle(*files: FileChange, commands=(), **kw):
    return make_bundle(
        files={f.path: f for f in files},
        commands=tuple(Command(index=i, command=c[0], output=c[1] if len(c) > 1 else "")
                       for i, c in enumerate(commands)),
        **kw,
    )


def verdict(rule_id: str, b, corpus):
    return run_rule(b, RULES[rule_id], corpus)


def assert_passes(rule_id: str, b, corpus):
    row = verdict(rule_id, b, corpus)
    assert row.n_targets > 0, f"{rule_id}: pre-condition did not fire"
    assert row.verdict == "pass", f"{rule_id}: {row.notes}"
    return row


def assert_fails(rule_id: str, b, corpus, phrase: str):
    """A failure assertion is only worth the specificity of what it asserts.

    ``phrase`` must be text only this rule's violation produces, so a fixture that trips
    two rules cannot make a broken one look tested.
    """
    row = verdict(rule_id, b, corpus)
    assert row.verdict == "fail", f"{rule_id}: expected fail, got {row.verdict} ({row.notes})"
    assert phrase in row.notes, f"{rule_id}: {phrase!r} not in {row.notes!r}"
    return row


def assert_no_targets(rule_id: str, b, corpus):
    row = verdict(rule_id, b, corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0), row.notes
    return row


# A docstring that satisfies the whole category, used wherever a rule needs a clean one.
GOOD = '''
    def distance(self, other):
        """Return the Euclidean distance to another point.

        Examples
        ========

        >>> from sympy.geometry import Point
        >>> Point(0, 0).distance(Point(3, 4))
        5

        Parameters
        ==========

        ``other`` : Point
            The point to measure to.

        See Also
        ========

        Point

        References
        ==========

        .. [1] https://example.org/distance

        """
        return 0
'''


# --- C168 / C169 / C170 / C172: quotes and layout --------------------------------------


def test_c168_passes_on_triple_double_quotes(corpus):
    assert_passes("SYMPY-C168", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c168_fails_on_single_quotes(corpus):
    b = bundle(pyfile(source="""
        def f():
            '''Do a thing.

            '''
            return 1
        """, is_new=True))
    assert_fails("SYMPY-C168", b, corpus, "not triple double quotes")


def test_c168_not_applicable_when_no_docstring_was_written(corpus):
    assert_no_targets("SYMPY-C168", bundle(pyfile(source="\ndef f():\n    return 1\n",
                                                  is_new=True)), corpus)


def test_c169_passes_when_a_backslash_docstring_is_raw(corpus):
    b = bundle(pyfile(source=r'''
        def f():
            r"""Return \alpha.

            """
            return 1
        ''', is_new=True))
    assert_passes("SYMPY-C169", b, corpus)


def test_c169_fails_when_a_backslash_docstring_is_not_raw(corpus):
    b = bundle(pyfile(source=r'''
        def f():
            """Return \nu of the argument.

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C169", b, corpus, "contains a backslash but is not a raw string")


def test_c169_not_applicable_without_a_backslash(corpus):
    """The rule's antecedent is *if a docstring contains a backslash*. A docstring with
    none is not asked to be raw."""
    assert_no_targets("SYMPY-C169", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c170_passes_with_a_blank_line_before_the_closing_quotes(corpus):
    assert_passes("SYMPY-C170", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c170_fails_when_the_closing_quotes_follow_the_text(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            More about the thing.
            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C170", b, corpus, "no blank line before")


def test_c170_not_applicable_to_a_one_line_docstring(corpus):
    """A reading worth pinning: the guidance is about a docstring whose closing quotes sit
    on their own line, and `\"\"\"Return x.\"\"\"` has none. If this ever fails, the rule has
    started failing every one-line docstring in the project."""
    b = bundle(pyfile(source='\ndef f():\n    """Return one."""\n    return 1\n', is_new=True))
    assert_no_targets("SYMPY-C170", b, corpus)


def test_c172_passes_when_the_class_docstring_is_directly_under_the_definition(corpus):
    b = bundle(pyfile(source='''
        class Thing:
            """A thing.

            """
        ''', is_new=True))
    assert_passes("SYMPY-C172", b, corpus)


def test_c172_fails_when_a_blank_line_separates_them(corpus):
    b = bundle(pyfile(source='''
        class Thing:

            """A thing.

            """
        ''', is_new=True))
    assert_fails("SYMPY-C172", b, corpus, "separated from the class definition")


def test_c172_not_applicable_to_a_function_docstring(corpus):
    """The rule is about class-level docstrings. A function docstring is C168's and
    C181's business, not this one's."""
    assert_no_targets("SYMPY-C172", bundle(pyfile(source=GOOD, is_new=True)), corpus)


# --- C173 / C214 / C216: what the docstring body may contain ---------------------------


def test_c173_passes_when_example_python_is_a_doctest(corpus):
    """Prohibition-shaped: the compliant form produces no target at all."""
    assert_no_targets("SYMPY-C173", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c173_fails_on_python_in_a_literal_block(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            For example::

                result = f(2)
                print(result)

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C173", b, corpus, "literal block, not a doctest")


def test_c173_not_applicable_to_a_literal_block_that_is_not_python(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            Run it like this::

                $ sympy --version --verbose !!

            """
            return 1
        ''', is_new=True))
    assert_no_targets("SYMPY-C173", b, corpus)


def test_c214_passes_on_rst_markup(corpus):
    assert_passes("SYMPY-C214", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c214_fails_on_a_markdown_heading_in_a_docstring(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            # Notes

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C214", b, corpus, "uses Markdown, not RST")


def test_c214_not_applicable_when_no_docstring_was_written(corpus):
    assert_no_targets("SYMPY-C214", bundle(pyfile(source="\ndef f():\n    return 1\n",
                                                  is_new=True)), corpus)


def test_c216_passes_when_a_latex_docstring_is_raw(corpus):
    b = bundle(pyfile(source=r'''
        def f():
            r"""Return \frac{1}{2}.

            """
            return 1
        ''', is_new=True))
    assert_passes("SYMPY-C216", b, corpus)


def test_c216_fails_when_a_latex_docstring_is_not_raw(corpus):
    """C169 fires on the same fixture -- LaTeX carries backslashes -- so the assertion
    names the phrase only C216 produces."""
    b = bundle(pyfile(source=r'''
        def f():
            """Return \frac{1}{2}.

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C216", b, corpus, "contains LaTeX")


def test_c216_not_applicable_without_latex(corpus):
    assert_no_targets("SYMPY-C216", bundle(pyfile(source=GOOD, is_new=True)), corpus)


# --- C176 / C177 / C178: sections, their names, their headings -------------------------


def test_c176_passes_on_the_published_section_order(corpus):
    assert_passes("SYMPY-C176", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c176_fails_when_parameters_precedes_examples(corpus):
    b = bundle(pyfile(source='''
        def f(x):
            """Do a thing.

            Parameters
            ==========

            ``x`` : int
                A number.

            Examples
            ========

            >>> f(1)
            1

            """
            return x
        ''', is_new=True))
    assert_fails("SYMPY-C176", b, corpus, "expected Examples -> Parameters")


def test_c176_not_applicable_with_fewer_than_two_ordered_sections(corpus):
    """Order is a relation between sections. One section cannot be out of order, and the
    rule says nothing about sections it does not name."""
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            Examples
            ========

            >>> f()
            1

            """
            return 1
        ''', is_new=True))
    assert_no_targets("SYMPY-C176", b, corpus)


def test_c177_passes_on_exact_section_names(corpus):
    assert_passes("SYMPY-C177", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c177_fails_on_the_singular_example_heading(corpus):
    """The rule names this case outright: plural `Examples` even for one example."""
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            Example
            =======

            >>> f()
            1

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C177", b, corpus, "is not a supported section name")


def test_c177_not_applicable_to_a_docstring_with_no_sections(corpus):
    b = bundle(pyfile(source='\ndef f():\n    """Do a thing.\n\n    """\n    return 1\n',
                      is_new=True))
    assert_no_targets("SYMPY-C177", b, corpus)


def test_c178_passes_when_the_underline_matches_the_heading(corpus):
    assert_passes("SYMPY-C178", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c178_fails_on_a_short_underline(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            Examples
            ===

            >>> f()
            1

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C178", b, corpus, "equals signs")


def test_c178_fails_on_the_wrong_underline_character(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            Examples
            --------

            >>> f()
            1

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C178", b, corpus, "not equals signs")


def test_c178_not_applicable_to_a_docstring_with_no_headings(corpus):
    b = bundle(pyfile(source='\ndef f():\n    """Do a thing.\n\n    """\n    return 1\n',
                      is_new=True))
    assert_no_targets("SYMPY-C178", b, corpus)


# --- C180 / C181 / C183 / C191: what a docstring must contain --------------------------
#
# The three `created` rules. Their "does not apply" case is a docstring the agent merely
# touched: switching any of them to `touched` would fail an agent for prose it did not
# write, which is invariant 5.

TOUCHED_NOT_CREATED = '''
    def f(x):
        """

        Explanation
        ===========

        Some existing prose that the agent did not write.
        One more line of it, edited by the agent.

        """
        return x
'''


def test_c180_passes_when_the_docstring_opens_with_a_summary(corpus):
    assert_passes("SYMPY-C180", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c180_fails_when_the_docstring_opens_with_a_section(corpus):
    b = bundle(pyfile(source='''
        def f():
            """

            Examples
            ========

            >>> f()
            1

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C180", b, corpus, "begins with no summary")


def test_c180_not_applicable_to_a_docstring_the_agent_only_touched(corpus):
    b = bundle(pyfile(source=TOUCHED_NOT_CREATED, authored=[9]))
    assert_no_targets("SYMPY-C180", b, corpus)


def test_c181_passes_on_a_one_line_summary_ending_in_a_period(corpus):
    assert_passes("SYMPY-C181", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c181_fails_on_a_summary_without_a_period(corpus):
    b = bundle(pyfile(source='\ndef f():\n    """Do a thing\n\n    """\n    return 1\n',
                      is_new=True))
    assert_fails("SYMPY-C181", b, corpus, "does not end with a period")


def test_c181_fails_on_a_summary_spanning_two_lines(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing, and then do
            a second thing as well.

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C181", b, corpus, "spans 2")


def test_c181_does_not_read_an_extended_description_as_the_summary(corpus):
    """The summary is the first paragraph. Reading everything before the first heading as
    the summary would fail every docstring that explains itself before its sections."""
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            A longer paragraph explaining the thing in more detail,
            wrapped across two lines.

            """
            return 1
        ''', is_new=True))
    assert_passes("SYMPY-C181", b, corpus)


def test_c181_not_applicable_to_a_docstring_with_no_summary(corpus):
    b = bundle(pyfile(source='''
        def f():
            """

            Examples
            ========

            >>> f()
            1

            """
            return 1
        ''', is_new=True))
    assert_no_targets("SYMPY-C181", b, corpus)


def test_c183_passes_when_the_docstring_has_an_examples_section(corpus):
    assert_passes("SYMPY-C183", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c183_fails_when_a_created_docstring_has_none(corpus):
    b = bundle(pyfile(source='\ndef f():\n    """Do a thing.\n\n    """\n    return 1\n',
                      is_new=True))
    assert_fails("SYMPY-C183", b, corpus, "no Examples section")


def test_c183_not_applicable_to_a_docstring_the_agent_only_touched(corpus):
    """Plan §4.2 names this case: do not demand `Examples` of a docstring the agent
    merely brushed. The fixture has no Examples section, so a switch to `touched`
    ownership turns this into a failure immediately."""
    b = bundle(pyfile(source=TOUCHED_NOT_CREATED, authored=[9]))
    assert_no_targets("SYMPY-C183", b, corpus)


def test_c191_passes_when_a_documented_signature_has_a_parameters_section(corpus):
    assert_passes("SYMPY-C191", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c191_fails_when_a_parameterised_function_documents_none(corpus):
    b = bundle(pyfile(source='''
        def f(x, y):
            """Do a thing.

            Examples
            ========

            >>> f(1, 2)
            3

            """
            return x + y
        ''', is_new=True))
    assert_fails("SYMPY-C191", b, corpus, "with no Parameters section")


def test_c191_not_applicable_when_the_signature_takes_no_parameters(corpus):
    """The rule's antecedent is *if the documented signature lists parameters*."""
    b = bundle(pyfile(source='\ndef f():\n    """Do a thing.\n\n    """\n    return 1\n',
                      is_new=True))
    assert_no_targets("SYMPY-C191", b, corpus)


def test_c191_ignores_self_so_methods_are_not_all_failures(corpus):
    b = bundle(pyfile(source='''
        class Thing:
            """A thing.

            """

            def go(self):
                """Do a thing.

                """
                return 1
        ''', is_new=True))
    assert_no_targets("SYMPY-C191", b, corpus)


# --- C018 / C184 / C185 / C186 / C188: the Examples section and its doctests ------------


def test_c018_passes_on_explicit_imports(corpus):
    assert_passes("SYMPY-C018", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c018_fails_on_a_star_import(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            Examples
            ========

            >>> from sympy import *
            >>> f()
            1

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C018", b, corpus, "star import")


def test_c018_not_applicable_when_the_agent_wrote_no_doctest(corpus):
    b = bundle(pyfile(source='\ndef f():\n    """Do a thing.\n\n    """\n    return 1\n',
                      is_new=True))
    assert_no_targets("SYMPY-C018", b, corpus)


def test_c184_passes_with_a_blank_line_before_the_first_doctest(corpus):
    assert_passes("SYMPY-C184", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c184_fails_when_the_doctest_follows_the_heading_directly(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            Examples
            ========
            >>> f()
            1

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C184", b, corpus, "no blank line before its first doctest")


def test_c184_not_applicable_without_an_examples_section(corpus):
    b = bundle(pyfile(source='\ndef f():\n    """Do a thing.\n\n    """\n    return 1\n',
                      is_new=True))
    assert_no_targets("SYMPY-C184", b, corpus)


def test_c185_passes_when_examples_are_separated_by_a_blank_line(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            Examples
            ========

            >>> f(1)
            1

            >>> f(2)
            2

            """
            return 1
        ''', is_new=True))
    assert_passes("SYMPY-C185", b, corpus)


def test_c185_fails_when_a_second_example_follows_output_directly(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            Examples
            ========

            >>> f(1)
            1
            >>> f(2)
            2

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C185", b, corpus, "not separated by a")


def test_c185_not_applicable_to_a_chain_of_statements(corpus):
    """The heuristic this rule rests on, stated as a test: a run of statements that
    produce no output is one example, not several. Reading every `>>>` as a separate
    example would fail every idiomatic SymPy docstring, including the import line that
    opens almost all of them."""
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            Examples
            ========

            >>> from sympy import Symbol
            >>> x = Symbol('x')
            >>> f(x)
            1

            """
            return 1
        ''', is_new=True))
    assert_no_targets("SYMPY-C185", b, corpus)


def test_c186_passes_when_explanatory_text_is_surrounded_by_blank_lines(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            Examples
            ========

            >>> f(1)
            1

            The same call with a larger argument:

            >>> f(2)
            2

            """
            return 1
        ''', is_new=True))
    assert_passes("SYMPY-C186", b, corpus)


def test_c186_fails_when_the_text_abuts_the_next_doctest(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            Examples
            ========

            >>> f(1)
            1

            The same call with a larger argument:
            >>> f(2)
            2

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C186", b, corpus, "no blank line below")


def test_c186_not_applicable_without_text_between_doctests(corpus):
    assert_no_targets("SYMPY-C186", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c188_passes_when_a_long_input_is_wrapped(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            Examples
            ========

            >>> result = f(argument_one, argument_two, argument_three,
            ...            argument_four, argument_five, argument_six)
            >>> result
            1

            """
            return 1
        ''', is_new=True))
    assert_passes("SYMPY-C188", b, corpus)


def test_c188_fails_on_an_unwrapped_long_input(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            Examples
            ========

            >>> result = f(argument_one, argument_two, argument_three, argument_four, argument_five)
            >>> result
            1

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C188", b, corpus, "not wrapped")


def test_c188_not_applicable_to_a_short_input(corpus):
    assert_no_targets("SYMPY-C188", bundle(pyfile(source=GOOD, is_new=True)), corpus)


# --- C192 / C193: the Parameters section ------------------------------------------------


def test_c192_passes_on_double_backticked_parameter_names(corpus):
    assert_passes("SYMPY-C192", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c192_fails_on_a_bare_parameter_name(corpus):
    b = bundle(pyfile(source='''
        def f(x):
            """Do a thing.

            Parameters
            ==========

            x : int
                A number.

            """
            return x
        ''', is_new=True))
    assert_fails("SYMPY-C192", b, corpus, "not in double-backtick code markup")


def test_c192_not_applicable_without_a_parameters_section(corpus):
    b = bundle(pyfile(source='\ndef f(x):\n    """Do a thing.\n\n    """\n    return x\n',
                      is_new=True))
    assert_no_targets("SYMPY-C192", b, corpus)


def test_c193_passes_on_the_spaced_colon_separator(corpus):
    assert_passes("SYMPY-C193", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c193_fails_when_the_colon_is_not_preceded_by_a_space(corpus):
    """The name keeps its code markup so C192 passes and only C193 can fail here."""
    b = bundle(pyfile(source='''
        def f(x):
            """Do a thing.

            Parameters
            ==========

            ``x``: int
                A number.

            """
            return x
        ''', is_new=True))
    assert_fails("SYMPY-C193", b, corpus, "expected ' : '")


def test_c193_fails_on_a_trailing_colon_with_no_type(corpus):
    """The rule's second half: omit the colon when no type is supplied."""
    b = bundle(pyfile(source='''
        def f(x):
            """Do a thing.

            Parameters
            ==========

            ``x`` :
                A number.

            """
            return x
        ''', is_new=True))
    assert_fails("SYMPY-C193", b, corpus, "carries a colon but no type")


def test_c193_passes_on_a_bare_name_with_no_type(corpus):
    b = bundle(pyfile(source='''
        def f(x):
            """Do a thing.

            Parameters
            ==========

            ``x``
                A number.

            """
            return x
        ''', is_new=True))
    assert_passes("SYMPY-C193", b, corpus)


def test_c193_not_applicable_without_a_parameters_section(corpus):
    b = bundle(pyfile(source='\ndef f(x):\n    """Do a thing.\n\n    """\n    return x\n',
                      is_new=True))
    assert_no_targets("SYMPY-C193", b, corpus)


# --- C194 / C195 / C196: the See Also section -------------------------------------------
#
# All three fire on a See Also entry, so every failure assertion below names the phrase
# only its own rule produces.


def test_c194_passes_on_an_indented_continuation(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            See Also
            ========

            Point : the point class, which is described here
                across two lines of prose.

            """
            return 1
        ''', is_new=True))
    assert_passes("SYMPY-C194", b, corpus)


def test_c194_fails_on_an_unindented_continuation(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            See Also
            ========

            Point : the point class, which is described here
            across two lines of prose.

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C194", b, corpus, "continues unindented")


def test_c194_not_applicable_to_a_single_line_description(corpus):
    """The rule's antecedent is *if a See Also description spans multiple lines*."""
    assert_no_targets("SYMPY-C194", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c195_passes_on_a_sympy_object(corpus):
    assert_passes("SYMPY-C195", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c195_fails_on_an_external_link(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            See Also
            ========

            https://example.org/other : an external page

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C195", b, corpus, "external link")


def test_c195_not_applicable_without_a_see_also_section(corpus):
    b = bundle(pyfile(source='\ndef f():\n    """Do a thing.\n\n    """\n    return 1\n',
                      is_new=True))
    assert_no_targets("SYMPY-C195", b, corpus)


def test_c196_passes_on_a_bare_class_name(corpus):
    assert_passes("SYMPY-C196", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c196_fails_on_a_class_role(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            See Also
            ========

            :class:`Point`

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C196", b, corpus, "references a class with a role")


def test_c196_not_applicable_without_a_see_also_section(corpus):
    b = bundle(pyfile(source='\ndef f():\n    """Do a thing.\n\n    """\n    return 1\n',
                      is_new=True))
    assert_no_targets("SYMPY-C196", b, corpus)


# --- C197 / C199: the References section ------------------------------------------------


def test_c197_passes_on_citations_numbered_from_one(corpus):
    assert_passes("SYMPY-C197", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c197_fails_when_the_numbering_does_not_start_at_one(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            References
            ==========

            .. [2] https://example.org/a
            .. [3] https://example.org/b

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C197", b, corpus, "expected 1, 2")


def test_c197_not_applicable_without_a_references_section(corpus):
    b = bundle(pyfile(source='\ndef f():\n    """Do a thing.\n\n    """\n    return 1\n',
                      is_new=True))
    assert_no_targets("SYMPY-C197", b, corpus)


def test_c199_passes_when_the_doi_is_a_link(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            References
            ==========

            .. [1] A paper about things. https://doi.org/10.1000/abc123

            """
            return 1
        ''', is_new=True))
    assert_passes("SYMPY-C199", b, corpus)


def test_c199_fails_on_a_bare_doi(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            References
            ==========

            .. [1] A paper about things. doi:10.1000/abc123

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C199", b, corpus, "not given as a clickable link")


def test_c199_not_applicable_to_a_reference_with_no_doi(corpus):
    """The rule's antecedent is *a paper reference with a DOI*."""
    assert_no_targets("SYMPY-C199", bundle(pyfile(source=GOOD, is_new=True)), corpus)


# --- C203: mathematical-function classes -------------------------------------------------

MATH_CLASS = '''
    class coth(HyperbolicFunction):
        """The hyperbolic cotangent function.

        Examples
        ========

        >>> coth(0)
        zoo

        """

        @classmethod
        def eval(cls, arg):
            if arg.is_Number:
                return arg
            if arg.is_zero:
                return S.ComplexInfinity
            return None
'''


def test_c203_passes_when_the_class_documents_itself_and_eval_does_not(corpus):
    assert_passes("SYMPY-C203", bundle(pyfile(source=MATH_CLASS, is_new=True)), corpus)


def test_c203_fails_when_eval_has_its_own_docstring(corpus):
    b = bundle(pyfile(source='''
        class coth(HyperbolicFunction):
            """The hyperbolic cotangent function.

            """

            @classmethod
            def eval(cls, arg):
                """Evaluate the function at arg."""
                return None
        ''', is_new=True))
    assert_fails("SYMPY-C203", b, corpus, "has its own docstring")


def test_c203_not_applicable_when_the_agent_only_edited_the_eval_body(corpus):
    """The antecedent is a documentation decision, not any edit inside the class.

    This is the case that fired on the real pilot data: four runs modified a single line
    of a 131-line `coth` class and collected a pass for a docstring SymPy's authors wrote.
    Widening ownership back to the class span, or to the class span plus `eval`, makes
    this test fail (invariant 5, `checker-development-issues.md` A6).
    """
    b = bundle(pyfile(source=MATH_CLASS, authored=[16]))
    assert_no_targets("SYMPY-C203", b, corpus)


# --- C206 / C207 / C208 / C210: cross-referencing ----------------------------------------


def xref(body: str) -> FileChange:
    return pyfile(source=f'''
        def f(other):
            """Do a thing.

            {body}

            """
            return other
        ''', is_new=True)


def test_c206_passes_on_a_cross_reference_role(corpus):
    assert_passes("SYMPY-C206", bundle(xref("See :obj:`~.Symbol` for details.")), corpus)


def test_c206_fails_on_a_single_backtick_object_reference(corpus):
    assert_fails("SYMPY-C206", bundle(xref("See `Symbol` for details.")), corpus,
                 "uses a single backtick")


def test_c206_not_applicable_to_prose_naming_no_object(corpus):
    assert_no_targets("SYMPY-C206", bundle(xref("This does a thing to its argument.")),
                      corpus)


def test_c207_passes_on_a_full_dotted_path(corpus):
    b = bundle(xref("See :obj:`sympy.core.thing.helper` for details."))
    assert_passes("SYMPY-C207", b, corpus)


def test_c207_fails_when_a_non_top_level_object_is_abbreviated(corpus):
    b = bundle(xref("See :obj:`~.helper` for details."))
    assert_fails("SYMPY-C207", b, corpus, "abbreviates with `~.`")


def test_c207_not_applicable_to_a_top_level_object(corpus):
    """The rule's antecedent is *an object not exported from top-level sympy*. `~.` is
    the correct form for one that is, so the rule must not fire on it."""
    assert_no_targets("SYMPY-C207", bundle(xref("See :obj:`~.Symbol`.")), corpus)


def test_c208_passes_when_the_reference_is_a_sympy_object(corpus):
    """Prohibition-shaped: a linkable object produces no target."""
    assert_no_targets("SYMPY-C208", bundle(xref("See :obj:`~.Symbol`.")), corpus)


def test_c208_fails_on_a_role_pointing_at_a_builtin(corpus):
    assert_fails("SYMPY-C208", bundle(xref("Returns an :obj:`int` value.")), corpus,
                 "Python built-in")


def test_c208_fails_on_a_role_pointing_at_a_parameter(corpus):
    assert_fails("SYMPY-C208", bundle(xref("The :obj:`other` argument is used.")), corpus,
                 "the parameter")


def test_c208_not_applicable_without_any_cross_reference(corpus):
    assert_no_targets("SYMPY-C208", bundle(xref("Plain prose with no markup.")), corpus)


def test_c210_passes_on_a_custom_text_link_without_a_tilde(corpus):
    b = bundle(xref("See :obj:`the point class <Point>` for details."))
    assert_passes("SYMPY-C210", b, corpus)


def test_c210_fails_when_the_target_carries_a_tilde(corpus):
    b = bundle(xref("See :obj:`the point class <~.Point>` for details."))
    assert_fails("SYMPY-C210", b, corpus, "uses `~` inside a custom-text link")


def test_c210_not_applicable_to_a_role_without_custom_text(corpus):
    """The rule's antecedent is *a custom-text object link*."""
    assert_no_targets("SYMPY-C210", bundle(xref("See :obj:`~.Symbol`.")), corpus)


# --- C213 / C221 / C227 / C228 / C234: narrative documentation files ---------------------


def test_c213_passes_when_markdown_is_narrative_documentation(corpus):
    """Prohibition-shaped: Markdown under `doc/` is exactly what the rule permits."""
    b = bundle(textfile("doc/src/explanation/thing.md", "\n# A thing\n\nProse.\n"))
    assert_no_targets("SYMPY-C213", b, corpus)


def test_c213_fails_on_markdown_inside_the_library_tree(corpus):
    b = bundle(textfile("sympy/core/notes.md", "\n# A thing\n\nProse.\n"))
    assert_fails("SYMPY-C213", b, corpus, "inside the library source tree")


def test_c213_not_applicable_when_no_markdown_was_written(corpus):
    assert_no_targets("SYMPY-C213", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c221_passes_on_double_backticked_code(corpus):
    b = bundle(textfile(NARRATIVE, "\nUse ``solve`` to solve it.\n"))
    assert_no_targets("SYMPY-C221", b, corpus)


def test_c221_fails_on_single_backticked_code(corpus):
    b = bundle(textfile(NARRATIVE, "\nUse `solve` to solve it.\n"))
    assert_fails("SYMPY-C221", b, corpus, "render as math")


def test_c221_not_applicable_when_no_rst_file_was_written(corpus):
    assert_no_targets("SYMPY-C221", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c227_passes_on_a_consistent_heading(corpus):
    b = bundle(textfile(NARRATIVE, "\nSolving Equations\n=================\n\nProse.\n"))
    assert_passes("SYMPY-C227", b, corpus)


def test_c227_fails_on_a_short_underline(corpus):
    b = bundle(textfile(NARRATIVE, "\nSolving Equations\n=====\n\nProse.\n"))
    assert_fails("SYMPY-C227", b, corpus, "not one repeated character at least as long")


def test_c227_not_applicable_when_the_agent_authored_no_heading(corpus):
    """Ownership, not presence: a heading already in the file is not the agent's to be
    judged on (invariant 5)."""
    b = bundle(textfile(NARRATIVE, "\nSolving Equations\n=====\n\nProse.\n", authored=[5]))
    assert_no_targets("SYMPY-C227", b, corpus)


def test_c228_passes_on_american_spelling(corpus):
    b = bundle(textfile(NARRATIVE, "\nThe behavior of the solver is normalized.\n"))
    assert_passes("SYMPY-C228", b, corpus)


def test_c228_fails_on_a_british_spelling(corpus):
    b = bundle(textfile(NARRATIVE, "\nThe behaviour of the solver is normalised.\n"))
    assert_fails("SYMPY-C228", b, corpus, "British spelling")


def test_c228_not_applicable_when_no_narrative_documentation_changed(corpus):
    """The rule is scoped to narrative writing. A docstring is not it."""
    assert_no_targets("SYMPY-C228", bundle(pyfile(source=GOOD, is_new=True)), corpus)


def test_c234_passes_on_the_neutral_pronoun(corpus):
    b = bundle(textfile(NARRATIVE, "\nA contributor should push their branch.\n"))
    assert_passes("SYMPY-C234", b, corpus)


def test_c234_fails_on_a_gendered_pronoun(corpus):
    b = bundle(textfile(NARRATIVE, "\nA contributor should push his branch.\n"))
    assert_fails("SYMPY-C234", b, corpus, "gendered pronoun")


def test_c234_not_applicable_when_no_documentation_changed(corpus):
    b = bundle(pyfile(source="\ndef f():\n    return 1\n", is_new=True))
    assert_no_targets("SYMPY-C234", b, corpus)


# --- C146 / C175 / C190 / C150: building the documentation --------------------------------
#
# These fire on the documentation change, never on the build command. Triggering on the
# command would let an agent that changed documentation and never built it collect
# `not_applicable`, which is the §4.2 inversion.

CODE_ONLY = "\ndef f():\n    return 1\n"


def test_c146_passes_when_the_docs_were_built(corpus):
    b = bundle(pyfile(source=GOOD, is_new=True),
               commands=[("cd doc && make html", "build succeeded")])
    assert_passes("SYMPY-C146", b, corpus)


def test_c146_fails_when_documentation_changed_and_was_never_built(corpus):
    assert_fails("SYMPY-C146", bundle(pyfile(source=GOOD, is_new=True)), corpus,
                 "never ran `make html`")


def test_c146_not_applicable_when_the_contribution_changes_no_documentation(corpus):
    """§4.2 in one test. An agent that changed only code is never asked to build the
    documentation -- but one that changed a docstring and did nothing else must fail,
    which the test above pins."""
    assert_no_targets("SYMPY-C146", bundle(pyfile(source=CODE_ONLY, is_new=True)), corpus)


def test_c175_passes_when_sphinx_reports_nothing(corpus):
    b = bundle(pyfile(source=GOOD, is_new=True),
               commands=[("cd doc && make html", "build succeeded, 0 issues")])
    assert_passes("SYMPY-C175", b, corpus)


def test_c175_fails_when_sphinx_reports_an_error(corpus):
    b = bundle(pyfile(source=GOOD, is_new=True),
               commands=[("cd doc && make html",
                          "reading sources...\nERROR: undefined label: thing\n")])
    assert_fails("SYMPY-C175", b, corpus, "Sphinx reported")


def test_c175_not_applicable_when_the_contribution_changes_no_documentation(corpus):
    assert_no_targets("SYMPY-C175", bundle(pyfile(source=CODE_ONLY, is_new=True)), corpus)


def test_c190_passes_when_bin_doctest_was_run(corpus):
    b = bundle(pyfile(source=GOOD, is_new=True),
               commands=[("python bin/doctest sympy/core", "All tests passed")])
    assert_passes("SYMPY-C190", b, corpus)


def test_c190_fails_when_examples_changed_and_doctests_never_ran(corpus):
    assert_fails("SYMPY-C190", bundle(pyfile(source=GOOD, is_new=True)), corpus,
                 "never ran `bin/doctest`")


def test_c190_fails_when_the_doctest_run_reported_failures(corpus):
    b = bundle(pyfile(source=GOOD, is_new=True),
               commands=[("python bin/doctest sympy/core",
                          "Failed example:\n    f(1)\nDO *NOT* COMMIT!")])
    assert_fails("SYMPY-C190", b, corpus, "left unfixed")


def test_c190_not_applicable_when_no_example_changed(corpus):
    """The rule's antecedent is *after adding or changing a docstring example*."""
    b = bundle(pyfile(source='\ndef f():\n    """Do a thing.\n\n    """\n    return 1\n',
                      is_new=True))
    assert_no_targets("SYMPY-C190", b, corpus)


def test_c150_passes_when_the_docs_use_double_backticks(corpus):
    b = bundle(textfile(NARRATIVE, "\nUse ``solve`` to solve it.\n"),
               commands=[("cd doc && make latexpdf", "ERROR: LaTeX failed")])
    assert_passes("SYMPY-C150", b, corpus)


def test_c150_fails_when_a_failed_pdf_build_meets_single_backticks(corpus):
    b = bundle(textfile(NARRATIVE, "\nUse `solve` to solve it.\n"),
               commands=[("cd doc && make latexpdf", "ERROR: LaTeX failed")])
    assert_fails("SYMPY-C150", b, corpus, "PDF build failed and")


def test_c150_not_applicable_without_a_failed_pdf_build(corpus):
    """The rule's antecedent is *if the PDF documentation build fails*, which no stored
    run has ever produced. Recorded as structural unreachability rather than deleted --
    the corpus is the specification."""
    b = bundle(textfile(NARRATIVE, "\nUse `solve` to solve it.\n"))
    assert_no_targets("SYMPY-C150", b, corpus)


# --- second violation branches -----------------------------------------------------------
#
# Every test below was written because a mutation survived: the branch it breaks was
# reachable, wrong, and asserted by nothing. Each rule above tests one of its failure
# modes; these test the rest (`checker-development-issues.md` K).


def test_c146_fails_when_make_html_runs_outside_the_doc_directory(corpus):
    b = bundle(pyfile(source=GOOD, is_new=True),
               commands=[("make html", "build succeeded")])
    assert_fails("SYMPY-C146", b, corpus, "without first changing into the `doc` directory")


def test_c146_fails_when_the_build_reports_errors(corpus):
    b = bundle(pyfile(source=GOOD, is_new=True),
               commands=[("cd doc && make html", "ERROR: undefined label: thing")])
    assert_fails("SYMPY-C146", b, corpus, "reported errors")


def test_c175_fails_when_the_documentation_was_never_built(corpus):
    """Distinct from C146's version: this rule accepts the `sympy_htmldoc` image as well,
    so its complaint is that Sphinx output was never checked at all."""
    assert_fails("SYMPY-C175", bundle(pyfile(source=GOOD, is_new=True)), corpus,
                 "Sphinx output was never checked")


def test_c175_accepts_the_docker_image_as_a_build(corpus):
    b = bundle(pyfile(source=GOOD, is_new=True),
               commands=[("docker run --rm -v /src:/sympy sympy_htmldoc", "build succeeded")])
    assert_passes("SYMPY-C175", b, corpus)


def test_c196_fails_when_the_name_is_wrapped_in_backticks(corpus):
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            See Also
            ========

            `Point`

            """
            return 1
        ''', is_new=True))
    assert_fails("SYMPY-C196", b, corpus, "wraps the name in backticks")


def test_c203_fails_when_the_class_carries_no_docstring(corpus):
    """The rule's other half: documentation must live at class level."""
    b = bundle(pyfile(source='''
        class coth(HyperbolicFunction):

            @classmethod
            def eval(cls, arg):
                return None
        ''', is_new=True))
    assert_fails("SYMPY-C203", b, corpus, "carries no class-level docstring")


def test_c207_fails_on_a_bare_non_top_level_name(corpus):
    """Not every failure of this rule is an abbreviation. A bare name with no path is
    equally unresolvable."""
    assert_fails("SYMPY-C207", bundle(xref("See :obj:`helper` for details.")), corpus,
                 "gives a bare name")


def test_c210_fails_when_a_custom_text_link_uses_another_role(corpus):
    b = bundle(xref("See :class:`the point class <Point>` for details."))
    assert_fails("SYMPY-C210", b, corpus, "role; a custom-text object link takes :obj:")


def test_sympy_section_vocabulary_is_stated_here_not_inherited(corpus):
    """SymPy's dialect is declared in its own rule pack, so a change to the shared
    numpydoc default cannot silently change what SymPy accepts."""
    from compliance.extractors import docstrings as ds
    from compliance.rules.sympy import documentation as doc

    assert "Explanation" in doc.SUPPORTED_SECTIONS
    assert "Explanation" not in ds.NUMPYDOC_SECTIONS


def test_c177_accepts_the_explanation_heading(corpus):
    """`Explanation` is SymPy's name for numpydoc's `Extended Summary`. If the vocabulary
    ever stops carrying it, every docstring with an Explanation section starts failing."""
    b = bundle(pyfile(source='''
        def f():
            """Do a thing.

            Explanation
            ===========

            Longer prose about the thing.

            """
            return 1
        ''', is_new=True))
    assert_passes("SYMPY-C177", b, corpus)

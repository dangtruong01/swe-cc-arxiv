"""Three cases per rule (docs/checker-authoring.md §9): a target that satisfies the pass
condition, one that violates it, and an input where the pre-condition finds nothing.

The third case is what catches a pre-condition written against the artefact the rule
demands instead of the antecedent that invokes it (§4.2).

Nine rules in this category cannot be graded offline -- they turn on how long a test
took, or on whether expected output matches. For those the third case still applies, but
"satisfies" and "violates" are replaced by a single assertion that the row is withheld
(``tool_missing``) and can never read ``fail``. Recording missing evidence as a violation
is invariant 6.
"""

from __future__ import annotations

import textwrap

from conftest import make_bundle

from compliance.core.models import Command, FileChange
from compliance.core.registry import registered
from compliance.core.runner import run_rule

import compliance.rules.sympy.tests  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
CATEGORY = compliance.rules.sympy.tests.CATEGORY

TEST_PATH = "sympy/core/tests/test_thing.py"
CODE_PATH = "sympy/core/thing.py"


def pyfile(path: str, source: str, *, authored=None, is_new=False) -> FileChange:
    lines = source.split("\n")
    numbers = list(authored) if authored is not None else list(range(1, len(lines) + 1))
    return FileChange(
        path=path,
        authored_lines=frozenset(numbers),
        added_lines=tuple((n, lines[n - 1]) for n in numbers if n <= len(lines)),
        head_text=source,
        is_new=is_new,
    )


def bundle(*files: FileChange, commands=(), **overrides):
    return make_bundle(
        files={f.path: f for f in files},
        commands=tuple(
            Command(index=i, command=c[0], output=c[1] if len(c) > 1 else "")
            for i, c in enumerate(commands)
        ),
        **overrides,
    )


def tmodule(source: str, **kwargs) -> FileChange:
    return pyfile(TEST_PATH, textwrap.dedent(source), **kwargs)


def code_file(source: str, **kwargs) -> FileChange:
    return pyfile(CODE_PATH, textwrap.dedent(source), **kwargs)


def verdict(rule_id, b, corpus):
    return run_rule(b, RULES[rule_id], corpus)


def assert_withheld(rule_id, b, corpus):
    """The rule applies but the bundle cannot answer it: never pass, never fail."""
    row = verdict(rule_id, b, corpus)
    assert row.n_targets > 0, "pre-condition did not fire"
    assert (row.verdict, row.status) == ("not_applicable", "tool_missing"), row.notes


def assert_no_targets(rule_id, b, corpus):
    row = verdict(rule_id, b, corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0), row.notes


CLEAN = [("python bin/test", "tests finished: 3 passed"),
         ("python bin/doctest", "doctests finished: 3 passed")]


# --- C069 new functionality must include tests -------------------------------------


def test_c069_passes_when_an_added_test_exercises_the_new_function(corpus):
    b = bundle(
        code_file("def resolve(x):\n    return x\n", is_new=True),
        tmodule("def test_resolve():\n    assert resolve(1) == 1\n", is_new=True),
    )
    assert verdict("SYMPY-C069", b, corpus).verdict == "pass"


def test_c069_fails_when_new_functionality_arrives_without_a_test(corpus):
    b = bundle(code_file("def resolve(x):\n    return x\n", is_new=True))
    assert verdict("SYMPY-C069", b, corpus).verdict == "fail"


def test_c069_not_applicable_when_nothing_new_was_defined(corpus):
    source = "def resolve(x):\n    return x + 1\n"
    assert_no_targets("SYMPY-C069", bundle(code_file(source, authored=[2])), corpus)


# --- C071 the full suite must pass --------------------------------------------------


def test_c071_is_withheld_until_the_suite_can_be_run(corpus):
    assert_withheld("SYMPY-C071", bundle(code_file("x = 1\n")), corpus)


def test_c071_not_applicable_without_a_contribution(corpus):
    assert_no_targets("SYMPY-C071", bundle(), corpus)


# --- C076 test function naming ------------------------------------------------------


def test_c076_passes_on_a_test_prefixed_name(corpus):
    b = bundle(tmodule("def test_widget():\n    assert True\n", is_new=True))
    assert verdict("SYMPY-C076", b, corpus).verdict == "pass"


def test_c076_fails_on_a_public_test_module_function_without_the_prefix(corpus):
    b = bundle(tmodule("def check_widget():\n    assert True\n", is_new=True))
    assert verdict("SYMPY-C076", b, corpus).verdict == "fail"


def test_c076_not_applicable_outside_a_test_module(corpus):
    b = bundle(code_file("def check_widget():\n    return True\n", is_new=True))
    assert_no_targets("SYMPY-C076", b, corpus)


# --- C078 run the local test and doctest suites -------------------------------------


def test_c078_passes_when_both_runners_were_used(corpus):
    b = bundle(code_file("x = 1\n"), commands=CLEAN)
    assert verdict("SYMPY-C078", b, corpus).verdict == "pass"


def test_c078_fails_when_only_one_runner_was_used(corpus):
    b = bundle(code_file("x = 1\n"), commands=CLEAN[:1])
    row = verdict("SYMPY-C078", b, corpus)
    assert row.verdict == "fail" and "bin/doctest" in row.notes


def test_c078_fails_when_a_runner_reported_failures(corpus):
    b = bundle(code_file("x = 1\n"),
               commands=[("python bin/test", "DO *NOT* COMMIT!"), CLEAN[1]])
    assert verdict("SYMPY-C078", b, corpus).verdict == "fail"


def test_c078_not_applicable_without_a_contribution(corpus):
    assert_no_targets("SYMPY-C078", bundle(commands=CLEAN), corpus)


# --- C084 expected exceptions use raises --------------------------------------------


RAISES_IMPORT = "from sympy.testing.pytest import raises\n"


def test_c084_passes_when_the_sympy_helper_is_used(corpus):
    b = bundle(tmodule(
        RAISES_IMPORT + "def test_bad():\n    raises(ValueError, lambda: f())\n"))
    assert verdict("SYMPY-C084", b, corpus).verdict == "pass"


def test_c084_fails_on_a_try_except_exception_test(corpus):
    b = bundle(tmodule("""\
        def test_bad():
            try:
                f()
            except ValueError:
                pass
        """))
    assert verdict("SYMPY-C084", b, corpus).verdict == "fail"


def test_c084_fails_when_raises_comes_from_pytest(corpus):
    b = bundle(tmodule(
        "from pytest import raises\n"
        "def test_bad():\n    raises(ValueError, lambda: f())\n"))
    assert verdict("SYMPY-C084", b, corpus).verdict == "fail"


def test_c084_not_applicable_when_no_exception_is_tested(corpus):
    assert_no_targets("SYMPY-C084",
                      bundle(tmodule("def test_ok():\n    assert f() == 1\n")), corpus)


# --- C085 raises wraps its code in a lambda -----------------------------------------


def test_c085_passes_on_the_lambda_form(corpus):
    b = bundle(tmodule(
        RAISES_IMPORT + "def test_bad():\n    raises(ValueError, lambda: f(1))\n"))
    assert verdict("SYMPY-C085", b, corpus).verdict == "pass"


def test_c085_fails_when_the_code_is_evaluated_eagerly(corpus):
    b = bundle(tmodule(
        RAISES_IMPORT + "def test_bad():\n    raises(ValueError, f(1))\n"))
    assert verdict("SYMPY-C085", b, corpus).verdict == "fail"


def test_c085_not_applicable_for_the_context_manager_form(corpus):
    b = bundle(tmodule(
        RAISES_IMPORT + "def test_bad():\n    with raises(ValueError):\n        f(1)\n"))
    assert_no_targets("SYMPY-C085", b, corpus)


# --- C086 deprecation tests go through the helper -----------------------------------


def test_c086_passes_with_warns_deprecated_sympy(corpus):
    b = bundle(tmodule("""\
        def test_old():
            with warns_deprecated_sympy():
                f(SymPyDeprecationWarning)
        """))
    assert verdict("SYMPY-C086", b, corpus).verdict == "pass"


def test_c086_fails_when_the_warning_is_caught_by_hand(corpus):
    b = bundle(tmodule("""\
        def test_old():
            with catch_warnings(record=True) as seen:
                f()
            assert seen[0].category is SymPyDeprecationWarning
        """))
    assert verdict("SYMPY-C086", b, corpus).verdict == "fail"


def test_c086_not_applicable_to_a_test_that_never_mentions_the_warning(corpus):
    assert_no_targets("SYMPY-C086",
                      bundle(tmodule("def test_ok():\n    assert f() == 1\n")), corpus)


# --- C089 warnings set stacklevel ---------------------------------------------------


def test_c089_passes_when_stacklevel_is_set(corpus):
    b = bundle(code_file(
        "import warnings\ndef f():\n    warnings.warn('old', stacklevel=2)\n"))
    assert verdict("SYMPY-C089", b, corpus).verdict == "pass"


def test_c089_fails_without_stacklevel(corpus):
    b = bundle(code_file("import warnings\ndef f():\n    warnings.warn('old')\n"))
    assert verdict("SYMPY-C089", b, corpus).verdict == "fail"


def test_c089_not_applicable_when_no_warning_is_emitted(corpus):
    assert_no_targets("SYMPY-C089", bundle(code_file("def f():\n    return 1\n")), corpus)


# --- C090 the stacklevel escape hatch -----------------------------------------------


def test_c090_passes_when_stacklevel_checking_is_explicitly_disabled(corpus):
    b = bundle(tmodule("""\
        def test_old():
            with warns(SymPyDeprecationWarning, test_stacklevel=False):
                f()
        """))
    assert verdict("SYMPY-C090", b, corpus).verdict == "pass"


def test_c090_fails_when_warns_is_used_without_the_flag(corpus):
    b = bundle(tmodule("""\
        def test_old():
            with warns(SymPyDeprecationWarning):
                f()
        """))
    assert verdict("SYMPY-C090", b, corpus).verdict == "fail"


def test_c090_not_applicable_to_warns_on_another_category(corpus):
    b = bundle(tmodule("def test_old():\n    with warns(UserWarning):\n        f()\n"))
    assert_no_targets("SYMPY-C090", b, corpus)


# --- C091 deprecated behaviour only in its own test ---------------------------------


def test_c091_passes_when_the_deprecated_call_is_inside_the_block(corpus):
    b = bundle(tmodule("""\
        def test_old():
            with warns_deprecated_sympy():
                deprecated_thing()
        """))
    assert verdict("SYMPY-C091", b, corpus).verdict == "pass"


def test_c091_fails_when_deprecated_behaviour_leaks_into_an_ordinary_test(corpus):
    b = bundle(tmodule("def test_other():\n    assert deprecated_thing() == 1\n"))
    assert verdict("SYMPY-C091", b, corpus).verdict == "fail"


def test_c091_not_applicable_to_a_test_with_no_deprecation(corpus):
    assert_no_targets("SYMPY-C091",
                      bundle(tmodule("def test_ok():\n    assert f() == 1\n")), corpus)


# --- C094 unevaluated assertions use unchanged --------------------------------------


def test_c094_passes_with_unchanged(corpus):
    b = bundle(tmodule("def test_keep():\n    assert unchanged(Add, x, y)\n"))
    assert verdict("SYMPY-C094", b, corpus).verdict == "pass"


def test_c094_fails_when_two_identical_evaluations_are_compared(corpus):
    b = bundle(tmodule(
        "def test_keep():\n"
        "    assert Add(x, y, evaluate=False) == Add(x, y, evaluate=False)\n"))
    assert verdict("SYMPY-C094", b, corpus).verdict == "fail"


def test_c094_not_applicable_to_an_ordinary_assertion(corpus):
    assert_no_targets("SYMPY-C094",
                      bundle(tmodule("def test_ok():\n    assert f(x) == 3\n")), corpus)


# --- C095 Dummy results use dummy_eq ------------------------------------------------


def test_c095_passes_with_dummy_eq(corpus):
    b = bundle(tmodule(
        "def test_d():\n    assert result.dummy_eq(f(Dummy('x')))\n"))
    assert verdict("SYMPY-C095", b, corpus).verdict == "pass"


def test_c095_fails_on_a_direct_equality(corpus):
    b = bundle(tmodule("def test_d():\n    assert result == f(Dummy('x'))\n"))
    assert verdict("SYMPY-C095", b, corpus).verdict == "fail"


def test_c095_not_applicable_without_a_dummy(corpus):
    assert_no_targets("SYMPY-C095",
                      bundle(tmodule("def test_ok():\n    assert result == 3\n")), corpus)


# --- C097 random tests are re-run ---------------------------------------------------


def test_c097_is_withheld_for_a_random_test(corpus):
    b = bundle(tmodule(
        "def test_r():\n    assert f(random_complex_number()) is not None\n"))
    assert_withheld("SYMPY-C097", b, corpus)


def test_c097_not_applicable_to_a_deterministic_test(corpus):
    assert_no_targets("SYMPY-C097",
                      bundle(tmodule("def test_ok():\n    assert f(1) == 1\n")), corpus)


# --- C098 / C099 skip markers -------------------------------------------------------


def test_c098_passes_when_an_expected_failure_uses_xfail(corpus):
    b = bundle(tmodule("@XFAIL\ndef test_broken():\n    assert f() == 1\n"))
    assert verdict("SYMPY-C098", b, corpus).verdict == "pass"


def test_c098_fails_when_an_expected_failure_uses_skip(corpus):
    b = bundle(tmodule(
        "@SKIP('this fails on master')\ndef test_broken():\n    assert f() == 1\n"))
    assert verdict("SYMPY-C098", b, corpus).verdict == "fail"


def test_c098_not_applicable_to_a_test_that_is_not_skipped(corpus):
    assert_no_targets("SYMPY-C098",
                      bundle(tmodule("def test_ok():\n    assert f() == 1\n")), corpus)


def test_c099_passes_when_a_slow_test_uses_the_slow_marker(corpus):
    b = bundle(tmodule("@slow\ndef test_big():\n    assert f() == 1\n"))
    assert verdict("SYMPY-C099", b, corpus).verdict == "pass"


def test_c099_fails_when_a_slow_test_is_skipped_instead(corpus):
    b = bundle(tmodule("@SKIP('too slow')\ndef test_big():\n    assert f() == 1\n"))
    assert verdict("SYMPY-C099", b, corpus).verdict == "fail"


def test_c099_not_applicable_to_a_test_that_is_not_skipped(corpus):
    assert_no_targets("SYMPY-C099",
                      bundle(tmodule("def test_ok():\n    assert f() == 1\n")), corpus)


# --- C102 / C104 / C105 need the tests run ------------------------------------------


def test_c102_is_withheld_for_an_xfail_test(corpus):
    b = bundle(tmodule("@XFAIL\ndef test_broken():\n    assert f() == 1\n"))
    assert_withheld("SYMPY-C102", b, corpus)


def test_c102_not_applicable_without_an_xfail_test(corpus):
    assert_no_targets("SYMPY-C102",
                      bundle(tmodule("def test_ok():\n    assert f() == 1\n")), corpus)


def test_c104_is_withheld_because_durations_are_not_recorded(corpus):
    assert_withheld("SYMPY-C104",
                    bundle(tmodule("def test_ok():\n    assert f() == 1\n")), corpus)


def test_c104_not_applicable_when_the_agent_wrote_no_test(corpus):
    assert_no_targets("SYMPY-C104", bundle(code_file("x = 1\n")), corpus)


def test_c105_is_withheld_because_hanging_is_only_visible_at_runtime(corpus):
    assert_withheld("SYMPY-C105",
                    bundle(tmodule("def test_ok():\n    assert f() == 1\n")), corpus)


def test_c105_not_applicable_when_the_agent_wrote_no_test(corpus):
    assert_no_targets("SYMPY-C105", bundle(code_file("x = 1\n")), corpus)


# --- C106 validating slow tests -----------------------------------------------------


SLOW_TEST = "@slow\ndef test_big():\n    assert f() == 1\n"


def test_c106_passes_when_the_slow_suite_was_run(corpus):
    b = bundle(tmodule(SLOW_TEST),
               commands=[("python bin/test --slow", "tests finished: 1 passed")])
    assert verdict("SYMPY-C106", b, corpus).verdict == "pass"


def test_c106_fails_when_the_slow_suite_was_never_run(corpus):
    assert verdict("SYMPY-C106", bundle(tmodule(SLOW_TEST)), corpus).verdict == "fail"


def test_c106_not_applicable_without_a_slow_test(corpus):
    assert_no_targets("SYMPY-C106",
                      bundle(tmodule("def test_ok():\n    assert f() == 1\n")), corpus)


# --- C107 optional dependencies -----------------------------------------------------


def test_c107_passes_when_the_dependency_goes_through_import_module(corpus):
    b = bundle(tmodule("numpy = import_module('numpy')\ndef test_n():\n    assert numpy\n"))
    assert verdict("SYMPY-C107", b, corpus).verdict == "pass"


def test_c107_fails_on_a_direct_import(corpus):
    b = bundle(tmodule("import numpy\ndef test_n():\n    assert numpy\n"))
    assert verdict("SYMPY-C107", b, corpus).verdict == "fail"


def test_c107_not_applicable_when_only_sympy_is_imported(corpus):
    b = bundle(tmodule("from sympy import Add\ndef test_n():\n    assert Add\n"))
    assert_no_targets("SYMPY-C107", b, corpus)


# --- doctest fixtures ----------------------------------------------------------------


def doc_file(body: str, **kwargs) -> FileChange:
    return code_file(body, **kwargs)


DOCTEST_OK = '''\
def f(x):
    """Do a thing.

    Examples
    ========

    >>> from sympy.core.thing import f
    >>> from sympy.abc import x
    >>> f(x)
    x
    """
    return x
'''

DOCTEST_NO_EXAMPLES = '''\
def f(x):
    """Do a thing."""
    return x
'''


# --- C112 doctests must be run ------------------------------------------------------


def test_c112_passes_when_bin_doctest_was_run(corpus):
    b = bundle(doc_file(DOCTEST_OK), commands=[CLEAN[1]])
    assert verdict("SYMPY-C112", b, corpus).verdict == "pass"


def test_c112_fails_when_the_doctest_runner_was_never_used(corpus):
    assert verdict("SYMPY-C112", bundle(doc_file(DOCTEST_OK)), corpus).verdict == "fail"


def test_c112_not_applicable_without_a_doctest(corpus):
    assert_no_targets("SYMPY-C112", bundle(doc_file(DOCTEST_NO_EXAMPLES)), corpus)


# --- C113 doctests import what they call --------------------------------------------


def test_c113_passes_when_every_called_name_is_imported(corpus):
    assert verdict("SYMPY-C113", bundle(doc_file(DOCTEST_OK)), corpus).verdict == "pass"


def test_c113_fails_on_an_unimported_call(corpus):
    b = bundle(doc_file('''\
        def f(x):
            """Do a thing.

            >>> from sympy.abc import x
            >>> simplify(x)
            x
            """
            return x
        '''))
    assert verdict("SYMPY-C113", b, corpus).verdict == "fail"


def test_c113_not_applicable_when_the_doctest_calls_nothing(corpus):
    b = bundle(doc_file('''\
        def f(x):
            """Do a thing.

            >>> from sympy.abc import x
            >>> x
            x
            """
            return x
        '''))
    assert_no_targets("SYMPY-C113", b, corpus)


# --- C114 doctests define their symbols ---------------------------------------------


def test_c114_passes_when_symbols_come_from_sympy_abc(corpus):
    assert verdict("SYMPY-C114", bundle(doc_file(DOCTEST_OK)), corpus).verdict == "pass"


def test_c114_fails_on_an_undefined_symbol(corpus):
    b = bundle(doc_file('''\
        def f(x):
            """Do a thing.

            >>> from sympy.core.thing import f
            >>> f(y)
            y
            """
            return x
        '''))
    assert verdict("SYMPY-C114", b, corpus).verdict == "fail"


def test_c114_not_applicable_when_no_symbol_is_used(corpus):
    b = bundle(doc_file('''\
        def f(x):
            """Do a thing.

            >>> from sympy.core.thing import f
            >>> f(1)
            1
            """
            return x
        '''))
    assert_no_targets("SYMPY-C114", b, corpus)


# --- C115 exact doctest output ------------------------------------------------------


def test_c115_is_withheld_because_exactness_needs_a_run(corpus):
    assert_withheld("SYMPY-C115", bundle(doc_file(DOCTEST_OK)), corpus)


def test_c115_not_applicable_without_a_doctest(corpus):
    assert_no_targets("SYMPY-C115", bundle(doc_file(DOCTEST_NO_EXAMPLES)), corpus)


# --- C118 dependency doctests declare their libraries -------------------------------


def test_c118_passes_when_the_dependency_is_declared(corpus):
    b = bundle(doc_file('''\
        @doctest_depends_on(modules=('numpy',))
        def f(x):
            """Do a thing.

            >>> import numpy
            >>> numpy.array([1])
            array([1])
            """
            return x
        '''))
    assert verdict("SYMPY-C118", b, corpus).verdict == "pass"


def test_c118_fails_when_the_example_is_silenced_with_skip(corpus):
    b = bundle(doc_file('''\
        def f(x):
            """Do a thing.

            >>> import numpy  # doctest: +SKIP
            >>> numpy.array([1])  # doctest: +SKIP
            array([1])
            """
            return x
        '''))
    assert verdict("SYMPY-C118", b, corpus).verdict == "fail"


def test_c118_not_applicable_to_a_dependency_free_doctest(corpus):
    assert_no_targets("SYMPY-C118", bundle(doc_file(DOCTEST_OK)), corpus)


# --- C119 blank lines in expected output --------------------------------------------


def test_c119_passes_when_the_marker_is_used(corpus):
    b = bundle(doc_file('''\
        def f(x):
            """Do a thing.

            >>> print(f(x))
            a
            <BLANKLINE>
            b
            """
            return x
        '''))
    assert verdict("SYMPY-C119", b, corpus).verdict == "pass"


def test_c119_fails_when_output_resumes_after_a_raw_blank_line(corpus):
    b = bundle(doc_file('''\
        def f(x):
            """Do a thing.

            >>> print(f(x))
            a

            b
            """
            return x
        '''))
    assert verdict("SYMPY-C119", b, corpus).verdict == "fail"


def test_c119_not_applicable_when_prose_follows_the_example(corpus):
    """Docstring prose wraps across lines, so the sentence has to be judged whole --
    the defect that made this rule fail a stock SymPy docstring on first run."""
    b = bundle(doc_file('''\
        def f(x):
            """Do a thing.

            >>> print(f(x))
            a

            Floats are automatically converted to Rational unless the
            evaluate flag is False:

            >>> print(f(x))
            a
            """
            return x
        '''))
    assert_no_targets("SYMPY-C119", b, corpus)


# --- C126 None results are printed --------------------------------------------------


def test_c126_passes_when_none_is_printed(corpus):
    b = bundle(doc_file('''\
        def f(x):
            """Do a thing.

            >>> print(f(1))
            None
            """
            return None
        '''))
    assert verdict("SYMPY-C126", b, corpus).verdict == "pass"


def test_c126_fails_on_a_bare_expression_expecting_none(corpus):
    b = bundle(doc_file('''\
        def f(x):
            """Do a thing.

            >>> f(1)
            None
            """
            return None
        '''))
    assert verdict("SYMPY-C126", b, corpus).verdict == "fail"


def test_c126_not_applicable_when_nothing_returns_none(corpus):
    assert_no_targets("SYMPY-C126", bundle(doc_file(DOCTEST_OK)), corpus)


# --- C130 replaced expectations -----------------------------------------------------


def test_c130_is_withheld_when_an_expectation_was_replaced(corpus):
    change = FileChange(
        path=TEST_PATH,
        authored_lines=frozenset({2}),
        added_lines=((2, "    assert f(x) == 3"),),
        removed_lines=("    assert f(x) == 2",),
        head_text="def test_f():\n    assert f(x) == 3\n",
    )
    assert_withheld("SYMPY-C130", bundle(change), corpus)


def test_c130_not_applicable_when_nothing_was_replaced(corpus):
    assert_no_targets("SYMPY-C130",
                      bundle(tmodule("def test_f():\n    assert f(x) == 3\n",
                                       is_new=True)), corpus)


# --- C137 / C142 exact versus float values ------------------------------------------


def test_c137_passes_on_an_exact_sympy_value(corpus):
    b = bundle(tmodule("def test_half():\n    assert f(S(1)/2) == 0\n"))
    assert verdict("SYMPY-C137", b, corpus).verdict == "pass"


def test_c137_fails_on_python_integer_division(corpus):
    b = bundle(tmodule("def test_half():\n    assert f(1/2) == 0\n"))
    assert verdict("SYMPY-C137", b, corpus).verdict == "fail"


def test_c137_not_applicable_inside_a_float_test(corpus):
    b = bundle(tmodule("def test_float_half():\n    assert f(1/2) == 0\n"))
    assert_no_targets("SYMPY-C137", b, corpus)


def test_c137_still_judges_a_test_that_merely_says_surround(corpus):
    """`sur-round` is not a float test."""
    b = bundle(tmodule("def test_surround():\n    assert f(1/2) == 0\n"))
    assert verdict("SYMPY-C137", b, corpus).verdict == "fail"


def test_c142_passes_on_an_explicit_float_literal(corpus):
    b = bundle(tmodule("def test_float_half():\n    assert f(0.5) == 0\n"))
    assert verdict("SYMPY-C142", b, corpus).verdict == "pass"


def test_c142_fails_when_a_float_test_uses_integer_division(corpus):
    b = bundle(tmodule("def test_float_half():\n    assert f(1/2) == 0\n"))
    assert verdict("SYMPY-C142", b, corpus).verdict == "fail"


def test_c142_not_applicable_outside_a_float_test(corpus):
    b = bundle(tmodule("def test_half():\n    assert f(S(1)/2) == 0\n"))
    assert_no_targets("SYMPY-C142", b, corpus)


# --- C139 compare expressions, not their strings ------------------------------------


def test_c139_passes_when_expressions_are_compared_directly(corpus):
    b = bundle(tmodule("def test_eq():\n    assert f(x) == g(x)\n"))
    assert verdict("SYMPY-C139", b, corpus).verdict == "pass"


def test_c139_fails_when_a_str_form_is_compared(corpus):
    b = bundle(tmodule("def test_eq():\n    assert str(f(x)) == 'x + 1'\n"))
    assert verdict("SYMPY-C139", b, corpus).verdict == "fail"


def test_c139_not_applicable_inside_a_printer_test(corpus):
    b = bundle(tmodule("def test_str_printing():\n    assert str(f(x)) == 'x + 1'\n"))
    assert_no_targets("SYMPY-C139", b, corpus)


def test_c139_still_judges_a_test_whose_name_merely_contains_printer_letters(corpus):
    """`con-str-uctor` is not a printer test. Substring matching silently excluded three
    real assertions in the pilot, and an over-narrow pre-condition raises nothing --
    it just shrinks the denominator."""
    b = bundle(tmodule(
        "def test_non_disjoint_cycles_constructor():\n    assert f(x) == g(x)\n"))
    assert verdict("SYMPY-C139", b, corpus).verdict == "pass"


# --- C140 construct expressions directly --------------------------------------------


def test_c140_passes_when_sympify_is_given_a_non_string(corpus):
    b = bundle(tmodule("def test_values():\n    assert sympify(1) == f(x)\n"))
    assert verdict("SYMPY-C140", b, corpus).verdict == "pass"


def test_c140_fails_when_a_test_input_is_a_string_expression(corpus):
    b = bundle(tmodule("def test_values():\n    assert sympify('x + 1') == f(x)\n"))
    assert verdict("SYMPY-C140", b, corpus).verdict == "fail"


def test_c140_not_applicable_inside_a_parser_test(corpus):
    b = pyfile("sympy/parsing/tests/test_expr.py",
               "def test_values():\n    assert sympify('x + 1') == f(x)\n")
    assert_no_targets("SYMPY-C140", bundle(b), corpus)


def test_c140_still_judges_a_sparse_matrix_test(corpus):
    """`s-pars-e` is not a parser test."""
    b = pyfile("sympy/matrices/tests/test_sparse.py",
               "def test_sparse_values():\n    assert sympify('x + 1') == f(x)\n")
    assert verdict("SYMPY-C140", bundle(b), corpus).verdict == "fail"


# --- C141 assumptions compared identically ------------------------------------------


def test_c141_passes_on_an_identity_comparison(corpus):
    b = bundle(tmodule("def test_a():\n    assert x.is_positive is True\n"))
    assert verdict("SYMPY-C141", b, corpus).verdict == "pass"


def test_c141_fails_when_the_assertion_relies_on_truthiness(corpus):
    b = bundle(tmodule("def test_a():\n    assert x.is_positive\n"))
    assert verdict("SYMPY-C141", b, corpus).verdict == "fail"


def test_c141_not_applicable_to_a_class_predicate(corpus):
    b = bundle(tmodule("def test_a():\n    assert x.is_Symbol\n"))
    assert_no_targets("SYMPY-C141", b, corpus)


# --- unparsable input is never a violation ------------------------------------------


BROKEN = "def test_x():\n    ssert f(1) == 1\n"


def test_an_unparsable_file_leaves_conditional_rules_unanswerable(corpus):
    """One pilot agent wrote `ssert` for `assert` through a bad `sed`, shipping a module
    that will not import.

    These rules stay withheld rather than failed, and the reason is the corpus, not caution.
    Nearly all of them are conditional -- C076 *"a test function must be named `test_`"*,
    C084 *"when testing an expected exception, use `raises`"*. Failing those on a file that
    does not parse asserts both that the situation arose and that the agent got it wrong, and
    neither is observable once the parse fails. The verdict would be manufactured.

    Where the parse error *is* provable non-compliance it is failed at the rule that can
    prove it -- see `test_a_broken_file_fails_the_rules_it_provably_defeats`.
    """
    b = bundle(pyfile(TEST_PATH, BROKEN))
    category = [rid for rid, r in RULES.items() if r.category == CATEGORY]
    rows = [verdict(rule_id, b, corpus) for rule_id in category]
    fabricated = [r.rule_id for r in rows
                  if r.verdict == "fail" and any(
                      t["key"].startswith("unreadable:") for t in r.targets)]
    assert fabricated == [], f"conditional rules failed on an unestablished antecedent: {fabricated}"
    assert any(r.status == "parse_error" for r in rows), \
        "the parse failure must still be recorded, not silently not_applicable"


def test_a_broken_file_does_not_condemn_a_clean_one_beside_it(corpus):
    """Scoped to the file, because targets are per-file. A second module that parses is
    judged on its own contents, not on its neighbour's syntax error."""
    b = bundle(pyfile(TEST_PATH, BROKEN))
    rows = [verdict(rid, b, corpus) for rid in
            [r for r, m in RULES.items() if m.category == CATEGORY]]
    for row in rows:
        for target in row.targets:
            if not target["key"].startswith("unreadable:"):
                assert target.get("file") != TEST_PATH or "does not parse" not in row.notes

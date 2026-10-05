"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

Two things this module is pinning beyond the usual three:

* **the §7.5 exclusions.** C053 must find no target for an extension test (C054 owns it),
  and C061 must accept a `.out` file in place of a `.result.json` (C063 owns that). Both
  are asserted rather than described, so the resolution is pinned instead of remembered.
* **the placement rules are scoped `created`.** Their no-target case is a functional test
  the agent merely edited: where a file already lived is not a placement the agent made.

The fixtures use the checkout's `tests/` spelling rather than the `/pylint/test` the guide
writes, for the reason the rule module's docstring records.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pylint_dev.tests  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("pylint/checkers/typecheck.py", [(1, "x = 1")], head_text="x = 1")
DOC = make_file("doc/user_guide/usage.rst", [(1, "Usage")], head_text="Usage")


@pytest.fixture(scope="module")
def corpus():
    """pylint-dev's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pylint-dev"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def cmds(*commands):
    return tuple(Command(index=i, command=c) for i, c in enumerate(commands))


def added(path, text="x = 1\n"):
    """A file the agent created."""
    body = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(body, 1)],
                     head_text=text, is_new=True)


def edited(path, text="x = 1\n", *, lines=None, base=None):
    """A file that already existed, of which the agent wrote ``lines``."""
    body = text.split("\n")
    numbers = lines if lines is not None else range(1, len(body) + 1)
    return make_file(path, [(n, body[n - 1]) for n in numbers],
                     head_text=text, base_text=base, is_new=False)


UNIT_TEST = added("tests/checkers/unittest_typecheck.py", "def test_x():\n    pass\n")
FUNCTIONAL_PY = "x = 1\na, b = 1  # [unbalanced-tuple-unpacking]\n"
FUNCTIONAL_TXT = ("unbalanced-tuple-unpacking:2:0:2:8::Possible unbalanced tuple "
                  "unpacking:UNDEFINED\n")


# --- C003 pylint's own test suite is run ----------------------------------------------


def test_c003_passes_when_the_suite_was_run(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("python -m pytest tests/"))
    assert verdict("PYLINT-DEV-C003", bundle, corpus).verdict == "pass"


def test_c003_fails_when_the_suite_was_never_run(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("git status", "git commit -m x"))
    row = verdict("PYLINT-DEV-C003", bundle, corpus)
    assert row.verdict == "fail" and "without any pytest or tox run" in row.notes


def test_c003_finds_no_target_for_an_empty_contribution(corpus):
    row = verdict("PYLINT-DEV-C003", make_bundle(files=[], commands=cmds("tox")), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C025 tests are included with the contribution ------------------------------------


def test_c025_passes_when_a_test_is_included(corpus):
    assert verdict("PYLINT-DEV-C025", make_bundle(files=[SOURCE, UNIT_TEST]),
                   corpus).verdict == "pass"


def test_c025_fails_when_the_contribution_ships_no_test(corpus):
    row = verdict("PYLINT-DEV-C025", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "fail" and "under the test tree" in row.notes


def test_c025_finds_no_target_for_an_empty_contribution(corpus):
    row = verdict("PYLINT-DEV-C025", make_bundle(files=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C032 the -k pattern omits the .py extension --------------------------------------


def test_c032_passes_when_the_pattern_omits_the_extension(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("pytest -k unittest_typecheck"))
    assert verdict("PYLINT-DEV-C032", bundle, corpus).verdict == "pass"


def test_c032_fails_when_the_pattern_carries_the_extension(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("pytest -k unittest_typecheck.py"))
    row = verdict("PYLINT-DEV-C032", bundle, corpus)
    assert row.verdict == "fail" and ".py" in row.notes


def test_c032_finds_no_target_when_the_run_was_not_restricted(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("pytest tests/"))
    row = verdict("PYLINT-DEV-C032", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C034 the stdlib primer invocation ------------------------------------------------


def test_c034_passes_on_the_marker_and_flag_together(corpus):
    bundle = make_bundle(files=[SOURCE],
                         commands=cmds("pytest -m primer_stdlib --primer-stdlib"))
    assert verdict("PYLINT-DEV-C034", bundle, corpus).verdict == "pass"


def test_c034_fails_when_the_marker_is_missing(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("pytest --primer-stdlib tests/"))
    row = verdict("PYLINT-DEV-C034", bundle, corpus)
    assert row.verdict == "fail" and "primer_stdlib" in row.notes


def test_c034_finds_no_target_when_the_primer_was_never_run(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("pytest tests/"))
    row = verdict("PYLINT-DEV-C034", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C037 new unit tests live in the unit test directory ------------------------------


def test_c037_passes_when_the_new_test_is_under_the_test_tree(corpus):
    assert verdict("PYLINT-DEV-C037", make_bundle(files=[SOURCE, UNIT_TEST]),
                   corpus).verdict == "pass"


def test_c037_fails_when_a_new_test_is_added_beside_the_package(corpus):
    bundle = make_bundle(files=[added("pylint/test_typecheck.py", "def test_x(): pass\n")])
    row = verdict("PYLINT-DEV-C037", bundle, corpus)
    assert row.verdict == "fail" and "not under" in row.notes


def test_c037_finds_no_target_when_an_existing_test_was_only_edited(corpus):
    bundle = make_bundle(files=[edited("tests/checkers/unittest_typecheck.py",
                                       "def test_x():\n    pass\n")])
    row = verdict("PYLINT-DEV-C037", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C039 unit-test data lives in regrtest_data ---------------------------------------


def test_c039_passes_when_the_data_file_is_in_regrtest_data(corpus):
    bundle = make_bundle(files=[UNIT_TEST,
                                added("tests/regrtest_data/example.json", "{}\n")])
    assert verdict("PYLINT-DEV-C039", bundle, corpus).verdict == "pass"


def test_c039_fails_when_the_data_file_is_added_elsewhere(corpus):
    bundle = make_bundle(files=[UNIT_TEST, added("tests/data/example.json", "{}\n")])
    row = verdict("PYLINT-DEV-C039", bundle, corpus)
    assert row.verdict == "fail" and "not in regrtest_data" in row.notes


def test_c039_finds_no_target_when_the_change_adds_no_data_file(corpus):
    row = verdict("PYLINT-DEV-C039", make_bundle(files=[SOURCE, UNIT_TEST]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C040 a functional test has a .txt companion --------------------------------------


def test_c040_passes_when_the_txt_companion_is_added(corpus):
    bundle = make_bundle(files=[added("tests/functional/u/unbalanced_tuple.py",
                                      FUNCTIONAL_PY),
                                added("tests/functional/u/unbalanced_tuple.txt",
                                      FUNCTIONAL_TXT)])
    assert verdict("PYLINT-DEV-C040", bundle, corpus).verdict == "pass"


def test_c040_fails_when_the_test_ships_without_its_txt(corpus):
    bundle = make_bundle(files=[added("tests/functional/u/unbalanced_tuple.py",
                                      FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C040", bundle, corpus)
    assert row.verdict == "fail" and "unbalanced_tuple.txt" in row.notes


def test_c040_finds_no_target_when_no_functional_test_is_added(corpus):
    row = verdict("PYLINT-DEV-C040", make_bundle(files=[SOURCE, UNIT_TEST]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C041 the .txt records exactly what the annotations expect ------------------------


FUNC = "tests/functional/u/unbalanced_tuple.py"
FUNC_TXT = "tests/functional/u/unbalanced_tuple.txt"


def functional_pair(source=FUNCTIONAL_PY, expected=FUNCTIONAL_TXT):
    return [added(FUNC, source), added(FUNC_TXT, expected)]


def test_c041_passes_when_the_two_agree(corpus):
    assert verdict("PYLINT-DEV-C041", make_bundle(files=functional_pair()),
                   corpus).verdict == "pass"


def test_c041_fails_when_the_txt_records_a_message_the_file_does_not_expect(corpus):
    bundle = make_bundle(files=functional_pair(
        expected="no-member:1:0:1:5::Instance has no member:UNDEFINED\n"))
    row = verdict("PYLINT-DEV-C041", bundle, corpus)
    assert row.verdict == "fail" and "no-member" in row.notes


def test_c041_finds_no_target_when_the_txt_is_not_in_the_patch(corpus):
    row = verdict("PYLINT-DEV-C041", make_bundle(files=[added(FUNC, FUNCTIONAL_PY)]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C042 every expected line carries an annotation ------------------------------------


def test_c042_passes_when_every_recorded_line_is_annotated(corpus):
    assert verdict("PYLINT-DEV-C042", make_bundle(files=functional_pair()),
                   corpus).verdict == "pass"


def test_c042_fails_when_a_recorded_line_carries_no_annotation(corpus):
    bundle = make_bundle(files=functional_pair(
        expected="unbalanced-tuple-unpacking:1:0:1:5::Possible unbalanced:UNDEFINED\n"))
    row = verdict("PYLINT-DEV-C042", bundle, corpus)
    assert row.verdict == "fail" and "no `# [unbalanced-tuple-unpacking]`" in row.notes


def test_c042_finds_no_target_when_the_test_expects_no_message(corpus):
    row = verdict("PYLINT-DEV-C042", make_bundle(files=functional_pair(expected="")),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C043 several messages on one line, in one bracket comment -------------------------


TWO_IN_ONE = "a, b, c = 1.test  # [unbalanced-tuple-unpacking, no-member]\n"
TWO_BRACKETS = "a, b, c = 1.test  # [unbalanced-tuple-unpacking] # [no-member]\n"


def test_c043_passes_on_one_comma_separated_bracket(corpus):
    bundle = make_bundle(files=[added(FUNC, TWO_IN_ONE)])
    assert verdict("PYLINT-DEV-C043", bundle, corpus).verdict == "pass"


def test_c043_fails_on_two_separate_bracket_comments(corpus):
    bundle = make_bundle(files=[added(FUNC, TWO_BRACKETS)])
    row = verdict("PYLINT-DEV-C043", bundle, corpus)
    assert row.verdict == "fail" and "separate bracket comments" in row.notes


def test_c043_finds_no_target_when_only_one_message_is_expected(corpus):
    bundle = make_bundle(files=[added(FUNC, FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C043", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C045 per-test configuration is a same-named .rc -----------------------------------


def test_c045_passes_on_a_same_named_rc_beside_the_test(corpus):
    bundle = make_bundle(files=[added(FUNC, FUNCTIONAL_PY),
                                added("tests/functional/u/unbalanced_tuple.rc",
                                      "[testoptions]\nmin_pyver=3.10\n")])
    assert verdict("PYLINT-DEV-C045", bundle, corpus).verdict == "pass"


def test_c045_fails_when_the_configuration_is_not_a_same_named_rc(corpus):
    bundle = make_bundle(files=[added(FUNC, FUNCTIONAL_PY),
                                added("tests/functional/u/pylintrc",
                                      "[MESSAGES CONTROL]\ndisable=all\n")])
    row = verdict("PYLINT-DEV-C045", bundle, corpus)
    assert row.verdict == "fail" and "other than a same-named" in row.notes


def test_c045_finds_no_target_when_the_test_needs_no_configuration(corpus):
    bundle = make_bundle(files=[added(FUNC, FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C045", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C046 runner options go under [testoptions] ----------------------------------------


RC = "tests/functional/u/unbalanced_tuple.rc"


def test_c046_passes_on_a_supported_key_under_testoptions(corpus):
    bundle = make_bundle(files=[added(RC, "[testoptions]\nmax_pyver=3.14\n")])
    assert verdict("PYLINT-DEV-C046", bundle, corpus).verdict == "pass"


def test_c046_fails_on_a_key_the_runner_does_not_support(corpus):
    bundle = make_bundle(files=[added(RC, "[testoptions]\nmax_python=3.14\n")])
    row = verdict("PYLINT-DEV-C046", bundle, corpus)
    assert row.verdict == "fail" and "max_python" in row.notes


def test_c046_finds_no_target_when_the_rc_sets_no_runner_option(corpus):
    bundle = make_bundle(files=[added(RC, "[MESSAGES CONTROL]\ndisable=all\n")])
    row = verdict("PYLINT-DEV-C046", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C047 max_pyver is the first unsupported version -----------------------------------


def test_c047_passes_when_the_bound_is_above_every_recorded_version(corpus):
    bundle = make_bundle(files=[added(RC, "[testoptions]\nmax_pyver=3.14\n"),
                                added(FUNC, FUNCTIONAL_PY)])
    assert verdict("PYLINT-DEV-C047", bundle, corpus).verdict == "pass"


def test_c047_fails_when_the_bound_excludes_a_version_the_test_records_output_for(corpus):
    bundle = make_bundle(files=[
        added(RC, "[testoptions]\nmax_pyver=3.14\n"),
        added(FUNC, FUNCTIONAL_PY),
        added("tests/functional/u/unbalanced_tuple.314.txt", "")])
    row = verdict("PYLINT-DEV-C047", bundle, corpus)
    assert row.verdict == "fail" and "excludes Python 3.14" in row.notes


def test_c047_finds_no_target_when_the_test_sets_no_max_pyver(corpus):
    bundle = make_bundle(files=[added(RC, "[testoptions]\nmin_pyver=3.10\n")])
    row = verdict("PYLINT-DEV-C047", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C048 the four supported comparison operators --------------------------------------


def conditional(op):
    return f"x = 1\na = undefined  # {op}3.12:[used-before-assignment]\n"


def test_c048_passes_on_a_supported_operator(corpus):
    bundle = make_bundle(files=[added(FUNC, conditional("<"))])
    assert verdict("PYLINT-DEV-C048", bundle, corpus).verdict == "pass"


def test_c048_fails_on_an_equality_comparison(corpus):
    bundle = make_bundle(files=[added(FUNC, conditional("=="))])
    row = verdict("PYLINT-DEV-C048", bundle, corpus)
    assert row.verdict == "fail" and "supported operators" in row.notes


def test_c048_finds_no_target_when_no_annotation_is_conditional(corpus):
    bundle = make_bundle(files=[added(FUNC, FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C048", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C049 both a versioned and a default .txt ------------------------------------------


def test_c049_passes_when_both_expectation_files_are_added(corpus):
    bundle = make_bundle(files=[
        added(FUNC, conditional("<")),
        added("tests/functional/u/unbalanced_tuple.314.txt", ""),
        added(FUNC_TXT, FUNCTIONAL_TXT)])
    assert verdict("PYLINT-DEV-C049", bundle, corpus).verdict == "pass"


def test_c049_fails_when_only_the_default_txt_is_added(corpus):
    bundle = make_bundle(files=[added(FUNC, conditional("<")),
                                added(FUNC_TXT, FUNCTIONAL_TXT)])
    row = verdict("PYLINT-DEV-C049", bundle, corpus)
    assert row.verdict == "fail" and "no `<stem>.<version>.txt`" in row.notes


def test_c049_finds_no_target_when_the_output_does_not_vary_by_version(corpus):
    bundle = make_bundle(files=[added(FUNC, FUNCTIONAL_PY), added(FUNC_TXT, FUNCTIONAL_TXT)])
    row = verdict("PYLINT-DEV-C049", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C050 version bounds, not conditions, for unparsable code --------------------------


NEW_SYNTAX = "try:\n    pass\nexcept* ValueError:  # <3.12:[used-before-assignment]\n    pass\n"


def test_c050_passes_when_the_test_is_bounded_by_pyver(corpus):
    bundle = make_bundle(files=[added(FUNC, NEW_SYNTAX),
                                added(RC, "[testoptions]\nmin_pyver=3.11\n")])
    assert verdict("PYLINT-DEV-C050", bundle, corpus).verdict == "pass"


def test_c050_fails_when_unparsable_code_relies_on_conditional_annotations(corpus):
    bundle = make_bundle(files=[added(FUNC, NEW_SYNTAX)])
    row = verdict("PYLINT-DEV-C050", bundle, corpus)
    assert row.verdict == "fail" and "min_pyver/max_pyver" in row.notes


def test_c050_finds_no_target_when_the_test_is_neither_bounded_nor_conditional(corpus):
    bundle = make_bundle(files=[added(FUNC, FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C050", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C051 a case for an existing checker is appended ------------------------------------


EXISTING_CHECKER = edited("pylint/checkers/typecheck.py", "x = 1\n")
NEW_CHECKER = added("pylint/checkers/my_checker.py", "x = 1\n")


def test_c051_passes_when_the_case_joins_the_existing_test_file(corpus):
    bundle = make_bundle(files=[EXISTING_CHECKER, edited(FUNC, FUNCTIONAL_PY)])
    assert verdict("PYLINT-DEV-C051", bundle, corpus).verdict == "pass"


def test_c051_fails_when_a_new_test_file_is_created_instead(corpus):
    bundle = make_bundle(files=[EXISTING_CHECKER, added(FUNC, FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C051", bundle, corpus)
    assert row.verdict == "fail" and "already existed" in row.notes


def test_c051_finds_no_target_when_the_checker_itself_is_new(corpus):
    bundle = make_bundle(files=[NEW_CHECKER, added(FUNC, FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C051", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C052 the test file is named for the message symbol ---------------------------------


NEW_MESSAGE = added("pylint/checkers/my_checker.py", '''\
from pylint.checkers import BaseChecker


class MyChecker(BaseChecker):
    name = "my-checker"
    msgs = {"W1234": ("A", "something-wrong", "A.")}
''')


def test_c052_passes_when_the_file_is_named_for_the_symbol(corpus):
    bundle = make_bundle(files=[NEW_MESSAGE,
                                added("tests/functional/s/something_wrong.py",
                                      FUNCTIONAL_PY)])
    assert verdict("PYLINT-DEV-C052", bundle, corpus).verdict == "pass"


def test_c052_fails_when_the_file_is_named_something_else(corpus):
    bundle = make_bundle(files=[NEW_MESSAGE,
                                added("tests/functional/m/my_new_test.py", FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C052", bundle, corpus)
    assert row.verdict == "fail" and "something_wrong" in row.notes


def test_c052_finds_no_target_when_the_change_declares_no_new_symbol(corpus):
    bundle = make_bundle(files=[SOURCE, added(FUNC, FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C052", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C053 the initial-letter sub-directory ---------------------------------------------


def test_c053_passes_when_the_directory_is_the_first_letter(corpus):
    bundle = make_bundle(files=[added("tests/functional/u/unbalanced_tuple.py",
                                      FUNCTIONAL_PY)])
    assert verdict("PYLINT-DEV-C053", bundle, corpus).verdict == "pass"


def test_c053_fails_when_the_directory_is_another_letter(corpus):
    bundle = make_bundle(files=[added("tests/functional/x/unbalanced_tuple.py",
                                      FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C053", bundle, corpus)
    assert row.verdict == "fail" and "begins with" in row.notes


def test_c053_finds_no_target_for_an_extension_test(corpus):
    """The §7.5 exclusion: `functional/ext/` is C054's business, not this rule's."""
    bundle = make_bundle(files=[added("tests/functional/ext/docparams/missing_doc.py",
                                      FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C053", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C055 regression tests live in a regression directory -------------------------------


REGRESSION = "tests/functional/r/regression/regression_1234.py"


def test_c055_passes_when_the_regression_test_is_in_its_directory(corpus):
    bundle = make_bundle(files=[added(REGRESSION, FUNCTIONAL_PY)])
    assert verdict("PYLINT-DEV-C055", bundle, corpus).verdict == "pass"


def test_c055_fails_when_a_prefixed_test_is_filed_elsewhere(corpus):
    bundle = make_bundle(files=[added("tests/functional/r/regression_1234.py",
                                      FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C055", bundle, corpus)
    assert row.verdict == "fail" and "outside" in row.notes


def test_c055_finds_no_target_for_an_ordinary_functional_test(corpus):
    bundle = make_bundle(files=[added(FUNC, FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C055", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C056 the regression_ filename prefix ----------------------------------------------


def test_c056_passes_on_the_prefixed_name(corpus):
    bundle = make_bundle(files=[added(REGRESSION, FUNCTIONAL_PY)])
    assert verdict("PYLINT-DEV-C056", bundle, corpus).verdict == "pass"


def test_c056_fails_when_a_test_in_the_directory_is_not_prefixed(corpus):
    bundle = make_bundle(files=[added("tests/functional/r/regression_02/my_test.py",
                                      FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C056", bundle, corpus)
    assert row.verdict == "fail" and "regression_" in row.notes


def test_c056_finds_no_target_outside_the_regression_directories(corpus):
    bundle = make_bundle(files=[added(FUNC, FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C056", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C057 the nested sub-directory matches the first word -------------------------------


def test_c057_passes_when_the_nested_directory_is_the_first_word(corpus):
    bundle = make_bundle(files=[added("tests/functional/u/use/use_foo.py", FUNCTIONAL_PY)])
    assert verdict("PYLINT-DEV-C057", bundle, corpus).verdict == "pass"


def test_c057_fails_when_the_nested_directory_is_something_else(corpus):
    bundle = make_bundle(files=[added("tests/functional/u/using/use_foo.py",
                                      FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C057", bundle, corpus)
    assert row.verdict == "fail" and "word before its first underscore" in row.notes


def test_c057_finds_no_target_when_the_file_name_has_no_underscore(corpus):
    bundle = make_bundle(files=[added("tests/functional/u/unused.py", FUNCTIONAL_PY)])
    row = verdict("PYLINT-DEV-C057", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C059 expected output is regenerated with the flag ----------------------------------


def test_c059_passes_when_the_flag_was_used(corpus):
    bundle = make_bundle(files=[edited(FUNC_TXT, FUNCTIONAL_TXT)],
                         commands=cmds("pytest tests/test_functional.py "
                                       "--update-functional-output"))
    assert verdict("PYLINT-DEV-C059", bundle, corpus).verdict == "pass"


def test_c059_fails_when_the_expectation_was_rewritten_by_hand(corpus):
    bundle = make_bundle(files=[edited(FUNC_TXT, FUNCTIONAL_TXT)],
                         commands=cmds("pytest tests/test_functional.py"))
    row = verdict("PYLINT-DEV-C059", bundle, corpus)
    assert row.verdict == "fail" and "--update-functional-output" in row.notes


def test_c059_finds_no_target_when_the_expectation_file_is_new(corpus):
    bundle = make_bundle(files=[added(FUNC_TXT, FUNCTIONAL_TXT)],
                         commands=cmds("pytest tests/"))
    row = verdict("PYLINT-DEV-C059", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C060 a configuration test in its format's directory --------------------------------


TOML_TEST = "tests/config/functional/toml/my_config.toml"


def test_c060_passes_when_the_directory_names_the_format(corpus):
    bundle = make_bundle(files=[added(TOML_TEST, "[tool.pylint]\njobs = 10\n")])
    assert verdict("PYLINT-DEV-C060", bundle, corpus).verdict == "pass"


def test_c060_fails_when_the_format_and_the_directory_disagree(corpus):
    bundle = make_bundle(files=[added("tests/config/functional/ini/my_config.toml",
                                      "[tool.pylint]\njobs = 10\n")])
    row = verdict("PYLINT-DEV-C060", bundle, corpus)
    assert row.verdict == "fail" and "not under toml/" in row.notes


def test_c060_finds_no_target_when_no_configuration_test_is_added(corpus):
    row = verdict("PYLINT-DEV-C060", make_bundle(files=[SOURCE, UNIT_TEST]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C061 the .result.json companion -----------------------------------------------------


def test_c061_passes_when_the_result_json_is_added(corpus):
    bundle = make_bundle(files=[
        added(TOML_TEST, "[tool.pylint]\njobs = 10\n"),
        added("tests/config/functional/toml/my_config.result.json", '{"jobs": 10}\n')])
    assert verdict("PYLINT-DEV-C061", bundle, corpus).verdict == "pass"


def test_c061_passes_when_an_out_file_expresses_an_expected_failure(corpus):
    """The §7.5 exclusion: a configuration expected to crash has no resulting
    configuration to record, and C063 is the row that governs its `.out` file."""
    bundle = make_bundle(files=[
        added(TOML_TEST, "[tool.pylint]\njobs = x\n"),
        added("tests/config/functional/toml/my_config.2.out", "")])
    assert verdict("PYLINT-DEV-C061", bundle, corpus).verdict == "pass"


def test_c061_fails_when_the_test_ships_neither_companion(corpus):
    bundle = make_bundle(files=[added(TOML_TEST, "[tool.pylint]\njobs = 10\n")])
    row = verdict("PYLINT-DEV-C061", bundle, corpus)
    assert row.verdict == "fail" and "my_config.result.json" in row.notes


def test_c061_finds_no_target_when_no_configuration_test_is_added(corpus):
    row = verdict("PYLINT-DEV-C061", make_bundle(files=[SOURCE, UNIT_TEST]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C062 the .result.json records only the difference ------------------------------------


RESULT = "tests/config/functional/toml/my_config.result.json"
FULL_DUMP = "{" + ", ".join(f'"option_{n}": {n}' for n in range(20)) + "}\n"


def test_c062_passes_on_a_small_delta(corpus):
    bundle = make_bundle(files=[added(RESULT, '{"jobs": 10}\n')])
    assert verdict("PYLINT-DEV-C062", bundle, corpus).verdict == "pass"


def test_c062_fails_on_what_reads_as_a_full_configuration(corpus):
    bundle = make_bundle(files=[added(RESULT, FULL_DUMP)])
    row = verdict("PYLINT-DEV-C062", bundle, corpus)
    assert row.verdict == "fail" and "difference from it" in row.notes


def test_c062_finds_no_target_when_the_file_is_not_valid_json(corpus):
    bundle = make_bundle(files=[added(RESULT, "{jobs: 10\n")])
    row = verdict("PYLINT-DEV-C062", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C063 the .out file names its test and its exit code ----------------------------------


def test_c063_passes_on_the_name_the_guide_gives(corpus):
    bundle = make_bundle(files=[
        added(TOML_TEST, "[tool.pylint]\njobs = x\n"),
        added("tests/config/functional/toml/my_config.2.out", "")])
    assert verdict("PYLINT-DEV-C063", bundle, corpus).verdict == "pass"


def test_c063_fails_when_the_exit_code_is_missing_from_the_name(corpus):
    bundle = make_bundle(files=[
        added(TOML_TEST, "[tool.pylint]\njobs = x\n"),
        added("tests/config/functional/toml/my_config.out", "")])
    row = verdict("PYLINT-DEV-C063", bundle, corpus)
    assert row.verdict == "fail" and "error_code" in row.notes


def test_c063_finds_no_target_when_no_failure_is_expected(corpus):
    bundle = make_bundle(files=[added(TOML_TEST, "[tool.pylint]\njobs = 10\n")])
    row = verdict("PYLINT-DEV-C063", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C065 the {abspath} and {relpath} placeholders ----------------------------------------


OUT = "tests/config/functional/toml/my_config.2.out"
PLACEHOLDERS = ("************* Module {abspath}\n"
                "{relpath}:1:0: E0015: Unrecognized option found: jobs (unrecognized-option)\n")
LITERAL_PATHS = ("************* Module my_config\n"
                 "my_config.toml:1:0: E0015: Unrecognized option found: jobs\n")


def test_c065_passes_when_both_placeholders_are_used(corpus):
    bundle = make_bundle(files=[added(OUT, PLACEHOLDERS)])
    assert verdict("PYLINT-DEV-C065", bundle, corpus).verdict == "pass"


def test_c065_fails_when_the_module_is_named_literally(corpus):
    bundle = make_bundle(files=[added(OUT, LITERAL_PATHS)])
    row = verdict("PYLINT-DEV-C065", bundle, corpus)
    assert row.verdict == "fail" and "{abspath}" in row.notes


def test_c065_finds_no_target_when_the_out_file_names_no_module_or_file(corpus):
    bundle = make_bundle(files=[added(OUT, "usage: pylint [options]\n")])
    row = verdict("PYLINT-DEV-C065", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

Half of this category names a marker, a flag or a directive, and for all of those the
satisfied case is the load-bearing one: it is what shows the pre-condition fires on the
*situation* rather than on the marker, and so that the rule can record a pass at all
(§7.1).

Two rules take the alternative triple (§9), because neither can be satisfied from a patch.
**C025** fails a doctest that is not valid Python and withholds on every other example.
**C037** fails a contribution that ships no test and withholds where one exists. **C205**
is not in that class -- it reads the harness's own run and grades both ways -- and is tested
four ways: the two failing grounds, the passing one, and the withhold when no run was
recorded.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.evaluation import EvalReport
from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.astropy.tests  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SRC = "astropy/io/fits/header.py"
TEST = "astropy/io/fits/tests/test_header.py"


def py(source: str, path: str = TEST, *, new: bool = False):
    """A Python file with every line marked as written by the agent."""
    lines = source.split("\n")
    return make_file(path, [(n, text) for n, text in enumerate(lines, start=1)],
                     head_text=source, is_new=new)


def rst(*lines: str, path: str = "docs/io/fits/index.rst"):
    source = "\n".join(lines)
    return make_file(path, [(n, text) for n, text in enumerate(lines, start=1)],
                     head_text=source)


@pytest.fixture(scope="module")
def corpus():
    """astropy's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("astropy"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def row(rule_id, files, corpus, **overrides):
    return verdict(rule_id, make_bundle(files=files, **overrides), corpus)


LIBRARY = py("def read(x):\n    return x\n", path=SRC)
DOC_ONLY = make_file("docs/io/fits/index.rst", [(1, "Text.")])


# --- C002 test modules are named for discovery ------------------------------------------


def test_c002_passes_on_the_discovery_name(corpus):
    assert row("ASTROPY-C002", [py("def test_x():\n    assert 1\n", new=True)],
               corpus).verdict == "pass"


def test_c002_fails_on_a_free_form_name(corpus):
    module = py("def test_x():\n    assert 1\n",
                path="astropy/io/fits/tests/header_checks.py", new=True)
    assert row("ASTROPY-C002", [module], corpus).verdict == "fail"


def test_c002_finds_no_target_outside_a_tests_directory(corpus):
    assert row("ASTROPY-C002", [py("x = 1\n", path=SRC, new=True)],
               corpus).verdict == "not_applicable"


# --- C003 test functions are prefixed ------------------------------------------------------


def test_c003_passes_on_a_prefixed_test(corpus):
    assert row("ASTROPY-C003", [py("def test_read():\n    assert 1\n", new=True)],
               corpus).verdict == "pass"


def test_c003_fails_on_an_unprefixed_assertion_function(corpus):
    assert row("ASTROPY-C003", [py("def check_read():\n    assert 1\n", new=True)],
               corpus).verdict == "fail"


def test_c003_finds_no_target_for_a_plain_helper(corpus):
    result = row("ASTROPY-C003", [py("def build():\n    return 1\n", new=True)], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C004 test classes ---------------------------------------------------------------------


def test_c004_passes_on_a_prefixed_class(corpus):
    module = py("class TestHeader:\n    def test_read(self):\n        assert 1\n", new=True)
    assert row("ASTROPY-C004", [module], corpus).verdict == "pass"


def test_c004_fails_on_a_class_with_an_init(corpus):
    module = py("class TestHeader:\n    def __init__(self):\n        self.x = 1\n"
                "    def test_read(self):\n        assert 1\n", new=True)
    assert row("ASTROPY-C004", [module], corpus).verdict == "fail"


def test_c004_finds_no_target_for_a_class_holding_no_tests(corpus):
    module = py("class Helper:\n    def build(self):\n        return 1\n", new=True)
    result = row("ASTROPY-C004", [module], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C006 a sub-package's tests live in its tests directory ------------------------------------


def test_c006_passes_inside_the_tests_directory(corpus):
    assert row("ASTROPY-C006", [py("def test_x():\n    assert 1\n", new=True)],
               corpus).verdict == "pass"


def test_c006_fails_beside_the_code(corpus):
    module = py("def test_x():\n    assert 1\n",
                path="astropy/io/fits/test_header.py", new=True)
    assert row("ASTROPY-C006", [module], corpus).verdict == "fail"


def test_c006_finds_no_target_for_library_code(corpus):
    result = row("ASTROPY-C006", [py("x = 1\n", path=SRC, new=True)], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C007 tests directories carry an __init__.py --------------------------------------------------


def test_c007_passes_when_the_init_file_is_added(corpus):
    init = py("", path="astropy/io/fits/tests/__init__.py", new=True)
    module = py("def test_x():\n    assert 1\n", new=True)
    assert row("ASTROPY-C007", [module, init], corpus).verdict == "pass"


def test_c007_fails_for_a_new_tests_directory_without_one(corpus):
    module = py("def test_x():\n    assert 1\n", path="astropy/io/new/tests/test_x.py",
                new=True)
    assert row("ASTROPY-C007", [module], corpus).verdict == "fail"


def test_c007_finds_no_target_when_no_test_module_was_added(corpus):
    result = row("ASTROPY-C007", [py("def test_x():\n    assert 1\n")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C008 cross-sub-package tests --------------------------------------------------------------------


CROSS = "from astropy.io import fits\nfrom astropy import units\n\ndef test_x():\n    assert 1\n"


def test_c008_passes_in_the_shared_directory(corpus):
    module = py(CROSS, path="astropy/tests/test_cross.py", new=True)
    assert row("ASTROPY-C008", [module], corpus).verdict == "pass"


def test_c008_fails_inside_one_sub_package(corpus):
    assert row("ASTROPY-C008", [py(CROSS, new=True)], corpus).verdict == "fail"


def test_c008_finds_no_target_for_a_single_sub_package_test(corpus):
    module = py("from astropy.io import fits\n\ndef test_x():\n    assert 1\n", new=True)
    result = row("ASTROPY-C008", [module], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C010 regression tests cite the issue URL ------------------------------------------------------------


def test_c010_passes_when_the_url_is_present(corpus):
    module = py("def test_read():\n"
                "    # https://github.com/astropy/astropy/issues/1234\n"
                "    assert 1\n", new=True)
    assert row("ASTROPY-C010", [module, LIBRARY], corpus).verdict == "pass"


def test_c010_fails_without_one(corpus):
    module = py("def test_read():\n    assert 1\n", new=True)
    assert row("ASTROPY-C010", [module, LIBRARY], corpus).verdict == "fail"


def test_c010_finds_no_target_when_no_library_code_changed(corpus):
    result = row("ASTROPY-C010", [py("def test_read():\n    assert 1\n", new=True)], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C012 remote-data tests are marked ------------------------------------------------------------------


def test_c012_passes_when_the_mark_is_present(corpus):
    module = py("import pytest\n\n@pytest.mark.remote_data\ndef test_fetch():\n"
                "    assert download_file('http://x/y.fits')\n")
    assert row("ASTROPY-C012", [module], corpus).verdict == "pass"


def test_c012_fails_without_it(corpus):
    module = py("def test_fetch():\n    assert download_file('http://x/y.fits')\n")
    assert row("ASTROPY-C012", [module], corpus).verdict == "fail"


def test_c012_finds_no_target_for_a_local_test(corpus):
    result = row("ASTROPY-C012", [py("def test_read():\n    assert 1\n")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C014 tests write into tmp_path -------------------------------------------------------------------------


def test_c014_passes_with_the_fixture(corpus):
    module = py("def test_write(tmp_path):\n"
                "    with open(tmp_path / 'f.fits', 'w') as handle:\n"
                "        handle.write('x')\n")
    assert row("ASTROPY-C014", [module], corpus).verdict == "pass"


def test_c014_fails_when_it_writes_to_a_fixed_path(corpus):
    module = py("def test_write():\n"
                "    with open('/tmp/f.fits', 'w') as handle:\n"
                "        handle.write('x')\n")
    assert row("ASTROPY-C014", [module], corpus).verdict == "fail"


def test_c014_finds_no_target_for_a_test_that_writes_nothing(corpus):
    result = row("ASTROPY-C014", [py("def test_read():\n    assert 1\n")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C016 optional-dependency tests are skippable -------------------------------------------------------------


def test_c016_passes_with_a_skipif(corpus):
    module = py("import pytest\nfrom astropy.utils.compat.optional_deps import HAS_SCIPY\n\n"
                "@pytest.mark.skipif(not HAS_SCIPY, reason='needs scipy')\n"
                "def test_fit():\n    import scipy\n    assert scipy\n")
    assert row("ASTROPY-C016", [module], corpus).verdict == "pass"


def test_c016_fails_without_a_guard(corpus):
    module = py("def test_fit():\n    import scipy\n    assert scipy\n")
    assert row("ASTROPY-C016", [module], corpus).verdict == "fail"


def test_c016_finds_no_target_without_an_optional_dependency(corpus):
    result = row("ASTROPY-C016", [py("def test_read():\n    assert 1\n")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C017 skip conditions come from the HAS_* flags --------------------------------------------------------------


def test_c017_passes_on_a_has_flag(corpus):
    module = py("import pytest\nfrom astropy.utils.compat.optional_deps import HAS_SCIPY\n\n"
                "@pytest.mark.skipif(not HAS_SCIPY, reason='needs scipy')\n"
                "def test_fit():\n    assert 1\n")
    assert row("ASTROPY-C017", [module], corpus).verdict == "pass"


def test_c017_fails_on_a_hand_rolled_condition(corpus):
    module = py("import sys\nimport pytest\n\n"
                "@pytest.mark.skipif(sys.platform == 'win32', reason='no')\n"
                "def test_fit():\n    assert 1\n")
    assert row("ASTROPY-C017", [module], corpus).verdict == "fail"


def test_c017_finds_no_target_without_a_skip_condition(corpus):
    result = row("ASTROPY-C017", [py("def test_read():\n    assert 1\n")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C020 warnings are asserted with pytest.warns ---------------------------------------------------------------------


def test_c020_passes_with_pytest_warns(corpus):
    module = py("import pytest\n\ndef test_warns():\n"
                "    with pytest.warns(UserWarning):\n        f()\n")
    assert row("ASTROPY-C020", [module], corpus).verdict == "pass"


def test_c020_fails_with_catch_warnings(corpus):
    module = py("import warnings\n\ndef test_warns():\n"
                "    with warnings.catch_warnings():\n        f()\n")
    assert row("ASTROPY-C020", [module], corpus).verdict == "fail"


def test_c020_finds_no_target_when_no_warning_is_checked(corpus):
    result = row("ASTROPY-C020", [py("def test_read():\n    assert 1\n")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C021 exceptions are asserted with pytest.raises -------------------------------------------------------------------


def test_c021_passes_with_pytest_raises(corpus):
    module = py("import pytest\n\ndef test_raises():\n"
                "    with pytest.raises(ValueError):\n        f()\n")
    assert row("ASTROPY-C021", [module], corpus).verdict == "pass"


def test_c021_fails_with_assert_raises(corpus):
    module = py("class TestRead:\n    def test_raises(self):\n"
                "        self.assertRaises(ValueError, f)\n")
    assert row("ASTROPY-C021", [module], corpus).verdict == "fail"


def test_c021_finds_no_target_when_no_exception_is_checked(corpus):
    result = row("ASTROPY-C021", [py("def test_read():\n    assert 1\n")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C023 coverage pragmas ----------------------------------------------------------------------------------------------


def test_c023_passes_on_the_published_spelling(corpus):
    module = py("def read(x):\n    if x:  # pragma: no cover\n        return 1\n", path=SRC)
    assert row("ASTROPY-C023", [module], corpus).verdict == "pass"


def test_c023_fails_on_a_misspelled_pragma(corpus):
    module = py("def read(x):\n    if x:  # pragma: nocover\n        return 1\n", path=SRC)
    assert row("ASTROPY-C023", [module], corpus).verdict == "fail"


def test_c023_finds_no_target_without_a_pragma(corpus):
    result = row("ASTROPY-C023", [py("def read(x):\n    return x\n", path=SRC)], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C024 figure tests --------------------------------------------------------------------------------------------------------


def test_c024_passes_with_the_convenience_decorator(corpus):
    module = py("from astropy.tests.figures import figure_test\n\n@figure_test\n"
                "def test_plot():\n    assert 1\n")
    assert row("ASTROPY-C024", [module], corpus).verdict == "pass"


def test_c024_fails_with_the_raw_marker(corpus):
    module = py("import pytest\n\n@pytest.mark.mpl_image_compare\n"
                "def test_plot():\n    assert 1\n")
    assert row("ASTROPY-C024", [module], corpus).verdict == "fail"


def test_c024_finds_no_target_for_a_non_figure_test(corpus):
    result = row("ASTROPY-C024", [py("def test_read():\n    assert 1\n")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C013 remote doctests ---------------------------------------------------------------------------------------------------------


def doctest_module(*example: str, path: str = SRC):
    body = "\n".join(f"    {line}" for line in example)
    return py(f'def read(x):\n    """Read it.\n\n{body}\n    """\n    return x\n', path=path)


def test_c013_passes_with_the_flag(corpus):
    module = doctest_module(">>> download_file('http://x/y.fits')  # doctest: +REMOTE_DATA",
                            "'y.fits'")
    assert row("ASTROPY-C013", [module], corpus).verdict == "pass"


def test_c013_fails_without_it(corpus):
    module = doctest_module(">>> download_file('http://x/y.fits')", "'y.fits'")
    assert row("ASTROPY-C013", [module], corpus).verdict == "fail"


def test_c013_finds_no_target_for_a_local_example(corpus):
    result = row("ASTROPY-C013", [doctest_module(">>> read(1)", "1")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C025 doctest examples run correctly ---------------------------------------------------------------------------------------------


def test_c025_fails_on_an_example_that_is_not_valid_python(corpus):
    row_ = row("ASTROPY-C025", [doctest_module(">>> read(1")], corpus)
    assert row_.verdict == "fail"


def test_c025_withholds_on_a_valid_example(corpus):
    """Whether the output matches is decided by running the doctests, not by reading them."""
    row_ = row("ASTROPY-C025", [doctest_module(">>> read(1)", "1")], corpus)
    assert row_.verdict == "not_applicable" and row_.status == "tool_missing"


def test_c025_finds_no_target_without_a_doctest(corpus):
    result = row("ASTROPY-C025", [py("def read(x):\n    return x\n", path=SRC)], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C026 non-executable examples are skipped -----------------------------------------------------------------------------------------------


def test_c026_passes_with_the_skip_flag(corpus):
    module = doctest_module(">>> read('path/to/file.fits')  # doctest: +SKIP")
    assert row("ASTROPY-C026", [module], corpus).verdict == "pass"


def test_c026_fails_without_it(corpus):
    module = doctest_module(">>> read('path/to/file.fits')")
    assert row("ASTROPY-C026", [module], corpus).verdict == "fail"


def test_c026_finds_no_target_for_a_runnable_example(corpus):
    result = row("ASTROPY-C026", [doctest_module(">>> read(1)", "1")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C027 __doctest_skip__ --------------------------------------------------------------------------------------------------------------------


def test_c027_passes_on_a_module_level_list(corpus):
    assert row("ASTROPY-C027", [py("__doctest_skip__ = ['*']\n", path=SRC)],
               corpus).verdict == "pass"


def test_c027_fails_on_a_bare_string(corpus):
    assert row("ASTROPY-C027", [py("__doctest_skip__ = '*'\n", path=SRC)],
               corpus).verdict == "fail"


def test_c027_finds_no_target_without_the_variable(corpus):
    result = row("ASTROPY-C027", [py("x = 1\n", path=SRC)], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C028 __doctest_requires__ ------------------------------------------------------------------------------------------------------------------


def test_c028_passes_on_a_module_level_dictionary(corpus):
    module = py("__doctest_requires__ = {'read': ['scipy']}\n", path=SRC)
    assert row("ASTROPY-C028", [module], corpus).verdict == "pass"


def test_c028_fails_on_a_list(corpus):
    assert row("ASTROPY-C028", [py("__doctest_requires__ = ['scipy']\n", path=SRC)],
               corpus).verdict == "fail"


def test_c028_finds_no_target_without_the_variable(corpus):
    result = row("ASTROPY-C028", [py("x = 1\n", path=SRC)], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C029 narrative doctest skipping -------------------------------------------------------------------------------------------------------------------


def test_c029_passes_with_the_directive(corpus):
    page = rst(".. doctest-skip::", "", "    >>> read(1)")
    assert row("ASTROPY-C029", [page], corpus).verdict == "pass"


def test_c029_fails_with_an_inline_flag(corpus):
    page = rst(">>> read(1)  # doctest: +SKIP")
    assert row("ASTROPY-C029", [page], corpus).verdict == "fail"


def test_c029_finds_no_target_when_nothing_is_skipped(corpus):
    result = row("ASTROPY-C029", [rst(">>> read(1)", "1")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C030 narrative doctest requirements ---------------------------------------------------------------------------------------------------------------------


def test_c030_passes_with_the_directive(corpus):
    page = rst(".. doctest-requires:: scipy", "", "    >>> read(1)")
    assert row("ASTROPY-C030", [page], corpus).verdict == "pass"


def test_c030_fails_with_the_module_variable(corpus):
    page = rst("__doctest_requires__ = {'*': ['scipy']}")
    assert row("ASTROPY-C030", [page], corpus).verdict == "fail"


def test_c030_finds_no_target_when_nothing_is_gated(corpus):
    result = row("ASTROPY-C030", [rst(">>> read(1)", "1")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C032 ignored doctest output --------------------------------------------------------------------------------------------------------------------------------


def test_c032_passes_with_the_flag(corpus):
    module = doctest_module(">>> read(1)  # doctest: +IGNORE_OUTPUT", "whatever")
    assert row("ASTROPY-C032", [module], corpus).verdict == "pass"


def test_c032_fails_when_the_output_is_elided_with_an_ellipsis(corpus):
    module = doctest_module(">>> read(1)", "...")
    assert row("ASTROPY-C032", [module], corpus).verdict == "fail"


def test_c032_finds_no_target_when_the_output_is_given(corpus):
    result = row("ASTROPY-C032", [doctest_module(">>> read(1)", "1")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C033 floating-point doctest output ------------------------------------------------------------------------------------------------------------------------------


def test_c033_passes_with_the_flag(corpus):
    module = doctest_module(">>> read(1)  # doctest: +FLOAT_CMP", "1.2345")
    assert row("ASTROPY-C033", [module], corpus).verdict == "pass"


def test_c033_fails_without_it(corpus):
    module = doctest_module(">>> read(1)", "1.2345")
    assert row("ASTROPY-C033", [module], corpus).verdict == "fail"


def test_c033_finds_no_target_for_integer_output(corpus):
    result = row("ASTROPY-C033", [doctest_module(">>> read(1)", "1")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C001 tests close the files they open ------------------------------------------------------------------------------------------------------------------------------


def test_c001_passes_on_a_context_manager(corpus):
    module = py("def test_read():\n    with open('f.fits') as handle:\n"
                "        assert handle\n")
    assert row("ASTROPY-C001", [module], corpus).verdict == "pass"


def test_c001_fails_on_an_unclosed_file(corpus):
    module = py("def test_read():\n    handle = open('f.fits')\n    assert handle\n")
    assert row("ASTROPY-C001", [module], corpus).verdict == "fail"


def test_c001_finds_no_target_for_a_test_that_opens_nothing(corpus):
    result = row("ASTROPY-C001", [py("def test_read():\n    assert 1\n")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C036 the --remote-data run --------------------------------------------------------------------------------------------------------------------------------------------


REMOTE_TEST = py("import pytest\n\n@pytest.mark.remote_data\ndef test_fetch():\n"
                 "    assert download_file('http://x/y.fits')\n")


def test_c036_passes_when_the_flag_was_used(corpus):
    commands = (Command(index=0, command="pytest astropy/io/fits --remote-data"),)
    assert row("ASTROPY-C036", [REMOTE_TEST], corpus,
               commands=commands).verdict == "pass"


def test_c036_fails_when_it_was_not(corpus):
    commands = (Command(index=0, command="pytest astropy/io/fits"),)
    assert row("ASTROPY-C036", [REMOTE_TEST], corpus, commands=commands).verdict == "fail"


def test_c036_finds_no_target_when_no_remote_data_is_involved(corpus):
    result = row("ASTROPY-C036", [py("def test_read():\n    assert 1\n")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C037 a test that fails before and passes after -----------------------------------------------------------------------------------------------------------------------------


def test_c037_fails_when_the_fix_ships_no_test(corpus):
    assert row("ASTROPY-C037", [LIBRARY], corpus).verdict == "fail"


def test_c037_withholds_when_a_test_is_present(corpus):
    """Whether it failed before the fix is decided by running it on both revisions."""
    result = row("ASTROPY-C037", [LIBRARY, py("def test_read():\n    assert 1\n")], corpus)
    assert result.verdict == "not_applicable" and result.status == "tool_missing"


def test_c037_finds_no_target_for_a_documentation_change(corpus):
    result = row("ASTROPY-C037", [DOC_ONLY], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C056 new code comes with tests ---------------------------------------------------------------------------------------------------------------------------------------------------


def test_c056_passes_when_the_sub_package_gains_a_test(corpus):
    assert row("ASTROPY-C056", [LIBRARY, py("def test_read():\n    assert 1\n")],
               corpus).verdict == "pass"


def test_c056_fails_when_no_test_is_added(corpus):
    assert row("ASTROPY-C056", [LIBRARY], corpus).verdict == "fail"


def test_c056_finds_no_target_for_a_documentation_change(corpus):
    result = row("ASTROPY-C056", [DOC_ONLY], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C201 every raised exception has a test ---------------------------------------------------------------------------------------------------------------------------------------------


RAISES = py("def read(x):\n    if not x:\n        raise ValueError('empty')\n    return x\n",
            path=SRC)


def test_c201_passes_when_a_test_asserts_it(corpus):
    module = py("import pytest\n\ndef test_read():\n"
                "    with pytest.raises(ValueError):\n        read(0)\n")
    assert row("ASTROPY-C201", [RAISES, module], corpus).verdict == "pass"


def test_c201_fails_when_nothing_tests_it(corpus):
    module = py("def test_read():\n    assert read(1) == 1\n")
    assert row("ASTROPY-C201", [RAISES, module], corpus).verdict == "fail"


def test_c201_finds_no_target_when_the_change_raises_nothing(corpus):
    result = row("ASTROPY-C201", [LIBRARY], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C205 tox -e test passes -------------------------------------------------------------------------------------------------------------------------------------------------------------


def test_c205_fails_on_python_that_will_not_parse(corpus):
    assert row("ASTROPY-C205", [py("def read(:\n", path=SRC)], corpus).verdict == "fail"


def test_c205_fails_on_a_regression_in_the_harness_report(corpus):
    report = EvalReport(shape="instance", resolved=False,
                        tests_status={"PASS_TO_PASS": {"failure": ("test_old",),
                                                       "success": ()}})
    assert row("ASTROPY-C205", [LIBRARY], corpus, evaluation=report).verdict == "fail"


def test_c205_passes_when_the_harness_reports_no_regression(corpus):
    report = EvalReport(shape="instance", resolved=True,
                        tests_status={"PASS_TO_PASS": {"success": ("test_old",),
                                                       "failure": ()}})
    assert row("ASTROPY-C205", [LIBRARY], corpus, evaluation=report).verdict == "pass"


def test_c205_withholds_when_no_run_was_recorded(corpus):
    """`evaluation` is a declared source; without it the rule may decline to grade."""
    result = row("ASTROPY-C205", [LIBRARY], corpus)
    assert result.verdict == "not_applicable" and result.status == "tool_missing"


def test_c205_finds_no_target_without_python(corpus):
    result = row("ASTROPY-C205", [DOC_ONLY], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0

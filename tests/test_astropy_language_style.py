"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

Two rules take the alternative triple (§9). **C107** withholds when no lint report exists,
so it is tested violated / withheld / no-target as well as satisfied. **C118 has no
satisfying and no violating case at all**: whether a parser accepts its own ``__str__``
output is decided by running both, so every target it selects is withheld. Its three cases
are withheld and two ways of finding no target.

The C103 no-target test is the §7.5 resolution between C098 and C103, pinned rather than
remembered: a ``print`` that C098 permits must not be graded by C103.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.lint import LintReport
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.astropy.language_style  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SRC = "astropy/io/fits/header.py"


def py(source: str, path: str = SRC, *, new: bool = False):
    """A Python file with every line marked as written by the agent."""
    lines = source.split("\n")
    return make_file(path, [(n, text) for n, text in enumerate(lines, start=1)],
                     head_text=source, is_new=new)


@pytest.fixture(scope="module")
def corpus():
    """astropy's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("astropy"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def check(rule_id, source, corpus, **kwargs):
    return verdict(rule_id, make_bundle(files=[py(source, **kwargs)]), corpus)


# --- C083 general utilities live in astropy.utils ---------------------------------------


def test_c083_passes_for_a_sub_package_module(corpus):
    row = check("ASTROPY-C083", "x = 1\n", corpus, path="astropy/io/fits/verify.py", new=True)
    assert row.verdict == "pass"


def test_c083_fails_for_a_utils_module_inside_a_sub_package(corpus):
    row = check("ASTROPY-C083", "x = 1\n", corpus, path="astropy/io/fits/utils.py", new=True)
    assert row.verdict == "fail"


def test_c083_finds_no_target_when_no_module_was_added(corpus):
    row = check("ASTROPY-C083", "x = 1\n", corpus, path="astropy/io/fits/utils.py")
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C098 print only for requested output ------------------------------------------------


def test_c098_passes_inside_an_output_function(corpus):
    row = check("ASTROPY-C098", "def print_header(h):\n    print(h)\n", corpus)
    assert row.verdict == "pass"


def test_c098_fails_inside_ordinary_library_code(corpus):
    row = check("ASTROPY-C098", "def compute(x):\n    print(x)\n    return x\n", corpus)
    assert row.verdict == "fail"


def test_c098_finds_no_target_in_a_test_module(corpus):
    row = check("ASTROPY-C098", "def test_x():\n    print(1)\n", corpus,
                path="astropy/io/fits/tests/test_header.py")
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C099 errors are raised exception classes --------------------------------------------


def test_c099_passes_on_a_raised_exception_class(corpus):
    row = check("ASTROPY-C099", "def f(x):\n    raise ValueError('bad')\n", corpus)
    assert row.verdict == "pass"


def test_c099_fails_when_an_error_is_signalled_by_assert_false(corpus):
    row = check("ASTROPY-C099", "def f(x):\n    if x:\n        assert False\n", corpus)
    assert row.verdict == "fail"


def test_c099_finds_no_target_when_nothing_signals_an_error(corpus):
    row = check("ASTROPY-C099", "def f(x):\n    return x + 1\n", corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C100 no bare Exception ---------------------------------------------------------------


def test_c100_passes_on_a_specific_exception(corpus):
    row = check("ASTROPY-C100", "def f():\n    raise ValueError('bad')\n", corpus)
    assert row.verdict == "pass"


def test_c100_fails_on_the_bare_exception_class(corpus):
    row = check("ASTROPY-C100", "def f():\n    raise Exception('bad')\n", corpus)
    assert row.verdict == "fail"


def test_c100_finds_no_target_without_a_raise(corpus):
    row = check("ASTROPY-C100", "def f():\n    return 1\n", corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C101 warnings go through warnings.warn ----------------------------------------------


WARN_IMPORTS = "import warnings\nfrom astropy.utils.exceptions import AstropyUserWarning\n"


def test_c101_passes_on_warnings_warn_with_a_class(corpus):
    row = check("ASTROPY-C101",
                WARN_IMPORTS + "def f():\n    warnings.warn('m', AstropyUserWarning)\n",
                corpus)
    assert row.verdict == "pass"


def test_c101_fails_when_the_warning_goes_through_the_logger(corpus):
    row = check("ASTROPY-C101",
                "from astropy import log\ndef f():\n    log.warning('m')\n", corpus)
    assert row.verdict == "fail"


def test_c101_finds_no_target_when_nothing_warns(corpus):
    row = check("ASTROPY-C101", "def f():\n    return 1\n", corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C102 the warning class ---------------------------------------------------------------


def test_c102_passes_with_astropy_user_warning(corpus):
    row = check("ASTROPY-C102",
                WARN_IMPORTS + "def f():\n    warnings.warn('m', AstropyUserWarning)\n",
                corpus)
    assert row.verdict == "pass"


def test_c102_fails_with_a_built_in_warning_class(corpus):
    row = check("ASTROPY-C102",
                "import warnings\ndef f():\n    warnings.warn('m', DeprecationWarning)\n",
                corpus)
    assert row.verdict == "fail"


def test_c102_finds_no_target_when_no_class_is_named(corpus):
    """Naming no class at all is C101's business, not this rule's."""
    row = check("ASTROPY-C102", "import warnings\ndef f():\n    warnings.warn('m')\n",
                corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C103 informational messages go through log -------------------------------------------


def test_c103_passes_on_log_info(corpus):
    row = check("ASTROPY-C103", "from astropy import log\ndef f():\n    log.info('m')\n",
                corpus)
    assert row.verdict == "pass"


def test_c103_fails_when_an_informational_message_is_printed(corpus):
    row = check("ASTROPY-C103", "def compute(x):\n    print('starting')\n    return x\n",
                corpus)
    assert row.verdict == "fail"


def test_c103_finds_no_target_for_a_print_c098_permits(corpus):
    """§7.5: the two rules would otherwise contradict each other on the same line."""
    row = check("ASTROPY-C103", "def print_header(h):\n    print(h)\n", corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C105 ruff format would change nothing -------------------------------------------------


def test_c105_passes_on_cleanly_formatted_lines(corpus):
    row = check("ASTROPY-C105", "def f():\n    return 1\n", corpus)
    assert row.verdict == "pass"


def test_c105_fails_on_trailing_whitespace(corpus):
    row = check("ASTROPY-C105", "def f():\n    return 1   \n", corpus)
    assert row.verdict == "fail"


def test_c105_finds_no_target_when_no_python_was_written(corpus):
    doc = make_file("docs/index.rst", [(1, "Text.")])
    row = verdict("ASTROPY-C105", make_bundle(files=[doc]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C106 imports are sorted ----------------------------------------------------------------


def test_c106_passes_when_the_groups_are_in_order(corpus):
    row = check("ASTROPY-C106", "import os\nimport numpy\nfrom astropy import units\n", corpus)
    assert row.verdict == "pass"


def test_c106_fails_when_a_group_comes_out_of_order(corpus):
    row = check("ASTROPY-C106", "from astropy import units\nimport os\n", corpus)
    assert row.verdict == "fail"


def test_c106_finds_no_target_for_a_single_import(corpus):
    row = check("ASTROPY-C106", "import os\n", corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C107 ruff checks pass ---------------------------------------------------------------


def test_c107_passes_on_a_clean_lint_report(corpus):
    bundle = make_bundle(files=[py("x = 1\n")],
                         lint={"ruff": LintReport(shape="report", tool="ruff")})
    assert verdict("ASTROPY-C107", bundle, corpus).verdict == "pass"


def test_c107_fails_on_python_that_will_not_parse(corpus):
    row = check("ASTROPY-C107", "def f(:\n", corpus)
    assert row.verdict == "fail"


def test_c107_withholds_when_no_linter_was_run(corpus):
    row = check("ASTROPY-C107", "x = 1\n", corpus)
    assert row.verdict == "not_applicable" and row.status == "tool_missing"


def test_c107_finds_no_target_without_python(corpus):
    doc = make_file("docs/index.rst", [(1, "Text.")])
    row = verdict("ASTROPY-C107", make_bundle(files=[doc]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C108 the licence line -----------------------------------------------------------------


LICENCE = "# Licensed under a 3-clause BSD style license - see LICENSE.rst"


def test_c108_passes_when_the_file_opens_with_it(corpus):
    row = check("ASTROPY-C108", LICENCE + "\nx = 1\n", corpus)
    assert row.verdict == "pass"


def test_c108_fails_when_the_file_opens_with_something_else(corpus):
    row = check("ASTROPY-C108", '"""A module."""\nx = 1\n', corpus)
    assert row.verdict == "fail"


def test_c108_finds_no_target_for_a_documentation_only_change(corpus):
    doc = make_file("docs/index.rst", [(1, "Text.")])
    row = verdict("ASTROPY-C108", make_bundle(files=[doc]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C110 state is exposed as attributes ---------------------------------------------------


def test_c110_passes_on_an_ordinary_method(corpus):
    row = check("ASTROPY-C110", "class Star:\n    def compute(self):\n        return 1\n",
                corpus)
    assert row.verdict == "pass"


def test_c110_fails_on_a_trivial_accessor(corpus):
    row = check("ASTROPY-C110",
                "class Star:\n    def get_color(self):\n        return self._color\n", corpus)
    assert row.verdict == "fail"


def test_c110_finds_no_target_for_a_module_level_function(corpus):
    row = check("ASTROPY-C110", "def get_color(obj):\n    return obj._color\n", corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C111 super-class calls go through super() ---------------------------------------------


def test_c111_passes_on_a_super_call(corpus):
    row = check("ASTROPY-C111",
                "class Star(Body):\n    def __init__(self, x):\n"
                "        super().__init__(x)\n", corpus)
    assert row.verdict == "pass"


def test_c111_fails_on_a_direct_super_class_call(corpus):
    row = check("ASTROPY-C111",
                "class Star(Body):\n    def __init__(self, x):\n"
                "        Body.__init__(self, x)\n", corpus)
    assert row.verdict == "fail"


def test_c111_finds_no_target_for_an_ordinary_method_call(corpus):
    row = check("ASTROPY-C111",
                "class Star:\n    def go(self):\n        self.step(1)\n", corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C116 __repr__ is ASCII ----------------------------------------------------------------


def test_c116_passes_on_an_ascii_repr(corpus):
    row = check("ASTROPY-C116",
                "class Star:\n    def __repr__(self):\n        return '<Star>'\n", corpus)
    assert row.verdict == "pass"


def test_c116_fails_on_a_non_ascii_repr(corpus):
    row = check("ASTROPY-C116",
                "class Star:\n    def __repr__(self):\n        return '<Star \u00b1>'\n",
                corpus)
    assert row.verdict == "fail"


def test_c116_finds_no_target_when_no_repr_was_written(corpus):
    row = check("ASTROPY-C116", "class Star:\n    def go(self):\n        return 1\n", corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C117 __str__ is ASCII unless unicode_output --------------------------------------------


def test_c117_passes_on_an_ascii_str(corpus):
    row = check("ASTROPY-C117",
                "class Star:\n    def __str__(self):\n        return 'Star'\n", corpus)
    assert row.verdict == "pass"


def test_c117_fails_on_unconditional_non_ascii(corpus):
    row = check("ASTROPY-C117",
                "class Star:\n    def __str__(self):\n        return 'Star \u00b1'\n", corpus)
    assert row.verdict == "fail"


def test_c117_finds_no_target_when_no_str_was_written(corpus):
    row = check("ASTROPY-C117", "class Star:\n    def go(self):\n        return 1\n", corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C118 the parser accepts its own __str__ output -----------------------------------------


ROUNDTRIP = ("class Angle:\n"
             "    def __str__(self):\n"
             "        return '1d'\n"
             "    @classmethod\n"
             "    def parse(cls, text):\n"
             "        return cls()\n")


def test_c118_withholds_on_a_round_trippable_class(corpus):
    """No satisfying or violating case exists: the answer needs both halves executed."""
    row = check("ASTROPY-C118", ROUNDTRIP, corpus)
    assert row.verdict == "not_applicable" and row.status == "tool_missing"
    assert row.n_targets == 1


def test_c118_finds_no_target_for_a_class_with_no_parser(corpus):
    row = check("ASTROPY-C118",
                "class Angle:\n    def __str__(self):\n        return '1d'\n", corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c118_finds_no_target_when_no_class_was_written(corpus):
    row = check("ASTROPY-C118", "def f():\n    return 1\n", corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

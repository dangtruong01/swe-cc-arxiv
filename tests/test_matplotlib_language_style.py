"""Three cases per rule (`docs/checker-authoring.md` §9): satisfied, violated, and an
input where the pre-condition finds nothing.

**C235 has no satisfying case reachable from a bundle alone, and that is not an omission
(§9).** It is graded off a ruff run over base and head that no stored run carries, so its
cases are violated, withheld (``not_applicable`` with a non-``ok`` status, never a silent
pass) and no target.

Four of the no-target cases pin this module's §7.5 narrowings: the general-language tests
for C117--C120, ``test_c253_finds_no_target_when_the_function_forwards_the_rest`` and
``test_c254_finds_no_target_when_the_function_forwards_nothing`` (the two keyword rules
never grading the same function), and
``test_c247_finds_no_target_for_a_pre_existing_wrapper``.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.lint import Finding, LintReport
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.matplotlib.language_style  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


@pytest.fixture(scope="module")
def corpus():
    """matplotlib's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("matplotlib"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def whole(path: str, body: str, **kwargs):
    lines = body.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=body, **kwargs)


def page(body: str, path: str = "doc/users/explain/quick_start.rst"):
    return whole(path, body)


LIB = "lib/matplotlib/axes/_axes.py"


# --- C117--C120 terminology capitalisation ------------------------------------------------


def test_c117_passes_when_figure_names_the_object(corpus):
    bundle = make_bundle(files=[page("The Figure is the working space for the visual.")])
    assert verdict("MATPLOTLIB-C117", bundle, corpus).verdict == "pass"


def test_c117_fails_when_the_object_is_written_in_lower_case(corpus):
    bundle = make_bundle(files=[page("The figure is the working space for visuals.")])
    assert verdict("MATPLOTLIB-C117", bundle, corpus).verdict == "fail"


def test_c117_finds_no_target_for_the_general_language_use(corpus):
    """The guide's own contrast case, so the rule stays out of ordinary English."""
    bundle = make_bundle(files=[page("Michelle Kwan is a famous figure skater.")])
    row = verdict("MATPLOTLIB-C117", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c118_passes_when_axes_names_the_object(corpus):
    bundle = make_bundle(files=[page("An Axes is a subplot within the Figure.")])
    assert verdict("MATPLOTLIB-C118", bundle, corpus).verdict == "pass"


def test_c118_fails_when_the_object_is_written_in_lower_case(corpus):
    bundle = make_bundle(files=[page("An axes is a subplot within the Figure.")])
    assert verdict("MATPLOTLIB-C118", bundle, corpus).verdict == "fail"


def test_c118_finds_no_target_for_the_plural_of_axis(corpus):
    bundle = make_bundle(files=[page(
        "There are no standard names for the coordinate axes.")])
    row = verdict("MATPLOTLIB-C118", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c119_passes_when_artist_names_the_object(corpus):
    bundle = make_bundle(files=[page("Every Artist draws itself onto the canvas.")])
    assert verdict("MATPLOTLIB-C119", bundle, corpus).verdict == "pass"


def test_c119_fails_when_the_object_is_written_in_lower_case(corpus):
    bundle = make_bundle(files=[page("Every artist draws itself onto the canvas.")])
    assert verdict("MATPLOTLIB-C119", bundle, corpus).verdict == "fail"


def test_c119_finds_no_target_for_the_general_language_use(corpus):
    bundle = make_bundle(files=[page("The plot was drawn by a graphic artist.")])
    row = verdict("MATPLOTLIB-C119", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c120_passes_when_axis_names_the_object(corpus):
    bundle = make_bundle(files=[page("Each Axis holds the ticks and their formatter.")])
    assert verdict("MATPLOTLIB-C120", bundle, corpus).verdict == "pass"


def test_c120_fails_when_the_object_is_written_in_lower_case(corpus):
    bundle = make_bundle(files=[page("Each axis holds the ticks and their formatter.")])
    assert verdict("MATPLOTLIB-C120", bundle, corpus).verdict == "fail"


def test_c120_finds_no_target_for_a_named_mathematical_axis(corpus):
    bundle = make_bundle(files=[page("Values are measured along the x-axis.")])
    row = verdict("MATPLOTLIB-C120", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C121/C122 the two usage patterns -------------------------------------------------------


def test_c121_passes_for_the_axes_interface(corpus):
    bundle = make_bundle(files=[page("Prefer the Axes interface for library code.")])
    assert verdict("MATPLOTLIB-C121", bundle, corpus).verdict == "pass"


def test_c121_fails_for_the_object_oriented_interface(corpus):
    bundle = make_bundle(files=[page("Prefer the object-oriented interface here.")])
    assert verdict("MATPLOTLIB-C121", bundle, corpus).verdict == "fail"


def test_c121_finds_no_target_when_no_usage_pattern_is_named(corpus):
    bundle = make_bundle(files=[page("The Axes owns its ticks.")])
    row = verdict("MATPLOTLIB-C121", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c122_passes_for_the_pyplot_interface(corpus):
    bundle = make_bundle(files=[page("Scripts often use the pyplot interface.")])
    assert verdict("MATPLOTLIB-C122", bundle, corpus).verdict == "pass"


def test_c122_fails_for_the_implicit_interface(corpus):
    bundle = make_bundle(files=[page("Scripts often use the implicit interface.")])
    assert verdict("MATPLOTLIB-C122", bundle, corpus).verdict == "fail"


def test_c122_fails_when_pyplot_is_capitalised(corpus):
    bundle = make_bundle(files=[page("Pyplot keeps the current Figure on a stack.")])
    assert verdict("MATPLOTLIB-C122", bundle, corpus).verdict == "fail"


def test_c122_finds_no_target_when_pyplot_is_never_mentioned(corpus):
    bundle = make_bundle(files=[page("The Axes owns its ticks.")])
    row = verdict("MATPLOTLIB-C122", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C044 accessor pairs ---------------------------------------------------------------------


PAIRED = ("class Line2D:\n"
          "    def set_width(self, w):\n"
          "        self._width = w\n"
          "\n"
          "    def get_width(self):\n"
          "        return self._width\n")
UNPAIRED = ("class Line2D:\n"
            "    def set_width(self, w):\n"
            "        self._width = w\n")


def test_c044_passes_for_a_matching_set_get_pair(corpus):
    assert verdict("MATPLOTLIB-C044", make_bundle(files=[whole(LIB, PAIRED)]),
                   corpus).verdict == "pass"


def test_c044_fails_for_a_setter_with_no_getter(corpus):
    assert verdict("MATPLOTLIB-C044", make_bundle(files=[whole(LIB, UNPAIRED)]),
                   corpus).verdict == "fail"


def test_c044_finds_no_target_for_a_read_only_accessor(corpus):
    body = "class Line2D:\n    def get_window_extent(self):\n        return None\n"
    row = verdict("MATPLOTLIB-C044", make_bundle(files=[whole(LIB, body)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C189 helpers are private -----------------------------------------------------------------


def test_c189_passes_for_an_underscored_helper(corpus):
    body = "def _clip(x):\n    return x\n"
    assert verdict("MATPLOTLIB-C189", make_bundle(files=[whole(LIB, body, is_new=True)]),
                   corpus).verdict == "pass"


def test_c189_fails_for_a_public_undocumented_helper(corpus):
    body = "def clip(x):\n    return x\n"
    assert verdict("MATPLOTLIB-C189", make_bundle(files=[whole(LIB, body, is_new=True)]),
                   corpus).verdict == "fail"


def test_c189_finds_no_target_for_a_documented_function(corpus):
    body = 'def clip(x):\n    """Clip x."""\n    return x\n'
    row = verdict("MATPLOTLIB-C189", make_bundle(files=[whole(LIB, body, is_new=True)]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C235/C236 PEP8 and line length -------------------------------------------------------------


def test_c235_fails_when_ruff_reports_a_new_pycodestyle_finding(corpus):
    report = LintReport("report", tool="ruff",
                        new_findings=(Finding(LIB, "E225", "missing whitespace"),))
    bundle = make_bundle(files=[whole(LIB, "x=1\n")], lint={"ruff": report})
    assert verdict("MATPLOTLIB-C235", bundle, corpus).verdict == "fail"


def test_c235_withholds_when_ruff_was_never_run(corpus):
    row = verdict("MATPLOTLIB-C235", make_bundle(files=[whole(LIB, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.status != "ok"


def test_c235_ignores_the_line_length_finding_c236_owns(corpus):
    """The §7.5 partition: E501 belongs to C236, so it must not fail here too."""
    report = LintReport("report", tool="ruff",
                        new_findings=(Finding(LIB, "E501", "line too long"),))
    bundle = make_bundle(files=[whole(LIB, "x = 1\n")], lint={"ruff": report})
    assert verdict("MATPLOTLIB-C235", bundle, corpus).verdict == "pass"


def test_c235_finds_no_target_when_no_python_was_submitted(corpus):
    row = verdict("MATPLOTLIB-C235", make_bundle(files=[page("Title")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c236_passes_for_short_lines(corpus):
    assert verdict("MATPLOTLIB-C236", make_bundle(files=[whole(LIB, "x = 1\n")]),
                   corpus).verdict == "pass"


def test_c236_fails_for_a_line_over_the_limit(corpus):
    body = "x = " + "1 + " * 40 + "1\n"
    assert verdict("MATPLOTLIB-C236", make_bundle(files=[whole(LIB, body)]),
                   corpus).verdict == "fail"


def test_c236_finds_no_target_when_no_python_changed(corpus):
    row = verdict("MATPLOTLIB-C236", make_bundle(files=[page("Title")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C238/C239 imports and rcParams ---------------------------------------------------------------


def test_c238_passes_for_the_listed_alias(corpus):
    body = "import numpy as np\nimport matplotlib.pyplot as plt\n"
    assert verdict("MATPLOTLIB-C238", make_bundle(files=[whole(LIB, body)]),
                   corpus).verdict == "pass"


def test_c238_fails_for_a_non_standard_alias(corpus):
    body = "import numpy as numpy_module\n"
    assert verdict("MATPLOTLIB-C238", make_bundle(files=[whole(LIB, body)]),
                   corpus).verdict == "fail"


def test_c238_finds_no_target_for_a_module_the_guide_does_not_list(corpus):
    body = "import functools\nfrom collections import abc\n"
    row = verdict("MATPLOTLIB-C238", make_bundle(files=[whole(LIB, body)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c239_passes_when_rcparams_is_reached_through_the_module(corpus):
    body = "import matplotlib as mpl\n\n\ndef f():\n    return mpl.rcParams['lines.lw']\n"
    assert verdict("MATPLOTLIB-C239", make_bundle(files=[whole(LIB, body)]),
                   corpus).verdict == "pass"


def test_c239_fails_when_the_name_is_imported_directly(corpus):
    body = "from matplotlib import rcParams\n\n\ndef f():\n    return rcParams['lines.lw']\n"
    assert verdict("MATPLOTLIB-C239", make_bundle(files=[whole(LIB, body)]),
                   corpus).verdict == "fail"


def test_c239_finds_no_target_when_rcparams_is_never_mentioned(corpus):
    row = verdict("MATPLOTLIB-C239", make_bundle(files=[whole(LIB, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C261 user-facing warnings ------------------------------------------------------------------


def test_c261_passes_for_warn_external(corpus):
    body = "from matplotlib import _api\n\n\ndef f():\n    _api.warn_external('careful')\n"
    assert verdict("MATPLOTLIB-C261", make_bundle(files=[whole(LIB, body)]),
                   corpus).verdict == "pass"


def test_c261_fails_for_a_direct_warnings_warn(corpus):
    body = "import warnings\n\n\ndef f():\n    warnings.warn('careful')\n"
    assert verdict("MATPLOTLIB-C261", make_bundle(files=[whole(LIB, body)]),
                   corpus).verdict == "fail"


def test_c261_finds_no_target_when_nothing_warns(corpus):
    row = verdict("MATPLOTLIB-C261", make_bundle(files=[whole(LIB, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C253/C254 keyword argument processing ---------------------------------------------------------


EXPLICIT = "def draw(self, artist, *, color=None, alpha=None):\n    return color\n"
GATHERED = "def draw(self, artist, **kwargs):\n    color = kwargs.pop('color')\n    return color\n"
FORWARDS_REST = ("def draw(self, artist, *, color=None, **kwargs):\n"
                 "    artist.set(**kwargs)\n"
                 "    return color\n")
POPS_AND_FORWARDS = ("def draw(self, artist, **kwargs):\n"
                     "    color = kwargs.pop('color')\n"
                     "    artist.set(**kwargs)\n"
                     "    return color\n")
FORWARDS_ALL = "def draw(self, artist, **kwargs):\n    return artist.set(**kwargs)\n"


def test_c253_passes_when_the_keywords_are_declared(corpus):
    assert verdict("MATPLOTLIB-C253", make_bundle(files=[whole(LIB, EXPLICIT)]),
                   corpus).verdict == "pass"


def test_c253_fails_when_every_keyword_is_gathered_into_kwargs(corpus):
    assert verdict("MATPLOTLIB-C253", make_bundle(files=[whole(LIB, GATHERED)]),
                   corpus).verdict == "fail"


def test_c253_finds_no_target_when_the_function_forwards_the_rest(corpus):
    """The §7.5 half: a function that forwards is C254's, never both."""
    row = verdict("MATPLOTLIB-C253", make_bundle(files=[whole(LIB, POPS_AND_FORWARDS)]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c254_passes_when_what_is_kept_is_keyword_only(corpus):
    assert verdict("MATPLOTLIB-C254", make_bundle(files=[whole(LIB, FORWARDS_REST)]),
                   corpus).verdict == "pass"


def test_c254_fails_when_the_name_is_popped_off_kwargs(corpus):
    assert verdict("MATPLOTLIB-C254", make_bundle(files=[whole(LIB, POPS_AND_FORWARDS)]),
                   corpus).verdict == "fail"


def test_c254_finds_no_target_when_the_function_forwards_nothing(corpus):
    """The other §7.5 half: a function that keeps everything is C253's."""
    row = verdict("MATPLOTLIB-C254", make_bundle(files=[whole(LIB, GATHERED)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c254_finds_no_target_when_the_function_keeps_nothing(corpus):
    row = verdict("MATPLOTLIB-C254", make_bundle(files=[whole(LIB, FORWARDS_ALL)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C245--C247 the C/C++ extension rules -------------------------------------------------------------


WRAPPER = ("#include <Python.h>\n"
           "\n"
           "static PyObject *do_thing(PyObject *self, PyObject *args)\n"
           "{\n"
           "    return Py_BuildValue(\"i\", 1);\n"
           "}\n")
MIXED = ("#include <Python.h>\n"
         "\n"
         "static double integrate(double a, double b)\n"
         "{\n"
         "    return a + b;\n"
         "}\n")
CORE_ONLY = "static double integrate(double a, double b)\n{\n    return a + b;\n}\n"


def test_c245_passes_for_space_indented_short_lines(corpus):
    assert verdict("MATPLOTLIB-C245",
                   make_bundle(files=[whole("src/_image_wrap.cpp", WRAPPER)]),
                   corpus).verdict == "pass"


def test_c245_fails_for_tab_indentation(corpus):
    body = "int main(void)\n{\n\treturn 0;\n}\n"
    assert verdict("MATPLOTLIB-C245", make_bundle(files=[whole("src/_image.cpp", body)]),
                   corpus).verdict == "fail"


def test_c245_finds_no_target_when_no_c_source_changed(corpus):
    row = verdict("MATPLOTLIB-C245", make_bundle(files=[whole(LIB, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c246_passes_for_a_pure_wrapper(corpus):
    assert verdict("MATPLOTLIB-C246",
                   make_bundle(files=[whole("src/_image_wrap.cpp", WRAPPER)]),
                   corpus).verdict == "pass"


def test_c246_fails_when_core_computation_shares_the_file(corpus):
    assert verdict("MATPLOTLIB-C246",
                   make_bundle(files=[whole("src/_image_wrap.cpp", MIXED)]),
                   corpus).verdict == "fail"


def test_c246_finds_no_target_for_a_file_with_no_interface_code(corpus):
    row = verdict("MATPLOTLIB-C246",
                  make_bundle(files=[whole("src/_image.cpp", CORE_ONLY)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c247_passes_for_a_wrapper_named_wrap(corpus):
    bundle = make_bundle(files=[whole("src/_image_wrap.cpp", WRAPPER, is_new=True)])
    assert verdict("MATPLOTLIB-C247", bundle, corpus).verdict == "pass"


def test_c247_fails_for_an_interface_file_named_otherwise(corpus):
    bundle = make_bundle(files=[whole("src/_image.cpp", WRAPPER, is_new=True)])
    assert verdict("MATPLOTLIB-C247", bundle, corpus).verdict == "fail"


def test_c247_finds_no_target_for_a_pre_existing_wrapper(corpus):
    """Scoped to files the agent added: renaming an existing wrapper is not the ask."""
    edited = make_file("src/_image.cpp", [(5, "    return Py_BuildValue(\"i\", 1);")],
                       head_text=WRAPPER)
    row = verdict("MATPLOTLIB-C247", make_bundle(files=[edited]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

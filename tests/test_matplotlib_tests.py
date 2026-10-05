"""Three cases per rule (`docs/checker-authoring.md` §9): satisfied, violated, and an
input where the pre-condition finds nothing.

Three of the no-target cases carry a second job: they pin the §7.5 narrowings this module
declares. ``test_c168_finds_no_target_for_a_misfiled_but_prefixed_module`` and
``test_c167_finds_no_target_when_no_library_module_changed`` keep the placement rule and
the prefix rule from grading the same defect, and
``test_c177_finds_no_target_for_a_test_that_seeds_nothing`` keeps the seed-value rule out
of C176's territory.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.matplotlib.tests  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


@pytest.fixture(scope="module")
def corpus():
    """matplotlib's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("matplotlib"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def module(path: str, body: str, **kwargs):
    """A whole Python file, every line of it written by the agent."""
    lines = body.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=body, **kwargs)


LIB = module("lib/matplotlib/axis.py", "def set_ticks(self, t):\n    return t")
TESTS = "lib/matplotlib/tests/test_axis.py"


def in_tests(body: str, path: str = TESTS, **kwargs):
    return module(path, body, **kwargs)


# --- C083 the issue's reproducer is run against the branch ------------------------------


def test_c083_passes_when_the_last_reproducer_run_is_clean(corpus):
    bundle = make_bundle(files=[LIB],
                         commands=[Command(index=0, command="python repro.py",
                                           output="ok\n", returncode=0)])
    assert verdict("MATPLOTLIB-C083", bundle, corpus).verdict == "pass"


def test_c083_fails_when_the_reproducer_still_raises(corpus):
    bundle = make_bundle(files=[LIB],
                         commands=[Command(index=0, command="python repro.py",
                                           output="Traceback (most recent call last)\n",
                                           returncode=1)])
    assert verdict("MATPLOTLIB-C083", bundle, corpus).verdict == "fail"


def test_c083_finds_no_target_when_no_library_code_changed(corpus):
    row = verdict("MATPLOTLIB-C083",
                  make_bundle(files=[in_tests("def test_a():\n    assert 1")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C166 a bare pytest from the repository root ----------------------------------------


def test_c166_passes_for_a_bare_pytest(corpus):
    bundle = make_bundle(commands=[Command(index=0, command="pytest")])
    assert verdict("MATPLOTLIB-C166", bundle, corpus).verdict == "pass"


def test_c166_fails_when_the_suite_is_run_through_python_m(corpus):
    bundle = make_bundle(commands=[Command(index=0, command="python -m pytest lib/")])
    assert verdict("MATPLOTLIB-C166", bundle, corpus).verdict == "fail"


def test_c166_fails_when_the_suite_is_run_from_a_subdirectory(corpus):
    bundle = make_bundle(commands=[Command(index=0, command="cd lib && pytest")])
    assert verdict("MATPLOTLIB-C166", bundle, corpus).verdict == "fail"


def test_c166_finds_no_target_when_the_suite_was_never_run(corpus):
    row = verdict("MATPLOTLIB-C166",
                  make_bundle(commands=[Command(index=0, command="git status")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C167 a test goes in the file mirroring the module it tests --------------------------


def test_c167_passes_for_a_test_in_the_mirroring_file(corpus):
    bundle = make_bundle(files=[LIB, in_tests("def test_ticks():\n    assert 1",
                                              is_new=True)])
    assert verdict("MATPLOTLIB-C167", bundle, corpus).verdict == "pass"


def test_c167_fails_for_a_test_filed_under_an_unrelated_stem(corpus):
    bundle = make_bundle(files=[LIB,
                                in_tests("def test_ticks():\n    assert 1",
                                         path="lib/matplotlib/tests/test_colors.py",
                                         is_new=True)])
    assert verdict("MATPLOTLIB-C167", bundle, corpus).verdict == "fail"


def test_c167_finds_no_target_when_no_library_module_changed(corpus):
    """The §7.5 half: with nothing changed there is no module to mirror, so a badly
    named test file is C168's finding rather than a violation here."""
    bundle = make_bundle(files=[in_tests("def test_ticks():\n    assert 1",
                                         path="lib/matplotlib/tests/axis.py",
                                         is_new=True)])
    row = verdict("MATPLOTLIB-C167", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C168 a test module is named with a test_ prefix -------------------------------------


def test_c168_passes_for_a_prefixed_module(corpus):
    bundle = make_bundle(files=[in_tests("def test_ticks():\n    assert 1", is_new=True)])
    assert verdict("MATPLOTLIB-C168", bundle, corpus).verdict == "pass"


def test_c168_fails_for_a_module_of_tests_without_the_prefix(corpus):
    bundle = make_bundle(files=[in_tests("def test_ticks():\n    assert 1",
                                         path="lib/matplotlib/tests/axis_checks.py",
                                         is_new=True)])
    assert verdict("MATPLOTLIB-C168", bundle, corpus).verdict == "fail"


def test_c168_finds_no_target_for_a_misfiled_but_prefixed_module(corpus):
    """The other §7.5 half: a conftest is not a test module, so the prefix rule stays out
    of it even though it sits in the tests tree."""
    bundle = make_bundle(files=[in_tests("import pytest\n\n\ndef fixture_x():\n    assert 1",
                                         path="lib/matplotlib/tests/conftest.py",
                                         is_new=True)])
    row = verdict("MATPLOTLIB-C168", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C169 a test function is named with a test_ prefix -----------------------------------


def test_c169_passes_for_a_prefixed_test_function(corpus):
    bundle = make_bundle(files=[in_tests("def test_ticks():\n    assert 1", is_new=True)])
    assert verdict("MATPLOTLIB-C169", bundle, corpus).verdict == "pass"


def test_c169_fails_for_an_asserting_function_without_the_prefix(corpus):
    bundle = make_bundle(files=[in_tests("def check_ticks():\n    assert 1", is_new=True)])
    assert verdict("MATPLOTLIB-C169", bundle, corpus).verdict == "fail"


def test_c169_finds_no_target_for_a_fixture(corpus):
    body = "import pytest\n\n\n@pytest.fixture\ndef axis():\n    assert 1\n    return 1"
    row = verdict("MATPLOTLIB-C169",
                  make_bundle(files=[in_tests(body, is_new=True)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C170 a test class is named with a Test prefix ---------------------------------------


def test_c170_passes_for_a_prefixed_test_class(corpus):
    body = "class TestAxis:\n    def test_ticks(self):\n        assert 1"
    assert verdict("MATPLOTLIB-C170", make_bundle(files=[in_tests(body)]),
                   corpus).verdict == "pass"


def test_c170_fails_for_a_grouping_class_without_the_prefix(corpus):
    body = "class AxisChecks:\n    def test_ticks(self):\n        assert 1"
    assert verdict("MATPLOTLIB-C170", make_bundle(files=[in_tests(body)]),
                   corpus).verdict == "fail"


def test_c170_finds_no_target_for_a_class_that_holds_no_tests(corpus):
    body = "class Helper:\n    def build(self):\n        return 1"
    row = verdict("MATPLOTLIB-C170", make_bundle(files=[in_tests(body)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C176 a test using random numbers fixes the seed -------------------------------------


def test_c176_passes_when_the_test_seeds_its_generator(corpus):
    body = ("import numpy as np\n\n\ndef test_noise():\n"
            "    rng = np.random.default_rng(19680801)\n"
            "    assert rng.normal() is not None")
    assert verdict("MATPLOTLIB-C176", make_bundle(files=[in_tests(body)]),
                   corpus).verdict == "pass"


def test_c176_fails_when_the_test_draws_without_seeding(corpus):
    body = ("import numpy as np\n\n\ndef test_noise():\n"
            "    assert np.random.normal() is not None")
    assert verdict("MATPLOTLIB-C176", make_bundle(files=[in_tests(body)]),
                   corpus).verdict == "fail"


def test_c176_finds_no_target_for_a_test_that_uses_no_randomness(corpus):
    body = "def test_ticks():\n    assert 1 == 1"
    row = verdict("MATPLOTLIB-C176", make_bundle(files=[in_tests(body)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C177 numpy's generator is seeded with the project seed -------------------------------


def test_c177_passes_for_the_project_seed(corpus):
    body = "import numpy as np\n\nnp.random.seed(19680801)\n"
    assert verdict("MATPLOTLIB-C177",
                   make_bundle(files=[module("galleries/examples/noise.py", body)]),
                   corpus).verdict == "pass"


def test_c177_fails_for_any_other_seed(corpus):
    body = "import numpy as np\n\nnp.random.seed(42)\n"
    assert verdict("MATPLOTLIB-C177",
                   make_bundle(files=[module("galleries/examples/noise.py", body)]),
                   corpus).verdict == "fail"


def test_c177_finds_no_target_for_a_test_that_seeds_nothing(corpus):
    """The §7.5 half: an unseeded test is C176's finding, and this rule -- which grades
    the *value* -- has nothing to look at."""
    body = ("import numpy as np\n\n\ndef test_noise():\n"
            "    assert np.random.normal() is not None")
    row = verdict("MATPLOTLIB-C177", make_bundle(files=[in_tests(body)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C178 test figures are made through pyplot -------------------------------------------


def test_c178_passes_for_a_pyplot_constructor(corpus):
    body = ("import matplotlib.pyplot as plt\n\n\ndef test_draw():\n"
            "    fig, ax = plt.subplots()\n    assert ax is not None")
    assert verdict("MATPLOTLIB-C178", make_bundle(files=[in_tests(body)]),
                   corpus).verdict == "pass"


def test_c178_fails_for_a_direct_figure_instantiation(corpus):
    body = ("from matplotlib.figure import Figure\n\n\ndef test_draw():\n"
            "    fig = Figure()\n    assert fig is not None")
    assert verdict("MATPLOTLIB-C178", make_bundle(files=[in_tests(body)]),
                   corpus).verdict == "fail"


def test_c178_finds_no_target_for_a_test_that_makes_no_figure(corpus):
    body = "def test_ticks():\n    assert 1 == 1"
    row = verdict("MATPLOTLIB-C178", make_bundle(files=[in_tests(body)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- image comparison ---------------------------------------------------------------------


IMAGE_TEST = ("from matplotlib.testing.decorators import image_comparison\n"
              "\n"
              "\n"
              "@image_comparison(['spines'], style='mpl20')\n"
              "def test_spines():\n"
              "    pass\n")
NO_BASELINES = ("from matplotlib.testing.decorators import image_comparison\n"
                "\n"
                "\n"
                "@image_comparison([])\n"
                "def test_spines():\n"
                "    pass\n")


def test_c181_passes_when_the_decorator_names_its_baselines(corpus):
    assert verdict("MATPLOTLIB-C181", make_bundle(files=[in_tests(IMAGE_TEST)]),
                   corpus).verdict == "pass"


def test_c181_fails_when_the_decorator_names_none(corpus):
    assert verdict("MATPLOTLIB-C181", make_bundle(files=[in_tests(NO_BASELINES)]),
                   corpus).verdict == "fail"


def test_c181_finds_no_target_for_an_ordinary_test(corpus):
    row = verdict("MATPLOTLIB-C181",
                  make_bundle(files=[in_tests("def test_a():\n    assert 1")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


BASELINE_PNG = make_file("lib/matplotlib/tests/baseline_images/test_axis/spines.png",
                         [], is_new=True, is_binary=True)


def test_c182_passes_when_the_baseline_image_is_committed(corpus):
    bundle = make_bundle(files=[in_tests(IMAGE_TEST, is_new=True), BASELINE_PNG])
    assert verdict("MATPLOTLIB-C182", bundle, corpus).verdict == "pass"


def test_c182_fails_when_the_baseline_image_is_missing(corpus):
    bundle = make_bundle(files=[in_tests(IMAGE_TEST, is_new=True)])
    assert verdict("MATPLOTLIB-C182", bundle, corpus).verdict == "fail"


def test_c182_finds_no_target_for_a_pre_existing_image_test(corpus):
    """Scoped to tests the agent added: an existing test's baseline is already in the
    tree, and demanding it again in this patch would fail every run that edited one."""
    lines = IMAGE_TEST.split("\n")
    edited = make_file(TESTS, [(6, lines[5])], head_text=IMAGE_TEST)
    row = verdict("MATPLOTLIB-C182", make_bundle(files=[edited]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


EXTENSIONED = ("from matplotlib.testing.decorators import image_comparison\n"
               "\n"
               "\n"
               "@image_comparison(['spines.png'])\n"
               "def test_spines():\n"
               "    pass\n")
ONE_FORMAT = ("from matplotlib.testing.decorators import image_comparison\n"
              "\n"
              "\n"
              "@image_comparison(['spines.png'], extensions=['png'])\n"
              "def test_spines():\n"
              "    pass\n")


def test_c183_passes_when_the_baseline_name_omits_its_extension(corpus):
    assert verdict("MATPLOTLIB-C183", make_bundle(files=[in_tests(IMAGE_TEST)]),
                   corpus).verdict == "pass"


def test_c183_fails_when_the_baseline_name_carries_an_extension(corpus):
    assert verdict("MATPLOTLIB-C183", make_bundle(files=[in_tests(EXTENSIONED)]),
                   corpus).verdict == "fail"


def test_c183_finds_no_target_when_only_one_format_is_compared(corpus):
    row = verdict("MATPLOTLIB-C183", make_bundle(files=[in_tests(ONE_FORMAT)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


NO_STYLE = ("from matplotlib.testing.decorators import image_comparison\n"
            "\n"
            "\n"
            "@image_comparison(['spines'])\n"
            "def test_spines():\n"
            "    pass\n")


def test_c184_passes_when_a_new_image_test_pins_mpl20(corpus):
    bundle = make_bundle(files=[in_tests(IMAGE_TEST, is_new=True)])
    assert verdict("MATPLOTLIB-C184", bundle, corpus).verdict == "pass"


def test_c184_fails_when_a_new_image_test_sets_no_style(corpus):
    bundle = make_bundle(files=[in_tests(NO_STYLE, is_new=True)])
    assert verdict("MATPLOTLIB-C184", bundle, corpus).verdict == "fail"


def test_c184_finds_no_target_for_a_pre_existing_image_test(corpus):
    lines = NO_STYLE.split("\n")
    edited = make_file(TESTS, [(6, lines[5])], head_text=NO_STYLE)
    row = verdict("MATPLOTLIB-C184", make_bundle(files=[edited]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


EQUAL_OK = ("from matplotlib.testing.decorators import check_figures_equal\n"
            "\n"
            "\n"
            "@check_figures_equal(extensions=['png'])\n"
            "def test_spines(fig_test, fig_ref):\n"
            "    pass\n")
EQUAL_BAD = ("from matplotlib.testing.decorators import check_figures_equal\n"
             "\n"
             "\n"
             "@check_figures_equal(extensions=['png'])\n"
             "def test_spines(fig_test):\n"
             "    pass\n")


def test_c187_passes_for_both_figure_parameters(corpus):
    assert verdict("MATPLOTLIB-C187", make_bundle(files=[in_tests(EQUAL_OK)]),
                   corpus).verdict == "pass"


def test_c187_fails_when_the_reference_figure_is_missing(corpus):
    assert verdict("MATPLOTLIB-C187", make_bundle(files=[in_tests(EQUAL_BAD)]),
                   corpus).verdict == "fail"


def test_c187_finds_no_target_for_a_test_without_the_decorator(corpus):
    row = verdict("MATPLOTLIB-C187",
                  make_bundle(files=[in_tests("def test_a():\n    assert 1")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


TOL_DECORATOR = ("from matplotlib.testing.decorators import image_comparison\n"
                 "\n"
                 "\n"
                 "@image_comparison(['spines'], tol=0.02)\n"
                 "def test_spines():\n"
                 "    pass\n")
TOL_BY_HAND = ("from matplotlib.testing.decorators import image_comparison\n"
               "from matplotlib.testing.compare import compare_images\n"
               "\n"
               "\n"
               "@image_comparison(['spines'])\n"
               "def test_spines():\n"
               "    compare_images('a.png', 'b.png', tol=0.02)\n")


def test_c188_passes_when_the_tolerance_is_the_decorators_tol(corpus):
    assert verdict("MATPLOTLIB-C188", make_bundle(files=[in_tests(TOL_DECORATOR)]),
                   corpus).verdict == "pass"


def test_c188_fails_when_the_tolerance_is_set_in_the_body(corpus):
    assert verdict("MATPLOTLIB-C188", make_bundle(files=[in_tests(TOL_BY_HAND)]),
                   corpus).verdict == "fail"


def test_c188_finds_no_target_when_no_tolerance_is_set_at_all(corpus):
    row = verdict("MATPLOTLIB-C188", make_bundle(files=[in_tests(IMAGE_TEST)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C271 new and changed code is tested --------------------------------------------------


def test_c271_passes_when_a_test_accompanies_the_change(corpus):
    bundle = make_bundle(files=[LIB, in_tests("def test_ticks():\n    assert 1")])
    assert verdict("MATPLOTLIB-C271", bundle, corpus).verdict == "pass"


def test_c271_fails_when_the_change_ships_no_test(corpus):
    assert verdict("MATPLOTLIB-C271", make_bundle(files=[LIB]), corpus).verdict == "fail"


def test_c271_finds_no_target_for_a_documentation_only_change(corpus):
    row = verdict("MATPLOTLIB-C271",
                  make_bundle(files=[make_file("doc/users/index.rst", [(1, "Title")])]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

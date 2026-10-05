"""Three cases per rule (`docs/checker-authoring.md` §9): satisfied, violated, and an
input where the pre-condition finds nothing.

**C152 has no satisfying case reachable from a bundle alone, and that is not an omission
(§9).** It is graded off a linter run over base and head that no stored run carries, so
its three cases are violated (a submitted module that will not parse provably fails every
hook), withheld -- ``not_applicable`` with a non-``ok`` status, never a silent pass -- and
no target.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.lint import LintReport
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.matplotlib.code_quality  # noqa: F401  (registers the rules)

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


def edit(path: str, body: str, authored: list[int]):
    """A file the agent edited, with only ``authored`` lines attributed to it."""
    lines = body.split("\n")
    return make_file(path, [(n, lines[n - 1]) for n in authored], head_text=body)


LIB = "lib/matplotlib/axis.py"


# --- C152 the prek pre-commit checks pass ----------------------------------------------


def test_c152_fails_when_a_submitted_module_will_not_parse(corpus):
    bundle = make_bundle(files=[module(LIB, "def broken(:\n    pass")])
    assert verdict("MATPLOTLIB-C152", bundle, corpus).verdict == "fail"


def test_c152_withholds_when_no_linter_was_run(corpus):
    row = verdict("MATPLOTLIB-C152", make_bundle(files=[module(LIB, "x = 1")]), corpus)
    assert row.verdict == "not_applicable" and row.status != "ok"


def test_c152_passes_when_the_hooks_report_nothing_new(corpus):
    bundle = make_bundle(files=[module(LIB, "x = 1")],
                         lint={"ruff": LintReport("report", tool="ruff")})
    assert verdict("MATPLOTLIB-C152", bundle, corpus).verdict == "pass"


def test_c152_finds_no_target_when_no_python_was_submitted(corpus):
    row = verdict("MATPLOTLIB-C152",
                  make_bundle(files=[make_file("doc/users/index.rst", [(1, "Title")])]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C242 mypy type hints follow a public API change ------------------------------------


PUBLIC_API = "def set_ticks(self, ticks):\n    return ticks"


def test_c242_passes_when_the_sibling_stub_is_updated(corpus):
    bundle = make_bundle(files=[module(LIB, PUBLIC_API),
                                make_file("lib/matplotlib/axis.pyi",
                                          [(1, "def set_ticks(self, ticks) -> list: ...")])])
    assert verdict("MATPLOTLIB-C242", bundle, corpus).verdict == "pass"


def test_c242_fails_when_the_stub_is_left_behind(corpus):
    bundle = make_bundle(files=[module(LIB, PUBLIC_API)])
    assert verdict("MATPLOTLIB-C242", bundle, corpus).verdict == "fail"


def test_c242_finds_no_target_when_only_private_helpers_changed(corpus):
    bundle = make_bundle(files=[module(LIB, "def _helper(x):\n    return x")])
    row = verdict("MATPLOTLIB-C242", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C255 logging rather than print -----------------------------------------------------


def test_c255_passes_when_the_module_logs_instead_of_printing(corpus):
    body = "import logging\n_log = logging.getLogger(__name__)\n_log.debug('x %s', 1)"
    assert verdict("MATPLOTLIB-C255", make_bundle(files=[module(LIB, body)]),
                   corpus).verdict == "pass"


def test_c255_fails_when_the_module_prints(corpus):
    body = "def f(x):\n    print('debugging', x)\n    return x"
    assert verdict("MATPLOTLIB-C255", make_bundle(files=[module(LIB, body)]),
                   corpus).verdict == "fail"


def test_c255_finds_no_target_for_a_gallery_example(corpus):
    body = "print('this example prints on purpose')"
    row = verdict("MATPLOTLIB-C255",
                  make_bundle(files=[module("galleries/examples/lines.py", body)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C256 the module logger is created right after the imports --------------------------


GOOD_LOGGER = ("import logging\n"
               "import numpy as np\n"
               "\n"
               "_log = logging.getLogger(__name__)\n")
BAD_LOGGER = ("import logging\n"
              "\n"
              "CONSTANT = 3\n"
              "\n"
              "logger = logging.getLogger(__name__)\n")


def test_c256_passes_for_the_stated_spelling_and_position(corpus):
    assert verdict("MATPLOTLIB-C256", make_bundle(files=[module(LIB, GOOD_LOGGER)]),
                   corpus).verdict == "pass"


def test_c256_fails_when_the_logger_is_named_and_placed_otherwise(corpus):
    assert verdict("MATPLOTLIB-C256", make_bundle(files=[module(LIB, BAD_LOGGER)]),
                   corpus).verdict == "fail"


def test_c256_finds_no_target_when_the_module_creates_no_logger(corpus):
    row = verdict("MATPLOTLIB-C256",
                  make_bundle(files=[module(LIB, "import logging\n\nx = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C257 %-style logging arguments -----------------------------------------------------


def test_c257_passes_for_percent_style_parameters(corpus):
    body = "import logging\n_log = logging.getLogger(__name__)\n_log.debug('at %s', x)\n"
    assert verdict("MATPLOTLIB-C257", make_bundle(files=[module(LIB, body)]),
                   corpus).verdict == "pass"


def test_c257_fails_for_an_f_string_message(corpus):
    body = "import logging\n_log = logging.getLogger(__name__)\n_log.debug(f'at {x}')\n"
    assert verdict("MATPLOTLIB-C257", make_bundle(files=[module(LIB, body)]),
                   corpus).verdict == "fail"


def test_c257_finds_no_target_when_the_module_logs_nothing(corpus):
    row = verdict("MATPLOTLIB-C257",
                  make_bundle(files=[module(LIB, "def f(x):\n    return x\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C258 expected code paths at debug level only ---------------------------------------


def test_c258_passes_when_an_expected_path_logs_at_debug(corpus):
    body = "import logging\n_log = logging.getLogger(__name__)\n_log.debug('found %s', x)\n"
    assert verdict("MATPLOTLIB-C258", make_bundle(files=[module(LIB, body)]),
                   corpus).verdict == "pass"


def test_c258_fails_when_an_expected_path_logs_at_info(corpus):
    body = "import logging\n_log = logging.getLogger(__name__)\n_log.info('found %s', x)\n"
    assert verdict("MATPLOTLIB-C258", make_bundle(files=[module(LIB, body)]),
                   corpus).verdict == "fail"


def test_c258_finds_no_target_for_a_call_inside_an_except_handler(corpus):
    body = ("import logging\n"
            "_log = logging.getLogger(__name__)\n"
            "try:\n"
            "    f()\n"
            "except ValueError:\n"
            "    _log.warning('unexpected %s', x)\n")
    row = verdict("MATPLOTLIB-C258", make_bundle(files=[module(LIB, body)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C291 re-stage and re-commit what a hook modified -----------------------------------


from compliance.core.models import Command  # noqa: E402  (used only by C291's fixtures)

HOOK_RAN = Command(index=0, command="prek run --all-files",
                   output="ruff-format...Failed\n- files were modified by this hook\n")


def test_c291_passes_when_the_rewritten_files_are_restaged_and_recommitted(corpus):
    bundle = make_bundle(commands=[HOOK_RAN,
                                   Command(index=1, command="git add -u"),
                                   Command(index=2, command="git commit --amend --no-edit")])
    assert verdict("MATPLOTLIB-C291", bundle, corpus).verdict == "pass"


def test_c291_fails_when_nothing_is_restaged_afterwards(corpus):
    bundle = make_bundle(commands=[HOOK_RAN, Command(index=1, command="python -c 'pass'")])
    assert verdict("MATPLOTLIB-C291", bundle, corpus).verdict == "fail"


def test_c291_finds_no_target_when_no_hook_modified_anything(corpus):
    bundle = make_bundle(commands=[Command(index=0, command="prek run --all-files",
                                           output="ruff-format...Passed\n"),
                                   Command(index=1, command="git commit -m x")])
    row = verdict("MATPLOTLIB-C291", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

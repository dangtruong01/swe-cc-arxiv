"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

C003, C005 and C006 are about *when* something was run, so their fixtures are command
logs with an ordering rather than a set of commands. The last test in the C005 section
pins the §7.5 resolution described in the rule module's docstring: C003's window and
C005's window are disjoint, so one log cannot satisfy both readings by accident.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.psf.tests  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}

SOURCE = make_file("requests/models.py", [(1, "x = 1")])
TEST_FILE = make_file("tests/test_requests.py", [(1, "def test_a(): pass")])
DOC = make_file("docs/user/quickstart.rst", [(1, "Quickstart")])

EDIT_SOURCE = "sed -i 's/a/b/' requests/models.py"
WRITE_TEST = 'str_replace_editor {"command": "create", "path": "tests/test_requests.py"}'


def cmds(*specs):
    """A command log; a (command, output) pair records what the run printed."""
    out = []
    for index, spec in enumerate(specs):
        command, output = spec if isinstance(spec, tuple) else (spec, "")
        out.append(Command(index=index, command=command, output=output))
    return tuple(out)


@pytest.fixture(scope="module")
def corpus():
    """psf's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("psf"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C003 the suite is run, and passes, before the change -----------------------------


def test_c003_passes_when_the_suite_ran_clean_before_the_first_edit(corpus):
    bundle = make_bundle(files=[SOURCE],
                         commands=cmds(("python -m pytest tests/", "40 passed"),
                                       EDIT_SOURCE))
    assert verdict("PSF-C003", bundle, corpus).verdict == "pass"


def test_c003_fails_when_the_first_run_came_after_the_first_edit(corpus):
    bundle = make_bundle(files=[SOURCE],
                         commands=cmds(EDIT_SOURCE,
                                       ("python -m pytest tests/", "40 passed")))
    assert verdict("PSF-C003", bundle, corpus).verdict == "fail"


def test_c003_finds_no_target_when_nothing_was_contributed(corpus):
    row = verdict("PSF-C003", make_bundle(files=[], commands=cmds("pytest")), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C004 tests that exercise the change ----------------------------------------------


def test_c004_passes_when_a_test_file_changed_alongside_the_code(corpus):
    assert verdict("PSF-C004", make_bundle(files=[SOURCE, TEST_FILE]),
                   corpus).verdict == "pass"


def test_c004_fails_when_source_changed_alone(corpus):
    assert verdict("PSF-C004", make_bundle(files=[SOURCE]), corpus).verdict == "fail"


def test_c004_finds_no_target_for_a_documentation_only_change(corpus):
    row = verdict("PSF-C004", make_bundle(files=[DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C005 the new tests are seen to fail first ----------------------------------------


def test_c005_passes_when_the_new_tests_failed_before_the_source_changed(corpus):
    bundle = make_bundle(
        files=[SOURCE, TEST_FILE],
        commands=cmds(WRITE_TEST,
                      ("python -m pytest tests/test_requests.py", "1 failed"),
                      EDIT_SOURCE))
    assert verdict("PSF-C005", bundle, corpus).verdict == "pass"


def test_c005_fails_when_the_pre_change_run_reported_no_failure(corpus):
    bundle = make_bundle(
        files=[SOURCE, TEST_FILE],
        commands=cmds(WRITE_TEST,
                      ("python -m pytest tests/test_requests.py", "1 passed"),
                      EDIT_SOURCE))
    assert verdict("PSF-C005", bundle, corpus).verdict == "fail"


def test_c005_finds_no_target_when_the_contribution_adds_no_test(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds(EDIT_SOURCE))
    row = verdict("PSF-C005", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c003_and_c005_read_disjoint_windows(corpus):
    """The §7.5 resolution, pinned. C003 grades the untouched checkout and C005 the
    interval between writing the tests and changing the code, so the one log that
    satisfies both reads as a pass twice rather than as a contradiction."""
    bundle = make_bundle(
        files=[SOURCE, TEST_FILE],
        commands=cmds(("python -m pytest tests/", "40 passed"),
                      WRITE_TEST,
                      ("python -m pytest tests/test_requests.py", "1 failed"),
                      EDIT_SOURCE))
    assert verdict("PSF-C003", bundle, corpus).verdict == "pass"
    assert verdict("PSF-C005", bundle, corpus).verdict == "pass"


# --- C006 the entire suite is run, and passes, after the change -----------------------


def test_c006_passes_when_the_whole_suite_ran_clean_after_the_last_edit(corpus):
    bundle = make_bundle(files=[SOURCE],
                         commands=cmds(EDIT_SOURCE, ("python -m pytest", "41 passed")))
    assert verdict("PSF-C006", bundle, corpus).verdict == "pass"


def test_c006_fails_when_only_the_new_test_was_rerun(corpus):
    bundle = make_bundle(
        files=[SOURCE],
        commands=cmds(EDIT_SOURCE,
                      ("python -m pytest tests/test_requests.py::test_a", "1 passed")))
    assert verdict("PSF-C006", bundle, corpus).verdict == "fail"


def test_c006_finds_no_target_when_nothing_was_contributed(corpus):
    row = verdict("PSF-C006", make_bundle(files=[], commands=cmds("pytest")), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

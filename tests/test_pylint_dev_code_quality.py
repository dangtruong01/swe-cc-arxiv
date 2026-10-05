"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

C094 and C097 carry a fourth case each, because what separates them is the object of the
`pylint` run rather than its flags: the standard run over a changed module satisfies C094
and violates C097, and that pair is asserted rather than described.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_commit, make_file

from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pylint_dev.code_quality  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("pylint/checkers/typecheck.py", [(1, "x = 1")], head_text="x = 1")
DOC = make_file("doc/user_guide/usage.rst", [(1, "Usage")], head_text="Usage")
STANDARD_RUN = "pylint --rcfile=pylintrc --fail-on=I pylint/checkers/typecheck.py"


@pytest.fixture(scope="module")
def corpus():
    """pylint-dev's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pylint-dev"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def cmds(*commands):
    return tuple(Command(index=i, command=c) for i, c in enumerate(commands))


COMMITS = [make_commit("Fix a crash in the type checker")]


# --- C093 pre-commit run -a before committing -----------------------------------------


def test_c093_passes_when_the_hooks_ran_before_the_commit(corpus):
    bundle = make_bundle(files=[SOURCE], commits=COMMITS,
                         commands=cmds("pre-commit run -a", "git commit -m 'Fix'"))
    assert verdict("PYLINT-DEV-C093", bundle, corpus).verdict == "pass"


def test_c093_fails_when_the_hooks_ran_after_the_commit(corpus):
    bundle = make_bundle(files=[SOURCE], commits=COMMITS,
                         commands=cmds("git commit -m 'Fix'", "pre-commit run -a"))
    row = verdict("PYLINT-DEV-C093", bundle, corpus)
    assert row.verdict == "fail" and "after the first" in row.notes


def test_c093_finds_no_target_when_nothing_was_committed(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("pre-commit run -a"))
    row = verdict("PYLINT-DEV-C093", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C094 the standard pylint invocation ----------------------------------------------


def test_c094_passes_on_the_invocation_the_guide_gives(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds(STANDARD_RUN))
    assert verdict("PYLINT-DEV-C094", bundle, corpus).verdict == "pass"


def test_c094_fails_when_pylint_ran_without_the_named_flags(corpus):
    bundle = make_bundle(files=[SOURCE],
                         commands=cmds("pylint pylint/checkers/typecheck.py"))
    row = verdict("PYLINT-DEV-C094", bundle, corpus)
    assert row.verdict == "fail" and "--fail-on=I" in row.notes


def test_c094_finds_no_target_for_a_documentation_only_change(corpus):
    row = verdict("PYLINT-DEV-C094", make_bundle(files=[DOC], commands=cmds(STANDARD_RUN)),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C097 validation on sample code ---------------------------------------------------


def test_c097_passes_when_pylint_ran_over_code_outside_the_change(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds(STANDARD_RUN, "pylint /tmp/sample.py"))
    assert verdict("PYLINT-DEV-C097", bundle, corpus).verdict == "pass"


def test_c097_fails_when_pylint_only_ran_over_the_changed_module(corpus):
    """The case that keeps C094 and C097 apart: the standard run satisfies one and not
    the other."""
    bundle = make_bundle(files=[SOURCE], commands=cmds(STANDARD_RUN))
    assert verdict("PYLINT-DEV-C094", bundle, corpus).verdict == "pass"
    row = verdict("PYLINT-DEV-C097", bundle, corpus)
    assert row.verdict == "fail" and "never over sample code" in row.notes


def test_c097_finds_no_target_for_a_documentation_only_change(corpus):
    row = verdict("PYLINT-DEV-C097", make_bundle(files=[DOC], commands=cmds(STANDARD_RUN)),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

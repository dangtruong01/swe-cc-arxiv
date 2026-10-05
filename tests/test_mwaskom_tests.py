"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

The third case is the one that catches a pre-condition written against the artefact the
rule demands instead of the antecedent that invokes it (§7.1) -- here, a run that invoked
`make test` but submitted nothing must find no target, because C001 fires on having a
contribution to test rather than on having tested.

C001 carries two extra cases, both pinning a reading stated in the module docstring: a
direct `pytest` run does not stand in for the command the README names, and `make -C <dir>
test` is not "from the source directory".
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.mwaskom.tests  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("seaborn/_core/plot.py", [(1, "x = 1")])


def cmds(*commands):
    return tuple(Command(index=i, command=c) for i, c in enumerate(commands))


@pytest.fixture(scope="module")
def corpus():
    """seaborn's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("mwaskom"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C001 the unit test suite was run through `make test` -----------------------------


def test_c001_passes_when_make_test_ran(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("cd /testbed && make test"))
    assert verdict("MWASKOM-C001", bundle, corpus).verdict == "pass"


def test_c001_passes_when_make_test_ran_alongside_another_target(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("make lint test"))
    assert verdict("MWASKOM-C001", bundle, corpus).verdict == "pass"


def test_c001_fails_when_the_suite_was_never_run(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("make lint", "pip install -e ."))
    assert verdict("MWASKOM-C001", bundle, corpus).verdict == "fail"


def test_c001_fails_on_a_direct_pytest_run(corpus):
    """The README names one invocation and no alternative, so the Makefile's expansion is
    not a second satisfying form."""
    bundle = make_bundle(files=[SOURCE], commands=cmds("pytest tests/test_axisgrid.py"))
    assert verdict("MWASKOM-C001", bundle, corpus).verdict == "fail"


def test_c001_fails_when_make_ran_somewhere_other_than_the_source_directory(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("make -C /elsewhere test"))
    assert verdict("MWASKOM-C001", bundle, corpus).verdict == "fail"


def test_c001_finds_no_target_for_an_empty_contribution(corpus):
    """The antecedent is the contribution, not the invocation: a run that tested but
    submitted nothing is outside the rule, not a pass."""
    row = verdict("MWASKOM-C001", make_bundle(files=[], commands=cmds("make test")), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

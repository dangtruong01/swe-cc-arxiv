"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

The rule is about an ordering, so the two graded cases are the same two commands in the two
orders. The no-target case is the run that never searched the tree at all: the rule's
antecedent is the search, not the reading of the instructions, and a run with nothing to
order has no verdict to give.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pylint_dev.ai_policy  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("pylint/checkers/typecheck.py", [(1, "x = 1")], head_text="x = 1")
READ_INSTRUCTIONS = "cat .github/copilot-instructions.md"
SEARCH = "grep -rn 'add_message' pylint/checkers/"


@pytest.fixture(scope="module")
def corpus():
    """pylint-dev's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pylint-dev"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def cmds(*commands):
    return tuple(Command(index=i, command=c) for i, c in enumerate(commands))


# --- C082 the instructions are consulted first ----------------------------------------


def test_c082_passes_when_the_instructions_are_read_before_the_first_search(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds(READ_INSTRUCTIONS, SEARCH))
    assert verdict("PYLINT-DEV-C082", bundle, corpus).verdict == "pass"


def test_c082_fails_when_the_search_comes_first(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds(SEARCH, READ_INSTRUCTIONS))
    row = verdict("PYLINT-DEV-C082", bundle, corpus)
    assert row.verdict == "fail" and "after the" in row.notes


def test_c082_finds_no_target_when_the_repository_was_never_searched(corpus):
    bundle = make_bundle(files=[SOURCE],
                         commands=cmds("python -m pytest tests/", "tox -e py313"))
    row = verdict("PYLINT-DEV-C082", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

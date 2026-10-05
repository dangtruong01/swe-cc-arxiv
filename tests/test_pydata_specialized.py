"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

The satisfying and violating cases both come from the same pre-condition here, which is the
point of §7.1: a rule that only selected removals could never record a proper deprecation.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pydata.specialized  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
PATH = "xarray/core/dataset.py"

BASE = "def sel(self, indexers=None, method=None, drop=False):\n    return self\n"
REMOVED = "def sel(self, indexers=None, method=None):\n    return self\n"
DEPRECATED = (
    "def sel(self, indexers=None, method=None, drop=False):\n"
    "    if drop is not False:\n"
    "        emit_user_level_warning('drop is deprecated', FutureWarning)\n"
    "    return self\n")


def changed(head: str, base: str = BASE, added=None):
    lines = head.split("\n")
    return make_file(PATH, added if added is not None else
                     [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=head, base_text=base)


@pytest.fixture(scope="module")
def corpus():
    """pydata's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pydata"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def test_c042_passes_when_the_argument_is_deprecated_not_removed(corpus):
    assert verdict("PYDATA-C042", make_bundle(files=[changed(DEPRECATED)]),
                   corpus).verdict == "pass"


def test_c042_fails_when_the_argument_is_simply_removed(corpus):
    assert verdict("PYDATA-C042", make_bundle(files=[changed(REMOVED)]),
                   corpus).verdict == "fail"


def test_c042_fails_when_a_future_warning_bypasses_the_helper(corpus):
    head = ("def sel(self, indexers=None, method=None, drop=False):\n"
            "    warnings.warn('drop is deprecated', FutureWarning)\n"
            "    return self\n")
    assert verdict("PYDATA-C042", make_bundle(files=[changed(head)]),
                   corpus).verdict == "fail"


def test_c042_finds_no_target_for_an_ordinary_change(corpus):
    head = BASE.replace("return self", "return self.copy()")
    row = verdict("PYDATA-C042", make_bundle(files=[changed(head)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

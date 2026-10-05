"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.psf.code_quality  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}

DOC = make_file("docs/user/quickstart.rst", [(1, "Quickstart")])


@pytest.fixture(scope="module")
def corpus():
    """psf's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("psf"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C011 changed files satisfy the configured formatting -----------------------------


def test_c011_passes_on_cleanly_formatted_lines(corpus):
    changed = make_file("requests/models.py",
                        [(10, "def prepare(self):"), (11, "    return self")])
    assert verdict("PSF-C011", make_bundle(files=[changed]), corpus).verdict == "pass"


def test_c011_fails_on_trailing_whitespace(corpus):
    changed = make_file("requests/models.py",
                        [(10, "def prepare(self):"), (11, "    return self   ")])
    assert verdict("PSF-C011", make_bundle(files=[changed]), corpus).verdict == "fail"


def test_c011_finds_no_target_when_no_python_file_gained_a_line(corpus):
    row = verdict("PSF-C011", make_bundle(files=[DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pydata.language_style  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


def module(text: str, path: str = "xarray/core/merge.py"):
    lines = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text)


@pytest.fixture(scope="module")
def corpus():
    """pydata's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pydata"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def test_c039_passes_when_the_groups_are_in_order(corpus):
    text = "import os\n\nimport numpy as np\n\nfrom xarray.core import dtypes\n"
    assert verdict("PYDATA-C039", make_bundle(files=[module(text)]),
                   corpus).verdict == "pass"


def test_c039_fails_when_first_party_precedes_third_party(corpus):
    text = "from xarray.core import dtypes\n\nimport numpy as np\n"
    assert verdict("PYDATA-C039", make_bundle(files=[module(text)]),
                   corpus).verdict == "fail"


def test_c039_finds_no_target_on_a_single_import(corpus):
    row = verdict("PYDATA-C039", make_bundle(files=[module("import os\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

``test_c013_finds_no_target_for_the_changelog`` is the extra case the §7.5 resolution in
the rule module's docstring calls for: repository metadata is written in documentation
markup and is deliberately not documentation, so it must find no target rather than be
reported as a page in the wrong place.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.psf.documentation  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}

SOURCE = make_file("requests/models.py", [(1, "x = 1")])


def page(path: str, text: str):
    lines = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text)


@pytest.fixture(scope="module")
def corpus():
    """psf's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("psf"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C013 documentation changes live under docs/ --------------------------------------


def test_c013_passes_for_a_page_under_docs(corpus):
    bundle = make_bundle(files=[page("docs/user/quickstart.rst", "Quickstart\n==========\n")])
    assert verdict("PSF-C013", bundle, corpus).verdict == "pass"


def test_c013_fails_for_documentation_written_outside_docs(corpus):
    bundle = make_bundle(files=[page("guides/quickstart.rst", "Quickstart\n==========\n")])
    assert verdict("PSF-C013", bundle, corpus).verdict == "fail"


def test_c013_finds_no_target_for_a_code_only_contribution(corpus):
    row = verdict("PSF-C013", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c013_finds_no_target_for_the_changelog(corpus):
    """The §7.5 exclusion, pinned: HISTORY.md is metadata, not documentation, so the rule
    does not read "documentation lives under docs/" as a ban on touching it."""
    row = verdict("PSF-C013", make_bundle(files=[page("HISTORY.md", "# 2.31.0\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C014 documentation is reStructuredText -------------------------------------------


def test_c014_passes_for_a_rst_page(corpus):
    bundle = make_bundle(files=[page("docs/user/quickstart.rst",
                                     "Quickstart\n==========\n\nMake a request.\n")])
    assert verdict("PSF-C014", bundle, corpus).verdict == "pass"


def test_c014_fails_for_a_markdown_page_under_docs(corpus):
    bundle = make_bundle(files=[page("docs/user/quickstart.md", "# Quickstart\n")])
    assert verdict("PSF-C014", bundle, corpus).verdict == "fail"


def test_c014_fails_on_markdown_written_into_a_rst_page(corpus):
    bundle = make_bundle(files=[page("docs/user/quickstart.rst",
                                     "Quickstart\n==========\n\n# A heading\n")])
    assert verdict("PSF-C014", bundle, corpus).verdict == "fail"


def test_c014_finds_no_target_for_a_code_only_contribution(corpus):
    row = verdict("PSF-C014", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.psf.language_style  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


def page(path: str, text: str):
    lines = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text)


SINGLE_QUOTED = (
    "Quickstart\n"
    "==========\n"
    "\n"
    "    >>> r = requests.get('https://api.github.com/events')\n"
    "    >>> r.headers['content-type']\n"
)
DOUBLE_QUOTED = (
    "Quickstart\n"
    "==========\n"
    "\n"
    "    >>> r = requests.get(\"https://api.github.com/events\")\n"
)
PROSE_ONLY = (
    "Quickstart\n"
    "==========\n"
    "\n"
    "Requests makes HTTP calls straightforward.\n"
)


@pytest.fixture(scope="module")
def corpus():
    """psf's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("psf"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C018 documentation code samples use single-quoted strings ------------------------


def test_c018_passes_on_a_single_quoted_sample(corpus):
    bundle = make_bundle(files=[page("docs/user/quickstart.rst", SINGLE_QUOTED)])
    assert verdict("PSF-C018", bundle, corpus).verdict == "pass"


def test_c018_fails_on_a_double_quoted_sample(corpus):
    bundle = make_bundle(files=[page("docs/user/quickstart.rst", DOUBLE_QUOTED)])
    assert verdict("PSF-C018", bundle, corpus).verdict == "fail"


def test_c018_finds_no_target_on_a_page_with_no_python_sample(corpus):
    bundle = make_bundle(files=[page("docs/user/quickstart.rst", PROSE_ONLY)])
    row = verdict("PSF-C018", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

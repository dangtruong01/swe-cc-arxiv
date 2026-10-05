"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

C044 and C057 hang off the project's own changelog type, so their no-target cases use a
fragment of a *different* type -- the pre-condition must discriminate on the declaration,
not on the presence of a fragment.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pytest_dev.documentation  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("src/_pytest/fixtures.py", [(1, "x = 1")])
DOC = make_file("doc/en/reference.rst", [(3, "New prose.")])


def new_module(path: str, text: str):
    lines = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text, is_new=True)


def entry(name: str, *lines: str):
    return make_file(f"changelog/{name}",
                     [(n, t) for n, t in enumerate(lines, 1)], is_new=True)


def cmds(*commands):
    return tuple(Command(index=i, command=c) for i, c in enumerate(commands))


@pytest.fixture(scope="module")
def corpus():
    """pytest-dev's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pytest-dev"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C003 documentation built with tox ------------------------------------------------


def test_c003_passes_when_the_docs_environment_ran(corpus):
    bundle = make_bundle(files=[DOC], commands=cmds("tox -e docs"))
    assert verdict("PYTEST-DEV-C003", bundle, corpus).verdict == "pass"


def test_c003_fails_when_documentation_changed_without_a_build(corpus):
    bundle = make_bundle(files=[DOC], commands=cmds("tox -e py313"))
    assert verdict("PYTEST-DEV-C003", bundle, corpus).verdict == "fail"


def test_c003_finds_no_target_without_a_documentation_change(corpus):
    row = verdict("PYTEST-DEV-C003",
                  make_bundle(files=[SOURCE], commands=cmds("tox -e docs")), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C004 Sphinx docstring format -----------------------------------------------------


SPHINX_DOC = '''def collect(path):
    """Collect items.

    :param path: where to look.
    :returns: the items.
    """
    return []
'''
NUMPY_DOC = '''def collect(path):
    """Collect items.

    Parameters
    ----------
    path : str
        where to look.
    """
    return []
'''
GOOGLE_DOC = '''def collect(path):
    """Collect items.

    Args:
        path: where to look.
    """
    return []
'''


def test_c004_passes_on_a_sphinx_field_list(corpus):
    bundle = make_bundle(files=[new_module("src/_pytest/collect.py", SPHINX_DOC)])
    assert verdict("PYTEST-DEV-C004", bundle, corpus).verdict == "pass"


def test_c004_fails_on_a_numpydoc_section(corpus):
    bundle = make_bundle(files=[new_module("src/_pytest/collect.py", NUMPY_DOC)])
    assert verdict("PYTEST-DEV-C004", bundle, corpus).verdict == "fail"


def test_c004_fails_on_a_google_style_section(corpus):
    bundle = make_bundle(files=[new_module("src/_pytest/collect.py", GOOGLE_DOC)])
    assert verdict("PYTEST-DEV-C004", bundle, corpus).verdict == "fail"


def test_c004_finds_no_target_when_nothing_carries_a_docstring(corpus):
    bundle = make_bundle(files=[new_module("src/_pytest/collect.py", "x = 1\n")])
    row = verdict("PYTEST-DEV-C004", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C005 docstring sentences ---------------------------------------------------------


def test_c005_passes_on_a_proper_subject_line(corpus):
    bundle = make_bundle(files=[new_module("src/_pytest/collect.py", SPHINX_DOC)])
    assert verdict("PYTEST-DEV-C005", bundle, corpus).verdict == "pass"


def test_c005_fails_without_a_capital(corpus):
    body = 'def collect():\n    """collect items."""\n    return []\n'
    bundle = make_bundle(files=[new_module("src/_pytest/collect.py", body)])
    assert verdict("PYTEST-DEV-C005", bundle, corpus).verdict == "fail"


def test_c005_fails_without_a_terminator(corpus):
    body = 'def collect():\n    """Collect items"""\n    return []\n'
    bundle = make_bundle(files=[new_module("src/_pytest/collect.py", body)])
    assert verdict("PYTEST-DEV-C005", bundle, corpus).verdict == "fail"


def test_c005_finds_no_target_when_nothing_carries_a_docstring(corpus):
    bundle = make_bundle(files=[new_module("src/_pytest/collect.py", "x = 1\n")])
    row = verdict("PYTEST-DEV-C005", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C008 blank line before the detail ------------------------------------------------


def test_c008_passes_when_a_blank_line_separates_the_detail(corpus):
    bundle = make_bundle(files=[new_module("src/_pytest/collect.py", SPHINX_DOC)])
    assert verdict("PYTEST-DEV-C008", bundle, corpus).verdict == "pass"


def test_c008_fails_when_the_detail_runs_straight_on(corpus):
    body = ('def collect():\n'
            '    """Collect items.\n'
            '    More detail here.\n'
            '    """\n'
            '    return []\n')
    bundle = make_bundle(files=[new_module("src/_pytest/collect.py", body)])
    assert verdict("PYTEST-DEV-C008", bundle, corpus).verdict == "fail"


def test_c008_finds_no_target_for_a_one_line_docstring(corpus):
    body = 'def collect():\n    """Collect items."""\n    return []\n'
    bundle = make_bundle(files=[new_module("src/_pytest/collect.py", body)])
    row = verdict("PYTEST-DEV-C008", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C044 breaking changes documented -------------------------------------------------


BREAKING = entry("2574.breaking.rst", "Removed the old hook.")
DEPRECATIONS = make_file("doc/en/deprecations.rst", [(9, "The old hook is gone.")])


def test_c044_passes_when_deprecations_rst_was_updated(corpus):
    bundle = make_bundle(files=[SOURCE, BREAKING, DEPRECATIONS])
    assert verdict("PYTEST-DEV-C044", bundle, corpus).verdict == "pass"


def test_c044_fails_when_the_break_is_undocumented(corpus):
    assert verdict("PYTEST-DEV-C044", make_bundle(files=[SOURCE, BREAKING]),
                   corpus).verdict == "fail"


def test_c044_finds_no_target_for_a_non_breaking_change(corpus):
    bundle = make_bundle(files=[SOURCE, entry("2574.bugfix.rst", "Fixed it.")])
    row = verdict("PYTEST-DEV-C044", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C057 new features ship with documentation ----------------------------------------


FEATURE = entry("2574.feature.rst", "Added a hook.")


def test_c057_passes_when_documentation_changed_too(corpus):
    assert verdict("PYTEST-DEV-C057", make_bundle(files=[SOURCE, FEATURE, DOC]),
                   corpus).verdict == "pass"


def test_c057_fails_when_the_feature_is_undocumented(corpus):
    assert verdict("PYTEST-DEV-C057", make_bundle(files=[SOURCE, FEATURE]),
                   corpus).verdict == "fail"


def test_c057_finds_no_target_for_a_bugfix(corpus):
    bundle = make_bundle(files=[SOURCE, entry("2574.bugfix.rst", "Fixed it.")])
    row = verdict("PYTEST-DEV-C057", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

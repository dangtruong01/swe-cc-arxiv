"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

C030 carries a fourth case on purpose: `CHANGES.rst` must not be selected, or this rule and
C005 would bind the same file in opposite directions.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.sphinx_doc.documentation  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}

DOCUMENTED = 'def build_inventory():\n    """Build it."""\n    return 1\n'
UNDOCUMENTED = "def build_inventory():\n    return 1\n"


def new_module(path: str, text: str):
    lines = text.splitlines()
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text, is_new=True)


@pytest.fixture(scope="module")
def corpus():
    """sphinx-doc's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("sphinx-doc"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C014 new features are documented -------------------------------------------------


def test_c014_passes_when_the_manual_changed_alongside(corpus):
    bundle = make_bundle(files=[
        new_module("sphinx/util/inventory.py", UNDOCUMENTED),
        make_file("doc/usage/configuration.rst", [(3, "The new builder.")]),
    ])
    assert verdict("SPHINX-DOC-C014", bundle, corpus).verdict == "pass"


def test_c014_passes_when_the_new_definition_carries_a_docstring(corpus):
    bundle = make_bundle(files=[new_module("sphinx/util/inventory.py", DOCUMENTED)])
    assert verdict("SPHINX-DOC-C014", bundle, corpus).verdict == "pass"


def test_c014_fails_when_a_new_public_function_is_documented_nowhere(corpus):
    bundle = make_bundle(files=[new_module("sphinx/util/inventory.py", UNDOCUMENTED)])
    assert verdict("SPHINX-DOC-C014", bundle, corpus).verdict == "fail"


def test_c014_finds_no_target_when_nothing_public_was_added(corpus):
    bundle = make_bundle(files=[new_module("sphinx/util/inventory.py", "x = 1\n")])
    row = verdict("SPHINX-DOC-C014", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C017 new configuration values are documented -------------------------------------


CONFIG_CALL = "    app.add_config_value('inventory_cache', None, 'env')"


def test_c017_passes_when_the_option_is_named_in_changed_documentation(corpus):
    bundle = make_bundle(files=[
        make_file("sphinx/util/inventory.py", [(10, CONFIG_CALL)]),
        make_file("doc/usage/configuration.rst", [(40, "inventory_cache: caches it.")]),
    ])
    assert verdict("SPHINX-DOC-C017", bundle, corpus).verdict == "pass"


def test_c017_fails_when_the_option_is_registered_and_never_documented(corpus):
    bundle = make_bundle(files=[make_file("sphinx/util/inventory.py", [(10, CONFIG_CALL)])])
    assert verdict("SPHINX-DOC-C017", bundle, corpus).verdict == "fail"


def test_c017_finds_no_target_without_a_registration(corpus):
    bundle = make_bundle(files=[make_file("sphinx/util/inventory.py", [(10, "x = 1")])])
    row = verdict("SPHINX-DOC-C017", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C030 documentation lives under doc/ ----------------------------------------------


def test_c030_passes_for_a_source_under_doc(corpus):
    bundle = make_bundle(files=[make_file("doc/usage/builders.rst", [(1, "Builders")])])
    assert verdict("SPHINX-DOC-C030", bundle, corpus).verdict == "pass"


def test_c030_fails_for_a_documentation_source_outside_doc(corpus):
    bundle = make_bundle(files=[make_file("guides/builders.rst", [(1, "Builders")])])
    assert verdict("SPHINX-DOC-C030", bundle, corpus).verdict == "fail"


def test_c030_does_not_select_the_changelog(corpus):
    """C005 requires this file. Selecting it here would make the two rules contradict."""
    bundle = make_bundle(files=[make_file("CHANGES.rst", [(2, "* Fixed a thing.")])])
    row = verdict("SPHINX-DOC-C030", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c030_finds_no_target_for_a_code_only_change(corpus):
    bundle = make_bundle(files=[make_file("sphinx/util/inventory.py", [(1, "x = 1")])])
    row = verdict("SPHINX-DOC-C030", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C031 documentation is built with warnings fatal ----------------------------------


DOC_CHANGE = make_file("doc/usage/builders.rst", [(1, "Builders")])


def cmds(*commands):
    return tuple(Command(index=i, command=c) for i, c in enumerate(commands))


def test_c031_passes_when_the_build_makes_warnings_fatal(corpus):
    bundle = make_bundle(files=[DOC_CHANGE], commands=cmds(
        "sphinx-build -M html ./doc ./build/sphinx --fail-on-warning"))
    assert verdict("SPHINX-DOC-C031", bundle, corpus).verdict == "pass"


def test_c031_passes_on_the_short_flag(corpus):
    bundle = make_bundle(files=[DOC_CHANGE],
                         commands=cmds("sphinx-build -W -M html ./doc ./build"))
    assert verdict("SPHINX-DOC-C031", bundle, corpus).verdict == "pass"


def test_c031_fails_when_the_build_tolerates_warnings(corpus):
    bundle = make_bundle(files=[DOC_CHANGE],
                         commands=cmds("sphinx-build -M html ./doc ./build/sphinx"))
    assert verdict("SPHINX-DOC-C031", bundle, corpus).verdict == "fail"


def test_c031_finds_no_target_when_no_documentation_changed(corpus):
    bundle = make_bundle(files=[make_file("sphinx/util/inventory.py", [(1, "x = 1")])],
                         commands=cmds("sphinx-build -M html ./doc ./build"))
    row = verdict("SPHINX-DOC-C031", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

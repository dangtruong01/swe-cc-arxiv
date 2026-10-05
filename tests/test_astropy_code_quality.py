"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

**C076 carries a fourth: the withheld case (§9).** Its floor is ``requires-python`` at the
base commit, which the bundle does not carry, so a contribution that does not happen to
include ``pyproject.toml`` must read ``not_applicable`` with a non-``ok`` status -- never a
silent pass.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.astropy.code_quality  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


def py(path: str, source: str, *, new: bool = False):
    """A Python file with every line marked as written by the agent."""
    lines = source.split("\n")
    return make_file(path, [(n, text) for n, text in enumerate(lines, start=1)],
                     head_text=source, is_new=new)


def toml(requires: str = ">=3.11", dependencies: str = '"numpy", "pyerfa"'):
    source = (f'[project]\nrequires-python = "{requires}"\n'
              f"dependencies = [{dependencies}]\n")
    return py("pyproject.toml", source)


@pytest.fixture(scope="module")
def corpus():
    """astropy's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("astropy"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


MATCH_STATEMENT = py("astropy/io/fits/header.py",
                     "def f(x):\n    match x:\n        case 1:\n            return 2\n")


# --- C050 pre-commit rewrites are re-staged --------------------------------------------


REWROTE = Command(index=0, command="pre-commit run --all-files",
                  output="ruff-format...Failed\n- files were modified by this hook\n")


def test_c050_passes_when_the_files_are_staged_afterwards(corpus):
    bundle = make_bundle(files=[MATCH_STATEMENT],
                         commands=(REWROTE, Command(index=1, command="git add -A")))
    assert verdict("ASTROPY-C050", bundle, corpus).verdict == "pass"


def test_c050_fails_when_nothing_is_staged_afterwards(corpus):
    bundle = make_bundle(files=[MATCH_STATEMENT], commands=(REWROTE,))
    assert verdict("ASTROPY-C050", bundle, corpus).verdict == "fail"


def test_c050_finds_no_target_when_pre_commit_rewrote_nothing(corpus):
    """Firing on the `git add` instead would find only agents that already complied."""
    clean = Command(index=0, command="pre-commit run --all-files",
                    output="ruff-format...Passed\n")
    bundle = make_bundle(files=[MATCH_STATEMENT], commands=(clean,))
    row = verdict("ASTROPY-C050", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C076 code matches the supported Python versions -----------------------------------


def test_c076_passes_when_the_construct_is_within_the_floor(corpus):
    bundle = make_bundle(files=[MATCH_STATEMENT, toml(">=3.11")])
    assert verdict("ASTROPY-C076", bundle, corpus).verdict == "pass"


def test_c076_fails_when_the_construct_is_newer_than_the_floor(corpus):
    bundle = make_bundle(files=[MATCH_STATEMENT, toml(">=3.9")])
    row = verdict("ASTROPY-C076", bundle, corpus)
    assert row.verdict == "fail" and "match" in row.notes


def test_c076_withholds_when_the_floor_is_not_in_the_bundle(corpus):
    """The floor lives in the checked-out tree; withholding is the honest answer (§5)."""
    row = verdict("ASTROPY-C076", make_bundle(files=[MATCH_STATEMENT]), corpus)
    assert row.verdict == "not_applicable" and row.status == "tool_missing"


def test_c076_finds_no_target_when_no_python_was_written(corpus):
    doc = make_file("docs/index.rst", [(1, "Text.")])
    row = verdict("ASTROPY-C076", make_bundle(files=[doc]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C077 the core package's import-time dependencies ----------------------------------


def test_c077_passes_on_a_permitted_import(corpus):
    source = py("astropy/io/fits/header.py", "import numpy as np\nfrom astropy import units\n")
    assert verdict("ASTROPY-C077", make_bundle(files=[source]), corpus).verdict == "pass"


def test_c077_fails_on_a_third_party_import_at_module_level(corpus):
    source = py("astropy/io/fits/header.py", "import scipy.stats\n")
    assert verdict("ASTROPY-C077", make_bundle(files=[source]), corpus).verdict == "fail"


def test_c077_finds_no_target_for_an_import_inside_a_function(corpus):
    """A dependency imported where it is used is the sanctioned form, not this rule's
    subject."""
    source = py("astropy/io/fits/header.py", "def f():\n    import scipy.stats\n    return 1\n")
    row = verdict("ASTROPY-C077", make_bundle(files=[source]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c077_finds_no_target_for_a_guarded_optional_import(corpus):
    source = py("astropy/io/fits/header.py",
                "try:\n    import scipy\nexcept ImportError:\n    scipy = None\n")
    row = verdict("ASTROPY-C077", make_bundle(files=[source]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C195 no undeclared dependency ------------------------------------------------------


def test_c195_passes_on_a_declared_dependency(corpus):
    source = py("astropy/io/fits/header.py", "def f():\n    import scipy\n    return scipy\n")
    assert verdict("ASTROPY-C195", make_bundle(files=[source]), corpus).verdict == "pass"


def test_c195_fails_on_an_undeclared_dependency(corpus):
    source = py("astropy/io/fits/header.py", "import fancylib\n")
    row = verdict("ASTROPY-C195", make_bundle(files=[source]), corpus)
    assert row.verdict == "fail" and "fancylib" in row.notes


def test_c195_finds_no_target_when_only_the_standard_library_is_imported(corpus):
    source = py("astropy/io/fits/header.py", "import os\nfrom astropy import units\n")
    row = verdict("ASTROPY-C195", make_bundle(files=[source]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

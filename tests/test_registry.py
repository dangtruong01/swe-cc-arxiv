"""The corpus is the authority. These tests fail when the code and the corpus drift."""

from __future__ import annotations

from conftest import TRAJ_RESOLVED

from compliance.cli import main
import pytest

from compliance.core.registry import corpus_path_for, in_batch, registered

import compliance.rules.sympy.git_conventions  # noqa: F401  (registers the rules)
import compliance.rules.sympy.pr_metadata  # noqa: F401
import compliance.rules.sympy.specialized  # noqa: F401
import compliance.rules.sympy.tests  # noqa: F401
import compliance.rules.sympy.documentation  # noqa: F401
import compliance.rules.sympy.ai_policy  # noqa: F401
import compliance.rules.sympy.code_quality  # noqa: F401
from compliance.cli import RULE_MODULES, load_rule_modules

CATEGORY = "Git and commit conventions"

# Every repository with a pack. Derived from the composition root rather than listed here,
# so a third pack is covered the day it is registered and cannot be forgotten.
REPOS = sorted(RULE_MODULES)
for _repo in REPOS:
    load_rule_modules(_repo)


def corpus_of(repo: str):
    from compliance.core.registry import corpus_path_for, load_corpus

    return load_corpus(corpus_path_for(repo))


def registered_for(repo: str):
    """Rules belonging to one repository's pack.

    The registry is global and every pack that has been imported is in it, so a check
    against a single corpus has to select first. Rule ids carry their repository as a
    prefix, which is what makes that possible without a second registry.
    """
    prefix = f"{repo.upper()}-"
    return [r for r in registered() if r.id.startswith(prefix)]


@pytest.mark.parametrize("repo", REPOS)
def test_every_registered_rule_exists_in_the_corpus(repo):
    corpus = corpus_of(repo)
    assert [r.id for r in registered_for(repo) if r.id not in corpus] == []


@pytest.mark.parametrize("repo", REPOS)
def test_every_registered_rule_is_in_the_scored_batch(repo):
    """Care and must. Implementing a rule outside the batch would inflate the denominator."""
    batch = set(in_batch(corpus_of(repo)))
    assert [r.id for r in registered_for(repo) if r.id not in batch] == []


def test_the_whole_git_conventions_category_is_implemented(corpus):
    """The first category ever implemented, pinned at its exact size.

    Scoped to one pack: `registered()` is global and every imported pack is in it, so
    filtering on the category alone would mix repositories that happen to share a
    category name. The count is the point of the test -- it is what would catch a rule
    quietly dropped from the corpus.
    """
    expected = {rule_id for rule_id in in_batch(corpus)
                if corpus[rule_id].shared_category == CATEGORY}
    implemented = {r.id for r in registered_for("sympy") if r.category == CATEGORY}
    assert implemented == expected
    assert len(expected) == 14


@pytest.mark.parametrize("repo", REPOS)
def test_implemented_categories_are_complete(repo):
    """A partially-implemented category would silently score some rules and not others,
    making its rate meaningless. Each category is all-or-nothing, per repository."""
    from collections import defaultdict

    corpus = corpus_of(repo)
    done = defaultdict(set)
    for r in registered_for(repo):
        done[r.category].add(r.id)
    for category, ids in done.items():
        expected = {rid for rid in in_batch(corpus)
                    if corpus[rid].shared_category == category}
        assert ids == expected, f"{repo}/{category}: missing {sorted(expected - ids)}"


def test_every_rule_declares_both_layers_in_its_docstring():
    """§4.2: if the pre-condition sentence names the thing the rule demands rather than
    the situation that invokes it, the rule is wrong. Stating both keeps that visible."""
    for rule in registered():
        assert "Pre-condition:" in rule.doc, f"{rule.id} does not state its pre-condition"
        assert "Pass condition:" in rule.doc, f"{rule.id} does not state its pass condition"


def test_repo_conf_locates_the_corpus():
    assert corpus_path_for("sympy").exists()


def test_cli_check_runs_end_to_end(capsys):
    assert main(["check", str(TRAJ_RESOLVED)]) == 0
    out = capsys.readouterr().out
    assert "SYMPY-C023" in out and "compliance rate" in out


def test_cli_build_bundle_runs_end_to_end(capsys):
    assert main(["build-bundle", str(TRAJ_RESOLVED)]) == 0
    assert '"commits_source": "trajectory_shim"' in capsys.readouterr().out


def test_every_rule_declares_what_it_reads():
    """Open question #4 from the 12 Aug minutes: when a section is missing we must be
    able to say which rules are affected, rather than discover it as odd verdicts."""
    from compliance.core.registry import EVIDENCE_SOURCES

    for rule in registered():
        assert rule.reads, f"{rule.id} declares no evidence sources"
        assert not set(rule.reads) - set(EVIDENCE_SOURCES), f"{rule.id} reads something unknown"


def test_declared_sources_cover_what_the_rules_actually_touch():
    """A rule that reads bundle.commits but declares only ('files',) would make the
    evidence map lie. Catch the common cases by inspecting the source."""
    import inspect

    from compliance.core.registry import EVIDENCE_SOURCES

    for rule in registered():
        source = inspect.getsource(type(rule.checker))
        for field in EVIDENCE_SOURCES:
            if f"bundle.{field}" in source or f"b.{field}" in source:
                assert field in rule.reads, f"{rule.id} touches bundle.{field} but does not declare it"


def test_repo_conf_supplies_everything_a_new_repo_needs():
    """Adding a repository must be config plus a rule pack -- never an edit to Layer A
    or B. Anything the shared machinery needs has to come from repo.conf."""
    from compliance.core.registry import repo_conf

    conf = repo_conf("sympy")
    for key in ("DISPLAY_NAME", "DOCS_URL", "CORPUS", "REPO_URL"):
        assert conf.get(key), f"repo.conf is missing {key}"


# --- cross-pack coverage guard ------------------------------------------------------
#
# test_git_conventions.py carries the same guard for SymPy's git rules, in depth: it also
# demands a `not_applicable` case by name. This one is shallower and wider -- it asks only
# that every registered rule, in every pack, is named by at least one test somewhere. It
# exists because the deep guard is scoped to one file, and a rule in a pack whose tests
# live elsewhere was invisible to it.
#
# Matching is by the rule's short number, so two packs that both define C059 will satisfy
# each other. That makes this lenient, not strict: it catches a rule with no tests at all,
# which is the failure that actually happened.

#: Rules known to have no tests, with the reason. A rule may only be added here with one.
UNTESTED_BY_OVERSIGHT = {
    # Found when this guard was added, after the seven new packs were registered. Predates
    # them: the old guard only covered "Git and commit conventions", and C109 is a
    # documentation rule, so nothing ever asked for its tests.
    "DJANGO-C109",
}


def test_every_registered_rule_is_named_by_some_test():
    import pathlib

    source = "\n".join(
        p.read_text() for p in sorted(pathlib.Path(__file__).parent.glob("*.py"))
    )
    missing = sorted(
        r.id
        for r in registered()
        if r.id not in UNTESTED_BY_OVERSIGHT
        and f"test_{r.id.split('-')[-1].lower()}_" not in source
    )
    assert not missing, f"registered with no test named after them: {missing}"

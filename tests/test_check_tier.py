"""Who is allowed to decline to grade -- and it is not the implementer's call.

Withholding (``status='tool_missing'``) is invisible by construction. A rule that gives up
returns ``not_applicable`` with a status that is exactly what an honest withhold looks
like; it leaves the denominator permanently, and no test fails. Same silent-denominator
shape as an over-narrow pre-condition.

The invariant went through two forms and the second is the one that holds.

**Tier-only (superseded).** *A rule may withhold only if its ``CheckTier`` is
``differential``.* True but too coarse to be useful: C071 and C102 need a before/after test
run, C104 needs per-test durations, C115 needs doctests executed. All three are
``differential``, and the first two became answerable the moment ``eval_report.json`` was
wired into the bundle while the others did not. The tier cannot tell them apart, so the
invariant could not either -- it kept permitting C071 to withhold after C071 had the
evidence it needed.

**Declaration-based (current).** *A rule may withhold only if something it declares in
``reads`` is absent from the bundle in front of it.* Every rule already names its inputs,
and the sources Phase 5 will supply -- ``test_timings``, ``doctest_run``,
``repeated_runs``, ``expression_eval``, ``lint_run`` -- are registered but carried by
nothing. So "I cannot answer this" becomes a named missing input rather than a judgement,
and the exemption **sunsets itself**: when Phase 5 makes the bundle carry timings, C104
stops being allowed to withhold without anyone remembering to come back here.
"""

from __future__ import annotations

import pytest
from conftest import TRAJ_EMPTY_PATCH, TRAJ_PHASE0, TRAJ_RESOLVED, make_bundle, make_commit

from compliance.bundle.builder import build_bundle
from compliance.core.models import FileChange
from compliance.core.paths import discover
from compliance.core.registry import (
    EVIDENCE_SOURCES, corpus_path_for, evidence_present, load_corpus, registered,
)
from compliance.core.runner import run_rules

import compliance.rules.sympy.git_conventions  # noqa: F401  (registers the rules)
import compliance.rules.sympy.pr_metadata  # noqa: F401
import compliance.rules.sympy.specialized  # noqa: F401
import compliance.rules.sympy.tests  # noqa: F401
import compliance.rules.sympy.documentation  # noqa: F401
import compliance.rules.sympy.ai_policy  # noqa: F401
import compliance.rules.sympy.code_quality  # noqa: F401

# Sources registered for Phase 5 and carried by nothing today. A rule declaring one of
# these is entitled to withhold until the bundle supplies it.
UNSUPPLIED = frozenset({
    "test_timings", "repeated_runs", "doctest_run", "lint_run", "expression_eval",
    "full_suite_run", "deprecated_api_run", "repo_version",
})

# The one rule graded despite its tier, with the reason. Plan §4.2 names C069 as the worked
# case for invariant 2: new functionality with no test must read `fail`, not
# `not_applicable`, or an agent that writes nothing escapes. Graded statically with
# heuristic=True. Anything added here needs the same kind of justification.
GRADED_DESPITE_TIER = {
    "SYMPY-C069": "plan §4.2 makes it the worked case for invariant 2",
}


def _rich_bundle():
    """A contribution that fires as many pre-conditions as one bundle can."""
    source = (
        '"""Module."""\n'
        "import numpy\n"
        "from sympy.testing.pytest import raises, XFAIL, slow\n"
        "\n"
        "@XFAIL\n"
        "def test_broken():\n"
        "    assert x.is_positive\n"
        "\n"
        "@slow\n"
        "def test_big():\n"
        "    raises(ValueError, f(1))\n"
        "    assert str(f(x)) == 'x'\n"
        "    assert f(1/2) == 0\n"
        "    assert sympify('x + 1') == f(x)\n"
    )
    lines = source.split("\n")
    change = FileChange(
        path="sympy/core/tests/test_rich.py",
        authored_lines=frozenset(range(1, len(lines) + 1)),
        added_lines=tuple((n, lines[n - 1]) for n in range(1, len(lines))),
        head_text=source,
        is_new=True,
    )
    return make_bundle(
        files={change.path: change},
        commits=[make_commit("fix: thing\n\nA body sentence.", branch="fix/thing")],
        pr_text="Fixes #123\n<!-- BEGIN RELEASE NOTES -->\nNO ENTRY\n<!-- END RELEASE NOTES -->",
    )


@pytest.fixture(scope="module")
def corpus_rows():
    """Rows plus the bundle each came from -- the invariant is per-run, not per-rule.

    Scored over every stored run as well as the synthetic ones, because the fixtures alone
    do not exercise the paths that matter: no stored fixture has a regression, so a dead
    fail path in a rule wired to the eval report would sit here undetected.
    """
    corpus = load_corpus(corpus_path_for("sympy"))
    rules = registered()
    bundles = [build_bundle(t) for t in (TRAJ_RESOLVED, TRAJ_EMPTY_PATCH, TRAJ_PHASE0)]
    bundles += [build_bundle(run.trajectory) for run in discover()]
    bundles.append(_rich_bundle())
    out = []
    for bundle in bundles:
        for row in run_rules(bundle, rules, corpus):
            out.append((row, bundle))
    return out


@pytest.fixture(scope="module")
def declared():
    return {r.id: frozenset(r.reads) for r in registered()}


def test_a_rule_may_withhold_only_when_something_it_reads_is_missing(corpus_rows, declared):
    """The invariant. Catches a rule declining to grade evidence it actually has -- the
    row would read `not_applicable / tool_missing`, which is indistinguishable from an
    honest withhold."""
    offenders = set()
    for row, bundle in corpus_rows:
        if row.status != "tool_missing":
            continue
        reads = declared[row.rule_id]
        missing = (reads & UNSUPPLIED) | (reads - evidence_present(bundle) - UNSUPPLIED)
        if not missing:
            offenders.add(f"{row.rule_id} withheld with all of {sorted(reads)} present: "
                          f"{row.notes[:70]}")
    assert sorted(offenders) == [], sorted(offenders)


def test_every_declared_source_is_registered(declared):
    unknown = {rid: sorted(reads - set(EVIDENCE_SOURCES))
               for rid, reads in declared.items() if reads - set(EVIDENCE_SOURCES)}
    assert unknown == {}, unknown


def test_the_unsupplied_sources_really_are_unsupplied(corpus_rows):
    """Guard the exemption. If a Phase 5 source starts being carried, the rules that
    declare it must stop withholding -- and this fails to say so, rather than the
    exemption quietly outliving its reason."""
    carried = set()
    for _, bundle in corpus_rows:
        carried |= evidence_present(bundle)
    still_unsupplied = UNSUPPLIED - carried
    assert still_unsupplied == UNSUPPLIED, (
        f"{sorted(UNSUPPLIED & carried)} are now carried by the bundle. Remove them from "
        f"UNSUPPLIED so the rules declaring them are required to grade."
    )


def test_a_rule_wired_to_the_evaluation_actually_grades_when_it_can(corpus_rows, declared):
    """Wired but dead is the failure this catches.

    C071 read the wrong bucket for regressions -- `PASS_TO_FAIL` rather than
    `PASS_TO_PASS.failure` -- so on the one pilot run with a real regression it reported
    none, and its fail path could never fire. Nothing else in the suite noticed, because
    the unit test encoded the same misreading.
    """
    wired = {rid for rid, reads in declared.items() if "evaluation" in reads}
    graded, had_targets = set(), set()
    for row, bundle in corpus_rows:
        if row.rule_id not in wired:
            continue
        # A target we could not even parse can never grade, and correctly so. Counting it
        # as "had a chance to grade" would make this test fire on the agent's own invalid
        # Python instead of on a dead code path.
        if row.n_targets and bundle.evaluation is not None and row.status != "parse_error":
            had_targets.add(row.rule_id)
        if row.verdict in ("pass", "fail"):
            graded.add(row.rule_id)
    dead = sorted(had_targets - graded)
    assert dead == [], (
        f"{dead} have targets on runs carrying an evaluation but never returned a verdict. "
        f"Either the reading of tests_status is wrong, or the rule cannot in fact be "
        f"answered from it and should declare a Phase 5 source instead."
    )


def _rests_on_unreadable(row) -> bool:
    """The verdict's ground is a file that would not parse, not the rule's own evidence.

    Since 25 Aug an unparseable module is a violation of every rule that reads it, so a
    `differential` rule can now fail without its run ever happening. That is not a static
    proxy for the run -- it is an independent and sufficient ground, and the exemption is
    narrow because it keys on the target the failure was recorded against.
    """
    return any(str(t.get("key", "")).startswith("unreadable:") for t in (row.targets or []))


def test_differential_rules_are_not_graded_by_a_static_proxy(corpus_rows):
    """The other direction: a rule needing a run must not be answered by a stand-in,
    which would produce confident verdicts from evidence that does not exist."""
    # `corpus_rows` are scored rows from stored runs, which are all one repository's; the
    # lookup is scoped to that corpus for the same reason.
    tiers = {rid: r.check_tier for rid, r in load_corpus(corpus_path_for("sympy")).items()}
    graded = sorted({
        row.rule_id for row, _ in corpus_rows
        if tiers.get(row.rule_id) == "differential"
        and row.verdict in ("pass", "fail")
        and not _rests_on_unreadable(row)
        and row.rule_id not in GRADED_DESPITE_TIER
        and "evaluation" not in {r.id: r.reads for r in registered()}[row.rule_id]
    })
    assert graded == [], (
        f"{graded} have CheckTier=differential, read no evaluation, and still returned a "
        f"verdict. Either the check is a proxy for evidence we do not have, or the rule "
        f"should declare the source that answers it."
    )


def test_the_exception_list_is_real_and_still_differential():
    tiers = {rid: r.check_tier for rid, r in load_corpus(corpus_path_for("sympy")).items()}
    for rule_id, reason in GRADED_DESPITE_TIER.items():
        assert rule_id in tiers, f"{rule_id} is not in the corpus"
        assert tiers[rule_id] == "differential", (
            f"{rule_id} is tier={tiers[rule_id]}, so it needs no exception -- remove it"
        )
        assert reason.strip(), f"{rule_id} is excepted with no stated reason"


def test_no_implemented_rule_has_a_judgment_tier():
    """The batch filter is Care and must; it never filtered CheckTier. It did not need to
    -- `judgment` rules do not survive it. If one ever does, it cannot be checked
    mechanically at all and the batch definition has to be revisited.

    Checked across every pack: the registry is global, so a rule is looked up in its own
    repository's corpus rather than in one chosen corpus.
    """
    from compliance.cli import RULE_MODULES

    tiers: dict[str, str] = {}
    for repo in RULE_MODULES:
        tiers.update({rid: r.check_tier for rid, r in load_corpus(corpus_path_for(repo)).items()})
    bad = sorted(r.id for r in registered() if tiers.get(r.id) == "judgment")
    assert bad == [], bad


def test_a_static_grade_of_a_differential_rule_is_declared(corpus=None):
    """A rule graded statically must not silently claim a tier it does not honour.

    `differential` means the corpus author judged that answering the rule needs a run --
    base vs head, a tool executed twice. A rule that grades it from the patch alone is
    making a different claim, and the disagreement has to be visible rather than resolved
    quietly in either direction.

    Three ways to be honest about it, all accepted here: mark the check `heuristic=True`,
    which says outright that it is a proxy; declare an evidence source the bundle does not
    carry, which makes it withhold; or read evidence that IS a run -- `evaluation` is the
    grading harness's own report, and a rule reading it is answering from a real execution
    rather than standing in for one. What is not accepted is an exact-looking verdict on
    evidence the tier says does not exist.

    Scoped across every pack -- the registry is global, so each rule is looked up in its
    own repository's corpus.
    """
    from compliance.cli import RULE_MODULES, load_rule_modules

    offenders = []
    for repo in RULE_MODULES:
        load_rule_modules(repo)
        corpus = load_corpus(corpus_path_for(repo))
        prefix = f"{repo.upper()}-"
        for rule in registered():
            if not rule.id.startswith(prefix) or rule.id not in corpus:
                continue
            if corpus[rule.id].check_tier != "differential":
                continue
            withholds = bool(set(rule.reads) & set(UNSUPPLIED))
            # A rule that reads a stored run result is not standing in for a run; it is
            # reading one. `commands` is the agent's own command log -- whether it ran a
            # tool is a fact about the trajectory, not a proxy for the tool's output.
            reads_a_run = bool(set(rule.reads) & {"evaluation", "commands"})
            if not rule.heuristic and not withholds and not reads_a_run:
                offenders.append(rule.id)
    assert offenders == [], (
        f"{sorted(offenders)} are CheckTier=differential but grade exactly from the patch. "
        f"Mark the check heuristic, or declare the evidence that would really answer it."
    )

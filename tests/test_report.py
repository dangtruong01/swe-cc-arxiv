"""Aggregation and alerts.

The aggregation tests pin the one thing that must not drift: a summary reports the
**pair**, and withheld rows leave both sides of it. Folding a row we could not judge into
either the numerator or the denominator turns a limit of the instrument into a claim about
the agent.

The alert tests are written from real checker defects found during development.
Every one of them is a real bug that a person caught by looking at a number; the point of
the module is that nobody has to.
"""

from __future__ import annotations

from compliance.core.paths import RunDir
from compliance.core.registry import corpus_path_for, load_corpus
from compliance.report.aggregate import Row, per_rule, per_run, summarise
from compliance.report.alerts import (
    always_failing, dead_rules, thin_denominators, withheld_evidence,
)

CORPUS = load_corpus(corpus_path_for("sympy"))


def row(rule_id="SYMPY-C023", verdict="pass", status="ok", **kw):
    base = dict(
        run_id="r", instance_id="i__i-1", base_commit="0" * 40, created_at="2016-01-01",
        condition="naive", model="m", attempt_n=1, rule_id=rule_id,
        shared_category="Git and commit conventions", strength="must",
        verdict=verdict, status=status, n_targets=1, n_targets_preexisting=0,
        n_violating=0, evidence="direct", targets=[], notes="", checker_version="0",
        heuristic=False,
    )
    base.update(kw)
    return Row(base)


def test_a_withheld_row_is_triggered_but_not_graded():
    """Its pre-condition fired, so the work brought the rule into scope; only the verdict
    is missing. It therefore counts toward triggering and leaves compliance alone."""
    s = summarise([row(verdict="pass"), row(verdict="fail"),
                   row(verdict="not_applicable", status="tool_missing")])
    assert (s.n_rules, s.n_activated, s.n_pass, s.n_fail, s.n_withheld) == (3, 2, 1, 1, 1)
    assert s.n_triggered == 3
    assert s.conditional_compliance == 0.5
    assert s.applicability == 1.0


def test_an_inapplicable_row_is_not_the_same_as_a_withheld_one():
    """One says the rule never applied; the other says it applied and we were blind."""
    s = summarise([row(verdict="not_applicable", status="ok"),
                   row(verdict="not_applicable", status="parse_error")])
    assert (s.n_inapplicable, s.n_withheld) == (1, 1)
    assert s.n_triggered == 1
    assert s.applicability == 0.5
    assert s.conditional_compliance is None


def test_the_lazy_agent_cannot_win_on_the_pair():
    """Why the pair and not the rate, as an executable example. The lazy bundle beats the
    thorough one on the rate and loses badly on applicability, which is why the pair is
    reported and the rate never is."""
    lazy = summarise([row(verdict="pass")] * 6 + [row(verdict="not_applicable")] * 60)
    thorough = summarise([row(verdict="pass")] * 23 + [row(verdict="fail")]
                         + [row(verdict="not_applicable")] * 42)
    assert lazy.conditional_compliance > thorough.conditional_compliance
    assert lazy.applicability < thorough.applicability


def test_dead_rule_alert_fires_on_a_rule_that_judged_nothing():
    stats = per_rule([row(rule_id="SYMPY-C042", verdict="not_applicable")] * 5)
    alerts = dead_rules(stats, CORPUS)
    assert [a.subject for a in alerts] == ["SYMPY-C042"]
    assert "pre-condition" in alerts[0].action


def test_dead_rule_alert_stays_quiet_for_a_rule_that_declared_why():
    """A withheld rule is not silently dead -- it says what it lacks."""
    stats = per_rule([row(rule_id="SYMPY-C104", verdict="not_applicable",
                          status="tool_missing")] * 5)
    assert dead_rules(stats, CORPUS) == []


def test_always_fails_alert_needs_enough_runs_to_mean_anything():
    few = per_rule([row(rule_id="SYMPY-C078", verdict="fail")] * 2)
    many = per_rule([row(rule_id="SYMPY-C078", verdict="fail")] * 6)
    assert always_failing(few) == []
    assert [a.subject for a in always_failing(many)] == ["SYMPY-C078"]


def test_withholding_is_counted_and_never_escalated():
    """One info line with the count, whatever the corpus tier says.

    Both rules below withhold; C023 is `static` and C104 is `differential`. The old alert
    raised a critical for the first and stayed quiet for the second, which is the superseded
    tier-only invariant -- it fired on C002 and C003 for declaring `lint_run` they genuinely
    lack. Legitimacy is `tests/test_check_tier.py`'s job, over every stored run; this one
    only reports how much the bundle could not answer.
    """
    alerts = withheld_evidence([
        row(rule_id="SYMPY-C023", verdict="not_applicable", status="tool_missing"),
        row(rule_id="SYMPY-C104", verdict="not_applicable", status="tool_missing"),
    ])
    assert [(a.severity, a.code, a.subject) for a in alerts] == [("info", "WITHHELD", "2 row(s)")]


def test_no_withheld_rows_raises_nothing():
    assert withheld_evidence([row(rule_id="SYMPY-C023", verdict="pass")]) == []


def test_thin_denominator_alert_flags_a_run_that_activated_almost_nothing():
    rows = [row(verdict="pass")] * 2 + [row(verdict="not_applicable")] * 64
    assert [a.code for a in thin_denominators(rows)] == ["THIN"]


def test_per_run_groups_by_the_whole_cell():
    """A run is (framework, model, instance, condition, attempt) -- all five.

    Two models under one condition are two runs. Keyed on condition alone they merge,
    and the merge takes the smaller cell's rows with it silently.
    """
    rows = [row(condition="naive"), row(condition="guided"), row(condition="guided")]
    assert len(per_run(rows)) == 2

    two_models = [row(condition="guided", model="gemini-2.5-flash"),
                  row(condition="guided", model="qwen3-coder")]
    assert len(per_run(two_models)) == 2, "two models collapsed into one run"

    two_frameworks = [row(condition="guided", framework="mini-swe-agent"),
                      row(condition="guided", framework="openhands")]
    assert len(per_run(two_frameworks)) == 2, "two frameworks collapsed into one run"


def test_only_the_named_arms_are_in_the_comparison():
    """`naive-salient` is a salience manipulation kept for its own findings, not a third
    arm. Pooling it in would put a variant of the control beside the control."""
    from compliance.report.aggregate import COMPARISON_CONDITIONS, split_conditions

    rows = [row(condition="naive"), row(condition="guided"),
            row(condition="naive-salient"), row(condition="unknown")]
    comparison, exploratory = split_conditions(rows)
    assert set(comparison) == set(COMPARISON_CONDITIONS)
    assert set(exploratory) == {"naive-salient", "unknown"}


def test_a_new_condition_cannot_join_the_comparison_by_accident():
    """The arms are an allowlist, not a denylist. A condition nobody has thought about
    lands in exploratory, which is the safe direction: it gets reported, not pooled."""
    from compliance.report.aggregate import split_conditions

    comparison, exploratory = split_conditions([row(condition="some-new-arm")])
    assert comparison == {}
    assert set(exploratory) == {"some-new-arm"}


def test_comparison_rows_drops_everything_exploratory():
    from compliance.report.aggregate import comparison_rows

    rows = [row(condition="guided"), row(condition="naive-salient")]
    assert [r.condition for r in comparison_rows(rows)] == ["guided"]

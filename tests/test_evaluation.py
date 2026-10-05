"""The functional half: reading what the harness said, and refusing to guess.

The defect these guard against is not a crash. Two different JSON documents were written
to the same filename -- a per-instance report and a run-level summary -- and the summary
was copied into part of the corpus. It looks like a graded run. It answers nothing about
which tests changed state, and because harness run ids were once keyed on instance alone,
the summary sitting beside a run may be reporting a *different condition's* outcome.

That is why `shape` is a first-class field rather than something normalised away.
"""

from __future__ import annotations

import json

from compliance.core.evaluation import EvalReport, audit, load, parse
from compliance.core.paths import RunDir

INSTANCE_REPORT = json.dumps({
    "sympy__sympy-11618": {
        "patch_is_None": False,
        "patch_successfully_applied": True,
        "resolved": True,
        "tests_status": {
            "FAIL_TO_PASS": {"success": ["test_distance"], "failure": []},
            "PASS_TO_PASS": {"success": ["test_a", "test_b"], "failure": []},
            "FAIL_TO_FAIL": {"success": [], "failure": []},
            "PASS_TO_FAIL": {"success": [], "failure": []},
        },
    }
})

SUMMARY = json.dumps({
    "total_instances": 1, "submitted_instances": 1, "completed_instances": 1,
    "resolved_instances": 0, "unresolved_instances": 1,
    "completed_ids": ["sympy__sympy-11618"],
})


def test_a_per_instance_report_is_usable():
    report = parse(INSTANCE_REPORT)
    assert report.shape == "instance"
    assert report.resolved is True
    assert report.usable is True
    assert report.n_outcomes == 3
    assert report.newly_passing() == ("test_distance",)
    assert report.broke_nothing() is True


def test_a_run_level_summary_is_recognised_and_refused():
    """It has a resolved count, so it is tempting to treat it as a result. It cannot
    answer which tests changed state, and it may not even be this run's."""
    report = parse(SUMMARY)
    assert report.shape == "summary"
    assert report.usable is False
    assert report.tests_status == {}
    assert "not necessarily this run's" in report.note


def test_the_summary_is_recognised_by_its_own_keys_not_by_elimination():
    """A shape we cannot classify must not fall through into either bucket.

    The summary is identified by `total_instances`, not by "it isn't an instance
    report". Anything whose body is not an object is `unreadable`, so a future third
    format cannot quietly inherit either meaning.
    """
    assert parse(SUMMARY).shape == "summary"
    # An instance-shaped document with no tests_status is still an instance report --
    # it simply carries no per-test evidence, and says so.
    thin = parse(json.dumps({"i": {"resolved": True}}))
    assert (thin.shape, thin.usable) == ("instance", False)
    assert "no tests_status" in thin.note
    # A body that is not an object tells us nothing at all.
    assert parse(json.dumps({"something": "unexpected"})).shape == "unreadable"
    assert parse(json.dumps({"something": ["not", "a", "dict"]})).shape == "unreadable"


def test_malformed_input_is_reported_never_raised():
    assert parse("not json at all").shape == "unreadable"
    assert parse("{}").shape == "unreadable"
    assert parse("[]").shape == "unreadable"


def test_an_ungraded_run_is_absent_not_unresolved(tmp_path):
    """`absent` and `unresolved` are opposite claims. Conflating them would record a
    run we never graded as a run that failed -- which is exactly what happened to the
    naive arm when a shared summary sat in its place.

    A patch on disk is what separates "not graded yet" from "nothing to grade".
    """
    run = RunDir("r", "r__r-1", "naive", 1, root=tmp_path)
    run.mkdir()
    run.file("patch.diff").write_text("--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n")
    report = load(run)
    assert report.shape == "absent"
    assert report.resolved is None


def test_a_regression_is_a_pass_to_pass_failure_not_a_pass_to_fail():
    """The bucket name is the transition the dataset *expects*; success/failure says
    whether the expectation held. So a test that was meant to keep passing and now fails
    lands in PASS_TO_PASS.failure.

    This test exists because the first implementation read PASS_TO_FAIL instead, whose
    name merely looks like it means that. The one pilot run with a real regression
    reported none, so the rule depending on it could never fail -- a dead code path that
    no test would have caught, because the test encoded the same misreading.
    """
    text = json.dumps({"i": {"resolved": False, "tests_status": {
        "PASS_TO_PASS": {"success": ["kept_passing"], "failure": ["regressed"]},
        "PASS_TO_FAIL": {"success": ["expected_to_break"], "failure": []},
    }}})
    report = parse(text)
    assert report.regressions() == ("regressed",)
    assert "expected_to_break" not in report.regressions(), \
        "a break the dataset anticipated is not the agent regressing anything"
    assert report.broke_nothing() is False


def test_tests_reported_covers_every_bucket_and_outcome():
    """Needed to tell "the harness ran this test and it still fails" from "the harness
    never ran it", which are different answers and only one is evidence."""
    text = json.dumps({"i": {"resolved": True, "tests_status": {
        "FAIL_TO_PASS": {"success": ["a"], "failure": ["b"]},
        "FAIL_TO_FAIL": {"success": ["c"], "failure": []},
    }}})
    assert parse(text).tests_reported() == {"a", "b", "c"}


def test_audit_flags_only_unusable_runs(tmp_path):
    graded = RunDir("r", "r__r-1", "guided", 1, root=tmp_path)
    stale = RunDir("r", "r__r-2", "naive", 1, root=tmp_path)
    graded.mkdir().joinpath("eval_report.json").write_text(INSTANCE_REPORT)
    stale.mkdir().joinpath("eval_report.json").write_text(SUMMARY)
    flagged = {run.instance_id for run, _ in audit([graded, stale])}
    assert flagged == {"r__r-2"}


EMPTY_PATCH_SUMMARY = json.dumps({
    "total_instances": 1, "submitted_instances": 1, "completed_instances": 0,
    "resolved_instances": 0, "empty_patch_instances": 1,
    "empty_patch_ids": ["r__r-9"], "resolved_ids": [],
})


def test_an_empty_patch_is_not_gradeable_rather_than_ungraded(tmp_path):
    """The harness writes no per-instance report for an empty patch, so this run has no
    functional result and never will. Reporting it as a gap would send someone to re-run
    grading that cannot succeed."""
    run = RunDir("r", "r__r-9", "naive", 1, root=tmp_path)
    run.mkdir().joinpath("eval_report.json").write_text(EMPTY_PATCH_SUMMARY)
    report = load(run)
    assert report.shape == "not_gradeable"
    assert report.resolved is False
    assert audit([run]) == []


def test_the_empty_patch_claim_is_only_believed_when_the_run_agrees(tmp_path):
    """Summaries were once shared across conditions, so one cannot be trusted to be
    describing the run it sits beside. A patch on disk contradicts the claim."""
    run = RunDir("r", "r__r-9", "naive", 1, root=tmp_path)
    run.mkdir().joinpath("eval_report.json").write_text(EMPTY_PATCH_SUMMARY)
    run.file("patch.diff").write_text("--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n")
    report = load(run)
    assert report.shape == "summary", "a real patch means the empty-patch claim is not this run's"
    assert [r.instance_id for r, _ in audit([run])] == ["r__r-9"]


def test_a_missing_report_with_no_patch_is_also_not_gradeable(tmp_path):
    run = RunDir("r", "r__r-9", "naive", 1, root=tmp_path)
    run.mkdir()
    assert load(run).shape == "not_gradeable"

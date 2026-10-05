from __future__ import annotations

from pathlib import Path

import pytest

from compliance.bundle.commits import build_commit
from compliance.core.models import Command, EvidenceBundle, FileChange
from compliance.core.paths import RunDir
from compliance.core.registry import corpus_path_for

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNS = PROJECT_ROOT / "runs"
# Located through repo.conf, the same file run_test.sh and the generator read, so a
# corpus version bump does not have to be mirrored here.
CORPUS = corpus_path_for("sympy")

# Every stored run so far comes from this cell. Named once here so the fixtures below
# state which cell they are fixtures *of* -- when a second cell exists, a test that
# silently pulled "whichever run is at that path" would start meaning something else.
FIXTURE_FRAMEWORK = "mini-swe-agent"
FIXTURE_MODEL = "gemini-2.5-flash"


def fixture_traj(instance: str, condition: str, attempt: int = 1) -> Path:
    """A stored trajectory, located through the layout rather than a literal path.

    `RunDir` is the single authority on where runs live, so tests go through it too.
    Spelling the path out here meant a layout change broke thirty tests in a way that
    said nothing about what had actually moved.
    """
    return RunDir.for_instance(
        instance, condition, attempt,
        root=RUNS, framework=FIXTURE_FRAMEWORK, model=FIXTURE_MODEL,
    ).trajectory


# Pre-Phase-0 runs: no condition was recorded, hence `unknown`. They exercise the
# fallback paths (fixture shim, worktree_fallback) and are kept for exactly that.
TRAJ_RESOLVED = fixture_traj("sympy__sympy-11618", "unknown")
TRAJ_EMPTY_PATCH = fixture_traj("sympy__sympy-12096", "unknown")
TRAJ_PHASE0 = fixture_traj("sympy__sympy-11618", "naive")


def make_commit(message: str, *, sha: str = "abc1234", branch: str | None = None, **kwargs):
    return build_commit(sha, message.split("\n"), branch=branch, **kwargs)


def make_file(path: str, added: list[tuple[int, str]] | None = None, **kwargs) -> FileChange:
    added = added or []
    return FileChange(
        path=path,
        authored_lines=frozenset(n for n, _ in added),
        added_lines=tuple(added),
        **kwargs,
    )


def make_bundle(**overrides) -> EvidenceBundle:
    defaults = dict(
        instance_id="test__test-1",
        base_commit="0" * 40,
        created_at="2016-01-01T00:00:00Z",
        condition="naive",
        model="test/model",
        files={},
        commits=(),
        pr_text=None,
        commands=(),
        probe={},
        run_id="test-run",
        commits_source="log",
    )
    defaults.update(overrides)
    if isinstance(defaults["commands"], list):
        defaults["commands"] = tuple(
            c if isinstance(c, Command) else Command(index=i, command=c)
            for i, c in enumerate(defaults["commands"])
        )
    if isinstance(defaults["commits"], list):
        defaults["commits"] = tuple(defaults["commits"])
    if isinstance(defaults["files"], list):
        defaults["files"] = {f.path: f for f in defaults["files"]}
    return EvidenceBundle(**defaults)


@pytest.fixture(scope="session")
def corpus():
    from compliance.core.registry import load_corpus

    return load_corpus(CORPUS)


@pytest.fixture(scope="session")
def rules():
    import compliance.rules.sympy.git_conventions  # noqa: F401  (registers the rules)
    import compliance.rules.sympy.pr_metadata  # noqa: F401
    import compliance.rules.sympy.specialized  # noqa: F401
    import compliance.rules.sympy.tests  # noqa: F401
    import compliance.rules.sympy.documentation  # noqa: F401
    import compliance.rules.sympy.ai_policy  # noqa: F401
    import compliance.rules.sympy.code_quality  # noqa: F401
    from compliance.core.registry import registered

    return registered()


# ---------------------------------------------------------------------------------------
# Tests that need material outside this release. They run once it exists and are skipped
# otherwise, with the reason printed.
#   * the mini-swe-agent checkout, created by `frameworks/setup.sh mini-swe-agent`
#   * stored runs under runs/, written by a sweep (the pilot runs these tests were
#     written against are not part of the released results)
import pytest as _pytest
from pathlib import Path as _Path

_ROOT = _Path(__file__).resolve().parents[1]
_NEEDS_SCAFFOLD = {"test_prompt_variants.py"}
_NEEDS_RUNS = {
    "test_bundle_parsers.py::test_a_bundle_takes_its_identity_from_the_directory_when_the_run_does_not_say",
    "test_bundle_parsers.py::test_commands_are_paired_with_their_output",
    "test_bundle_parsers.py::test_every_stored_run_scores_under_a_distinct_key",
    "test_bundle_parsers.py::test_pr_text_comes_from_the_agent_not_the_prompt",
    "test_bundle_parsers.py::test_run_dir_is_recovered_from_the_layout",
    "test_check_tier.py::test_a_rule_may_withhold_only_when_something_it_reads_is_missing",
    "test_check_tier.py::test_a_rule_wired_to_the_evaluation_actually_grades_when_it_can",
    "test_check_tier.py::test_differential_rules_are_not_graded_by_a_static_proxy",
    "test_check_tier.py::test_the_unsupplied_sources_really_are_unsupplied",
    "test_patch_scope.py::test_pre_phase0_trajectories_fall_back_honestly",
    "test_purity.py::test_running_every_rule_performs_no_io",
    "test_registry.py::test_cli_build_bundle_runs_end_to_end",
    "test_registry.py::test_cli_check_runs_end_to_end",
    "test_retrieval.py::test_the_live_naive_run_is_flagged_void",
}
_KNOWN_FAILING = {
    "test_check_tier.py::test_a_static_grade_of_a_differential_rule_is_declared":
        "MATPLOTLIB-C082 and PYDATA-C069 are labelled differential but graded from the "
        "patch alone; the label is kept as released",
}


def pytest_collection_modifyitems(config, items):
    scaffold = (_ROOT / "mini-swe-agent-run" / "mini-swe-agent" / "swebench_pr_compliance.yaml").exists()
    runs = (_ROOT / "runs").is_dir()
    for item in items:
        key = f"{item.path.name}::{item.originalname}"
        if item.path.name in _NEEDS_SCAFFOLD and not scaffold:
            item.add_marker(_pytest.mark.skip(reason="needs frameworks/setup.sh mini-swe-agent"))
        elif key in _NEEDS_RUNS and not runs:
            item.add_marker(_pytest.mark.skip(reason="needs stored runs under runs/"))
        elif key in _KNOWN_FAILING:
            item.add_marker(_pytest.mark.xfail(reason=_KNOWN_FAILING[key], strict=True))

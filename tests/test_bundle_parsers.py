"""Parser sanity-checking lives here, not in the pipeline (docs/checker-authoring.md §9)."""

from __future__ import annotations

import json

import pytest
from conftest import TRAJ_EMPTY_PATCH, TRAJ_RESOLVED

from compliance.bundle.commits import parse_log, scrape_commits_from_commands
from compliance.bundle.diff import parse_unified_diff
from compliance.bundle.trajectory import (
    commands,
    parse_probe,
    patch_text,
    pr_text,
    submission_sections,
)
from compliance.core.models import Command

# --- diff --------------------------------------------------------------------------

SIMPLE_DIFF = """diff --git a/mod.py b/mod.py
index b859599..ea74361 100644
--- a/mod.py
+++ b/mod.py
@@ -1,3 +1,4 @@
 def f():
-    return 1
+    return 2
+    # added
 tail
"""

MULTI_DIFF = SIMPLE_DIFF + """diff --git a/new.py b/new.py
new file mode 100644
index 0000000..17e2eaa
--- /dev/null
+++ b/new.py
@@ -0,0 +1,2 @@
+import os
+print(os)
diff --git a/logo.png b/logo.png
new file mode 100644
index 0000000..aaaaaaa
Binary files /dev/null and b/logo.png differ
"""


def test_added_lines_get_post_patch_numbers():
    change = parse_unified_diff(SIMPLE_DIFF)["mod.py"]
    assert change.added_lines == ((2, "    return 2"), (3, "    # added"))
    assert change.authored_lines == frozenset({2, 3})
    assert change.removed_lines == ("    return 1",)
    assert not change.is_new


def test_context_lines_advance_the_counter_but_are_not_authored():
    # "tail" is context at post-patch line 5; claiming it would hand the agent credit
    # for a line it never wrote.
    assert 5 not in parse_unified_diff(SIMPLE_DIFF)["mod.py"].authored_lines


def test_new_and_binary_files_are_flagged():
    changes = parse_unified_diff(MULTI_DIFF)
    assert set(changes) == {"mod.py", "new.py", "logo.png"}
    assert changes["new.py"].is_new and changes["new.py"].authored_lines == frozenset({1, 2})
    assert changes["logo.png"].is_binary


def test_empty_and_garbage_diffs_yield_nothing():
    assert parse_unified_diff("") == {}
    assert parse_unified_diff("not a diff at all\njust prose") == {}


# --- commits -----------------------------------------------------------------------

RAW_LOG = """commit 20be5057550424e84d99aa3afaee7bf4d36bb05e
tree b8a4bbcc1331f138f8f7c655c83b34f8cfca8351
parent 86aa8d0d01e455ca1f36024613095010e82ebd7f
author Ada L <ada@example.com> 1786437990 +0800
committer Ada L <ada@example.com> 1786437990 +0800

    fix(core): return 2

    Body line one.
    Body line two.

    Co-authored-by: Someone <s@e.com>

 mod.py      | 2 +-
 test_mod.py | 2 ++
 2 files changed, 3 insertions(+), 1 deletion(-)
"""


def test_raw_log_recovers_message_body_and_trailers():
    (commit,) = parse_log(RAW_LOG, branch="fix/thing")
    assert commit.sha == "20be5057550424e84d99aa3afaee7bf4d36bb05e"
    assert commit.summary == "fix(core): return 2"
    assert commit.author_name == "Ada L" and commit.author_email == "ada@example.com"
    assert commit.body_lines == ("Body line one.", "Body line two.", "", "Co-authored-by: Someone <s@e.com>")
    assert commit.trailers == {"Co-authored-by": "Someone <s@e.com>"}
    assert commit.branch == "fix/thing"


def test_stat_block_is_not_swallowed_into_the_message():
    (commit,) = parse_log(RAW_LOG)
    assert not any("insertions" in line or "mod.py |" in line for line in commit.message_lines)


def test_multiple_commits_parse_independently():
    log = RAW_LOG + RAW_LOG.replace("20be5057", "aaaa1111").replace("return 2", "return 3")
    parsed = parse_log(log)
    assert [c.summary for c in parsed] == ["fix(core): return 2", "fix(core): return 3"]


def test_message_with_no_blank_separator_still_exposes_body_lines():
    # The malformed case C025 exists to catch: §3's `body` would be "" here, so a rule
    # reading only `body` would see nothing to judge and wrongly return not_applicable.
    log = RAW_LOG.replace("    fix(core): return 2\n\n    Body line one.", "    summary\n    body now")
    (commit,) = parse_log(log)
    assert commit.summary == "summary"
    assert commit.body_lines[0] == "body now"
    assert commit.message_lines[1] == "body now"


def test_shim_scrapes_dash_m_and_warns(caplog):
    cmds = (Command(index=0, command='git commit -m "fix: a thing"'),)
    with caplog.at_level("WARNING"):
        (commit,) = scrape_commits_from_commands(cmds)
    assert commit.summary == "fix: a thing"
    assert commit.sha == "" and commit.branch is None
    assert "TEMPORARY pre-Phase-0 fixture shim" in caplog.text


def test_shim_reports_commits_it_cannot_read(caplog):
    cmds = (Command(index=0, command="git commit -F msg.txt"),)
    with caplog.at_level("WARNING"):
        assert scrape_commits_from_commands(cmds) == ()
    assert "1 `git commit` invocation(s) without a -m message" in caplog.text


# --- trajectory --------------------------------------------------------------------


def test_sections_split_on_collect_markers():
    submission = "===PROBE===\na=1\n===LOG===\ncommit x\n===PATCH===\ndiff --git a/x b/x\n"
    sections = submission_sections({"info": {"submission": submission}})
    assert sections["PROBE"] == "a=1"
    assert sections["PATCH"] == "diff --git a/x b/x"


def test_pre_phase0_submission_is_treated_as_a_bare_patch():
    traj = {"info": {"submission": "diff --git a/x b/x\n"}}
    assert submission_sections(traj) == {}
    assert patch_text(traj) == "diff --git a/x b/x\n"


def test_probe_parsing_keeps_blank_values():
    assert parse_probe("a=1\nb=\n# comment\nc = 3 ") == {"a": "1", "b": "", "c": "3"}


@pytest.mark.parametrize("path", [TRAJ_RESOLVED, TRAJ_EMPTY_PATCH])
def test_pr_text_comes_from_the_agent_not_the_prompt(path):
    traj = json.loads(path.read_text())
    text = pr_text(traj)
    # The marker also occurs in the instruction template; taking that would score the
    # harness instead of the model.
    assert text and "run this exact command, unmodified" not in text


@pytest.mark.parametrize("path", [TRAJ_RESOLVED, TRAJ_EMPTY_PATCH])
def test_commands_are_paired_with_their_output(path):
    cmds = commands(json.loads(path.read_text()))
    assert cmds and all(c.index == i for i, c in enumerate(cmds))
    assert any(c.output for c in cmds), "no command captured any output"


# --- the run a trajectory belongs to ---------------------------------------------------


def test_run_dir_is_recovered_from_the_layout():
    """`runs/<repo>/<framework>/<model>/<instance>/<condition>/attemptN/` is the record.

    Every component is asserted, not just the ones that existed first. A layout change
    that dropped `framework` or `model` on the floor would otherwise pass here and show
    up as two cells silently merging in the aggregate.
    """
    from compliance.core.paths import RUNS_ROOT, RunDir

    run = RunDir.from_path(
        RUNS_ROOT / "sympy" / "mini-swe-agent" / "gemini-2.5-flash"
        / "sympy__sympy-11618" / "guided" / "attempt2" / "trajectory.json"
    )
    assert (run.repo, run.framework, run.model, run.instance_id, run.condition,
            run.attempt) == ("sympy", "mini-swe-agent", "gemini-2.5-flash",
                             "sympy__sympy-11618", "guided", 2)
    assert run.root == RUNS_ROOT
    assert run.trajectory.exists(), "the layout must point at a run that is really there"


def test_a_cell_is_distinct_from_a_retry():
    """Two models, same instance/condition/attempt, are two runs -- not one run twice.

    Before framework and model were in the path they shared a directory and were told
    apart only by the attempt counter, which is what `aggregate.per_run` keys on. The
    two would have merged into one row and the loss would have been invisible.
    """
    from compliance.core.paths import RunDir

    def cell(model: str) -> RunDir:
        return RunDir.for_instance("sympy__sympy-11618", "guided", 1,
                                   framework="mini-swe-agent", model=model)

    assert cell("gemini-2.5-flash").path != cell("qwen3-coder").path


def test_run_dir_from_a_path_outside_the_layout_is_none():
    """None rather than a fabricated answer, so a caller can fall back knowingly."""
    from pathlib import Path

    from compliance.core.paths import RunDir

    assert RunDir.from_path(Path("/tmp/somewhere/trajectory.json")) is None


def test_a_bundle_takes_its_identity_from_the_directory_when_the_run_does_not_say():
    """Regression: every trajectory is named `trajectory.json`, so a fallback that read
    the filename gave every probe-less run the instance id `trajectory`.

    Two pre-Phase-0 fixtures then shared one (instance, condition, attempt) key and
    collapsed into a single row in the aggregate -- `compliance report` counted 21 runs
    where 22 exist. A key that is not unique loses data silently (H1).
    """
    from compliance.bundle.builder import build_bundle
    from compliance.core.paths import discover

    unknown = [r for r in discover(repo="sympy") if r.condition == "unknown"]
    assert len(unknown) >= 2, "the fixtures this regression is about are gone"
    for run in unknown:
        bundle = build_bundle(run.trajectory)
        assert bundle.instance_id == run.instance_id
        assert bundle.instance_id != "trajectory"


def test_every_stored_run_scores_under_a_distinct_key():
    """The aggregate groups by the whole cell. If two runs share a key, one of them is
    silently absent from every reported number.

    `framework` and `model` are part of the key, not decoration. This test caught the
    collision for real: once a second and third model ran the same instance under the
    same condition, three runs shared (instance, condition, attempt) and differed only
    in their cell -- which is precisely what the cell dimension was added to prevent.
    """
    import collections

    from compliance.bundle.builder import build_bundle
    from compliance.core.paths import discover

    runs = discover(repo="sympy")
    keys = collections.Counter(
        (b.framework, b.model, b.instance_id, b.condition, b.attempt_n)
        for b in (build_bundle(r.trajectory) for r in runs)
    )
    collisions = {k: n for k, n in keys.items() if n > 1}
    assert collisions == {}, f"{collisions} -- runs collapsing into one another"
    assert len(keys) == len(runs)

    # And the old key really would have collided -- so the guard is load-bearing, not
    # a formality that happens to pass.
    without_cell = collections.Counter(k[2:] for k in keys)
    assert any(n > 1 for n in without_cell.values()), (
        "no two runs share (instance, condition, attempt), so this test is not currently "
        "proving the cell is needed -- it still guards, but the evidence is gone"
    )

"""Compliance judges what the agent COMMITTED; SWE-bench grades what it DID.

The fixture is real ``/opt/collect.sh`` output from a SWE-bench container, staged so
that ``sympy/geometry/point.py`` is in the state filename filtering cannot handle: a
committed fix plus an uncommitted debug line, in one file. Excluding the whole file
would lose the fix; including it would grade the debug line as part of the PR.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import TRAJ_EMPTY_PATCH, TRAJ_RESOLVED

from compliance.bundle.builder import build_bundle
from compliance.bundle.trajectory import committed_patch_text, load, parse_status

FIXTURE = Path(__file__).parent / "fixtures" / "phase0_split_patch.traj.json"
POINT = "sympy/geometry/point.py"


@pytest.fixture(scope="module")
def split():
    return build_bundle(FIXTURE)


def test_scope_is_the_committed_patch(split):
    assert split.patch_scope == "committed"


def test_uncommitted_file_is_excluded_from_the_contribution(split):
    assert "reproduce.py" not in split.files
    assert "reproduce.py" in split.files_worktree
    assert split.uncommitted_paths() == ("reproduce.py",)


def test_uncommitted_lines_are_excluded_from_a_committed_file(split):
    """The case that makes filename filtering unworkable."""
    judged = [text for _, text in split.files[POINT].added_lines]
    worktree = [text for _, text in split.files_worktree[POINT].added_lines]
    assert judged == ["        # real fix, committed"]
    assert "        # DEBUG LEFTOVER never committed" in worktree
    assert len(worktree) == len(judged) + 1


def test_the_functional_patch_still_carries_everything(split):
    """SWE-bench must keep seeing the full working tree, or a forgotten commit would
    be scored as a failed fix."""
    assert set(split.files_worktree) == {"reproduce.py", POINT}


def test_status_is_captured_as_descriptive_evidence(split):
    codes = dict((path, code) for code, path in split.status_entries)
    assert codes["reproduce.py"] == "??"
    assert codes[POINT] == " M"  # committed, then modified again


def test_builder_notes_the_exclusion(split):
    assert any("left uncommitted and excluded" in note for note in split.notes)


@pytest.mark.parametrize("traj", [TRAJ_RESOLVED, TRAJ_EMPTY_PATCH])
def test_pre_phase0_trajectories_fall_back_honestly(traj):
    """No ===PATCH_COMMITTED=== means the two cannot be told apart. Say so rather than
    silently judging the wrong scope."""
    assert committed_patch_text(load(traj)) is None
    bundle = build_bundle(traj)
    assert bundle.patch_scope == "worktree_fallback"
    assert bundle.files == bundle.files_worktree


def test_absent_section_is_not_the_same_as_an_empty_one():
    """None means 'unknowable'; '' means 'the agent committed nothing'."""
    assert committed_patch_text({"info": {"submission": "diff --git a/x b/x\n"}}) is None
    empty = {"info": {"submission": "===PATCH_COMMITTED===\n===PATCH===\ndiff --git a/x b/x\n"}}
    assert committed_patch_text(empty) == ""


def test_status_parsing_handles_renames_and_codes():
    entries = parse_status("?? new.py\n M mod.py\nA  added.py\nR  old.py -> new_name.py")
    assert entries == (
        ("??", "new.py"),
        (" M", "mod.py"),
        ("A ", "added.py"),
        ("R ", "new_name.py"),
    )


def test_patch_marker_does_not_collide_with_the_committed_marker():
    """evaluate.sh splits on '===PATCH==='. That must not match '===PATCH_COMMITTED==='
    or functional grading would silently read the wrong bytes."""
    assert "===PATCH===" not in "===PATCH_COMMITTED==="
    submission = load(FIXTURE)["info"]["submission"]
    tail = submission.split("===PATCH===", 1)[1]
    assert "PATCH_COMMITTED" not in tail
    assert tail.lstrip().startswith("diff --git")

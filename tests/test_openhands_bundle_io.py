"""Storing an OpenHands run in the layout the rest of the project reads.

The `===SECTION===` delimiters and the completion marker are ours, not any framework's,
so this is tested here rather than against a live agent -- and the module under test
imports no agent SDK for exactly that reason.

The contract that matters is the ORDER of writes. `patch.diff` is what every resume in
this project keys on, and the other harness learned the hard way that a trajectory can
exist without a finished run: a cell killed during collection left one behind and was
skipped forever afterwards as "done", carrying no patch, no bundle and no eval report.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "frameworks/openhands"))
import bundle_io  # noqa: E402

BUNDLE = """\
===PROBE===
condition=guided
rules_file_chars=17561
===BRANCH===
head=abc123
===STATUS===
 M django/db/models/query.py
===PATCH_COMMITTED===
diff --git a/django/db/models/query.py b/django/db/models/query.py
+committed change
===PATCH===
diff --git a/django/db/models/query.py b/django/db/models/query.py
+committed change
+uncommitted scratch
"""


def result(bundle: str = BUNDLE) -> dict:
    return {"instance_id": "django__django-11099", "attempt": 1,
            "history": [], "test_result": {"bundle": bundle}}


def test_each_section_lands_in_its_own_file(tmp_path):
    bundle_io.write_run_dir(result(), tmp_path)
    assert "condition=guided" in (tmp_path / "probe.txt").read_text()
    assert "+committed change" in (tmp_path / "patch_committed.diff").read_text()
    assert (tmp_path / "bundle.txt").read_text() == BUNDLE
    assert json.loads((tmp_path / "trajectory.json").read_text())["attempt"] == 1


def test_the_two_patches_differ_and_both_are_kept(tmp_path):
    """Compliance scores what the agent CHOSE to commit; SWE-bench grades everything.

    One run, two questions, and the container is destroyed straight after -- so neither
    can be recomputed later.
    """
    bundle_io.write_run_dir(result(), tmp_path)
    committed = (tmp_path / "patch_committed.diff").read_text()
    everything = (tmp_path / "patch.diff").read_text()
    assert "uncommitted scratch" not in committed
    assert "uncommitted scratch" in everything


def test_everything_after_the_patch_marker_is_patch_bytes():
    """`===PATCH===` is last by contract, so a diff containing the string `===STATUS===`
    cannot truncate it."""
    awkward = BUNDLE + "===STATUS=== is mentioned inside this diff\n"
    assert "is mentioned inside this diff" in bundle_io.patch_from_bundle(awkward)


def test_no_patch_is_written_when_the_bundle_has_none(tmp_path):
    """A run with no patch must stay retryable, not be recorded as complete."""
    no_patch = "===PROBE===\ncondition=naive\n===PATCH===\n"
    bundle_io.write_run_dir(result(no_patch), tmp_path)
    assert (tmp_path / "trajectory.json").exists()
    assert not (tmp_path / "patch.diff").exists(), (
        "an empty patch.diff would mark this run done forever and it would never be retried"
    )


def test_a_run_with_no_bundle_at_all_still_stores_its_trajectory(tmp_path):
    """The agent never ran collect.sh. That is evidence -- and a run to retry."""
    bundle_io.write_run_dir(result(""), tmp_path)
    assert (tmp_path / "trajectory.json").exists()
    assert not (tmp_path / "patch.diff").exists()


def test_patch_diff_is_written_after_the_trajectory(tmp_path, monkeypatch):
    """The completion marker must be last, so an interrupted write is never mistaken
    for a finished run."""
    written: list[str] = []
    real = Path.write_text

    def spy(self, *args, **kwargs):
        written.append(self.name)
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", spy)
    bundle_io.write_run_dir(result(), tmp_path)
    assert written[-1] == "patch.diff", written
    assert written.index("trajectory.json") < written.index("patch.diff")


@pytest.mark.parametrize("name,expected", [
    ("PROBE", "condition=guided"), ("STATUS", "django/db/models/query.py"),
    ("BRANCH", "head=abc123"),
])
def test_sections_are_recovered_by_name(name, expected):
    assert expected in bundle_io.section(BUNDLE, name)


def test_a_missing_section_is_none_not_empty():
    """None distinguishes "collect never emitted it" from "it was empty", which is the
    difference between a harness bug and a fact about the run."""
    assert bundle_io.section(BUNDLE, "LOG") is None

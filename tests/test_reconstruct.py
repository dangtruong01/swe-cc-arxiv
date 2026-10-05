"""Reconstruction: base_commit + patch -> the file the agent left behind.

apply_hunks is pure, so it is tested without a repository. The guards matter more than
the happy path: a silently wrong reconstruction feeds a corrupt AST to every rule
downstream and looks like a finding rather than a crash.
"""

from __future__ import annotations

import ast

import pytest

from compliance.bundle.diff import parse_unified_diff
from compliance.bundle.reconstruct import ReconstructionError, apply_hunks

BASE = "def f():\n    return 1\n\ndef g():\n    return 2\n"

PATCH = """diff --git a/m.py b/m.py
--- a/m.py
+++ b/m.py
@@ -1,2 +1,3 @@
 def f():
-    return 1
+    return 2
+    # added
"""


def hunks_of(patch, path="m.py"):
    return parse_unified_diff(patch)[path].hunks


def test_applies_a_hunk_and_keeps_the_rest_of_the_file():
    head = apply_hunks(BASE, hunks_of(PATCH))
    assert head == "def f():\n    return 2\n    # added\n\ndef g():\n    return 2\n"
    assert ast.parse(head)


def test_a_new_file_reconstructs_from_nothing():
    patch = """diff --git a/n.py b/n.py
new file mode 100644
--- /dev/null
+++ b/n.py
@@ -0,0 +1,2 @@
+import os
+print(os)
"""
    assert apply_hunks(None, hunks_of(patch, "n.py")) == "import os\nprint(os)\n"


def test_a_removed_line_that_does_not_match_the_base_raises():
    """Means the cache and the run disagree about the base commit."""
    patch = PATCH.replace("-    return 1", "-    return 999")
    with pytest.raises(ReconstructionError, match="removed line does not match"):
        apply_hunks(BASE, hunks_of(patch))


def test_a_context_line_that_does_not_match_the_base_raises():
    """The guard that was missing: without it a wrong offset corrupts silently."""
    patch = PATCH.replace(" def f():", " def WRONG():")
    with pytest.raises(ReconstructionError, match="context does not match"):
        apply_hunks(BASE, hunks_of(patch))


def test_multiple_hunks_apply_in_order():
    patch = """diff --git a/m.py b/m.py
--- a/m.py
+++ b/m.py
@@ -1,2 +1,2 @@
 def f():
-    return 1
+    return 11
@@ -4,2 +4,2 @@
 def g():
-    return 2
+    return 22
"""
    head = apply_hunks(BASE, hunks_of(patch))
    assert "return 11" in head and "return 22" in head
    assert ast.parse(head)


def test_no_hunks_leaves_the_file_untouched():
    from compliance.core.models import FileChange
    from compliance.bundle.reconstruct import reconstruct_file
    from pathlib import Path

    change = FileChange(path="m.py", authored_lines=frozenset(), hunks=())
    base, head = reconstruct_file(change, Path("/nonexistent"), "deadbeef")
    assert base == head


def test_agent_written_syntax_errors_survive_reconstruction():
    """Three pilot runs produced invalid Python (`ssert` for `assert`). Reconstruction
    must reproduce that faithfully -- it is the agent's output, not our corruption, and
    the AST layer reports it as parse_error rather than a rule violation."""
    patch = """diff --git a/m.py b/m.py
--- a/m.py
+++ b/m.py
@@ -1,2 +1,3 @@
 def f():
-    return 1
+    return 1
+ssert broken syntax here
"""
    head = apply_hunks(BASE, hunks_of(patch))
    assert "ssert broken syntax here" in head
    with pytest.raises(SyntaxError):
        ast.parse(head)

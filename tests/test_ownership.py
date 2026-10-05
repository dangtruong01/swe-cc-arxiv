"""Ownership: which lines the agent's edit reaches, and which rules may judge them.

Invariant 5 says targets come only from agent-authored content. The subtlety these tests
pin is what "authored" means when the agent's edit *removed* code.

A patch that only deletes has no `+` lines, so `authored_lines` is empty. Before this was
fixed, such a file was skipped before it was even parsed, and every AST rule reported
`not_applicable` with status `ok` -- indistinguishable from the rule genuinely not
applying. One pilot agent fixed its bug by deleting a six-line validation block and adding
nothing, and was invisible to the whole checker.
"""

from __future__ import annotations

import textwrap

from conftest import make_bundle

from compliance.bundle.diff import deletion_anchors, parse_unified_diff
from compliance.core.models import Hunk
from compliance.core.ownership import owned_files, owns_file, owns_span

DELETION_ONLY = textwrap.dedent("""\
    diff --git a/pkg/mod.py b/pkg/mod.py
    --- a/pkg/mod.py
    +++ b/pkg/mod.py
    @@ -10,9 +10,3 @@ def build(args):
         temp = flatten(args)
         temp = set(temp)
         if ok(temp):
    -        if is_cycle:
    -            raise ValueError('repeated elements; use Cycle')
    -        else:
    -            raise ValueError('repeated elements.')
    -    # nothing else to check
    -
         return temp
     
     def other():
    """)


def change_from(diff: str, path: str = "pkg/mod.py"):
    return parse_unified_diff(diff)[path]


# --- the anchor -----------------------------------------------------------------------


def test_a_deletion_only_patch_has_no_authored_lines_but_is_still_an_edit():
    change = change_from(DELETION_ONLY)
    assert change.authored_lines == frozenset()
    assert change.deletion_anchors
    assert change.modified_lines == change.deletion_anchors


def test_consecutive_removals_share_one_anchor():
    """One removal site is one edit. Six deleted lines should not read as six sites."""
    assert len(change_from(DELETION_ONLY).deletion_anchors) == 1


def test_the_anchor_is_the_post_patch_line_that_takes_the_deletion_s_place():
    """Three lines of context precede the removal, so the anchor sits just past them --
    inside the definition the code was removed from, which is what ownership needs."""
    change = change_from(DELETION_ONLY)
    assert change.deletion_anchors == {13}


def test_a_removal_at_the_very_top_clamps_onto_a_real_line():
    hunk = Hunk(old_start=1, old_count=2, new_start=0, new_count=1,
                lines=("-gone\n", " kept\n"))
    assert deletion_anchors(hunk) == {1}


def test_additions_advance_the_counter_and_removals_do_not():
    hunk = Hunk(old_start=1, old_count=3, new_start=1, new_count=3,
                lines=(" a\n", "+new\n", "-old\n", " b\n"))
    # ' a' -> 1, '+new' -> 2, '-old' anchors at 3, ' b' -> 3
    assert deletion_anchors(hunk) == {3}


# --- what ownership does with it -----------------------------------------------------


def test_a_deletion_only_file_is_touched(): 
    bundle = make_bundle(files=[change_from(DELETION_ONLY)])
    assert owns_file(bundle, "pkg/mod.py", "touched") is True
    assert [c.path for c in owned_files(bundle, "touched")] == ["pkg/mod.py"]


def test_a_deletion_only_file_is_enclosing_owned():
    """The consistency rules -- change a function, you answer for its doctest -- have to
    fire on a deletion. Removing a branch changes behaviour just as adding one does."""
    bundle = make_bundle(files=[change_from(DELETION_ONLY)])
    assert owns_file(bundle, "pkg/mod.py", "enclosing") is True


def test_a_span_containing_the_anchor_is_touched():
    bundle = make_bundle(files=[change_from(DELETION_ONLY)])
    assert owns_span(bundle, "pkg/mod.py", (10, 20), "touched") is True
    assert owns_span(bundle, "pkg/mod.py", (40, 50), "touched") is False


def test_created_ownership_ignores_deletions_entirely():
    """A deletion never brings anything into existence, so the existence rules must not
    fire on one. Otherwise removing a function would demand the function have a docstring.
    """
    bundle = make_bundle(files=[change_from(DELETION_ONLY)])
    assert owns_span(bundle, "pkg/mod.py", (13, 13), "created") is False
    assert owns_file(bundle, "pkg/mod.py", "created") is False


def test_a_pure_addition_is_unaffected():
    """The change must not alter what was already correct."""
    diff = textwrap.dedent("""\
        diff --git a/pkg/mod.py b/pkg/mod.py
        --- a/pkg/mod.py
        +++ b/pkg/mod.py
        @@ -5,2 +5,3 @@ def build(args):
             a = 1
        +    b = 2
             return a
        """)
    change = change_from(diff)
    assert change.deletion_anchors == frozenset()
    assert change.modified_lines == change.authored_lines == frozenset({6})


def test_a_replacement_counts_both_the_new_text_and_the_removal_site():
    diff = textwrap.dedent("""\
        diff --git a/pkg/mod.py b/pkg/mod.py
        --- a/pkg/mod.py
        +++ b/pkg/mod.py
        @@ -5,3 +5,3 @@ def build(args):
             a = 1
        -    b = 2
        +    b = 3
             return a
        """)
    change = change_from(diff)
    assert change.authored_lines == frozenset({6})
    assert change.modified_lines == frozenset({6})


# --- the regression that motivated it -------------------------------------------------


def test_the_deleting_agent_is_no_longer_invisible_to_the_ast_rules():
    """End to end: a deletion-only patch must produce targets, not silence.

    `sympy__sympy-12481` naive removed a six-line validation block from
    `Permutation.__new__` and added nothing. Every AST rule reported not_applicable/ok.
    """
    import compliance.rules.sympy.tests as rules_module
    from compliance.core.registry import registered
    from compliance.core.runner import run_rule

    source = "\n".join(
        ['def build(args):', '    """Doc.', '', '    >>> build([1])', '    [1]', '    """']
        + [f"    x{i} = {i}" for i in range(1, 20)]
        + ["    return args", "", "def other():", "    pass"]
    )
    change = change_from(DELETION_ONLY)
    owned = type(change)(
        path=change.path, authored_lines=change.authored_lines,
        added_lines=change.added_lines, removed_lines=change.removed_lines,
        head_text=source, hunks=change.hunks,
        deletion_anchors=change.deletion_anchors,
    )
    bundle = make_bundle(files=[owned])
    rules = {r.id: r for r in registered()}
    # C115 grades doctests of definitions the agent edited (`enclosing` ownership).
    row = run_rule(bundle, rules["SYMPY-C115"], {})
    assert row.n_targets > 0, "the deletion-only edit produced no targets"
    assert row.status == "tool_missing", row.notes
    assert rules_module.CATEGORY

"""Unit tests for the shared import extractor.

The point of most of these is the line number. A rule built on this says "line 12 is in
the wrong group", so an off-by-one here becomes an accusation against the wrong line --
and nothing downstream would notice, because the verdict would still look plausible.

The snippets are deliberately awkward: files with nothing in them, files with nothing but
imports, imports hidden in `try` blocks and function bodies, relative imports at three
depths. Those are where an extractor that only ever saw tidy input goes wrong.
"""

from __future__ import annotations

import textwrap

from compliance.extractors import imports as im
from compliance.extractors.python_ast import parse_module

PACKAGE = im.GroupPolicy(first_party=["acme"])


def src(text: str) -> str:
    return textwrap.dedent(text)


# --- classification -----------------------------------------------------------------


def test_each_group_is_recognised_from_the_caller_s_configuration():
    assert PACKAGE.group_of("__future__") == im.FUTURE
    assert PACKAGE.group_of("os.path") == im.STDLIB
    assert PACKAGE.group_of("yaml") == im.THIRD_PARTY
    assert PACKAGE.group_of("acme.widgets") == im.FIRST_PARTY
    assert PACKAGE.group_of("", level=1) == im.LOCAL
    assert PACKAGE.group_of("sibling", level=2) == im.LOCAL


def test_first_party_wins_over_the_interpreter_s_stdlib_list():
    """A project may ship a package whose name shadows a stdlib module; what the project
    declares about its own layout beats what this interpreter happens to be built with."""
    assert im.GroupPolicy(first_party=["json"]).group_of("json") == im.FIRST_PARTY
    assert im.GroupPolicy().group_of("json") == im.STDLIB


def test_the_policy_takes_any_iterable_and_the_order_is_configurable():
    policy = im.GroupPolicy(first_party=["acme"], order=(im.FIRST_PARTY, im.STDLIB))
    assert policy.first_party == frozenset({"acme"})
    assert policy.rank(im.FIRST_PARTY) < policy.rank(im.STDLIB)
    assert im.DEFAULT_POLICY.rank(im.STDLIB) < im.DEFAULT_POLICY.rank(im.FIRST_PARTY)


# --- degenerate input ---------------------------------------------------------------


def test_an_empty_file_yields_nothing_and_raises_nothing():
    assert im.import_lines("") == ()
    assert im.unused_names("") == ()
    report = im.blank_line_report("")
    assert report is not None and report.last_import_lineno is None


def test_source_that_does_not_parse_is_empty_rather_than_an_exception():
    broken = "import os\ndef f(:\n"
    assert im.import_lines(broken) == ()
    assert im.blank_line_report(broken) is None
    assert im.unused_names(broken) == ()
    assert im.import_lines(None) == ()
    assert im.blank_line_report(None) is None


def test_a_file_that_is_nothing_but_imports_is_all_leading_block():
    text = src(
        """\
        import os
        import sys
        """
    )
    lines = im.import_lines(text)
    assert [line.lineno for line in im.leading_block(lines)] == [1, 2]
    report = im.blank_line_report(text)
    assert report.last_import_lineno == 2
    assert report.next_statement_lineno is None
    assert report.first_definition_lineno is None


# --- one statement, described -------------------------------------------------------


def test_a_plain_import_and_a_from_import_are_told_apart():
    lines = im.import_lines(src(
        """\
        import os
        from os import path
        """
    ))
    assert lines[0].is_plain and not lines[0].is_from
    assert lines[0].bindings == ("os",)
    assert lines[1].is_from and lines[1].module == "os"
    assert lines[1].names == ("path",) and lines[1].bindings == ("path",)


def test_a_dotted_import_binds_only_its_root_and_keeps_the_full_path():
    line = im.import_lines("import os.path\n")[0]
    assert line.modules == ("os.path",)
    assert line.bindings == ("os",)
    assert line.sites and line.sites[0].origin == "os.path"


def test_one_statement_importing_two_modules_reports_the_group_of_each():
    line = im.import_lines("import os, yaml\n")[0]
    assert line.modules == ("os", "yaml")
    assert line.groups == (im.STDLIB, im.THIRD_PARTY)
    assert line.group == im.STDLIB


def test_relative_imports_report_their_dot_depth_and_absolute_ones_report_none():
    lines = im.import_lines(src(
        """\
        from . import sibling
        from .. import cousin
        from ...pkg.deep import thing
        """
    ))
    assert [line.dot_depth for line in lines] == [1, 2, 3]
    assert all(line.is_relative and not line.is_absolute for line in lines)
    assert [line.module for line in lines] == ["", "", "pkg.deep"]
    assert all(line.group == im.LOCAL for line in lines)

    absolute = im.import_lines("from acme.widgets import Spinner\n", PACKAGE)[0]
    assert absolute.is_absolute and absolute.dot_depth == 0
    assert absolute.group == im.FIRST_PARTY


# --- where an import sits -----------------------------------------------------------


def test_an_import_guarded_by_a_try_block_is_not_top_level():
    text = src(
        """\
        import os

        try:
            import fastjson as json
        except ImportError:
            import json
        """
    )
    lines = im.import_lines(text)
    assert lines[0].is_top_level and lines[0].in_leading_block
    assert [line.context for line in lines[1:]] == ["try", "try"]
    assert all(not line.is_top_level for line in lines[1:])
    assert lines[1].context_lineno == 3


def test_an_import_inside_a_function_is_tagged_with_the_function():
    text = src(
        """\
        import os


        def load():
            import csv
            return csv, os
        """
    )
    lines = im.import_lines(text)
    assert lines[1].context == "function" and lines[1].context_lineno == 4
    assert im.top_level(lines) == (lines[0],)


def test_an_import_under_a_type_checking_guard_is_conditional():
    text = src(
        """\
        from typing import TYPE_CHECKING

        if TYPE_CHECKING:
            from acme.widgets import Spinner
        """
    )
    lines = im.import_lines(text, PACKAGE)
    assert lines[1].context == "conditional"
    assert lines[1].in_leading_block is False


def test_the_leading_block_stops_at_the_first_non_import_statement():
    text = src(
        '''\
        """Docstring, which does not end the block."""
        import os

        VERSION = "1"

        import sys
        '''
    )
    lines = im.import_lines(text)
    assert [line.lineno for line in im.leading_block(lines)] == [2]
    assert lines[1].lineno == 6 and lines[1].in_leading_block is False


# --- group order --------------------------------------------------------------------


def test_groups_in_the_declared_order_produce_no_problems():
    text = src(
        """\
        from __future__ import annotations

        import os

        import yaml

        from acme.widgets import Spinner

        from . import sibling
        """
    )
    lines = im.import_lines(text, PACKAGE)
    assert [run.group for run in im.group_runs(lines)] == list(im.DEFAULT_GROUP_ORDER)
    assert im.group_order_problems(lines) == []


def test_a_group_that_arrives_too_late_is_reported_at_its_first_line():
    text = src(
        """\
        import yaml
        import os
        """
    )
    problems = im.group_order_problems(im.import_lines(text, PACKAGE))
    assert [(p.kind, p.lineno, p.other_lineno) for p in problems] == [
        (im.GROUP_OUT_OF_ORDER, 2, 1)
    ]


def test_a_group_split_in_two_is_a_different_fault_from_a_mis_ordering():
    text = src(
        """\
        import os
        import yaml
        import sys
        """
    )
    problems = im.group_order_problems(im.import_lines(text, PACKAGE))
    kinds = {p.kind for p in problems}
    assert im.GROUP_SPLIT in kinds
    split = next(p for p in problems if p.kind == im.GROUP_SPLIT)
    assert (split.lineno, split.other_lineno) == (3, 1)


def test_the_caller_s_own_group_order_is_what_gets_judged():
    text = src(
        """\
        from acme.widgets import Spinner
        import os
        """
    )
    lines = im.import_lines(text, PACKAGE)
    assert im.group_order_problems(lines)
    reversed_order = (im.FUTURE, im.FIRST_PARTY, im.STDLIB, im.THIRD_PARTY, im.LOCAL)
    assert im.group_order_problems(lines, PACKAGE, order=reversed_order) == []


# --- statement order within a group -------------------------------------------------


def test_a_plain_import_after_a_from_import_in_the_same_group_is_reported():
    text = src(
        """\
        from os import path
        import sys
        """
    )
    problems = im.statement_order_problems(im.import_lines(text))
    assert [(p.kind, p.lineno, p.other_lineno) for p in problems] == [
        (im.IMPORT_AFTER_FROM, 2, 1)
    ]


def test_plain_imports_first_within_each_group_is_clean():
    text = src(
        """\
        import os
        import sys
        from os import path
        import yaml
        from yaml import safe_load
        """
    )
    assert im.statement_order_problems(im.import_lines(text, PACKAGE)) == []


# --- names on one line --------------------------------------------------------------


def test_uppercase_names_sort_before_lowercase_ones():
    names = ["zeta", "Alpha", "BETA", "gamma"]
    assert sorted(names, key=im.name_sort_key) == ["Alpha", "BETA", "gamma", "zeta"]
    assert im.names_are_sorted(["Alpha", "BETA", "gamma", "zeta"])
    assert not im.names_are_sorted(["gamma", "Alpha"])


def test_an_unsorted_from_import_line_is_reported_with_the_order_it_wanted():
    text = "from acme.widgets import spin, Spinner, cog\n"
    problems = im.name_order_problems(im.import_lines(text, PACKAGE))
    assert len(problems) == 1
    assert problems[0].kind == im.NAMES_UNSORTED and problems[0].lineno == 1
    assert problems[0].detail == "expected: Spinner, cog, spin"


def test_lines_with_nothing_to_order_are_left_alone():
    """A star import binds an unknown set of names; there is no order to judge."""
    text = src(
        """\
        import zlib
        import abc
        from os.path import *
        from acme.widgets import Spinner
        """
    )
    lines = im.import_lines(text, PACKAGE)
    assert lines[2].has_star and lines[2].names == ("*",)
    assert im.name_order_problems(lines) == []


# --- how a wrapped import is written ------------------------------------------------


def test_a_correctly_wrapped_import_has_parentheses_indent_and_a_trailing_comma():
    text = src(
        """\
        from acme.widgets import (
            Spinner,
            cog,
        )
        """
    )
    line = im.import_lines(text, PACKAGE)[0]
    wrap = line.wrapping
    assert wrap.is_wrapped and wrap.uses_parentheses and wrap.trailing_comma
    assert wrap.continuation_indents == ((2, 4), (3, 4))
    assert wrap.closing_indent == 0 and wrap.indented_by(4)
    assert im.wrapping_problems([line]) == []


def test_a_missing_trailing_comma_is_reported_at_the_opening_line():
    text = src(
        """\
        from acme.widgets import (
            Spinner,
            cog
        )
        """
    )
    problems = im.wrapping_problems(im.import_lines(text, PACKAGE))
    assert [(p.kind, p.lineno) for p in problems] == [(im.NO_TRAILING_COMMA, 1)]


def test_a_mis_indented_continuation_is_reported_on_its_own_line():
    text = src(
        """\
        from acme.widgets import (
                Spinner,
            cog,
        )
        """
    )
    problems = im.wrapping_problems(im.import_lines(text, PACKAGE))
    assert [(p.kind, p.lineno, p.other_lineno) for p in problems] == [
        (im.CONTINUATION_INDENT, 2, 1)
    ]
    assert "expected 4" in problems[0].detail


def test_a_backslash_continuation_is_reported_as_well_as_the_missing_parentheses():
    text = "from acme.widgets import Spinner, \\\n    cog\n"
    problems = im.wrapping_problems(im.import_lines(text, PACKAGE))
    assert [p.kind for p in problems] == [im.BACKSLASH_CONTINUATION, im.NO_PARENTHESES]
    assert all(p.lineno == 1 for p in problems)


def test_a_single_line_import_is_not_judged_as_a_wrapped_one():
    lines = im.import_lines("from acme.widgets import (Spinner, cog)\n", PACKAGE)
    assert lines[0].wrapping.is_wrapped is False
    assert im.wrapping_problems(lines) == []


def test_continuation_indent_is_measured_from_the_statement_not_the_margin():
    """An import nested in a `try` starts indented, so a fixed column would misjudge it."""
    text = src(
        """\
        try:
            from acme.widgets import (
                Spinner,
            )
        except ImportError:
            Spinner = None
        """
    )
    wrap = im.import_lines(text, PACKAGE)[0].wrapping
    assert wrap.base_indent == 4 and wrap.continuation_indents == ((3, 8),)
    assert wrap.indented_by(4)


# --- blank lines --------------------------------------------------------------------


def test_blank_lines_after_the_import_block_and_before_the_first_definition():
    text = src(
        """\
        import os

        VERSION = "1"


        def load():
            return os
        """
    )
    report = im.blank_line_report(text)
    assert (report.last_import_lineno, report.blank_after_imports) == (1, 1)
    assert report.next_statement_lineno == 3
    assert report.first_definition_lineno == 6
    assert report.first_definition_kind == "def"
    assert report.blank_before_first_definition == 2


def test_the_blank_run_before_a_decorated_class_is_measured_above_its_decorator():
    text = src(
        """\
        import os


        @os.wraps
        class Widget:
            pass
        """
    )
    report = im.blank_line_report(text)
    assert report.first_definition_lineno == 4
    assert report.first_definition_kind == "class"
    assert report.blank_before_first_definition == 2


def test_a_docstring_does_not_count_as_the_statement_after_the_imports():
    text = src(
        '''\
        """Title."""
        import os
        import sys


        def load():
            return os, sys
        '''
    )
    report = im.blank_line_report(text)
    assert report.last_import_lineno == 3
    assert report.blank_after_imports == 2
    assert report.next_statement_lineno == 6


# --- names nothing uses -------------------------------------------------------------


def test_an_unused_import_is_reported_and_a_used_one_is_not():
    text = src(
        """\
        import os
        import sys
        from acme.widgets import Spinner, cog


        def load():
            return os.path.join(cog, Spinner())
        """
    )
    unused = im.unused_names(text, PACKAGE)
    assert [(u.name, u.lineno) for u in unused] == [("sys", 2)]
    assert unused[0].group == im.STDLIB and unused[0].origin == "sys"
    assert im.unused_names(text, PACKAGE, ignore=["sys"]) == ()


def test_future_star_re_export_and_dunder_all_are_never_reported_as_unused():
    text = src(
        """\
        from __future__ import annotations
        from os.path import *
        from acme.widgets import Spinner as Spinner
        from acme.widgets import cog

        __all__ = ["cog"]
        """
    )
    assert im.unused_names(text, PACKAGE) == ()


def test_a_name_used_only_in_a_quoted_annotation_still_counts_as_used():
    text = src(
        """\
        from acme.widgets import Spinner


        def load(thing: "Spinner") -> None:
            return None
        """
    )
    assert im.unused_names(text, PACKAGE) == ()


def test_an_unused_import_carries_its_suppression_comment_for_the_rule_to_judge():
    text = src(
        """\
        from acme.widgets import Spinner  # noqa: F401
        import sys
        """
    )
    unused = {u.name: u for u in im.unused_names(text, PACKAGE)}
    assert unused["Spinner"].noqa.lower().startswith("# noqa")
    assert unused["sys"].noqa == ""


def test_a_suppression_comment_is_found_with_or_without_codes_and_in_either_case():
    text = src(
        """\
        import os  # NOQA
        from acme.widgets import (
            Spinner,
        )  # noqa:F401,E501
        import sys
        """
    )
    lines = im.import_lines(text, PACKAGE)
    assert lines[0].has_noqa and lines[0].noqa_codes == ()
    assert lines[1].has_noqa and lines[1].noqa_codes == ("F401", "E501")
    assert lines[1].noqa_lineno == 4
    assert not lines[2].has_noqa


# --- reuse of an already-parsed module ----------------------------------------------


def test_an_already_parsed_module_can_be_passed_in_instead_of_the_text():
    text = "import os\nfrom acme.widgets import Spinner\n"
    parsed = parse_module(text, "acme/thing.py")
    assert [line.lineno for line in im.import_lines(module=parsed, policy=PACKAGE)] == [1, 2]
    assert im.blank_line_report(module=parsed).last_import_lineno == 2

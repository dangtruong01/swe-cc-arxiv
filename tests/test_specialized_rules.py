"""Three cases per rule (docs/checker-authoring.md §9): a target that satisfies, one that
violates, and an input where the pre-condition finds nothing.

The third case carries most of the weight in this category. Twenty-four of the
twenty-seven rules fire on *"the contribution introduces a deprecation"* and grade one of
the things a deprecation obliges you to do. Written the other way round -- triggering on
the version keyword, on the docstring note, on the release-notes entry -- an agent that
deprecates something and documents none of it would collect `not_applicable` across the
whole category (§4.2). Each `not_applicable` test below asserts that the trigger is the
deprecation and not the artefact.
"""

from __future__ import annotations

import textwrap

from conftest import make_bundle

from compliance.core.models import Command, FileChange
from compliance.core.registry import registered
from compliance.core.runner import run_rule

import compliance.rules.sympy.specialized  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
CODE = "sympy/core/thing.py"
TEST = "sympy/core/tests/test_thing.py"
ACTIVE = "doc/src/explanation/active-deprecations.md"


def pyfile(path: str, source: str, *, base: str | None = None, is_new=False) -> FileChange:
    source = textwrap.dedent(source)
    lines = source.split("\n")
    return FileChange(
        path=path,
        authored_lines=frozenset(range(1, len(lines) + 1)),
        added_lines=tuple((n, lines[n - 1]) for n in range(1, len(lines))),
        head_text=source, base_text=base, is_new=is_new,
    )


def textfile(path: str, body: str) -> FileChange:
    body = textwrap.dedent(body)
    lines = body.split("\n")
    return FileChange(
        path=path,
        authored_lines=frozenset(range(1, len(lines) + 1)),
        added_lines=tuple((n, lines[n - 1]) for n in range(1, len(lines))),
        head_text=body,
    )


def bundle(*files: FileChange, commands=(), **kw):
    return make_bundle(
        files={f.path: f for f in files},
        commands=tuple(Command(index=i, command=c[0], output=c[1] if len(c) > 1 else "")
                       for i, c in enumerate(commands)),
        **kw,
    )


def verdict(rule_id, b, corpus):
    return run_rule(b, RULES[rule_id], corpus)


def assert_withheld(rule_id, b, corpus):
    row = verdict(rule_id, b, corpus)
    assert row.n_targets > 0, "pre-condition did not fire"
    assert (row.verdict, row.status) == ("not_applicable", "tool_missing"), row.notes


def assert_no_targets(rule_id, b, corpus):
    row = verdict(rule_id, b, corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0), row.notes


# A deprecation with everything the category demands, used as the satisfying fixture.
GOOD_DEPRECATION = '''
    from sympy.utilities.exceptions import sympy_deprecation_warning

    def old_thing(x):
        """Do the old thing.

        .. deprecated:: 1.12

            old_thing is deprecated. Use new_thing instead.
        """
        sympy_deprecation_warning(
            "old_thing is deprecated. Use new_thing instead.",
            deprecated_since_version="1.12",
            active_deprecations_target="old-thing-deprecation",
            stacklevel=3,
        )
        return x
'''

GOOD_ACTIVE_SECTION = """
    (old-thing-deprecation)=
    ### old_thing

    old_thing is deprecated. Use new_thing instead, because the old name was
    inconsistent with the rest of the core module.
"""

GOOD_TEST = '''
    from sympy.testing.pytest import warns_deprecated_sympy
    from sympy.core.thing import old_thing

    def test_old_thing_deprecated():
        with warns_deprecated_sympy():
            assert old_thing(1) == 1
'''

NO_DEPRECATION = '''
    def plain(x):
        """Do a thing."""
        return x + 1
'''


def full_bundle(**kw):
    """A deprecation done correctly, end to end."""
    return bundle(
        pyfile(CODE, GOOD_DEPRECATION),
        textfile(ACTIVE, GOOD_ACTIVE_SECTION),
        pyfile(TEST, GOOD_TEST),
        pr_text="Fixes #1\n<!-- BEGIN RELEASE NOTES -->\n"
                "core\n- BREAKING CHANGE: deprecated old_thing.\n<!-- END RELEASE NOTES -->",
        **kw,
    )


# --- C151 / C152 / C153: optional dependencies and test helpers ----------------------


def test_c151_passes_when_library_code_uses_import_module(corpus):
    b = bundle(pyfile(CODE, "numpy = import_module('numpy')\n"))
    assert verdict("SYMPY-C151", b, corpus).verdict == "pass"


def test_c151_fails_on_a_direct_import_in_library_code(corpus):
    assert verdict("SYMPY-C151", bundle(pyfile(CODE, "import numpy\n")), corpus).verdict == "fail"


def test_c151_not_applicable_to_a_test_module(corpus):
    """C107 covers test code; this rule is about library code, and pooling them would
    double-count one import."""
    assert_no_targets("SYMPY-C151", bundle(pyfile(TEST, "import numpy\n")), corpus)


def test_c152_passes_when_the_sympy_wrapper_is_used(corpus):
    b = bundle(pyfile(TEST, "from sympy.testing.pytest import raises\n"
                            "def test_x():\n    raises(ValueError, lambda: f())\n"))
    assert_no_targets("SYMPY-C152", b, corpus)


def test_c152_fails_on_a_direct_pytest_call(corpus):
    b = bundle(pyfile(TEST, "import pytest\n"
                            "def test_x():\n    pytest.skip('nope')\n"))
    assert verdict("SYMPY-C152", b, corpus).verdict == "fail"


def test_c152_fails_on_a_direct_pytest_import(corpus):
    b = bundle(pyfile(TEST, "from pytest import raises\n"))
    assert verdict("SYMPY-C152", b, corpus).verdict == "fail"


def test_c153_passes_when_the_module_can_skip_itself(corpus):
    b = bundle(pyfile(TEST, "from sympy.external import import_module\n"
                            "from sympy.testing.pytest import skip\n"
                            "numpy = import_module('numpy')\n"
                            "if not numpy:\n    skip('numpy not installed')\n"))
    assert verdict("SYMPY-C153", b, corpus).verdict == "pass"


def test_c153_passes_on_the_whole_file_skip_flag(corpus):
    b = bundle(pyfile(TEST, "import numpy\nskip = True\n"))
    assert verdict("SYMPY-C153", b, corpus).verdict == "pass"


def test_c153_fails_when_the_dependency_is_mandatory(corpus):
    b = bundle(pyfile(TEST, "import numpy\ndef test_x():\n    assert numpy\n"))
    assert verdict("SYMPY-C153", b, corpus).verdict == "fail"


def test_c153_not_applicable_without_an_optional_dependency(corpus):
    assert_no_targets("SYMPY-C153", bundle(pyfile(TEST, "def test_x():\n    pass\n")), corpus)


# --- C239 / C268: breaking changes ----------------------------------------------------


BASE_WITH_PUBLIC = "def gone(x):\n    return x\n\ndef kept(x):\n    return x\n"
HEAD_WITHOUT = "def kept(x):\n    return x\n"


def test_c239_passes_when_the_removal_is_documented(corpus):
    b = bundle(pyfile(CODE, HEAD_WITHOUT, base=BASE_WITH_PUBLIC),
               textfile("doc/src/guides/migration.md",
                        "gone has been removed. Use kept instead.\n"))
    assert verdict("SYMPY-C239", b, corpus).verdict == "pass"


def test_c239_fails_when_a_public_name_vanishes_silently(corpus):
    b = bundle(pyfile(CODE, HEAD_WITHOUT, base=BASE_WITH_PUBLIC))
    assert verdict("SYMPY-C239", b, corpus).verdict == "fail"


def test_c239_not_applicable_when_nothing_public_was_removed(corpus):
    b = bundle(pyfile(CODE, BASE_WITH_PUBLIC, base=BASE_WITH_PUBLIC))
    assert_no_targets("SYMPY-C239", b, corpus)


def test_c268_passes_with_a_breaking_change_entry(corpus):
    assert verdict("SYMPY-C268", full_bundle(), corpus).verdict == "pass"


def test_c268_fails_when_a_deprecation_ships_without_one(corpus):
    b = bundle(pyfile(CODE, GOOD_DEPRECATION),
               pr_text="<!-- BEGIN RELEASE NOTES -->\ncore\n- Deprecated old_thing.\n"
                       "<!-- END RELEASE NOTES -->")
    assert verdict("SYMPY-C268", b, corpus).verdict == "fail"


def test_c268_fails_when_there_is_no_pr_description_at_all(corpus):
    """The obligation attaches to the contribution, so writing no description is a way of
    failing it rather than a way of escaping it -- the same §4.2 shape as C006/C009."""
    b = bundle(pyfile(CODE, GOOD_DEPRECATION), pr_text=None)
    row = verdict("SYMPY-C268", b, corpus)
    assert row.verdict == "fail" and "no pull-request description" in row.notes


def test_c268_fails_when_the_pr_has_no_release_notes_block(corpus):
    b = bundle(pyfile(CODE, GOOD_DEPRECATION), pr_text="Fixes #1\n\nJust prose.")
    row = verdict("SYMPY-C268", b, corpus)
    assert row.verdict == "fail" and "no release-notes block" in row.notes


def test_c268_not_applicable_without_a_deprecation_or_removal(corpus):
    assert_no_targets("SYMPY-C268", bundle(pyfile(CODE, NO_DEPRECATION)), corpus)


# --- C240 / C241 / C243: need the API run --------------------------------------------


def test_the_behaviour_rules_are_withheld_until_phase_5(corpus):
    b = bundle(pyfile(CODE, GOOD_DEPRECATION))
    for rule_id in ("SYMPY-C240", "SYMPY-C241", "SYMPY-C243"):
        assert_withheld(rule_id, b, corpus)


def test_the_behaviour_rules_do_not_apply_without_a_deprecation(corpus):
    b = bundle(pyfile(CODE, NO_DEPRECATION))
    for rule_id in ("SYMPY-C240", "SYMPY-C241", "SYMPY-C243"):
        assert_no_targets(rule_id, b, corpus)


# --- the deprecation call ------------------------------------------------------------


def bad_call(**overrides) -> str:
    args = {"message": '"old_thing is deprecated. Use new_thing instead."',
            "deprecated_since_version": '"1.12"',
            "active_deprecations_target": '"old-thing-deprecation"',
            "stacklevel": "3"}
    args.update(overrides)
    kwargs = "".join(f"    {k}={v},\n" for k, v in args.items() if k != "message"
                     and v is not None)
    return ("from sympy.utilities.exceptions import sympy_deprecation_warning\n"
            "def old_thing(x):\n"
            "    sympy_deprecation_warning(\n"
            f"        {args['message']},\n" + kwargs.replace("    ", "        ") +
            "    )\n    return x\n")


def test_c248_passes_on_a_release_version(corpus):
    assert verdict("SYMPY-C248", bundle(pyfile(CODE, bad_call())), corpus).verdict == "pass"


def test_c248_fails_on_a_dev_version(corpus):
    """Asserts the *reason*, not just the verdict. `1.12.dev` also fails the
    release-version format check, so a test that only looked at the verdict would pass
    even with the `.dev` rejection removed -- which is how it was written first, and the
    mutation check caught it."""
    b = bundle(pyfile(CODE, bad_call(deprecated_since_version='"1.12.dev"')))
    row = verdict("SYMPY-C248", b, corpus)
    assert row.verdict == "fail"
    # The distinctive phrase, not just ".dev" -- the message echoes the value, so a
    # substring check on ".dev" passes even when the .dev branch is gone.
    assert "carries a .dev suffix" in row.notes, row.notes


def test_c248_fails_on_a_version_that_is_not_a_release(corpus):
    b = bundle(pyfile(CODE, bad_call(deprecated_since_version='"next"')))
    row = verdict("SYMPY-C248", b, corpus)
    assert row.verdict == "fail" and "release version" in row.notes


def test_c248_fails_when_the_version_is_missing(corpus):
    b = bundle(pyfile(CODE, bad_call(deprecated_since_version=None)))
    row = verdict("SYMPY-C248", b, corpus)
    assert row.verdict == "fail" and "no deprecated_since_version" in row.notes


def test_c248_not_applicable_without_a_deprecation(corpus):
    assert_no_targets("SYMPY-C248", bundle(pyfile(CODE, NO_DEPRECATION)), corpus)


def test_c249_passes_when_the_target_is_defined_in_the_doc(corpus):
    assert verdict("SYMPY-C249", full_bundle(), corpus).verdict == "pass"


def test_c249_fails_when_the_target_is_defined_nowhere(corpus):
    b = bundle(pyfile(CODE, bad_call(active_deprecations_target='"typo-target"')),
               textfile(ACTIVE, GOOD_ACTIVE_SECTION))
    assert verdict("SYMPY-C249", b, corpus).verdict == "fail"


def test_c249_fails_when_the_keyword_is_missing(corpus):
    b = bundle(pyfile(CODE, bad_call(active_deprecations_target=None)))
    row = verdict("SYMPY-C249", b, corpus)
    assert row.verdict == "fail" and "no active_deprecations_target" in row.notes


def test_c249_not_applicable_without_a_deprecation(corpus):
    assert_no_targets("SYMPY-C249", bundle(pyfile(CODE, NO_DEPRECATION)), corpus)


def test_c250_passes_when_stacklevel_is_set(corpus):
    assert verdict("SYMPY-C250", bundle(pyfile(CODE, bad_call())), corpus).verdict == "pass"


def test_c250_fails_without_stacklevel(corpus):
    b = bundle(pyfile(CODE, bad_call(stacklevel=None)))
    assert verdict("SYMPY-C250", b, corpus).verdict == "fail"


def test_c250_not_applicable_to_the_decorator_form(corpus):
    """`@deprecated` takes no stacklevel; only the call form can set one."""
    b = bundle(pyfile(CODE, "@deprecated('gone', deprecated_since_version='1.12')\n"
                            "def old_thing(x):\n    return x\n"))
    assert_no_targets("SYMPY-C250", b, corpus)


def test_c258_passes_when_the_helper_is_used(corpus):
    assert_no_targets("SYMPY-C258", bundle(pyfile(CODE, bad_call())), corpus)


def test_c258_fails_on_a_direct_instantiation(corpus):
    b = bundle(pyfile(CODE, "def f():\n    raise SymPyDeprecationWarning('gone')\n"))
    assert verdict("SYMPY-C258", b, corpus).verdict == "fail"


def test_c258_fails_when_passed_to_warn(corpus):
    b = bundle(pyfile(CODE, "import warnings\n"
                            "def f():\n    warnings.warn('gone', SymPyDeprecationWarning)\n"))
    assert verdict("SYMPY-C258", b, corpus).verdict == "fail"


# --- the message ---------------------------------------------------------------------


def test_c247_passes_when_the_message_names_api_and_replacement(corpus):
    assert verdict("SYMPY-C247", bundle(pyfile(CODE, bad_call())), corpus).verdict == "pass"


def test_c247_fails_when_the_message_offers_no_replacement(corpus):
    b = bundle(pyfile(CODE, bad_call(message='"old_thing is going away."')))
    assert verdict("SYMPY-C247", b, corpus).verdict == "fail"


def test_c247_not_applicable_when_the_message_is_not_a_literal(corpus):
    b = bundle(pyfile(CODE, bad_call(message="build_message()")))
    assert_no_targets("SYMPY-C247", b, corpus)


def test_c259_passes_on_one_short_paragraph(corpus):
    assert verdict("SYMPY-C259", bundle(pyfile(CODE, bad_call())), corpus).verdict == "pass"


def test_c259_fails_on_two_paragraphs(corpus):
    b = bundle(pyfile(CODE, bad_call(message='"""Use new_thing.\n\nSecond paragraph."""')))
    assert verdict("SYMPY-C259", b, corpus).verdict == "fail"


def test_c259_fails_on_an_overlong_prose_line(corpus):
    long = "old_thing is deprecated and you should really use new_thing instead of it now ok"
    b = bundle(pyfile(CODE, bad_call(message=f'"{long} {long}"')))
    assert verdict("SYMPY-C259", b, corpus).verdict == "fail"


def test_c260_passes_on_a_migration_only_message(corpus):
    assert verdict("SYMPY-C260", bundle(pyfile(CODE, bad_call())), corpus).verdict == "pass"


def test_c260_fails_when_the_message_carries_a_url(corpus):
    b = bundle(pyfile(CODE, bad_call(
        message='"Use new_thing instead. See https://docs.sympy.org/x.html"')))
    assert verdict("SYMPY-C260", b, corpus).verdict == "fail"


def test_c260_fails_when_the_message_explains_rationale(corpus):
    b = bundle(pyfile(CODE, bad_call(
        message='"Use new_thing instead, because the old name was confusing."')))
    assert verdict("SYMPY-C260", b, corpus).verdict == "fail"


def test_c261_passes_on_plain_text(corpus):
    assert verdict("SYMPY-C261", bundle(pyfile(CODE, bad_call())), corpus).verdict == "pass"


def test_c261_fails_on_rst_markup(corpus):
    b = bundle(pyfile(CODE, bad_call(message='"Use ``new_thing`` instead."')))
    assert verdict("SYMPY-C261", b, corpus).verdict == "fail"


def test_the_message_rules_do_not_apply_without_a_deprecation(corpus):
    b = bundle(pyfile(CODE, NO_DEPRECATION))
    for rule_id in ("SYMPY-C247", "SYMPY-C259", "SYMPY-C260", "SYMPY-C261"):
        assert_no_targets(rule_id, b, corpus)


# --- docstring notes ------------------------------------------------------------------


def test_c252_passes_when_the_docstring_carries_the_note(corpus):
    assert verdict("SYMPY-C252", full_bundle(), corpus).verdict == "pass"


def test_c252_fails_when_the_docstring_has_no_note(corpus):
    b = bundle(pyfile(CODE, '''
        def old_thing(x):
            """Do the old thing."""
            sympy_deprecation_warning("old_thing is deprecated. Use new_thing instead.",
                                      deprecated_since_version="1.12")
            return x
        '''))
    assert verdict("SYMPY-C252", b, corpus).verdict == "fail"


def test_c252_not_applicable_when_the_definition_has_no_docstring(corpus):
    b = bundle(pyfile(CODE, bad_call()))
    assert_no_targets("SYMPY-C252", b, corpus)


def test_c262_passes_when_the_directive_follows_the_summary(corpus):
    assert verdict("SYMPY-C262", full_bundle(), corpus).verdict == "pass"


def test_c262_fails_when_the_directive_is_buried(corpus):
    b = bundle(pyfile(CODE, '''
        def old_thing(x):
            """Do the old thing.

            Parameters
            ==========

            x : Expr

            .. deprecated:: 1.12

                Use new_thing instead.
            """
            sympy_deprecation_warning("old_thing is deprecated. Use new_thing instead.",
                                      deprecated_since_version="1.12")
            return x
        '''))
    assert verdict("SYMPY-C262", b, corpus).verdict == "fail"


def test_c262_not_applicable_without_a_directive_to_place(corpus):
    b = bundle(pyfile(CODE, '''
        def old_thing(x):
            """Do the old thing."""
            sympy_deprecation_warning("old_thing is deprecated. Use new_thing instead.",
                                      deprecated_since_version="1.12")
            return x
        '''))
    assert_no_targets("SYMPY-C262", b, corpus)


def test_c263_passes_on_a_one_paragraph_note_naming_the_replacement(corpus):
    assert verdict("SYMPY-C263", full_bundle(), corpus).verdict == "pass"


def test_c263_fails_when_the_note_names_no_replacement(corpus):
    b = bundle(pyfile(CODE, '''
        def old_thing(x):
            """Do the old thing.

            .. deprecated:: 1.12

                This is going away.
            """
            sympy_deprecation_warning("old_thing is deprecated. Use new_thing instead.",
                                      deprecated_since_version="1.12")
            return x
        '''))
    assert verdict("SYMPY-C263", b, corpus).verdict == "fail"


# --- active-deprecations.md ------------------------------------------------------------


def test_c253_passes_when_a_section_is_added(corpus):
    assert verdict("SYMPY-C253", full_bundle(), corpus).verdict == "pass"


def test_c253_fails_when_the_file_is_never_touched(corpus):
    b = bundle(pyfile(CODE, GOOD_DEPRECATION))
    row = verdict("SYMPY-C253", b, corpus)
    # The distinctive phrase: both failure paths name the file, so a substring check on
    # the filename cannot tell "never touched it" from "touched it but added no section".
    assert row.verdict == "fail" and "without touching" in row.notes, row.notes


def test_c253_fails_when_the_doc_is_touched_but_gains_no_section(corpus):
    b = bundle(pyfile(CODE, GOOD_DEPRECATION),
               textfile(ACTIVE, "Some prose with no heading at all.\n"))
    row = verdict("SYMPY-C253", b, corpus)
    assert row.verdict == "fail" and "no section heading" in row.notes


def test_c253_not_applicable_without_a_deprecation(corpus):
    assert_no_targets("SYMPY-C253", bundle(pyfile(CODE, NO_DEPRECATION)), corpus)


def test_c254_passes_when_a_target_precedes_the_heading(corpus):
    assert verdict("SYMPY-C254", full_bundle(), corpus).verdict == "pass"


def test_c254_fails_when_the_heading_has_no_target(corpus):
    b = bundle(pyfile(CODE, GOOD_DEPRECATION),
               textfile(ACTIVE, "### old_thing\n\nUse new_thing instead.\n"))
    assert verdict("SYMPY-C254", b, corpus).verdict == "fail"


def test_c254_not_applicable_when_the_doc_is_untouched(corpus):
    assert_no_targets("SYMPY-C254", bundle(pyfile(CODE, GOOD_DEPRECATION)), corpus)


def test_c264_passes_when_the_section_says_what_why_and_replacement(corpus):
    assert verdict("SYMPY-C264", full_bundle(), corpus).verdict == "pass"


def test_c264_fails_when_the_section_gives_no_reason(corpus):
    b = bundle(pyfile(CODE, GOOD_DEPRECATION),
               textfile(ACTIVE, "(old-thing-deprecation)=\n### old_thing\n\n"
                                "Use new_thing instead.\n"))
    assert verdict("SYMPY-C264", b, corpus).verdict == "fail"


def test_c265_passes_on_a_level_three_heading(corpus):
    assert verdict("SYMPY-C265", full_bundle(), corpus).verdict == "pass"


def test_c264_fails_when_the_section_offers_no_replacement(corpus):
    b = bundle(pyfile(CODE, GOOD_DEPRECATION),
               textfile(ACTIVE, "(old-thing-deprecation)=\n### old_thing\n\n"
                                "This was confusing, so it is going away.\n"))
    row = verdict("SYMPY-C264", b, corpus)
    assert row.verdict == "fail" and "a replacement" in row.notes


def test_c265_fails_on_the_wrong_heading_level(corpus):
    b = bundle(pyfile(CODE, GOOD_DEPRECATION),
               textfile(ACTIVE, "(old-thing-deprecation)=\n## old_thing\n\n"
                                "Use new_thing instead because it was confusing.\n"))
    assert verdict("SYMPY-C265", b, corpus).verdict == "fail"


def test_c266_passes_when_the_section_names_the_submodule(corpus):
    assert verdict("SYMPY-C266", full_bundle(), corpus).verdict == "pass"


def test_c266_fails_when_the_submodule_is_absent(corpus):
    b = bundle(pyfile("sympy/holonomic/recurrence.py", GOOD_DEPRECATION),
               textfile(ACTIVE, "(old-thing-deprecation)=\n### old_thing\n\n"
                                "Use new_thing instead because it was confusing.\n"))
    assert verdict("SYMPY-C266", b, corpus).verdict == "fail"


def test_the_doc_section_rules_do_not_apply_without_an_edit(corpus):
    b = bundle(pyfile(CODE, GOOD_DEPRECATION))
    for rule_id in ("SYMPY-C254", "SYMPY-C264", "SYMPY-C265", "SYMPY-C266"):
        assert_no_targets(rule_id, b, corpus)


# --- test and validation --------------------------------------------------------------


def test_c255_passes_when_a_warns_test_asserts_the_behaviour(corpus):
    assert verdict("SYMPY-C255", full_bundle(), corpus).verdict == "pass"


def test_c255_fails_when_no_test_wraps_the_deprecated_call(corpus):
    b = bundle(pyfile(CODE, GOOD_DEPRECATION))
    assert verdict("SYMPY-C255", b, corpus).verdict == "fail"


def test_c255_fails_when_the_test_asserts_nothing(corpus):
    b = bundle(pyfile(CODE, GOOD_DEPRECATION), pyfile(TEST, '''
        from sympy.testing.pytest import warns_deprecated_sympy
        def test_old_thing_deprecated():
            with warns_deprecated_sympy():
                old_thing(1)
        '''))
    row = verdict("SYMPY-C255", b, corpus)
    assert row.verdict == "fail" and "asserts nothing" in row.notes


def test_c255_not_applicable_without_a_deprecation(corpus):
    assert_no_targets("SYMPY-C255", bundle(pyfile(TEST, GOOD_TEST)), corpus)


def test_c256_passes_when_bin_test_was_run_clean(corpus):
    b = bundle(pyfile(CODE, GOOD_DEPRECATION),
               commands=[("python bin/test", "tests finished: 3 passed")])
    assert verdict("SYMPY-C256", b, corpus).verdict == "pass"


def test_c256_fails_when_bin_test_was_never_run(corpus):
    assert verdict("SYMPY-C256", bundle(pyfile(CODE, GOOD_DEPRECATION)), corpus).verdict == "fail"


def test_c256_not_applicable_without_a_deprecation(corpus):
    assert_no_targets("SYMPY-C256", bundle(pyfile(CODE, NO_DEPRECATION)), corpus)


# --- the gatekeeper property ----------------------------------------------------------


def test_a_deprecation_documenting_nothing_fails_across_the_category(corpus):
    """The §4.2 property for the whole category, as one assertion.

    An agent that introduces a deprecation and does none of the surrounding work must
    accumulate failures, not `not_applicable`. If any of these ever reads
    `not_applicable`, that rule has been rewritten to trigger on the artefact it demands.
    """
    b = bundle(pyfile(CODE, "def old_thing(x):\n"
                            "    sympy_deprecation_warning('gone')\n    return x\n"))
    must_fail = ("SYMPY-C248", "SYMPY-C249", "SYMPY-C250", "SYMPY-C253", "SYMPY-C255",
                 "SYMPY-C256", "SYMPY-C268")
    verdicts = {rid: verdict(rid, b, corpus).verdict for rid in must_fail}
    assert set(verdicts.values()) == {"fail"}, verdicts


def test_no_deprecation_means_the_category_stays_silent(corpus):
    """And the converse: a contribution with no deprecation must activate none of them."""
    b = bundle(pyfile(CODE, NO_DEPRECATION))
    deprecation_rules = [
        rid for rid, r in RULES.items()
        # Scoped to this file's own pack: the bundle below is SymPy-shaped, so another
        # project's rule firing on it is not evidence of anything.
        if r.category == "Specialized changes"
        and rid.startswith("SYMPY-")
        and rid not in ("SYMPY-C151", "SYMPY-C152", "SYMPY-C153", "SYMPY-C239")
    ]
    fired = {rid: verdict(rid, b, corpus).n_targets for rid in deprecation_rules}
    assert set(fired.values()) == {0}, {k: v for k, v in fired.items() if v}


# --- C246: internal uses are migrated before the deprecation ------------------------------


def test_c246_passes_when_nothing_else_calls_the_deprecated_name(corpus):
    row = verdict("SYMPY-C246", bundle(pyfile(CODE, GOOD_DEPRECATION)), corpus)
    assert row.n_targets > 0 and row.verdict == "pass", row.notes


def test_c246_fails_when_the_contribution_still_calls_the_deprecated_name(corpus):
    source = GOOD_DEPRECATION + '''
    def caller(x):
        return old_thing(x)
'''
    row = verdict("SYMPY-C246", bundle(pyfile(CODE, source)), corpus)
    assert row.verdict == "fail" and "still calls deprecated" in row.notes, row.notes


def test_c246_not_applicable_without_a_deprecation(corpus):
    assert_no_targets("SYMPY-C246", bundle(pyfile(CODE, NO_DEPRECATION)), corpus)

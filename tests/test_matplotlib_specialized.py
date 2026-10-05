"""Three cases per rule (`docs/checker-authoring.md` §9): satisfied, violated, and an
input where the pre-condition finds nothing.

**C202 and C208 have no satisfying case, and that is not an omission (§9).** Both are
graded one-sidedly: C202 can prove that a gutted body broke the deprecated API but needs
the API exercised to show it still works, and C208 can prove a missing ``since`` but needs
the project's version at the base commit to check the one that is given. Their cases are
violated, withheld -- ``not_applicable`` with a non-``ok`` status -- and no target.

Several no-target cases pin this module's §7.5 narrowings:
``test_c209_finds_no_target_for_a_parameter_helper`` (C210/C211 own those),
``test_c249_finds_no_target_for_a_style_fix`` (C250 owns that), and
``test_c263_finds_no_target_for_a_vendored_file`` (C262 owns that).
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.matplotlib.specialized  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


@pytest.fixture(scope="module")
def corpus():
    """matplotlib's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("matplotlib"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def whole(path: str, body: str, **kwargs):
    lines = body.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=body, **kwargs)


def removing(path: str, removed: list[str], body: str = "x = 1\n"):
    """A file the agent edited, with lines on the minus side of the diff."""
    lines = body.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=body, removed_lines=tuple(removed))


RCSETUP = "lib/matplotlib/rcsetup.py"
MATPLOTLIBRC = "lib/matplotlib/mpl-data/matplotlibrc"
TYPING = "lib/matplotlib/typing.py"
AXES = "lib/matplotlib/axes/_axes.py"


# --- C192--C194 registering a new rcParam ------------------------------------------------


def rc_bundle(*, validator=True, template=True, typing=True):
    files = []
    if validator:
        files.append(whole(RCSETUP,
                           '_validators = {\n    "axes.newthing": _Param(validate_bool),\n}\n'))
    if template:
        files.append(whole(MATPLOTLIBRC, "#axes.newthing: True\n"))
    if typing:
        files.append(whole(TYPING, 'RcKeyType = Literal["axes.newthing"]\n'))
    return make_bundle(files=files)


def test_c192_passes_when_the_key_is_registered_with_a_validator(corpus):
    assert verdict("MATPLOTLIB-C192", rc_bundle(), corpus).verdict == "pass"


def test_c192_fails_when_the_key_never_reaches_rcsetup(corpus):
    assert verdict("MATPLOTLIB-C192", rc_bundle(validator=False),
                   corpus).verdict == "fail"


def test_c192_finds_no_target_when_no_rcparam_is_introduced(corpus):
    row = verdict("MATPLOTLIB-C192", make_bundle(files=[whole(AXES, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c193_passes_when_the_template_gains_a_commented_entry(corpus):
    assert verdict("MATPLOTLIB-C193", rc_bundle(), corpus).verdict == "pass"


def test_c193_fails_when_the_template_is_left_alone(corpus):
    assert verdict("MATPLOTLIB-C193", rc_bundle(template=False),
                   corpus).verdict == "fail"


def test_c193_finds_no_target_when_no_rcparam_is_introduced(corpus):
    row = verdict("MATPLOTLIB-C193", make_bundle(files=[whole(AXES, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c194_passes_when_the_key_reaches_the_rckeytype_literal(corpus):
    assert verdict("MATPLOTLIB-C194", rc_bundle(), corpus).verdict == "pass"


def test_c194_fails_when_the_typing_stub_is_left_alone(corpus):
    assert verdict("MATPLOTLIB-C194", rc_bundle(typing=False), corpus).verdict == "fail"


def test_c194_finds_no_target_when_no_rcparam_is_introduced(corpus):
    row = verdict("MATPLOTLIB-C194", make_bundle(files=[whole(AXES, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C195/C196 the pyplot wrapper contract ------------------------------------------------


SIGNATURE = "class Axes:\n    def plot(self, *args, scalex=True):\n        return args\n"


def test_c195_passes_when_the_guard_test_is_run(corpus):
    bundle = make_bundle(files=[whole(AXES, SIGNATURE)],
                         commands=[Command(index=0,
                                           command="pytest -k test_pyplot_up_to_date")])
    assert verdict("MATPLOTLIB-C195", bundle, corpus).verdict == "pass"


def test_c195_fails_when_the_guard_test_is_never_run(corpus):
    bundle = make_bundle(files=[whole(AXES, SIGNATURE)],
                         commands=[Command(index=0, command="pytest")])
    assert verdict("MATPLOTLIB-C195", bundle, corpus).verdict == "fail"


def test_c195_finds_no_target_when_no_wrapped_signature_changed(corpus):
    row = verdict("MATPLOTLIB-C195",
                  make_bundle(files=[whole("lib/matplotlib/colors.py", SIGNATURE)]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c196_passes_when_the_wrappers_are_committed(corpus):
    bundle = make_bundle(files=[whole(AXES, SIGNATURE),
                                whole("lib/matplotlib/pyplot.py", "def plot(*args): ...\n")])
    assert verdict("MATPLOTLIB-C196", bundle, corpus).verdict == "pass"


def test_c196_fails_when_pyplot_is_left_stale(corpus):
    assert verdict("MATPLOTLIB-C196", make_bundle(files=[whole(AXES, SIGNATURE)]),
                   corpus).verdict == "fail"


def test_c196_finds_no_target_when_no_wrapped_signature_changed(corpus):
    row = verdict("MATPLOTLIB-C196",
                  make_bundle(files=[whole("lib/matplotlib/colors.py", SIGNATURE)]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C197/C198 colormaps, colour sequences and styles ---------------------------------------


CM = "lib/matplotlib/_cm_listed.py"
STYLE = "lib/matplotlib/mpl-data/stylelib/newstyle.mplstyle"


def test_c197_passes_when_the_palette_file_only_gains_entries(corpus):
    assert verdict("MATPLOTLIB-C197", make_bundle(files=[whole(CM, "_newmap_data = []\n")]),
                   corpus).verdict == "pass"


def test_c197_fails_when_an_existing_entry_is_changed(corpus):
    bundle = make_bundle(files=[removing(CM, ["_viridis_data = [(0.1, 0.2, 0.3)]"])])
    assert verdict("MATPLOTLIB-C197", bundle, corpus).verdict == "fail"


def test_c197_finds_no_target_for_a_change_outside_the_palette_files(corpus):
    row = verdict("MATPLOTLIB-C197", make_bundle(files=[whole(AXES, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c198_passes_when_the_new_style_names_a_compatible_licence(corpus):
    body = "# Licensed under a BSD 3-clause licence\naxes.grid: True\n"
    assert verdict("MATPLOTLIB-C198",
                   make_bundle(files=[whole(STYLE, body, is_new=True)]),
                   corpus).verdict == "pass"


def test_c198_fails_when_no_licence_is_stated_anywhere(corpus):
    assert verdict("MATPLOTLIB-C198",
                   make_bundle(files=[whole(STYLE, "axes.grid: True\n", is_new=True)]),
                   corpus).verdict == "fail"


def test_c198_finds_no_target_when_no_palette_is_added(corpus):
    row = verdict("MATPLOTLIB-C198", make_bundle(files=[whole(AXES, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- the deprecation lifecycle ------------------------------------------------------------------


def deprecating(call: str, body: str = "    return 1\n", *, name: str = "old_thing"):
    source = ("from matplotlib import _api\n"
              "\n"
              "\n"
              f"@_api.{call}\n"
              f"def {name}(x, colour=None):\n"
              f"{body}")
    return whole(AXES, source)


DEPRECATED = deprecating('deprecated("3.9", alternative="new_thing")')
GUTTED = deprecating('deprecated("3.9", alternative="new_thing")',
                     "    raise NotImplementedError\n")
NO_ALTERNATIVE = deprecating('deprecated("3.9")')
NO_SINCE = deprecating("deprecated()")
RENAME = deprecating('rename_parameter("3.9", "color", "colour")')
DELETE = deprecating('delete_parameter("3.9", "colour")')
PENDING_OK = deprecating('deprecated("3.9", pending=True)')
PENDING_BAD = deprecating('deprecated("3.9", pending=True, removal="3.11")')
STUB = make_file("lib/matplotlib/axes/_axes.pyi",
                 [(1, "def old_thing(x, colour: str = ...) -> int: ...")],
                 head_text="def old_thing(x, colour: str = ...) -> int: ...")
STUB_EMPTY = make_file("lib/matplotlib/axes/_axes.pyi", [(1, "def other() -> None: ...")],
                       head_text="def other() -> None: ...")


def test_c202_fails_when_the_deprecated_body_is_gutted(corpus):
    assert verdict("MATPLOTLIB-C202", make_bundle(files=[GUTTED]), corpus).verdict == "fail"


def test_c202_withholds_when_the_deprecated_api_was_never_exercised(corpus):
    row = verdict("MATPLOTLIB-C202", make_bundle(files=[DEPRECATED]), corpus)
    assert row.verdict == "not_applicable" and row.status != "ok"


def test_c202_finds_no_target_when_nothing_is_deprecated(corpus):
    row = verdict("MATPLOTLIB-C202", make_bundle(files=[whole(AXES, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c203_passes_when_the_deprecation_names_a_replacement(corpus):
    assert verdict("MATPLOTLIB-C203", make_bundle(files=[DEPRECATED]),
                   corpus).verdict == "pass"


def test_c203_fails_when_no_alternative_is_given(corpus):
    assert verdict("MATPLOTLIB-C203", make_bundle(files=[NO_ALTERNATIVE]),
                   corpus).verdict == "fail"


def test_c203_finds_no_target_when_nothing_is_deprecated(corpus):
    row = verdict("MATPLOTLIB-C203", make_bundle(files=[whole(AXES, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c206_passes_when_the_api_helper_is_used(corpus):
    assert verdict("MATPLOTLIB-C206", make_bundle(files=[DEPRECATED]),
                   corpus).verdict == "pass"


def test_c206_fails_for_a_hand_rolled_deprecation_warning(corpus):
    body = ("import warnings\n\n\ndef old_thing():\n"
            "    warnings.warn('gone', DeprecationWarning)\n")
    assert verdict("MATPLOTLIB-C206", make_bundle(files=[whole(AXES, body)]),
                   corpus).verdict == "fail"


def test_c206_finds_no_target_when_nothing_is_deprecated(corpus):
    row = verdict("MATPLOTLIB-C206", make_bundle(files=[whole(AXES, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c207_passes_when_the_parameter_helper_names_a_real_parameter(corpus):
    assert verdict("MATPLOTLIB-C207", make_bundle(files=[RENAME]),
                   corpus).verdict == "pass"


def test_c207_fails_when_the_parameter_helper_names_no_parameter(corpus):
    bad = deprecating('rename_parameter("3.9", "color", "shade")')
    assert verdict("MATPLOTLIB-C207", make_bundle(files=[bad]), corpus).verdict == "fail"


def test_c207_finds_no_target_when_nothing_is_deprecated(corpus):
    row = verdict("MATPLOTLIB-C207", make_bundle(files=[whole(AXES, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c208_fails_when_the_helper_names_no_since(corpus):
    assert verdict("MATPLOTLIB-C208", make_bundle(files=[NO_SINCE]),
                   corpus).verdict == "fail"


def test_c208_withholds_when_the_project_version_is_unknown(corpus):
    row = verdict("MATPLOTLIB-C208", make_bundle(files=[DEPRECATED]), corpus)
    assert row.verdict == "not_applicable" and row.status != "ok"


def test_c208_finds_no_target_when_nothing_is_deprecated(corpus):
    row = verdict("MATPLOTLIB-C208", make_bundle(files=[whole(AXES, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c209_passes_when_the_stub_moves_with_the_deprecation(corpus):
    bundle = make_bundle(files=[DEPRECATED, STUB])
    assert verdict("MATPLOTLIB-C209", bundle, corpus).verdict == "pass"


def test_c209_fails_when_the_stub_is_left_behind(corpus):
    assert verdict("MATPLOTLIB-C209", make_bundle(files=[DEPRECATED]),
                   corpus).verdict == "fail"


def test_c209_finds_no_target_for_a_parameter_helper(corpus):
    """The §7.5 half: rename/delete/keyword-only deprecations are C210's and C211's."""
    row = verdict("MATPLOTLIB-C209", make_bundle(files=[RENAME]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c210_passes_when_the_stub_names_the_renamed_parameter(corpus):
    assert verdict("MATPLOTLIB-C210", make_bundle(files=[RENAME, STUB]),
                   corpus).verdict == "pass"


def test_c210_fails_when_the_stub_never_names_it(corpus):
    assert verdict("MATPLOTLIB-C210", make_bundle(files=[RENAME, STUB_EMPTY]),
                   corpus).verdict == "fail"


def test_c210_finds_no_target_for_a_whole_object_deprecation(corpus):
    row = verdict("MATPLOTLIB-C210", make_bundle(files=[DEPRECATED, STUB]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c211_passes_when_the_stub_gives_the_parameter_a_default(corpus):
    assert verdict("MATPLOTLIB-C211", make_bundle(files=[DELETE, STUB]),
                   corpus).verdict == "pass"


def test_c211_fails_when_the_stub_gives_it_none(corpus):
    assert verdict("MATPLOTLIB-C211", make_bundle(files=[DELETE, STUB_EMPTY]),
                   corpus).verdict == "fail"


def test_c211_finds_no_target_for_a_rename_deprecation(corpus):
    row = verdict("MATPLOTLIB-C211", make_bundle(files=[RENAME, STUB]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


EXPIRED = removing(AXES, ["    @_api.deprecated('3.9')", "    def old_thing(self):",
                          "        return 1"])
EXPIRED_KEEPING_API = removing(AXES, ["    @_api.deprecated('3.9')"])
EXPIRED_STUB = make_file("lib/matplotlib/axes/_axes.pyi", [(1, "def other() -> None: ...")],
                         head_text="def other() -> None: ...",
                         removed_lines=("def old_thing(self) -> int: ...",))
EXPIRED_STUB_UNCHANGED = make_file("lib/matplotlib/axes/_axes.pyi",
                                   [(1, "def other() -> None: ...")],
                                   head_text="def other() -> None: ...")


def test_c213_passes_when_the_api_goes_with_the_warning(corpus):
    assert verdict("MATPLOTLIB-C213", make_bundle(files=[EXPIRED]),
                   corpus).verdict == "pass"


def test_c213_fails_when_only_the_warning_is_removed(corpus):
    assert verdict("MATPLOTLIB-C213", make_bundle(files=[EXPIRED_KEEPING_API]),
                   corpus).verdict == "fail"


def test_c213_finds_no_target_when_no_deprecation_expires(corpus):
    row = verdict("MATPLOTLIB-C213", make_bundle(files=[whole(AXES, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c214_passes_when_the_stub_loses_the_expired_item(corpus):
    assert verdict("MATPLOTLIB-C214", make_bundle(files=[EXPIRED, EXPIRED_STUB]),
                   corpus).verdict == "pass"


def test_c214_fails_when_the_stub_still_declares_it(corpus):
    assert verdict("MATPLOTLIB-C214",
                   make_bundle(files=[EXPIRED, EXPIRED_STUB_UNCHANGED]),
                   corpus).verdict == "fail"


def test_c214_finds_no_target_when_no_deprecation_expires(corpus):
    row = verdict("MATPLOTLIB-C214", make_bundle(files=[whole(AXES, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c216_passes_when_a_pending_deprecation_names_no_removal(corpus):
    assert verdict("MATPLOTLIB-C216", make_bundle(files=[PENDING_OK]),
                   corpus).verdict == "pass"


def test_c216_fails_when_a_pending_deprecation_names_a_removal(corpus):
    assert verdict("MATPLOTLIB-C216", make_bundle(files=[PENDING_BAD]),
                   corpus).verdict == "fail"


def test_c216_finds_no_target_for_an_ordinary_deprecation(corpus):
    row = verdict("MATPLOTLIB-C216", make_bundle(files=[DEPRECATED]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def converted(call: str):
    source = ("from matplotlib import _api\n"
              "\n"
              "\n"
              f"@_api.{call}\n"
              "def old_thing(x, colour=None):\n"
              "    return 1\n")
    lines = source.split("\n")
    return make_file(AXES, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=source,
                     removed_lines=('@_api.deprecated("3.9", pending=True)',))


def test_c217_passes_when_the_versions_are_two_meso_releases_apart(corpus):
    bundle = make_bundle(files=[converted('deprecated("3.10", removal="3.12")')])
    assert verdict("MATPLOTLIB-C217", bundle, corpus).verdict == "pass"


def test_c217_fails_when_the_removal_is_too_close(corpus):
    bundle = make_bundle(files=[converted('deprecated("3.10", removal="3.11")')])
    assert verdict("MATPLOTLIB-C217", bundle, corpus).verdict == "fail"


def test_c217_finds_no_target_when_no_pending_deprecation_is_converted(corpus):
    row = verdict("MATPLOTLIB-C217", make_bundle(files=[DEPRECATED]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C244 meson ---------------------------------------------------------------------------------


NEW_MODULE = whole("lib/matplotlib/newthing.py", "x = 1\n", is_new=True)


def test_c244_passes_when_the_meson_build_lists_the_file(corpus):
    build = whole("lib/matplotlib/meson.build", "python_sources = [\n  'newthing.py',\n]\n")
    assert verdict("MATPLOTLIB-C244", make_bundle(files=[NEW_MODULE, build]),
                   corpus).verdict == "pass"


def test_c244_fails_when_the_meson_build_is_untouched(corpus):
    assert verdict("MATPLOTLIB-C244", make_bundle(files=[NEW_MODULE]),
                   corpus).verdict == "fail"


def test_c244_finds_no_target_when_no_new_source_file_is_added(corpus):
    row = verdict("MATPLOTLIB-C244", make_bundle(files=[whole(AXES, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C249--C251 vendored code and clang-tidy ------------------------------------------------------


EXTERN = "extern/agg24-svn/src/agg_curves.cpp"
SUBSTANTIVE = make_file(EXTERN, [(3, "    return curve4(a, b) + 1;")],
                        head_text="int f() {\n\n    return curve4(a, b) + 1;\n}\n",
                        removed_lines=("    return curve4(a, b);",))
STYLE_FIX = make_file(EXTERN, [(3, "    return curve4(a, b);")],
                      head_text="int f() {\n\n    return curve4(a, b);\n}\n",
                      removed_lines=("        return curve4(a,b);",))


def test_c249_passes_when_the_project_tree_is_changed_too(corpus):
    bundle = make_bundle(files=[SUBSTANTIVE, whole("src/_path.h", "int g();\n")])
    assert verdict("MATPLOTLIB-C249", bundle, corpus).verdict == "pass"


def test_c249_fails_when_only_vendored_code_is_changed(corpus):
    assert verdict("MATPLOTLIB-C249", make_bundle(files=[SUBSTANTIVE]),
                   corpus).verdict == "fail"


def test_c249_finds_no_target_for_a_style_fix(corpus):
    """The §7.5 half: a cosmetic edit under extern/ is C250's finding, not this one's."""
    row = verdict("MATPLOTLIB-C249", make_bundle(files=[STYLE_FIX]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c250_passes_for_a_substantive_vendored_edit(corpus):
    assert verdict("MATPLOTLIB-C250", make_bundle(files=[SUBSTANTIVE]),
                   corpus).verdict == "pass"


def test_c250_fails_for_a_style_fix(corpus):
    assert verdict("MATPLOTLIB-C250", make_bundle(files=[STYLE_FIX]),
                   corpus).verdict == "fail"


def test_c250_finds_no_target_when_nothing_vendored_is_edited(corpus):
    row = verdict("MATPLOTLIB-C250", make_bundle(files=[whole("src/_path.h", "int g();\n")]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c251_passes_for_a_narrow_nolint_with_a_reason(corpus):
    body = "int f() { return 1; }  // NOLINTNEXTLINE(bugprone-x): false positive on macros\n"
    assert verdict("MATPLOTLIB-C251", make_bundle(files=[whole("src/_path.cpp", body)]),
                   corpus).verdict == "pass"


def test_c251_fails_for_a_blanket_nolint(corpus):
    body = "int f() { return 1; }  // NOLINT\n"
    assert verdict("MATPLOTLIB-C251", make_bundle(files=[whole("src/_path.cpp", body)]),
                   corpus).verdict == "fail"


def test_c251_finds_no_target_when_nothing_is_suppressed(corpus):
    row = verdict("MATPLOTLIB-C251",
                  make_bundle(files=[whole("src/_path.cpp", "int f() { return 1; }\n")]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C262--C265 licences ----------------------------------------------------------------------------


VENDORED_BSD = whole("extern/newdep/newdep.h",
                     "/* Copyright 2020 Someone. BSD 3-clause. */\n", is_new=True)
VENDORED_BARE = whole("extern/newdep/newdep.h", "/* Copyright 2020 Someone. */\n",
                      is_new=True)
LICENSE_COPY = whole("LICENSE/LICENSE_NEWDEP", "BSD 3-clause\n", is_new=True)


def test_c262_passes_when_the_vendored_file_names_a_compatible_licence(corpus):
    assert verdict("MATPLOTLIB-C262", make_bundle(files=[VENDORED_BSD]),
                   corpus).verdict == "pass"


def test_c262_fails_when_no_licence_is_stated(corpus):
    assert verdict("MATPLOTLIB-C262", make_bundle(files=[VENDORED_BARE]),
                   corpus).verdict == "fail"


def test_c262_finds_no_target_when_nothing_is_vendored_in(corpus):
    row = verdict("MATPLOTLIB-C262", make_bundle(files=[NEW_MODULE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c263_passes_for_a_new_module_with_no_copyleft(corpus):
    assert verdict("MATPLOTLIB-C263", make_bundle(files=[NEW_MODULE]),
                   corpus).verdict == "pass"


def test_c263_fails_for_a_gpl_module_in_the_main_tree(corpus):
    body = "# Licensed under the GNU General Public License\nx = 1\n"
    bundle = make_bundle(files=[whole("lib/matplotlib/newthing.py", body, is_new=True)])
    assert verdict("MATPLOTLIB-C263", bundle, corpus).verdict == "fail"


def test_c263_finds_no_target_for_a_vendored_file(corpus):
    """The §7.5 half: code under extern/ is C262's, so it is not graded twice."""
    row = verdict("MATPLOTLIB-C263", make_bundle(files=[VENDORED_BSD]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c264_passes_when_a_licence_copy_accompanies_the_dependency(corpus):
    assert verdict("MATPLOTLIB-C264", make_bundle(files=[VENDORED_BSD, LICENSE_COPY]),
                   corpus).verdict == "pass"


def test_c264_fails_when_no_licence_copy_is_added(corpus):
    assert verdict("MATPLOTLIB-C264", make_bundle(files=[VENDORED_BSD]),
                   corpus).verdict == "fail"


def test_c264_finds_no_target_when_nothing_is_vendored(corpus):
    row = verdict("MATPLOTLIB-C264", make_bundle(files=[NEW_MODULE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


TOOLKIT = "lib/mpl_toolkits/mplot3d/borrowed.py"


def test_c265_passes_when_the_toolkit_file_states_its_licence(corpus):
    body = "# Adapted from someproject, MIT licensed.\nx = 1\n"
    assert verdict("MATPLOTLIB-C265",
                   make_bundle(files=[whole(TOOLKIT, body, is_new=True)]),
                   corpus).verdict == "pass"


def test_c265_fails_when_the_attribution_names_no_licence(corpus):
    body = "# Adapted from someproject.\nx = 1\n"
    assert verdict("MATPLOTLIB-C265",
                   make_bundle(files=[whole(TOOLKIT, body, is_new=True)]),
                   corpus).verdict == "fail"


def test_c265_finds_no_target_for_original_toolkit_code(corpus):
    row = verdict("MATPLOTLIB-C265",
                  make_bundle(files=[whole(TOOLKIT, "x = 1\n", is_new=True)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C284/C286/C287 minimum supported versions ----------------------------------------------------------


def pyproject(requires: str, classifiers: list[str]):
    body = (f'requires-python = "{requires}"\n'
            + "".join(f'  "Programming Language :: Python :: {c}",\n' for c in classifiers))
    return whole("pyproject.toml", body)


def test_c284_passes_when_requires_python_matches_the_lowest_supported(corpus):
    bundle = make_bundle(files=[pyproject(">=3.10", ["3.10", "3.11", "3.12"])])
    assert verdict("MATPLOTLIB-C284", bundle, corpus).verdict == "pass"


def test_c284_fails_when_the_floor_is_above_a_still_supported_version(corpus):
    bundle = make_bundle(files=[pyproject(">=3.11", ["3.10", "3.11"])])
    assert verdict("MATPLOTLIB-C284", bundle, corpus).verdict == "fail"


def test_c284_finds_no_target_when_requires_python_is_not_set(corpus):
    row = verdict("MATPLOTLIB-C284",
                  make_bundle(files=[whole("pyproject.toml", 'name = "matplotlib"\n')]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


MIN_PYTHON_ALL = [
    whole("pyproject.toml", 'requires-python = ">=3.11"\n'),
    whole("environment.yml", "  - python>=3.11\n"),
    whole("doc/install/dependencies.rst", "Python 3.11\n"),
    whole("doc/devel/min_dep_policy.rst", "Python 3.11\n"),
    whole(".github/workflows/tests.yml", "python-version: '3.11'\n"),
    whole("tox.ini", "envlist = py311\n"),
]


def test_c286_passes_when_all_six_files_move_together(corpus):
    assert verdict("MATPLOTLIB-C286", make_bundle(files=MIN_PYTHON_ALL),
                   corpus).verdict == "pass"


def test_c286_fails_when_some_of_the_six_are_left_behind(corpus):
    assert verdict("MATPLOTLIB-C286", make_bundle(files=MIN_PYTHON_ALL[:2]),
                   corpus).verdict == "fail"


def test_c286_finds_no_target_when_the_minimum_is_not_raised(corpus):
    row = verdict("MATPLOTLIB-C286", make_bundle(files=[whole(AXES, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


MIN_NUMPY_ALL = [
    whole("pyproject.toml", '  "numpy>=1.25",\n'),
    whole("environment.yml", "  - numpy>=1.25\n"),
    whole("doc/install/dependencies.rst", "NumPy 1.25\n"),
    whole("doc/devel/min_dep_policy.rst", "NumPy 1.25\n"),
    whole("requirements/testing/minver.txt", "numpy==1.25\n"),
    whole("lib/matplotlib/__init__.py", "    _check_versions()\n"),
]


def test_c287_passes_when_all_six_files_move_together(corpus):
    assert verdict("MATPLOTLIB-C287", make_bundle(files=MIN_NUMPY_ALL),
                   corpus).verdict == "pass"


def test_c287_fails_when_some_of_the_six_are_left_behind(corpus):
    assert verdict("MATPLOTLIB-C287", make_bundle(files=MIN_NUMPY_ALL[:2]),
                   corpus).verdict == "fail"


def test_c287_finds_no_target_when_the_minimum_is_not_raised(corpus):
    row = verdict("MATPLOTLIB-C287", make_bundle(files=[whole(AXES, "x = 1\n")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

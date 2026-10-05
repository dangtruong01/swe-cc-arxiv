"""Three cases per rule (docs/checker-authoring.md §9): one target that satisfies the pass
condition, one that violates it, and one input where the pre-condition finds nothing.

The third case is the one that catches a pre-condition written against the artefact the
rule demands instead of the antecedent that invokes it (§4.2). Do not skip it.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_commit, make_file

from compliance.core.models import Command
from compliance.core.registry import registered
from compliance.core.runner import run_rule

import compliance.rules.sympy.git_conventions  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def cmds(*commands_with_output):
    return tuple(
        Command(index=i, command=c[0], output=c[1] if len(c) > 1 else "")
        for i, c in enumerate(commands_with_output)
    )


PY_FILE = make_file("sympy/core/mod.py", [(1, "x = 1")])


# --- C012 create a contribution branch ---------------------------------------------


def test_c012_passes_when_a_branch_was_created(corpus):
    bundle = make_bundle(files=[PY_FILE], commands=cmds(("git checkout -b fix/point",)))
    assert verdict("SYMPY-C012", bundle, corpus).verdict == "pass"


def test_c012_fails_when_the_agent_changed_code_on_whatever_it_started_on(corpus):
    bundle = make_bundle(files=[PY_FILE], commands=cmds(("git add .",)))
    assert verdict("SYMPY-C012", bundle, corpus).verdict == "fail"


def test_c012_not_applicable_when_nothing_was_changed(corpus):
    row = verdict("SYMPY-C012", make_bundle(), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C013 do not commit to master --------------------------------------------------


def test_c013_passes_on_a_feature_branch(corpus):
    bundle = make_bundle(commits=[make_commit("fix: thing", branch="fix/thing")])
    assert verdict("SYMPY-C013", bundle, corpus).verdict == "pass"


def test_c013_fails_when_committed_on_master(corpus):
    bundle = make_bundle(commits=[make_commit("fix: thing", branch="master")])
    assert verdict("SYMPY-C013", bundle, corpus).verdict == "fail"


def test_c013_not_applicable_without_commits(corpus):
    assert verdict("SYMPY-C013", make_bundle(), corpus).verdict == "not_applicable"


def test_c013_unknown_branch_is_undetermined_never_a_violation(corpus):
    # Invariant 6: missing evidence must not be recorded as non-compliance.
    row = verdict("SYMPY-C013", make_bundle(commits=[make_commit("fix: x")]), corpus)
    assert (row.verdict, row.status, row.n_violating) == ("not_applicable", "parse_error", 0)


# --- C014 no git verbs while on master ---------------------------------------------


def test_c014_passes_when_the_verbs_ran_off_master(corpus):
    bundle = make_bundle(probe={"start_branch": "fix/x"}, commands=cmds(("git add .",)))
    assert verdict("SYMPY-C014", bundle, corpus).verdict == "pass"


def test_c014_fails_when_the_verbs_ran_on_master(corpus):
    bundle = make_bundle(probe={"start_branch": "master"}, commands=cmds(("git commit -m x",)))
    assert verdict("SYMPY-C014", bundle, corpus).verdict == "fail"


def test_c014_not_applicable_when_no_such_command_ran(corpus):
    bundle = make_bundle(probe={"start_branch": "master"}, commands=cmds(("ls -la",)))
    assert verdict("SYMPY-C014", bundle, corpus).verdict == "not_applicable"


def test_c014_tracks_a_branch_switch_partway_through(corpus):
    bundle = make_bundle(
        probe={"start_branch": "master"},
        commands=cmds(("git checkout -b fix/x",), ("git commit -m x",)),
    )
    assert verdict("SYMPY-C014", bundle, corpus).verdict == "pass"


# --- C021 no junk files ------------------------------------------------------------


def test_c021_passes_on_ordinary_source_files(corpus):
    assert verdict("SYMPY-C021", make_bundle(files=[PY_FILE]), corpus).verdict == "pass"


@pytest.mark.parametrize(
    "path", [".vscode/settings.json", "sympy/x.pyc", "notes.orig", "patch.txt", ".DS_Store"]
)
def test_c021_fails_on_junk(corpus, path):
    bundle = make_bundle(files=[make_file(path, [(1, "junk")])])
    assert verdict("SYMPY-C021", bundle, corpus).verdict == "fail"


def test_c021_fails_on_binary_files(corpus):
    bundle = make_bundle(files=[make_file("logo.png", is_binary=True, is_new=True)])
    assert verdict("SYMPY-C021", bundle, corpus).verdict == "fail"


def test_c021_not_applicable_with_an_empty_patch(corpus):
    assert verdict("SYMPY-C021", make_bundle(), corpus).verdict == "not_applicable"


# --- C023 summary length -----------------------------------------------------------


def test_c023_passes_at_the_limit(corpus):
    bundle = make_bundle(commits=[make_commit("x" * 71)])
    assert verdict("SYMPY-C023", bundle, corpus).verdict == "pass"


def test_c023_fails_one_character_over(corpus):
    row = verdict("SYMPY-C023", make_bundle(commits=[make_commit("x" * 72)]), corpus)
    assert row.verdict == "fail" and "72 chars" in row.notes


def test_c023_not_applicable_without_commits(corpus):
    assert verdict("SYMPY-C023", make_bundle(), corpus).verdict == "not_applicable"


# --- C024 body line length ---------------------------------------------------------


def test_c024_passes_on_short_body_lines(corpus):
    bundle = make_bundle(commits=[make_commit("summary\n\nA short body line.")])
    assert verdict("SYMPY-C024", bundle, corpus).verdict == "pass"


def test_c024_fails_one_character_over(corpus):
    bundle = make_bundle(commits=[make_commit("summary\n\n" + "x" * 79)])
    assert verdict("SYMPY-C024", bundle, corpus).verdict == "fail"


def test_c024_not_applicable_when_there_is_no_body(corpus):
    # The acceptance case: a one-line `git commit -m` has no body for the rule to attach
    # to. Returning pass here would invent compliance out of an absent artefact.
    row = verdict("SYMPY-C024", make_bundle(commits=[make_commit("summary only")]), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C025 blank line after summary -------------------------------------------------


def test_c025_passes_with_a_blank_separator(corpus):
    bundle = make_bundle(commits=[make_commit("summary\n\nbody")])
    assert verdict("SYMPY-C025", bundle, corpus).verdict == "pass"


def test_c025_fails_without_one(corpus):
    bundle = make_bundle(commits=[make_commit("summary\nbody")])
    assert verdict("SYMPY-C025", bundle, corpus).verdict == "fail"


def test_c025_not_applicable_when_there_is_nothing_to_separate(corpus):
    row = verdict("SYMPY-C025", make_bundle(commits=[make_commit("summary only")]), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C026 no trailing period -------------------------------------------------------


def test_c026_passes_without_a_period(corpus):
    bundle = make_bundle(commits=[make_commit("fix: correct the thing")])
    assert verdict("SYMPY-C026", bundle, corpus).verdict == "pass"


def test_c026_fails_with_one(corpus):
    bundle = make_bundle(commits=[make_commit("fix: correct the thing.")])
    assert verdict("SYMPY-C026", bundle, corpus).verdict == "fail"


def test_c026_not_applicable_without_commits(corpus):
    assert verdict("SYMPY-C026", make_bundle(), corpus).verdict == "not_applicable"


# --- C030 complete sentences -------------------------------------------------------


def test_c030_passes_on_a_well_formed_body(corpus):
    bundle = make_bundle(commits=[make_commit("summary\n\nThis fixes the calculation.")])
    assert verdict("SYMPY-C030", bundle, corpus).verdict == "pass"


def test_c030_fails_on_a_fragment(corpus):
    bundle = make_bundle(commits=[make_commit("summary\n\nfixed the calculation")])
    assert verdict("SYMPY-C030", bundle, corpus).verdict == "fail"


def test_c030_not_applicable_when_there_is_no_body(corpus):
    row = verdict("SYMPY-C030", make_bundle(commits=[make_commit("summary only")]), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


def test_c030_is_flagged_as_a_heuristic(corpus):
    bundle = make_bundle(commits=[make_commit("summary\n\nThis fixes it.")])
    assert verdict("SYMPY-C030", bundle, corpus).heuristic is True


# --- C034 co-author trailer form ---------------------------------------------------


def test_c034_passes_on_the_exact_trailer(corpus):
    commit = make_commit("summary\n\nBody.\n\nCo-authored-by: Ada L <ada@example.com>")
    assert verdict("SYMPY-C034", make_bundle(commits=[commit]), corpus).verdict == "pass"


def test_c034_fails_on_a_malformed_credit(corpus):
    commit = make_commit("summary\n\nCo-authored by: Ada L (no angle brackets)")
    assert verdict("SYMPY-C034", make_bundle(commits=[commit]), corpus).verdict == "fail"


def test_c034_not_applicable_when_no_co_author_is_credited(corpus):
    row = verdict("SYMPY-C034", make_bundle(commits=[make_commit("summary\n\nBody.")]), corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0)


# --- C040 do not edit AUTHORS ------------------------------------------------------


def test_c040_passes_when_authors_is_untouched(corpus):
    assert verdict("SYMPY-C040", make_bundle(files=[PY_FILE]), corpus).verdict == "pass"


def test_c040_fails_when_authors_is_edited(corpus):
    bundle = make_bundle(files=[make_file("AUTHORS", [(3, "Ada L <ada@example.com>")])])
    assert verdict("SYMPY-C040", bundle, corpus).verdict == "fail"


def test_c040_not_applicable_with_an_empty_patch(corpus):
    assert verdict("SYMPY-C040", make_bundle(), corpus).verdict == "not_applicable"


# --- C041 mailmap matches commit identity ------------------------------------------


def test_c041_passes_when_the_source_email_matches_the_committer(corpus):
    bundle = make_bundle(
        files=[make_file(".mailmap", [(9, "Ada L <ada@example.com> <ada@old.example.com>")])],
        commits=[make_commit("summary", author_name="Ada L", author_email="ada@old.example.com")],
    )
    assert verdict("SYMPY-C041", bundle, corpus).verdict == "pass"


def test_c041_fails_when_it_matches_nobody(corpus):
    bundle = make_bundle(
        files=[make_file(".mailmap", [(9, "Ada L <ada@example.com> <someone@else.com>")])],
        commits=[make_commit("summary", author_name="Ada L", author_email="ada@old.example.com")],
    )
    assert verdict("SYMPY-C041", bundle, corpus).verdict == "fail"


def test_c041_not_applicable_when_mailmap_was_not_edited(corpus):
    assert verdict("SYMPY-C041", make_bundle(files=[PY_FILE]), corpus).verdict == "not_applicable"


# --- C042 run mailmap_check --------------------------------------------------------

MAILMAP_EDIT = make_file(".mailmap", [(9, "Ada L <ada@example.com> <ada@old.example.com>")])
MAILMAP_OK = "No changes needed in .mailmap"


def test_c042_passes_when_the_check_reported_success(corpus):
    bundle = make_bundle(
        files=[MAILMAP_EDIT],
        commands=cmds(("python bin/mailmap_check.py", MAILMAP_OK)),
    )
    assert verdict("SYMPY-C042", bundle, corpus).verdict == "pass"


def test_c042_fails_when_the_check_never_ran(corpus):
    bundle = make_bundle(files=[MAILMAP_EDIT], commands=cmds(("git add .mailmap",)))
    assert verdict("SYMPY-C042", bundle, corpus).verdict == "fail"


def test_c042_not_applicable_when_mailmap_was_not_edited(corpus):
    bundle = make_bundle(files=[PY_FILE], commands=cmds(("python bin/mailmap_check.py", MAILMAP_OK)))
    assert verdict("SYMPY-C042", bundle, corpus).verdict == "not_applicable"


# --- C043 stage and commit .mailmap after the check ---------------------------------


def test_c043_passes_when_staged_and_committed_properly(corpus):
    bundle = make_bundle(
        files=[MAILMAP_EDIT],
        commands=cmds(("python bin/mailmap_check.py", MAILMAP_OK), ("git add .mailmap",)),
        commits=[make_commit("author: add Ada L to .mailmap")],
    )
    assert verdict("SYMPY-C043", bundle, corpus).verdict == "pass"


def test_c043_fails_when_mailmap_was_never_staged(corpus):
    bundle = make_bundle(
        files=[MAILMAP_EDIT],
        commands=cmds(("python bin/mailmap_check.py", MAILMAP_OK)),
        commits=[make_commit("author: add Ada L to .mailmap")],
    )
    assert verdict("SYMPY-C043", bundle, corpus).verdict == "fail"


def test_c043_not_applicable_before_the_check_succeeds(corpus):
    bundle = make_bundle(files=[MAILMAP_EDIT], commands=cmds(("git add .mailmap",)))
    assert verdict("SYMPY-C043", bundle, corpus).verdict == "not_applicable"


# --- coverage guard ----------------------------------------------------------------


def test_every_registered_rule_has_all_three_cases_here():
    """A rule added without its not_applicable case is exactly the §4.2 bug."""
    source = __import__("pathlib").Path(__file__).read_text()
    # Scoped to this file's own category. Unscoped, the test passed or failed on module
    # import order -- whichever rule packs happened to be registered first.
    # Scoped to this file's own category AND pack. Unscoped by category, this passed or
    # failed on module import order; unscoped by pack, it demands that every project's git
    # rules be tested in SymPy's test file. The cross-pack version of this guard lives in
    # tests/test_registry.py.
    for rule_id in [r.id for r in RULES.values()
                    if r.category == "Git and commit conventions" and r.id.startswith("SYMPY-")]:
        short = rule_id.split("-")[-1].lower()  # SYMPY-C023 -> c023
        assert f"test_{short}_" in source, f"{rule_id} has no tests in this file"
        assert f"def test_{short}_not_applicable" in source, f"{rule_id} has no not_applicable case"

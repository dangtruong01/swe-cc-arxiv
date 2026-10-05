"""Satisfying and violating cases for the Django rules that had only a not-applicable case.

Until this file, these 23 rules were covered only by the empty-contribution test in
``test_django_language_style.py``. Each rule below gets the outcomes its checker can reach:
a pass and a fail for the ordinary rules, and a fail plus a withheld case (or a withheld case
alone) for the four that need a suite or docs toolchain run (C076, C078, C103, C104).
"""

from __future__ import annotations

import textwrap

import pytest
from conftest import make_bundle, make_commit, make_file

from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.django.documentation  # noqa: F401  (registers the rules)
import compliance.rules.django.git_conventions  # noqa: F401
import compliance.rules.django.pr_metadata  # noqa: F401
import compliance.rules.django.tests  # noqa: F401

RULES = {r.id: r for r in registered()}

SOURCE = "django/utils/text.py"
NEW_MODULE = "django/utils/slugs.py"
TEST = "tests/utils_tests/test_text.py"
DOC = "docs/ref/utils.txt"
NOTES = "docs/releases/6.0.txt"
IMAGE = "docs/_images/admin-actions.png"

PLAIN_CODE = """
def truncate(text, n):
    return text[:n]
"""
NEW_FEATURE = """
def slugify_unicode(value):
    return value.lower()
"""
TEST_CODE = """
from django.test import SimpleTestCase


class TextTests(SimpleTestCase):
    def test_truncate(self):
        self.assertEqual(truncate("abc", 2), "ab")
"""


@pytest.fixture(scope="module")
def corpus():
    """Django's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("django"))


def changed(path, source):
    """A file the agent wrote in full, carrying its post-patch text."""
    source = textwrap.dedent(source).lstrip("\n")
    lines = source.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    added = [(n, lines[n - 1]) for n in range(1, len(lines) + 1)]
    return make_file(path, added, head_text=source, is_new=True)


def bundle(*files, commands=(), commits=(), **overrides):
    return make_bundle(
        files=list(files),
        commands=tuple(Command(index=i, command=c[0], output=c[1] if len(c) > 1 else "")
                       for i, c in enumerate(commands)),
        commits=list(commits),
        **overrides,
    )


def verdict(rule_id, b, corpus):
    return run_rule(b, RULES[rule_id], corpus)


def assert_passes(rule_id, b, corpus):
    row = verdict(rule_id, b, corpus)
    assert row.n_targets > 0, f"{rule_id}: vacuous pass, the pre-condition found nothing"
    assert row.verdict == "pass", f"{rule_id}: got {row.verdict} -- {row.notes}"


def assert_fails(rule_id, b, corpus, phrase):
    row = verdict(rule_id, b, corpus)
    assert row.verdict == "fail", f"{rule_id}: got {row.verdict} -- {row.notes}"
    assert phrase in row.notes, f"{rule_id}: {phrase!r} not in {row.notes!r}"


def assert_withheld(rule_id, b, corpus):
    row = verdict(rule_id, b, corpus)
    assert row.n_targets > 0, f"{rule_id}: pre-condition did not fire"
    assert (row.verdict, row.status) == ("not_applicable", "tool_missing"), row.notes


def doc(body):
    return changed(DOC, body)


# --- git and pull-request metadata --------------------------------------------------------


def test_c044_passes_on_a_plain_push(corpus):
    assert_passes("DJANGO-C044", bundle(commands=[("git push origin ticket-123",)]), corpus)


def test_c044_fails_on_a_force_push(corpus):
    b = bundle(commands=[("git push --force origin main",)])
    assert_fails("DJANGO-C044", b, corpus, "force push")


def test_c046_passes_on_a_past_tense_subject_with_a_period(corpus):
    b = bundle(commits=[make_commit("Fixed #123 -- Added truncation to Truncator.")])
    assert_passes("DJANGO-C046", b, corpus)


def test_c046_fails_on_an_imperative_subject_without_a_period(corpus):
    b = bundle(commits=[make_commit("Add truncation to Truncator")])
    assert_fails("DJANGO-C046", b, corpus, "does not end with a period")


def test_c052_passes_when_a_commit_closes_the_ticket(corpus):
    b = bundle(commits=[make_commit("Fixed #34567 -- Added truncation to Truncator.")])
    assert_passes("DJANGO-C052", b, corpus)


def test_c052_fails_when_no_commit_closes_the_ticket(corpus):
    b = bundle(commits=[make_commit("Added truncation to Truncator.")])
    assert_fails("DJANGO-C052", b, corpus, "Fixed #xxxxx")


def test_c053_passes_when_another_ticket_is_introduced_by_refs(corpus):
    b = bundle(commits=[make_commit("Fixed #100 -- Added truncation.\n\nRefs #200.")])
    assert_passes("DJANGO-C053", b, corpus)


def test_c053_fails_when_another_ticket_is_named_without_refs(corpus):
    b = bundle(commits=[make_commit("Fixed #100 -- Added truncation.\n\nSee #200 for context.")])
    assert_fails("DJANGO-C053", b, corpus, "without `Refs`")


def test_c055_passes_when_the_docs_change_with_the_code(corpus):
    b = bundle(changed(SOURCE, PLAIN_CODE), doc("Truncation\n==========\n\nText.\n"))
    assert_passes("DJANGO-C055", b, corpus)


def test_c055_fails_when_only_library_code_changes(corpus):
    assert_fails("DJANGO-C055", bundle(changed(SOURCE, PLAIN_CODE)), corpus,
                 "touches no documentation")


def test_c079_passes_when_a_release_note_is_added(corpus):
    b = bundle(changed(NEW_MODULE, NEW_FEATURE), changed(NOTES, "* Added ``slugify_unicode()``.\n"))
    assert_passes("DJANGO-C079", b, corpus)


def test_c079_fails_without_a_release_note(corpus):
    assert_fails("DJANGO-C079", bundle(changed(NEW_MODULE, NEW_FEATURE)), corpus,
                 "no `docs/releases/A.B.txt` entry")


# --- tests: fail when absent, withheld when present ---------------------------------------


def test_c076_fails_when_a_fix_ships_no_test(corpus):
    assert_fails("DJANGO-C076", bundle(changed(SOURCE, PLAIN_CODE)), corpus, "adds no test")


def test_c076_is_withheld_when_a_test_is_present(corpus):
    assert_withheld("DJANGO-C076", bundle(changed(SOURCE, PLAIN_CODE), changed(TEST, TEST_CODE)),
                    corpus)


def test_c078_fails_when_new_code_ships_no_test(corpus):
    assert_fails("DJANGO-C078", bundle(changed(NEW_MODULE, NEW_FEATURE)), corpus, "no test")


def test_c078_is_withheld_when_a_test_is_present(corpus):
    b = bundle(changed(NEW_MODULE, NEW_FEATURE), changed(TEST, TEST_CODE))
    assert_withheld("DJANGO-C078", b, corpus)


# --- documentation ------------------------------------------------------------------------


def test_c074_passes_when_the_docs_build_cleanly(corpus):
    b = bundle(doc("Text\n====\n\nBody.\n"), commands=[("cd docs && make html", "build succeeded.")])
    assert_passes("DJANGO-C074", b, corpus)


def test_c074_fails_when_the_docs_are_never_built(corpus):
    assert_fails("DJANGO-C074", bundle(doc("Text\n====\n\nBody.\n")), corpus, "never run")


def test_c080_passes_with_a_version_directive(corpus):
    b = bundle(changed(NEW_MODULE, NEW_FEATURE),
               doc(".. function:: slugify_unicode(value)\n\n    .. versionadded:: 6.0\n"))
    assert_passes("DJANGO-C080", b, corpus)


def test_c080_fails_without_a_version_directive(corpus):
    assert_fails("DJANGO-C080", bundle(changed(NEW_MODULE, NEW_FEATURE)), corpus,
                 "no versionadded/versionchanged directive")


def test_c103_is_withheld_because_the_docs_checks_were_not_run(corpus):
    assert_withheld("DJANGO-C103", bundle(doc("Text\n====\n\nBody.\n")), corpus)


def test_c104_is_withheld_because_blacken_docs_was_not_run(corpus):
    body = "Example\n=======\n\n.. code-block:: python\n\n    x = {'a': 1}\n"
    assert_withheld("DJANGO-C104", bundle(doc(body)), corpus)


def test_c106_passes_on_a_gender_neutral_pronoun(corpus):
    assert_passes("DJANGO-C106", bundle(doc("A developer should check their settings.\n")),
                  corpus)


def test_c106_fails_on_a_gendered_pronoun(corpus):
    assert_fails("DJANGO-C106", bundle(doc("A developer should check his settings.\n")),
                 corpus, "gendered pronoun")


def test_c108_passes_on_correct_capitalization(corpus):
    assert_passes("DJANGO-C108", bundle(doc("Django renders the template with Python.\n")),
                  corpus)


def test_c108_fails_on_a_lowercase_django(corpus):
    assert_fails("DJANGO-C108", bundle(doc("Then django renders the template.\n")), corpus,
                 "should be 'Django'")


def test_c109_passes_on_american_spelling(corpus):
    assert_passes("DJANGO-C109", bundle(doc("You can customize the output.\n")), corpus)


def test_c109_fails_on_british_spelling(corpus):
    assert_fails("DJANGO-C109", bundle(doc("You can customise the output.\n")), corpus,
                 "British `-ise` spelling")


def test_c110_passes_on_a_sentence_case_heading(corpus):
    assert_passes("DJANGO-C110", bundle(doc("Using the cache framework\n"
                                            "=========================\n\nText.\n")), corpus)


def test_c110_fails_on_a_title_case_heading(corpus):
    assert_fails("DJANGO-C110", bundle(doc("Using The Cache Framework\n"
                                           "=========================\n\nText.\n")),
                 corpus, "title-case heading")


def test_c115_passes_on_a_heading_one_level_down(corpus):
    body = "Caching\n=======\n\nText.\n\nLocal memory\n------------\n\nText.\n"
    assert_passes("DJANGO-C115", bundle(doc(body)), corpus)


def test_c115_fails_on_an_underline_outside_the_hierarchy(corpus):
    body = "Caching\n=======\n\nText.\n\nLocal memory\n^^^^^^^^^^^^\n\nText.\n"
    assert_fails("DJANGO-C115", bundle(doc(body)), corpus, "not one of Django's")


def test_c116_passes_on_an_rfc_role(corpus):
    assert_passes("DJANGO-C116", bundle(doc("See :rfc:`9110` for the semantics.\n")), corpus)


def test_c116_fails_on_a_plain_text_rfc(corpus):
    assert_fails("DJANGO-C116", bundle(doc("See RFC 9110 for the semantics.\n")), corpus,
                 "written as plain text")


def test_c117_passes_on_an_envvar_role(corpus):
    assert_passes("DJANGO-C117", bundle(doc("Set :envvar:`DJANGO_SETTINGS_MODULE` first.\n")),
                  corpus)


def test_c117_fails_on_a_bare_environment_variable(corpus):
    assert_fails("DJANGO-C117", bundle(doc("Set DJANGO_SETTINGS_MODULE first.\n")), corpus,
                 ":envvar: role")


def test_c118_passes_on_a_four_space_description(corpus):
    body = ".. function:: truncate(text, n)\n\n    Returns the first n characters.\n"
    assert_passes("DJANGO-C118", bundle(doc(body)), corpus)


def test_c118_fails_on_a_misindented_description(corpus):
    body = ".. function:: truncate(text, n)\n\n  Returns the first n characters.\n"
    assert_fails("DJANGO-C118", bundle(doc(body)), corpus, "not 4")


def test_c123_passes_when_versionchanged_closes_its_section(corpus):
    body = ("Truncation\n==========\n\nTruncates text.\n\n"
            ".. versionchanged:: 6.0\n\n    Added the ``n`` argument.\n")
    assert_passes("DJANGO-C123", bundle(doc(body)), corpus)


def test_c123_fails_when_prose_follows_versionchanged(corpus):
    body = ("Truncation\n==========\n\n.. versionchanged:: 6.0\n\n"
            "    Added the ``n`` argument.\n\nTruncates text.\n")
    assert_fails("DJANGO-C123", bundle(doc(body)), corpus, "it belongs at the end")


def test_c125_passes_when_the_image_was_compressed(corpus):
    b = bundle(make_file(IMAGE, [], is_new=True),
               commands=[(f"optipng -o7 {IMAGE}",), (f"advpng -z -4 {IMAGE}",)])
    assert_passes("DJANGO-C125", b, corpus)


def test_c125_fails_when_the_image_was_not_compressed(corpus):
    assert_fails("DJANGO-C125", bundle(make_file(IMAGE, [], is_new=True)), corpus,
                 "without running optipng and advpng")


def test_c143_passes_with_a_blank_line_after_the_directive(corpus):
    body = ".. versionadded:: 6.0\n\n    Added ``truncate()``.\n"
    assert_passes("DJANGO-C143", bundle(doc(body)), corpus)


def test_c143_fails_without_a_blank_line_after_the_directive(corpus):
    body = ".. versionadded:: 6.0\n    Added ``truncate()``.\n"
    assert_fails("DJANGO-C143", bundle(doc(body)), corpus, "with no blank line between")

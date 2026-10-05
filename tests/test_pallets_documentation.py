"""Three cases per rule (spec §9): satisfied, violated, and an input where the
pre-condition finds nothing.

Two no-target cases carry a decision rather than an edge case. C041's pins the tutorial
exemption -- the same sentence that violates it elsewhere finds no target under
`docs/tutorial/`. C050's pins the §7.5 resolution: its ban on issue references "anywhere
in the codebase" exempts `CHANGES.rst`, which is where C086 and C053 require the agent to
write.

Every prose rule here grades one-sidedly, so its satisfying case proves only that the
wrong form is absent. That is stated in each predicate's docstring and is what the
`heuristic=True` flag on all ten of them declares.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pallets.documentation  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


def py_file(path, source, *, is_new=False, owned=None, removed=()):
    lines = source.split("\n")
    numbers = range(1, len(lines) + 1) if owned is None else owned
    return make_file(path, [(n, lines[n - 1]) for n in numbers],
                     head_text=source, is_new=is_new, removed_lines=tuple(removed))


def doc_file(path, source, *, owned=None, removed=()):
    return py_file(path, source, owned=owned, removed=removed)


SOURCE = make_file("src/flask/app.py", [(10, "    return None")])

RST_DOCSTRING = (
    "def create_app():\n"
    '    """Create the application.\n'
    "\n"
    "    :param name: the import name.\n"
    '    """\n'
    "    return None\n"
)
MARKDOWN_DOCSTRING = (
    "def create_app():\n"
    '    """Create the application.\n'
    "\n"
    "    See the [quickstart](https://example.com) for details.\n"
    '    """\n'
    "    return None\n"
)
NO_DOCSTRING = "def create_app():\n    return None\n"


@pytest.fixture(scope="module")
def corpus():
    """pallets' corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pallets"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C032 docstrings are reStructuredText ----------------------------------------------


def test_c032_passes_on_a_docstring_written_in_rst(corpus):
    bundle = make_bundle(files=[py_file("src/flask/app.py", RST_DOCSTRING)])
    assert verdict("PALLETS-C032", bundle, corpus).verdict == "pass"


def test_c032_fails_on_a_docstring_carrying_markdown(corpus):
    bundle = make_bundle(files=[py_file("src/flask/app.py", MARKDOWN_DOCSTRING)])
    row = verdict("PALLETS-C032", bundle, corpus)
    assert row.verdict == "fail" and "Markdown" in row.notes


def test_c032_finds_no_target_when_the_edited_code_has_no_docstring(corpus):
    bundle = make_bundle(files=[py_file("src/flask/app.py", NO_DOCSTRING)])
    row = verdict("PALLETS-C032", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C037 a typo is fixed everywhere it occurs -----------------------------------------


TYPO_FIXED = (
    "The client will receive the response.\n"
    "Another sentence entirely.\n"
)
TYPO_ELSEWHERE = (
    "The API reference.\n"
    "The server will recieve the request.\n"
    "An unrelated edited line.\n"
)


def test_c037_passes_when_the_old_spelling_survives_nowhere(corpus):
    changed = doc_file("docs/quickstart.rst", TYPO_FIXED, owned=[1],
                       removed=["The client will recieve the response."])
    assert verdict("PALLETS-C037", make_bundle(files=[changed]),
                   corpus).verdict == "pass"


def test_c037_fails_when_the_same_typo_survives_in_another_changed_page(corpus):
    changed = doc_file("docs/quickstart.rst", TYPO_FIXED, owned=[1],
                       removed=["The client will recieve the response."])
    other = doc_file("docs/api.rst", TYPO_ELSEWHERE, owned=[3])
    row = verdict("PALLETS-C037", make_bundle(files=[changed, other]), corpus)
    assert row.verdict == "fail" and "docs/api.rst:2" in row.notes


def test_c037_finds_no_target_when_the_change_adds_new_prose(corpus):
    """The antecedent is a word swapped for a near-miss of it, not any documentation edit."""
    changed = doc_file("docs/quickstart.rst", "A brand new sentence about routing.\n",
                       owned=[1])
    row = verdict("PALLETS-C037", make_bundle(files=[changed]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C038 no drive-by typo fixes in code comments --------------------------------------


COMMENT_TYPO = (
    "def create_app():\n"
    "    # the response is received here\n"
    "    return None\n"
)


def test_c038_passes_when_the_code_around_the_comment_is_also_edited(corpus):
    changed = py_file("src/flask/app.py", COMMENT_TYPO, owned=[2, 3],
                      removed=["    # the response is recieved here"])
    assert verdict("PALLETS-C038", make_bundle(files=[changed]),
                   corpus).verdict == "pass"


def test_c038_fails_on_a_comment_only_typo_fix(corpus):
    changed = py_file("src/flask/app.py", COMMENT_TYPO, owned=[2],
                      removed=["    # the response is recieved here"])
    row = verdict("PALLETS-C038", make_bundle(files=[changed]), corpus)
    assert row.verdict == "fail" and "built docs never show" in row.notes


def test_c038_finds_no_target_when_no_comment_was_corrected(corpus):
    changed = py_file("src/flask/app.py", COMMENT_TYPO, owned=[3])
    row = verdict("PALLETS-C038", make_bundle(files=[changed]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C041 no "you" or "we" outside tutorials -------------------------------------------


IMPERSONAL = "The application object is created by calling the class.\n"
SECOND_PERSON = "You can create the application by calling the class.\n"


def test_c041_passes_on_impersonal_prose(corpus):
    bundle = make_bundle(files=[doc_file("docs/quickstart.rst", IMPERSONAL)])
    assert verdict("PALLETS-C041", bundle, corpus).verdict == "pass"


def test_c041_fails_when_the_page_addresses_the_reader(corpus):
    bundle = make_bundle(files=[doc_file("docs/quickstart.rst", SECOND_PERSON)])
    row = verdict("PALLETS-C041", bundle, corpus)
    assert row.verdict == "fail" and "You" in row.notes


def test_c041_finds_no_target_for_the_same_sentence_in_a_tutorial(corpus):
    """The exemption the sentence names, pinned rather than remembered."""
    bundle = make_bundle(files=[doc_file("docs/tutorial/index.rst", SECOND_PERSON)])
    row = verdict("PALLETS-C041", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C044 documentation is written in English ------------------------------------------


def test_c044_passes_on_english_prose(corpus):
    bundle = make_bundle(files=[doc_file("docs/quickstart.rst", IMPERSONAL)])
    assert verdict("PALLETS-C044", bundle, corpus).verdict == "pass"


def test_c044_fails_on_prose_in_another_script(corpus):
    bundle = make_bundle(files=[doc_file("docs/quickstart.rst",
                                         "Приложение создаётся вызовом класса.\n")])
    row = verdict("PALLETS-C044", bundle, corpus)
    assert row.verdict == "fail" and "not written in English" in row.notes


def test_c044_finds_no_target_when_the_page_gained_only_markup(corpus):
    bundle = make_bundle(files=[doc_file("docs/quickstart.rst",
                                         ".. note:: See the API reference.\n")])
    row = verdict("PALLETS-C044", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C046 the serial comma in documentation prose --------------------------------------


def test_c046_passes_on_a_list_with_the_serial_comma(corpus):
    bundle = make_bundle(files=[doc_file(
        "docs/quickstart.rst",
        "Flask supports routing, templating, and sessions.\n")])
    assert verdict("PALLETS-C046", bundle, corpus).verdict == "pass"


def test_c046_fails_on_a_list_without_it(corpus):
    bundle = make_bundle(files=[doc_file(
        "docs/quickstart.rst",
        "Flask supports routing, templating and sessions.\n")])
    row = verdict("PALLETS-C046", bundle, corpus)
    assert row.verdict == "fail" and "serial comma" in row.notes


def test_c046_finds_no_target_on_a_sentence_that_lists_nothing(corpus):
    bundle = make_bundle(files=[doc_file("docs/quickstart.rst", IMPERSONAL)])
    row = verdict("PALLETS-C046", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C047 no consistency sweep across existing docs ------------------------------------


def _sweep_page(name, fixed, typo):
    return doc_file(f"docs/{name}.rst", fixed + "An untouched sentence.\n",
                    owned=[1], removed=[typo])


def test_c047_passes_when_the_documentation_change_adds_content(corpus):
    pages = [doc_file(f"docs/{name}.rst", "A newly written paragraph about routing.\n")
             for name in ("quickstart", "api", "config")]
    assert verdict("PALLETS-C047", make_bundle(files=pages), corpus).verdict == "pass"


def test_c047_fails_on_a_like_for_like_sweep_across_three_pages(corpus):
    pages = [_sweep_page(name, "The client will receive the response.\n",
                         "The client will recieve the response.")
             for name in ("quickstart", "api", "config")]
    row = verdict("PALLETS-C047", make_bundle(files=pages), corpus)
    assert row.verdict == "fail" and "consistency sweep" in row.notes


def test_c047_finds_no_target_for_a_contribution_touching_no_documentation(corpus):
    row = verdict("PALLETS-C047", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C050 no issue references anywhere in the codebase ---------------------------------


def test_c050_passes_when_no_line_references_an_issue(corpus):
    bundle = make_bundle(files=[py_file("src/flask/app.py", NO_DOCSTRING)])
    assert verdict("PALLETS-C050", bundle, corpus).verdict == "pass"


def test_c050_fails_on_an_issue_number_in_a_code_comment(corpus):
    source = "def create_app():\n    # workaround for #1234\n    return None\n"
    bundle = make_bundle(files=[py_file("src/flask/app.py", source)])
    row = verdict("PALLETS-C050", bundle, corpus)
    assert row.verdict == "fail" and "#1234" in row.notes


def test_c050_finds_no_target_in_the_changelog_which_c086_requires(corpus):
    """The §7.5 resolution: the sentence names the changelog as its own exception, and
    C086 and C053 require the agent to write there."""
    entry = make_file("CHANGES.rst", [(7, "-   Fix routing. :issue:`1234`")])
    row = verdict("PALLETS-C050", make_bundle(files=[entry]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C085 documentation updated with the change ----------------------------------------


def test_c085_passes_when_a_page_changes_with_the_code(corpus):
    bundle = make_bundle(files=[SOURCE, doc_file("docs/quickstart.rst", IMPERSONAL)])
    assert verdict("PALLETS-C085", bundle, corpus).verdict == "pass"


def test_c085_fails_when_the_code_changes_alone(corpus):
    row = verdict("PALLETS-C085", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "fail" and "no docstring" in row.notes


def test_c085_finds_no_target_for_a_documentation_only_contribution(corpus):
    bundle = make_bundle(files=[doc_file("docs/quickstart.rst", IMPERSONAL)])
    row = verdict("PALLETS-C085", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C088 changed behaviour carries .. versionchanged:: --------------------------------


CHANGED_WITH_DIRECTIVE = (
    "class Flask:\n"
    "    def run(self):\n"
    '        """Run the development server.\n'
    "\n"
    "        .. versionchanged:: 3.1\n"
    "            The server now returns None.\n"
    '        """\n'
    "        return None\n"
)
CHANGED_WITHOUT_DIRECTIVE = (
    "class Flask:\n"
    "    def run(self):\n"
    '        """Run the development server."""\n'
    "        return None\n"
)
PRIVATE_CHANGE = (
    "class Flask:\n"
    "    def _run(self):\n"
    '        """Run the development server."""\n'
    "        return None\n"
)


def test_c088_passes_when_the_docstring_gains_the_directive(corpus):
    changed = py_file("src/flask/app.py", CHANGED_WITH_DIRECTIVE, owned=[5, 6, 8])
    assert verdict("PALLETS-C088", make_bundle(files=[changed]),
                   corpus).verdict == "pass"


def test_c088_fails_when_a_public_method_changes_without_one(corpus):
    changed = py_file("src/flask/app.py", CHANGED_WITHOUT_DIRECTIVE, owned=[4])
    row = verdict("PALLETS-C088", make_bundle(files=[changed]), corpus)
    assert row.verdict == "fail" and "versionchanged" in row.notes


def test_c088_finds_no_target_when_only_a_private_helper_changed(corpus):
    changed = py_file("src/flask/app.py", PRIVATE_CHANGE, owned=[4])
    row = verdict("PALLETS-C088", make_bundle(files=[changed]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

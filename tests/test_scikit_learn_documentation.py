"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

Two shapes recur. The docstring rules select a *type line* or a *section*, so their
no-target case is a docstring that carries neither -- which is what keeps them from
grading every docstring in the patch against a convention it never invoked. The
user-guide rules select a page under `doc/`, and one of them is pinned explicitly: a
changelog fragment under `doc/whats_new/` must find no target, because a changelog is not
documentation and C048 is the rule that asks for it (§7.5).
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.scikit_learn.documentation  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


@pytest.fixture(scope="module")
def corpus():
    """scikit-learn's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("scikit-learn"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def module_with(text, path="sklearn/svm/_base.py", new=True):
    lines = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text, is_new=new)


def documented(*doc_lines, signature="def fit(self, X, y=None):",
               path="sklearn/svm/_base.py"):
    """A module holding one documented definition, built from its docstring lines."""
    body = "\n".join(f"    {line}".rstrip() for line in doc_lines)
    text = f'{signature}\n    """Summary line.\n\n{body}\n    """\n    return self\n'
    return module_with(text, path)


def params(*entry_lines):
    return documented("Parameters", "----------", *entry_lines)


def page(*lines, path="doc/modules/svm.rst", new=True):
    text = "\n".join(lines)
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text, is_new=new)


NEW_FEATURE = module_with("def spectral_biclustering(X):\n"
                          '    """Cluster X."""\n'
                          "    return X\n",
                          path="sklearn/cluster/_bicluster.py")
UNDOCUMENTED_FEATURE = module_with("def spectral_biclustering(X):\n    return X\n",
                                   path="sklearn/cluster/_bicluster.py")
UNCHANGED_SOURCE = make_file("sklearn/svm/_base.py", [(1, "x = 1")])


# --- C036 a new feature has narrative user-guide documentation -------------------------


def test_c036_passes_when_a_user_guide_page_gains_a_snippet(corpus):
    guide = page("Biclustering", "============", "", "    >>> from sklearn import cluster")
    assert verdict("SCIKIT-LEARN-C036", make_bundle(files=[NEW_FEATURE, guide]),
                   corpus).verdict == "pass"


def test_c036_fails_when_the_feature_is_undocumented(corpus):
    assert verdict("SCIKIT-LEARN-C036", make_bundle(files=[NEW_FEATURE]),
                   corpus).verdict == "fail"


def test_c036_finds_no_target_without_a_new_public_definition(corpus):
    row = verdict("SCIKIT-LEARN-C036", make_bundle(files=[UNCHANGED_SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C038 the user guide states complexity and scalability ----------------------------


def test_c038_passes_when_both_are_stated(corpus):
    guide = page("Biclustering", "============", "",
                 "The complexity is O(n log n) and it scales to 100000 samples.")
    assert verdict("SCIKIT-LEARN-C038", make_bundle(files=[NEW_FEATURE, guide]),
                   corpus).verdict == "pass"


def test_c038_fails_when_neither_is_stated(corpus):
    guide = page("Biclustering", "============", "", "It groups rows and columns.")
    assert verdict("SCIKIT-LEARN-C038", make_bundle(files=[NEW_FEATURE, guide]),
                   corpus).verdict == "fail"


def test_c038_finds_no_target_when_no_user_guide_page_was_written(corpus):
    """The missing page is C036's finding, not a missing complexity statement."""
    row = verdict("SCIKIT-LEARN-C038", make_bundle(files=[NEW_FEATURE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c038_finds_no_target_for_a_changelog_fragment(corpus):
    """A changelog is not documentation -- C048 is the rule that asks for it."""
    fragment = page("- Added biclustering.",
                    path="doc/whats_new/upcoming_changes/sklearn.cluster/1.feature.rst")
    row = verdict("SCIKIT-LEARN-C038", make_bundle(files=[NEW_FEATURE, fragment]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C039 a new feature has a gallery example -----------------------------------------


def test_c039_passes_when_an_example_is_added(corpus):
    example = module_with("import sklearn\n", path="examples/cluster/plot_bicluster.py")
    assert verdict("SCIKIT-LEARN-C039", make_bundle(files=[NEW_FEATURE, example]),
                   corpus).verdict == "pass"


def test_c039_fails_without_one(corpus):
    assert verdict("SCIKIT-LEARN-C039", make_bundle(files=[NEW_FEATURE]),
                   corpus).verdict == "fail"


def test_c039_finds_no_target_without_a_new_public_definition(corpus):
    row = verdict("SCIKIT-LEARN-C039", make_bundle(files=[UNCHANGED_SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C060 API documentation lives beside the code -------------------------------------


def test_c060_passes_when_the_new_definition_has_a_docstring(corpus):
    assert verdict("SCIKIT-LEARN-C060", make_bundle(files=[NEW_FEATURE]),
                   corpus).verdict == "pass"


def test_c060_fails_when_it_has_none(corpus):
    assert verdict("SCIKIT-LEARN-C060", make_bundle(files=[UNDOCUMENTED_FEATURE]),
                   corpus).verdict == "fail"


def test_c060_finds_no_target_for_a_private_helper(corpus):
    private = module_with("def _helper(X):\n    return X\n",
                          path="sklearn/cluster/_bicluster.py")
    row = verdict("SCIKIT-LEARN-C060", make_bundle(files=[private]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C062 gallery examples live under examples/ ---------------------------------------


def test_c062_passes_for_an_example_in_the_gallery(corpus):
    example = module_with("# %%\nimport sklearn\n",
                          path="examples/cluster/plot_bicluster.py")
    assert verdict("SCIKIT-LEARN-C062", make_bundle(files=[example]),
                   corpus).verdict == "pass"


def test_c062_fails_for_one_written_elsewhere(corpus):
    example = module_with("# %%\nimport sklearn\n",
                          path="sklearn/cluster/plot_bicluster.py")
    assert verdict("SCIKIT-LEARN-C062", make_bundle(files=[example]),
                   corpus).verdict == "fail"


def test_c062_finds_no_target_for_an_ordinary_module(corpus):
    row = verdict("SCIKIT-LEARN-C062", make_bundle(files=[NEW_FEATURE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C064 docstring sections are in the stated order ----------------------------------


def test_c064_passes_on_the_stated_order(corpus):
    doc = documented("Parameters", "----------", "X : ndarray", "    The data.", "",
                     "Returns", "-------", "self : object", "    The estimator.")
    assert verdict("SCIKIT-LEARN-C064", make_bundle(files=[doc]),
                   corpus).verdict == "pass"


def test_c064_fails_when_returns_precedes_parameters(corpus):
    doc = documented("Returns", "-------", "self : object", "    The estimator.", "",
                     "Parameters", "----------", "X : ndarray", "    The data.")
    assert verdict("SCIKIT-LEARN-C064", make_bundle(files=[doc]),
                   corpus).verdict == "fail"


def test_c064_finds_no_target_on_a_single_section(corpus):
    doc = documented("Parameters", "----------", "X : ndarray", "    The data.")
    row = verdict("SCIKIT-LEARN-C064", make_bundle(files=[doc]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C065 parameter types use Python basic names --------------------------------------


def test_c065_passes_on_bool(corpus):
    bundle = make_bundle(files=[params("copy : bool, default=True", "    Copy X.")])
    assert verdict("SCIKIT-LEARN-C065", bundle, corpus).verdict == "pass"


def test_c065_fails_on_boolean(corpus):
    bundle = make_bundle(files=[params("copy : boolean, default=True", "    Copy X.")])
    assert verdict("SCIKIT-LEARN-C065", bundle, corpus).verdict == "fail"


def test_c065_finds_no_target_without_a_parameters_section(corpus):
    row = verdict("SCIKIT-LEARN-C065",
                  make_bundle(files=[documented("Just prose.")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C066 array shapes are parenthesised ----------------------------------------------


def test_c066_passes_on_a_parenthesised_shape(corpus):
    bundle = make_bundle(files=[params("X : ndarray of shape (n_samples, n_features)",
                                       "    The data.")])
    assert verdict("SCIKIT-LEARN-C066", bundle, corpus).verdict == "pass"


def test_c066_fails_without_parentheses(corpus):
    bundle = make_bundle(files=[params("X : ndarray of shape n_samples x n_features",
                                       "    The data.")])
    assert verdict("SCIKIT-LEARN-C066", bundle, corpus).verdict == "fail"


def test_c066_finds_no_target_when_no_shape_is_given(corpus):
    bundle = make_bundle(files=[params("copy : bool", "    Copy X.")])
    row = verdict("SCIKIT-LEARN-C066", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C067 string options are a brace-enclosed set -------------------------------------


def test_c067_passes_on_a_brace_set(corpus):
    bundle = make_bundle(files=[params("loss : {'log', 'squared'}, default='log'",
                                       "    The loss.")])
    assert verdict("SCIKIT-LEARN-C067", bundle, corpus).verdict == "pass"


def test_c067_fails_on_a_bare_list_of_options(corpus):
    bundle = make_bundle(files=[params("loss : 'log' or 'squared'", "    The loss.")])
    assert verdict("SCIKIT-LEARN-C067", bundle, corpus).verdict == "fail"


def test_c067_finds_no_target_on_a_single_option(corpus):
    bundle = make_bundle(files=[params("loss : str", "    The loss.")])
    row = verdict("SCIKIT-LEARN-C067", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C069 frame-like parameters are called dataframes ---------------------------------


def test_c069_passes_when_the_type_says_dataframe(corpus):
    bundle = make_bundle(files=[params("X : dataframe of shape (n_samples, n_features)",
                                       "    Uses the column names.")])
    assert verdict("SCIKIT-LEARN-C069", bundle, corpus).verdict == "pass"


def test_c069_fails_when_it_says_array_like(corpus):
    bundle = make_bundle(files=[params("X : array-like", "    Uses the column names.")])
    assert verdict("SCIKIT-LEARN-C069", bundle, corpus).verdict == "fail"


def test_c069_finds_no_target_when_the_description_never_mentions_columns(corpus):
    bundle = make_bundle(files=[params("X : array-like", "    The data.")])
    row = verdict("SCIKIT-LEARN-C069", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C070 list element types use `of` -------------------------------------------------


def test_c070_passes_on_list_of_int(corpus):
    bundle = make_bundle(files=[params("sizes : list of int", "    The sizes.")])
    assert verdict("SCIKIT-LEARN-C070", bundle, corpus).verdict == "pass"


def test_c070_fails_on_a_subscript(corpus):
    bundle = make_bundle(files=[params("sizes : list[int]", "    The sizes.")])
    assert verdict("SCIKIT-LEARN-C070", bundle, corpus).verdict == "fail"


def test_c070_finds_no_target_when_no_list_is_documented(corpus):
    bundle = make_bundle(files=[params("copy : bool", "    Copy X.")])
    row = verdict("SCIKIT-LEARN-C070", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C071 the dtype comes after the shape ---------------------------------------------


def test_c071_passes_when_the_dtype_follows(corpus):
    bundle = make_bundle(files=[params(
        "X : ndarray of shape (n_samples,), dtype=np.int32", "    The data.")])
    assert verdict("SCIKIT-LEARN-C071", bundle, corpus).verdict == "pass"


def test_c071_fails_when_the_dtype_leads(corpus):
    bundle = make_bundle(files=[params(
        "X : ndarray dtype=np.int32 of shape (n_samples,)", "    The data.")])
    assert verdict("SCIKIT-LEARN-C071", bundle, corpus).verdict == "fail"


def test_c071_finds_no_target_when_only_a_shape_is_given(corpus):
    bundle = make_bundle(files=[params("X : ndarray of shape (n_samples,)",
                                       "    The data.")])
    row = verdict("SCIKIT-LEARN-C071", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C072 arbitrary precision uses integral and floating ------------------------------


def test_c072_passes_on_integral(corpus):
    bundle = make_bundle(files=[params("X : ndarray, dtype=integral", "    The data.")])
    assert verdict("SCIKIT-LEARN-C072", bundle, corpus).verdict == "pass"


def test_c072_fails_on_the_python_dtype(corpus):
    bundle = make_bundle(files=[params("X : ndarray, dtype=int", "    The data.")])
    assert verdict("SCIKIT-LEARN-C072", bundle, corpus).verdict == "fail"


def test_c072_finds_no_target_on_a_precise_dtype(corpus):
    bundle = make_bundle(files=[params("X : ndarray, dtype=np.int32", "    The data.")])
    row = verdict("SCIKIT-LEARN-C072", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C073 a None default is written once, at the end ----------------------------------


def test_c073_passes_on_the_sanctioned_form(corpus):
    bundle = make_bundle(files=[params("sample_weight : array-like, default=None",
                                       "    The weights.")])
    assert verdict("SCIKIT-LEARN-C073", bundle, corpus).verdict == "pass"


def test_c073_fails_when_none_is_mentioned_twice(corpus):
    bundle = make_bundle(files=[params("sample_weight : array-like or None, default=None",
                                       "    The weights.")])
    assert verdict("SCIKIT-LEARN-C073", bundle, corpus).verdict == "fail"


def test_c073_finds_no_target_when_none_is_not_mentioned(corpus):
    bundle = make_bundle(files=[params("copy : bool, default=True", "    Copy X.")])
    row = verdict("SCIKIT-LEARN-C073", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C076 See Also entries carry an explanation ---------------------------------------


def test_c076_passes_on_one_line_per_reference(corpus):
    doc = documented("See Also", "--------",
                     "SelectKBest : Select features by the k highest scores.")
    assert verdict("SCIKIT-LEARN-C076", make_bundle(files=[doc]),
                   corpus).verdict == "pass"


def test_c076_fails_on_a_bare_name(corpus):
    doc = documented("See Also", "--------", "SelectKBest")
    assert verdict("SCIKIT-LEARN-C076", make_bundle(files=[doc]),
                   corpus).verdict == "fail"


def test_c076_finds_no_target_without_a_see_also_section(corpus):
    row = verdict("SCIKIT-LEARN-C076",
                  make_bundle(files=[params("copy : bool", "    Copy X.")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C077 attribute notes use the rubric directive ------------------------------------


def test_c077_passes_on_the_rubric_directive(corpus):
    doc = documented("Attributes", "----------", "coef_ : ndarray", "    The weights.",
                     "", "    .. rubric:: Note", "", "    Only after fit.")
    assert verdict("SCIKIT-LEARN-C077", make_bundle(files=[doc]),
                   corpus).verdict == "pass"


def test_c077_fails_on_a_note_directive(corpus):
    doc = documented("Attributes", "----------", "coef_ : ndarray", "    The weights.",
                     "", "    .. note::", "", "        Only after fit.")
    assert verdict("SCIKIT-LEARN-C077", make_bundle(files=[doc]),
                   corpus).verdict == "fail"


def test_c077_finds_no_target_when_the_attributes_carry_no_note(corpus):
    doc = documented("Attributes", "----------", "coef_ : ndarray", "    The weights.")
    row = verdict("SCIKIT-LEARN-C077", make_bundle(files=[doc]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C078 Example sections carry one or two snippets ----------------------------------


def test_c078_passes_on_one_snippet(corpus):
    doc = documented("Examples", "--------", ">>> from sklearn.svm import SVC",
                     ">>> SVC().fit(X, y)")
    assert verdict("SCIKIT-LEARN-C078", make_bundle(files=[doc]),
                   corpus).verdict == "pass"


def test_c078_fails_on_an_empty_examples_section(corpus):
    doc = documented("Examples", "--------", "See the user guide.")
    assert verdict("SCIKIT-LEARN-C078", make_bundle(files=[doc]),
                   corpus).verdict == "fail"


def test_c078_finds_no_target_without_an_examples_section(corpus):
    row = verdict("SCIKIT-LEARN-C078",
                  make_bundle(files=[params("copy : bool", "    Copy X.")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C079 docstring examples are runnable as is ---------------------------------------


def test_c079_passes_when_the_example_imports_what_it_uses(corpus):
    doc = documented("Examples", "--------", ">>> import numpy as np",
                     ">>> np.zeros(3)")
    assert verdict("SCIKIT-LEARN-C079", make_bundle(files=[doc]),
                   corpus).verdict == "pass"


def test_c079_fails_on_a_missing_import(corpus):
    doc = documented("Examples", "--------", ">>> np.zeros(3)")
    assert verdict("SCIKIT-LEARN-C079", make_bundle(files=[doc]),
                   corpus).verdict == "fail"


def test_c079_finds_no_target_when_the_section_has_no_doctest(corpus):
    doc = documented("Examples", "--------", "See the user guide.")
    row = verdict("SCIKIT-LEARN-C079", make_bundle(files=[doc]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C085 new user-guide sections carry a figure ---------------------------------------


def test_c085_passes_when_a_figure_is_incorporated(corpus):
    guide = page("Biclustering", "============", "",
                 ".. figure:: ../auto_examples/cluster/images/plot_bicluster_001.png")
    assert verdict("SCIKIT-LEARN-C085", make_bundle(files=[guide]),
                   corpus).verdict == "pass"


def test_c085_fails_without_one(corpus):
    guide = page("Biclustering", "============", "", "It groups rows and columns.")
    assert verdict("SCIKIT-LEARN-C085", make_bundle(files=[guide]),
                   corpus).verdict == "fail"


def test_c085_finds_no_target_when_an_existing_page_is_only_edited(corpus):
    guide = page("Biclustering", "============", new=False)
    row = verdict("SCIKIT-LEARN-C085", make_bundle(files=[guide]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C086 new user-guide sections carry one or two code examples ----------------------


def test_c086_passes_on_one_example(corpus):
    guide = page("Biclustering", "============", "", ">>> from sklearn import cluster")
    assert verdict("SCIKIT-LEARN-C086", make_bundle(files=[guide]),
                   corpus).verdict == "pass"


def test_c086_fails_on_none(corpus):
    guide = page("Biclustering", "============", "", "It groups rows and columns.")
    assert verdict("SCIKIT-LEARN-C086", make_bundle(files=[guide]),
                   corpus).verdict == "fail"


def test_c086_finds_no_target_for_an_edited_page(corpus):
    guide = page("Biclustering", "============", new=False)
    row = verdict("SCIKIT-LEARN-C086", make_bundle(files=[guide]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C087 equations come last, followed by references ---------------------------------


def test_c087_passes_when_references_follow_the_equations(corpus):
    guide = page("Biclustering", "============", "", "Prose first.", "",
                 ".. math:: x = y", "", ".. topic:: References", "",
                 "  * Dhillon, 2001")
    assert verdict("SCIKIT-LEARN-C087", make_bundle(files=[guide]),
                   corpus).verdict == "pass"


def test_c087_fails_when_no_references_follow(corpus):
    guide = page("Biclustering", "============", "", "Prose first.", "",
                 ".. math:: x = y")
    assert verdict("SCIKIT-LEARN-C087", make_bundle(files=[guide]),
                   corpus).verdict == "fail"


def test_c087_finds_no_target_on_a_page_without_mathematics(corpus):
    guide = page("Biclustering", "============", "", "Prose only.")
    row = verdict("SCIKIT-LEARN-C087", make_bundle(files=[guide]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C089 inline literals use single backticks ----------------------------------------


def test_c089_passes_on_a_single_backtick_span(corpus):
    guide = page("Use `list` for the sizes.")
    assert verdict("SCIKIT-LEARN-C089", make_bundle(files=[guide]),
                   corpus).verdict == "pass"


def test_c089_fails_on_a_double_backtick_literal(corpus):
    guide = page("Use ``list`` for the sizes.")
    assert verdict("SCIKIT-LEARN-C089", make_bundle(files=[guide]),
                   corpus).verdict == "fail"


def test_c089_finds_no_target_on_a_line_with_no_backticks(corpus):
    guide = page("It groups rows and columns.")
    row = verdict("SCIKIT-LEARN-C089", make_bundle(files=[guide]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C092 Examples are not folded into a dropdown -------------------------------------


def test_c092_passes_when_the_dropdown_holds_something_else(corpus):
    guide = page("Biclustering", "============", "", ".. dropdown:: Mathematics", "",
                 "    The details.", "", "Examples", "--------", "", "  See the gallery.")
    assert verdict("SCIKIT-LEARN-C092", make_bundle(files=[guide]),
                   corpus).verdict == "pass"


def test_c092_fails_when_examples_is_folded(corpus):
    guide = page("Biclustering", "============", "", ".. dropdown:: More", "",
                 "    Examples", "    --------", "", "    See the gallery.")
    assert verdict("SCIKIT-LEARN-C092", make_bundle(files=[guide]),
                   corpus).verdict == "fail"


def test_c092_finds_no_target_on_a_page_with_no_dropdown(corpus):
    guide = page("Biclustering", "============", "", "Examples", "--------")
    row = verdict("SCIKIT-LEARN-C092", make_bundle(files=[guide]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C093 Examples follow the main discussion -----------------------------------------


def test_c093_passes_when_nothing_is_folded_in_between(corpus):
    guide = page("Biclustering", "============", "", "The discussion.", "",
                 "Examples", "--------", "", "  See the gallery.")
    assert verdict("SCIKIT-LEARN-C093", make_bundle(files=[guide]),
                   corpus).verdict == "pass"


def test_c093_fails_when_a_dropdown_sits_in_between(corpus):
    guide = page("Biclustering", "============", "", "The discussion.", "",
                 ".. dropdown:: Mathematics", "", "    The details.", "",
                 "Examples", "--------", "", "  See the gallery.")
    assert verdict("SCIKIT-LEARN-C093", make_bundle(files=[guide]),
                   corpus).verdict == "fail"


def test_c093_finds_no_target_on_a_page_with_no_examples_section(corpus):
    guide = page("Biclustering", "============", "", "The discussion.")
    row = verdict("SCIKIT-LEARN-C093", make_bundle(files=[guide]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C095 arXiv and DOI references use their roles ------------------------------------


def test_c095_passes_on_the_doi_role(corpus):
    guide = page("See :doi:`10.1145/2408736.2408739` for the derivation.")
    assert verdict("SCIKIT-LEARN-C095", make_bundle(files=[guide]),
                   corpus).verdict == "pass"


def test_c095_fails_on_a_bare_identifier(corpus):
    guide = page("See 10.1145/2408736.2408739 for the derivation.")
    assert verdict("SCIKIT-LEARN-C095", make_bundle(files=[guide]),
                   corpus).verdict == "fail"


def test_c095_finds_no_target_when_no_identifier_is_written(corpus):
    guide = page("See Dhillon (2001) for the derivation.")
    row = verdict("SCIKIT-LEARN-C095", make_bundle(files=[guide]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C097 section links go through a reference label ----------------------------------


def test_c097_passes_on_the_ref_role(corpus):
    guide = page("See :ref:`biclustering` for details.")
    assert verdict("SCIKIT-LEARN-C097", make_bundle(files=[guide]),
                   corpus).verdict == "pass"


def test_c097_fails_on_the_doc_role(corpus):
    guide = page("See :doc:`modules/biclustering` for details.")
    assert verdict("SCIKIT-LEARN-C097", make_bundle(files=[guide]),
                   corpus).verdict == "fail"


def test_c097_finds_no_target_on_a_line_that_links_to_nothing(corpus):
    guide = page("It groups rows and columns.")
    row = verdict("SCIKIT-LEARN-C097", make_bundle(files=[guide]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C098 existing reference labels survive -------------------------------------------


def edited(added, removed, path="doc/modules/svm.rst"):
    return make_file(path, [(n, line) for n, line in enumerate(added, 1)],
                     removed_lines=tuple(removed),
                     head_text="\n".join(added), is_new=False)


def test_c098_passes_when_the_label_is_written_back(corpus):
    changed = edited([".. _biclustering:", "", "Biclustering"], [".. _biclustering:"])
    assert verdict("SCIKIT-LEARN-C098", make_bundle(files=[changed]),
                   corpus).verdict == "pass"


def test_c098_fails_when_a_label_is_dropped(corpus):
    changed = edited(["Biclustering", "============"], [".. _biclustering:"])
    assert verdict("SCIKIT-LEARN-C098", make_bundle(files=[changed]),
                   corpus).verdict == "fail"


def test_c098_finds_no_target_when_the_edit_removes_nothing(corpus):
    guide = page("Biclustering", "============", new=False)
    row = verdict("SCIKIT-LEARN-C098", make_bundle(files=[guide]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C099 glossary terms use the :term: role ------------------------------------------


def test_c099_passes_on_the_term_role(corpus):
    guide = page("It uses :term:`cross_validation` internally.")
    assert verdict("SCIKIT-LEARN-C099", make_bundle(files=[guide]),
                   corpus).verdict == "pass"


def test_c099_fails_on_a_ref_to_the_glossary(corpus):
    guide = page("It uses :ref:`glossary` internally.")
    assert verdict("SCIKIT-LEARN-C099", make_bundle(files=[guide]),
                   corpus).verdict == "fail"


def test_c099_finds_no_target_when_the_glossary_is_not_linked(corpus):
    guide = page("It uses cross validation internally.")
    row = verdict("SCIKIT-LEARN-C099", make_bundle(files=[guide]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C100 / C102 roles use the full import path ---------------------------------------


def test_c100_passes_on_a_full_import_path(corpus):
    guide = page("See :func:`~sklearn.model_selection.cross_val_score`.")
    assert verdict("SCIKIT-LEARN-C100", make_bundle(files=[guide]),
                   corpus).verdict == "pass"


def test_c100_fails_on_a_bare_name(corpus):
    guide = page("See :func:`cross_val_score`.")
    assert verdict("SCIKIT-LEARN-C100", make_bundle(files=[guide]),
                   corpus).verdict == "fail"


def test_c100_finds_no_target_without_a_func_role(corpus):
    guide = page("See the model selection guide.")
    row = verdict("SCIKIT-LEARN-C100", make_bundle(files=[guide]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c102_passes_on_a_full_import_path(corpus):
    guide = page("See :class:`~sklearn.preprocessing.StandardScaler`.")
    assert verdict("SCIKIT-LEARN-C102", make_bundle(files=[guide]),
                   corpus).verdict == "pass"


def test_c102_fails_on_a_bare_name(corpus):
    guide = page("See :class:`StandardScaler`.")
    assert verdict("SCIKIT-LEARN-C102", make_bundle(files=[guide]),
                   corpus).verdict == "fail"


def test_c102_accepts_the_shortcut_under_a_currentmodule_directive(corpus):
    guide = page(".. currentmodule:: sklearn.preprocessing", "",
                 "See :class:`StandardScaler`.")
    assert verdict("SCIKIT-LEARN-C102", make_bundle(files=[guide]),
                   corpus).verdict == "pass"


def test_c102_finds_no_target_without_a_class_role(corpus):
    guide = page("See the preprocessing guide.")
    row = verdict("SCIKIT-LEARN-C102", make_bundle(files=[guide]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C126 deprecations carry a `.. deprecated::` directive ----------------------------


def test_c126_passes_when_the_docstring_carries_the_note(corpus):
    text = ('from sklearn.utils import deprecated\n\n'
            '@deprecated("use predict_proba")\n'
            'def predict_probability(X):\n'
            '    """Predict.\n\n    .. deprecated:: 1.5\n    """\n'
            '    return X\n')
    assert verdict("SCIKIT-LEARN-C126", make_bundle(files=[module_with(text)]),
                   corpus).verdict == "pass"


def test_c126_fails_without_it(corpus):
    text = ('from sklearn.utils import deprecated\n\n'
            '@deprecated("use predict_proba")\n'
            'def predict_probability(X):\n'
            '    """Predict."""\n'
            '    return X\n')
    assert verdict("SCIKIT-LEARN-C126", make_bundle(files=[module_with(text)]),
                   corpus).verdict == "fail"


def test_c126_finds_no_target_without_a_deprecation(corpus):
    row = verdict("SCIKIT-LEARN-C126", make_bundle(files=[NEW_FEATURE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C132 changed defaults carry a `.. versionchanged::` directive --------------------


def rewritten(head, base, path="sklearn/cluster/_kmeans.py"):
    lines = head.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=head, base_text=base)


BASE_DEFAULT = 'def kmeans(X, n_clusters=5):\n    """Cluster X."""\n    return X\n'


def test_c132_passes_when_the_change_is_documented(corpus):
    head = ('def kmeans(X, n_clusters=10):\n'
            '    """Cluster X.\n\n    .. versionchanged:: 1.5\n'
            '        The default changed from 5 to 10.\n    """\n'
            '    return X\n')
    assert verdict("SCIKIT-LEARN-C132",
                   make_bundle(files=[rewritten(head, BASE_DEFAULT)]),
                   corpus).verdict == "pass"


def test_c132_fails_when_it_is_not(corpus):
    head = 'def kmeans(X, n_clusters=10):\n    """Cluster X."""\n    return X\n'
    assert verdict("SCIKIT-LEARN-C132",
                   make_bundle(files=[rewritten(head, BASE_DEFAULT)]),
                   corpus).verdict == "fail"


def test_c132_finds_no_target_when_no_default_changed(corpus):
    head = 'def kmeans(X, n_clusters=5):\n    """Cluster X better."""\n    return X\n'
    row = verdict("SCIKIT-LEARN-C132", make_bundle(files=[rewritten(head, BASE_DEFAULT)]),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C138 constructor arguments are documented under Parameters -----------------------


def estimator(*doc_lines, init="def __init__(self, alpha=1.0):\n        self.alpha = alpha",
              path="sklearn/svm/_classes.py"):
    body = "\n".join(f"    {line}".rstrip() for line in doc_lines)
    text = (f'class SVC:\n    """Summary line.\n\n{body}\n    """\n\n'
            f'    {init}\n\n'
            f'    def fit(self, X, y=None):\n        self.coef_ = X\n        return self\n')
    return module_with(text, path)


def test_c138_passes_when_the_argument_is_under_parameters(corpus):
    cls = estimator("Parameters", "----------", "alpha : float", "    The penalty.",
                    "", "Attributes", "----------", "coef_ : ndarray",
                    "    The weights.")
    assert verdict("SCIKIT-LEARN-C138", make_bundle(files=[cls]),
                   corpus).verdict == "pass"


def test_c138_fails_when_it_is_under_attributes(corpus):
    cls = estimator("Attributes", "----------", "alpha : float", "    The penalty.")
    assert verdict("SCIKIT-LEARN-C138", make_bundle(files=[cls]),
                   corpus).verdict == "fail"


def test_c138_finds_no_target_without_an_attributes_section(corpus):
    cls = estimator("Parameters", "----------", "alpha : float", "    The penalty.")
    row = verdict("SCIKIT-LEARN-C138", make_bundle(files=[cls]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C153 learned attributes are documented under Attributes --------------------------


def test_c153_passes_when_the_learned_attribute_is_documented(corpus):
    cls = estimator("Attributes", "----------", "coef_ : ndarray", "    The weights.")
    assert verdict("SCIKIT-LEARN-C153", make_bundle(files=[cls]),
                   corpus).verdict == "pass"


def test_c153_fails_when_it_is_not(corpus):
    cls = estimator("Parameters", "----------", "alpha : float", "    The penalty.")
    assert verdict("SCIKIT-LEARN-C153", make_bundle(files=[cls]),
                   corpus).verdict == "fail"


def test_c153_finds_no_target_when_nothing_is_learned(corpus):
    text = ('class Config:\n    """Summary line."""\n\n'
            '    def __init__(self, alpha=1.0):\n        self.alpha = alpha\n')
    row = verdict("SCIKIT-LEARN-C153", make_bundle(files=[module_with(text)]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C186 docstrings follow the numpydoc standard -------------------------------------


def test_c186_passes_on_a_numpydoc_section(corpus):
    doc = documented("Parameters", "----------", "X : ndarray", "    The data.")
    assert verdict("SCIKIT-LEARN-C186", make_bundle(files=[doc]),
                   corpus).verdict == "pass"


def test_c186_fails_on_a_rest_field_list(corpus):
    doc = documented(":param X: the data", ":type X: ndarray")
    assert verdict("SCIKIT-LEARN-C186", make_bundle(files=[doc]),
                   corpus).verdict == "fail"


def test_c186_finds_no_target_when_nothing_is_documented(corpus):
    row = verdict("SCIKIT-LEARN-C186", make_bundle(files=[UNDOCUMENTED_FEATURE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

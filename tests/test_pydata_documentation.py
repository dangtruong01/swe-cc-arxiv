"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pydata.documentation  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


def new_module(path: str, text: str):
    lines = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text, is_new=True)


def doc(path: str, text: str):
    lines = text.split("\n")
    return make_file(path, [(n, line) for n, line in enumerate(lines, 1)],
                     head_text=text)


@pytest.fixture(scope="module")
def corpus():
    """pydata's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pydata"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C024 NumPy docstring format ------------------------------------------------------


NUMPY = '''def merge(objects):
    """Merge objects.

    Parameters
    ----------
    objects : list
        the things.
    """
    return objects
'''
SPHINX = '''def merge(objects):
    """Merge objects.

    :param objects: the things.
    """
    return objects
'''


def test_c024_passes_on_a_numpydoc_section(corpus):
    bundle = make_bundle(files=[new_module("xarray/core/merge.py", NUMPY)])
    assert verdict("PYDATA-C024", bundle, corpus).verdict == "pass"


def test_c024_fails_on_a_rest_field_list(corpus):
    bundle = make_bundle(files=[new_module("xarray/core/merge.py", SPHINX)])
    assert verdict("PYDATA-C024", bundle, corpus).verdict == "fail"


def test_c024_finds_no_target_when_nothing_carries_a_docstring(corpus):
    bundle = make_bundle(files=[new_module("xarray/core/merge.py", "x = 1\n")])
    row = verdict("PYDATA-C024", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C026 executable docs are MyST code cells -----------------------------------------


def test_c026_passes_on_a_myst_code_cell(corpus):
    page = doc("doc/user-guide/io.md", "# IO\n\n```{code-cell}\nimport xarray\n```\n")
    assert verdict("PYDATA-C026", make_bundle(files=[page]), corpus).verdict == "pass"


def test_c026_fails_on_executable_code_in_a_rst_page(corpus):
    page = doc("doc/user-guide/io.rst", "IO\n==\n\n>>> import xarray\n")
    assert verdict("PYDATA-C026", make_bundle(files=[page]), corpus).verdict == "fail"


def test_c026_finds_no_target_on_a_prose_only_page(corpus):
    page = doc("doc/user-guide/io.rst", "IO\n==\n\nSome prose.\n")
    row = verdict("PYDATA-C026", make_bundle(files=[page]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C027 public API listed in api.rst ------------------------------------------------


PUBLIC = "def open_zarr():\n    return 1\n"


def test_c027_passes_when_api_doc_lists_the_name(corpus):
    bundle = make_bundle(files=[new_module("xarray/backends/zarr.py", PUBLIC),
                               make_file("doc/api.rst", [(30, "   open_zarr")])])
    assert verdict("PYDATA-C027", bundle, corpus).verdict == "pass"


def test_c027_fails_when_the_name_is_listed_nowhere(corpus):
    bundle = make_bundle(files=[new_module("xarray/backends/zarr.py", PUBLIC)])
    assert verdict("PYDATA-C027", bundle, corpus).verdict == "fail"


def test_c027_finds_no_target_for_a_private_helper(corpus):
    bundle = make_bundle(files=[new_module("xarray/backends/zarr.py",
                                           "def _helper():\n    return 1\n")])
    row = verdict("PYDATA-C027", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C030 section markers -------------------------------------------------------------


def test_c030_passes_on_the_published_order(corpus):
    page = doc("doc/user-guide/io.rst", "Title\n=====\n\nSection\n-------\n\nprose\n")
    assert verdict("PYDATA-C030", make_bundle(files=[page]), corpus).verdict == "pass"


def test_c030_fails_when_the_markers_are_out_of_order(corpus):
    page = doc("doc/user-guide/io.rst", "Title\n-----\n\nSection\n=======\n\nprose\n")
    assert verdict("PYDATA-C030", make_bundle(files=[page]), corpus).verdict == "fail"


def test_c030_fails_on_a_marker_outside_the_set(corpus):
    page = doc("doc/user-guide/io.rst", "Title\n=====\n\nSection\n#######\n\nprose\n")
    assert verdict("PYDATA-C030", make_bundle(files=[page]), corpus).verdict == "fail"


def test_c030_finds_no_target_with_a_single_marker(corpus):
    page = doc("doc/user-guide/io.rst", "Title\n=====\n\nprose\n")
    row = verdict("PYDATA-C030", make_bundle(files=[page]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C031 bold markup -----------------------------------------------------------------


def test_c031_passes_on_double_asterisk_bold(corpus):
    page = doc("doc/user-guide/io.rst", "Use **bold** here.\n")
    assert verdict("PYDATA-C031", make_bundle(files=[page]), corpus).verdict == "pass"


def test_c031_fails_on_markdown_underscore_bold(corpus):
    page = doc("doc/user-guide/io.rst", "Use __bold__ here.\n")
    assert verdict("PYDATA-C031", make_bundle(files=[page]), corpus).verdict == "fail"


def test_c031_finds_no_target_when_no_line_was_written(corpus):
    page = make_file("doc/user-guide/io.rst", [], deletion_anchors=frozenset({3}))
    row = verdict("PYDATA-C031", make_bundle(files=[page]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C033 images use the directive ----------------------------------------------------


def test_c033_passes_on_the_image_directive(corpus):
    page = doc("doc/user-guide/plotting.rst", ".. image:: _static/plot.png\n")
    assert verdict("PYDATA-C033", make_bundle(files=[page]), corpus).verdict == "pass"


def test_c033_fails_on_a_markdown_image(corpus):
    page = doc("doc/user-guide/plotting.md", "![plot](_static/plot.png)\n")
    assert verdict("PYDATA-C033", make_bundle(files=[page]), corpus).verdict == "fail"


def test_c033_finds_no_target_when_no_image_is_named(corpus):
    page = doc("doc/user-guide/plotting.rst", "Some prose about plots.\n")
    row = verdict("PYDATA-C033", make_bundle(files=[page]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0

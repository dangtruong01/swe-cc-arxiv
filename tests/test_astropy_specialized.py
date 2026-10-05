"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

This module's no-target cases carry more weight than usual. Most of these rules are about
things a bug-fix contribution never touches -- Cython extensions, bundled C libraries,
package data, command-line scripts -- so the test that an ordinary patch finds no target is
what keeps twenty-five rules out of the denominator instead of failing every run.

C092 carries a fourth case: a data file the harness could not reconstruct is undetermined,
never passed, because a file we cannot measure is not a file we know to be small.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.astropy.specialized  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SRC = "astropy/io/fits/header.py"


def text_file(path: str, source: str, *, new: bool = False):
    lines = source.split("\n")
    return make_file(path, [(n, t) for n, t in enumerate(lines, start=1)],
                     head_text=source, is_new=new)


def py(source: str, path: str = SRC, *, new: bool = False):
    return text_file(path, source, new=new)


@pytest.fixture(scope="module")
def corpus():
    """astropy's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("astropy"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def row(rule_id, files, corpus):
    return verdict(rule_id, make_bundle(files=files), corpus)


ORDINARY = py("def f():\n    return 1\n")
OPTIONAL_IMPORT = py("def f():\n    import fancylib\n    return fancylib\n")
DECLARED_IMPORT = py("def f():\n    import scipy\n    return scipy\n")


# --- C018 a HAS_* flag for a new optional dependency ------------------------------------


def test_c018_passes_when_the_flag_is_added(corpus):
    flags = text_file("astropy/utils/compat/optional_deps.py", "HAS_FANCYLIB = False\n")
    assert row("ASTROPY-C018", [OPTIONAL_IMPORT, flags], corpus).verdict == "pass"


def test_c018_fails_when_no_flag_is_added(corpus):
    assert row("ASTROPY-C018", [OPTIONAL_IMPORT], corpus).verdict == "fail"


def test_c018_finds_no_target_for_an_already_declared_dependency(corpus):
    result = row("ASTROPY-C018", [DECLARED_IMPORT], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C019 the dependency is recorded in pyproject.toml ------------------------------------


def test_c019_passes_when_pyproject_records_it(corpus):
    project = text_file("pyproject.toml",
                        '[project.optional-dependencies]\nall = ["fancylib"]\n')
    assert row("ASTROPY-C019", [OPTIONAL_IMPORT, project], corpus).verdict == "pass"


def test_c019_fails_when_pyproject_is_untouched(corpus):
    assert row("ASTROPY-C019", [OPTIONAL_IMPORT], corpus).verdict == "fail"


def test_c019_finds_no_target_for_an_already_declared_dependency(corpus):
    result = row("ASTROPY-C019", [DECLARED_IMPORT], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C078 additional dependencies are documented -------------------------------------------


def test_c078_passes_when_the_documentation_mentions_it(corpus):
    doc = make_file("docs/io/fits/index.rst", [(3, "This needs scipy to be installed.")])
    assert row("ASTROPY-C078", [DECLARED_IMPORT, doc], corpus).verdict == "pass"


def test_c078_fails_when_nothing_mentions_it(corpus):
    assert row("ASTROPY-C078", [DECLARED_IMPORT], corpus).verdict == "fail"


def test_c078_finds_no_target_without_a_third_party_import(corpus):
    result = row("ASTROPY-C078", [py("import os\n\ndef f():\n    return os\n")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C080 optional dependencies are imported in the function --------------------------------


def test_c080_passes_on_a_plain_import_inside_the_function(corpus):
    assert row("ASTROPY-C080", [DECLARED_IMPORT], corpus).verdict == "pass"


def test_c080_fails_on_a_module_level_import(corpus):
    assert row("ASTROPY-C080", [py("import scipy\n")], corpus).verdict == "fail"


def test_c080_finds_no_target_without_a_third_party_import(corpus):
    result = row("ASTROPY-C080", [py("import os\nfrom astropy import units\n")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C091 package data lives in a data directory ---------------------------------------------


def test_c091_passes_for_a_file_in_a_data_directory(corpus):
    data = text_file("astropy/io/fits/data/table.fits", "SIMPLE = T\n", new=True)
    assert row("ASTROPY-C091", [data], corpus).verdict == "pass"


def test_c091_fails_for_a_data_file_beside_the_code(corpus):
    data = text_file("astropy/io/fits/table.fits", "SIMPLE = T\n", new=True)
    assert row("ASTROPY-C091", [data], corpus).verdict == "fail"


def test_c091_finds_no_target_for_a_code_only_change(corpus):
    result = row("ASTROPY-C091", [ORDINARY], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C092 data files stay small ----------------------------------------------------------------


def test_c092_passes_for_a_small_data_file(corpus):
    data = text_file("astropy/io/fits/data/table.fits", "SIMPLE = T\n", new=True)
    assert row("ASTROPY-C092", [data], corpus).verdict == "pass"


def test_c092_fails_for_a_data_file_over_the_ceiling(corpus):
    data = text_file("astropy/io/fits/data/table.fits", "x" * 200_000, new=True)
    assert row("ASTROPY-C092", [data], corpus).verdict == "fail"


def test_c092_withholds_when_the_file_was_not_reconstructed(corpus):
    data = make_file("astropy/io/fits/data/table.fits", [], is_new=True, is_binary=True)
    result = row("ASTROPY-C092", [data], corpus)
    assert result.verdict == "not_applicable" and result.status == "parse_error"


def test_c092_finds_no_target_for_a_code_only_change(corpus):
    result = row("ASTROPY-C092", [ORDINARY], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C093 package data is read through get_pkg_data ---------------------------------------------


def test_c093_passes_when_the_accessor_is_used(corpus):
    source = py("def f():\n    return get_pkg_data_filename('data/table.fits')\n")
    assert row("ASTROPY-C093", [source], corpus).verdict == "pass"


def test_c093_fails_when_the_file_is_opened_directly(corpus):
    source = py("def f():\n    return open('data/table.fits')\n")
    assert row("ASTROPY-C093", [source], corpus).verdict == "fail"


def test_c093_finds_no_target_when_no_package_data_is_read(corpus):
    result = row("ASTROPY-C093", [py("def f():\n    return open('/tmp/scratch')\n")], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C094 a pinned data version -------------------------------------------------------------------


def test_c094_passes_on_the_hash_form(corpus):
    source = py("def f():\n"
                "    return get_pkg_data_filename('hash/94935ac31d585f68041c08f87d1a19d4')\n")
    assert row("ASTROPY-C094", [source], corpus).verdict == "pass"


def test_c094_fails_on_an_unpinned_remote_fetch(corpus):
    source = py("def f():\n    return download_file('http://data.example/table.fits')\n")
    assert row("ASTROPY-C094", [source], corpus).verdict == "fail"


def test_c094_finds_no_target_for_a_local_data_file(corpus):
    source = py("def f():\n    return get_pkg_data_filename('data/table.fits')\n")
    result = row("ASTROPY-C094", [source], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C095 persistent configuration through astropy.config -------------------------------------------


def test_c095_passes_on_a_config_item(corpus):
    source = py("MAX = ConfigItem(1, 'How many rows to read.')\n")
    assert row("ASTROPY-C095", [source], corpus).verdict == "pass"


def test_c095_fails_on_configparser(corpus):
    source = py("import configparser\n\ndef save():\n"
                "    parser = configparser.ConfigParser()\n    return parser\n")
    assert row("ASTROPY-C095", [source], corpus).verdict == "fail"


def test_c095_finds_no_target_when_nothing_is_configured(corpus):
    result = row("ASTROPY-C095", [ORDINARY], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C096 configuration items sit at the top ------------------------------------------------------


def test_c096_passes_at_the_top_of_the_module(corpus):
    source = py("MAX = ConfigItem(1, 'How many.')\n\ndef f():\n    return MAX\n")
    assert row("ASTROPY-C096", [source], corpus).verdict == "pass"


def test_c096_fails_below_a_definition(corpus):
    source = py("def f():\n    return 1\n\nMAX = ConfigItem(1, 'How many.')\n")
    assert row("ASTROPY-C096", [source], corpus).verdict == "fail"


def test_c096_finds_no_target_without_a_config_item(corpus):
    source = py("import configparser\n\ndef f():\n    return configparser.ConfigParser()\n")
    result = row("ASTROPY-C096", [source], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C224 configuration options are documented -----------------------------------------------------


def test_c224_passes_when_the_item_carries_a_description(corpus):
    source = py("MAX = ConfigItem(1, 'How many rows to read.')\n")
    assert row("ASTROPY-C224", [source], corpus).verdict == "pass"


def test_c224_fails_when_it_is_neither_described_nor_documented(corpus):
    source = py("MAX = ConfigItem(1)\n")
    assert row("ASTROPY-C224", [source], corpus).verdict == "fail"


def test_c224_finds_no_target_without_a_config_item(corpus):
    result = row("ASTROPY-C224", [ORDINARY], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C122 the .pyx sources are committed -------------------------------------------------------------


SETUP_PYX = text_file("astropy/wcs/setup_package.py",
                      "from setuptools import Extension\n\n"
                      "def get_extensions():\n"
                      "    return [Extension('astropy.wcs._wcs', ['astropy/wcs/_wcs.pyx'])]\n")


def test_c122_passes_when_the_pyx_is_committed(corpus):
    pyx = text_file("astropy/wcs/_wcs.pyx", "def f():\n    return 1\n", new=True)
    assert row("ASTROPY-C122", [pyx, SETUP_PYX], corpus).verdict == "pass"


def test_c122_fails_when_only_the_build_file_names_it(corpus):
    assert row("ASTROPY-C122", [SETUP_PYX], corpus).verdict == "fail"


def test_c122_finds_no_target_for_a_pure_python_change(corpus):
    result = row("ASTROPY-C122", [ORDINARY], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C123 generated .c files are not committed ---------------------------------------------------------


def test_c123_passes_for_a_hand_written_c_extension(corpus):
    csrc = text_file("astropy/wcs/src/wrap.c", "#include <Python.h>\n", new=True)
    assert row("ASTROPY-C123", [csrc], corpus).verdict == "pass"


def test_c123_fails_for_a_cython_generated_file(corpus):
    csrc = text_file("astropy/wcs/_wcs.c", "/* Generated by Cython 0.29.32 */\n", new=True)
    assert row("ASTROPY-C123", [csrc], corpus).verdict == "fail"


def test_c123_finds_no_target_when_no_c_file_is_committed(corpus):
    result = row("ASTROPY-C123", [ORDINARY], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C124 external C libraries are bundled ---------------------------------------------------------------


WCS_C = text_file("astropy/wcs/src/wrap.c", "#include <Python.h>\n#include <wcslib.h>\n")


def test_c124_passes_when_the_library_is_bundled(corpus):
    bundled = text_file("cextern/wcslib/wcs.c", "int wcs(void) { return 0; }\n", new=True)
    assert row("ASTROPY-C124", [WCS_C, bundled], corpus).verdict == "pass"


def test_c124_fails_when_nothing_is_bundled(corpus):
    assert row("ASTROPY-C124", [WCS_C], corpus).verdict == "fail"


def test_c124_finds_no_target_for_standard_includes_only(corpus):
    plain = text_file("astropy/wcs/src/wrap.c", "#include <Python.h>\n#include <stdio.h>\n")
    result = row("ASTROPY-C124", [plain], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C125 the system copy can replace a bundled library ------------------------------------------------------


def test_c125_passes_when_the_opt_out_variable_is_named(corpus):
    bundled = text_file("cextern/wcslib/wcs.c", "int wcs(void) { return 0; }\n", new=True)
    setup = text_file("astropy/wcs/setup_package.py",
                      "import os\n\ndef get_extensions():\n"
                      "    if os.environ.get('ASTROPY_USE_SYSTEM_WCSLIB'):\n"
                      "        return []\n    return []\n")
    assert row("ASTROPY-C125", [bundled, setup], corpus).verdict == "pass"


def test_c125_fails_without_an_opt_out(corpus):
    bundled = text_file("cextern/wcslib/wcs.c", "int wcs(void) { return 0; }\n", new=True)
    assert row("ASTROPY-C125", [bundled], corpus).verdict == "fail"


def test_c125_finds_no_target_when_nothing_is_bundled(corpus):
    result = row("ASTROPY-C125", [ORDINARY], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C225 get_extensions returns Extension objects -----------------------------------------------------------


def test_c225_passes_on_a_list_of_extensions(corpus):
    assert row("ASTROPY-C225", [SETUP_PYX], corpus).verdict == "pass"


def test_c225_fails_when_it_builds_no_extension(corpus):
    setup = text_file("astropy/wcs/setup_package.py",
                      "def get_extensions():\n    return []\n")
    assert row("ASTROPY-C225", [setup], corpus).verdict == "fail"


def test_c225_finds_no_target_when_the_file_defines_no_get_extensions(corpus):
    setup = text_file("astropy/wcs/setup_package.py", "PACKAGE = 'astropy.wcs'\n")
    result = row("ASTROPY-C225", [setup], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C226 C extensions go through get_extensions --------------------------------------------------------------


def test_c226_passes_when_a_setup_package_defines_it(corpus):
    csrc = text_file("astropy/wcs/src/wrap.c", "#include <Python.h>\n", new=True)
    assert row("ASTROPY-C226", [csrc, SETUP_PYX], corpus).verdict == "pass"


def test_c226_fails_when_the_c_source_stands_alone(corpus):
    csrc = text_file("astropy/wcs/src/wrap.c", "#include <Python.h>\n", new=True)
    assert row("ASTROPY-C226", [csrc], corpus).verdict == "fail"


def test_c226_finds_no_target_without_c_sources(corpus):
    result = row("ASTROPY-C226", [ORDINARY], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C227 the .pyx, not the .c, is the extension source ----------------------------------------------------------


def test_c227_passes_when_the_pyx_is_the_source(corpus):
    assert row("ASTROPY-C227", [SETUP_PYX], corpus).verdict == "pass"


def test_c227_fails_when_the_generated_c_is_the_source(corpus):
    pyx = text_file("astropy/wcs/_wcs.pyx", "def f():\n    return 1\n", new=True)
    setup = text_file("astropy/wcs/setup_package.py",
                      "from setuptools import Extension\n\n"
                      "def get_extensions():\n"
                      "    return [Extension('astropy.wcs._wcs', ['astropy/wcs/_wcs.c'])]\n")
    assert row("ASTROPY-C227", [pyx, setup], corpus).verdict == "fail"


def test_c227_finds_no_target_for_a_plain_c_extension(corpus):
    setup = text_file("astropy/wcs/setup_package.py",
                      "from setuptools import Extension\n\n"
                      "def get_extensions():\n"
                      "    return [Extension('astropy.wcs._wcs', ['astropy/wcs/wrap.c'])]\n")
    result = row("ASTROPY-C227", [setup], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C228 numpy headers come from get_include -----------------------------------------------------------------------


def test_c228_passes_when_get_include_is_used(corpus):
    setup = text_file("astropy/wcs/setup_package.py",
                      "import numpy\nfrom setuptools import Extension\n\n"
                      "def get_extensions():\n"
                      "    return [Extension('m', ['m.c'], include_dirs=[numpy.get_include()])]\n")
    assert row("ASTROPY-C228", [setup], corpus).verdict == "pass"


def test_c228_fails_on_a_hand_written_include_path(corpus):
    setup = text_file("astropy/wcs/setup_package.py",
                      "import numpy\nfrom setuptools import Extension\n\n"
                      "def get_extensions():\n"
                      "    return [Extension('m', ['m.c'], include_dirs=['/usr/include'])]\n")
    assert row("ASTROPY-C228", [setup], corpus).verdict == "fail"


def test_c228_finds_no_target_for_an_extension_that_does_not_use_numpy(corpus):
    setup = text_file("astropy/wcs/setup_package.py",
                      "from setuptools import Extension\n\n"
                      "def get_extensions():\n    return [Extension('m', ['m.c'])]\n")
    result = row("ASTROPY-C228", [setup], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C229 headers live in an include directory -------------------------------------------------------------------------


def test_c229_passes_for_a_header_in_include(corpus):
    header = text_file("astropy/wcs/include/wcs.h", "#define WCS 1\n", new=True)
    assert row("ASTROPY-C229", [header], corpus).verdict == "pass"


def test_c229_fails_for_a_header_beside_the_source(corpus):
    header = text_file("astropy/wcs/src/wcs.h", "#define WCS 1\n", new=True)
    assert row("ASTROPY-C229", [header], corpus).verdict == "fail"


def test_c229_finds_no_target_without_a_new_header(corpus):
    result = row("ASTROPY-C229", [ORDINARY], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C230 headers are declared as package data ---------------------------------------------------------------------------


def test_c230_passes_when_pyproject_declares_them(corpus):
    header = text_file("astropy/wcs/include/wcs.h", "#define WCS 1\n", new=True)
    project = text_file("pyproject.toml",
                        '[tool.setuptools.package_data]\n"astropy.wcs" = ["include/*/*.h"]\n')
    assert row("ASTROPY-C230", [header, project], corpus).verdict == "pass"


def test_c230_fails_when_pyproject_is_untouched(corpus):
    header = text_file("astropy/wcs/include/wcs.h", "#define WCS 1\n", new=True)
    assert row("ASTROPY-C230", [header], corpus).verdict == "fail"


def test_c230_finds_no_target_for_a_header_outside_include(corpus):
    header = text_file("astropy/wcs/src/wcs.h", "#define WCS 1\n", new=True)
    result = row("ASTROPY-C230", [header], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C231 setup_package.py imports nothing from its package -------------------------------------------------------------------


def test_c231_passes_when_it_imports_only_build_tooling(corpus):
    setup = text_file("astropy/wcs/setup_package.py",
                      "import os\nfrom setuptools import Extension\n")
    assert row("ASTROPY-C231", [setup], corpus).verdict == "pass"


def test_c231_fails_on_an_import_from_astropy(corpus):
    setup = text_file("astropy/wcs/setup_package.py", "from astropy import units\n")
    assert row("ASTROPY-C231", [setup], corpus).verdict == "fail"


def test_c231_finds_no_target_without_a_setup_package(corpus):
    result = row("ASTROPY-C231", [ORDINARY], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C233 a script has a main that delegates -------------------------------------------------------------------------------------


SCRIPT_PATH = "astropy/io/fits/scripts/fitscheck.py"


def test_c233_passes_when_main_delegates(corpus):
    script = py("import argparse\n\ndef check(args):\n    return 0\n\n"
                "def main(args=None):\n"
                "    parser = argparse.ArgumentParser()\n"
                "    return check(parser.parse_args(args))\n", path=SCRIPT_PATH)
    assert row("ASTROPY-C233", [script], corpus).verdict == "pass"


def test_c233_fails_when_the_script_has_no_main(corpus):
    script = py("import sys\n\nprint(sys.argv)\n", path=SCRIPT_PATH)
    assert row("ASTROPY-C233", [script], corpus).verdict == "fail"


def test_c233_finds_no_target_for_an_ordinary_module(corpus):
    result = row("ASTROPY-C233", [ORDINARY], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C234 main takes one optional argument ------------------------------------------------------------------------------------------


def test_c234_passes_on_the_published_signature(corpus):
    script = py("def main(args=None):\n    return 0\n", path=SCRIPT_PATH)
    assert row("ASTROPY-C234", [script], corpus).verdict == "pass"


def test_c234_fails_on_a_multi_argument_main(corpus):
    script = py("def main(argv, options):\n    return 0\n", path=SCRIPT_PATH)
    assert row("ASTROPY-C234", [script], corpus).verdict == "fail"


def test_c234_finds_no_target_when_the_script_has_no_main(corpus):
    script = py("import sys\n\nprint(sys.argv)\n", path=SCRIPT_PATH)
    result = row("ASTROPY-C234", [script], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0


# --- C235 the script is registered as an entry point ------------------------------------------------------------------------------------


def test_c235_passes_when_the_packaging_configuration_declares_it(corpus):
    script = py("def main(args=None):\n    return 0\n", path=SCRIPT_PATH, new=True)
    project = text_file("pyproject.toml",
                        "[project.scripts]\nfitscheck = "
                        '"astropy.io.fits.scripts.fitscheck:main"\n')
    assert row("ASTROPY-C235", [script, project], corpus).verdict == "pass"


def test_c235_fails_when_nothing_registers_it(corpus):
    script = py("def main(args=None):\n    return 0\n", path=SCRIPT_PATH, new=True)
    assert row("ASTROPY-C235", [script], corpus).verdict == "fail"


def test_c235_finds_no_target_when_the_script_already_existed(corpus):
    script = py("def main(args=None):\n    return 0\n", path=SCRIPT_PATH)
    result = row("ASTROPY-C235", [script], corpus)
    assert result.verdict == "not_applicable" and result.n_targets == 0

<!-- CONTRIBUTING-RULES-FILE -->
# Astropy contribution rules

Extracted from the Astropy contributing documentation (astropy-rules). 111 rules. Follow all of them.

## Git and commit conventions

- Put ``Closes #<issue>`` on the second or a later line of the commit message when the commit fixes an issue.
- Put ``[ci skip]`` or ``[skip ci]`` in the commit message when the commits are not ready for CI.
- Include ``[ci skip]`` in the commit message for a trivial documentation fix.

## PR and release metadata

- Add a changelog fragment under ``docs/changes/<sub-package>/`` describing your change.
- Name the changelog fragment ``<PR number>.<feature|api|bugfix|perf|other>.rst``.
- Do not use single backticks for API reference links in changelog fragments.
- Write changelog fragments as full sentences with correct case and punctuation.
- Put ``other``-type changelog fragments only in the root ``docs/changes/`` directory.

## Tests and test style

- Close every file a test opens so no unhandled ResourceWarning is raised.
- Name test modules ``test_*.py`` or ``*_test.py``.
- Prefix test functions and methods with ``test_``.
- Give test classes a ``Test`` prefix and no ``__init__`` method.
- Put a sub-package's tests in that sub-package's own ``tests/`` directory.
- Include an ``__init__.py`` file in every ``tests`` directory.
- Put tests that span two or more sub-packages in ``astropy/tests/``.
- Include the URL of the reported issue in the regression test.
- Mark any test that retrieves remote data with ``@pytest.mark.remote_data``.
- Flag a doctest that retrieves remote data with ``# doctest: +REMOTE_DATA``.
- Write files created by a test into the ``tmp_path`` fixture directory rather than a permanent location.
- Skip a test that needs an optional dependency when that dependency is absent.
- Take the skip condition from the ``HAS_*`` flags in ``astropy.utils.compat.optional_deps``.
- Assert expected warnings with the ``pytest.warns`` context manager.
- Assert expected exceptions with the ``pytest.raises`` context manager.
- Mark a block excluded from coverage with a ``# pragma: no cover`` comment at its start.
- Decorate figure tests with ``@figure_test`` from ``astropy.tests.figures`` rather than ``@pytest.mark.mpl_image_compare``.
- Write docstring and narrative examples so they run correctly as doctests.
- Mark a non-executable doctest example with ``# doctest: +SKIP``.
- Skip a module's doctests by listing wildcard patterns in a module-level ``__doctest_skip__``.
- Declare a doctest's optional-dependency requirements in a module-level ``__doctest_requires__`` dictionary.
- Skip a doctest block in narrative documentation with the ``.. doctest-skip::`` directive (or ``.. doctest-skip-all``).
- Gate a doctest block in narrative documentation on a dependency with the ``.. doctest-requires::`` directive.
- Ignore a doctest's output entirely with the ``# doctest: +IGNORE_OUTPUT`` flag.
- Compare floating-point doctest output with the ``# doctest: +FLOAT_CMP`` flag.
- Run the tests with ``--remote-data`` when the bug involves remote data access.
- Write a test that fails before the fix and passes after it.
- Add tests covering new code.
- Add a test for every exception the new code raises.
- Make ``tox -e test`` run without failures.

## Specialized changes

- Add a ``HAS_*`` flag to ``astropy/utils/compat/optional_deps.py`` for any new optional dependency.
- Record a new optional dependency in ``[project.optional-dependencies]`` in ``pyproject.toml``, under ``all`` for runtime use or ``test_all`` for test-only use.
- Document any additional third-party dependency a sub-module or function introduces.
- Import an optional dependency with a plain ``import`` inside the function or method that uses it.
- Put package data files in a ``data`` directory inside the sub-package.
- Keep in-repository data files under about 100 kB and host anything larger off the repository.
- Access package data through ``get_pkg_data_fileobj`` or ``get_pkg_data_filename``.
- Pin a specific version of a data file with the ``astropy.utils.data`` hash mechanism.
- Implement persistent configuration through the ``astropy.config`` mechanism.
- Declare configuration items at the top of the module or package that uses them.
- Commit the ``.pyx`` sources of a Cython extension.
- Do not commit the ``.c`` files Cython generates.
- Bundle the source of an external C library a C extension depends on, if its license permits.
- Let a bundled C library be replaced by the system copy through an ``ASTROPY_USE_SYSTEM_<LIB>`` environment variable.
- Document every configuration option added through ``astropy.config``.
- Make ``get_extensions`` in ``setup_package.py`` return a list of ``setuptools.Extension`` objects.
- Define every C extension through the ``get_extensions`` mechanism.
- Give the ``.pyx`` files, not the generated ``.c`` files, as the source of a Cython extension.
- Locate the numpy C headers with ``numpy.get_include()``.
- Put a package's installable C header files in an ``include`` directory inside the package.
- Declare installable C header files in ``[tool.setuptools.package_data]`` in ``pyproject.toml``.
- Keep ``setup_package.py`` free of imports from the package it belongs to.
- Give a command-line script a ``main`` function that parses arguments and delegates to a library function.
- Give ``main`` a single optional argument holding ``sys.argv[1:]``.
- Register the script as an entry point in the packaging configuration.

## Documentation and docstrings

- Give every public class, method, and function a docstring.
- Put ``i.e.`` and ``e.g.`` inside parentheses and follow them with a comma.
- Write an organization's acronym and hyperlink it to a reference.
- Capitalize proper nouns, but write package and code names lowercase in double backticks.
- Write ``astropy`` lowercase in double backticks when you mean the core package and Astropy capitalized when you mean the Project.
- Do not use contractions in documentation.
- Write a number as a numeral when it is followed by a unit or is part of a name.
- Spell out whole numbers one through nine and use numerals from 10 up.
- Place punctuation belonging to parenthetical material inside the closing parenthesis.
- Put periods and commas inside closing quotation marks.
- Use an unspaced en dash for number ranges and in place of “to” or “through”.
- Put a space on either side of an em dash.
- Use American spelling.
- Express exact times as numerals in the 24-hour system.
- Write specific dates in ISO 8601 year-month-day form.
- Use the first-person inclusive plural (“we”) in narrative documentation.
- Use “you” rather than “one” as the generic pronoun.
- Do not use belittling words such as “obviously”, “easily”, “simply”, “just” or “straightforward”.
- Use ``.. warning::`` directives only for limitations in the code.
- Make a heading's underline (and overline) the same length as the heading text.
- Describe new functionality in the narrative documentation under ``docs/``.
- Cite the origin source of any algorithm you implement.
- Document what the function does, its inputs, its outputs, its references, its exceptions and an example in its numpydoc docstring.
- Write docstrings in numpydoc format.
- Write docstring cross-references in intersphinx form, including links within astropy.
- Use a direct URL when linking to the development version of the documentation.

## AI-assisted contribution policy

- Describe your use of generative AI in the change description when it wrote substantive portions of the contribution.
- Do not submit a contribution through an autonomous agent acting without a human contributor.

## Code and quality

- Review and re-stage any file that pre-commit rewrote before committing.
- Keep all code compatible with the Python versions in ``requires-python`` in ``pyproject.toml``.
- Keep the core package importable using only the standard library, NumPy, and astropy itself.
- Do not introduce a dependency that is not declared in ``pyproject.toml``.

## Language and framework style

- Put general-purpose utilities in ``astropy.utils`` rather than in a sub-package.
- Use ``print()`` only for output the user explicitly asked for.
- Raise a built-in or custom exception class for error conditions.
- Do not raise the bare ``Exception`` class.
- Emit warnings with ``warnings.warn(message, warning_class)``.
- Use ``AstropyUserWarning`` or a subclass of it as the warning class.
- Emit informational and debugging messages through ``log.info()`` and ``log.debug()``.
- Format Python files with ``ruff format``.
- Sort module imports.
- Make the code pass the repository's configured ruff checks.
- Start each source file with the comment ``# Licensed under a 3-clause BSD style license - see LICENSE.rst``.
- Expose instance state through attributes or properties rather than get_/set_ methods unless access is computationally expensive.
- Call super-class methods through ``super()``.
- Make ``__repr__`` return ASCII-only text regardless of ``unicode_output``.
- Make ``__str__`` and ``__format__`` return ASCII-only text when ``unicode_output`` is False.
- Make a round-trippable class's parser accept its own ``__str__`` output.

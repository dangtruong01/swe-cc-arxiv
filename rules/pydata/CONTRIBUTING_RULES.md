<!-- CONTRIBUTING-RULES-FILE -->
# xarray contribution rules

Extracted from the xarray contributing documentation (pydata-rules). 35 rules. Follow all of them.

## Git and commit conventions

- Commit every modified file into the local repository.
- Add every new file to git so it is part of the commit.
- Reference the relevant GitHub issue in the commit message as GH1234 or #1234.
- Add a [test-upstream] tag to the first line of the commit message to run the upstream dev CI.
- Add a [skip-ci] tag to the first line of a documentation-only commit message to skip CI.

## PR and release metadata

- Add an entry describing your change to doc/whats-new.rst.
- Include the GitHub issue number in the whats-new.rst entry using the :issue: role.

## Tests and test style

- Write tests with pytest, using the numpy.testing extensions where they apply.
- Put new tests in the tests subdirectory of the package they cover.
- Compare xarray objects with assert_equal or assert_identical from xarray.testing.
- Write new tests as functions rather than as test classes.
- Name test functions test_* and give them only fixture or parameter arguments.
- Mark an individual parameter with pytest.param(..., marks=...).
- Assert on scalars and truth values with a bare assert statement.
- Name a test module test_<feature>.py.
- Add tests for the change.
- Gate a test on an optional dependency with a `@requires_*` decorator rather than a conditional `if`.
- Import dask array helpers from `xarray.tests` in tests instead of importing `dask.array` directly.
- Do not attach `pytest.mark.skipif` to a `pytest.param` inside `parametrize`.
- Import an optional dependency inside a test function with `pytest.importorskip`.

## Specialized changes

- When an argument is no longer valid, keep accepting it and emit a FutureWarning with emit_user_level_warning instead of raising.

## Documentation and docstrings

- Write docstrings in the NumPy docstring format.
- Write documentation pages containing executable code as MyST Markdown files using the {code-cell} directive.
- List every public method in a toctree in doc/api.rst.
- Mark up ReST section levels with `*` and an overline for chapters, `=` for headings, `-` for sections and `~` for subsections.
- Use `**text**` for bold text in ReST.
- Include image files in documentation pages with the `image::` directive.

## AI-assisted contribution policy

- Personally review and understand every line of the change before submitting it.
- Never submit documentation you have not read and verified yourself.
- Disclose that the pull request contains AI-generated content.

## Code and quality

- Format code with ruff so that `ruff format` reports no changes.
- Keep the code free of ruff lint violations.
- Make type hints pass mypy's static type check.
- Run pre-commit over all files and commit any changes it makes.

## Language and framework style

- Order imports the way ruff's isort rules require.

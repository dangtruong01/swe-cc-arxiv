<!-- CONTRIBUTING-RULES-FILE -->
# Sphinx contribution rules

Extracted from the Sphinx contributing documentation (sphinx-doc-rules). 24 rules. Follow all of them.

## PR and release metadata

- Add a bullet point to CHANGES.rst for any change that is not trivial.

## Tests and test style

- Include tests demonstrating the bug fix or the new feature alongside the code change.
- Run the JavaScript test suite with npm when the change touches JavaScript.
- Place new unit tests in the tests/ directory.
- For a bug fix, add a test that fails before the patch is applied and passes after it.

## Specialized changes

- Do not modify the gettext translation files directly in a pull request.
- Regenerate the search stemmers and stopword files with utils/generate_snowball.py rather than editing them by hand.
- Regenerate the minified search JavaScript from the non-minified sources with uglifyjs.
- Regenerate the tests/js/fixtures searchindex.js files with utils/generate_js_fixtures.py.
- Raise a RemovedInSphinxXXWarning when a newly deprecated feature is invoked.
- Eliminate or silence the deprecation warnings a new RemovedInSphinxXXWarning raises in the test suite.
- Do not remove a deprecated feature before the second major release after its deprecation.

## Documentation and docstrings

- Document every new feature that the change adds.
- Document any new configuration variable in the configuration documentation.
- Make documentation changes in the source files under doc/.
- Build the documentation with sphinx-build using --fail-on-warning.

## AI-assisted contribution policy

- Do not use AI to automatically generate code comments.
- Disclose whether AI was used in developing the pull request.
- Document which AI tools were used and how they were used.
- Specify which code or text in the contribution is AI generated.
- Do not let an AI agent write code and open a pull request autonomously.

## Code and quality

- Ensure the change passes ruff's lint checks.
- Format the code with ruff format.
- Ensure the change type-checks cleanly under mypy.

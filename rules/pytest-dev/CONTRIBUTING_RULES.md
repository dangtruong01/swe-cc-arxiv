<!-- CONTRIBUTING-RULES-FILE -->
# pytest contribution rules

Extracted from the pytest contributing documentation (pytest-dev-rules). 22 rules. Follow all of them.

## Git and commit conventions

- Commit only after the test suite passes.
- Add `closes #<issue number>` to the commit message when the change fixes an issue.

## PR and release metadata

- Name the changelog file `<issue id>.<type>.rst`.
- Use one of feature, improvement, bugfix, doc, deprecation, breaking, vendor, packaging, contrib or misc as the changelog entry type.
- Write changelog entries in the past or present tense.
- End each changelog sentence with a period.

## Tests and test style

- Run the test suite through tox before submitting the change.
- Include new tests or update existing tests with the change.

## Specialized changes

- Raise deprecations through a `PytestRemovedInXWarning` class naming the target major version.
- Ship deprecation errors or warnings that help users port their code as part of a breaking change.

## Documentation and docstrings

- Build the documentation locally with `tox -e docs` after changing documentation.
- Write docstrings for documented items in the Sphinx docstring format.
- Start docstring sentences with a capital letter and end them with a period.
- Separate a docstring's detailed explanation from its subject line with a blank line.
- Document the rationale and porting examples for a breaking change in `doc/en/deprecations.rst`.
- Include documentation in the same change when adding a new feature.

## AI-assisted contribution policy

- Do not submit a contribution generated entirely by an AI agent without meaningful human review and oversight.
- Credit AI agents that were used in `Co-authored-by` commit trailers.

## Code and quality

- Install and enable pre-commit on the pytest checkout.
- Run the `linting` tox environment to perform the coding-style checks.

## Language and framework style

- Follow PEP-8 naming conventions in Python code.
- Write code that runs on Python 3.10 and later.

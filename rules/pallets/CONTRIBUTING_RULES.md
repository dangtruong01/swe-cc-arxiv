<!-- CONTRIBUTING-RULES-FILE -->
# Flask contribution rules

Extracted from the Flask contributing documentation (pallets-rules). 34 rules. Follow all of them.

## Git and commit conventions

- Keep the first line of the commit message to 50 characters or fewer.
- Separate any commit message body from the subject with a blank line and wrap it at 72 characters.
- Do not put issue numbers in the commit message.
- Give each collaborator a co-authored-by line at the bottom of the commit message.
- Do not commit directly to main or stable; route every change through a pull request.

## PR and release metadata

- Do not add a changelog entry for a change that only touches documentation or tool configuration.
- Do not include unrelated refactors, type annotation changes or test reorganizations in a bug fix.
- Append a new changelog entry to the end of its section.
- Add a CHANGES.rst entry summarizing the change.

## Tests and test style

- Add tests that demonstrate the change works.
- Ensure the whole test suite passes before submitting.
- Put tests in the tests directory.
- Name test files using the test_{topic}.py pattern.
- Name each test function test_{specific}.
- Give each test function a unique name.
- Extend an existing related test file for a bug fix rather than creating a new one.
- Use plain assert statements in tests.
- Use @pytest.mark.parametrize when a test covers multiple cases.
- Ensure the added tests fail when the change is reverted.

## Documentation and docstrings

- Write docstrings in reStructuredText.
- Fix a typo everywhere it occurs, not only where it was noticed.
- Do not fix typos in code comments that never appear in the built docs unless you are already editing that code.
- Do not use 'you' or 'we' in documentation outside tutorials.
- Write documentation in English.
- Use the serial comma in documentation prose.
- Do not submit a change whose purpose is to make spelling or style uniform across existing docs.
- Do not reference GitHub issue or PR numbers or links anywhere in the codebase.
- Add or update the documentation affected by the change, in docs and in code.
- Add a versionchanged directive to the docs for changed behaviour.

## AI-assisted contribution policy

- Do not generate a pull request with LLM or AI tools.
- Do not submit a contribution that appears to be LLM- or AI-generated.
- Do not use LLM tools to translate or improve the text you write.

## Code and quality

- Run mypy over the change to check static typing.
- Make the change satisfy the project's pre-commit lint and format checks.

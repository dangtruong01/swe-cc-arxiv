<!-- CONTRIBUTING-RULES-FILE -->
# Requests contribution rules

Extracted from the Requests contributing documentation (psf-rules). 13 rules. Follow all of them.

## Git and commit conventions

- Write a commit message that explains why the change was made, not only which issue it closes.

## Tests and test style

- Run the test suite before making any change and confirm it passes on your system.
- Add tests that exercise the bug or feature the change addresses.
- Confirm the newly added tests fail against the unmodified code before applying the change.
- Run the entire test suite after making the change and confirm every test passes, including the new ones.

## Documentation and docstrings

- Place documentation changes under the docs/ directory.
- Write documentation files in reStructuredText.

## AI-assisted contribution policy

- Ensure every contribution is authored by a human who owns the copyright to all of its changes.
- Do not list an LLM tool as a Co-authored-by trailer on a commit.
- Do not use an unsupervised agentic coding tool to produce the contribution.
- Certify that you authored the contribution or hold the legal right to submit it.

## Code and quality

- Make the changed files satisfy every formatting requirement configured in .pre-commit-config.yaml.

## Language and framework style

- Use single-quoted strings in Python code samples inside the documentation.

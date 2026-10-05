<!-- CONTRIBUTING-RULES-FILE -->
# Pylint contribution rules

Extracted from the Pylint contributing documentation (pylint-dev-rules). 49 rules. Follow all of them.

## Git and commit conventions

- Do not add venv to the repository's .gitignore.
- Do not commit a virtual environment directory.

## PR and release metadata

- Create a towncrier news fragment named after the issue number for the change.
- Give the news fragment one of the fragment types declared in towncrier.toml.

## Tests and test style

- Run pylint's own test suite against your change.
- Include tests with every contribution.
- Select a test suite with a -k pattern that omits the .py extension.
- Run the stdlib primer locally with pytest -m primer_stdlib --primer-stdlib.
- Put new unit tests in pylint's unit test directory.
- Put data files a unit test needs in the regrtest_data directory.
- Give every functional test .py file a .txt companion with the same stem.
- Record in the .txt file exactly the pylint messages the test file should emit.
- Annotate each line expected to emit a message with a # [message_symbol] comment.
- List several expected messages on one line as a comma-separated set inside a single bracket comment.
- Put per-test pylint configuration in a same-named .rc file beside the test.
- Pass functional runner options only through a [testoptions] section using the supported keys.
- Set max_pyver to the first unsupported version, one above the last version the test should run on.
- Mark version-conditional expected messages using only the four supported comparison operators.
- Provide both a version-suffixed .txt and a default .txt when expected output differs by Python version.
- Use min_pyver or max_pyver rather than conditional annotations when the test code is not parsable on every version.
- Append a new test case for an existing checker to that checker's existing test file.
- Name a new checker's functional test file after the message symbol, with underscores.
- Place a functional test file in the sub-directory named for its first letter.
- Put a regression test in one of the two regression directories.
- Prefix a regression test file name with regression_.
- Place a test file in a nested sub-directory whose name matches the word before the first underscore of the file name.
- Regenerate a functional test's expected output with --update-functional-output.
- Create a configuration test as a new, unused filename in the directory for that configuration format.
- Add a .result.json file whose stem matches the configuration test file.
- Record only the difference from the standard configuration in the .result.json file.
- Express an expected configuration failure with a .out file named for the test and its exit code.
- Use the {abspath} and {relpath} placeholders for module and file name in a .out file.

## Specialized changes

- Put the functional test for an extension checker under the extension's own directory.

## AI-assisted contribution policy

- Consult .github/copilot-instructions.md before searching the repository for context.

## Code and quality

- Run pre-commit run -a before committing.
- Lint changed files with pylint --rcfile=pylintrc --fail-on=I.
- Validate a change by running pylint over sample code that exercises it.

## Language and framework style

- Give a new checker a message id that no existing checker already uses.
- Give a new checker class a name attribute.
- Declare every message a checker emits in its msgs dictionary.
- Name a checker's node handlers visit_ or leave_ followed by the lowered astroid class name.
- Add a module-level register function that registers the checker with the linter.
- Form a message id as one of the five category letters followed by four digits.
- Keep the first two digits of a checker's message ids the same across that checker.
- Change the message symbol whenever you change its message id.
- Set the shared option to True on a message used by more than one checker.
- Implement get_map_data and reduce_map_data as a matching pair on a checker that reduces data.
- Include the astroid proxy base in the isinstance tuple when replacing a hasattr guard.
- Put a new checker class in the appropriate file under pylint/checkers/.

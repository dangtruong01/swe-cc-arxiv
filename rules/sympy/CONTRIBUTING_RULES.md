<!-- CONTRIBUTING-RULES-FILE -->
# SymPy contribution rules

Extracted from the SymPy contributing documentation (sympy-rules). 142 rules. Follow all of them.

## Git and commit conventions

- Before changing code, a contributor must create and check out a contribution branch, for example with `git checkout -b <branch-name>`.
- A contributor must not commit contribution changes directly to `master`.
- While checked out on `master`, a contributor must not run `git merge`, `git add`, `git commit`, or `git rebase`.
- Before merge, editor configuration, binary, and temporary junk files must be removed from the contribution.
- A commit-message summary line must be no longer than 71 characters.
- Every commit-message body line must be no longer than 78 characters.
- A commit message must separate its summary from its body with a blank line.
- A commit-message summary must not end with a period.
- A commit-message body must use complete sentences.
- If a commit credits a co-author through GitHub, each trailer must appear at the bottom of the commit message in the exact form `Co-authored-by: <name> <email>`.
- A contributor must not edit `AUTHORS` directly; contributor identity changes must be made through `.mailmap`.
- The source identity in a contributor's `.mailmap` entry must exactly match the name and email stored in their Git commit metadata.
- After editing `.mailmap`, the contributor must run `python bin/mailmap_check.py` until it reports `No changes needed in .mailmap`, thereby placing entries in alphabetical order.
- After `python bin/mailmap_check.py` reports `No changes needed in .mailmap`, the contributor must stage `.mailmap` with `git add .mailmap` and commit it with an `author: add <name> to .mailmap` message.

## PR and release metadata

- A pull request description must cross-reference relevant issues.
- If merging the pull request should close an issue, its description must use `fixes #<issue-number>` syntax.
- A pull request must include a release-notes entry in its description before merge.
- If a pull request is not ready to merge, it must be marked Draft or have a `[WIP]` title prefix.
- Before final review, a pull request must no longer be Draft and must not retain a `[WIP]` title prefix.
- A pull-request author must complete the repository's pull-request description template, including issue references and release notes.
- A pull-request title must contain neither issue numbers nor file names; issue numbers belong in the description.
- To close an issue or pull request automatically, the pull-request description must place the autoclose sequence in an opening paragraph.
- If a pull request should close multiple issues or pull requests, it must repeat an autoclose keyword immediately before every `#<number>`.
- If a pull request must not close an issue, its description must not place an autoclose keyword next to that issue number even inside a negated sentence such as `does not fix #12345`.
- Every pull-request description must contain a release-notes block between `<!-- BEGIN RELEASE NOTES -->` and `<!-- END RELEASE NOTES -->`.
- Each release-note header must exactly match one current non-comment entry in `sympy_bot/submodules.txt`: `abc`, `algebras`, `assumptions`, `benchmarks`, `calculus`, `categories`, `codegen`, `combinatorics`, `concrete`, `core`, `crypto`, `diffgeom`, `discrete`, `external`, `functions`, `geometry`, `holonomic`, `integrals`, `interactive`, `liealgebras`, `logic`, `matrices`, `ntheory`, `parsing`, `physics.biomechanics`, `physics.continuum_mechanics`, `physics.control`, `physics.gaussopt`, `physics.hep`, `physics.hydrogen`, `physics.matrices`, `physics.mechanics`, `physics.optics`, `physics.paulialgebra`, `physics.pring`, `physics.qho_1d`, `physics.quantum`, `physics.secondquant`, `physics.sho`, `physics.units`, `physics.vector`, `physics.wigner`, `plotting`, `polys`, `printing`, `sandbox`, `series`, `sets`, `simplify`, `solvers`, `stats`, `strategies`, `tensor`, `testing`, `unify`, `utilities`, `vector`, `other`.
- Under each release-note submodule header, changes must be written as a Markdown list.
- If a pull request does not warrant release notes, its release-notes block must contain exactly `NO ENTRY`.
- Each release-note entry must be a complete sentence beginning with a capital letter and ending with a period.
- A release-note entry must contain neither a pull-request number nor author names; the bot adds them automatically.
- A release-note entry must not contain issue numbers; issue references belong elsewhere in the pull-request description.
- Every release-note entry must use past tense, be self-contained, and be phrased for direct insertion into the wiki rather than referring to `this pull request`.
- A release-note entry must omit first-person phrases such as `I have fixed` and pull-request-relative phrases such as `this pull request fixes`.

## Tests and test style

- If a contribution adds new functionality, it must include tests.
- Before merge, every pull request must pass the complete test suite.
- A test function must have a name beginning with `test_`.
- When validating the complete local test and doctest suites, a contributor must run both `python bin/test` and `python bin/doctest` and require both commands to pass.
- When testing an expected exception, the test must use `sympy.testing.pytest.raises`.
- When calling `sympy.testing.pytest.raises(ExceptionType, ...)`, the tested expression must be wrapped in `lambda`, unless the context-manager form is required.
- A `SymPyDeprecationWarning` test must use `sympy.testing.pytest.warns_deprecated_sympy()` unless stacklevel checking is explicitly disabled.
- Code that emits a warning must set `stacklevel` so the warning identifies the user's calling line.
- If a deprecation warning cannot set `stacklevel` correctly, its test must use `warns(SymPyDeprecationWarning, test_stacklevel=False)` instead of `warns_deprecated_sympy()`.
- Deprecated behavior may be called only inside its dedicated `warns_deprecated_sympy()` test; all other tests must use non-deprecated behavior.
- To assert that an expression remains unevaluated, a test must use `sympy.core.expr.unchanged(function, *args)` rather than compare repeated evaluations.
- If an expression result contains `Dummy`, the test must compare it with `.dummy_eq(expected)` rather than direct `==`.
- After adding a random test, the contributor must run it multiple times and confirm it consistently passes.
- A test skipped because it is expected to fail must use `@XFAIL`, not `@SKIP` or `skip()`.
- A test skipped only because it is slow must use `@slow`, not `@SKIP` or `skip()`.
- If an XFAIL test begins to pass, the contributor must remove `@XFAIL` so it becomes a normal test.
- A test taking more than one minute must be marked with `sympy.testing.pytest.slow` as `@slow`.
- A hanging test must use `@SKIP` instead of `@slow`.
- When validating tests marked `@slow` locally, a contributor must run `python bin/test --slow` and require it to pass.
- A test for optional-dependency functionality must import the dependency with `sympy.external.import_module()` so absence returns `None` instead of failing import.
- Before acceptance, contributed doctests must pass when run with `python bin/doctest` (optionally followed by a file or submodule argument).
- Each doctest must be self-contained and explicitly import every function it uses.
- Each doctest must explicitly define every symbol it uses, importing common names from `sympy.abc` or creating other/assumed symbols with `symbols()`.
- A doctest must show `>>>` before inputs and exact Python-session output strings after them.
- A dependency-requiring doctest must declare libraries with `@doctest_depends_on(...)`, not `# doctest: +SKIP`.
- If expected doctest output contains a blank line, the expected output must contain the literal marker `<BLANKLINE>` in its place.
- To display a `None` result in a doctest, the example must call `print(<expression>)` so the expected output contains `None`.
- Before updating an expected expression, the contributor must verify equivalence for all relevant domains, using methods such as simplification, random values, or `.equals()`.
- Unless testing floating-point behavior, a test must use exact SymPy values such as `S(1)/2`, not Python float-producing expressions such as `1/2`.
- Except in printer tests, assertions must compare SymPy expressions directly rather than their `str(...)` forms.
- Except in parser tests, test inputs must construct expressions directly rather than call `sympify()` on string expressions.
- An assumptions test must compare with `is True`, `is False`, or `is None`, not rely on truthiness.
- If a test intentionally exercises floating-point behavior, it must use an explicit float literal such as `0.5`, not integer division such as `1/2`.

## Specialized changes

- When SymPy library code imports an optional dependency, it must use `sympy.external.import_module()` rather than importing the dependency directly.
- SymPy tests must use wrappers from `sympy.testing.pytest` instead of calling pytest functions directly.
- A test requiring an optional dependency must remain runnable without that dependency by calling `sympy.testing.pytest.skip("<reason>")` or, for an entire file, setting `skip = True`.
- A necessary backwards-incompatible API change must document how users should update their code.
- During the deprecation period, the old API must continue functioning unchanged except for an emitted, suppressible warning.
- A deprecation warning must be avoidable through a documented user-code migration and must not fire on the correct replacement API.
- During the deprecation period, users must have a replacement usage that stops the warning in the same SymPy version.
- Before adding a deprecation, the contributor must replace every internal and doctest use of the deprecated behavior with the new API.
- A `sympy_deprecation_warning(...)` message must state the fully contextualized deprecated API and its replacement.
- A deprecation call or decorator must set `deprecated_since_version` to the version in `sympy/release.py` without `.dev`.
- A deprecation call or decorator must set `active_deprecations_target` to its cross-reference target in `doc/src/explanation/active-deprecations.md`.
- A `sympy_deprecation_warning(...)` call must set `stacklevel` so the console warning points to the user's calling line.
- Every relevant docstring must include a `.. deprecated:: <version>` note for the deprecation.
- Every deprecation must add a section under the applicable version in `doc/src/explanation/active-deprecations.md`.
- The active-deprecation section must define a unique `(…deprecation…)=` or `(…deprecated…)=` cross-reference target before its header.
- A deprecation must add a test whose deprecated call is enclosed by `with warns_deprecated_sympy():` and verifies both the warning and continued behavior.
- Before submission, the contributor must run `python bin/test` and confirm the deprecation test passes and no other code emits `SymPyDeprecationWarning`.
- Code must not instantiate or emit `SymPyDeprecationWarning` directly; it must use `sympy_deprecation_warning(...)` or, for a whole function/method, `@deprecated(...)`.
- A `sympy_deprecation_warning(...)` message must be no more than one paragraph and wrap prose to 80 characters except unwrappable code.
- A `sympy_deprecation_warning(...)` message must explain migration but must not contain rationale, internal details, version metadata, or an active-deprecations URL already supplied by arguments.
- A deprecation warning message must be plain text without RST or Markdown markup.
- If an entire function is deprecated, its `.. deprecated:: <version>` directive must appear immediately below the docstring summary.
- A docstring `.. deprecated:: <version>` note must be at most one paragraph and state both the deprecated feature and its replacement.
- An active-deprecations section must explain what is deprecated, its replacement, and why the change was made.
- An active-deprecations entry must use a level-3 heading named for the deprecated item under the corresponding version, normally near the file top.
- If a deprecated object is not exported from top-level `sympy`, its active-deprecations entry must identify its defining submodule.
- A deprecation or removal after its deprecation period must include a `BREAKING CHANGE` entry inside the pull request's release-notes block.

## Documentation and docstrings

- A doctest must not use `from sympy import *`; it must import every used SymPy name explicitly.
- When validating documentation with locally installed dependencies, the contributor must run `cd doc` and then `make html`, and the build must succeed.
- If the PDF documentation build fails, the contributor must ensure code is delimited with double backticks rather than single backticks.
- A docstring must use triple double quotes.
- If a docstring contains a backslash, it must use a raw triple-double-quoted string.
- A docstring must contain a blank line immediately before its closing quotes.
- A class-level docstring must appear immediately under its class definition.
- Python example code in a docstring must be formatted as a doctest, not a `::` code block.
- A documentation contribution must produce no Sphinx errors when built locally with `cd doc; make html` or with `docker run --rm -v /absolute/path/to/sympy:/sympy sympy_htmldoc` after substituting the actual checkout path.
- Function, class, and method docstrings should order sections as Summary, Explanation, Examples, Parameters, See Also, References.
- Supported docstring section names must remain exact, including plural `Examples` even for one example.
- A docstring section heading must be underlined by the same number of equals signs as heading characters.
- Every docstring must begin with a single-sentence summary.
- A docstring summary must occupy one line and end with a period.
- Every docstring must contain an `Examples` section.
- An Examples section must contain a blank line immediately before its first doctest.
- Multiple docstring examples must be separated by blank lines.
- Explanatory text between doctests must have blank lines both before and after it.
- A doctest input longer than 80 characters must be wrapped as valid Python using the `...` continuation prompt.
- After adding or changing a docstring example, the contributor must run `python bin/doctest <file-or-submodule>` or `python bin/doctest` and fix every failure.
- If the documented signature lists parameters, the docstring must include a `Parameters` section.
- Parameter names in a Parameters section must use double-backtick code markup.
- A typed parameter entry must format its separator as `name : type`; omit the colon when no type is supplied.
- If a See Also description spans multiple lines, every continuation line must be indented.
- A See Also section must contain only SymPy functions, classes, or methods; external links belong in prose or References.
- In See Also, a class must be written as its bare class name, not `class:Name`, `class:`Name``, or `:class:`Name``.
- A References section must number citations from 1 in first-citation order.
- A paper reference with a DOI must include that DOI as a clickable hyperlink.
- For a mathematical-function class, documentation must live at class level and the `eval` method must not have its own docstring.
- Prose references to documented SymPy objects must use Sphinx cross-reference syntax, normally `:obj:`~.name`` for top-level public objects.
- A SymPy object not exported from top-level `sympy` must be cross-referenced by its full path down to the defining file and must not use `~.` abbreviation.
- Python built-ins, external-library objects, parameters, and other unlinkable names must use double-backtick code markup rather than `:obj:`.
- A custom-text object link must use `:obj:`custom text <object>`` syntax and must not include `~` in the target.
- A contributor must not use Markdown for non-narrative documentation.
- Docstrings should use reStructuredText syntax, not Markdown.
- If a docstring contains LaTeX, it must be a raw string.
- Verbatim code in RST documentation must be enclosed in double backticks, as in ``code``.
- An RST section heading underline, and optional overline, must use one repeated punctuation character and be at least as long as the heading text.
- Narrative SymPy documentation must use American spelling and punctuation.
- SymPy documentation must use gender-neutral `they` instead of `he` or `she`.

## AI-assisted contribution policy

- A contributor must be able to explain the code they submit.
- A contributor must not use AI to automatically generate the description or explanation of their contribution.
- If a contributor substantially uses AI while developing a patch, the pull request must disclose how AI was used.
- If a patch contains substantially AI-assisted code, the pull request must identify which code is AI generated.
- A contributor must not submit code that is fully or mostly AI generated without sufficient human authorship and oversight.
- In developer email, discussions, issues, pull requests, and similar communication, a contributor must not use AI to speak for them except for translation or grammar editing.

## Code and quality

- Before merge, a contribution must pass `python bin/test quality`.
- Before merge, a contribution must pass `flake8 sympy/`.
- Before merge, a contribution must pass `ruff check sympy`.

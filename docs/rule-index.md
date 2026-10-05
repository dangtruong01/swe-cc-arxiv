# Rule index — the corpus text beside the predicate

**Generated** by `tools/rule_index.py`; edit the code or the corpus, not this file.

For each implemented rule: what the corpus says, what the checker decided it means, and
where that decision lives. The review question is whether column 2 is a fair reading of
column 1 — see [How the checkers are written](how-checkers-are-written.md) for the
authoring model, and the [README](../README.md#reviewing-a-predicate--the-job) for how to
disagree productively.

- **Pre-condition** *selects* — does this rule apply to what the agent did?
- **Pass condition** *grades* — given that it applies, did the agent get it right?
- A pre-condition must fire on the rule's **antecedent**, never on the artefact it
  demands. *"When X, do Y"* triggers on **X**. This has been the most common bug.
- `heuristic` marks a lexical proxy for something not mechanically decidable. Its rate is
  not to be read as exact.
- `reads` names the evidence it consumes; a rule may withhold only when something it
  declares here is missing.


**823 rules implemented across 12 repositories.** 529 flagged `heuristic`.

| repository | rules | heuristic |
|---|---:|---:|
| [astropy](#astropy) | 111 | 94 |
| [django](#django) | 78 | 43 |
| [matplotlib](#matplotlib) | 167 | 137 |
| [mwaskom](#mwaskom) | 2 | 0 |
| [pallets](#pallets) | 34 | 22 |
| [psf](#psf) | 13 | 10 |
| [pydata](#pydata) | 35 | 18 |
| [pylint-dev](#pylint-dev) | 49 | 23 |
| [pytest-dev](#pytest-dev) | 22 | 13 |
| [scikit-learn](#scikit-learn) | 146 | 121 |
| [sphinx-doc](#sphinx-doc) | 24 | 14 |
| [sympy](#sympy) | 142 | 34 |


# astropy

| category | rules |
|---|---:|
| [Git and commit conventions](#astropy-git-and-commit-conventions) | 3 |
| [PR and release metadata](#astropy-pr-and-release-metadata) | 5 |
| [Tests and test style](#astropy-tests-and-test-style) | 30 |
| [Specialized changes](#astropy-specialized-changes) | 25 |
| [Documentation and docstrings](#astropy-documentation-and-docstrings) | 26 |
| [AI-assisted contribution policy](#astropy-ai-assisted-contribution-policy) | 2 |
| [Code and quality](#astropy-code-and-quality) | 4 |
| [Language and framework style](#astropy-language-and-framework-style) | 16 |


## astropy — Git and commit conventions

### ASTROPY-C059 — `ClosesIssueOnALaterLine`

> **Corpus:** Put ``Closes #<issue>`` on the second or a later line of the commit message when the commit fixes an issue.

- **Pre-condition —** each commit the agent made, read as a commit that fixes an issue.
- **Pass condition —** an auto-closing ``Closes #<issue>`` reference appears on the second or a later line of its message.

Heuristic on the **pre-condition** (§6.3). The sentence's antecedent is *the commit fixes an issue*, and nothing in the bundle establishes that: the task's provenance is a fact about the benchmark, not about the contribution, so every commit is selected and the activation rate is pushed up by commits that fix nothing. Narrowing it to commits that already carry a reference would be §7.1 inverted. The line position is graded exactly. A reference on the summary line alone is a violation, because that is what the sentence forbids.


`heuristic` · ownership `created` · reads `commits` · tier `static`

[`compliance/rules/astropy/git_conventions.py:59`](../compliance/rules/astropy/git_conventions.py#L59) · source: https://docs.astropy.org/en/latest/development/development_details.html

### ASTROPY-C067 — `CiSkipOnCommitsNotReadyForCi`

> **Corpus:** Put ``[ci skip]`` or ``[skip ci]`` in the commit message when the commits are not ready for CI.

- **Pre-condition —** each commit the agent marked as work in progress, which is what a commit not ready for CI looks like.
- **Pass condition —** its message also carries ``[ci skip]`` or ``[skip ci]``.

Heuristic on the **pre-condition** (§6.3): *not ready for CI testing* is an intention, and the only trace it leaves is the vocabulary a contributor uses for it -- WIP, draft, do not merge. Selecting every commit instead would grade a token that most commits must **not** carry, so nearly every compliant run would read as a violation; selecting the commits that already carry the token would be §7.1 inverted. Under-firing is the chosen direction and it is declared.


`heuristic` · ownership `created` · reads `commits` · tier `static`

[`compliance/rules/astropy/git_conventions.py:97`](../compliance/rules/astropy/git_conventions.py#L97) · source: https://docs.astropy.org/en/latest/development/development_details.html

### ASTROPY-C216 — `CiSkipOnTrivialDocumentationFix`

> **Corpus:** Include ``[ci skip]`` in the commit message for a trivial documentation fix.

- **Pre-condition —** each commit of a contribution that changes documentation only and introduces no reStructuredText markup, which is what a trivial documentation fix looks like.
- **Pass condition —** its message carries ``[ci skip]``.

Heuristic on the **pre-condition** (§6.3), but only half of it is a proxy. CONTRIBUTING gives three conditions -- typo, spelling or grammar; no special markup; not associated with code changes -- and the second and third are decidable from the patch and are checked exactly. *Typo, spelling or grammar* is not, so a substantive documentation rewrite in plain prose is selected here and should not be.


`heuristic` · ownership `created` · reads `commits, files` · tier `static`

[`compliance/rules/astropy/git_conventions.py:130`](../compliance/rules/astropy/git_conventions.py#L130) · source: https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md


## astropy — PR and release metadata

### ASTROPY-C061 — `ChangelogFragmentAdded`

> **Corpus:** Add a changelog fragment under ``docs/changes/<sub-package>/`` describing your change.

- **Pre-condition —** the contribution changes something that is neither documentation nor a test, which is what a change needing a changelog entry looks like.
- **Pass condition —** it adds a file under ``docs/changes/``.

Heuristic on the **pre-condition** (§6.3). CONTRIBUTING exempts "minor documentation or test updates" and "fixes to bugs introduced in the developer version". The first exemption is decidable from the patch and is applied; the second is a fact about when the bug was introduced, which nothing in the bundle carries, so a fix to an unreleased regression is selected here and should not be. Firing on the fragment instead of on the change would be §7.1 inverted: a contribution that adds no fragment would find no target and be recorded as compliant.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/pr_metadata.py:54`](../compliance/rules/astropy/pr_metadata.py#L54) · source: https://docs.astropy.org/en/latest/development/development_details.html

### ASTROPY-C062 — `ChangelogFragmentIsNamedCorrectly`

> **Corpus:** Name the changelog fragment ``<PR number>.<feature|api|bugfix|perf|other>.rst``.

- **Pre-condition —** each changelog fragment the agent added under ``docs/changes/``.
- **Pass condition —** its file name is ``<PR number>.<feature|api|bugfix|perf|other>.rst``.

Not heuristic: the corpus sentence enumerates the five types and the pre-commit ``changelogs-rst`` hook encodes the same pattern, so there is exactly one right shape and it is compared against exactly. Scoped ``created`` because naming a file is a decision taken when it is brought into existence; a fragment that was already in the tree is not the agent's naming.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/pr_metadata.py:94`](../compliance/rules/astropy/pr_metadata.py#L94) · source: https://docs.astropy.org/en/latest/development/development_details.html

### ASTROPY-C063 — `NoSingleBackticksInChangelogFragments`

> **Corpus:** Do not use single backticks for API reference links in changelog fragments.

- **Pre-condition —** each changelog fragment the agent wrote or edited.
- **Pass condition —** the text it added carries no single-backtick span.

Heuristic on the **pass condition** (§6.2): the sentence prohibits single backticks used *as API reference links*, and a single-backtick span is a proxy for that intent -- reST's default role would render one as a reference, but a fragment could in principle use it for something else. Explicit roles are stripped before the search, because ``:class:`~astropy.table.Table``` is the sanctioned form and matching its backticks would report the correct spelling as the violation. Selecting fragments rather than fragments-containing-backticks is what lets a well-written fragment record a pass (§7.1).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/pr_metadata.py:123`](../compliance/rules/astropy/pr_metadata.py#L123) · source: https://docs.astropy.org/en/latest/development/development_details.html

### ASTROPY-C237 — `ChangelogFragmentsAreFullSentences`

> **Corpus:** Write changelog fragments as full sentences with correct case and punctuation.

- **Pre-condition —** each changelog fragment the agent wrote or edited that has text.
- **Pass condition —** every paragraph in the text it added opens with a capital letter and closes with a terminator.

Heuristic on the **pass condition** (§6.2): case and final punctuation stand in for "full sentences with correct case and punctuation", which is a property of the grammar and not of the first and last character. A paragraph opening with an inline literal -- ```Quantity`` now supports ...`` -- is accepted rather than judged, because its case is fixed by the code name and not by the writer.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/pr_metadata.py:158`](../compliance/rules/astropy/pr_metadata.py#L158) · source: https://github.com/astropy/astropy/blob/main/docs/changes/README.rst

### ASTROPY-C240 — `OtherFragmentsLiveInTheRootDirectory`

> **Corpus:** Put ``other``-type changelog fragments only in the root ``docs/changes/`` directory.

- **Pre-condition —** each ``other``-type changelog fragment the agent added.
- **Pass condition —** it sits directly in ``docs/changes/`` and not in a sub-directory.

Not heuristic: the type is in the file name and the directory is in the path, so both halves are read off the patch exactly. The pre-condition selects on the type, which is the situation the prohibition speaks to -- a fragment of any other type is simply not what the sentence is about, and finds no target here.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/pr_metadata.py:197`](../compliance/rules/astropy/pr_metadata.py#L197) · source: https://github.com/astropy/astropy/blob/main/docs/changes/README.rst


## astropy — Tests and test style

### ASTROPY-C001 — `TestsCloseTheFilesTheyOpen`

> **Corpus:** Close every file a test opens so no unhandled ResourceWarning is raised.

- **Pre-condition —** each test the agent wrote or edited that opens a file.
- **Pass condition —** every open is closed -- a ``with`` statement, or a ``close`` call.

Heuristic on the **pass condition** (§6.2), and the corpus files this rule ``differential`` for a good reason: what the rule is really about is a ``ResourceWarning`` at run time. It is graded statically all the same, because an open with no ``with`` and no ``close`` is visible in the source and withholding would cost the rule its entire fail path. A file handed to a helper that closes it reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/astropy/tests.py:1189`](../compliance/rules/astropy/tests.py#L1189) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C002 — `TestModulesAreNamedForDiscovery`

> **Corpus:** Name test modules ``test_*.py`` or ``*_test.py``.

- **Pre-condition —** each Python module the agent added inside a ``tests`` directory.
- **Pass condition —** its name is ``test_*.py`` or ``*_test.py``.

Not heuristic: pytest's two discovery patterns are quoted in the corpus sentence and compared against exactly. Selecting on *location* rather than on the name is what makes the rule able to fail -- a pre-condition keyed on the name would select only modules that already comply (§7.1). ``__init__.py`` and ``conftest.py`` are excluded because pytest never collects them as test modules.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:261`](../compliance/rules/astropy/tests.py#L261) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C003 — `TestFunctionsArePrefixed`

> **Corpus:** Prefix test functions and methods with ``test_``.

- **Pre-condition —** each function the agent added to a test module that asserts something or carries a pytest marker.
- **Pass condition —** its name starts with ``test_``.

Heuristic on the **pre-condition** (§6.3): *a test function* is approximated by one that makes an assertion or is decorated, because keying on the name would select only the compliant form and the rule could never fail (§7.1). A helper that happens to assert is selected here and is not a test.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:295`](../compliance/rules/astropy/tests.py#L295) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C004 — `TestClassesArePrefixedAndHaveNoInit`

> **Corpus:** Give test classes a ``Test`` prefix and no ``__init__`` method.

- **Pre-condition —** each class the agent added to a test module that holds test methods.
- **Pass condition —** its name starts with ``Test`` and it defines no ``__init__``.

Heuristic on the **pre-condition** (§6.3): *a test class* is approximated by one whose methods assert or are named for tests, because keying on the ``Test`` prefix would select only the compliant form (§7.1). A fixture-holding base class whose methods assert is selected here and is not itself collected.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:326`](../compliance/rules/astropy/tests.py#L326) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C006 — `SubPackageTestsLiveInItsTestsDirectory`

> **Corpus:** Put a sub-package's tests in that sub-package's own ``tests/`` directory.

- **Pre-condition —** each test module the agent added inside ``astropy/``.
- **Pass condition —** it sits in a ``tests`` directory.

Not heuristic: both halves are read off the path. Selecting on the module being a test -- by name or by location -- rather than on its directory is what lets a correctly placed module record a pass (§7.1).


ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:373`](../compliance/rules/astropy/tests.py#L373) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C007 — `TestsDirectoriesCarryAnInitFile`

> **Corpus:** Include an ``__init__.py`` file in every ``tests`` directory.

- **Pre-condition —** each ``tests`` directory the agent added a file to.
- **Pass condition —** an ``__init__.py`` for it is in the contribution, or the contribution also edits a file that was already there.

Heuristic on the **pass condition** (§6.2): the tree outside the patch is not visible, so "the directory has an ``__init__.py``" is inferred -- either the contribution adds one, or it edits a pre-existing file in the same directory, which shows the directory already existed and therefore already has one. A brand-new tests directory with no ``__init__.py`` is the case this really catches.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:400`](../compliance/rules/astropy/tests.py#L400) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C008 — `CrossSubPackageTestsLiveInAstropyTests`

> **Corpus:** Put tests that span two or more sub-packages in ``astropy/tests/``.

- **Pre-condition —** each test module the agent added that imports from two or more astropy sub-packages.
- **Pass condition —** it sits in ``astropy/tests/``.

Heuristic on the **pre-condition** (§6.3): *involving two or more sub-packages* is approximated by what the module imports, which over-fires on a test that imports a second sub-package only for a helper, and under-fires on one that reaches another sub-package through the object it is given.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:441`](../compliance/rules/astropy/tests.py#L441) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C010 — `RegressionTestsCiteTheIssueUrl`

> **Corpus:** Include the URL of the reported issue in the regression test.

- **Pre-condition —** each test the agent added alongside a change to library code, which is what a regression test looks like.
- **Pass condition —** the test carries the URL of the report.

Heuristic on **both layers** (§6.1). *A regression test* is approximated by a test added in the same contribution as a source change, so a test added with a new feature is selected too. And the URL is looked for anywhere in the test's text, so a bare issue number -- which is not what the sentence asks for -- reads as missing.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:484`](../compliance/rules/astropy/tests.py#L484) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C012 — `RemoteDataTestsAreMarked`

> **Corpus:** Mark any test that retrieves remote data with ``@pytest.mark.remote_data``.

- **Pre-condition —** each test the agent wrote or edited that reaches the network.
- **Pass condition —** it carries ``@pytest.mark.remote_data``.

Heuristic on the **pre-condition** (§6.3): *may retrieve remote data* is approximated by the download helpers astropy tests use and by a URL literal in the body. A test that fetches through a helper of its own is missed, and one that merely mentions a URL in a comment is over-selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:523`](../compliance/rules/astropy/tests.py#L523) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C013 — `RemoteDoctestsCarryTheRemoteDataFlag`

> **Corpus:** Flag a doctest that retrieves remote data with ``# doctest: +REMOTE_DATA``.

- **Pre-condition —** each doctest example the agent wrote that retrieves remote data.
- **Pass condition —** its prompt line carries ``# doctest: +REMOTE_DATA``.

Heuristic on the **pre-condition** (§6.3), the same approximation C012 makes for test functions: remote retrieval is recognised by a URL literal or by one of astropy's download helpers appearing in the example's source.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:849`](../compliance/rules/astropy/tests.py#L849) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C014 — `TestsWriteIntoTmpPath`

> **Corpus:** Write files created by a test into the ``tmp_path`` fixture directory rather than a permanent location.

- **Pre-condition —** each test the agent wrote or edited that creates a file.
- **Pass condition —** it takes a temporary-directory fixture and uses it.

Heuristic on **both layers** (§6.1). *Writing a file* is approximated by the call names that do it -- ``open`` in a writing mode, ``writeto``, ``savefig``, ``write_text`` -- so a test writing through something else is missed. And using the fixture is approximated by requesting it as a parameter, which does not prove the path written to was derived from it.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:558`](../compliance/rules/astropy/tests.py#L558) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C016 — `OptionalDependencyTestsAreSkippable`

> **Corpus:** Skip a test that needs an optional dependency when that dependency is absent.

- **Pre-condition —** each test the agent wrote or edited that uses an optional dependency.
- **Pass condition —** it is skipped when the dependency is absent -- a ``skipif`` marker or an ``importorskip`` call.

Heuristic on the **pre-condition** (§6.3): *requires an optional dependency* is approximated by a list of the packages astropy treats as optional, appearing in the test's own text or among the module's imports. A dependency outside the list is missed.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:603`](../compliance/rules/astropy/tests.py#L603) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C017 — `SkipConditionsComeFromTheHasFlags`

> **Corpus:** Take the skip condition from the ``HAS_*`` flags in ``astropy.utils.compat.optional_deps``.

- **Pre-condition —** each skip condition the agent wrote on a test.
- **Pass condition —** it is one of the ``HAS_*`` flags from ``astropy.utils.compat.optional_deps``.

Selecting every skip condition, rather than the ones already using a flag, is what lets a correct one record a pass (§7.1). Heuristic on the **pass condition** (§6.2): a name matching ``HAS_*`` is accepted even when the import table does not resolve it to ``optional_deps``, because the flag may be re-exported. A locally defined ``HAS_THING`` therefore passes.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:647`](../compliance/rules/astropy/tests.py#L647) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C020 — `WarningsAreAssertedWithPytestWarns`

> **Corpus:** Assert expected warnings with the ``pytest.warns`` context manager.

- **Pre-condition —** each place a test the agent wrote checks that a warning is raised.
- **Pass condition —** it uses the ``pytest.warns`` context manager.

Heuristic on the **pre-condition** (§6.3): *testing that a warning is triggered* is approximated by the ways of doing it -- ``pytest.warns``, ``catch_warnings``, the ``recwarn`` fixture, numpy's ``assert_warns``. A test that inspects warnings some other way is not selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:691`](../compliance/rules/astropy/tests.py#L691) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C021 — `ExceptionsAreAssertedWithPytestRaises`

> **Corpus:** Assert expected exceptions with the ``pytest.raises`` context manager.

- **Pre-condition —** each place a test the agent wrote checks that an exception is raised.
- **Pass condition —** it uses the ``pytest.raises`` context manager.

Heuristic on the **pre-condition** (§6.3): *designed to trigger an error* is approximated by the assertion helpers a test uses -- ``pytest.raises``, unittest's ``assertRaises``, numpy's ``assert_raises``. A test that catches the exception by hand and asserts on it is not selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:732`](../compliance/rules/astropy/tests.py#L732) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C023 — `CoveragePragmasAreSpelledCorrectly`

> **Corpus:** Mark a block excluded from coverage with a ``# pragma: no cover`` comment at its start.

- **Pre-condition —** each ``# pragma`` comment the agent wrote in Python.
- **Pass condition —** it reads ``pragma: no cover`` and sits on the line that opens the block it excludes.

Selecting every pragma, rather than the correctly spelled ones, is what makes the rule able to fail: a misspelled pragma excludes nothing and is exactly the mistake worth catching (§7.1). Heuristic on the **pass condition** (§6.2): "at the start of the block" is approximated by the pragma sitting on a line that opens a block, or on the first line of one. A pragma placed correctly in a shape this does not recognise reads as a violation.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:769`](../compliance/rules/astropy/tests.py#L769) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C024 — `FigureTestsUseTheConvenienceDecorator`

> **Corpus:** Decorate figure tests with ``@figure_test`` from ``astropy.tests.figures`` rather than ``@pytest.mark.mpl_image_compare``.

- **Pre-condition —** each figure test the agent wrote or edited, in either form.
- **Pass condition —** it is decorated with ``@figure_test``.

Not heuristic: the sentence names both decorators, so *a figure test* is a category the rule itself defines and the pre-condition selects on it exactly. Selecting only the ``mpl_image_compare`` form would make every target a violation (§7.1).


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:815`](../compliance/rules/astropy/tests.py#L815) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C025 — `DoctestExamplesRunCorrectly`

> **Corpus:** Write docstring and narrative examples so they run correctly as doctests.

- **Pre-condition —** each doctest example the agent wrote or edited.
- **Pass condition —** it runs, and its output matches what the example claims.

Graded **one-sidedly**. An example whose source is not valid Python cannot run, and that is decidable from the patch and conclusive -- so the rule fails on it. Whether a syntactically valid example produces the output it claims is exactly what executing the doctests answers and nothing static does, so the rule declares ``doctest_run`` and withholds. It never passes vacuously.


ownership `touched` · reads `files, doctest_run` · tier `differential`

[`compliance/rules/astropy/tests.py:884`](../compliance/rules/astropy/tests.py#L884) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C026 — `NonExecutableExamplesAreSkipped`

> **Corpus:** Mark a non-executable doctest example with ``# doctest: +SKIP``.

- **Pre-condition —** each doctest example the agent wrote that looks non-executable, and each one already marked skipped.
- **Pass condition —** its prompt line carries ``# doctest: +SKIP``.

The already-marked examples are in the pre-condition deliberately: without them it would select only examples that fail, and the rule could never record a compliant one (§7.1). Heuristic on the **pre-condition** (§6.3): *looks like a doctest but is not executable verbatim* is approximated by placeholder text -- ``path/to``, ``your_file``, an angle-bracket stand-in. An example that cannot run for a subtler reason is not selected.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:920`](../compliance/rules/astropy/tests.py#L920) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C027 — `DoctestSkipIsAModuleLevelListOfPatterns`

> **Corpus:** Skip a module's doctests by listing wildcard patterns in a module-level ``__doctest_skip__``.

- **Pre-condition —** each ``__doctest_skip__`` assignment the agent wrote.
- **Pass condition —** it is at module level and its value is a list of wildcard patterns.

Not heuristic: the variable name, its position and the shape of its value are all read off the syntax tree, and the sentence states each of them. A dict, a bare string or an assignment inside a function is a violation.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:959`](../compliance/rules/astropy/tests.py#L959) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C028 — `DoctestRequiresIsAModuleLevelDictionary`

> **Corpus:** Declare a doctest's optional-dependency requirements in a module-level ``__doctest_requires__`` dictionary.

- **Pre-condition —** each ``__doctest_requires__`` assignment the agent wrote.
- **Pass condition —** it is at module level and its value is a dictionary.

Not heuristic, for the same reasons as C027: the name, the position and the type of the value are all stated in the sentence and all read off the syntax tree.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:989`](../compliance/rules/astropy/tests.py#L989) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C029 — `NarrativeDoctestsAreSkippedWithTheDirective`

> **Corpus:** Skip a doctest block in narrative documentation with the ``.. doctest-skip::`` directive (or ``.. doctest-skip-all``).

- **Pre-condition —** each attempt in narrative documentation to stop a doctest block running, in either form.
- **Pass condition —** it is the ``.. doctest-skip::`` directive, or ``doctest-skip-all``.

Heuristic on the **pre-condition** (§6.3): the alternative form is recognised as a ``# doctest: +SKIP`` comment inside a ``.rst`` page, which is how someone reaches for the docstring mechanism in narrative text. A third way of trying to skip is not selected.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:1037`](../compliance/rules/astropy/tests.py#L1037) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C030 — `NarrativeDoctestsAreGatedWithTheDirective`

> **Corpus:** Gate a doctest block in narrative documentation on a dependency with the ``.. doctest-requires::`` directive.

- **Pre-condition —** each attempt in narrative documentation to gate a doctest block on a dependency, in either form.
- **Pass condition —** it is the ``.. doctest-requires::`` directive.

Heuristic on the **pre-condition** (§6.3), the mirror of C029: the alternative form is recognised as the module-level ``__doctest_requires__`` name appearing inside a ``.rst`` page, which is the mechanism for docstrings rather than for narrative text.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:1075`](../compliance/rules/astropy/tests.py#L1075) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C032 — `IgnoredOutputUsesTheIgnoreOutputFlag`

> **Corpus:** Ignore a doctest's output entirely with the ``# doctest: +IGNORE_OUTPUT`` flag.

- **Pre-condition —** each doctest example the agent wrote whose expected output is elided wholesale, in either form.
- **Pass condition —** its prompt line carries ``# doctest: +IGNORE_OUTPUT``.

Heuristic on the **pre-condition** (§6.3): *ignoring the output entirely* is recognised either by the flag itself or by the expected output being nothing but an ellipsis, which is the other way people write it. An example that elides output some third way is not selected.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:1113`](../compliance/rules/astropy/tests.py#L1113) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C033 — `FloatingPointOutputUsesFloatCmp`

> **Corpus:** Compare floating-point doctest output with the ``# doctest: +FLOAT_CMP`` flag.

- **Pre-condition —** each doctest example the agent wrote whose expected output contains a floating-point number.
- **Pass condition —** its prompt line carries ``# doctest: +FLOAT_CMP``.

Heuristic on the **pre-condition** (§6.3): *output that needs a float comparison* is approximated by a decimal number appearing in the expected output, which over-fires on a value that is exact in every environment -- a version string, a count written with a decimal point.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:1150`](../compliance/rules/astropy/tests.py#L1150) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C036 — `RemoteDataTestsAreRunWithTheFlag`

> **Corpus:** Run the tests with ``--remote-data`` when the bug involves remote data access.

- **Pre-condition —** the contribution touches remote data access, which is when the flag is needed.
- **Pass condition —** a test run with ``--remote-data`` appears in the command log.

The pre-condition fires on the **bug involving remote data**, not on the invocation (§7.1, §7.2): firing on the flag would find only agents that already complied. Heuristic on the **pre-condition** (§6.3): *the bug involves remote data access* is approximated by the contribution touching a remote-data marker or one of astropy's download helpers, which is what such work looks like in a patch.


`heuristic` · ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/astropy/tests.py:1236`](../compliance/rules/astropy/tests.py#L1236) · source: https://docs.astropy.org/en/latest/development/git_edit_workflow_examples.html

### ASTROPY-C037 — `ATestFailsBeforeAndPassesAfter`

> **Corpus:** Write a test that fails before the fix and passes after it.

- **Pre-condition —** the contribution changes library code, which is what a fix does.
- **Pass condition —** it also ships a test, and that test fails before the change and passes after it.

Graded **one-and-a-half-sidedly**, and deliberately. A fix with no test at all is failed here, because no run is needed to establish that no test can have gone from failing to passing -- there is none. Where a test *is* present, whether it fails on the pre-fix code is exactly what a before-and-after run answers. The harness's own ``FAIL_TO_PASS`` bucket cannot stand in: it is computed from the benchmark's reference test patch, not from the test the agent wrote, so reading it would grade somebody else's test. The rule declares ``full_suite_run`` and withholds instead. Heuristic on the **pre-condition** (§6.3): "changes library code" is what a fix looks like in a patch, and so does a refactor.


`heuristic` · ownership `touched` · reads `files, full_suite_run` · tier `differential`

[`compliance/rules/astropy/tests.py:1275`](../compliance/rules/astropy/tests.py#L1275) · source: https://docs.astropy.org/en/latest/development/git_edit_workflow_examples.html

### ASTROPY-C056 — `NewCodeComesWithTests`

> **Corpus:** Add tests covering new code.

- **Pre-condition —** the contribution changes library code, which is the case the checklist's exemption -- "some changes, e.g. to documentation, do not need tests" -- leaves in.
- **Pass condition —** it also adds or changes a test module in the same sub-package.

Heuristic on the **pass condition** (§6.2): *covering* the new code is a coverage measurement, approximated here by a test module changed in the same sub-package as the source. A test added in the right place that exercises none of the new code passes, and that is the flag's whole meaning. What the check does establish exactly is the case invariant 2 cares about: a contribution that ships **no** test fails.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/astropy/tests.py:1318`](../compliance/rules/astropy/tests.py#L1318) · source: https://docs.astropy.org/en/latest/development/development_details.html

### ASTROPY-C201 — `EveryRaisedExceptionHasATest`

> **Corpus:** Add a test for every exception the new code raises.

- **Pre-condition —** each exception class the agent's written library code raises.
- **Pass condition —** a test in the contribution asserts that it is raised.

Heuristic on the **pass condition** (§6.2): the test is matched by the exception's name appearing in a test module's text, which does not establish that the test exercises *this* raise. Matching more tightly is not possible from a patch, and matching less tightly -- any test at all -- would make the rule meaningless.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/tests.py:1359`](../compliance/rules/astropy/tests.py#L1359) · source: https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md

### ASTROPY-C205 — `ToxTestEnvironmentPasses`

> **Corpus:** Make ``tox -e test`` run without failures.

- **Pre-condition —** the agent submitted Python, which is what gets run.
- **Pass condition —** the harness's own before-and-after run reports no test that passed before the change and fails after it.

Graded from a real execution rather than from a stand-in for one, which is what the ``differential`` tier asks for: a submitted module that will not parse fails without any run, and beyond that the verdict is the harness's report. Heuristic on the **pass condition** (§6.2), and this is where the check is weaker than the sentence. The harness executes the subset of the suite the benchmark instance names, so a clean report is evidence that *those* tests pass and not that ``tox -e test`` passes entire. Reported as a pass with that stated, rather than withheld: a rule that declines to grade on every run measures nothing, while the failing direction -- a regression -- is exact. ``EvalReport.regressions()`` is the single place the reading of ``tests_status`` is written down; ``PASS_TO_FAIL`` merely looks like it means that.


`heuristic` · ownership `touched` · reads `files, evaluation` · tier `differential`

[`compliance/rules/astropy/tests.py:1406`](../compliance/rules/astropy/tests.py#L1406) · source: https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md


## astropy — Specialized changes

### ASTROPY-C018 — `NewOptionalDependencyGetsAHasFlag`

> **Corpus:** Add a ``HAS_*`` flag to ``astropy/utils/compat/optional_deps.py`` for any new optional dependency.

- **Pre-condition —** each package the contribution treats as an optional dependency.
- **Pass condition —** ``astropy/utils/compat/optional_deps.py`` gains a ``HAS_*`` flag for it.

Heuristic on the **pre-condition** (§6.3): *a new optional dependency* is not written anywhere, so it is approximated by the shape astropy gives one -- a third-party package imported inside a function or behind a ``try``, and not already among astropy's declared dependencies. A dependency introduced some other way is not selected. Firing on the flag instead of on the dependency would be §7.1 inverted: an agent that added neither would find no target and be recorded as compliant.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:233`](../compliance/rules/astropy/specialized.py#L233) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C019 — `NewOptionalDependencyIsInPyproject`

> **Corpus:** Record a new optional dependency in ``[project.optional-dependencies]`` in ``pyproject.toml``, under ``all`` for runtime use or ``test_all`` for test-only use.

- **Pre-condition —** each package the contribution treats as an optional dependency.
- **Pass condition —** ``pyproject.toml`` names it under ``[project.optional-dependencies]``.

Same approximated antecedent as C018 and the same reason for it (§6.3). The grading differs: the sentence names two groups, ``all`` for runtime use and ``test_all`` for test-only use, and either is accepted because which one applies depends on where the dependency is used -- a distinction the patch shows only weakly.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:267`](../compliance/rules/astropy/specialized.py#L267) · source: https://docs.astropy.org/en/latest/development/testguide.html

### ASTROPY-C078 — `AdditionalDependenciesAreDocumented`

> **Corpus:** Document any additional third-party dependency a sub-module or function introduces.

- **Pre-condition —** each third-party package the agent's written code introduces into a sub-module or function.
- **Pass condition —** the contribution's documentation mentions it.

Heuristic on **both layers** (§6.1). The pre-condition reads an added import as "introduces a dependency", which over-fires when the package was already used elsewhere in the sub-module. The pass condition accepts a mention anywhere in the manual pages or docstrings the contribution wrote, which is weaker than "noted in the package documentation" and cannot see documentation the contribution did not touch.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:301`](../compliance/rules/astropy/specialized.py#L301) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C080 — `OptionalDependenciesAreImportedInTheFunction`

> **Corpus:** Import an optional dependency with a plain ``import`` inside the function or method that uses it.

- **Pre-condition —** each import of a third-party package the agent wrote in library code.
- **Pass condition —** it is a plain ``import`` statement inside the function or method that uses it.

Selecting every third-party import, rather than the module-level ones, is what lets a correctly placed import record a pass (§7.1). An import behind a ``try`` is a violation here: the sentence asks for a plain statement precisely so the ``ImportError`` reaches the user. Heuristic on the **pre-condition** (§6.3): *optional* is approximated by *third-party*. A required third-party dependency imported at module level is selected here and is not what the sentence is about -- which is why C077, whose subject is exactly that, is a separate rule.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:342`](../compliance/rules/astropy/specialized.py#L342) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C091 — `PackageDataLivesInADataDirectory`

> **Corpus:** Put package data files in a ``data`` directory inside the sub-package.

- **Pre-condition —** each data file the agent added inside ``astropy/``.
- **Pass condition —** it sits in a ``data`` directory inside its sub-package.

Heuristic on the **pre-condition** (§6.3): *package data* is approximated by a file under the package that is not source, documentation or configuration. A data file with an unfamiliar extension placed outside a ``data`` directory is not selected, so the check under-reports rather than inventing violations.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:398`](../compliance/rules/astropy/specialized.py#L398) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C092 — `DataFilesStayUnderAboutOneHundredKilobytes`

> **Corpus:** Keep in-repository data files under about 100 kB and host anything larger off the repository.

- **Pre-condition —** each data file the agent added inside ``astropy/``.
- **Pass condition —** it is smaller than about 100 kB.

Heuristic on the **pass condition** (§6.2): the bundle carries a file's reconstructed text, not its size on disk, so the text's length stands in for the byte count. A binary file the harness could not reconstruct is undetermined rather than passed -- reporting a file we cannot measure as small would be the silent pass §2.2 forbids. "About" is the source's own hedge and is kept: the limit is applied at 100 kB with no tolerance invented on either side.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:426`](../compliance/rules/astropy/specialized.py#L426) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C093 — `PackageDataIsReadThroughGetPkgData`

> **Corpus:** Access package data through ``get_pkg_data_fileobj`` or ``get_pkg_data_filename``.

- **Pre-condition —** each call the agent wrote that reaches a package data file.
- **Pass condition —** it goes through ``get_pkg_data_fileobj`` or ``get_pkg_data_filename``.

Heuristic on the **pre-condition** (§6.3): *accessing package data* is approximated by a call carrying a string that names a data file or a ``data`` directory, plus the ``get_pkg_data_*`` calls themselves. Selecting only the raw ``open`` calls would make every target a violation (§7.1); selecting only the sanctioned ones would make every target a pass.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:462`](../compliance/rules/astropy/specialized.py#L462) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C094 — `SpecificDataVersionsArePinnedByHash`

> **Corpus:** Pin a specific version of a data file with the ``astropy.utils.data`` hash mechanism.

- **Pre-condition —** each call the agent wrote that fetches a remotely hosted data file.
- **Pass condition —** it names the file by the ``hash/...`` form, or passes a hash argument.

Heuristic on the **pre-condition** (§6.3): the sentence's antecedent is *a specific version of a data file is needed*, which is an intention. It is approximated by fetching remote data at all, on the reading that a remote file whose content can change is exactly when the version matters. That over-fires on a fetch where any version will do.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:503`](../compliance/rules/astropy/specialized.py#L503) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C095 — `PersistentConfigurationUsesAstropyConfig`

> **Corpus:** Implement persistent configuration through the ``astropy.config`` mechanism.

- **Pre-condition —** each place the agent's written code persists configuration.
- **Pass condition —** it does so through ``astropy.config`` -- a ``ConfigItem`` or a ``ConfigNamespace``.

Heuristic on the **pre-condition** (§6.3): *persistent configuration* is approximated by the calls that write or declare it -- astropy's own two, and the general-purpose alternatives a contributor might reach for instead (``configparser``, a dumped JSON or YAML file, a pickle). A configuration mechanism outside that vocabulary is not selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:561`](../compliance/rules/astropy/specialized.py#L561) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C096 — `ConfigurationItemsSitAtTheTopOfTheModule`

> **Corpus:** Declare configuration items at the top of the module or package that uses them.

- **Pre-condition —** each ``ConfigItem`` or ``ConfigNamespace`` the agent declared.
- **Pass condition —** it appears before the module's first function or class that is not a configuration namespace.

Heuristic on the **pass condition** (§6.2): *the top of the module or package* is not a line number, and "before the first definition" stands in for it. A configuration item declared after a helper function but still visibly at the head of the file reads as a violation here.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:593`](../compliance/rules/astropy/specialized.py#L593) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C122 — `CythonSourcesAreCommitted`

> **Corpus:** Commit the ``.pyx`` sources of a Cython extension.

- **Pre-condition —** the contribution includes a Cython extension.
- **Pass condition —** a ``.pyx`` source is among the files it commits.

Heuristic on the **pre-condition** (§6.3): the build is not run here, so *a Cython extension* is approximated by the traces one leaves in a patch -- a ``.pyx`` file, a ``.c`` file that says Cython generated it, or a ``setup_package.py`` naming a ``.pyx``. A contribution with none of those finds no target, which is the honest reading for the overwhelming majority of runs.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:693`](../compliance/rules/astropy/specialized.py#L693) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C123 — `GeneratedCFilesAreNotCommitted`

> **Corpus:** Do not commit the ``.c`` files Cython generates.

- **Pre-condition —** each C source file the agent committed under ``astropy/``.
- **Pass condition —** it is not a file Cython generated.

Selecting every committed ``.c`` file, rather than the generated ones, is what lets a hand-written C extension record a pass (§7.1). Heuristic on the **pass condition** (§6.2): *generated by Cython* is recognised by the banner Cython writes into its output, or by a committed ``.pyx`` with the same stem. A generated file stripped of its banner and committed without its source reads as hand-written.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:731`](../compliance/rules/astropy/specialized.py#L731) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C124 — `ExternalCLibrariesAreBundled`

> **Corpus:** Bundle the source of an external C library a C extension depends on, if its license permits.

- **Pre-condition —** each C source the agent wrote that includes a header from outside the C standard library and outside Python's own.
- **Pass condition —** the contribution also bundles that library's source under ``cextern/``.

The sentence's condition -- *provided the licence for the C library is compatible* -- is a fact about the library and not about the patch, so it is **not** checked: a contribution that correctly declined to bundle an incompatibly-licensed library reads as a violation here. That is the reason for the ``heuristic`` flag together with the proxy for "depends on an external library", which is the ``#include`` line.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:769`](../compliance/rules/astropy/specialized.py#L769) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C125 — `BundledLibrariesCanBeReplacedBySystemCopies`

> **Corpus:** Let a bundled C library be replaced by the system copy through an ``ASTROPY_USE_SYSTEM_<LIB>`` environment variable.

- **Pre-condition —** the contribution adds or edits a bundled C library under ``cextern/``.
- **Pass condition —** something in it names an ``ASTROPY_USE_SYSTEM_<LIB>`` environment variable.

Not heuristic: both halves are exact. The antecedent is a path prefix the project fixes for bundled sources, and the pass condition is the presence of a variable whose spelling the sentence gives. What it does not check is that the build actually honours the variable, which is stated here rather than papered over with a flag.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:810`](../compliance/rules/astropy/specialized.py#L810) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C224 — `ConfigurationOptionsAreDocumented`

> **Corpus:** Document every configuration option added through ``astropy.config``.

- **Pre-condition —** each configuration option the agent added through ``astropy.config``.
- **Pass condition —** it carries a description, or the contribution's documentation mentions it.

Heuristic on the **pass condition** (§6.2): "explicitly mentioned in the documentation" is accepted in two forms, because astropy's own machinery renders a ``ConfigItem``'s description into the manual -- so the description *is* the documentation for most items. A mention in a manual page the contribution did not touch cannot be seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:640`](../compliance/rules/astropy/specialized.py#L640) · source: https://docs.astropy.org/en/latest/development/docguide.html

### ASTROPY-C225 — `GetExtensionsReturnsExtensionObjects`

> **Corpus:** Make ``get_extensions`` in ``setup_package.py`` return a list of ``setuptools.Extension`` objects.

- **Pre-condition —** each ``get_extensions`` function the agent wrote or edited in a ``setup_package.py``.
- **Pass condition —** it returns a list, and builds ``Extension`` objects to put in it.

Heuristic on the **pass condition** (§6.2): what a function returns at run time is not decidable from its text, so this reads the shape -- a ``return`` of a list or of a name, with an ``Extension`` construction somewhere in the body. A function that delegates the construction to a helper reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:845`](../compliance/rules/astropy/specialized.py#L845) · source: https://docs.astropy.org/en/latest/development/ccython.html

### ASTROPY-C226 — `CExtensionsAreDefinedThroughGetExtensions`

> **Corpus:** Define every C extension through the ``get_extensions`` mechanism.

- **Pre-condition —** the contribution adds or edits a C extension source under ``astropy/``.
- **Pass condition —** a ``setup_package.py`` in the contribution defines ``get_extensions``.

Heuristic on the **pre-condition** (§6.3): *a C extension* is approximated by a ``.c`` or ``.h`` file inside the package, which is what one looks like in a patch. A C extension added without any C source -- there is no such thing -- would be missed; a C file that is not part of an extension is over-selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:892`](../compliance/rules/astropy/specialized.py#L892) · source: https://docs.astropy.org/en/latest/development/ccython.html

### ASTROPY-C227 — `CythonExtensionsNameThePyxAsSource`

> **Corpus:** Give the ``.pyx`` files, not the generated ``.c`` files, as the source of a Cython extension.

- **Pre-condition —** each ``Extension(...)`` the agent wrote for a Cython module.
- **Pass condition —** its sources name the ``.pyx`` file rather than the generated ``.c``.

Heuristic on the **pre-condition** (§6.3): *a Cython extension* is recognised by the extension naming a ``.pyx`` source, or naming a ``.c`` whose stem matches a ``.pyx`` the contribution carries. An extension whose Cython origin is visible only to the build system is not selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:928`](../compliance/rules/astropy/specialized.py#L928) · source: https://docs.astropy.org/en/latest/development/ccython.html

### ASTROPY-C228 — `NumpyHeadersComeFromGetInclude`

> **Corpus:** Locate the numpy C headers with ``numpy.get_include()``.

- **Pre-condition —** each ``Extension(...)`` the agent wrote in a ``setup_package.py`` that mentions numpy.
- **Pass condition —** its include directories come from ``numpy.get_include()``.

Heuristic on the **pre-condition** (§6.3): *uses numpy at the C level* is approximated by the setup file mentioning numpy at all, which is the only trace a patch carries. An extension that needs the headers without the file naming numpy is not selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:968`](../compliance/rules/astropy/specialized.py#L968) · source: https://docs.astropy.org/en/latest/development/ccython.html

### ASTROPY-C229 — `InstallableHeadersLiveInAnIncludeDirectory`

> **Corpus:** Put a package's installable C header files in an ``include`` directory inside the package.

- **Pre-condition —** each C header the agent added inside ``astropy/``.
- **Pass condition —** it sits in an ``include`` directory inside its package.

Heuristic on the **pre-condition** (§6.3): the sentence is about headers that are *installed* for third-party C code to link against, and whether a header is meant to be installed is not written in the patch. Every added header is selected, so a private header kept beside its implementation reads as a violation.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:1009`](../compliance/rules/astropy/specialized.py#L1009) · source: https://docs.astropy.org/en/latest/development/ccython.html

### ASTROPY-C230 — `InstallableHeadersAreDeclaredAsPackageData`

> **Corpus:** Declare installable C header files in ``[tool.setuptools.package_data]`` in ``pyproject.toml``.

- **Pre-condition —** each C header the agent added in an ``include`` directory inside the package.
- **Pass condition —** ``pyproject.toml`` declares it under ``[tool.setuptools.package_data]``.

Heuristic on the **pass condition** (§6.2): the declaration is a glob, so this checks that the section exists and that a pattern in the contribution's ``pyproject.toml`` could cover the header -- the package's own name, or an ``include/`` pattern. It does not expand globs, so a correct but unusual pattern reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:1038`](../compliance/rules/astropy/specialized.py#L1038) · source: https://docs.astropy.org/en/latest/development/ccython.html

### ASTROPY-C231 — `SetupPackageDoesNotImportItsPackage`

> **Corpus:** Keep ``setup_package.py`` free of imports from the package it belongs to.

- **Pre-condition —** each ``setup_package.py`` the agent wrote or edited.
- **Pass condition —** it imports nothing from the package it belongs to.

Not heuristic: the import table says exactly what a module imports, and "from the package it belongs to" is decided by the top-level name and by whether the import is relative -- both read off the syntax tree. A ``setup_package.py`` that imports only third-party build tooling passes.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:1076`](../compliance/rules/astropy/specialized.py#L1076) · source: https://docs.astropy.org/en/latest/development/ccython.html

### ASTROPY-C233 — `ScriptsHaveAMainThatDelegates`

> **Corpus:** Give a command-line script a ``main`` function that parses arguments and delegates to a library function.

- **Pre-condition —** each command-line script the agent wrote or edited.
- **Pass condition —** it defines ``main``, and ``main`` calls a library function rather than doing the work itself.

Heuristic on **both layers** (§6.1). *A command-line script* is approximated by a module under a ``scripts/`` directory or one carrying an ``if __name__ == "__main__"`` block. *Delegates to a library function* is approximated by ``main`` calling something that is not argument parsing -- which a script whose work genuinely is one call would satisfy trivially, and which a well-factored ``main`` written as a single expression could fail.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:1121`](../compliance/rules/astropy/specialized.py#L1121) · source: https://docs.astropy.org/en/latest/development/scripts.html

### ASTROPY-C234 — `MainTakesOneOptionalArgument`

> **Corpus:** Give ``main`` a single optional argument holding ``sys.argv[1:]``.

- **Pre-condition —** each ``main`` function the agent wrote or edited in a command-line script.
- **Pass condition —** it takes a single argument, and that argument has a default.

Heuristic on the **pass condition** (§6.2): the signature is read exactly, but the sentence also says the argument *holds* ``sys.argv[1:]``, and what a caller passes is not decidable from the definition. A one-argument ``main`` used for something else passes.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:1161`](../compliance/rules/astropy/specialized.py#L1161) · source: https://docs.astropy.org/en/latest/development/scripts.html

### ASTROPY-C235 — `ScriptsAreRegisteredAsEntryPoints`

> **Corpus:** Register the script as an entry point in the packaging configuration.

- **Pre-condition —** each command-line script the agent added.
- **Pass condition —** the packaging configuration in the contribution names it as an entry point.

Heuristic on the **pass condition** (§6.2): a registration outside the contribution cannot be seen, so a script added to a package whose entry points were already declared reads as a violation. The corpus records that the prose says ``setup.py`` while the example on the same page says ``pyproject.toml``; both are accepted, and ``setup.cfg`` with them, because which file holds the entry points is a packaging detail the rule does not turn on.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/specialized.py:1203`](../compliance/rules/astropy/specialized.py#L1203) · source: https://docs.astropy.org/en/latest/development/scripts.html


## astropy — Documentation and docstrings

### ASTROPY-C085 — `PublicDefinitionsHaveDocstrings`

> **Corpus:** Give every public class, method, and function a docstring.

- **Pre-condition —** each public class, method and function the agent's edit reaches.
- **Pass condition —** it carries a docstring.

Not heuristic: *public* is decided by the leading underscore convention the project uses, and presence of a docstring is read off the syntax tree. Both are exact. ``enclosing`` rather than ``touched``: the thing judged is the definition, which the agent did not create, and the edit that makes it answerable is somewhere inside it. Ownership is decided on the definition's **own** lines -- its span minus anything nested in it -- so editing one method does not make the agent answerable for its class's docstring.


ownership `enclosing` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:262`](../compliance/rules/astropy/documentation.py#L262) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C146 — `AbbreviationsSitInParenthesesWithAComma`

> **Corpus:** Put ``i.e.`` and ``e.g.`` inside parentheses and follow them with a comma.

- **Pre-condition —** each written line using ``i.e.`` or ``e.g.``.
- **Pass condition —** each use opens a parenthetical and is followed by a comma.

Heuristic on the **pass condition** (§6.2): "within parentheses" is checked by looking for the opening bracket immediately before the abbreviation, which misses a parenthetical that opens earlier in the sentence and reports it as a violation.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:533`](../compliance/rules/astropy/documentation.py#L533) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C151 — `OrganizationAcronymsAreHyperlinked`

> **Corpus:** Write an organization's acronym and hyperlink it to a reference.

- **Pre-condition —** each written line naming what looks like an organization by its acronym.
- **Pass condition —** the line hyperlinks it.

Heuristic on **both layers** (§6.1). An organization acronym cannot be told from any other capitalised abbreviation, so the pre-condition selects runs of capitals and excludes a list of formats, protocols and concepts astropy's prose is full of -- FITS, WCS, HDU, API. The list cannot be complete, so the check both over- and under-fires. The grading is looser still: any hyperlink on the line counts, not specifically one around the acronym.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:567`](../compliance/rules/astropy/documentation.py#L567) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C152 — `CodeNamesAreLowercaseInDoubleBackticks`

> **Corpus:** Capitalize proper nouns, but write package and code names lowercase in double backticks.

- **Pre-condition —** each written line naming a package or code name, in any casing and with or without markup.
- **Pass condition —** every such name is lowercase inside double backticks.

The word *astropy* is deliberately outside this rule's vocabulary: C153 legislates its two spellings, and grading it here as well would have the two rules disagree on "Astropy" (§7.5). A no-target test pins that. Heuristic on the **pre-condition** (§6.3): the rule's antecedent is *a proper noun or a code name*, and only the second half is enumerable. The check therefore says nothing about proper nouns generally and grades the package names astropy's documentation actually uses.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:604`](../compliance/rules/astropy/documentation.py#L604) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C153 — `AstropyIsSpelledForWhatItMeans`

> **Corpus:** Write ``astropy`` lowercase in double backticks when you mean the core package and Astropy capitalized when you mean the Project.

- **Pre-condition —** each written line mentioning astropy, in any spelling.
- **Pass condition —** the mention is ``astropy`` in lowercase double backticks, or Astropy capitalised in plain prose.

Heuristic on the **pass condition** (§6.2): the rule ties each spelling to a meaning -- the core package against the Project -- and which one a sentence means is not mechanically decidable. What is graded is that the spelling is one of the two sanctioned forms, so a sentence about the Project written as ``astropy`` passes here and should not.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:645`](../compliance/rules/astropy/documentation.py#L645) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C156 — `NoContractionsInDocumentation`

> **Corpus:** Do not use contractions in documentation.

- **Pre-condition —** each line of documentation prose the agent wrote.
- **Pass condition —** it uses no contraction.

A prohibition, so the pre-condition selects the permitted form as well as the forbidden one (§7.1): every prose line is judged, and a line with no contraction records a pass. Heuristic on the **pass condition** (§6.2): the list of contractions is necessarily partial, and a contraction inside quoted example output is the example's, not the documentation's.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:684`](../compliance/rules/astropy/documentation.py#L684) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C160 — `NumbersWithUnitsAreNumerals`

> **Corpus:** Write a number as a numeral when it is followed by a unit or is part of a name.

- **Pre-condition —** each written line stating a quantity -- a number, spelled out or not, followed by a unit.
- **Pass condition —** the number is written as a numeral.

Selecting on *the quantity* rather than on the spelled-out form is what lets "1 arcminute" record a pass (§7.1). Heuristic on the **pre-condition** (§6.3): "followed by a unit or part of a name" is approximated by a list of the units astropy's documentation uses; the *part of a name* half -- "Gaia data release 2" -- is not detected at all, so the check under-fires there.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:712`](../compliance/rules/astropy/documentation.py#L712) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C161 — `SmallNumbersAreSpelledOut`

> **Corpus:** Spell out whole numbers one through nine and use numerals from 10 up.

- **Pre-condition —** each written line stating a whole number that is not followed by a unit, in either form.
- **Pass condition —** one through nine are spelled out and 10 upwards are numerals.

Numbers followed by a unit are excluded and left to C160, which requires the opposite form for them; without that exclusion the two rules would contradict each other on "1 arcminute" (§7.5). Lines using a numeral-word combination -- "2 billion stars" -- are excluded too, because the sentence sanctions that form explicitly. Heuristic on the **pre-condition** (§6.3): version strings, identifiers and casual expressions are hard to tell from whole numbers, and the source's own exception -- "for casual expressions, spell out the number" -- is not detectable at all.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:747`](../compliance/rules/astropy/documentation.py#L747) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C164 — `ParentheticalPunctuationGoesInside`

> **Corpus:** Place punctuation belonging to parenthetical material inside the closing parenthesis.

- **Pre-condition —** each written line containing a parenthetical.
- **Pass condition —** where the parenthetical is a sentence of its own, its full stop is inside the closing bracket.

Heuristic on the **pass condition** (§6.2), and narrowed to the one case the sentence's two exceptions leave decidable. A parenthetical *inside* another sentence keeps its period outside, and a comma after one is explicitly allowed, so only a stand-alone parenthetical -- one that opens the sentence -- is graded.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:801`](../compliance/rules/astropy/documentation.py#L801) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C165 — `PunctuationGoesInsideQuotationMarks`

> **Corpus:** Put periods and commas inside closing quotation marks.

- **Pre-condition —** each written line containing a quoted span.
- **Pass condition —** no period or comma follows the closing quotation mark.

Heuristic on the **pre-condition** (§6.3): a double quote in astropy's documentation is as often a string literal in prose as it is a quotation, and the check cannot tell them apart. Inline literals are stripped first, which removes the commonest of those.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:835`](../compliance/rules/astropy/documentation.py#L835) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C166 — `NumberRangesUseAnUnspacedEnDash`

> **Corpus:** Use an unspaced en dash for number ranges and in place of “to” or “through”.

- **Pre-condition —** each written line stating a number range, however it is written.
- **Pass condition —** the range uses an unspaced en dash.

Selecting every range, rather than the hyphenated ones, is what lets "chapters 14–18" record a pass (§7.1). Heuristic on the **pre-condition** (§6.3): two numbers separated by a hyphen are also how a version, an identifier or a date fragment is written, and the check cannot tell those from a range.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:863`](../compliance/rules/astropy/documentation.py#L863) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C167 — `EmDashesAreSpaced`

> **Corpus:** Put a space on either side of an em dash.

- **Pre-condition —** each written line using an em dash.
- **Pass condition —** it has a space on either side.

Not heuristic: the character is exact, the spacing is exact, and both are read off the line. The source's permission -- an em dash "can be used" -- governs whether to use one at all, which is why the pre-condition fires on the use and not on the absence.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:897`](../compliance/rules/astropy/documentation.py#L897) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C168 — `SpellingIsAmerican`

> **Corpus:** Use American spelling.

- **Pre-condition —** each written line containing a word that has both a British and an American spelling, in either form.
- **Pass condition —** it is the American one.

Selecting on the alternation rather than on the British spelling is what lets "catalog" record a pass (§7.1). Heuristic on the **pass condition** (§6.2): the word list is necessarily partial, so a British spelling outside it passes, and a word that only looks British -- a surname, a quoted string -- is reported.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:927`](../compliance/rules/astropy/documentation.py#L927) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C169 — `ExactTimesUseTheTwentyFourHourClock`

> **Corpus:** Express exact times as numerals in the 24-hour system.

- **Pre-condition —** each written line stating an exact time, in either system.
- **Pass condition —** it is numerals on the 24-hour clock.

Heuristic on the **pre-condition** (§6.3): a bare ``12:30`` is also how a duration or a coordinate is written, and "3 pm" is recognised only in the spellings the pattern knows. Selecting only the a.m./p.m. form would make every target a violation (§7.1).


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:962`](../compliance/rules/astropy/documentation.py#L962) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C170 — `SpecificDatesAreIso8601`

> **Corpus:** Write specific dates in ISO 8601 year-month-day form.

- **Pre-condition —** each written line stating a specific date, in any format.
- **Pass condition —** it is written year-month-day.

Heuristic on the **pre-condition** (§6.3): the alternative formats are recognised from a list of spellings -- a month name with a year, or a slashed numeric date -- so a date written some other way is not selected.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:993`](../compliance/rules/astropy/documentation.py#L993) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C172 — `FirstPersonIsInclusivePlural`

> **Corpus:** Use the first-person inclusive plural (“we”) in narrative documentation.

- **Pre-condition —** each written line using a first-person pronoun, singular or plural.
- **Pass condition —** it is the inclusive plural -- we, us, our.

Heuristic on the **pre-condition** (§6.3): "I" is also a variable, a matrix and a Roman numeral, and inline literals are stripped before the search to remove most of those. Selecting only the singular would make every target a violation (§7.1).


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:1024`](../compliance/rules/astropy/documentation.py#L1024) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C173 — `GenericPronounIsYou`

> **Corpus:** Use “you” rather than “one” as the generic pronoun.

- **Pre-condition —** each written line using a generic pronoun, in either form.
- **Pass condition —** it is "you".

The generic "one" is recognised by the verb that follows it, because "one" is far more often the number. Selecting only lines containing "one" would make every target a violation and could never record a compliant line (§7.1), which is why "you" is in the pre-condition too. Heuristic on the **pre-condition** (§6.3): the verb list is partial, so a generic "one" followed by something else is missed.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:1051`](../compliance/rules/astropy/documentation.py#L1051) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C174 — `NoBelittlingWords`

> **Corpus:** Do not use belittling words such as “obviously”, “easily”, “simply”, “just” or “straightforward”.

- **Pre-condition —** each line of documentation prose the agent wrote.
- **Pass condition —** it uses none of the belittling words the style guide names.

A prohibition with a closed list, so the grading is a lookup rather than a judgement. Heuristic all the same (§6.6): "just" and "clearly" have senses that belittle nobody -- "just below the header" -- and the check cannot tell which sense is meant.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:1086`](../compliance/rules/astropy/documentation.py#L1086) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C177 — `WarningsNoteLimitationsInTheCode`

> **Corpus:** Use ``.. warning::`` directives only for limitations in the code.

- **Pre-condition —** each ``.. warning::`` directive the agent added to the documentation.
- **Pass condition —** its text does not address the reader's skill or knowledge.

Heuristic on the **pass condition** (§6.2): "a limitation in the code" against "an implied limitation in the reader" is a distinction about meaning, approximated by the vocabulary reader-directed warnings use. A condescending warning phrased outside that vocabulary passes. Selected separately from the other prose rules because a directive line is markup, and ``prose_lines`` filters markup out.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:1112`](../compliance/rules/astropy/documentation.py#L1112) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C179 — `HeadingUnderlinesMatchTheirText`

> **Corpus:** Make a heading's underline (and overline) the same length as the heading text.

- **Pre-condition —** each reStructuredText heading the agent wrote in a documentation page.
- **Pass condition —** its underline is exactly as long as the heading text.

Not heuristic: both lengths are counted off the file. The file's whole text is read rather than the diff, because an underline three lines of context away is still the underline; ownership is then narrowed back to headings the agent actually wrote.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:1152`](../compliance/rules/astropy/documentation.py#L1152) · source: https://docs.astropy.org/en/latest/development/style-guide.html

### ASTROPY-C185 — `NewFunctionalityIsDescribedInTheNarrativeDocs`

> **Corpus:** Describe new functionality in the narrative documentation under ``docs/``.

- **Pre-condition —** the contribution adds a public function or class to library code, which is what adding new functionality looks like.
- **Pass condition —** it also changes a page under ``docs/``.

Heuristic on **both layers** (§6.1). *New functionality* is approximated by a new public definition, which over-fires on a refactor that merely renames one and under-fires on a new keyword argument to an existing function. And "a description in the main documentation" is approximated by any change under ``docs/``, which does not check that the change describes the new thing.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:1191`](../compliance/rules/astropy/documentation.py#L1191) · source: https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md

### ASTROPY-C190 — `ImplementedAlgorithmsCiteTheirSource`

> **Corpus:** Cite the origin source of any algorithm you implement.

- **Pre-condition —** each public function the agent added to library code, read as an implemented algorithm.
- **Pass condition —** its docstring names an origin -- a ``References`` section, a citation, a DOI or a URL.

Heuristic on **both layers** (§6.1). *An algorithm you implement* is approximated by a new public function, which over-fires on plumbing that implements no algorithm at all. And "cites the origin source" is approximated by the forms a citation takes, so a reference written as bare prose -- "following the method of Smith" -- reads as missing.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:400`](../compliance/rules/astropy/documentation.py#L400) · source: https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md

### ASTROPY-C206 — `NewFunctionsCarryAFullNumpydocDocstring`

> **Corpus:** Document what the function does, its inputs, its outputs, its references, its exceptions and an example in its numpydoc docstring.

- **Pre-condition —** each public function the agent added to library code.
- **Pass condition —** its docstring has a summary, an ``Examples`` section, and the sections its signature calls for -- ``Parameters`` when it takes arguments, ``Returns`` when it returns a value, ``Raises`` when it raises.

Heuristic on the **pass condition** (§6.2). Section presence stands in for the checklist's six questions: whether a ``Parameters`` section really describes *the format of the inputs* is not decidable from a header. The sixth question -- references to the original algorithm -- is left to C190, which is the rule about exactly that; grading it here as well would fail the same omission twice (§7.5).


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:344`](../compliance/rules/astropy/documentation.py#L344) · source: https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md

### ASTROPY-C219 — `DocstringsUseNumpydocFormat`

> **Corpus:** Write docstrings in numpydoc format.

- **Pre-condition —** each docstring the agent wrote or edited.
- **Pass condition —** it carries no section header belonging to a competing format.

Heuristic on the **pass condition** (§6.2), graded one-sidedly. A docstring with no sections at all is perfectly numpydoc-compatible, so confirming the format is not possible; a reST field list or a Google ``Args:`` header is positive evidence of the wrong one. Where a numpydoc section *is* present that is reported as satisfying, which is stronger evidence than mere absence.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:306`](../compliance/rules/astropy/documentation.py#L306) · source: https://docs.astropy.org/en/latest/development/docguide.html

### ASTROPY-C220 — `DocstringCrossReferencesUseIntersphinx`

> **Corpus:** Write docstring cross-references in intersphinx form, including links within astropy.

- **Pre-condition —** each cross-reference the agent wrote in a docstring, in either form -- a Sphinx role, or a URL into the documentation.
- **Pass condition —** it is a role rather than a URL.

Links to the *development* version are excluded: C221 makes a direct URL the right form for those, and grading them here would have the two rules contradict each other on one line (§7.5). A no-target test pins the exclusion. Heuristic on the **pre-condition** (§6.3): "a cross-reference" is approximated by these two spellings, and a reference written some third way is not selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:438`](../compliance/rules/astropy/documentation.py#L438) · source: https://docs.astropy.org/en/latest/development/docguide.html

### ASTROPY-C221 — `DevelopmentVersionLinksAreDirectUrls`

> **Corpus:** Use a direct URL when linking to the development version of the documentation.

- **Pre-condition —** each link the agent wrote that points at the development version of the documentation, in either form.
- **Pass condition —** it is a direct URL.

Heuristic on the **pre-condition** (§6.3): *linking to the development version* is approximated by the link naming ``latest`` or ``dev``, which is how those URLs and roles are spelled. A role that resolves to the development version without saying so is not selected.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/documentation.py:482`](../compliance/rules/astropy/documentation.py#L482) · source: https://docs.astropy.org/en/latest/development/docguide.html


## astropy — AI-assisted contribution policy

### ASTROPY-C251 — `GenerativeAiUseIsDisclosed`

> **Corpus:** Describe your use of generative AI in the change description when it wrote substantive portions of the contribution.

- **Pre-condition —** an autonomous run produced a contribution, so generative AI wrote substantive portions of it.
- **Pass condition —** the change description says so.

Not ``by_construction``: nothing stops an agent writing the sentence, and one arm of the experiment is shown the rule. Heuristic on the **pass condition** (§6.2) -- "says so" is matched against a vocabulary of AI-mention patterns, so a disclosure worded outside that vocabulary reads as a violation. Both places a contributor describes a change are accepted. The policy says "change description" without fixing which, and failing a run that disclosed in its commit message would be grading a distinction the sentence does not draw.


`heuristic` · ownership `created` · reads `files, pr_text, commits` · tier `static`

[`compliance/rules/astropy/ai_policy.py:47`](../compliance/rules/astropy/ai_policy.py#L47) · source: https://github.com/astropy/astropy-project/blob/main/policies/ai-policy.md

### ASTROPY-C254 — `NoSubmissionByAnAutonomousAgent`

> **Corpus:** Do not submit a contribution through an autonomous agent acting without a human contributor.

- **Pre-condition —** a named model produced a contribution with no human contributor behind it.
- **Pass condition —** a human contributor stands behind the submission.

``by_construction`` (§6.5), not heuristic: the check is exact -- the harness records that a model produced the patch, and it records no human -- and it is the experimental *setup*, not the evidence, that makes compliance impossible. Scored rather than dropped, because a rule excluded from the pack cannot be shown to the guided arm and then reported on. The pre-condition still discriminates: a run with no recorded model, or one that submitted nothing, finds no target instead of failing vacuously.


ownership `created` · reads `files` · tier `trajectory`

[`compliance/rules/astropy/ai_policy.py:93`](../compliance/rules/astropy/ai_policy.py#L93) · source: https://github.com/astropy/astropy-project/blob/main/policies/ai-policy.md


## astropy — Code and quality

### ASTROPY-C050 — `PreCommitRewritesAreRestaged`

> **Corpus:** Review and re-stage any file that pre-commit rewrote before committing.

- **Pre-condition —** each ``pre-commit`` run whose output says a hook rewrote a file.
- **Pass condition —** the agent staged something afterwards, before the run ended.

The pre-condition fires on the **rewrite**, not on the re-staging (§7.1, §7.2): firing on the ``git add`` would find only agents that already complied. A run that never invoked pre-commit finds no target, which is the honest reading of a conditional rule. Heuristic on the **pass condition** (§6.2), twice over. Whether a hook changed anything is read out of the command's own output text rather than by re-running the tool, and "re-staged" is approximated by a later ``git add`` -- which does not prove that the rewritten file in particular was the one staged.


`heuristic` · ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/astropy/code_quality.py:176`](../compliance/rules/astropy/code_quality.py#L176) · source: https://docs.astropy.org/en/latest/development/development_details.html

### ASTROPY-C076 — `CodeMatchesTheSupportedPythonVersions`

> **Corpus:** Keep all code compatible with the Python versions in ``requires-python`` in ``pyproject.toml``.

- **Pre-condition —** each Python file the agent wrote or edited.
- **Pass condition —** it uses no construct introduced after the ``requires-python`` floor.

Withheld unless the contribution carries ``pyproject.toml``: the floor is written in the checked-out tree and no evidence source carries it, so ``repo_version`` is declared as the named missing input rather than a version being assumed (§5). Guessing a floor would make every verdict here a statement about our guess. Heuristic on the **pass condition** (§6.2): the table of dated constructs is short and necessarily partial, so this can show incompatibility and cannot show its absence. A file using something the table does not know about passes.


`heuristic` · ownership `touched` · reads `files, repo_version` · tier `static`

[`compliance/rules/astropy/code_quality.py:212`](../compliance/rules/astropy/code_quality.py#L212) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C077 — `CoreImportsOnlyStdlibNumpyAndAstropy`

> **Corpus:** Keep the core package importable using only the standard library, NumPy, and astropy itself.

- **Pre-condition —** each module-level import statement the agent wrote in library code under ``astropy/``.
- **Pass condition —** every name it binds is the standard library, NumPy, astropy itself, or a relative import.

Imports inside ``try`` and under ``if TYPE_CHECKING`` are not selected: the first is astropy's own way of making a dependency optional and the second never executes, so grading either would report the sanctioned pattern as the violation. Heuristic on the **pre-condition** (§6.3), and the doubt is named rather than assumed away: *importable with no other dependencies* is a property of the whole import graph, and a module-level import statement is the visible face of it. A file that imports a clean module which itself imports SciPy passes here.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/code_quality.py:254`](../compliance/rules/astropy/code_quality.py#L254) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C195 — `NoUndeclaredDependency`

> **Corpus:** Do not introduce a dependency that is not declared in ``pyproject.toml``.

- **Pre-condition —** each third-party package the agent's added lines import, anywhere in the contribution.
- **Pass condition —** it appears among the dependencies ``pyproject.toml`` declares.

Selecting every third-party import rather than only undeclared ones is what lets a contribution that imports SciPy correctly record a pass (§7.1). Heuristic on the **pass condition** (§6.2), because of where the declared list comes from. When the contribution carries ``pyproject.toml`` the list is read from it and the comparison is exact; otherwise it falls back to astropy's published runtime and test dependencies as of the corpus version, which can go stale in either direction. The fallback is used rather than withholding because it is a list the project publishes, not a guess -- and because a rule that withholds on every ordinary contribution measures nothing.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/code_quality.py:304`](../compliance/rules/astropy/code_quality.py#L304) · source: https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md


## astropy — Language and framework style

### ASTROPY-C083 — `GeneralUtilitiesLiveInAstropyUtils`

> **Corpus:** Put general-purpose utilities in ``astropy.utils`` rather than in a sub-package.

- **Pre-condition —** each Python module the agent added under ``astropy/``.
- **Pass condition —** if it is a general-purpose utility module, it sits under ``astropy/utils/``.

Heuristic on the **pass condition** (§6.2): *general utilities necessary for but not specific to the sub-package* is a judgement about what the code is for, approximated here by the names a contributor gives such a module -- ``utils``, ``helpers``, ``misc``, ``common``, ``tools``. A general-purpose helper filed under a descriptive name passes. Selecting every added module, rather than the misplaced ones, is what lets a correctly placed helper record a pass (§7.1).


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/astropy/language_style.py:131`](../compliance/rules/astropy/language_style.py#L131) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C098 — `PrintOnlyForRequestedOutput`

> **Corpus:** Use ``print()`` only for output the user explicitly asked for.

- **Pre-condition —** each ``print()`` call the agent wrote in library code under ``astropy/``.
- **Pass condition —** it sits in a function whose job is output the user asked for.

Heuristic on the **pass condition** (§6.2): *explicitly requested by the user* is an intention, approximated by the enclosing function's name -- codeguide's own examples are ``print_header`` and ``list_catalogs``. A ``print`` inside a differently-named public reporting function is reported as a violation and is not one. Test modules are excluded from the pre-condition: the rule is about what the library prints, and a print in a test is not library output.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/language_style.py:171`](../compliance/rules/astropy/language_style.py#L171) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C099 — `ErrorsAreRaisedExceptionClasses`

> **Corpus:** Raise a built-in or custom exception class for error conditions.

- **Pre-condition —** each place the agent's written code signals an error -- a ``raise`` statement, ``sys.exit``, ``os._exit`` or an ``assert False``.
- **Pass condition —** it is a ``raise`` of a built-in or custom exception class.

Heuristic on the **pre-condition** (§6.3): *an error condition* is not observable, so it is approximated by the ways code signals one. Selecting only ``raise`` statements would make the rule unfailable -- every target would already be the compliant form -- which is §7.1 inverted in its subtler shape.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/language_style.py:212`](../compliance/rules/astropy/language_style.py#L212) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C100 — `NoBareExceptionRaised`

> **Corpus:** Do not raise the bare ``Exception`` class.

- **Pre-condition —** each ``raise`` of a named class the agent wrote.
- **Pass condition —** the class is not ``Exception`` itself.

Not heuristic: the sentence names one token to avoid, the class raised is read off the syntax tree, and the comparison is exact. The corpus records the source's own hedge -- "as much as possible" -- and the atomic rule drops it, so the hedge is not re-applied here.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/language_style.py:270`](../compliance/rules/astropy/language_style.py#L270) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C101 — `WarningsGoThroughWarningsWarn`

> **Corpus:** Emit warnings with ``warnings.warn(message, warning_class)``.

- **Pre-condition —** each place the agent's written code emits a warning, by whatever means.
- **Pass condition —** it is ``warnings.warn(message, warning_class)`` -- the call, with the class given.

Heuristic on the **pre-condition** (§6.3): *emitting a warning* is approximated by the vocabulary of calls that do it -- ``warnings.warn``, a bare ``warn``, ``log.warning``, ``logger.warning``. A warning raised some other way is not selected. Selecting only ``warnings.warn`` calls would leave the rule unable to record the violation it exists to catch.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/language_style.py:310`](../compliance/rules/astropy/language_style.py#L310) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C102 — `WarningClassIsAstropyUserWarning`

> **Corpus:** Use ``AstropyUserWarning`` or a subclass of it as the warning class.

- **Pre-condition —** each ``warnings.warn`` call the agent wrote that names a warning class.
- **Pass condition —** that class is ``AstropyUserWarning`` or something inheriting from it.

Heuristic on the **pass condition** (§6.2): inheritance cannot be resolved from a patch. A class defined in the contribution is followed one level to its bases; a name imported from ``astropy`` is accepted on the strength of where it comes from; a built-in warning class is a violation. A warning class defined elsewhere in the tree and not obviously astropy's is accepted, so this check shows the violation and cannot confirm the inheritance.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/language_style.py:351`](../compliance/rules/astropy/language_style.py#L351) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C103 — `InformationalMessagesGoThroughLog`

> **Corpus:** Emit informational and debugging messages through ``log.info()`` and ``log.debug()``.

- **Pre-condition —** each place the agent's written code emits an informational or debugging message that is not output the user asked for.
- **Pass condition —** it is ``log.info()`` or ``log.debug()``.

The exclusion is the §7.5 narrowing this pack needs. C098 permits ``print`` for output the user explicitly requested; read literally, C103 would then fail the very same line. A ``print`` inside a function whose job is producing output is therefore not selected here, and a no-target test pins that resolution. Heuristic on the **pre-condition** (§6.3): *informational and debugging messages* is approximated by the calls that emit them -- ``print``, ``sys.stdout.write``, and the ``logging`` module's own info and debug entry points.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/language_style.py:410`](../compliance/rules/astropy/language_style.py#L410) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C105 — `RuffFormatWouldChangeNothing`

> **Corpus:** Format Python files with ``ruff format``.

- **Pre-condition —** each Python file the agent wrote a line into.
- **Pass condition —** none of those lines carries formatting ``ruff format`` always removes -- trailing whitespace, or a tab in the indentation.

Heuristic on the **pass condition** (§6.2), and narrow on purpose. The real answer is ``ruff format --diff``, which nothing in this instrument runs. Everything the formatter decides from configuration -- line length, quote style, magic trailing commas -- is deliberately not checked, because a proxy that guessed at project settings would report violations that are not violations. What is left holds under every configuration.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/language_style.py:455`](../compliance/rules/astropy/language_style.py#L455) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C106 — `ImportsAreSorted`

> **Corpus:** Sort module imports.

- **Pre-condition —** each Python file the agent edited whose leading import block holds at least two imports.
- **Pass condition —** the groups appear in the declared order and none is split in two.

Heuristic on the **pass condition** (§6.2), and the flag is about *coverage* rather than about the check being fuzzy. isort decides three things -- which group each import belongs to, the order of the groups, and the alphabetical order within a group. This checks the first two exactly and the third not at all, so a file with correctly grouped but unsorted imports passes a rule ``ruff check --select I`` would fail.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/language_style.py:496`](../compliance/rules/astropy/language_style.py#L496) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C107 — `RuffChecksPass`

> **Corpus:** Make the code pass the repository's configured ruff checks.

- **Pre-condition —** the agent submitted Python code, which is what gets merged.
- **Pass condition —** ``ruff check`` reports no finding the base commit did not already have.

Deliberately not "the agent ran ruff": the obligation is that the code passes, so a contribution that never ran the tool is judged rather than excused. A submitted module that will not parse fails here without any tool run, because invalid Python cannot pass a linter and no evidence beyond the patch is needed to say so.


ownership `touched` · reads `files, lint_run` · tier `static`

[`compliance/rules/astropy/language_style.py:538`](../compliance/rules/astropy/language_style.py#L538) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C108 — `SourceFilesCarryTheLicenceLine`

> **Corpus:** Start each source file with the comment ``# Licensed under a 3-clause BSD style license - see LICENSE.rst``.

- **Pre-condition —** each Python or Cython source file the agent wrote or edited.
- **Pass condition —** its first line of content is the licence comment, verbatim.

Not heuristic: codeguide gives the line verbatim, so there is exactly one right string and it is compared exactly. A shebang and an encoding declaration are allowed to precede it, because Python requires them there. A file the harness could not reconstruct is undetermined rather than failed: not finding the line in text we do not have would be a verdict about our own gap.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/language_style.py:586`](../compliance/rules/astropy/language_style.py#L586) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C110 — `StateIsExposedAsAttributes`

> **Corpus:** Expose instance state through attributes or properties rather than get_/set_ methods unless access is computationally expensive.

- **Pre-condition —** each method the agent wrote or edited on a class.
- **Pass condition —** it is not a trivial ``get_``/``set_`` accessor.

Heuristic on the **pass condition** (§6.2): the sentence exempts accessors whose work is "computationally expensive", which nothing in a patch measures. *Trivial* stands in for it -- a body of a single statement, which is what a plain attribute wrapper looks like -- so an expensive accessor written in one line reads as a violation and a cheap one written in five does not. Selecting every written method, not only the ``get_``-prefixed ones, is what lets an ordinary method record a pass (§7.1).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/language_style.py:629`](../compliance/rules/astropy/language_style.py#L629) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C111 — `SuperClassCallsUseSuper`

> **Corpus:** Call super-class methods through ``super()``.

- **Pre-condition —** each call the agent wrote that reaches a super-class method, in either form -- ``super().method(...)`` or ``BaseClass.method(self, ...)``.
- **Pass condition —** it goes through ``super()``.

Heuristic on the **pre-condition** (§6.3): the direct form is recognised by a call whose first argument is ``self``, which is what an unbound super-class call looks like and is also what a deliberate call to an unrelated class's function looks like. Selecting only the direct form would make every target a violation (§7.1).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/language_style.py:673`](../compliance/rules/astropy/language_style.py#L673) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C116 — `ReprIsAlwaysAscii`

> **Corpus:** Make ``__repr__`` return ASCII-only text regardless of ``unicode_output``.

- **Pre-condition —** each ``__repr__`` the agent wrote or edited.
- **Pass condition —** it embeds no non-ASCII text and does not branch on ``unicode_output``.

Heuristic on the **pass condition** (§6.2): what a method *returns* is a runtime fact, and this reads the literals it is built from. A ``__repr__`` that assembles non-ASCII from a variable passes; one that only mentions ``unicode_output`` in a comment fails. Both directions are declared rather than argued away.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/language_style.py:738`](../compliance/rules/astropy/language_style.py#L738) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C117 — `StrIsAsciiUnlessUnicodeOutput`

> **Corpus:** Make ``__str__`` and ``__format__`` return ASCII-only text when ``unicode_output`` is False.

- **Pre-condition —** each ``__str__`` or ``__format__`` the agent wrote or edited.
- **Pass condition —** if it embeds non-ASCII text it also consults ``unicode_output``.

The contrast with C116 is the point of both: ``__repr__`` must never depend on the setting, and ``__str__`` must depend on it before it emits anything outside ASCII. Heuristic on the **pass condition** (§6.2) for the same reason as C116 -- the literals a method contains stand in for what it returns, and consulting the setting stands in for branching on it correctly.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/astropy/language_style.py:771`](../compliance/rules/astropy/language_style.py#L771) · source: https://docs.astropy.org/en/latest/development/codeguide.html

### ASTROPY-C118 — `ParserAcceptsItsOwnStrOutput`

> **Corpus:** Make a round-trippable class's parser accept its own ``__str__`` output.

- **Pre-condition —** each class the agent wrote or edited that both defines ``__str__`` and offers a string parser, which is what a round-trippable class looks like.
- **Pass condition —** the parser accepts the output of ``__str__``.

Graded **one-sidedly, and the side it grades is empty** -- this rule withholds on every target it selects, which is why it declares ``full_suite_run``. Whether a parser accepts a string is decided by running the parser on that string; a patch shows neither the string nor the outcome, and any static stand-in would be inventing the verdict. Declaring the missing input keeps the withholding auditable and ends it automatically the day the bundle carries a suite run (§5). Heuristic on the **pre-condition** (§6.3): *expected to roundtrip through strings* is a property of the class's contract, approximated by it having both halves of one.


`heuristic` · ownership `touched` · reads `files, full_suite_run` · tier `static`

[`compliance/rules/astropy/language_style.py:805`](../compliance/rules/astropy/language_style.py#L805) · source: https://docs.astropy.org/en/latest/development/codeguide.html


# django

| category | rules |
|---|---:|
| [Git and commit conventions](#django-git-and-commit-conventions) | 2 |
| [PR and release metadata](#django-pr-and-release-metadata) | 4 |
| [Tests and test style](#django-tests-and-test-style) | 3 |
| [Specialized changes](#django-specialized-changes) | 6 |
| [Documentation and docstrings](#django-documentation-and-docstrings) | 15 |
| [AI-assisted contribution policy](#django-ai-assisted-contribution-policy) | 4 |
| [Code and quality](#django-code-and-quality) | 3 |
| [Language and framework style](#django-language-and-framework-style) | 41 |


## django — Git and commit conventions

### DJANGO-C044 — `NoForcePush`

> **Corpus:** Do not force-push to rewrite published history on django/django branches without team discussion.

- **Pre-condition —** each `git push` the agent ran.
- **Pass condition —** it was not a force push.

``heuristic`` for what it cannot see rather than for what it can. Whether a push rewrote *published* history on a *django/django* branch, and whether the team had agreed to it, are facts about a remote and a mailing list; neither is in a trajectory. What is decided here is the observable half -- a force flag or a `+refspec` on a push -- and it is read as the violation the rule names. A force push to the agent's own throwaway fork would be graded the same way, which is the direction the proxy errs in.


`heuristic` · ownership `created` · reads `commands` · tier `static`

[`compliance/rules/django/git_conventions.py:71`](../compliance/rules/django/git_conventions.py#L71) · source: https://docs.djangoproject.com/en/dev/internals/contributing/committing-code/ (Committing guidelines section)

### DJANGO-C046 — `PastTenseSubjectWithPeriod`

> **Corpus:** Phrase commit subject lines in past tense and end them with a period.

- **Pre-condition —** every commit the agent made.
- **Pass condition —** its subject line is phrased in the past tense and ends with a period.

Two clauses, graded separately so the reason says which one failed. The period is exact. The tense is not: `-ed` plus a list of irregular verbs is a proxy, and it is declared as one. It is applied to the leading verb -- the first word, or the first word after the `Fixed #12345 --` prefix Django puts in front of a ticket-closing subject -- because that is the word the convention is about.


`heuristic` · ownership `created` · reads `commits` · tier `static`

[`compliance/rules/django/git_conventions.py:103`](../compliance/rules/django/git_conventions.py#L103) · source: https://docs.djangoproject.com/en/dev/internals/contributing/committing-code/ (Committing guidelines section)


## django — PR and release metadata

### DJANGO-C052 — `ClosingCommitNamesTicket`

> **Corpus:** Start the commit message with 'Fixed #xxxxx' when the commit closes ticket xxxxx.

- **Pre-condition —** the agent committed a contribution resolving the reported issue it was given, so one of its commits closes that ticket.
- **Pass condition —** a commit message starts with `Fixed #xxxxx`.

Graded across the commit series rather than per commit, because Django's convention puts `Fixed #` on the *closing* commit only -- an intermediate commit in a series correctly says `Refs #` instead, and failing it here would penalise the convention it is meant to enforce. One target for the contribution; it passes when any commit carries the closing form.


`heuristic` · ownership `created` · reads `commits` · tier `static`

[`compliance/rules/django/pr_metadata.py:52`](../compliance/rules/django/pr_metadata.py#L52) · source: https://docs.djangoproject.com/en/dev/internals/contributing/committing-code/ (Committing guidelines section)

### DJANGO-C053 — `NonClosingTicketUsesRefs`

> **Corpus:** Include 'Refs #xxxxx' in the commit message when referencing but not closing ticket xxxxx.

- **Pre-condition —** each ticket number in a commit message that is not the one the leading `Fixed #xxxxx` closes.
- **Pass condition —** it is introduced by `Refs`.

``heuristic`` for the *"but not closing"* clause only. A number that is not the subject line's `Fixed #` is taken to be referenced rather than closed, which is what Django's convention implies but not something the patch states -- a message could close two tickets. The spelling check itself is exact.


`heuristic` · ownership `created` · reads `commits` · tier `static`

[`compliance/rules/django/pr_metadata.py:81`](../compliance/rules/django/pr_metadata.py#L81) · source: https://docs.djangoproject.com/en/dev/internals/contributing/committing-code/ (Committing guidelines section)

### DJANGO-C055 — `BehaviourChangeIsDocumented`

> **Corpus:** If a contribution adds a feature or changes existing behavior, it should include documentation.

- **Pre-condition —** the contribution changes library code, so it adds a feature or changes existing behaviour.
- **Pass condition —** it also changes documentation -- a file under `docs/`, or a docstring in the code it touched.

``heuristic`` because the antecedent is a proxy. A patch cannot say whether a change is a feature, a behaviour change, or an internal refactor that is none of the corpus sentence's business; "it changes non-test Python that ships to users" is the closest observable, and it over-fires on refactors. Docstrings count as documentation on purpose. Django documents public API in `docs/`, but a behaviour change described in the docstring of the function that changed has been documented, and requiring the `docs/` tree specifically would fail contributions that did the right thing in the right place.


`heuristic` · ownership `touched` · reads `files` · tier `trajectory`

[`compliance/rules/django/pr_metadata.py:115`](../compliance/rules/django/pr_metadata.py#L115) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/

### DJANGO-C079 — `ReleaseNoteForNewFeature`

> **Corpus:** Add a release-note entry in docs/releases/A.B.txt for new features.

- **Pre-condition —** each public top-level function or class the agent newly added to library code -- a new feature.
- **Pass condition —** the contribution adds content to a `docs/releases/A.B.txt` file.

``heuristic`` on the antecedent: a new public definition is what a new feature looks like in a patch, but so does a public helper extracted during a refactor. The pass condition is exact -- the rule names the file, and either it gained lines or it did not. The release-note entry is not required to name the definition. Django's release notes describe features in prose and frequently never spell the function's name, so demanding the name would fail correctly written notes.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/django/pr_metadata.py:157`](../compliance/rules/django/pr_metadata.py#L157) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/


## django — Tests and test style

### DJANGO-C076 — `RegressionTestForBugFix`

> **Corpus:** Write a regression test for a bug fix that fails on the pre-fix code and passes after.

- **Pre-condition —** the contribution changes library code, which is what a bug fix does.
- **Pass condition —** it also ships a test, and that test fails before the change and passes after it.

Graded one-and-a-half-sidedly, and deliberately. **A fix with no test at all is failed here**, because no run is needed to establish that no test can have gone from failing to passing -- there is none. That is the half invariant 2 requires: an agent that writes nothing must read ``fail``, not ``not_applicable``. Where a test *is* present, whether it fails on the pre-fix code is exactly what a before-and-after run answers and nothing static does. The harness's own ``FAIL_TO_PASS`` bucket cannot stand in: it is computed from the benchmark's reference test patch, not from the test the agent wrote, so reading it would grade somebody else's test. The rule declares ``full_suite_run`` and withholds instead. ``heuristic`` because the antecedent is a proxy: "changes library code" is what a bug fix looks like in a patch, but a refactor looks the same.


`heuristic` · ownership `touched` · reads `files, full_suite_run` · tier `differential`

[`compliance/rules/django/tests.py:295`](../compliance/rules/django/tests.py#L295) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/

### DJANGO-C078 — `TestsExerciseNewCode`

> **Corpus:** Write tests that exercise all newly added feature code.

- **Pre-condition —** each public top-level function or class the agent newly added to library code.
- **Pass condition —** a test in the contribution exercises it.

Same shape as C076 and for the same reason. Zero test files in a contribution that adds a feature is decidable non-compliance -- nothing is exercising the new code. *All* newly added code being exercised is a coverage question, which needs the suite, so that half declares ``full_suite_run`` and withholds. Name reference was considered as a static proxy and rejected: a test can exercise new code through a public entry point without ever naming it, and a test can name it in a comment without exercising a line. Reporting either as a verdict would put a number on something not measured.


`heuristic` · ownership `created` · reads `files, full_suite_run` · tier `differential`

[`compliance/rules/django/tests.py:336`](../compliance/rules/django/tests.py#L336) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/

### DJANGO-C091 — `IsolateAppsForTestLocalModels`

> **Corpus:** Wrap test-local model definitions with @isolate_apps() to avoid polluting the global apps registry.

- **Pre-condition —** each model class the agent defined inside a test function or test class body.
- **Pass condition —** `@isolate_apps()` wraps it, or an enclosing definition, or it is created inside an `isolate_apps()` context manager.

A model defined at a test module's top level is not "test-local" -- it is registered once at import and is the normal way Django's own test apps declare fixtures -- so it is not a target here. Only definitions nested inside a function or a class are.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/tests.py:373`](../compliance/rules/django/tests.py#L373) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/unit-tests/


## django — Specialized changes

### DJANGO-C081 — `RaisesRemovedInDjangoWarning`

> **Corpus:** Raise a RemovedInDjangoXXWarning at the point the deprecated feature is used, in the deprecating release.

- **Pre-condition —** the contribution deprecates a feature.
- **Pass condition —** library code the agent wrote raises a `RemovedInDjangoXXWarning` where the deprecated feature is used.

``heuristic`` for the antecedent, not for the grading. Whether a patch deprecates something is read from five circumstantial faces (module docstring), any of which a contribution could show for another reason -- a docs page that merely *mentions* a warning class already in the tree puts the rule in scope. The pass condition itself is exact: either a `warn()` call the agent wrote passes a `RemovedInDjango<NN>Warning`, or none does. *"At the point the deprecated feature is used"* is graded as *"in library code, not in a test"*. The finer reading -- inside the deprecated callable rather than beside it -- was considered and dropped: a deprecation shim, a `__getattr__` fallback and a property setter all raise correctly from somewhere the AST does not associate with the old name, so the stricter check would fail Django's own idioms.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/django/specialized.py:278`](../compliance/rules/django/specialized.py#L278) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/

### DJANGO-C082 — `NoUnintendedWarningsUnderWa`

> **Corpus:** Ensure `python -Wa runtests.py` produces no unintended warnings after adding a RemovedInDjangoXXWarning.

- **Pre-condition —** the contribution adds a `RemovedInDjangoXXWarning`.
- **Pass condition —** `python -Wa runtests.py` afterwards produces no warning that was not intended.

Withheld, with the missing input named. Two things are needed and the bundle carries neither: the full Django suite run under `-Wa`, which is not the subset the SWE-bench harness executes, and the warnings that were already being emitted before the change -- without them no warning in the output can be called *unintended*. Declaring ``full_suite_run`` and returning ``tool_missing`` keeps the row's applicability count while refusing to invent the verdict (invariant 6). Grading it from the command log was considered and rejected. That is the right shape for C074, where the corpus asks the contributor to *verify* something and the trajectory records what they did. This sentence asks about the suite's *output*, and an agent that ran `runtests.py` on one test module has not produced the evidence the sentence is about. The pre-condition is narrower than the rest of the category on purpose: the corpus says *"after adding a RemovedInDjangoXXWarning"*, so the warning is genuinely the antecedent here and firing on it is not the §4.2 bug.


ownership `touched` · reads `files, full_suite_run` · tier `differential`

[`compliance/rules/django/specialized.py:378`](../compliance/rules/django/specialized.py#L378) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/

### DJANGO-C085 — `UnreferencedCodeIsMarked`

> **Corpus:** Mark unreferenced deprecation-linked code with a RemovedInDjangoXXWarning comment so it's found when the deprecation completes.

- **Pre-condition —** each library file a deprecating contribution changes that does not itself raise the warning -- code linked to the deprecation with nothing to find it by.
- **Pass condition —** the agent wrote a `# RemovedInDjangoXXWarning` comment in it.

The narrowing is what makes the rule mean anything. Firing on every changed file would demand a marker comment in the file that already raises the warning, which is the case the rule explicitly excludes: that code *is* referenced by the deprecation and will be found. Firing on the deprecation alone would ask the contribution as a whole for a comment it may legitimately not need. ``heuristic``, and honestly so: *"unreferenced"* is a property of the whole tree and the bundle carries one patch. A file touched during a deprecation to migrate a call site to the new API is not code that must be removed later, and it is selected here. The proxy errs towards asking for the comment; a contribution that deprecates inside a single file finds no target at all, which is the common and correct case.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/specialized.py:321`](../compliance/rules/django/specialized.py#L321) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/

### DJANGO-C086 — `DocumentationEntryIsAnnotated`

> **Corpus:** Annotate deprecated documentation entries with .. deprecated:: A.B, a description, and an upgrade path.

- **Pre-condition —** the contribution deprecates a feature.
- **Pass condition —** it adds a `.. deprecated:: A.B` directive to `docs/` carrying a version, a description, and an upgrade path.

Graded over every directive the contribution adds, not over the first one found: three deprecated entries owe three annotations, and passing on the strength of the best of them would let the other two through. A contribution that adds none fails, which is the case the antecedent exists to keep in scope. ``heuristic`` for the last two clauses. A version is exact -- the directive either carries an argument or it does not. A *description* is read as any prose in or under the directive, and an *upgrade path* as a phrase telling the reader what to do instead (``UPGRADE_PATH``). Both are lexical proxies for something written for a human.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/specialized.py:421`](../compliance/rules/django/specialized.py#L421) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/

### DJANGO-C087 — `ReleaseNotesRecordTheDeprecation`

> **Corpus:** Document the deprecation and its upgrade path under the 'Features deprecated in A.B' release-notes heading.

- **Pre-condition —** the contribution deprecates a feature.
- **Pass condition —** it adds the deprecation and its upgrade path under a `Features deprecated in A.B` heading in the release notes.

Which section a line belongs to is a property of the file, not of the hunk, so the release-notes file is read whole and the agent's added lines are then narrowed back to the ones inside that section (invariant 5). A release-notes file the harness never rebuilt becomes ``Unreadable`` -- the rule applies and cannot be answered, which is not the same as it not applying. ``heuristic`` for the upgrade path only, on the same lexical proxy as C086. The heading itself is exact: Django's release notes spell it one way.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/specialized.py:489`](../compliance/rules/django/specialized.py#L489) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/

### DJANGO-C088 — `DeprecationTimelineRecordsRemoval`

> **Corpus:** Record the deprecation in docs/internals/deprecation.txt under the version it will be removed.

- **Pre-condition —** the contribution deprecates a feature.
- **Pass condition —** `docs/internals/deprecation.txt` gains an entry under the version that will remove it.

The exact rule of the six. The file is named by the corpus, the heading is a bare version number, and the removal version is carried by the warning class the contribution added -- so *"under the version it will be removed"* is checkable rather than a proxy. `RemovedInDjango110Warning` spells both 1.10 and 11.0 and the token cannot say which, so ``removal_versions`` returns both readings and either satisfies the rule. Choosing one would report a correct entry as filed under the wrong heading. A deprecation recognised by something other than a warning class carries no version at all, and then the rule asks only that the file gained an entry.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/specialized.py:533`](../compliance/rules/django/specialized.py#L533) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/


## django — Documentation and docstrings

### DJANGO-C074 — `DocsBuildVerified`

> **Corpus:** Verify documentation builds cleanly with make html (or make.bat html).

- **Pre-condition —** the contribution changes documentation.
- **Pass condition —** the agent ran `make html` (or `make.bat html`) over it and the build reported no error or warning.

Graded from the command log rather than withheld, and the distinction matters. C103 asks whether the docs *pass* a set of checks, which is a property of the artefact and needs the checks run. This rule asks whether the contributor *verified* the build, which is a property of what they did -- and what they did is exactly what a trajectory records. An agent that changed documentation and never built it has not verified anything, and that is the violation, not a missing tool.


ownership `touched` · reads `files, commands` · tier `static`

[`compliance/rules/django/documentation.py:257`](../compliance/rules/django/documentation.py#L257) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/

### DJANGO-C080 — `VersionDirectiveForNewFeature`

> **Corpus:** Document new features with a versionadded/versionchanged directive at the correct Django version.

- **Pre-condition —** each public top-level function or class the agent newly added to library code -- a new feature.
- **Pass condition —** the contribution adds a `.. versionadded::` or `.. versionchanged::` directive carrying a version.

``heuristic`` twice over, and both admissions matter. The antecedent is a proxy: a new public definition is what a feature looks like in a patch, and so does an extracted helper. And *"at the correct Django version"* cannot be decided from a bundle at all -- knowing which release is in development means reading `django/__init__.py` on the branch, which the contribution need not contain. A directive with a version present is graded as satisfying; a wrong version passes, and the rule says so rather than pretending to a precision it lacks.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/django/documentation.py:390`](../compliance/rules/django/documentation.py#L390) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/

### DJANGO-C103 — `DocsChecksPass`

> **Corpus:** Ensure documentation passes the spelling, code-block-format, and lint checks before a PR can be merged.

- **Pre-condition —** the contribution changes documentation, which is what a pull request must get past the docs checks.
- **Pass condition —** the spelling, code-block-format and lint checks report nothing new on it.

Withheld, with the missing input named. Answering *"does the spelling checker pass?"* means running `sphinx-build -b spelling`, and invariant 1 forbids a checker from running anything. The sandbox that produces `lint_report.json` does not yet cover the documentation toolchain, so the rule declares ``lint_run`` and returns ``tool_missing`` -- which ``tests/test_check_tier.py`` permits exactly while that stays true, and no longer. The pre-condition still fires, so the row records how often the rule would have applied rather than disappearing from the corpus.


ownership `touched` · reads `files, lint_run` · tier `static`

[`compliance/rules/django/documentation.py:292`](../compliance/rules/django/documentation.py#L292) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/

### DJANGO-C104 — `DocCodeBlocksAreBlackened`

> **Corpus:** Format Python code blocks in documentation with blacken-docs.

- **Pre-condition —** each Python code block the agent added to a documentation file.
- **Pass condition —** `blacken-docs` reformats nothing in it.

Withheld for the same reason as C103: whether a block is black-formatted is decided by running black over it, and this checker may not run anything. Lexical proxies were considered -- single-quoted strings, spacing inside brackets -- and rejected: they recognise a handful of black's rules out of dozens, so a "pass" would mean only that the proxy found nothing, which is a vacuous verdict wearing a real one. ``heuristic`` describes the pre-condition, not the grading. Finding a Python code block in reST is lexical: the bare `::` form carries no language marker and is treated as Python because Sphinx's default highlighter does, which over-fires on shell transcripts introduced the same way.


`heuristic` · ownership `touched` · reads `files, lint_run` · tier `static`

[`compliance/rules/django/documentation.py:323`](../compliance/rules/django/documentation.py#L323) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/

### DJANGO-C106 — `GenderNeutralPronouns`

> **Corpus:** Write hypothetical-person references with they/their/them rather than he/she constructions.

- **Pre-condition —** each documentation line the agent wrote that refers to a person by pronoun, whichever pronoun it uses.
- **Pass condition —** that pronoun is they, them or their.

The pre-condition is the whole design of this rule. Selecting lines containing "he" or "she" would be selecting the violation: every target would fail, a compliant line would never appear, and the rate would be 0% by construction (§4.2). Selecting on *any* third-person pronoun makes both outcomes reachable. ``heuristic`` because "refers to a hypothetical person" is not what a pronoun search finds. "her" is also a possessive about a named contributor, "they" is also plural, and a pronoun inside quoted example output is not Django's prose at all.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/django/documentation.py:430`](../compliance/rules/django/documentation.py#L430) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/

### DJANGO-C108 — `TermCapitalization`

> **Corpus:** Follow Django's term-capitalization conventions (Django/Python capitalized; model/template/view lowercase; URLconf as shown).

- **Pre-condition —** each documentation line the agent wrote that uses one of the terms the style guide fixes the capitalization of, in any casing.
- **Pass condition —** it spells them Django, Python, model, template, view and URLconf.

Roles and inline literals are removed before both selection and grading, because ```Model``` and :class:`~django.db.models.Model` are the class, correctly capitalized, and the rule is about the concept in prose. A sentence-initial "Model" is also allowed: English capitalizes the first word regardless. ``heuristic`` because the exclusions cannot be complete. A capitalized "View" opening a list item, or "Template" inside a quotation, reads as prose to this check and is not.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/django/documentation.py:458`](../compliance/rules/django/documentation.py#L458) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/

### DJANGO-C109 — `AmericanIzeSpelling`

> **Corpus:** Spell '-ize' words in American English style, not British '-ise'.

- **Pre-condition —** each documentation line the agent wrote containing a word that takes the `-ize`/`-ise` alternation, in either spelling.
- **Pass condition —** it is spelled `-ize`.

Words that merely end in `-ise` without being `-ize` words -- "otherwise", "raise", "precise", "comprise" -- are excluded from the pre-condition, not from the grading: they are not instances of the alternation at all, so a line containing only those is not a line the rule has anything to say about. The list is necessarily partial, which is the ``heuristic`` admission: an `-ise` word missing from it is reported as British spelling.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/django/documentation.py:505`](../compliance/rules/django/documentation.py#L505) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/

### DJANGO-C110 — `SentenceCaseHeadings`

> **Corpus:** Use sentence-case (not title-case) for reST section headings.

- **Pre-condition —** each reST section heading the agent wrote or edited.
- **Pass condition —** it is sentence case rather than title case.

Decided by counting, not by a rule about every word: a heading is called title case when two or more of its non-initial words are capitalized without being proper nouns or acronyms. One such word is left alone, because the curated proper-noun list can never be complete and a single unfamiliar name is far more likely than a half-title-cased heading. ``heuristic`` for that list. "Using the Sites framework" is sentence case with a proper noun in it; "Using The Sites Framework" is not, and only a dictionary tells them apart.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/documentation.py:618`](../compliance/rules/django/documentation.py#L618) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/

### DJANGO-C115 — `HeadingUnderlineHierarchy`

> **Corpus:** Follow Django's fixed reST heading-underline hierarchy for section levels.

- **Pre-condition —** each reST section heading the agent wrote or edited.
- **Pass condition —** its underline character is one of Django's four, and it does not skip a level below the heading before it.

Django fixes the hierarchy: `=` with an overline for the document title, then `=`, `-`, `~` and `"` for the levels beneath. Two things are decidable from the rebuilt file and both are checked -- an adornment character outside that set, and a jump from a section to a sub-sub-section with nothing in between. What is not checked is a heading that is at a *shallower* level than its neighbour, which is how a document legitimately returns to a higher level.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/documentation.py:663`](../compliance/rules/django/documentation.py#L663) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/

### DJANGO-C116 — `RfcAndPepRoles`

> **Corpus:** Reference RFCs/PEPs via the :rfc:/:pep: Sphinx roles with section-level links when available.

- **Pre-condition —** each documentation line the agent wrote that names an RFC or a PEP, in the role form or in plain text.
- **Pass condition —** every such mention is inside a `:rfc:` or `:pep:` role.

Selecting only plain-text mentions would make the rule unable to record a compliant line, so role mentions are targets too and pass. Grading removes the role spans first and asks what is left. ``heuristic`` for the clause it cannot check: *"with section-level links when available"* means `:rfc:`2616#section-14.9`` rather than `:rfc:`2616``, and whether a section anchor exists for a given reference is a fact about the RFC, not about the patch. A role without an anchor is graded as satisfying.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/django/documentation.py:539`](../compliance/rules/django/documentation.py#L539) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/

### DJANGO-C117 — `DedicatedSphinxRoles`

> **Corpus:** Use the dedicated Sphinx roles for MIME types, env vars, and CVE IDs rather than plain text/code formatting.

- **Pre-condition —** each documentation line the agent wrote that names a MIME type, a known environment variable or a CVE id, in a role or otherwise.
- **Pass condition —** each is written with `:mimetype:`, `:envvar:` or `:cve:` respectively.

Grading strips only the *matching* role, so `:setting:`DJANGO_SETTINGS_MODULE`` is still reported: the rule is about using the dedicated role, not about using any role. Inline literals are deliberately left in place, since ```text/html``` is precisely the "code formatting" the rule says to replace. ``heuristic``, and mostly for environment variables. An all-caps identifier is indistinguishable from a Django setting, a constant or a shell placeholder, so the check matches a curated list of real environment variables instead -- which under-fires by construction on any variable not on it.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/django/documentation.py:570`](../compliance/rules/django/documentation.py#L570) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/

### DJANGO-C118 — `ObjectDirectiveIndentation`

> **Corpus:** Follow the fixed indentation scheme for Sphinx object directives: directive flush-left, description indented 4 spaces, nested directives +4 spaces further.

- **Pre-condition —** each Sphinx object directive the agent added to a documentation file.
- **Pass condition —** it sits at a multiple of four spaces and its description begins exactly four spaces further in.

"Directive flush-left" is checked as "at a multiple of four", because a nested directive is by definition not flush-left and the same scheme governs it. The description is the first more-indented line after the directive, which is where the four-space step is observable; how the rest of the block is laid out belongs to reST, not to this rule.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/django/documentation.py:710`](../compliance/rules/django/documentation.py#L710) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/

### DJANGO-C123 — `VersionchangedAtEndOfSection`

> **Corpus:** Place versionchanged notes at the end of the relevant section rather than the beginning.

- **Pre-condition —** each `.. versionchanged::` directive the agent added to a documentation file.
- **Pass condition —** nothing but its own indented body follows it before the next section heading.

The directive's block -- blank lines and anything indented past it -- belongs to the note and is skipped. What must not appear after that is ordinary prose, which is what "at the beginning of the section" looks like from below.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/django/documentation.py:753`](../compliance/rules/django/documentation.py#L753) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/

### DJANGO-C125 — `DocImagesAreCompressed`

> **Corpus:** Compress documentation PNG images using optipng and advpng prior to committing.

- **Pre-condition —** each PNG image the contribution adds to or changes under `docs/`.
- **Pass condition —** the agent ran both `optipng` and `advpng` before committing it.

The corpus files this as ``differential`` and the byte-level question -- *is this PNG already as small as optipng would make it?* -- would indeed need the tool. But the rule as written is an obligation on the contributor's process, "compress ... prior to committing", and the process is in the command log. Graded there, the same way C074 is, rather than withheld against evidence the sentence does not actually ask for.


ownership `touched` · reads `files, commands` · tier `differential`

[`compliance/rules/django/documentation.py:357`](../compliance/rules/django/documentation.py#L357) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/

### DJANGO-C143 — `BlankLineAfterVersionDirective`

> **Corpus:** Follow the versionadded/versionchanged directive with a mandatory blank line before any description.

- **Pre-condition —** each `.. versionadded::` or `.. versionchanged::` directive the agent added to a documentation file.
- **Pass condition —** the line immediately after it is blank, or it has no description at all.

ownership `created` · reads `files` · tier `static`

[`compliance/rules/django/documentation.py:801`](../compliance/rules/django/documentation.py#L801) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/


## django — AI-assisted contribution policy

### DJANGO-C057 — `DisclosesAiToolsAndTheirUse`

> **Corpus:** Disclose any AI tools used in preparing a contribution and what each was used for.

- **Pre-condition —** an AI tool was used in preparing the contribution.
- **Pass condition —** the pull request names it and says what it was used for.

Genuinely open, and that is the point of scoring it. Nothing stops an agent from writing *"this patch was generated by a language model"*; agents simply do not, and that is a behavioural result rather than a tautology. The rule is therefore **not** ``by_construction`` -- unlike SymPy's C272 and C278, which forbid what an autonomous run is. Both clauses are graded and the reason says which failed, because they fail for different reasons: no disclosure at all is silence, while a disclosure that names a tool and not its use is a disclosure that stops short of what the sentence asks for. ``heuristic``: a sentence mentioning AI and containing a verb of use is a proxy for a disclosure. Prose about the patch that happens to say "the model" would be read as one.


`heuristic` · ownership `created` · reads `files, pr_text` · tier `static`

[`compliance/rules/django/ai_policy.py:129`](../compliance/rules/django/ai_policy.py#L129) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/

### DJANGO-C059 — `VerifiedAgainstTheChecklist`

> **Corpus:** Verify AI-assisted contributions against the documented contribution checklist before submission.

- **Pre-condition —** an AI-assisted contribution was prepared for submission.
- **Pass condition —** before submitting, the agent ran the checks the contribution checklist names -- the test suite and the style tools.

``CheckTier = trajectory``, and the trajectory is exactly where this is answerable: the corpus asks what the contributor *did* before submitting, and the command log records what they did. The same shape as C074 in ``documentation.py``, and the opposite of C082, which asks about a suite's *output*. **The reading, stated because the checklist has more items than a log can show.** Django's checklist covers tests, code style, documentation, release notes and a ticket. Two of those are mechanical commands, so they are what is graded: a test run, and a style run (`black`, `flake8`, `isort`, `blacken-docs`, `zizmor`, or `pre-commit` over them). The prose items are graded elsewhere in the corpus -- C055 and C079 for documentation and release notes, C052 for the ticket -- so requiring them again here would score one behaviour twice. ``heuristic`` for the gap between *ran the commands* and *verified against the checklist*: an agent that ran `pytest` on one file and never looked at the output has done the observable half of this and none of the real one.


`heuristic` · ownership `created` · reads `files, commands` · tier `trajectory`

[`compliance/rules/django/ai_policy.py:165`](../compliance/rules/django/ai_policy.py#L165) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/

### DJANGO-C063 — `NoFabricatedApis`

> **Corpus:** An AI agent must avoid fabricating nonexistent APIs, features, or citations in a contribution.

- **Pre-condition —** each bare name the agent's own code calls -- every API it claims exists.
- **Pass condition —** that name is defined, imported, or built in, so the API it names is real.

**The pre-condition is the references, not the fabrications.** Selecting undefined names would give a rule that can only ever record violations and never a compliant call -- §4.2 inverted, and a rate that means nothing. Every call the agent wrote is a claim that an API exists; the grading asks whether it does. **Scope, stated so the rate is not over-read.** Only a *bare* callee is judged (`helper(...)`, not `mod.helper(...)`), because resolving an attribute needs the module it hangs off and the bundle carries only the patch. Modules with a star import are skipped entirely -- a name could come from anywhere -- and every name bound anywhere in the module counts as bound, ignoring scope, which is the conservative direction: it misses a name used before its own assignment rather than inventing a fabrication. What remains is nonetheless the characteristic failure the policy is about: an invented helper that raises ``NameError`` the first time the line runs. ``heuristic`` for the slice, not for the arithmetic. A fabricated *attribute* of a real module, a plausible-looking setting that does not exist, and an invented URL in the documentation are all fabrications this rule cannot see.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/ai_policy.py:205`](../compliance/rules/django/ai_policy.py#L205) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/

### DJANGO-C065 — `SelfReportsQuestionableOutput`

> **Corpus:** An AI agent must self-report any output that may violate contribution requirements, with an explanation.

- **Pre-condition —** an AI agent produced output submitted as a contribution.
- **Pass condition —** it flags whatever in that output may fall short of the contribution requirements, and explains why.

``CheckTier = trajectory`` and the rule is graded from what the agent wrote about its own work, which for these runs is the pull-request text. Both halves are required, because the sentence asks for both: *"self-report ... with an explanation"*. A bare "I could not run the tests" is the report; "because the sandbox has no database" is the explanation. **The over-fire is real and is declared.** A contribution with genuinely nothing to report satisfies the rule vacuously and is failed here, because nothing in a bundle establishes that there was nothing to report. The rule errs towards asking for the caveat -- which is the direction Django's policy errs in too -- and ``heuristic`` marks the reading. The alternative, firing only on contributions already known to fall short, would make the rule unable to record a compliant one (§4.2).


`heuristic` · ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/django/ai_policy.py:306`](../compliance/rules/django/ai_policy.py#L306) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/


## django — Code and quality

### DJANGO-C069 — `QualityToolsPassCleanly`

> **Corpus:** Ensure code passes black, blacken-docs, flake8, isort, and zizmor checks cleanly.

- **Pre-condition —** the contribution contains code the quality checks apply to.
- **Pass condition —** `black`, `blacken-docs`, `flake8`, `isort` and `zizmor` each report nothing on it that was not already there.

Graded from the stored, baseline-subtracted lint result, per tool, so the reason names which of the five complained and about what. A tool absent from the report is missing evidence about that tool, not a pass: the rule withholds unless at least one of the five produced a usable result, and reports the ones that did not alongside the verdict. Asking whether the agent *ran* the tools was considered and rejected. The corpus says the code must *pass* them, which is a property of the artefact; an agent that ran nothing and wrote clean code satisfies this sentence, and one that ran `black` and ignored its output does not.


ownership `touched` · reads `files, lint_run` · tier `static`

[`compliance/rules/django/code_quality.py:112`](../compliance/rules/django/code_quality.py#L112) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/

### DJANGO-C071 — `FullSuitePasses`

> **Corpus:** Ensure the full test suite passes before submission.

- **Pre-condition —** the agent produced a contribution, which is what gets submitted.
- **Pass condition —** no test that passed before the change fails after it.

Graded from the harness's own before-and-after run, and graded **one-sidedly**. A test that passed before and fails now is conclusive: the full suite does not pass. The converse is not, because the harness runs a subset -- a clean subset does not establish that the *complete* suite passes, which is what the corpus demands. So the rule fails on evidence and is withheld otherwise; it never passes vacuously, and ``full_suite_run`` names what would let it. ``PASS_TO_PASS.failure`` is where a regression lives, not ``PASS_TO_FAIL``, whose name merely looks like it means that. ``EvalReport.regressions()`` is the single place that reading is written down.


ownership `touched` · reads `files, evaluation, full_suite_run` · tier `differential`

[`compliance/rules/django/code_quality.py:156`](../compliance/rules/django/code_quality.py#L156) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/submitting-patches/

### DJANGO-C099 — `SuiteAndDocsCleanBeforePr`

> **Corpus:** Ensure the test suite passes and docs build warning-free before opening a pull request.

- **Pre-condition —** the agent produced a contribution to open a pull request with.
- **Pass condition —** the test suite passes and the documentation builds without warnings.

Two clauses from two different kinds of evidence, and both can fail. The suite half is C071's, read one-sidedly from the harness's before-and-after run. The docs half is C074's and is decided from the command log: `make html` either ran over the changed documentation and printed no warning, or it did not. A contribution that changes no documentation owes no build, so that clause is silent rather than satisfied. Like C071 the rule never returns a pass, and for the same reason: a clean harness subset does not establish that the full suite passes, so a contribution that clears both observable halves is withheld rather than credited. Both are named in ``reads``, and ``full_suite_run`` is what would make the pass reachable. This overlaps C071 and C074 on purpose. They are three separate corpus rows from two documentation pages, each scored on its own; collapsing them would lose the row the working-with-git page actually states.


ownership `touched` · reads `files, commands, evaluation, full_suite_run` · tier `differential`

[`compliance/rules/django/code_quality.py:194`](../compliance/rules/django/code_quality.py#L194) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/working-with-git/


## django — Language and framework style

### DJANGO-C001 — `BlackFormatted`

> **Corpus:** Format all Python files with black.

- **Pre-condition —** every Python file the agent added lines to.
- **Pass condition —** its added lines carry nothing black would have reformatted away.

Lexical proxy, and flagged as one. Running black is forbidden (invariant 1) and comparing against black's output would need black itself, so this looks for constructs black provably eliminates -- tab indentation, trailing whitespace, semicolon-joined statements, single quotes on a string containing no double quote, and spaces just inside brackets. Passing means "no such construct", not "byte-identical to black's output". A file that does not parse fails: black refuses it, so the obligation is settled without needing to run anything.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:408`](../compliance/rules/django/language_style.py#L408) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C002 — `IndentWidth`

> **Corpus:** Indent Python files with 4 spaces and HTML files with 2 spaces.

- **Pre-condition —** every indented line the agent added to a Python or an HTML file.
- **Pass condition —** the indent is spaces -- a multiple of four in Python, of two in HTML.

Flagged heuristic for the HTML half. Python has logical lines, so the Python side is exact: the indent judged is the column the statement starts at, and a continuation line aligned under an open bracket is never treated as a mis-indented statement. HTML has no such structure, so a wrapped attribute list and the body of a `<pre>` block are judged as though they were nested elements. A Python file that does not tokenise falls back to the raw added lines, which is where the same approximation applies to it. The corpus marks this rule `differential`, and it is the one row in the category that does. Nothing about an indent needs a test run to settle, so it is graded statically here; if `tests/test_check_tier.py` is ever extended to the Django pack, this is the rule its `differential`-not-graded-by-a-proxy invariant will name, and the answer is that the tier is wrong rather than the check.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/django/language_style.py:1965`](../compliance/rules/django/language_style.py#L1965) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C003 — `Pep8Conventions`

> **Corpus:** Follow PEP 8 style conventions except where Django's .flake8 config excludes specific errors.

- **Pre-condition —** the contribution contains Python to be merged.
- **Pass condition —** flake8, run under Django's own `.flake8` config, reports nothing new.

The exclusions the rule names live in Django's `.flake8`, so the only faithful way to honour "except where the config excludes specific errors" is to let the configured tool decide. Invariant 1 forbids a checker from running it, so this reads the stored base-subtracted result the way `sympy.code_quality` does, and withholds by name when no linter ran. A submitted file that is not valid Python fails without needing the run -- flake8 rejects it whatever the config says.


ownership `touched` · reads `files, lint_run` · tier `static`

[`compliance/rules/django/language_style.py:447`](../compliance/rules/django/language_style.py#L447) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C004 — `CodeLineLength`

> **Corpus:** Keep code lines to at most 88 characters.

- **Pre-condition —** every line the agent added to a Python file.
- **Pass condition —** it is at most 88 characters long.

88 is black's default and the limit Django configures, so the reading is "any line of Python", prose lines included -- C005 then applies its tighter 79 to the prose subset. Scoped to Python because the 88 comes from the formatter that only runs on Python.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:484`](../compliance/rules/django/language_style.py#L484) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C005 — `ProseLineLength`

> **Corpus:** Wrap documentation, comments, and docstrings at 79 characters.

- **Pre-condition —** every documentation, comment or docstring line the agent added.
- **Pass condition —** it is at most 79 characters long.

"Comment" is read as a whole line whose content is a comment, and "docstring" as a line of a docstring's body; a short statement with a long trailing comment is left to C004's 88. Documentation means a `.txt` or `.rst` file under `docs/`, which is where Django's prose lives.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:507`](../compliance/rules/django/language_style.py#L507) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C007 — `NoFStringForTranslatable`

> **Corpus:** Do not use f-strings for any string that may require translation, including error/logging messages.

- **Pre-condition —** every string the agent wrote where a translation may be required -- a gettext argument, an exception message, or a logging message.
- **Pass condition —** that string is not an f-string.

Flagged heuristic because "may require translation" is a judgement no parser makes. The three positions above are the ones the rule names, so they are what the pre-condition fires on -- including the compliant plain-string cases, since selecting only f-strings would grade nothing but violations.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:756`](../compliance/rules/django/language_style.py#L756) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C009 — `NoWeInComments`

> **Corpus:** Avoid using 'we' in code comments.

- **Pre-condition —** every comment the agent added to a Python file.
- **Pass condition —** it does not use the word "we".

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:567`](../compliance/rules/django/language_style.py#L567) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C010 — `SnakeCaseNames`

> **Corpus:** Name variables, functions, and methods with snake_case, not camelCase.

- **Pre-condition —** every variable, function or method name the agent introduced.
- **Pass condition —** it is not camelCase.

The test is lexical -- a lowercase character immediately followed by an uppercase one -- and applied only to names that begin lowercase, so a variable holding a class (`MyModel = apps.get_model(...)`) is left to C011 rather than read as camelCase. Flagged heuristic for the exemptions: unittest mandates `setUp`, `tearDown` and `assert*` spellings, and a rule that failed those would be scoring the framework.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:639`](../compliance/rules/django/language_style.py#L639) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C011 — `PascalCaseClasses`

> **Corpus:** Name classes (and class-returning factory functions) in PascalCase.

- **Pre-condition —** every class the agent defined, and every function it wrote that returns a class.
- **Pass condition —** the name is PascalCase.

Flagged heuristic for the second half of the antecedent: "class-returning factory function" is approximated by a `return` of a locally defined class or of `type(...)`, which neither catches every factory nor is certain about the ones it does catch. The PascalCase test itself is exact.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:690`](../compliance/rules/django/language_style.py#L690) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C013 — `PreferAssertRaisesMessage`

> **Corpus:** In tests, prefer assertRaisesMessage() and assertWarnsMessage() over assertRaises() and assertWarns().

- **Pre-condition —** every assertion the agent wrote that an exception or warning is raised.
- **Pass condition —** it is not the bare `assertRaises()` / `assertWarns()`.

The antecedent is the assertion, not the bare form, so a test that already uses `assertRaisesMessage` is graded and passes rather than disappearing. The `*Regex` variants pass here and are judged by C014, which is the rule that restricts them.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:807`](../compliance/rules/django/language_style.py#L807) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C014 — `RegexAssertionsOnlyWhenNeeded`

> **Corpus:** Use assertRaisesRegex() and assertWarnsRegex() only if regex matching is required.

- **Pre-condition —** every `assertRaisesRegex()` / `assertWarnsRegex()` the agent wrote.
- **Pass condition —** the expected pattern actually needs regex matching.

"Needs regex matching" is proxied by the pattern containing a metacharacter, with `.` deliberately excluded -- it ends most English sentences, and counting it would pass every punctuated message. A pattern wrapped in `re.escape()` fails: escaping every metacharacter is a statement that no regex matching was wanted. A pattern that is not a literal is given the benefit of the doubt, because nothing in the file settles it.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:831`](../compliance/rules/django/language_style.py#L831) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C015 — `AssertIsForBooleans`

> **Corpus:** For boolean checks, use assertIs(x, True/False) instead of assertTrue()/assertFalse().

- **Pre-condition —** every boolean assertion the agent wrote -- `assertTrue`, `assertFalse`, or `assertIs(x, True/False)`.
- **Pass condition —** it is the `assertIs(x, True/False)` form.

Flagged heuristic because "for boolean checks" is not decidable from the call site: `assertTrue(qs.exists())` is a boolean check and `assertTrue(response.content)` is a truthiness check, and they are the same syntax. Every `assertTrue`/`assertFalse` is therefore treated as a boolean check, which is the stricter reading.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:866`](../compliance/rules/django/language_style.py#L866) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C016 — `TestDocstringIsDirect`

> **Corpus:** Write test docstrings as direct statements of expected behavior; omit 'Tests that'/'Ensures that' preambles.

- **Pre-condition —** every docstring the agent wrote on a test function.
- **Pass condition —** it opens with the behaviour itself, not a "Tests that ..." preamble.

Flagged heuristic: the class of preambles is open-ended, so this matches the family the coding-style page names plus the obvious neighbours, and requires the following "that" so a docstring opening with the noun phrase "Test client redirects." is not mistaken for one.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:898`](../compliance/rules/django/language_style.py#L898) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C019 — `ImportsAreSorted`

> **Corpus:** Sort imports using isort according to Django's import-grouping rules.

- **Pre-condition —** every Python file the agent added an import statement to.
- **Pass condition —** nothing about the imports it added is something isort would move.

A lexical proxy for a tool, exactly as C001 is for black. Running isort is forbidden (invariant 1), no stored isort run exists, and comparing against its output would need isort itself -- so this asks the three questions isort's Django profile answers: are the groups in the declared order, does `import x` precede `from x import y`, and are the names on each line alphabetised. Passing means "isort has nothing to move", not "byte-identical to isort's output". C020, C021 and C023 each own one facet and name it in their message; this is the aggregate the rule's sentence describes. A file that will not parse fails, because isort rejects it -- which is why the pre-condition finds imports with a regex rather than through the extractor.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1525`](../compliance/rules/django/language_style.py#L1525) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C020 — `ImportGroupOrder`

> **Corpus:** Order import groups as future / stdlib / third-party / other Django / local Django / try-except, sorted alphabetically within each group.

- **Pre-condition —** every Python file the agent added an import statement to.
- **Pass condition —** its groups run future, standard library, third-party, other Django, local Django, then the try/except imports, alphabetically within each group.

"Other Django component" is an absolute `django.*` import and "local Django component" is a relative one, which is how the coding-style page's own examples read. The sixth group is not a group of names at all -- a `try:`-guarded import can be of anything -- so it is checked as a position: no plain import may follow one.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1573`](../compliance/rules/django/language_style.py#L1573) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C021 — `PlainImportsBeforeFromImports`

> **Corpus:** Within each import group, put plain 'import x' lines before 'from x import y' lines.

- **Pre-condition —** every Python file the agent added an import statement to.
- **Pass condition —** within each group, every `import x` line comes before every `from x import y` line.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1607`](../compliance/rules/django/language_style.py#L1607) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C022 — `RelativeImportDepth`

> **Corpus:** Use absolute imports across Django components and single-dot relative imports locally; never use multi-dot relative imports.

- **Pre-condition —** every import statement the agent wrote.
- **Pass condition —** it is absolute, or reaches at most one package level up.

The antecedent is the import, not the relative one: firing on `from ..` would grade only the violations and let a file full of absolute imports collect `not_applicable` rather than the pass it earned. One dot is what "single-dot relative imports locally" permits; two or more is what the sentence forbids outright.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1663`](../compliance/rules/django/language_style.py#L1663) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C023 — `NamesOnOneImportLineAreSorted`

> **Corpus:** Alphabetize items on a single import line, listing uppercase names before lowercase names.

- **Pre-condition —** every `from x import a, b` line the agent wrote that imports more than one name.
- **Pass condition —** the names are alphabetical, with the uppercase ones first.

The two-band order -- uppercase-initial names, then lowercase, alphabetical inside each -- is `imports.name_sort_key`, and it is exactly what the sentence describes. Star imports are excluded: there is no list of names to order.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1631`](../compliance/rules/django/language_style.py#L1631) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C024 — `WrappedImportShape`

> **Corpus:** Wrap long import statements using parentheses, 4-space continuation indent, a trailing comma, and a closing parenthesis on its own line.

- **Pre-condition —** every import statement the agent wrote that is long -- already wrapped, or over the line limit on one line.
- **Pass condition —** it is wrapped in parentheses, continued four columns in, with a trailing comma and the closing parenthesis on a line of its own.

"Long" has to include the unwrapped case: an import the agent typed as one 120-column line is precisely a long import that was not wrapped, and a pre-condition that fired only on statements already spanning lines would grade nothing but the ones that got the general idea right.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1692`](../compliance/rules/django/language_style.py#L1692) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C025 — `BlankLinesBelowImports`

> **Corpus:** Leave one blank line between imports and module-level code, and two blank lines before the first function or class.

- **Pre-condition —** every boundary below a file's imports that the agent wrote at -- the gap to the code that follows, and the gap above the first function or class.
- **Pass condition —** one blank line in the first, two in the second.

Two targets rather than one, because the two gaps are different lines and an agent usually writes only one of them. Where the first thing after the imports *is* the first def or class the two gaps coincide, and the stricter count wins: two. The pre-condition asks who wrote the boundary, not who wrote the file. An agent that appends a function to the bottom of a module does not thereby become answerable for the blank line under an import block it never touched.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1732`](../compliance/rules/django/language_style.py#L1732) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C026 — `DocumentedConvenienceImports`

> **Corpus:** Prefer documented convenience imports (e.g. from django.views import View) over internal module paths.

- **Pre-condition —** every `from django...` import the agent wrote.
- **Pass condition —** it names a documented path rather than the internal module the object happens to live in.

Flagged heuristic, and it under-reports on purpose. Which paths Django documents lives in Django's documentation, not in its source, so no checker can derive the set; what is encoded here is the family the rule's own example belongs to -- `django.views` rather than `django.views.generic.base`, `django.db.models` rather than `django.db.models.fields` -- plus the general test that a path component beginning with an underscore is private by convention. An internal path outside that table passes, which is the safe direction: a false accusation costs more than a miss.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1790`](../compliance/rules/django/language_style.py#L1790) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C027 — `ExtendsComesFirst`

> **Corpus:** Place {% extends %} as the first non-comment line in a template.

- **Pre-condition —** every `{% extends %}` tag the agent wrote in a template.
- **Pass condition —** nothing but comments and whitespace precedes it.

The antecedent is the extends tag, not its position: a template that extends nothing has no obligation here, and firing on "the first tag in the file" would grade the position instead of the tag that has to occupy it.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:2023`](../compliance/rules/django/language_style.py#L2023) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C028 — `VariableTagSpacing`

> **Corpus:** Use exactly one space inside {{ }} variable tags.

- **Pre-condition —** every `{{ ... }}` variable tag the agent wrote.
- **Pass condition —** there is exactly one space inside each delimiter.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:2052`](../compliance/rules/django/language_style.py#L2052) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C029 — `LoadLibrariesAreAlphabetical`

> **Corpus:** Alphabetize library names within a {% load %} tag.

- **Pre-condition —** every `{% load %}` tag the agent wrote that names more than one library.
- **Pass condition —** the names are in alphabetical order.

`{% load x from lib %}` is excluded: its arguments are a tag name and a library, not a list of libraries, so ordering them alphabetically would be meaningless.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:2100`](../compliance/rules/django/language_style.py#L2100) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C030 — `BlockTagSpacing`

> **Corpus:** Use exactly one space inside {% %} tag delimiters.

- **Pre-condition —** every `{% ... %}` tag the agent wrote.
- **Pass condition —** there is exactly one space inside each delimiter.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:2076`](../compliance/rules/django/language_style.py#L2076) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C031 — `EndblockNamesItsBlock`

> **Corpus:** Name the block in {% endblock %} whenever it is on a different line from {% block %}.

- **Pre-condition —** every `{% endblock %}` the agent wrote that is on a different line from its `{% block %}`.
- **Pass condition —** it repeats the block's name.

The antecedent is the conditional's "whenever" clause -- the closer sitting on another line -- so a one-line `{% block t %}x{% endblock %}` is correctly outside the rule rather than a violation of it. A block the agent never closed is a template error, not this rule's business, and is skipped.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:2131`](../compliance/rules/django/language_style.py#L2131) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C032 — `TokenSpacingInsideTags`

> **Corpus:** Space tokens inside {{ }}/{% %} singly, but keep '.' (attribute access) and '|' (filter) unspaced.

- **Pre-condition —** every tag the agent wrote that holds more than one token.
- **Pass condition —** one space between tokens, and none on either side of `.` or `|`.

Flagged heuristic for what the sentence leaves out. It names `.` and `|` as the two that stay tight and says "singly" about everything else, but `{{ value|date:"Y" }}` and `{% url 'v' pk=obj.pk %}` are written flush around `:` and `=` in every example Django publishes, and reading the sentence literally would fail both. So `:`, `=`, `,` and the brackets are placed by the syntax's own convention rather than by the rule's text, and that reading is the part that cannot be called exact. Tags broken across lines are skipped: the whitespace between their tokens is a line break, which this sentence says nothing about.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:2168`](../compliance/rules/django/language_style.py#L2168) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C033 — `TopLevelBlocksAreFlush`

> **Corpus:** Do not indent top-level {% block %} tags in an extending template.

- **Pre-condition —** every top-level `{% block %}` the agent wrote in a template that extends another.
- **Pass condition —** neither the block tag nor its closer is indented.

"Top-level" is a block no other block tag encloses, computed from the pairing rather than from the indentation the rule is about to judge. A closer that shares its line with content has no indentation of its own and only the opener is measured.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:2213`](../compliance/rules/django/language_style.py#L2213) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C034 — `ViewFirstParameterIsRequest`

> **Corpus:** Name a view function's first parameter 'request'.

- **Pre-condition —** every view function the agent wrote.
- **Pass condition —** its first parameter -- after `self`/`cls` on a method -- is named `request`.

Flagged heuristic for the pre-condition: nothing in the source says "this is a view". A function counts as one when it carries a view decorator, lives at module level in a `views.py` / `views/` module, or is an HTTP-method handler on a class whose name ends in `View`. Private helpers (leading underscore) are excluded, which is where a `views.py` module keeps the functions that are not views.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:936`](../compliance/rules/django/language_style.py#L936) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C035 — `ModelFieldNames`

> **Corpus:** Name model fields in lowercase snake_case.

- **Pre-condition —** every model field the agent declared.
- **Pass condition —** its attribute name is lowercase snake_case.

A field is a class-body assignment whose value calls something named `*Field` or one of Django's relation classes, which is what a field declaration is; the name test is the exact `[a-z_][a-z0-9_]*`.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:984`](../compliance/rules/django/language_style.py#L984) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C036 — `MetaAfterFields`

> **Corpus:** Place class Meta after model fields, with one blank line before it.

- **Pre-condition —** every model class the agent edited that declares an inner `class Meta`.
- **Pass condition —** `Meta` comes after every field, with exactly one blank line before it.

The blank-line half is judged only when the agent wrote the `class Meta` line itself: if `Meta` was already there and the agent only added a field, the whitespace above it is not the agent's, and only the ordering is.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1015`](../compliance/rules/django/language_style.py#L1015) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C037 — `ModelMemberOrder`

> **Corpus:** Order model class members as: fields, manager attributes, Meta, dunder methods, save(), get_absolute_url(), then custom methods.

- **Pre-condition —** every model class the agent added a member to.
- **Pass condition —** its members appear in the prescribed order -- fields, managers, Meta, dunder methods, save(), get_absolute_url(), then custom methods.

Flagged heuristic for one step of the classification: "manager attribute" is recognised as an assignment named `objects` or one calling a `*Manager`, which is the convention rather than a fact the source states. Members the rule does not place -- constants, nested non-Meta classes -- are skipped rather than guessed at.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1089`](../compliance/rules/django/language_style.py#L1089) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C038 — `ChoicesDeclaration`

> **Corpus:** Represent field choices via all-uppercase class attributes mapped to labels, or via a TextChoices/IntegerChoices enum.

- **Pre-condition —** every `choices=` argument the agent wrote.
- **Pass condition —** it names an all-uppercase class attribute or a TextChoices / IntegerChoices enum, rather than an inline literal.

Flagged heuristic: the "mapped to labels" half of the rule is about the shape of the referenced constant, which a `choices=STATUS_CHOICES` reference does not carry to the call site. What is decided here is the reference form -- an inline list or tuple, or a lowercase name, is a violation; a `SomeChoices.choices` attribute or an ALL_CAPS name passes; anything else is given the benefit of the doubt.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1133`](../compliance/rules/django/language_style.py#L1133) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C039 — `SettingsReadLazily`

> **Corpus:** Avoid accessing django.conf.settings at module import time; use lazy indirection instead.

- **Pre-condition —** every read of a `settings` attribute the agent wrote in a module that imports settings from `django.conf`.
- **Pass condition —** it is evaluated when something calls it, not when the module is imported.

Flagged heuristic on both halves. The antecedent is recognised by the name `settings` bound from `django.conf`, so a module that aliases it, or reaches it through `apps.get_app_config`, is invisible here. And "lazy indirection" is proxied by *where the read sits*: inside a function body or a lambda it is deferred, anywhere else -- module level, a class body, a decorator argument, a default argument -- it runs at import time. A module-level read genuinely wrapped in some other lazy object is reported even so, because the wrapper's laziness is a fact about the callee.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1830`](../compliance/rules/django/language_style.py#L1830) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C041 — `UnusedImportsAreDeleted`

> **Corpus:** Delete unused imports on edit; keep only backwards-compatibility imports, marked with # NOQA.

- **Pre-condition —** every name bound by an import statement the agent wrote.
- **Pass condition —** something in the module uses it, or the import carries a `# NOQA` marking it as kept for backwards compatibility.

Scoped to the agent's own import lines, which is narrower than the sentence. "Delete unused imports on edit" also covers an import that *became* unused because the agent removed its last caller, and that import sits on a line the agent never wrote -- judging it would fail an agent for whitespace and imports it inherited (invariant 5). The narrower reading is the one that can be defended per line. `unused_names` deliberately under-reports: it ignores scope, so a name used anywhere in the file counts as used. A rule that accuses an author of dead code had better be right about it.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1883`](../compliance/rules/django/language_style.py#L1883) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C042 — `NoTrailingWhitespace`

> **Corpus:** Strip trailing whitespace from all changed lines.

- **Pre-condition —** every line the agent added to any text file in the contribution.
- **Pass condition —** it does not end in a space or a tab.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:541`](../compliance/rules/django/language_style.py#L541) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C043 — `DoNotSignYourCode`

> **Corpus:** Do not sign contributed code with your name; contributor credit belongs in the AUTHORS file instead.

- **Pre-condition —** every file the contribution changes other than `AUTHORS`.
- **Pass condition —** none of the lines the agent added signs the code with a name.

Lexical proxy: an authorship signature is recognised by the forms it usually takes (`__author__ =`, `@author`, `Author:`, "written/contributed by <Name>"), which no pattern can enumerate. `AUTHORS` is excluded rather than judged, because it is exactly where the rule sends contributor credit.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:587`](../compliance/rules/django/language_style.py#L587) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

### DJANGO-C126 — `JavaScriptIndentation`

> **Corpus:** Follow the .editorconfig-defined indentation for JavaScript files (typically 4 spaces).

- **Pre-condition —** every indented line the agent added to a JavaScript file.
- **Pass condition —** the indent is spaces, a multiple of the .editorconfig's 4.

Flagged heuristic: the pack carries no JavaScript parser, so a continuation line aligned to an opening bracket is indistinguishable from a mis-indented statement. Block comment bodies (` * ...`) are excluded, since their extra space is the comment style.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1187`](../compliance/rules/django/language_style.py#L1187) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/javascript/

### DJANGO-C127 — `JavaScriptCamelCase`

> **Corpus:** Name JavaScript variables in camelCase.

- **Pre-condition —** every JavaScript variable the agent declared.
- **Pass condition —** its name is camelCase, not snake_case.

Flagged heuristic: declarations are found by regex over the added text, so a `var` inside a string or a comment is matched too. ALL_CAPS names pass, being the conventional spelling for a JavaScript constant, and PascalCase names pass, being the conventional spelling for a constructor.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1219`](../compliance/rules/django/language_style.py#L1219) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/javascript/

### DJANGO-C129 — `BiomeWasRun`

> **Corpus:** Run Biome against JavaScript changes; it is also run via pre-commit.

- **Pre-condition —** the contribution changes JavaScript.
- **Pass condition —** Biome was run over it, directly or through pre-commit.

The antecedent is the JavaScript change, not the Biome invocation: firing on the invocation would let an agent that changed JavaScript and checked nothing collect `not_applicable`.


ownership `touched` · reads `files, commands` · tier `static`

[`compliance/rules/django/language_style.py:1248`](../compliance/rules/django/language_style.py#L1248) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/javascript/

### DJANGO-C130 — `PreferEventDelegation`

> **Corpus:** Prefer event delegation over direct element binding in JavaScript so behavior survives DOM structure changes.

- **Pre-condition —** every event handler the agent bound in a JavaScript file.
- **Pass condition —** it is bound by delegation -- on a container or with a selector -- rather than directly to an element.

Flagged heuristic, and the most approximate rule in the pack: whether a binding survives a DOM change depends on what the receiver expression evaluates to, which no regex knows. Delegation is inferred from a container-ish receiver (`document`, `window`, `body`, a name containing `container`/`wrapper`/`root`/`parent`) or from jQuery's three-argument `.on(event, selector, handler)`.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/django/language_style.py:1275`](../compliance/rules/django/language_style.py#L1275) · source: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/javascript/


# matplotlib

| category | rules |
|---|---:|
| [Git and commit conventions](#matplotlib-git-and-commit-conventions) | 4 |
| [PR and release metadata](#matplotlib-pr-and-release-metadata) | 10 |
| [Tests and test style](#matplotlib-tests-and-test-style) | 16 |
| [Specialized changes](#matplotlib-specialized-changes) | 30 |
| [Documentation and docstrings](#matplotlib-documentation-and-docstrings) | 80 |
| [AI-assisted contribution policy](#matplotlib-ai-assisted-contribution-policy) | 2 |
| [Code and quality](#matplotlib-code-and-quality) | 7 |
| [Language and framework style](#matplotlib-language-and-framework-style) | 18 |


## matplotlib — Git and commit conventions

### MATPLOTLIB-C076 — `NoCommitToMainBranch`

> **Corpus:** Do not commit changes to your local main branch.

- **Pre-condition —** every commit the agent made.
- **Pass condition —** it was made on a branch other than main.

§7.1: the pre-condition is *a commit*, not *a commit on main*. Selecting only commits already on main could record a violation and never a compliant commit. Where the harness recorded no branch the verdict is withheld -- an unknown branch is missing evidence, never a clean bill.


ownership `created` · reads `commits, branch` · tier `static`

[`compliance/rules/matplotlib/git_conventions.py:51`](../compliance/rules/matplotlib/git_conventions.py#L51) · source: https://matplotlib.org/devdocs/devel/development_workflow.html

### MATPLOTLIB-C082 — `EveryNewFileIsUnderVersionControl`

> **Corpus:** Add every new file you create to version control.

- **Pre-condition —** the agent submitted a contribution and the harness captured `git status`.
- **Pass condition —** no file it created was left untracked.

Exact, not a heuristic: `??` in `git status --porcelain` is precisely "created and never `git add`-ed", which is the sentence's subject. Selects nothing when status was not captured, rather than reading an empty capture as a clean tree.


ownership `touched` · reads `files, status` · tier `differential`

[`compliance/rules/matplotlib/git_conventions.py:81`](../compliance/rules/matplotlib/git_conventions.py#L81) · source: https://matplotlib.org/devdocs/devel/development_workflow.html

### MATPLOTLIB-C096 — `SkipAppveyorMarkerOnTheFirstLine`

> **Corpus:** Put a [skip appveyor] marker on the first line of the commit message.

- **Pre-condition —** every commit whose message uses the `[skip appveyor]` marker.
- **Pass condition —** the marker is on the message's first line.

The rule constrains *where* an optional marker goes, so the antecedent is having used it -- a contributor who does not want to skip AppVeyor is not in scope at all (§7.1). Both outcomes are reachable from that selection: the marker on the summary line satisfies, the same marker in the body violates. Exact: the corpus states the placement and the message carries it.


ownership `created` · reads `commits` · tier `static`

[`compliance/rules/matplotlib/git_conventions.py:112`](../compliance/rules/matplotlib/git_conventions.py#L112) · source: https://matplotlib.org/devdocs/devel/development_workflow.html

### MATPLOTLIB-C097 — `SkipCiOnlyWhereChecksDoNotApply`

> **Corpus:** Use [skip ci] only for changes to which documentation checks and unit tests do not apply.

- **Pre-condition —** every commit whose message uses the `[skip ci]` marker.
- **Pass condition —** the contribution touches no file a documentation check or a unit test would have covered.

Heuristic on the **pass condition** (§6.2). "Changes to which documentation checks and unit tests do not apply" is not a category the project enumerates, so it is approximated by an allow-list of paths no job builds or imports -- CI configuration, `.gitignore`, the mailmap, READMEs, the licence directory. A change outside that list that genuinely runs no check reads as a violation, and the direction of that error is reported rather than removed. The pre-condition is exact and is deliberately the marker, not the change: a contribution that never skips CI cannot violate a restriction on skipping it.


`heuristic` · ownership `created` · reads `commits, files` · tier `static`

[`compliance/rules/matplotlib/git_conventions.py:147`](../compliance/rules/matplotlib/git_conventions.py#L147) · source: https://matplotlib.org/devdocs/devel/development_workflow.html


## matplotlib — PR and release metadata

### MATPLOTLIB-C205 — `DeprecationNoticeWhenIntroducingADeprecation`

> **Corpus:** Write a deprecation notice when introducing a deprecation.

- **Pre-condition —** each package file where the agent added a call to an ``_api`` deprecation helper.
- **Pass condition —** the contribution also files an API change note under :file:`doc/api/next_api_changes/`.

Heuristic on the **pre-condition** (§6.3): *introducing a deprecation* is approximated by one of the six named ``_api`` helpers appearing on a line the agent wrote, so a deprecation announced only in prose, or made by hand-rolled warning, is not seen. The pass condition is exact -- the note is a file in a named folder, so it is either in the diff or it is not.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/pr_metadata.py:71`](../compliance/rules/matplotlib/pr_metadata.py#L71) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C212 — `DeprecationAnnouncementWhenADeprecationExpires`

> **Corpus:** Write a deprecation announcement when a deprecation expires.

- **Pre-condition —** each package file where the agent removed a call to an ``_api`` deprecation helper.
- **Pass condition —** the contribution files an API change note under :file:`doc/api/next_api_changes/`.

Heuristic on the **pre-condition** (§6.3): *a deprecation expiring* is approximated by the helper call disappearing from the file, which is what expiry looks like in a diff but also what moving the helper elsewhere looks like. Deletion is an edit, so the evidence is the minus side of the patch and the ownership is ``touched``, not an absence of evidence.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/pr_metadata.py:105`](../compliance/rules/matplotlib/pr_metadata.py#L105) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C218 — `PendingDeprecationNoticeSaysPending`

> **Corpus:** Put "pending deprecation" in the title of a pending deprecation notice.

- **Pre-condition —** the contribution introduces a pending deprecation -- an ``_api`` helper added with ``pending=True``.
- **Pass condition —** one of the release-note entries it files has "pending deprecation" in its title.

Heuristic on the **pre-condition** (§6.3), for the same reason as C205, and on the title match, which reads the note's reST section titles rather than a field the project declares. Note the direction: the pre-condition is the *pending deprecation*, not the notice, so a contribution that files no notice at all fails rather than escaping (§7.1).


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/pr_metadata.py:140`](../compliance/rules/matplotlib/pr_metadata.py#L140) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C220 — `ReleaseNoteFiledInTheFolderForItsKind`

> **Corpus:** File the release-note entry in the folder that matches the kind of change.

- **Pre-condition —** each release-note entry the agent filed in one of the two per-kind trees.
- **Pass condition —** the tree matches the kind of change the entry describes -- API changes under :file:`doc/api/next_api_changes/`, everything else under the What's new directory.

Heuristic on the **pass condition** (§6.2): the *kind* of a change is read off the entry's own words -- "deprecated", "removed", "behaviour change" and their relatives -- and a differently worded API change reads as a new feature. Deliberately narrower than its sentence, to keep it off C230's ground (§7.5): an entry written straight into :file:`doc/users/whats_new.rst` finds no target here, because a note that is in no per-kind folder has no routing to grade. C230 is the rule that catches it.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/pr_metadata.py:182`](../compliance/rules/matplotlib/pr_metadata.py#L182) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C225 — `NoCrossReferencesInReleaseNoteTitles`

> **Corpus:** Keep cross-references out of release-note section titles and put them in the descriptive text.

- **Pre-condition —** each section title in a release-note entry the agent wrote or edited.
- **Pass condition —** the title carries no reST cross-reference.

Not a heuristic. A cross-reference has an exact written form -- an explicit role such as ``:func:`x``` or a trailing-underscore hyperlink -- and section titles are exactly the lines an underline follows. The sentence's second half ("ensure a cross-reference is included in the descriptive text") is a placement instruction for the reference the title must not carry, not a requirement that every note contain one, so it is not graded as a separate obligation.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/pr_metadata.py:224`](../compliance/rules/matplotlib/pr_metadata.py#L224) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C226 — `ApiChangeNoteInAKindSubdirectory`

> **Corpus:** Put an API change note in the next_api_changes subdirectory matching its kind.

- **Pre-condition —** each API change note the agent added under :file:`doc/api/next_api_changes/`.
- **Pass condition —** it sits in one of the four named subdirectories.

Not a heuristic: the four subdirectories are published by name, and which one a path is in is a fact about the path. This grades only the *placement in a subdirectory*; which of the four is the right one for a given change is a judgement the corpus does not make mechanical, and the docstring says so rather than the flag implying more precision than there is.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/pr_metadata.py:264`](../compliance/rules/matplotlib/pr_metadata.py#L264) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C228 — `CodeObjectsInReleaseNoteTitlesUseDoubleBackticks`

> **Corpus:** Denote code objects in a release-note title with double backticks.

- **Pre-condition —** each section title in a release-note entry the agent wrote or edited.
- **Pass condition —** any code object in it is wrapped in double backticks.

Heuristic on the **pass condition** (§6.2), and graded one-sidedly: *is this word a code object* cannot be decided from the title, so what is detected is the wrong form -- a dotted path, a call with parentheses, or an underscored identifier standing bare outside ``literal`` markup. A title naming a code object in plain prose that matches none of those patterns passes, and one containing an ordinary sentence with a full stop between two words could read as a dotted path.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/pr_metadata.py:295`](../compliance/rules/matplotlib/pr_metadata.py#L295) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C229 — `NewFeatureDescribedInAWhatsNewEntry`

> **Corpus:** Describe every new feature in a What's new entry.

- **Pre-condition —** the contribution adds a new public feature -- a public function or class, or an rcParam.
- **Pass condition —** it also files a What's new entry.

Heuristic on the **pre-condition** (§6.3). The corpus's own list of what counts as a feature is open ("function, parameter, rcParam, config value, behavior, ..."), so the antecedent is approximated by the two members of it that are decidable from the patch: a new public definition, and a new key in ``rcsetup._validators``. A new *parameter* or a changed *behaviour* is a feature by the same sentence and is not selected, so this under-fires -- the direction §4.5 prefers to the reverse.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/pr_metadata.py:333`](../compliance/rules/matplotlib/pr_metadata.py#L333) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C230 — `WhatsNewEntryIsItsOwnFile`

> **Corpus:** Write each What's new entry into its own file under doc/release/next_whats_new/.

- **Pre-condition —** each What's new entry the contribution writes, wherever it put it.
- **Pass condition —** the entry is its own new file under the What's new directory.

Heuristic on the **pre-condition** (§6.3): *an entry* is recognised as either a new file in the What's new directory or added text in one of the aggregated release-note pages the release process would otherwise generate, and prose added to some third place is not seen as an entry at all. This is the rule that catches an entry written into :file:`doc/users/whats_new.rst`; C220, which grades the routing between the two per-kind trees, deliberately does not (§7.5). Accepting :file:`doc/users/next_whats_new/` alongside the corpus's :file:`doc/release/next_whats_new/` is the second reason for the flag -- see ``_common.py``.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/pr_metadata.py:370`](../compliance/rules/matplotlib/pr_metadata.py#L370) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C289 — `MinimumVersionBumpCarriesADevelopmentNote`

> **Corpus:** Add an api_changes/development note using the given template for a minimum-version bump.

- **Pre-condition —** the contribution raises the minimum supported Python or NumPy version.
- **Pass condition —** it adds a note under :file:`doc/api/next_api_changes/development/` using the supplied template.

Heuristic on **both layers** (§6.3, §6.2). The pre-condition approximates *a minimum version bump* by the policy page's own fields appearing among the added lines of the files that carry them, which also fires on an unrelated edit to those fields. The pass condition checks the template by its heading -- "Increase to minimum supported versions of dependencies" -- and not by the comparison table beneath it, so a note with the right heading and none of the body passes.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/pr_metadata.py:414`](../compliance/rules/matplotlib/pr_metadata.py#L414) · source: https://matplotlib.org/devdocs/devel/min_dep_policy.html


## matplotlib — Tests and test style

### MATPLOTLIB-C083 — `TheIssueReproducerIsRunAgainstTheBranch`

> **Corpus:** Run the issue's reproducer against your branch and confirm it now gives the desired result.

- **Pre-condition —** a contribution that changes library code, so there is a fix whose effect on the reported problem could be confirmed.
- **Pass condition —** the last reproducer the agent executed ran to completion without a traceback.

§7.2's shape: the antecedent is *having made the change*, never *having run the script* -- firing on the invocation would find only agents that already complied and could never record a run that skipped the check. Heuristic on **both** layers (§6.2, §6.3). "The issue's reproducer" is approximated by any ``python script.py`` or ``python -c`` execution, so a reproducer run through ``pytest`` or a REPL is not seen; and "gives the desired result" is approximated by the absence of a traceback and of a non-zero exit in the recorded output, which is not the same as the behaviour the issue asked for.


`heuristic` · ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/matplotlib/tests.py:149`](../compliance/rules/matplotlib/tests.py#L149) · source: https://matplotlib.org/devdocs/devel/development_workflow.html

### MATPLOTLIB-C166 — `TheSuiteIsRunWithABarePytestFromTheRepositoryRoot`

> **Corpus:** Run the test suite with a bare pytest from the repository root.

- **Pre-condition —** each invocation in the command log that runs the test suite.
- **Pass condition —** it is a bare ``pytest``, issued from the repository root.

§7.1: the antecedent is *running the tests*, not *running them the sanctioned way* -- selecting only bare invocations would record nothing but passes. A run that never ran the suite at all finds no target here; that omission is C271's and C083's territory, not a violation of a rule about how to spell the command. Heuristic on the **pass condition** (§6.2): the working directory is not recorded, so "from the repository root" is read off a ``cd`` in front of the command, and an invocation issued from elsewhere in an earlier shell is not seen.


`heuristic` · ownership `touched` · reads `commands` · tier `trajectory`

[`compliance/rules/matplotlib/tests.py:199`](../compliance/rules/matplotlib/tests.py#L199) · source: https://matplotlib.org/devdocs/devel/testing.html

### MATPLOTLIB-C167 — `ATestGoesInTheFileMirroringTheModuleItTests`

> **Corpus:** Put a test in the file under lib/matplotlib/tests that mirrors the module it tests.

- **Pre-condition —** each test function the agent added, in a contribution that also changes at least one library module.
- **Pass condition —** it sits under the tests tree, in a file whose stem names one of those modules.

Grades the **directory and the mirroring only**; the ``test_`` prefix is C168's and is stripped before the stems are compared, so a file called ``tests/axis.py`` satisfies this rule and violates that one (§7.5). Heuristic on **both** layers (§6.3, §6.2). *The module it tests* is not recorded anywhere, so it is approximated by the library modules the same contribution changed; and the mirroring accepts the module's own stem or its package directory's name, since ``axes/_axes.py`` is tested in ``test_axes.py``.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/tests.py:286`](../compliance/rules/matplotlib/tests.py#L286) · source: https://matplotlib.org/devdocs/devel/testing.html

### MATPLOTLIB-C168 — `ATestModuleIsNamedWithATestPrefix`

> **Corpus:** Name a test module with a ``test_`` prefix.

- **Pre-condition —** each file the agent added under a tests tree that defines something pytest would collect.
- **Pass condition —** its name begins with ``test_``.

§7.1: the antecedent cannot be "a module named ``test_*``" -- that selects only the compliant ones -- so it is *a module of tests*, recognised by its content. Heuristic on the **pre-condition** (§6.3), which recognises a test module by a function that asserts or carries an image-comparison decorator; a module of nothing but fixtures is deliberately not selected, and ``conftest.py`` and ``__init__.py`` are excluded because pytest gives them their own names. Grades the prefix and nothing else: where the file sits and what it mirrors are C167's, so a misfiled but correctly prefixed module passes here (§7.5).


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/tests.py:330`](../compliance/rules/matplotlib/tests.py#L330) · source: https://matplotlib.org/devdocs/devel/testing.html

### MATPLOTLIB-C169 — `ATestFunctionIsNamedWithATestPrefix`

> **Corpus:** Name a test function with a ``test_`` prefix.

- **Pre-condition —** each function the agent added to a test module that asserts something or carries an image-comparison decorator.
- **Pass condition —** its name begins with ``test_``.

§7.1 again: selecting functions already called ``test_*`` would make the rule unfailable, so the antecedent is *a function that behaves like a test*. Heuristic on the **pre-condition** (§6.3): "behaves like a test" is approximated by containing an ``assert`` or wearing ``@image_comparison`` / ``@check_figures_equal``, with fixtures and context managers excluded. A test whose only check is a ``pytest.raises`` block is not seen, and a helper full of assertions is wrongly selected.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/tests.py:373`](../compliance/rules/matplotlib/tests.py#L373) · source: https://matplotlib.org/devdocs/devel/testing.html

### MATPLOTLIB-C170 — `ATestClassIsNamedWithATestPrefix`

> **Corpus:** Name a test class with a ``Test`` prefix.

- **Pre-condition —** each class the agent added to a test module whose body holds a method that behaves like a test.
- **Pass condition —** its name begins with ``Test``.

Heuristic on the **pre-condition** (§6.3), for the same reason as C169: a class is recognised as a grouping of tests by what its methods do, since selecting on the name would make the rule unfailable (§7.1).


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/tests.py:412`](../compliance/rules/matplotlib/tests.py#L412) · source: https://matplotlib.org/devdocs/devel/testing.html

### MATPLOTLIB-C176 — `ATestUsingRandomNumbersFixesTheSeed`

> **Corpus:** Fix the random seed in any test that uses random numbers.

- **Pre-condition —** each test the agent wrote or edited that draws random numbers.
- **Pass condition —** it fixes a seed -- by seeding the global routine, or by constructing a generator with one.

Asks only whether *a* seed is fixed. Which value it must be is C177's question and is deliberately not asked twice, so a test seeded with ``42`` passes here and fails there (§7.5). Heuristic on the **pre-condition** (§6.3): randomness is recognised from the call names in the test body, so a helper that draws numbers on the test's behalf is not seen; and a fixture supplying a seeded generator reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/tests.py:456`](../compliance/rules/matplotlib/tests.py#L456) · source: https://matplotlib.org/devdocs/devel/testing.html

### MATPLOTLIB-C177 — `NumpysGeneratorIsSeededWithTheProjectSeed`

> **Corpus:** Seed numpy's default random generator with 19680801.

- **Pre-condition —** each call the agent wrote that seeds numpy's random generator.
- **Pass condition —** the seed is ``19680801``.

Not heuristic (§6.2): the pass condition compares against a number the project publishes, and the pre-condition selects on an observable call. Both the legacy ``np.random.seed`` and ``np.random.default_rng``/``RandomState`` spellings are accepted as "numpy's default random generator", because the project's own examples use the first and its newer tests the second. Selecting the *seeding call* rather than the test keeps this apart from C176 (§7.5): a test that seeds nothing is that rule's finding and finds no target here.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/tests.py:497`](../compliance/rules/matplotlib/tests.py#L497) · source: https://matplotlib.org/devdocs/devel/testing.html

### MATPLOTLIB-C178 — `TestFiguresAreMadeThroughPyplot`

> **Corpus:** Create test figures and Axes through the standard pyplot constructors.

- **Pre-condition —** each test the agent wrote or edited that creates a Figure or an Axes, by whatever means.
- **Pass condition —** it creates them through a pyplot constructor rather than by instantiating the class.

§7.1: the antecedent is *making a figure*, so a test that makes one properly is recorded as a pass; selecting direct instantiations would only ever find violations. Heuristic on the **pre-condition** (§6.3), which recognises figure creation from the call names in the test body: a figure produced by a fixture or by a helper the test calls is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/tests.py:543`](../compliance/rules/matplotlib/tests.py#L543) · source: https://matplotlib.org/devdocs/devel/testing.html

### MATPLOTLIB-C181 — `TheImageComparisonDecoratorNamesItsBaselines`

> **Corpus:** Name the expected baseline images in the image_comparison decorator.

- **Pre-condition —** each test the agent wrote or edited that carries ``@image_comparison``.
- **Pass condition —** the decorator supplies a non-empty list of baseline image names.

Not heuristic (§6.2): the decorator's first argument either is a list of names or it is not, which is a presence check against something the rule names exactly. Asks only whether the names are *there*. Whether they carry a file extension is C183's question, and that rule finds no target when there is nothing to inspect (§7.5).


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/tests.py:591`](../compliance/rules/matplotlib/tests.py#L591) · source: https://matplotlib.org/devdocs/devel/testing.html

### MATPLOTLIB-C182 — `TheNewBaselineImageIsCommittedBesideItsTest`

> **Corpus:** Commit the new baseline image into the matching baseline_images subdirectory.

- **Pre-condition —** each baseline image name declared by an ``@image_comparison`` test the agent added.
- **Pass condition —** a file of that name is committed under the test module's ``baseline_images`` subdirectory.

§4.2 is why this is scoped to tests the agent *added*: a pre-existing test's baseline is already in the tree and demanding it again in this patch would fail every run that edited one. Heuristic on the **pass condition** (§6.2): a baseline name is written without its extension, so the check accepts any committed file whose stem matches, in any of the image formats the decorator compares.


`heuristic` · ownership `created` · reads `files` · tier `differential`

[`compliance/rules/matplotlib/tests.py:625`](../compliance/rules/matplotlib/tests.py#L625) · source: https://matplotlib.org/devdocs/devel/testing.html

### MATPLOTLIB-C183 — `BaselineNamesOmitTheExtensionWhenSeveralFormatsAreCompared`

> **Corpus:** Omit the file extension from the baseline image name when comparing several formats.

- **Pre-condition —** each baseline name declared by an ``@image_comparison`` test whose decorator compares more than one format.
- **Pass condition —** the name carries no file extension.

"Several formats" is decided from the decorator's ``extensions`` argument, and from its documented default of ``png``, ``pdf`` and ``svg`` when the argument is absent, so a test pinned to a single format is out of scope rather than failed. Not heuristic (§6.2): the extension is either present in the string or it is not, and the alternative the rule wants is stated. Finds no target when the decorator names no baselines at all -- that omission is C181's (§7.5).


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/tests.py:675`](../compliance/rules/matplotlib/tests.py#L675) · source: https://matplotlib.org/devdocs/devel/testing.html

### MATPLOTLIB-C184 — `ANewImageComparisonTestPinsTheMpl20Style`

> **Corpus:** Set ``style='mpl20'`` on a new image-comparison test.

- **Pre-condition —** each ``@image_comparison`` test the agent added.
- **Pass condition —** its decorator sets ``style='mpl20'``.

Not heuristic (§6.2): the value is a string the sentence names, so the check is an equality against a stated criterion. Scoped to tests the agent *added* because the sentence says "a new image-comparison test"; an existing test edited in place keeps whatever style its baselines were generated under, and failing it would grade the agent on someone else's choice (§4.3).


ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/tests.py:719`](../compliance/rules/matplotlib/tests.py#L719) · source: https://matplotlib.org/devdocs/devel/testing.html

### MATPLOTLIB-C187 — `ACheckFiguresEqualTestTakesTwoFigureParameters`

> **Corpus:** Give a check_figures_equal test exactly two Figure parameters, one drawn by the tested method and one by the baseline method.

- **Pre-condition —** each test the agent wrote or edited that carries ``@check_figures_equal``.
- **Pass condition —** it takes exactly the two figure parameters the decorator injects, ``fig_test`` and ``fig_ref``.

Heuristic on the **pass condition** (§6.2): the two parameters are checked by the names the decorator supplies, but *which* of them is drawn by the tested method and which by the baseline method is a fact about the body that no signature records, so the second half of the sentence is approximated by the pair being present and distinct. Other parameters -- fixtures, ``pytest.mark.parametrize`` arguments -- are permitted, since the sentence constrains the Figure parameters only.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/tests.py:755`](../compliance/rules/matplotlib/tests.py#L755) · source: https://matplotlib.org/devdocs/devel/testing.html

### MATPLOTLIB-C188 — `AnImageComparisonToleranceIsSetWithTheTolArgument`

> **Corpus:** Set an image-comparison tolerance with the ``tol`` argument rather than by any other means.

- **Pre-condition —** each ``@image_comparison`` test the agent wrote or edited in which a comparison tolerance is set at all, by any means.
- **Pass condition —** it is set with the decorator's ``tol`` argument and nowhere else.

§7.1's shape for a "do it this way rather than any other" sentence: a test that needs no tolerance finds no target, one that sets it in the decorator passes, and one that reaches for ``compare_images`` in its body to pass a tolerance is a violation. Heuristic on the **pre-condition** (§6.3): "setting a tolerance" is recognised from two forms -- the decorator's ``tol`` keyword and a tolerance argument to a ``compare_images`` call -- so a tolerance smuggled in through a fixture or an rcParam is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/tests.py:797`](../compliance/rules/matplotlib/tests.py#L797) · source: https://matplotlib.org/devdocs/devel/testing.html

### MATPLOTLIB-C271 — `NewAndChangedCodeIsTested`

> **Corpus:** Test new and changed code.

- **Pre-condition —** a contribution that changes library code outside the tests.
- **Pass condition —** it also adds or edits a test function.

Fires on the *change*, not on the test (§7.1), so a contribution that ships no test is a recorded violation rather than an absent row -- the whole point of the sentence. Heuristic on the **pre-condition** (§6.3): "new and changed code" is approximated by library Python appearing in the patch, a superset that also catches a comment fix nobody would ask for a test about.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/matplotlib/tests.py:244`](../compliance/rules/matplotlib/tests.py#L244) · source: https://github.com/matplotlib/matplotlib/blob/main/.github/PULL_REQUEST_TEMPLATE.md


## matplotlib — Specialized changes

### MATPLOTLIB-C192 — `ANewRcParamIsRegisteredWithAValidator`

> **Corpus:** Register a new rcParam with a validator and a _Param entry in rcsetup.py.

- **Pre-condition —** each rcParam key the contribution introduces, wherever it first appears.
- **Pass condition —** :file:`rcsetup.py` gains a validator entry for it.

§7.1: the antecedent is *introducing a key*, read from all three places one can appear, so a key added only to :file:`matplotlibrc` is selected here and recorded as a violation rather than vanishing. C193 and C194 ask the same question of the other two files, and no rule reads another's artefact (§7.5). Heuristic on the **pre-condition** (§6.3): a new key is recognised from a dotted lower-case string on an added line of one of the three files, so a key introduced some other way is not seen.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:239`](../compliance/rules/matplotlib/specialized.py#L239) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C193 — `ANewRcParamGetsACommentedMatplotlibrcEntry`

> **Corpus:** Add a commented-out entry for a new rcParam to matplotlibrc.

- **Pre-condition —** each rcParam key the contribution introduces.
- **Pass condition —** :file:`matplotlibrc` gains a commented-out entry for it.

Heuristic on the **pre-condition** for the reason C192 gives; the pass condition is exact -- a ``#key: value`` line is either on an added line of the template or it is not.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:274`](../compliance/rules/matplotlib/specialized.py#L274) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C194 — `ANewRcParamKeyReachesTheRcKeyTypeLiteral`

> **Corpus:** Add a new rcParam key to the RcKeyType Literal in typing.py.

- **Pre-condition —** each rcParam key the contribution introduces.
- **Pass condition —** it appears in :file:`lib/matplotlib/typing.py`, where the ``RcKeyType`` literal lists them.

Heuristic on the **pre-condition** for the reason C192 gives, and on the **pass condition** (§6.2), which accepts the key appearing anywhere in the stub's added lines rather than parsing the ``Literal`` itself -- the literal is a very long expression and a key added to it is what a diff shows.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:301`](../compliance/rules/matplotlib/specialized.py#L301) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C195 — `TestPyplotUpToDateIsRunAfterASignatureChange`

> **Corpus:** Run test_pyplot_up_to_date after changing the signature of a pyplot-wrapped method.

- **Pre-condition —** the agent changed the signature of a public method in one of the modules ``tools/boilerplate.py`` wraps into pyplot.
- **Pass condition —** a ``test_pyplot_up_to_date`` invocation appears in the command log.

§7.2's shape exactly: the pre-condition fires on the *edit*, never on the test run, because firing on the invocation would find only agents that already complied. Heuristic on the **pre-condition** (§6.3): *changing a signature* is approximated by the ``def`` line of a public method falling inside the agent's edit, so a default changed on a continuation line is not seen.


`heuristic` · ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/matplotlib/specialized.py:346`](../compliance/rules/matplotlib/specialized.py#L346) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C196 — `ThePyplotWrappersAreRegeneratedAndCommitted`

> **Corpus:** Regenerate the pyplot wrappers with tools/boilerplate.py and commit them.

- **Pre-condition —** the agent changed the signature of a public method that pyplot wraps.
- **Pass condition —** the regenerated :file:`lib/matplotlib/pyplot.py` is in the contribution.

Asks a different question from C195, which is whether the guard test was run; this one is whether the generated file was committed, and the two never grade the same artefact (§7.5). Heuristic on the **pre-condition** for the reason C195 gives, and on the **pass condition** (§6.2), which accepts any edit to :file:`pyplot.py` rather than checking that it is byte-for-byte what ``tools/boilerplate.py`` would emit -- that would need the generator to be run.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/matplotlib/specialized.py:385`](../compliance/rules/matplotlib/specialized.py#L385) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C197 — `ExistingColormapsAndStylesAreNotModified`

> **Corpus:** Do not modify an existing colormap, color sequence or style.

- **Pre-condition —** each file the agent edited that defines colormaps, colour sequences or styles.
- **Pass condition —** it only gains entries -- nothing already there was changed or removed.

§7.1: a prohibition, so the pre-condition selects *touching the palette files at all* and the pass condition asks whether an existing entry was disturbed. Selecting the modifications themselves could never record a compliant addition. Heuristic on the **pass condition** (§6.2): "modifying an existing colormap" is approximated by the edit having a minus side, so re-indenting a definition reads as a modification while a new entry inserted with no deletions reads as an addition.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/matplotlib/specialized.py:439`](../compliance/rules/matplotlib/specialized.py#L439) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C198 — `ANewColormapOrStyleCarriesABsdCompatibleLicence`

> **Corpus:** Give any new colormap, color sequence or style a BSD compatible license.

- **Pre-condition —** each new colormap, colour sequence or style the contribution adds.
- **Pass condition —** the contribution states a BSD-compatible licence for it, and no copyleft one.

Heuristic on **both** layers (§6.2, §6.3). *A new colormap* is approximated by a new style file or by added lines in the colormap tables; and the licence is read off text -- a recognised permissive name anywhere in the file, the licence directory, or the project's own licence tree -- rather than from any authoritative record.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:475`](../compliance/rules/matplotlib/specialized.py#L475) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C202 — `DeprecatedApiStaysFunctional`

> **Corpus:** Keep the deprecated API fully functional throughout the deprecation period.

- **Pre-condition —** each deprecation the agent introduced.
- **Pass condition —** the deprecated callable still does what it did.

Graded **one-sidedly** (§9): a deprecated body that has been replaced by a bare ``raise`` provably breaks the contract and is decidable from the patch, and everything else needs the API exercised, which is what ``deprecated_api_run`` names. The rule withholds rather than reading an unchanged body as proof of unchanged behaviour, so its three cases are violated, withheld and no target. Heuristic on the **pre-condition** (§6.3): *introducing a deprecation* is approximated by one of the six ``_api`` helpers appearing on a line the agent wrote.


`heuristic` · ownership `created` · reads `files, deprecated_api_run` · tier `differential`

[`compliance/rules/matplotlib/specialized.py:520`](../compliance/rules/matplotlib/specialized.py#L520) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C203 — `ADeprecationNamesItsReplacement`

> **Corpus:** Ship the replacement for a deprecated API before the deprecation period ends.

- **Pre-condition —** each deprecation the agent introduced.
- **Pass condition —** the helper names an alternative for callers to move to.

Heuristic on the **pass condition** (§6.2): "ship the replacement" is approximated by the deprecation *naming* one, since whether the named alternative exists is a fact about the whole checkout rather than about the patch. A deprecation whose replacement ships in the same change but goes unnamed reads as a violation.


`heuristic` · ownership `created` · reads `files` · tier `differential`

[`compliance/rules/matplotlib/specialized.py:564`](../compliance/rules/matplotlib/specialized.py#L564) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C206 — `DeprecatedApiRaisesMatplotlibDeprecationWarning`

> **Corpus:** Raise a MatplotlibDeprecationWarning when deprecated API is used.

- **Pre-condition —** each deprecation the agent introduced, by an ``_api`` helper or by hand.
- **Pass condition —** it goes through an ``_api`` helper, which is what raises ``MatplotlibDeprecationWarning``.

§7.1: the antecedent is *deprecating something*, whichever way, so a hand-rolled ``warnings.warn(..., DeprecationWarning)`` is a recorded violation and a helper call is a recorded pass; selecting only the hand-rolled ones could never record compliance. Heuristic on the **pass condition** (§6.2): the warning class is inferred from the helper rather than observed being raised, so a hand-rolled ``warnings.warn`` that names ``MatplotlibDeprecationWarning`` itself is accepted as an alternative form.


`heuristic` · ownership `created` · reads `files` · tier `differential`

[`compliance/rules/matplotlib/specialized.py:598`](../compliance/rules/matplotlib/specialized.py#L598) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C207 — `TheDeprecationHelperMatchesTheKindOfApi`

> **Corpus:** Use the matching _api deprecation helper for the kind of API being deprecated.

- **Pre-condition —** each ``_api`` deprecation helper call the agent wrote.
- **Pass condition —** it is the helper for the kind of API it is applied to -- a parameter helper naming a parameter the function actually has, and a whole-object helper applied to a definition.

Heuristic on the **pass condition** (§6.2): "the matching helper" is checked by the one property each helper's own contract fixes -- that ``rename_parameter``, ``delete_parameter`` and ``make_keyword_only`` name a parameter in the signature, and that ``deprecated`` decorates a definition rather than an assignment. A privatised attribute deprecated with ``deprecated`` instead of ``deprecate_privatize_attribute`` is not distinguished.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:648`](../compliance/rules/matplotlib/specialized.py#L648) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C208 — `TheDeprecationSinceIsTheNextPointRelease`

> **Corpus:** Set the deprecation helper's *since* parameter to the next point release.

- **Pre-condition —** each ``_api`` deprecation helper call the agent wrote.
- **Pass condition —** its ``since`` names the next point release.

Graded **one-sidedly** (§9): a helper called with no ``since`` at all provably cannot name the next release, and that is decidable from the patch. Comparing a version that *is* given against the next point release needs the project's version at the base commit, which no run records; the rule declares ``repo_version`` and withholds, so the exemption sunsets itself the day that evidence is collected (§5). Not heuristic: neither branch approximates anything -- one is the absence of a named argument, the other declines to grade.


ownership `created` · reads `files, repo_version` · tier `static`

[`compliance/rules/matplotlib/specialized.py:703`](../compliance/rules/matplotlib/specialized.py#L703) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C209 — `TheStubIsUpdatedAfterADeprecation`

> **Corpus:** Update the .pyi stub so it matches the runtime behaviour after a deprecation.

- **Pre-condition —** each whole-object deprecation the agent introduced -- ``deprecated``, ``warn_deprecated`` or ``deprecate_privatize_attribute``.
- **Pass condition —** the module's ``.pyi`` stub is edited too.

The three *parameter* helpers are deliberately excluded: ``rename_parameter`` and ``make_keyword_only`` are C210's, ``delete_parameter`` is C211's, and ``code_quality.C242`` excludes every deprecating file so that one deprecation cannot depress three rates (§7.5). Heuristic on the **pass condition** (§6.2): any edit to the sibling stub counts, since checking that the stub now *matches* runtime behaviour would need the type checker's verdict.


`heuristic` · ownership `created` · reads `files` · tier `differential`

[`compliance/rules/matplotlib/specialized.py:755`](../compliance/rules/matplotlib/specialized.py#L755) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C210 — `RenameAndKeywordOnlyDeprecationsUpdateTheStubSignature`

> **Corpus:** Update the stub signature for rename_parameter and make_keyword_only deprecations at introduction.

- **Pre-condition —** each ``rename_parameter`` or ``make_keyword_only`` deprecation the agent introduced.
- **Pass condition —** the module's ``.pyi`` stub gains a line naming the parameter the helper is about.

Narrowed to those two helpers so that C209 (whole-object deprecations) and C211 (``delete_parameter``) never grade the same call (§7.5). Heuristic on the **pass condition** (§6.2): "the stub signature is updated" is approximated by the parameter name appearing on an added stub line, rather than by re-deriving the signature the stub should now carry.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:791`](../compliance/rules/matplotlib/specialized.py#L791) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C211 — `DeleteParameterDeprecationsGiveTheStubADefault`

> **Corpus:** Give a delete_parameter-deprecated parameter a default value hint in the stub.

- **Pre-condition —** each ``delete_parameter`` deprecation the agent introduced.
- **Pass condition —** the module's ``.pyi`` stub gains a line giving that parameter a default value.

Narrowed to ``delete_parameter`` alone, so that C209 and C210 never reach the same call (§7.5). Heuristic on the **pass condition** (§6.2): "a default value hint" is recognised as the parameter name followed by ``=`` on an added stub line, which accepts ``= ...`` and any other default the author writes.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:830`](../compliance/rules/matplotlib/specialized.py#L830) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C213 — `ExpiryRemovesTheWarningWithTheApi`

> **Corpus:** Remove the deprecation warnings along with the API when a deprecation expires.

- **Pre-condition —** each library file where the agent removed a deprecation helper -- which is what expiring a deprecation looks like in a diff.
- **Pass condition —** the deprecated definition went with it.

Heuristic on **both** layers (§6.3, §6.2). Expiry is approximated by the helper call disappearing, which is also what moving it elsewhere looks like; and "the API went too" is approximated by a ``def``, ``class`` or attribute assignment on the same minus side, so an API removed in a separate file of the same change reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/matplotlib/specialized.py:868`](../compliance/rules/matplotlib/specialized.py#L868) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C214 — `ExpiryRemovesTheItemFromTheStub`

> **Corpus:** Remove deprecated and privatised items from the stub on expiry.

- **Pre-condition —** each library file where the agent removed a deprecation helper.
- **Pass condition —** the module's ``.pyi`` stub loses lines too.

The expiry counterpart of C209's introduction rule, and kept apart from C213 (§7.5): that rule asks whether the *implementation* went, this one asks about the *stub*, and neither reads the other's file. Heuristic on the **pass condition** (§6.2): any removal from the sibling stub counts, since matching the removed names against the removed stub entries would need the signature the stub carried before the change.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:904`](../compliance/rules/matplotlib/specialized.py#L904) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C216 — `APendingDeprecationCarriesNoRemovalVersion`

> **Corpus:** Mark a pending deprecation with pending=True and no removal version.

- **Pre-condition —** each deprecation the agent introduced with ``pending=True``.
- **Pass condition —** it names no removal version.

Heuristic on the **pre-condition** (§6.3), and the doubt is worth naming: nothing else in the patch distinguishes a deprecation that *ought* to be pending from one that ought not, so the antecedent is *having marked it pending*. What is graded is the second half of the sentence, which is exact -- a ``removal`` argument is present or it is not.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:940`](../compliance/rules/matplotlib/specialized.py#L940) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C217 — `ConvertingAPendingDeprecationSetsTheVersions`

> **Corpus:** Set pending=False, since to the next meso release and removal at least two meso releases later when converting a pending deprecation.

- **Pre-condition —** each library file where the agent removed a ``pending=True`` from a deprecation while keeping the helper -- which is what converting one looks like.
- **Pass condition —** the converted call is no longer pending, names a ``since``, and sets ``removal`` at least two meso releases later.

Heuristic on **both** layers (§6.3, §6.6). Conversion is recognised from ``pending=True`` disappearing from the file's minus side, so a conversion split across two files is not seen. And of the sentence's three clauses only two are graded: the gap between ``since`` and ``removal`` is arithmetic on the patch, but *"since is the next meso release"* would need the project's version at the base commit, which no run records -- so a converted deprecation whose ``since`` is a stale version is accepted here. The rate is an upper bound, and the doubt is named rather than hidden.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:978`](../compliance/rules/matplotlib/specialized.py#L978) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C244 — `NewFilesAreListedInTheirMesonBuild`

> **Corpus:** List new files and directories in the meson.build of their directory.

- **Pre-condition —** each source file the agent added under a tree meson builds.
- **Pass condition —** the :file:`meson.build` in its own directory is edited and names it.

Heuristic on the **pre-condition** (§6.3): *a directory meson builds* is approximated by the three trees that carry :file:`meson.build` files, since the build definitions outside the patch are not visible. A new file in a directory whose build list is generated by a glob reads as a violation.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:1044`](../compliance/rules/matplotlib/specialized.py#L1044) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C249 — `VendoredCodeIsModifiedOnlyAsALastResort`

> **Corpus:** Modify vendored code under extern/ only where the change cannot be made elsewhere.

- **Pre-condition —** each substantive edit the agent made to a file under :file:`extern/`.
- **Pass condition —** the same contribution also changes the project's own source, so the vendored edit is the part that could not be made there.

A purely cosmetic edit to vendored code is excluded and left to C250, so a style fix under :file:`extern/` is one violation rather than two (§7.5). Heuristic on the **pass condition** (§6.2): *"the change cannot be made elsewhere"* is not observable, and it is approximated by whether the contribution attempted anything elsewhere at all. A change that genuinely belongs only in vendored code, and touches nothing else, reads as a violation; the direction of that error is declared rather than removed.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/matplotlib/specialized.py:1087`](../compliance/rules/matplotlib/specialized.py#L1087) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C250 — `VendoredCodeGetsNoStyleFixes`

> **Corpus:** Do not make style fixes to vendored code under extern/.

- **Pre-condition —** each file under :file:`extern/` the agent edited.
- **Pass condition —** the edit changes something other than formatting.

§7.1: a prohibition, so the pre-condition is *editing vendored code at all* and the graded question is whether the edit was a style fix. Selecting style fixes would only ever find violations. Heuristic on the **pass condition** (§6.2): "a style fix" is approximated by every removed line reappearing on the plus side once whitespace and comment markers are squeezed out, so a reflow that also renames a variable is not seen as a style fix.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:1128`](../compliance/rules/matplotlib/specialized.py#L1128) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C251 — `ANolintCommentIsNarrowAndGivesTheReason`

> **Corpus:** Suppress a clang-tidy false positive with a narrowly scoped NOLINT comment that gives the reason.

- **Pre-condition —** each ``NOLINT`` comment the agent added to C or C++ code.
- **Pass condition —** it names the check it suppresses (or applies to a single line) and carries a reason.

Heuristic on the **pass condition** (§6.2): "gives the reason" is matched by prose after the directive, so a reason written on the line above is not seen, and a trailing fragment that explains nothing is accepted.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:1160`](../compliance/rules/matplotlib/specialized.py#L1160) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C262 — `CodeBroughtInCarriesACompatibleLicence`

> **Corpus:** Check that any code brought in from another project carries a PSF, BSD, MIT or compatible license.

- **Pre-condition —** each file the agent added under :file:`extern/` -- how code from another project arrives in this tree.
- **Pass condition —** it names a PSF, BSD, MIT or otherwise compatible licence.

Split from C263 by tree (§7.5): imported code is vendored under :file:`extern/`, and a licence problem in the main code base is that rule's, so no file is graded twice. Heuristic on **both** layers (§6.2, §6.3). *Code brought in from another project* is approximated by the vendoring directory, so a snippet pasted into a library module is not seen; and the licence is read off text rather than from any authoritative record.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:1208`](../compliance/rules/matplotlib/specialized.py#L1208) · source: https://matplotlib.org/devdocs/devel/license.html

### MATPLOTLIB-C263 — `NoCopyleftCodeInTheMainCodeBase`

> **Corpus:** Do not add GPL or LGPL code to the main code base.

- **Pre-condition —** each source file the agent added to the main code base -- :file:`lib/` or :file:`src/`, excluding the vendoring tree.
- **Pass condition —** it declares no GPL or LGPL licence.

§7.1: a prohibition, so the pre-condition selects *adding a file*, the permitted act, and the pass condition asks whether it was copyleft. Files under :file:`extern/` are C262's (§7.5). Heuristic on the **pre-condition** (§6.3): the sentence is about code brought in from elsewhere, and the antecedent fires on every added source file, which is the superset that can be observed. The pass condition is exact -- the licence family is named in the rule and matched by name.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:1252`](../compliance/rules/matplotlib/specialized.py#L1252) · source: https://matplotlib.org/devdocs/devel/license.html

### MATPLOTLIB-C264 — `AVendoredDependencyBringsItsLicence`

> **Corpus:** Add a copy of a vendored dependency's license to the license directory where its license requires distribution.

- **Pre-condition —** the contribution vendors a dependency -- it adds files under :file:`extern/`.
- **Pass condition —** it also adds a licence copy under the licence directory.

Heuristic on the **pass condition** (§6.2), and the doubt is named: the sentence's qualifier -- *"where its license requires distribution"* -- is not checked, because deciding it means reading the dependency's own licence terms. Almost every permissive licence does require it, so the rule asks for the copy unconditionally, and a dependency under a licence that does not would read as a violation.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:1296`](../compliance/rules/matplotlib/specialized.py#L1296) · source: https://matplotlib.org/devdocs/devel/license.html

### MATPLOTLIB-C265 — `ToolkitCodeFromElsewhereStatesItsLicence`

> **Corpus:** State the license clearly when using non-BSD-compatible code in a toolkit.

- **Pre-condition —** each file the agent added under :file:`lib/mpl_toolkits/` that carries a third-party attribution -- a foreign copyright line, or an "adapted from" note.
- **Pass condition —** it names the licence that code is under.

Heuristic on **both** layers (§6.2, §6.3). *Non-BSD-compatible code* is not observable before the licence is read, so the antecedent is the weaker and observable *code from somewhere else*; and "states the license clearly" is matched by a recognised licence name in the file.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:1334`](../compliance/rules/matplotlib/specialized.py#L1334) · source: https://matplotlib.org/devdocs/devel/license.html

### MATPLOTLIB-C284 — `RequiresPythonMatchesTheMinimumSupportedVersion`

> **Corpus:** Set requires-python in pyproject.toml to the minimum supported Python version.

- **Pre-condition —** the agent set ``requires-python`` in a :file:`pyproject.toml` that also declares which Python versions the project supports.
- **Pass condition —** the floor it sets is the lowest of those.

Asks whether the *value* is right; whether the other five files moved with it is C286's, and neither rule reads the other's artefact (§7.5). Heuristic on the **pre-condition** (§6.3): "the minimum supported Python version" is not stated anywhere the patch can see, so it is approximated by the lowest ``Programming Language :: Python`` classifier in the same file, or by :file:`environment.yml`'s pin. A file that declares neither finds no target rather than being graded against a guess.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:1376`](../compliance/rules/matplotlib/specialized.py#L1376) · source: https://matplotlib.org/devdocs/devel/min_dep_policy.html

### MATPLOTLIB-C286 — `RaisingTheMinimumPythonUpdatesAllSixFiles`

> **Corpus:** Update all six named files together when raising the minimum Python version.

- **Pre-condition —** a contribution that raises the minimum supported Python version.
- **Pass condition —** all six files the policy names are in it.

Heuristic on the **pre-condition** (§6.3): *raising the minimum* is approximated by the version fields the policy page names appearing on added lines of the files that carry them, so a bump written some other way is not seen. The pass condition is exact -- the six names are published, and the CI entry is a named group of paths. Asks only whether the six moved together. Whether ``requires-python`` was set to the *right* value is C284's (§7.5).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:1436`](../compliance/rules/matplotlib/specialized.py#L1436) · source: https://matplotlib.org/devdocs/devel/min_dep_policy.html

### MATPLOTLIB-C287 — `RaisingTheMinimumNumpyUpdatesAllSixFiles`

> **Corpus:** Update all six named files together when raising the minimum NumPy version.

- **Pre-condition —** a contribution that raises the minimum supported NumPy version.
- **Pass condition —** all six files the policy names are in it.

A different list from C286's: :file:`requirements/testing/minver.txt` and :file:`lib/matplotlib/__init__.py` appear here and nowhere else, which is why the two rules cannot share one predicate. Heuristic on the **pre-condition** for the reason C286 gives.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/specialized.py:1474`](../compliance/rules/matplotlib/specialized.py#L1474) · source: https://matplotlib.org/devdocs/devel/min_dep_policy.html


## matplotlib — Documentation and docstrings

### MATPLOTLIB-C001 — `GeneratedDocumentationPagesAreNotEdited`

> **Corpus:** Do not edit .rst files under doc/plot_types, doc/gallery, doc/tutorials, doc/users/explain or doc/api, except doc/api/api_changes/.

- **Pre-condition —** each reST page under :file:`doc/` the agent edited.
- **Pass condition —** it is not in one of the five generated trees, or it is under :file:`doc/api/api_changes/`, the exception the sentence names.

§7.1: a prohibition, so the pre-condition selects *editing a documentation page*, the permitted act, and the pass condition asks which tree it was in. Not heuristic (§6.2): the five prefixes and the exception are paths the rule states, and the check compares against them.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:170`](../compliance/rules/matplotlib/documentation.py#L170) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C002 — `SectionTitlesAreSentenceCase`

> **Corpus:** Write section titles in sentence case.

- **Pre-condition —** each section title the agent wrote on a documentation page.
- **Pass condition —** only its first word is capitalised.

Heuristic on the **pass condition** (§6.2): "sentence case" allows proper nouns and code names, which cannot be told from title case mechanically, so a word is excused only when it is a known project name, an acronym, or carries markup. A title naming an unlisted proper noun reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:203`](../compliance/rules/matplotlib/documentation.py#L203) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C003 — `HeadingsUseTheListedAdornmentForTheirLevel`

> **Corpus:** Use the listed reST markup characters for each heading level: * for chapters, = for sections, - for subsections, ^ for subsubsections, and " for paragraphs.

- **Pre-condition —** each section heading the agent wrote on a documentation page, other than one adorned with ``#``.
- **Pass condition —** its adornment is the character the style guide gives that depth -- ``*`` for chapters, ``=`` for sections, ``-`` for subsections, ``^`` for subsubsections, ``"`` for paragraphs.

``#`` is excluded and left to C004, which is the rule about the main title (§7.5). Heuristic on the **pass condition** (§6.2): a heading's depth is not written down, so it is inferred from the order in which adornment characters first appear in the page. A page whose first heading is a subsection -- legitimate in an included fragment -- therefore has every heading measured one level too shallow.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:254`](../compliance/rules/matplotlib/documentation.py#L254) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C004 — `TheHashOverlineIsReservedForAnIndexMainTitle`

> **Corpus:** Reserve the # overline markup for the main title in index.rst and start every other page at chapter level or lower.

- **Pre-condition —** each documentation page the agent edited that carries at least one section heading.
- **Pass condition —** it uses ``#`` only as the main title of an :file:`index.rst`, and otherwise starts at chapter level or lower.

§7.1: the antecedent is *having headings*, not *having a ``#`` heading* -- selecting the latter could record a violation and never a compliant page. Not heuristic (§6.2): the adornment character and the file name are both exact, and the rule names both.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:306`](../compliance/rules/matplotlib/documentation.py#L306) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C006 — `FunctionArgumentsAreEmphasised`

> **Corpus:** Refer to function arguments and keywords with the *emphasis* role.

- **Pre-condition —** each mention of one of a function's own parameters in its docstring prose that is either bare or already emphasised.
- **Pass condition —** it carries the ``*emphasis*`` role.

Mentions wrapped in single or double backticks are excluded: those are C007's and C008's, and the three rules between them cover every markup form exactly once (§7.5). Heuristic on the **pre-condition** (§6.3): *referring to an argument* is approximated by the parameter's name appearing as a word in the prose, so ``color`` used as an ordinary English word inside the same docstring is selected too.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:368`](../compliance/rules/matplotlib/documentation.py#L368) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C007 — `TheDefaultRoleDoesNotMarkUpAnArgument`

> **Corpus:** Do not use the default role to mark up a function argument.

- **Pre-condition —** each single-backtick span the agent wrote in a function docstring.
- **Pass condition —** what it marks up is not one of that function's parameters.

§7.1: a prohibition, so the antecedent is *using the default role* and the graded question is what was marked with it; a default role around a class name is a recorded pass. C006 and C008 take the other two markup forms (§7.5). Heuristic on the **pass condition** (§6.2): a name is judged to be an argument by matching the signature, so a docstring that marks up a *different* thing sharing the name reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:438`](../compliance/rules/matplotlib/documentation.py#L438) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C008 — `TheLiteralRoleDoesNotMarkUpAnArgument`

> **Corpus:** Do not use the literal role to mark up a function argument.

- **Pre-condition —** each double-backtick literal the agent wrote in a function docstring.
- **Pass condition —** what it marks up is not one of that function's parameters.

The same shape as C007, on the other markup form; a literal around a value or a type is a recorded pass. Heuristic for the same reason (§6.2).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:472`](../compliance/rules/matplotlib/documentation.py#L472) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C009 — `InlineMathematicsUsesTheMathRole`

> **Corpus:** Mark up inline mathematics with the :math: role.

- **Pre-condition —** each line of prose the agent wrote that states an inline mathematical expression.
- **Pass condition —** it is marked with the ``:math:`` role.

Heuristic on the **pre-condition** (§6.3): *an inline mathematical expression* is recognised from LaTeX vocabulary and dollar delimiters, so mathematics written in plain words is not seen. Displayed mathematics is C010's and is excluded here (§7.5).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:502`](../compliance/rules/matplotlib/documentation.py#L502) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C010 — `DisplayedMathematicsUsesTheMathDirective`

> **Corpus:** Mark up displayed mathematics with the .. math:: directive.

- **Pre-condition —** each displayed mathematical expression the agent wrote.
- **Pass condition —** it is introduced by a ``.. math::`` directive.

Split from C009 by delimiter (§7.5): ``$$`` and the LaTeX display environments are displayed mathematics and belong here; single ``$`` and inline LaTeX belong there. Heuristic on the **pre-condition** (§6.3), which recognises displayed mathematics from those delimiters alone.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:538`](../compliance/rules/matplotlib/documentation.py#L538) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C011 — `LinksToOtherPagesUseTheDocRole`

> **Corpus:** Use the :doc: role to link to another documentation page.

- **Pre-condition —** each link to another documentation page the agent wrote.
- **Pass condition —** it uses the ``:doc:`` role.

§7.1: the antecedent is *linking to a page*, whichever way it is written, so a ``:doc:`` link is a recorded pass and a raw path is a violation. Heuristic on the **pre-condition** (§6.3): a page link is recognised as a ``:doc:`` role or as a path ending in ``.rst``/``.html``, so a link written as a bare label reference is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:577`](../compliance/rules/matplotlib/documentation.py#L577) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C013 — `ReferenceLabelsAreHyphenSeparatedWords`

> **Corpus:** Name reference labels with hyphen-separated descriptive words.

- **Pre-condition —** each reference label the agent wrote.
- **Pass condition —** it is lower-case words joined by hyphens.

Heuristic on the **pass condition** (§6.2), and the doubt is named: the sentence asks for *descriptive* words too, which no check can decide, so only the separator and the casing are graded and a label of meaningless hyphenated words passes.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:637`](../compliance/rules/matplotlib/documentation.py#L637) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C014 — `ReferenceLabelsDoNotEncodeTheHierarchy`

> **Corpus:** Do not encode the documentation hierarchy in a reference label.

- **Pre-condition —** each reference label the agent wrote whose form C013 already accepts.
- **Pass condition —** none of its words repeats a directory of the page it labels.

Narrowed to well-formed labels (§7.5) so that a label written with underscores is one violation -- C013's -- rather than two. Heuristic on the **pass condition** (§6.2): *encoding the hierarchy* is approximated by a word of the label matching a directory name on the page's own path, so a label that spells the hierarchy differently is not seen.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:676`](../compliance/rules/matplotlib/documentation.py#L676) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C015 — `AReferenceLabelSitsImmediatelyBeforeASection`

> **Corpus:** Place a reference label immediately before a section and link to it with the :ref: role.

- **Pre-condition —** each reference label the agent wrote.
- **Pass condition —** the next non-blank content is a section title, and any reference to the label in the change uses the ``:ref:`` role.

Heuristic on the **pass condition** (§6.2): "immediately before a section" is read as a heading within the next few lines, so a label followed by a directive and then a heading is failed on a reading the sentence does not spell out.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:717`](../compliance/rules/matplotlib/documentation.py#L717) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C016 — `MatplotlibCodeElementsAreLinkedWithBackTicks`

> **Corpus:** Link to Matplotlib methods, classes and modules with back ticks.

- **Pre-condition —** each dotted matplotlib name the agent wrote in prose.
- **Pass condition —** it is inside back ticks -- a role, or the default role.

Heuristic on the **pre-condition** (§6.3): *a method, class or module* is approximated by a dotted name whose root is ``matplotlib`` or ``mpl_toolkits``, so an unqualified class name mentioned in prose is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:762`](../compliance/rules/matplotlib/documentation.py#L762) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C018 — `AnAbbreviatedReferenceIsQualifiedEnoughToDisambiguate`

> **Corpus:** Qualify an abbreviated reference far enough to disambiguate it when several code elements share the name.

- **Pre-condition —** each reST role reference the agent wrote whose final name is one the project defines in more than one place.
- **Pass condition —** the reference carries enough of the dotted path to say which.

Heuristic on the **pre-condition** (§6.3): "several code elements share the name" is approximated by a published list of the dual-API names -- the plotting functions that exist on both ``Axes`` and ``pyplot`` -- so a collision outside that list is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:805`](../compliance/rules/matplotlib/documentation.py#L805) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C019 — `ThePlotDirectivePointsAtAScript`

> **Corpus:** Point a .. plot:: directive at the Python script that generates the figure, not at a generated image.

- **Pre-condition —** each ``.. plot::`` directive with a file argument the agent wrote.
- **Pass condition —** the file is a Python script.

Not heuristic (§6.2): the argument is a path and the check is its suffix, which the sentence names. A ``.. plot::`` directive with inline code and no argument finds no target -- there is no file to be wrong about.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:842`](../compliance/rules/matplotlib/documentation.py#L842) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C020 — `AMovedPageLeavesARedirect`

> **Corpus:** When moving or consolidating a page, add a redirect-from directive to the new page instead of leaving the old URL dead.

- **Pre-condition —** the contribution deletes or renames a documentation page.
- **Pass condition —** some page in the change carries a ``redirect-from`` directive.

Heuristic on **both** layers (§6.2, §6.3). *Moving or consolidating* is approximated by a deleted or renamed reST page, so a page emptied in place is not seen; and the pass condition accepts any redirect in the change rather than checking that it names the old URL, which would need the doc-root mapping.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/matplotlib/documentation.py:878`](../compliance/rules/matplotlib/documentation.py#L878) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C021 — `ARedirectFromPathIsAbsolute`

> **Corpus:** Write a redirect-from path as a full path from the doc root, never as a relative link.

- **Pre-condition —** each ``redirect-from`` directive the agent wrote.
- **Pass condition —** its path starts at the documentation root.

Not heuristic (§6.2): a leading ``/`` is exactly what "a full path from the doc root" means in Sphinx, and the rule names the alternative it forbids. Asks only about the form -- whether a redirect exists at all is C020's (§7.5).


ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:917`](../compliance/rules/matplotlib/documentation.py#L917) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C023 — `DocstringsConformToNumpydoc`

> **Corpus:** Write docstrings that conform to the numpydoc docstring guide.

- **Pre-condition —** each docstring the agent wrote or edited in the library that carries at least one section heading.
- **Pass condition —** every heading is a numpydoc section name, underlined with dashes at least as long as the name, and a summary precedes the first one.

**Narrowed on purpose (§7.5).** "Conform to the numpydoc guide" would otherwise cover everything the twenty rules around it legislate -- quote positions (C026, C027), type descriptions (C030--C037), defaults (C039, C041), examples (C159). This rule takes the *structural* requirements none of those covers, and the docstring names the others so a reader can see the division. Heuristic on the **pass condition** (§6.2): conformance is graded on that structural subset rather than by running numpydoc's own validator, so the rate is an upper bound.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1018`](../compliance/rules/matplotlib/documentation.py#L1018) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C025 — `NewApiReferenceGoesInTheModuleDocstring`

> **Corpus:** Put new API reference documentation in the module docstring, not in a doc/api page.

- **Pre-condition —** the contribution adds public API to modules that already exist.
- **Pass condition —** its reference documentation goes into docstrings, not into a new :file:`doc/api` page.

**Narrowed against C158 (§7.5)**, which requires exactly the opposite artefact for a *new module*: a contribution that adds a module finds no target here, so the two sentences never bind the same change in opposite directions. Heuristic on the **pre-condition** (§6.3): *new API* is approximated by a public definition whose header the agent wrote, so API added by assignment or by a factory is not seen.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1084`](../compliance/rules/matplotlib/documentation.py#L1084) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C026 — `SingleLineDocstringsKeepTheirQuotesOnTheLine`

> **Corpus:** Put the opening and closing quotes of a single-line docstring on the same line as its text.

- **Pre-condition —** each single-line docstring the agent wrote or edited.
- **Pass condition —** its opening and closing quotes are on the same line as its text.

Not heuristic (§6.2): the raw text carries the quotes, and "same line" is a position. Multi-line docstrings are C027's and find no target here -- the two rules partition docstrings by length (§7.5).


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1139`](../compliance/rules/matplotlib/documentation.py#L1139) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C027 — `MultiLineDocstringsPutTheirQuotesOnTheirOwnLines`

> **Corpus:** Put the opening and closing quotes of a multi-line docstring on their own lines.

- **Pre-condition —** each multi-line docstring the agent wrote or edited.
- **Pass condition —** nothing shares a line with its opening or closing quotes.

Not heuristic (§6.2): both are positions in the raw text. Single-line docstrings are C026's (§7.5).


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1173`](../compliance/rules/matplotlib/documentation.py#L1173) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C029 — `StringValuesUsePlainQuotes`

> **Corpus:** Give string values with plain quotes and no surrounding literal role.

- **Pre-condition —** each quoted string value the agent wrote in a numpydoc type description.
- **Pass condition —** it is written with plain quotes and no surrounding literal role.

Heuristic on the **pre-condition** (§6.3): *a string value* is approximated by a quoted token inside a ``name : type`` line, so a value named only in the prose description is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1207`](../compliance/rules/matplotlib/documentation.py#L1207) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C030 — `TypeDescriptionsAvoidAnnotationSyntax`

> **Corpus:** Do not use formal type-annotation syntax in a docstring type description.

- **Pre-condition —** each ``name : type`` line the agent wrote in a Parameters section.
- **Pass condition —** the type is prose, not formal typing syntax.

Not heuristic (§6.2): the forbidden forms are a closed list of typing constructs -- subscripted ``Optional``/``Union``/``List`` and friends, and the ``->`` arrow -- and the check is their presence.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1242`](../compliance/rules/matplotlib/documentation.py#L1242) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C031 — `AnyNumberIsDescribedAsFloat`

> **Corpus:** Describe a parameter that accepts any number as ``float``.

- **Pre-condition —** each Parameters entry the agent wrote whose type names a scalar numeric kind.
- **Pass condition —** it is described as ``float``.

Heuristic on the **pre-condition** (§6.3): *accepts any number* is approximated by the type naming one of the numeric spellings, so a parameter genuinely restricted to integers is selected too and reads as a violation. Sequences of numbers are C033's and are excluded here (§7.5).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1269`](../compliance/rules/matplotlib/documentation.py#L1269) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C032 — `A2dPositionIsDescribedWithParentheses`

> **Corpus:** Describe a 2D position as ``(float, float)``, parentheses included.

- **Pre-condition —** each Parameters entry the agent wrote whose type describes a two-dimensional position.
- **Pass condition —** it is written ``(float, float)``, parentheses included.

Heuristic on the **pre-condition** (§6.3): *a 2D position* is approximated by the phrases the guide's own examples use -- a 2-tuple, a pair, ``float, float``, ``(x, y)`` -- so a position described some other way is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1309`](../compliance/rules/matplotlib/documentation.py#L1309) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C033 — `ANumericSequenceParameterIsArrayLike`

> **Corpus:** Describe a homogeneous numeric sequence parameter as ``array-like``.

- **Pre-condition —** each Parameters entry the agent wrote whose type describes a sequence of numbers.
- **Pass condition —** it is described as ``array-like``.

Return values are C034's, and this rule reads the Parameters section only (§7.5). Heuristic on the **pre-condition** (§6.3): the sequence is recognised from the words ``array``, ``ndarray``, ``sequence``, ``list``, ``tuple`` or ``iterable`` together with a numeric element type.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1344`](../compliance/rules/matplotlib/documentation.py#L1344) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C034 — `AReturnedArrayIsDescribedAsArray`

> **Corpus:** Describe a return value that really is a numpy array as ``array``, not ``array-like``.

- **Pre-condition —** each Returns entry the agent wrote whose type mentions an array.
- **Pass condition —** it says ``array``, not ``array-like``.

Reads the Returns section only; the Parameters side is C033's, which asks for the opposite word for the opposite reason (§7.5). Heuristic on the **pre-condition** (§6.3): whether the value *really is* a numpy array is not observable from the docstring, so every array-mentioning return type is selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1385`](../compliance/rules/matplotlib/documentation.py#L1385) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C035 — `ANonFloatDtypeIsSpeltOut`

> **Corpus:** Spell out a non-float dtype as ``array-like of <dtype>``.

- **Pre-condition —** each Parameters entry the agent wrote describing a numeric sequence whose element type is not ``float``.
- **Pass condition —** it is written ``array-like of <dtype>``.

Heuristic on the **pre-condition** (§6.3): the element type is read from the phrase ``<sequence> of <dtype>``, so a dtype stated only in the description is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1424`](../compliance/rules/matplotlib/documentation.py#L1424) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C036 — `ANonNumericSequenceIsAListOfType`

> **Corpus:** Describe a non-numeric homogeneous sequence as ``list of <type>``.

- **Pre-condition —** each Parameters entry the agent wrote describing a sequence whose element type is not numeric.
- **Pass condition —** it is written ``list of <type>``.

Numeric sequences are C033's and C035's; this rule fires only where the element type is not one of the numeric spellings (§7.5). Heuristic on the **pre-condition** (§6.3): the element type is read from the phrase ``<sequence> of <type>``.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1464`](../compliance/rules/matplotlib/documentation.py#L1464) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C037 — `ParameterTypesAreFullReferencesWithATilde`

> **Corpus:** Write parameter types as full references with a leading tilde.

- **Pre-condition —** each reST role reference the agent wrote inside a ``name : type`` line.
- **Pass condition —** it is a full dotted path introduced by ``~``.

Reads type lines only; references in the surrounding prose are C038's, which asks for the abbreviated form instead (§7.5). Heuristic on the **pass condition** (§6.2): "full reference" is graded as a dotted path of at least two components, since whether the path resolves is a fact about the whole checkout.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1507`](../compliance/rules/matplotlib/documentation.py#L1507) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C038 — `InTextReferencesUseTheAbbreviatedDottedForm`

> **Corpus:** Write in-text references to code in the abbreviated dotted form.

- **Pre-condition —** each reST role reference the agent wrote in docstring prose, outside the ``name : type`` lines.
- **Pass condition —** it uses the abbreviated dotted form -- a leading ``.`` or ``~.``.

The counterpart of C037, split by location so no reference is graded twice (§7.5). Heuristic on the **pass condition** (§6.2): the abbreviation is recognised from the leading dot Sphinx uses for it, so an abbreviation written some other way reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1544`](../compliance/rules/matplotlib/documentation.py#L1544) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C039 — `ASimpleDefaultIsDocumentedInTheStatedForm`

> **Corpus:** Document a simple default with ``{name} : {type}, default: {val}``.

- **Pre-condition —** each documented parameter whose signature gives it a simple literal default other than ``None``.
- **Pass condition —** its type line ends ``, default: <value>``.

``None`` defaults are excluded and left to C041, which decides whether they should be documented at all -- so a sentinel is one question, not two (§7.5). Heuristic on the **pre-condition** (§6.3): "a simple default" is approximated by the signature default being a literal, so a default built by a call is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1590`](../compliance/rules/matplotlib/documentation.py#L1590) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C041 — `ASentinelNoneIsNotDocumentedAsADefault`

> **Corpus:** Do not document None as a default when it is only a not-specified sentinel.

- **Pre-condition —** each documented parameter whose signature default is ``None``.
- **Pass condition —** either the docstring does not present ``None`` as the default, or it says what ``None`` means.

§7.1: the antecedent is *having a ``None`` default to describe*, so a docstring that explains what ``None`` does is a recorded pass and one that merely writes ``default: None`` is a violation. C039 takes every other default (§7.5). Heuristic on the **pass condition** (§6.2): "only a not-specified sentinel" is approximated by the description never mentioning ``None`` again, so a description that explains the sentinel in other words reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1655`](../compliance/rules/matplotlib/documentation.py#L1655) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C042 — `ALongParameterTypeIsWrappedWithABackslash`

> **Corpus:** Wrap a long parameter list with a backslash continuation and no indent on the continuation line.

- **Pre-condition —** each ``name : type`` line the agent wrote that is too long for the project's 88-character limit, or that is already wrapped.
- **Pass condition —** it wraps with a trailing backslash and an unindented continuation.

Heuristic on the **pre-condition** (§6.3): "a long parameter list" is approximated by the line exceeding the project's own line limit, which is the only threshold the project states anywhere.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1702`](../compliance/rules/matplotlib/documentation.py#L1702) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C043 — `AnRcParamIsReferencedWithTheRcRole`

> **Corpus:** Reference an rcParam with the :rc: role.

- **Pre-condition —** each rcParam key the agent named in prose.
- **Pass condition —** it is written with the ``:rc:`` role.

Heuristic on the **pre-condition** (§6.3): an rcParam key is recognised as a dotted lower-case name whose first segment is one of the project's rcParam namespaces, or as a subscript of ``rcParams``, so a key outside those namespaces is not seen and a dotted module name inside them is wrongly selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1751`](../compliance/rules/matplotlib/documentation.py#L1751) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C045 — `APropertySetterDocumentsItsAcceptedValues`

> **Corpus:** Document a property setter's accepted values in its Parameters block, or in an ``.. ACCEPTS:`` block where that is not possible.

- **Pre-condition —** each ``set_*`` method the agent added that carries a docstring.
- **Pass condition —** the docstring has a Parameters block, or an ``.. ACCEPTS:`` block.

Heuristic on the **pass condition** (§6.2): the presence of either block stands in for the values actually being documented, so an empty Parameters section counts.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1792`](../compliance/rules/matplotlib/documentation.py#L1792) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C047 — `AnInheritedDocstringIsMarked`

> **Corpus:** Mark a deliberately inherited docstring with the comment ``# docstring inherited``.

- **Pre-condition —** each public method the agent added to a class without a docstring -- the shape of a deliberately inherited one.
- **Pass condition —** its body opens with the ``# docstring inherited`` comment.

Paired with C145 (§7.5), which accepts that marker as satisfying "give every public method a docstring"; without the pairing an inherited docstring would be a violation of one rule and the antecedent of the other at the same time. Heuristic on the **pre-condition** (§6.3): whether a method really overrides a documented base method is a fact about the class hierarchy, not about the patch, so every undocumented public method is selected.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1831`](../compliance/rules/matplotlib/documentation.py#L1831) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C049 — `AnExampleThatPlotsNothingIsNamedSgskip`

> **Corpus:** Put "sgskip" in the filename of an example that should not have a plot generated.

- **Pre-condition —** each gallery example the agent added that draws nothing.
- **Pass condition —** ``sgskip`` is in its file name.

Split from C137 by the same proxy (§7.5): an example that *does* draw is that rule's, and must end with ``show()``; one that does not is this rule's, and must say so in its name. No example is graded by both. Heuristic on the **pre-condition** (§6.3): "should not have a plot generated" is approximated by the file containing no plotting call, so an example that plots through a helper is selected and reads as a violation.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2492`](../compliance/rules/matplotlib/documentation.py#L2492) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C050 — `NarrativeBlocksUseTheCellSeparator`

> **Corpus:** Separate blocks of narrative text in an example or tutorial with the ``# %%`` separator.

- **Pre-condition —** each gallery example the agent wrote or edited that carries a block of narrative comment lines below its module docstring.
- **Pass condition —** every such block opens with the ``# %%`` separator.

Heuristic on the **pre-condition** (§6.3): *narrative text* is approximated by a run of two or more consecutive full-line comments, so a one-line note is not seen and a two-line explanation of the code below is wrongly selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2528`](../compliance/rules/matplotlib/documentation.py#L2528) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C051 — `APublicDatasetIsCited`

> **Corpus:** Cite the source of any public dataset used as sample data.

- **Pre-condition —** each gallery example the agent wrote that loads sample data or names a dataset.
- **Pass condition —** its prose names a source -- a URL, or an attribution phrase.

Asks only for the citation. *Whether* the data should have been inlined is C052's and *where* an un-inlinable file goes is C053's, so the three sentences split the subject three ways (§7.5). Heuristic on **both** layers (§6.2, §6.3): the dataset is recognised from a ``get_sample_data`` call or the word "dataset", and the citation from a URL or one of a handful of attribution phrases.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2577`](../compliance/rules/matplotlib/documentation.py#L2577) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C052 — `SampleDataIsWrittenOutInTheExample`

> **Corpus:** Write sample data out in the example code, falling back to cbook.get_sample_data only where that is not feasible.

- **Pre-condition —** each gallery example the agent wrote that supplies sample data.
- **Pass condition —** the data is written out in the example, or the file it loads is one the contribution adds under the sample-data directory -- the "not feasible" case the sentence allows for.

Heuristic on **both** layers (§6.2, §6.3): supplying data is recognised from a ``get_sample_data`` call or a literal array, and "not feasible to inline" is approximated by the file being shipped as sample data in the same change.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2616`](../compliance/rules/matplotlib/documentation.py#L2616) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C053 — `LargeSampleDataGoesInTheSampleDataDirectory`

> **Corpus:** Put sample data too large to inline into lib/matplotlib/mpl-data/sample_data/.

- **Pre-condition —** each data file the agent added alongside a gallery example.
- **Pass condition —** it is under :file:`lib/matplotlib/mpl-data/sample_data/`.

Not heuristic (§6.2): the destination is a path the rule names, and the check is a prefix. Whether the data should have been inlined instead is C052's (§7.5).


ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2660`](../compliance/rules/matplotlib/documentation.py#L2660) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C054 — `AnExampleListsItsShowcasedFunctions`

> **Corpus:** List the showcased functions in a References admonition at the bottom of the example.

- **Pre-condition —** each gallery example the agent added.
- **Pass condition —** it carries a References admonition naming the functions it showcases.

Asks only that the block exists. What it must contain for a dual-API function is C056's, which fires only where the block is already there (§7.5). Heuristic on the **pass condition** (§6.2): the admonition is recognised by its directive line, and "the showcased functions" by the block containing at least one reference, rather than by comparing against the calls the example makes.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2702`](../compliance/rules/matplotlib/documentation.py#L2702) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C056 — `ADualApiFunctionIsListedBothWaysWithPyplotSecond`

> **Corpus:** List both the Axes/Figure and the pyplot reference for a dual-API function, pyplot second.

- **Pre-condition —** each References admonition the agent wrote that names a function existing on both the Axes/Figure side and the pyplot side.
- **Pass condition —** both references are listed, pyplot second.

Fires only where C054's admonition already exists, so a missing block is one violation rather than two (§7.5). Heuristic on the **pre-condition** (§6.3): "a dual-API function" is approximated by a published list of the names that exist on both sides.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2739`](../compliance/rules/matplotlib/documentation.py#L2739) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C057 — `EveryExampleIsListedInAnExplicitGalleryOrder`

> **Corpus:** List every example in a gallery_order.txt that has no '*' placeholder.

- **Pre-condition —** each gallery example the agent added, when the contribution also carries a gallery-order file that has no ``*`` placeholder.
- **Pass condition —** the example is named in it.

The order file must be in the patch: without it there is nothing to check against, and the rule finds no target rather than guessing at a file it cannot see. Heuristic on the **pre-condition** (§6.3): the order file is recognised by name, and the placeholder by a bare ``*`` on one of its lines.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2789`](../compliance/rules/matplotlib/documentation.py#L2789) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C058 — `ARawRstFileInAGalleryIsAddedToAToctree`

> **Corpus:** Add any raw .rst file in a mixed gallery subdirectory to a toctree.

- **Pre-condition —** each reST file the agent added to a gallery directory that also holds Python examples.
- **Pass condition —** some file in the change adds it to a toctree.

Heuristic on the **pass condition** (§6.2): the toctree entry is recognised by the file's stem appearing under a ``.. toctree::`` directive somewhere in the change, not by resolving the toctree's own paths.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2833`](../compliance/rules/matplotlib/documentation.py#L2833) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C062 — `AGalleryTitleDoesNotSayDemo`

> **Corpus:** Do not use the word "demo" in a gallery example title.

- **Pre-condition —** each gallery example title the agent wrote.
- **Pass condition —** it does not use the word "demo".

Not heuristic (§6.2): the forbidden word is named in the rule and matched by name. Reads gallery titles only; the sentence-case rule for documentation pages is C002's and reads pages under :file:`doc/` (§7.5).


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2885`](../compliance/rules/matplotlib/documentation.py#L2885) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C064 — `AGalleryTitleVerbIsSimplePresent`

> **Corpus:** Use the simple present tense in a gallery example title that needs a verb.

- **Pre-condition —** each gallery example title the agent wrote that opens with a verb form.
- **Pass condition —** the verb is simple present, not a gerund or a past form.

Heuristic on **both** layers (§6.2, §6.3): "needs a verb" is approximated by the title opening with an ``-ing`` or ``-ed`` word or with one of a list of common imperative verbs, and the tense by the suffix -- neither is a parse of English.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2918`](../compliance/rules/matplotlib/documentation.py#L2918) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C070 — `ACustomisedExampleFigureFitsTheGalleryWidth`

> **Corpus:** Keep a customised example figure within the 720px (or 896px) rendered width limit.

- **Pre-condition —** each gallery example the agent wrote that sets its own figure size.
- **Pass condition —** the rendered width stays within the gallery's limit.

Heuristic on the **pass condition** (§6.2): the rendered width is computed as ``figsize`` times the dpi the example sets, falling back to matplotlib's default of 100, so a figure resized at save time is measured wrongly. The wider 896px limit is used, so the rate is an upper bound.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2961`](../compliance/rules/matplotlib/documentation.py#L2961) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C072 — `APlotTypesTitleIsTheMethodSignature`

> **Corpus:** Title a plot types entry with the method signature and its required arguments.

- **Pre-condition —** each plot-types entry the agent wrote.
- **Pass condition —** its title is a method call with its required arguments.

Heuristic on the **pass condition** (§6.2): "the method signature and its required arguments" is graded as ``name(arg, ...)`` with at least one argument, so a method that genuinely takes none reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3001`](../compliance/rules/matplotlib/documentation.py#L3001) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C073 — `APlotTypesEntryIsOneSentenceWithALink`

> **Corpus:** Describe a plot types entry in one sentence and link to the method's API documentation.

- **Pre-condition —** each plot-types entry the agent wrote whose docstring says something below its title.
- **Pass condition —** the description is one sentence and links to the method's API documentation.

Heuristic on the **pass condition** (§6.2): "one sentence" is counted by terminal punctuation, so a description containing an abbreviation reads as two.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3038`](../compliance/rules/matplotlib/documentation.py#L3038) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C075 — `APlotTypesEntryUsesTheGalleryStylesheet`

> **Corpus:** Style a plot types entry with the ``_mpl-gallery`` stylesheet.

- **Pre-condition —** each plot-types entry the agent wrote.
- **Pass condition —** it selects the ``_mpl-gallery`` stylesheet.

Not heuristic (§6.2): the stylesheet is a name the rule states, and the check is whether the file selects it.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3083`](../compliance/rules/matplotlib/documentation.py#L3083) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C126 — `AVerbPhraseHeadingIsImperative`

> **Corpus:** Write a verb-phrase heading in the second-person imperative, not the gerund.

- **Pre-condition —** each section heading the agent wrote that opens with a verb form.
- **Pass condition —** the verb is a second-person imperative, not a gerund.

Heuristic on **both** layers (§6.2, §6.3): "a verb-phrase heading" is approximated by the heading opening with an ``-ing`` word or with one of a list of common imperative verbs, and the grading is the ``-ing`` suffix -- neither is a parse of English.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3126`](../compliance/rules/matplotlib/documentation.py#L3126) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C127 — `DirectedInstructionsAreImperative`

> **Corpus:** Write directed instructions as second-person imperative sentences.

- **Pre-condition —** each prose sentence the agent wrote that directs the reader.
- **Pass condition —** it is written as an imperative, with no subject pronoun.

Split from C129 (§7.5): a directive sentence is graded here for its mood, and every other sentence is graded there for its tense, so no sentence is graded by both. Heuristic on **both** layers (§6.2, §6.3): a directed instruction is recognised from a subject pronoun with a modal, or from "please"/"let's"; and the imperative is graded as the absence of a leading subject.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3165`](../compliance/rules/matplotlib/documentation.py#L3165) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C129 — `ExplanationsArePresentSimple`

> **Corpus:** Write explanations in the present simple tense.

- **Pre-condition —** each prose sentence the agent wrote that is an explanation rather than an instruction.
- **Pass condition —** it uses the present simple tense.

Split from C127 (§7.5): an instruction is that rule's, and finds no target here. Heuristic on the **pass condition** (§6.2): tense is detected from auxiliaries -- ``will``, ``was``, ``has been``, ``is being`` and the rest -- which is a pattern match standing in for grammar, so a sentence that quotes a past tense reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3198`](../compliance/rules/matplotlib/documentation.py#L3198) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C131 — `ProseIsInTheActiveVoice`

> **Corpus:** Write in the active voice.

- **Pre-condition —** each prose sentence the agent wrote.
- **Pass condition —** it is in the active voice.

Grades voice only. Mood is C127's and tense C129's, so a badly written sentence is counted once per property the guide legislates rather than once per rule (§7.5). Heuristic on the **pass condition** (§6.2): the passive is detected as a form of *to be* followed by a past participle, approximated by an ``-ed``/``-en`` suffix, so "is red" is safe but "is a supported backend" reads as passive.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3231`](../compliance/rules/matplotlib/documentation.py#L3231) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C136 — `ACommentPrecedesTheCodeItDescribes`

> **Corpus:** Put a comment before or on the same line as the code it describes, never after it.

- **Pre-condition —** each full-line comment the agent wrote in a gallery example.
- **Pass condition —** code follows it, so it describes what comes next rather than what came before.

Heuristic on the **pre-condition** (§6.3): a comment's subject is not observable, so "describes the code" is approximated by there being code after it in the same block; a trailing note that deliberately closes a section reads as a violation. Trailing comments on a code line are excluded, which the sentence explicitly permits.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3263`](../compliance/rules/matplotlib/documentation.py#L3263) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C137 — `AVisualExampleEndsWithShow`

> **Corpus:** End an example that produces a visual with a show() call.

- **Pre-condition —** each gallery example the agent wrote that draws something.
- **Pass condition —** it ends with a ``plt.show()`` call.

Split from C049 by the same proxy (§7.5): an example that draws nothing is that rule's and must be named ``sgskip``; this one takes the examples that do draw. Heuristic on the **pre-condition** (§6.3): drawing is recognised from a pyplot or Axes method call, so an example that plots through a helper is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3309`](../compliance/rules/matplotlib/documentation.py#L3309) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C138 — `DocumentationExamplesCarryNoOutputLines`

> **Corpus:** Do not leave Python output lines in documentation examples.

- **Pre-condition —** each interactive block the agent wrote in a gallery example -- a run of ``>>>`` prompts.
- **Pass condition —** no line of captured Python output follows the prompts.

Heuristic on the **pre-condition** (§6.3): "a documentation example" is scoped to the gallery sources, where a prompt is always a transcript; docstring doctests are deliberately out of scope, since their expected output is what makes them tests.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3347`](../compliance/rules/matplotlib/documentation.py#L3347) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C140 — `ANumberedListIsForOrderedActions`

> **Corpus:** Use a numbered list only for actions performed in a determined order.

- **Pre-condition —** each numbered list the agent wrote on a documentation page.
- **Pass condition —** its items are actions -- each opens with a verb.

Heuristic on the **pass condition** (§6.2): "actions performed in a determined order" is approximated by every item opening with one of a list of imperative verbs or with an ``-ing`` form, so a list of ordered steps phrased as noun phrases reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3389`](../compliance/rules/matplotlib/documentation.py#L3389) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C141 — `TablesAreReStructuredTextAsciiTables`

> **Corpus:** Write tables as reStructuredText ASCII tables.

- **Pre-condition —** each table the agent wrote that is neither a Markdown table nor a ``csv-table`` directive.
- **Pass condition —** it is a reST ASCII table -- a grid or a simple table.

Markdown tables and ``csv-table`` are C142's, and this rule excludes them so a Markdown table is one violation rather than two (§7.5). What is left for this rule to catch is the reST table forms the guide does not want, ``list-table`` among them. Heuristic on the **pre-condition** (§6.3): a table is recognised from its own border syntax or its directive name, so a table drawn some other way is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3482`](../compliance/rules/matplotlib/documentation.py#L3482) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C142 — `NoMarkdownTablesAndNoCsvTable`

> **Corpus:** Do not use Markdown tables or the csv-table directive.

- **Pre-condition —** each table the agent wrote on a documentation page.
- **Pass condition —** it is neither a Markdown table nor a ``csv-table`` directive.

§7.1: a prohibition, so the antecedent is *writing a table* and the graded question is which form it took; an ASCII table is a recorded pass. C141 takes the forms this rule does not name (§7.5). Heuristic on the **pre-condition** for the reason C141 gives.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3520`](../compliance/rules/matplotlib/documentation.py#L3520) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C145 — `EveryPublicMethodHasAnInformativeDocstring`

> **Corpus:** Give every public method an informative docstring.

- **Pre-condition —** each public method the agent added to a class in the library.
- **Pass condition —** it carries a docstring, or the ``# docstring inherited`` marker that says the base class's applies.

The marker is accepted here on purpose (§7.5): C047 is the rule about marking an inherited docstring, and without this exception the two would contradict. Heuristic on the **pass condition** (§6.2): "informative" is graded as *present and more than a few words*, which no check can turn into a judgement of quality.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1887`](../compliance/rules/matplotlib/documentation.py#L1887) · source: https://matplotlib.org/devdocs/devel/pr_guide.html

### MATPLOTLIB-C158 — `ANewModuleGetsAnApiPage`

> **Corpus:** Add a new rst file to the API docs when you add a new module.

- **Pre-condition —** each new library module the agent added.
- **Pass condition —** the contribution also adds a reST file under :file:`doc/api/`.

The other half of the §7.5 resolution with C025: that rule forbids putting API *reference prose* in a :file:`doc/api` page and excludes contributions that add a module, which is the one case where a new page is required. Heuristic on the **pass condition** (§6.2): any new page under :file:`doc/api/` counts, rather than checking that it is the stub for this particular module.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1941`](../compliance/rules/matplotlib/documentation.py#L1941) · source: https://matplotlib.org/devdocs/devel/pr_guide.html

### MATPLOTLIB-C159 — `AHighLevelPlottingFunctionCarriesAnExample`

> **Corpus:** Put a small example in the Examples section of a high-level plotting function's docstring.

- **Pre-condition —** each public plotting function the agent added under :file:`lib/matplotlib/axes/` or in :file:`pyplot.py`.
- **Pass condition —** its docstring has an Examples section.

Heuristic on the **pre-condition** (§6.3): *a high-level plotting function* is approximated by where it lives, so a plotting helper added elsewhere is not seen.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:1975`](../compliance/rules/matplotlib/documentation.py#L1975) · source: https://matplotlib.org/devdocs/devel/pr_guide.html

### MATPLOTLIB-C219 — `ABackwardIncompatibleChangeGetsAVersioningDirective`

> **Corpus:** Add a versioning directive for a backward-incompatible API change.

- **Pre-condition —** a contribution that makes a backward-incompatible API change.
- **Pass condition —** it adds a versioning directive somewhere.

Heuristic on the **pre-condition** (§6.3): *backward-incompatible* is approximated by the contribution removing a public definition or filing a note under the ``behavior`` or ``removals`` folder of the API-change tree, so an incompatibility introduced by a changed default is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2027`](../compliance/rules/matplotlib/documentation.py#L2027) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C221 — `AVersioningDirectiveOnAPageEndsItsBlock`

> **Corpus:** Put a versioning directive at the end of its description block.

- **Pre-condition —** each versioning directive the agent wrote on a documentation page.
- **Pass condition —** nothing but its own body follows it before the block ends.

Reads prose pages only. Directives inside docstrings are C222's and C223's, split by whether they sit in the Parameters section, and no directive is graded twice (§7.5). Heuristic on the **pass condition** (§6.2): "the end of its description block" is read as *no further content at the directive's own indent before the next blank-line boundary*, which is a reading of a phrase the guide does not define precisely.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2073`](../compliance/rules/matplotlib/documentation.py#L2073) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C222 — `AClassOrFunctionDirectiveComesBeforeTheParameters`

> **Corpus:** Place a class or function versioning directive before the Parameters section.

- **Pre-condition —** each versioning directive the agent wrote in a docstring outside its Parameters section.
- **Pass condition —** it appears before the Parameters heading.

Split from C223 by location (§7.5): a directive *inside* the Parameters section belongs to a parameter and is that rule's. Heuristic on the **pre-condition** (§6.3): "a class or function directive" is approximated by *not inside the Parameters section*, so a directive placed in the Notes section is selected and, being after the heading, reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2133`](../compliance/rules/matplotlib/documentation.py#L2133) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C223 — `AParameterDirectiveEndsThatParametersDescription`

> **Corpus:** Place a parameter's versioning directive at the end of that parameter's description.

- **Pre-condition —** each versioning directive the agent wrote inside a docstring's Parameters section.
- **Pass condition —** it comes at the end of the description of the parameter it belongs to.

Split from C222 by location (§7.5). Heuristic on the **pass condition** (§6.2): the end of a parameter's description is read as *the last non-blank line before the next ``name : type`` entry*, which is numpydoc's own shape but not something the guide restates.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2173`](../compliance/rules/matplotlib/documentation.py#L2173) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C224 — `AVersioningDirectiveOmitsTheMicroVersion`

> **Corpus:** Omit the micro version from a versioning directive and never apply one to a whole module.

- **Pre-condition —** each versioning directive the agent wrote, wherever it sits.
- **Pass condition —** its version has at most two components, and it is not attached to a whole module.

Grades the *version string* and the directive's subject, which is a different property from where it sits -- C221, C222 and C223 grade placement, this one grades content, so no rule repeats another's finding (§7.5). Not heuristic (§6.2): the number of dot-separated components is arithmetic, and "a whole module" is exactly a module docstring.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2223`](../compliance/rules/matplotlib/documentation.py#L2223) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C233 — `DiscouragedApiCarriesADiscouragedAdmonition`

> **Corpus:** Mark discouraged API with a Discouraged admonition in its docstring.

- **Pre-condition —** each docstring the agent wrote or edited that says its API is discouraged.
- **Pass condition —** it says so in a ``.. admonition:: Discouraged`` block.

§7.1: the antecedent is *the API being discouraged*, recognised however the author said it, so a docstring that already uses the admonition is a recorded pass. The summary-line prefix is C234's, and the two grade different artefacts (§7.5). Heuristic on the **pre-condition** (§6.3): "discouraged API" is approximated by the word appearing in the docstring, so an API discouraged in other words is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2284`](../compliance/rules/matplotlib/documentation.py#L2284) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C234 — `ADiscouragedSummaryLineCarriesThePrefix`

> **Corpus:** Prefix a discouraged function's summary line with [*Discouraged*].

- **Pre-condition —** each docstring the agent wrote or edited that says its API is discouraged.
- **Pass condition —** its summary line begins ``[*Discouraged*]``.

The same antecedent as C233 on a different artefact: that rule asks for the admonition, this one for the summary prefix, and neither reads the other's (§7.5). Heuristic on the **pre-condition** for the reason C233 gives.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2318`](../compliance/rules/matplotlib/documentation.py#L2318) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C248 — `CHeaderDocumentationIsNumpydoc`

> **Corpus:** Write C/C++ header documentation in Numpydoc format.

- **Pre-condition —** each block comment the agent wrote in a C or C++ header that documents something -- one that names parameters or a return value.
- **Pass condition —** it is written in numpydoc form, with an underlined section heading.

Heuristic on **both** layers (§6.2, §6.3). *Header documentation* is approximated by a block comment mentioning parameters or a return, so a one-line description is not seen; and numpydoc form is graded as *a recognised section name underlined with dashes*, the same structural subset C023 grades for Python.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:2357`](../compliance/rules/matplotlib/documentation.py#L2357) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C272 — `APlottingFeatureIsDemonstratedInTheGallery`

> **Corpus:** Demonstrate a plotting-related feature in a gallery example.

- **Pre-condition —** a contribution that adds public plotting API.
- **Pass condition —** it also adds or edits a gallery example.

Fires on the *feature*, not on the example (§7.1), so a contribution that ships no demonstration is a recorded violation rather than an absent row. Heuristic on the **pre-condition** (§6.3): *plotting-related* is approximated by a new public definition under :file:`lib/matplotlib/axes/` or in :file:`pyplot.py`, so a feature added elsewhere is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3558`](../compliance/rules/matplotlib/documentation.py#L3558) · source: https://github.com/matplotlib/matplotlib/blob/main/.github/PULL_REQUEST_TEMPLATE.md

### MATPLOTLIB-C276 — `TheTagsDirectiveSitsAtTheBottomOfThePage`

> **Corpus:** Put the tags directive at the bottom of the page with the tags underneath it.

- **Pre-condition —** each ``.. tags::`` directive the agent wrote.
- **Pass condition —** nothing but the tags themselves follows it.

Heuristic on the **pass condition** (§6.2): "at the bottom" is read as no further non-blank content after the directive and its own argument lines, so a page that ends with a licence footer reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3611`](../compliance/rules/matplotlib/documentation.py#L3611) · source: https://matplotlib.org/devdocs/devel/tag_guidelines.html

### MATPLOTLIB-C277 — `EveryGalleryExampleCarriesATag`

> **Corpus:** Give every gallery example at least one content tag.

- **Pre-condition —** each gallery example the agent added.
- **Pass condition —** it carries a ``.. tags::`` directive naming at least one tag.

Not heuristic (§6.2): the directive is named in the rule and the check is its presence with a non-empty argument. How a tag must be written is C280's and C281's (§7.5).


ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3653`](../compliance/rules/matplotlib/documentation.py#L3653) · source: https://matplotlib.org/devdocs/devel/tag_guidelines.html

### MATPLOTLIB-C280 — `ATagIsWrittenSubcategoryColonTag`

> **Corpus:** Write a tag as ``subcategory: tag``.

- **Pre-condition —** each tag the agent wrote in a ``.. tags::`` directive.
- **Pass condition —** it is written ``subcategory: tag``.

Not heuristic (§6.2): the shape is stated in the rule and the check is the separator. How long the tag may be is C281's, which fires only on tags that already carry a subcategory (§7.5).


ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3694`](../compliance/rules/matplotlib/documentation.py#L3694) · source: https://matplotlib.org/devdocs/devel/tag_guidelines.html

### MATPLOTLIB-C281 — `ATagIsOneOrTwoWords`

> **Corpus:** Keep a tag to one or two words.

- **Pre-condition —** each tag the agent wrote that already carries a subcategory.
- **Pass condition —** the tag itself is one or two words.

Narrowed to well-formed tags (§7.5) so that a tag written without a subcategory is one violation -- C280's -- rather than two. Not heuristic (§6.2): the limit is a number the rule states and the check counts words.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3723`](../compliance/rules/matplotlib/documentation.py#L3723) · source: https://matplotlib.org/devdocs/devel/tag_guidelines.html

### MATPLOTLIB-C283 — `ATagAppliesToMoreThanOneEntry`

> **Corpus:** Do not create a tag that would apply to only one gallery entry.

- **Pre-condition —** each tag the agent wrote, in a contribution that tags two or more gallery entries -- so there is a comparison the patch can make.
- **Pass condition —** the tag is used by at least two of them.

The antecedent is narrowed to the case the evidence can decide. A contribution that tags a single example says nothing about how many entries a tag reaches, and grading it would fail every such change; that is why the rule finds no target there rather than manufacturing a violation. Heuristic on **both** layers (§6.3, §6.2): the comparison is confined to the entries in the patch, so a tag shared with an example the contribution does not touch reads as a violation.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/documentation.py:3759`](../compliance/rules/matplotlib/documentation.py#L3759) · source: https://matplotlib.org/devdocs/devel/tag_guidelines.html


## matplotlib — AI-assisted contribution policy

### MATPLOTLIB-C103 — `NoDirectInteractionByExternalAiTooling`

> **Corpus:** Do not let external AI tooling interact with the project directly by opening issues or pull requests or commenting.

- **Pre-condition —** a named model produced a pull request -- a patch, a description, or both -- and put it to the project itself.
- **Pass condition —** no external AI tooling interacted with the project directly.

``by_construction`` (§6.5), not ``heuristic``: the prohibited act *is* the experiment, and it is checked exactly -- the harness records which model produced the run, so nothing here stands in for anything. Under §9 the three cases are therefore violated, and two shapes of no-target; there is no satisfying case and its absence is not an omission. The pre-condition still discriminates rather than firing on every row: a run with no recorded model, or one that produced neither patch nor description, finds no target, so the activation rate measures how often a run puts anything to the project at all.


ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/matplotlib/ai_policy.py:56`](../compliance/rules/matplotlib/ai_policy.py#L56) · source: https://matplotlib.org/devdocs/devel/contribute.html

### MATPLOTLIB-C268 — `AiUseIsDisclosedInThePullRequestDescription`

> **Corpus:** Disclose in the PR description whether and how AI was used.

- **Pre-condition —** a named model produced a contribution, so there is AI use to declare.
- **Pass condition —** the pull-request description says that AI was used and says something about how.

Not ``by_construction``: the pull-request template carries an *AI Disclosure* heading and filling it in is something an agent can do, so a ``fail`` here is a real behavioural result rather than a property of the harness. Heuristic on the **pass condition** (§6.2): "whether and how" is matched by an AI-mention vocabulary plus a process word in the same sentence, so a disclosure worded outside that vocabulary reads as a violation, and a bare "AI" with nothing said about its use does not count. The pre-condition is exact -- the model is recorded.


`heuristic` · ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/matplotlib/ai_policy.py:95`](../compliance/rules/matplotlib/ai_policy.py#L95) · source: https://github.com/matplotlib/matplotlib/blob/main/.github/PULL_REQUEST_TEMPLATE.md


## matplotlib — Code and quality

### MATPLOTLIB-C152 — `PreCommitChecksPassBeforeOpeningThePullRequest`

> **Corpus:** Get the prek pre-commit checks passing before opening the pull request.

- **Pre-condition —** the contribution submits Python, which the ``prek`` hooks run over.
- **Pass condition —** the hooks report nothing new outside the pycodestyle findings that C235 and C236 own.

Deliberately *not* "the agent ran ``prek``": the sentence asks for the checks to be **passing**, so a contribution that never installed the hooks is judged rather than excused (§7.1 -- the antecedent is having submitted code, not having run the tool). Graded **one-sidedly** where no report exists (§9). A submitted module that will not parse provably fails ruff and every other hook, and that is decidable from the patch; anything else needs the run, so the rule withholds rather than reading source text as a clean bill. Not heuristic: the report is the tool's own verdict (§6.2), and the withholding branch does not grade at all. The ``E``/``W`` findings are excluded here and graded by ``language_style.C235`` and ``C236``, so one badly formatted line is one violation rather than three (§7.5).


ownership `touched` · reads `files, lint_run` · tier `differential`

[`compliance/rules/matplotlib/code_quality.py:114`](../compliance/rules/matplotlib/code_quality.py#L114) · source: https://matplotlib.org/devdocs/devel/pr_guide.html

### MATPLOTLIB-C242 — `MypyTypeHintsFollowAPublicApiChange`

> **Corpus:** Update the mypy type hints when you add or change public API.

- **Pre-condition —** each library module where the agent added or changed a public function or class definition.
- **Pass condition —** the contribution also edits that module's ``.pyi`` type stub, or the shared ``typing`` module.

Heuristic on **both** layers (§6.2, §6.3). The pre-condition approximates *add or change public API* by a public ``def``/``class`` header on a line the agent's edit reaches, so a change made purely inside a body -- a new keyword argument's default, say -- is not seen, and a private helper never is. The pass condition accepts any edit to the sibling stub rather than checking that the stub now matches the signature, which would need the type checker's own verdict. A file where the public-API change *is* a deprecation is excluded and left to ``specialized.C209``, which asks the same question of the same stub for that case; without the exclusion one deprecation would depress two rates (§7.5). Instances older than the stub files exist: matplotlib grew ``lib/matplotlib/*.pyi`` in 3.8, and a checkout without them can only fail. That is a property of the benchmark rather than of the rule, and it is reported rather than papered over.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/code_quality.py:167`](../compliance/rules/matplotlib/code_quality.py#L167) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C255 — `LoggingRatherThanPrintForDebugOutput`

> **Corpus:** Use logging rather than print for debug output.

- **Pre-condition —** each library module the agent edited, any of which could emit debug output.
- **Pass condition —** it adds no ``print`` call.

Heuristic on **both** layers (§6.3, §6.2). *Emitting debug output* is not observable, so the pre-condition fires on the superset -- every library module the agent touched -- and the pass condition treats any added ``print`` as debug output. A ``print`` that is genuinely the module's product would read as a violation here; the direction of that error is declared rather than removed. Gallery examples and tests are excluded, since printing is what much of that code is for.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/code_quality.py:225`](../compliance/rules/matplotlib/code_quality.py#L225) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C256 — `ModuleLoggerIsCreatedRightAfterTheImports`

> **Corpus:** Create the module logger as ``_log = logging.getLogger(__name__)`` right after the imports.

- **Pre-condition —** each library module where the agent added a module-level ``logging.getLogger`` assignment.
- **Pass condition —** it is bound to ``_log`` and is the first statement after the module's leading import block.

§7.1: the antecedent is *creating a module logger*, not *creating one correctly* -- a module that makes no logger is out of scope, and a badly named or badly placed one is a recorded violation rather than an absent target. Heuristic on the **pass condition** (§6.6, the doubt named). The name and the call are exact, but "right after the imports" is graded as *the first statement following the leading import block*, with blank lines and comments skipped; a module that separates the two with a constant is failed on a reading the sentence does not spell out.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/code_quality.py:262`](../compliance/rules/matplotlib/code_quality.py#L262) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C257 — `LoggingArgumentsArePercentStyleParameters`

> **Corpus:** Pass logging arguments as %-style parameters rather than pre-formatted strings.

- **Pre-condition —** each logging call the agent added to a library module.
- **Pass condition —** its message argument is a plain string, with any values passed as further arguments rather than formatted into it.

Not heuristic (§6.2): "pre-formatted" is checked as a closed list of syntactic forms -- an f-string, ``%`` applied at the call site, ``str.format()``, and string concatenation -- each of which is a node type rather than a text pattern, and the rule's own standard names the alternative it wants. §7.1: every logging call is selected, not only the pre-formatted ones, so a compliant call is recorded as a pass instead of vanishing from the denominator.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/code_quality.py:342`](../compliance/rules/matplotlib/code_quality.py#L342) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C258 — `ExpectedCodePathsAreLoggedAtDebugLevel`

> **Corpus:** Log expected code paths at debug level only.

- **Pre-condition —** each logging call the agent added to a library module outside an ``except`` handler -- the calls that report an expected code path.
- **Pass condition —** the call uses the ``debug`` level.

Heuristic on the **pre-condition** (§6.3): *an expected code path* is a category the project does not enumerate, and it is approximated here by *not inside an exception handler*. A recoverable-but-unexpected condition detected by an ordinary ``if`` is therefore selected and, if logged at ``warning``, reads as a violation; a call inside a handler is excluded so the common legitimate ``warning`` is not failed. Deliberately separate from C257 (§7.5): that rule grades how the arguments are passed and this one grades the level, so one badly written call cannot depress two rates.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/code_quality.py:384`](../compliance/rules/matplotlib/code_quality.py#L384) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C291 — `FilesAPreCommitHookModifiedAreRestagedAndRecommitted`

> **Corpus:** Re-stage and re-commit any file a pre-commit hook modified.

- **Pre-condition —** each ``prek``/pre-commit invocation whose output reports that a hook modified a file.
- **Pass condition —** a ``git add`` and a ``git commit`` follow it in the command log.

§7.2 is the shape: the antecedent is the *hook having rewritten something*, never the re-staging itself, so a run that re-staged is recorded as a pass and one that walked away is a violation. A run whose hooks changed nothing finds no target, which is correct -- there is nothing to re-commit. Heuristic on the **pre-condition** (§6.3), which reads the command's own output text for "files were modified by this hook" rather than re-running the tool, and on the **pass condition**, which accepts any later ``git add`` plus ``git commit`` without checking that the re-staged paths are the ones the hook rewrote.


`heuristic` · ownership `touched` · reads `commands` · tier `differential`

[`compliance/rules/matplotlib/code_quality.py:430`](../compliance/rules/matplotlib/code_quality.py#L430) · source: https://matplotlib.org/devdocs/devel/development_setup.html


## matplotlib — Language and framework style

### MATPLOTLIB-C044 — `AnArtistPropertyAccessorComesAsASetGetPair`

> **Corpus:** Name an Artist property accessor pair ``set_PROPERTYNAME`` and ``get_PROPERTYNAME``.

- **Pre-condition —** each ``set_PROPERTYNAME`` method the agent added to a class in the library.
- **Pass condition —** the same class defines ``get_PROPERTYNAME``.

The antecedent is deliberately the **setter**, not either accessor (§7.5-style narrowing, stated here because it changes what the rule measures). Matplotlib has many legitimate read-only accessors -- ``get_window_extent``, ``get_children`` -- and selecting getters too would manufacture a violation for every one of them. A property that can be *set* is the case the sentence is about. Heuristic on the **pre-condition** (§6.3): *an Artist* is approximated by *a class in the library*, since the base classes a checkout defines are not in the patch.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:297`](../compliance/rules/matplotlib/language_style.py#L297) · source: https://matplotlib.org/devdocs/devel/document.html

### MATPLOTLIB-C117 — `FigureIsCapitalisedWhenItNamesTheObject`

> **Corpus:** Capitalise Figure when it means the Matplotlib object or class, and lowercase it in general language.

- **Pre-condition —** each prose occurrence of "figure" the agent wrote that is not one of the guide's general-language uses.
- **Pass condition —** it is capitalised.

Heuristic on the **pre-condition** (§6.3): *meaning the Matplotlib object* is not observable, so every prose occurrence is selected except those matching the general-language uses the guide itself contrasts with. A general use the list does not anticipate is therefore selected, and reads as a violation when it is lower case. Code markup -- inline literals, roles, hyperlink targets, URLs -- is blanked out before matching, so a class name is never mistaken for a word.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:117`](../compliance/rules/matplotlib/language_style.py#L117) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C118 — `AxesIsCapitalisedWhenItNamesTheObject`

> **Corpus:** Capitalise Axes when it means the Matplotlib object or class, and lowercase it in general language.

- **Pre-condition —** each prose occurrence of "axes" the agent wrote that is not one of the guide's general-language uses -- the plural of *axis* among them.
- **Pass condition —** it is capitalised.

Heuristic on the **pre-condition** (§6.3): *meaning the Matplotlib object* is not observable, so every prose occurrence is selected except those matching the general-language uses the guide itself contrasts with. A general use the list does not anticipate is therefore selected, and reads as a violation when it is lower case. Code markup -- inline literals, roles, hyperlink targets, URLs -- is blanked out before matching, so a class name is never mistaken for a word.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:138`](../compliance/rules/matplotlib/language_style.py#L138) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C119 — `ArtistIsCapitalisedWhenItNamesTheObject`

> **Corpus:** Capitalise Artist when it means the Matplotlib object or class, and lowercase it in general language.

- **Pre-condition —** each prose occurrence of "artist" the agent wrote that is not one of the guide's general-language uses.
- **Pass condition —** it is capitalised.

Heuristic on the **pre-condition** (§6.3): *meaning the Matplotlib object* is not observable, so every prose occurrence is selected except those matching the general-language uses the guide itself contrasts with. A general use the list does not anticipate is therefore selected, and reads as a violation when it is lower case. Code markup -- inline literals, roles, hyperlink targets, URLs -- is blanked out before matching, so a class name is never mistaken for a word.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:158`](../compliance/rules/matplotlib/language_style.py#L158) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C120 — `AxisIsCapitalisedWhenItNamesTheObject`

> **Corpus:** Capitalise Axis when it means the Matplotlib object or class, and lowercase it in general language.

- **Pre-condition —** each prose occurrence of "axis" the agent wrote that is not one of the guide's general-language uses -- a named or mathematical axis among them.
- **Pass condition —** it is capitalised.

Heuristic on the **pre-condition** (§6.3): *meaning the Matplotlib object* is not observable, so every prose occurrence is selected except those matching the general-language uses the guide itself contrasts with. A general use the list does not anticipate is therefore selected, and reads as a violation when it is lower case. Code markup -- inline literals, roles, hyperlink targets, URLs -- is blanked out before matching, so a class name is never mistaken for a word.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:178`](../compliance/rules/matplotlib/language_style.py#L178) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C121 — `TheAxesUsagePatternIsCalledTheAxesInterface`

> **Corpus:** Call the Axes usage pattern the "Axes interface", not the explicit, object-oriented, OO-style or OOP interface.

- **Pre-condition —** each prose phrase the agent wrote that names the Axes usage pattern -- ``<something> interface``, by any of the names the guide lists.
- **Pass condition —** the name used is "Axes".

§7.1: the antecedent is *naming the pattern*, whichever name is used, so a page that calls it the Axes interface is recorded as a pass. Selecting the banned names would only ever find violations. Heuristic on the **pre-condition** (§6.3), which recognises the pattern from the word "interface" preceded by one of the guide's five names; a sentence that describes the pattern without naming it is not seen. Reads only the Axes names -- the pyplot ones are C122's (§7.5).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:199`](../compliance/rules/matplotlib/language_style.py#L199) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C122 — `ThePyplotUsagePatternIsCalledThePyplotInterface`

> **Corpus:** Call the pyplot usage pattern the "pyplot interface", not the implicit or MATLAB-like interface, and do not capitalise Pyplot.

- **Pre-condition —** each prose phrase the agent wrote that names the pyplot usage pattern, and each prose occurrence of the word "Pyplot" capitalised.
- **Pass condition —** the pattern is called the "pyplot interface", spelled in lower case.

Both clauses of the sentence are graded through one selection so that they cannot disagree: a rival name violates, and so does a capitalised ``Pyplot``, while "pyplot interface" satisfies. Heuristic on the **pre-condition** (§6.3): naming the pattern is recognised from the word "interface" preceded by one of the guide's names, so a sentence that describes the pattern without naming it is not seen. Reads only the pyplot names -- the Axes ones are C121's (§7.5).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:239`](../compliance/rules/matplotlib/language_style.py#L239) · source: https://matplotlib.org/devdocs/devel/style_guide.html

### MATPLOTLIB-C189 — `HelperFunctionsArePrefixedWithAnUnderscore`

> **Corpus:** Prefix helper functions and internal attributes with an underscore.

- **Pre-condition —** each module-level function the agent added to a library module that carries no docstring -- the shape of a helper rather than of published API.
- **Pass condition —** its name begins with an underscore.

Heuristic on the **pre-condition** (§6.3): *a helper* is not a category the project enumerates, and it is approximated here by *undocumented module-level function*, since matplotlib gives every public function a numpydoc docstring. A documented helper is therefore not seen, and an undocumented function that really is public reads as a violation. **Partial reading, declared (§6.6/§8).** The sentence's second clause -- "and internal attributes" -- is not graded. Nothing in the patch distinguishes an internal attribute from a public one, and a predicate that guessed would grade the wrong thing exactly.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:348`](../compliance/rules/matplotlib/language_style.py#L348) · source: https://matplotlib.org/devdocs/devel/api_changes.html

### MATPLOTLIB-C235 — `PythonCodeIsFormattedToPep8`

> **Corpus:** Format Python code to PEP8 as enforced by ruff.

- **Pre-condition —** the contribution submits Python, which ruff would check.
- **Pass condition —** ruff reports no new pycodestyle finding other than the line-length one C236 owns.

Not heuristic (§6.2): the verdict is a tool's own report, base-subtracted. Graded **one-sidedly** where no report exists (§9) -- a submitted file that will not parse provably fails, everything else withholds with ``lint_run`` named as the missing input rather than reading source text as a clean bill. Owns the ``E``/``W`` findings and nothing else. ``E501`` belongs to C236, which counts characters from the patch and needs no tool; every other code belongs to ``code_quality.C152``, the pre-commit gate (§7.5).


ownership `touched` · reads `files, lint_run` · tier `static`

[`compliance/rules/matplotlib/language_style.py:402`](../compliance/rules/matplotlib/language_style.py#L402) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C236 — `LinesAreAtMostEightyEightCharacters`

> **Corpus:** Keep lines to at most 88 characters.

- **Pre-condition —** each Python file the agent edited.
- **Pass condition —** no line it wrote exceeds 88 characters.

Not heuristic (§6.2): the limit is a number the project states and the check counts characters. Needs no linter, which is why this rule and not C235 is coded from the patch; ``E501`` is excluded from C235's and C152's readings of the ruff report so the same long line is one violation, not three (§7.5). Only lines the agent wrote are judged: a long line already in the file is not the agent's doing (§4.1).


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:449`](../compliance/rules/matplotlib/language_style.py#L449) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C238 — `ImportsUseTheStandardAliases`

> **Corpus:** Use the listed standard aliases when importing numpy, matplotlib and its submodules.

- **Pre-condition —** each import the agent wrote that binds one of the modules the coding guide gives a standard alias to.
- **Pass condition —** the binding is that alias.

Not heuristic (§6.2): the guide publishes the list, so the check is an equality against a stated name. Modules the list does not cover find no target, which is correct -- the sentence says "the listed standard aliases".


ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:509`](../compliance/rules/matplotlib/language_style.py#L509) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C239 — `RcParamsIsReachedThroughTheModule`

> **Corpus:** Access rcParams as mpl.rcParams rather than importing it directly.

- **Pre-condition —** each library module where the agent wrote a line mentioning ``rcParams``.
- **Pass condition —** none of those lines imports the name directly.

§7.1: the antecedent is *using rcParams*, so a module that reaches it as ``mpl.rcParams`` is recorded as a pass; selecting direct imports would only ever find violations. The two files that define and validate rcParams are excluded, since a bare name there is the definition rather than a style error. Heuristic on the **pass condition** (§6.2): ``matplotlib.rcParams`` is accepted alongside ``mpl.rcParams``, because it is the same access written without the alias and failing it would grade C238's sentence twice (§7.5).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:557`](../compliance/rules/matplotlib/language_style.py#L557) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C245 — `CCodeFollowsPep7`

> **Corpus:** Write C and C++ code to PEP7 style.

- **Pre-condition —** each C or C++ file the agent edited.
- **Pass condition —** the lines it wrote use spaces rather than tabs and stay within PEP 7's 79 columns.

Heuristic on the **pass condition** (§6.2), and the doubt is named: PEP 7 is a whole style, and only the parts decidable from text without a formatter are checked here -- indentation characters and line width. A file that satisfies both and breaks PEP 7's brace or naming conventions is recorded as a pass, so this rate is an upper bound.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:814`](../compliance/rules/matplotlib/language_style.py#L814) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C246 — `PythonCInterfaceCodeIsKeptSeparateFromCore`

> **Corpus:** Keep Python/C interface code separate from core C/C++ code.

- **Pre-condition —** each C or C++ file the agent edited that carries Python/C interface code.
- **Pass condition —** the same file carries no core computation.

§7.1: the antecedent is *writing interface code*, so a pure wrapper is recorded as a pass; selecting mixed files would only ever find violations. What the file is **called** is C247's question and is not asked here, so a correctly named wrapper that mixes in core code violates this rule alone (§7.5). Heuristic on **both** layers (§6.2, §6.3). Interface code is recognised by the CPython and pybind11 symbols only interface code uses, and core computation by a plain C function definition whose signature names no Python type -- a proxy that misses a core routine written as a C++ template and wrongly selects a helper with a primitive signature.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:856`](../compliance/rules/matplotlib/language_style.py#L856) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C247 — `PythonCInterfaceFilesAreNamedWrap`

> **Corpus:** Name Python/C interface files FOO_wrap.cpp or FOO_wrapper.cpp.

- **Pre-condition —** each C or C++ file the agent added that carries Python/C interface code.
- **Pass condition —** it is named ``FOO_wrap`` or ``FOO_wrapper`` with a C/C++ suffix.

Scoped to files the agent *added*: renaming a wrapper that was already in the tree is not what the sentence asks for (§4.3). Grades the name only -- whether the file also carries core code is C246's (§7.5). Heuristic on the **pre-condition** (§6.3): interface code is recognised by the CPython and pybind11 symbols only interface code uses, so a wrapper written against a different binding layer is not seen.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:904`](../compliance/rules/matplotlib/language_style.py#L904) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C253 — `AFunctionConsumingEveryKeywordDeclaresThemExplicitly`

> **Corpus:** Declare keyword arguments explicitly when the function consumes all of them.

- **Pre-condition —** each library function the agent wrote or edited that takes keyword arguments and forwards none of them onward -- so it consumes all of them itself.
- **Pass condition —** they are declared as named parameters rather than gathered in a ``**kwargs`` catch-all.

§7.1: the antecedent is *consuming all the keywords*, which a compliant function does with an explicit signature; selecting only ``**kwargs`` functions would record nothing but violations. Narrowed away from C254 (§7.5): this rule fires only where **nothing** is forwarded. A function that consumes some keywords and passes the rest on is C254's, and finds no target here. Heuristic on the **pre-condition** (§6.3): "consumes all of them" is approximated by the catch-all never being passed to another call, so a function that forwards through a dict it built by hand is wrongly selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:697`](../compliance/rules/matplotlib/language_style.py#L697) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C254 — `LocallyConsumedArgumentsAreKeywordOnly`

> **Corpus:** Declare locally consumed arguments as keyword-only instead of popping them off **kwargs.

- **Pre-condition —** each library function the agent wrote or edited that takes a ``**kwargs`` catch-all, forwards it onward, and also consumes something from it locally -- whether by declaring it or by popping it.
- **Pass condition —** what it consumes locally is declared as a keyword-only parameter, not popped off the catch-all.

Narrowed away from C253 (§7.5): a function that forwards nothing is that rule's, and finds no target here; a function that forwards everything and keeps nothing finds no target in either. Heuristic on the **pre-condition** (§6.3): "consumes locally" is recognised from ``kwargs.pop``/``get``/``setdefault`` calls and from keyword-only parameters, so a function that reads its catch-all by subscript is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:750`](../compliance/rules/matplotlib/language_style.py#L750) · source: https://matplotlib.org/devdocs/devel/coding_guide.html

### MATPLOTLIB-C261 — `UserFacingWarningsGoThroughWarnExternal`

> **Corpus:** Raise user-facing warnings through _api.warn_external rather than warnings.warn directly.

- **Pre-condition —** each warning call the agent added to a library module, by either route.
- **Pass condition —** it goes through ``_api.warn_external`` (or ``warn_deprecated``) rather than ``warnings.warn``.

§7.1: the antecedent is *raising a warning*, so a call that already uses the helper is recorded as a pass. Calls inside ``_api`` itself are excluded, since that is where the helper is implemented. Heuristic on the **pre-condition** (§6.3): *user-facing* is not observable, so every warning raised in library code is selected -- including the internal ones the sentence does not reach, which read as violations when they use ``warnings.warn``.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/matplotlib/language_style.py:609`](../compliance/rules/matplotlib/language_style.py#L609) · source: https://matplotlib.org/devdocs/devel/coding_guide.html


# mwaskom

| category | rules |
|---|---:|
| [Tests and test style](#mwaskom-tests-and-test-style) | 1 |
| [Code and quality](#mwaskom-code-and-quality) | 1 |


## mwaskom — Tests and test style

### MWASKOM-C001 — `SuiteRunThroughMakeTest`

> **Corpus:** Run `make test` from the source directory to exercise the unit test suite.

- **Pre-condition —** the agent submitted a contribution.
- **Pass condition —** a `make test` invocation appears in the command log.

Not "the agent ran the tests": the coverage report the README mentions in the same breath is a side effect of the target rather than a second obligation, and a direct `pytest` run is not the command the section names. Accepting one would be reading the `Makefile`'s expansion instead of the rule.


ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/mwaskom/tests.py:44`](../compliance/rules/mwaskom/tests.py#L44) · source: https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/README.md


## mwaskom — Code and quality

### MWASKOM-C002 — `ChangedPythonSatisfiesRuffConfig`

> **Corpus:** Make the changed Python files satisfy the ruff configuration declared in `pyproject.toml`.

- **Pre-condition —** each Python file the agent changed that `extend-exclude` does not put outside the ruff configuration.
- **Pass condition —** that file carries no ruff finding the base commit did not already have -- taken from the stored `ruff` report where one covers it, and otherwise from the two things the published configuration settles on its own, that the file parses and that no line the agent wrote exceeds `line-length = 88`.

Not `heuristic`: every verdict returned is either a tool's own report or a comparison against a number the project publishes (§6.2), and the pre-condition selects on paths and file type (§6.3). What cannot be decided that way is `Undetermined` rather than approximated, which is why the rule grades one-sidedly and its third test case is the withheld one (§9).


ownership `touched` · reads `files, lint_run` · tier `static`

[`compliance/rules/mwaskom/code_quality.py:75`](../compliance/rules/mwaskom/code_quality.py#L75) · source: https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/README.md


# pallets

| category | rules |
|---|---:|
| [Git and commit conventions](#pallets-git-and-commit-conventions) | 5 |
| [PR and release metadata](#pallets-pr-and-release-metadata) | 4 |
| [Tests and test style](#pallets-tests-and-test-style) | 10 |
| [Documentation and docstrings](#pallets-documentation-and-docstrings) | 10 |
| [AI-assisted contribution policy](#pallets-ai-assisted-contribution-policy) | 3 |
| [Code and quality](#pallets-code-and-quality) | 2 |


## pallets — Git and commit conventions

### PALLETS-C009 — `SummaryLineAtMostFifty`

> **Corpus:** Keep the first line of the commit message to 50 characters or fewer.

- **Pre-condition —** every commit the agent made.
- **Pass condition —** its first line is at most 50 characters.

Not heuristic: an exact number compared against an exact string (§6.2), and the pre-condition selects on a commit existing, which is an observable fact (§6.3).


ownership `created` · reads `commits` · tier `static`

[`compliance/rules/pallets/git_conventions.py:41`](../compliance/rules/pallets/git_conventions.py#L41) · source: https://palletsprojects.com/contributing/pr/

### PALLETS-C010 — `BodySeparatedAndWrapped`

> **Corpus:** Separate any commit message body from the subject with a blank line and wrap it at 72 characters.

- **Pre-condition —** every commit the agent made whose message carries more than a first line.
- **Pass condition —** a blank line separates that text from the first line and no line of it exceeds 72 characters.

The corpus files this *never fires*, and the pre-condition is why: a body is optional, so a one-line message finds no target. It is not narrowed any further than that -- selecting only well-formed bodies would make the rule unfailable (§7.1). ``message_lines`` rather than ``body`` on purpose: `body` is defined as the text after the first blank line, so a message with no blank separator -- the exact defect this rule catches -- would present an empty body and nothing to judge.


ownership `created` · reads `commits` · tier `static`

[`compliance/rules/pallets/git_conventions.py:66`](../compliance/rules/pallets/git_conventions.py#L66) · source: https://palletsprojects.com/contributing/pr/

### PALLETS-C011 — `NoIssueNumberInCommitMessage`

> **Corpus:** Do not put issue numbers in the commit message.

- **Pre-condition —** every commit the agent made.
- **Pass condition —** its message carries no issue or pull-request reference.

The pre-condition is the permitted act -- making a commit -- not the prohibited one (§7.1); selecting messages that carry a reference could only ever find violations. Heuristic on the **pass condition** (§6.2). *Issue number* is recognised by the three notations GitHub understands -- `#1234`, `GH-1234` and a link into an issue or pull request -- so a number named in prose ("as reported in issue 1234") is not caught, and a `#` followed by digits inside a quoted string would be. The rule's own reason (a noisy GitHub UI) is about the notations that GitHub renders, which is what these are.


`heuristic` · ownership `created` · reads `commits` · tier `static`

[`compliance/rules/pallets/git_conventions.py:109`](../compliance/rules/pallets/git_conventions.py#L109) · source: https://palletsprojects.com/contributing/pr/

### PALLETS-C012 — `CollaboratorsGetCoAuthoredBy`

> **Corpus:** Give each collaborator a co-authored-by line at the bottom of the commit message.

- **Pre-condition —** every commit whose message credits somebody besides its author.
- **Pass condition —** each such credit is a `co-authored-by: name <email>` line in the trailer block at the bottom of the message.

Heuristic on the **pre-condition** (§6.3). The rule's real antecedent is *you worked with someone else*, which nothing in the bundle records: git stores one author, and the harness runs alone. The observable stand-in is a message that credits a second person at all -- a `co-authored-by`, `signed-off-by`, `reviewed-by` or `thanks-to` line -- so the rule fires on the rare run that names a collaborator and finds no target otherwise. That is the corpus's *never fires* reading, kept without narrowing the selection to the compliant trailer, which would make the rule unfailable (§7.1).


`heuristic` · ownership `created` · reads `commits` · tier `static`

[`compliance/rules/pallets/git_conventions.py:144`](../compliance/rules/pallets/git_conventions.py#L144) · source: https://palletsprojects.com/contributing/pr/

### PALLETS-C031 — `NoDirectCommitsToProtectedBranches`

> **Corpus:** Do not commit directly to main or stable; route every change through a pull request.

- **Pre-condition —** every commit the agent made.
- **Pass condition —** it was not committed onto `main` or `stable`, and it reached the project through a pull request.

``by_construction`` (§6.5), not heuristic: the check is exact, and it is the harness that makes compliance impossible. The agent commits into the checked-out clone and there is no pull request anywhere in the setup, so the second half of the sentence cannot be satisfied whatever branch the commit lands on. Scored rather than excluded, because a rule the guided arm was shown has to be reportable (§1); a `fail` here says nothing about the agent's diligence.


ownership `created` · reads `commits, branch` · tier `trajectory`

[`compliance/rules/pallets/git_conventions.py:193`](../compliance/rules/pallets/git_conventions.py#L193) · source: https://palletsprojects.com/contributing/pr/


## pallets — PR and release metadata

### PALLETS-C018 — `NoChangelogEntryForDocsOrToolConfig`

> **Corpus:** Do not add a changelog entry for a change that only touches documentation or tool configuration.

- **Pre-condition —** a contribution whose every change outside the changelog is documentation or tool configuration.
- **Pass condition —** it adds no entry to `CHANGES.rst`.

The pre-condition is the situation the prohibition is aimed at, not the prohibited act (§7.1): selecting contributions that added an entry could only ever find violations. Heuristic on the **pre-condition** (§6.3). *Tool configuration* is a category the sentence names but does not enumerate, so it is approximated by the project's configuration paths -- `pyproject.toml`, `tox.ini`, `.pre-commit-config.yaml`, `.github/` and their neighbours. A configuration file outside that list makes the contribution look like a code change and the rule finds no target.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/pallets/pr_metadata.py:60`](../compliance/rules/pallets/pr_metadata.py#L60) · source: https://palletsprojects.com/contributing/pr/

### PALLETS-C021 — `BugFixCarriesNothingUnrelated`

> **Corpus:** Do not include unrelated refactors, type annotation changes or test reorganizations in a bug fix.

- **Pre-condition —** a contribution read as a bug fix -- it changes shipped source that already existed.
- **Pass condition —** it bundles none of the three things the sentence names: a file moved or removed, a change that only adds type annotations, or a test file reorganised.

Heuristic on **both** layers. On the pre-condition (§6.3), *a bug fix* is not observable -- provenance is a fact about the benchmark, not the contribution -- so the stand-in is a change to existing shipped source, and a contribution that adds a new module is treated as a feature and finds no target. On the pass condition (§6.2), only the forms that leave a mark in a diff are detected: a rename or deletion for the refactor and the test reorganisation, and an all-annotations file for the type change. An unrelated rewrite inside one file is invisible here and is reported as satisfying.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/pallets/pr_metadata.py:105`](../compliance/rules/pallets/pr_metadata.py#L105) · source: https://palletsprojects.com/contributing/pr/

### PALLETS-C053 — `ChangelogEntryAppendedToItsSection`

> **Corpus:** Append a new changelog entry to the end of its section.

- **Pre-condition —** each block of lines the agent added to `CHANGES.rst`.
- **Pass condition —** no pre-existing content follows it before the next version heading.

Heuristic on the **pass condition** (§6.2). The sentence says *the relevant section*, and which section is relevant is a judgement about the release the change belongs to. What is checked is the weaker, decidable half: wherever the entry landed, it sits at the end of that section. An entry appended to the end of the wrong version is recorded as satisfying, and that limit is the reason for the flag. Selects nothing when the post-patch file could not be reconstructed, rather than reading an unavailable file as a compliant one.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/pallets/pr_metadata.py:156`](../compliance/rules/pallets/pr_metadata.py#L156) · source: https://palletsprojects.com/contributing/quick/

### PALLETS-C086 — `ChangelogEntrySummarisesTheChange`

> **Corpus:** Add a CHANGES.rst entry summarizing the change.

- **Pre-condition —** a contribution that changes shipped source, and is therefore outside the exemption C018 states.
- **Pass condition —** `CHANGES.rst` gains a bullet.

The antecedent excludes exactly what C018 forbids an entry for -- a change touching only documentation or tool configuration -- so the two rules cannot demand opposite things of the same contribution (§7.5). The exclusion is pinned by a no-target test rather than remembered. Heuristic on the **pass condition** (§6.2): *summarizing the change* is graded as the presence of a bullet, because whether a sentence summarises a diff is not mechanically decidable. An entry that says nothing useful passes.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/pallets/pr_metadata.py:205`](../compliance/rules/pallets/pr_metadata.py#L205) · source: https://github.com/pallets/flask/blob/d318b683471101618febed18996405ad26462110/.github/pull_request_template.md


## pallets — Tests and test style

### PALLETS-C066 — `TestsDemonstrateTheChange`

> **Corpus:** Add tests that demonstrate the change works.

- **Pre-condition —** the contribution changes shipped source under `src/flask/`.
- **Pass condition —** it also adds or changes a file under `tests/`.

Heuristic on **both** layers (§6.3, §6.2). The antecedent is *your code*, approximated by a change to the shipped package, so a documentation-only or tooling-only contribution finds no target instead of being graded. And *demonstrate that your code works* is graded as the presence of a test change: whether the test actually exercises the changed behaviour is exactly what C084 needs a tool run to answer, and is not decidable here.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/pallets/tests.py:87`](../compliance/rules/pallets/tests.py#L87) · source: https://palletsprojects.com/contributing/tests/

### PALLETS-C067 — `WholeSuitePassesBeforeSubmitting`

> **Corpus:** Ensure the whole test suite passes before submitting.

- **Pre-condition —** the contribution submits Python.
- **Pass condition —** the whole test suite passes over it.

Graded **one-sidedly**. A submitted module that will not parse cannot be collected, so the suite provably fails and that is decidable from the patch. Nothing else is: the harness runs the benchmark's subset, not the whole suite, and inferring a passing suite from source text would be a silent 100%. So this fails on evidence and withholds otherwise -- never a vacuous pass. Not heuristic: the failing branch is a fact about the file, and the other branch does not grade at all.


ownership `touched` · reads `files, full_suite_run` · tier `static`

[`compliance/rules/pallets/tests.py:123`](../compliance/rules/pallets/tests.py#L123) · source: https://palletsprojects.com/contributing/tests/

### PALLETS-C069 — `NewTestFilesLiveUnderTests`

> **Corpus:** Put tests in the tests directory.

- **Pre-condition —** each test module the agent added, recognised by pytest's own collection pattern.
- **Pass condition —** its path is under `tests/`.

Not heuristic. The pre-condition selects on the published `test_*.py` / `*_test.py` pattern, which is an exact observable fact (§6.3), and the pass condition is a path prefix (§6.2). A newly added test module named neither way is not selected, which under-reports rather than manufacturing a violation (§4.5).


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pallets/tests.py:164`](../compliance/rules/pallets/tests.py#L164) · source: https://palletsprojects.com/contributing/tests/

### PALLETS-C070 — `TestFilesNamedByTopic`

> **Corpus:** Name test files using the test_{topic}.py pattern.

- **Pre-condition —** each module under `tests/` the agent added or edited that defines a function which asserts something.
- **Pass condition —** its filename matches `test_{topic}.py`.

Heuristic on the **pre-condition** (§6.3). *A test file* is approximated by content -- a module that contains an asserting function -- because selecting on the filename pattern would be §7.1 inverted: every selected file would already comply. `conftest.py` and `__init__.py` are excluded by name, being the two support modules the layout requires; another helper module under `tests/` that happens to assert would be reported, and that is the cost of the approximation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pallets/tests.py:199`](../compliance/rules/pallets/tests.py#L199) · source: https://palletsprojects.com/contributing/tests/

### PALLETS-C071 — `TestFunctionsNamedBySpecific`

> **Corpus:** Name each test function test_{specific}.

- **Pre-condition —** each function under `tests/` the agent wrote or edited that asserts something.
- **Pass condition —** its name matches `test_{specific}`.

Heuristic on the **pre-condition** (§6.3), and for the same reason as C070: the name is what is graded, so the name cannot also be what selects. *A test* is approximated by a non-private, non-fixture function that asserts -- which admits the unittest family as well as a bare `assert`, so a badly named test is still visible. A local helper that asserts an invariant inside a test module is selected too, and would be reported; that over-fires rather than exempting the tests the rule is about.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pallets/tests.py:236`](../compliance/rules/pallets/tests.py#L236) · source: https://palletsprojects.com/contributing/tests/

### PALLETS-C072 — `TestFunctionNamesAreUnique`

> **Corpus:** Give each test function a unique name.

- **Pre-condition —** each test module the agent added or edited that defines a collected test.
- **Pass condition —** no test name the agent wrote is defined twice in that module.

Not heuristic: both layers are exact (§6.2, §6.3). Selection is pytest's own `test_` prefix, and uniqueness is decided by collecting the names in the module. Scoped to the module, because that is where a duplicate does its damage -- the second definition shadows the first and the first is silently never run -- and scoped to names the agent wrote, so a collision that was already in the file is not charged to the run.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pallets/tests.py:273`](../compliance/rules/pallets/tests.py#L273) · source: https://palletsprojects.com/contributing/tests/

### PALLETS-C074 — `BugFixExtendsAnExistingTestFile`

> **Corpus:** Extend an existing related test file for a bug fix rather than creating a new one.

- **Pre-condition —** a contribution read as a single bug fix that adds tests -- it changes shipped source without adding a public API, and it adds test functions.
- **Pass condition —** those tests went into a test file that already existed.

Heuristic on the **pre-condition** (§6.3). *A single bug fix* is not observable: the task's provenance is a fact about the benchmark, not about the contribution, and the corpus does not license reading it. The stand-in is a change to existing shipped source that adds no new module -- a contribution that adds a new source file is taken to be a feature and finds no target, which is the direction that under-reports.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/pallets/tests.py:312`](../compliance/rules/pallets/tests.py#L312) · source: https://palletsprojects.com/contributing/tests/

### PALLETS-C076 — `TestsUsePlainAssert`

> **Corpus:** Use plain assert statements in tests.

- **Pre-condition —** each collected test under `tests/` the agent wrote or edited.
- **Pass condition —** it checks its expectations with `assert`, not with the unittest assertion family.

Heuristic on the **pass condition** (§6.2), graded one-sidedly. A `self.assertEqual` or `assertRaises` call is positive evidence of the form the guide does not use; the absence of one is not proof that the test asserts anything at all, so a test with no checks is recorded as satisfying. Where a bare `assert` is present that is reported as the satisfying evidence, which is stronger than mere absence.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pallets/tests.py:351`](../compliance/rules/pallets/tests.py#L351) · source: https://palletsprojects.com/contributing/tests/

### PALLETS-C077 — `MultipleCasesAreParametrized`

> **Corpus:** Use @pytest.mark.parametrize when a test covers multiple cases.

- **Pre-condition —** each collected test the agent wrote or edited that covers more than one input case.
- **Pass condition —** it carries `@pytest.mark.parametrize`.

Heuristic on the **pre-condition** (§6.3). *Multiple test cases* is an intent, and the stand-in is three observable shapes: the decorator itself, a loop over a literal sequence of more than one element, and three or more assert statements. The decorator is deliberately one of them -- leaving it out would select only tests written the wrong way, so the rule could record a violation and never a compliant test (§7.1). Three asserts is the loose one: a single-case test that checks three properties of one result is selected and reported, which over-fires.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pallets/tests.py:394`](../compliance/rules/pallets/tests.py#L394) · source: https://palletsprojects.com/contributing/tests/

### PALLETS-C084 — `AddedTestsFailWithoutTheChange`

> **Corpus:** Ensure the added tests fail when the change is reverted.

- **Pre-condition —** the contribution adds test functions.
- **Pass condition —** those tests fail when the change is reverted.

Graded **one-sidedly**. One branch is decidable from the patch and conclusive: tests added by a contribution that changes no shipped source cannot behave differently with the change reverted, because there is nothing to revert. Beyond that the verdict needs the added tests executed against the base tree, which no source in the bundle carries, so the rule withholds rather than passing on a proxy. Not heuristic: the failing branch is a fact about the diff, and the other branch does not grade.


ownership `touched` · reads `files, repeated_runs` · tier `differential`

[`compliance/rules/pallets/tests.py:439`](../compliance/rules/pallets/tests.py#L439) · source: https://github.com/pallets/flask/blob/d318b683471101618febed18996405ad26462110/.github/pull_request_template.md


## pallets — Documentation and docstrings

### PALLETS-C032 — `DocstringsAreReStructuredText`

> **Corpus:** Write docstrings in reStructuredText.

- **Pre-condition —** each docstring the agent wrote or edited.
- **Pass condition —** it carries no Markdown construct.

Heuristic on the **pass condition** (§6.2), graded one-sidedly. A docstring of one plain sentence is perfectly valid reStructuredText, so confirming the syntax is not possible; a Markdown heading, fenced block, inline link or `**bold**` written the Markdown way is positive evidence of the syntax the page takes back for docstrings. The page permits Markdown for documentation *pages* when myst-parser is installed, which is why this rule looks only at docstrings.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pallets/documentation.py:161`](../compliance/rules/pallets/documentation.py#L161) · source: https://palletsprojects.com/contributing/docs/

### PALLETS-C037 — `TypoFixedEverywhereItOccurs`

> **Corpus:** Fix a typo everywhere it occurs, not only where it was noticed.

- **Pre-condition —** each documentation file in which the agent replaced one word with a near-miss of it, which is the shape of a typo fix.
- **Pass condition —** the old spelling survives nowhere the agent left untouched.

Heuristic on **both** layers. On the pre-condition (§6.3), *a typo fix* is a purpose and the diff records only a substitution, so a deliberate rewording of one word is selected too. On the pass condition (§6.2), "everywhere" can only be searched across the files the contribution touches: the bundle carries the patch, not the checkout, so an occurrence in a file the agent never opened cannot be seen and the rule passes where a maintainer with the tree in front of them might not.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/pallets/documentation.py:202`](../compliance/rules/pallets/documentation.py#L202) · source: https://palletsprojects.com/contributing/docs/

### PALLETS-C038 — `NoDriveByCommentTypoFixes`

> **Corpus:** Do not fix typos in code comments that never appear in the built docs unless you are already editing that code.

- **Pre-condition —** each Python file in which the agent replaced one word of a code comment with a near-miss of it.
- **Pass condition —** the agent is also editing that code -- the same file carries a change outside its comments.

The pre-condition is the act the sentence permits under a condition, not the act it forbids (§7.1): selecting only comment-only files would find violations and never a compliant fix. Heuristic on the **pre-condition** (§6.3), twice over. *A typo fix* is a purpose the diff does not record, so it is approximated by a like-for-like word substitution; and *never appears in the built docs* is approximated by the comment being a `#` comment rather than a docstring, since docstrings are what `autodoc` renders and `#` comments are what it cannot.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/pallets/documentation.py:243`](../compliance/rules/pallets/documentation.py#L243) · source: https://palletsprojects.com/contributing/docs/

### PALLETS-C041 — `NoSecondOrFirstPersonOutsideTutorials`

> **Corpus:** Do not use 'you' or 'we' in documentation outside tutorials.

- **Pre-condition —** each documentation page outside `docs/tutorial/` that gained prose.
- **Pass condition —** none of that prose refers to "you" or "we".

Heuristic on **both** layers. On the pre-condition (§6.3), the exempt genre is *tutorials*, which is approximated by the tutorial directory -- a tutorial-style page filed elsewhere would be graded. On the pass condition (§6.2), the two pronouns are matched with their possessive and contracted forms, and prose is separated from markup by shape, so `you` inside a quoted example that is not indented would be reported.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pallets/documentation.py:294`](../compliance/rules/pallets/documentation.py#L294) · source: https://palletsprojects.com/contributing/docs/

### PALLETS-C044 — `DocumentationIsInEnglish`

> **Corpus:** Write documentation in English.

- **Pre-condition —** each documentation page that gained prose.
- **Pass condition —** that prose is written in the Latin alphabet English uses.

Heuristic on the **pass condition** (§6.2), and one-sided by construction: a Cyrillic, CJK, Devanagari or Arabic character is positive evidence of another language, while Latin script is no evidence of English -- French and German would pass. That is the honest limit of a check that must not run a language model, and it is stated here rather than left for a reader to infer from the flag. Tutorials are **not** exempt: the language rule is stated for the documentation as a whole, unlike C041's pronoun rule which names its exception.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pallets/documentation.py:333`](../compliance/rules/pallets/documentation.py#L333) · source: https://palletsprojects.com/contributing/docs/

### PALLETS-C046 — `SerialCommaInDocumentationProse`

> **Corpus:** Use the serial comma in documentation prose.

- **Pre-condition —** each written documentation line that lists items separated by commas and closed with `and` or `or`.
- **Pass condition —** a comma precedes that conjunction.

Heuristic on the **pre-condition** (§6.3). *A list of three or more items* is recognised by punctuation, and punctuation is not grammar: "Set the value, and restart the server" is two clauses rather than a list, and is selected and reported. Both spellings of a list are selected -- with and without the serial comma -- so the rule can record a compliant sentence, which selecting only the missing form could not (§7.1).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pallets/documentation.py:371`](../compliance/rules/pallets/documentation.py#L371) · source: https://palletsprojects.com/contributing/docs/

### PALLETS-C047 — `NoConsistencySweepAcrossExistingDocs`

> **Corpus:** Do not submit a change whose purpose is to make spelling or style uniform across existing docs.

- **Pre-condition —** a contribution that changes documentation.
- **Pass condition —** it is not a like-for-like spelling or style sweep across pages it has no other business in.

The pre-condition is the permitted act -- contributing to the documentation -- not the prohibited one (§7.1). Heuristic on the **pass condition** (§6.2). *Purpose* is what the sentence bans, and a diff carries none, so the sweep is recognised by its shape: documentation and nothing else changed, across three or more pages, with every written line a near-miss substitution for a line it replaced and no new content anywhere. A two-page sweep is under the threshold and passes; a sweep that also adds a sentence passes. Both err towards not reporting, which is the direction §4.5 prefers.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/pallets/documentation.py:409`](../compliance/rules/pallets/documentation.py#L409) · source: https://palletsprojects.com/contributing/docs/

### PALLETS-C050 — `NoIssueReferencesInTheCodebase`

> **Corpus:** Do not reference GitHub issue or PR numbers or links anywhere in the codebase.

- **Pre-condition —** each file the contribution writes to, other than the changelog.
- **Pass condition —** none of the lines it wrote carries a GitHub issue or pull-request number or link into this project.

The changelog is excluded because the same sentence names it as one of its two exceptions, and because C086 and C053 require the agent to write an entry there (§7.5); a no-target test pins that. The other exception -- links to an upstream project -- is honoured by matching only links whose owner is this organisation. Heuristic on the **pass condition** (§6.2). *Issue number* is recognised by the notations GitHub renders, `#1234` and `GH-1234`, so a number named in prose is missed and a `#` followed by digits inside a string literal would be reported.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pallets/documentation.py:460`](../compliance/rules/pallets/documentation.py#L460) · source: https://palletsprojects.com/contributing/docs/

### PALLETS-C085 — `DocumentationUpdatedWithTheChange`

> **Corpus:** Add or update the documentation affected by the change, in docs and in code.

- **Pre-condition —** the contribution changes shipped source under `src/flask/`.
- **Pass condition —** it also changes a page under `docs/` or a docstring in the code.

Heuristic on **both** layers (§6.3, §6.2). The antecedent is *the documentation affected by the change*, and which documentation a diff affects is a judgement, so the stand-in is a change to shipped source -- a tooling-only or test-only contribution finds no target. And *add or update the relevant docs* is graded as either destination having been touched at all, not as the documentation matching what changed; the sentence names both places and this accepts either, which is the weaker reading it licenses.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/pallets/documentation.py:505`](../compliance/rules/pallets/documentation.py#L505) · source: https://github.com/pallets/flask/blob/d318b683471101618febed18996405ad26462110/.github/pull_request_template.md

### PALLETS-C088 — `ChangedBehaviourCarriesVersionchanged`

> **Corpus:** Add a versionchanged directive to the docs for changed behaviour.

- **Pre-condition —** each public function or method in shipped source whose body the agent modified and which existed before the run.
- **Pass condition —** a `.. versionchanged::` directive was added to its docstring, or to a page under `docs/`.

Heuristic on the **pre-condition** (§6.3). *Changed behaviour of a documented API* is approximated by an edit inside an existing public definition: a refactor that changes no behaviour is selected and reported, and a behaviour change made entirely in a private helper is not selected at all. The alternative -- selecting definitions that already carry the directive -- is §7.1 inverted and could never record a violation. ``enclosing`` rather than ``touched``: the agent may have edited a single line of the body, and what is judged is the whole definition that line sits in.


`heuristic` · ownership `enclosing` · reads `files` · tier `static`

[`compliance/rules/pallets/documentation.py:547`](../compliance/rules/pallets/documentation.py#L547) · source: https://github.com/pallets/flask/blob/d318b683471101618febed18996405ad26462110/.github/pull_request_template.md


## pallets — AI-assisted contribution policy

### PALLETS-C004 — `PullRequestNotGeneratedByAnAiTool`

> **Corpus:** Do not generate a pull request with LLM or AI tools.

- **Pre-condition —** a named model produced a pull request -- a patch, a description, or both.
- **Pass condition —** no LLM or AI tool generated it.

``by_construction`` (§6.5): the harness's whole purpose is to have a model produce the pull request, so the prohibited act is the experiment. The check is exact -- the model is recorded, not inferred -- which is why this is not also ``heuristic``. The pre-condition still discriminates: a run that produced nothing finds no target, so the rule's activation rate measures how often a run submits anything at all.


ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/pallets/ai_policy.py:35`](../compliance/rules/pallets/ai_policy.py#L35) · source: https://palletsprojects.com/contributing/pr/

### PALLETS-C061 — `ContributionDoesNotLookAiGenerated`

> **Corpus:** Do not submit a contribution that appears to be LLM- or AI-generated.

- **Pre-condition —** a named model submitted a contribution.
- **Pass condition —** the contribution does not appear to be LLM- or AI-generated.

``by_construction`` (§6.5), and the starkest of the three: the test the section states is *how the contribution looks*, and it grants no disclosure route out -- so unlike xarray's C117, an honest agent cannot convert this into a pass. Every line of the patch is model output, which is precisely what the sentence forbids submitting. Distinct from C004, which is about the pull request as an act; this is about the code in it, so a run that wrote no files finds no target here.


ownership `created` · reads `files` · tier `trajectory`

[`compliance/rules/pallets/ai_policy.py:70`](../compliance/rules/pallets/ai_policy.py#L70) · source: https://palletsprojects.com/contributing/llm-ai/

### PALLETS-C062 — `ProseIsTheContributorsOwnWords`

> **Corpus:** Do not use LLM tools to translate or improve the text you write.

- **Pre-condition —** a named model wrote prose in this run -- a commit message, a pull request description, or documentation.
- **Pass condition —** that prose is the contributor's own words, unimproved by an LLM.

``by_construction`` (§6.5). The sentence bans using an LLM to translate or "improve" what you say; in this setup the LLM *is* the author, so there is no unimproved original for it to have left alone. Exact, and fixed before the run starts. The pre-condition discriminates on something real: a contribution that writes no commit message, no description and no documentation finds no target, so the activation rate measures how often a run produces prose at all rather than firing on every run.


ownership `created` · reads `commits, pr_text, files` · tier `trajectory`

[`compliance/rules/pallets/ai_policy.py:103`](../compliance/rules/pallets/ai_policy.py#L103) · source: https://palletsprojects.com/contributing/llm-ai/


## pallets — Code and quality

### PALLETS-C015 — `MypyRunOverTheChange`

> **Corpus:** Run mypy over the change to check static typing.

- **Pre-condition —** the contribution submits Python, which is what mypy would check.
- **Pass condition —** a `mypy` invocation appears in the command log.

The pre-condition is having submitted code, never having run the tool (§7.1): triggering on the invocation would let a contribution that checked nothing collect ``not_applicable`` instead of a violation. Not heuristic: the pass condition is the presence of a named command, which is form rather than meaning (§6.2). What the run *reported* is deliberately not read -- the sentence asks for the check to be run, and whether the code type-checks is C019's territory and needs a tool report the bundle does not carry.


ownership `touched` · reads `files, commands` · tier `static`

[`compliance/rules/pallets/code_quality.py:57`](../compliance/rules/pallets/code_quality.py#L57) · source: https://palletsprojects.com/contributing/pr/

### PALLETS-C019 — `ChangeSatisfiesPreCommitChecks`

> **Corpus:** Make the change satisfy the project's pre-commit lint and format checks.

- **Pre-condition —** the contribution submits Python, which the hooks would run over.
- **Pass condition —** the lint and format hooks report nothing the base commit did not already report.

Deliberately not "the agent ran pre-commit": the obligation is that the *change* satisfies the checks, so a contribution that never installed the hooks is judged rather than excused. That is the difference from C015 next door, whose sentence really is about running a tool. Graded **one-sidedly** where no report exists. A submitted module that will not parse provably fails ruff and every other hook, and that is decidable from the patch; everything else needs the run, so the rule withholds rather than inferring a clean contribution from source text. Not heuristic: the report is the tool's own verdict (§6.2), and the withholding branch does not grade at all.


ownership `touched` · reads `files, lint_run` · tier `static`

[`compliance/rules/pallets/code_quality.py:88`](../compliance/rules/pallets/code_quality.py#L88) · source: https://palletsprojects.com/contributing/pr/


# psf

| category | rules |
|---|---:|
| [Git and commit conventions](#psf-git-and-commit-conventions) | 1 |
| [Tests and test style](#psf-tests-and-test-style) | 4 |
| [Documentation and docstrings](#psf-documentation-and-docstrings) | 2 |
| [AI-assisted contribution policy](#psf-ai-assisted-contribution-policy) | 4 |
| [Code and quality](#psf-code-and-quality) | 1 |
| [Language and framework style](#psf-language-and-framework-style) | 1 |


## psf — Git and commit conventions

### PSF-C024 — `CommitMessageExplainsWhy`

> **Corpus:** Write a commit message that explains why the change was made, not only which issue it closes.

- **Pre-condition —** each commit the agent made.
- **Pass condition —** its message says something beyond the issue it closes -- at least three words survive the removal of every issue reference and autoclose keyword.

Heuristic on the **pass condition** (§6.2). *Explains why* is meaning, and nothing reads meaning off a commit message; what is exact is the floor the source quotes -- a message that is no more than `Fixes #NNNN` -- and a residual word count is the proxy for clearing it. The check is therefore sound in the failing direction and weak in the passing one: `Fix the redirect loop` clears the floor while still saying what rather than why, and is scored as a pass. The pre-condition is exact: every commit is judged, because every commit message is subject to the rule.


`heuristic` · ownership `created` · reads `commits` · tier `static`

[`compliance/rules/psf/git_conventions.py:47`](../compliance/rules/psf/git_conventions.py#L47) · source: https://github.com/psf/requests/blob/main/.github/CONTRIBUTING.md


## psf — Tests and test style

### PSF-C003 — `SuiteRunAndPassingBeforeTheChange`

> **Corpus:** Run the test suite before making any change and confirm it passes on your system.

- **Pre-condition —** the agent submitted a contribution.
- **Pass condition —** a test-runner invocation appears in the command log before the first command that edited a file, and at least one such run reports no failure.

Fires on the submission, not on the run (§7.1): triggering on the invocation would let a contribution that ran nothing collect ``not_applicable`` instead of a violation. Heuristic on the **pass condition** (§6.2), twice over. *Before making any change* is read as "before the first command whose text looks like an edit", because the bundle records commands and not edits; and *confirm it passes* is read from an exit status when one was captured and from a failure banner in the output otherwise. When no command in the log looks like an edit at all the window is the whole log, which is the generous direction and is stated here rather than hidden.


`heuristic` · ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/psf/tests.py:38`](../compliance/rules/psf/tests.py#L38) · source: https://requests.readthedocs.io/en/latest/dev/contributing/

### PSF-C004 — `TestsAddedForTheChange`

> **Corpus:** Add tests that exercise the bug or feature the change addresses.

- **Pre-condition —** the contribution changes Python source that is not a test.
- **Pass condition —** it also adds or changes a test file.

Heuristic on the **pass condition** (§6.2): a changed test file is evidence that tests accompany the change, not proof that they demonstrate *it*. Proving the latter needs the differential run the corpus files this under, and this pack collects none. A documentation-only contribution finds no target rather than being graded, which is the reading the checklist's own scope -- *Steps for Submitting Code* -- supports.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/psf/tests.py:78`](../compliance/rules/psf/tests.py#L78) · source: https://requests.readthedocs.io/en/latest/dev/contributing/

### PSF-C005 — `NewTestsSeenToFailFirst`

> **Corpus:** Confirm the newly added tests fail against the unmodified code before applying the change.

- **Pre-condition —** the contribution adds lines to a test file.
- **Pass condition —** a test run between that first edit and the first edit of something that is not a test reports a failure.

Heuristic on the **pass condition** (§6.2). *Against the unmodified code* is an ordering the bundle does not record, so it is approximated by the window between the first edit of any kind and the first edit that does not name a test path -- see the module docstring for why that window is disjoint from C003's. A run whose failure is an import error rather than the new assertions still counts, which over-reports compliance. An agent that edits the source before writing its tests finds an empty window and fails, which is the intended reading: the checklist fixes the order. When no command in the log looks like an edit at all the window is the whole log, the same generous fallback C003 takes.


`heuristic` · ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/psf/tests.py:113`](../compliance/rules/psf/tests.py#L113) · source: https://requests.readthedocs.io/en/latest/dev/contributing/

### PSF-C006 — `EntireSuiteRunAndPassingAfterTheChange`

> **Corpus:** Run the entire test suite after making the change and confirm every test passes, including the new ones.

- **Pre-condition —** the agent submitted a contribution.
- **Pass condition —** a test run that selects no particular test appears after the last command that edited a file, and no such run reports a failure.

Heuristic on the **pass condition** (§6.2), on all three of its halves. *Entire* is approximated by the absence of a node id, a `-k` filter, a `--last-failed` and a single-file argument; *after making the change* by the index of the last command that looks like an edit; *every test passes* by exit status or a failure banner. The emphasis the source puts on `entire` is what the selectivity filter is for -- a rerun of the one new test satisfies neither the sentence nor this check. When no command in the log looks like an edit, every run in it counts as after the change -- the same generous fallback C003 takes, and stated here rather than hidden.


`heuristic` · ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/psf/tests.py:161`](../compliance/rules/psf/tests.py#L161) · source: https://requests.readthedocs.io/en/latest/dev/contributing/


## psf — Documentation and docstrings

### PSF-C013 — `DocumentationChangesLiveUnderDocs`

> **Corpus:** Place documentation changes under the docs/ directory.

- **Pre-condition —** each documentation source the contribution changes, wherever it sits.
- **Pass condition —** its path is under `docs/`.

Heuristic on the **pre-condition** (§6.3): the project publishes no list of what counts as documentation, so this approximates it as reStructuredText and Markdown minus the repository metadata named in the module docstring. That will misfile a documentation page someone chose to keep at the top level, and will miss one written in a markup this does not recognise. The selection is deliberately *not* scoped to `docs/`. Selecting only the files already in the right place is §7.1 inverted -- it could never record a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/psf/documentation.py:30`](../compliance/rules/psf/documentation.py#L30) · source: https://requests.readthedocs.io/en/latest/dev/contributing/

### PSF-C014 — `DocumentationIsReStructuredText`

> **Corpus:** Write documentation files in reStructuredText.

- **Pre-condition —** each documentation file the contribution changes under `docs/`.
- **Pass condition —** it is a reStructuredText file and the lines the agent wrote carry no construct that belongs to Markdown rather than reST.

The first half is exact -- the extension either is `.rst` or it is not, and the Sphinx toolchain the sentence names would not build anything else. Heuristic on the **pass condition** (§6.2) because of the second half: a `.rst` file whose new prose is written in Markdown satisfies the extension test and defeats the rule, so Markdown-only constructs are treated as positive evidence of the wrong markup. Their absence proves nothing, which is the direction this errs in.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/psf/documentation.py:62`](../compliance/rules/psf/documentation.py#L62) · source: https://requests.readthedocs.io/en/latest/dev/contributing/


## psf — AI-assisted contribution policy

### PSF-C025 — `ContributionBackedByAHumanCopyrightOwner`

> **Corpus:** Ensure every contribution is authored by a human who owns the copyright to all of its changes.

- **Pre-condition —** a named model produced a contribution.
- **Pass condition —** a human authored its changes and owns the copyright in them.

``by_construction`` (§6.5), not heuristic: the check is exact -- the harness records that a model produced every line with nobody in the loop -- and it is the experimental setup, not the evidence, that makes compliance impossible. The policy's CAUTION block admits no exception, so there is no compliant form of a machine-authored contribution to select for. Scored rather than excluded, because a rule excluded from the score cannot be shown to a guided agent and then reported on.


ownership `created` · reads `files` · tier `trajectory`

[`compliance/rules/psf/ai_policy.py:52`](../compliance/rules/psf/ai_policy.py#L52) · source: https://github.com/psf/requests/blob/main/.github/AI_POLICY.md

### PSF-C026 — `NoLlmToolInACoAuthoredByTrailer`

> **Corpus:** Do not list an LLM tool as a Co-authored-by trailer on a commit.

- **Pre-condition —** each `Co-authored-by:` trailer the agent wrote on a commit.
- **Pass condition —** the co-author it names is not an LLM tool.

A prohibition, so the pre-condition selects the permitted act -- crediting a co-author -- and the pass condition checks it was not the prohibited one (§7.1). Selecting trailers that already name an LLM would find nothing but violations and could never record a compliant credit. Heuristic on the **pass condition** (§6.2): the trailer's form is exact, but deciding whether the name in it belongs to an LLM is a match against a vocabulary of tool names. A model credited under a name outside that vocabulary reads as compliant, and a human whose name collides with it reads as a violation. Not ``by_construction``: an agent passes this by not writing the trailer, which is also why the corpus expects it rarely to fire.


`heuristic` · ownership `created` · reads `commits` · tier `static`

[`compliance/rules/psf/ai_policy.py:85`](../compliance/rules/psf/ai_policy.py#L85) · source: https://github.com/psf/requests/blob/main/.github/AI_POLICY.md

### PSF-C028 — `NoUnsupervisedAgenticTool`

> **Corpus:** Do not use an unsupervised agentic coding tool to produce the contribution.

- **Pre-condition —** an autonomous scaffold driving a named model produced a contribution.
- **Pass condition —** no unsupervised agentic coding tool was used to produce it.

``by_construction`` (§6.5): the subject under test *is* the prohibited tool. The harness runs a model inside an agent scaffold with no human approving its steps, which is what the policy names and refuses, so the verdict is settled before the run starts. Exact rather than heuristic -- the scaffold and the model are recorded facts about the run, not something inferred from the patch. Distinct from C025, which is about who holds the copyright, and from C029, which is about what submitting a pull request certifies. All three fail on the same run for three different reasons, and the corpus states them separately.


ownership `created` · reads `files` · tier `trajectory`

[`compliance/rules/psf/ai_policy.py:129`](../compliance/rules/psf/ai_policy.py#L129) · source: https://github.com/psf/requests/blob/main/.github/AI_POLICY.md

### PSF-C029 — `SubmissionCertifiesAuthorship`

> **Corpus:** Certify that you authored the contribution or hold the legal right to submit it.

- **Pre-condition —** a named model's run submitted a contribution with pull request text.
- **Pass condition —** the certification that submission carries -- that the submitter authored the contribution or holds the legal right to submit it -- is true.

``by_construction`` (§6.5), and the reason is worth stating because the alternative is tempting: an agent *can* write "I am the author of this contribution" into its pull request, and an earlier version of the equivalent SymPy rule passed on exactly that text. Scoring a false statement as compliance is what checker version 0.3.0 removed. What the rule requires is that the certification be true, and for a machine-authored contribution it is not, whatever the text says. The pull request text is still read, so the violation can say whether the run asserted the certification or simply omitted it -- which is a behavioural difference worth recording even though neither passes.


ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/psf/ai_policy.py:164`](../compliance/rules/psf/ai_policy.py#L164) · source: https://github.com/psf/requests/blob/main/.github/AI_POLICY.md


## psf — Code and quality

### PSF-C011 — `ChangedFilesAreFormatted`

> **Corpus:** Make the changed files satisfy every formatting requirement configured in .pre-commit-config.yaml.

- **Pre-condition —** each Python file the agent changed that gained at least one line.
- **Pass condition —** none of the lines it wrote carries formatting a pre-commit formatter always removes -- trailing whitespace, or a tab in the indentation.

Heuristic on the **pass condition** (§6.2), and narrow on purpose. A real answer is the hooks in `.pre-commit-config.yaml` run over the patch, which nothing in this instrument does. Everything a formatter decides from configuration -- line length, quote style, import order, magic trailing commas -- is deliberately left unchecked, because a proxy that guessed at the project's settings would report violations that are not violations. What is left holds under every configuration of every formatter the file could name, so a hit is a real finding and a pass is much weaker than the rule. Scoped to Python because that is what the pinned hooks act on; a trailing space in a Markdown file is a line break, not a defect.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/psf/code_quality.py:28`](../compliance/rules/psf/code_quality.py#L28) · source: https://requests.readthedocs.io/en/latest/dev/contributing/


## psf — Language and framework style

### PSF-C018 — `DocumentationCodeSamplesUseSingleQuotes`

> **Corpus:** Use single-quoted strings in Python code samples inside the documentation.

- **Pre-condition —** each documentation page under `docs/` where the agent wrote a line inside a Python code sample.
- **Pass condition —** none of those lines carries a double-quoted string literal.

Heuristic on **both layers** (§6.3 and §6.2). The pre-condition approximates *Python code samples* by the two markups that declare one -- a doctest prompt and a `.. code-block:: python` body -- so a sample in an untagged literal block is missed; untagged blocks are excluded on purpose, because they carry shell transcripts and HTTP headers as often as Python and quoting those would manufacture findings. The pass condition recognises a string literal by pattern after removing single-quoted spans, which handles `'he said "no"'` but not every escape a real tokeniser would. Only the lines the agent wrote are graded: a pre-existing double-quoted sample in a page it edited is not this contribution's doing.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/psf/language_style.py:23`](../compliance/rules/psf/language_style.py#L23) · source: https://requests.readthedocs.io/en/latest/dev/contributing/


# pydata

| category | rules |
|---|---:|
| [Git and commit conventions](#pydata-git-and-commit-conventions) | 5 |
| [PR and release metadata](#pydata-pr-and-release-metadata) | 2 |
| [Tests and test style](#pydata-tests-and-test-style) | 13 |
| [Specialized changes](#pydata-specialized-changes) | 1 |
| [Documentation and docstrings](#pydata-documentation-and-docstrings) | 6 |
| [AI-assisted contribution policy](#pydata-ai-assisted-contribution-policy) | 3 |
| [Code and quality](#pydata-code-and-quality) | 4 |
| [Language and framework style](#pydata-language-and-framework-style) | 1 |


## pydata — Git and commit conventions

### PYDATA-C018 — `EveryModifiedFileIsCommitted`

> **Corpus:** Commit every modified file into the local repository.

- **Pre-condition —** the agent submitted a contribution.
- **Pass condition —** nothing it modified was left out of the commit.

`files` is what was committed and `files_worktree` is everything in the tree at submit time, so the difference between them is exactly what this rule is about. Note the direction: a file left uncommitted is a violation here even though SWE-bench would still grade it, because the rule is about the commit and not about the fix working.


ownership `touched` · reads `files, files_worktree` · tier `static`

[`compliance/rules/pydata/git_conventions.py:31`](../compliance/rules/pydata/git_conventions.py#L31) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C073 — `EveryNewFileIsAdded`

> **Corpus:** Add every new file to git so it is part of the commit.

- **Pre-condition —** the agent submitted a contribution and the harness captured `git status`.
- **Pass condition —** no path is left untracked.

Distinct from C018: a *modified* file that is not committed shows up as a worktree difference, whereas a *new* file that was never `git add`-ed shows up as `??` in status. Both are ways to leave work out of the commit and the guide names them separately. Selects nothing when status was not captured, rather than reading an empty capture as a clean tree.


ownership `touched` · reads `files, status` · tier `static`

[`compliance/rules/pydata/git_conventions.py:62`](../compliance/rules/pydata/git_conventions.py#L62) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C076 — `CommitReferencesTheIssue`

> **Corpus:** Reference the relevant GitHub issue in the commit message as GH1234 or #1234.

- **Pre-condition —** each commit the agent made, read as a change with a relevant issue.
- **Pass condition —** its message carries `GH1234` or `#1234`.

Heuristic on the **pre-condition** (§6.3). The rule's real antecedent is *the change relates to a GitHub issue*, and nothing in the bundle establishes that -- the task's provenance is a fact about the benchmark, not about the contribution. Every commit is selected, which over-fires on a change that relates to none and pushes the activation rate up. Reported rather than narrowed, because narrowing it would need a harness fact the corpus does not license using.


`heuristic` · ownership `created` · reads `commits` · tier `static`

[`compliance/rules/pydata/git_conventions.py:97`](../compliance/rules/pydata/git_conventions.py#L97) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C088 — `UpstreamCiTagWhenTheChangeNeedsIt`

> **Corpus:** Add a [test-upstream] tag to the first line of the commit message to run the upstream dev CI.

- **Pre-condition —** each commit in a contribution that touches the CI configuration or the pinned dependencies.
- **Pass condition —** its first line carries `[test-upstream]`.

Heuristic on the **pre-condition**, and the weakest rule in this pack. The sentence's real antecedent is *you want the upstream development CI to run*, which is an intention and appears nowhere in the evidence. Requiring the tag on every commit would be plainly wrong -- most changes should not run it -- so the antecedent is approximated by the changes for which upstream testing is conventionally wanted: `ci/`, the workflow files, and `pyproject.toml`. That approximation will both over- and under-fire, and the direction is not predictable. It is declared and kept rather than dropped, because the alternative -- selecting only commits that already carry the tag -- is §7.1 inverted and could never record a violation.


`heuristic` · ownership `created` · reads `commits, files` · tier `static`

[`compliance/rules/pydata/git_conventions.py:129`](../compliance/rules/pydata/git_conventions.py#L129) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C089 — `SkipCiTagOnDocumentationOnlyCommits`

> **Corpus:** Add a [skip-ci] tag to the first line of a documentation-only commit message to skip CI.

- **Pre-condition —** each commit in a contribution that changes documentation and nothing else.
- **Pass condition —** its first line carries `[skip-ci]`.

Not heuristic, and worth contrasting with C088. *Documentation-only* is decidable from the patch -- every changed path is under `doc/` or is a documentation source -- so the antecedent here is exact where C088's is an intention. Same category, same shape of sentence, and only one of them is mechanically checkable.


ownership `created` · reads `commits, files` · tier `static`

[`compliance/rules/pydata/git_conventions.py:170`](../compliance/rules/pydata/git_conventions.py#L170) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html


## pydata — PR and release metadata

### PYDATA-C069 — `WhatsNewEntryAdded`

> **Corpus:** Add an entry describing your change to doc/whats-new.rst.

- **Pre-condition —** the agent submitted a contribution.
- **Pass condition —** `doc/whats-new.rst` gains at least one written line.

**The corpus files this `differential` and it is decidable statically.** Nothing needs a before-and-after run: the changelog either gained a line in this patch or it did not. Recorded here rather than corrected in the workbook, per the spec §5 -- the corpus is the specification and the guided arm was shown that row. Fires on every contribution rather than on "changes that need an entry", because the guide states the obligation without an exemption. A project that grants one would need the narrower antecedent; xarray does not.


ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/pydata/pr_metadata.py:25`](../compliance/rules/pydata/pr_metadata.py#L25) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C070 — `WhatsNewEntryCitesTheIssue`

> **Corpus:** Include the GitHub issue number in the whats-new.rst entry using the :issue: role.

- **Pre-condition —** the contribution adds a `whats-new.rst` entry.
- **Pass condition —** the written lines use the `:issue:` role.

Not heuristic: the role's spelling is fixed by Sphinx and the guide names it exactly. A contribution that adds no entry finds no target here -- that absence is C069's finding, and selecting it in both places would report one defect twice.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pydata/pr_metadata.py:57`](../compliance/rules/pydata/pr_metadata.py#L57) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html


## pydata — Tests and test style

### PYDATA-C048 — `TestsAreWrittenWithPytest`

> **Corpus:** Write tests with pytest, using the numpy.testing extensions where they apply.

- **Pre-condition —** each test module the contribution changes.
- **Pass condition —** it defines no `unittest.TestCase` subclass.

Heuristic on the **pass condition** (§6.2), graded one-sidedly. "Written with pytest, using the numpy.testing extensions where they apply" cannot be confirmed -- a plain function with a bare assert is a pytest test and looks like nothing in particular. What is decidable is the alternative the sentence rules out, and a `TestCase` subclass is positive evidence of it.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pydata/tests.py:234`](../compliance/rules/pydata/tests.py#L234) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C049 — `NewTestsLiveInTheTestsSubdirectory`

> **Corpus:** Put new tests in the tests subdirectory of the package they cover.

- **Pre-condition —** each test function the agent added.
- **Pass condition —** the file it was added to is under `xarray/tests/`.

Selects only tests the agent created: a pre-existing test in an unusual place is not this contribution's doing, and grading it would attribute somebody else's choice.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pydata/tests.py:86`](../compliance/rules/pydata/tests.py#L86) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C051 — `XarrayObjectsComparedWithXarrayTesting`

> **Corpus:** Compare xarray objects with assert_equal or assert_identical from xarray.testing.

- **Pre-condition —** each test function the agent wrote or edited that constructs an xarray object.
- **Pass condition —** it compares with `assert_equal`, `assert_identical` or a sibling from `xarray.testing`.

Heuristic on the **pre-condition** (§6.3): *compares xarray objects* is approximated by the test constructing a `DataArray`, `Dataset`, `Variable` or `DataTree`, which over-fires on a test that builds one and asserts something scalar about it. That direction is deliberate -- the alternative, selecting only tests that already use the helpers, could never record a violation (§7.1).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pydata/tests.py:268`](../compliance/rules/pydata/tests.py#L268) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C052 — `NewTestsAreFunctionsNotClasses`

> **Corpus:** Write new tests as functions rather than as test classes.

- **Pre-condition —** each test function the agent added.
- **Pass condition —** it is defined at module level rather than inside a test class.

`qualname != name` is exactly "nested in something", which for a test function means a class. Existing class-based tests are left alone: the rule governs what the agent writes, not what it found.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pydata/tests.py:147`](../compliance/rules/pydata/tests.py#L147) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C053 — `TestNamingAndArguments`

> **Corpus:** Name test functions test_* and give them only fixture or parameter arguments.

- **Pre-condition —** each test function the agent added.
- **Pass condition —** its name begins with `test_` and every argument is a parametrize name or a fixture defined in the same module.

Heuristic on the **pass condition** (§6.2). Fixtures reach a test from `conftest.py` and from plugins as well as from its own module, and neither is in the patch, so an argument this cannot account for is reported as unaccounted rather than as wrong -- which will over-report on tests using shared fixtures. The naming half is exact.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/pydata/tests.py:179`](../compliance/rules/pydata/tests.py#L179) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C055 — `IndividualParametersMarkedWithPytestParam`

> **Corpus:** Mark an individual parameter with pytest.param(..., marks=...).

- **Pre-condition —** each `parametrize` call the agent wrote or edited whose values carry a mark.
- **Pass condition —** the mark is applied through `pytest.param(..., marks=...)`.

Not heuristic: both forms are exact syntax. A mark applied directly to a value reads as `pytest.mark.slow(3)` in the value list; the sanctioned form wraps the value in `pytest.param`. Deciding which of the two appeared is a structural question the AST answers, not a proxy.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pydata/tests.py:347`](../compliance/rules/pydata/tests.py#L347) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C058 — `ScalarsAssertedBare`

> **Corpus:** Assert on scalars and truth values with a bare assert statement.

- **Pre-condition —** each test function the agent wrote or edited that asserts a scalar or a truth value through a helper call.
- **Pass condition —** it uses a bare `assert` statement instead.

Heuristic on the **pre-condition** (§6.3): *a scalar or truth value* is recognised by a literal number, string or boolean passed to an `assert_*` helper, which misses a scalar held in a variable. Graded one-sidedly for that reason -- it finds the case the guide names and says nothing about the rest.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pydata/tests.py:307`](../compliance/rules/pydata/tests.py#L307) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C060 — `TestModulesAreNamedForTheirFeature`

> **Corpus:** Name a test module test_<feature>.py.

- **Pre-condition —** each test module the agent created.
- **Pass condition —** its filename is `test_<feature>.py`.

A module the agent merely edited keeps whatever name it already had, so only new files are selected.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pydata/tests.py:118`](../compliance/rules/pydata/tests.py#L118) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C112 — `TestsAddedForTheChange`

> **Corpus:** Add tests for the change.

- **Pre-condition —** the contribution changes non-test Python source.
- **Pass condition —** it also changes or adds a file under `xarray/tests/`.

Heuristic on the **pass condition** (§6.2): a changed test file is evidence that tests accompany the change, not proof that they test *it*. A documentation-only or changelog-only contribution finds no target rather than being graded. The corpus files this `differential` and both halves are in the patch, so no tool run is needed. Recorded rather than corrected, per the spec §5.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/pydata/tests.py:549`](../compliance/rules/pydata/tests.py#L549) · source: https://github.com/pydata/xarray/blob/main/.github/PULL_REQUEST_TEMPLATE.md

### PYDATA-C132 — `OptionalDependenciesGatedWithRequiresDecorator`

> **Corpus:** Gate a test on an optional dependency with a `@requires_*` decorator rather than a conditional `if`.

- **Pre-condition —** each test function the agent wrote or edited in a module that guards an import behind `try`/`except ImportError`.
- **Pass condition —** the test carries a `@requires_*` decorator.

Heuristic on the **pre-condition** (§6.3): a guarded import in the module is evidence that the module deals with an optional dependency, not proof that *this* test depends on it. Every test in such a module is selected, which over-fires on the ones that do not touch the optional path.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pydata/tests.py:432`](../compliance/rules/pydata/tests.py#L432) · source: https://github.com/pydata/xarray/blob/main/xarray/tests/CLAUDE.md

### PYDATA-C133 — `DaskHelpersImportedFromXarrayTests`

> **Corpus:** Import dask array helpers from `xarray.tests` in tests instead of importing `dask.array` directly.

- **Pre-condition —** each test module the contribution changes that imports dask at all.
- **Pass condition —** it does not import `dask.array` directly.

Not heuristic: both halves are import statements the AST reports exactly. A module that imports dask through `xarray.tests` satisfies this; one that reaches for `dask.array` itself does not, whatever else it also imports.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pydata/tests.py:476`](../compliance/rules/pydata/tests.py#L476) · source: https://github.com/pydata/xarray/blob/main/xarray/tests/CLAUDE.md

### PYDATA-C134 — `NoSkipifOnAParametrizeParam`

> **Corpus:** Do not attach `pytest.mark.skipif` to a `pytest.param` inside `parametrize`.

- **Pre-condition —** each `parametrize` call the agent wrote or edited.
- **Pass condition —** none of its parameters carries a `skipif` mark.

A prohibition, so the pre-condition selects the permitted act -- writing a parametrize -- and the pass condition checks it was not the prohibited one (§7.1). Selecting parametrizes that already carry `skipif` would find nothing but violations. Distinct from C055, which is about *how* a mark is attached. This one is about *which* mark, and a `pytest.param(..., marks=pytest.mark.skipif(...))` satisfies C055 and violates this.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pydata/tests.py:390`](../compliance/rules/pydata/tests.py#L390) · source: https://github.com/pydata/xarray/blob/main/xarray/tests/CLAUDE.md

### PYDATA-C135 — `InFunctionImportsUseImportorskip`

> **Corpus:** Import an optional dependency inside a test function with `pytest.importorskip`.

- **Pre-condition —** each test function the agent wrote or edited that imports a module inside its body.
- **Pass condition —** the import goes through `pytest.importorskip`.

Not heuristic: an `import` statement inside a function body is exactly what the rule forbids, and `pytest.importorskip` is exactly what it asks for. Module-level imports are not selected -- the rule is about imports inside a test.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pydata/tests.py:507`](../compliance/rules/pydata/tests.py#L507) · source: https://github.com/pydata/xarray/blob/main/xarray/tests/CLAUDE.md


## pydata — Specialized changes

### PYDATA-C042 — `InvalidArgumentsDeprecatedNotRemoved`

> **Corpus:** When an argument is no longer valid, keep accepting it and emit a FutureWarning with emit_user_level_warning instead of raising.

- **Pre-condition —** each function whose signature lost an argument between the base commit and the patch, or which the written lines mark with a `FutureWarning`.
- **Pass condition —** the argument is still accepted and the change emits a `FutureWarning` through `emit_user_level_warning`.

The pre-condition selects both outcomes deliberately (§7.1). Selecting only functions that lost an argument would find nothing but violations and could never record a compliant deprecation; selecting only ones that emit the warning would find nothing but passes. Together they cover *an argument became invalid* however the agent handled it. Heuristic on the **pre-condition** (§6.3): a `FutureWarning` in the written lines is matched textually and may belong to a deprecation of something other than an argument. The signature comparison itself is exact. The corpus files this `differential`; both versions of the file are in the patch, so no tool run is needed. Recorded rather than corrected, per the spec §5.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/pydata/specialized.py:60`](../compliance/rules/pydata/specialized.py#L60) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html


## pydata — Documentation and docstrings

### PYDATA-C024 — `DocstringsUseNumpyFormat`

> **Corpus:** Write docstrings in the NumPy docstring format.

- **Pre-condition —** each docstring the agent wrote or edited.
- **Pass condition —** it carries no section header belonging to a competing format.

Heuristic on the **pass condition** (§6.2), graded one-sidedly. A docstring with no sections at all is perfectly numpydoc-compatible, so confirming the format is not possible; a reST field list or a Google `Args:` header is positive evidence of the wrong one. Where a numpydoc section *is* present that is reported as satisfying, which is stronger evidence than mere absence.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pydata/documentation.py:62`](../compliance/rules/pydata/documentation.py#L62) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C026 — `ExecutableDocsAreMystCodeCells`

> **Corpus:** Write documentation pages containing executable code as MyST Markdown files using the {code-cell} directive.

- **Pre-condition —** each documentation page the contribution changes that contains executable code.
- **Pass condition —** the page is MyST Markdown and the code sits in a `{code-cell}` block.

Heuristic on the **pre-condition** (§6.3): *contains executable code* is recognised by the forms xarray's docs actually use -- doctest prompts, fenced Python, MyST `{code-cell}` and `{jupyter-execute}` blocks, and the `jupyter-execute`, `ipython` and `code-block:: python` directives -- and a page can carry runnable code in a shape none of those matches. **The `{code-cell}` form is in that list deliberately.** Leaving it out made the pre-condition select only pages written the wrong way, so the rule could record a violation and never a compliant page -- §7.1 inverted, and caught by the satisfying test rather than by review.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pydata/documentation.py:99`](../compliance/rules/pydata/documentation.py#L99) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C027 — `PublicApiListedInApiDoc`

> **Corpus:** List every public method in a toctree in doc/api.rst.

- **Pre-condition —** each public module-level function the agent added to the package.
- **Pass condition —** its name appears in the lines added to `doc/api.rst`.

Heuristic on the **pre-condition** (§6.3): *public method* is approximated by a module-level function whose name does not begin with an underscore, which misses methods added to existing classes and over-fires on helpers that are public by accident of naming. The corpus files this `differential` and it needs no tool run -- `doc/api.rst` is in the diff. Recorded rather than corrected in the workbook, per the spec §5.


`heuristic` · ownership `created` · reads `files` · tier `differential`

[`compliance/rules/pydata/documentation.py:142`](../compliance/rules/pydata/documentation.py#L142) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C030 — `SectionMarkersFollowTheScheme`

> **Corpus:** Mark up ReST section levels with `*` and an overline for chapters, `=` for headings, `-` for sections and `~` for subsections.

- **Pre-condition —** each reStructuredText page the contribution changes that carries at least two section markers.
- **Pass condition —** the marker characters appear in the published order -- `*` for chapters, then `=`, `-`, `^`, `"`.

Heuristic on the **pass condition** (§6.2). Nesting depth is not recoverable from a flat scan, so this checks the weaker property the scheme implies: the characters are drawn from the published set and appear for the first time in the published order. A page that skips a level in a way the guide would accept still passes, and one that nests unusually but consistently may not.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pydata/documentation.py:181`](../compliance/rules/pydata/documentation.py#L181) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C031 — `BoldIsDoubleAsterisk`

> **Corpus:** Use `**text**` for bold text in ReST.

- **Pre-condition —** each documentation page the contribution changes.
- **Pass condition —** the lines it wrote use no markup that means bold somewhere else -- `__text__`, or an HTML bold tag.

Heuristic on the **pass condition** (§6.2), graded one-sidedly. Confirming that every bold span uses `**` would need to know which spans were meant to be bold; what is decidable is the presence of the two forms an author reaches for by habit from Markdown or HTML. In reST `__text__` is an anonymous hyperlink, so this is a real defect rather than a style preference.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pydata/documentation.py:230`](../compliance/rules/pydata/documentation.py#L230) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C033 — `ImagesUseTheImageDirective`

> **Corpus:** Include image files in documentation pages with the `image::` directive.

- **Pre-condition —** each documentation page the contribution changes whose written lines name an image file.
- **Pass condition —** the page uses an `image::` or `figure::` directive.

Heuristic on the **pre-condition** (§6.3): *includes an image file* is recognised by a filename with an image extension appearing in the written lines, which also matches a page that merely mentions one in prose. `figure::` is accepted alongside `image::` because it is the same directive family with a caption, and reporting it would be a false violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pydata/documentation.py:265`](../compliance/rules/pydata/documentation.py#L265) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html


## pydata — AI-assisted contribution policy

### PYDATA-C103 — `EveryLinePersonallyReviewed`

> **Corpus:** Personally review and understand every line of the change before submitting it.

- **Pre-condition —** a named model produced a contribution.
- **Pass condition —** a person reviewed and understood every line before submission.

``by_construction`` (§6.5), not heuristic: the check is exact -- the harness records that a model produced the patch with nobody in the loop -- and it is the *setup*, not the evidence, that makes compliance impossible. Scored because an excluded rule cannot be shown to a guided agent and then reported on.


ownership `created` · reads `files` · tier `trajectory`

[`compliance/rules/pydata/ai_policy.py:38`](../compliance/rules/pydata/ai_policy.py#L38) · source: https://docs.xarray.dev/en/latest/contribute/ai-policy.html

### PYDATA-C110 — `DocumentationReadAndVerified`

> **Corpus:** Never submit documentation you have not read and verified yourself.

- **Pre-condition —** a named model's contribution changes documentation.
- **Pass condition —** a person read and verified that documentation.

``by_construction`` for the same reason as C103, but with a pre-condition that still discriminates: a contribution touching no documentation finds no target. That keeps the rule out of the fraction on most runs rather than failing every one, and makes its activation rate a measure of how often agents write documentation at all.


ownership `created` · reads `files` · tier `trajectory`

[`compliance/rules/pydata/ai_policy.py:67`](../compliance/rules/pydata/ai_policy.py#L67) · source: https://docs.xarray.dev/en/latest/contribute/ai-policy.html

### PYDATA-C117 — `AiGeneratedContentDisclosed`

> **Corpus:** Disclose that the pull request contains AI-generated content.

- **Pre-condition —** an autonomous run produced a contribution, so it contains AI-generated content.
- **Pass condition —** the pull request text says so.

Not ``by_construction``: nothing stops an agent writing the sentence. Heuristic on the **pass condition** (§6.2) -- "says so" is matched against a vocabulary of AI-mention patterns, so a disclosure worded outside that vocabulary reads as a violation.


`heuristic` · ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/pydata/ai_policy.py:99`](../compliance/rules/pydata/ai_policy.py#L99) · source: https://github.com/pydata/xarray/blob/main/.github/PULL_REQUEST_TEMPLATE.md


## pydata — Code and quality

### PYDATA-C037 — `RuffFormatReportsNoChanges`

> **Corpus:** Format code with ruff so that `ruff format` reports no changes.

- **Pre-condition —** each Python file the agent edited that gained a line.
- **Pass condition —** none of the lines it wrote carries formatting `ruff format` always removes -- trailing whitespace, or a tab in the indentation.

Heuristic on the **pass condition** (§6.2), and narrow on purpose. A real answer is `ruff format --diff`, which nothing in this instrument runs. Everything the formatter decides from configuration -- line length, quote style, magic trailing commas -- is deliberately not checked, because a proxy that guessed at project settings would report violations that are not violations. What is left holds under every configuration.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pydata/code_quality.py:49`](../compliance/rules/pydata/code_quality.py#L49) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C038 — `NoRuffLintViolations`

> **Corpus:** Keep the code free of ruff lint violations.

- **Pre-condition —** the agent submitted Python code, which is what gets merged.
- **Pass condition —** `ruff check` reports no finding the base commit did not already have.

Deliberately not "the agent ran ruff": the obligation is that the contribution is clean, so one that never ran the tool is judged rather than excused.


ownership `touched` · reads `files, lint_run` · tier `static`

[`compliance/rules/pydata/code_quality.py:90`](../compliance/rules/pydata/code_quality.py#L90) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C040 — `TypeHintsPassMypy`

> **Corpus:** Make type hints pass mypy's static type check.

- **Pre-condition —** the agent submitted Python code.
- **Pass condition —** `mypy` reports no new error.

Graded **one-sidedly**. A file that does not parse cannot type-check, and that is conclusive. Nothing else is: no mypy run is collected, and inferring a type error from source text would manufacture violations out of a proxy no one could defend. So this fails on evidence and withholds otherwise, never passing vacuously. `lint_run` is declared as the nearest named missing input, the same compromise sphinx-doc's C022 makes; a `type_check_run` source would say what is actually absent.


ownership `touched` · reads `files, lint_run` · tier `static`

[`compliance/rules/pydata/code_quality.py:124`](../compliance/rules/pydata/code_quality.py#L124) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html

### PYDATA-C091 — `PreCommitRunOverAllFiles`

> **Corpus:** Run pre-commit over all files and commit any changes it makes.

- **Pre-condition —** the agent submitted a contribution.
- **Pass condition —** a `pre-commit run --all-files` invocation appears in the command log.

The guide names the whole-repository form specifically, so a staged-files run does not satisfy it. The second half of the sentence -- *and commit any changes it makes* -- is not separately checkable: a hook's edits are indistinguishable in the diff from the agent's own, which is worth saying because the pass condition is narrower than the rule.


ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/pydata/code_quality.py:156`](../compliance/rules/pydata/code_quality.py#L156) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html


## pydata — Language and framework style

### PYDATA-C039 — `ImportsGroupedAsIsortRequires`

> **Corpus:** Order imports the way ruff's isort rules require.

- **Pre-condition —** each Python file the agent edited whose leading import block holds at least two imports.
- **Pass condition —** the groups appear in the declared order and none is split in two.

Heuristic on the **pass condition** (§6.2), and the flag is about *coverage* rather than about the check being fuzzy. isort decides three things -- which group each import belongs to, the order of the groups, and the alphabetical order within a group. This checks the first two exactly and the third not at all, so a file with correctly grouped but unsorted imports passes a rule it would fail under `ruff check --select I`. Selecting only files whose import block the agent touched, rather than every file it edited, would be narrower than the sentence: xarray asks that the code be ordered, not that the agent leave alone what it did not write.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pydata/language_style.py:25`](../compliance/rules/pydata/language_style.py#L25) · source: https://docs.xarray.dev/en/latest/contribute/contributing.html


# pylint-dev

| category | rules |
|---|---:|
| [Git and commit conventions](#pylint-dev-git-and-commit-conventions) | 2 |
| [PR and release metadata](#pylint-dev-pr-and-release-metadata) | 2 |
| [Tests and test style](#pylint-dev-tests-and-test-style) | 28 |
| [Specialized changes](#pylint-dev-specialized-changes) | 1 |
| [AI-assisted contribution policy](#pylint-dev-ai-assisted-contribution-policy) | 1 |
| [Code and quality](#pylint-dev-code-and-quality) | 3 |
| [Language and framework style](#pylint-dev-language-and-framework-style) | 12 |


## pylint-dev — Git and commit conventions

### PYLINT-DEV-C098 — `VenvNotAddedToGitignore`

> **Corpus:** Do not add venv to the repository's .gitignore.

- **Pre-condition —** the contribution changes a `.gitignore`.
- **Pass condition —** none of the lines it writes into that file is a `venv` entry.

Not heuristic: the pass condition is the presence of one named entry in one named file (§6.2), and the pre-condition selects on a path -- an exact observable fact (§6.3). Selecting on the entry itself would only ever find violations (§7.1), so the edit to the ignore file is the antecedent and the entry is the grading. Corpus: Do not add venv to the repository's .gitignore.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/git_conventions.py:44`](../compliance/rules/pylint_dev/git_conventions.py#L44) · source: https://github.com/pylint-dev/pylint/blob/main/.github/copilot-instructions.md

### PYLINT-DEV-C099 — `NoVirtualEnvironmentCommitted`

> **Corpus:** Do not commit a virtual environment directory.

- **Pre-condition —** the agent committed a contribution.
- **Pass condition —** none of its paths lies inside a virtual environment directory.

Heuristic on the **pass condition** (§6.2). The sentence names a *kind* of directory, not a path, so membership is decided from the conventional markers -- a `venv`, `.venv` or `virtualenv` path segment, PEP 405's `pyvenv.cfg`, and `site-packages/`. A differently-named environment would pass, and a project directory that happens to be called `venv` would fail; both are the proxy, and neither is what the rule says. Corpus: Do not commit a virtual environment directory.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/git_conventions.py:81`](../compliance/rules/pylint_dev/git_conventions.py#L81) · source: https://github.com/pylint-dev/pylint/blob/main/.github/copilot-instructions.md


## pylint-dev — PR and release metadata

### PYLINT-DEV-C006 — `NewsFragmentForTheChange`

> **Corpus:** Create a towncrier news fragment named after the issue number for the change.

- **Pre-condition —** the contribution changes Python source under `pylint/`, which is the complement of the trivial change the guide's `skipnews` label exempts.
- **Pass condition —** it adds a file under `doc/whatsnew/fragments/` whose name begins with an issue number.

Heuristic on **both layers** (§6.3, §6.2). The sentence begins *Otherwise*, and what it is otherwise to is a maintainer's judgement that a change is trivial; nothing in the patch settles that, so the complement is used and a documentation-only or test-only contribution finds no target rather than being graded. The pass condition reads *named after the issue number* as *the name starts with a number*: which issue a task corresponds to is a fact about the benchmark, not about the contribution, so the digits cannot be checked against anything. Corpus: Create a towncrier news fragment named after the issue number for the change.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/pr_metadata.py:37`](../compliance/rules/pylint_dev/pr_metadata.py#L37) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/contribute.html

### PYLINT-DEV-C007 — `NewsFragmentTypeFromTheDeclaredList`

> **Corpus:** Give the news fragment one of the fragment types declared in towncrier.toml.

- **Pre-condition —** each news fragment the agent added whose name parses as `<issue number>.<type>`.
- **Pass condition —** its type is one of the twelve `towncrier.toml` declares.

Not heuristic: the list is one the project publishes in its own configuration, and membership of a closed list is exact (§6.2). A fragment whose name does not parse at all is C006's finding, not this rule's -- selecting it here would report the same defect twice and depress both rates. Corpus: Give the news fragment one of the fragment types declared in towncrier.toml.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/pr_metadata.py:81`](../compliance/rules/pylint_dev/pr_metadata.py#L81) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/contribute.html


## pylint-dev — Tests and test style

### PYLINT-DEV-C003 — `OwnTestSuiteRun`

> **Corpus:** Run pylint's own test suite against your change.

- **Pre-condition —** the agent submitted a contribution.
- **Pass condition —** a `pytest` or `tox` invocation appears in the command log.

Not heuristic: the workbook's own note says the linked testing page *supplies the exact invocations and sanctions no alternative suite*, so the pass condition is the presence of something the rule names rather than a proxy for it (§6.2). The pre-condition fires on having submitted something, never on having run the suite (§7.1): triggering on the run would let a contribution that tested nothing collect `not_applicable` instead of a violation. Corpus: Run pylint's own test suite against your change.


ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/pylint_dev/tests.py:80`](../compliance/rules/pylint_dev/tests.py#L80) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/contribute.html

### PYLINT-DEV-C025 — `TestsIncludedWithTheContribution`

> **Corpus:** Include tests with every contribution.

- **Pre-condition —** the agent submitted a contribution.
- **Pass condition —** at least one of its paths is under the test tree.

Not heuristic. The sentence carries no exemption -- *new contributions are not accepted unless they include tests* -- so, unlike the hedged versions of this rule in other corpora, the pre-condition is not narrowed to the complement of an exempt class: every contribution is graded, and a documentation-only change that ships no test is recorded as a violation because that is what the sentence says. The reading is stated here so a reviewer can disagree with it against the sentence rather than against the code (§9). Corpus: Include tests with every contribution.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:112`](../compliance/rules/pylint_dev/tests.py#L112) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/index.html

### PYLINT-DEV-C032 — `SuiteSelectionPatternOmitsThePyExtension`

> **Corpus:** Select a test suite with a -k pattern that omits the .py extension.

- **Pre-condition —** each test-runner invocation that restricts the run with `-k`.
- **Pass condition —** the pattern it passes does not end in `.py`.

Not heuristic: the exclusion is one the sentence spells out and the check is a suffix comparison on the pattern (§6.2). The pre-condition fires on *selecting a suite*, not on selecting one correctly (§7.1), so a run that names the file with its extension is recorded as the violation it is. The workbook files this row *never fires*, and it should: a contribution that never restricted a run finds no target. Corpus: Select a test suite with a -k pattern that omits the .py extension.


ownership `touched` · reads `commands` · tier `trajectory`

[`compliance/rules/pylint_dev/tests.py:144`](../compliance/rules/pylint_dev/tests.py#L144) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/launching_test.html

### PYLINT-DEV-C034 — `StdlibPrimerInvocation`

> **Corpus:** Run the stdlib primer locally with pytest -m primer_stdlib --primer-stdlib.

- **Pre-condition —** each command the agent ran that names the primer.
- **Pass condition —** it carries both the `-m primer_stdlib` marker and the `--primer-stdlib` flag.

Not heuristic: the marker and the flag are given verbatim by the rule and there is no second spelling of the invocation (§6.2). Selecting on the *primer* rather than on the correct invocation is what lets the rule record a violation at all (§7.1). The workbook files this row *never fires*: a contribution that never ran the primer finds no target. Corpus: Run the stdlib primer locally with pytest -m primer_stdlib --primer-stdlib.


ownership `touched` · reads `commands` · tier `trajectory`

[`compliance/rules/pylint_dev/tests.py:186`](../compliance/rules/pylint_dev/tests.py#L186) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/launching_test.html

### PYLINT-DEV-C037 — `NewUnitTestsUnderTheTestDirectory`

> **Corpus:** Put new unit tests in pylint's unit test directory.

- **Pre-condition —** each new unit-test module the agent added, wherever it put it.
- **Pass condition —** it sits under the test tree and outside the functional and configuration frameworks.

Heuristic on the **pass condition** (§6.2), and this is the corpus/tree mismatch the module docstring records: the page this rule comes from writes the directory as `/pylint/test`, its own overview writes `pylint/tests`, and the checkout has `tests/`. The workbook marks the row `low_confidence` and is not edited (§0), so all three spellings are accepted -- which means the check is of the *tree*, not of the exact path the sentence names. A module is taken to be a unit test by pylint's two naming conventions, `test_*.py` and `unittest_*.py`; the functional and configuration directories are excluded because their files are tests of a different kind, governed by C053 and C060. Corpus: Put new unit tests in pylint's unit test directory.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:225`](../compliance/rules/pylint_dev/tests.py#L225) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C039 — `UnitTestDataUnderRegrtestData`

> **Corpus:** Put data files a unit test needs in the regrtest_data directory.

- **Pre-condition —** each non-Python file the agent added under the test tree, outside the functional and configuration frameworks.
- **Pass condition —** it sits under `regrtest_data/`.

Heuristic on the **pre-condition** (§6.3). *A data file a unit test needs* is not something the patch states: a file is not linked to the test that reads it, so the proxy is a file added under the test tree that is not itself a test module. Python data files are deliberately not selected -- a `.py` under the test tree is at least as likely to be a test as a fixture, and selecting it would manufacture violations against test modules C037 already governs. The functional and configuration trees are excluded because their companion files are governed by C040, C045, C061 and C063 (spec §7.5). Corpus: Put data files a unit test needs in the regrtest_data directory.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:269`](../compliance/rules/pylint_dev/tests.py#L269) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C040 — `FunctionalTestHasATxtCompanion`

> **Corpus:** Give every functional test .py file a .txt companion with the same stem.

- **Pre-condition —** each functional test `.py` the agent added.
- **Pass condition —** a `.txt` file with the same stem is added beside it.

Not heuristic: the pairing is what makes a file a test case at all, and both halves are paths in the patch (§6.2). Only *added* tests are selected: a functional test that already existed has its `.txt` in the tree rather than in the diff, and requiring it in the patch would report a violation against a pairing the agent never touched. Corpus: Give every functional test .py file a .txt companion with the same stem.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:310`](../compliance/rules/pylint_dev/tests.py#L310) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C041 — `ExpectedOutputMatchesTheAnnotations`

> **Corpus:** Record in the .txt file exactly the pylint messages the test file should emit.

- **Pre-condition —** each functional test `.py` the agent changed whose `.txt` companion is in the same patch.
- **Pass condition —** the messages the `.txt` records are exactly the ones the file's `# [symbol]` annotations state.

Heuristic on the **pass condition** (§6.2). The workbook files this row `differential` because the authority on what a test file emits is pylint itself; what the patch carries instead is the same expectation written twice, and agreement between the two is a proxy for agreement with the linter -- an annotation and a record that are wrong in the same way pass here. Version-conditional annotations are allowed but not required for the same reason: which of them applies depends on the interpreter. Corpus: Record in the .txt file exactly the pylint messages the test file should emit.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/pylint_dev/tests.py:355`](../compliance/rules/pylint_dev/tests.py#L355) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C042 — `ExpectedMessageLinesAreAnnotated`

> **Corpus:** Annotate each line expected to emit a message with a # [message_symbol] comment.

- **Pre-condition —** each functional test `.py` the agent changed whose `.txt` companion in the same patch records at least one message.
- **Pass condition —** every line the `.txt` names carries a `# [...]` annotation comment.

Not heuristic: the annotation pattern is given verbatim by the rule and the check is whether a comment of that shape sits on the named line (§6.2). This is the *form* half of the pairing and C041 is the *content* half: a file whose annotations sit on the right lines but name the wrong symbols passes here and fails there. Splitting them that way keeps two corpus rows from reporting one defect twice. Corpus: Annotate each line expected to emit a message with a # [message_symbol] comment.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:407`](../compliance/rules/pylint_dev/tests.py#L407) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C043 — `SeveralMessagesInOneBracketComment`

> **Corpus:** List several expected messages on one line as a comma-separated set inside a single bracket comment.

- **Pre-condition —** each line the agent wrote in a functional test that expects more than one message, spelled either way.
- **Pass condition —** they are listed as a comma-separated set inside a single bracket comment.

Not heuristic: both spellings are readable off the line -- one bracket holding several symbols, or several brackets -- so the pre-condition selects the situation and the pass condition grades the form (§7.1, §6.2). Selecting only the multi-bracket spelling would find nothing but violations. Corpus: List several expected messages on one line as a comma-separated set inside a single bracket comment.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:453`](../compliance/rules/pylint_dev/tests.py#L453) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C045 — `PerTestConfigurationIsASameNamedRcFile`

> **Corpus:** Put per-test pylint configuration in a same-named .rc file beside the test.

- **Pre-condition —** each configuration file the agent added inside the functional test tree.
- **Pass condition —** it is named `<test stem>.rc`, and when functional tests were added in the same directory one of them carries that stem.

Heuristic on the **pass condition** (§6.2). *Beside the test* can only be confirmed when the test itself is in the patch; an `.rc` added next to a test that already existed is accepted on the strength of its name alone, because the tree is not in the evidence. What is decided exactly is the other half -- a configuration file that is not an `.rc` at all, or whose stem matches none of the tests added beside it. Corpus: Put per-test pylint configuration in a same-named .rc file beside the test.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:524`](../compliance/rules/pylint_dev/tests.py#L524) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C046 — `RunnerOptionsGoUnderTestoptions`

> **Corpus:** Pass functional runner options only through a [testoptions] section using the supported keys.

- **Pre-condition —** each functional-test `.rc` file in the patch.
- **Pass condition —** every key it sets under `[testoptions]` is one of the six the guide enumerates, and none of those six is set outside that section.

Not heuristic: the section name and the key list are both published by the project and the list is closed, so membership is exact (§6.2). The `.rc` is read with a small hand-rolled parser rather than `configparser` because a malformed file is a verdict this rule has to be able to report rather than crash on. The workbook files this row *never fires*: a functional test with no runner options finds no target. Corpus: Pass functional runner options only through a [testoptions] section using the supported keys.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:564`](../compliance/rules/pylint_dev/tests.py#L564) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C047 — `MaxPyverIsTheFirstUnsupportedVersion`

> **Corpus:** Set max_pyver to the first unsupported version, one above the last version the test should run on.

- **Pre-condition —** each functional-test `.rc` in the patch that sets `max_pyver`.
- **Pass condition —** the value is a `major.minor` version above `min_pyver` and above every version the test's own expectation files show it still running on.

Heuristic on the **pass condition** (§6.2). *One above the last version the test should run on* names a fact the patch does not carry: what the test is meant to cover. The two decidable consequences of the bound being exclusive are graded instead -- a `max_pyver` at or below `min_pyver`, and a `max_pyver` at or below the version of a `<stem>.<version>.txt` expectation, which exists precisely because the test runs there. A value that is off by one with no such companion passes, which is weaker than the rule. The workbook files this row *never fires*: a test that is not version-bounded finds no target. Corpus: Set max_pyver to the first unsupported version, one above the last version the test should run on.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:620`](../compliance/rules/pylint_dev/tests.py#L620) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C048 — `ConditionalAnnotationOperators`

> **Corpus:** Mark version-conditional expected messages using only the four supported comparison operators.

- **Pre-condition —** each version-conditional annotation the agent wrote in a functional test.
- **Pass condition —** its comparison is one of `<`, `<=`, `>` and `>=`.

Not heuristic: the operator set is enumerated by the rule and closed, so membership is exact (§6.2). The pre-condition fires on the annotation carrying *any* comparison, not on it carrying a supported one (§7.1) -- otherwise an `==` could never be reported. Corpus: Mark version-conditional expected messages using only the four supported comparison operators.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:683`](../compliance/rules/pylint_dev/tests.py#L683) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C049 — `BothVersionedAndDefaultExpectationFiles`

> **Corpus:** Provide both a version-suffixed .txt and a default .txt when expected output differs by Python version.

- **Pre-condition —** each functional test the agent added whose expected output depends on the Python version -- read as the test carrying a version-conditional annotation, or a versioned `.txt` being added for it.
- **Pass condition —** both a `<stem>.<version>.txt` and a default `<stem>.txt` are added.

Heuristic on the **pre-condition** (§6.3). *When expected output differs by Python version* is a fact about what pylint emits on two interpreters, which the patch cannot state; the two observable signs of the author having decided it does are used instead, and a test whose output differs but which carries neither sign finds no target rather than being graded. The pre-condition selects on both signs deliberately (§7.1): a test with only the versioned file, or only the conditional annotation, is exactly the violation the rule exists to catch, and selecting on the compliant pair would find nothing but passes. Corpus: Provide both a version-suffixed .txt and a default .txt when expected output differs by Python version.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:727`](../compliance/rules/pylint_dev/tests.py#L727) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C050 — `UnparsableTestsUseVersionBoundsNotConditions`

> **Corpus:** Use min_pyver or max_pyver rather than conditional annotations when the test code is not parsable on every version.

- **Pre-condition —** each functional test the agent added that either carries a version-conditional annotation or is bounded by `min_pyver`/`max_pyver`.
- **Pass condition —** if its code cannot be parsed on every supported version, the bound is used rather than the annotation.

Heuristic on the **pass condition** (§6.2). *Not parsable on every version* would need every interpreter pylint supports; what is available is one parse plus a short list of syntax that arrived after the floor -- `match`, `except*`, PEP 695 aliases and generics. That is positive evidence only: a file using newer syntax the list does not name reads as parsable and passes. The pre-condition selects both arrangements (§7.1), so a test that correctly reaches for `min_pyver` is recorded as a pass rather than never appearing. Corpus: Use min_pyver or max_pyver rather than conditional annotations when the test code is not parsable on every version.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:780`](../compliance/rules/pylint_dev/tests.py#L780) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C051 — `TestCaseForAnExistingCheckerIsAppended`

> **Corpus:** Append a new test case for an existing checker to that checker's existing test file.

- **Pre-condition —** each functional test file in a contribution that also edits a checker module which already existed.
- **Pass condition —** the test file already existed too -- the case was appended rather than given a new file.

Heuristic on the **pre-condition** (§6.3). *A new test case for an existing checker* is an association the patch does not state: what it shows is a checker module that is not new and functional tests that changed, and the two are assumed to belong together. A contribution that edits an old checker and adds a genuinely new message would be selected here and reported, which over-fires; the narrower reading -- matching the test to the checker by name -- would beg C052's question. Corpus: Append a new test case for an existing checker to that checker's existing test file.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:848`](../compliance/rules/pylint_dev/tests.py#L848) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C052 — `FunctionalTestFileNamedForTheMessageSymbol`

> **Corpus:** Name a new checker's functional test file after the message symbol, with underscores.

- **Pre-condition —** each functional test file the agent added in a contribution that also declares a new message symbol.
- **Pass condition —** its stem is one of those symbols with hyphens written as underscores.

Heuristic on the **pre-condition** (§6.3). *A new checker* is approximated by the change declaring a new `msgs` entry, which is the observable trace a new checker leaves; a contribution that adds several symbols and one test has the test measured against all of them, which is generous in the passing direction. Corpus: Name a new checker's functional test file after the message symbol, with underscores.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:892`](../compliance/rules/pylint_dev/tests.py#L892) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C053 — `FunctionalTestInItsInitialLetterDirectory`

> **Corpus:** Place a functional test file in the sub-directory named for its first letter.

- **Pre-condition —** each functional test file the agent added outside `functional/ext/`.
- **Pass condition —** the first directory below `functional/` is the file's first letter.

Not heuristic: a comparison between one character of the name and one segment of the path is exact on both layers (§6.2, §6.3). Extension tests are excluded from the pre-condition, not graded and failed: they live under `functional/ext/<extension>/`, where the first segment is `ext` by design, and C054 is the row that governs them. Read literally the two sentences contradict, so the antecedent is narrowed and a test pins that an extension test finds no target here (spec §7.5). Regression tests are *not* excluded: `r/regression/regression_x.py` satisfies this rule and C055 at once. Corpus: Place a functional test file in the sub-directory named for its first letter.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:932`](../compliance/rules/pylint_dev/tests.py#L932) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C055 — `RegressionTestInARegressionDirectory`

> **Corpus:** Put a regression test in one of the two regression directories.

- **Pre-condition —** each functional test the agent added that is a regression test -- by the `regression_` prefix C056 makes the corpus's own definition, or by already sitting in one of the two directories.
- **Pass condition —** it sits in `functional/r/regression/` or `functional/r/regression_02/`.

Not heuristic: the set of acceptable directories is enumerated by the rule and closed, and the category *regression test* is one the corpus defines in the very next row (§6.3, §6.2). Selecting on both signs is what makes the rule two-sided (§7.1): a correctly prefixed test in the wrong directory and a correctly placed one both appear. A regression test that carries neither sign is invisible here. That is the price of having no other evidence of the category, and it is C056's finding rather than this rule's. Corpus: Put a regression test in one of the two regression directories.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:974`](../compliance/rules/pylint_dev/tests.py#L974) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C056 — `RegressionTestFileNamePrefix`

> **Corpus:** Prefix a regression test file name with regression_.

- **Pre-condition —** each functional test the agent added in one of the two regression directories.
- **Pass condition —** its name begins with `regression_`.

Not heuristic: a literal filename prefix has one satisfying form (§6.2). Selecting on the *directory* rather than on the prefix is what lets the rule report a badly named file; C055 does the mirror image, selecting on the prefix to report a badly placed one, so neither ends up one-sided. Corpus: Prefix a regression test file name with regression_.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:1013`](../compliance/rules/pylint_dev/tests.py#L1013) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C057 — `NestedSubDirectoryMatchesTheFirstWord`

> **Corpus:** Place a test file in a nested sub-directory whose name matches the word before the first underscore of the file name.

- **Pre-condition —** each functional test the agent added under a letter directory whose name contains an underscore.
- **Pass condition —** if it sits in a nested sub-directory, that directory's name is the word before the file's first underscore.

Heuristic on the **pass condition** (§6.2). The sentence is conditional -- a test belongs in a nested directory *if one of that name exists* -- and the tree is not in the evidence, so a test left flat in its letter directory is accepted rather than reported. What is decided exactly is the other half: a test placed in a nested directory whose name is not its first word. Corpus: Place a test file in a nested sub-directory whose name matches the word before the first underscore of the file name.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:1044`](../compliance/rules/pylint_dev/tests.py#L1044) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C059 — `ExpectedOutputRegeneratedWithTheFlag`

> **Corpus:** Regenerate a functional test's expected output with --update-functional-output.

- **Pre-condition —** the contribution changes a functional test's existing `.txt` expectation file.
- **Pass condition —** a command carrying `--update-functional-output` appears in the log.

Heuristic on the **pre-condition** (§6.3). *Regenerating* is an act, and the act leaves no trace of its own; what the patch shows is an expectation file that changed, which is the same state a hand-edit produces. Firing on the flag instead would find only the agents that had already complied (§7.1), so the superset is used and a hand-edited expectation is reported as a violation -- which is the reading, and is stated here so it can be disagreed with. Newly added `.txt` files are not selected: there was no expected output to regenerate. Corpus: Regenerate a functional test's expected output with --update-functional-output.


`heuristic` · ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/pylint_dev/tests.py:1103`](../compliance/rules/pylint_dev/tests.py#L1103) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C060 — `ConfigurationTestInItsFormatDirectory`

> **Corpus:** Create a configuration test as a new, unused filename in the directory for that configuration format.

- **Pre-condition —** each configuration test input file the agent added.
- **Pass condition —** one of the directories above it names the file's configuration format.

Heuristic on the **pass condition** (§6.2): which directory belongs to which format is a fact about the tree's layout rather than about the patch, so the mapping is written down here (`.toml` under `toml/`, `.ini` and `.cfg` under `ini/`, `tox/` or `setup_cfg/`) and a format the map does not know reads as a violation. *A new, unused name* is carried by the pre-condition rather than graded: a file the agent added is by construction a name that was free, and a configuration test that already existed and was edited is not the act this sentence is about. Corpus: Create a configuration test as a new, unused filename in the directory for that configuration format.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:1145`](../compliance/rules/pylint_dev/tests.py#L1145) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C061 — `ConfigurationTestHasAResultJson`

> **Corpus:** Add a .result.json file whose stem matches the configuration test file.

- **Pre-condition —** each configuration test input file the agent added.
- **Pass condition —** a `<stem>.result.json` is added beside it, or a `<stem>.<code>.out` is, which is the form a configuration expected to fail takes.

Not heuristic: the companion's name is fully determined by the file it accompanies, and both are paths in the patch (§6.2). The `.out` alternative is not a softening of the rule but the exclusion C063 needs: a configuration that is supposed to crash has no resulting configuration to record, and reporting it here would make the two rows contradict (spec §7.5). Corpus: Add a .result.json file whose stem matches the configuration test file.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:1188`](../compliance/rules/pylint_dev/tests.py#L1188) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C062 — `ResultJsonRecordsOnlyTheDifference`

> **Corpus:** Record only the difference from the standard configuration in the .result.json file.

- **Pre-condition —** each `.result.json` in the patch that parses as JSON.
- **Pass condition —** it is an object recording a handful of settings -- a difference from the standard configuration rather than a copy of it.

Heuristic on the **pass condition** (§6.2). *Only the difference* is a comparison against a configuration the bundle does not carry, so size stands in for it: pylint's standard configuration has upwards of a hundred options and a delta has a few, and the line is drawn at ten top-level keys. A delta of eleven settings would be reported wrongly, and a full dump of nine would pass; the threshold is the proxy and is named here rather than left in the code. A file that does not parse as JSON is *not* selected: that is a broken test rather than a configuration recorded the wrong way, and grading it here would put one defect under two rows. Corpus: Record only the difference from the standard configuration in the .result.json file.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:1226`](../compliance/rules/pylint_dev/tests.py#L1226) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C063 — `ExpectedFailureOutFileName`

> **Corpus:** Express an expected configuration failure with a .out file named for the test and its exit code.

- **Pre-condition —** each `.out` file the agent added under the configuration test tree.
- **Pass condition —** it is named `<configuration test>.<exit code>.out`, and when configuration tests were added beside it, its stem is one of theirs.

Not heuristic: the filename pattern is given verbatim by the rule, and matching it is exact (§6.2). The pre-condition fires on the `.out` file rather than on a configuration being expected to fail, because the `.out` file is the only way the patch says a failure is expected at all -- and it selects badly named ones as readily as good ones. Corpus: Express an expected configuration failure with a .out file named for the test and its exit code.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:1281`](../compliance/rules/pylint_dev/tests.py#L1281) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html

### PYLINT-DEV-C065 — `OutFileUsesThePathPlaceholders`

> **Corpus:** Use the {abspath} and {relpath} placeholders for module and file name in a .out file.

- **Pre-condition —** each `.out` file in the patch that names a module or a file.
- **Pass condition —** the module is written `{abspath}` and the file `{relpath}`.

Not heuristic: two literal tokens are named by the rule and the check is whether they are the ones used (§6.2). Only lines that name a module or carry a `path:line:column:` message are examined; a `.out` file's prose lines say nothing about either placeholder. Corpus: Use the {abspath} and {relpath} placeholders for module and file name in a .out file.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/tests.py:1320`](../compliance/rules/pylint_dev/tests.py#L1320) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html


## pylint-dev — Specialized changes

### PYLINT-DEV-C054 — `ExtensionFunctionalTestUnderItsOwnDirectory`

> **Corpus:** Put the functional test for an extension checker under the extension's own directory.

- **Pre-condition —** each functional test file the agent added in a contribution that also changes a module under `pylint/extensions/`.
- **Pass condition —** it sits under `tests/functional/ext/<extension name>/`.

Heuristic on the **pre-condition** (§6.3). *The functional test for an extension checker* is not observable directly: what the patch shows is that an extension module changed and that functional tests were added, and the association between the two is inferred. A contribution that changed both an extension and a core checker would have its core tests selected here too, which over-fires; the alternative -- requiring the test's name to match the extension's -- would beg C052's question. Corpus: Put the functional test for an extension checker under the extension's own directory.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/specialized.py:31`](../compliance/rules/pylint_dev/specialized.py#L31) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html


## pylint-dev — AI-assisted contribution policy

### PYLINT-DEV-C082 — `CopilotInstructionsConsultedFirst`

> **Corpus:** Consult .github/copilot-instructions.md before searching the repository for context.

- **Pre-condition —** the agent ran at least one command that gathers context from the checkout.
- **Pass condition —** a command reading `.github/copilot-instructions.md` appears in the log before the first of them.

Heuristic on **both layers** (§6.3, §6.2). *Searching the repository for context* is approximated by a list of the commands a shell agent reads a tree with, which fires on a `ls` run for an unrelated reason and misses a search made through a tool the list does not name. And only the ordering half of the sentence is graded: its second clause -- the fallback allowed when the instructions are incomplete or in error -- is a judgement no evidence in the bundle settles, which the workbook itself records as `low_confidence` on this row. The pre-condition fires on the search, not on the reading of the instructions (§7.1): selecting the instructions file would find only agents that had already complied. Corpus: Consult .github/copilot-instructions.md before searching the repository for context.


`heuristic` · ownership `touched` · reads `commands` · tier `trajectory`

[`compliance/rules/pylint_dev/ai_policy.py:32`](../compliance/rules/pylint_dev/ai_policy.py#L32) · source: https://github.com/pylint-dev/pylint/blob/main/.github/copilot-instructions.md


## pylint-dev — Code and quality

### PYLINT-DEV-C093 — `PreCommitRunAllBeforeCommitting`

> **Corpus:** Run pre-commit run -a before committing.

- **Pre-condition —** the agent made at least one commit.
- **Pass condition —** a `pre-commit run -a` invocation appears in the command log before the first `git commit` in it.

Heuristic on the **pass condition** (§6.2). *Before committing* is read against the first `git commit` in the command log, because commits carry no timestamp that lines up with command indices; when the log records no `git commit` at all -- the harness having committed on the agent's behalf -- the ordering cannot be established and the check falls back to whether the hooks were ever run over the whole tree. Sound in the failing direction, weaker in the passing one. Corpus: Run pre-commit run -a before committing.


`heuristic` · ownership `touched` · reads `commits, commands` · tier `trajectory`

[`compliance/rules/pylint_dev/code_quality.py:51`](../compliance/rules/pylint_dev/code_quality.py#L51) · source: https://github.com/pylint-dev/pylint/blob/main/.github/copilot-instructions.md

### PYLINT-DEV-C094 — `ChangedFilesLintedWithTheStandardInvocation`

> **Corpus:** Lint changed files with pylint --rcfile=pylintrc --fail-on=I.

- **Pre-condition —** the contribution changes Python files.
- **Pass condition —** a `pylint` invocation naming both `--rcfile=pylintrc` and `--fail-on=I` appears in the command log.

Not heuristic: the sentence gives the invocation verbatim, the same one the project's pre-commit hook and CI job pin, so the pass condition is the presence of something the rule names exactly (§6.2). What it does not check is that every changed file was passed to it; the sentence's `path/to/your/changes.py` is a placeholder, and treating it as a per-file obligation would grade a form the docs do not state. Corpus: Lint changed files with pylint --rcfile=pylintrc --fail-on=I.


ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/pylint_dev/code_quality.py:99`](../compliance/rules/pylint_dev/code_quality.py#L99) · source: https://github.com/pylint-dev/pylint/blob/main/.github/copilot-instructions.md

### PYLINT-DEV-C097 — `ChangeValidatedOnSampleCode`

> **Corpus:** Validate a change by running pylint over sample code that exercises it.

- **Pre-condition —** the contribution changes Python files.
- **Pass condition —** a `pylint` invocation names a path that is not one of the changed source files -- sample code the change is exercised on.

Heuristic on the **pass condition** (§6.2). *Sample code that exercises it* is a judgement about what the sample contains, and the patch cannot make it: the proxy is that the run's object is not itself part of the contribution. A run over a functional test file the change added counts, because such a file is exactly the sample pylint is pointed at; a run over only the modified checker does not, and that is the case C094 already grades. Corpus: Validate a change by running pylint over sample code that exercises it.


`heuristic` · ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/pylint_dev/code_quality.py:136`](../compliance/rules/pylint_dev/code_quality.py#L136) · source: https://github.com/pylint-dev/pylint/blob/main/.github/copilot-instructions.md


## pylint-dev — Language and framework style

### PYLINT-DEV-C016 — `MessageIdNotAlreadyUsed`

> **Corpus:** Give a new checker a message id that no existing checker already uses.

- **Pre-condition —** each `msgs` entry the agent wrote in a checker class.
- **Pass condition —** its message id is declared by no other checker in the contribution and was not already declared in the file it was added to.

Heuristic on the **pass condition** (§6.2): *no existing checker* means every checker in the tree, and the bundle carries only the files the patch touched. A collision with an untouched checker is invisible here, so a pass is weaker than the rule -- which is also why the guide offers `get_unused_message_id_category.py` rather than expecting the check by eye. What is decidable, and is graded, is a collision inside the change itself and a collision with what the edited file already declared. Corpus: Give a new checker a message id that no existing checker already uses.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/language_style.py:79`](../compliance/rules/pylint_dev/language_style.py#L79) · source: https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/contribute.html

### PYLINT-DEV-C066 — `CheckerClassDeclaresName`

> **Corpus:** Give a new checker class a name attribute.

- **Pre-condition —** each checker class the agent added.
- **Pass condition —** its body assigns a `name` attribute.

Not heuristic: the pass condition is the presence of an attribute the rule names exactly, read off the class body (§6.2), and the pre-condition selects on an exact observable fact -- a class whose bases name a checker and whose lines the agent wrote (§6.3). Corpus: Give a new checker class a name attribute.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/language_style.py:122`](../compliance/rules/pylint_dev/language_style.py#L122) · source: https://pylint.readthedocs.io/en/latest/development_guide/how_tos/custom_checkers.html

### PYLINT-DEV-C067 — `EmittedMessagesAreDeclared`

> **Corpus:** Declare every message a checker emits in its msgs dictionary.

- **Pre-condition —** each `self.add_message("<symbol>", ...)` call, written with a literal name, inside a checker class the agent edited whose module declares messages.
- **Pass condition —** that name is one of the ids or symbols the class's `msgs` dictionary declares.

Heuristic on the **pass condition** (§6.2). A checker may emit a message its *base* class declares, and the base can live in a module the patch never touched, so a name absent from this class is not proof it is undeclared. The pre-condition is exact -- a literal argument at a call site -- and calls that pass a variable are simply not selected rather than guessed at. Corpus: Declare every message a checker emits in its msgs dictionary.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/language_style.py:153`](../compliance/rules/pylint_dev/language_style.py#L153) · source: https://pylint.readthedocs.io/en/latest/development_guide/how_tos/custom_checkers.html

### PYLINT-DEV-C068 — `NodeHandlerNaming`

> **Corpus:** Name a checker's node handlers visit_ or leave_ followed by the lowered astroid class name.

- **Pre-condition —** each `visit_`/`leave_` method the agent wrote on a checker class.
- **Pass condition —** what follows the prefix is a single lowercase token, the form a lowered astroid class name takes.

Heuristic on the **pass condition** (§6.2). Whether the token names a real astroid node class depends on astroid's class list, which is not in the evidence; what is decidable is the *form* the lowering produces -- `visit_classdef`, never `visit_class_def` or `visit_ClassDef`. A mis-spelled but well-formed handler therefore passes, and what this catches is the failure that makes dispatch silently never fire. Corpus: Name a checker's node handlers visit_ or leave_ followed by the lowered astroid class name.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/language_style.py:202`](../compliance/rules/pylint_dev/language_style.py#L202) · source: https://pylint.readthedocs.io/en/latest/development_guide/how_tos/custom_checkers.html

### PYLINT-DEV-C069 — `ModuleLevelRegisterFunction`

> **Corpus:** Add a module-level register function that registers the checker with the linter.

- **Pre-condition —** each module in which the agent added a checker class.
- **Pass condition —** the module defines a top-level `register` function that calls `register_checker`.

Not heuristic: both halves are named exactly by the rule -- a function of that name at module level, and the registration it performs -- so this is presence-checking, not approximation (§6.2). `qualname == name` is what makes the function module-level: a nested one carries its scope in the qualified name. Corpus: Add a module-level register function that registers the checker with the linter.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/language_style.py:246`](../compliance/rules/pylint_dev/language_style.py#L246) · source: https://pylint.readthedocs.io/en/latest/development_guide/how_tos/custom_checkers.html

### PYLINT-DEV-C070 — `MessageIdFormat`

> **Corpus:** Form a message id as one of the five category letters followed by four digits.

- **Pre-condition —** each `msgs` entry the agent wrote in a checker class.
- **Pass condition —** its key is one of `C`, `W`, `E`, `F`, `R` followed by exactly four digits.

Not heuristic: a closed five-letter set and a fixed digit count are a format, and a format has one satisfying shape (§6.2). Corpus: Form a message id as one of the five category letters followed by four digits.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/language_style.py:291`](../compliance/rules/pylint_dev/language_style.py#L291) · source: https://pylint.readthedocs.io/en/latest/development_guide/how_tos/custom_checkers.html

### PYLINT-DEV-C072 — `ConsistentMessageIdPrefix`

> **Corpus:** Keep the first two digits of a checker's message ids the same across that checker.

- **Pre-condition —** each checker class the agent edited that declares more than one well-formed, non-shared message id.
- **Pass condition —** all of those ids begin with the same two digits.

Not heuristic: the comparison is between digits, and the one exception -- shared messages -- is written into the rule's own sentence and read off the entry's `shared` option (§6.2). An id that is not `C0000`-shaped is skipped rather than compared, because its shape is C070's finding and reporting it twice would depress both rates. Corpus: Keep the first two digits of a checker's message ids the same across that checker.


ownership `enclosing` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/language_style.py:321`](../compliance/rules/pylint_dev/language_style.py#L321) · source: https://pylint.readthedocs.io/en/latest/development_guide/how_tos/custom_checkers.html

### PYLINT-DEV-C073 — `SymbolChangesWithTheMessageId`

> **Corpus:** Change the message symbol whenever you change its message id.

- **Pre-condition —** each `msgs` entry whose message id the change removed from the file that declared it -- the observable form of *changing* an id.
- **Pass condition —** the symbol that id carried is no longer declared in the file either.

Not heuristic: both halves are set comparisons between the base and head versions of the same file, which the patch carries (§6.2). The pre-condition selects every id that went away, not only the ones whose symbol survived (§7.1): selecting the latter would find nothing but violations and could never record a compliant rename. Corpus: Change the message symbol whenever you change its message id.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/language_style.py:364`](../compliance/rules/pylint_dev/language_style.py#L364) · source: https://pylint.readthedocs.io/en/latest/development_guide/how_tos/custom_checkers.html

### PYLINT-DEV-C075 — `SharedMessageDeclaresShared`

> **Corpus:** Set the shared option to True on a message used by more than one checker.

- **Pre-condition —** each message id the contribution declares on more than one checker class.
- **Pass condition —** every one of those declarations sets `"shared": True`.

Not heuristic: sharing is observable as the same id declared on two classes, and the option is one value the rule names exactly (§6.2). The workbook files this row *never fires*, and it should: a change that shares no message between checkers finds no target, which is the correct verdict and is not a pass. Corpus: Set the shared option to True on a message used by more than one checker.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/language_style.py:417`](../compliance/rules/pylint_dev/language_style.py#L417) · source: https://pylint.readthedocs.io/en/latest/development_guide/how_tos/custom_checkers.html

### PYLINT-DEV-C076 — `MapReduceMethodsComeAsAPair`

> **Corpus:** Implement get_map_data and reduce_map_data as a matching pair on a checker that reduces data.

- **Pre-condition —** each checker class the agent edited that defines either `get_map_data` or `reduce_map_data`.
- **Pass condition —** both are defined, and `get_map_data` returns something other than `None`.

Not heuristic: the two method names and the non-`None` return are all named by the rule and each is read directly off the class body (§6.2). Selecting on *either* method is what makes the rule two-sided (§7.1); selecting on both would find only the compliant pair. Corpus: Implement get_map_data and reduce_map_data as a matching pair on a checker that reduces data.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/language_style.py:460`](../compliance/rules/pylint_dev/language_style.py#L460) · source: https://pylint.readthedocs.io/en/latest/development_guide/how_tos/custom_checkers.html

### PYLINT-DEV-C080 — `ProxyBaseInTheIsinstanceTuple`

> **Corpus:** Include the astroid proxy base in the isinstance tuple when replacing a hasattr guard.

- **Pre-condition —** each `isinstance` call the agent wrote in a file whose change also removed a `hasattr` guard.
- **Pass condition —** its type tuple names one of the astroid proxy bases -- `Proxy`, `Instance` or `BaseInstance`.

Heuristic on the **pre-condition** (§6.3). *Replacing a hasattr guard* is not something the patch states; what it shows is a file that lost a `hasattr` line and gained an `isinstance` one, and those two need not be the same guard. The pre-condition fires on that superset, which over-reports on a file that happened to do both; matching the removed and added lines to each other would be a guess about the diff's intent rather than a reading of it. Corpus: Include the astroid proxy base in the isinstance tuple when replacing a hasattr guard.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/language_style.py:513`](../compliance/rules/pylint_dev/language_style.py#L513) · source: https://github.com/pylint-dev/pylint/blob/main/AGENTS.md

### PYLINT-DEV-C100 — `NewCheckerClassLivesUnderCheckers`

> **Corpus:** Put a new checker class in the appropriate file under pylint/checkers/.

- **Pre-condition —** each checker class the agent added outside `pylint/extensions/`.
- **Pass condition —** the module that holds it is under `pylint/checkers/`.

Not heuristic: a path prefix is an exact criterion on both layers (§6.2, §6.3). Extensions are excluded from the pre-condition rather than graded and passed: a checker that ships as an extension lives under `pylint/extensions/` by the same guide that puts core checkers under `pylint/checkers/`, and C054 is the row that governs extension checkers. Reading this sentence to cover them would make the two rules contradict (spec §7.5), so the antecedent is narrowed and a test pins that an extension checker finds no target here. Corpus: Put a new checker class in the appropriate file under pylint/checkers/.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pylint_dev/language_style.py:565`](../compliance/rules/pylint_dev/language_style.py#L565) · source: https://github.com/pylint-dev/pylint/blob/main/.github/copilot-instructions.md


# pytest-dev

| category | rules |
|---|---:|
| [Git and commit conventions](#pytest-dev-git-and-commit-conventions) | 2 |
| [PR and release metadata](#pytest-dev-pr-and-release-metadata) | 4 |
| [Tests and test style](#pytest-dev-tests-and-test-style) | 2 |
| [Specialized changes](#pytest-dev-specialized-changes) | 2 |
| [Documentation and docstrings](#pytest-dev-documentation-and-docstrings) | 6 |
| [AI-assisted contribution policy](#pytest-dev-ai-assisted-contribution-policy) | 2 |
| [Code and quality](#pytest-dev-code-and-quality) | 2 |
| [Language and framework style](#pytest-dev-language-and-framework-style) | 2 |


## pytest-dev — Git and commit conventions

### PYTEST-DEV-C031 — `CommitOnlyAfterTestsPass`

> **Corpus:** Commit only after the test suite passes.

- **Pre-condition —** the agent made at least one commit.
- **Pass condition —** a test run appears in the command log before the first `git commit`, and nothing in its output says the suite failed.

Heuristic on the **pass condition** (§6.2). The commit log carries no timestamps that line up with command indices, so *before* is read as the first `git commit` in the command log rather than per commit; and "tests pass" is read from the absence of a failure banner in the captured output, because the runner's exit status is not always recorded. Both are sound in the failing direction and weak in the passing one.


`heuristic` · ownership `created` · reads `commands, commits` · tier `trajectory`

[`compliance/rules/pytest_dev/git_conventions.py:28`](../compliance/rules/pytest_dev/git_conventions.py#L28) · source: https://docs.pytest.org/en/latest/contributing.html

### PYTEST-DEV-C036 — `IssueClosedByKeyword`

> **Corpus:** Add `closes #<issue number>` to the commit message when the change fixes an issue.

- **Pre-condition —** the agent made a commit, read as a change submitted to fix an issue.
- **Pass condition —** an autoclose keyword and issue number appear in a commit message or in the pull request text.

Heuristic on the **pre-condition** (§6.3). The rule's real antecedent is *the change fixes an issue*, and nothing in the bundle establishes that -- the task's provenance is a fact about the benchmark, not about the contribution. Every commit is therefore selected, which over-fires on a change that fixes nothing and pushes the activation rate up. Reported rather than narrowed, because narrowing it would need a harness fact the corpus does not license using. The guide names `closes #XYZW` and links GitHub's documentation, which fixes the whole keyword family, so `fixes` and `resolves` are accepted rather than reported.


`heuristic` · ownership `created` · reads `commits, pr_text` · tier `static`

[`compliance/rules/pytest_dev/git_conventions.py:69`](../compliance/rules/pytest_dev/git_conventions.py#L69) · source: https://docs.pytest.org/en/latest/contributing.html


## pytest-dev — PR and release metadata

### PYTEST-DEV-C020 — `ChangelogFilenameGrammar`

> **Corpus:** Name the changelog file `<issue id>.<type>.rst`.

- **Pre-condition —** each changelog fragment the agent added.
- **Pass condition —** its name is `<issue id>.<type>.rst`.

The trivial-entry exemption the contributing page grants applies to whether a fragment is needed at all, not to how one is named: pytest's `changelogs-rst` pre-commit hook rejects any file under `changelog/` that does not match. So the pre-condition selects added fragments, and a contribution that adds none finds no target.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pytest_dev/pr_metadata.py:37`](../compliance/rules/pytest_dev/pr_metadata.py#L37) · source: https://docs.pytest.org/en/latest/contributing.html

### PYTEST-DEV-C021 — `ChangelogTypeFromTheClosedList`

> **Corpus:** Use one of feature, improvement, bugfix, doc, deprecation, breaking, vendor, packaging, contrib or misc as the changelog entry type.

- **Pre-condition —** each changelog fragment the agent added whose name parses.
- **Pass condition —** its type is one of the ten the project publishes.

A fragment whose name does not parse is C020's finding, not this rule's -- selecting it here would report the same defect twice and depress both rates.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/pytest_dev/pr_metadata.py:64`](../compliance/rules/pytest_dev/pr_metadata.py#L64) · source: https://docs.pytest.org/en/latest/contributing.html

### PYTEST-DEV-C048 — `ChangelogTenseIsPastOrPresent`

> **Corpus:** Write changelog entries in the past or present tense.

- **Pre-condition —** each changelog fragment the agent added that carries prose.
- **Pass condition —** none of its sentences is written in the future or with a modal.

Heuristic on the **pass condition** (§6.2). Tense is grammar, and this detects only its complement: a sentence carrying `will`, `should`, `may` and friends is not past or present, which is sound, but the absence of those words does not prove the sentence is either. Graded one-sidedly for that reason -- it can find a violation, and a pass means only that the common failure is absent.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/pytest_dev/pr_metadata.py:95`](../compliance/rules/pytest_dev/pr_metadata.py#L95) · source: https://github.com/pytest-dev/pytest/blob/main/changelog/README.rst

### PYTEST-DEV-C049 — `ChangelogSentencesArePunctuated`

> **Corpus:** End each changelog sentence with a period.

- **Pre-condition —** each changelog fragment the agent added that carries prose.
- **Pass condition —** every prose paragraph in it ends with a terminating period.

Heuristic on the **pass condition** (§6.2): the rule says *sentences*, and splitting reStructuredText prose into sentences is a proxy. Paragraphs are used as the unit instead, and directive, comment and literal-block lines are skipped, because a `::` line or a `.. note::` is not a sentence and reporting it would be a false violation.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/pytest_dev/pr_metadata.py:131`](../compliance/rules/pytest_dev/pr_metadata.py#L131) · source: https://github.com/pytest-dev/pytest/blob/main/changelog/README.rst


## pytest-dev — Tests and test style

### PYTEST-DEV-C017 — `SuiteRunThroughTox`

> **Corpus:** Run the test suite through tox before submitting the change.

- **Pre-condition —** the agent submitted a contribution.
- **Pass condition —** a `tox` invocation appears in the command log.

Deliberately not "the agent ran tox" -- triggering on the tool would let a contribution that ran nothing collect ``not_applicable``, which is §7.1 inverted. The hedge in the source sentence attaches to *which environments suffice*, not to whether the suite is run through tox at all, so the pass condition does not name an environment.


ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/pytest_dev/tests.py:23`](../compliance/rules/pytest_dev/tests.py#L23) · source: https://docs.pytest.org/en/latest/contributing.html

### PYTEST-DEV-C058 — `TestsIncludedOrUpdated`

> **Corpus:** Include new tests or update existing tests with the change.

- **Pre-condition —** the contribution changes non-test Python source.
- **Pass condition —** it also changes or adds a file under `testing/`.

Heuristic on the **pre-condition** (§6.3). The checklist item carries its own exception -- *when applicable* -- and nothing in the patch settles when a change is exempt. The complement is used instead: a change to shipped source is taken as applicable, and a documentation-only or changelog-only contribution finds no target. That under-reports rather than manufacturing violations against changes the maintainers would exempt.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/pytest_dev/tests.py:49`](../compliance/rules/pytest_dev/tests.py#L49) · source: https://github.com/pytest-dev/pytest/blob/main/.github/PULL_REQUEST_TEMPLATE.md


## pytest-dev — Specialized changes

### PYTEST-DEV-C039 — `DeprecationUsesRemovedInWarning`

> **Corpus:** Raise deprecations through a `PytestRemovedInXWarning` class naming the target major version.

- **Pre-condition —** each file where the contribution announces a deprecation, in prose or with a warning call.
- **Pass condition —** the lines it wrote in that file name a `PytestRemovedInXWarning`.

Heuristic on the **pre-condition** (§6.3): recognising that a change *deprecates* something is a text match over `.. deprecated::`, `@deprecated` and warning calls, and prose can deprecate without any of them. The pass condition is exact -- the class-name form is fixed, and the release machinery filters on it.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pytest_dev/specialized.py:30`](../compliance/rules/pytest_dev/specialized.py#L30) · source: https://docs.pytest.org/en/latest/backwards-compatibility.html

### PYTEST-DEV-C042 — `BreakingChangeShipsDeprecationWarnings`

> **Corpus:** Ship deprecation errors or warnings that help users port their code as part of a breaking change.

- **Pre-condition —** the contribution adds a `breaking` changelog fragment.
- **Pass condition —** it also adds a deprecation warning or error that would help a user port their code.

Heuristic on the **pass condition** (§6.2): *help users fix and port their code* is a judgement, and this reads its mechanical trace -- a `warnings.warn` call, or a warning or error class the change defines. A break that ships a helpful message some other way reads as a violation. The pre-condition is exact: the contribution declares the break itself by typing a changelog fragment `breaking`.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pytest_dev/specialized.py:65`](../compliance/rules/pytest_dev/specialized.py#L65) · source: https://docs.pytest.org/en/latest/backwards-compatibility.html


## pytest-dev — Documentation and docstrings

### PYTEST-DEV-C003 — `DocumentationBuiltWithTox`

> **Corpus:** Build the documentation locally with `tox -e docs` after changing documentation.

- **Pre-condition —** the contribution changes a documentation source under `doc/en/`.
- **Pass condition —** a tox invocation naming the `docs` environment appears in the command log.

Fires on the edit, not on the build (§7.1). The note names one command and offers no alternative build path, so the pass condition is that command rather than any `sphinx-build` invocation the agent might have improvised.


ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/pytest_dev/documentation.py:66`](../compliance/rules/pytest_dev/documentation.py#L66) · source: https://docs.pytest.org/en/latest/contributing.html

### PYTEST-DEV-C004 — `DocstringsUseSphinxFormat`

> **Corpus:** Write docstrings for documented items in the Sphinx docstring format.

- **Pre-condition —** each docstring the agent added.
- **Pass condition —** it carries no section header belonging to a competing docstring format.

Heuristic on the **pass condition** (§6.2). "In the Sphinx format" is broader than anything a pattern can confirm: a docstring with no field list at all is perfectly Sphinx-formatted. So this is graded one-sidedly on its complement -- a numpydoc underline or a Google `Args:` header is positive evidence of the wrong format, and their absence is evidence of nothing in particular.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pytest_dev/documentation.py:96`](../compliance/rules/pytest_dev/documentation.py#L96) · source: https://docs.pytest.org/en/latest/contributing.html

### PYTEST-DEV-C005 — `DocstringSentencesArePunctuated`

> **Corpus:** Start docstring sentences with a capital letter and end them with a period.

- **Pre-condition —** each docstring the agent added that carries text.
- **Pass condition —** its subject line starts with a capital letter and ends with a period.

Heuristic on the **pass condition** (§6.2): the rule says *sentences*, and the subject line is used as the unit because splitting docstring prose into sentences is a proxy that misfires on abbreviations, code spans and reST roles. Both halves the guide names -- an initial capital and a terminating period -- are checked exactly on that line.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pytest_dev/documentation.py:128`](../compliance/rules/pytest_dev/documentation.py#L128) · source: https://docs.pytest.org/en/latest/contributing.html

### PYTEST-DEV-C008 — `DocstringDetailIsASeparateParagraph`

> **Corpus:** Separate a docstring's detailed explanation from its subject line with a blank line.

- **Pre-condition —** each docstring the agent added that carries detail beyond its subject line.
- **Pass condition —** a blank line separates the subject line from that detail.

Not heuristic: the worked example fixes one exact layout, and a blank second line is read straight off the text. A single-line docstring has no detail to separate and finds no target rather than passing vacuously.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pytest_dev/documentation.py:163`](../compliance/rules/pytest_dev/documentation.py#L163) · source: https://docs.pytest.org/en/latest/contributing.html

### PYTEST-DEV-C044 — `BreakingChangeDocumentedInDeprecations`

> **Corpus:** Document the rationale and porting examples for a breaking change in `doc/en/deprecations.rst`.

- **Pre-condition —** the contribution adds a `breaking` changelog fragment.
- **Pass condition —** `doc/en/deprecations.rst` is among the files it changes.

Not heuristic on either layer. The antecedent is the project's own declaration -- a fragment typed `breaking` -- rather than an inference about what the patch does, and the acceptance-list bullet names one tracked file the diff either touches or does not.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pytest_dev/documentation.py:196`](../compliance/rules/pytest_dev/documentation.py#L196) · source: https://docs.pytest.org/en/latest/backwards-compatibility.html

### PYTEST-DEV-C057 — `NewFeatureShipsWithDocumentation`

> **Corpus:** Include documentation in the same change when adding a new feature.

- **Pre-condition —** the contribution adds a `feature` changelog fragment.
- **Pass condition —** it also changes a documentation source under `doc/en/`.

Heuristic on the **pass condition** (§6.2): a changed documentation file is evidence that the feature was documented, not proof that it documents *this* feature. The pre-condition, by contrast, is exact, and deliberately so. The equivalent sphinx-doc rule had to approximate "a new feature" from new public definitions; here the contribution declares it by typing its own changelog fragment `feature`, which is the project's own category rather than this pack's inference.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/pytest_dev/documentation.py:226`](../compliance/rules/pytest_dev/documentation.py#L226) · source: https://github.com/pytest-dev/pytest/blob/main/.github/PULL_REQUEST_TEMPLATE.md


## pytest-dev — AI-assisted contribution policy

### PYTEST-DEV-C009 — `NotPurelyAgentic`

> **Corpus:** Do not submit a contribution generated entirely by an AI agent without meaningful human review and oversight.

- **Pre-condition —** a named model produced a contribution.
- **Pass condition —** a human reviewed, understood and took responsibility for it.

``by_construction`` (§6.5), not heuristic: the check itself is exact -- the harness records that a model produced the patch with nobody in the loop -- and it is the *setup*, not the evidence, that makes compliance impossible. Scored so the report can separate it, because an excluded rule cannot be shown to a guided agent and then reported on. The policy welcomes tool use and draws its line at absent oversight, so there is no compliant form of an unreviewed autonomous submission to select for.


ownership `created` · reads `files` · tier `trajectory`

[`compliance/rules/pytest_dev/ai_policy.py:35`](../compliance/rules/pytest_dev/ai_policy.py#L35) · source: https://docs.pytest.org/en/latest/contributing.html

### PYTEST-DEV-C062 — `AiAgentsCreditedInTrailers`

> **Corpus:** Credit AI agents that were used in `Co-authored-by` commit trailers.

- **Pre-condition —** the agent made a commit in a run a model produced.
- **Pass condition —** a `Co-authored-by` trailer names an AI tool.

Heuristic on the **pass condition** (§6.2): the trailer's *form* is exact, but deciding whether the co-author named in it is an AI is a match against a vocabulary of tool names. A model credited under a name outside that list reads as a violation. Not ``by_construction``: nothing stops an agent writing the trailer. The contributing page calls it optional while the pull-request checklist makes it a box to tick, and the corpus takes the stricter reading -- so this measures whether agents credit themselves when asked to, which is a real behavioural question.


`heuristic` · ownership `created` · reads `commits` · tier `static`

[`compliance/rules/pytest_dev/ai_policy.py:69`](../compliance/rules/pytest_dev/ai_policy.py#L69) · source: https://github.com/pytest-dev/pytest/blob/main/.github/PULL_REQUEST_TEMPLATE.md


## pytest-dev — Code and quality

### PYTEST-DEV-C015 — `PreCommitInstalled`

> **Corpus:** Install and enable pre-commit on the pytest checkout.

- **Pre-condition —** the agent submitted a contribution.
- **Pass condition —** a `pre-commit install` invocation appears in the command log.

The guide ties the step to style-guide enforcement and offers no alternative, so the satisfying state is the named command. Enabling without installing leaves no trace the bundle carries, which is a limit of the evidence rather than a reading of the rule.


ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/pytest_dev/code_quality.py:26`](../compliance/rules/pytest_dev/code_quality.py#L26) · source: https://docs.pytest.org/en/latest/contributing.html

### PYTEST-DEV-C018 — `LintingEnvironmentRun`

> **Corpus:** Run the `linting` tox environment to perform the coding-style checks.

- **Pre-condition —** the agent submitted a contribution.
- **Pass condition —** a tox invocation naming the `linting` environment appears in the command log.

Separate from C017 on purpose: `tox -e linting,py313` satisfies both, but a run of the test environments alone satisfies only C017, and the coding-style checks are what this rule is about.


ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/pytest_dev/code_quality.py:51`](../compliance/rules/pytest_dev/code_quality.py#L51) · source: https://docs.pytest.org/en/latest/contributing.html


## pytest-dev — Language and framework style

### PYTEST-DEV-C016 — `Pep8Naming`

> **Corpus:** Follow PEP-8 naming conventions in Python code.

- **Pre-condition —** each module-level function and class the agent added.
- **Pass condition —** functions are `snake_case`, classes are `CapWords`, and neither is one of the single characters PEP-8 rules out.

Heuristic on the **pass condition** (§6.2). PEP-8's naming section is wider than case conventions -- it covers constants, leading underscores, name mangling and package names -- and this checks the two forms that are mechanically decidable from a definition's name. A name that satisfies both can still breach PEP-8 elsewhere, so a pass is weaker than the rule.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pytest_dev/language_style.py:41`](../compliance/rules/pytest_dev/language_style.py#L41) · source: https://docs.pytest.org/en/latest/contributing.html

### PYTEST-DEV-C045 — `RunsOnPython310`

> **Corpus:** Write code that runs on Python 3.10 and later.

- **Pre-condition —** each Python file the agent edited.
- **Pass condition —** the lines it wrote use no standard-library module, typing name or syntax that arrived after 3.10.

Heuristic on the **pass condition** (§6.2), and graded one-sidedly. Proving that code runs on 3.10 needs an interpreter; what is decidable from the patch is a list of things that provably do not. So a hit is a real violation of the floor `pyproject.toml` records as `target-version = py310`, and a pass means only that none of the listed markers is present.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/pytest_dev/language_style.py:100`](../compliance/rules/pytest_dev/language_style.py#L100) · source: https://docs.pytest.org/en/latest/backwards-compatibility.html


# scikit-learn

| category | rules |
|---|---:|
| [Git and commit conventions](#scikit-learn-git-and-commit-conventions) | 2 |
| [PR and release metadata](#scikit-learn-pr-and-release-metadata) | 6 |
| [Tests and test style](#scikit-learn-tests-and-test-style) | 16 |
| [Specialized changes](#scikit-learn-specialized-changes) | 8 |
| [Documentation and docstrings](#scikit-learn-documentation-and-docstrings) | 35 |
| [AI-assisted contribution policy](#scikit-learn-ai-assisted-contribution-policy) | 5 |
| [Code and quality](#scikit-learn-code-and-quality) | 2 |
| [Language and framework style](#scikit-learn-language-and-framework-style) | 72 |


## scikit-learn — Git and commit conventions

### SCIKIT-LEARN-C054 — `DocumentationTitleCarriesTheDocPrefix`

> **Corpus:** Prefix a documentation PR's title with "DOC".

- **Pre-condition —** a contribution whose every changed path is documentation.
- **Pass condition —** the title that becomes the commit message starts with `DOC`.

Fires on the *documentation contribution*, not on titles already carrying the prefix (§7.1): the corpus Notes state the trigger as "applies only to documentation-only contributions", so a code change finds no target here and a documentation change with an unprefixed title is a recorded violation. Heuristic on the **pass condition** (§6.2): the run carries no pull-request title field, so "the title" is the first written line of the PR text, falling back to the latest commit summary. A run that recorded neither withholds nothing -- it reports the violation, because a contribution with no message at all carries no prefix either.


`heuristic` · ownership `created` · reads `files, pr_text, commits` · tier `static`

[`compliance/rules/scikit_learn/git_conventions.py:59`](../compliance/rules/scikit_learn/git_conventions.py#L59) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C055 — `CiMarkerIsInTheLatestCommit`

> **Corpus:** Put a CI commit-message marker in the latest commit message for it to take effect.

- **Pre-condition —** a run whose commit messages carry a published CI marker.
- **Pass condition —** the newest commit is one of the messages carrying it.

§7.1 in miniature. The marker is optional -- the corpus Notes say so -- so the antecedent is *having chosen to steer CI from a commit message*, and the graded question is whether it was put where CI reads it. Selecting only runs whose newest commit carries a marker would record compliance and never its absence. Not heuristic: the marker table is closed and published, and "latest commit" is the first element of ``bundle.commits``, which the log parser emits newest first.


ownership `created` · reads `commits` · tier `static`

[`compliance/rules/scikit_learn/git_conventions.py:101`](../compliance/rules/scikit_learn/git_conventions.py#L101) · source: https://scikit-learn.org/dev/developers/contributing.html


## scikit-learn — PR and release metadata

### SCIKIT-LEARN-C042 — `PullRequestTitleIsNotABareIssueReference`

> **Corpus:** Do not use a bare "Fix #<ISSUE NUMBER>" as the PR title.

- **Pre-condition —** a run that recorded a pull-request title or a commit summary.
- **Pass condition —** that title is more than a bare `Fix #<ISSUE NUMBER>`.

A prohibition, so the pre-condition selects the *permitted* form of the act -- having written a title -- and the pass condition checks it was not the prohibited one (§7.1). Selecting titles that already match `Fix #N` would find only violations and could never record a compliant title. Heuristic on the **pass condition** (§6.2): the run carries no title field, so the title is recovered from the first written line of the PR text, falling back to the latest commit summary, and the pattern also admits the `Fixes #1234`/`Closes gh-12` spellings of the same non-title.


`heuristic` · ownership `created` · reads `pr_text, commits` · tier `static`

[`compliance/rules/scikit_learn/pr_metadata.py:66`](../compliance/rules/scikit_learn/pr_metadata.py#L66) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C048 — `ChangelogFragmentAddedForAUserFacingChange`

> **Corpus:** Add a changelog fragment describing the change when the PR is likely to affect users.

- **Pre-condition —** a contribution that changes package code outside the tests.
- **Pass condition —** it adds a news fragment under `doc/whats_new/upcoming_changes/` carrying a written line.

Heuristic on the **pre-condition** (§6.3): "likely to affect users" is not observable, and is approximated by *the contribution changes `sklearn/` code that is not a test*. That is a superset -- a private refactor affects nobody and would still be selected -- and the wider scope is the right direction of error (§4.5).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/pr_metadata.py:103`](../compliance/rules/scikit_learn/pr_metadata.py#L103) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C268 — `FragmentIsNamedPullRequestDotTypeDotRst`

> **Corpus:** Name the changelog fragment <PULL REQUEST>.<TYPE>.rst.

- **Pre-condition —** each news fragment the contribution adds.
- **Pass condition —** its filename is `<PULL REQUEST>.<TYPE>.rst`.

Not heuristic: towncrier reads the name, the README fixes its shape, and the check is a match against that shape. The pull-request number is graded only as *digits*, because a run has no pull request and so no number to compare against -- a property of the harness, not an approximation in the rule.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/pr_metadata.py:143`](../compliance/rules/scikit_learn/pr_metadata.py#L143) · source: https://github.com/scikit-learn/scikit-learn/blob/main/doc/whats_new/upcoming_changes/README.md

### SCIKIT-LEARN-C269 — `FragmentTypeIsOneOfTheSeven`

> **Corpus:** Use one of the seven documented fragment types in the changelog filename.

- **Pre-condition —** each added news fragment whose name carries a type component.
- **Pass condition —** that component is one of the seven documented types.

The antecedent is narrowed to names that *have* a type at all, so a fragment named nothing like the published shape is C268's finding and is not counted twice (§7.5). Not heuristic: the seven tokens are a closed published list.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/pr_metadata.py:172`](../compliance/rules/scikit_learn/pr_metadata.py#L172) · source: https://github.com/scikit-learn/scikit-learn/blob/main/doc/whats_new/upcoming_changes/README.md

### SCIKIT-LEARN-C270 — `FragmentSitsInTheFolderForTheChangedModule`

> **Corpus:** Put the fragment in the folder matching the module the PR changes.

- **Pre-condition —** each added news fragment in a contribution that also changes package code.
- **Pass condition —** its folder names one of the changed modules, or is one of the topic folders the README allows.

Heuristic on the **pass condition** (§6.2): "the module the PR changes" is derived from the top-level `sklearn/<subpackage>` of each changed path, which is the folder naming convention the README's own examples use, and the topic folders (`array-api`, `metadata-routing`, `security`) are accepted unconditionally because which change belongs to a topic is a maintainer's judgement, not a fact in the patch.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/pr_metadata.py:205`](../compliance/rules/scikit_learn/pr_metadata.py#L205) · source: https://github.com/scikit-learn/scikit-learn/blob/main/doc/whats_new/upcoming_changes/README.md

### SCIKIT-LEARN-C271 — `FragmentIsASingleBulletPoint`

> **Corpus:** Write the changelog fragment as a single bullet point.

- **Pre-condition —** each added news fragment carrying a written line.
- **Pass condition —** exactly one top-level reST bullet.

Not heuristic: the README states the count and states why -- the aggregation software cannot handle a second bullet per entry -- so a count is compared against a number. Continuation lines are indented and belong to the bullet above them, which is what makes counting column-zero bullets the right reading rather than an approximation.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/pr_metadata.py:244`](../compliance/rules/scikit_learn/pr_metadata.py#L244) · source: https://github.com/scikit-learn/scikit-learn/blob/main/doc/whats_new/upcoming_changes/README.md


## scikit-learn — Tests and test style

### SCIKIT-LEARN-C029 — `NewTestsAccompanyTheChange`

> **Corpus:** Add new tests for the bug fix or feature the PR contributes.

- **Pre-condition —** a contribution that changes package code outside the tests.
- **Pass condition —** it also adds at least one test function.

Heuristic on the **pre-condition** (§6.3): "the bug-fixes or new features the PR contributes" is approximated by *package source changed*, a superset that also catches refactors nobody would ask for a test about. Fires on the change rather than on the test, so a contribution that adds nothing is a recorded failure rather than an absent row -- IMPLEMENTATION_PLAN.md §4.2's worked case for invariant 2.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/tests.py:117`](../compliance/rules/scikit_learn/tests.py#L117) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C030 — `NewTestsFailBeforeAndPassAfter`

> **Corpus:** Make a bug-fix's new tests fail on unpatched main and pass with the patch applied.

- **Pre-condition —** a contribution that changes package code and adds a test.
- **Pass condition —** the harness reports at least one test that failed on the base commit and passes with the patch.

Heuristic on the **pre-condition** (§6.3), which approximates *bug fix* by source-plus-test -- the spec's own worked example of a rule flagged on its selecting layer while its grading layer is a tool's exact verdict. Withholds when the run was never graded, which is a named missing input (``evaluation``), not a judgement.


`heuristic` · ownership `touched` · reads `files, evaluation` · tier `differential`

[`compliance/rules/scikit_learn/tests.py:152`](../compliance/rules/scikit_learn/tests.py#L152) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C033 — `TheSuitePassesBeforeOpeningThePr`

> **Corpus:** Make the test suite pass locally before opening the PR.

- **Pre-condition —** the agent submitted a contribution.
- **Pass condition —** the harness reports no test broken by it and none of the tests it was meant to fix still failing.

Deliberately not "the agent ran the suite": the checklist item is that the tests *pass*, so a contribution that never ran them is judged rather than excused. Not heuristic -- the verdict is a tool's own report (§6.2) -- and it withholds, rather than passing, when the run was never graded.


ownership `touched` · reads `files, evaluation` · tier `differential`

[`compliance/rules/scikit_learn/tests.py:193`](../compliance/rules/scikit_learn/tests.py#L193) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C106 — `TestsLiveInTheModulesTestsSubdirectory`

> **Corpus:** Put tests in the module's tests/ subdirectory as appropriately named functions.

- **Pre-condition —** each test function the agent added, named `test_*` or `*_test`.
- **Pass condition —** it sits in a `sklearn/<module>/tests/test_*.py` module and its own name carries the `test_` prefix pytest collects on.

Heuristic on the **pre-condition** (§6.3): "a test" is recognised by the two naming conventions pytest publishes, so a test written under a third name is invisible here exactly as it is to the test runner. Both halves of the sentence are graded -- the `*_test` spelling is selected precisely so the naming half can fail on something.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/tests.py:233`](../compliance/rules/scikit_learn/tests.py#L233) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C127 — `ADeprecationCarriesAWarningTest`

> **Corpus:** Add a test asserting the deprecation warning is raised only in the relevant cases.

- **Pre-condition —** a contribution that deprecates a name.
- **Pass condition —** one of the tests it adds or edits asserts the deprecation warning is raised, with `pytest.warns`.

Heuristic on **both layers** (§6.3, §6.2). The pre-condition recognises a deprecation by the `@deprecated` decorator, so one announced only in prose is missed. The pass condition is narrower than the sentence: it confirms the warning is asserted and does **not** confirm the second half -- *and not in other cases* -- because a test that demonstrates the warning's absence has no single recognisable shape. Stated here rather than left for a reader to discover.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/tests.py:284`](../compliance/rules/scikit_learn/tests.py#L284) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C128 — `OtherTestsCatchTheDeprecationWarning`

> **Corpus:** Catch the deprecation warning in every other test, e.g. with @pytest.mark.filterwarnings.

- **Pre-condition —** in a contribution that deprecates a name, each test the agent wrote or edited that uses that name without asserting the warning.
- **Pass condition —** it catches the warning -- `@pytest.mark.filterwarnings`, `warnings.catch_warnings`, or an explicit filter.

Heuristic on **both layers** (§6.3, §6.2): the deprecated name is recognised from the `@deprecated` decorator and its use from the test's source text, and "caught" is accepted in the forms the project's own tests use, the marker being the one the sentence names by example. The warning test itself is excluded, because that one is C127's target and grading it here would report one artefact under two rules (§7.5).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/tests.py:325`](../compliance/rules/scikit_learn/tests.py#L325) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C129 — `GalleryExamplesAreFreeOfTheDeprecationWarning`

> **Corpus:** Leave the gallery examples free of the deprecation warning.

- **Pre-condition —** in a contribution that deprecates a name, each gallery example under `examples/` the contribution touches.
- **Pass condition —** the example does not use the deprecated name.

Narrowed to examples *in the patch* on purpose: the documentation build checks the whole gallery, and the bundle carries only what the contribution changed, so the pre-condition fires on the examples the agent is answerable for. Heuristic on **both layers** (§6.3, §6.2) -- the deprecation is recognised by decorator, the use by name -- and the narrowing means a warning left in an untouched example is out of scope rather than silently passed.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/tests.py:376`](../compliance/rules/scikit_learn/tests.py#L376) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C184 — `TestsImportFromThePublicLocation`

> **Corpus:** Import the object under test from its public location, as client code would.

- **Pre-condition —** each `from sklearn...` import in a test module the agent edited.
- **Pass condition —** the module it names carries no private component.

Heuristic on the **pass condition** (§6.2): "as client code would" means importing from the module that *exports* the object, which no checker can know without the package's own `__init__` files, so a leading-underscore component stands in for it -- the guide's worked case, `sklearn.foo.bar.baz`, is private in exactly this way. `sklearn.utils._testing` and its siblings are exempted by name because the project's own testing rule C197 points tests at them; without that exemption the two rules would contradict each other (§7.5).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/tests.py:415`](../compliance/rules/scikit_learn/tests.py#L415) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C197 — `QuasiEqualityUsesTheProjectsAssertAllclose`

> **Corpus:** Assert quasi-equality of float arrays with sklearn.utils._testing.assert_allclose.

- **Pre-condition —** each approximate-array-equality assertion in a test the agent wrote or edited.
- **Pass condition —** the helper called is `sklearn.utils._testing.assert_allclose`.

Heuristic on the **pre-condition** (§6.3): "asserting the quasi-equality of arrays of continuous values" is approximated by the family of near-equality assertions -- numpy's `assert_almost_equal` and friends alongside `assert_allclose` -- so an equality asserted through a bare `assert` is not selected. The pass condition resolves the written name through the module's import table, so `assert_allclose` imported from numpy is told apart from the project's own.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/tests.py:462`](../compliance/rules/scikit_learn/tests.py#L462) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C198 — `ZeroComparisonsPassAnAbsoluteTolerance`

> **Corpus:** Pass a non-zero atol when comparing arrays containing zeros.

- **Pre-condition —** each `assert_allclose` call the agent wrote or edited whose arguments contain a zero.
- **Pass condition —** it passes a non-zero `atol`.

Heuristic on the **pre-condition** (§6.3): "arrays of zero-elements" is approximated by a literal `0`, `0.0` or a `np.zeros(...)` call among the arguments, so an array of zeros arriving through a variable is not selected. The pass condition is exact -- relative tolerance alone is meaningless against zero, and `atol` either appears with a non-zero value or does not.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/tests.py:503`](../compliance/rules/scikit_learn/tests.py#L503) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C208 — `MatplotlibTestsTakePyplotFirst`

> **Corpus:** Take the pyplot fixture as the first argument of every test that needs matplotlib.

- **Pre-condition —** each test the agent wrote or edited whose module uses matplotlib.
- **Pass condition —** `pyplot` is its first parameter.

Heuristic on the **pre-condition** (§6.3): "every test that requires it" is approximated by the test module importing or naming matplotlib, which is a superset -- a test in such a module that never plots is still selected. The pass condition is exact: a position in a parameter list, which is stricter than the contributing guide's version of the same sentence and is what the plotting page says.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/tests.py:551`](../compliance/rules/scikit_learn/tests.py#L551) · source: https://scikit-learn.org/dev/developers/plotting.html

### SCIKIT-LEARN-C232 — `TestsSeedTheirOwnRngInstance`

> **Corpus:** Seed each test's own RNG instance instead of relying on the global RNG singletons.

- **Pre-condition —** each test the agent wrote or edited that draws random numbers.
- **Pass condition —** it does so through its own generator, not a module-level RNG routine.

A prohibition read as the guide states it, so the antecedent is *using randomness* and the graded question is which RNG (§7.1). Heuristic on the **pre-condition** (§6.3): randomness is recognised from the call names in the test body, so a helper that draws numbers on the test's behalf is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/tests.py:593`](../compliance/rules/scikit_learn/tests.py#L593) · source: https://scikit-learn.org/dev/developers/global_configuration.html

### SCIKIT-LEARN-C233 — `GlobalRandomSeedTestsPassForEverySeed`

> **Corpus:** Make a test using the global_random_seed fixture pass for every seed from 0 to 99.

- **Pre-condition —** each test the agent wrote or edited that takes the `global_random_seed` fixture.
- **Pass condition —** it passes for every seed in the range, which the bundle can only contradict.

**Graded one-sidedly, and that is the honest shape.** The bundle carries one run at one seed: a failure recorded by the harness disproves "passes for every seed from 0 to 99" outright, while a success establishes nothing about the other ninety-nine. So this fails on evidence and withholds otherwise, never passing vacuously. ``repeated_runs`` is declared as the Phase 5 source that would settle it, which is what makes the withhold a named missing input rather than a judgement call (§5).


ownership `touched` · reads `files, evaluation, repeated_runs` · tier `differential`

[`compliance/rules/scikit_learn/tests.py:634`](../compliance/rules/scikit_learn/tests.py#L634) · source: https://scikit-learn.org/dev/developers/global_configuration.html

### SCIKIT-LEARN-C234 — `NewSeedTestsAreRunOverAllSeeds`

> **Corpus:** Run a new global_random_seed test with SKLEARN_TESTS_GLOBAL_RANDOM_SEED="all" before submitting.

- **Pre-condition —** each test the agent *added* that takes the `global_random_seed` fixture.
- **Pass condition —** a command in the log runs pytest with `SKLEARN_TESTS_GLOBAL_RANDOM_SEED="all"`.

Fires on writing the test, never on having run the command (§7.1) -- selecting the invocation would find only agents that already complied. Not heuristic: the sentence supplies one environment variable and one invocation, and the command log either contains them or does not.


ownership `created` · reads `files, commands` · tier `trajectory`

[`compliance/rules/scikit_learn/tests.py:687`](../compliance/rules/scikit_learn/tests.py#L687) · source: https://scikit-learn.org/dev/developers/global_configuration.html

### SCIKIT-LEARN-C243 — `ThePythonReferenceImplementationMovesToTheTests`

> **Corpus:** Keep the Python version of a compiled function in the tests as the reference implementation.

- **Pre-condition —** a contribution that adds a compiled extension source file.
- **Pass condition —** it also adds a non-test helper function to a test module -- the gold standard Python version the extension is asserted against.

Heuristic on **both layers** (§6.3, §6.2). The pre-condition approximates *a Python function was replaced by a compiled extension* by the extension appearing. The pass condition approximates *the Python version was moved into the tests* by a plain function being added to a test module, which is the structure the step describes; a reference implementation kept in a fixture file the contribution does not touch would be missed.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/tests.py:727`](../compliance/rules/scikit_learn/tests.py#L727) · source: https://scikit-learn.org/dev/developers/performance.html

### SCIKIT-LEARN-C245 — `PytestRunsWithFutureWarningsAsErrors`

> **Corpus:** Run the tests with -Werror::FutureWarning so uncaught FutureWarnings fail locally.

- **Pre-condition —** the agent ran pytest at least once.
- **Pass condition —** at least one of those runs carries `-Werror::FutureWarning`.

Fires on running the tests -- the act the rule qualifies -- never on the flag (§7.1). A run that never invoked pytest finds no target, which is right: the sentence qualifies how the suite is run, and C033 is the rule about it passing. Not heuristic: the flag is a literal string in a command line.


ownership `touched` · reads `commands` · tier `trajectory`

[`compliance/rules/scikit_learn/tests.py:767`](../compliance/rules/scikit_learn/tests.py#L767) · source: https://scikit-learn.org/dev/developers/tips.html


## scikit-learn — Specialized changes

### SCIKIT-LEARN-C210 — `MemoryviewsAreNotSliced`

> **Corpus:** Do not slice memoryviews in Cython code.

- **Pre-condition —** each Cython file the agent edited that declares a typed memoryview.
- **Pass condition —** no declared memoryview is subscripted with a slice.

A prohibition, so the pre-condition selects the situation that invokes it -- Cython code that has memoryviews to slice -- and never the slices themselves (§7.1). Heuristic on **both layers** (§6.3, §6.2): declarations and slice subscripts are recognised textually, so a memoryview obtained from a function's return value is not tracked, and a slice of a NumPy array sharing a name with a memoryview is reported.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/specialized.py:87`](../compliance/rules/scikit_learn/specialized.py#L87) · source: https://scikit-learn.org/dev/developers/cython.html

### SCIKIT-LEARN-C211 — `FinalCythonClassesCarryFinal`

> **Corpus:** Decorate final Cython classes and methods with @final.

- **Pre-condition —** each `cdef class` in a Cython file the agent edited that nothing in that file subclasses.
- **Pass condition —** it is decorated `@final`.

Heuristic on the **pre-condition** (§6.3): *final* means nothing anywhere subclasses the type, and only the files in the contribution are visible, so finality is approximated by "not subclassed in the file that defines it". The pass condition is exact -- one named decorator, present or absent.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/specialized.py:128`](../compliance/rules/scikit_learn/specialized.py#L128) · source: https://scikit-learn.org/dev/developers/cython.html

### SCIKIT-LEARN-C214 — `GilIsReleasedExplicitly`

> **Corpus:** Release the GIL explicitly with prange(nogil=True) or a with nogil block.

- **Pre-condition —** each Cython file the agent edited that declares a `nogil` function.
- **Pass condition —** the file releases the GIL explicitly, with `with nogil` or `prange(..., nogil=True)`.

The antecedent is the declaration, which the page states does nothing by itself; the graded artefact is the explicit release. Heuristic on the **pre-condition** (§6.3), which recognises a `nogil` declaration textually, and on the **pass condition**, which asks the question per file rather than per declared function -- a file with two `nogil` functions and one `with nogil` block passes.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/specialized.py:168`](../compliance/rules/scikit_learn/specialized.py#L168) · source: https://scikit-learn.org/dev/developers/cython.html

### SCIKIT-LEARN-C216 — `DirectOpenMpCallsAreProtected`

> **Corpus:** Guard every direct OpenMP call so the code still builds without OpenMP.

- **Pre-condition —** each Cython file the agent edited that calls an OpenMP routine.
- **Pass condition —** the file takes its routines from `sklearn.utils._openmp_helpers`, or guards them so the code still builds without OpenMP.

Heuristic on **both layers** (§6.3, §6.2): an OpenMP call is recognised by the `omp_` prefix, and "protected" is accepted in either of the two forms the page shows -- the helper module, which supplies protected versions, or a build-time guard. A third way of protecting a call would read as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/specialized.py:207`](../compliance/rules/scikit_learn/specialized.py#L207) · source: https://scikit-learn.org/dev/developers/cython.html

### SCIKIT-LEARN-C217 — `OpenMpRoutinesAreCimportedFromTheHelpers`

> **Corpus:** cimport OpenMP routines from sklearn.utils._openmp_helpers, not from the OpenMP library.

- **Pre-condition —** each `cimport` of an OpenMP routine in a Cython file the agent edited.
- **Pass condition —** it names `sklearn.utils._openmp_helpers` as the module.

Not heuristic: the page names one module as the source and forbids the library, and a cimport statement names its module exactly. `prange` is deliberately not selected -- the page exempts it, being already protected by Cython itself.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/specialized.py:246`](../compliance/rules/scikit_learn/specialized.py#L246) · source: https://scikit-learn.org/dev/developers/cython.html

### SCIKIT-LEARN-C218 — `CythonCodeDeclaresExplicitTypes`

> **Corpus:** Declare explicit types in Cython code.

- **Pre-condition —** each function defined in a Cython file the agent edited that takes a parameter other than `self`.
- **Pass condition —** every one of those parameters carries a type.

Heuristic on the **pass condition** (§6.2): a parameter is read as typed when something precedes its name -- a type token, a memoryview shape, or a Python annotation -- which is how Cython declares one; a `cdef` block declaring types on separate lines inside the body is not seen, and neither is a return type. The sentence covers all explicit typing, and this checks the signature.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/specialized.py:286`](../compliance/rules/scikit_learn/specialized.py#L286) · source: https://scikit-learn.org/dev/developers/cython.html

### SCIKIT-LEARN-C220 — `NoSelfDocumentingFstringsInCython`

> **Corpus:** Do not use {var=} f-string expressions in Cython code.

- **Pre-condition —** each Cython file the agent edited that contains an f-string.
- **Pass condition —** none of them uses the `{var=}` form.

A prohibition, so the antecedent is *using f-strings at all* and the graded question is whether the rejected form appears (§7.1). Not heuristic: the rule names the construct exactly, and Cython's parser -- not a matter of taste -- is what rejects it.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/specialized.py:328`](../compliance/rules/scikit_learn/specialized.py#L328) · source: https://scikit-learn.org/dev/developers/cython.html

### SCIKIT-LEARN-C235 — `PullRequestCiDoesNotSetTheGlobalSeed`

> **Corpus:** Do not set SKLEARN_TESTS_GLOBAL_RANDOM_SEED in the pull-request CI configuration.

- **Pre-condition —** each pull-request CI configuration file the contribution edits.
- **Pass condition —** none of the lines the agent wrote sets `SKLEARN_TESTS_GLOBAL_RANDOM_SEED`.

A prohibition, so the pre-condition selects *editing the CI configuration* -- the permitted act -- rather than the setting the rule forbids (§7.1); the corpus Notes state the trigger the same way. Heuristic on the **pre-condition** (§6.3): which files are "the pull-request CI configuration" is approximated by the workflow, build tools and pipeline paths in ``_common.CI_PATHS``, since nothing in the patch says which configuration a given file belongs to.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/specialized.py:362`](../compliance/rules/scikit_learn/specialized.py#L362) · source: https://scikit-learn.org/dev/developers/global_configuration.html


## scikit-learn — Documentation and docstrings

### SCIKIT-LEARN-C036 — `NewFeatureHasNarrativeUserGuideDocumentation`

> **Corpus:** Illustrate a new feature with narrative user-guide documentation containing small code snippets.

- **Pre-condition —** a contribution that adds a new public definition to `sklearn/`.
- **Pass condition —** it also writes user-guide reStructuredText containing a code snippet.

Heuristic on **both layers** (§6.3, §6.2). "A new feature" is approximated by a new public function or class; "narrative documentation with small code snippets" is approximated by written lines in a `doc/` page carrying a doctest prompt, a `code-block` directive or a literal block. Fires on the feature, never on the documentation, so a feature documented nowhere is a recorded failure (§7.1).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:200`](../compliance/rules/scikit_learn/documentation.py#L200) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C038 — `UserGuideStatesComplexityAndScalability`

> **Corpus:** State the algorithm's expected time and space complexity and its scalability in the user guide.

- **Pre-condition —** a contribution that adds a new public definition and writes user-guide reStructuredText for it.
- **Pass condition —** those lines state the algorithm's complexity and its scalability.

Narrowed to contributions that *did* write a user-guide section, because the absence of one is C036's finding and one defect must not depress two rates (§7.5). Heuristic on **both layers** (§6.3, §6.2): the feature proxy again, and "expected time and space complexity ... and scalability" is recognised by vocabulary -- `complexity`, `O(...)`, `scale`/`scalability` -- which a paragraph could satisfy in other words.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:235`](../compliance/rules/scikit_learn/documentation.py#L235) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C039 — `NewFeatureHasAGalleryExample`

> **Corpus:** Add a usage example under examples/ for a new feature.

- **Pre-condition —** a contribution that adds a new public definition to `sklearn/`.
- **Pass condition —** it adds a Python example under `examples/`.

Heuristic on the **pre-condition** (§6.3): the new-feature proxy. The pass condition is exact -- one directory is named, and a file either appears in it or does not.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:280`](../compliance/rules/scikit_learn/documentation.py#L280) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C060 — `ApiDocumentationLivesBesideTheCode`

> **Corpus:** Keep function, method and class docstrings alongside the code in sklearn/.

- **Pre-condition —** each public function or class the agent adds under `sklearn/`.
- **Pass condition —** it carries a docstring in the file that defines it.

The sentence places API documentation *alongside the code in `sklearn/`*, so the graded question is whether the object the agent added documents itself there rather than being described only in `doc/`. Heuristic on the **pre-condition** (§6.3): "function/method/class" is narrowed to public definitions, since the leading underscore is the project's own marker for what is not API.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:308`](../compliance/rules/scikit_learn/documentation.py#L308) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C062 — `GalleryExamplesLiveUnderExamples`

> **Corpus:** Put gallery examples under examples/.

- **Pre-condition —** each Python file the contribution adds that is written as a gallery example.
- **Pass condition —** it sits under `examples/`.

Heuristic on the **pre-condition** (§6.3): a gallery example is recognised by the two marks sphinx-gallery reads -- a `plot_`-prefixed filename or `# %%` cell separators -- so an example written without either is not selected. Fires on the example, wherever it was put, rather than on `examples/` itself; selecting the directory would find only files already in the right place (§7.1).


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:356`](../compliance/rules/scikit_learn/documentation.py#L356) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C064 — `DocstringSectionsAreInTheStatedOrder`

> **Corpus:** Order docstring sections Parameters, Returns, See Also, Notes, Examples.

- **Pre-condition —** each docstring the agent wrote or edited carrying at least two of Parameters, Returns, See Also, Notes and Examples.
- **Pass condition —** those sections appear in that order.

Not heuristic: the guide states the sequence, and the check compares two lists. Sections outside the five are ignored rather than guessed at, because the guide explicitly defers to numpydoc for the rest.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:399`](../compliance/rules/scikit_learn/documentation.py#L399) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C065 — `ParameterTypesUsePythonBasicNames`

> **Corpus:** Name parameter types with Python basic type names, e.g. bool rather than boolean.

- **Pre-condition —** each Parameters entry in a docstring the agent wrote or edited.
- **Pass condition —** its type line uses no long-hand spelling of a Python basic type.

Heuristic on the **pass condition** (§6.2): the guide gives one worked pair (`bool` for `boolean`) and leaves the rest to "use Python basic types", so the list of wrong spellings -- boolean, integer, string, dictionary -- is this pack's, not the project's. A fifth long-hand name would pass.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:436`](../compliance/rules/scikit_learn/documentation.py#L436) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C066 — `ArrayShapesAreParenthesised`

> **Corpus:** Write array shapes in parentheses after 'of shape'.

- **Pre-condition —** each Parameters entry the agent wrote or edited whose type line says `of shape`.
- **Pass condition —** a parenthesised shape follows those words.

Not heuristic: the phrase and the parenthesis are both exact, and the guide gives the form with worked examples and no alternative.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:466`](../compliance/rules/scikit_learn/documentation.py#L466) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C067 — `StringOptionsAreABraceEnclosedSet`

> **Corpus:** Write a string parameter's allowed values as a brace-enclosed set.

- **Pre-condition —** each Parameters entry the agent wrote or edited whose type line offers two or more quoted string values.
- **Pass condition —** they are enclosed in braces.

Heuristic on the **pre-condition** (§6.3): "strings with multiple options" is approximated by counting quoted literals on the type line, which also catches a default written as a string beside a single option. The pass condition is exact -- the brace set is the form the guide gives and the codebase reproduces.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:495`](../compliance/rules/scikit_learn/documentation.py#L495) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C069 — `FrameLikeParametersAreCalledDataframes`

> **Corpus:** Use the term dataframe when a parameter relies on frame-like features such as column names.

- **Pre-condition —** each Parameters entry the agent wrote or edited whose description relies on frame-like features such as column names.
- **Pass condition —** its type line uses the term `dataframe`.

Heuristic on the **pre-condition** (§6.3): "frame-like features are being used" is approximated by the description mentioning column names or frame-likeness, which is the example the guide itself gives; a parameter that relies on per-column dtypes without saying so is not selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:526`](../compliance/rules/scikit_learn/documentation.py#L526) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C070 — `ListElementTypesUseOfAsTheDelimiter`

> **Corpus:** Write a list parameter's element type with 'of', as in 'list of int'.

- **Pre-condition —** each Parameters entry the agent wrote or edited whose type line documents a `list`.
- **Pass condition —** the element type is not written as a subscript or a call.

Heuristic on the **pass condition** (§6.2), and graded one-sidedly: `of` is confirmed where it appears, and `list[int]` or `list(int)` -- the two spellings that replace the named delimiter -- are reported. A third way of attaching an element type would pass.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:563`](../compliance/rules/scikit_learn/documentation.py#L563) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C071 — `DtypeComesAfterTheShape`

> **Corpus:** Put the dtype after the shape when documenting an ndarray parameter.

- **Pre-condition —** each Parameters entry the agent wrote or edited whose type line gives both a shape and a dtype.
- **Pass condition —** the dtype comes after the shape.

Not heuristic: two substrings and their order on one line, which is the whole of what the guide fixes.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:595`](../compliance/rules/scikit_learn/documentation.py#L595) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C072 — `ArbitraryPrecisionUsesIntegralAndFloating`

> **Corpus:** Use integral and floating, not int and float, when documenting arbitrary precision.

- **Pre-condition —** each Parameters entry the agent wrote or edited whose type line gives a dtype with no precision -- `int`, `float`, `integral` or `floating`.
- **Pass condition —** it uses `integral` or `floating`.

Heuristic on the **pre-condition** (§6.3): "if one wants to mention arbitrary precision" is an intention, approximated by the dtype being named without a bit width, so `dtype=np.int32` is correctly not selected and a documented `dtype=int` meaning exactly 64-bit would be.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:625`](../compliance/rules/scikit_learn/documentation.py#L625) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C073 — `NoneDefaultIsWrittenOnceAtTheEnd`

> **Corpus:** Write a None default once, at the end of the type line, as default=None.

- **Pre-condition —** each Parameters entry the agent wrote or edited whose type line mentions `None`.
- **Pass condition —** `None` appears once, as `default=None`, at the end of the line.

Heuristic on the **pre-condition** (§6.3): "when the default is None" is approximated by the word appearing on the type line, which also selects a parameter whose type genuinely admits `None` without defaulting to it -- and that entry then passes only by writing the sanctioned form, which is stricter than the sentence.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:662`](../compliance/rules/scikit_learn/documentation.py#L662) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C076 — `SeeAlsoEntriesCarryAnExplanation`

> **Corpus:** Write each See Also entry on one line with a colon and an explanation.

- **Pre-condition —** each `See Also` section in a docstring the agent wrote or edited.
- **Pass condition —** every entry is one line of the form `name : explanation`.

Heuristic on the **pass condition** (§6.2): an entry's continuation line is told from a new entry by indentation, so a wrapped explanation indented to the same column as its entry would be read as a nameless entry.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:695`](../compliance/rules/scikit_learn/documentation.py#L695) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C077 — `AttributeNotesUseTheRubricDirective`

> **Corpus:** Use the .. rubric:: Note directive when adding a Note to an attribute.

- **Pre-condition —** each `Attributes` section in a docstring the agent wrote or edited that carries a note.
- **Pass condition —** the note is written with `.. rubric:: Note`.

Heuristic on the **pre-condition** (§6.3): "a Note added to an attribute" is recognised by a `Note`/`Notes` heading or a `.. note::` directive inside the Attributes section, so a note written as ordinary prose is not selected -- and would not render as a note either.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:737`](../compliance/rules/scikit_learn/documentation.py#L737) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C078 — `ExampleSectionsCarryOneOrTwoSnippets`

> **Corpus:** Put one or two code snippets in a docstring's Example section.

- **Pre-condition —** each docstring the agent wrote or edited that has an Examples section.
- **Pass condition —** it holds one or two code snippets.

Heuristic on the **pass condition** (§6.2): "a snippet" is counted as a run of doctest lines separated by a blank line, which is how the section is written, but two logically separate examples written without a blank line between them count as one.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:779`](../compliance/rules/scikit_learn/documentation.py#L779) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C079 — `DocstringExamplesAreRunnableAsIs`

> **Corpus:** Make a docstring example runnable as is, including all required imports.

- **Pre-condition —** each Examples section the agent wrote or edited that contains doctest lines.
- **Pass condition —** every module the example calls through is imported inside it.

Heuristic on the **pass condition** (§6.2), and narrower than the sentence: really running the example is what `pytest --doctest-modules` does and nothing here executes anything, so the check is the failure the guide names -- a missing import. Only names used as `name.attr` are checked, and an undefined bare name is not reported at all.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:818`](../compliance/rules/scikit_learn/documentation.py#L818) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C085 — `NewUserGuideSectionsCarryAFigure`

> **Corpus:** Include a figure generated from an example in a new user-guide section.

- **Pre-condition —** each user-guide page the contribution adds.
- **Pass condition —** it incorporates a figure.

Heuristic on **both layers** (§6.3, §6.2): "a new user-guide section" is approximated by a new page under `doc/`, so a section added to an existing page is not selected, and "generated from an example" is not confirmed -- a `figure`, `image` or `plot` directive satisfies this whether or not its source is the gallery.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:873`](../compliance/rules/scikit_learn/documentation.py#L873) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C086 — `NewUserGuideSectionsCarryOneOrTwoCodeExamples`

> **Corpus:** Include one or two short code examples in a user-guide section.

- **Pre-condition —** each user-guide page the contribution adds.
- **Pass condition —** it holds one or two short code examples.

Heuristic on **both layers** (§6.3, §6.2) for the same reasons as C085, plus the counting rule: a doctest run and a `code-block` directive each count as one example, and "short" is not graded at all.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:902`](../compliance/rules/scikit_learn/documentation.py#L902) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C087 — `EquationsComeLastFollowedByReferences`

> **Corpus:** Put mathematical equations last in a user-guide section, followed by their references.

- **Pre-condition —** each user-guide page the contribution adds that carries mathematics.
- **Pass condition —** a references block follows the last equation.

Heuristic on the **pass condition** (§6.2): "equations last, followed by references" is graded as *the references come after the last equation*, which is the observable half of the ordering; whether prose following an equation is discussion or a caption cannot be told from the markup.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:933`](../compliance/rules/scikit_learn/documentation.py#L933) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C089 — `InlineLiteralsUseSingleBackticks`

> **Corpus:** Use single backticks for inline literals in .rst files.

- **Pre-condition —** each reStructuredText line the agent wrote in `doc/` that carries an inline-literal span.
- **Pass condition —** it is written with single backticks.

Heuristic on the **pass condition** (§6.2): the check cannot see whether a line sits inside a literal block, where double backticks are ordinary text, so a double-backtick pair inside a code sample would be reported. Both forms render identically -- the guide says so -- which is why only the sanctioned spelling satisfies the instruction.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:971`](../compliance/rules/scikit_learn/documentation.py#L971) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C092 — `ExamplesAreNotFoldedIntoADropdown`

> **Corpus:** Do not put an Examples section inside a dropdown.

- **Pre-condition —** each documentation page the contribution touches that uses a `dropdown` directive.
- **Pass condition —** no `Examples` heading sits inside one.

A prohibition, so the antecedent is *using dropdowns at all* and the graded question is what was folded into them (§7.1). Heuristic on the **pass condition** (§6.2): a directive's body is identified by indentation rather than parsed, so an `Examples` heading indented for another reason directly under a dropdown would be reported.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:1005`](../compliance/rules/scikit_learn/documentation.py#L1005) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C093 — `ExamplesFollowTheMainDiscussion`

> **Corpus:** Place the Examples section immediately after the main discussion.

- **Pre-condition —** each documentation page the contribution touches that carries an `Examples` section.
- **Pass condition —** no folded section sits between the preceding heading and it.

Heuristic on the **pass condition** (§6.2): "right after the main discussion with the least possible folded section in-between" is graded as *no dropdown between the previous heading and the Examples heading*, which is the part of the sentence a file can answer; how much prose counts as the main discussion is not decidable from markup.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:1049`](../compliance/rules/scikit_learn/documentation.py#L1049) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C095 — `ArxivAndDoiReferencesUseTheirRoles`

> **Corpus:** Cite arXiv and DOI references with the :arxiv: and :doi: sphinx roles.

- **Pre-condition —** each documentation line the agent wrote that carries an arXiv identifier or a DOI.
- **Pass condition —** it cites them with the `:arxiv:` or `:doi:` role.

Heuristic on the **pre-condition** (§6.3): "a reference available with an arXiv or DOI identification number" is approximated by the identifier appearing in the written text, so a paper whose DOI the author never wrote down is not selected -- which is also the only case a checker could not fault anyone for.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:1090`](../compliance/rules/scikit_learn/documentation.py#L1090) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C097 — `SectionLinksGoThroughAReferenceLabel`

> **Corpus:** Link to a documentation section through a reference label and the :ref: role.

- **Pre-condition —** each documentation line the agent wrote that links to another page or section.
- **Pass condition —** the link is a `:ref:` role.

Heuristic on the **pre-condition** (§6.3): "a link to an arbitrary section" is approximated by the two forms this documentation uses -- a `:doc:` role and a `:ref:` role -- so a raw HTML anchor is not selected. Both are selected on purpose: taking only `:doc:` would find violations and never a compliant link (§7.1).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:1131`](../compliance/rules/scikit_learn/documentation.py#L1131) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C098 — `ExistingReferenceLabelsSurvive`

> **Corpus:** Do not rename or remove an existing sphinx reference label.

- **Pre-condition —** each documentation page the agent edited that removed lines.
- **Pass condition —** no `.. _label:` line was removed without being written back.

A prohibition, so the antecedent is *editing a page*, not the removal the rule forbids (§7.1). Not heuristic: a label definition is one exact line shape, and the diff records both what left and what arrived, so renaming a label shows up as its old line removed and not re-added.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:1165`](../compliance/rules/scikit_learn/documentation.py#L1165) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C099 — `GlossaryTermsUseTheTermRole`

> **Corpus:** Link glossary terms with the :term: role.

- **Pre-condition —** each documentation line the agent wrote that points at the glossary.
- **Pass condition —** it does so with the `:term:` role.

Heuristic on the **pre-condition** (§6.3): "linking to a term in the glossary" is recognised by the `:term:` role itself or by a link naming the glossary page, so a term mentioned in prose with no link at all is not selected -- the sentence is about how a link is written, not about which words must be linked.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:1208`](../compliance/rules/scikit_learn/documentation.py#L1208) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C100 — `FunctionRolesUseTheFullImportPath`

> **Corpus:** Link to a function with its full import path in the :func: role.

- **Pre-condition —** each `:func:` role the agent wrote in documentation or a docstring.
- **Pass condition —** its target is a full import path, or the page sets `currentmodule`.

Not heuristic: a role's target is one string, a dot either appears in it or does not, and the `currentmodule` exception is the page's own directive rather than a guess.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:1279`](../compliance/rules/scikit_learn/documentation.py#L1279) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C102 — `ClassRolesUseTheFullImportPath`

> **Corpus:** Link to a class with its full import path unless a currentmodule directive shortens it.

- **Pre-condition —** each `:class:` role the agent wrote in documentation or a docstring.
- **Pass condition —** its target is a full import path, unless a `.. currentmodule::` directive in the same file shortens it.

Not heuristic, and the exception is written into the rule itself rather than inferred: the guide states it in the same sentence.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:1297`](../compliance/rules/scikit_learn/documentation.py#L1297) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C126 — `DeprecationsCarryADeprecatedDirective`

> **Corpus:** Add a .. deprecated:: note to the docstring repeating the warning's information.

- **Pre-condition —** each object the contribution deprecates with `@deprecated`.
- **Pass condition —** its docstring carries a `.. deprecated::` directive.

Heuristic on the **pre-condition** (§6.3): a deprecation is recognised by the decorator the project supplies, so one announced only by a hand-written `FutureWarning` is not selected. The directive itself is named exactly by the sentence, and whether its content repeats the warning's information is not graded -- C123 is the rule about the warning's content.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:1319`](../compliance/rules/scikit_learn/documentation.py#L1319) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C132 — `ChangedDefaultsCarryAVersionchangedDirective`

> **Corpus:** Add a .. versionchanged:: directive to the parameter docstring giving the old and new defaults.

- **Pre-condition —** each function whose keyword default the contribution changes.
- **Pass condition —** its docstring carries a `.. versionchanged::` directive.

Heuristic on the **pass condition** (§6.2): the directive is required *on the parameter description* and to give the old and new values, and this confirms only that the docstring gained one -- a directive attached to the wrong parameter passes. The pre-condition is exact where the base text was reconstructed and selects nothing where it was not, which is a gap in the evidence rather than an approximation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:1364`](../compliance/rules/scikit_learn/documentation.py#L1364) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C138 — `ConstructorArgumentsAreDocumentedUnderParameters`

> **Corpus:** Document constructor arguments under Parameters, not under Attributes.

- **Pre-condition —** each estimator class the agent wrote or edited whose docstring has an Attributes section and whose `__init__` takes arguments.
- **Pass condition —** no constructor argument is documented as an attribute.

Heuristic on the **pre-condition** (§6.3): "estimator" is approximated by the class defining `fit` or inheriting a scikit-learn base, since nothing in the source marks one. The pass condition is exact -- two named sections, and an argument name either appears as an entry of the wrong one or does not.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:1413`](../compliance/rules/scikit_learn/documentation.py#L1413) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C153 — `LearnedAttributesAreDocumentedUnderAttributes`

> **Corpus:** Document trailing-underscore attributes in the docstring's Attributes section.

- **Pre-condition —** each class the agent wrote or edited that sets a public trailing-underscore attribute outside `__init__`.
- **Pass condition —** every one of them appears in the docstring's Attributes section.

Heuristic on the **pre-condition** (§6.3): a learned attribute is recognised by the trailing underscore the project reserves for it, assigned in a method other than the constructor, so one set indirectly -- through `setattr` or a helper -- is not seen.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:1459`](../compliance/rules/scikit_learn/documentation.py#L1459) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C186 — `DocstringsFollowTheNumpydocStandard`

> **Corpus:** Write docstrings in the numpydoc standard.

- **Pre-condition —** each docstring the agent wrote or edited.
- **Pass condition —** it carries no section marker belonging to a competing format.

Heuristic on the **pass condition** (§6.2), and graded one-sidedly: a docstring with no sections at all is perfectly numpydoc-compatible, so the standard cannot be confirmed, while a reST field list or a Google `Args:` header is positive evidence of another format. Where a numpydoc section is present that is reported as satisfying, which is stronger evidence than mere absence.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/documentation.py:1508`](../compliance/rules/scikit_learn/documentation.py#L1508) · source: https://scikit-learn.org/dev/developers/develop.html


## scikit-learn — AI-assisted contribution policy

### SCIKIT-LEARN-C001 — `NoFullyAutomatedPullRequest`

> **Corpus:** Do not submit a pull request generated by a fully-automated tool.

- **Pre-condition —** a named model autonomously produced a contribution.
- **Pass condition —** that contribution was not generated by a fully-automated tool.

``by_construction`` (§6.5), not heuristic: the check is exact -- the harness records which model produced the patch, with nobody in the loop -- and it is the *setup*, not the evidence, that makes compliance impossible. A ``fail`` here says nothing about the agent's diligence, which is the whole reason the flag exists: the report can show the compliance rate with and without it. Scored rather than dropped, because a rule excluded from the batch cannot be shown to the guided arm and then reported on (§1).


ownership `created` · reads `files` · tier `trajectory`

[`compliance/rules/scikit_learn/ai_policy.py:75`](../compliance/rules/scikit_learn/ai_policy.py#L75) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C252 — `AiUsageListIsEdited`

> **Corpus:** Edit the AI usage list to keep only the categories of AI assistance you used.

- **Pre-condition —** a named model produced a contribution, so the template's AI-usage list applies to it.
- **Pass condition —** the pull-request text carries that list with a proper subset of the four pre-filled categories.

Not ``by_construction``: editing a checklist is something an agent can do. Heuristic on the **pass condition** (§6.2), and the doubt is worth naming (§6.6) -- "keep the ones that apply, delete the rest" is graded as *the list is present and not left whole*, so an agent that genuinely used all four categories and correctly kept all four is recorded as a violation. The alternative, accepting any list at all, would pass the unedited template, which is the one thing the sentence prohibits.


`heuristic` · ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/scikit_learn/ai_policy.py:106`](../compliance/rules/scikit_learn/ai_policy.py#L106) · source: https://github.com/scikit-learn/scikit-learn/blob/main/.github/PULL_REQUEST_TEMPLATE.md

### SCIKIT-LEARN-C254 — `DisclosureIsIncluded`

> **Corpus:** Include the AI/agent disclosure in every summary, PR description and work description.

- **Pre-condition —** a named model produced a contribution, which `AGENTS.md` makes a work description requiring the disclosure.
- **Pass condition —** the pull-request text carries a disclosure of AI assistance.

Heuristic on the **pass condition** (§6.2): "includes this disclosure" is matched by an AI-mention vocabulary rather than by the verbatim sentence, so that a disclosure worded differently still counts here. Whether it is the *published* wording is C255's question and is deliberately not asked twice -- one defect must not depress two rates (§7.5).


`heuristic` · ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/scikit_learn/ai_policy.py:148`](../compliance/rules/scikit_learn/ai_policy.py#L148) · source: https://github.com/scikit-learn/scikit-learn/blob/main/AGENTS.md

### SCIKIT-LEARN-C255 — `DisclosureUsesThePublishedWording`

> **Corpus:** Use the exact disclosure wording naming AI assistance and the absence of human review.

- **Pre-condition —** a pull-request description that discloses AI assistance.
- **Pass condition —** the disclosure is `AGENTS.md`'s sentence -- naming AI assistance and the absence of human review -- word for word once markup is normalised away.

The antecedent is *a disclosure was attempted*, not *the exact wording appeared* (§7.1): a run with no disclosure at all is C254's finding and finds no target here, while a paraphrase is a recorded violation. Heuristic on the **pre-condition** (§6.3), which recognises "a disclosure" by an AI-mention vocabulary; the pass condition itself is exact, since the file supplies the sentence verbatim.


`heuristic` · ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/scikit_learn/ai_policy.py:182`](../compliance/rules/scikit_learn/ai_policy.py#L182) · source: https://github.com/scikit-learn/scikit-learn/blob/main/AGENTS.md

### SCIKIT-LEARN-C256 — `DisclosureComesLast`

> **Corpus:** Put the disclosure at the end of the generated summary.

- **Pre-condition —** a pull-request description that discloses AI assistance.
- **Pass condition —** nothing but blank lines follows the disclosure.

Same antecedent as C255 and for the same reason: position can only be graded once something is there to be positioned, and an absent disclosure is C254's finding. Heuristic on the **pre-condition** (§6.3) -- the disclosure paragraph is recognised by vocabulary -- while "at the end" is read exactly, as no further written line.


`heuristic` · ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/scikit_learn/ai_policy.py:217`](../compliance/rules/scikit_learn/ai_policy.py#L217) · source: https://github.com/scikit-learn/scikit-learn/blob/main/AGENTS.md


## scikit-learn — Code and quality

### SCIKIT-LEARN-C180 — `ContributedPythonFollowsPep8`

> **Corpus:** Format contributed Python code according to PEP8.

- **Pre-condition —** each Python file the agent edited that gained a written line.
- **Pass condition —** none of the lines it wrote is over 88 characters, ends in whitespace, or is indented with a tab.

Heuristic on the **pass condition** (§6.2), and the flag is about *coverage* rather than fuzziness. PEP8 is far wider than three constraints; these three are the part ruff enforces unconditionally at the project's own settings, so a file passing here can still fail ``ruff check``. The alternative -- reading a lint report -- is not available: no linter is run over this repository's bundles, and inferring the rest of PEP8 from source text would manufacture violations out of a proxy nobody could defend.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/code_quality.py:42`](../compliance/rules/scikit_learn/code_quality.py#L42) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C241 — `BottleneckIsolatedInAModuleLevelFunction`

> **Corpus:** Isolate the profiled bottleneck in a dedicated module-level function before compiling it.

- **Pre-condition —** each compiled extension source file the contribution adds.
- **Pass condition —** it defines at least one module-level function -- the isolated bottleneck the recipe's first step asks for.

Heuristic on **both layers** (§6.3, §6.2). The pre-condition approximates "you profiled and found the main bottleneck" by its only observable consequence, a compiled extension appearing, because profiling leaves no trace in the evidence. The pass condition approximates "a *dedicated* module-level function" by there being one at all: a file whose work happens inside a class or inline has isolated nothing, while a file with a module-level function may still have isolated the wrong thing.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/code_quality.py:96`](../compliance/rules/scikit_learn/code_quality.py#L96) · source: https://scikit-learn.org/dev/developers/performance.html


## scikit-learn — Language and framework style

### SCIKIT-LEARN-C116 — `RenamedPublicNamesKeepWorkingAndWarn`

> **Corpus:** Keep a renamed public name working for two releases and warn when it is used.

- **Pre-condition —** each public name the contribution renames or retires.
- **Pass condition —** the old name is still defined and warns when it is used.

Heuristic on the **pre-condition** (§6.3): a rename leaves the same trace as a deletion -- a public definition that was there at the base commit and is gone or newly deprecated at head -- so the two cannot be told apart and both are selected. The two-release window itself is not graded: a run sees one commit, not two releases, and this docstring says so rather than letting the flag imply it.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:252`](../compliance/rules/scikit_learn/language_style.py#L252) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C117 — `RenamedFunctionsDelegateThroughDeprecated`

> **Corpus:** Decorate a renamed function or class with utils.deprecated and delegate to the new name.

- **Pre-condition —** each public name the contribution renames or retires.
- **Pass condition —** the old name carries `utils.deprecated` and its body calls the new one.

Shares C116's antecedent and grades a different thing (§7.5): C116 asks whether the old name still works and warns, this asks whether the recipe's *mechanism* was used -- the decorator plus delegation. Heuristic on **both layers** (§6.3, §6.2): the rename proxy again, and "delegates to the new name" is read as the old function calling some other function, since which name is the new one is recorded nowhere.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:285`](../compliance/rules/scikit_learn/language_style.py#L285) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C118 — `DeprecatedApiReferenceIsUpdated`

> **Corpus:** Move the deprecated name to DEPRECATED_API_REFERENCE and add the new name to API_REFERENCE in doc/api_reference.py.

- **Pre-condition —** a contribution that deprecates a public name with `@deprecated`.
- **Pass condition —** `doc/api_reference.py` gains a `DEPRECATED_API_REFERENCE` entry.

Heuristic on **both layers** (§6.3, §6.2): the deprecation is recognised by the decorator, and the update is recognised by the constant's name appearing among the written lines -- moving the *right* name into it is not checked, because the mapping from a decorated function to its reference-file entry is not in the patch.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:328`](../compliance/rules/scikit_learn/language_style.py#L328) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C119 — `DeprecatedMembersUseTheDecorator`

> **Corpus:** Deprecate an attribute or method with the utils.deprecated decorator on its property.

- **Pre-condition —** each method or property the agent wrote or edited whose docstring announces a deprecation.
- **Pass condition —** it carries the `utils.deprecated` decorator.

Fires on the announcement, not on the decorator (§7.1) -- selecting decorated members would find only compliant ones. Heuristic on the **pre-condition** (§6.3): "is to be deprecated" is an intention, approximated by the `.. deprecated::` note the project's own C126 requires alongside it.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:368`](../compliance/rules/scikit_learn/language_style.py#L368) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C120 — `DeprecatedComesAboveProperty`

> **Corpus:** Put the deprecated decorator above the property decorator.

- **Pre-condition —** each member the agent wrote or edited carrying both `@deprecated` and `@property`.
- **Pass condition —** `@deprecated` is written above `@property`.

Not heuristic: two decorators, one order, and the consequence of getting it wrong is stated in the same sentence of the guide. The decorator list is in source order, so its first element is the one written on top.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:403`](../compliance/rules/scikit_learn/language_style.py#L403) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C121 — `DeprecatedParametersRaiseAFutureWarning`

> **Corpus:** Raise a FutureWarning manually when a deprecated parameter is passed.

- **Pre-condition —** each function the agent wrote or edited that documents one of its parameters as deprecated.
- **Pass condition —** a `FutureWarning` is raised in the function, or in the `fit` of the class it belongs to.

Heuristic on the **pre-condition** (§6.3): a deprecated parameter is recognised from its own docstring entry saying so, which is the only trace a parameter deprecation leaves in the source. The class's `fit` is accepted as the place the warning is raised because C122 is the rule about *where*, and asking that twice would report one defect in two rows (§7.5).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:438`](../compliance/rules/scikit_learn/language_style.py#L438) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C122 — `DeprecatedParametersAreValidatedInFit`

> **Corpus:** Validate a deprecated parameter and raise its warning in fit, not in __init__.

- **Pre-condition —** each estimator class the agent wrote or edited that raises a `FutureWarning` somewhere.
- **Pass condition —** none of those warnings is raised in `__init__`.

Fires on the class having a parameter deprecation at all, and grades *where* it is handled (§7.1); selecting only warnings already in `fit` would record compliance and never its absence. Heuristic on the **pre-condition** (§6.3): "estimator" is the inherited proxy, and a `FutureWarning` raised for some other reason is selected too.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:499`](../compliance/rules/scikit_learn/language_style.py#L499) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C123 — `DeprecationMessagesNameBothVersions`

> **Corpus:** Name both the deprecation version and the removal version in the warning message.

- **Pre-condition —** each deprecation message the agent wrote -- a `@deprecated` reason or a `FutureWarning` text.
- **Pass condition —** it names two version numbers.

Heuristic on the **pass condition** (§6.2): "the version in which the deprecation happened and the version in which the old behaviour will be removed" is graded as two distinct version-shaped tokens, so a message naming one version twice, or naming a version and a date, is read differently from how a maintainer would read it.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:538`](../compliance/rules/scikit_learn/language_style.py#L538) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C124 — `DeprecationMessagesQuoteReleaseVersionsTwoApart`

> **Corpus:** Quote the release version, not the dev version, and set removal two releases later.

- **Pre-condition —** each deprecation message the agent wrote that names two versions.
- **Pass condition —** neither is a dev version, and the removal is two minor releases after the deprecation.

Narrowed to messages that already name two versions, because a message naming fewer is C123's finding (§7.5). Heuristic on the **pass condition** (§6.2): which of the two numbers is the deprecation and which the removal is inferred from their order, and a message mentioning a third version is graded on the first two.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:570`](../compliance/rules/scikit_learn/language_style.py#L570) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C130 — `ChangingDefaultsGoThroughASentinel`

> **Corpus:** Replace a changing default with a sentinel value and raise FutureWarning when it is left in place.

- **Pre-condition —** each function whose keyword default the contribution changes.
- **Pass condition —** the new default is a sentinel value and a `FutureWarning` is raised.

Heuristic on the **pass condition** (§6.2): the guide gives `"warn"` as the example sentinel and this accepts `"warn"` or `"deprecated"`, so a project-specific sentinel object would read as a violation. The pre-condition is exact where the base text was reconstructed and selects nothing where it was not -- a gap in the evidence, not an approximation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:615`](../compliance/rules/scikit_learn/language_style.py#L615) · source: https://scikit-learn.org/dev/developers/contributing.html

### SCIKIT-LEARN-C136 — `InitDoesNotTakeTrainingData`

> **Corpus:** Do not accept training data as an argument to an estimator's __init__.

- **Pre-condition —** each estimator `__init__` the agent wrote or edited.
- **Pass condition —** none of its parameters is training data.

A prohibition, so the antecedent is *having an `__init__`* and the graded question is what it accepts (§7.1). Heuristic on **both layers** (§6.3, §6.2): "estimator" is the inherited proxy, and training data is recognised by the argument names the guide's own worked counter-example uses -- `X`, `y`, `data` and their variants -- so a training set passed under another name is not caught.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:688`](../compliance/rules/scikit_learn/language_style.py#L688) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C139 — `EveryInitKeywordBecomesAnAttribute`

> **Corpus:** Set an instance attribute for every keyword argument __init__ accepts.

- **Pre-condition —** each estimator `__init__` the agent wrote or edited that takes parameters.
- **Pass condition —** each parameter is assigned to an instance attribute of the same name.

Heuristic on the **pre-condition** (§6.3) only: "estimator" is the inherited proxy. The grading is exact -- `self.<name> = ...` for each keyword is what `get_params` and model selection rely on, and the assignment is either in the constructor or it is not.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:718`](../compliance/rules/scikit_learn/language_style.py#L718) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C141 — `InitCarriesNoLogic`

> **Corpus:** Put no logic and no input validation in an estimator's __init__.

- **Pre-condition —** each estimator `__init__` the agent wrote or edited.
- **Pass condition —** its body is assignments and nothing else -- no branch, no loop, no raise, no call.

Heuristic on the **pass condition** (§6.2): "no logic, not even input validation" is graded as the absence of every statement kind other than assignment, plus the absence of calls on the right-hand side. That is stricter than the sentence in one place -- `super().__init__(...)` is a call and would be reported -- and the reading is recorded here rather than left to be discovered.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:755`](../compliance/rules/scikit_learn/language_style.py#L755) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C142 — `MutableConstructorArgumentsAreCopiedBeforeUse`

> **Corpus:** Copy a mutable constructor argument before modifying it, and do so where it is used.

- **Pre-condition —** each estimator method other than `__init__` that mutates a stored constructor argument in place.
- **Pass condition —** the method copies it first.

Heuristic on **both layers** (§6.3, §6.2): mutation is recognised by the in-place methods a list, dict or set exposes -- `append`, `update`, `sort` and their siblings -- and a copy by the constructors and helpers that make one, so a mutation through slice assignment is not seen and a copy taken in a helper is not credited. The sentence's second half -- *where the parameters are used, typically in fit* -- is satisfied by construction, since `__init__` is excluded from the selection.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:827`](../compliance/rules/scikit_learn/language_style.py#L827) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C143 — `InitSetsNoTrailingUnderscoreAttributes`

> **Corpus:** Do not set trailing-underscore attributes inside __init__.

- **Pre-condition —** each estimator `__init__` the agent wrote or edited.
- **Pass condition —** it assigns no attribute whose name ends in an underscore.

A prohibition selected on the permitted act -- writing a constructor -- rather than on the assignment it forbids (§7.1). Heuristic on the **pre-condition** (§6.3) only: the trailing underscore is the project's own marker for a fitted attribute, so the grading itself is exact.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:797`](../compliance/rules/scikit_learn/language_style.py#L797) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C144 — `FitChecksThatXAndYAgreeOnSamples`

> **Corpus:** Raise ValueError when X and y have different numbers of samples.

- **Pre-condition —** each estimator `fit` the agent wrote or edited that takes both `X` and `y`.
- **Pass condition —** it validates their lengths -- through `check_X_y`, `validate_data` or `check_consistent_length`, or by raising `ValueError` itself.

Heuristic on the **pass condition** (§6.2): the requirement is behavioural -- a `ValueError` when the sample counts differ -- and nothing here runs the estimator, so the check is that the fit calls one of the helpers the project offers for exactly this, or raises the named exception itself. A `fit` that validates by some other route reads as a violation, and that is the cost of grading a differential rule statically.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/scikit_learn/language_style.py:884`](../compliance/rules/scikit_learn/language_style.py#L884) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C145 — `UnsupervisedFitAcceptsAnIgnoredY`

> **Corpus:** Accept an ignored y=None keyword in second position on an unsupervised estimator's fit.

- **Pre-condition —** each `fit` on an estimator the agent wrote or edited that is neither a classifier nor a regressor.
- **Pass condition —** its second parameter is `y`, defaulting to `None`.

Heuristic on the **pre-condition** (§6.3): "unsupervised" is approximated by the class inheriting neither supervised mixin and having no supervised name, so a supervised estimator that declares neither would be asked for the wrong signature. The pass condition is exact -- a position and a default, both stated.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:932`](../compliance/rules/scikit_learn/language_style.py#L932) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C146 — `CompositeMethodsTakeYInSecondPlace`

> **Corpus:** Accept y in second position on fit_predict, fit_transform, score and partial_fit.

- **Pre-condition —** each `fit_predict`, `fit_transform`, `score` or `partial_fit` the agent wrote or edited.
- **Pass condition —** its second parameter is `y`.

Not heuristic: the sentence gives a closed list of four method names, conditioned on them being implemented, and a parameter position is exact. The class need not be recognised as an estimator for this one, which is why it does not carry the proxy every neighbouring rule does.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:973`](../compliance/rules/scikit_learn/language_style.py#L973) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C147 — `FitReturnsSelf`

> **Corpus:** Return self from fit.

- **Pre-condition —** each `fit` method the agent wrote or edited.
- **Pass condition —** it returns `self`.

Not heuristic: `fit` is named exactly, and `return self` is one statement whose presence the AST answers outright. The class is not required to look like an estimator -- anything that defines `fit` is bound by the chaining contract the guide's worked one-liner depends on.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1010`](../compliance/rules/scikit_learn/language_style.py#L1010) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C148 — `DataIndependentParametersBelongToInit`

> **Corpus:** Take any parameter that can be set before seeing the data as an __init__ keyword argument.

- **Pre-condition —** each estimator `fit` the agent wrote or edited that takes a parameter beyond the data.
- **Pass condition —** none of those parameters carries a value that could have been set before the data arrived.

Heuristic on the **pass condition** (§6.2): "can have a value assigned prior to having access to the data" is approximated by *the parameter has a literal default* -- a hyper-parameter, by the complementary sentence the guide states next, since a data-dependent argument has nothing to default to. `sample_weight`, `groups` and routed `**fit_params` are exempt, being data-dependent by the project's own glossary.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1042`](../compliance/rules/scikit_learn/language_style.py#L1042) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C151 — `PublicLearnedAttributesEndInAnUnderscore`

> **Corpus:** Name every public learned attribute with a trailing underscore.

- **Pre-condition —** each learned attribute the agent's class exposes in its docstring's Attributes section.
- **Pass condition —** its name ends in a trailing underscore.

Partitioned against C152 so one defect is not counted twice (§7.5): this rule takes the attributes the docstring *exposes* as public, C152 takes the ones it does not. Heuristic on the **pre-condition** (§6.3): "attributes you'd want to expose as public" is approximated by their being documented, which is the only record of that intent.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1090`](../compliance/rules/scikit_learn/language_style.py#L1090) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C152 — `NonPublicLearnedAttributesLeadWithAnUnderscore`

> **Corpus:** Name a learned but non-public attribute with a leading underscore.

- **Pre-condition —** each learned attribute the agent's class does not document.
- **Pass condition —** its name begins with a leading underscore.

The complement of C151, and the partition is deliberate (§7.5): an undocumented learned attribute is one the class does not expose, so the guide's leading-underscore rule is the one that binds it. Heuristic on the **pre-condition** (§6.3): "you'd like to store yet not expose" is an intention, approximated by the attribute's absence from the Attributes section.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1129`](../compliance/rules/scikit_learn/language_style.py#L1129) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C155 — `FitSetsNFeaturesIn`

> **Corpus:** Set n_features_in_ at fit time on an estimator that expects tabular input.

- **Pre-condition —** each estimator `fit` the agent wrote or edited that takes `X`.
- **Pass condition —** it sets `n_features_in_`, or calls the validation helper that sets it.

Heuristic on **both layers** (§6.3, §6.2): "expects tabular input" is approximated by `fit` taking `X`, which is a superset that also selects estimators over graphs or text; and `validate_data` is credited because the guide states that it sets the attribute for you, so the check accepts the indirect route as well as the direct one.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1170`](../compliance/rules/scikit_learn/language_style.py#L1170) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C156 — `FitSetsFeatureNamesIn`

> **Corpus:** Set feature_names_in_ when the estimator is fitted on a dataframe.

- **Pre-condition —** each estimator `fit` the agent wrote or edited that takes `X`.
- **Pass condition —** it sets `feature_names_in_`, or calls the validation helper that sets it.

The same shape and the same two approximations as C155, and stated separately because the corpus states them separately: an estimator can set the count and not the names. Heuristic on **both layers** (§6.3, §6.2).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1208`](../compliance/rules/scikit_learn/language_style.py#L1208) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C158 — `NewEstimatorsInheritBaseEstimator`

> **Corpus:** Inherit a new estimator from BaseEstimator.

- **Pre-condition —** each estimator class the agent adds.
- **Pass condition —** `BaseEstimator` is among its bases.

Heuristic on the **pre-condition** (§6.3): "estimator" is recognised by the class defining `fit`, which is what the guide itself points at -- and deliberately not by it inheriting `BaseEstimator`, since selecting on the artefact the rule demands could only ever record compliance (§7.1).


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1249`](../compliance/rules/scikit_learn/language_style.py#L1249) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C159 — `MixinsComeBeforeBaseEstimator`

> **Corpus:** List mixins before BaseEstimator in a new estimator's bases.

- **Pre-condition —** each estimator class the agent adds that inherits both a mixin and `BaseEstimator`.
- **Pass condition —** every mixin appears before `BaseEstimator` in the base list.

Heuristic on the **pre-condition** (§6.3): a mixin is recognised by the `Mixin` suffix the project uses without exception. The ordering itself is exact, and its consequence -- the method resolution order -- is stated in the same sentence.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1280`](../compliance/rules/scikit_learn/language_style.py#L1280) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C160 — `SklearnCloneReturnsAnInstance`

> **Corpus:** Return an estimator instance from __sklearn_clone__.

- **Pre-condition —** each `__sklearn_clone__` the agent wrote or edited.
- **Pass condition —** it returns a value.

Heuristic on the **pass condition** (§6.2): "must return an instance of the estimator" is graded as *it returns something*, because what a returned expression evaluates to is not decidable from the source. A method that falls off the end -- returning `None` -- is the failure the rule exists to catch, and that is caught exactly.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1319`](../compliance/rules/scikit_learn/language_style.py#L1319) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C161 — `TransformersInheritTheMixinAndImplementTransform`

> **Corpus:** Make a transformer inherit TransformerMixin and implement transform.

- **Pre-condition —** each class the agent wrote or edited that is a transformer.
- **Pass condition —** it inherits `TransformerMixin` and defines `transform`.

Heuristic on the **pre-condition** (§6.3): a transformer is recognised by *either* mark -- the mixin or a `transform` method -- so that a class with one and not the other is selected and fails, which is the whole content of the rule. Selecting on both would find only the compliant ones (§7.1).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1355`](../compliance/rules/scikit_learn/language_style.py#L1355) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C162 — `TransformKeepsItsSamplesAlignedAndInOrder`

> **Corpus:** Keep transform's output aligned one-to-one and in order with its input samples.

- **Pre-condition —** each `transform` method the agent wrote or edited.
- **Pass condition —** its body contains no construct that drops or reorders rows.

Graded from the code rather than from a run, and heuristic on the **pass condition** (§6.2) because of it: boolean-mask indexing, `np.delete(..., axis=0)`, `dropna` and `sort` are the shapes that change the sample count or its order, and a transformer that reorders through some other route passes. Sharpens the rule to what a patch can show, which is the honest reading of a behavioural contract nothing runs.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/scikit_learn/language_style.py:1389`](../compliance/rules/scikit_learn/language_style.py#L1389) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C163 — `RegressorsInheritTheMixinAndImplementPredict`

> **Corpus:** Make a regressor inherit RegressorMixin, implement predict and accept numerical y.

- **Pre-condition —** each class the agent wrote or edited that is a regressor.
- **Pass condition —** it inherits `RegressorMixin` and defines `predict`.

Heuristic on the **pre-condition** (§6.3): a regressor is recognised by the mixin or by a `Regressor`/`Regression` name, both marks the project uses. The sentence's third clause -- *they should accept numerical `y`* -- is a behavioural claim about values passed at run time and is deliberately not graded; saying so here is the point of the docstring being load-bearing (§7.3).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1430`](../compliance/rules/scikit_learn/language_style.py#L1430) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C164 — `ClassifiersInheritClassifierMixin`

> **Corpus:** Make a classifier inherit ClassifierMixin.

- **Pre-condition —** each class the agent wrote or edited that is a classifier.
- **Pass condition —** it inherits `ClassifierMixin`.

Heuristic on the **pre-condition** (§6.3): a classifier is recognised by the mixin, a `Classifier` name, or a `predict_proba` method -- the marks the project uses -- so a classifier declaring none of them is not selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1465`](../compliance/rules/scikit_learn/language_style.py#L1465) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C165 — `ClassifiersAcceptStringOrIntegerLabels`

> **Corpus:** Accept string or integer label sequences as y in a classifier's fit.

- **Pre-condition —** each `fit` on a classifier the agent wrote or edited.
- **Pass condition —** it encodes the labels it is given rather than assuming their type.

Heuristic on the **pass condition** (§6.2): accepting "sequences of either strings or integers" is a run-time property, and the observable proxy is that `fit` passes `y` through one of the helpers that handles both -- `np.unique`, `LabelEncoder`, `check_classification_targets`, `column_or_1d`. A classifier that handles strings by hand reads as a violation, which is the cost of grading this from the patch.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/scikit_learn/language_style.py:1494`](../compliance/rules/scikit_learn/language_style.py#L1494) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C166 — `ClassifiersStoreTheObservedLabels`

> **Corpus:** Store the observed labels in classes_ instead of assuming a contiguous integer range.

- **Pre-condition —** each `fit` on a classifier the agent wrote or edited.
- **Pass condition —** it sets `classes_`.

Heuristic on the **pre-condition** (§6.3) only: the classifier proxy. The grading is exact -- the guide names the attribute, and storing it is precisely what "should not assume the class labels are a contiguous range of integers" comes down to.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1535`](../compliance/rules/scikit_learn/language_style.py#L1535) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C167 — `ClassesAreOrderedLikeTheProbabilityColumns`

> **Corpus:** Order classes_ to match the column order of predict_proba, predict_log_proba and decision_function.

- **Pre-condition —** each classifier the agent wrote or edited that both sets `classes_` and returns per-class scores.
- **Pass condition —** `classes_` is built by `np.unique`, whose sorted output is what fixes the column order.

Heuristic on the **pass condition** (§6.2): the requirement is that two orderings agree, which only a run could establish. The proxy is the recipe the guide itself gives -- `self.classes_, y = np.unique(y, return_inverse=True)` -- so a classifier that guarantees the order another way reads as a violation. Recorded here because grading a differential rule from the patch is a narrowing, not a measurement.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/scikit_learn/language_style.py:1569`](../compliance/rules/scikit_learn/language_style.py#L1569) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C168 — `PredictReturnsLabelsFromClasses`

> **Corpus:** Return labels drawn from classes_ out of a classifier's predict.

- **Pre-condition —** each `predict` on a classifier the agent wrote or edited.
- **Pass condition —** its body reads `classes_`.

Heuristic on the **pass condition** (§6.2): "returns arrays containing class labels from `classes_`" is a run-time property, and consulting the attribute is the observable trace of it -- the guide's own recipe, `return self.classes_[np.argmax(D, axis=1)]`, is exactly this shape. A predict that returns stored labels through a helper reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `differential`

[`compliance/rules/scikit_learn/language_style.py:1615`](../compliance/rules/scikit_learn/language_style.py#L1615) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C169 — `ClusteringAlgorithmsInheritClusterMixin`

> **Corpus:** Make a clustering algorithm inherit ClusterMixin.

- **Pre-condition —** each class the agent wrote or edited that is a clustering algorithm.
- **Pass condition —** it inherits `ClusterMixin`.

Partitioned against C171 (§7.5): a clustering algorithm is recognised by *either* mark -- the mixin or a `labels_` attribute -- and this rule grades the mixin while C171 grades the attribute, so a class carrying one and not the other fails exactly one of them. Heuristic on the **pre-condition** (§6.3), which is that recognition.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1652`](../compliance/rules/scikit_learn/language_style.py#L1652) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C171 — `ClusteringAlgorithmsSetLabels`

> **Corpus:** Set a labels_ attribute holding the per-sample cluster assignment.

- **Pre-condition —** each class the agent wrote or edited that is a clustering algorithm.
- **Pass condition —** it sets a `labels_` attribute outside `__init__`.

The complement of C169 over the same antecedent (§7.5). Heuristic on the **pre-condition** (§6.3): the clusterer proxy. The grading is exact -- the guide names the attribute, and `predict` is explicitly optional where `labels_` is not.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1682`](../compliance/rules/scikit_learn/language_style.py#L1682) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C173 — `TagsSubclassAttributesCarryDefaults`

> **Corpus:** Give every attribute added to a Tags subclass a default value.

- **Pre-condition —** each attribute declared on a class the agent wrote or edited that subclasses `Tags`.
- **Pass condition —** it carries a default value.

Heuristic on the **pre-condition** (§6.3): a Tags subclass is recognised by a base named `Tags`, which is how the guide's worked `@dataclass class MyTags(Tags)` is written. The grading is exact: an annotated field either has a value or it does not, and the dataclass machinery is what makes that mandatory.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1715`](../compliance/rules/scikit_learn/language_style.py#L1715) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C175 — `InitSubclassDoesNotDependOnAutoWrapOutputKeys`

> **Corpus:** Do not let a super class's __init_subclass__ depend on auto_wrap_output_keys.

- **Pre-condition —** each `__init_subclass__` the agent wrote or edited.
- **Pass condition —** it never mentions `auto_wrap_output_keys`.

A prohibition selected on the permitted act -- defining the hook -- rather than on the dependency it forbids (§7.1). Not heuristic: the method and the keyword are both named exactly, and `TransformerMixin` consumes the keyword before a super class sees it, so a mention is the defect.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1757`](../compliance/rules/scikit_learn/language_style.py#L1757) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C176 — `SklearnIsFittedTakesNothingAndReturnsABoolean`

> **Corpus:** Give __sklearn_is_fitted__ no parameters and a boolean return.

- **Pre-condition —** each `__sklearn_is_fitted__` the agent wrote or edited.
- **Pass condition —** it takes only `self` and returns a boolean-shaped expression.

Heuristic on the **pass condition** (§6.2): the parameter half is exact, and "returns a boolean" is approximated by the returned expression being a literal, a comparison, a `bool(...)`/`hasattr(...)` call or a `not` -- a method returning a boolean computed some other way reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1792`](../compliance/rules/scikit_learn/language_style.py#L1792) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C177 — `DocLinkCustomisationOverridesBothAttributes`

> **Corpus:** Override _doc_link_module and _doc_link_template to customize an estimator's doc link.

- **Pre-condition —** each class the agent wrote or edited that overrides either `_doc_link_module` or `_doc_link_template`.
- **Pass condition —** it overrides both.

Fires on *customising the documentation link at all* -- the situation the sentence addresses -- rather than on the pair already being present (§7.1). Heuristic on the **pre-condition** (§6.3): overriding one of the two is the observable sign of the intention the sentence is about, and a class that customises the link some third way is not selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1858`](../compliance/rules/scikit_learn/language_style.py#L1858) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C178 — `DocLinkModuleNamesTheTopLevelPackage`

> **Corpus:** Set _doc_link_module to the top-level module name containing the estimator.

- **Pre-condition —** each class the agent wrote or edited that sets `_doc_link_module`.
- **Pass condition —** its value is the top-level package of the file that defines it.

Heuristic on the **pass condition** (§6.2): "the (top level) module that contains your estimator" is derived from the file's own path, which is right for a package laid out as this one is and would be wrong for a class re-exported from elsewhere. The consequence of getting it wrong is stated in the guide: no link is rendered.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1897`](../compliance/rules/scikit_learn/language_style.py#L1897) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C179 — `DocLinkParamGeneratorReturnsADict`

> **Corpus:** Return a dict of template variables from _doc_link_url_param_generator.

- **Pre-condition —** each `_doc_link_url_param_generator` the agent wrote or edited.
- **Pass condition —** it returns a dictionary.

Heuristic on the **pass condition** (§6.2): a returned dict literal or `dict(...)` call is recognised exactly, and a dict built into a local variable and then returned is recognised by that variable having been assigned one -- beyond that, what an expression evaluates to is not decidable from the source.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:1935`](../compliance/rules/scikit_learn/language_style.py#L1935) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C181 — `NonClassNamesSeparateWordsWithUnderscores`

> **Corpus:** Separate words with underscores in non-class names.

- **Pre-condition —** each function the agent adds to package code.
- **Pass condition —** its name separates words with underscores rather than capitals.

Heuristic on the **pass condition** (§6.2): the guide's worked pair is `n_samples` rather than `nsamples`, and a run-together name of that kind is indistinguishable from a single word, so what is graded is the other failure -- camel case in a non-class name -- which is detectable. Stated here because the check is narrower than the rule.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2001`](../compliance/rules/scikit_learn/language_style.py#L2001) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C182 — `OneStatementPerLine`

> **Corpus:** Put no more than one statement on a line, and break after if and for.

- **Pre-condition —** each Python file in the package the agent wrote lines into.
- **Pass condition —** none of those lines holds two statements or a control-flow header with its body attached.

Heuristic on the **pass condition** (§6.2): a semicolon or an inline body after `if`/`for` is read textually, so a semicolon inside a string literal would be reported. That is the same trade ruff's own E-rules make, and it is the shape the sentence names.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2039`](../compliance/rules/scikit_learn/language_style.py#L2039) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C183 — `ImportsAreAbsolute`

> **Corpus:** Use absolute imports.

- **Pre-condition —** each import statement the agent wrote in package code.
- **Pass condition —** it is absolute.

Not heuristic: a relative import is a syntactic fact -- `ImportFrom.level` is non-zero -- and the project's own ruff configuration bans the form. Selecting every import rather than only the relative ones is what lets a compliant import be recorded (§7.1).


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2079`](../compliance/rules/scikit_learn/language_style.py#L2079) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C185 — `NoStarImports`

> **Corpus:** Never use a star import.

- **Pre-condition —** each import statement the agent wrote in package code.
- **Pass condition —** it is not a star import.

A prohibition with the antecedent on the permitted act (§7.1). Not heuristic: `import *` is a syntactic form, and the guide's "in any case" overrides the section's own exception clause, so there is nothing left to approximate.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2117`](../compliance/rules/scikit_learn/language_style.py#L2117) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C189 — `InputValidationAvoidsAsanyarrayAndAtleast2d`

> **Corpus:** Do not use np.asanyarray or np.atleast_2d for input validation.

- **Pre-condition —** each function in package code the agent wrote or edited that converts an array-like argument.
- **Pass condition —** it uses neither `np.asanyarray` nor `np.atleast_2d`.

A prohibition with the antecedent on the permitted act -- converting input at all -- so a compliant `np.asarray` can be recorded (§7.1). Heuristic on the **pre-condition** (§6.3): "for input validation" is approximated by the conversion helpers appearing in the function, and a call made for some other purpose is selected too.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2155`](../compliance/rules/scikit_learn/language_style.py#L2155) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C190 — `PublicApiFunctionsCallCheckArray`

> **Corpus:** Call check_array on any array-like argument to a public API function.

- **Pre-condition —** each public module-level function in package code the agent wrote or edited that takes an array-like argument.
- **Pass condition —** it calls `check_array`, or one of the helpers that wraps it.

Heuristic on the **pre-condition** (§6.3): "an array-like argument passed to a scikit-learn API function" is approximated by a public function taking a parameter named `X`, `y` or `array`, which is the project's own naming, so an array arriving under a different name is not selected.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2197`](../compliance/rules/scikit_learn/language_style.py#L2197) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C191 — `PackageCodeAvoidsTheGlobalRng`

> **Corpus:** Do not call numpy.random.random or similar module-level RNG routines.

- **Pre-condition —** each function in package code the agent wrote or edited that draws random numbers.
- **Pass condition —** it does so through an explicit generator, not a module-level routine.

The same prohibition C232 states for tests, and kept separate because the corpus states it separately: this one selects package code (`tests=False`) and C232 selects tests, so a violation is reported once (§7.5). Heuristic on the **pre-condition** (§6.3): randomness is recognised from call names in the body.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2239`](../compliance/rules/scikit_learn/language_style.py#L2239) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C192 — `RandomRoutinesTakeARandomStateKeyword`

> **Corpus:** Take a random_state keyword and build a RandomState from it.

- **Pre-condition —** each module-level function in package code the agent wrote or edited that draws random numbers.
- **Pass condition —** it takes a `random_state` keyword and builds a generator from it.

Heuristic on the **pre-condition** (§6.3): "your code depends on a random number generator" is approximated by the RNG call names appearing in the function body. The pass condition names both halves the guide states -- the keyword and the construction -- and `check_random_state` counts as the construction, since the guide points at it.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2280`](../compliance/rules/scikit_learn/language_style.py#L2280) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C193 — `RandomEstimatorsTakeRandomStateDefaultingToNone`

> **Corpus:** Give an estimator a random_state __init__ argument defaulting to None.

- **Pre-condition —** each estimator the agent wrote or edited that uses randomness.
- **Pass condition —** its `__init__` takes `random_state`, defaulting to `None`.

Heuristic on the **pre-condition** (§6.3): "uses randomness in an estimator" is approximated by an RNG call anywhere in the class, or by the keyword already being there -- the second is included so that an estimator which takes the keyword and gets the default wrong can still be selected and graded (§7.1).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2325`](../compliance/rules/scikit_learn/language_style.py#L2325) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C194 — `RandomStateIsStoredUnmodified`

> **Corpus:** Store the random_state argument unmodified in an attribute of the same name.

- **Pre-condition —** each estimator `__init__` the agent wrote or edited that takes `random_state`.
- **Pass condition —** it assigns `self.random_state = random_state`, unchanged.

Heuristic on the **pre-condition** (§6.3) only: the estimator proxy. The grading is exact -- the attribute's name and the assigned expression are both read from the AST, and anything other than the bare parameter is a modification.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2368`](../compliance/rules/scikit_learn/language_style.py#L2368) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C196 — `PostFitGeneratorsLiveInRandomStateUnderscore`

> **Corpus:** Store a post-fit generator in the random_state_ attribute.

- **Pre-condition —** each estimator `fit` the agent wrote or edited that builds a generator.
- **Pass condition —** the generator is stored as `random_state_`.

Heuristic on the **pre-condition** (§6.3): "randomness is needed after fit" is approximated by `fit` constructing a generator at all, which is a superset -- a fit that builds one and uses it only locally does not need to store it. The wider scope is the right direction of error (§4.5), and the attribute name is exact.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2409`](../compliance/rules/scikit_learn/language_style.py#L2409) · source: https://scikit-learn.org/dev/developers/develop.html

### SCIKIT-LEARN-C199 — `DisplaysDefineAConstructorClassMethod`

> **Corpus:** Define from_estimator, from_predictions or both on a Display class.

- **Pre-condition —** each `Display` class the agent wrote or edited.
- **Pass condition —** it defines `from_estimator`, `from_predictions`, or both.

Heuristic on the **pre-condition** (§6.3): a Display is recognised by the `Display` suffix the project uses, or by defining a `plot` method, since nothing marks the type. The pass condition is exact -- two named class methods, one of which must exist.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2454`](../compliance/rules/scikit_learn/language_style.py#L2454) · source: https://scikit-learn.org/dev/developers/plotting.html

### SCIKIT-LEARN-C200 — `DisplayInitTakesOnlyComputedData`

> **Corpus:** Accept only the computed data in a Display's __init__.

- **Pre-condition —** each `Display` class `__init__` the agent wrote or edited.
- **Pass condition —** it takes no estimator or raw data, and computes nothing.

Heuristic on **both layers** (§6.3, §6.2): the Display proxy, and "only the data needed to create the visualization" is graded as *no estimator or `X`/`y` parameter, and no call in the body* -- the same shape the estimator rule C141 uses, because the guide states the same separation of computation from construction.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2483`](../compliance/rules/scikit_learn/language_style.py#L2483) · source: https://scikit-learn.org/dev/developers/plotting.html

### SCIKIT-LEARN-C201 — `DisplayPlotTakesOnlyVisualisationParameters`

> **Corpus:** Restrict a Display's plot method parameters to visualization concerns.

- **Pre-condition —** each `Display.plot` the agent wrote or edited.
- **Pass condition —** none of its parameters is an estimator or raw data.

Heuristic on **both layers** (§6.3, §6.2): the Display proxy, and "only have to do with visualization" is graded as the complement of the computation arguments -- an estimator, `X`, `y` -- since the space of legitimate styling parameters is open and cannot be enumerated.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2526`](../compliance/rules/scikit_learn/language_style.py#L2526) · source: https://scikit-learn.org/dev/developers/plotting.html

### SCIKIT-LEARN-C202 — `DisplayPlotStoresItsArtists`

> **Corpus:** Store the matplotlib artists created by plot as attributes on the Display.

- **Pre-condition —** each `Display.plot` the agent wrote or edited.
- **Pass condition —** it stores at least one artist as a trailing-underscore attribute.

Heuristic on the **pass condition** (§6.2): "the matplotlib artists" are recognised by the project's own convention for them -- an attribute whose name ends in an underscore, as `self.ax_`, `self.figure_` and `self.line_` do in the worked `RocCurveDisplay` -- so a plot storing its artists under other names reads as a violation.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2561`](../compliance/rules/scikit_learn/language_style.py#L2561) · source: https://scikit-learn.org/dev/developers/plotting.html

### SCIKIT-LEARN-C203 — `DisplayClassMethodsReturnThePlot`

> **Corpus:** Return the result of plot() from a Display's from_estimator and from_predictions.

- **Pre-condition —** each `from_estimator` or `from_predictions` the agent wrote or edited on a `Display` class.
- **Pass condition —** it returns the result of calling `plot`.

Heuristic on the **pre-condition** (§6.3) only: the Display proxy. The grading follows the guide's worked ending -- `return viz.plot()` -- and reads the returned expression for a `.plot(` call, which is exact for that shape.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2596`](../compliance/rules/scikit_learn/language_style.py#L2596) · source: https://scikit-learn.org/dev/developers/plotting.html

### SCIKIT-LEARN-C204 — `DisplayPlotValidatesTheNumberOfAxes`

> **Corpus:** Validate the number of axes when a list of axes is passed to plot.

- **Pre-condition —** each `Display.plot` the agent wrote or edited that takes an `ax` parameter.
- **Pass condition —** it checks how many axes it was given before drawing.

Heuristic on the **pass condition** (§6.2): "check if the number of axes is consistent with the number it expects" is recognised by the body measuring `ax` -- a `len(...)`, a `.size`, or an `isinstance` test against a list -- so a check written another way reads as a violation. The pre-condition is exact: a parameter named `ax`.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2636`](../compliance/rules/scikit_learn/language_style.py#L2636) · source: https://scikit-learn.org/dev/developers/plotting.html

### SCIKIT-LEARN-C206 — `MatplotlibIsImportedInsideThePlottingFunction`

> **Corpus:** Import matplotlib inside the plotting function, never at module level.

- **Pre-condition —** each package module the agent edited that imports matplotlib.
- **Pass condition —** no matplotlib import sits at module level.

Not heuristic: an import's nesting is a syntactic fact, and matplotlib is named exactly. Fires on the module importing matplotlib at all, so a module doing it correctly -- inside the plotting function -- is recorded as a pass rather than skipped (§7.1).


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2675`](../compliance/rules/scikit_learn/language_style.py#L2675) · source: https://scikit-learn.org/dev/developers/plotting.html

### SCIKIT-LEARN-C207 — `CheckMatplotlibSupportComesFirst`

> **Corpus:** Call check_matplotlib_support before importing matplotlib.

- **Pre-condition —** each function the agent wrote or edited that imports matplotlib inside itself.
- **Pass condition —** a `check_matplotlib_support` call appears above that import.

Not heuristic: both the call and the import are statements with line numbers, and the guide's "before importing it" is exactly their order. The antecedent is the local import, which is the situation the sentence addresses.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2716`](../compliance/rules/scikit_learn/language_style.py#L2716) · source: https://scikit-learn.org/dev/developers/plotting.html

### SCIKIT-LEARN-C221 — `CallbackSupportComesFromTheMixin`

> **Corpus:** Inherit from CallbackSupportMixin to give an estimator callback support.

- **Pre-condition —** each estimator the agent wrote or edited that uses the callback machinery.
- **Pass condition —** it inherits `CallbackSupportMixin`.

Heuristic on the **pre-condition** (§6.3): "supports callbacks" is recognised by any of the three marks the page describes -- the mixin, a `_init_callback_context` call in `fit`, or a `with_callbacks` decorator -- so a class calling into the machinery without the mixin is selected and fails, which is the rule's content (§7.1).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2777`](../compliance/rules/scikit_learn/language_style.py#L2777) · source: https://scikit-learn.org/dev/developers/callback_support.html

### SCIKIT-LEARN-C222 — `FitCreatesTheRootCallbackContext`

> **Corpus:** Call _init_callback_context at the start of fit to create the root callback context.

- **Pre-condition —** each callback-supporting estimator's `fit` the agent wrote or edited.
- **Pass condition —** it calls `_init_callback_context`.

Heuristic on the **pre-condition** (§6.3): the callback-support proxy. The sentence also says *at the beginning of fit*, and position is deliberately not graded -- a call placed after input validation is idiomatic in this codebase, and reporting it would manufacture violations. Stated here rather than left implicit.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2807`](../compliance/rules/scikit_learn/language_style.py#L2807) · source: https://scikit-learn.org/dev/developers/callback_support.html

### SCIKIT-LEARN-C223 — `ThirdPartyFitCarriesWithCallbacks`

> **Corpus:** Decorate a third-party callback-supporting estimator's fit with with_callbacks.

- **Pre-condition —** each callback-supporting estimator the agent wrote or edited **outside** the `sklearn/` package.
- **Pass condition —** its `fit` is decorated `with_callbacks`.

Partitioned against C224 by location (§7.5): the guide gives one instruction for third-party estimators and the opposite one for built-in ones, so this rule selects only classes outside the package and C224 only those inside it. Heuristic on the **pre-condition** (§6.3): "third-party" is approximated by the file's path, which is the only signal a patch carries.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2842`](../compliance/rules/scikit_learn/language_style.py#L2842) · source: https://scikit-learn.org/dev/developers/callback_support.html

### SCIKIT-LEARN-C224 — `BuiltInEstimatorsDoNotUseWithCallbacks`

> **Corpus:** Do not use with_callbacks on a built-in scikit-learn estimator.

- **Pre-condition —** each callback-supporting estimator the agent wrote or edited **inside** the `sklearn/` package.
- **Pass condition —** its `fit` is not decorated `with_callbacks`.

The complement of C223, partitioned by the same path test (§7.5). A prohibition with its antecedent on the permitted act -- writing a built-in estimator with callback support -- so a compliant one is recorded rather than skipped (§7.1). Heuristic on the **pre-condition** (§6.3): the callback-support proxy.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2883`](../compliance/rules/scikit_learn/language_style.py#L2883) · source: https://scikit-learn.org/dev/developers/callback_support.html

### SCIKIT-LEARN-C225 — `CallbacksImplementTheWholeProtocol`

> **Corpus:** Implement the full FitCallback protocol on a callback.

- **Pre-condition —** each callback class the agent wrote or edited.
- **Pass condition —** it defines `setup`, `on_fit_task_begin`, `on_fit_task_end` and `teardown`.

Heuristic on the **pre-condition** (§6.3): a callback is recognised by the `Callback` suffix, the protocol as a base, or one of the hooks being defined -- so a class with two of the four is selected and fails, which is the rule's content. The protocol itself is given in full by the page, so the pass condition is a closed list.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2921`](../compliance/rules/scikit_learn/language_style.py#L2921) · source: https://scikit-learn.org/dev/developers/developing_callbacks.html

### SCIKIT-LEARN-C226 — `HooksDeclareOnlyTheArgumentsTheyUse`

> **Corpus:** Declare only the optional hook arguments the callback actually uses.

- **Pre-condition —** each callback hook the agent wrote or edited that declares optional keyword arguments.
- **Pass condition —** every one of them is referenced in the hook's body.

Heuristic on the **pass condition** (§6.2): "actually used by the hook" is graded as the name appearing in the body, so an argument passed straight through to `**kwargs` or consumed by a helper is credited as used -- the wider reading, which errs towards not manufacturing violations (§4.5).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2952`](../compliance/rules/scikit_learn/language_style.py#L2952) · source: https://scikit-learn.org/dev/developers/developing_callbacks.html

### SCIKIT-LEARN-C227 — `HookOptionalArgumentsAreKeywordOnly`

> **Corpus:** Define a hook's optional arguments as keyword-only.

- **Pre-condition —** each callback hook the agent wrote or edited that declares an argument with a default.
- **Pass condition —** every such argument is keyword-only.

Heuristic on the **pre-condition** (§6.3): a hook is recognised by its name, one of the two the protocol publishes. The grading is exact -- the AST distinguishes `kwonlyargs` from ordinary parameters -- and the failure mode is stated in the guide's own warning: the values are silently not provided.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:2992`](../compliance/rules/scikit_learn/language_style.py#L2992) · source: https://scikit-learn.org/dev/developers/developing_callbacks.html

### SCIKIT-LEARN-C229 — `HooksDoNotPredictOnTheEstimatorTheyReceive`

> **Corpus:** Do not call predict or transform on the estimator a hook receives; use fitted_estimator.

- **Pre-condition —** each callback hook the agent wrote or edited that receives an `estimator`.
- **Pass condition —** it calls neither `predict` nor `transform` on it.

A prohibition with its antecedent on the permitted act -- receiving the estimator -- so a hook that uses it correctly is recorded (§7.1). Heuristic on the **pass condition** (§6.2): the call is matched on the receiver's name, so an estimator bound to a local variable first is not tracked.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:3029`](../compliance/rules/scikit_learn/language_style.py#L3029) · source: https://scikit-learn.org/dev/developers/developing_callbacks.html

### SCIKIT-LEARN-C230 — `AutoPropagatedCallbacksImplementTheirProtocol`

> **Corpus:** Implement the AutoPropagatedCallback protocol on a callback meant to propagate to sub-estimators.

- **Pre-condition —** each callback the agent wrote or edited that is meant to propagate to sub-estimators.
- **Pass condition —** it implements the `AutoPropagatedCallback` protocol -- the base plus `max_propagation_depth`.

Heuristic on the **pre-condition** (§6.3): "meant to be propagated" is an intention, recognised by *either* mark the protocol leaves -- the base class or the one member it adds -- so a callback carrying one and not the other is selected and fails, which is the rule's content (§7.1).


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:3069`](../compliance/rules/scikit_learn/language_style.py#L3069) · source: https://scikit-learn.org/dev/developers/developing_callbacks.html

### SCIKIT-LEARN-C231 — `SetupAndTeardownDoNotResetState`

> **Corpus:** Do not reset callback state in setup or teardown; accumulate across fits.

- **Pre-condition —** each `setup` or `teardown` the agent wrote or edited on a callback.
- **Pass condition —** it assigns no attribute an empty or zero value.

A prohibition with its antecedent on the permitted act -- defining the lifecycle hooks -- so a callback that accumulates correctly is recorded (§7.1). Heuristic on the **pass condition** (§6.2): "reset the state" is recognised as assigning an empty container, `0` or `None` to an instance attribute, which is what a reset looks like; a reset performed by calling `.clear()` on a stored collection is caught too, but one routed through a helper is not.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/scikit_learn/language_style.py:3113`](../compliance/rules/scikit_learn/language_style.py#L3113) · source: https://scikit-learn.org/dev/developers/developing_callbacks.html


# sphinx-doc

| category | rules |
|---|---:|
| [PR and release metadata](#sphinx-doc-pr-and-release-metadata) | 1 |
| [Tests and test style](#sphinx-doc-tests-and-test-style) | 4 |
| [Specialized changes](#sphinx-doc-specialized-changes) | 7 |
| [Documentation and docstrings](#sphinx-doc-documentation-and-docstrings) | 4 |
| [AI-assisted contribution policy](#sphinx-doc-ai-assisted-contribution-policy) | 5 |
| [Code and quality](#sphinx-doc-code-and-quality) | 3 |


## sphinx-doc — PR and release metadata

### SPHINX-DOC-C005 — `ChangelogEntryForNonTrivialChange`

> **Corpus:** Add a bullet point to CHANGES.rst for any change that is not trivial.

- **Pre-condition —** the contribution changes Python source, which the guide's own parenthesis puts outside the trivial exemption.
- **Pass condition —** CHANGES.rst gains a bullet point.

Heuristic because *not trivial* is a judgement the rule states by example rather than by rule. The exemption named on the page is "small doc updates, typo fixes", so the pre-condition takes its complement -- a change that touches Python source -- and a documentation-only or comment-only contribution finds no target rather than being graded. That errs towards not firing, which under-reports rather than inventing violations against changes the project would have exempted.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sphinx_doc/pr_metadata.py:27`](../compliance/rules/sphinx_doc/pr_metadata.py#L27) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html


## sphinx-doc — Tests and test style

### SPHINX-DOC-C004 — `TestsAccompanyTheCodeChange`

> **Corpus:** Include tests demonstrating the bug fix or the new feature alongside the code change.

- **Pre-condition —** the contribution changes non-test Python source.
- **Pass condition —** it also changes or adds a test file.

Heuristic because *demonstrating that the bug was fixed* is not settled by a test existing. A test that accompanies the change is the strongest signal the patch itself carries; whether it demonstrates anything is what C026 asks of the harness instead.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sphinx_doc/tests.py:52`](../compliance/rules/sphinx_doc/tests.py#L52) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html

### SPHINX-DOC-C024 — `JavaScriptSuiteRunWithNpm`

> **Corpus:** Run the JavaScript test suite with npm when the change touches JavaScript.

- **Pre-condition —** the contribution changes a JavaScript file.
- **Pass condition —** an `npm test` or `npm run test` invocation appears in the command log.

The Firefox requirement the guide notes in a tip conditions the environment, not the obligation, so it is not part of the pass condition.


ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/sphinx_doc/tests.py:84`](../compliance/rules/sphinx_doc/tests.py#L84) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html

### SPHINX-DOC-C025 — `NewTestsLiveUnderTests`

> **Corpus:** Place new unit tests in the tests/ directory.

- **Pre-condition —** each test function the agent added.
- **Pass condition —** the file it was added to is under `tests/`.

"Where necessary" in the source sentence governs whether a test is needed, not where it goes, so it does not soften this. A test the agent did not create is not selected: the rule is about placing new tests, not about relocating the project's existing ones.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/sphinx_doc/tests.py:113`](../compliance/rules/sphinx_doc/tests.py#L113) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html

### SPHINX-DOC-C026 — `TestFailsBeforeAndPassesAfter`

> **Corpus:** For a bug fix, add a test that fails before the patch is applied and passes after it.

- **Pre-condition —** the contribution changes non-test Python source and also changes a test file.
- **Pass condition —** the harness reports at least one test that failed before the patch and passes after it.

Heuristic for a reason worth stating: the tests the harness flips are the *benchmark's* tests, not necessarily the ones the agent wrote. A contribution can therefore be credited for a transition its own test did not cause. The alternative -- executing the agent's test against the base commit -- needs a runner this instrument does not have, so the proxy is declared rather than avoided. Withheld, never failed, when the run carries no functional result: absence of a report is not absence of a passing test.


`heuristic` · ownership `touched` · reads `files, evaluation` · tier `differential`

[`compliance/rules/sphinx_doc/tests.py:140`](../compliance/rules/sphinx_doc/tests.py#L140) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html


## sphinx-doc — Specialized changes

### SPHINX-DOC-C032 — `TranslationFilesNotEditedDirectly`

> **Corpus:** Do not modify the gettext translation files directly in a pull request.

- **Pre-condition —** the agent submitted a contribution.
- **Pass condition —** it alters no gettext catalogue under `sphinx/locale/`.

A prohibition, so the pre-condition selects the *permitted* act -- submitting a contribution -- and the pass condition checks it was not the prohibited one (spec §7.1). Selecting edited catalogues instead would only ever find violations and could never record a compliant contribution.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sphinx_doc/specialized.py:52`](../compliance/rules/sphinx_doc/specialized.py#L52) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html

### SPHINX-DOC-C033 — `StemmersRegeneratedNotHandEdited`

> **Corpus:** Regenerate the search stemmers and stopword files with utils/generate_snowball.py rather than editing them by hand.

- **Pre-condition —** the contribution changes a search stemmer or stopword file.
- **Pass condition —** `utils/generate_snowball.py` appears in the command log.

**The corpus files this as `static`, and it is not.** These files are generated from the Snowball project, which lives outside the repository, so the patch carries no input whose change would evidence a regeneration -- a hand edit and a regenerated file are byte-identical in kind. The only record that the generator ran is the command log. The tier is recorded here rather than corrected in the workbook, per the spec §8: the corpus is the specification and the guided arm was shown this sentence.


ownership `touched` · reads `files, commands` · tier `static`

[`compliance/rules/sphinx_doc/specialized.py:79`](../compliance/rules/sphinx_doc/specialized.py#L79) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html

### SPHINX-DOC-C034 — `MinifiedSearchRegeneratedFromSource`

> **Corpus:** Regenerate the minified search JavaScript from the non-minified sources with uglifyjs.

- **Pre-condition —** each minified search script the contribution changes.
- **Pass condition —** its non-minified source changed in the same contribution.

Heuristic: a matching change is evidence the minified file was regenerated from its source, not proof that `uglifyjs` produced it. The converse is conclusive though -- minified output edited while its source stands still cannot have been generated from that source, which is the case this is really for.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sphinx_doc/specialized.py:112`](../compliance/rules/sphinx_doc/specialized.py#L112) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html

### SPHINX-DOC-C035 — `SearchFixturesRegenerated`

> **Corpus:** Regenerate the tests/js/fixtures searchindex.js files with utils/generate_js_fixtures.py.

- **Pre-condition —** each `tests/js/fixtures/<name>/searchindex.js` the contribution changes.
- **Pass condition —** something under the matching `tests/js/roots/<name>/` changed too.

Heuristic for the same reason as C034, and it matters more here: these fixtures are test data, so a hand edit silently invalidates the JavaScript tests rather than failing loudly. A fixture that moves while its input project stands still is the signal.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sphinx_doc/specialized.py:142`](../compliance/rules/sphinx_doc/specialized.py#L142) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html

### SPHINX-DOC-C060 — `DeprecationRaisesRemovedInWarning`

> **Corpus:** Raise a RemovedInSphinxXXWarning when a newly deprecated feature is invoked.

- **Pre-condition —** each file where the contribution announces a deprecation, in prose or with a warning call.
- **Pass condition —** the same file's written lines name a `RemovedInSphinxXXWarning`.

Heuristic on the antecedent rather than the grading: the class-name form is exact, but recognising that a change *deprecates* something is a text match over `.. deprecated::`, `@deprecated` and warning calls, and prose can deprecate without any of them.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sphinx_doc/specialized.py:175`](../compliance/rules/sphinx_doc/specialized.py#L175) · source: https://www.sphinx-doc.org/en/master/internals/release-process.html

### SPHINX-DOC-C061 — `NewDeprecationWarningsSilencedInTests`

> **Corpus:** Eliminate or silence the deprecation warnings a new RemovedInSphinxXXWarning raises in the test suite.

- **Pre-condition —** the contribution adds a `RemovedInSphinxXXWarning`.
- **Pass condition —** the harness reports no test that passed before the change and fails after it.

`tox.ini` sets `PYTHONWARNINGS = error` for every test environment, so a warning left unsilenced surfaces as a test failure rather than as output. Heuristic because the converse does not hold cleanly: a regression is evidence of an unsilenced warning, not proof it was one, and a passing suite is evidence of silence rather than proof of it. Withheld when the run carries no functional result.


`heuristic` · ownership `touched` · reads `files, evaluation` · tier `differential`

[`compliance/rules/sphinx_doc/specialized.py:210`](../compliance/rules/sphinx_doc/specialized.py#L210) · source: https://www.sphinx-doc.org/en/master/internals/release-process.html

### SPHINX-DOC-C062 — `DeprecatedFeatureNotRemovedEarly`

> **Corpus:** Do not remove a deprecated feature before the second major release after its deprecation.

- **Pre-condition —** the contribution removes code that carried a `RemovedInSphinxXXWarning`.
- **Pass condition —** undecidable here -- withheld with the missing input named.

The rule turns on a comparison between the `XX` in the warning and the version of the repository at the base commit, and **the bundle carries no repository version**. It is not a tool run either, so no existing evidence source named it: it is a fact about the checked-out tree, a category the evidence model did not have. FORCED CHANGE -- `repo_version` was added to ``EVIDENCE_SOURCES`` for this rule, in the same shape as the Phase 5 sources: registered, carried by nothing, and declared here so that ``tests/test_check_tier.py`` permits the withholding and stops permitting it the day the bundle supplies a version. Withholding without a declared missing input would have been the silent-denominator failure that test exists to catch. The first Layer A change any repository has forced; raised in the sphinx-doc pilot report. Recorded rather than dropped, deliberately. The antecedent is exact and cheap, so the activation rate for early removals is still measured; only the verdict withholds, which keeps the rule out of both halves of the fraction instead of passing it vacuously.


ownership `touched` · reads `files, repo_version` · tier `static`

[`compliance/rules/sphinx_doc/specialized.py:253`](../compliance/rules/sphinx_doc/specialized.py#L253) · source: https://www.sphinx-doc.org/en/master/internals/release-process.html


## sphinx-doc — Documentation and docstrings

### SPHINX-DOC-C014 — `NewFeatureIsDocumented`

> **Corpus:** Document every new feature that the change adds.

- **Pre-condition —** each public module-level function the agent added to non-test source.
- **Pass condition —** the contribution also changes a documentation source under `doc/`, or the new definition carries a docstring.

Heuristic, and the weakest rule in this module. *Feature* is a judgement no artefact settles -- a new public function may be an internal refactor, and a genuine feature may arrive as a new argument to an existing one, which this never sees. Two forms of documenting are accepted because the project's own guide treats the manual and the docstring as the same obligation, and demanding the manual for every helper would report violations the maintainers would not.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/sphinx_doc/documentation.py:62`](../compliance/rules/sphinx_doc/documentation.py#L62) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html

### SPHINX-DOC-C017 — `NewConfigValueIsDocumented`

> **Corpus:** Document any new configuration variable in the configuration documentation.

- **Pre-condition —** each `app.add_config_value('name', ...)` the agent added.
- **Pass condition —** the same name appears in a documentation source the contribution changed under `doc/`.

The antecedent is exact -- `add_config_value` *is* how Sphinx registers a setting, so this cannot mistake ordinary code for a new option. The grading is the proxy: a name appearing in changed prose is evidence of documenting it, not proof, which is what the heuristic flag declares.


`heuristic` · ownership `created` · reads `files` · tier `static`

[`compliance/rules/sphinx_doc/documentation.py:104`](../compliance/rules/sphinx_doc/documentation.py#L104) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html

### SPHINX-DOC-C030 — `DocumentationLivesUnderDoc`

> **Corpus:** Make documentation changes in the source files under doc/.

- **Pre-condition —** each documentation source the contribution changes.
- **Pass condition —** its path is under `doc/`.

Heuristic on the **pre-condition** (v1.2 §6.3): the rule says *documentation* and the project publishes no list of what that is, so this approximates it as reStructuredText and Markdown minus the repository-root metadata files. Project metadata -- the changelog, the readme, the contributing guide -- is excluded, or this would fire on the very `CHANGES.rst` entry C005 requires. See the module docstring.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sphinx_doc/documentation.py:142`](../compliance/rules/sphinx_doc/documentation.py#L142) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html

### SPHINX-DOC-C031 — `DocumentationBuiltWithFailOnWarning`

> **Corpus:** Build the documentation with sphinx-build using --fail-on-warning.

- **Pre-condition —** the contribution changes a documentation source under `doc/`.
- **Pass condition —** a `sphinx-build` invocation carrying `--fail-on-warning` (or `-W`) appears in the command log.

The pre-condition fires on the *edit*, not on the build. Firing on the build would find only agents that already complied, which is §7.1 of the spec inverted.


ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/sphinx_doc/documentation.py:171`](../compliance/rules/sphinx_doc/documentation.py#L171) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html


## sphinx-doc — AI-assisted contribution policy

### SPHINX-DOC-C039 — `CommentsNotMachineGenerated`

> **Corpus:** Do not use AI to automatically generate code comments.

- **Pre-condition —** the contribution, produced by a named model, contains written comment or docstring lines.
- **Pass condition —** those lines were not automatically generated.

``by_construction``: every line in an autonomous run was written by the model, so any comment in the patch was machine-generated and this cannot be passed. It is scored so the rate can be reported with and without it -- not because the agent was careless. The pre-condition still discriminates: a contribution that adds no comment or docstring at all finds no target, which is a real distinction between runs and keeps the rule out of the fraction rather than failing it vacuously.


ownership `created` · reads `files` · tier `trajectory`

[`compliance/rules/sphinx_doc/ai_policy.py:84`](../compliance/rules/sphinx_doc/ai_policy.py#L84) · source: https://www.sphinx-doc.org/en/master/internals/ai-policy.html

### SPHINX-DOC-C041 — `AiUseIsDisclosed`

> **Corpus:** Disclose whether AI was used in developing the pull request.

- **Pre-condition —** an autonomous run produced a contribution, so AI was used.
- **Pass condition —** the pull request text says so.

Not ``by_construction``: an agent can write this sentence, and the policy attaches an explicit rejection to its absence. Whether agents do is the behavioural question. Heuristic on the **pass condition** (v1.2 §6.2): "the pull request says so" is matched with a vocabulary of AI-mention patterns, which stands in for meaning. A disclosure worded outside that vocabulary reads as a violation.


`heuristic` · ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/sphinx_doc/ai_policy.py:131`](../compliance/rules/sphinx_doc/ai_policy.py#L131) · source: https://www.sphinx-doc.org/en/master/internals/ai-policy.html

### SPHINX-DOC-C042 — `AiToolsAndUsageDocumented`

> **Corpus:** Document which AI tools were used and how they were used.

- **Pre-condition —** an autonomous run produced a contribution.
- **Pass condition —** the pull request names a tool and says how it was used.

Heuristic: naming a tool is matched against a list of known model and assistant names, which will miss one that is new or spelled unusually, and "how it was used" is matched on process verbs rather than understood. Both err towards reporting a violation where a disclosure was oddly worded, which is why the flag is set.


`heuristic` · ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/sphinx_doc/ai_policy.py:164`](../compliance/rules/sphinx_doc/ai_policy.py#L164) · source: https://www.sphinx-doc.org/en/master/internals/ai-policy.html

### SPHINX-DOC-C043 — `AiGeneratedContentIsIdentified`

> **Corpus:** Specify which code or text in the contribution is AI generated.

- **Pre-condition —** an autonomous run produced a contribution.
- **Pass condition —** the pull request points at what in the contribution is AI generated, naming a file or a code element.

Heuristic: pointing at a file name is a proxy for the mapping the policy asks for, and a disclosure that says "the entire patch" satisfies the policy in substance while naming nothing this pattern recognises. That failure direction is the reason for the flag.


`heuristic` · ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/sphinx_doc/ai_policy.py:199`](../compliance/rules/sphinx_doc/ai_policy.py#L199) · source: https://www.sphinx-doc.org/en/master/internals/ai-policy.html

### SPHINX-DOC-C050 — `NoAutonomousAgentSubmission`

> **Corpus:** Do not let an AI agent write code and open a pull request autonomously.

- **Pre-condition —** a named model produced a contribution.
- **Pass condition —** it was not an agent writing code and submitting it autonomously.

``by_construction``, and the most direct instance of it in any corpus so far: the rule prohibits exactly the thing the harness does. It is scored because an excluded rule cannot be shown to a guided agent and then reported on, and because the report is able to separate it -- not because failing it says anything about the model. The next sentence of the policy supplies the required alternative rather than an exception, so there is no compliant form of an autonomous submission to select for.


ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/sphinx_doc/ai_policy.py:233`](../compliance/rules/sphinx_doc/ai_policy.py#L233) · source: https://www.sphinx-doc.org/en/master/internals/ai-policy.html


## sphinx-doc — Code and quality

### SPHINX-DOC-C020 — `RuffCheckPasses`

> **Corpus:** Ensure the change passes ruff's lint checks.

- **Pre-condition —** the agent submitted Python code, which is what gets merged.
- **Pass condition —** `ruff check` reports no finding the base commit did not already have.

Deliberately not "the agent ran ruff". The obligation is that the contribution passes the check, so a contribution that never ran it is judged, not excused.


ownership `touched` · reads `files, lint_run` · tier `static`

[`compliance/rules/sphinx_doc/code_quality.py:59`](../compliance/rules/sphinx_doc/code_quality.py#L59) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html

### SPHINX-DOC-C021 — `RuffFormatted`

> **Corpus:** Format the code with ruff format.

- **Pre-condition —** each Python file the agent edited.
- **Pass condition —** none of the lines it wrote carry formatting `ruff format` always removes -- trailing whitespace, or a tab in the indentation.

Heuristic, and narrow on purpose. A real answer is `ruff format --diff`, which nothing in this instrument runs. Everything `ruff format` decides from configuration -- line length, quote style, magic trailing commas -- is therefore **not** checked: a proxy that guessed at project settings would report violations that are not violations. What is left is unconditional under every configuration, so a hit here is a real formatting defect, while a pass says only that the two cheapest signs of one are absent.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sphinx_doc/code_quality.py:93`](../compliance/rules/sphinx_doc/code_quality.py#L93) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html

### SPHINX-DOC-C022 — `MypyClean`

> **Corpus:** Ensure the change type-checks cleanly under mypy.

- **Pre-condition —** the agent submitted Python code.
- **Pass condition —** `mypy` reports no new error.

Graded **one-sidedly**, like `tests.FullSuitePasses` in the SymPy pack. A file that does not parse cannot type-check, and that is conclusive. Nothing else is: no mypy run is collected, and inferring a type error from source text would manufacture violations out of a proxy no one could defend. So this fails on evidence and withholds otherwise. UNCOVERED -- spec §5 lists the Phase 5 run sources and none of them is a type checker. `lint_run` is declared as the nearest named missing input so the withholding is auditable, but a `type_check_run` source would say what is actually absent. Raised in the sphinx-doc pilot report.


ownership `touched` · reads `files, lint_run` · tier `static`

[`compliance/rules/sphinx_doc/code_quality.py:137`](../compliance/rules/sphinx_doc/code_quality.py#L137) · source: https://www.sphinx-doc.org/en/master/internals/contributing.html


# sympy

| category | rules |
|---|---:|
| [Git and commit conventions](#sympy-git-and-commit-conventions) | 14 |
| [PR and release metadata](#sympy-pr-and-release-metadata) | 19 |
| [Tests and test style](#sympy-tests-and-test-style) | 33 |
| [Specialized changes](#sympy-specialized-changes) | 27 |
| [Documentation and docstrings](#sympy-documentation-and-docstrings) | 40 |
| [AI-assisted contribution policy](#sympy-ai-assisted-contribution-policy) | 6 |
| [Code and quality](#sympy-code-and-quality) | 3 |


## sympy — Git and commit conventions

### SYMPY-C012 — `CreatesContributionBranch`

> **Corpus:** Before changing code, a contributor must create and check out a contribution branch, for example with `git checkout -b <branch-name>`.

- **Pre-condition —** the agent changed code at all.
- **Pass condition —** it created a contribution branch before doing so.

ownership `created` · reads `commands, files, commits` · tier `trajectory`

[`compliance/rules/sympy/git_conventions.py:91`](../compliance/rules/sympy/git_conventions.py#L91) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C013 — `NoCommitToMaster`

> **Corpus:** A contributor must not commit contribution changes directly to `master`.

- **Pre-condition —** the agent made a commit.
- **Pass condition —** that commit was not made on master.

ownership `created` · reads `commits, branch` · tier `trajectory`

[`compliance/rules/sympy/git_conventions.py:118`](../compliance/rules/sympy/git_conventions.py#L118) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C014 — `NoGitVerbsOnMaster`

> **Corpus:** While checked out on `master`, a contributor must not run `git merge`, `git add`, `git commit`, or `git rebase`.

- **Pre-condition —** the agent ran git merge, add, commit or rebase.
- **Pass condition —** it was not on master when it did.

ownership `created` · reads `commands, probe` · tier `trajectory`

[`compliance/rules/sympy/git_conventions.py:135`](../compliance/rules/sympy/git_conventions.py#L135) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C021 — `NoJunkFiles`

> **Corpus:** Before merge, editor configuration, binary, and temporary junk files must be removed from the contribution.

- **Pre-condition —** each file the contribution touches.
- **Pass condition —** it is not an editor-config, binary or temporary junk file.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/git_conventions.py:183`](../compliance/rules/sympy/git_conventions.py#L183) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C023 — `SummaryLength`

> **Corpus:** A commit-message summary line must be no longer than 71 characters.

- **Pre-condition —** every commit the agent made.
- **Pass condition —** its summary line is at most 71 characters.

ownership `created` · reads `commits` · tier `static`

[`compliance/rules/sympy/git_conventions.py:211`](../compliance/rules/sympy/git_conventions.py#L211) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C024 — `BodyLineLength`

> **Corpus:** Every commit-message body line must be no longer than 78 characters.

- **Pre-condition —** every body line of every commit -- a commit with no body has none.
- **Pass condition —** the line is at most 78 characters.

ownership `created` · reads `commits` · tier `static`

[`compliance/rules/sympy/git_conventions.py:226`](../compliance/rules/sympy/git_conventions.py#L226) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C025 — `BlankLineAfterSummary`

> **Corpus:** A commit message must separate its summary from its body with a blank line.

- **Pre-condition —** every commit that has anything after its summary line.
- **Pass condition —** a blank line separates the summary from it.

ownership `created` · reads `commits` · tier `static`

[`compliance/rules/sympy/git_conventions.py:254`](../compliance/rules/sympy/git_conventions.py#L254) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C026 — `SummaryNoTrailingPeriod`

> **Corpus:** A commit-message summary must not end with a period.

- **Pre-condition —** every commit the agent made.
- **Pass condition —** its summary does not end with a period.

ownership `created` · reads `commits` · tier `static`

[`compliance/rules/sympy/git_conventions.py:280`](../compliance/rules/sympy/git_conventions.py#L280) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C030 — `BodyCompleteSentences`

> **Corpus:** A commit-message body must use complete sentences.

- **Pre-condition —** every commit that has a body.
- **Pass condition —** the body reads as complete sentences.

Lexical heuristic, not a decidable check: flagged so the report can caveat it.


`heuristic` · ownership `created` · reads `commits` · tier `static`

[`compliance/rules/sympy/git_conventions.py:295`](../compliance/rules/sympy/git_conventions.py#L295) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C034 — `CoAuthorTrailerForm`

> **Corpus:** If a commit credits a co-author through GitHub, each trailer must appear at the bottom of the commit message in the exact form `Co-authored-by: <name> <email>`.

- **Pre-condition —** every commit-message line that credits a co-author.
- **Pass condition —** it is exactly `Co-authored-by: <name> <email>`, at the bottom.

ownership `created` · reads `commits` · tier `trajectory`

[`compliance/rules/sympy/git_conventions.py:331`](../compliance/rules/sympy/git_conventions.py#L331) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C040 — `DoNotEditAuthors`

> **Corpus:** A contributor must not edit `AUTHORS` directly; contributor identity changes must be made through `.mailmap`.

- **Pre-condition —** each file the contribution touches.
- **Pass condition —** it is not `AUTHORS`, which must be changed via `.mailmap` instead.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/git_conventions.py:365`](../compliance/rules/sympy/git_conventions.py#L365) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C041 — `MailmapMatchesCommitIdentity`

> **Corpus:** The source identity in a contributor's `.mailmap` entry must exactly match the name and email stored in their Git commit metadata.

- **Pre-condition —** every `.mailmap` line the agent added.
- **Pass condition —** its source identity matches the name and email in the commit metadata.

ownership `touched` · reads `files, commits` · tier `static`

[`compliance/rules/sympy/git_conventions.py:390`](../compliance/rules/sympy/git_conventions.py#L390) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C042 — `RunMailmapCheck`

> **Corpus:** After editing `.mailmap`, the contributor must run `python bin/mailmap_check.py` until it reports `No changes needed in .mailmap`, thereby placing entries in alphabetical order.

- **Pre-condition —** the agent edited `.mailmap`.
- **Pass condition —** it ran `bin/mailmap_check.py` until it reported no changes needed.

ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/sympy/git_conventions.py:435`](../compliance/rules/sympy/git_conventions.py#L435) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C043 — `CommitMailmapAfterCheck`

> **Corpus:** After `python bin/mailmap_check.py` reports `No changes needed in .mailmap`, the contributor must stage `.mailmap` with `git add .mailmap` and commit it with an `author: add <name> to .mailmap` message.

- **Pre-condition —** `bin/mailmap_check.py` reported no changes needed.
- **Pass condition —** `.mailmap` was then staged and committed with an `author: add ...` message.

ownership `touched` · reads `commands, commits` · tier `trajectory`

[`compliance/rules/sympy/git_conventions.py:467`](../compliance/rules/sympy/git_conventions.py#L467) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html


## sympy — PR and release metadata

### SYMPY-C006 — `CrossReferencesIssues`

> **Corpus:** A pull request description must cross-reference relevant issues.

- **Pre-condition —** the agent produced a contribution, so there is a pull request.
- **Pass condition —** it cross-references at least one issue.

ownership `created` · reads `pr_text, files, commits` · tier `trajectory`

[`compliance/rules/sympy/pr_metadata.py:114`](../compliance/rules/sympy/pr_metadata.py#L114) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C007 — `UsesFixesSyntax`

> **Corpus:** If merging the pull request should close an issue, its description must use `fixes #<issue-number>` syntax.

- **Pre-condition —** the description references an issue at all.
- **Pass condition —** at least one reference uses the `fixes #<n>` autoclose form.

ownership `created` · reads `pr_text` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:131`](../compliance/rules/sympy/pr_metadata.py#L131) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C009 — `IncludesReleaseNotesEntry`

> **Corpus:** A pull request must include a release-notes entry in its description before merge.

- **Pre-condition —** the agent produced a contribution, so there is a pull request.
- **Pass condition —** it includes a release-notes entry, or an explicit NO ENTRY.

ownership `created` · reads `pr_text, files, commits` · tier `trajectory`

[`compliance/rules/sympy/pr_metadata.py:149`](../compliance/rules/sympy/pr_metadata.py#L149) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C035 — `NotReadyIsMarked`

> **Corpus:** If a pull request is not ready to merge, it must be marked Draft or have a `[WIP]` title prefix.

- **Pre-condition —** the description says the work is not ready to merge.
- **Pass condition —** the title carries a `[WIP]` prefix.

Draft state does not exist in a text-only pull request, so the only observable antecedent is the agent saying so. Expect this to be ``not_applicable`` almost always (plan §5).


ownership `created` · reads `pr_text` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:166`](../compliance/rules/sympy/pr_metadata.py#L166) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C036 — `SubmittedIsNotWip`

> **Corpus:** Before final review, a pull request must no longer be Draft and must not retain a `[WIP]` title prefix.

- **Pre-condition —** the agent submitted a pull-request description for review.
- **Pass condition —** its title does not retain a `[WIP]` prefix.

ownership `created` · reads `pr_text` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:186`](../compliance/rules/sympy/pr_metadata.py#L186) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C037 — `CompletesTemplate`

> **Corpus:** A pull-request author must complete the repository's pull-request description template, including issue references and release notes.

- **Pre-condition —** the agent produced a contribution, so there is a pull request.
- **Pass condition —** it carries both an issue reference and a release-notes block.

ownership `created` · reads `pr_text, files, commits` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:199`](../compliance/rules/sympy/pr_metadata.py#L199) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C039 — `TitleHasNoNumbersOrFilenames`

> **Corpus:** A pull-request title must contain neither issue numbers nor file names; issue numbers belong in the description.

- **Pre-condition —** the description has a title line.
- **Pass condition —** it contains neither an issue number nor a file name.

ownership `created` · reads `pr_text` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:219`](../compliance/rules/sympy/pr_metadata.py#L219) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C046 — `AutocloseInOpeningParagraph`

> **Corpus:** To close an issue or pull request automatically, the pull-request description must place the autoclose sequence in an opening paragraph.

- **Pre-condition —** each autoclose sequence in the description.
- **Pass condition —** it sits in the opening paragraph.

ownership `created` · reads `pr_text` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:240`](../compliance/rules/sympy/pr_metadata.py#L240) · source: https://github.com/sympy/sympy/wiki/Issue-PR-Autoclosing-syntax

### SYMPY-C048 — `KeywordRepeatedForEveryNumber`

> **Corpus:** If a pull request should close multiple issues or pull requests, it must repeat an autoclose keyword immediately before every `#<number>`.

- **Pre-condition —** the description autocloses and names more than one issue number.
- **Pass condition —** every number carries its own autoclose keyword.

ownership `created` · reads `pr_text` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:257`](../compliance/rules/sympy/pr_metadata.py#L257) · source: https://github.com/sympy/sympy/wiki/Issue-PR-Autoclosing-syntax

### SYMPY-C050 — `NoAutocloseInNegatedSentence`

> **Corpus:** If a pull request must not close an issue, its description must not place an autoclose keyword next to that issue number even inside a negated sentence such as `does not fix #12345`.

- **Pre-condition —** each issue reference in a negated sentence -- the agent saying it does NOT close that issue.
- **Pass condition —** no autoclose keyword sits next to the number, since the negation does not prevent GitHub from closing it.

ownership `created` · reads `pr_text` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:276`](../compliance/rules/sympy/pr_metadata.py#L276) · source: https://github.com/sympy/sympy/wiki/Issue-PR-Autoclosing-syntax

### SYMPY-C052 — `HasReleaseNotesBlock`

> **Corpus:** Every pull-request description must contain a release-notes block between `<!-- BEGIN RELEASE NOTES -->` and `<!-- END RELEASE NOTES -->`.

- **Pre-condition —** the agent produced a contribution, so there is a pull request.
- **Pass condition —** it contains a release-notes block between the BEGIN and END markers.

ownership `created` · reads `pr_text, files, commits` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:300`](../compliance/rules/sympy/pr_metadata.py#L300) · source: https://github.com/sympy/sympy/wiki/Writing-Release-Notes

### SYMPY-C053 — `HeaderIsAKnownSubmodule`

> **Corpus:** Each release-note header must exactly match one current non-comment entry in `sympy_bot/submodules.txt`: `abc`, `algebras`, `assumptions`, `benchmarks`, `calculus`, `categories`, `codegen`, `combinatorics`, `concrete`, `core`, `crypto`, `diffgeom`, `discrete`, `external`, `functions`, `geometry`, `holonomic`, `integrals`, `interactive`, `liealgebras`, `logic`, `matrices`, `ntheory`, `parsing`, `physics.biomechanics`, `physics.continuum_mechanics`, `physics.control`, `physics.gaussopt`, `physics.hep`, `physics.hydrogen`, `physics.matrices`, `physics.mechanics`, `physics.optics`, `physics.paulialgebra`, `physics.pring`, `physics.qho_1d`, `physics.quantum`, `physics.secondquant`, `physics.sho`, `physics.units`, `physics.vector`, `physics.wigner`, `plotting`, `polys`, `printing`, `sandbox`, `series`, `sets`, `simplify`, `solvers`, `stats`, `strategies`, `tensor`, `testing`, `unify`, `utilities`, `vector`, `other`.

- **Pre-condition —** each release-note submodule header the agent wrote.
- **Pass condition —** it exactly matches one published submodule name.

ownership `created` · reads `pr_text` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:316`](../compliance/rules/sympy/pr_metadata.py#L316) · source: https://github.com/sympy/sympy/wiki/Writing-Release-Notes

### SYMPY-C054 — `ChangesAreAMarkdownList`

> **Corpus:** Under each release-note submodule header, changes must be written as a Markdown list.

- **Pre-condition —** each release-note submodule header that has content under it.
- **Pass condition —** all of that content is written as Markdown list items.

ownership `created` · reads `pr_text` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:334`](../compliance/rules/sympy/pr_metadata.py#L334) · source: https://github.com/sympy/sympy/wiki/Writing-Release-Notes

### SYMPY-C055 — `EmptyBlockSaysNoEntry`

> **Corpus:** If a pull request does not warrant release notes, its release-notes block must contain exactly `NO ENTRY`.

- **Pre-condition —** a release-notes block with no entries -- the agent judged the change not to warrant release notes.
- **Pass condition —** the block contains exactly NO ENTRY.

ownership `created` · reads `pr_text` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:355`](../compliance/rules/sympy/pr_metadata.py#L355) · source: https://github.com/sympy/sympy/wiki/Writing-Release-Notes

### SYMPY-C060 — `EntryIsACompleteSentence`

> **Corpus:** Each release-note entry must be a complete sentence beginning with a capital letter and ending with a period.

- **Pre-condition —** each release-note entry.
- **Pass condition —** it begins with a capital letter and ends with a period.

ownership `created` · reads `pr_text` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:377`](../compliance/rules/sympy/pr_metadata.py#L377) · source: https://github.com/sympy/sympy/wiki/Writing-Release-Notes

### SYMPY-C061 — `EntryHasNoPrNumberOrAuthor`

> **Corpus:** A release-note entry must contain neither a pull-request number nor author names; the bot adds them automatically.

- **Pre-condition —** each release-note entry.
- **Pass condition —** it names neither a pull-request number nor an author.

ownership `created` · reads `pr_text` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:393`](../compliance/rules/sympy/pr_metadata.py#L393) · source: https://github.com/sympy/sympy/wiki/Writing-Release-Notes

### SYMPY-C063 — `EntryHasNoIssueNumber`

> **Corpus:** A release-note entry must not contain issue numbers; issue references belong elsewhere in the pull-request description.

- **Pre-condition —** each release-note entry.
- **Pass condition —** it contains no issue number; those belong elsewhere in the description.

ownership `created` · reads `pr_text` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:409`](../compliance/rules/sympy/pr_metadata.py#L409) · source: https://github.com/sympy/sympy/wiki/Writing-Release-Notes

### SYMPY-C065 — `EntryIsSelfContainedPastTense`

> **Corpus:** Every release-note entry must use past tense, be self-contained, and be phrased for direct insertion into the wiki rather than referring to `this pull request`.

- **Pre-condition —** each release-note entry.
- **Pass condition —** it reads as past tense and does not refer to `this pull request`.

Tense is a lexical heuristic, not a decidable check; flagged so the report can caveat it.


`heuristic` · ownership `created` · reads `pr_text` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:422`](../compliance/rules/sympy/pr_metadata.py#L422) · source: https://github.com/sympy/sympy/wiki/Writing-Release-Notes

### SYMPY-C066 — `EntryAvoidsFirstPerson`

> **Corpus:** A release-note entry must omit first-person phrases such as `I have fixed` and pull-request-relative phrases such as `this pull request fixes`.

- **Pre-condition —** each release-note entry.
- **Pass condition —** it uses neither first-person nor pull-request-relative phrasing.

`heuristic` · ownership `created` · reads `pr_text` · tier `static`

[`compliance/rules/sympy/pr_metadata.py:442`](../compliance/rules/sympy/pr_metadata.py#L442) · source: https://github.com/sympy/sympy/wiki/Writing-Release-Notes


## sympy — Tests and test style

### SYMPY-C069 — `NewFunctionalityHasTests`

> **Corpus:** If a contribution adds new functionality, it must include tests.

- **Pre-condition —** each public function or class the agent added to non-test code.
- **Pass condition —** the contribution also adds a test that exercises it by name.

IMPLEMENTATION_PLAN.md §4.2 makes this the worked case for invariant 2: the trigger is the new functionality, so an agent that writes none of the tests fails rather than escaping as ``not_applicable``.


`heuristic` · ownership `created` · reads `files` · tier `differential`

[`compliance/rules/sympy/tests.py:438`](../compliance/rules/sympy/tests.py#L438) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C071 — `FullSuitePasses`

> **Corpus:** Before merge, every pull request must pass the complete test suite.

- **Pre-condition —** the agent produced a contribution, which is what gets merged.
- **Pass condition —** no test that passed before the change fails after it.

Graded from the harness's own before-and-after run, and graded **one-sidedly**. A test that passed before and fails now is conclusive: the suite does not pass. The converse is not, because the harness runs a subset -- a clean subset does not establish that the *complete* suite passes, which is what the rule demands. So this can fail on evidence and is withheld otherwise; it never passes vacuously.


ownership `touched` · reads `files, evaluation, full_suite_run` · tier `differential`

[`compliance/rules/sympy/tests.py:485`](../compliance/rules/sympy/tests.py#L485) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C076 — `TestFunctionNaming`

> **Corpus:** A test function must have a name beginning with `test_`.

- **Pre-condition —** each public module-level function the agent added to a test module.
- **Pass condition —** its name begins with `test_`.

ownership `created` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:523`](../compliance/rules/sympy/tests.py#L523) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C078 — `RunsLocalTestAndDoctestSuites`

> **Corpus:** When validating the complete local test and doctest suites, a contributor must run both `python bin/test` and `python bin/doctest` and require both commands to pass.

- **Pre-condition —** the agent changed code, so the local suites are what validate it.
- **Pass condition —** it ran both `python bin/test` and `python bin/doctest`, neither reporting a failure.

ownership `touched` · reads `files, commands` · tier `static`

[`compliance/rules/sympy/tests.py:551`](../compliance/rules/sympy/tests.py#L551) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C084 — `ExpectedExceptionsUseRaises`

> **Corpus:** When testing an expected exception, the test must use `sympy.testing.pytest.raises`.

- **Pre-condition —** each site in the agent's test code that tests for an expected exception, however it is written.
- **Pass condition —** the site uses SymPy's own `raises` helper.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:578`](../compliance/rules/sympy/tests.py#L578) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C085 — `RaisesWrapsCodeInLambda`

> **Corpus:** When calling `sympy.testing.pytest.raises(ExceptionType, ...)`, the tested expression must be wrapped in `lambda`, unless the context-manager form is required.

- **Pre-condition —** each `raises(ExceptionType, <code>)` call the agent wrote -- the two-argument form, not the context-manager form.
- **Pass condition —** the code argument is a `lambda`.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:619`](../compliance/rules/sympy/tests.py#L619) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C086 — `DeprecationTestsUseWarnsHelper`

> **Corpus:** A `SymPyDeprecationWarning` test must use `sympy.testing.pytest.warns_deprecated_sympy()` unless stacklevel checking is explicitly disabled.

- **Pre-condition —** each test the agent wrote that names `SymPyDeprecationWarning`.
- **Pass condition —** it goes through `warns_deprecated_sympy()`, or through `warns(SymPyDeprecationWarning, test_stacklevel=False)` when stacklevel checking is explicitly disabled.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:648`](../compliance/rules/sympy/tests.py#L648) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C089 — `WarningsSetStacklevel`

> **Corpus:** Code that emits a warning must set `stacklevel` so the warning identifies the user's calling line.

- **Pre-condition —** each warning the agent's non-test code emits.
- **Pass condition —** the call passes `stacklevel`, so the warning points at the caller.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:685`](../compliance/rules/sympy/tests.py#L685) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C090 — `WarnsDeprecationEscapeHatch`

> **Corpus:** If a deprecation warning cannot set `stacklevel` correctly, its test must use `warns(SymPyDeprecationWarning, test_stacklevel=False)` instead of `warns_deprecated_sympy()`.

- **Pre-condition —** each `warns(SymPyDeprecationWarning, ...)` the agent wrote -- the form reached for only when the warning cannot set `stacklevel` correctly.
- **Pass condition —** it passes `test_stacklevel=False`, which is what that form is for.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:709`](../compliance/rules/sympy/tests.py#L709) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C091 — `DeprecatedBehaviourOnlyInItsOwnTest`

> **Corpus:** Deprecated behavior may be called only inside its dedicated `warns_deprecated_sympy()` test; all other tests must use non-deprecated behavior.

- **Pre-condition —** each test the agent wrote that mentions deprecation at all.
- **Pass condition —** every such mention sits inside a `warns_deprecated_sympy()` block.

Which APIs are deprecated is not derivable from the patch, so "mentions deprecation" is a lexical stand-in and the rule is flagged as a heuristic.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:738`](../compliance/rules/sympy/tests.py#L738) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C094 — `UnevaluatedAssertionsUseUnchanged`

> **Corpus:** To assert that an expression remains unevaluated, a test must use `sympy.core.expr.unchanged(function, *args)` rather than compare repeated evaluations.

- **Pre-condition —** each assertion the agent wrote that an expression stays unevaluated -- written either with `unchanged(...)` or by comparing two identical evaluations.
- **Pass condition —** it is the `unchanged(...)` form.

`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:801`](../compliance/rules/sympy/tests.py#L801) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C095 — `DummyResultsUseDummyEq`

> **Corpus:** If an expression result contains `Dummy`, the test must compare it with `.dummy_eq(expected)` rather than direct `==`.

- **Pre-condition —** each assertion the agent wrote whose expression involves a `Dummy`.
- **Pass condition —** it compares with `.dummy_eq(...)` rather than `==`.

Whether a result *contains* a Dummy is a runtime property; the mention of `Dummy` in the assertion is a stand-in for it, hence the heuristic flag.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:851`](../compliance/rules/sympy/tests.py#L851) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C097 — `RandomTestsRunRepeatedly`

> **Corpus:** After adding a random test, the contributor must run it multiple times and confirm it consistently passes.

- **Pre-condition —** each test the agent wrote that draws on randomness.
- **Pass condition —** it was run repeatedly and passed every time -- withheld, because the bundle records no repeated-run outcome.

ownership `touched` · reads `files, repeated_runs` · tier `differential`

[`compliance/rules/sympy/tests.py:895`](../compliance/rules/sympy/tests.py#L895) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C098 — `ExpectedFailuresUseXfail`

> **Corpus:** A test skipped because it is expected to fail must use `@XFAIL`, not `@SKIP` or `skip()`.

- **Pre-condition —** each test the agent wrote that is skipped because it is expected to fail -- however that is spelled.
- **Pass condition —** it is marked `@XFAIL`, not `@SKIP` or `skip()`.

`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:922`](../compliance/rules/sympy/tests.py#L922) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C099 — `SlowTestsUseSlowMarker`

> **Corpus:** A test skipped only because it is slow must use `@slow`, not `@SKIP` or `skip()`.

- **Pre-condition —** each test the agent wrote that is skipped only because it is slow.
- **Pass condition —** it is marked `@slow`, not `@SKIP` or `skip()`.

`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:941`](../compliance/rules/sympy/tests.py#L941) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C102 — `XfailRemovedOncePassing`

> **Corpus:** If an XFAIL test begins to pass, the contributor must remove `@XFAIL` so it becomes a normal test.

- **Pre-condition —** each `@XFAIL` test in the code the agent touched.
- **Pass condition —** the test still fails, so the marker is still warranted.

Answered per test from the harness's before-and-after run: a test named in `FAIL_TO_PASS` has started to pass, and keeping `@XFAIL` on it is the violation. A test the harness did not run is withheld individually rather than assumed still failing.


ownership `touched` · reads `files, evaluation` · tier `differential`

[`compliance/rules/sympy/tests.py:998`](../compliance/rules/sympy/tests.py#L998) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C104 — `SlowTestsAreMarkedSlow`

> **Corpus:** A test taking more than one minute must be marked with `sympy.testing.pytest.slow` as `@slow`.

- **Pre-condition —** each test the agent wrote, any of which could exceed a minute.
- **Pass condition —** it is marked `@slow` if it takes more than a minute -- withheld, because the bundle records no test durations.

ownership `touched` · reads `files, test_timings` · tier `differential`

[`compliance/rules/sympy/tests.py:1040`](../compliance/rules/sympy/tests.py#L1040) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C105 — `HangingTestsUseSkip`

> **Corpus:** A hanging test must use `@SKIP` instead of `@slow`.

- **Pre-condition —** each test the agent wrote, any of which could hang.
- **Pass condition —** it is marked `@SKIP` rather than `@slow` if it hangs -- withheld, because a hanging test is only distinguishable from a slow one by running it.

ownership `touched` · reads `files, test_timings` · tier `differential`

[`compliance/rules/sympy/tests.py:1056`](../compliance/rules/sympy/tests.py#L1056) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C106 — `ValidatesSlowTests`

> **Corpus:** When validating tests marked `@slow` locally, a contributor must run `python bin/test --slow` and require it to pass.

- **Pre-condition —** the contribution carries a test marked `@slow`.
- **Pass condition —** `python bin/test --slow` was run and reported no failure.

ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/sympy/tests.py:1082`](../compliance/rules/sympy/tests.py#L1082) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C107 — `OptionalDependenciesViaImportModule`

> **Corpus:** A test for optional-dependency functionality must import the dependency with `sympy.external.import_module()` so absence returns `None` instead of failing import.

- **Pre-condition —** each reference the agent's test code makes to an optional dependency, whether by a plain import or by `import_module()`.
- **Pass condition —** it goes through `sympy.external.import_module()`, which returns `None` when the dependency is absent instead of breaking collection.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:1104`](../compliance/rules/sympy/tests.py#L1104) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C112 — `DoctestsRunAndPass`

> **Corpus:** Before acceptance, contributed doctests must pass when run with `python bin/doctest` (optionally followed by a file or submodule argument).

- **Pre-condition —** the agent contributed or edited a docstring carrying doctests.
- **Pass condition —** `python bin/doctest` was run and reported no failure.

ownership `enclosing` · reads `files, commands` · tier `static`

[`compliance/rules/sympy/tests.py:1148`](../compliance/rules/sympy/tests.py#L1148) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C113 — `DoctestsImportWhatTheyCall`

> **Corpus:** Each doctest must be self-contained and explicitly import every function it uses.

- **Pre-condition —** each doctest the agent owns that calls a function by a bare name.
- **Pass condition —** every such name is explicitly imported or defined inside the doctest itself, so the example is self-contained.

ownership `enclosing` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:1171`](../compliance/rules/sympy/tests.py#L1171) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C114 — `DoctestsDefineTheirSymbols`

> **Corpus:** Each doctest must explicitly define every symbol it uses, importing common names from `sympy.abc` or creating other/assumed symbols with `symbols()`.

- **Pre-condition —** each doctest the agent owns that uses a bare symbol name.
- **Pass condition —** every such name is bound in the doctest, by importing it from `sympy.abc` or by creating it with `symbols()`.

"A symbol name" is taken to be the set `sympy.abc` publishes -- single letters and Greek names -- which is a stand-in for knowing what is a symbol, hence heuristic.


`heuristic` · ownership `enclosing` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:1204`](../compliance/rules/sympy/tests.py#L1204) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C115 — `DoctestOutputIsExact`

> **Corpus:** A doctest must show `>>>` before inputs and exact Python-session output strings after them.

- **Pre-condition —** each doctest example the agent owns.
- **Pass condition —** its expected output matches a real session exactly -- withheld, because exactness can only be established by running the example.

ownership `enclosing` · reads `files, doctest_run` · tier `differential`

[`compliance/rules/sympy/tests.py:1245`](../compliance/rules/sympy/tests.py#L1245) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C118 — `DependencyDoctestsDeclareTheirLibraries`

> **Corpus:** A dependency-requiring doctest must declare libraries with `@doctest_depends_on(...)`, not `# doctest: +SKIP`.

- **Pre-condition —** each doctest the agent owns that needs an optional library -- whether it imports one or skips itself to avoid one.
- **Pass condition —** the library is declared with `@doctest_depends_on(...)` and the example is not silenced with `# doctest: +SKIP`.

`heuristic` · ownership `enclosing` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:1270`](../compliance/rules/sympy/tests.py#L1270) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C119 — `BlankLinesInOutputUseMarker`

> **Corpus:** If expected doctest output contains a blank line, the expected output must contain the literal marker `<BLANKLINE>` in its place.

- **Pre-condition —** each doctest the agent owns whose expected output runs across a blank line -- written either with the marker or with a raw blank line.
- **Pass condition —** the blank line is written as the literal `<BLANKLINE>`.

A raw blank line terminates expected output, so it is invisible to the doctest parser and has to be found by scanning the docstring text; the scan is a heuristic.


`heuristic` · ownership `enclosing` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:1310`](../compliance/rules/sympy/tests.py#L1310) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C126 — `NoneResultsArePrinted`

> **Corpus:** To display a `None` result in a doctest, the example must call `print(<expression>)` so the expected output contains `None`.

- **Pre-condition —** each doctest example the agent owns whose expected output is `None`.
- **Pass condition —** the example calls `print(...)`, which is what makes `None` show.

ownership `enclosing` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:1409`](../compliance/rules/sympy/tests.py#L1409) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C130 — `ChangedExpectationsAreVerified`

> **Corpus:** Before updating an expected expression, the contributor must verify equivalence for all relevant domains, using methods such as simplification, random values, or `.equals()`.

- **Pre-condition —** each expected value the agent replaced in an existing test or doctest.
- **Pass condition —** the new value was verified equivalent across the relevant domains -- withheld, since nothing in the bundle records that verification.

ownership `touched` · reads `files, expression_eval` · tier `differential`

[`compliance/rules/sympy/tests.py:1437`](../compliance/rules/sympy/tests.py#L1437) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C137 — `ExactValuesInTests`

> **Corpus:** Unless testing floating-point behavior, a test must use exact SymPy values such as `S(1)/2`, not Python float-producing expressions such as `1/2`.

- **Pre-condition —** each numeric-constant division the agent wrote in a test that is not about floating point.
- **Pass condition —** at least one side is an exact SymPy number, so the value is `S(1)/2` rather than Python's `1/2`.

`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:1477`](../compliance/rules/sympy/tests.py#L1477) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C139 — `CompareExpressionsNotStrings`

> **Corpus:** Except in printer tests, assertions must compare SymPy expressions directly rather than their `str(...)` forms.

- **Pre-condition —** each equality assertion the agent wrote outside a printer test.
- **Pass condition —** neither side is the `str(...)` form of an expression.

`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:1563`](../compliance/rules/sympy/tests.py#L1563) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C140 — `ConstructExpressionsDirectly`

> **Corpus:** Except in parser tests, test inputs must construct expressions directly rather than call `sympify()` on string expressions.

- **Pre-condition —** each `sympify`/`S`/`parse_expr` call the agent wrote in a test that is not a parser test.
- **Pass condition —** its argument is not a string expression -- the input is constructed directly instead.

`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:1605`](../compliance/rules/sympy/tests.py#L1605) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C141 — `AssumptionsComparedIdentically`

> **Corpus:** An assumptions test must compare with `is True`, `is False`, or `is None`, not rely on truthiness.

- **Pre-condition —** each assertion the agent wrote that queries an assumption.
- **Pass condition —** it compares with `is True`, `is False` or `is None` rather than relying on truthiness.

`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:1643`](../compliance/rules/sympy/tests.py#L1643) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html

### SYMPY-C142 — `FloatTestsUseFloatLiterals`

> **Corpus:** If a test intentionally exercises floating-point behavior, it must use an explicit float literal such as `0.5`, not integer division such as `1/2`.

- **Pre-condition —** each numeric constant the agent wrote in a test that does exercise floating-point behaviour.
- **Pass condition —** it is written as an explicit float literal, not as integer division.

`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/tests.py:1498`](../compliance/rules/sympy/tests.py#L1498) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/writing-tests.html


## sympy — Specialized changes

### SYMPY-C151 — `LibraryOptionalDependencyImports`

> **Corpus:** When SymPy library code imports an optional dependency, it must use `sympy.external.import_module()` rather than importing the dependency directly.

- **Pre-condition —** each reference the agent's library code makes to an optional dependency, by plain import or by `import_module()`.
- **Pass condition —** it goes through `sympy.external.import_module()`, so an absent dependency yields `None` rather than breaking the import.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:216`](../compliance/rules/sympy/specialized.py#L216) · source: https://docs.sympy.org/dev/contributing/dependencies.html

### SYMPY-C152 — `TestsUseSympyPytestWrappers`

> **Corpus:** SymPy tests must use wrappers from `sympy.testing.pytest` instead of calling pytest functions directly.

- **Pre-condition —** each `pytest.<helper>` the agent used in a test module, where SymPy publishes its own wrapper.
- **Pass condition —** none -- the wrapper from `sympy.testing.pytest` must be used instead, so any direct use is the violation.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:265`](../compliance/rules/sympy/specialized.py#L265) · source: https://docs.sympy.org/dev/contributing/dependencies.html

### SYMPY-C153 — `OptionalDependencyTestsStaySkippable`

> **Corpus:** A test requiring an optional dependency must remain runnable without that dependency by calling `sympy.testing.pytest.skip("<reason>")` or, for an entire file, setting `skip = True`.

- **Pre-condition —** each test module the agent wrote that needs an optional dependency.
- **Pass condition —** it can still be collected without that dependency, by calling `skip("<reason>")` or setting a module-level `skip = True`.

"Needs an optional dependency" is read from the module's own imports and `import_module()` calls, which is a stand-in for actually requiring it -- hence the heuristic flag.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:303`](../compliance/rules/sympy/specialized.py#L303) · source: https://docs.sympy.org/dev/contributing/dependencies.html

### SYMPY-C239 — `BreakingChangeDocumentsMigration`

> **Corpus:** A necessary backwards-incompatible API change must document how users should update their code.

- **Pre-condition —** each public definition the agent removed from library code.
- **Pass condition —** the contribution documents how users should update their code.

Reading a removed public name as a backwards-incompatible change is a stand-in: some removals are internal refactors whose name merely looks public. Flagged accordingly.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:368`](../compliance/rules/sympy/specialized.py#L368) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C240 — `OldApiKeepsWorking`

> **Corpus:** During the deprecation period, the old API must continue functioning unchanged except for an emitted, suppressible warning.

- **Pre-condition —** each deprecation the agent introduced.
- **Pass condition —** the old API still behaves as before, changed only by a suppressible warning -- withheld, because that is only observable by calling it.

ownership `touched` · reads `files, deprecated_api_run` · tier `differential`

[`compliance/rules/sympy/specialized.py:429`](../compliance/rules/sympy/specialized.py#L429) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C241 — `WarningIsAvoidable`

> **Corpus:** A deprecation warning must be avoidable through a documented user-code migration and must not fire on the correct replacement API.

- **Pre-condition —** each deprecation the agent introduced.
- **Pass condition —** the documented migration silences the warning and the replacement API does not itself warn -- withheld, because that needs both paths executed.

ownership `touched` · reads `files, deprecated_api_run` · tier `differential`

[`compliance/rules/sympy/specialized.py:446`](../compliance/rules/sympy/specialized.py#L446) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C243 — `ReplacementAvailableSameVersion`

> **Corpus:** During the deprecation period, users must have a replacement usage that stops the warning in the same SymPy version.

- **Pre-condition —** each deprecation the agent introduced.
- **Pass condition —** a replacement usage exists in this same version that stops the warning -- withheld, because confirming it needs the replacement executed.

ownership `touched` · reads `files, deprecated_api_run` · tier `differential`

[`compliance/rules/sympy/specialized.py:463`](../compliance/rules/sympy/specialized.py#L463) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C246 — `InternalUsesMigratedFirst`

> **Corpus:** Before adding a deprecation, the contributor must replace every internal and doctest use of the deprecated behavior with the new API.

- **Pre-condition —** each deprecation the agent introduced.
- **Pass condition —** the contribution leaves no use of the deprecated name outside the deprecation site itself.

Only the patch is visible, so a use elsewhere in the repository cannot be seen; this checks what the contribution itself still calls, which is a lower bound.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:483`](../compliance/rules/sympy/specialized.py#L483) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C247 — `MessageNamesApiAndReplacement`

> **Corpus:** A `sympy_deprecation_warning(...)` message must state the fully contextualized deprecated API and its replacement.

- **Pre-condition —** each `sympy_deprecation_warning(...)` message the agent wrote.
- **Pass condition —** it names the deprecated API in context and its replacement.

"Names the replacement" is judged by migration wording plus a second identifier, which is a proxy for meaning it.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:523`](../compliance/rules/sympy/specialized.py#L523) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C248 — `DeprecationSetsSinceVersion`

> **Corpus:** A deprecation call or decorator must set `deprecated_since_version` to the version in `sympy/release.py` without `.dev`.

- **Pre-condition —** each deprecation the agent introduced.
- **Pass condition —** it sets `deprecated_since_version` to a release version with no `.dev` suffix.

Whether that version equals the one in `sympy/release.py` is not checked: the release module is not part of the contribution, so the bundle does not carry it. The form is.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:564`](../compliance/rules/sympy/specialized.py#L564) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C249 — `DeprecationSetsCrossReferenceTarget`

> **Corpus:** A deprecation call or decorator must set `active_deprecations_target` to its cross-reference target in `doc/src/explanation/active-deprecations.md`.

- **Pre-condition —** each deprecation the agent introduced.
- **Pass condition —** it sets `active_deprecations_target`, and if the contribution also edits `active-deprecations.md`, that target is defined there.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:594`](../compliance/rules/sympy/specialized.py#L594) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C250 — `DeprecationSetsStacklevel`

> **Corpus:** A `sympy_deprecation_warning(...)` call must set `stacklevel` so the console warning points to the user's calling line.

- **Pre-condition —** each `sympy_deprecation_warning(...)` the agent wrote.
- **Pass condition —** it passes `stacklevel`, so the warning points at the user's call.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:622`](../compliance/rules/sympy/specialized.py#L622) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C252 — `DocstringCarriesDeprecatedNote`

> **Corpus:** Every relevant docstring must include a `.. deprecated:: <version>` note for the deprecation.

- **Pre-condition —** each deprecation the agent introduced on a documented definition.
- **Pass condition —** that definition's docstring carries a `.. deprecated:: <version>` note.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:756`](../compliance/rules/sympy/specialized.py#L756) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C253 — `AddsActiveDeprecationsSection`

> **Corpus:** Every deprecation must add a section under the applicable version in `doc/src/explanation/active-deprecations.md`.

- **Pre-condition —** each deprecation the agent introduced.
- **Pass condition —** the contribution adds a section to `active-deprecations.md` under a version heading.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:864`](../compliance/rules/sympy/specialized.py#L864) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C254 — `ActiveSectionDefinesTarget`

> **Corpus:** The active-deprecation section must define a unique `(…deprecation…)=` or `(…deprecated…)=` cross-reference target before its header.

- **Pre-condition —** the contribution adds lines to `active-deprecations.md`.
- **Pass condition —** a `(…deprecation…)=` cross-reference target is defined before the section's heading.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:894`](../compliance/rules/sympy/specialized.py#L894) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C255 — `DeprecationHasAWarnsTest`

> **Corpus:** A deprecation must add a test whose deprecated call is enclosed by `with warns_deprecated_sympy():` and verifies both the warning and continued behavior.

- **Pre-condition —** each deprecation the agent introduced.
- **Pass condition —** the contribution adds a test whose deprecated call sits inside `with warns_deprecated_sympy():` and which also checks the behaviour still holds.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:1013`](../compliance/rules/sympy/specialized.py#L1013) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C256 — `ValidatesDeprecationWithBinTest`

> **Corpus:** Before submission, the contributor must run `python bin/test` and confirm the deprecation test passes and no other code emits `SymPyDeprecationWarning`.

- **Pre-condition —** each deprecation the agent introduced.
- **Pass condition —** `python bin/test` was run and reported no failure.

ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/sympy/specialized.py:1056`](../compliance/rules/sympy/specialized.py#L1056) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C258 — `NoDirectDeprecationWarning`

> **Corpus:** Code must not instantiate or emit `SymPyDeprecationWarning` directly; it must use `sympy_deprecation_warning(...)` or, for a whole function/method, `@deprecated(...)`.

- **Pre-condition —** each reference the agent's library code makes to `SymPyDeprecationWarning`.
- **Pass condition —** the warning is raised through `sympy_deprecation_warning(...)` or `@deprecated(...)`, not instantiated or emitted directly.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:640`](../compliance/rules/sympy/specialized.py#L640) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C259 — `MessageIsOneWrappedParagraph`

> **Corpus:** A `sympy_deprecation_warning(...)` message must be no more than one paragraph and wrap prose to 80 characters except unwrappable code.

- **Pre-condition —** each `sympy_deprecation_warning(...)` message the agent wrote.
- **Pass condition —** it is a single paragraph whose prose lines are within 80 characters.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:679`](../compliance/rules/sympy/specialized.py#L679) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C260 — `MessageExplainsMigrationOnly`

> **Corpus:** A `sympy_deprecation_warning(...)` message must explain migration but must not contain rationale, internal details, version metadata, or an active-deprecations URL already supplied by arguments.

- **Pre-condition —** each `sympy_deprecation_warning(...)` message the agent wrote.
- **Pass condition —** it explains migration and carries no rationale, version metadata or active-deprecations URL, all of which the call's own arguments already supply.

Rationale is detected lexically, so this is a proxy rather than a decision.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:701`](../compliance/rules/sympy/specialized.py#L701) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C261 — `MessageIsPlainText`

> **Corpus:** A deprecation warning message must be plain text without RST or Markdown markup.

- **Pre-condition —** each `sympy_deprecation_warning(...)` message the agent wrote.
- **Pass condition —** it is plain text, with no RST or Markdown markup -- the message is printed to a console, not rendered.

Markup is detected by its common spellings, so unusual constructs may pass.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:730`](../compliance/rules/sympy/specialized.py#L730) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C262 — `DeprecatedDirectiveFollowsSummary`

> **Corpus:** If an entire function is deprecated, its `.. deprecated:: <version>` directive must appear immediately below the docstring summary.

- **Pre-condition —** each `.. deprecated::` note in a docstring the agent deprecated.
- **Pass condition —** it sits immediately below the docstring's summary line.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:794`](../compliance/rules/sympy/specialized.py#L794) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C263 — `DeprecatedDirectiveIsOneParagraph`

> **Corpus:** A docstring `.. deprecated:: <version>` note must be at most one paragraph and state both the deprecated feature and its replacement.

- **Pre-condition —** each `.. deprecated::` note in a docstring the agent deprecated.
- **Pass condition —** it is at most one paragraph and names both the deprecated feature and its replacement.

"Names the replacement" is judged by migration wording, which is a proxy.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:818`](../compliance/rules/sympy/specialized.py#L818) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C264 — `ActiveSectionExplainsTheChange`

> **Corpus:** An active-deprecations section must explain what is deprecated, its replacement, and why the change was made.

- **Pre-condition —** the contribution adds lines to `active-deprecations.md`.
- **Pass condition —** the section says what is deprecated, what replaces it, and why.

All three are judged from wording, so this is a proxy for the content being adequate.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:916`](../compliance/rules/sympy/specialized.py#L916) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C265 — `ActiveSectionUsesLevelThreeHeading`

> **Corpus:** An active-deprecations entry must use a level-3 heading named for the deprecated item under the corresponding version, normally near the file top.

- **Pre-condition —** the contribution adds lines to `active-deprecations.md`.
- **Pass condition —** the entry is a level-3 heading named for the deprecated item.

Whether the heading sits under the *corresponding* version cannot be seen from added lines alone when the version heading is pre-existing context, so only the level and a non-empty name are graded.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:943`](../compliance/rules/sympy/specialized.py#L943) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C266 — `ActiveSectionNamesSubmodule`

> **Corpus:** If a deprecated object is not exported from top-level `sympy`, its active-deprecations entry must identify its defining submodule.

- **Pre-condition —** each deprecation the agent introduced outside a top-level export, for which an active-deprecations section was added.
- **Pass condition —** that section identifies the submodule the object is defined in.

Whether an object is exported from top-level `sympy` is not visible in the patch, so the pre-condition fires on every added deprecation and the check looks for the defining module path anywhere in the section.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/specialized.py:971`](../compliance/rules/sympy/specialized.py#L971) · source: https://docs.sympy.org/dev/contributing/deprecations.html

### SYMPY-C268 — `BreakingChangeInReleaseNotes`

> **Corpus:** A deprecation or removal after its deprecation period must include a `BREAKING CHANGE` entry inside the pull request's release-notes block.

- **Pre-condition —** the contribution introduces a deprecation or removes a public API.
- **Pass condition —** its release-notes block carries a `BREAKING CHANGE` entry.

ownership `created` · reads `files, pr_text` · tier `static`

[`compliance/rules/sympy/specialized.py:1074`](../compliance/rules/sympy/specialized.py#L1074) · source: https://docs.sympy.org/dev/contributing/deprecations.html


## sympy — Documentation and docstrings

### SYMPY-C018 — `DoctestNoStarImport`

> **Corpus:** A doctest must not use `from sympy import *`; it must import every used SymPy name explicitly.

- **Pre-condition —** every doctest example the agent wrote or edited.
- **Pass condition —** it does not import from SymPy with a star.

Only the prohibition is checked. The rule's other half -- that every used name be imported explicitly -- needs name resolution over the whole example, which is C113's business in `tests.py`, not a second implementation here.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:885`](../compliance/rules/sympy/documentation.py#L885) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C146 — `DocsBuiltLocally`

> **Corpus:** When validating documentation with locally installed dependencies, the contributor must run `cd doc` and then `make html`, and the build must succeed.

- **Pre-condition —** the contribution changes documentation.
- **Pass condition —** the agent ran `cd doc` and then `make html`, and the build succeeded.

ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/sympy/documentation.py:1745`](../compliance/rules/sympy/documentation.py#L1745) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/build-docs.html

### SYMPY-C150 — `PdfBuildUsesDoubleBackticks`

> **Corpus:** If the PDF documentation build fails, the contributor must ensure code is delimited with double backticks rather than single backticks.

- **Pre-condition —** a PDF documentation build the agent ran that failed.
- **Pass condition —** the documentation it wrote delimits code with double backticks.

Structurally unreachable on this benchmark, and recorded as such rather than removed. The antecedent is a *failing PDF build*: SWE-bench instances are bug fixes, no stored run has ever invoked `make latexpdf`, and the corpus is the specification. The rule reports `not_applicable` for the honest reason that its antecedent never arises -- which is different from a broken pre-condition, and `docs/rule-reachability.md` records which is which.


ownership `touched` · reads `files, commands` · tier `static`

[`compliance/rules/sympy/documentation.py:1820`](../compliance/rules/sympy/documentation.py#L1820) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/build-docs.html

### SYMPY-C168 — `TripleDoubleQuotes`

> **Corpus:** A docstring must use triple double quotes.

- **Pre-condition —** every docstring the agent wrote or edited.
- **Pass condition —** it is opened with triple double quotes.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:464`](../compliance/rules/sympy/documentation.py#L464) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C169 — `RawWhenBackslash`

> **Corpus:** If a docstring contains a backslash, it must use a raw triple-double-quoted string.

- **Pre-condition —** every docstring the agent owns whose source contains a backslash.
- **Pass condition —** it is written as a raw string.

Read from the source bytes, not the parsed value: without the `r` prefix Python has already turned the backslash into whatever it escaped, so the parsed text no longer contains one. That silent substitution is the defect.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:485`](../compliance/rules/sympy/documentation.py#L485) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C170 — `BlankLineBeforeClosingQuotes`

> **Corpus:** A docstring must contain a blank line immediately before its closing quotes.

- **Pre-condition —** every multi-line docstring the agent owns.
- **Pass condition —** the line immediately before its closing quotes is blank.

Single-line docstrings are excluded: the guidance is about the layout of a docstring whose closing quotes sit on their own line, and `"""Return x."""` has none.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:512`](../compliance/rules/sympy/documentation.py#L512) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C172 — `ClassDocstringUnderDefinition`

> **Corpus:** A class-level docstring must appear immediately under its class definition.

- **Pre-condition —** every class docstring the agent owns.
- **Pass condition —** it opens on the line following the class statement, with no blank line between them.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:535`](../compliance/rules/sympy/documentation.py#L535) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C173 — `ExampleCodeIsADoctest`

> **Corpus:** Python example code in a docstring must be formatted as a doctest, not a `::` code block.

- **Pre-condition —** every `::` literal block in a docstring the agent owns whose body reads as Python.
- **Pass condition —** none -- example Python belongs in a doctest, so a literal block holding it is the violation.

"Reads as Python" is decided lexically from the block's own text, which is why this is a heuristic: a literal block of shell or output that happens to contain an equals sign would be mistaken for one.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:556`](../compliance/rules/sympy/documentation.py#L556) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C175 — `DocumentationBuildsWithoutSphinxErrors`

> **Corpus:** A documentation contribution must produce no Sphinx errors when built locally with `cd doc; make html` or with `docker run --rm -v /absolute/path/to/sympy:/sympy sympy_htmldoc` after substituting the actual checkout path.

- **Pre-condition —** the contribution changes documentation.
- **Pass condition —** a local documentation build was run -- through the makefile or the `sympy_htmldoc` image -- and Sphinx emitted no errors.

ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/sympy/documentation.py:1768`](../compliance/rules/sympy/documentation.py#L1768) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C176 — `SectionOrder`

> **Corpus:** Function, class, and method docstrings should order sections as Summary, Explanation, Examples, Parameters, See Also, References.

- **Pre-condition —** every docstring the agent owns carrying at least two of the sections the guide orders.
- **Pass condition —** those sections appear in the published order.

Only the sections the rule enumerates are ordered. A docstring may also carry Returns or Notes, and the rule says nothing about where those go, so they are ignored rather than assumed.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:671`](../compliance/rules/sympy/documentation.py#L671) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C177 — `ExactSectionNames`

> **Corpus:** Supported docstring section names must remain exact, including plural `Examples` even for one example.

- **Pre-condition —** every section heading the agent wrote, recognised by the published name or by a common variant of one.
- **Pass condition —** it is spelled exactly as the published name, plural `Examples` included.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:703`](../compliance/rules/sympy/documentation.py#L703) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C178 — `HeadingUnderlineLength`

> **Corpus:** A docstring section heading must be underlined by the same number of equals signs as heading characters.

- **Pre-condition —** every docstring section heading the agent wrote.
- **Pass condition —** its underline is equals signs, exactly as many as the heading has characters.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:732`](../compliance/rules/sympy/documentation.py#L732) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C180 — `SummaryRequired`

> **Corpus:** Every docstring must begin with a single-sentence summary.

- **Pre-condition —** every function or class docstring the agent created.
- **Pass condition —** it opens with a summary, before any section heading.

`created`, not `touched`: a docstring the agent merely edited a line of already had whatever summary it has, and demanding one would score its original author.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:764`](../compliance/rules/sympy/documentation.py#L764) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C181 — `SummaryIsOneSentence`

> **Corpus:** A docstring summary must occupy one line and end with a period.

- **Pre-condition —** every docstring the agent owns that has a summary.
- **Pass condition —** the summary occupies one line and ends with a period.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:785`](../compliance/rules/sympy/documentation.py#L785) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C183 — `ExamplesSectionRequired`

> **Corpus:** Every docstring must contain an `Examples` section.

- **Pre-condition —** every function or class docstring the agent created.
- **Pass condition —** it carries an `Examples` section.

Plan §4.2 names this rule as the worked case for `created` ownership: an `Examples` block is not demanded of a docstring the agent merely brushed. Module docstrings are out of scope -- the guide's Examples section governs the documented object.


ownership `created` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:808`](../compliance/rules/sympy/documentation.py#L808) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C184 — `BlankLineBeforeFirstDoctest`

> **Corpus:** An Examples section must contain a blank line immediately before its first doctest.

- **Pre-condition —** every Examples section the agent owns that contains a doctest.
- **Pass condition —** a blank line separates the section heading from its first doctest.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:915`](../compliance/rules/sympy/documentation.py#L915) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C185 — `ExamplesSeparatedByBlankLines`

> **Corpus:** Multiple docstring examples must be separated by blank lines.

- **Pre-condition —** every point in an Examples section the agent owns where a new example begins -- a fresh statement after a previous one produced output.
- **Pass condition —** a blank line separates it from the example before it.

Heuristic: a run of statements with no intervening output is one example, and a statement after output starts another. That is a proxy for what a reader would call a separate example, and reading every `>>>` as one would fail every idiomatic docstring in the project.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:953`](../compliance/rules/sympy/documentation.py#L953) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C186 — `ExplanatoryTextIsSeparated`

> **Corpus:** Explanatory text between doctests must have blank lines both before and after it.

- **Pre-condition —** every run of prose sitting between two doctests in an Examples section the agent owns.
- **Pass condition —** a blank line above it and a blank line below it.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:997`](../compliance/rules/sympy/documentation.py#L997) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C188 — `LongDoctestInputIsWrapped`

> **Corpus:** A doctest input longer than 80 characters must be wrapped as valid Python using the `...` continuation prompt.

- **Pre-condition —** every doctest example the agent owns whose input is longer than 80 characters.
- **Pass condition —** it is wrapped across lines with the `...` continuation prompt, so no single line exceeds the limit.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1062`](../compliance/rules/sympy/documentation.py#L1062) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C190 — `DoctestsRunAfterChangingExamples`

> **Corpus:** After adding or changing a docstring example, the contributor must run `python bin/doctest <file-or-submodule>` or `python bin/doctest` and fix every failure.

- **Pre-condition —** the agent added or changed a docstring example.
- **Pass condition —** it ran `python bin/doctest`, and the run reported no failure.

ownership `touched` · reads `files, commands` · tier `trajectory`

[`compliance/rules/sympy/documentation.py:1792`](../compliance/rules/sympy/documentation.py#L1792) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C191 — `ParametersSectionRequired`

> **Corpus:** If the documented signature lists parameters, the docstring must include a `Parameters` section.

- **Pre-condition —** every function docstring the agent created whose signature takes parameters other than `self` or `cls`.
- **Pass condition —** it carries a `Parameters` section.

ownership `created` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:830`](../compliance/rules/sympy/documentation.py#L830) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C192 — `ParameterNamesInCodeMarkup`

> **Corpus:** Parameter names in a Parameters section must use double-backtick code markup.

- **Pre-condition —** every entry of a Parameters section the agent owns.
- **Pass condition —** its parameter name is wrapped in double backticks.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1119`](../compliance/rules/sympy/documentation.py#L1119) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C193 — `ParameterTypeSeparator`

> **Corpus:** A typed parameter entry must format its separator as `name : type`; omit the colon when no type is supplied.

- **Pre-condition —** every entry of a Parameters section the agent owns.
- **Pass condition —** an entry that supplies a type separates it as `name : type`, and an entry that supplies none carries no colon at all.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1143`](../compliance/rules/sympy/documentation.py#L1143) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C194 — `SeeAlsoContinuationIndented`

> **Corpus:** If a See Also description spans multiple lines, every continuation line must be indented.

- **Pre-condition —** every See Also entry the agent owns whose description continues past its first line.
- **Pass condition —** every continuation line is indented under the entry.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1170`](../compliance/rules/sympy/documentation.py#L1170) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C195 — `SeeAlsoOnlySymPyObjects`

> **Corpus:** A See Also section must contain only SymPy functions, classes, or methods; external links belong in prose or References.

- **Pre-condition —** every See Also entry the agent owns.
- **Pass condition —** it names a SymPy object rather than an external link.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1230`](../compliance/rules/sympy/documentation.py#L1230) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C196 — `SeeAlsoBareClassNames`

> **Corpus:** In See Also, a class must be written as its bare class name, not `class:Name`, `class:`Name``, or `:class:`Name``.

- **Pre-condition —** every See Also entry the agent owns.
- **Pass condition —** it is written as a bare name, with no `:class:` role and no backticks.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1265`](../compliance/rules/sympy/documentation.py#L1265) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C197 — `ReferencesNumberedFromOne`

> **Corpus:** A References section must number citations from 1 in first-citation order.

- **Pre-condition —** every References section the agent owns that carries numbered citations.
- **Pass condition —** they run from 1 upwards in the order they are written.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1289`](../compliance/rules/sympy/documentation.py#L1289) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C199 — `DoiIsAHyperlink`

> **Corpus:** A paper reference with a DOI must include that DOI as a clickable hyperlink.

- **Pre-condition —** every reference the agent owns that carries a DOI.
- **Pass condition —** the DOI is given as a clickable link.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1322`](../compliance/rules/sympy/documentation.py#L1322) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C203 — `MathFunctionDocumentedAtClassLevel`

> **Corpus:** For a mathematical-function class, documentation must live at class level and the `eval` method must not have its own docstring.

- **Pre-condition —** every mathematical-function class defining `eval` whose documentation the agent wrote -- its class docstring, a docstring on `eval`, or the class itself.
- **Pass condition —** the class carries the docstring and `eval` carries none.

The antecedent is a *documentation decision*, not any edit inside the class. Two narrowings, both found by running this rule against the pilot before trusting it. Deciding ownership on the class span made an agent that edited one line of a 131-line `coth` class the owner of a docstring SymPy's authors wrote -- the A6 defect. Deciding it on the class's own lines plus `eval` still credited an agent that had only fixed logic inside `eval`'s body, which is not documentation work either. Both produced four spurious passes, and invariant 5 forbids both.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1355`](../compliance/rules/sympy/documentation.py#L1355) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C206 — `ProseCrossReferencesUseRoles`

> **Corpus:** Prose references to documented SymPy objects must use Sphinx cross-reference syntax, normally `:obj:`~.name`` for top-level public objects.

- **Pre-condition —** every reference to a SymPy object in the prose of a docstring the agent owns, written either as a role or as a single-backtick span.
- **Pass condition —** it is written as a Sphinx cross-reference role.

Heuristic twice over: a single-backtick span naming an identifier is taken to be an object reference, and whether the name is a SymPy object is decided against a curated list. A bare name in prose with no markup at all is not detected, which narrows the pre-condition rather than the grading.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1430`](../compliance/rules/sympy/documentation.py#L1430) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C207 — `NonTopLevelObjectsUseFullPath`

> **Corpus:** A SymPy object not exported from top-level `sympy` must be cross-referenced by its full path down to the defining file and must not use `~.` abbreviation.

- **Pre-condition —** every cross-reference in a docstring the agent owns whose target is not a name SymPy exports from its top level.
- **Pass condition —** it gives the object's full dotted path and does not abbreviate with `~.`.

Heuristic: "not exported from the top level" is decided against a curated list of top-level names, which is necessarily partial.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1478`](../compliance/rules/sympy/documentation.py#L1478) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C208 — `UnlinkableNamesUseCodeMarkup`

> **Corpus:** Python built-ins, external-library objects, parameters, and other unlinkable names must use double-backtick code markup rather than `:obj:`.

- **Pre-condition —** every `:obj:` cross-reference the agent wrote whose target is a Python built-in, an external library's object, or a parameter of the documented function.
- **Pass condition —** none -- nothing unlinkable may be given a role, so each such reference is the violation.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1508`](../compliance/rules/sympy/documentation.py#L1508) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C210 — `CustomTextLinksOmitTilde`

> **Corpus:** A custom-text object link must use `:obj:`custom text <object>`` syntax and must not include `~` in the target.

- **Pre-condition —** every cross-reference the agent wrote that supplies custom link text.
- **Pass condition —** it uses the `:obj:`text <object>`` form with no `~` in the target.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1544`](../compliance/rules/sympy/documentation.py#L1544) · source: https://docs.sympy.org/dev/contributing/docstring.html

### SYMPY-C213 — `NoMarkdownOutsideNarrativeDocs`

> **Corpus:** A contributor must not use Markdown for non-narrative documentation.

- **Pre-condition —** every Markdown file the agent added or edited inside the library source tree, where documentation is not narrative.
- **Pass condition —** none -- Markdown is supported for narrative documentation only, so such a file is the violation.

Scoped to the library tree deliberately. `doc/` is where narrative documentation lives, and a Markdown file at the repository root is project metadata rather than the non-narrative documentation this rule governs.


ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1569`](../compliance/rules/sympy/documentation.py#L1569) · source: https://docs.sympy.org/dev/contributing/documentation-style-guide.html

### SYMPY-C214 — `DocstringsUseRst`

> **Corpus:** Docstrings should use reStructuredText syntax, not Markdown.

- **Pre-condition —** every docstring the agent wrote or edited.
- **Pass condition —** it carries no Markdown-only construct.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:649`](../compliance/rules/sympy/documentation.py#L649) · source: https://docs.sympy.org/dev/contributing/documentation-style-guide.html

### SYMPY-C216 — `RawWhenLatex`

> **Corpus:** If a docstring contains LaTeX, it must be a raw string.

- **Pre-condition —** every docstring the agent owns whose source contains LaTeX.
- **Pass condition —** it is written as a raw string.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:630`](../compliance/rules/sympy/documentation.py#L630) · source: https://docs.sympy.org/dev/contributing/documentation-style-guide.html

### SYMPY-C221 — `VerbatimCodeUsesDoubleBackticks`

> **Corpus:** Verbatim code in RST documentation must be enclosed in double backticks, as in ``code``.

- **Pre-condition —** every single-backtick span the agent wrote in an RST documentation file.
- **Pass condition —** none -- a single backtick renders as math rather than code, so verbatim code needs double backticks and a single-backtick span is the violation.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1596`](../compliance/rules/sympy/documentation.py#L1596) · source: https://docs.sympy.org/dev/contributing/documentation-style-guide.html

### SYMPY-C227 — `RstHeadingAdornment`

> **Corpus:** An RST section heading underline, and optional overline, must use one repeated punctuation character and be at least as long as the heading text.

- **Pre-condition —** every RST section heading the agent wrote.
- **Pass condition —** its underline, and its overline if it has one, is one repeated punctuation character at least as long as the heading text.

ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1620`](../compliance/rules/sympy/documentation.py#L1620) · source: https://docs.sympy.org/dev/contributing/documentation-style-guide.html

### SYMPY-C228 — `NarrativeDocsUseAmericanSpelling`

> **Corpus:** Narrative SymPy documentation must use American spelling and punctuation.

- **Pre-condition —** every narrative documentation file the agent wrote lines in.
- **Pass condition —** none of those lines uses a British spelling.

Heuristic: a word list is a proxy for a spelling standard, never the standard itself. It cannot see a British spelling it does not list, and cannot tell a quoted British spelling from an authored one.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1649`](../compliance/rules/sympy/documentation.py#L1649) · source: https://docs.sympy.org/dev/contributing/documentation-style-guide.html

### SYMPY-C234 — `DocumentationUsesGenderNeutralThey`

> **Corpus:** SymPy documentation must use gender-neutral `they` instead of `he` or `she`.

- **Pre-condition —** every piece of documentation the agent wrote -- a narrative documentation file, or a docstring.
- **Pass condition —** it refers to a person as `they` rather than `he` or `she`.

Heuristic: matching pronoun words cannot tell a pronoun from a quoted one, nor `her` the pronoun from a name. It is a proxy for the tone the guide asks for.


`heuristic` · ownership `touched` · reads `files` · tier `static`

[`compliance/rules/sympy/documentation.py:1690`](../compliance/rules/sympy/documentation.py#L1690) · source: https://docs.sympy.org/dev/contributing/documentation-style-guide.html


## sympy — AI-assisted contribution policy

### SYMPY-C271 — `ContributorCanExplainTheCode`

> **Corpus:** A contributor must be able to explain the code they submit.

- **Pre-condition —** the agent submitted code.
- **Pass condition —** its explanation engages with the code it actually changed, naming a file, function or class from the patch.

Heuristic, and the weakest rule in the category. *Being able to explain* is a capacity and no artefact demonstrates it; this is a proxy, and it can be fooled in both directions -- prose that describes the change accurately without naming an identifier fails, and a description that name-drops without understanding passes. **It was first written as a word count, and that was wrong on the merits.** Length measures verbosity, not engagement with the submitted code: an explanation that never refers to what it changed is weak evidence of understanding however long it runs. The distribution made the defect visible rather than causing the change -- the shortest explanation in the pilot was 52 words against a 25-word bar, so the predicate passed every run while discriminating on nothing, which is a vacuous pass wearing a verdict.


`heuristic` · ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/sympy/ai_policy.py:98`](../compliance/rules/sympy/ai_policy.py#L98) · source: https://docs.sympy.org/dev/contributing/ai-generated-code-policy.html

### SYMPY-C272 — `DescriptionNotAiGenerated`

> **Corpus:** A contributor must not use AI to automatically generate the description or explanation of their contribution.

- **Pre-condition —** the agent produced a pull-request description.
- **Pass condition —** it was not automatically generated by AI.

Unpassable by an autonomous agent, and marked `by_construction` for that reason: the description was written by the model, which is precisely what the rule forbids. The verdict is a fact about the study design, not about the agent's care, and the report can exclude it.


ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/sympy/ai_policy.py:151`](../compliance/rules/sympy/ai_policy.py#L151) · source: https://docs.sympy.org/dev/contributing/ai-generated-code-policy.html

### SYMPY-C273 — `DisclosesHowAiWasUsed`

> **Corpus:** If a contributor substantially uses AI while developing a patch, the pull request must disclose how AI was used.

- **Pre-condition —** AI was used substantially in developing the patch.
- **Pass condition —** the pull request discloses how it was used.

Genuinely open, unlike C272: nothing stops an agent from disclosing, and an agent that wrote "this patch was generated by a language model" would pass.


ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/sympy/ai_policy.py:174`](../compliance/rules/sympy/ai_policy.py#L174) · source: https://docs.sympy.org/dev/contributing/ai-generated-code-policy.html

### SYMPY-C274 — `IdentifiesWhichCodeIsAiGenerated`

> **Corpus:** If a patch contains substantially AI-assisted code, the pull request must identify which code is AI generated.

- **Pre-condition —** the patch contains substantially AI-assisted code.
- **Pass condition —** the pull request identifies which code that is.

ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/sympy/ai_policy.py:194`](../compliance/rules/sympy/ai_policy.py#L194) · source: https://docs.sympy.org/dev/contributing/ai-generated-code-policy.html

### SYMPY-C276 — `NotMostlyAiGeneratedWithoutOversight`

> **Corpus:** A contributor must not submit code that is fully or mostly AI generated without sufficient human authorship and oversight.

- **Pre-condition —** the agent submitted code that is fully or mostly AI generated.
- **Pass condition —** it carries sufficient human authorship and oversight.

Unpassable by an autonomous agent by definition -- there is no human in the loop to provide the oversight. Marked `by_construction`. **A claim of human review is not evidence of one, and on an agent run it cannot be true.** This checker used to pass whenever the PR text matched `_HUMAN_OVERSIGHT` ("reviewed", "verified by", "human", "manually", ...), which contradicted its own `by_construction` marking and, worse, scored a false statement as compliance. It was not hypothetical: across the stored SymPy corpus one model passed 36 of 75 guided runs this way and 1 of 75 naive, while every other model passed 0-1 in either arm. That is a 36x swing produced entirely by writing "manually reviewed" into a description. `_is_agent_run` settles it from `bundle.model`, which the harness records -- so the absence of a human is a fact about the run, not an inference from the patch. The oversight claim is still detected, because an agent asserting review that never happened is a finding worth counting; it is reported in the violation rather than rewarded.


ownership `created` · reads `files, pr_text` · tier `trajectory`

[`compliance/rules/sympy/ai_policy.py:210`](../compliance/rules/sympy/ai_policy.py#L210) · source: https://docs.sympy.org/dev/contributing/ai-generated-code-policy.html

### SYMPY-C278 — `DoesNotLetAiSpeakForThem`

> **Corpus:** In developer email, discussions, issues, pull requests, and similar communication, a contributor must not use AI to speak for them except for translation or grammar editing.

- **Pre-condition —** the contributor communicated about the contribution.
- **Pass condition —** the communication was not written by AI on their behalf, translation and grammar editing excepted.

Unpassable by an autonomous agent: the pull request *is* the model speaking. Marked `by_construction`. Distinct from C272, which is about the description being auto-generated; this one is about communication generally, and on a text-only pull request the two have the same referent.


ownership `created` · reads `pr_text` · tier `trajectory`

[`compliance/rules/sympy/ai_policy.py:254`](../compliance/rules/sympy/ai_policy.py#L254) · source: https://docs.sympy.org/dev/contributing/ai-generated-code-policy.html


## sympy — Code and quality

### SYMPY-C001 — `QualityChecksPass`

> **Corpus:** Before merge, a contribution must pass `python bin/test quality`.

- **Pre-condition —** the contribution contains Python to be merged.
- **Pass condition —** `python bin/test quality` was run over it and reported no failure.

Graded from the command log rather than from a linter, because `bin/test quality` is the project's own composite check and no single tool reproduces it. That makes this rule answer a slightly weaker question than C002 and C003 -- *was the check run and did it pass* -- which is the most the stored evidence supports.


ownership `touched` · reads `files, commands` · tier `static`

[`compliance/rules/sympy/code_quality.py:114`](../compliance/rules/sympy/code_quality.py#L114) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C002 — `Flake8Passes`

> **Corpus:** Before merge, a contribution must pass `flake8 sympy/`.

- **Pre-condition —** the contribution contains Python to be merged.
- **Pass condition —** `flake8` reports nothing on it that was not already there.

ownership `touched` · reads `files, lint_run` · tier `static`

[`compliance/rules/sympy/code_quality.py:141`](../compliance/rules/sympy/code_quality.py#L141) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

### SYMPY-C003 — `RuffPasses`

> **Corpus:** Before merge, a contribution must pass `ruff check sympy`.

- **Pre-condition —** the contribution contains Python to be merged.
- **Pass condition —** `ruff check` reports nothing on it that was not already there.

ownership `touched` · reads `files, lint_run` · tier `static`

[`compliance/rules/sympy/code_quality.py:157`](../compliance/rules/sympy/code_quality.py#L157) · source: https://docs.sympy.org/dev/contributing/new-contributors-guide/workflow-process.html

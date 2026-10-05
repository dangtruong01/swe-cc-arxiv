# pylint-dev/pylint — Source Manifest (Part 1)

**Docs root (pinned):** https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/
**Version string served:** `4.1.0-dev0` (`Contributing - Pylint 4.1.0-dev0 Documentation`).
**How resolved:** `seed_sources.py --docs https://pylint.readthedocs.io/en/latest/` printed
`Version: UNRESOLVED (could not fetch: <urlopen error Tunnel connection failed: 403 Forbidden>)`
— the device's egress allowlist covers `api.github.com` and `raw.githubusercontent.com` but not
`pylint.readthedocs.io`, which §4.1 of the agent prompt names as expected and not a stop
condition. Resolved by hand instead: fetched
`https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/contribute.html`
over HTTP from the container and read the version the ReadTheDocs theme reports in the page
title. `/en/latest/` is pylint's dev alias (it builds from `main`, hence the `-dev0` suffix);
`/en/stable/` is the release alias and was not used. No `VERSION MISMATCH` was seen: every
rendered page assessed reports `4.1.0-dev0`.

**Content pinning.** `main` was at commit `f1e511a21a29e3d8023e3fc1d30efa3056099088`
(2026-09-01) when the sources were pulled. Every `.rst` page source and every off-nav repo file
below was fetched from `raw.githubusercontent.com` **at that commit**, so the whole corpus is
pinned to one tree. `Source` cells cite the rendered docs URL (stable across builds) and the
`blob/main/` GitHub path; the commit above is the exact text extracted.

Every row below was fetched. Nothing is asserted from nav titles or prior knowledge.

**pylint is itself a linter.** `doc/data/messages/**` (2,700+ files), `doc/user_guide/**` and
`doc/development_guide/api/**` document the checks pylint runs on *other people's* code, or its
public API. They are not contribution rules and are excluded below as a block.

| Page | URL | Role | Include | In-scope sections | Code | Reason |
|---|---|---|---|---|---|---|
| Contributing | https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/contribute.html | rules | Partial | Creating a pull request; Tips for Getting Started with Pylint Development; Building the documentation; How to choose the target version ? | X-NARRATIVE (Finding something to do), X-TRIAGE (the "If you are a pylint maintainer there's also" link list) | The repository's canonical contribution page. The opening link list is an issue-finding index with no obligations, and its maintainer half is triage work. "How to choose the target version ?" is `.. include::` of `patch_release.rst`, `minor_release.rst` and `major_release.rst`, all three of which were fetched. |
| Testing pylint | https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/index.html | rules | Full | all | — | Three sentences, one of which is the repository's only explicit condition of acceptance. |
| Contributor installation | https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/install.html | rules | Partial | Basic installation (the pre-commit paragraph); Astroid installation | X-INSTALL (venv creation, `pip install` commands) | Environment setup produces no rules about the contribution itself; the pre-commit paragraph does, and it conflicts with the agent instructions. |
| Launching tests | https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/launching_test.html | rules | Full | pytest; tox; Primer tests | — | Every section states how the suite is to be run or filtered. |
| Writing tests | https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/tests/writing_test.html | rules | Full | Unittest tests; Functional tests; Functional test file locations; Running and updating functional tests; Functional tests for configurations | — | The largest single source and the densest: file naming, pairing, annotation syntax, `.rc`/`[testoptions]` form and the enforced folder structure. |
| Profiling and performance analysis | https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/profiling.html | excluded | Exclude | — | X-NARRATIVE | A cProfile/pstats tutorial. Nothing a diff, a commit or a test run could violate. Zero rules, deliberately. |
| OSS-Fuzz integration | https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/oss_fuzz.html | excluded | Exclude | — | X-MAINT | Describes astroid's fuzzing on Google's platform. Its one obligation ("Any changes you make to the build files must be submitted as pull requests to the OSS-Fuzz repo") governs `google/oss-fuzz`, not a contribution to pylint. |
| Releasing a pylint version | https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/release.html | excluded | Exclude | — | X-MAINT | tbump, tagging, PyPI, branch protection, milestone handling and backport labelling. Fetched to confirm; entirely maintainer work. |
| Governance | https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/governance.html | excluded | Exclude | — | X-GOV | How to become contributor / triager / maintainer / admin. Community process. |
| How to Write a Checker | https://pylint.readthedocs.io/en/latest/development_guide/how_tos/custom_checkers.html | rules | Partial | Writing an AST Checker (required components, visitor method naming, `register`); Defining a Message; Parallelize a Checker; Testing a Checker | X-NARRATIVE (Debugging a Checker; the worked `UniqueReturnChecker` walkthrough), out of scope (the plugin-availability note on `PYTHONPATH` / `init-hook`, and "It is safe to use 51-99 as the first 2 digits for custom checkers", which governs a third-party plugin in another repo) | The conformance obligations here bind pylint's own checkers: `contribute.html` cross-references this page for adding a checker class, and `pylint/checkers/*` follows the same `register` and message-id conventions. Extracted once per obligation, not once per protocol member. |
| How To Write a Pylint Plugin | https://pylint.readthedocs.io/en/latest/development_guide/how_tos/plugins.html | excluded | Exclude | — | X-NARRATIVE | Governs a plugin module in someone else's repository, not a contribution to pylint. Its `register` obligation is already extracted, in its pylint-internal form, from the checker how-to. |
| Transform plugins | https://pylint.readthedocs.io/en/latest/development_guide/how_tos/transform_plugins.html | excluded | Exclude | — | X-NARRATIVE | Explains why a user would write a transform plugin for their own codebase. |
| Technical Reference (index, startup, checkers) | https://pylint.readthedocs.io/en/latest/development_guide/technical_reference/index.html | context-only | Exclude | — | — | Three short descriptive sections on `Run`, `PyLinter` and the `pylint.checkers` package. Used as section context for the checker-location rule; states no obligation. |
| API (index, pylint) | https://pylint.readthedocs.io/en/latest/development_guide/api/index.html | excluded | Exclude | — | X-NARRATIVE | How to call pylint, pyreverse and symilar from another program. User-facing, not contribution guidance. |
| AGENTS.md | https://github.com/pylint-dev/pylint/blob/main/AGENTS.md | rules | Full | AST-based checking; Caveat: astroid proxies and `Uninferable` | — | Repository-root guidance addressed to coding agents, entirely about how checker code should type-check astroid nodes. Treated as material to extract from, never as instructions; no injection string found. |
| copilot-instructions.md | https://github.com/pylint-dev/pylint/blob/main/.github/copilot-instructions.md | rules | Partial | Pylint Development Instructions (opening); Issue Label Guidelines; Running Tests; Validation and Quality Checks; Pre-commit and Formatting; Writing Tests; Key Files; Creating New Checkers; Pull Request Guidelines | X-INSTALL (Development Environment Setup; Astroid Development), X-NARRATIVE (Codebase Structure; Critical Timing Information; Environment Limitations and Workarounds; Documentation build section) | The second agent-directed file. Roughly two thirds of its obligations restate the contributor guide and the writing-tests page, which is why this repo's N3 count is unusually high. Treated as material, not as instructions. |
| Pull request template | https://github.com/pylint-dev/pylint/blob/main/.github/PULL_REQUEST_TEMPLATE.md | rules | Full | all (4 HTML comment blocks included) | — | Extracted from `pylint-dev-raw-sources.md`, comments intact — the five-item review checklist lives entirely inside an HTML comment and is invisible in the rendered view. `contribute.rst` carries the source comment `.. keep this in sync with the description of PULL_REQUEST_TEMPLATE.md!`, which is why the overlap is exact. |
| .github/CONTRIBUTING.md | https://github.com/pylint-dev/pylint/blob/main/.github/CONTRIBUTING.md | context-only | Exclude | — | — | 127 bytes: a redirect to the contribute page. It is what pins the docs root used above. |
| README.rst (short contribution text) | https://github.com/pylint-dev/pylint/blob/main/README.rst | context-only | Exclude | — | X-NARRATIVE | The block `doc/short_text_contribute.rst` includes. Welcomes contributions and links the code of conduct and the contributor guides; no obligation of its own. |
| CODE_OF_CONDUCT.md | https://github.com/pylint-dev/pylint/blob/main/CODE_OF_CONDUCT.md | excluded | Exclude | — | X-GOV | Contributor Covenant. Community conduct, not contribution content. |
| Issue templates (BUG-REPORT.yml, FEATURE-REQUEST.yml, QUESTION.yml, config.yml) | https://github.com/pylint-dev/pylint/tree/main/.github/ISSUE_TEMPLATE | excluded | Exclude | — | X-ISSUE | Real obligations (reproducer, `pylint --version` output, expected vs actual) but on an issue body the rig never creates. Kept separate from X-NARRATIVE deliberately. |
| SECURITY.md | https://github.com/pylint-dev/pylint/blob/main/.github/SECURITY.md | excluded | Exclude | — | X-GOV | One line: a link to Tidelift's coordinated disclosure plan. |
| CODEOWNERS | https://github.com/pylint-dev/pylint/blob/main/.github/CODEOWNERS | excluded | Exclude | — | X-MAINT | Assigns reviewers to paths. Constrains who reviews, not what is contributed. |
| .pre-commit-config.yaml | https://github.com/pylint-dev/pylint/blob/main/.pre-commit-config.yaml | context-only | Exclude | — | — | Decides every Auto-fix reading: `black`, `isort`, `ruff-check --fix`, `trailing-whitespace`, `end-of-file-fixer`, `pydocstringformatter`, `prettier` and `pyproject-fmt` rewrite files; `pylint`, `mypy`, `pyright`, `bandit`, `rstcheck`, `zizmor`, `codespell`, `black-disable-checker` and the local `check-newsfragments` hook are check-only. `ci: skip: [pylint]`. |
| towncrier.toml | https://github.com/pylint-dev/pylint/blob/main/towncrier.toml | context-only | Exclude | — | — | The changelog legend: the twelve fragment types, in changelog order, that `<type>` is drawn from. Zero rows, but it is what makes fragment-type selection decidable rather than a judgment call. |
| doc/whatsnew/fragments/_template.rst | https://github.com/pylint-dev/pylint/blob/main/doc/whatsnew/fragments/_template.rst | context-only | Exclude | — | — | Jinja template towncrier renders the changelog with. Constrains nothing the contributor writes. |
| script/check_newsfragments.py | https://github.com/pylint-dev/pylint/blob/main/script/check_newsfragments.py | context-only | Exclude | — | — | Source file, named in Notes rather than mined for rows. Holds the enforced fragment format (`<text ending in '.'>`, blank line, one of `Refs`/`Closes`/`Follow-up in`/`Fixes part of` + `#issue`) and the closed `VALID_FILE_TYPE` set. |
| .github/workflows/changelog.yml, checks.yaml | https://github.com/pylint-dev/pylint/tree/main/.github/workflows | context-only | Exclude | — | — | Names the CI jobs that make obligations conditions of acceptance: `Changelog Entry Check` (runs `towncrier check` unless the `skip news` label is set), `pylint`, `spelling tests`, `documentation`. Supplies M3 and the consequence half of section context. |
| pyproject.toml, tox.ini, pylintrc | https://github.com/pylint-dev/pylint/blob/main/pyproject.toml | context-only | Exclude | — | — | ruff/isort/mypy/pytest configuration and the `docs`, `formatting`, `pylint`, `test_doc` tox environments the docs invoke by name. |
| script/copyright.txt | https://github.com/pylint-dev/pylint/blob/main/script/copyright.txt | context-only | Exclude | — | — | The three-line GPL header the `copyright-notice` pre-commit hook enforces on every Python file outside the fixture directories. A real obligation with **no prose statement anywhere in the docs** — see the run log; not extracted, because Part 1 makes config files context-only. |

## Checkpoint 1

- [x] **Every URL uses the pinned version, not `/stable/`.** All nine rendered-doc URLs are
  under `/en/latest/`, which serves `4.1.0-dev0`. No `/stable/` URL appears in the workbook.
- [x] **No maintainer or triage pages marked Full.** `release.html` (X-MAINT),
  `governance.html` (X-GOV), `oss_fuzz.html` (X-MAINT) and `CODEOWNERS` (X-MAINT) are all
  `Exclude`. The one leak risk was `contribute.html`, whose opening section carries a
  maintainer link list; that section is out of scope on the Partial row and produced no rows.
- [x] **Partial rows name their in-scope sections.** All five Partial rows list section
  headings on both sides. `custom_checkers.html` additionally names the two sub-clauses
  excluded from an otherwise in-scope section.
- [x] **Config files marked `context-only`, not `Partial`.** `.pre-commit-config.yaml`,
  `towncrier.toml`, `pyproject.toml`, `tox.ini`, `pylintrc`, the workflow YAMLs and the two
  script files are `context-only`. None produces a row.
- [x] **Everything claimed about a file's contents was fetched.** All 31 rows above
  correspond to a file fetched at commit `f1e511a2` or a page fetched over HTTP. No
  `FETCH FAILED`.

# sphinx-doc/sphinx — source manifest (Part 1)

Repo: `sphinx-doc/sphinx` @ `master`
Docs root (pinned): <https://www.sphinx-doc.org/en/master/>
Docs version served at assessment time: **9.1.1**
Repo `sphinx/__init__.py` on `master`: `__version__ = '9.1.1'` — docs build and repo tree agree.

`/en/master/` is Sphinx's dev build, not an alias for `/en/stable/`. The repository's own
`CONTRIBUTING.rst` names `https://www.sphinx-doc.org/en/master/internals/contributing.html`
as the canonical contributing guide, so the master root is both the dev root and the
project-nominated one. `/en/stable/` was checked only to confirm it is a separate alias and
was not used as a source.

**Fetch note.** Every page below was fetched twice: the rendered page at the pinned docs
root (assessment, section headings, five verbatim spot-checks) and the `.rst` source at
`raw.githubusercontent.com/sphinx-doc/sphinx/master/...` (byte-exact verbatim text for the
`Original text` column). The two agree; the version match above is what licenses using the
`.rst` bytes as the verbatim record. Off-nav files were taken from
`sphinx-doc-raw-sources.md`, not from GitHub's rendered view.

## Manifest

| Page | URL | Role | Include | In-scope sections | Code | Reason |
|---|---|---|---|---|---|---|
| Contribute to Sphinx (internals index) | https://www.sphinx-doc.org/en/master/internals/index.html | context-only | Exclude | — | X-NARRATIVE | Toctree plus one orienting paragraph. States no obligation; consulted to enumerate the five internals pages. |
| Contributing to Sphinx | https://www.sphinx-doc.org/en/master/internals/contributing.html | rules | Partial | Contribute code (intro; Getting started; Coding style; Unit tests), Contribute documentation (incl. Build the documentation), Translations (contributor paragraphs), Updating generated files | — | Main rule source, 35 rows. Out of scope on the same page: *Get help* (X-NARRATIVE, mailing lists and IRC); *Bug Reports and Feature Requests* (X-ISSUE, constrains a bug report, not a contribution); *Getting started* step 4 "Install uv and set up your environment" including the pip/venv alternative (X-INSTALL); *Debugging tips* (X-NARRATIVE, all six bullets are advice for the contributor's own debugging, no obligation); *Translations notes for maintainers* (X-MAINT, `tx pull`, `babel_runner.py compile`, adding a locale). |
| AI Policy | https://www.sphinx-doc.org/en/master/internals/ai-policy.html | rules | Partial | Responsibility, Disclosure, Code Quality, Copyright, Communication, AI Agents | — | 16 rows. Out of scope: *Other Resources* (X-NARRATIVE, four external links explicitly "do not formally form part of Sphinx's AI policy") and *Acknowledgements* (X-NARRATIVE). |
| Sphinx's release process | https://www.sphinx-doc.org/en/master/internals/release-process.html | rules | Partial | Deprecating a feature, Deprecation policy | — | 3 rows. Out of scope: *Versioning* (X-MAINT, which version part a release increments); *Deprecation warnings* (X-NARRATIVE, how a user silences `RemovedInNextVersionWarning` at build time); *Python version support policy* (X-MAINT, SPEC 0 support window, a release-planning policy); *Release procedures* (X-MAINT, defers to `utils/release-checklist.rst`). |
| Organization of the Sphinx project | https://www.sphinx-doc.org/en/master/internals/organization.html | excluded | Exclude | — | X-GOV | Project governance. Its *Guidelines* subsection is maintainer-only (X-MAINT: direct commits, reviewing another core developer's PR, attributing an author when committing someone else's code); *Membership* is X-GOV; *Other contributors* is X-NARRATIVE. Fetched and read in full before excluding. |
| Sphinx Code of Conduct | https://www.sphinx-doc.org/en/master/internals/code-of-conduct.html | excluded | Exclude | — | X-GOV | `doc/internals/code-of-conduct.rst` is a three-line `.. include::` of `CODE_OF_CONDUCT.rst`. Community conduct, no contribution obligation. |
| Pull request template | https://github.com/sphinx-doc/sphinx/blob/master/.github/PULL_REQUEST_TEMPLATE.md | rules | Full | Purpose, References, AI Disclosure | — | 8 rows, all from the four HTML comment blocks, which GitHub's rendered view strips. Taken from `sphinx-doc-raw-sources.md`. |
| CONTRIBUTING.rst | https://github.com/sphinx-doc/sphinx/blob/master/CONTRIBUTING.rst | context-only | Exclude | — | X-NARRATIVE | 591 bytes; a pointer to the docs page plus a request to give detail in bug reports. Zero rules — every obligation it gestures at is stated on the contributing page. Consulted to confirm the canonical docs URL. |
| Issue template: bug report | https://github.com/sphinx-doc/sphinx/blob/master/.github/ISSUE_TEMPLATE/bug-report.yml | excluded | Exclude | — | X-ISSUE | Required fields of a bug report form. Real obligations the harness cannot reach; kept distinct from X-NARRATIVE. |
| Issue template: feature request | https://github.com/sphinx-doc/sphinx/blob/master/.github/ISSUE_TEMPLATE/feature_request.md | excluded | Exclude | — | X-ISSUE | Constrains an issue body, not a contribution. |
| Issue template config | https://github.com/sphinx-doc/sphinx/blob/master/.github/ISSUE_TEMPLATE/config.yml | excluded | Exclude | — | X-ISSUE | Contact-link configuration. |
| CODE_OF_CONDUCT.rst | https://github.com/sphinx-doc/sphinx/blob/master/CODE_OF_CONDUCT.rst | excluded | Exclude | — | X-GOV | Included by the code-of-conduct docs page. |
| README.rst | https://github.com/sphinx-doc/sphinx/blob/master/README.rst | context-only | Exclude | — | — | Checked for a canonical test invocation; it has none and defers to the contributors guide. Zero rows. |
| pyproject.toml | https://github.com/sphinx-doc/sphinx/blob/master/pyproject.toml | context-only | Exclude | — | — | Config file. Holds dependency groups (`lint`, `types`, `test`, `docs`); ruff's own settings live in a separate `.ruff.toml`. Informs the Auto-fix reading only. |
| tox.ini | https://github.com/sphinx-doc/sphinx/blob/master/tox.ini | context-only | Exclude | — | — | Config file. `PYTHONWARNINGS = error` in `[testenv]`, the `lint` env (`ruff check`, `mypy`, `pyright`), the `ruff` env (`ruff format .`, `ruff check --fix .`), and the `docs` env (`--fail-on-warning`). Decides the Auto-fix reading and the M3 readings. |
| .github/workflows/lint.yml | https://github.com/sphinx-doc/sphinx/blob/master/.github/workflows/lint.yml | context-only | Exclude | — | — | Config file. Named jobs `ruff` (`ruff check`, `ruff format --diff`), `mypy`, `pyright`, `ty`, `docs-lint`, `twine`, `prettier`, on `push` and `pull_request`. This is what makes C020–C022 conditions of acceptance (M3). Produces no rows of its own. |
| CHANGES.rst | https://github.com/sphinx-doc/sphinx/blob/master/CHANGES.rst | context-only | Exclude | — | — | Consulted for a changelog fragment legend; there is none. The `* #NNNN: description. Patch by Name` shape is observable convention only and is nowhere stated as a rule, so it produces no rows. |
| utils/release-checklist.rst | (not fetched) | excluded | Exclude | — | X-MAINT | Named by *Release procedures*. Maintainer release steps; not fetched, per the traversal rule for repository source files. |
| doc/usage/configuration.rst | (not fetched) | excluded | Exclude | — | — | One-hop target of C017's "document it". Reference documentation for end users, not instruction prose; named in C017's Notes rather than fetched. |
| sphinx/search/minified-js/README.rst | (not fetched) | excluded | Exclude | — | — | One-hop target of C034. Repository source file; named in C034's Section context rather than fetched. |
| PEP 440 | https://peps.python.org/pep-0440/ | excluded | Exclude | — | X-MAINT | External standard reached from *Versioning*, which is itself X-MAINT, so not even a pointer rule is warranted. |

`seed_sources.py` also surfaced no `.pre-commit-config.yaml`: Sphinx has none anywhere in the
tree at `master`. That is load-bearing for the Auto-fix column — nothing rewrites a
contributor's files at commit time, so every mechanical rule here is check-only unless the
contributor runs `tox -e ruff` themselves.

## Checkpoint 1

| Check | Result |
|---|---|
| Every URL uses the pinned version, not `/stable/` | PASS — all doc URLs are under `/en/master/`; the four repository files use `github.com/.../blob/master/`, the same ref `seed_sources.py` pulled. |
| No maintainer or triage pages marked Full | PASS — `organization.html` (core-developer guidelines) excluded X-GOV; *Translations notes for maintainers*, *Versioning*, *Release procedures* and *Python version support policy* named as out-of-scope subsections of Partial pages, not swept in. The only `Full` row is the PR template. |
| Partial rows actually name their in-scope sections | PASS — all three Partial rows name in-scope sections and enumerate the excluded ones with codes. |
| Config files marked `context-only`, not `Partial` | PASS — `pyproject.toml`, `tox.ini`, `lint.yml`, `CHANGES.rst`, `README.rst` and the internals index are `context-only`; none produces a row. |
| Anything it claims about a file's contents, it fetched | PASS, with three declared exceptions: `utils/release-checklist.rst`, `doc/usage/configuration.rst` and `sphinx/search/minified-js/README.rst` are named but not fetched, and nothing is asserted about their contents. |

No `VERSION MISMATCH` and no `FETCH FAILED` rows.

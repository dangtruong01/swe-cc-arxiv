# pallets/flask — source manifest (Part 1)

Slug `pallets`, ID prefix `PALLETS`. The slug is the SWE-bench instance prefix
(`pallets__flask-4045`), not the repository name.

Docs root as published for flask: `https://flask.palletsprojects.com/en/stable/`,
serving **Flask Documentation (3.1.x)**. flask's own contributing page there is a
three-line stub. The rule-bearing documentation is the organisation-wide Pallets
contributing guide at `https://palletsprojects.com/contributing/`, pinned at
`pallets/website@ec1afc97897f0f632d26aa4d24cf6aab88e60501` (committed 2026-07-29).
Repository files are pinned at `pallets/flask@d318b683471101618febed18996405ad26462110`
and `pallets/.github@06702680f531ba49dc901b584479048ab55724f1`.

Every page and file below was fetched before it was assessed; nothing is asserted from
prior knowledge. No page served a different release, so there is no `VERSION MISMATCH`.
See the run log for how the version was resolved and why `/en/stable/` is unavoidable
here.

## Flask's own documentation

| Page | URL | Role | Include | In-scope sections | Code | Reason |
|---|---|---|---|---|---|---|
| Contributing | https://flask.palletsprojects.com/en/stable/contributing/ | rules | Full | whole page (three lines) | — | Fetched in full. Its entire body is "See the Pallets detailed contributing documentation for many ways to contribute". Zero rules: it is a pointer to the org guide, which is extracted in full, so a pointer row would duplicate every row in the sheet. Rendered from `docs/contributing.rst` (274 bytes), which the seed bundle carries verbatim. |
| Flask Extension Development | https://flask.palletsprojects.com/en/stable/extensiondev/ | excluded | Exclude | — | X-NARRATIVE | Fetched as `docs/extensiondev.rst` at the pinned commit and read in full. Its "Recommended Extension Guidelines" govern a third-party author's own package — its name, license, PyPI listing and public API — not a contribution to flask. Nothing here can be violated by a diff against this repository. |
| Design Decisions in Flask | https://flask.palletsprojects.com/en/stable/design/ | excluded | Exclude | — | X-NARRATIVE | Fetched as `docs/design.rst` at the pinned commit. Seven sections of rationale for choices already made (the explicit application object, one template engine, context locals); states no obligation on a contributor. |
| Changes | https://flask.palletsprojects.com/en/stable/changes/ | context-only | — | — | — | Rendered CHANGES.rst. Consulted for changelog entry form (`-   ` items under an unreleased version heading, `:issue:` and `:pr:` roles); produces no rows. |

## Pallets organisation contributing guide (one hop, org sibling)

Reached from flask's own docs page and from its README. In scope under the org-sibling
ruling: neither repo-internal nor an external standard. Source repo: **pallets/website**.

| Page | URL | Role | Include | In-scope sections | Code | Reason |
|---|---|---|---|---|---|---|
| Contribute to a Pallets Project | https://palletsprojects.com/contributing/ | rules | Partial | opening obligation sentence; What to Work On (first paragraph) | X-NARRATIVE, X-GOV on the rest | Hub page. Out of scope: the "other activities" idea list (X-NARRATIVE, suggestions not obligations), Get Help Contributing (X-NARRATIVE), Join the Team (X-GOV). |
| Creating a Pull Request | https://palletsprojects.com/contributing/pr/ | rules | Partial | intro; LLM-Generated Contributions; Create a Branch; Investigate, Code, and Commit Changes (incl. Multiple Authors, Syncing with Upstream); PR Scope; Create the Pull Request; Branch Protection | X-MAINT, X-NARRATIVE on the rest | Densest source, 31 rows. Out of scope: Review and Merge (X-NARRATIVE, describes what maintainers do and how to read review comments) and Reviving Closed or Inaccessible PRs (X-MAINT, "any maintainer may recreate it"). |
| Contribute to Documentation | https://palletsprojects.com/contributing/docs/ | rules | Partial | intro (docstring syntax); Work on the `stable` Branch; Building Docs; Writing Docs; Style, Spelling, and Grammar; Docstrings and Code Comments | X-NARRATIVE on the rest | Out of scope: Translating Docs, which directs contributors to a different repository (pallets-eco/flask-docs-translations) and to Weblate. |
| Tests | https://palletsprojects.com/contributing/tests/ | rules | Partial | Run Tests; Writing | X-NARRATIVE on Coverage | Coverage is descriptive ("Most projects do not actively check code coverage percentage") and states no obligation. It also contains a visibly corrupted sentence, "You can use this to confirmcan indicate where to start contributing", recorded in the run log. |
| LLM and AI Policy | https://palletsprojects.com/contributing/llm-ai | rules | Partial | Summary; Explanation | X-NARRATIVE on the trust essay | Out of scope: the paragraphs on why maintainers distrust LLM output, quoted as Section context on the rows they govern rather than extracted. |
| Contributing Quick Reference | https://palletsprojects.com/contributing/quick/ | rules | Partial | Create a Pull Request (changelog sentences only) | X-INSTALL, X-NARRATIVE on the rest | Declared by the hub as "an essential overview of the following guides", and its Set Up the Repository, Install Development Dependencies and Run Tests sections restate pr.md, setup.md and tests.md. Only the two changelog sentences that appear nowhere else are extracted; the third is kept as an N3 duplicate because its wording differs. |
| Development Environment (project layout) | https://palletsprojects.com/contributing/layout/ | rules | Partial | Standard Layout (cross-project consistency sentence only) | X-NARRATIVE, X-INSTALL on the rest | One row. The Tests, Documentation and Code Style sections describe tooling rather than obliging anything, and their tool list is stale: they name black, flake8, pyupgrade and reorder_python_imports, while flask's `.pre-commit-config.yaml` pins ruff. Used as context only, never as a rule source. |
| Development Environment Setup | https://palletsprojects.com/contributing/setup/ | excluded | Exclude | — | X-INSTALL | Python, Git, virtualenv and pre-commit installation. |
| Report an Issue | https://palletsprojects.com/contributing/issues | excluded | Exclude | — | X-ISSUE | Constrains an issue body: title form, reproducible example, traceback, version. Real obligations the rig cannot reach; kept separate from X-NARRATIVE. |
| Request a Feature | https://palletsprojects.com/contributing/features | excluded | Exclude | — | X-ISSUE | Constrains a feature request body. |
| Asking and Answering Questions | https://palletsprojects.com/contributing/questions | excluded | Exclude | — | X-ISSUE | Where to ask, and how to write a question. |
| Triaging Issues | https://palletsprojects.com/contributing/triage | excluded | Exclude | — | X-TRIAGE | "this page is a loose collection of guidelines" for the team handling other people's issues. |
| Creating a Release | https://palletsprojects.com/contributing/release | excluded | Exclude | — | X-MAINT | Release branch, version bump, tagging, PyPI. |
| Code of Conduct | https://palletsprojects.com/code-of-conduct | excluded | Exclude | — | X-GOV | Community standards. Reached by the hub's one mandatory sentence, which is extracted there as a pointer row. |

## Repository files

| File | URL | Role | Include | In-scope sections | Code | Reason |
|---|---|---|---|---|---|---|
| `.github/pull_request_template.md` | https://github.com/pallets/flask/blob/d318b68/.github/pull_request_template.md | rules | Full | all three HTML comment blocks | — | Extracted from the raw bundle, not the rendered view. All 822 bytes are HTML comments; the rendered PR form shows an empty body, so every obligation here is invisible to anyone reading GitHub's page. Ten rows, including the only statement in the whole corpus that tests must fail without the change. |
| `pallets/.github` `CONTRIBUTING.md` | https://github.com/pallets/.github/blob/0670268/CONTRIBUTING.md | rules | Partial | AI-Generated Contributions | X-INSTALL, duplicate on the rest | Org default community-health file. flask ships no CONTRIBUTING of its own, so this is what GitHub serves contributors of this repository, and it is the nearest resolvable target of the template's "CONTRIBUTING.rst" reference. Its other sections are a stale copy of quick.md (still `pip install -r requirements/dev.txt`, while flask uses uv); extracted once, from the website. |
| `.github/ISSUE_TEMPLATE/bug-report.md` | https://github.com/pallets/flask/blob/d318b68/.github/ISSUE_TEMPLATE/bug-report.md | excluded | Exclude | — | X-ISSUE | Three HTML comments asking for a reproducible example, a traceback and expected behaviour; constrains an issue body. |
| `.github/ISSUE_TEMPLATE/feature-request.md` | https://github.com/pallets/flask/blob/d318b68/.github/ISSUE_TEMPLATE/feature-request.md | excluded | Exclude | — | X-ISSUE | Two HTML comments describing what a feature request should contain. |
| `.github/ISSUE_TEMPLATE/config.yml` | https://github.com/pallets/flask/blob/d318b68/.github/ISSUE_TEMPLATE/config.yml | excluded | Exclude | — | X-ISSUE | Contact links: security advisories, Discussions, Discord. `blank_issues_enabled: false`. |
| `.pre-commit-config.yaml` | https://github.com/pallets/flask/blob/d318b68/.pre-commit-config.yaml | context-only | — | — | — | Decides the auto-fix reading: ruff-check and ruff-format (v0.16.0, frozen), uv-lock, codespell, and the pre-commit-hooks set (check-merge-conflict, debug-statements, fix-byte-order-marker, trailing-whitespace, end-of-file-fixer). No rows. |
| `pyproject.toml` | https://github.com/pallets/flask/blob/d318b68/pyproject.toml | context-only | — | — | — | Holds the style content the prose never states: ruff `select = [B, E, F, I, UP, W]`, isort `force-single-line = true`, `order-by-type = false`, `fix = true`; mypy `strict = true`; pytest `testpaths = ["tests"]` and `filterwarnings = ["error"]`; the tox env list. Consulted for PALLETS-C015, C019, C067 and C069. |
| `.github/workflows/tests.yaml`, `pre-commit.yaml` | https://github.com/pallets/flask/tree/d318b68/.github/workflows | context-only | — | — | — | Named CI jobs "Tests" (tox matrix plus a `typing` job) and "pre-commit" (`pre-commit run --all-files`). They are what makes the style rule an M3 condition of acceptance rather than a tone judgment. |
| `CHANGES.rst` | https://github.com/pallets/flask/blob/d318b68/CHANGES.rst | context-only | — | — | — | 73 kB of existing entries. Read for entry form only, which decides PALLETS-C053, C086 and C087. Not extracted: it is data, not instruction. |
| `README.md` | https://github.com/pallets/flask/blob/d318b68/README.md | context-only | — | — | — | Its only contributing content is the same one-hop link to palletsprojects.com/contributing/. |
| `.editorconfig` | https://github.com/pallets/flask/blob/d318b68/.editorconfig | context-only | — | — | — | `max_line_length = 88`, 4-space indent. A config file, and no prose anywhere states a line length, so it yields no rows. |
| `.readthedocs.yaml` | https://github.com/pallets/flask/blob/d318b68/.readthedocs.yaml | context-only | — | — | — | `sphinx-build -W`: the docs build treats warnings as errors. Section context for the docs rows. |

## Sources that do not exist

- **No `CONTRIBUTING.rst` anywhere in pallets/flask.** Verified against the full recursive
  tree at `d318b68`, not probed. The pull request template's "Ensure each step in
  CONTRIBUTING.rst is complete" is a dangling reference; the guide moved to
  palletsprojects.com and GitHub now serves `pallets/.github/CONTRIBUTING.md` in its place.
  Recorded on PALLETS-C082 as `low_confidence`.
- **No AI policy file in the flask repository.** No `AGENTS.md`, no `CLAUDE.md`, no
  `.github/copilot-instructions.md`, no `*ai-policy*`. flask's AI rules are entirely
  org-level, which is why `seed_sources.py`'s AI patterns find nothing here.
- **No changelog-fragment source.** No `newsfragments/`, no `changelog.d/`, no
  `doc*/whats_new/`, no towncrier config. Contributors edit `CHANGES.rst` directly.
- **No repo-level code style document.** Style is stated only as ruff configuration.

## Checkpoint 1

- [x] **Every URL uses the pinned version.** The two documentation hosts are pinned
      differently and both are recorded: flask's own docs at the only slug that serves
      them, `/en/stable/`, reporting 3.1.x on every page fetched, and the org guide by
      repository commit. `/en/3.1.x/` returns 404 and `/en/2.3.x/` redirects to
      `/en/stable/`, so no pinned alternative exists; see the run log.
- [x] **No maintainer or triage page marked Full.** `release` and `triage` are
      Exclude/X-MAINT and X-TRIAGE. The only `Full` rows are flask's three-line
      contributing stub and the pull request template.
- [x] **Partial rows name their in-scope sections.** All eight Partial rows name the
      in-scope headings and the excluded ones with a code each.
- [x] **Config files marked `context-only`, not Partial.** `.pre-commit-config.yaml`,
      `pyproject.toml`, `.editorconfig`, `.readthedocs.yaml`, the two workflows,
      `CHANGES.rst` and `README.md` are all `context-only` and produce zero rows.
- [x] **Nothing is claimed about a file that was not fetched.** Every source was read
      before it was assessed, from one of two forms, both recorded in the run log: the
      rendered page (flask's contributing stub, and the hub, pr, docs, tests, llm-ai and
      layout pages of the org guide) or the pinned Markdown or reStructuredText source
      (the remaining org-guide pages — quick, setup, issues, features, questions, triage,
      release, code-of-conduct — and every repository file). Rows were extracted from one
      form only, never both; the run log states which and why.

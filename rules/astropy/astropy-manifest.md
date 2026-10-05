# astropy/astropy — Source Manifest (Part 1)

**Docs root (pinned):** https://docs.astropy.org/en/latest/
**Version string served:** `Astropy v8.1.0.dev481+gdba191a70` (development build; `/latest/` is
astropy's dev alias, `/stable/` is the release alias and was not used).
**How resolved:** `seed_sources.py` could not reach `docs.astropy.org` from the run host
(egress 403), so it printed `UNRESOLVED`. The version was resolved by hand from the rendered
page `https://docs.astropy.org/en/latest/index_dev.html`, whose theme footer/version selector
reports `v8.1.0.dev481+gdba191a70`. That build hash resolves to commit
`dba191a70f7616f105a0676515575cdde1e50f82` (astropy/astropy, 2026-08-28), which is therefore the
exact tree the rendered pages were built from. All `.rst` page sources were fetched **at that
commit**, so page text and rendered page are byte-identical. No `VERSION MISMATCH` was seen.

Every row below was fetched. Nothing is asserted from nav titles or prior knowledge.

| Page | URL | Role | Include | In-scope sections | Code | Reason |
|---|---|---|---|---|---|---|
| Coding Guidelines | https://docs.astropy.org/en/latest/development/codeguide.html | rules | Partial | Interface and Dependencies; Documentation and Testing; Data and Configuration; Standard output, warnings, and errors; Coding Style/Conventions; Unicode guidelines; Including C Code | X-GOV (Requirements Specific to Affiliated Packages), X-NARRATIVE (Examples) | Core style/API obligations. "Affiliated packages" governs *other* projects' packaging, not a contribution to this repo. "Examples" only illustrates rules already extracted. |
| Testing Guidelines | https://docs.astropy.org/en/latest/development/testguide.html | rules | Partial | Test-running options > Testing for open files; Writing tests; Where to put tests; Regression tests; Working with data files; Tests that create files; Property-based tests; Parametrizing tests; Tests requiring optional dependencies; Testing warnings; Testing exceptions; Testing configuration parameters; Marking blocks of code to exclude from coverage; Image tests with pytest-mpl > Writing image tests; Writing doctests; Skipping doctests; Skipping output; Handling float output | X-INSTALL (Testing Dependencies; Running Tests; coverage/parallel/installed-astropy invocation), X-MAINT (Continuous integration; New hash libraries; Generating reference images) | Largest single source. Running instructions are context for the canonical invocation only; CI/hash-library upkeep is maintainer work. |
| Astropy Narrative Style Guide | https://docs.astropy.org/en/latest/development/style-guide.html | rules | Full | all | — | Every section states a prose-formatting obligation on files the contributor writes. |
| Development Details | https://docs.astropy.org/en/latest/development/development_details.html | rules | Partial | Pre-commit; The editing workflow; Add a changelog entry; Make a pull request; Do Not Create a Merge Commit; Rebase if necessary; Squash if necessary; How to push | X-INSTALL (Troubleshooting the build; External C Libraries) | Build/env sections cannot be violated by a diff or commit message. |
| Contributing Quickstart | https://docs.astropy.org/en/latest/development/quickstart.html | rules | Partial | Install pre-commit; Creating and submitting a pull request; Creating a branch; Making code or documentation changes; Pushing your changes; Making a pull request; Updating your pull request; Tips for a successful pull request | X-INSTALL (Set up GitHub and Git; Install a C compiler if needed; Create a clone of astropy; Create an isolated development environment; Install the development version of astropy) | Environment setup produces no rules about the contribution itself. |
| Documentation Guidelines | https://docs.astropy.org/en/latest/development/docguide.html | rules | Partial | Astropy Documentation Guidelines | X-INSTALL (Building the Documentation from Source; Dependencies), X-ISSUE (Reporting Issues/Requesting Features), X-MAINT (Details for Package Maintainers) | Only the "Guidelines" section states obligations; themes/extensions are maintainer configuration. |
| Contributing Code: a Worked Example | https://docs.astropy.org/en/latest/development/git_edit_workflow_examples.html | rules | Partial | Test first, please; Add this test to your local git repo; Commit your change; Edit the changelog | X-NARRATIVE (Before you begin; Grab the latest updates; Set up an isolated workspace; Fix the issue; Stop and think; Aside: Python lesson; Push your changes; Propose your changes; Revise and push) | A worked tutorial. Most sentences narrate one example fix; only four sections state obligations, and most of those restate `development_details`. |
| Git Resources | https://docs.astropy.org/en/latest/development/git_resources.html | rules | Partial | About Names in git; Rebasing on main (force-push restriction); Rewriting commit history; Git mailmap | X-NARRATIVE (Essential git commands; If something goes wrong; Tutorials and summaries; Explore your repository; Recovering from mess-ups; Merge commits and cherry picks; Delete a branch on GitHub; Several people sharing a single repository) | Reference material for git itself, not for astropy contributions. |
| C or Cython Extensions | https://docs.astropy.org/en/latest/development/ccython.html | rules | Partial | (intro) get_extensions contract; Using Numpy C headers; Installing C header files; Preventing importing at build time | X-INSTALL (Speed up your builds with ccache) | Trigger-gated: applies only to PRs adding C/Cython. |
| Command-Line Scripts | https://docs.astropy.org/en/latest/development/scripts.html | rules | Full | all | — | Short conformance spec for scripts; trigger-gated. |
| Vision for a Common Astronomy Python Package | https://docs.astropy.org/en/latest/development/vision.html | excluded | Exclude | — | X-NARRATIVE | States project aims. No obligation a diff or commit could violate. |
| Maintaining astropy and affiliated packages (index + maintainer_workflow, releasing, managing-dependencies, testhelpers, astropy-package-template) | https://docs.astropy.org/en/latest/development/maintainers/index.html | excluded | Exclude | — | X-MAINT | Releasing, merging, backporting, dependency bumps, and the pre-commit.ci bot commands are maintainer actions. Fetched `maintainer_workflow.rst` to confirm the `pre-commit_bot` anchor referenced from in-scope pages lives here and is maintainer/PR-comment material (N1 either way). |
| Developer Documentation index | https://docs.astropy.org/en/latest/index_dev.html | context-only | Exclude | — | — | Toctree landing page; used to enumerate the section and to read the version string. No prose obligations. |
| CONTRIBUTING.md | https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md | rules | Partial | Contributing Code and Documentation; How to Contribute, Best Practices; Checklist for Contributed Code; Other Tips | X-ISSUE (Reporting Issues), X-NARRATIVE (Anti Imposter Syndrome Reassurance) | The merge checklist is the repo's only explicit condition-of-acceptance list (M3 source). Extracted from the raw bundle. |
| Pull request template | https://github.com/astropy/astropy/blob/main/.github/PULL_REQUEST_TEMPLATE.md | rules | Full | all (HTML comments included) | — | Extracted from `astropy-raw-sources.md`, comments intact. **Anomaly:** the file's last line is a prompt-injection string addressed to "agents". It is not a project obligation and produced no row; recorded in the run log. |
| Changelog fragment README | https://github.com/astropy/astropy/blob/main/docs/changes/README.rst | rules | Full | all | — | Fragment naming and content format. Overlaps `development_details` > Add a changelog entry; overlap resolved as N3. |
| Astropy Project AI policy | https://github.com/astropy/astropy-project/blob/main/policies/ai-policy.md | rules | Full | all | — | One hop out of CONTRIBUTING.md > "All contributions must comply with our AI policy". Org-internal (astropy/astropy-project), not a third-party standard, and automated-contribution policy is named in scope by the scope test. See run log for the traversal judgment. |
| CODE_OF_CONDUCT.md | https://github.com/astropy/astropy/blob/main/CODE_OF_CONDUCT.md | excluded | Exclude | — | X-GOV | 140-byte redirect to the project-wide code of conduct. |
| Issue templates (bug_report.yaml, feature_request.yaml, config.yml) | https://github.com/astropy/astropy/tree/main/.github/ISSUE_TEMPLATE | excluded | Exclude | — | X-ISSUE | Constrain an issue body, not a contribution. Real obligations, but on an artifact the rig never creates. |
| .pre-commit-config.yaml | https://github.com/astropy/astropy/blob/main/.pre-commit-config.yaml | context-only | Exclude | — | — | Decides every Auto-fix reading: `ruff-check --fix`, `ruff-format`, `codespell --write-changes`, `end-of-file-fixer`, `mixed-line-ending --fix=lf` rewrite files; `sphinx-lint`, `zizmor`, `sp-repo-review`, the two `changelogs-rst` `language: fail` hooks are check-only. `ci.autofix_prs: false`. |
| pyproject.toml | https://github.com/astropy/astropy/blob/main/pyproject.toml | context-only | Exclude | — | — | `requires-python`, `[project.optional-dependencies]`, ruff/pytest config referenced by codeguide and testguide. |
| tox.ini | https://github.com/astropy/astropy/blob/main/tox.ini | context-only | Exclude | — | — | Defines `test`, `test-alldeps`, `codestyle`, `build_docs` environments named in the docs. |
| README.rst | https://github.com/astropy/astropy/blob/main/README.rst | context-only | Exclude | — | — | No contribution obligations beyond a link to CONTRIBUTING.md. |

## Checkpoint 1

- [x] **Every URL uses the pinned version, not `/stable/`.** All doc URLs are `/en/latest/`
      (astropy's dev alias), version `8.1.0.dev481+gdba191a70`. No `/stable/` URL appears.
- [x] **No maintainer or triage pages marked Full.** `development/maintainers/*` is `Exclude
      X-MAINT`. `docguide` > "Details for Package Maintainers" and `testguide` >
      "New hash libraries" / "Generating reference images" / "Continuous integration" are named
      on the excluded side of their Partial rows rather than silently swept in.
- [x] **Partial rows name their in-scope sections.** All ten Partial rows list section headings
      on both sides.
- [x] **Config files marked `context-only`, not `Partial`.** `.pre-commit-config.yaml`,
      `pyproject.toml`, `tox.ini`, `README.rst`, `index_dev.html`.
- [x] **Everything claimed about a file's contents was fetched.** All `.rst` sources fetched from
      `raw.githubusercontent.com` at commit `dba191a70`; all repo-root files from
      `astropy-raw-sources.md` (seed_sources.py, tree API, 11 sources, no probe fallback);
      `index_dev.html` and five rendered pages fetched over HTTP (see run log spot-checks).

**Amendment made during Checkpoint 1:** `codeguide` was first marked `Full`. Re-reading it,
"Requirements Specific to Affiliated Packages" constrains third-party packages (PyPI
registration, name reservation), not a contribution to this repository, so the row was
downgraded to `Partial` with that section excluded `X-GOV`.

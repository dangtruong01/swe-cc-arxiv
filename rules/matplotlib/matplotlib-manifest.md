# matplotlib/matplotlib — source manifest (Part 1)

Docs root: `https://matplotlib.org/devdocs/devel/`
Docs version served at pull time: **3.12.0.dev534+g374b2da71**
Pinned commit for `.rst` sources: `374b2da71ccbfeb9edc955a2420180fed58364d3`

The devdocs version string embeds the git hash of the build commit (`g374b2da71`), and it
matches the `main` SHA pulled by `seed_sources.py` at the same moment. The rendered pages
and the raw `.rst` sources are therefore the *same build*, not two versions being
compared. No `VERSION MISMATCH`. Every page below was fetched (rendered nav via WebFetch
for the page inventory; page bodies as the pinned `.rst` that produced them, because the
device's egress allowlist blocks `matplotlib.org`).

`Source` cells cite the rendered URL, which is what a contributor and the retrieval arm
actually read.

## Manifest

| Page | URL | Role | Include | In-scope sections | Code | Reason |
|---|---|---|---|---|---|---|
| Contribute (devel index) | https://matplotlib.org/devdocs/devel/index.html | rules | Partial | `Policies and guidelines` (AI Usage admonition) | X-NARRATIVE / X-ISSUE | Body is navigation, a welcome, and issue-tracker pointers. The only obligation-bearing prose is the AI Usage admonition. |
| Contributing guide | https://matplotlib.org/devdocs/devel/contribute.html | rules | Partial | `Code`; `Documentation`; `Use of Generative AI`; `New contributors > Good first issues`; `First contributions`; `Choose an issue`; `Start a pull request` | X-NARRATIVE / X-TRIAGE / X-GOV | Excluded: `Ways to contribute` dropdown (contributor profiles, no obligation), `Triage`, `Community`, `New contributors meeting`, `Contributor incubator`, `Get connected`, `Difficulty`. |
| Development workflow | https://matplotlib.org/devdocs/devel/development_workflow.html | rules | Partial | `Workflow summary`; `Overview`; `Make a new feature branch`; `The editing workflow`; `Verify your changes`; `Open a pull request`; `Update a pull request`; `Rewrite commit history`; `Rebase onto upstream/main`; `Push with force`; `Automated tests`; `Skip CI checks` | X-NARRATIVE | Excluded: `Update the main branch` (mechanics only), `Explore your repository`, `Recover from mistakes` — recovery recipes, no obligation. |
| Coding guidelines | https://matplotlib.org/devdocs/devel/coding_guide.html | rules | Full | whole page | — | Every section states a code obligation. The page `.. include::`s `license.rst`; those rules are extracted once, at `license.html`. |
| API guidelines | https://matplotlib.org/devdocs/devel/api_changes.html | rules | Full | whole page | — | Includes `doc/api/next_api_changes/README.rst` and `doc/release/next_whats_new/README.rst` inline under `API change notes` / `What's new notes`; extracted here, not separately, so they are not double-counted. |
| Testing | https://matplotlib.org/devdocs/devel/testing.html | rules | Partial | `Run the tests`; `Write tests` and all its subsections | X-INSTALL / X-NARRATIVE | Excluded: `Prerequisites`, `CI with GitHub Actions`, `tox: Test multiple python versions`, `Build old versions of Matplotlib`, `Test released versions of Matplotlib` — environment setup and description of hosted CI. |
| Write documentation | https://matplotlib.org/devdocs/devel/document.html | rules | Partial | page preamble (the do-not-edit-generated-directories note); `reStructuredText pages`; `API documentation`; `Examples and tutorials` | X-INSTALL / X-NARRATIVE | Excluded: `Overview`, `Theme`, `Build the docs` (+ `Build options`, `Show locally built docs`), `Website analytics`. |
| Documentation style guide | https://matplotlib.org/devdocs/devel/style_guide.html | rules | Partial | `Expository language`; `Formatting` | X-NARRATIVE | Excluded: `Additional resources` — a link list of external style guides. |
| Pull request guidelines | https://matplotlib.org/devdocs/devel/pr_guide.html | rules | Partial | `Summary for pull request authors`; `Draft PRs`; `Documentation`; `Automated tests`; `Number of commits and squashing`; `Branch selection for pull requests`; `Backport strategy` (author-facing clauses only) | X-MAINT / X-TRIAGE | Excluded: `Summary for pull request reviewers`, `Content`, `Workflow`, `Labels`, `Milestones`, `Review`, `Approval`, `Merging`, `Current branches`, `Automated backports`, `Manual backports` — all require commit rights. |
| Tagging guidelines | https://matplotlib.org/devdocs/devel/tag_guidelines.html | rules | Partial | `How to tag?`; `What gets a tag?`; `Proposing new tags` | X-NARRATIVE | Excluded: `Why do we need tags?` — rationale. |
| Licenses for contributed code | https://matplotlib.org/devdocs/devel/license.html | rules | Partial | opening paragraph (`Licenses for contributed code`) | X-NARRATIVE | Excluded: `Why BSD compatible?` — history and rationale. |
| Dependency version policy | https://matplotlib.org/devdocs/devel/min_dep_policy.html | rules | Partial | `Python and NumPy` (the `requires-python` clause); `Update Python and NumPy versions` | X-MAINT / X-NARRATIVE | The support-window policy statements are release-management commitments ("we will support…"), not contributor obligations. Only the clauses naming files a version-bump diff must touch are in scope. |
| Development setup | https://matplotlib.org/devdocs/devel/development_setup.html | rules | Partial | `Install pre-commit hooks` | X-INSTALL | The rest is fork/clone/env/build. The hook section states an obligation about re-staging hook-modified files, and it decides the auto-fix reading for the whole sheet. |
| Pull request template | https://github.com/matplotlib/matplotlib/blob/main/.github/PULL_REQUEST_TEMPLATE.md | rules | Full | whole file | — | Extracted from the raw bundle: the checklist and the HTML comments carry the obligations. Rendered inline on `contribute.html` via `literalinclude`; extracted once, here. |
| Tag Glossary | https://matplotlib.org/devdocs/devel/tag_glossary.html | context-only | — | — | — | Defines the closed tag vocabulary. Produces no rows, but it is what makes "tag with 1+ content tags" decidable rather than a judgment call. |
| `.pre-commit-config.yaml` | https://github.com/matplotlib/matplotlib/blob/main/.pre-commit-config.yaml | context-only | — | — | — | Decides every `Auto-fix risk` reading. `ruff-check` runs with `--fix`; `oxipng`, `end-of-file-fixer`, `trailing-whitespace`, `mixed-line-ending`, `isort` rewrite files; `mypy`, `codespell`, `rstcheck`, `yamllint`, `shellcheck`, `no-commit-to-branch`, `name-tests-test` are check-only. `ci.autofix_prs: false`. |
| `pyproject.toml` | https://github.com/matplotlib/matplotlib/blob/main/pyproject.toml | context-only | — | — | — | Holds the ruff line-length setting and pytest config. No rows. |
| `tox.ini` | https://github.com/matplotlib/matplotlib/blob/main/tox.ini | context-only | — | — | — | Holds the `stubtest` environment named by the coding guide. No rows. |
| `README.md` | https://github.com/matplotlib/matplotlib/blob/main/README.md | context-only | — | — | — | Checked for a canonical test invocation; it defers to the devdocs. No rows. |
| `.github/CONTRIBUTING.md` | https://github.com/matplotlib/matplotlib/blob/main/.github/CONTRIBUTING.md | rules | Exclude | — | X-NARRATIVE | One sentence, a bare redirect to the contributing guide. **Zero-rule source**, recorded rather than omitted. |
| Bug triage and issue curation | https://matplotlib.org/devdocs/devel/triage.html | rules | Exclude | — | X-TRIAGE | Labelling, closing, and reviewing other people's issues and PRs. Its `AI-generated contributions` section restates the AI policy at reviewers, so no rule is lost by excluding it. |
| Release guide | https://matplotlib.org/devdocs/devel/release_guide.html | rules | Exclude | — | X-MAINT | Branching, tagging, uploading to PyPI, deploying docs. |
| Community management guide | https://matplotlib.org/devdocs/devel/communication_guide.html | rules | Exclude | — | X-GOV | Moderation, social accounts, campaigns. Nothing a diff or commit can violate. |
| Troubleshooting | https://matplotlib.org/devdocs/devel/troubleshooting.html | rules | Exclude | — | X-INSTALL | Windows build errors and git-config fixes. |
| Codespaces | https://github.com/matplotlib/matplotlib/blob/main/doc/devel/codespaces.md | rules | Exclude | — | X-INSTALL | 54 words of Codespace setup, transcluded into `development_setup`. |
| Matplotlib Enhancement Proposals | https://matplotlib.org/devdocs/devel/MEP/index.html | rules | Exclude | — | X-GOV | The MEP process and 18 individual proposals: a governance process for accepting designs, not a constraint on a diff. |
| `.github/ISSUE_TEMPLATE/*.yml` (6 files) | https://github.com/matplotlib/matplotlib/tree/main/.github/ISSUE_TEMPLATE | rules | Exclude | — | X-ISSUE | `bug_report`, `documentation`, `feature_request`, `maintenance`, `tag_proposal`, `config`. Real obligations on an issue body; the rig writes no issue. Kept separate from X-NARRATIVE so this is not read as "never rules". |
| `CODE_OF_CONDUCT.md` | https://github.com/matplotlib/matplotlib/blob/main/CODE_OF_CONDUCT.md | rules | Exclude | — | X-GOV | Placeholder file pointing at the rendered CoC. |

### External standards — one pointer rule each, then stop

| Standard | Reached from | Handling |
|---|---|---|
| PEP8 | coding_guide `PEP8, as enforced by ruff` | one pointer rule (MATPLOTLIB-C049), with matplotlib's own 88-char amendment extracted separately |
| PEP7 | coding_guide `C/C++ extensions` | one pointer rule |
| numpydoc docstring guide | document `API documentation` | one pointer rule |
| NEP 29 / SPEC 0 | min_dep_policy | context only; the policy statements it governs are X-MAINT |

### Source files named, not fetched

`meson.build`, `lib/matplotlib/rcsetup.py`, `lib/matplotlib/typing.py`,
`lib/matplotlib/mpl-data/matplotlibrc`, `tools/boilerplate.py`, `tools/run_clang_tidy.py`,
`tools/visualize_tests.py`, `tools/triage_tests.py`, `.clang-tidy`,
`ci/mypy-stubtest-allowlist.txt`, `doc/sphinxext/gallery_order.py`,
`matplotlib.testing.conftest` — all named inside rules, none fetched.

## Checkpoint 1

- [x] **Every URL uses the pinned version, not `/stable/`.** All doc URLs are
  `matplotlib.org/devdocs/`. One `/stable/` string appears *inside* a quoted rule
  (`document.rst` tells authors to write `redirect-from` paths relative to the stable
  doc root); that is quoted text, not a fetch target.
- [x] **No maintainer or triage page marked Full.** `release_guide`, `triage`,
  `communication_guide` are excluded outright. `pr_guide` — the page most at risk here,
  because it carries author and reviewer guidance under one heading — is `Partial` with
  the eleven reviewer/maintainer sections named on the excluded side. `min_dep_policy` was
  demoted from an early `Full` reading to `Partial` for the same reason: its support
  windows are commitments the project makes, not obligations on a contributor's diff.
- [x] **Partial rows name their in-scope sections.** All thirteen do, by heading.
- [x] **Config files marked `context-only`, not `Partial`.** `.pre-commit-config.yaml`,
  `pyproject.toml`, `tox.ini`, `README.md`, `tag_glossary` — five context-only rows, zero
  rows produced from any of them.
- [x] **Anything claimed about a file's contents was fetched.** Every `.rst` under
  `doc/devel/`, both changelog READMEs, the PR template, and the pre-commit config were
  pulled at the pinned SHA and read in full before this table was written. The six issue
  templates and `pyproject.toml`/`tox.ini`/`README.md` came through the
  `seed_sources.py` bundle.

**Amendments made at Checkpoint 1:** the `Write documentation` in-scope list gained the page
preamble, whose do-not-edit note (MATPLOTLIB-C001) is a real obligation sitting above the
first heading rather than inside `Overview`. Also: `min_dep_policy` Full → Partial (above), and
`development_setup` Exclude → Partial once the `Install pre-commit hooks` section was read
in full and found to state a real obligation about re-staging hook-modified files.

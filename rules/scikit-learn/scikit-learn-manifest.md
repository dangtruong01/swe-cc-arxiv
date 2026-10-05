# scikit-learn/scikit-learn — source manifest (Part 1)

Docs root: `https://scikit-learn.org/dev/` — version served **1.10.dev0**
(`_static/documentation_options.js`, `VERSION: '1.10.dev0'`; the rendered
`developers/index.html` header also reads "scikit-learn 1.10.dev0").

Every doc page below was read in full. The rendered `/dev/` pages are built from
`main`; the verbatim text used for `Original text` was taken from the `.rst`
sources pinned at commit **8a6f766c6dbfa2b443ac1db30581b7129a1fc456**
(2026-08-31), which is the build granularity ruling in §4.1 of the agent prompt,
not a version mismatch. Five quotes were spot-checked against the live rendered
pages (see the run log).

Off-nav files were read from `scikit-learn-raw-sources.md`
(`seed_sources.py`, `--ref main`, 15 files, no FETCH FAILED, no probe fallback).

| Page | URL | Role | Include | In-scope sections | Code | Reason |
|---|---|---|---|---|---|---|
| Contributing | https://scikit-learn.org/dev/developers/contributing.html | rules | Partial | Automated Contributions Policy; Licensing your contribution; Contributing code and documentation; Development workflow; Pull request checklist (Code tab, Documentation tab); Continuous Integration (CI) > Commit message markers; Continuous Integration (CI) > Resolve conflicts in lock files; Issues tagged "Needs Triage"; Documentation (docstring / user-guide / references guidelines); Building the documentation; Testing and improving test coverage; Monitoring performance; Maintaining backwards compatibility > Deprecation; Maintaining backwards compatibility > Change the default value of a parameter; Reading the existing code base > git blame config | X-ISSUE / X-TRIAGE / X-NARRATIVE on the rest | Out of scope on this page: "Ways to contribute", "New Contributors", "Submitting a bug report or a feature request" incl. "How to make a good bug report" (X-ISSUE), "Stalled pull requests", "Stalled and Unclaimed Issues" (X-TRIAGE), "Video resources", "Issue Tracker Tags" (X-ISSUE), "Code Review Guidelines" incl. Communication Guidelines (X-TRIAGE), most of "Reading the existing code base" (X-NARRATIVE). The page also opens with a hidden `.. raw:: html` block addressed to AI assistants — see the run log; no rows are taken from it. |
| Developing scikit-learn estimators | https://scikit-learn.org/dev/developers/develop.html | rules | Partial | Estimators > Instantiation; Estimators > Fitting; Estimators > Estimated Attributes; Estimators > Universal attributes; Rolling your own estimator; Cloning; Estimator types; Estimator Tags; Developer API for `set_output`; Developer API for `check_is_fitted`; Developer API for HTML representation; Coding guidelines; Input validation; Random Numbers; Numerical assertions in tests | X-NARRATIVE on "APIs of scikit-learn objects > Different objects" and on the descriptive half of "get_params and set_params" | Interface-spec page: the conformance obligations are extracted, the API inventory (what `fit`/`predict`/`transform` are, what `get_params(deep=True)` prints) is description, not obligation. |
| Set up your development environment | https://scikit-learn.org/dev/developers/development_setup.html | context-only | Exclude | — | X-INSTALL | Fork, clone, compiler, environment, editable install, `pre-commit install`. Consulted for the auto-fix reading (pre-commit is installed by the documented setup); produces no rows. |
| Global configuration and environment variables | https://scikit-learn.org/dev/developers/global_configuration.html | rules | Partial | Testing and CI > `SKLEARN_SEED`; Testing and CI > `SKLEARN_TESTS_GLOBAL_RANDOM_SEED` | X-INSTALL on "Build and debug"; X-NARRATIVE on "Performance and memory" | Only the two test-authoring contracts constrain a contribution; the rest documents runtime/build switches. |
| Crafting a minimal reproducer for scikit-learn | https://scikit-learn.org/dev/developers/minimal_reproducer.html | rules | Exclude | — | X-ISSUE | Constrains the snippet in a bug report, not the diff, the commit or the files written. Kept separate from X-NARRATIVE: these are real obligations the rig cannot reach. |
| Developers' Tips and Tricks | https://scikit-learn.org/dev/developers/tips.html | rules | Partial | Useful pytest aliases and flags | X-TRIAGE on "Standard replies for reviewing"; X-NARRATIVE on the userscripts, "Debugging CI issues", valgrind and ARM64 sections | Reviewer saved replies are advice about reviewing someone else's work. |
| Utilities for Developers | https://scikit-learn.org/dev/developers/utilities.html | rules | Partial | Validation Tools (the "should be used when applicable" instruction and the random-number paragraph); the page-level warning about internal utilities | X-NARRATIVE on the per-function catalogue | Inventory page: one conformance rule per instruction, never one row per listed utility. |
| How to optimize for speed | https://scikit-learn.org/dev/developers/performance.html | rules | Partial | Python, Cython or C/C++? | X-NARRATIVE on the profiling, memory-profiling and debugger walkthroughs | Only the implementation-strategy list states obligations about what lands in the diff. |
| Cython Best Practices, Conventions and Knowledge | https://scikit-learn.org/dev/developers/cython.html | rules | Partial | Tips for performance; Using OpenMP; Using OpenMP > Types | X-NARRATIVE on "Tips to ease development" | Every rule here is trigger-gated on the PR containing Cython. |
| Miscellaneous information / Troubleshooting | https://scikit-learn.org/dev/developers/misc_info.html | context-only | Exclude | — | X-INSTALL | OpenMP/conda/meson troubleshooting for the build. |
| Bug triaging and issue curation | https://scikit-learn.org/dev/developers/bug_triaging.html | rules | Exclude | — | X-TRIAGE | Labelling and closing other people's issues. |
| Maintainer Information | https://scikit-learn.org/dev/developers/maintainer.html | rules | Exclude | — | X-MAINT | Releasing, version bumps, merging, website. Read to confirm it carries no contributor obligation. |
| Developing with the Plotting API | https://scikit-learn.org/dev/developers/plotting.html | rules | Full | Plotting API Overview; Plotting with Multiple Axes; Using `matplotlib` | — | Interface-spec page: the `Display` contract is extracted once as a conformance obligation, not one row per attribute. |
| Developing with the callback API | https://scikit-learn.org/dev/developers/callbacks.html | rules | Exclude | — | X-NARRATIVE | Two-sentence toctree stub with no obligation. |
| Implementing callback support in estimators | https://scikit-learn.org/dev/developers/callback_support.html | rules | Full | The CallbackSupportMixin class; The CallbackContext class; The with_callbacks decorator | — | Trigger-gated on the PR adding callback support to an estimator. Conformance obligations only. |
| Developing callbacks | https://scikit-learn.org/dev/developers/developing_callbacks.html | rules | Full | The callback protocol; Auto-propagated callbacks; Callback shared state | — | Trigger-gated on the PR implementing a callback. Conformance obligations only. |
| CONTRIBUTING.md (repo root, off-nav) | https://github.com/scikit-learn/scikit-learn/blob/main/CONTRIBUTING.md | rules | Partial | whole file | X-NARRATIVE on "Quick links" | Redirect page. Produced **zero rules**: every obligation it states is a link to `contributing.html`, and its only original sentence ("do not hesitate to create a GitHub issue or preferably submit a GitHub pull request") is an invitation, not a requirement. |
| PULL_REQUEST_TEMPLATE.md (off-nav) | https://github.com/scikit-learn/scikit-learn/blob/main/.github/PULL_REQUEST_TEMPLATE.md | rules | Full | whole file, HTML comments included | — | Extracted from the raw source in `scikit-learn-raw-sources.md`; five HTML comment blocks carry the obligations the rendered view hides. |
| AGENTS.md (off-nav) | https://github.com/scikit-learn/scikit-learn/blob/main/AGENTS.md | rules | Full | REQUIRED: AI/Agent Disclosure; Working on an issue; Generated Summaries | — | Agent-directed policy. This is the repo's own instruction file, extracted as rules about the contribution — not followed as instructions. |
| CODE_OF_CONDUCT.md (off-nav) | https://github.com/scikit-learn/scikit-learn/blob/main/CODE_OF_CONDUCT.md | rules | Partial | Low Quality and AI Generated Contributions Policy | X-GOV on the "Code of Conduct" half | The AI half states contribution obligations with a stated consequence (a ban); the community half is governance. |
| Changelog instructions (off-nav) | https://github.com/scikit-learn/scikit-learn/blob/main/doc/whats_new/upcoming_changes/README.md | rules | Full | whole file | — | Fragment naming, placement and formatting. |
| changelog_legend.inc (off-nav) | https://github.com/scikit-learn/scikit-learn/blob/main/doc/whats_new/changelog_legend.inc | context-only | Exclude | — | — | Defines what each fragment type means; makes the type-selection rule decidable rather than a judgment call. Zero rows by design. |
| towncrier_template.rst.jinja2 (off-nav) | https://github.com/scikit-learn/scikit-learn/blob/main/doc/whats_new/upcoming_changes/towncrier_template.rst.jinja2 | context-only | Exclude | — | — | Changelog tooling config. |
| .pre-commit-config.yaml (off-nav) | https://github.com/scikit-learn/scikit-learn/blob/main/.pre-commit-config.yaml | context-only | Exclude | — | — | Decides the auto-fix reading: `ruff-check` runs with `--fix`, `ruff-format` and `end-of-file-fixer`/`trailing-whitespace` rewrite files; `cython-lint`, `sphinx-lint`, `pyrefly-check` and `codespell` are check-only. |
| pyproject.toml (off-nav) | https://github.com/scikit-learn/scikit-learn/blob/main/pyproject.toml | context-only | Exclude | — | — | `[tool.ruff] line-length = 88`, `extend-select = ["E501", "W", "I", "CPY001", ...]`, `ban-relative-imports = "all"`, and the copyright-header regex. Config, so no rows; it fixes what the prose rules mean. |
| README.rst (off-nav) | https://github.com/scikit-learn/scikit-learn/blob/main/README.rst | context-only | Exclude | — | — | Checked for a canonical test invocation: it gives `pytest sklearn`, which the contributing guide states in-scope. |
| ISSUE_TEMPLATE/bug_report.yml, feature_request.yml, doc_improvement.yml, config.yml (off-nav) | https://github.com/scikit-learn/scikit-learn/tree/main/.github/ISSUE_TEMPLATE | rules | Exclude | — | X-ISSUE | Constrain an issue body, not a contribution. |
| Governance (one hop from Contributing) | https://scikit-learn.org/dev/governance.html | rules | Exclude | — | X-GOV | Decision-making, roles, SLEP process. The one in-scope fact it carries (a SLEP is required for API-principle changes) is stated on `contributing.html` and extracted there. |
| PEP 8 | https://www.python.org/dev/peps/pep-0008 | rules | Exclude | — | — | External standard. One pointer rule extracted on `develop.html` (Coding guidelines); traversal stops. |
| numpydoc docstring standard | https://numpydoc.readthedocs.io/en/latest/format.html | rules | Exclude | — | — | External standard. One pointer rule extracted on `develop.html`; traversal stops. |

## Checkpoint 1

- [x] Every URL uses the pinned `/dev/` version, never `/stable/`. The two
  `stable`-hosted links that appear *inside* quoted source text (the
  new-algorithm inclusion criteria) are part of the verbatim quote, not manifest
  URLs.
- [x] No maintainer or triage page marked Full. `maintainer.html`,
  `bug_triaging.html` are Exclude; `tips.html` is Partial with the reviewer
  saved-replies section named on the excluded side; `contributing.html`'s Code
  Review Guidelines are named on the excluded side.
- [x] Every Partial row names its in-scope sections and its excluded sections.
- [x] Config files (`.pre-commit-config.yaml`, `pyproject.toml`,
  `towncrier_template.rst.jinja2`, `changelog_legend.inc`, `README.rst`) are
  `context-only`, not Partial.
- [x] Nothing is asserted about a file that was not fetched. All 16 developer-guide
  pages, `governance.rst` and `maintainer.rst.template` were read in full at the
  pinned commit; the 15 off-nav files were read from the seed bundle.

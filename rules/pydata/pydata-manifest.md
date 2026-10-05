# pydata/xarray — source manifest (Part 1)

Repo: `pydata/xarray` @ `main`
Docs root (pinned): <https://docs.xarray.dev/en/latest/contribute/>
Docs version served at assessment time: **2026.7.1.dev28+ge902fe896**

`/en/latest/` is xarray's development build, not an alias for `/en/stable/`. The version
string it serves carries the git hash of the build (`ge902fe896`), so the docs are pinned to
commit `e902fe89698be3061ba161c5894826985e45e147` rather than merely to a release. Every
`.rst`/`.md` source quoted below was pulled from **that commit**, and every rendered page
assessed reported the same version string, so no page is on a different build.
`/en/stable/` was never used as a source.

**Fetch note.** Each doc page was reached twice: the rendered page at the pinned docs root
(assessment, headings, five verbatim spot-checks) and its source at
`raw.githubusercontent.com/pydata/xarray/e902fe896.../doc/...` for byte-exact verbatim text.
The build-hash pin above is what licenses using the source bytes as the verbatim record.
Off-nav files were taken from `pydata-raw-sources.md`, not from GitHub's rendered view —
the PR template's obligations live in HTML comments that the rendered view strips.

## Manifest

| Page | URL | Role | Include | In-scope sections | Code | Reason |
|---|---|---|---|---|---|---|
| Xarray Developer's Guide (index) | https://docs.xarray.dev/en/latest/contribute/index.html | context-only | Exclude | — | X-NARRATIVE | Toctree plus one welcoming paragraph. States no obligation; fetched to enumerate the section's pages. |
| Contributing to xarray | https://docs.xarray.dev/en/latest/contribute/contributing.html | rules | Partial | Overview (AI-policy sentence only); Development workflow (all subsections); Contributing to the documentation (About; How to build; Writing ReST pages); Contributing to the code base (Code standards; Code Formatting; Backwards Compatibility; Testing With CI; TDD; Writing tests; Transitioning to pytest; Using pytest; Running the test suite; Running the performance test suite; Documenting your code); Contributing your changes (Committing; Pushing; Review; Finally, make the pull request; Delete your merged branch; PR checklist) | — | Main rule source, 94 rows. Out of scope on the same page: *Where to start?* (X-NARRATIVE, how to pick an issue); *Bug reports and enhancement requests* incl. *Submitting a bug report* (X-ISSUE — the three numbered requirements constrain an issue body, not a contribution); *Getting started with Git* (X-INSTALL); *Creating a development environment* and *Creating a Python Environment* (X-INSTALL, Pixi install and `pixi info`/`pixi shell`); the code-of-conduct sentence in *Overview* (X-GOV). |
| AI Usage Policy | https://docs.xarray.dev/en/latest/contribute/ai-policy.html | rules | Partial | Core Principle: Changes; Core Principle: Communication; Code and Tests (Review Every Line, incl. the Not Acceptable / Acceptable examples; Large AI-Assisted Contributions); Documentation | — | 16 rows. Out of scope: the opening **Note** paragraph and its two footnotes (X-NARRATIVE, rationale for the policy and a link on skill formation); the sentence "Maintainers reserve the right to delete or hide comments…" (X-MAINT). |
| Pull request template | https://github.com/pydata/xarray/blob/main/.github/PULL_REQUEST_TEMPLATE.md | rules | Full | Description; Checklist; AI Disclosure | — | 11 rows, 4 of them from the three HTML comment blocks GitHub's rendered view hides (the third comment, 'Feel free to remove check-list items…', grants a permission and yields no row). Taken from `pydata-raw-sources.md`. |
| `CLAUDE.md` (repo root) | https://github.com/pydata/xarray/blob/main/CLAUDE.md | rules | Partial | Code Style Guidelines (Import Organization); GitHub Interaction Guidelines; Run tests; Linting & type checking | — | **Added in the C122 append.** Agent-instruction file at the repository root, in scope under the Part 1 traversal table wherever it exists, even though it sits outside the docs navigation — which is why the first pass missed it: nothing in `doc/` links it and none of `seed_sources.py`'s PATTERNS matches a bare `CLAUDE.md`. 10 rows (C122–C131), taken from the raw file in `pydata-raw-sources.md`, not from GitHub's rendered view. Out of scope on the same page: *Setup* (`uv sync`, X-INSTALL). |
| `xarray/tests/CLAUDE.md` | https://github.com/pydata/xarray/blob/main/xarray/tests/CLAUDE.md | rules | Full | Handling Optional Dependencies (Standard Decorators; DO NOT use conditional imports or skipif; Multiple dependencies; Importing optional dependencies in tests; Common patterns); Key Points | — | **Added in the C122 append.** Per-directory agent-instruction file governing test style. Same discovery gap as the root file. 8 rows (C132–C139). Ordinary test conventions that happen to live in a Claude-named file; classified on their merits. |
| `AI_POLICY.md` (repo root) | https://github.com/pydata/xarray/blob/main/AI_POLICY.md | context-only | Exclude | — | — | 28-byte pointer to `doc/contribute/ai-policy.md`, which is already the source of C095–C110. Fetched during the append and confirmed to contain no obligation of its own; re-extracting it would have duplicated 16 rows. |
| Development roadmap | https://docs.xarray.dev/en/latest/roadmap.html | excluded | Exclude | — | X-NARRATIVE | Source fetched in full at the pinned commit (1.6k words, dated September 7 2021). Project direction and philosophy; no obligation attaches to a diff, a commit or a written file. |
| What's New | https://docs.xarray.dev/en/latest/whats-new.html | context-only | Exclude | — | — | The release-in-progress head of `doc/whats-new.rst` was read at the pinned commit; the rest of the file is historical changelog. Consulted for a changelog fragment legend; there is none. The `(:issue:`NNNN`, :pull:`NNNN`)` / "By `Name <url>`_" shape is observable convention only; the one part stated as a rule (the `:issue:` role) is C070, taken from the contributing guide. |
| Developers meeting | https://docs.xarray.dev/en/latest/contribute/developers-meeting.html | excluded | Exclude | — | X-NARRATIVE | Source fetched in full at the pinned commit. Zoom link, notes link and a calendar embed. Community logistics, no contribution obligation. |
| Xarray Internals (index + 9 pages: internal-design, interoperability, duck-arrays-integration, chunked-arrays, extending-xarray, how-to-add-new-backend, how-to-create-custom-index, zarr-encoding-spec, time-coding) | https://docs.xarray.dev/en/latest/internals/index.html | excluded | Exclude | — | X-NARRATIVE | All ten fetched in full as source at the pinned commit (~10.4k words) before excluding. The index states the audience: contributors wanting to understand internals, and **developers of other packages** extending xarray. The pages that do state conformance obligations state them for code that lives *outside* this repository — `how-to-add-new-backend` opens "Adding a new backend for read support to Xarray does not require one to integrate any code in Xarray", and `extending-xarray` and `how-to-create-custom-index` are the same shape. Design and extension reference, not contribution instruction prose. Including them would have added an estimated 8–12 API-conformance rows about third-party packages. |
| CONTRIBUTING.md | https://github.com/pydata/xarray/blob/main/CONTRIBUTING.md | context-only | Exclude | — | X-NARRATIVE | 139 bytes; a single sentence redirecting to the online contributor guide. Zero rules. Consulted to confirm the canonical docs URL. |
| README.md | https://github.com/pydata/xarray/blob/main/README.md | context-only | Exclude | — | — | Checked for a canonical test invocation; it has none and defers to the contributing page (via a stale `/en/stable/contributing.html` link that now redirects into `/contribute/`). Zero rows. |
| .pre-commit-config.yaml | https://github.com/pydata/xarray/blob/main/.pre-commit-config.yaml | context-only | Exclude | — | — | Config file. `ruff-check` runs with `--fix`, plus `ruff-format`, `blackdoc`, `prettier`, `taplo-format`, whitespace/EOF fixers; `mypy` is pinned to the **manual** hook stage. Decides every Auto-fix reading in the sheet. Produces no rows. |
| pyproject.toml | https://github.com/pydata/xarray/blob/main/pyproject.toml | context-only | Exclude | — | — | Config file. `[tool.ruff.lint]` rule set, `known-first-party = ["xarray"]`, `ban-relative-imports = "all"`, per-file ignores. Fixes what C038 and C039 actually require. Produces no rows. |
| CODE_OF_CONDUCT.md | https://github.com/pydata/xarray/blob/main/CODE_OF_CONDUCT.md | excluded | Exclude | — | X-GOV | NumFOCUS code of conduct. Community conduct; no obligation reachable from a diff or a commit. |
| Issue template: bug report | https://github.com/pydata/xarray/blob/main/.github/ISSUE_TEMPLATE/bugreport.yml | excluded | Exclude | — | X-ISSUE | Required fields of a bug-report form. Real obligations the harness cannot reach; kept distinct from X-NARRATIVE. |
| Issue template: new feature | https://github.com/pydata/xarray/blob/main/.github/ISSUE_TEMPLATE/newfeature.yml | excluded | Exclude | — | X-ISSUE | Constrains an issue body, not a contribution. |
| Issue template: misc | https://github.com/pydata/xarray/blob/main/.github/ISSUE_TEMPLATE/misc.yml | excluded | Exclude | — | X-ISSUE | Constrains an issue body, not a contribution. |
| Issue template config | https://github.com/pydata/xarray/blob/main/.github/ISSUE_TEMPLATE/config.yml | excluded | Exclude | — | X-ISSUE | Contact-link configuration. |
| numpydoc docstring standard | https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard | excluded | Exclude | — | — | External standard. One pointer rule (C024), then stop, per the traversal rule. |
| `pixi.toml` | (not fetched) | excluded | Exclude | — | — | Repository config file named by *Creating a Python Environment* ("All these Pixi environments and tasks are defined in the `pixi.toml` file"). Named in Notes rather than fetched; the Auto-fix reading is already decided by `.pre-commit-config.yaml`. |
| `doc/api.rst` | (not fetched) | excluded | Exclude | — | — | One-hop target of C027 and C114. Generated API reference for end users, not instruction prose; named in those rows rather than fetched. |
| `asv.conf.json` | (not fetched) | excluded | Exclude | — | — | Named by C067 as where the default asv environment manager lives. Repository config file; named in Notes, not fetched. |

`seed_sources.py` found no changelog-fragment directory anywhere in the tree: xarray edits a
single `doc/whats-new.rst` by hand, which is why C069/C070 are file-edit rules rather than
fragment-format rules. It also does **not** match `doc/contribute/ai-policy.md` with any of
its patterns — that file was found by listing `doc/contribute/` through the GitHub contents
API, and it is the second-largest rule source in this repo.

## Checkpoint 1

| Check | Result |
|---|---|
| Every URL uses the pinned version, not `/stable/` | PASS — every doc URL is under `/en/latest/`; the repository files use `github.com/.../blob/main/`, the same ref `seed_sources.py` pulled, and every quoted byte comes from commit `e902fe896`. |
| No maintainer or triage pages marked Full | PASS — the only `Full` row is the PR template. The one maintainer sentence encountered ("Maintainers reserve the right to delete or hide comments…") is named as an out-of-scope X-MAINT clause of a Partial page. xarray has no separate maintainer or triage guide in its documentation. |
| Partial rows actually name their in-scope sections | PASS — both Partial rows enumerate in-scope sections and list the excluded ones with codes. |
| Config files marked `context-only`, not `Partial` | PASS — `.pre-commit-config.yaml`, `pyproject.toml`, `README.md`, `CONTRIBUTING.md`, `whats-new.rst` and the guide index are `context-only`; none produces a row. |
| Anything it claims about a file's contents, it fetched | PASS, with three declared exceptions: `pixi.toml`, `doc/api.rst` and `asv.conf.json` are named but not fetched, and nothing is asserted about their contents. |


## Append (C122–C139): two off-nav agent-instruction files

The three rows marked *Added in the C122 append* were assessed after the original run
closed at C121. Both `CLAUDE.md` files sit outside the documentation navigation and outside
`seed_sources.py`'s PATTERNS, which is the same discovery gap that hid
`doc/contribute/ai-policy.md` in the first pass; Part 1's traversal table puts
agent-instruction files in scope wherever they exist, so they should have been reached.
Both were fetched raw from `raw.githubusercontent.com` at `main` and are reproduced
verbatim in `pydata-raw-sources.md`.

Checkpoint 1 re-run over the three added rows:

| Check | Result |
|---|---|
| Every URL uses the pinned version, not `/stable/` | PASS — repository files, cited at `blob/main/`, the same ref the rest of the repo-file rows use. |
| No maintainer or triage pages marked Full | PASS — the one `Full` row is a test-style file; neither file contains maintainer or triage material. |
| Partial rows actually name their in-scope sections | PASS — the root file's row names its four in-scope headings and its one excluded one. |
| Config files marked `context-only`, not `Partial` | PASS — `AI_POLICY.md` is the only new non-rules row and is `context-only`. |
| Anything it claims about a file's contents, it fetched | PASS — all three fetched; the two rule sources are pasted verbatim into `pydata-raw-sources.md`. |

Neither file is a doc page, so no version string applies to them; the docs pin above is
untouched by the append and no existing row moved.

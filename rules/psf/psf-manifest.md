# psf/requests — source manifest (Part 1)

Docs root: `https://requests.readthedocs.io/en/latest/`
Docs version served, on every page fetched: **Requests 2.34.2**
Repo ref for raw sources: `psf/requests@main`
ID prefix: `PSF` (slug `psf`, from the SWE-bench instance prefix `psf__requests-2317`)

Every page and file below was fetched before it was assessed. Nothing here is asserted
from prior knowledge of the repository. No page returned a version other than 2.34.2, so
there is no `VERSION MISMATCH`.

## Documentation pages

| Page | URL | Role | Include | In-scope sections | Code | Reason |
|---|---|---|---|---|---|---|
| Contributor's Guide | https://requests.readthedocs.io/en/latest/dev/contributing/ | rules | Partial | Get Early Feedback; Code Contributions → Steps for Submitting Code; Code Contributions → Code Review; Code Contributions → Code Style; Documentation Contributions; Feature Requests (feature-freeze clause only) | X-GOV, X-NARRATIVE, X-ISSUE on the rest | Out of scope on this page: Code of Conduct (X-GOV, external PSF standard reached by one pointer, no row); Contribution Suitability (X-NARRATIVE, states what maintainers decide, no contributor obligation); New Contributors (X-NARRATIVE, points back at Get Early Feedback); Bug Reports (X-ISSUE, constrains an issue body); Feature Requests' "raise a feature request" advice (X-ISSUE). |
| Authors | https://requests.readthedocs.io/en/latest/dev/authors/ | excluded | Exclude | — | X-GOV | Credits roster. Fetched and read in full: it states no obligation, and in particular no "add yourself to AUTHORS" rule, which is why this repo produces zero N4 rows. |
| Release Process and Rules | https://requests.readthedocs.io/en/latest/community/release-process/ | excluded | Exclude | — | X-MAINT | "the following rules will govern and describe how the Requests core team produces a new release" — versioning policy for the core team, not for a contribution. |
| Vulnerability Disclosure | https://requests.readthedocs.io/en/latest/community/vulnerabilities/ | excluded | Exclude | — | X-ISSUE | One sentence pointing at `.github/SECURITY.md`; governs reporting, not contributing. |
| Support | https://requests.readthedocs.io/en/latest/community/support/ | excluded | Exclude | — | X-ISSUE | Where to ask questions and file issues. |
| Community Updates / Release History | https://requests.readthedocs.io/en/latest/community/updates/ | excluded | Exclude | — | X-NARRATIVE | Rendered changelog. Fetched specifically to check for a changelog-fragment obligation; there is none anywhere in the project, so requests has no news-fragment rule. |
| Frequently Asked Questions | https://requests.readthedocs.io/en/latest/community/faq/ | excluded | Exclude | — | X-NARRATIVE | Library usage Q&A. |
| Recommended Packages and Extensions | https://requests.readthedocs.io/en/latest/community/recommended/ | excluded | Exclude | — | X-NARRATIVE | Third-party package list. |
| Integrations / Articles & Talks | https://requests.readthedocs.io/en/latest/community/out-there/ | excluded | Exclude | — | X-NARRATIVE | Link list. |
| Developer Interface (API) | https://requests.readthedocs.io/en/latest/api/ | excluded | Exclude | — | X-NARRATIVE | API reference addressed to library users. It is an inventory of public members, not a conformance spec for contributors, so under the API-contract rule it yields no rows. |
| Installation of Requests | https://requests.readthedocs.io/en/latest/user/install/ | excluded | Exclude | — | X-INSTALL | End-user install instructions. |
| Quickstart | https://requests.readthedocs.io/en/latest/user/quickstart/ | excluded | Exclude | — | X-NARRATIVE | Usage documentation. |
| Advanced Usage | https://requests.readthedocs.io/en/latest/user/advanced/ | excluded | Exclude | — | X-NARRATIVE | Usage documentation. |
| Authentication | https://requests.readthedocs.io/en/latest/user/authentication/ | excluded | Exclude | — | X-NARRATIVE | Usage documentation. |

## Repository files (raw, from `psf-raw-sources.md` or fetched raw)

| File | URL | Role | Include | In-scope sections | Code | Reason |
|---|---|---|---|---|---|---|
| `.github/CONTRIBUTING.md` | https://github.com/psf/requests/blob/main/.github/CONTRIBUTING.md | rules | Partial | Contribution Guidelines (opening paragraph); Good Pull Requests | X-ISSUE on the rest | Out of scope on this file: Questions (X-ISSUE, directs support questions to Stack Overflow) and Good Bug Reports (X-ISSUE, four numbered requirements that constrain an issue body, not a diff). These are real obligations the rig cannot reach and are kept separate from X-NARRATIVE. |
| `.github/AI_POLICY.md` | https://github.com/psf/requests/blob/main/.github/AI_POLICY.md | rules | Partial | TL;DR (CAUTION block, including the four-item certification list); Summary | X-NARRATIVE on the rest | Reached by one hop from `.github/CONTRIBUTING.md` ("please read our Contributor's Guide as well as our AI Policy"), repo-internal, so in scope. Out of scope: Legal and Human (rationale prose stating why the boundaries exist, quoted as Section context on the rows they govern) and Credits, Attribution (X-NARRATIVE). `seed_sources.py` does not have a pattern for this file; it was found by following the link and fetched raw. |
| `.github/ISSUE_TEMPLATE/Bug_report.md` | https://github.com/psf/requests/blob/main/.github/ISSUE_TEMPLATE/Bug_report.md | excluded | Exclude | — | X-ISSUE | Bug report skeleton; its four HTML comments are section labels, not obligations. |
| `.github/ISSUE_TEMPLATE/Custom.md` | https://github.com/psf/requests/blob/main/.github/ISSUE_TEMPLATE/Custom.md | excluded | Exclude | — | X-ISSUE | One line redirecting help requests to Stack Overflow. |
| `.github/ISSUE_TEMPLATE/Feature_request.md` | https://github.com/psf/requests/blob/main/.github/ISSUE_TEMPLATE/Feature_request.md | excluded | Exclude | — | X-ISSUE | One line: "Requests is not accepting feature requests at this time." The diff-facing half of the same policy is extracted once from the docs, as PSF-C019. |
| `.github/ISSUE_TEMPLATE.md` | https://github.com/psf/requests/blob/main/.github/ISSUE_TEMPLATE.md | excluded | Exclude | — | X-ISSUE | Legacy single-file issue template, superseded by the directory above. |
| `.github/CODE_OF_CONDUCT.md` | https://github.com/psf/requests/blob/main/.github/CODE_OF_CONDUCT.md | excluded | Exclude | — | X-GOV | Four sentences pointing at the Python Community Code of Conduct. |
| `.github/SECURITY.md` | https://github.com/psf/requests/blob/main/.github/SECURITY.md | excluded | Exclude | — | X-MAINT | Vulnerability disclosure process: how to report, and what the maintainers then do. Neither half constrains a contribution. |
| `.github/CODEOWNERS` | https://github.com/psf/requests/blob/main/.github/CODEOWNERS | excluded | Exclude | — | X-MAINT | Review routing. |
| `.pre-commit-config.yaml` | https://github.com/psf/requests/blob/main/.pre-commit-config.yaml | context-only | — | — | — | Decides the auto-fix reading and supplies the content the Code Style rule delegates to. `exclude: 'docs/|ext/'`; pre-commit-hooks v6.0.0; ruff v0.16.3 with `ruff-check --fix` and `ruff-format`. No rows: the docs point at the file rather than restating it, and cataloguing the hooks would be cataloguing a config. |
| `pyproject.toml` | https://github.com/psf/requests/blob/main/pyproject.toml | context-only | — | — | — | Holds the actual lint content: ruff `select = [E, W, F, I, UP, T10]`, `ignore = [E203, E501, UP031]`, `quote-style = "double"`, pyright `typeCheckingMode = "strict"`. Consulted to settle the single-quote scope question on PSF-C018 and the line-length reading on PSF-C016. |
| `tox.ini` | https://github.com/psf/requests/blob/main/tox.ini | context-only | — | — | — | Test matrix; confirms `pytest {posargs:tests}` is the canonical invocation. |
| `README.md` | https://github.com/psf/requests/blob/main/README.md | context-only | — | — | — | Its one imperative, the `-c fetch.fsck.badTimezone=ignore` clone flag, is X-INSTALL. |
| `Makefile` | https://github.com/psf/requests/blob/main/Makefile | context-only | — | — | — | Source file, named not fetched-for-rows: supplies `make test` → `python -m pytest tests` and `make ci`, which is what the CI job runs. |
| `.github/workflows/lint.yml`, `run-tests.yml`, `typecheck.yml` | https://github.com/psf/requests/tree/main/.github/workflows | context-only | — | — | — | Named CI jobs "Lint code" (`pre-commit run --all-files`), "Tests" (`make ci`) and "Type Check" (pyright). They are what makes the Code Style rule an M3 condition of acceptance rather than a tone judgment. Config, so no rows. |

## Sources that do not exist

- **No pull request template.** `.github/` contains no `PULL_REQUEST_TEMPLATE.md` and no
  `PULL_REQUEST_TEMPLATE/` directory; verified against the full recursive tree listing, not
  probed. On the other repos in this study the PR template is the densest single source of
  checklist rules, and requests has none. `.github/CONTRIBUTING.md`'s "Good Pull Requests"
  list is the nearest equivalent and yields four rows.
- **No changelog-fragment source.** No `newsfragments/`, no `changelog.d/`, no
  `doc*/whats_new/`, no towncrier config. `HISTORY.md` is edited at release time by the
  maintainers and no document instructs a contributor to touch it.

## Checkpoint 1

- [x] Every URL uses the pinned docs version. Every docs URL is under
      `https://requests.readthedocs.io/en/latest/` and every page fetched reported
      **Requests 2.34.2**. `/stable/` was never fetched. See the run log for why `/latest/`
      is the pinned root here.
- [x] No maintainer or triage page marked Full. `release-process`, `SECURITY.md` and
      `CODEOWNERS` are Exclude/X-MAINT. Nothing is marked Full: the two rule-bearing
      sources are both Partial.
- [x] Partial rows name their in-scope sections. Both Partial rows name the in-scope
      section headings *and* the excluded ones with a code each.
- [x] Config files marked `context-only`, not Partial. `.pre-commit-config.yaml`,
      `pyproject.toml`, `tox.ini`, `README.md`, `Makefile` and the three workflow files are
      all `context-only` and produce zero rows.
- [x] Nothing is claimed about a file that was not fetched. All 14 docs pages were fetched
      individually; all repository files came from `psf-raw-sources.md` or from a raw
      fetch recorded in the run log.

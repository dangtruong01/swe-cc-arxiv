# mwaskom/seaborn — source manifest (Part 1)

Pinned source root: `https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/`
Version served by that tree: **seaborn 0.14.0.dev0** (`seaborn/__init__.py:__version__`)
Published docs site, assessed and excluded: `https://seaborn.pydata.org/` — **seaborn 0.13.2 documentation**
Repo ref for raw sources: `mwaskom/seaborn@master` (seaborn's default branch is `master`, not `main`)
ID prefix: `MWASKOM` (slug `mwaskom`, from the SWE-bench instance prefix `mwaskom__seaborn-3069`)

Every file below was fetched raw at the pinned commit before it was assessed. Nothing
here is asserted from prior knowledge of the repository.

## Why the pinned root is a git tree and not a docs URL

seaborn publishes no development or contributing documentation on its website. The site
was fetched (`https://seaborn.pydata.org/`, reporting *seaborn 0.13.2 documentation*) and
its whole navigation is Installing / Gallery / Tutorial / API / Releases / Citing / FAQ —
there is no contributing, development or contributor-guide page, and `doc/faq.rst`
contains no occurrence of the string "contribut" at all. The repository's `doc/` directory
confirms it: `api.rst`, `citing.rst`, `faq.rst`, `index.rst`, `installing.rst`,
`whatsnew/` and nothing else.

Every contribution rule seaborn states therefore lives in repository files, so the pin is
a commit SHA rather than a docs build. There is no `VERSION MISMATCH`: no rule is
extracted from the 0.13.2 site, and every extracted quote comes from the single commit
`f04b6cd5484267a0885d1fed068e99dff3a1b226` (0.14.0.dev0). `/stable/` was never fetched.

## Documentation pages

| Page | URL | Role | Include | In-scope sections | Code | Reason |
|---|---|---|---|---|---|---|
| seaborn docs home | https://seaborn.pydata.org/ | excluded | Exclude | — | X-NARRATIVE | Fetched to establish what the published site carries. Landing page plus feature grid; its navigation has no contributing or development entry, which is the finding that moves the pin into the repo. |
| Installing and getting started | https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/doc/installing.rst | excluded | Exclude | — | X-INSTALL, X-ISSUE | End-user install, dependency list and quickstart (X-INSTALL). Its closing "Getting help" section restates `.github/CONTRIBUTING.md`'s bug-report requirements near-verbatim (X-ISSUE); had either been in scope the pair would have been an N3 conflict, and neither is. |
| Frequently asked questions | https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/doc/faq.rst | excluded | Exclude | — | X-NARRATIVE | 4,168 words of library-usage Q&A across six sections (Getting started, Tricky concepts, Specifying data, Layout problems, Other customizations, Statistical inquiries, Common curiosities). Read in full; zero occurrences of "contribut", "pull request" or "test suite". |
| API reference | https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/doc/api.rst | excluded | Exclude | — | X-NARRATIVE | An `autosummary` inventory of public functions addressed to library users. Under the API-contract rule it states no conformance obligation, so it yields no rows. |
| Seaborn changelog | https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/doc/whatsnew/index.rst | excluded | Exclude | — | X-MAINT | Fetched specifically to look for a changelog-fragment obligation. It is a bare `toctree` over 26 hand-written per-release files; no document anywhere instructs a contributor to add an entry. |
| Docs home / Citing | https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/doc/index.rst | excluded | Exclude | — | X-NARRATIVE | Landing page source and citation request. Its only imperative is "To see the code or report a bug, please visit the GitHub repository". |

## Repository files

| File | URL | Role | Include | In-scope sections | Code | Reason |
|---|---|---|---|---|---|---|
| `README.md` | https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/README.md | rules | Partial | Testing (second and third paragraphs) | X-INSTALL, X-ISSUE, X-NARRATIVE on the rest | **This is seaborn's only source of diff-facing contribution rules.** In scope: "To test the code, run `make test`…" and "Code style is enforced with `ruff`… Run `make lint` to check. Alternately, you can use `pre-commit`…". Out of scope: Testing's first sentence (`uv sync` dependency install, X-INSTALL); Documentation, Dependencies, Installation and Citing (X-NARRATIVE / X-INSTALL, addressed to library users); Development (X-ISSUE — where to file bugs and ask usage questions). `seed_sources.py` classifies `README.md` as `context` by pattern; that default is overridden here because the Testing section states obligations the scope test admits. Recorded as a deliberate deviation in the run log. |
| `.github/CONTRIBUTING.md` | https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/.github/CONTRIBUTING.md | rules | Partial | New features (development-focus clause only) | X-NARRATIVE, X-ISSUE on the rest | Despite its name this file is a bug-reporting guide, not a contributor guide. Out of scope: General support (X-NARRATIVE, directs "how do I do X?" to StackOverflow); Reporting bugs in its entirety (X-ISSUE — the four "must include" bullets, the synthetic-data preference, the "do not share data as a pickle file" prohibition, the search-before-filing advice and the reproduce-in-matplotlib suggestion all constrain an issue body, not a diff). In scope: the second sentence of New features, which tempers what kind of change is welcome and so can be read against the diff. The first sentence ("you can open an issue to discuss it") is X-ISSUE. |
| `SECURITY.md` | https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/SECURITY.md | excluded | Exclude | — | X-ISSUE | Private vulnerability disclosure. "Do not disclose it as a public issue" and the 90-day embargo constrain a report and the maintainer's response, not a contribution. |
| `doc/README.md` | https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/doc/README.md | excluded | Exclude | — | X-INSTALL | "Building the seaborn docs". Reached by one hop from README.md's Documentation section. Fetched and read in full: install the `[stats,docs]` extras, set `NB_KERNEL`, run `make notebooks html` from `doc/`, `make clean`. Every imperative is a build or environment action; none can be violated by a diff. It states no docs *style* rule, which is why seaborn's Documentation and docstrings bucket is empty. |
| `.pre-commit-config.yaml` | https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/.pre-commit-config.yaml | context-only | — | — | — | Decides the auto-fix reading. `pre-commit-hooks` v4.3.0 (`check-yaml`, `end-of-file-fixer`, `trailing-whitespace` excluding `.svg`), `ruff-pre-commit` v0.15.20 with `id: ruff` and **no `--fix` argument**, `ty-pre-commit` v0.0.56. So the ruff hook reports and does not repair, while the whitespace hooks do rewrite files. No rows: cataloguing hooks is cataloguing a config. |
| `pyproject.toml` | https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/pyproject.toml | context-only | — | — | — | Holds the content README.md's style rule delegates to: `[tool.ruff] line-length = 88`, `extend-exclude = ["seaborn/cm.py", "seaborn/external"]`, `[tool.ruff.lint] select = ["E", "W", "F"]`, `ignore = ["E741", "F522"]`. Also `requires-python = ">=3.10"`, the pytest `filterwarnings` list and the coverage `omit`/`exclude_lines` lists. Consulted for MWASKOM-C002; produces no rows of its own. |
| `Makefile` | https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/Makefile | context-only | — | — | — | Source file, named and fetched for context only: supplies what the README's two commands expand to — `test` → `uv run --no-sync pytest -n auto --cov=seaborn --cov=tests --cov-config=pyproject.toml tests`, `lint` → `uv run --no-sync ruff check seaborn/ tests/`, plus `typecheck` and `docs` targets the prose never mentions. |
| `.github/workflows/ci.yaml` | https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/.github/workflows/ci.yaml | context-only | — | — | — | Four named CI jobs — `build-docs`, `run-tests` (7-way Python matrix, runs `make test`), `lint` (runs `make lint`), `typecheck` (runs `make typecheck`) — triggered on `pull_request` to `master`. They are what makes MWASKOM-C001 and C002 M3 conditions of acceptance rather than tone readings. Config, so no rows. |
| `seaborn/conftest.py`, `seaborn/_testing.py`, `tests/` | https://github.com/mwaskom/seaborn/tree/f04b6cd5484267a0885d1fed068e99dff3a1b226/tests | — | — | — | — | Source files. Named, not fetched for rows, per the traversal table. seaborn's test conventions live only in these files; no prose documents them. |
| `CITATION.cff`, `LICENSE.md`, `.github/dependabot.yml`, `doc/Makefile`, `doc/conf.py`, `.gitignore` | https://github.com/mwaskom/seaborn/tree/f04b6cd5484267a0885d1fed068e99dff3a1b226 | excluded | Exclude | — | X-NARRATIVE, X-MAINT | Citation metadata, licence, dependency-bot schedule, Sphinx build plumbing. None states a contributor obligation. |

## Sources that do not exist

Verified against the full recursive tree listing of `mwaskom/seaborn@master`
(325 blobs, `truncated: false`), not against a probe list.

- **No pull request template.** `.github/` holds exactly three files: `CONTRIBUTING.md`,
  `dependabot.yml` and `workflows/ci.yaml`. There is no `PULL_REQUEST_TEMPLATE.md` and no
  `PULL_REQUEST_TEMPLATE/` directory. On most repos in this study the PR template is the
  densest single source of checklist rules; seaborn has nothing in its place, and its
  `CONTRIBUTING.md` carries no pull-request section either.
- **No issue templates.** No `.github/ISSUE_TEMPLATE/` and no `ISSUE_TEMPLATE.md`. The
  bug-report requirements are prose in `CONTRIBUTING.md` and `doc/installing.rst` instead.
- **No AI or agent policy.** No `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`,
  `AI_POLICY.md` or any path matching `*ai-policy*` / `*ai_policy*`. seaborn's
  AI-assisted contribution policy bucket is empty because the repo states no such policy.
- **No code of conduct.** No `CODE_OF_CONDUCT.md` anywhere in the tree.
- **No changelog-fragment source.** No `newsfragments/`, no `changelog.d/`, no
  `doc/whats_new/README`, no towncrier config. `doc/whatsnew/*.rst` are release notes
  written at release time.
- **No coding-style, docstring, commit-message or branch-naming document.** Searched the
  tree for `contrib`, `develop`, `style`, `testing`, `policy`, `govern`, `conduct`,
  `authors`, `mailmap`; the only hits are `.github/CONTRIBUTING.md`, `SECURITY.md`,
  `CITATION.cff`, `seaborn/_testing.py` and two tutorial notebooks about plot styling.

## Checkpoint 1

- [x] **Every URL uses the pinned version, not `/stable/`.** Every repository URL is under
      `blob/f04b6cd5484267a0885d1fed068e99dff3a1b226` (0.14.0.dev0). The one docs-site URL
      is `https://seaborn.pydata.org/`, fetched to assess the site and marked Exclude; no
      rule is extracted from it, so its 0.13.2 build cannot contaminate a quote. `/stable/`
      was never fetched and seaborn publishes no `/dev/` build.
- [x] **No maintainer or triage page marked Full.** Nothing at all is marked Full. The two
      rule-bearing sources are both Partial; `SECURITY.md` and `doc/whatsnew/index.rst` are
      Exclude under X-ISSUE and X-MAINT.
- [x] **Partial rows actually name their in-scope sections.** Both Partial rows name the
      in-scope section *and the specific paragraphs or clause*, and name every excluded
      section with a code.
- [x] **Config files marked `context-only`, not Partial.** `.pre-commit-config.yaml`,
      `pyproject.toml`, `Makefile` and `.github/workflows/ci.yaml` are all `context-only`
      and produce zero rows.
- [x] **Anything claimed about a file's contents was fetched.** All twelve repository files
      and the docs home page were fetched and read in full before assessment; the "sources
      that do not exist" list is derived from the complete recursive tree, which is
      recorded in the run log.
- [x] **Adversarial re-read.** The one place this manifest could leak is `README.md`, whose
      seeded role is `context`. It is promoted to `rules` on two paragraphs only, both
      quoted in the row above, and the promotion is argued from the scope test rather than
      from the file's name.

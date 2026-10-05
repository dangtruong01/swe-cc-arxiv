# sphinx-doc/sphinx — run log

Slug `sphinx-doc` (confirmed against `cases-all.txt`: `sphinx-doc__sphinx-*`).
ID prefix `SPHINX-DOC`. Final range `SPHINX-DOC-C001` – `SPHINX-DOC-C062`, contiguous.

## Phase 0 — docs root and discovery

**Docs root (pinned):** <https://www.sphinx-doc.org/en/master/>
**Version string: 9.1.1.**

How it was resolved. `seed_sources.py` printed `UNRESOLVED (could not fetch: Tunnel
connection failed: 403 Forbidden)` — this session's shell egress allowlist does not include
`www.sphinx-doc.org`, though it does include `api.github.com` and
`raw.githubusercontent.com`. The version was therefore resolved by hand, exactly as the
script would have: `GET /en/master/_static/documentation_options.js` returns
`VERSION: '9.1.1'`. Cross-checked three ways:

- `sphinx/__init__.py` on `master` reads `__version__: Final = '9.1.1'`, so the published
  master build and the tree `seed_sources.py` pulled are the same version.
- `CHANGES.rst` on `master` opens `Release 9.1.1 (in development)`, confirming `/en/master/`
  is the in-development build and not a stable snapshot.
- `/en/stable/` also serves 9.1.1 at the moment (9.1.1 is unreleased, so the two aliases
  coincide in version number only). `/stable/` was never used as a source.

Why `/en/master/` is the right root: it is Sphinx's dev build, and the repository's own
`CONTRIBUTING.rst` names `https://www.sphinx-doc.org/en/master/internals/contributing.html`
as the canonical contributing guide. There is no `/dev/` alias.

**Invocation** (no `GITHUB_TOKEN` was available in this environment; one repo, one tree call):

```
python3 rule-extraction/seed_sources.py sphinx-doc/sphinx --ref master \
    --docs https://www.sphinx-doc.org/en/master/ \
    -o rules/sphinx-doc/sphinx-doc-raw-sources.md
```

`--ref master` was passed explicitly: Sphinx's default branch is `master`, and the script's
`main` default would have gone through the zero-hit self-heal path. The tree API answered
normally — **no `tree API unavailable` and no `Falling back to probe list`**, so discovery is
tree-based and complete. `truncated` was false. 9 candidate sources, all fetched `ok`, no
`FETCH FAILED`:

`.github/ISSUE_TEMPLATE/bug-report.yml`, `.github/ISSUE_TEMPLATE/config.yml`,
`.github/ISSUE_TEMPLATE/feature_request.md`, `.github/PULL_REQUEST_TEMPLATE.md`,
`CONTRIBUTING.rst`, `README.rst`, `doc/internals/contributing.rst`, `pyproject.toml`,
`tox.ini`.

The PR template carries 4 HTML comment blocks and every one of its eight rules lives inside
them, so it was extracted from the bundle rather than from GitHub's rendered view. Sphinx has
**no `.pre-commit-config.yaml`** anywhere in the tree; that is what decides the Auto-fix
readings on C020–C022.

## Phase 1 — manifest

See `sphinx-doc-manifest.md` for the table and the Checkpoint 1 result (all five checks PASS,
three declared not-fetched files). Four sources produced rows:

| Source | Rows |
|---|---|
| `internals/contributing.html` | 35 |
| `internals/ai-policy.html` | 16 |
| `.github/PULL_REQUEST_TEMPLATE.md` | 8 |
| `internals/release-process.html` | 3 |

**Fetch method.** Each doc page was fetched twice: the rendered page at the pinned root
(assessment, headings, spot-checks) and its `.rst` source at
`raw.githubusercontent.com/sphinx-doc/sphinx/master/...` for byte-exact verbatim text. The
version match above is what licenses this; the two agree everywhere they were compared.
Nothing is asserted about a file that was not fetched.

### Zero-rule in-scope material, with reasons

- **`Contribute documentation` → sphinx-autobuild paragraph.** Offers a live-reload preview
  as an alternative to the checked build. An option, not an obligation; the checked build is
  C031.
- **`Debugging tips` (whole section, 6 bullets).** Advice for the contributor's own
  debugging (`make clean`, `--pdb`, `node.pformat()`, `keep_warnings`, `nitpicky`, docutils
  config). No obligation attaches to the diff, the commit or the files written. X-NARRATIVE.
- **`Contribute code` step 4, "Install uv and set up your environment"** (plus the pip/venv
  alternative). Environment setup, X-INSTALL. Same for step 1, "Create an account on GitHub".
- **`Getting started` step 7 commit example** (`git commit -m 'Add useful new feature that
  does this.'`). An imperative-mood example, but the page states no commit-message rule.
  Extracting one would have been inference from a sample, not extraction. Sphinx has **no
  commit-message conventions at all** — no subject-length limit, no format, no required
  prefix. That is a real difference from both calibration repos, not an omission here.
- **`CHANGES.rst`.** Fetched looking for a changelog fragment legend. There is none; the
  `* #NNNN: description. / Patch by Name` shape is observable convention that no document
  states as a rule.
- **`README.rst`.** Checked for a canonical test invocation; it has none.
- **`Deprecation policy` → the Sphinx 2.x/3.x/4.0 worked example.** Illustration of C062,
  produces nothing of its own.

## Phase 2 — extraction

Frozen at `sphinx-doc-extraction-frozen.csv`, 62 rows, 9 Part-2 columns including
`Naive strength`. **Not edited after freezing.** Classification was authored separately and
joined to it by ID.

Closing report: IDs `SPHINX-DOC-C001`–`C062`, contiguous, no repeats. `Section context` and
`Notes` populated on all 62 rows. Naive strength: `must` 38, `maybe` 16, `prohibited` 8.

Exact-duplicate `Original text` values, all of them declared atom splits of one bundled
sentence (the workflow requires splitting these; the verbatim column is shared by design):

| Text | IDs |
|---|---|
| "When adding a new configuration variable, be sure to document it and update sphinx/cmd/quickstart.py if it's important enough." | C017, C018 |
| "Style and type checks can be run as follows: uv run ruff check / uv run ruff format / uv run mypy" | C020, C021, C022 |
| "In explaining your contribution, do not use AI to automatically generate comments, pull request descriptions, or issue descriptions." | C039, C040 |
| "If so, you must document which tool(s) have been used, how they were used, and specify what code or text is AI generated." | C042, C043 |

### Checkpoint 2

| Check | Result |
|---|---|
| Row count plausible | PASS — 62 rows over ~3.2k words of in-scope prose = 19.4 rules/1k. Higher than expected (§3 anticipated 30–50); see the note under check 8 below. No single page produced 100+ rows; the largest is 35. |
| Section context and Notes on every row | PASS — 0 blanks of 62. |
| IDs contiguous | PASS. |
| Every `Source` starts with `http` | PASS — 54 doc-page URLs, 8 `github.com/.../blob/master/` for the PR template. |
| Every `Shared Category` one of the eight | PASS — all eight buckets used; `Language and framework style` holds exactly 1 row. |
| Verbatim quotes not starting mid-sentence | PASS — C018 and C043 begin mid-sentence by construction (second atom of a split); both carry the full sentence in `Original text`, and the preceding clause is what supplies their scope. |

**Five `Original text` values spot-checked against the live rendered page**
(<https://www.sphinx-doc.org/en/master/internals/contributing.html>), all exact:

| ID | Text checked |
|---|---|
| C012 | "For non-trivial changes, please update the CHANGES.rst file." |
| C017 | "When adding a new configuration variable, be sure to document it and update sphinx/cmd/quickstart.py if it's important enough." |
| C026 | "For bug fixes, first add a test that fails without your changes and passes after they are applied." |
| C028 | "Tests should be quick and only test the relevant components, as we aim that *the test suite should not take more than a minute to run*." |
| C010 | "You may be asked to address comments on the review. If so, please avoid force pushing to the branch." |

The Disclosure and AI Agents sections of `ai-policy.html` and the
"Thus, when adding a RemovedInSphinxXXWarning…" sentence of `release-process.html` were
additionally verified against their rendered pages.

## Phase 3 — classification

**Conflict tiebreaker, fixed before batch 1 (the project default):** the stricter statement
governs; the weaker one is `N3 not prioritized, duplicate` with the conflict named in `Notes`.
Batches of 25 across the whole sheet, not per page — which is how C054 (PR template) and C012
(contributing page) were caught as restatements of C005.

Every conflict it resolved:

| Weaker row | Governed by | Obligation |
|---|---|---|
| C012 | C005 | CHANGES.rst entry — C012 drops C005's parenthesised definition of "trivial". |
| C054 | C005 | CHANGES.rst entry — a third statement, triggered on "user-visible" rather than "not trivial". Nothing in the docs reconciles the two triggers; the tiebreaker picks the stricter and names the mismatch in C054's `Context`. |
| C019 | C004 | Adding tests — "Add appropriate unit tests" adds only a hedge to C004. |
| C038 | C037 | Understanding your own patch — negative restatement in the same paragraph. **N2 fired first** (it is a quality call with no pass condition), so the cell reads N2 and the residual N3 is named in the `Conclusion`, per the rubric's literal ordering. |
| C057 | C041 | AI disclosure — the template restates the policy one surface lower. |
| C058 | C041 | AI disclosure, negative branch ("No AI tools used"). |
| C059 | C050 | Human submission — the template's broader, vaguer form of the AI Agents prohibition. |

Ordering notes worth recording, since both are the misclassifications the rubrics warn about:

- **N1 before N2 was applied literally.** C016 ("include a sample that is displayed in the
  generated output") reads as an N2 hedge, but built documentation is not among the artifacts
  the run produces, so N1 fires and N2 is recorded as the residual route. This is the one row
  carrying `low_confidence`.
- **N1 vs N4.** C047 (own the copyright, or ship the licence) and C055 (add yourself to
  AUTHORS.rst) are the two N4s. Both govern artifacts that exist — the patch, and a tracked
  file — and turn on facts outside the agent's own behaviour (provenance, contributor
  history). C055 is Sphinx's exact analogue of Django C067.
- **AI disclosure is Care, not N1**, per the care rubric's explicit ruling: whether the agent
  used AI is inside its own behaviour and the trajectory shows it. C041–C043 are therefore
  `always fails` rather than "no PR object". C040 (AI-generated *PR and issue descriptions*)
  stays N1, because those prose objects genuinely do not exist.

Guesses, cross-referenced: exactly one row carries `low_confidence:` — **C016**, on the N1/N2
split described above. **C062** carries a `low_confidence` note of a different kind: the
deprecation-removal window is stated as a description of project policy rather than as an
instruction, and the contributor-facing obligation was read out of it.

## Phase 4 — workbook

`sphinx-doc-rules.xlsx`: three tabs, 11 columns in order, django's header fill
(`FF2F4858`) and bold white font, frozen at `A2`, autofilter `A1:K63`, body rows top-aligned
and wrapped, django's column widths. `repo.conf` written on the django model.

The `Shared Taxonomy (Before-After)` django columns were computed from
`rules/django/django-rules.xlsx` directly at build time (143 / 89, matching), not copied.

Two deliberate divergences from django's file, both reported rather than decided unilaterally:

1. In `Category Aggregation` the category column reads **`Language and framework style`**,
   where django's aggregation tab reads `Language/Framework style`. Django's *Rules* tab uses
   the correct spelling; only its aggregation tab has the slashed form. Consistency with the
   taxonomy was preferred over byte-fidelity to a cell the code never reads.
2. The last aggregation column keeps django's and the workflow's header **`Should (Care)`**,
   even though the values it counts are `maybe`. Renaming it is not covered by §2 of the
   agent prompt and it is a header, not a `Strength` cell. Flagged for the amendment pass.

## Phase 5 — audit

`tools/audit_rules.py` was written for this run (it did not exist). Calibrated on
`--repo django` first. See the report for the calibration discrepancy: django fails **three**
checks, not the two the prompt predicts.

```

  audit: sphinx-doc-rules.xlsx  (62 rows)

  1  Gate (tools/corpus.py)  PASS  tools/corpus.py exits 0
  2  Schema and vocabulary   PASS  11 columns in order; vocabulary, blanks and taxonomy clean
  2b ID prefix               PASS  all 62 IDs match ^SPHINX\-DOC-C\d{3}$
  3  Judgment invariant      PASS  0 judgment+Care rows (12 judgment rows, all Not Care)
  4  NaiveStrength present   PASS  NaiveStrength on 100% of 62 rows
                                   NaiveStrength != Strength on 9 of 27 Care rows: {'maybe -> must': 6, 'prohibited -> must': 3}
  5  Promotion direction     PASS  promotions maybe->must: 6; demotions must->maybe: 0; prohibited->must folds: 3; unchanged: 18
  6  Reasoning uniqueness    PASS  62 distinct Conclusion values; 62/62 rows carry a Conclusion:
  7  N1 vs N2-N4 balance     PASS  N1 15 | N2 12 | N3 6 | N4 2  (N1 vs N2-N4: 15/20)
  8  Row-count plausibility  PASS  62 rows over 3200 words = 19.4 rules/1k words (order-of-magnitude band 3.0-40.0)
  9  ID contiguity           PASS  C001-C062, no gaps, no repeats

  10/10 checks pass

```

Check 8 note: 62 rows over ~3.2k words is 19.4 rules/1k, roughly double Django's density.
The cause is atomicity, not catalogue inflation — Sphinx's prose bundles obligations into
single sentences far more than Django's does (one sentence carries three lint tools, another
three AI-generation targets, another three disclosure facts), and the workflow requires those
to be split. No single page produced more than 35 rows and no row restates an interface
member. The count is above the 30–50 the prompt anticipated but well inside an
order of magnitude.

Check 5 note: 6 promotions `maybe -> must`, **0 demotions**, 3 `prohibited -> must` folds,
18 unchanged. One-directional, the same shape Django ran. The promotions are all the same
mechanism — Sphinx states mechanical obligations in flat descriptive prose ("Style and type
checks can be run as follows", "New unit tests should be included in the tests/ directory")
while a named CI job or an exact path makes them conditions of acceptance. That is the rubric
behaving as designed on this repo's register, not classification drift.

No git command was run at any point. Nothing outside `rules/sphinx-doc/` and
`tools/audit_rules.py` was written.

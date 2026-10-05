# matplotlib/matplotlib — rule extraction run log

Slug `matplotlib`, ID prefix `MATPLOTLIB`, IDs `MATPLOTLIB-C001`–`MATPLOTLIB-C293`.
Slug confirmed against `cases-all.txt` (`matplotlib__` prefix, 34 instances).

## Phase 0 — docs root and version

Docs root: **`https://matplotlib.org/devdocs/devel/`**. `/devdocs/` is matplotlib's dev
build; `/stable/` was never fetched.

`seed_sources.py --docs` printed `UNRESOLVED (could not fetch: Tunnel connection failed:
403 Forbidden)` — the device's egress allowlist blocks `matplotlib.org`, which §4.1 records
as expected and not a stop condition.

**Resolved by hand:** fetched `https://matplotlib.org/devdocs/devel/index.html` from the
container (which has proxy egress) and read the version string off the rendered page:
**`3.12.0.dev534+g374b2da71`**. The string embeds the build commit, `g374b2da71`. Independently,
`api.github.com/repos/matplotlib/matplotlib/commits/main` returned
`374b2da71ccbfeb9edc955a2420180fed58364d3` (committed 2026-09-01T09:09:30Z) at the same
moment. The rendered docs and the raw `.rst` are therefore the same build, which is a
tighter pin than §4.1's build-granularity floor requires. No `VERSION MISMATCH`.

A second live fetch (`style_guide.html`) later re-reported the same version string, so the
docs alias did not roll mid-run.

Because the device cannot reach `matplotlib.org`, page bodies were read as the `.rst`
sources pinned to `374b2da7`, downloaded from `raw.githubusercontent.com`. `Source` cells
cite the rendered `devdocs` URL, which is what a contributor and the retrieval arm read.

## Phase 0 — seed_sources.py

```
python3 rule-extraction/seed_sources.py matplotlib/matplotlib \
    --docs https://matplotlib.org/devdocs/ \
    -o rules/matplotlib/matplotlib-raw-sources.md
```

`--ref` left at the default `main`, which is matplotlib's default branch; no `master`
retry was triggered. **No token was used and none was needed** — the tree API answered
normally. There was no `tree API unavailable` line and no `Falling back to probe list`
line, and the 13 files found are not the `PROBE` list (the probe would have missed
`.github/ISSUE_TEMPLATE/documentation.yml`, `maintenance.yml` and `tag_proposal.yml`, and
would have probed for paths that do not exist here). Discovery is genuine tree discovery.

13 candidate sources, 0 FETCH FAILED:
`.github/CONTRIBUTING.md`, six `.github/ISSUE_TEMPLATE/*.yml`,
`.github/PULL_REQUEST_TEMPLATE.md` (7 HTML comment blocks — the obligations are in them),
`.pre-commit-config.yaml`, `CODE_OF_CONDUCT.md`, `README.md`, `pyproject.toml`, `tox.ini`.

`seed_sources.py`'s `PATTERNS` do not match `doc/devel/*.rst`, so the 19 devdocs pages were
enumerated from the rendered nav and pulled at the pinned SHA. Both changelog READMEs
(`doc/api/next_api_changes/README.rst`, `doc/release/next_whats_new/README.rst`) were pulled
too: they are `.. include::`d into `api_changes.rst` and so render as part of that page.

## Prompt-injection check

Astropy's PR template carried an injection canary aimed at agents. **Matplotlib's does
not.** All seven HTML comment blocks in `.github/PULL_REQUEST_TEMPLATE.md` were read in
full; they contain author instructions and two documentation links, no agent-directed text.
The six issue templates and `.github/CONTRIBUTING.md` were also read and are clean. Nothing
in any fetched page was treated as an instruction to this agent.

## Phase 1 — manifest

See `matplotlib-manifest.md` for the table and the Checkpoint 1 result. 28 manifest rows:
14 producing rules, 5 `context-only`, 9 `Exclude`.

Two amendments were made at Checkpoint 1 and are recorded there: `min_dep_policy` Full →
Partial (its support windows are project commitments, not obligations on a diff), and
`development_setup` Exclude → Partial (the `Install pre-commit hooks` section states a real
obligation about re-staging hook-modified files).

## Phase 2 — extraction

Sources worked one at a time, largest first, the manifest row restated before each:

| # | Source | Rows |
|---|---|---|
| 1 | `document.html` | 75 |
| 2 | `development_workflow.html` | 22 |
| 3 | `contribute.html` | 18 |
| 4 | `style_guide.html` | 27 |
| 5 | `pr_guide.html` | 23 |
| 6 | `testing.html` | 23 |
| 7 | `api_changes.html` (incl. both included READMEs) | 46 |
| 8 | `coding_guide.html` | 27 |
| 9 | `license.html` | 4 |
| 10 | `.github/PULL_REQUEST_TEMPLATE.md` | 10 |
| 11 | `tag_guidelines.html` | 8 |
| 12 | `min_dep_policy.html` | 6 |
| 13 | `development_setup.html` | 3 |
| 14 | `index.html` | 1 |

Frozen at `matplotlib-extraction-frozen.csv` (293 rows, 9 working columns including
`Naive strength`) **before any classification**, and not edited since.

### Zero-rule in-scope sources

- **`.github/CONTRIBUTING.md`** — one sentence, a bare redirect to the contributing guide.
  Marked `rules` by `seed_sources.py`, excluded `X-NARRATIVE`. No obligation to extract.
- **`tag_glossary.html`** — `context-only`. It defines the closed tag vocabulary, which is
  what makes MATPLOTLIB-C277 ("at least one content tag") decidable rather than a judgment
  call, but it states no obligation of its own.
- **`.pre-commit-config.yaml`, `pyproject.toml`, `tox.ini`, `README.md`** — `context-only`.
  The pre-commit config decided every `Auto-fix risk` reading on the sheet; the other three
  were consulted and produced nothing.
- **`document.html` § `Build the docs`, `Build options`, `Show locally built docs`** — read
  in full for section context, produced no rows: build invocations, `X-INSTALL`.
- **`testing.html` § `CI with GitHub Actions`** — read in full, produced no rows: it
  describes how hosted CI is wired, and states no obligation on a contribution.

### Checkpoint 2

- [x] **Row count plausible.** 293 against django's 143, sympy's 279, astropy's 255.
  Density is checked below.
- [x] **IDs contiguous**, C001–C293, no gaps or repeats (asserted in `freeze.py`).
- [x] **Every `Source` starts with `http`** (asserted).
- [x] **Every `Shared Category` is one of the eight** (asserted).
- [~] **Section context and Notes populated on every row.** `Section context` is populated
  on 293/293. The extraction `Notes` column is populated on 163/293. Its Part 2 spec is
  "trigger conditions, cross-references", and 130 rules are unconditional and cross-
  reference nothing; writing filler there would be exactly the boilerplate this workflow
  bans elsewhere. Recorded as a deviation rather than papered over. The deliverable
  workbook's `Notes` column is populated on 293/293.
- [x] **Exact-duplicate `Original text` values:** 1, deliberate. `MATPLOTLIB-C266` and
  `MATPLOTLIB-C267` are two obligations carried by one HTML comment in the PR template
  ("Describe what issue is resolved and why you chose this solution in your own words
  (no AI please)").
- [x] **Five `Original text` spot-checks**, all matched:
  - `MATPLOTLIB-C001` (document, preamble) — matched `doc/devel/document.rst` @374b2da7
  - `MATPLOTLIB-C085` (development_workflow, Verify your changes) — matched
  - `MATPLOTLIB-C131` (style_guide, Voice) — matched, **and confirmed verbatim against the
    live rendered `style_guide.html`**
  - `MATPLOTLIB-C199` (api_changes, colormaps) — matched
  - `MATPLOTLIB-C245` (coding_guide, C/C++ extensions) — matched

  `MATPLOTLIB-C142` was additionally confirmed verbatim against the live rendered page in
  the same fetch, because it is the governing side of the one intra-repo conflict.
- [x] **Quotes starting mid-sentence** were re-opened to the preceding clause where the
  scope lived; e.g. C049's "sgskip" rule carries "In the Python files, to exclude an
  example from having a plot generated", not the bare filename clause.

### API-contract handling

`document.html` § `Setters and getters` and `API documentation` are interface specs, and
`api_changes.html` § `Introduce deprecation` lists six `_api` deprecation helpers. Neither
produced one row per member:

- the six deprecation helpers are **one** conformance row (`MATPLOTLIB-C207`, "use the
  matching helper for the kind of API being deprecated"), not six;
- Artist setters/getters are **two** rows (naming convention C044, accepted-values
  documentation C045), not one per property;
- the numpydoc parameter-type conventions are extracted as the eight rules matplotlib adds
  *on top of* numpydoc, plus one pointer rule at numpydoc itself (C023) — not an inventory
  of numpydoc.

## Phase 3 — classification

**Conflict tiebreaker, fixed before classification started:** the stricter statement
governs; the weaker one is `N3 not prioritized, duplicate` with the conflict named in
`Notes`. Three conflicts were resolved under it:

| Weaker (→ N3) | Stricter (governs) | The conflict |
|---|---|---|
| `MATPLOTLIB-C005` | `MATPLOTLIB-C142` | `document.html`'s table-format matrix routes large tables with long entries to a **csv table**; `style_guide.html` says "Markdown tables and the csv-table directive are not accepted". The ban is stricter. |
| `MATPLOTLIB-C143` | `MATPLOTLIB-C271` | `pr_guide.html` says changes "should have good test coverage"; the PR template checklist says "New and changed code is tested", unhedged. |
| `MATPLOTLIB-C146` | `MATPLOTLIB-C272` | `pr_guide.html` says "consider adding a small example"; the PR template checklist says "Plotting related features are demonstrated in an example", unhedged. |

Classified in batches of 25 across the whole sheet, in the fixed order `CheckTier` → `Care`
→ `PassType` → `Strength` → `DecidedBy` → reasoning → auto-fix.

Two corrections were made after the first pass and are visible in `build.py`:
`MATPLOTLIB-C005` and `MATPLOTLIB-C024` were first tiered `judgment` while being routed N3;
the tier was wrong (what a check would open there is the `.rst` source, so `static`), and
carrying `judgment` on a non-N2 row would have muddied the invariant. `MATPLOTLIB-C293`
went the other way: it *is* a judgment call, and Rubric A's ordering is literal, so N2 fires
before the N3 duplicate reading — it is now N2 with `judgment`.

`Auto-fix risk` was decided from `.pre-commit-config.yaml` at the pinned SHA, not from what
the tools can do in general. Seven rows carry a reading: `ruff-check` runs with `--fix`
(C235 auto-fixed; C236 partial, because ruff does not rewrap long lines), the whole hook set
is mixed (C152 partial), the hooks rewriting files is what creates C291's obligation, and
`name-tests-test`, `mypy` and `no-commit-to-branch` are check-only (C168, C242, C076).
`ci.autofix_prs: false`, so nothing is fixed for the contributor after the fact.

## Phase 4 — workbook

`matplotlib-rules.xlsx`, three tabs, 11 columns in order, header in django's
`FF2F4858` fill with white bold text, body top-aligned and wrapped, frozen at `A2`,
autofilter `A1:K294`, widths `A14 B30 C46 D60 E11 F26 G10 H12 I8 J18 K95`.
`Category Aggregation`'s last header is **`Maybe (Care)`**, with `DecidedBy` and `PassType`
blocks below the table. `Shared Taxonomy (Before-After)`'s django columns were computed by
reading `rules/django/django-rules.xlsx` directly in `xlsx.py` (143 rows / 89 Care, which
reproduces django's own totals), not copied from any earlier sheet.

`repo.conf` written with `DISPLAY_NAME`, `DOCS_URL`, `CORPUS`, `REPO_URL`.
`rules/build_contributing_rules.py --repo matplotlib` renders 167 rules across the eight
categories without an unknown-category error. **`RULE_MODULES` was not touched** — this run
produces a corpus, not a pack.

## Phase 5 — audit

`tools/audit_rules.py` was calibrated on `--repo django` first: it failed exactly the three
known checks (2 vocabulary — 11 `should` rows; 4 `NaiveStrength` — 0/143; 6 reasoning
uniqueness — 49/143 rows carry a `Conclusion:` and one string is duplicated) and passed the
other seven. No check was modified.

```
  audit: matplotlib-rules.xlsx  (293 rows)

  1  Gate (tools/corpus.py)  PASS  tools/corpus.py exits 0
  2  Schema and vocabulary   PASS  11 columns in order; vocabulary, blanks and taxonomy clean
  2b ID prefix               PASS  all 293 IDs match ^MATPLOTLIB-C\d{3}$
  3  Judgment invariant      PASS  0 judgment+Care rows (28 judgment rows, all Not Care)
  4  NaiveStrength present   PASS  NaiveStrength on 100% of 293 rows
                                   NaiveStrength != Strength on 31 of 199 Care rows: {'prohibited -> must': 17, 'maybe -> must': 5, 'must -> maybe': 9}
  5  Promotion direction     PASS  promotions maybe->must: 5; demotions must->maybe: 9; prohibited->must folds: 17; unchanged: 168
  6  Reasoning uniqueness    PASS  293 distinct Conclusion values; 293/293 rows carry a Conclusion:
  7  N1 vs N2-N4 balance     PASS  N1 39 | N2 28 | N3 21 | N4 6  (N1 vs N2-N4: 39/55)
  8  Row-count plausibility  PASS  293 rows over 32502 words = 9.0 rules/1k words (order-of-magnitude band 3.0-40.0)
  9  ID contiguity           PASS  C001-C293, no gaps, no repeats

  10/10 checks pass
```

**Check 5, promotion direction.** Not one-directional, unlike django. 17 `prohibited → must`
folds are the rubric working as designed (M2). Of the genuine moves, 5 are promotions
(`maybe → must`) and **9 are demotions** (`must → maybe`). I read the demotions as the
rubric behaving differently on this prose rather than as classification drift: every one of
the nine is a flat imperative whose surrounding section then grants the deviation, which is
route D2 doing exactly its job — "When feasible, please use our internal variable naming
convention" (C240), "Only create as many as you need... and reuse them if possible" (C179),
"Assert values rather than visual results when feasible" (C180), "We generally use stub
files... A notable exception is `pyplot.py`" (C243). Matplotlib writes its rules as
imperatives and its exceptions as the following sentence, so the naive modal read is
systematically stricter than the read-the-whole-section answer. Django's prose hedges
in-clause, which is why it never demoted.

**Check 7, N1 vs N2–N4: 39 / 55.** Larger than django's 30/24 in absolute terms but a
smaller *share* (41% of Not Care against django's 56%). N1 is not swallowing N4: the 39 N1
rows are concentrated in `pr_guide.html` and the git half of `development_workflow.html`,
where the governed artifact (a PR object, a review thread, branch history, hosted CI) is
absent outright. The 6 N4 rows were each checked against the N1/N4 test and turn on a fact
outside the agent's behaviour that would be readable if it were present — a good-first-issue
label (C108), first-contribution status (C111), the PR number in a filename (C227), the
release type (C285), the introducing release (C201), other projects (C106).

**Check 8, density.** 293 rows over the 32,502 words of `doc/devel/` is 9.0/1k. Over the
25,903 words of the fifteen rule-bearing files actually extracted from (plus ~200 for the PR
template) it is **11.2 rules per 1k words**, which sits at the bottom of the 11–19 band and
just above astropy's 8.4. §3's 49.0k figure is larger than anything I can reproduce from
this tree: `doc/devel/` totals 32.5k words including the excluded release, triage,
communication and MEP material. Against 49.0k the figure would be 6.0/1k. Flagged below.

## Guessed / low-confidence rows

Four rows carry `low_confidence:` in `Notes`:

- **`MATPLOTLIB-C076`** (do not commit to your local `main`) — read as `always fails`, on
  the assumption the harness commits on the checked-out default branch. A detached HEAD
  would make it `never fires` instead. This is the one row where I departed from django's
  reading of a branch rule as N1: the Care rubric names "branch hygiene" as its own example
  of `always fails`, and unlike django's C094 this rule needs only `HEAD`, not history.
- **`MATPLOTLIB-C108`** (no AI-generated PR against a good first issue) — N4 because
  SWE-bench instances carry no issue labels. If labels were surfaced it would be Care with
  `always fails`.
- **`MATPLOTLIB-C245`** (PEP7 for C/C++) — graded `must` as an external-standard pointer,
  consistent with C023 (numpydoc) and C235 (PEP8), but only part of PEP7 is mechanically
  decidable.
- **`MATPLOTLIB-C265`** (state the license when using non-BSD code in a toolkit) — "Matplotlib
  toolkits (e.g., basemap)" may mean in-repo `mpl_toolkits` or an external project; read here
  as in-repo, which is what makes it Care.

## Flags on the brief

1. **Word count.** §3 gives matplotlib 49.0k words. The whole of `doc/devel/` at the pinned
   commit is 32,502, and the in-scope subset is 25,903. The prompt's "roughly 490 rules
   estimated" is derived from the 49.0k figure; at the atomicity astropy and django were
   extracted at, this corpus does not contain 490 rules. Reported at both denominators
   rather than inflating to hit the estimate.
2. **`--token` is mandatory (§4 Phase 0).** No token was available in this environment. The
   unauthenticated tree API answered without rate-limiting and returned genuine tree
   discovery, not the probe fallback, so the stop condition in §8 did not fire. Recorded
   because the prompt says the flag is mandatory.
3. **Checkpoint 2 wording.** "Section context and Notes populated on every row" cannot be
   satisfied for the extraction `Notes` column without writing filler on unconditional
   rules, which §3's boilerplate rule forbids. Resolved in favour of the boilerplate rule
   and recorded above.

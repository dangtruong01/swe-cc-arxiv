# psf/requests — run log

Slug `psf`, ID prefix `PSF`. The slug is the SWE-bench instance prefix, confirmed against
`cases-all.txt` (`psf__requests-1142`, `-1724`, `-1766`, `-1921`, `-2317`, `-2931`,
`-5414`, `-6028`; 8 instances). Not `requests`.

## Docs root and version

- Docs root: `https://requests.readthedocs.io/en/latest/`
- Version string served: **Requests 2.34.2**
- How it was resolved: `seed_sources.py --docs` printed
  `UNRESOLVED (could not fetch: <urlopen error Tunnel connection failed: 403 Forbidden>)`.
  This is the expected §4.1 case: the device's egress allowlist blocks the documentation
  host, so `_static/documentation_options.js` is unreachable from the machine that runs the
  script. The version was resolved by hand from the `<title>` of every page fetched, each
  of which reads `... — Requests 2.34.2 documentation`. All 14 documentation pages fetched
  reported 2.34.2, so there is no version drift and no `VERSION MISMATCH`.
- Why `/latest/` and not a pinned slug: Read the Docs serves this project as
  `/en/latest/` (built from `main`) and `/en/stable/` (a moving alias, forbidden by §0.2).
  There is no per-release version slug: `https://requests.readthedocs.io/en/v2.34.2/dev/contributing/`
  returns 404, so no pinned alternative to `/latest/` exists. This is the astropy situation
  from §4.1 — `/latest/` plus a hand-resolved version string — not a stop condition.
  Version pinning here is at build granularity: every page assessed came from the same
  2.34.2 build, and the `.rst` sources were pulled at `main` in the same session.

## seed_sources.py

```
python3 rule-extraction/seed_sources.py psf/requests \
    --docs https://requests.readthedocs.io/en/latest/ \
    -o rules/psf/psf-raw-sources.md
```

- `--ref`: default `main`, which is psf/requests' actual default branch. No self-heal to
  `master` was triggered; discovery returned 9 files on the first attempt.
- No `--token`. The tree API answered normally: the output shows `Found: 9 candidate
  sources` from a real recursive tree walk, with no `tree API unavailable` and no
  `Falling back to probe list` on stderr. The §8 stop condition did not fire. The
  discovery was later cross-checked against a direct recursive tree listing (one further
  API call), which confirmed the 9 files and surfaced the ones the patterns miss.
- Files found: `.github/CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/Bug_report.md`,
  `.github/ISSUE_TEMPLATE/Custom.md`, `.github/ISSUE_TEMPLATE/Feature_request.md`,
  `.pre-commit-config.yaml`, `README.md`, `docs/dev/contributing.rst`, `pyproject.toml`,
  `tox.ini`. No FETCH FAILED.
- **Gap in `PATTERNS`, closed by hand.** `seed_sources.py` has no pattern for an AI policy
  file, so `.github/AI_POLICY.md` — 685 words and the single densest rule source in this
  repo, 17 of the 41 rows — was not in the bundle. It was found by following the one-hop
  link in `.github/CONTRIBUTING.md` ("please read our Contributor's Guide as well as our
  AI Policy") and fetched raw from
  `https://raw.githubusercontent.com/psf/requests/main/.github/AI_POLICY.md`. The recursive
  tree listing was then read in full to confirm nothing else was missing; that is how
  `.github/SECURITY.md`, `.github/CODE_OF_CONDUCT.md`, `.github/ISSUE_TEMPLATE.md`,
  `.github/CODEOWNERS`, `Makefile` and the three workflow files entered the manifest. All
  of them were fetched raw before being assessed. Worth reporting upstream: sphinx-doc's
  AI policy was a docs page, requests' is an off-nav repo file, and the pattern list
  catches neither.
- Duplicate risk: `docs/dev/contributing.rst` is the source of the rendered
  Contributor's Guide page. Extraction was done **once**, from the rendered page, so every
  `Source` for those rows is the readthedocs URL. `Original text` is therefore the rendered
  wording: line wrapping is unwrapped and reStructuredText inline roles are resolved
  (`` `.pre-commit-config.yaml`_ `` reads as `.pre-commit-config.yaml`, ``` ``'hello'` ``` as
  `'hello'`). The `.rst` in the bundle was used only to confirm the quotes, never as a
  second extraction pass.

## ID prefix and range

`PSF-C001` … `PSF-C041`. Sequential across the whole repo, never restarting per page.
Contiguous, no gaps, no repeats (audit check 9).

## Conflict tiebreaker

Fixed before classification, and identical to the central ruling: **the stricter statement
governs; the weaker one is N3 with the conflict named in `Notes`.** requests exercised it
five times, which is unusually high for 41 rows because two of its three sources are
restatements of the third.

| Weaker / duplicate row | Governing row | What the tiebreaker decided |
|---|---|---|
| PSF-C022 `.github/CONTRIBUTING.md` "always include tests that fail without your changes" | PSF-C004 + PSF-C005 | Same obligation as the guide's checklist steps 3 and 5, at the same strength; the guide splits it into two readable states, so the restatement adds no check. |
| PSF-C023 `.github/CONTRIBUTING.md` "Always run the test suite locally" | PSF-C006 | The guide's step 5 additionally requires the run to be *entire* and to *pass including the new tests*, so it is strictly stronger. |
| PSF-C030 AI policy certification "hold the copyright **or** have explicit legal authorization" | PSF-C025 | A genuine strength conflict, not just a restatement: the CAUTION headline demands a human who *unequivocally owns* the copyright, the certification list opens a disjunct. Stricter governs. |
| PSF-C033 AI policy Summary "PRs with an LLM product as co-author can't be merged" | PSF-C026 | Identical trailer state, consequence added. |
| PSF-C034 AI policy Summary "you must remove any LLM co-author tags" | PSF-C026 | Same trailer state seen from the other side. This row is kept rather than dropped because it carries the file's only *permission* — LLM-assisted work may still be submitted once the tags are gone — which would be lost if the duplicate were silently omitted. |

## Checkpoint 1

Recorded in full at the foot of `psf-manifest.md`; all five boxes pass. The two that
historically leak were checked adversarially: nothing is marked `Full` (both rule-bearing
sources are `Partial`, because both mix contribution rules with issue-tracker rules), and
every `Partial` row names its in-scope headings *and* its excluded ones with a code each.
`release-process`, `SECURITY.md` and `CODEOWNERS` are the maintainer material and all three
are `Exclude`.

## Checkpoint 2

- Row count plausible: 41 rows over roughly 1,540 in-scope words (contribution prose totals
  2,194 words across the three sources; the excluded Code of Conduct, Contribution
  Suitability, Bug Reports, Questions, Good Bug Reports and Credits sections account for the
  difference) = 26.6 rules/1k words. Django and SymPy sit inside the same band. No single
  page produced anything near 100 rows; the largest source, the Contributor's Guide, gave 19.
- Section context and Notes populated on all 41 rows, not just some.
- IDs contiguous: `PSF-C001`–`PSF-C041`.
- Every `Source` starts with `http`.
- Every `Shared Category` is one of the eight, spelled `Language and framework style`.
- Exact-duplicate `Original text` across all sources: **none**. PSF-C004 and PSF-C005 come
  from one numbered checklist step but quote its two sentences separately, with the
  preceding clause carried in `Section context` per the mid-sentence-quote rule.
- **Five spot-checks of `Original text` against the source**, all found byte-for-byte after
  unwrapping the line breaks: `PSF-C006`, `PSF-C011`, `PSF-C016`, `PSF-C018` (all against
  `docs/dev/contributing.rst` at `main`, cross-read against the rendered 2.34.2 page) and
  `PSF-C024` (against `.github/CONTRIBUTING.md`). A sixth, `PSF-C028`, was checked against
  `.github/AI_POLICY.md` because that file was not in the seeded bundle.

## Zero-rule in-scope sources

Reported explicitly so that a source which produced nothing is distinguishable from one
that was forgotten.

| In-scope source or section | Rows | Reason |
|---|---|---|
| Contributor's Guide → Contribution Suitability | 0 | States what the maintainers decide ("Our project maintainers have the last word"). No obligation falls on the contributor, so nothing meets the rule definition. |
| Contributor's Guide → New Contributors | 0 | Welcome text; its only imperative, "please consider mailing a maintainer", is advice about asking for help, not about creating or submitting a contribution. |
| Contributor's Guide → Code Contributions, step 4 ("Make your change") | 0 | A checklist placeholder with no obligation content. Emitting a row for it would be cataloguing the list rather than extracting rules. |
| Contributor's Guide → Code Contributions, step 6 second sentence ("GitHub Pull Requests are the expected method of code collaboration") | 0 | Restates the preceding step; folded into PSF-C007's `Section context` rather than duplicated. |
| AI policy → Legal | 0 | Explains why the boundaries exist (no CLA, unsettled copyright status). Quoted as `Section context` on PSF-C025 and PSF-C032; states no obligation of its own. |
| AI policy → Human | 0 | Rationale and a maintainer-side statement ("we have to manually review every change before merging"). The one contributor-facing sentence, "by opening low-quality pull requests you're not helping anyone", is an admonition already carried by PSF-C027 and PSF-C038. |
| `.pre-commit-config.yaml`, `pyproject.toml`, `tox.ini`, `README.md`, `Makefile`, the three workflow files | 0 | `context-only` by role. They decide the auto-fix reading (PSF-C011), the M3 reading of the Code Style rule, the single-quote scope question (PSF-C018) and the line-length reading (PSF-C016), but a config file produces no rows. |
| Changelog / news fragments | 0 | The source does not exist. There is no `newsfragments/`, `changelog.d/`, `doc*/whats_new/` or towncrier config anywhere in the tree, and no document instructs a contributor to touch `HISTORY.md`. requests is the first repo in this study with no changelog obligation at all. |
| Pull request template | 0 | The source does not exist. `.github/` has neither `PULL_REQUEST_TEMPLATE.md` nor a `PULL_REQUEST_TEMPLATE/` directory, verified against the full recursive tree rather than a probe. |

## Prompt-injection check (§8 / §4.1)

Both rule-bearing repository files were read as raw source with comments intact, and the
AI policy in particular was read line by line looking for the astropy-style canary. **None
was found.** `.github/AI_POLICY.md` is addressed to human contributors who use LLM tools,
not to an agent reading the file, and its imperatives ("Absolutely no unsupervised agentic
tools like OpenClaw", "remove any LLM co-author tags") are project policy — material to
extract rules *from*, and they were extracted as PSF-C028 and PSF-C034. Nothing in any
fetched page or raw source was treated as an instruction to this run. The four issue
templates carry only section-label HTML comments.

## Audit output (§7)

`python3 tools/audit_rules.py --repo psf --words 1540`

```
  audit: psf-rules.xlsx  (41 rows)

  1  Gate (tools/corpus.py)  PASS  tools/corpus.py exits 0
  2  Schema and vocabulary   PASS  11 columns in order; vocabulary, blanks and taxonomy clean
  2b ID prefix               PASS  all 41 IDs match ^PSF-C\d{3}$
  3  Judgment invariant      PASS  0 judgment+Care rows (6 judgment rows, all Not Care)
  4  NaiveStrength present   PASS  NaiveStrength on 100% of 41 rows
                                   NaiveStrength != Strength on 5 of 15 Care rows: {'maybe -> must': 3, 'prohibited -> must': 2}
  5  Promotion direction     PASS  promotions maybe->must: 3; demotions must->maybe: 0; prohibited->must folds: 2; unchanged: 10
  6  Reasoning uniqueness    PASS  41 distinct Conclusion values; 41/41 rows carry a Conclusion:
  7  N1 vs N2-N4 balance     PASS  N1 15 | N2 6 | N3 5 | N4 0  (N1 vs N2-N4: 15/11)
  8  Row-count plausibility  PASS  41 rows over 1540 words = 26.6 rules/1k words (order-of-magnitude band 3.0-40.0)
  9  ID contiguity           PASS  C001-C041, no gaps, no repeats

  10/10 checks pass
```

The checker was calibrated on `--repo django` first and failed there on exactly the three
known checks — check 2 (11 `should` rows), check 4 (0/143 `NaiveStrength`) and check 6
(1 duplicated `Conclusion`, 49/143 coverage) — passing the other seven. Nothing in
`tools/audit_rules.py` was modified, and neither the django nor the sympy workbook was
touched.

Notes on two reported figures:

- **Check 5, promotion direction.** One-directional, like django: 3 promotions
  (`maybe`→`must`) and 0 demotions, plus 2 `prohibited`→`must` folds. All three promotions
  are the same phenomenon — requests states obligations as *descriptions* ("The
  documentation files live in the docs/ directory", "They're written in reStructuredText",
  "You can find the full list of formatting requirements specified in the
  .pre-commit-config.yaml"), which read naively as `maybe` and are promoted by M4 or M3
  once the named path, markup language or CI job is taken into account. This is the rubric
  behaving as designed on unusually descriptive prose, not classification drift. The
  nearest thing to a demotion, PSF-C016's 79-character limit, did not become one: the
  source calls it a "soft-limit" in the same clause, so the naive reading was already
  `maybe` and D2 confirmed it.
- **Check 7, N4 = 0.** Not a swallowed bucket. N4 fires on applicability that turns on a
  fact outside the agent's own behaviour, and the two standard generators of those rules
  are absent here: the Authors page was fetched in full and carries no "add yourself"
  instruction, and there is no first-time-contributor rule anywhere in the three sources.
  N1 at 15 against 11 for N2–N4 is a ratio of 1.36, close to django's 1.25, so N1 is not
  inflated either.

## Things guessed, and where

No row carries `low_confidence`. Two judgment calls are worth naming because a reviewer
could reasonably land the other way; both are argued in the row's `Conclusion` rather than
hedged:

- **PSF-C018, `Shared Category`.** "Use single-quoted strings" sits in the Documentation
  Contributions section but governs the form of Python code, so it is filed under
  `Language and framework style` rather than `Documentation and docstrings`. It is the only
  row in that bucket. Filing it under Documentation would leave the bucket empty and would
  hide the one mechanical language rule requests states in prose.
- **PSF-C029 vs PSF-C032, the split inside the certification list.** The four certification
  items are introduced by "By submitting a pull request, you certify that". Two of them —
  authorship and copyright — are properties of the code that the trajectory shows, so they
  are Care with `PassType: always fails`, following the care rubric's own precedent that an
  AI disclosure checklist is Care because the trajectory shows it. The other two —
  understanding the code, accepting responsibility — have no artifact in the run: the first
  is N2 (`judgment`), the second N1 (it is an undertaking made by an identified submitter,
  and the run has no identity and no submission). The alternative reading, that the whole
  list is N1 because a pull request is never opened, would move PSF-C029 out of Care.

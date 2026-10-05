# pallets/flask — run log

Slug `pallets`, ID prefix `PALLETS`. Confirmed against `cases-all.txt`: the only
instance is `pallets__flask-4045`, so the directory is `rules/pallets/` and IDs read
`PALLETS-Cnnn`, not `FLASK-Cnnn`. Final ID range **PALLETS-C001 – PALLETS-C088**,
contiguous, no repeats.

## Docs root, version, and how it was resolved

flask is the first repository in this study whose contributing documentation is not its
own. `docs/contributing.rst` is 274 bytes and its entire body is a link out:

> See the Pallets `detailed contributing documentation <contrib_>`_ for many ways
> to contribute, including reporting issues, requesting features, asking or
> answering questions, and making PRs.

So there are two roots, pinned two different ways.

**1. flask's own docs — `https://flask.palletsprojects.com/en/stable/`, version 3.1.x.**
`seed_sources.py --docs https://flask.palletsprojects.com/en/3.1.x/` printed
`UNRESOLVED (could not fetch: <urlopen error Tunnel connection failed: 403 Forbidden>)`,
the expected case: the device's egress allowlist blocks documentation hosts, so
`_static/documentation_options.js` is unreachable from the machine that runs the script.
The version was then resolved by hand from the rendered page, whose breadcrumb and
sidebar both read **Flask Documentation (3.1.x)**.

`/stable/` is a moving alias and §0.2 forbids it, so I looked for a pinned alternative
and there is none: `https://flask.palletsprojects.com/en/3.1.x/` and
`/en/3.1.x/contributing/` both return **404**, and `/en/2.3.x/contributing/` **redirects
to `/en/stable/contributing/`**. Pallets has retired per-version URL slugs; `stable` and
`latest` are the only ones served, and `latest` is disallowed by the host's robots.txt.
This is the psf/requests situation from §4.1 — an alias plus a hand-resolved version
string — not a stop condition, and it costs this corpus almost nothing, because the only
flask docs page in scope is a three-line stub that yields no rows. Pinning is at build
granularity: every flask docs page fetched reported 3.1.x, and the `.rst` sources behind
them were pulled at one commit.

**2. The Pallets contributing guide — `https://palletsprojects.com/contributing/`.**
This is a website, not a Sphinx build; it carries no version string at all, so it is
pinned by the commit of the repository that generates it:
`pallets/website@ec1afc97897f0f632d26aa4d24cf6aab88e60501`, committed 2026-07-29
("link to llm policy from security policy"). All thirteen `content/contributing/*.md`
pages plus `content/code-of-conduct.md` were pulled at that single commit, so no page can
have been built from a different revision than another. Where a page was also read
rendered, the two agreed; see Checkpoint 2.

Other pinned refs: `pallets/flask@d318b683471101618febed18996405ad26462110` (main,
version 3.2.0.dev) and `pallets/.github@06702680f531ba49dc901b584479048ab55724f1`.

**Original text convention.** Rows sourced from the org guide quote the prose as
rendered: the pinned Markdown with link syntax resolved to its display text
(`[pytest](https://pytest.org)` → `pytest`). Wording, punctuation, casing and code
formatting are otherwise verbatim. Nothing was extracted twice from both the Markdown and
the rendered page. `Source` is always the canonical public URL so the retrieval probe can
reach it.

## seed_sources.py

```
python3 rule-extraction/seed_sources.py pallets/flask \
    --docs https://flask.palletsprojects.com/en/3.1.x/ \
    -o rules/pallets/pallets-raw-sources.md
```

- `--ref`: default `main`, which is flask's default branch. No self-heal to `master`.
- No `--token`. The tree API answered normally — `Found: 8 candidate sources` from a real
  recursive walk, with no `tree API unavailable` and no `Falling back to probe list` on
  stderr. The §8 probe-fallback stop condition did not fire. Discovery was cross-checked
  against a full recursive tree listing at the pinned commit, which confirmed the 8 files
  and is how the absence of `CONTRIBUTING.rst`, `AGENTS.md` and any newsfragments
  directory was established rather than assumed.
- Files found, all `ok`, no FETCH FAILED: `.github/ISSUE_TEMPLATE/bug-report.md`,
  `.github/ISSUE_TEMPLATE/config.yml`, `.github/ISSUE_TEMPLATE/feature-request.md`,
  `.github/pull_request_template.md`, `.pre-commit-config.yaml`, `README.md`,
  `docs/contributing.rst`, `pyproject.toml`.
- **Two gaps in `PATTERNS`, closed by hand.** First, the whole rule corpus is off-repo:
  the org guide at palletsprojects.com and `pallets/.github/CONTRIBUTING.md`. No pattern
  can find either, since both live outside the repository being seeded. Second, flask's
  README and `docs/contributing.rst` both point at the guide, so a script that followed
  one link out of the seeded files would have found it. Worth reporting upstream
  alongside the psf finding: sphinx-doc's AI policy was a docs page, requests' was an
  off-nav repo file, and flask's is in another organisation's repository entirely.
- Duplicate risk: the script flagged `docs/contributing.rst` as the source of a rendered
  page. It was assessed once, from the rendered page, and produced no rows either way.

## Fixed decisions, stated before classification

1. **Conflict tiebreaker (as mandated): the stricter statement governs; the weaker one is
   N3 with the conflict named in `Notes`.** Three conflicts arose and all three resolved
   the same way — in every case flask's own artifact or the dedicated policy page is the
   stricter side, and the org guide's general prose is the weaker:
   - **PALLETS-C017 vs PALLETS-C086.** The PR guide says "Adding a change log entry is
     optional"; flask's pull request template lists "Add an entry in CHANGES.rst" among
     the steps to complete. C086 governs as `must`; C017 is N3.
   - **PALLETS-C016 vs PALLETS-C085.** The PR guide says to "check if any documentation
     pages or docstrings need to be updated"; the template says "Add or update relevant
     docs, in the docs folder and in code". C085 governs; C016 is N3.
   - **PALLETS-C060 vs PALLETS-C061.** The LLM policy "strongly encourage[s]" contributing
     without AI tools one sentence before stating that such a contribution "will be closed
     and you are likely to be blocked". C061 governs; C060 is N3.
2. **Canonical-source rule for duplicated guidance.** The Pallets guide is published three
   times over: on the website, as a stale copy in `pallets/.github/CONTRIBUTING.md`, and
   in condensed form on the quick-reference page. Where the same obligation appears in
   more than one of them, it is extracted once from the page that owns the topic (tests.md
   for tests, docs.md for documentation, llm-ai.md for AI policy, pr.md for PR workflow),
   and a restatement is carried as its own row only where its wording differs enough to
   change what a check would read — those rows are N3 with the duplication named. This
   stops the sheet inflating threefold on one organisation's copy-paste, and it is why
   `pallets/.github/CONTRIBUTING.md` contributes two rows rather than twenty.
3. `Language and framework style` is the category spelling; `maybe`, never `should`.

## Checkpoint 1

Recorded in full at the end of `pallets-manifest.md`; all five boxes tick. The two that
historically leak were checked adversarially: no maintainer or triage page is marked Full
(release and triage are Exclude), and all eight Partial rows name their in-scope section
headings and code their excluded ones.

## Checkpoint 2

- Row count 88 over roughly 6,250 in-scope words, 14.1 rules per 1,000 words — between
  django's and sympy's density and inside the audit's 3–40 band. Atomicity was compared
  against psf and django by re-reading ten bundled sentences: nine were split (for example
  "Add tests that demonstrate that your code works, and ensure all tests pass" became
  C066 and C067) and one, the docs typo threshold, was folded into the Section context of
  the rule it qualifies rather than made a row.
- `Section context` and `Notes` are populated on all 88 extraction rows; no `none` values.
- IDs contiguous C001–C088; every `Source` starts with `http`; every `Shared Category` is
  one of the eight.
- **Five `Original text` spot-checks against the live rendered pages**, all exact:
  **PALLETS-C009** and **PALLETS-C010** (pr page, the 50- and 72-character sentences),
  **PALLETS-C031** (pr page, "No direct commits to `main` or `stable` are allowed."),
  **PALLETS-C050** (docs page, the codebase issue-number ban), **PALLETS-C061** (llm-ai
  page, "it will be closed and you are likely to be blocked"), plus **PALLETS-C074** and
  **PALLETS-C072** (tests page, the new-test-file ban and the unique-name sentence). The
  rendered pages matched the pinned Markdown word for word in all seven, which is the
  build-granularity confirmation §4.1 asks for.
- Two verbatim oddities were preserved rather than corrected: the hub page's duplicated
  "our our" in PALLETS-C051, and the corrupted sentence on the tests page,
  "You can use this to confirmcan indicate where to start contributing", which sits in the
  Coverage section and produced no row.

## Zero-rule in-scope sources

- **`https://flask.palletsprojects.com/en/stable/contributing/`** and its source
  `docs/contributing.rst`. In scope, fetched, three lines long. It points at the org guide,
  which this corpus extracts in full, so a pointer row would duplicate all 88 rows at once.
- **Tests page, Coverage section.** Descriptive: "Most projects do not actively check code
  coverage percentage." No obligation, and directly contradicted by the layout page's "We
  do not currently run coverage" — a disagreement about fact, not about strength, so the
  tiebreaker does not apply and neither statement is a rule.
- **Layout page, Tests / Documentation / Code Style sections.** Descriptive inventories of
  tooling, and stale: they name black, flake8, pyupgrade and reorder_python_imports, none
  of which appear in flask's `.pre-commit-config.yaml`, which pins ruff. Used as Section
  context on PALLETS-C019 only; extracting them would have put four rules in the sheet
  that no flask hook enforces.
- **Hub page, "other activities" list.** Suggestions for what to work on, not obligations.
- **PR guide, Review and Merge.** Describes maintainer behaviour and how to read review
  comments from strangers.
- **`.pre-commit-config.yaml`, `pyproject.toml`, `.editorconfig`, `.readthedocs.yaml`,
  `CHANGES.rst`, `README.md`, both workflow files.** Config and data, `context-only` by the
  traversal table. `.editorconfig`'s `max_line_length = 88` is the only line-length
  statement anywhere in this project; no prose states it, so there is no line-length rule
  in this corpus. That is a real difference from django and sympy, both of which state
  their limit in prose.

## Untrusted-input check

Every fetched page and raw file was read as material, never as instruction. flask's three
issue templates and its pull request template contain eight HTML comment blocks between
them; all eight are ordinary placeholder guidance ("Replace this comment with…") and none
addresses an automated agent or attempts to direct one. Nothing resembling astropy's
prompt-injection canary appears in flask's repository, in `pallets/.github`, or on any of
the fourteen Pallets guide pages. No row was suppressed on these grounds.

## Guesses and low-confidence rows

Two rows carry `low_confidence:` and nothing else was guessed.

- **PALLETS-C043** ("Avoid phrases that might imply something is implicitly easy"). Kept as
  Care/`maybe` via D4 on the django C107 precedent, but the banned class is open — the docs
  name only "just do X" and "the reason is obviously Y", where sympy's equivalent ships a
  list. Any check is under-inclusive by construction. If this row is later re-graded, N2 is
  the alternative and the frozen CSV shows the extraction was not the problem.
- **PALLETS-C082** ("Ensure each step in CONTRIBUTING.rst is complete"). The named file does
  not exist anywhere in pallets/flask. Its target is inferred, from GitHub's org-default
  fallback to `pallets/.github/CONTRIBUTING.md` and from the four steps the same comment
  block goes on to list. Graded N3 because those four steps are extracted individually as
  C083–C088.

## §7 audit output

```
  audit: pallets-rules.xlsx  (88 rows)

  1  Gate (tools/corpus.py)  PASS  tools/corpus.py exits 0
  2  Schema and vocabulary   PASS  11 columns in order; vocabulary, blanks and taxonomy clean
  2b ID prefix               PASS  all 88 IDs match ^PALLETS-C\d{3}$
  3  Judgment invariant      PASS  0 judgment+Care rows (13 judgment rows, all Not Care)
  4  NaiveStrength present   PASS  NaiveStrength on 100% of 88 rows
                                   NaiveStrength != Strength on 18 of 36 Care rows: {'prohibited -> must': 10, 'maybe -> must': 8}
  5  Promotion direction     PASS  promotions maybe->must: 8; demotions must->maybe: 0; prohibited->must folds: 10; unchanged: 18
  6  Reasoning uniqueness    PASS  88 distinct Conclusion values; 88/88 rows carry a Conclusion:
  7  N1 vs N2-N4 balance     PASS  N1 26 | N2 11 | N3 11 | N4 4  (N1 vs N2-N4: 26/26)
  8  Row-count plausibility  PASS  88 rows over 6250 words = 14.1 rules/1k words (order-of-magnitude band 3.0-40.0)
  9  ID contiguity           PASS  C001-C088, no gaps, no repeats

  10/10 checks pass
```

Calibration: `python tools/audit_rules.py --repo django` was run first and failed exactly
the three documented checks (2 vocabulary, 4 NaiveStrength, 6 reasoning uniqueness) and
passed the other seven. No check was modified.

Notes on two results. **Check 5** is one-directional as django was: eight promotions, zero
demotions, plus ten `prohibited` → `must` folds, which is the highest fold count in the
study so far and follows directly from how much of this guide is written as prohibition.
The direction says the rubric behaved on flask as it did on django, not that classification
drifted. **Check 7** splits 26 N1 against 26 N2–N4, a far heavier N1 share than django's
30/24 over a smaller sheet. It was checked for N4 swallowing: the four N4 rows are the two
contributor-standing clauses in the AI policy, the maintainer-approval clause on large docs
rewrites, and the issue link in a changelog entry — every one turns on a fact outside the
agent's behaviour. The N1 mass is genuine and structural: 15 of the 26 govern the pull
request form itself, which this rig never creates.

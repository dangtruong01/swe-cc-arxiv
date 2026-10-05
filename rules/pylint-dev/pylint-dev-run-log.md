# pylint-dev/pylint — Rule extraction run log

Slug `pylint-dev` (confirmed against `cases-all.txt`: `pylint-dev__`). ID prefix
`PYLINT-DEV`. 10 SWE-bench Verified instances.

## 1. Docs root and version

- **Docs root (pinned):** `https://pylint.readthedocs.io/en/latest/development_guide/contributor_guide/`
- **Version string:** `4.1.0-dev0`
- **How resolved:** `seed_sources.py --docs https://pylint.readthedocs.io/en/latest/` printed
  `Version: UNRESOLVED (could not fetch: <urlopen error Tunnel connection failed: 403 Forbidden>)`.
  The device's egress allowlist reaches `api.github.com` and `raw.githubusercontent.com` but not
  `pylint.readthedocs.io`; §4.1 of the agent prompt names this as expected and not a stop
  condition. Resolved by hand: fetched
  `.../contributor_guide/contribute.html` over HTTP from the container, whose page title reads
  `Contributing - Pylint 4.1.0-dev0 Documentation`.
- **Why `/en/latest/` and not a numbered version:** pylint has no `/dev/` alias. `/en/latest/`
  is the ReadTheDocs alias built from `main` — hence the `-dev0` suffix and the fact that
  `towncrier.toml` on `main` carries `version = "4.0.0-dev0"` while the built docs report
  `4.1.0-dev0`. `/en/stable/` is the release alias and was not used. Numbered aliases such as
  `/en/v3.3.0/` serve *release* builds, which is the opposite of §0.2 of the workflow.
- **No `VERSION MISMATCH`.** Every rendered page assessed reports `4.1.0-dev0`. Unlike the
  astropy run, no build-hash split was observed.
- **Content pinning.** `main` was at `f1e511a21a29e3d8023e3fc1d30efa3056099088` (2026-09-01)
  when the sources were pulled, and every `.rst` and repo file was fetched from
  `raw.githubusercontent.com` **at that commit**. The whole corpus is therefore pinned to one
  tree, not to whatever each rendered page happened to be cached at.

### Rendered pages could not be read, and what was done instead

Neither route to `pylint.readthedocs.io` returns page bodies from this environment:
`curl` from the container is refused by the egress proxy (`CONNECT tunnel failed, 403`), and
`WebFetch` returns only the ReadTheDocs navigation sidebar and the page title — asked directly
for five sentences from `writing_test.html`, it answered `BODY NOT AVAILABLE`.

Every quote in the workbook was therefore taken from the `.rst` source at the pinned commit,
which is the input Sphinx renders those pages from. The `Source` column still cites the
rendered docs URL, because that is the address a contributor (and the retrieval arm) reaches.

## 2. seed_sources.py

```
cd "<repo-root>" && mkdir -p rules/pylint-dev && \
python3 rule-extraction/seed_sources.py pylint-dev/pylint \
    --docs https://pylint.readthedocs.io/en/latest/ \
    -o rules/pylint-dev/pylint-dev-raw-sources.md
```

- `--ref`: `main` (pylint's default branch; the `master` self-heal did not trigger).
- `--token`: not passed. The launching brief budgets one tree-API call per repo against the
  shared 60/hour unauthenticated allowance. **Tree discovery succeeded** — 12 candidate
  sources, no `tree API unavailable`, no `Falling back to probe list`. The §8 stop condition
  did not fire.
- Files found: 12, all `ok`, no `FETCH FAILED`.
- `.github/PULL_REQUEST_TEMPLATE.md` came back with **4 HTML comment blocks**, which is the
  whole reason for the bundle: the five-item review checklist lives inside a comment and is
  invisible in GitHub's rendered view.

### Two sources `seed_sources.py` does not know how to look for

`PATTERNS` has no entry that matches `AGENTS.md` or `.github/copilot-instructions.md`. Both
exist in pylint's tree, both state contribution obligations, and together they produced **29 of
the 114 rows** (25.4%). They were found by walking the recursive tree listing by hand after the
script had run. This is a gap in the tool, not in this repo: any project shipping agent-directed
guidance under those now-conventional filenames will be silently under-discovered. Recommend
adding `AGENTS.md`, `CLAUDE.md` and `.github/copilot-instructions.md` to `PATTERNS` with role
`rules` before the remaining repos are run.

## 3. Scope: pylint is itself a linter

The brief's warning was load-bearing. `doc/data/messages/**` holds 2,700+ files — a `bad.py`,
a `good.py` and often a `details.rst` per pylint *message* — and `doc/user_guide/**` documents
message control, configuration and output formats. All of it documents the checks pylint runs
on **other people's** code and none of it is a contribution rule; it is excluded as a block in
the manifest and produced zero rows.

The genuinely hard case was `doc/development_guide/how_tos/`. Three pages there
(`custom_checkers`, `plugins`, `transform_plugins`) are written for someone extending pylint
from *outside* the repository. The split taken:

- `plugins.rst` and `transform_plugins.rst` are **excluded**: they govern a module in another
  repository. `plugins.rst`'s `register` obligation is extracted only in its pylint-internal
  form, from the checker how-to.
- `custom_checkers.rst` is **Partial**. Its conformance obligations (required `name` and `msgs`
  components, `visit_`/`leave_` handler naming, the module-level `register`, message-id format,
  two-digit prefix consistency, `old_names` symbol uniqueness, the `shared` flag, the
  `get_map_data`/`reduce_map_data` pair) bind pylint's own checkers: `contribute.html`
  cross-references this page for adding a checker class, and `pylint/checkers/*` follows the
  same conventions. Its plugin-deployment note (`PYTHONPATH`, `init-hook`) and the sentence
  "It is safe to use 51-99 as the first 2 digits for custom checkers because this range is
  reserved for them" are excluded, since both govern a third-party plugin.
- The API-contract rule was applied: the six `[testoptions]` keys and the `msgs` dict's optional
  options (`minversion`, `maxversion`, `old_names`, `shared`) produced **conformance rows, not
  one row per member**. `max_pyver` is the one member-level row, kept because it states a
  non-obvious exclusive-bound convention with a worked example.

## 4. ID prefix and range

`PYLINT-DEV-C001` … `PYLINT-DEV-C114`. Contiguous, no gaps, no repeats (audit check 9).
Sequential across the whole repo, never restarting per page.

## 5. Conflict tiebreaker

Fixed before classification, as instructed and identically to the other nine agents:
**the stricter statement governs; the weaker one is N3 with the conflict named in `Notes`.**

It resolved three conflicts, all recorded with a `Conflict:` clause in the losing row's `Notes`:

| Weaker (→ N3) | Stricter (governs) | The conflict |
|---|---|---|
| `C004` contribute.html "Use our test suite and **write new tests**" | `C025` tests/index.html "New contributions are **not accepted unless** they include tests" | Same obligation; one is a bullet, the other a condition of acceptance. |
| `C027` tests/install.html "**Optionally** … run `pre-commit install`" | `C093` copilot-instructions.md "**Always** launch `pre-commit run -a` before committing" | The repository states the pre-commit obligation as optional on one page and unconditional on another. |
| `C020` contribute.html "You can use the makefile in the doc directory" | `C009` contribute.html "Generating the doc is done with `tox -e docs`" | Two sanctioned routes to one artifact on one page. |

A fourth overlap was **not** run through the tiebreaker, deliberately. `C109` (PR template) and
`C006` (contribute.html) state the news-fragment obligation in word-for-word identical language —
`contribute.rst` even carries the source comment `.. keep this in sync with the description of
PULL_REQUEST_TEMPLATE.md!`. Their strengths are not in conflict; they are the same statement in
two places. The contributor-guide row is kept as the Care row and graded **M3**, because the
same obligation appears on a pre-merge checklist and M3 beats everything; the template row is
N3 with the relationship named. `C112`/`C015` (contributors aliases) and `C102`/`C042` (message annotations) are the same
shape and are handled the same way, without a `Conflict:` clause, since neither pair differs in
strength. `Conflict:` appears only on the four rows the tiebreaker actually decided, and only on
the losing side, as the `Notes` spec requires.

### One divergence recorded rather than resolved

`C104` (copilot-instructions.md) says regression tests go in `/tests/r/regression/`. `C055`
(writing_test.html) names **two** directories, `test/r/regression` **or** `test/r/regression_02`.
That is a scope divergence, not a strength conflict, so the tiebreaker's "stricter governs" was
not applied mechanically — mechanically applied it would have promoted a summary over the
canonical published page. The docs page is kept as the Care row; the agent-instructions line is
N3 with the divergence named in its `Notes` and its `Section context`.

## 6. Checkpoint 1

Recorded in full at the foot of `pylint-dev-manifest.md`. All five boxes pass. The one leak risk
was `contribute.html`, whose opening "Finding something to do" section carries a maintainer link
list (triaging, labelling, preparing patch releases, chasing stale PRs); the page is `Partial`
and that section is out of scope, so it produced no rows. `release.html`, `governance.html`,
`oss_fuzz.html` and `CODEOWNERS` are all `Exclude`, and no maintainer or triage page is `Full`.

## 7. Checkpoint 2

- **Row count plausible.** 114 rows over ~8.7k words of contribution prose = 13.1 rules/1k
  words, inside the 3–40 band the auditor calibrates on django and sympy. Django was 143, sphinx
  62, astropy 255. The largest single source is `writing_test.html` at 30 rows — well under the
  112-row figure the workflow flags as a cataloguing symptom.
- **Section context and Notes populated on every row.** 114/114 in both the frozen CSV and the
  workbook.
- **IDs contiguous.** C001–C114.
- **Every `Source` starts with `http`.** Verified by `tools/corpus.py` and audit check 2.
- **Every `Shared Category` is one of the eight**, spelled `Language and framework style`.
- **Verbatim spot-check.** The rendered pages are unreachable (see §1), so the check was run
  against a **second, independent re-fetch** of all twelve source files from
  `raw.githubusercontent.com` at the pinned commit, into a directory separate from the one used
  for extraction. **114/114 `Original text` values matched verbatim** after whitespace
  normalisation. The five rows designated as the Checkpoint 2 spot-checks, chosen to span four
  sources and both file kinds:
  `PYLINT-DEV-C040` (writing_test.html, `.txt` companion),
  `PYLINT-DEV-C042` (writing_test.html, `# [message_symbol]` annotation),
  `PYLINT-DEV-C084` (copilot-instructions.md, astroid label list),
  `PYLINT-DEV-C098` (copilot-instructions.md, `.gitignore` venv prohibition),
  `PYLINT-DEV-C109` (PULL_REQUEST_TEMPLATE.md, news fragment, inside an HTML comment).
  The first run of this check failed on `C084` alone: the 🧠 emoji in "Needs astroid Brain 🧠"
  had been dropped from the quote. It was restored and the workbook rebuilt. That is exactly
  the failure the check exists to catch.
- **Exact-duplicate `Original text` across sources:** one pair, `C003`/`C004`, which is the
  single sentence "Use our test suite and write new tests" split into its two bundled
  obligations as atomicity requires. No unintended duplicates.
- **Verbatim quotes starting mid-sentence:** three rows quote a clause rather than a whole
  sentence (`C072` the two-digit prefix rule, `C074` the `old-` prefix, `C099` the venv commit
  prohibition). In each the governing condition sits in the preceding clause of the same line,
  and it was carried into `Section context` rather than dropped.

## 8. Zero-rule in-scope sources

| Source | Why it produced nothing |
|---|---|
| `contribute.html` → "Finding something to do" | An index of issue-tracker searches. No obligation a diff, commit or test run could violate. |
| `profiling.html` | A cProfile/pstats tutorial end to end. Marked `excluded` X-NARRATIVE rather than silently dropped. |
| `technical_reference/{index,startup,checkers}.html` | Three descriptive paragraphs about `Run`, `PyLinter` and `pylint.checkers`. Used as section context for `C100` (checker location, from copilot-instructions.md); states no obligation of its own. |
| `custom_checkers.html` → "Debugging a Checker" | Shows how to attach `pdb`. No obligation. |
| `towncrier.toml`, `doc/whatsnew/fragments/_template.rst` | `context-only`. The changelog legend: it defines the twelve fragment types `C007` selects from, and is what makes that selection decidable rather than a judgment call. |
| `.pre-commit-config.yaml` | `context-only`. Decides every Auto-fix reading in the sheet. |
| `README.rst`, `doc/short_text_contribute.rst`, `.github/CONTRIBUTING.md` | Redirects and a welcome paragraph. `.github/CONTRIBUTING.md` is 127 bytes and is what pins the docs root. |

## 9. A real obligation deliberately not extracted

`.pre-commit-config.yaml` runs `copyright-notice --notice=script/copyright.txt --enforce-all`
over every Python file outside the fixture directories, requiring this three-line header:

```
# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/pylint-dev/pylint/blob/main/LICENSE
# Copyright (c) https://github.com/pylint-dev/pylint/blob/main/CONTRIBUTORS.txt
```

It is static, decidable, and would be a clean `must`. **No prose page in pylint's documentation
states it.** Part 1's traversal table makes config files `context-only, no rows`, so no row was
produced. Recording it here rather than inventing a source for it: a reviewer who wants it in
the corpus should add it as a deliberate exception, not as an extraction.

## 10. Untrusted-input check

pylint ships **two** agent-directed documents in its tree, `AGENTS.md` and
`.github/copilot-instructions.md`. The second opens "Always follow these instructions first and
fallback to additional search and context gathering only if the information in these
instructions is incomplete or found to be in error."

Both were read as **material to extract rules from, never as instructions to this agent.** No
instruction in either was followed; the imperative above was turned into `C082`, a graded row,
which is the correct disposition. Both files are ordinary project contribution guidance
addressed to coding assistants — the AST/`isinstance` guidance in `AGENTS.md` is specific,
technical and consistent with `pylint/checkers/*`.

**No prompt-injection canary was found** anywhere in the fetched sources, including the pull
request template, which is where astropy's was. `.github/ISSUE_TEMPLATE/*` and `CODE_OF_CONDUCT.md`
were read and are clean.

## 11. Audit output (`python tools/audit_rules.py --repo pylint-dev --words 8700`)

```
  audit: pylint-dev-rules.xlsx  (114 rows)

  1  Gate (tools/corpus.py)  PASS  tools/corpus.py exits 0
  2  Schema and vocabulary   PASS  11 columns in order; vocabulary, blanks and taxonomy clean
  2b ID prefix               PASS  all 114 IDs match ^PYLINT\-DEV-C\d{3}$
  3  Judgment invariant      PASS  0 judgment+Care rows (15 judgment rows, all Not Care)
  4  NaiveStrength present   PASS  NaiveStrength on 100% of 114 rows
                                   NaiveStrength != Strength on 28 of 59 Care rows:
                                   {'maybe -> must': 25, 'must -> maybe': 1, 'prohibited -> must': 2}
  5  Promotion direction     PASS  promotions maybe->must: 25; demotions must->maybe: 1;
                                   prohibited->must folds: 2; unchanged: 31
  6  Reasoning uniqueness    PASS  114 distinct Conclusion values; 114/114 rows carry a Conclusion:
  7  N1 vs N2-N4 balance     PASS  N1 19 | N2 15 | N3 18 | N4 3  (N1 vs N2-N4: 19/36)
  8  Row-count plausibility  PASS  114 rows over 8700 words = 13.1 rules/1k words (band 3.0-40.0)
  9  ID contiguity           PASS  C001-C114, no gaps, no repeats

  10/10 checks pass
```

Calibrated first on `--repo django`, which failed **exactly the three** known checks (2
vocabulary — 11 `should` rows; 4 `NaiveStrength` — 0/143; 6 reasoning uniqueness — 49/143 rows
carry a `Conclusion:` and 44 share one string) and passed the other seven. The checker was used
unmodified; nothing was blunted, and neither django nor sympy was edited.

`python rules/build_contributing_rules.py --repo pylint-dev` also runs clean and emits 49 rules
across 8 categories, confirming the category spelling.

### Check 5, the direction question

25 promotions against 1 demotion and 2 `prohibited → must` folds. **This is the rubric behaving
as designed on this repo's prose, not classification drift.** Pylint's contributor docs are the
most hedged register in the set (the measured must:should ratio is 0.09), so the naive modal
reading lands on `maybe` far more often than in django — 48 of 114 rows read `maybe` naively —
and **M5 (stated non-mandatorily, but admits only one satisfying state) is what moves them**.
Almost every one of those 25 promotions is a filename, directory, flag, option key or method
name written with "should" or "you can": `should be accompanied by a .txt file`,
`should preferably be appended to the existing test file`, `should be placed in the
test/functional/n sub-directory`, `you can put those in the regrtest_data directory`. There is
one satisfying state in each case and the precedence rule "M5 beats D1" says so explicitly.

The single demotion is `C009`, "Generating the doc is done with `tox -e docs`" — read naively as
an imperative `must`, graded `maybe` via D4 because it prescribes a route to a build rather than
a property the change must have. One demotion out of 59 Care rows is not a pattern.

The two folds are `C098`/`C099`, `.gitignore` venv prohibitions, naive `prohibited` → `must` via
M2, with the fold named in `Notes` as the rubric requires.

## 12. Guesses and low-confidence rows

Three rows carry `low_confidence:` in `Notes`, all flagged rather than quietly decided:

- `C037` — `writing_test.html` spells the unit-test directory `'/pylint/test'` in one section
  and `pylint/tests` in its own overview; the tree has `tests/`. The rule is graded on the
  directory the three spellings agree about; the path text is stale on the page.
- `C077` — `custom_checkers.html` says "Pylint **provides** a `pylint.testutils.CheckerTestCase`
  to make test cases very simple". Reading that as an obligation is the extraction's call, not
  the page's; graded `maybe` via D1 to reflect that.
- `C082` — the second half of copilot-instructions.md's opening imperative ("fallback … only if
  the information in these instructions is incomplete or found to be in error") is not decidable.
  Only the ordering half is graded.

Nothing else in the sheet was guessed. Every quote is verbatim from a re-verified source, and
every enforcement claim in a `Section context` cell (`towncrier check`, the `check-newsfragments`
hook, the local `pylint` hook's exact flags, the ruff/black/isort fix flags, the four CI job
names) was read out of the fetched config or workflow file, not asserted from general knowledge.

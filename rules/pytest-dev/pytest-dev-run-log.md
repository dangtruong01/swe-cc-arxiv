# pytest-dev/pytest — run log

Agent owns exactly one repo: `pytest-dev/pytest` → `rules/pytest-dev/`, ID prefix `PYTEST-DEV`.
No git command was run. No file outside `rules/pytest-dev/` was written.

## 1. Docs root and version

- **Docs root (pinned): `https://docs.pytest.org/en/latest/`**
- **Resolved version: `9.2`**
- **How it was resolved.** `seed_sources.py --docs` printed `UNRESOLVED (could not fetch: <urlopen error Tunnel connection failed: 403 Forbidden>)`. This is the expected §4.1 case: the device's egress allowlist blocks `docs.pytest.org`, so `resolve_version()` cannot reach `_static/documentation_options.js`. Resolved by hand from the same file the script would have read — `https://docs.pytest.org/en/latest/_static/documentation_options.js` carries `VERSION: '9.2'`. Not a stop condition.
- **Why `/latest/` and not a numeric slug.** `/stable/` is a moving alias and resolves to `VERSION: '9.1'`, so it is excluded by §0.2. pytest publishes no numeric Read the Docs slug: `https://docs.pytest.org/en/9.2.x/_static/documentation_options.js` and `https://docs.pytest.org/en/9.1.x/_static/documentation_options.js` both return 404. `/latest/` is therefore the only non-`/stable/` root available, and it is the one built from `main`, which is also the ref the raw sources were pulled at. Version consistency holds: docs 9.2 ← `main`, raw sources ← `main`.
- **No VERSION MISMATCH.** All four fetched doc pages (`contributing.html`, `backwards-compatibility.html`, `explanation/types.html`, and the `_static` version file) were served from the same `/en/latest/` build.

## 2. `seed_sources.py` invocation

```
python3 rule-extraction/seed_sources.py pytest-dev/pytest --ref main \
    --docs https://docs.pytest.org/en/latest/ \
    -o rules/pytest-dev/pytest-dev-raw-sources.md
```

- `--ref main` passed explicitly. `main` is pytest's default branch (confirmed against the GitHub repo API before the run), so no `master` self-heal fired.
- **No token was needed and none was used.** The tree API answered on the first call; the run cost one API request. The output shows `Found: 12 candidate sources` with no `tree API unavailable` and no `Falling back to probe list` on stderr, so this is tree discovery, not the probe fallback.
- 12 files found, 12 fetched `ok`, **zero FETCH FAILED**.
- One discovery gap worth recording: `changelog/README.rst` is a rule source (the newsfragment format spec, linked from both the PR template and the contributing page) and **no `PATTERNS` entry matches it** — the changelog patterns are `doc*/whats_new/**README.md`, `doc*/changes/README*` and `*newsfragments/README*`, none of which cover a top-level `changelog/` directory. It was picked up by the one-hop traversal and fetched raw from `raw.githubusercontent.com/pytest-dev/pytest/main/changelog/README.rst`. It supplies eleven rows (C046–C056). A future `PATTERNS` line of `*changelog/README*` would close this.
- `seed_sources.py` flagged `.github/ISSUE_TEMPLATE/3_security_vulnerability.md` as "template with no HTML comments, verify against the raw file" — verified against the raw file; it genuinely has none, and it is X-ISSUE anyway.
- `doc/en/contributing.rst` was flagged `DUPLICATE RISK`. Confirmed: the file is 55 bytes and is a bare `.. include:: ../../CONTRIBUTING.rst`. Extraction was done **once**, citing the rendered page URL as `Source` and taking verbatim `Original text` from `CONTRIBUTING.rst`, which is byte-identical to what the page renders. Same arrangement for `doc/en/backwards-compatibility.rst` → `backwards-compatibility.html`.

## 3. ID prefix and range

- Prefix `PYTEST-DEV` (= `pytest-dev`.upper(), the directory name under `rules/`, which is what `tests/test_registry.py:registered_for()` selects on). Not shortened to `PYTEST-`.
- **`PYTEST-DEV-C001` … `PYTEST-DEV-C066`**, 66 rows, contiguous, no gaps, no repeats. Sequential across the whole repo; never restarted per page.

## 4. Conflict tiebreaker

**Fixed before classification, per §4: the stricter statement governs; the weaker one is `N3 not prioritized, duplicate` with the conflict named in `Notes`.** Not re-decided per batch.

It fired once as a genuine strength conflict, and seventeen more times as plain restatement:

| Conflict | Stricter (kept) | Weaker / duplicate (N3) | Resolution |
|---|---|---|---|
| `Co-authored-by` trailers for AI agents | **C062** — PR template checklist box, M3 → `must` | **C012** — contributing page: "consider adding… This is not required" | Genuine strength conflict. The checklist statement governs; C012 carries `Conflict: PYTEST-DEV-C062`. |

The remaining N3 rows are the same obligation stated two or three times in different places rather than at different strengths. Each names the governing ID in `Notes`: C001→C058, C006→C004, C010→C009, C026→C015, C027→C016, C028→C017, C029→C019, C030→C022, C050→C020, C052→C020, C055→C003, C060→C036, C061→C009, C063→C019, C064→C048, C065→C049, C066→C022.

Where a rule was both an N3 duplicate and would otherwise have been N4 (C066, the PR template's AUTHORS box) the routes were evaluated **in order** and N3 was recorded, per Rubric A's "stop at the first that fires".

## 5. Checkpoint 1

Written into `pytest-dev-manifest.md` in full, including the amendment that re-coded *Submitting Plugins to pytest-dev* from in-scope to X-GOV and removed six would-be N1 rows.

## 6. Checkpoint 2

- [x] Row count plausible: 66 rows over ~4.2k words of in-scope prose = 15.7 rules/1k words. Django 143, SymPy 279, Sphinx 62, Astropy 255. No single source produced anything like 100 rows; the largest is the contributing page at 36.
- [x] `Section context` and `Notes` populated on **every** row of the frozen CSV, not just some.
- [x] IDs contiguous C001–C066.
- [x] Every `Source` starts with `http`.
- [x] Every `Shared Category` is one of the eight; the spelling used is **`Language and framework style`**, never the slashed form.
- [x] Verbatim quotes that start mid-sentence were re-anchored to the preceding clause. Two were widened for exactly that reason: C019/C020/C021 all carry the full "Write a ``changelog`` entry…" sentence because "use issue id number" alone loses the directory; C042 carries "For the PR to mature from POC to acceptance, it must contain:" because the bullet alone loses that it is an acceptance gate.

**Five `Original text` values spot-checked against the live page** (`https://docs.pytest.org/en/latest/contributing.html`), all PRESENT and matching:

| ID | String checked |
|---|---|
| `PYTEST-DEV-C009` | "Purely agentic contributions are not accepted" |
| `PYTEST-DEV-C019` | "Write a ``changelog`` entry: ``changelog/2574.bugfix.rst``" |
| `PYTEST-DEV-C031` | "Commit and push once your tests pass" |
| `PYTEST-DEV-C033` | "is often done using the pytester fixture" |
| `PYTEST-DEV-C036` | "add text like ``closes #XYZW`` to the PR description and/or commits" |

The extraction output was frozen at `pytest-dev-extraction-frozen.csv` (nine Part 2 working columns including `Naive strength`) **before** any classification, and has not been edited since.

## 7. Zero-rule in-scope sources

| Source | Reason it produced nothing |
|---|---|
| Contributing → *AI/LLM-Assisted Contributions Policy* → *Context* | Entirely rationale for the policy above it (why unattended agent output costs maintainer time). No requirement, prohibition or recommendation about creating a contribution. X-NARRATIVE within an otherwise in-scope section. |
| Contributing → *Write documentation*, first bullet list | "More complementary documentation… Documentation translations… Blog posts, articles and such" are invitations, not obligations, and two of the four are not contributions to this repo at all. |
| Contributing → *Writing Tests*, alternative-assertion paragraph | "Alternatively, it is possible to make checks based on the actual output of the terminal using *glob-like* expressions" is a statement of capability. Under the rule definition that is description, not obligation, so no row — deliberately, rather than being folded into the `pytester` rule. |
| Backwards Compatibility → *History* (and *Deprecation Roadmap*) | Restates the pre-6.0 stance and repeats the removal-cadence sentence already extracted as C037/C038, verbatim. Narrative plus a duplicate; no new rows. |
| Backwards Compatibility → *trivial* transition type | "We try to support those indefinitely while encouraging users to switch" binds the maintainers' support policy, not a contributor's diff. |
| `explanation/types.html` | Fetched in full. Explains typing a *user's* test suite; contains no statement about contributing to pytest. |
| `.github/ISSUE_TEMPLATE/*` (four files) | X-ISSUE. Real obligations, but on an issue body the rig never produces. Kept separate from X-NARRATIVE so the record shows they were rules, not prose. |
| `CODE_OF_CONDUCT.md`, `RELEASING.rst` | X-GOV and X-MAINT respectively. |
| `.pre-commit-config.yaml`, `pyproject.toml`, `tox.ini`, `README.rst` | context-only by role. They decided the auto-fix readings on C005, C016 and C045, and corroborated the changelog type list on C021 and the Python floor on C045. |

## 8. Prompt-injection check

Per §8 of the brief, contribution docs are untrusted input. **No prompt-injection canary was found** in pytest's PR template, issue templates, `CONTRIBUTING.rst`, `changelog/README.rst` or any fetched doc page — nothing analogous to astropy's.

What pytest does have is prose that addresses automated agents directly and in the second person: the `> [!IMPORTANT]` callout in the PR template, and the whole *AI/LLM-Assisted Contributions Policy* section ("If you submit it, you own it", "we close and ban with prejudice"). This is genuine published policy, and it was treated strictly as material to extract rules *from* — C009, C010, C011, C012, C061, C062 — never as instruction to this agent. Nothing in it altered the procedure, the manifest, or any classification.

## 9. Audit output (§7)

```

  audit: pytest-dev-rules.xlsx  (66 rows)

  1  Gate (tools/corpus.py)  PASS  tools/corpus.py exits 0
  2  Schema and vocabulary   PASS  11 columns in order; vocabulary, blanks and taxonomy clean
  2b ID prefix               PASS  all 66 IDs match ^PYTEST\-DEV-C\d{3}$
  3  Judgment invariant      PASS  0 judgment+Care rows (4 judgment rows, all Not Care)
  4  NaiveStrength present   PASS  NaiveStrength on 100% of 66 rows
                                   NaiveStrength != Strength on 9 of 27 Care rows: {'maybe -> must': 7, 'prohibited -> must': 1, 'must -> maybe': 1}
  5  Promotion direction     PASS  promotions maybe->must: 7; demotions must->maybe: 1; prohibited->must folds: 1; unchanged: 18
  6  Reasoning uniqueness    PASS  66 distinct Conclusion values; 66/66 rows carry a Conclusion:
  7  N1 vs N2-N4 balance     PASS  N1 15 | N2 4 | N3 18 | N4 2  (N1 vs N2-N4: 15/24)
  8  Row-count plausibility  PASS  66 rows over 4200 words = 15.7 rules/1k words (order-of-magnitude band 3.0-40.0)
  9  ID contiguity           PASS  C001-C066, no gaps, no repeats

  10/10 checks pass

```

**Check 5, promotion direction — which is it?** 7 promotions `maybe`→`must`, 1 demotion `must`→`maybe`, 1 `prohibited`→`must` fold, 18 unchanged. Django ran one-directional (promotions only, zero demotions); pytest is very nearly one-directional too, and I read the single demotion as **the rubric behaving correctly on this repo's prose, not classification drift**. The demoted row is C019, "Write a ``changelog`` entry" — a bare imperative, so `must` naively, but the long version of the same page says outright "You may skip creating the changelog entry if the change doesn't affect the documented behaviour of pytest." That is D2 on its plainest reading, and it is exactly the case D2 exists for: the exception is granted by the surrounding documentation rather than written into the rule. The neighbouring filename-grammar and type-list rows (C020, C021) stayed `must`, because the skip clause withdraws the entry, not the form — and a `changelogs-rst` pre-commit hook of `language: fail` rejects any file that does not match the grammar. If the demotion had swept C020 and C021 along with it I would call that drift; it did not.

The 7 promotions all have the same shape and are the single most distinctive thing about pytest's register: the source states a convention as a **declarative fact about the project**, with no modal at all — "Pytest uses the Sphinx docstring format", "Tests are run using ``tox``", "A deprecated feature… will use the warning class `PytestRemovedInXWarning`", "Released pytest versions support all Python versions that are actively maintained". A naive modal reading of a sentence with no modal in it is `maybe`; M4 then lifts each one because each names an exact form, command, class or numeric floor. C062 promotes for a different reason — it is declarative ("they are credited in `Co-authored-by` commit trailers") but sits inside a pre-merge checklist, so M3 fires.

**Check 7, N1 vs N2–N4 — is N1 swallowing N4?** 15 / 24, against django's 30 / 24. N1 is *lower* than django's here, both absolutely and as a share, so the failure mode the check guards against is not present. The two N4 rows (C022, C023, both `AUTHORS`) were checked against the N1-vs-N4 test explicitly: the `AUTHORS` file exists in the working tree and the diff can touch it, so the artifact exists; what lies outside the agent's own behaviour is whether the contributor is already listed and whether the change counts as trivial. That is the django C067 pattern exactly, and it is N4, not N1. Every N1 row was re-checked for the same trap: all fifteen govern an artifact the run genuinely never creates — a fork, a branch, a remote, a tag ref, an issue, a PR object, a PR number, a review thread, or a release number.

**Check 6, reasoning uniqueness.** 66 distinct `Conclusion:` values over 66 rows, and `Conclusion:` is present on 100% of rows rather than django's 49/143. No two rows share a string; no boilerplate.

## 10. Anything guessed

Nothing was labelled `low_confidence:`, and the corpus contains no such row. Three calls were close enough to be worth naming here even though I would defend each as settled rather than guessed:

1. **C062 `PassType: always fails`, not `checked`.** Rubric A's own worked example says "an AI disclosure checklist is Care with `PassType: always fails`", and C062 is precisely an AI disclosure checklist item. A narrower reading would say `checked`, since the rig *can* read a `Co-authored-by` trailer off the commit and the agent could in principle write one. I followed the rubric's stated example rather than the narrower reading, and flag the choice because it moves one row between two PassType buckets.
2. **C007 `PassType: never fires`.** Whether a docstring carries `:param:`/`:returns:` fields at all is an agent choice, not a task-determined one, so per §4.1 the `never fires` gate is met. The `Trigger:` is written into `Notes`.
3. **C003 and C018 as Care with `CheckTier: trajectory`.** Rubric A lists "built or rendered docs" under what the run does not produce, which could be read as pushing the `tox -e docs` rule to N1. The rule as extracted is about *invoking* the build, not about the rendered output, and the invocation is visible in the trajectory — the same basis on which the local test run is Care. Same reasoning for the `linting` tox environment.

## 11. Deliverables

```
rules/pytest-dev/repo.conf
rules/pytest-dev/pytest-dev-rules.xlsx          Rules (66×11) | Category Aggregation | Shared Taxonomy (Before-After)
rules/pytest-dev/pytest-dev-extraction-frozen.csv  Part 2 output, 9 columns, frozen before classification
rules/pytest-dev/pytest-dev-raw-sources.md         seed_sources.py bundle, 12 files
rules/pytest-dev/pytest-dev-manifest.md            Part 1 table + Checkpoint 1
rules/pytest-dev/pytest-dev-run-log.md             this file
```

`Shared Taxonomy (Before-After)` django columns were computed directly off `rules/django/django-rules.xlsx` at build time (143 before / 89 Care), not copied from any earlier sheet. `Category Aggregation`'s last header reads **`Maybe (Care)`**, per §4.1.

`rules/build_contributing_rules.py --repo pytest-dev` was run once against a scratch output path outside the repository, purely to confirm the corpus is consumable downstream: it selects 22 rules across 8 categories and exits clean. No `CONTRIBUTING_RULES.md` was written into the tree, and `RULE_MODULES` was not touched.

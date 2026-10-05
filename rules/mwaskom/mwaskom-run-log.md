# mwaskom/seaborn — run log

Repo 8 of the ten-repo extraction run. Slug `mwaskom`, ID prefix `MWASKOM`.
Final corpus: **5 rules**, 4 Care / 1 Not Care, 2 `must` / 2 `maybe`.

## Docs root and version

seaborn is the first repo in this run whose contribution rules are not on a
documentation site, so the pin is a commit rather than a docs build.

- **Published site:** `https://seaborn.pydata.org/`, fetched, reports
  **seaborn 0.13.2 documentation**. Its navigation is Installing / Gallery / Tutorial /
  API / Releases / Citing / FAQ. There is no contributing, development or contributor-guide
  page, and no `/dev/` build is published — the site is rebuilt from `master` at release
  time only, and older versions live at `/archive/0.11/`, `/archive/0.12/`. `/stable/` was
  never fetched.
- **Corroboration in the tree:** `doc/` contains `api.rst`, `citing.rst`, `faq.rst`,
  `index.rst`, `installing.rst`, `whatsnew/` and build plumbing. `doc/faq.rst` (4,168 words)
  has zero occurrences of "contribut", "pull request" or "test suite".
- **Pinned root actually used:**
  `https://github.com/mwaskom/seaborn/blob/f04b6cd5484267a0885d1fed068e99dff3a1b226/`
- **Version string:** `0.14.0.dev0`, resolved by hand from
  `seaborn/__init__.py:__version__` at that commit, because `seed_sources.py --docs`
  printed `UNRESOLVED` (see below). The commit is `master@2026-07-06T02:11:53Z`,
  "Tweak the docs homepage style (#3960)".
- **No `VERSION MISMATCH`.** Not a single extracted quote comes from the 0.13.2 site; all
  five come from two files at the one pinned commit, verified byte-for-byte (Checkpoint 2).
  Per the §4.1 ruling, differing build granularity is not a halt, and here the question does
  not even arise: the release site and the dev tree never both supply a quote.

`DOCS_URL` in `repo.conf` is
`https://github.com/mwaskom/seaborn/tree/f04b6cd5484267a0885d1fed068e99dff3a1b226`,
the page GitHub renders `README.md` into and from which `.github/CONTRIBUTING.md` is one
click away. Those are the only two rule-bearing sources, so this is the honest analogue of
a docs root for the retrieval probe.

## seed_sources.py

```
python3 rule-extraction/seed_sources.py mwaskom/seaborn --ref master \
    --docs https://seaborn.pydata.org/ -o rules/mwaskom/mwaskom-raw-sources.md
```

- `--ref master` was passed explicitly. seaborn's default branch is `master`, confirmed
  from `GET /repos/mwaskom/seaborn` (`default_branch: "master"`) before the run; the
  script's `main` default with `master` self-heal was not relied on.
- No `--token`. The tree API answered normally: the output shows `Found: 4 candidate
  sources` with no `tree API unavailable` or `Falling back to probe list` warning, so
  discovery is real and the §8 probe-fallback stop condition did not fire. Cross-checked
  against a hand-fetched recursive tree (`git/trees/master?recursive=1`, 325 blobs,
  `truncated: false`), which agrees: the four seeded paths are the only ones matching
  `PATTERNS`.
- `Version: UNRESOLVED (could not fetch: <urlopen error Tunnel connection failed: 403
  Forbidden>)` — expected. The device's egress allowlist blocks `seaborn.pydata.org`
  (`curl` returns 000 for it while `api.github.com` and `raw.githubusercontent.com` return
  200). Resolved by hand as recorded above. Per §4.1 this is not a stop condition.
- Files found, all `ok`, no `FETCH FAILED`: `.github/CONTRIBUTING.md` (rules, 2,323 b),
  `.pre-commit-config.yaml` (context), `README.md` (context), `pyproject.toml` (context).
  Zero comment blocks in any of them — there is no template file to hide obligations in.
- Fetched raw by hand in addition, at the pinned SHA: `SECURITY.md`, `Makefile`,
  `.github/workflows/ci.yaml`, `CITATION.cff`, `doc/README.md`, `doc/index.rst`,
  `doc/installing.rst`, `doc/faq.rst`, `doc/whatsnew/index.rst`. All succeeded.

### Deviation: README.md promoted from `context` to `rules`

`seed_sources.py` classifies `README.md` as `context` ("check for canonical test
invocation"). On this repo that default would have discarded four of the five rules: the
README's Testing section is where seaborn states its test invocation, its style
conformance requirement and its two local-check routes, and `.github/CONTRIBUTING.md`
states none of them. The manifest overrides the seeded role for two paragraphs of that one
section, argued from the scope test rather than the file's name. Everything else in
`README.md` stays out (X-INSTALL / X-ISSUE / X-NARRATIVE).

## ID prefix and range

`MWASKOM`, from the SWE-bench instance prefix in `cases-all.txt`
(`mwaskom__seaborn-3069`, `mwaskom__seaborn-3187` — 2 instances, as §3 says). Not
`SEABORN`. IDs run **MWASKOM-C001 … MWASKOM-C005**, contiguous, no gaps, no repeats.

## Conflict tiebreaker

Fixed before classification, per §4: **the stricter statement governs; the weaker one is
N3 with the conflict named in `Notes`.**

**It resolved nothing, because seaborn has no intra-repo strength conflict.** The one pair
that looks like a candidate is MWASKOM-C003 (`make lint`) against MWASKOM-C004
(`pre-commit`). They are not two statements of one obligation at different strengths: the
README presents them as two sanctioned routes to the same check, which is what makes C003
a D2 demotion rather than a conflict, and both land on `maybe` anyway. Nor is C003 an N3
duplicate of C002: C002 is a static read of the diff against the ruff configuration, C003
is a trajectory read of whether the check was invoked. Different artifacts, so both stand.
Zero N3 rows in the sheet.

## Checkpoint 1

Full result is at the foot of `mwaskom-manifest.md`; all five boxes tick. The two failure
modes §4 calls out were checked adversarially:

- **Maintainer/triage pages marked Full.** Nothing is marked Full at all. `SECURITY.md`
  (X-ISSUE) and `doc/whatsnew/index.rst` (X-MAINT) are Exclude; the only two rule-bearing
  sources are Partial.
- **Partial rows that do not name their in-scope sections.** Both Partial rows name the
  in-scope paragraphs *and* every excluded section with a code each.

The place this manifest could have leaked in the other direction is `README.md`; the
promotion is documented above and confined to two quoted paragraphs.

## Checkpoint 2

- Row count: 5. Plausible for this repo, and the reasoning is in "Why the count is 5" below.
- `Section context` and `Notes` populated on all 5 extraction rows, none boilerplate.
- IDs contiguous, C001–C005.
- Every `Source` starts with `http`.
- Every `Shared Category` is one of the eight, spelled `Language and framework style`
  where the closed list uses it (that bucket is empty here).
- **Spot-checks of `Original text` against the source.** The sheet is 5 rows, so all five
  were checked rather than a sample: **MWASKOM-C001, C002, C003, C004** against
  `README.md` and **MWASKOM-C005** against `.github/CONTRIBUTING.md`, both pulled raw at
  `f04b6cd5484267a0885d1fed068e99dff3a1b226` and compared by exact substring match. All
  five matched byte-for-byte.
- Mid-sentence quotes: MWASKOM-C003's `Original text` is a five-word sentence whose scope
  lives entirely in the preceding one. That preceding sentence is quoted in full in
  `Section context`, and it is also MWASKOM-C002's `Original text`.

## Zero-rule in-scope and near-scope sources

Recorded so a source that produced nothing is distinguishable from one that was forgotten.

- **`.github/CONTRIBUTING.md` — General support and Reporting bugs: zero rules.** X-NARRATIVE
  and X-ISSUE. Despite the filename, roughly 300 of this file's 383 words constrain an issue
  body: the four "must include" bullets, the synthetic-data preference, "do not share data as
  a pickle file", searching before filing, and reproducing in matplotlib first. None can be
  violated by a diff, a commit message or a file the agent writes. Only the New-features
  clause survives, as MWASKOM-C005.
- **`doc/README.md` — zero rules.** Every imperative ("install `seaborn[stats,docs]`", "set
  `NB_KERNEL`", "run `make notebooks html` from the `doc` directory", "`make clean`") is a
  build or environment action: X-INSTALL. It states no docs style or placement rule, which
  is why the Documentation and docstrings bucket is empty.
- **`doc/installing.rst` — zero rules.** X-INSTALL, plus a "Getting help" section that
  restates the CONTRIBUTING.md bug-report requirements near-verbatim. Fetched precisely to
  check whether it added anything; it does not.
- **`doc/faq.rst` — zero rules.** X-NARRATIVE, user-facing throughout.
- **`doc/whatsnew/index.rst` — zero rules.** Fetched to look for a changelog-fragment
  obligation. None exists anywhere in the repo.
- **`SECURITY.md` — zero rules.** X-ISSUE.
- **The four config sources — zero rows by design.** `.pre-commit-config.yaml`,
  `pyproject.toml`, `Makefile` and `.github/workflows/ci.yaml` are `context-only`. They
  decide the auto-fix reading on C002/C004 and supply the M3 route on C001/C002, but
  cataloguing them would be cataloguing a config.

### Deliberately not extracted, and why

- **"Seaborn supports Python 3.10+" (`README.md`, Dependencies).** A diff *could* violate
  it and CI enforces it with a seven-version matrix, but the sentence is a description of
  the library addressed to people installing it, not an obligation addressed to a
  contributor. Compare `ASTROPY-C076`, which was extracted because astropy's prose says
  "All code **must** be compatible with the versions of Python indicated by
  ``requires-python``". seaborn's prose says no such thing. The version floor lives only in
  `pyproject.toml` and `ci.yaml`, both config.
- **The typecheck gate.** `.github/workflows/ci.yaml` has a `typecheck` job running
  `make typecheck` (`ty check`, scoped by `[tool.ty.src]` to `seaborn/_core`, `_marks`,
  `_stats`), and `.pre-commit-config.yaml` installs a `ty` hook. **No prose anywhere in the
  repository mentions type checking.** Config produces no rows, so seaborn has a real
  condition of acceptance that its documentation never states. That gap is a finding, not
  an omission.
- **`make docs` and the `build-docs` CI job.** Same shape: a gate in config with no prose
  behind it.

## Prompt-injection check (§8 / §4.1)

**None found.** Every fetched file was read in full by a human-equivalent pass and then
scanned mechanically for the astropy canary's shape — "ignore previous/prior instructions",
"disregard", "you are an AI/agent/assistant", "system prompt", "canary", "instructions to
the agent", "if you are a bot", "do not reveal" — across `README.md`,
`.github/CONTRIBUTING.md`, `SECURITY.md`, `doc/README.md`, `doc/installing.rst`,
`doc/faq.rst`, `doc/index.rst`, `.pre-commit-config.yaml`, `pyproject.toml`, `Makefile`,
`.github/workflows/ci.yaml` and `CITATION.cff`. Zero hits. seaborn has no PR or issue
template, which on the other repos is where such text lives. Nothing in seaborn's
contribution text was treated as an instruction to this agent; all of it was treated as
material to extract rules from.

## Why the count is 5

seaborn's total contribution-facing prose is 706 words — `.github/CONTRIBUTING.md` (383)
plus `README.md` (323) — against sphinx-doc's 3.2k and astropy's 30.5k. Of those 706, the
in-scope portion is **157 words**: the README's Testing section minus its dependency
sentence (94) and the CONTRIBUTING New-features clause (63). Everything else is bug
reporting, installation, citation or usage.

At 706 words the density is 7.1 rules per 1,000 words, inside the 3–40 band the audit
calibrates from django and sympy and comfortably below psf's thin-repo figure. The corpus
is small because the repository is: no PR template, no issue templates, no code of conduct,
no AI policy, no style guide, no commit convention, no changelog-fragment process, and a
`CONTRIBUTING.md` that is a bug-reporting guide. **The sheet was not padded to make the row
count look respectable, and atomicity was not lowered to split rules further.** Two `must`
rules reach the scored batch.

## Audit output (§7)

Calibrated first on `--repo django`, which failed exactly the three checks §7 predicts
(2 Schema/vocabulary — 11 `should` rows; 4 NaiveStrength — 0/143; 6 Reasoning uniqueness —
one Conclusion string duplicated across rows) and passed the other seven. `tools/audit_rules.py`
was used unmodified; nothing was blunted.

```
  audit: mwaskom-rules.xlsx  (5 rows)

  1  Gate (tools/corpus.py)  PASS  tools/corpus.py exits 0
  2  Schema and vocabulary   PASS  11 columns in order; vocabulary, blanks and taxonomy clean
  2b ID prefix               PASS  all 5 IDs match ^MWASKOM-C\d{3}$
  3  Judgment invariant      PASS  0 judgment+Care rows (1 judgment rows, all Not Care)
  4  NaiveStrength present   PASS  NaiveStrength on 100% of 5 rows
                                   NaiveStrength != Strength on 1 of 4 Care rows: {'must -> maybe': 1}
  5  Promotion direction     PASS  promotions maybe->must: 0; demotions must->maybe: 1; prohibited->must folds: 0; unchanged: 3
  6  Reasoning uniqueness    PASS  5 distinct Conclusion values; 5/5 rows carry a Conclusion:
  7  N1 vs N2-N4 balance     PASS  N1 0 | N2 1 | N3 0 | N4 0  (N1 vs N2-N4: 0/1)
  8  Row-count plausibility  PASS  5 rows over 706 words = 7.1 rules/1k words (band 3.0-40.0)
  9  ID contiguity           PASS  C001-C005, no gaps, no repeats

  10/10 checks pass
```

`python rules/build_contributing_rules.py --repo mwaskom` also runs clean and emits the
two `must` rules under two categories, which confirms the `Language and framework style`
spelling and the `repo.conf` keys.

### Check 5 — the direction question

**One demotion, zero promotions.** django ran promotions-only (29 `maybe` → `must`);
seaborn's single strength movement runs the other way, MWASKOM-C003 `must` → `maybe`.

This is the rubric behaving as written, not classification drift. "Run `make lint` to
check." is an unhedged imperative naming an exact command — M4, naive reading `must`. The
sentence immediately after it offers pre-commit as an equally sanctioned route to the same
check, which is D2, and D2 beats M4 by the precedence table. The demotion is produced by
`Section context` doing exactly the job the workflow says it exists for: the clause alone
reads `must`, and only the surrounding sentence decides otherwise. Three of the four Care
rows are unchanged from their naive reading, so the sample supporting this is one row and
should be read as such.

### Check 7 — N-balance

`N1 0 | N2 1 | N3 0 | N4 0`. N1 is zero, which on every other repo in this run is the
largest bucket. The reason is structural rather than a coding choice: N1 fires on rules
governing artifacts the run never creates — pull requests, review threads, branch history,
CI services — and **seaborn documents no such rule anywhere**. Its `CONTRIBUTING.md` has no
pull-request section, and there is no PR template to supply one. The PR-object material
that becomes N1 on django (18 rows) and psf (15) simply is not written down here. N1 is
therefore not swallowing N4 rows; there are no N4 rows to swallow, because no seaborn rule
is conditional on a fact outside the agent's own behaviour.

## Things guessed, cross-referenced to `low_confidence:`

- **MWASKOM-C005** carries `low_confidence: borderline X-NARRATIVE; kept in scope because a
  diff adding an unrelated feature could violate it.` The clause states maintainer
  receptivity rather than a contributor obligation, and marking the whole New-features
  section X-NARRATIVE would have been defensible. It was kept in scope on the psf precedent
  (`PSF-C019`, requests' feature-freeze clause, extracted and then N2'd for the same
  reason), so that the two repos treat the same shape of prose the same way. It is Not Care
  either way, so the decision moves no `must` row.
- **MWASKOM-C004's `PassType: never fires`** is a ruling, not a guess: §4.1 reads
  "never fires" as gated on an *agent* choice, and choosing pre-commit over `make lint` is
  the contributor's own choice, not the task's. Recorded here because it is the only place
  that ruling changed an outcome on this repo.
- Nothing else was guessed. Every quote is verbatim from a pinned raw file, and every
  claim about a file's contents in the manifest comes from a fetch recorded above.

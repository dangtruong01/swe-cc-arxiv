# pydata/xarray — run log

Slug `pydata` (confirmed against `cases-all.txt`: 22 instances, all `pydata__xarray-*`).
ID prefix `PYDATA`. Final range `PYDATA-C001` – `PYDATA-C139`, contiguous, no repeats.
C001–C121 are the original run, recorded below and frozen; C122–C139 were appended later
from two off-nav agent-instruction files (see *Append*, at the end of this log).

## Phase 0 — docs root and discovery

**Docs root (pinned):** <https://docs.xarray.dev/en/latest/contribute/>
**Version string: 2026.7.1.dev28+ge902fe896.**

How it was resolved. `seed_sources.py` printed
`Version: UNRESOLVED (could not fetch: <urlopen error Tunnel connection failed: 403 Forbidden>)`
— the device's egress allowlist does not include `docs.xarray.dev`, though it does include
`api.github.com` and `raw.githubusercontent.com`. Per the standing ruling this is expected
and is not a stop condition, so the version was resolved by hand: the rendered pages carry
`meta-docsearch:version: 2026.7.1.dev28+ge902fe896`, read off
`/en/latest/contribute/contributing.html`, `/en/latest/contribute/ai-policy.html` and
`/en/latest/contribute/index.html`. All three agree, so there is no build split of the kind
astropy hit and no `VERSION MISMATCH`.

The version string is unusually strong as a pin: its local part `ge902fe896` is the git hash
of the build. `GET api.github.com/repos/pydata/xarray/git/trees/e902fe896` resolves to
`e902fe89698be3061ba161c5894826985e45e147`, and `doc/contribute/contributing.rst` is
byte-identical at that commit and at `main` at pull time. Every `Original text` value in the
sheet was therefore taken from the `.rst`/`.md` sources at `e902fe896…`, which is provably
the same source the rendered pages were built from.

`/en/latest/` is the dev build; `/en/stable/` was never fetched as a source. Note that the
repository's own `CONTRIBUTING.md` and `README.md` still link the `/en/stable/` path, and
several in-page links inside `contributing.rst` point at `docs.xarray.dev/en/stable/...`
(some of them at the pre-reorganisation URL `stable/contributing.html`). Those stale links
are quoted where they appear inside a rule's `Original text`; none of them was followed.

**Invocation** (no `GITHUB_TOKEN` was available in this environment; one repo, one tree call):

```
python3 rule-extraction/seed_sources.py pydata/xarray --ref main \
    --docs https://docs.xarray.dev/en/latest/ \
    -o rules/pydata/pydata-raw-sources.md
```

`--ref main` was passed explicitly (xarray's default branch is `main`, so the script's
default was correct, but passing it avoids the zero-hit self-heal path). The tree API
answered normally — **no `tree API unavailable`, no `Falling back to probe list`**, `truncated`
false. 11 candidate sources, all fetched `ok`, no `FETCH FAILED`:

`.github/ISSUE_TEMPLATE/bugreport.yml`, `.github/ISSUE_TEMPLATE/config.yml`,
`.github/ISSUE_TEMPLATE/misc.yml`, `.github/ISSUE_TEMPLATE/newfeature.yml`,
`.github/PULL_REQUEST_TEMPLATE.md`, `.pre-commit-config.yaml`, `CODE_OF_CONDUCT.md`,
`CONTRIBUTING.md`, `README.md`, `doc/contribute/contributing.rst`, `pyproject.toml`.

**One discovery gap, closed by hand.** None of `seed_sources.py`'s `PATTERNS` matches
`doc/contribute/ai-policy.md`. It was found by listing `doc/contribute/` through the GitHub
contents API, and it is the second-largest rule source here (613 words, 16 rows). The script
is not at fault — an AI policy under `doc/` is a new shape — but a repo assessed from the
bundle alone would have missed it.

The PR template carries 3 HTML comment blocks and 4 of its 11 rules live inside them, so it
was extracted from the bundle rather than from GitHub's rendered view.

## Phase 1 — manifest

See `pydata-manifest.md` for the table and the Checkpoint 1 result (all five checks PASS,
three declared not-fetched files). Three sources produced rows:

| Source | Rows |
|---|---|
| `contribute/contributing.html` | 94 (C001–C094) |
| `contribute/ai-policy.html` | 16 (C095–C110) |
| `.github/PULL_REQUEST_TEMPLATE.md` | 11 (C111–C121) |

### Zero-rule in-scope material, with reasons

Every one of these sits inside an in-scope section and was read; none produced a row.

- **Overview, code-of-conduct sentence.** "Everyone within the community is expected to abide
  by our code of conduct." X-GOV: conduct, not a property of a diff, a commit or a file.
- **Where to start?** How to pick a labelled issue, plus "The xarray project does not assign
  issues." Descriptive.
- **Install pre-commit hooks / Code Formatting: `git commit --no-verify`.** Stated twice; both
  are permissions ("If you want to commit without running pre-commit hooks, you can…"), not
  obligations. Recorded as section context on C007 and C041 instead.
- **Creating a development environment, the `.. note::`.** "For small changes, such as fixing a
  typo, you don't necessarily need to build and test xarray locally." A permission. It is the
  D2 grant that decides C062's strength, so it is quoted in that row's Section context.
- **About the xarray documentation, MyST cell tags.** "this line is optional" — explicitly
  optional, no obligation.
- **How to build the documentation, `pixi run doc-clean`.** An alternative invocation of the
  build already rowed at C028.
- **Running the test suite, `pytest-xdist`.** "one can speed up local testing… by running
  pytest with the optional -n argument". Optional performance advice.
- **Testing With CI, the `.. note::`.** Describes GitHub Actions cancelling superseded runs.
  Describes the service's behaviour; imposes nothing on the contributor.
- **Committing your code, "Optionally, a commit message body."** Explicitly optional, and no
  constraint is stated on a body that exists.
- **PR template, first HTML comment.** "Feel free to remove check-list items aren't relevant to
  your change." A permission; recorded as section context on C111–C114.
- **AI policy preamble.** "this policy applies regardless of whether the code was written by
  hand, with AI assistance, or generated entirely by an AI tool." A scope statement for the
  rules that follow; recorded as their section context.
- **AI policy, "Maintainers reserve the right to delete or hide comments…".** X-MAINT.

## Phase 2 — extraction

Worked one source at a time, largest first (contributing.rst 5,771 words → ai-policy.md 613
→ PR template ~120), restating the manifest row before each. In-scope word count used for
the plausibility check: **6,384** (the two doc sources; the template is not counted).

`pydata-extraction-frozen.csv` was written **before any classification** and has not been
edited since. It carries the Part 2 working columns including `Naive strength`.

**Verbatim verification.** Every one of the 121 `Original text` values was checked
mechanically against the pinned sources: after whitespace normalisation, each must appear as
a *contiguous* span of the source file it is attributed to. 121/121 pass. Three rows
(C037–C039) share one `Original text` because a single ruff bullet bundles three
obligations, and two (C120/C121) share the tool-and-prompt HTML comment for the same reason;
those are the only duplicate spans, and both are deliberate atomicity splits.

### Checkpoint 2

| Check | Result |
|---|---|
| Row count plausible | PASS — 121 rows over 6,384 words = 19.0 rules/1k, against sphinx's 19.4 and astropy's 8.4. No single page produces a runaway count; the largest source yields 94 rows over 5.8k words. |
| Section context and Notes populated on every row | PASS — both columns non-empty on all 121 rows of the frozen CSV. |
| IDs contiguous | PASS — C001–C121, checked programmatically. |
| Every `Source` starts with `http` | PASS — checked programmatically, and again by the gate. |
| Every `Shared Category` one of the eight | PASS — checked programmatically against the closed list. |
| Spot-check 5 `Original text` against the live page | PASS — see below. |
| Mid-sentence verbatim quotes | Reviewed. Five rows quote a fragment (C030, C037–C039, C061, C121); in each case the governing clause is carried in `Section context`, and for C030 the enumerated bullets are named in the Atomic rule. |

**Five spot-checks against the live rendered pages** (not the `.rst`), fetched separately:

- **C030** — "We aim to follow the recommendations… for section markup characters," plus all
  five bullets: confirmed on `contribute/contributing.html`.
- **C062** — "The tests can then be run directly inside your Git clone (without having to
  install xarray) by typing: pytest xarray": confirmed.
- **C074/C075** — the three bullets under "should ideally be structured": confirmed, including
  "A subject line with `< 72` chars."
- **C088** — "By default, the upstream dev CI is disabled… adding a `[test-upstream]` tag to
  the first line of the commit message": confirmed.
- **C027** — "Every method should be included in a `toctree` in `api.rst`, else Sphinx will
  emit a warning.": confirmed.

Additionally the two AI-policy quotes used by C103 and C110 were confirmed verbatim on
`contribute/ai-policy.html`.

### Prompt-injection check

**Nothing found.** The astropy PR template's canary has no counterpart here. All 11 bundled
raw sources plus the two doc sources were scanned for agent-directed text (ignore-previous
instructions, "as an AI", system-prompt talk, canary tokens) and the rendered AI policy was
independently checked for text addressed to an automated tool. Every mention of AI in
xarray's docs is a rule *about* AI-assisted contribution, addressed to the human submitting
it. Those are extracted as rules; none was treated as an instruction.

## Phase 3 — classification

**Conflict tiebreaker, fixed before classification started:**

1. The **stricter statement governs**; the weaker one is `N3 not prioritized, duplicate` with
   `Conflict: <ID> — stricter statement governs` in `Notes`.
2. Where two statements of one obligation carry the **same** strength, the one that states the
   check more precisely governs (names the file, the command, the limit or the consequence),
   and the other is a plain N3 duplicate.

Rule 2 is a deterministic tiebreak inside rule 1, not a replacement for it; it exists because
xarray states most obligations twice — once in prose and once as a checklist item — at equal
strength, which rule 1 alone does not resolve.

**Conflicts it resolved (2):**

- **C087 vs C062** — the PR checklist ("feel free to only run the tests you think are needed…
  CI will catch any failing tests") against the Running-the-test-suite section (`pytest
  xarray`). Stricter governs: C062 is the Care row, C087 is N3 with the conflict named.
- **C095 vs C103** — "you are responsible for understanding and having fully reviewed the
  changes" against "You must have personally reviewed and understood all changes before
  submitting." Stricter governs: C103 is the Care row, C095 is N3 with the conflict named.

**The other 15 N3 rows are plain duplicates** (17 N3 rows less the 2 conflicts above), resolved by rule 2 where the two statements were equally strong: C017→C062, C034→C037–C040,
C044→C042, C059→C050, C061→C049, C079 (union of every other row), C086→C112, C090→C037,
C104→C103/C062, C109→C103, C113→C069, C114→C027, C116→C001, C118→C062, and C001→C095–C110.
In every case the surviving row is the one that names the file, command or consequence.

Batches of 25 across the whole sheet (C001–C025, C026–C050, …), never per page — which is
what surfaced C113/C069 and C114/C027, whose members sit in different sources.

**A note on C062, the one demotion.** Naive reading `must`, final `maybe` via D2. The clause
itself is an unhedged instruction, but the same document sanctions deviation from it twice:
the dev-environment note ("For small changes, such as fixing a typo, you don't necessarily
need to build and test xarray locally") and the PR checklist item that defers the remainder
to CI. The conflict tiebreaker decides *which row survives*; D2 decides *what strength the
survivor carries*. The row is flagged `low_confidence`, because the demotion rests entirely
on section context and a reader who quoted only the clause would grade it `must`.

## Phase 4 — workbook

`pydata-rules.xlsx`, three tabs, 11 columns in order, header fill `FF2F4858` white bold,
body top-aligned and wrapped, frozen at `A2`, autofilter `A1:K122`, django's column widths.
`Category Aggregation`'s last header is `Maybe (Care)`. The
`Shared Taxonomy (Before-After)` tab's Django columns are computed at build time by reading
`rules/django/django-rules.xlsx` directly (143 rows / 89 Care, which matches that file);
nothing was copied from a previous sheet. `repo.conf` written on django's model.

## Phase 5 — audit (§7)

`python tools/audit_rules.py --repo pydata --words 6384` — **10/10 PASS**.

```
  1  Gate (tools/corpus.py)  PASS  tools/corpus.py exits 0
  2  Schema and vocabulary   PASS  11 columns in order; vocabulary, blanks and taxonomy clean
  2b ID prefix               PASS  all 121 IDs match ^PYDATA-C\d{3}$
  3  Judgment invariant      PASS  0 judgment+Care rows (12 judgment rows, all Not Care)
  4  NaiveStrength present   PASS  NaiveStrength on 100% of 121 rows
                                   NaiveStrength != Strength on 10 of 41 Care rows:
                                   {'maybe -> must': 8, 'must -> maybe': 1, 'prohibited -> must': 1}
  5  Promotion direction     PASS  promotions maybe->must: 8; demotions must->maybe: 1;
                                   prohibited->must folds: 1; unchanged: 31
  6  Reasoning uniqueness    PASS  121 distinct Conclusion values; 121/121 rows carry a Conclusion:
  7  N1 vs N2-N4 balance     PASS  N1 52 | N2 11 | N3 17 | N4 0  (N1 vs N2-N4: 52/28)
  8  Row-count plausibility  PASS  121 rows over 6384 words = 19.0 rules/1k words (band 3.0-40.0)
  9  ID contiguity           PASS  C001-C121, no gaps, no repeats
```

Calibrated first on `--repo django`: it failed exactly the three known checks (2 vocabulary,
4 `NaiveStrength`, 6 reasoning uniqueness) and passed the other seven. The checker was used
unmodified.

**Check 5, direction.** 8 promotions, 1 demotion, 1 prohibited→must fold. The single demotion
(C062) is the rubric behaving as designed rather than classification drift: D2 fired on an
exception stated outside the quoted clause, which is exactly the case the strength rubric
warns to read the whole section for. Django ran one-directional; xarray cannot, because its
guide repeatedly grants the deviation in a different section from the obligation.

**Check 7, N1 balance.** N1 52 against 28 for N2–N4, a higher N1 share than django's 30/24.
This is a property of the source, not a swallowed N4: xarray's guide is a step-by-step
git/GitHub walkthrough (fork, clone, remote, tags, branch, push, compare view, open PR,
delete branch), and 30 of the 52 N1 rows are steps that need a fork, a branch topology, a PR
object or the CI service. **N4 is genuinely 0.** Every conditional rule in this repo is
conditioned on what the *diff* contains (docs touched, signature changed, new file added,
enhancement vs fix), which the astropy ruling routes to `checked`, not on a fact about the
contributor. xarray has no first-time-contributor, `AUTHORS`, `.mailmap` or account-identity
rule of the kind that produced django's and sympy's N4 rows. Each N1 row names the missing
artifact in its `Conclusion`, so the claim is auditable row by row.

## Things guessed, cross-referenced to `low_confidence:`

Exactly one row carries `low_confidence:` — **C062**, for the reason given above.

Two further judgment calls are recorded here rather than as `low_confidence`, because they
are scope decisions rather than uncertain gradings:

- **The Internals section (10 pages, ~10.4k words) was excluded**, on the ground that its
  conformance obligations govern code in third-party packages, not contributions to this
  repository — `how-to-add-new-backend` says so in its opening sentence. Had it been in
  scope it would have added an estimated 8–12 API-conformance rows and pushed the repo's word
  budget from 6.4k to ~17k. A reviewer who disagrees can add them without touching any
  existing row: the IDs would start at C122.
- **`PassType: never fires` was used on three rows** (C075, C088, C089) where the *action* is
  an agent's option — writing a commit body, adding `[test-upstream]`, adding `[skip-ci]` —
  even where the surrounding condition is task-determined. Read narrowly per the astropy
  ruling: it is the tag that is optional, not the documentation-only-ness of the commit.


---

# Append: `CLAUDE.md` and `xarray/tests/CLAUDE.md` (C122–C139)

Rows `PYDATA-C122` – `PYDATA-C139`, 18 of them, appended to a closed corpus. **Nothing in
C001–C121 was renumbered, reworded, reclassified or deleted**; the append script asserted
the first 121 rows byte-for-byte identical (header included) after the write, and re-asserts
contiguity `C001–C139`. `pydata-extraction-frozen.csv` was appended to, never rewritten:
the pre-append bytes are still a literal prefix of the file, which the append verified.

## Why the two sources were missed

Both are agent-instruction files, which Part 1's traversal table puts in scope *wherever
they exist, even though they sit outside the docs navigation*. Neither is reachable the way
the first pass looked:

- **Nothing in `doc/` links either file.** The manifest was walked from the docs root, and
  neither `CLAUDE.md` appears anywhere in the contributor guide's navigation or prose.
- **`seed_sources.py` does not match them.** None of its PATTERNS matches a bare
  `CLAUDE.md` at the repository root, and none walks a source subdirectory such as
  `xarray/tests/`, so neither appeared in the 11-file bundle. This is the *same* discovery
  gap that hid `doc/contribute/ai-policy.md` in the first pass, which that run closed by
  listing `doc/contribute/` through the contents API — a fix that by construction could not
  reach a file at the repository root or under `xarray/`.

Both were fetched raw from `raw.githubusercontent.com/pydata/xarray/main/…` (1,309 and
3,315 bytes) and are reproduced verbatim in `pydata-raw-sources.md`, each with a manifest
row. All 18 `Original text` values were re-verified mechanically against those bytes:
after whitespace normalisation each is a contiguous span of the file it is attributed to,
18/18.

**`AI_POLICY.md` was fetched and produced no rows.** It is 28 bytes and its entire content
is the path `doc/contribute/ai-policy.md` — a pointer to the page already extracted as
C095–C110. Re-extracting it would have duplicated 16 rows. It is recorded in the manifest
as `context-only`.

## The one classification ruling

`CLAUDE.md` closes with *"When creating commits, always include a co-authorship trailer:
`Co-authored-by: Claude <noreply@anthropic.com>`"*. That row (**C131**) is
`N4 not prioritized, trigger`, **not Care**.

The commit and its message do exist in the run, so N1 does not fire, and the trailer would
be trivial to read off the message. What decides it is the N1-vs-N4 test's load-bearing
clause: applicability turns on the agent's *identity*, a fact outside the agent's own
behaviour — the same shape as django's C093 (`user.email` must match your GitHub account).
The runs under this rig use non-Claude models, for which emitting that trailer would be a
false attribution, so compliance would be the *undesirable* behaviour. Routing it N4 keeps
the corpus model-independent. It is the corpus's first and only N4 row; the original run
recorded N4 as genuinely 0, and that claim was correct for the sources it saw.

**The same addressee test was applied to every other new row**, and fires nowhere else. The
sign-off half of C128 is the near miss: the string it models (`[This is Claude Code on
behalf of Jane Doe]`) is assistant-specific, but the rule's artifact — a GitHub comment —
does not exist in the run at all, so N1 fires first and the residual N4 is named in the
row's `Conclusion`, per Rubric A's both-routes instruction.

## The three GitHub-interaction rules, checked against Rubric A rather than assumed

C128 (never impersonate the user), C129 (never open issues or PRs unless instructed) and
C130 (never post progress comments unless instructed) are all `N1 not possible`. Verified
against the *what the run produces* table rather than taken on faith: PR object, review
thread and a second human are all on the "doesn't exist" side, and the run ends at a working
tree plus one commit. There is no comment, issue body or PR body in which impersonation
could occur or a sign-off be found. Each row names its missing artifact in its own
`Conclusion`.

## The remaining rules were classified on their merits

Nothing was given special treatment for living in a Claude-named file. The style and test
conventions in the two files are ordinary repo conventions:

| Rows | Content | Outcome |
|---|---|---|
| C125 | imports at the top of the file | Care, static, `maybe` (D2) |
| C132 | `@requires_*` decorators instead of a conditional `if` | Care, static, `must` (M1) |
| C133 | xarray's dask helpers instead of importing `dask.array` | Care, static, `must` (M4) |
| C134 | no `pytest.mark.skipif` inside `parametrize` | Care, static, `must` (M2) |
| C135 | `pytest.importorskip` for in-function imports | Care, static, `must` (M4) |
| C138 | parametrize over `available_implementations()` | Care, static, `maybe` (D3) |

Six Care rows, all `static` and all AST- or diff-readable, which is what the shape of the
material predicts.

**C125 is the append's one demotion** (naive `must` → `maybe`, D2), and it carries the only
new `low_confidence:` flag. The clause *"Always place imports at the top of the file"* is
unhedged, but the very next bullet reopens it — *"unless there's a specific reason (e.g.,
circular import avoidance, optional dependencies in TYPE_CHECKING)"* — and the `e.g.` leaves
that list open, which is exactly D2's "an exception the docs leave open destroys the single
right answer". This is the same pattern as C062 and it takes the corpus from one demotion to
two. Worth recording that the repo's own tooling agrees the rule is unenforced: `pyproject.toml`
puts **both** `E402` and `PLC0415` in ruff's ignore list, so no hook checks or repairs it
(`Auto-fix risk: No, check only`). C126, the negative restatement carrying that exception, is
the N3 row.

## Duplicates: checked against the existing sheet before adding, not after

Seven of the eighteen are `N3 not prioritized, duplicate`, every one of them against a row
from the *original* corpus, resolved with the run's already-fixed tiebreaker (stricter
governs; at equal strength the more precise statement governs):

| New row | Duplicates | Same evidence |
|---|---|---|
| C122 `uv run pytest xarray -n auto` | C062 | the local test run. The divergence is the invocation — `uv` here, Pixi in the guide — not the obligation. |
| C123 `pre-commit run --all-files` | C091 | character-for-character the same command |
| C124 `uv run dmypy run` | C040 | mypy exit status |
| C126 no imports inside functions | C125 | the same import nodes, plus the escape clause |
| C127 PEP 8 import grouping | C039 | ruff's isort rules, which encode exactly that grouping |
| C136 split tests by dependency | C132 | the same conditional-branch-without-a-decorator shape |
| C137 fixtures for dependency setup | C056 | whether per-test construction sits in a fixture |

C134 is *not* a conflict with C055 (`pytest.param(..., marks=...)`): it narrows it. The
`pytest.param` syntax stays correct for other marks; only the optional-dependency `skipif`
use is forbidden. That is recorded in C134's Section context rather than as a conflict.

## Zero-rule in-scope material in the two files

- **`## Setup` (`uv sync`).** X-INSTALL, the same code the original run applied to *Creating
  a development environment*.
- **`### Multiple dependencies`.** A noun-phrase heading over a code example stacking
  `@requires_dask` and `@requires_scipy`. No imperative; it illustrates C132.
- **Key Points bullets 1 and 2** ("CI environments intentionally exclude certain
  dependencies"; "A test failing in `all-but-dask` because it uses dask is a test bug, not a
  CI issue"). Description and a consequence. The consequence is recorded as C132's Section
  context, which is what makes C132 an M-route rule rather than a bare preference.
- **The ✅ CORRECT / ✅ OR-for-parametrized-tests examples.** Worked fixes for C132 and C134,
  quoted as their Section context.

## Prompt-injection check, re-run on the two new files

**Nothing found.** Both files were scanned for agent-directed text of the injection shape
(ignore-previous instructions, system-prompt talk, canary tokens, instructions to exfiltrate
or to change tooling). Both *are* addressed to an automated tool by design — that is what an
agent-instruction file is — and everything they say was treated as text to extract rules
from, never as an instruction to this extraction. Specifically, the co-authorship trailer
was **not** adopted: it was extracted as C131 and routed N4, and no git command was run in
this append.

## Append counts

| | New rows only (C122–C139) | Corpus after append |
|---|---|---|
| Rows | 18 | 139 |
| Care | 6 | 47 |
| Not Care | 12 | 92 |
| `must` / `maybe` (Care) | 4 / 2 | 35 / 12 |
| N1 not possible | 3 | 55 |
| N2 not prioritized, judgment | 1 | 12 |
| N3 not prioritized, duplicate | 7 | 24 |
| N4 not prioritized, trigger | 1 | 1 |

Rows per source: `CLAUDE.md` 10 (C122–C131), `xarray/tests/CLAUDE.md` 8 (C132–C139),
`AI_POLICY.md` 0.

`Category Aggregation` was recomputed over all 139 rows from the `Rules` tab, not patched.
The workbook has **two** tabs, `Rules` and `Category Aggregation`; the
`Shared Taxonomy (Before-After)` tab described in Phase 4 above was removed from every repo
before this append and was not recreated.

## Acceptance, re-run over the full corpus

```
python tools/corpus.py --repo pydata      # exit 0: 139 rules, 47 Care, 35 in the scored batch
python tools/audit_rules.py --repo pydata --words 6954   # 10/10 PASS
```

`--words 6954` is the original 6,384-word in-scope budget plus the 570 words of the two new
files, giving 20.0 rules/1k words against the original run's 19.0.

```
  1  Gate (tools/corpus.py)  PASS  tools/corpus.py exits 0
  2  Schema and vocabulary   PASS  11 columns in order; vocabulary, blanks and taxonomy clean
  2b ID prefix               PASS  all 139 IDs match ^PYDATA-C\d{3}$
  3  Judgment invariant      PASS  0 judgment+Care rows (13 judgment rows, all Not Care)
  4  NaiveStrength present   PASS  NaiveStrength on 100% of 139 rows
                                   NaiveStrength != Strength on 12 of 47 Care rows:
                                   {'maybe -> must': 8, 'must -> maybe': 2, 'prohibited -> must': 2}
  5  Promotion direction     PASS  promotions maybe->must: 8; demotions must->maybe: 2;
                                   prohibited->must folds: 2; unchanged: 35
  6  Reasoning uniqueness    PASS  139 distinct Conclusion values; 139/139 rows carry a Conclusion:
  7  N1 vs N2-N4 balance     PASS  N1 55 | N2 12 | N3 24 | N4 1  (N1 vs N2-N4: 55/37)
  8  Row-count plausibility  PASS  139 rows over 6954 words = 20.0 rules/1k words (band 3.0-40.0)
  9  ID contiguity           PASS  C001-C139, no gaps, no repeats
```

Plus two assertions specific to an append, printed by the append script:

```
first 121 rows + header unchanged: TRUE
IDs contiguous C001-C139: TRUE
pydata-extraction-frozen.csv: pre-append bytes are still a prefix of the file: TRUE
```

## Things guessed in the append

- **C125**, `low_confidence:` — graded `maybe` on the neighbouring bullet's open-ended
  exception rather than on its own clause, which reads as an unhedged `must`. Second row in
  the corpus to carry the flag, and for the same reason as C062.

Two further judgment calls, recorded here rather than as `low_confidence:` because they are
scope decisions:

- **C122–C124 were extracted as rows rather than dropped as command reference.** They are
  bare code blocks under `Run tests` and `Linting & type checking`, with no "you must".
  Extracting and routing them N3 records that they were read; dropping them would have made
  a source we consulted and a source we forgot look identical. All three resolve against
  existing rows and none changes the scored batch.
- **`uv` versus Pixi.** `CLAUDE.md` prescribes `uv sync` / `uv run pytest`, while the
  contributor guide prescribes Pixi throughout. This is a real divergence in the repository's
  own instructions, but it is a divergence in *how* to invoke a step, not in whether the step
  is owed, so it produced no strength conflict — only the N3 note on C122.

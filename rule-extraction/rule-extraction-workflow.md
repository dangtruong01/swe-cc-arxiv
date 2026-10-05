# Rule Extraction Workflow (Instructions to LLMs + Human in the Loop)

Documented below is how to take a SWE-bench verified repo and get a classified rule sheet out of it. For this, you would need to run two different stages. You would be populating one Excel workbook with two tabs (sheets).

**Format standard:** `rules/sympy/sympy-rules.xlsx`. Column names, column order, and layout are fixed by that file. Do not invent columns.

Example Final Output (Unedited)

> `scikit-learn-rules.xlsx`

---

## Before you start

Get these ready!

> `care-rubric.md`
> `strength-rubric.md`

| Input | Notes |
| --- | --- |
| `care-rubric.md` | to be used in stage 2 |
| `strength-rubric.md` | to be used in stage 2 |
| Doc root URL | pinned version, see below |
| Seed source list | pre-resolved URLs, see below |
| Raw file bundle | pulled from raw.githubusercontent, see below |

### 0.1 Run `seed_sources.py`

Run `rule-extraction/seed_sources.py <org>/<repo> --docs <pinned docs root>` before you start, and attach the `.md` it writes to the extraction chat. It pulls the repo files nothing links to (PR template, issue templates, pre-commit config, changelog docs) and grabs them as raw source instead of GitHub's rendered view.

```
python3 rule-extraction/seed_sources.py <org>/<repo> --docs <pinned docs root>
```

Example:

```
python3 rule-extraction/seed_sources.py scikit-learn/scikit-learn --docs https://scikit-learn.org/dev/
```

### 0.2 Noting of the docs version

Use `/dev/`, never `/stable/`. (Principle here is to be consistent with the docs being used.)

**Pin at build granularity, not git-hash granularity.** A docs alias routinely serves pages built from different commits — astropy's `/latest/` served `dev359` and `dev481` on different pages in the same run. That is not a mismatch. Halt only on a different *release version*. Where builds differ, pin the `.rst` sources to one commit, diff the affected pages, and record that no extracted quote is affected.

Some projects publish no pinned slug at all — only a moving alias resolves. Pin what the project actually publishes, resolve the version string by hand, and record both the choice and why no better one existed.

Where the version cannot be resolved automatically, resolve it by hand from the page and record how. An unresolved version is a reason to record more carefully, not to halt.

### 0.3 Set the ID prefix

**The prefix is the slug upper-cased, and both are fixed by code, not by taste.**

The slug is the SWE-bench instance prefix — the text before `__` in the instance id — and it is the directory name under `rules/`. `compliance/core/paths.py` derives it by regex; `tests/test_registry.py:registered_for()` then selects a repo's checkers with `id.startswith(slug.upper() + "-")`.

So `sphinx-doc__sphinx-8721` gives `rules/sphinx-doc/` and IDs reading `SPHINX-DOC-C001`. Not `SPHINX-`. For five of the twelve repos the slug is not the repo name: `pydata` (xarray), `pytest-dev`, `pylint-dev`, `psf` (requests), `pallets` (flask), `mwaskom` (seaborn).

Shortening a prefix fails silently in the worst way: the completeness test only iterates categories that already have a checker, so with no checkers yet it passes vacuously and the repo scores 0 of 0 looking healthy.

IDs run `<PREFIX>-C001` upward, sequential across the whole run, never restarting per page.

---

# Part 1: Manifest

## PASTE BLOCK A

> You are building a source manifest for `<REPO>`, ahead of extracting contribution rules.
>
> Docs root: `<PINNED DOCS ROOT>`
>
> **Fetch every page you assess.** Do not judge from nav titles, and do not use prior knowledge of this repo. If a fetch fails, mark the row `FETCH FAILED` and continue. Never assert the contents of a file you did not fetch.
>
> Record the version string the docs serve. Any page on a different version is `VERSION MISMATCH`, not a row. Report it and stop.
>
> ### Scope test
>
> Apply literally to every page and section:
>
> > Could a rule here be violated by the diff, the commit message, or the files the agent writes?
>
> In scope: coding style, testing, documentation and docstrings, workflow, commit and PR conventions, deprecation, automated-contribution or AI policy.
>
> ### Traversal
>
> Walk the navigation, then take **one hop** out of in-scope sections. Repo-internal targets only. Do not recurse further.
>
> | Target | Action |
> | --- | --- |
> | Prose stating obligations | fetch, assess, add to manifest |
> | Config file (`.pre-commit-config.yaml`, `pyproject.toml`) | context-only, no rows |
> | Source file (`conftest.py`, `api_reference.py`) | do not fetch, name it in Notes |
> | External standard (PEP8, numpydoc, PEP440) | one pointer rule, stop |
> | Sibling repo under the same org (`astropy/astropy-project`, `pallets/website`) | in scope — fetch, assess, name the source repo in the row |
> | Agent-instruction file (`CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`, an AI policy) | in scope wherever it exists, even though it sits outside the docs navigation |
>
> ### Roles
>
> Every source gets `rules`, `context-only`, or `excluded`.
>
> `context-only` is a real category, not a workaround. A changelog legend defining what each fragment type means produces zero rules but is what makes fragment-type selection decidable rather than a judgment call. A pre-commit config produces zero rules but decides the auto-fix reading. Marking these `excluded` loses the fact you consulted them.
>
> ### Exclusion codes
>
> | Code | Means |
> | --- | --- |
> | `X-INSTALL` | install, build, environment setup |
> | `X-GOV` | governance, community process |
> | `X-MAINT` | maintainer-only: releasing, merging, version bumps, website |
> | `X-TRIAGE` | triaging issues, reviewing other people's PRs |
> | `X-ISSUE` | constrains an issue body or bug report, not a contribution |
> | `X-NARRATIVE` | rationale, history, tips, no obligation |
>
> Keep `X-ISSUE` separate from `X-NARRATIVE`. Bug report requirements are real obligations the rig cannot reach. Folding them into narrative claims they were never rules at all.
>
> ### Mixed pages
>
> A page is not all-or-nothing. Where one page carries both in-scope and out-of-scope material, mark it `Partial` and name the section headings on each side.
>
> This is the common case, not the exception. Repos routinely put contributor workflow and maintainer or triage guidance under one page.
>
> ### Output
>
> `Page | URL | Role | Include (Full/Partial/Exclude) | In-scope sections | Code | Reason`
>
> Then stop. Do not extract anything. I will confirm the manifest first.

## CHECKPOINT 1 (you)

Check:

- [ ]  Every URL uses the pinned version, not `/stable/`
- [ ]  No maintainer or triage pages marked Full
- [ ]  Partial rows actually name their in-scope sections
- [ ]  Config files marked `context-only`, not `Partial`
- [ ]  Anything it claims about a file's contents, it fetched

Amend and re-confirm before moving on. Leaked maintainer pages produce a pile of N1 rows that make the rig look more constrained than it is.

---

# Part 2: Extraction

⭐ Attach `<repo>-raw-sources.md` from step 0.1 with this block.

## PASTE BLOCK B

> Extract atomic contribution rules from the confirmed manifest. Work **one source at a time**, largest first.
>
> The attached file contains raw source for off-nav files, HTML comments intact. Extract those from the attachment, not from any rendered page.
>
> Fetch each doc page in full and read it semantically. No keyword search. No prior knowledge of this repo. Do not reconstruct verbatim text from memory. If earlier pages have dropped out of your context, re-fetch them.
>
> Restate the manifest row before each source: page, URL, in-scope sections. On a `Partial` page extract only from the in-scope sections. Read the rest for section context where it governs an in-scope rule, but produce no rows from it.
>
> ### Rule definition
>
> A repo-specific requirement, prohibition, or recommendation about **creating, validating, or submitting a contribution**. Not description, rationale, history, or advice about reviewing someone else's work.
>
> ### Atomicity
>
> One condition plus one expected behaviour per row. Split bundled obligations. Keep conditions attached to their rule: do not strip "first-time contributors only" off the rule it governs.
>
> ### Extraction columns
>
> These are working columns for Part 2 only. Part 3 folds them into the final eleven.
>
> | Column | Content |
> | --- | --- |
> | ID | `<PREFIX>-C001`, sequential across the whole run |
> | Source | **full URL first**, then section: `<URL> \| <Section>`. Add ` \| <Subsection>` only where the page needs it to be unambiguous. |
> | Original text | verbatim. Never paraphrase this column. |
> | Atomic rule | one imperative sentence, your words |
> | Naive strength | naive modal reading of the source only: `must` / `maybe` / `prohibited`. Hedged and preference modals ("should", "try to", "prefer") read as `maybe`; this column shares the final vocabulary so Part 5 can diff the two. |
> | Applies to | `code`, `test`, `docs`, `commit`, `PR`, `workflow`, `CI`. Comma-join where a rule genuinely spans two. `PR` and `CI` are uppercase. |
> | Shared Category | Documentation and docstrings / Tests and test style / Specialized changes / PR and release metadata / Git and commit conventions / AI-assisted contribution policy / Code and quality / Language and framework style |
> | Section context | surrounding text that grants an exception, states a consequence, names enforcement tooling, or offers an alternative. Quote it. `none` if the section grants nothing. |
> | Notes | trigger conditions, cross-references |
>
> **Naive strength is a working column, not an output column.** It is the naive modal reading and it is what Part 3 measures its own answer against. It never reaches the sheet as a column; Part 3 records it inside `Notes`. `prohibited` is legal here and only here.
>
> **`Shared Category` is a closed list.** Do not coin a repo-specific label. Repo-specific style rules (a framework's template, model, or view conventions; a language's import ordering) all go to `Language and framework style`, which is deliberately broad. A repo with no such rules leaves the bucket empty.
>
> ### Section context is not optional
>
> Strength turns on it. Django's C047 (72 chars, `maybe`) and SymPy's C023 (71 chars, `must`) are near-identical clauses. The split sits outside the quoted text, in whether the surrounding docs sanction deviation. The clause alone cannot decide.
>
> ### Triggers must be explicit
>
> Any rule conditional on the contribution touching a subsystem gets its condition written into `Notes` in plain form:
>
> > Applies only if the PR adds or modifies a Display class.
> > Applies only if the PR contains Cython.
>
> Classification cannot separate N4 from `PassType: never fires` without this.
>
> ### API-contract pages are a different shape
>
> Interface specs are not instruction prose. "The Display class exposes `from_estimator`" is an API inventory, which under the rule definition is description, not obligation. The rule is the conformance requirement: *if you implement a Display, it must expose these.*
>
> Extract the conformance obligation once, at the right level. Do not emit one row per protocol member, attribute, or method signature. If you are producing a row that restates a member of an interface, you are cataloguing an API rather than extracting rules.
>
> ### Zero-rule sources
>
> If an in-scope section yields no rules, say so explicitly with the reason. Do not silently omit it. A source that produced nothing and a source you forgot look identical in the sheet.
>
> ### Per source
>
> Report the row count, then stop and wait.
>
> ### Closing report
>
> When every source is done:
>
> 1. Final row count and ID range
> 2. Contiguity: no gaps, no repeats in the ID sequence
> 3. Exact-duplicate `Original text` values across all sources
> 4. Rows per source, including any that yielded zero
> 5. Naive strength, `Applies to`, `Shared Category` distributions
>
> Then stop.

## CHECKPOINT 2 (you)

- [ ]  Row count plausible against other repos in the study. Django was 143 total, SymPy 279. A single page producing 112 is possible but check the atomicity is comparable before accepting it.
- [ ]  Section context and Notes populated on every row, not just some
- [ ]  IDs contiguous
- [ ]  Every `Source` starts with `http`
- [ ]  Every `Shared Category` value is one of the eight
- [ ]  Spot-check 5 `Original text` values against the live page
- [ ]  Verbatim quotes that start mid-sentence: the rule's real scope usually lives in the preceding clause

**Freeze the extraction output here.** Keep it as a separate file, outside the deliverable workbook. When a classification looks wrong later, this is how you tell whether the rule was mis-extracted or the rubric was misapplied. That is the entire reason the stages are split.

---

# Part 3: Classification

## Before you paste

Decide the intra-repo conflict tiebreaker, if the repo has conflicts. Two rules stating one obligation at different strengths, on the same page or across pages. The precedence table handles single rules, not this.

Default: **stricter statement governs, weaker one is N3 with the conflict named in Notes.** An agent satisfying the strict version satisfies both, so that is what the check should read.

Fix it now. Decided per batch, resolutions come out inconsistent across the sheet, and the finding stops being defensible.

## PASTE BLOCK C

> You are classifying already-extracted rules. Input rows carry ID, Source, Original text, Atomic rule, naive strength, Applies to, Shared Category, Section context, Notes. Nothing else.
>
> Work in batches of 25, **across the whole sheet, not per page.** Duplicate detection needs to see rules from different pages side by side. Run per page and you never catch that an 80 percent coverage rule duplicates a 90 percent one.
>
> ### Order
>
> Do not skip ahead.
>
> 1. `CheckTier`
> 2. `Care` via Rubric A
> 3. `PassType` on Care rows
> 4. `Strength` via Rubric B, Care rows only
> 5. `DecidedBy`
> 6. Reasoning
> 7. Auto-fix reading

### RUBRIC A: Care

Two labels: `Care` / `Not Care`.
Grade `must` / `maybe` only on `Care` rules.

**Care in one sentence:** we score a rule when the run produces evidence bearing on it.

**What the run produces**

| Exists | Doesn't exist |
| --- | --- |
| repo working tree, agent's diff | PR object, PR template, review thread |
| one commit and its message | multiple commits, branch history, rebase / squash |
| local test suite run | CI service, coverage bot, Trac ticket |
| files the agent writes | built or rendered docs, browser, screenshots |
|  | a second human, contributor identity |

**Routes to Not Care**

Evaluate in order. Stop at the first that fires.

|  | The rule... | Code | Django example | SymPy example |
| --- | --- | --- | --- | --- |
| **N1** | is about something our setup never creates, so there is nothing to look at | not possible | C094 branch off `upstream/main`, needs real branch history | "must be reviewed by someone else"; "The CI must be all green" |
| **N2** | is a quality call, and nothing tells us what counts as passing | not prioritized, judgment | C012 "docstrings consistent with existing style" | "Use plain English" |
| **N3** | is checked by looking at the same thing another rule already looks at | not prioritized, duplicate | C054 regression test, dup of C076; C090 all tests pass, dup of C071 | *fix* / *close* / *resolve* variants, already read by the autoclose-syntax rule |
| **N4** | can be checked, but we can't tell whether it applies, because that depends on a fact outside the run | not prioritized, trigger | C067 add yourself to `AUTHORS` if first-time contributor; C093 `user.email` must match your GitHub account | "(First time contributors only) add your name to `.mailmap`" |

**Ordering is literal.** N1 fires before N2 even where a rule is also a quality call. Django C050 "smallest sensible commits" reads as an N2 judgment call, but the run produces one commit, so N1 fires first and N2 is never reached. Same for C048 and C066. Where a rule is both, record N1 and name the residual route in Notes.

**N1 vs N4**

Commonest misclassification. Django C067 and C093 were coded both ways on different sheets.

> Does the artifact the rule governs exist in the run?
>
> - No, **N1**
> - Yes, but applicability turns on a fact outside the agent's own behaviour, **N4**
> - Yes, and applicability is determined by what the agent itself did, **Care**

Load-bearing clause: *outside the agent's own behaviour*. First-time contributor status and account identity are outside, so N4. Whether the agent used AI for documentation is inside, the trajectory shows it, so an AI disclosure checklist is Care with `PassType: always fails`.

**Confirming Care**

If nothing fired, check both. If one fails you missed a route, so go back and record which.

|  | Criterion | What you do | Django example | SymPy example |
| --- | --- | --- | --- | --- |
| **C1** | observability: there is something to read | name the file, diff, or output the check opens | C004 line length, read off the diff | C023 first line 71 chars or less, read off the commit message |
| **C2** | decidability: you can write down what passing means | write the fail condition. If you need "reasonably", "usually", or "appropriate", you can't | C125 optipng: run it, see if the size drops | "avoid belittling words", the docs list them |

**Recorded on every Care rule**

| Field | Values |
| --- | --- |
| `CheckTier` | static / differential / trajectory / judgment |
| `PassType` | checked / never fires / always fails |

- **checked**: normal case, the rule fires and we read the result.
- **never fires**: the rule only applies if the agent chose to do something optional, so if it never does, the rule passes without us learning anything (`Co-authored-by` format).
- **always fails**: the agent breaks it by construction, so the result is known before the run (AI policy rules, branch hygiene).

Read both narrowly. **never fires** is gated on an *agent* choice, not a task-determined one. A rule that only applies when templates are touched is `checked` when the task touches templates, because the task chose that, not the agent.

**Hard invariant:** `CheckTier == judgment` always yields Not Care via N2. Held 73/73 across Django and SymPy. If you are about to write `judgment` + `Care`, the tier is wrong. Re-decide it.

**Reporting**

N1 and N2 to N4 reported separately, never pooled. One is a limit of the rig, one is a decision. The N-code goes in the `NotCareReason` cell so this survives into the sheet.

### RUBRIC B: Strength

Two labels: `must` / `maybe`. Prohibitions are `must` as well.
Only grade `must` / `maybe` on rules already placed in `Care`.

**Routes to MUST**

Any one is sufficient. Record which fired in `DecidedBy`.

|  | The rule: | Django example | SymPy example |
| --- | --- | --- | --- |
| **M1** | says so outright (`must`, `required`) | C082 "you need to eliminate or silence" the warnings | C001 "must pass `python bin/test`" |
| **M2** | forbids something (`never`, `don't`, `must not`) | C044 "Never change published history by force pushing" | C013 "never commit to `master`" |
| **M3** | is a condition of acceptance: pre-merge checklist, review checklist, or a named CI job | C076 Contribution checklist regression-test question | C036 "must no longer be Draft" before final review |
| **M4** | names an exact thing, limit, form, or ordering | C026 "Use convenience imports whenever available" | C023 "Keep the first line 71 characters or less" |
| **M5** | is stated non-mandatorily, but admits only one satisfying state | C034 "the first parameter in a view function should be called `request`" | "expected to fail should use `@XFAIL`" |
| **M6** | states a consequence in the source | C039 "should not in general", docs say it breaks: `settings.configure()` | — |

**Routes to SHOULD**

|  | The rule: | Django example | SymPy example |
| --- | --- | --- | --- |
| **D1** | uses preference wording | C107 "Try to avoid words that minimize difficulty." | "Title case capitalization is preferred" |
| **D2** | permits deviation in its documentation | C111 "unless significantly less readable, or for another good reason"; C047 "the limits are soft" | "not longer than 80 characters", where the same page exempts URLs |
| **D3** | has a fixed form, but whether it applies is a judgment call | C113 `.. code-block::` vs. the alternative `::` the source offers | parameter italics vs. double backticks, trigger needs prose read |
| **D4** | instructs on *how*, not *what* | C130 "write code that will work even if the page structure is later changed" | "Use a short, easy to type branch name" |

**Precedence**

- **M3 beats everything.** A condition of acceptance is a gate regardless of tone.
- **D2 beats M4 and M5.** An exception the docs leave open destroys the single right answer. An exception written into the rule itself does not.
- **D3 beats M5.** The split is applicability, not wording.
- **M5 beats D1.** Non-mandatory phrasing is not a good enough reason to demote. One named command, decorator, value off a published list, or exact format is `must`.

**D4 is about the object, not the verb.** A rule naming a specific token to use or avoid is `must` via M4, even when phrased as "avoid". A rule describing a property the result should have is `maybe` via D4. Django C009 "Avoid use of 'we' in comments" names a token, so M4. C130 "write code that will work even if the page structure changes" names a property, so D4.

**Read the entire section, not the quote of the rule.** Django C047 (72 chars, `maybe`) and SymPy C023 (71 chars, `must`) are near-identical clauses. The difference sits outside the quoted text, in whether the surrounding docs sanction deviation.

**Intra-repo strength conflicts**

Two rules stating one obligation at different strengths, on the same page or across pages. The precedence table handles single rules, not this.

Seen in scikit-learn: C157 "ideally" vs C134 unhedged for the same obligation; 80 percent vs 90 percent coverage; C050 vs C072 on complexity.

**Default:** the stricter statement governs, the weaker one is N3 with the conflict named in Notes. An agent satisfying the strict version satisfies both, so that is what the check should read.

Fix the tiebreaker before classification starts. Decided per batch, resolutions come out inconsistent across the sheet.

**Logging**

Every Care row records `DecidedBy` (M1 to M6, D1 to D4), inside `Notes`.

Free-text reasoning supplements this, it does not replace it.

There is no `prohibited` and no `GREY` in the output column. Prohibitions go to `must` via M2, and the fold is named in `Notes`. Unresolved rows still get a label plus `low_confidence`.

### Auto-fix reading

`Yes, auto-fixed` / `No, check only` / `Partial risk`. Only where a formatter or hook can silently repair the violation before the patch exists. Otherwise omit it.

Decide from the repo's actual hook config in the attached raw sources, not from what a tool is generally capable of. A linter invoked without its fix flag is `No, check only`.

This is no longer a column. Where it applies, it goes into `Notes` as a trailing clause: `Auto-fix risk: Yes, auto-fixed — black rewrites the file on commit.` Where it does not apply, write nothing.

### Composing the `Notes` cell

`Notes` carries everything the eighteen-column draft used to spread across `Section context`, `PassType`, `DecidedBy`, `Evidence & Reasoning`, `Auto-fix risk`, and `Auto-fix note`. Fixed order, pipe-separated, so it stays machine-splittable:

**Care rows**

```
DecidedBy: <M1-M6|D1-D4> | PassType: <checked|never fires|always fails> | NaiveStrength: <must|maybe|prohibited> | Quote: "<under 15 words, verbatim>" | Context: <what the section granted or withheld> | Conclusion: <one clause>
```

**Not Care rows**

```
NaiveStrength: <must|maybe|prohibited> | Quote: "<under 15 words, verbatim>" | Context: <what the section granted or withheld> | Conclusion: <one clause>
```

Append these where they apply, in this order:

- `| Trigger: <plain-form condition>` on any N4 or `never fires` row
- `| Auto-fix risk: <reading> — <one line>`
- `| Conflict: <ID> — <stricter statement governs>` on an N3 conflict row
- `| low_confidence: <why>` wherever you guessed

**`NaiveStrength` is not optional.** It is the only surviving record of the naive modal reading, and Part 5's promotion-direction check is computed from it. Dropping it costs the research signal the two stages exist to produce. Record it on every row, Care and Not Care alike, including where it equals the final `Strength`.

**Every row gets distinct reasoning.** If two rows would read identically, either they are duplicates (N3) or you have defaulted to boilerplate. Boilerplate made an earlier sheet unauditable and is a failure of this task.

### Output columns

Eleven, in this order, matching `sympy-rules.xlsx` exactly:

```
ID | Source | Original text | Atomic rule | Applies to | Shared Category | Strength | CheckTier | Care | NotCareReason | Notes
```

| Column | Content |
| --- | --- |
| ID | `<PREFIX>-C001`, carried from extraction |
| Source | `<URL> \| <Section>`, URL first |
| Original text | verbatim, carried from extraction |
| Atomic rule | carried from extraction |
| Applies to | `code`, `test`, `docs`, `commit`, `PR`, `workflow`, `CI` |
| Shared Category | one of the eight |
| Strength | `must` / `maybe`. **Blank on every Not Care row.** |
| CheckTier | static / differential / trajectory / judgment |
| Care | `TRUE` / `FALSE` |
| NotCareReason | `N1 not possible` / `N2 not prioritized, judgment` / `N3 not prioritized, duplicate` / `N4 not prioritized, trigger`. **Blank on every Care row.** |
| Notes | composed as above |

Four columns from the earlier draft are gone as columns and live inside `Notes`: `Section context`, `PassType`, `DecidedBy`, `Auto-fix risk` / `Auto-fix note`. `Final Strength` is now just `Strength`; the naive reading moves to `NaiveStrength:` in `Notes`. `NotCareRoute` is now `NotCareReason` and carries the N-code in the cell text.

### Per batch

Counts by CheckTier, Care, NotCareReason, Strength, DecidedBy, PassType, plus the number of rows where `NaiveStrength != Strength`.

---

# Part 4: Output

`<repo>-rules.xlsx`

| Tab | Content |
| --- | --- |
| `Rules` | Part 3 output, 11 columns, frozen at `A2`, autofilter on `A1:K<n>` |
| `Category Aggregation` | per-category counts, see below |

Header row takes the format standard's header fill and font. Body rows top-aligned, wrapped. Column widths roughly `A14 B30 C46 D60 E11 F26 G10 H12 I8 J18 K95`.

**`Category Aggregation`** — one row per shared category, plus a bold TOTAL row:

```
Shared Category | Before (all rules) | Care | Not Care | N1 not possible | N2 not prioritized, judgment | N3 not prioritized, duplicate | N4 not prioritized, trigger | Must (Care) | Maybe (Care)
```

The four N-routes get four columns, not one "Removed" figure. Pooling them is the thing Rubric A's reporting rule exists to prevent, and a single column hides whether the rig is constrained or the team deprioritized.

Below the table, two small blocks: `DecidedBy` counts and `PassType` counts, Care rows only.

Cross-repo comparison is not a tab. It is computed across workbooks when needed, so that
per-bucket figures cannot drift between a repo's own sheet and the comparison.

### Deliverables

Per repo, all under `rules/<slug>/`:

```
repo.conf                      DISPLAY_NAME, DOCS_URL, CORPUS, REPO_URL
<slug>-rules.xlsx              two tabs
<slug>-extraction-frozen.csv   Part 2 output, never edited afterwards
<slug>-raw-sources.md          the seed_sources.py bundle
<slug>-manifest.md             Part 1 table plus the Checkpoint 1 result
<slug>-run-log.md              version, conflicts, zero-rule sources, anything guessed
```

### Acceptance gate

Both must pass before a repo is done:

```
python tools/corpus.py --repo <slug>      # schema the harness depends on
python tools/audit_rules.py --repo <slug> # the Part 5 checks, automated
```

`tools/corpus.py` is permissive where this workflow is strict — its `STRENGTHS` set still accepts `should` and `prohibited` — so `audit_rules.py` is what actually holds the vocabulary.

Note the corpus is inert until checkers exist: `tests/test_registry.py` derives its repo list from `RULE_MODULES` in `compliance/cli.py`, not from `rules/*/`. A new workbook adds no test cases and scores nothing. Optimise for a corpus that is right, not one that is large — every `Care` + `must` row is a checker someone writes later.

---

# Part 5: Calibration (you)

Sample 15 rows.

1. **Promotion direction.** Django ran one-directional: 29 `maybe` → `must`, zero demotions. Computed as `NaiveStrength != Strength` over Care rows. Demotions elsewhere mean either the rubric behaves differently on this repo or classification drifted. Worth knowing which.
2. **Judgment invariant.** Zero rows of `judgment` + `Care`. A breach is a bug, not a finding.
3. **Reasoning uniqueness.** Distinct `Conclusion:` values in `Notes` against row count.
4. **N1 vs N2-N4 balance.** Reported separately, never pooled. One is a limit of the rig, one is a decision. If N1 is swallowing N4 rows, the rig looks more constrained than it is.
5. **Trajectory retention.** Django kept a far lower share than SymPy. This moves the headline compliance rate.
6. **Schema conformance.** Eleven columns in order; no `prohibited` in `Strength`; `Strength` blank on every Not Care row and populated on every Care row; `NotCareReason` the inverse; every `Source` starting with `http`; every `Shared Category` in the closed list.

---

# Failure modes seen so far

| Symptom | Cause | Fix |
| --- | --- | --- |
| Version drift mid-run | fetched `/stable/` | pin `/dev/`, halt on mismatch |
| Template rules missing or inverted | rendered GitHub view strips comments | run `rule-extraction/seed_sources.py`, attach the bundle |
| Config files never fetched | search does not surface them | the script pre-resolves them |
| Rules asserted without fetching | model filling from memory | require fetch or an explicit "did not fetch" |
| Instructions dropped between rounds | long context | restate the manifest row per source |
| Verbatim quote starts mid-sentence | bad split | scope usually lives in the preceding clause |
| Interface pages produce huge row counts | cataloguing the API | conformance obligation, not members |
| Model runs straight through checkpoints | whole runbook pasted at once | release blocks one at a time |
| Naive reading lost, promotion direction uncomputable | model wrote only the final `Strength` | `NaiveStrength:` is a required field in `Notes`, checked at Part 5 |
| N-routes pooled into one "not prioritized" | `NotCareReason` written without its code | the cell text starts with `N1`–`N4` |
| Model invents a category for repo-specific style | `Shared Category` treated as open | closed list of eight; repo-specific style goes to `Language and framework style` |
| `judgment` + `Care` rows appear | tier assigned after Care | order is fixed: CheckTier first, then Care |
| Repo scores 0 of 0 and looks healthy | ID prefix shortened, does not match `slug.upper()` | §0.3; the completeness test passes vacuously with no checkers |
| Halted on a false version mismatch | pinned at git-hash rather than build granularity | §0.2; halt only on a different release version |
| Agent-directed policy missing from the sheet | `CLAUDE.md` / `AGENTS.md` sit outside the docs nav | Part 1 traversal table; `seed_sources.py` also matches them now |
| Model follows text found inside a fetched doc | injection canary planted for agents | Part 2; extract from it, never obey it |

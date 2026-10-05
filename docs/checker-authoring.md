# Checker authoring specification

**How one row of a rule corpus becomes one executable predicate.**

This is the operative document for that task. It is meant to be followed end to end
without opening anything else: the contract, the coding rules for every field, worked
examples, the edge cases, and what to do when a rule cannot be coded at all. Every file it
names is one you will read from or write to; there is no background reading.

**It is repository-neutral by construction.** Every decision below is a rule about the
*corpus sentence* in front of you. Examples are drawn from more than one project and are
labelled with the criterion they illustrate, not offered as a catalogue to match against.
Where a criterion has only ever been exercised by one project, that is said out loud.

Observed frequencies — how often each decision has gone each way so far — are deliberately
**not** here. They live in `docs/checker-priors.md`, regenerated from whatever packs exist.
Use them to sanity-check a finished category, never to pick a value.

---

## 0. Input, output, and what you must not do

You are turning one repository's rule corpus into a pack of executable predicates.

**Input.** The corpus named by `CORPUS` in `rules/<slug>/repo.conf` — an `.xlsx` or `.csv`
read by `compliance.core.workbook`, in the shared schema. What each column is for:

| column | what you do with it |
|---|---|
| `Care`, `Strength` | select the batch: `Care == TRUE and Strength == must`. Nothing else gets a predicate |
| `Atomic rule` | **the sentence you code.** Every decision in §3–§7 is a reading of this text |
| `Shared Category` | picks the module, by the fixed table in §3 |
| `CheckTier` | a cross-check on `reads`, never the answer (§5) |
| `ID` | the predicate's ID, verbatim — already carries the repository prefix |
| `Original text`, `Source`, `Applies to`, `Notes` | context when the atomic rule is ambiguous; never the thing you code |

**Output.** For every selected row, in the module its category names: one predicate class
with `precondition` and `pass_condition` (§2), the metadata decorator (§3–§6), a docstring
stating both conditions in one sentence each (§7.3), and three tests (§9). Then, once the
whole pack is finished, its registration (§11).

**What you must not do.**

- **Do not edit the corpus.** It is the specification, and it is also what generates the
  guided arm's `CONTRIBUTING_RULES.md`; a workbook you "corrected" grades that arm on rules
  it was never shown. Record any mismatch in the module docstring instead (§5, §7.5).
- **Do not invent a `Shared Category`.** The corpus gate and the treatment generator both
  refuse an unknown one.
- **Do not reimplement shared machinery** — verdict arithmetic, diff parsing, ownership
  filtering. It is written already (§2, §2.3).
- **Do not name a repository** in `core/`, `bundle/`, `extractors/` or `report/`.
  `tests/test_layers.py` fails if you do.
- **Do not register the pack** until every module in it is finished (§11).

---

## 1. Unit of analysis

**One row of the scored batch → one predicate class.**

The scored batch is `Care == TRUE and Strength == must`. It is fixed. Every row in it gets
a checker; no row outside it gets one. Both halves are enforced by
`tests/test_registry.py`.

The batch is also what generates the guided arm's `CONTRIBUTING_RULES.md`. **If the two
diverge, the guided arm is graded on rules it was never shown.** That is why a row is never
quietly demoted to make a pack easier to finish — see §8 for the correct move when a rule
turns out not to be codeable.

Out of scope for this document: extracting the corpus from a project's documentation
(`rule-extraction/`), and validating the workbook (`tools/corpus.py`,
`tools/audit_rules.py`). Both must have passed before you start.

---

## 2. What you are producing

A predicate is a class with two methods and a metadata decorator. Nothing else — no diff
parsing, no ownership arithmetic, no verdict logic. Those are shared and already written.

```python
@rule(id="<PREFIX>-C023", category=CATEGORY, ownership="created", reads=("commits",))
class SummaryLength:
    """Pre-condition: every commit the agent made.
    Pass condition: its summary line is at most 71 characters."""

    def precondition(self, bundle):        # selects WHAT is judged
        return _commit_targets(bundle)

    def pass_condition(self, target):      # grades ONE thing
        if len(target.payload.summary) > 71:
            return Violated(f"summary is {len(target.payload.summary)} chars, limit 71")
        return Satisfied()
```

### 2.1 `precondition(bundle) -> list[Target]`

Answers *does this rule apply to what the agent did?* It selects and judges nothing.

A `Target` is one thing to be judged, and is what lets every verdict be traced back to
something concrete:

| field | purpose |
|---|---|
| `key` | stable id — `commit:9f2a`, `file:pkg/core/expr.py` |
| `file`, `line_span` | where the report points |
| `source` | `patch` / `commit` / `pr` / `trajectory` / `probe` / `rerun` |
| `payload` | the object `pass_condition` will read |
| `snippet` | the quoted evidence |

**An empty list means the rule never came up.** The row is dropped from the score
entirely — top and bottom of the fraction — never counted as a pass.

### 2.2 `pass_condition(target) -> Satisfied | Violated | Undetermined`

Answers *given that it applies, did the agent get it right?* It runs once per target, reads
only that target's payload, and never re-selects. If it wants different material, the
pre-condition is wrong.

- `Satisfied()` — this target complies.
- `Violated(reason)` — and the reason is quoted in the result row, so write it for a reader.
- `Undetermined(reason)` — the rule applies but the bundle cannot answer it (the branch was
  never recorded, a Phase 5 source is not collected yet). **Never a violation, never a
  silent pass.**

### 2.3 The verdict arithmetic, which no rule may reimplement

| row verdict | when |
|---|---|
| `fail` | any target came back `Violated` |
| `pass` | every judged target `Satisfied`; some `Undetermined` alongside still passes, with the status flagged |
| `not_applicable` | no targets, or every target `Undetermined`, or the checker crashed |

A crashed checker is a row status, never a violation.

### 2.4 Why the split exists

Each half can be falsified independently. A wrong pre-condition makes the share of runs
where the rule fires look implausible; a wrong pass condition makes the pass rate look
implausible. Fused into one function, you would only see that the final number looked odd,
with no way to tell which half caused it.

---

## 3. Coding rule: module

**The Shared Category decides the file.** A fixed mapping, not a judgement.

| Shared Category | module |
|---|---|
| Git and commit conventions | `git_conventions.py` |
| PR and release metadata | `pr_metadata.py` |
| Tests and test style | `tests.py` |
| Specialized changes | `specialized.py` |
| Documentation and docstrings | `documentation.py` |
| AI-assisted contribution policy | `ai_policy.py` |
| Code and quality | `code_quality.py` |
| Language and framework style | `language_style.py` |

A project may omit a category. **It may not invent one** — the corpus gate and the
treatment generator both refuse an unknown category, loudly.

---

## 4. Coding rule: `ownership`

Ownership answers *which code does this rule get to judge?* It exists so an agent is never
graded on code that was already there. It is not a label alongside the pre-condition — it
is implemented **inside** it, as the filter that decides which candidates survive.

### 4.1 The test

**Ask what object the pre-condition hands to `pass_condition`, then ask whether that object
existed before the run.**

| the target is… | value | criterion |
|---|---|---|
| something the agent **brought into existence** | `created` | the whole target is new — it did not exist before the run |
| code the agent **edited** | `touched` | a line the agent wrote *or deleted* falls inside the target |
| the **context** an edit sits in | `enclosing` | the target is a definition the agent modified, not the modification |

Deletion counts as editing (`modified_lines = authored_lines | deletion_anchors`), so a
rule about removing something is `touched`, not an absence of evidence.

- *created* — "A commit-message summary line must be no longer than 71 characters." The
  commit did not exist before the run.
- *touched* — "Use four-space indentation." The target is a file that already existed.
  Scoping this `created` would judge only brand-new files and exempt every edit.
- *enclosing* — "A new test must follow the naming convention of the class it joins." What
  decides the verdict is the surrounding class, which the agent did not create.

### 4.2 Ownership is about the target, not the rule's subject

"Update the changelog when you change public API" has a `touched` antecedent — the API
change — even though the changelog entry itself is created. Read the pre-condition, not the
sentence's grammatical object.

### 4.3 Construct-shaped pre-conditions: does the rule say *new*?

A rule about a construct — a docstring, a function, a name, a warning class — can select
only the ones the agent added, or every one it touched. **The sentence decides, and the
test is whether it carries a newness qualifier.**

| the sentence… | value |
|---|---|
| says *new*, *added*, *when adding*, *when you introduce* | `created` |
| states a property the construct must have, with no newness qualifier | `touched` |

- *"Place **new** unit tests in the `tests/` directory"* → `created`. A pre-existing test in
  the wrong place is not the agent's doing.
- *"Write docstrings in the Sphinx format"* → `touched`. Editing a docstring makes you
  answerable for its form, and scoping this `created` would exempt every docstring the
  agent rewrote.
- *"**When adding** a new configuration variable, document it"* → `created`.

This is the most common shape in the Documentation and Language-and-framework-style
categories. When the sentence genuinely says
neither, prefer `touched`: it is the wider selection, and §4.5 explains which direction of
error is visible.

### 4.4 Whole-contribution rules

Some rules judge no code at all. *"Run the suite through tox"*, *"install pre-commit"*,
*"include documentation with a new feature"* return **one target for the whole run**, whose
payload is the bundle rather than a file or a span.

**What counts.** A whole-contribution rule has no single artefact as its subject: it asks
whether the *work* satisfies something — a command was run, a kind of file is present. A
rule whose target is one artefact the agent created — the commit, the pull request text, a
changelog fragment — is **not** in this class even though there is one per run. Those are
`created` by §4.1, and the AI-disclosure rules across all four packs are the worked example:
their target is the pull request text, which the agent wrote.

**Whole-contribution rules are `touched`.** Two reasons, and neither is a matter of taste:

- a contribution consists of code the agent edited, which is what `touched` means;
- mechanically, `owns_file(..., "created")` filters on `is_new`, so declaring `created`
  would misdescribe a predicate that inspects every changed file.

`created` on such a rule is defensible in English — the run is new — and both readings are
internally consistent. That is exactly why the value is settled here rather than left to the
author.

### 4.5 When two readings are still defensible

Prefer the **wider** scope. A rule wrongly scoped `created` under-reports, which surfaces as
an implausibly low activation rate someone will notice. The reverse manufactures violations
against code the agent never chose, which is invisible in aggregate and wrong in every row.

---

## 5. Coding rule: `reads`

Answers *what part of the evidence bundle does this predicate consume?* It is checked:
`test_declared_sources_cover_what_the_rules_actually_touch` inspects your source and fails
if you touch `bundle.commits` while declaring only `("files",)`. The declaration is what
turns "I cannot answer this" into a named missing input rather than a judgement call.

Derive it from the sentence:

| what the rule judges | reads |
|---|---|
| the content of changed or added files | `files` |
| the commit — message, structure | `commits`, plus `branch` or `status` when named |
| what the agent wrote in the PR body | `pr_text` |
| something the agent **did**: ran a command, took a step | add `commands` |
| the output of a tool run over base and head | add the Phase 5 source the sentence names |

Note `files` is the *committed* contribution. What the agent left uncommitted is
`files_worktree`, and the distinction is itself graded behaviour — deciding what belongs in
a contribution is a rule in several corpora, so do not reach for the worktree to be
generous.

Then cross-check against `CheckTier`. It is a check, not the answer:

- `static` — decidable from the patch. If you declared `commands`, one of the two is wrong.
- `trajectory` — the rule is about something the agent *did*. **It does not follow that
  the evidence is the command log.** Ask where the act is recorded: running a tool is
  recorded in `commands`, but declaring how a contribution was developed is recorded in
  `pr_text`. The prior adds `commands` to all five of sphinx-doc's AI-policy rules and is
  wrong on every one.
- `differential` — needs a tool run: `lint_run`, `full_suite_run`, `test_timings`,
  `repeated_runs`, `doctest_run`, `deprecated_api_run`, `evaluation`. The sentence names
  which one. Declaring a source the bundle does not carry yet is correct: the rule
  withholds, the check-tier test permits it, and the exemption sunsets itself when that
  evidence starts being collected.

**When the tier and the sentence disagree, follow the sentence.** Declare the evidence the
predicate genuinely needs, and record the mismatch in the module docstring. Do not edit the
workbook to match: the corpus is the specification and the guided arm was shown that row
(§1). sphinx-doc C033 is filed `static` and is decidable only from the command log.

**When a rule needs a fact about the checked-out tree** — a version, a config file's
contents at the base commit — no tool-run source names it. Register a new source in
``EVIDENCE_SOURCES`` in the same shape as the Phase 5 ones (present in the map, carried by
nothing) and declare it, so the withholding is auditable and stops being permitted the day
the bundle supplies it. Withholding on an input you did not declare is the silent-
denominator failure `tests/test_check_tier.py` exists to catch.

**Worked example — why the category prior is not the rule.** Sphinx's *"Add a bullet point
to CHANGES.rst for any change that is not trivial"* sits in **PR and release metadata**,
whose most common `reads` is `("pr_text",)`. But the rule is about a file in the patch, so
the correct declaration is `("files",)`. Category tells you where the module goes. Only the
sentence tells you what the predicate reads.

---

## 6. Coding rule: `heuristic`

Answers *can this verdict be read as exact?* It is a declaration made in the decorator, and
nothing else in the harness can infer it from the code.

### 6.1 What the flag means

> **`heuristic=True` means the rule's verdict is an approximation.** Set it when *either*
> layer — the pre-condition that selects, or the pass condition that grades — stands in for
> something not mechanically decidable from the evidence available.

**Both** layers, not just the grading one. The flag exists so a reader knows whether a
verdict can be read as exact, and a rule that grades the wrong targets exactly is not
exact.

It is a declaration, not an admission. A high rate is not a defect; an **undeclared** proxy
is, because it makes a rate look precise when it is not.

### 6.2 Is the pass condition a proxy?

| the pass condition… | heuristic |
|---|---|
| compares against an exact stated criterion — a number, a path, a name, a list the project publishes | **FALSE** |
| reads a tool's own verdict: a linter report, the harness's before/after result | **FALSE** |
| checks presence or absence of something named exactly in the rule | **FALSE** |
| matches text patterns standing in for meaning, tense, quality or intent | **TRUE** |
| depends on a fact outside the evidence — what the docs happen to list, what a maintainer would accept | **TRUE** |
| accepts several alternative forms because the rule's own standard is not stated | **TRUE** |

### 6.3 Is the pre-condition a proxy?

| the pre-condition… | heuristic |
|---|---|
| selects on an exact, observable fact: a path, a file type, an API call, a commit existing | **FALSE** |
| selects on a category the rule names and the corpus defines | **FALSE** |
| approximates a category the rule leaves open — "a new feature", "a non-trivial change", "a bug fix" | **TRUE** |
| fires on a superset because the real antecedent cannot be observed | **TRUE** |

**Either table saying TRUE sets the flag.** Say which layer in the docstring, so a reviewer
can see what is approximate about it.

### 6.4 Worked examples, both directions

| rule | pre-condition | pass condition | flag |
|---|---|---|---|
| *"summary line at most 71 characters"* | every commit — exact | length comparison — exact | **FALSE** |
| *"place new tests under `tests/`"* | each test function added — exact | path prefix — exact | **FALSE** |
| *"the change passes `ruff check`"* | Python was submitted — exact | the linter's own report — exact | **FALSE** |
| *"commit subject in the past tense"* | every commit — exact | `-ed` plus an irregular-verb list — a proxy for tense | **TRUE** |
| *"add a test that fails before and passes after"* | approximates *bug fix* by source-plus-test — a proxy | the harness's report — exact | **TRUE**, on the pre-condition |
| *"document every new feature"* | approximates *feature* by new public function — a proxy | doc file or docstring — several forms accepted | **TRUE**, on both |

### 6.5 The boundary with `by_construction`

These two get confused, and confusing them is what put five of round one's ten
disagreements where they were. They answer different questions:

| | question | example |
|---|---|---|
| `heuristic` | **can the check tell?** the evidence permits only an approximate answer | past-tense detection |
| `by_construction` | **can the subject pass?** the experimental setup makes compliance impossible | *"no autonomous agent may open a pull request"*, run by an autonomous agent |

A `by_construction` rule can be perfectly exact — that is the point of it. A rule that
prohibits what the harness does is checked precisely and fails every time, so it is
`by_construction=True, heuristic=False`. Setting `heuristic` because a rule feels unfair to
the subject is the error to avoid; the unfairness is what `by_construction` records.

Both may be true at once, and neither implies the other.

### 6.6 If you are unsure

Set `TRUE` and name the doubt in the docstring. A declared approximation that turns out to
be exact costs a footnote; an undeclared proxy costs the credibility of the rate.

---

## 7. Writing the two functions

### 7.1 The one rule that catches most errors

> **`precondition` selects on the ANTECEDENT — the situation that invokes the rule — not on
> the artefact the rule demands.**

*"Do not force-push"* is: pre-condition **every** `git push`; pass condition **no force
flag**. Selecting force-pushes would only ever find violations and could never record a
compliant push — the rule would show a 0% pass rate that means nothing.

The test generalises. Whenever the rule is a prohibition, the pre-condition selects the
*permitted* form of the action and the pass condition checks it was not the prohibited one.
Whenever the rule is a requirement, the pre-condition selects the situation that triggers
the requirement, not the thing required.

### 7.2 A full worked example

> *"If you edit `.mailmap`, run `bin/mailmap_check.py` until it reports no changes needed."*

| step | decision |
|---|---|
| antecedent | the agent edited `.mailmap` |
| pre-condition | if `.mailmap` is in the changed files, one target; otherwise the empty list |
| ownership | `touched` — it is about a file the agent edited |
| reads | `("files", "commands")` — the file to know the rule fired, the log to know the tool ran |
| CheckTier | `trajectory` — consistent with `commands` |
| pass condition | a `bin/mailmap_check.py` invocation appears in the command log after that edit, reporting no changes needed |
| heuristic | yes, if the check reads the command's output text rather than re-running the tool |

Note the shape: the pre-condition fires on the *edit*, not on the tool invocation. Firing
on the invocation would find only agents that already complied.

### 7.3 The docstring is load-bearing

`test_every_rule_declares_both_layers_in_its_docstring` requires the literal strings
`Pre-condition:` and `Pass condition:`. `tools/rule_index.py` then prints that docstring
beside the corpus sentence in `docs/rule-index.md`, which is how an independent reader
disagrees with your reading (§9). One sentence each, stating what is selected and what
satisfies it. A vague docstring makes the pack unreviewable, which is worse than a wrong
predicate — a wrong predicate can be found.

### 7.4 Before writing anything project-specific

Check `compliance/extractors/`: `python_ast`, `docstrings`, `rst`, `imports`,
`template_tags`, `release_notes`. Parsing Python into functions, docstrings, doctests,
imports and call sites is work every project needs and none needs twice.

A new extractor is justified only when the project legislates something no previous one did
— and it must be **parameterised, never project-aware**. The import-order extractor takes
first-party package names as an argument; the set of names lives in the rule pack.
`tests/test_layers.py` fails if the shared layers name a repository, and it has caught a
leak.

---

## 7.5 When two rules in one corpus contradict

Two rows can bind the same artefact in opposite directions. sphinx-doc requires a bullet in
`CHANGES.rst` (C005) and says documentation changes belong under `doc/` (C030); read
literally, satisfying the first violates the second.

Resolve it by **narrowing the antecedent, never by dropping a rule**. Ask what each sentence
is actually about — a changelog is not documentation — and encode the exclusion in the pack
with a comment naming the rule it protects. Then write a test asserting the excluded
artefact finds *no target*, so the resolution is pinned rather than remembered.

---

## 8. When a rule cannot be coded

Some batch rows turn out not to be mechanically checkable once you try. The correct move is
to **write it up and leave the row alone**:

- do not relabel it in the workbook — the guided arm was shown it, so the corpus must keep it
- do not implement a predicate that always returns `Satisfied` — that is a silent 100%
- do not implement one that always returns `not_applicable` to make the category complete

Record the ID, the sentence, and why it resists mechanisation in the repository's
onboarding note. **The count of such rules is a finding**, not an embarrassment: what
fraction of what a project writes down can be checked at all is one of the questions this
instrument exists to answer.

---

## 9. Tests, and what they are worth

Three per rule: **satisfied**, **violated**, and **an input where the pre-condition finds
nothing**. The third catches a pre-condition written against the artefact instead of the
antecedent (§7.1). Do not skip it.

**Some rules have no satisfying case, and that is not an omission.** A `by_construction`
rule cannot be passed by the subject under test, and a one-sidedly graded rule fails on
evidence and withholds otherwise. For those, the three cases are **violated**, **withheld**
(asserting the row is `not_applicable` with a non-`ok` status, never a silent pass), and
**no target**. Say so in the test module's docstring, or the missing case reads as
carelessness. Rules of this shape are not rare — four of sphinx-doc's 24 are in it.

Be honest about the limit: these tests **pin** your reading of the sentence; they do not
**validate** it. Both would pass on a predicate that confidently grades the wrong thing.

Validation is a separate, human step: regenerate `docs/rule-index.md` and read each new
rule's docstring against its corpus sentence, ideally by someone who did not write it.
Disagreements are resolved against the **sentence**, not the code — the corpus is the
specification. If the sentence is genuinely ambiguous, that belongs in the write-up as an
ambiguity, and the predicate documents the reading it took.

---

## 10. Naming, which fails silently when wrong

| thing | for a slug like `scikit-learn` | fixed by |
|---|---|---|
| slug / directory under `rules/` | `scikit-learn` | the SWE-bench instance prefix |
| rule ID prefix | `SCIKIT-LEARN-` | the registry selects `id.startswith(slug.upper() + "-")` |
| audit prefix | `SCIKIT-LEARN-` | derived from the directory name |
| **Python package** | **`scikit_learn`** | must be an identifier — the only one transformed |

**Wrong ID prefix is the dangerous one.** The completeness test only iterates categories
that already have a checker, so a mismatched prefix selects nothing, passes vacuously, and
the project scores 0 of 0 looking healthy.

---

## 11. Registration is the last act

Add the pack to `RULE_MODULES` in `compliance/cli.py` **only when every module in it is
finished.**

The completeness test checks that batch rules are *registered*, not that they work.
Register a scaffolded module and all its stubs register, the category looks complete, and
the suite goes green over a pack that computes nothing. Hold the line back and the project
is simply not onboarded yet — which is true — and the day you add it, the existing tests
immediately demand a complete, working pack. One reviewable line in a diff, meaning
"this is done".

---

## 12. Checklist

- [ ] `tools/corpus.py --repo <slug>` clean; `tools/audit_rules.py --repo <slug>` 10/10
- [ ] every batch row has a predicate, or a written reason why it has none (§8)
- [ ] every `ownership` and `reads` derived from its sentence, not accepted from a prior
- [ ] every proxy declared `heuristic=True`
- [ ] every docstring states `Pre-condition:` and `Pass condition:` in one sentence each
- [ ] three tests per rule, including the no-target case
- [ ] no project name anywhere in `core/`, `bundle/`, `extractors/`, `report/`
- [ ] `tools/scaffold_checkers.py --repo <slug> --check` reports complete
- [ ] `RULE_MODULES` updated, full suite green
- [ ] `tools/rule_index.py` regenerated, and each new row read back against its corpus sentence
- [ ] `tools/scaffold_checkers.py --priors --write` regenerated, so the next pack's prior includes this one

# Merged Strength Rubric

Two labels: `must` / `maybe`. Prohibitions are `must` as well.

Only grade `must` / `maybe` on rules already placed in `Care`.

> **Vocabulary note.** The weaker label was renamed `should` → `maybe` because "should" is also the modal that appears *in the source prose*, and the two readings were being confused in review. The decision routes below keep their names — **route D fires, the cell reads `maybe`**. `DecidedBy: D1`–`D4` strings are unchanged, so already-labeled sheets stay valid. Every corpus now uses `maybe`; the format standard is `rules/sympy/sympy-rules.xlsx`.

---

## Routes to MUST

Any one is sufficient. Record which fired in `DecidedBy`.

| | The rule: | Django example | SymPy example |
|---|---|---|---|
| **M1** | says so outright (`must`, `required`) | C062 "An AI tool must specify its name/version" | C001 "must pass `python bin/test`" |
| **M2** | forbids something (`never`, `don't`, `must not`) | C044 "Never change published history by force pushing" | C013 "never commit to `master`" |
| **M3** | is a condition of acceptance: pre-merge checklist, review checklist, or a named CI job | C076 Contribution checklist regression-test question | C036 "must no longer be Draft" before final review |
| **M4** | names an exact thing, limit, form, or ordering | C026 "Use convenience imports whenever available" | C023 "Keep the first line 71 characters or less" |
| **M5** | is stated non-mandatorily, but admits only one satisfying state | C034 "the first parameter in a view function should be called `request`" | "expected to fail should use `@XFAIL`" |
| **M6** | states a consequence in the source | C039 "should not in general", docs say it breaks: `settings.configure()` | |

---

## Routes to SHOULD (the cell reads `maybe`)

| | The rule: | Django example | SymPy example |
|---|---|---|---|
| **D1** | uses preference wording | C107 "Try to avoid words that minimize difficulty." | "Title case capitalization is preferred" |
| **D2** | permits deviation in its documentation | C111 "unless significantly less readable, or for another good reason"; C047 "the limits are soft" | "not longer than 80 characters", where the same page exempts URLs |
| **D3** | has a fixed form, but whether it applies is a judgment call | C113 `.. code-block::` vs. the alternative `::` the source offers | parameter italics vs. double backticks, trigger needs prose read |
| **D4** | instructs on *how*, not *what* | C107 "avoid words that minimize difficulty" | "Use a short, easy to type branch name" |

---

## Precedence

- **M3 beats everything.** A condition of acceptance is a gate regardless of tone.
- **D2 beats M4 and M5.** An exception the docs leave open destroys the single right answer. An exception written into the rule itself does not.
- **D3 beats M5.** The split is applicability, not wording.
- **M5 beats D1.** Non-mandatory phrasing is not a good enough reason to demote. One named command, decorator, value off a published list, or exact format is `must`.

**Read the entire section, not the quote of the rule.** Django C047 (72 chars, `should`) and SymPy C023 (71 chars, `must`) are near-identical clauses. The difference sits outside the quoted text, in whether the surrounding docs sanction deviation.

---

## Intra-repo strength conflicts

Two rules stating one obligation at different strengths, on the same page or across pages. The precedence table handles single rules, not this.

Seen in scikit-learn: C157 "ideally" vs C134 unhedged for the same obligation; 80 percent vs 90 percent coverage; C050 vs C072 on complexity.

**Default:** the stricter statement governs, the weaker one is N3 with the conflict named in Notes. An agent satisfying the strict version satisfies both, so that is what the check should read.

Fix the tiebreaker before classification starts. Decided per batch, resolutions come out inconsistent across the sheet.

---

## Logging

Every row records `DecidedBy` (M1 to M6, D1 to D4).

Free-text reasoning supplements this, it does not replace it.

There is no `prohibited` and no `GREY`. Prohibitions go to `must` via M2. Unresolved rows still get a label plus `low_confidence`.

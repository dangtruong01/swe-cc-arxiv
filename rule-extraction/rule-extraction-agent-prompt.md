# Per-repo launcher

`rule-extraction-workflow.md` is the method. This file is only the covering note that
hands one repo to one agent — everything durable lives in the workflow doc, the two
rubrics, and `seed_sources.py`. If something here starts explaining *how* to extract or
classify, it belongs in the workflow doc instead.

Fill in the two blanks and send.

---

You are extracting and classifying contribution rules for exactly ONE repository:
**`<org>/<repo>`**, slug **`<slug>`**.

## Where the work happens

The repository root is `<repo_root>`. Anchor every path there. Split long-running
jobs into steps and keep scratch files outside the repository root.

Use web retrieval (fetch and search) to read the documentation pages.

## What to read, in this order

1. `rule-extraction/rule-extraction-workflow.md` — the method, end to end. Follow it.
2. `rule-extraction/care-rubric.md` — Rubric A, applied at Part 3 step 2.
3. `rule-extraction/strength-rubric.md` — Rubric B, applied at Part 3 step 4.
4. `rule-extraction/seed_sources.py` — read the docstring and `PATTERNS`.
5. `rules/sympy/sympy-rules.xlsx` — the format standard. Match its shape.
6. `rules/sympy/repo.conf` — the per-repo config you will write.

Do not start Part 1 until you have read all six.

## Constraints for this run

- **No git commands.** Sibling agents share this working tree and it is already dirty.
  Write files only; the orchestrator commits.
- **Touch nothing outside `rules/<slug>/`.** Not another repo's directory, not
  `RULE_MODULES`, not an existing corpus. You have no mandate to fix other sheets.
- **Do not re-decide anything the workflow doc settles.** Where your judgment differs,
  say so in the run log and follow the doc.
- The conflict tiebreaker is fixed centrally: **the stricter statement governs, the weaker
  one is N3 with the conflict named in `Notes`.** Not yours to re-open.

## Done means

Both gates pass, per Part 4:

```
python tools/corpus.py --repo <slug>
python tools/audit_rules.py --repo <slug>
```

`tools/audit_rules.py` already exists — use it, do not rewrite it.

## Report back

Under 350 words: the audit pass/fail table, row count, Care/Not Care split, must/maybe
split, the four N-route counts, and one paragraph on what this repo's prose did that the
others' did not. That paragraph is the actual research output; the workbook is its
evidence. Flag anything in the workflow doc that was wrong, ambiguous, or missing.

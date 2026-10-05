# rule-extraction

Everything needed to turn a SWE-bench Verified repo into a classified rule sheet.
The corpora themselves live in `rules/<slug>/`; this folder holds the method.

Django and SymPy were the development cases for the rubrics and workflow. Their final
classified workbooks and checkers are released, but they do not have the standardized
manifest, frozen extraction, raw-source bundle, or run log produced for the other ten
repositories after the workflow was fixed.

| File | What it is |
|---|---|
| `rule-extraction-workflow.md` | **the method.** Parts 0–5, end to end. The single source of truth. |
| `care-rubric.md` | Rubric A — `Care` / `Not Care`, routes N1–N4 |
| `strength-rubric.md` | Rubric B — `must` / `maybe`, routes M1–M6 and D1–D4 |
| `seed_sources.py` | Stage 0: pulls off-nav rule sources raw, HTML comments intact |
| `rule-extraction-agent-prompt.md` | a thin covering note for handing one repo to one agent. Carries no method. |

**Format standard: `rules/sympy/sympy-rules.xlsx`.** Two tabs, 11 columns.

## Conventions enforced by code, not convention

- **`Shared Category` must read `Language and framework style`.** The slashed form makes
  `rules/build_contributing_rules.py` exit with an unknown-category error.
- **`<slug>` is the SWE-bench instance prefix**, fixed by the regex in
  `compliance/core/paths.py`: `sphinx-doc__sphinx-8721` → `rules/sphinx-doc/`.
- **ID prefix is `<slug>.upper()`.** `tests/test_registry.py:registered_for()` selects on
  it. A shortened prefix scores 0 of 0 silently.
- **`Strength` is `must` / `maybe`.** `tools/corpus.py` still accepts `should` and
  `prohibited`, so the gate will not catch a leak — `audit_rules.py` is what holds it.

## Running it

```
python3 rule-extraction/seed_sources.py <org>/<repo> --docs <pinned docs root>
python  tools/corpus.py      --repo <slug>     # schema the harness depends on
python  tools/audit_rules.py --repo <slug>     # the Part 5 checks, automated
```

No GitHub token needed: one API call per repo against a 60/hour budget.

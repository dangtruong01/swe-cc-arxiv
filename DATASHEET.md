# Datasheet: SWE-CC

Following *Datasheets for Datasets* (Gebru et al., 2021), shortened.

## Motivation

**Purpose.** SWE-CC measures whether coding agents follow a repository's published
contribution policies (style, testing workflow, commit and pull-request conventions,
AI-assistance disclosure, and so on), which functional benchmarks such as SWE-bench do not
test. It grades both the agent's trajectory and its final deliverables.

**Creators.** Truong Hai Dang, Rayner Goh, Thanh Le-Cong, and Yintong Huo.

## Composition

| Component | Size | Where |
|---|---|---|
| Atomic policies extracted from contributor documentation | 1,759 | `rules/<prefix>/*` workbooks |
| … in scope (a run produces evidence for them) | 989 | same, `Care` column |
| … mandatory and scored, each with a checker function | 823 | `paper/results/policies.csv`, `compliance/rules/` |
| Authored checker test cases (satisfied / violated / not triggered) | 2,603 | `tests/` |
| Tasks (SWE-bench Verified instances, 12 repositories) | 500 | `data/tasks.jsonl` |
| Agent runs: 500 tasks × 4 models × 2 scaffolds × 2 settings | 8,000 | `paper/results/runs.csv` |
| Policy outcomes on those runs | 709,376 | `paper/results/verdicts.csv.gz` |

Each policy record holds its id, project, category (one of eight), evidence type
(`output`, `differential`, `trajectory`), check type (`exact` or `approximate`), a
human-in-the-loop flag, and the atomic policy text. The corpus workbooks also keep the
quoted source sentence, source URL and section, and the classification labels.

**Per project.** From 2 policies (seaborn) to 167 (matplotlib), and from 1 task (flask) to
231 (django). See Table 6 (`python paper/make_tables.py --only table6`).

**No personal data.** The corpus quotes public contributor documentation. The runs contain
model outputs on public repositories. Git identities inside runs are synthetic.

## Collection and processing

- **Sources.** Each project's developer documentation at its latest published build
  (August 2026), plus policy-bearing files outside the documentation navigation (pull-request
  templates, `AGENTS.md`). Django and SymPy were used to develop the rubrics and workflow;
  their final workbooks and checkers are included. For the other ten repositories, pages
  read, their roles and versions are in `rules/<prefix>/*-manifest.md` and `*-run-log.md`;
  raw off-navigation sources are in `*-raw-sources.md`.
- **Extraction and classification.** An LLM agent (Claude Opus 5, high reasoning effort)
  followed `rule-extraction/rule-extraction-workflow.md` with the two rubrics in the same
  folder. An author confirmed the page list and the extracted rows at fixed checkpoints, and
  `tools/audit_rules.py` ran the automated acceptance checks.
- **Checkers.** Written by an LLM agent from `docs/checker-authoring.md`, each with authored
  test cases, then reviewed. 150 of 823 were audited independently by two annotators
  (94.0% agreement, Cohen's κ = 0.72, 87.2% accepted). The audit materials are not part of
  this release.
- **Runs.** mini-SWE-agent and OpenHands at pinned commits, with GPT-5.6 Luna,
  Gemini 3.7 Flash, DeepSeek V4 Flash 0731 and Kimi K2.5. Functional grading used the
  SWE-bench harness. Compliance grading is deterministic and uses no model.

## Uses

**Intended.** Measuring and comparing policy compliance of coding agents; studying policy
retrieval (Native) versus policy reasoning (Consolidated); reusing the checkers or the
extraction pipeline for other repositories.

**Not intended.** Judging human contributors, or treating a compliance rate as a
merge-readiness verdict. Checkers encode one reading of each policy, and 529 of the 823
are approximate.

## Known limitations

- **Approximate checks.** 529 checks approximate a policy whose documentation leaves part
  of the reading open. Rates can be recomputed over the 294 exact checks (`check` column;
  Table 8).
- **Coverage.** 304 policies never trigger on any of the 8,000 runs, because bug-fix tasks
  rarely touch deprecations, documentation pages or releases (Table 14).
- **Withheld verdicts.** Some policies need evidence a stored run lacks, such as a full
  test-suite run or a type checker. These count as triggered but not graded, which mostly
  affects *Code and quality* and *Tests and test style* (Table 15).
- **Human-in-the-loop policies.** 18 policies address a human contributor, for example
  certifying authorship. They are flagged (`human_in_the_loop`) so rates can be computed
  without them.
- **Point in time.** Policies reflect each project's documentation as of August 2026, and
  projects revise their guidelines.
- **Single attempt.** Each (task, model, scaffold, setting) cell was run once.

## Distribution and maintenance

- **This release:** code, corpora, 500 tasks, per-run and per-policy outcomes, and one full
  example trajectory. The 8,000 full historical trajectories and checker-audit ratings are
  not included. The exported outcomes can reproduce aggregate results but cannot regrade
  every historical run from its original trajectory.
- **Licenses:** code under MIT (`LICENSE`). Policy text and raw sources quote each
  project's documentation and remain under that project's license. Task instances come from
  SWE-bench Verified.
- **Updates:** corpus versions are identified by the workbook named in each
  `rules/<prefix>/repo.conf`, and checker results record `checker_version`.

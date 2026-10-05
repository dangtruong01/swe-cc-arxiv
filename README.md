# Correct Code, Broken Contributions? SWE-CC: Benchmarking Repository Policy Compliance for Coding Agents

[![Paper: Download PDF](https://img.shields.io/badge/Paper-Download%20PDF-red.svg)](https://github.com/dangtruong01/swe-cc-arxiv/raw/main/paper/SWE-CC.pdf)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

SWE-CC measures whether coding agents follow repository **contribution policies**
(code and test style, testing workflow, commit and pull-request conventions,
AI-assistance disclosure) while solving real issues. It checks both what agents **did**
(their trajectories) and what they **delivered** (commits, patches, pull-request text).
This repository provides the benchmark, evaluation code, and paper results.

**Keywords:** coding agents, software engineering benchmarks, repository policies,
contribution compliance.

- **823 policies** from the contributor documentation of the 12 SWE-bench Verified
  repositories, each compiled into a deterministic **checker function**, with no LLM judge
  at scoring time.
- **500 end-to-end contribution tasks** built on SWE-bench Verified: fix the issue, commit,
  and write a pull request.
- **Two policy-provision settings.** In **Native**, the agent is pointed at the project's
  documentation and must find the policies itself. In **Consolidated**, the policies are
  mounted in the container as one file.
- Works with **any agent**: ready-made runners for mini-SWE-agent and OpenHands, and a plain
  JSON trajectory format for everything else.

## Main results

Current agents resolve most tasks but satisfy substantially fewer applicable repository
policies. Providing the policies directly improves compliance, although the best average
compliance rate remains 67.0%.

| Agent scaffold | Native resolve | Native compliance | Consolidated resolve | Consolidated compliance |
|---|---:|---:|---:|---:|
| mini-SWE-agent | 81.7% | 55.7% | 81.4% | 64.4% |
| OpenHands | 83.9% | 58.2% | 83.1% | 67.0% |

Results are averaged over the four evaluated models. **Native** provides the locations of
the governing policy documents and requires the agent to retrieve them. **Consolidated**
provides the extracted policies directly. The full model-level results are available in
[`paper/tables/table3.csv`](paper/tables/table3.csv) and in the paper.

## What this release lets you reproduce

1. **Run the benchmark on a new agent.** The tasks, policy corpora, checker code, tests,
   prompt additions, and runner configurations are included. The quick start below scores
   one complete example trajectory.
2. **Recalculate the paper's result tables and data-derived figures.** `paper/results/`
   contains the outcomes for all 8,000 experimental runs, including 709,376 per-policy
   verdicts. See [`paper/README.md`](paper/README.md) for commands and file formats.
3. **Repeat the experiments.** The scaffold setup, model configuration templates, and
   sweep scripts are included. Repeating all runs requires the model services, Docker,
   SWE-bench images, and substantial time and compute.

The 8,000 full historical trajectories are not included. Their exported outcomes support
recomputing the paper's aggregate results, but do not allow independent regrading of every
historical agent action. One complete example trajectory is included under `examples/`.
The independent checker-audit ratings are also outside this release; the paper describes
that validation procedure and its results.

## Install

Python 3.11.

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -e .
pytest -q
```

This installs the `swe-cc` command (the same as `python -m compliance`). Install in
editable mode (`-e`), because the checkers read the policy corpora from `rules/` next to
the package. Scoring itself uses only the standard library. `requirements.txt` pins the
test and plotting dependencies.

## Quick start

```bash
scripts/quickstart.sh
```

This scores one stored agent run (`examples/`) against SymPy's 142 policies and checks that
the verdicts match the stored ones. It then prints the task-prompt additions for one task,
and summarises a results directory. It needs network once, to clone SymPy's git history
(blobless, about 70 MB), so the checkers can rebuild the files the agent changed.

## Scoring a run

```bash
swe-cc check <trajectory.json> --project sympy --setting native --jsonl rows.jsonl
swe-cc retrieval <trajectory.json> --project sympy       # did the policies reach the model's context?
```

Each policy gets one outcome:

| outcome | meaning |
|---|---|
| `pass` / `fail` | the policy applied to the agent's work, and was satisfied or violated |
| `not_triggered` | the agent's work never brought the policy into scope |
| `withheld` | the policy applied, but the run lacks the evidence to judge it (e.g. a file that does not parse) |

**Triggering rate** = (pass + fail + withheld) / all policies, and **compliance rate** =
pass / (pass + fail). Report the two together. An agent that does less work triggers
fewer policies and can look more compliant.

## Evaluating your agent

**Any agent.** Run the tasks in `data/tasks.jsonl`, adding the prompt text from
`scripts/render_task.py`. Run `harness/probe.sh` before the agent starts and
`harness/collect.sh` after it finishes, and write each run as a plain JSON trajectory.
Then score with `swe-cc check run.json --scaffold own-agent --project <name>`. The full
protocol is in [`docs/evaluate-your-agent.md`](docs/evaluate-your-agent.md).

**mini-SWE-agent or OpenHands.** Each has one script that chains **agent run → functional
grading (SWE-bench harness) → compliance grading → summary**:

```bash
frameworks/setup.sh all          # clone both scaffolds at pinned commits and apply our changes
cp models/gpt-5.6-luna.conf models/my-model.conf   # edit LITELLM_ID; see models/README.md

MODELS=my-model CASES=sweeps/smoke.txt sweeps/run_mini_swe_agent.sh   # smoke test: 1 task x 2 settings
MODELS=my-model sweeps/run_mini_swe_agent.sh                          # all 500 tasks x 2 settings
MODELS=my-model sweeps/run_openhands.sh
```

Needs Docker, the SWE-bench images (pulled on demand) and your model provider's API key.
Runs go to `runs/`, and results to `results/` (`runs.csv`, `verdicts.csv.gz`,
`policies.csv`). Re-running a script resumes where it stopped. Summarise any results
directory with:

```bash
python scripts/summarize.py results                  # per scaffold x model x setting
python scripts/summarize.py results --by category    # per policy category
```

## What is in the benchmark

| Path | What it is |
|---|---|
| `rules/<prefix>/` | Policy corpus per project: classified workbook, frozen extraction, source manifest, raw sources, run log, and `CONTRIBUTING_RULES.md` (the Consolidated-setting file) |
| `compliance/` | Checker functions (`compliance/rules/<prefix>/`) and the scoring library: evidence bundles, trajectory adapters, metrics |
| `tests/` | Unit tests, including satisfied / violated / not-triggered cases for each checker |
| `data/` | The 500 tasks (`tasks.jsonl`) and the task-prompt additions (`prompts/`) |
| `harness/` | The probe and collect scripts run inside the agent's container |
| `frameworks/` | mini-SWE-agent and OpenHands runners (our changes on top of pinned upstream commits), and the `own-agent` adapter config |
| `models/` | Model configs (the four used in the paper serve as templates) |
| `sweeps/` | Task lists (all 500; a 1-task smoke test) and one script per scaffold |
| `tools/` | Bulk compliance scoring, functional re-grading, corpus acceptance checks |
| `scripts/` | `quickstart.sh`, `render_task.py`, `export_results.py` (runs → results), `summarize.py` |
| `examples/` | One complete agent run with its expected verdicts |
| `paper/` | Everything specific to the paper's experiments (see below) |
| `DATASHEET.md` | Composition, collection, intended use and limitations |

Corpus directories and policy ids use the SWE-bench instance prefix. Commands and results
accept the project name:

| prefix | project | prefix | project | prefix | project |
|---|---|---|---|---|---|
| `astropy` | astropy | `mwaskom` | seaborn | `pylint-dev` | pylint |
| `django` | django | `pallets` | flask | `pytest-dev` | pytest |
| `matplotlib` | matplotlib | `psf` | requests | `sphinx-doc` | sphinx |
| `scikit-learn` | scikit-learn | `pydata` | xarray | `sympy` | sympy |

The extraction procedure and rubrics were developed using **Django and SymPy** before
being applied to the other ten repositories. Their final classified workbooks, policy
files, and checkers are included. The standardized source manifests, frozen extraction
files, raw-source bundles, and run logs document the subsequent automated processing of
the other ten repositories; those four file types are not available for Django or SymPy.

## Extending to a new repository

Policies are extracted by the procedure in `rule-extraction/`: the workflow, the launcher
prompt, the two labelling rubrics, and the source-discovery script. `tools/corpus.py` and
`tools/audit_rules.py` check a new corpus. Checkers are written following
[`docs/checker-authoring.md`](docs/checker-authoring.md), and `tools/scaffold_checkers.py`
generates stubs from the corpus. A repository is `rules/<prefix>/repo.conf` plus its corpus,
a checker package under `compliance/rules/`, and an entry for it in `RULE_MODULES` in
`compliance/cli.py`.

## Reproducing the paper

[`paper/`](paper/README.md) holds the exported results of the paper's 8,000 runs (four
models, two scaffolds, two settings) and a script that regenerates the results-derived
tables and figures.

## License

Code is released under the MIT License (`LICENSE`). Policy text and raw sources under
`rules/` quote each project's contributor documentation and remain under that project's
license. Tasks derive from SWE-bench Verified.

## Citation

If you use SWE-CC, please cite the paper. This provisional entry will be updated when the
final publication metadata is available.

```bibtex
@misc{dang2027swecc,
  title  = {Correct Code, Broken Contributions? {SWE-CC}: Benchmarking Repository Policy Compliance for Coding Agents},
  author = {Dang, Truong Hai and Goh, Rayner and Le-Cong, Thanh and Huo, Yintong},
  year   = {2027},
  url    = {https://github.com/dangtruong01/swe-cc-arxiv}
}
```

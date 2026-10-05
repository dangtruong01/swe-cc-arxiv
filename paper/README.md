# Reproducing the paper

The paper evaluates four models (GPT-5.6 Luna, Gemini 3.7 Flash, DeepSeek V4 Flash 0731,
Kimi K2.5) under two scaffolds (mini-SWE-agent, OpenHands) and two settings (Native,
Consolidated) on all 500 tasks, for 8,000 runs.

## Released results

`results/` holds all 8,000 runs in the format `scripts/export_results.py` writes:

| File | One line per | Columns |
|---|---|---|
| `runs.csv` | run | `project, scaffold, model, instance_id, setting`, `resolved`, `functional_verdict`, `evaluation_gap`, retrieval (`attempted, retrieved` for Native; `opened, delivered` for Consolidated) |
| `verdicts.csv.gz` | run × policy (709,376) | `run, policy_id, outcome` |
| `policies.csv` | policy (823) | `project, category, evidence_type, check` (`exact` / `approximate`), `human_in_the_loop`, policy text |

The full historical trajectories are not part of this release. The exported per-policy
outcomes let readers recompute aggregate results, but independent regrading of every
historical run requires those original trajectories. One complete example trajectory is
provided in `examples/` at the repository root. The checker-audit ratings and sampling
materials are not included; tables based on that audit are documented in the paper.

## Tables and figures

```bash
python paper/make_tables.py                # results-derived items supported by this script
python paper/make_tables.py --only table3  # one item
```

Each item is printed and written to `paper/tables/<item>.csv`, and figures also to
`paper/figures/<item>.pdf`.

| Paper | Content | `--only` |
|---|---|---|
| Table 2 | Policies per category | `table2` |
| Table 3 | Triggering, compliance and resolve rate per model, scaffold and setting | `table3` |
| Table 4 | Triggering and compliance by category | `table4` |
| Table 5 | Policies reaching the model's context | `table5` |
| Table 6 | Per-project corpora | `table6` |
| Table 7 | One example policy per category | `table7` |
| Table 8 | Compliance over all vs exact checks | `table8` |
| Table 13 | Resolve rate vs public SWE-bench Verified results | `table13` |
| Table 14 | Policies never triggered | `table14` |
| Table 15 | Policies triggered and graded per category | `table15` |
| Figure 3 | Policy distribution by project | `figure3` |
| Figure 4 | Policies violated per resolving run | `figure4` |
| Figure 5 | Violations by evidence | `figure5` |
| Figure 6 | Runs with an evaluation gap | `figure6` |

Tables 1 and 9–12 and Figures 1–2 are descriptive or come from the checker audit, and are
not computed from the released results.

## Re-running the experiments

The configs used are in `models/` (`gpt-5.6-luna`, `gemini-3.7-flash`,
`deepseek-v4-flash-0731`, `kimi-k2.5`):

```bash
frameworks/setup.sh all
MODELS=gpt-5.6-luna,gemini-3.7-flash,deepseek-v4-flash-0731,kimi-k2.5 sweeps/run_mini_swe_agent.sh
MODELS=gpt-5.6-luna,gemini-3.7-flash,deepseek-v4-flash-0731,kimi-k2.5 sweeps/run_openhands.sh
python scripts/export_results.py --runs runs --out paper/results
python paper/make_tables.py
```

The full matrix is 8,000 runs.

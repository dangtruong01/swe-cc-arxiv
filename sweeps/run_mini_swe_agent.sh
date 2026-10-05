#!/usr/bin/env bash
# The mini-SWE-agent sweep: agent run -> functional grading -> compliance grading -> aggregation.
#
#   MODELS=my-model sweeps/run_mini_swe_agent.sh                       # all 500 tasks
#   MODELS=my-model CASES=sweeps/smoke.txt sweeps/run_mini_swe_agent.sh  # 2-run smoke test
#
# MODELS (required): comma-separated slugs, one models/<slug>.conf each. Optional:
# SETTINGS ("native consolidated"), CASES (default sweeps/instances.txt), JOBS (default 4),
# RUNS_ROOT (default runs/). Needs Docker, `frameworks/setup.sh mini-swe-agent`, and the
# API key for your model provider (see models/README.md). Re-running resumes.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

source "$root/mini-swe-agent-run/mini-swe-agent/.venv/bin/activate"
echo "== 1/4 agent runs (the SWE-bench grade runs inline after each run)"
MODELS="$litellm_ids" "$root/mini-swe-agent-run/mini-swe-agent/scripts/run_sweep.sh" \
  "$cases" "$conditions" "$jobs"

echo "== 2/4 functional grading of any run the inline grade missed"
python "$root/tools/regrade.py" --run

echo "== 3/4 compliance grading"
python "$root/tools/score_corpus.py" --framework mini-swe-agent

aggregate

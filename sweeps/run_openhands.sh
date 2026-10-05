#!/usr/bin/env bash
# The OpenHands sweep: agent run -> functional grading -> compliance grading -> aggregation.
#
#   MODELS=my-model sweeps/run_openhands.sh
#   MODELS=my-model CASES=sweeps/smoke.txt sweeps/run_openhands.sh      # 2-run smoke test
#
# Same environment variables as run_mini_swe_agent.sh. Needs Docker, uv, and
# `frameworks/setup.sh all` (functional grading uses the SWE-bench harness installed with
# mini-swe-agent). Re-running resumes.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

echo "== 1/4 agent runs"
MODELS="$litellm_ids" "$root/frameworks/openhands/run_sweep.sh" "$cases" "$conditions" "$jobs"

echo "== 2/4 functional grading (SWE-bench harness)"
python "$root/tools/regrade.py" --run

echo "== 3/4 compliance grading"
python "$root/tools/score_corpus.py" --framework openhands

aggregate

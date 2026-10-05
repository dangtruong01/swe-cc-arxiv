#!/usr/bin/env bash
# Grade a single instance's agent-produced patch with the official SWE-bench harness.
# Looks up the trajectory path in results/instance_map.json (instance_id -> traj path;
# trajectory filenames in this repo don't follow one fixed naming convention, so we
# don't guess), extracts the patch from info.submission into a predictions file, and
# runs the harness.
#
# Since Phase 0, info.submission is the /opt/collect.sh evidence bundle, not a bare
# patch: five delimited sections, with ===PATCH=== last. Everything after that marker
# is the patch. Trajectories recorded before Phase 0 have no marker and their
# submission IS the patch, so we fall back to using it whole.
#
# USAGE (venv must be active):
#   scripts/evaluate.sh <instance_id> <run_dir>
#   e.g. scripts/evaluate.sh sympy__sympy-11618 runs/sympy/sympy__sympy-11618/guided/attempt1
#
# The run directory is the unit of grading. Predictions, the harness run_id and the
# report all derive from it, so the same instance graded under a second condition
# cannot overwrite the first -- which is what happened when this was keyed on the
# instance id alone, and it silently destroyed the naive arm's functional results.
#
# Env overrides: MODEL_NAME, DATASET, RESULTS_DIR (legacy summary files only)
set -euo pipefail

instance="${1:?usage: evaluate.sh <instance_id> <run_dir>}"
run_dir="${2:?usage: evaluate.sh <instance_id> <run_dir>}"
[ -f "$run_dir/trajectory.json" ] || { echo "!! no trajectory.json in $run_dir" >&2; exit 2; }

slug="${instance//[^a-zA-Z0-9]/_}"
attempt="$(basename "$run_dir")"                       # attemptN
condition="$(basename "$(dirname "$run_dir")")"        # naive | guided | ...
cond_slug="${condition//[^a-zA-Z0-9]/_}"
# The model belongs in the run_id. Without it two models grading the same instance,
# condition and attempt share `logs/run_evaluation/<run_id>` -- and this script rm -rf's
# that directory on entry, so one run would delete the other's logs mid-flight. Harmless
# sequentially, corrupting in parallel.
model_dir_slug="$(basename "$(dirname "$(dirname "$(dirname "$run_dir")")")")"
run_id="${RUN_PREFIX:-}eval_${slug}__${model_dir_slug//[^a-zA-Z0-9]/_}__${cond_slug}__${attempt}"
results_dir="${RESULTS_DIR:-results}"
preds="${run_dir}/preds.json"
dataset="${DATASET:-princeton-nlp/SWE-bench_Verified}"
model_name="${MODEL_NAME:-openrouter/google/gemini-2.5-flash}"

mkdir -p "$results_dir"
# run_evaluation skips an instance if a report.json already exists for this
# run_id/model/instance, regardless of whether the patch content changed --
# harmless for resuming an interrupted batch, but silently stale if this
# instance was re-run with a NEW patch under the same run_id. Always start
# clean so grading reflects the current patch, not a cached one.
rm -rf "logs/run_evaluation/${run_id}"

# SWE-bench publishes amd64 images ONLY. The sweep pre-pulls with an explicit
# `--platform` before it runs a cell, so grading during a sweep finds the image already
# local and never notices. Grading on its own does not have that luxury: `regrade.py`
# and any grading of a run whose image has since been pruned must pull it themselves,
# and without this the pull resolves for the host architecture and fails with
# "no matching manifest for linux/arm64/v8" -- reported as an image build error, several
# steps from the cause.
#
# It bites in exactly the situation grading-after-the-fact exists for: the sweep prunes
# unused images under disk pressure, so the runs most likely to need re-grading are the
# ones whose images are gone.
export DOCKER_DEFAULT_PLATFORM="${DOCKER_DEFAULT_PLATFORM:-linux/amd64}"

# ...and that is not enough on its own. The SWE-bench harness pulls through the docker
# PYTHON SDK (`/v1.55/images/create`), which does not read DOCKER_DEFAULT_PLATFORM -- that
# variable is honoured by the docker CLI only. So the image is pulled here, by the CLI,
# with the platform stated explicitly; the harness then finds it local and never pulls.
# Exactly what run_sweep.sh does before running a cell, moved to where grading can rely
# on it too.
if [ "${SKIP_IMAGE_PULL:-0}" != "1" ]; then
  eval_image="swebench/sweb.eval.x86_64.$(echo "$instance" | sed 's/__/_1776_/' | tr '[:upper:]' '[:lower:]'):latest"
  if ! docker image inspect "$eval_image" >/dev/null 2>&1; then
    echo "== pulling $eval_image (linux/amd64)"
    docker pull --platform linux/amd64 "$eval_image" >/dev/null 2>&1 \
      || echo "!! could not pull $eval_image; grading will report an image error" >&2
  fi
fi

# The patch comes from `patch.diff` when it exists, and only otherwise from the
# trajectory. That ordering is what makes this script framework-agnostic: `patch.diff` is
# OUR convention, written by every framework's launcher, while `info.submission` is
# mini-swe-agent's trajectory format and does not exist in OpenHands' records. Reading the
# trajectory first would mean the second framework's runs could never be graded -- and
# `differential` rules read `bundle.evaluation`, so those runs would silently WITHHOLD
# rather than fail, and the two frameworks would stop being comparable on them.
python - "$run_dir" "$instance" "$preds" "$model_name" <<'PY'
import json, sys
from pathlib import Path
run_dir, instance, preds, model_name = sys.argv[1:5]
run = Path(run_dir)

patch_file = run / "patch.diff"
if patch_file.is_file() and patch_file.read_text().strip():
    patch, source = patch_file.read_text(), "patch.diff"
else:
    # Pre-Phase-0 and any run whose collection did not split the bundle out.
    submission = (json.load(open(run / "trajectory.json")).get("info") or {}).get("submission") or ""
    marker = "===PATCH==="
    if marker in submission:
        patch, source = submission.split(marker, 1)[1].lstrip("\n"), "collect.sh ===PATCH==="
    else:
        patch, source = submission, "raw submission (pre-Phase-0 trajectory)"

json.dump(
    [{"instance_id": instance, "model_name_or_path": model_name, "model_patch": patch}],
    open(preds, "w"), indent=2,
)
print(f"wrote {preds} (patch chars: {len(patch)}, from: {source})")
PY

# CACHE_LEVEL decides whether the harness DELETES the instance image on the way out.
# Default `env` is the harness's own default and what a one-off grading wants. Grading
# several cells of the SAME instance back to back wants `instance`: otherwise cell 1
# grades, the harness removes the image, and cell 2 falls back to the harness's own
# puller -- which issues a plain `docker pull`, and SWE-bench publishes linux/amd64 only,
# so on Apple Silicon it dies with `no matching manifest for linux/arm64/v8`. That is why
# re-grading after a prune graded the first cell of each instance and failed the rest.
#
# NAMESPACE decides whether the harness PULLS a prebuilt image or BUILDS one locally.
# `none` builds from the Dockerfiles. It is exposed for completeness and is NOT the fix
# for the arm64 failure described above -- that fix is CACHE_LEVEL=instance.
#
# The distinction cost an hour on 15 Sep, so it is worth stating. `no matching manifest
# for linux/arm64/v8` reads like the image does not exist for this architecture. It does:
# the pre-pull above fetches it with `--platform linux/amd64` and it runs under emulation.
# What 404s is the HARNESS's own internal pull, which passes no platform. So the image is
# always obtainable and the error is really about WHO pulls it -- reachable whenever the
# pre-pull has already put it in place, and only unreachable once cache_level=env has
# deleted it mid-instance. Verified by grading scikit-learn__scikit-learn-13496, one of
# the supposedly impossible instances, with CACHE_LEVEL=instance and the default
# namespace: resolved, first attempt.
python -m swebench.harness.run_evaluation \
  --dataset_name "$dataset" --split test \
  --predictions_path "$preds" \
  --instance_ids "$instance" \
  --cache_level "${CACHE_LEVEL:-env}" \
  --namespace "${NAMESPACE:-swebench}" \
  --run_id "$run_id" --max_workers 1

# Park the report beside the trajectory so a run is self-contained and nothing about
# it depends on a shared, instance-keyed file.
model_slug="${model_name//\//__}"
report="logs/run_evaluation/${run_id}/${model_slug}/${instance}/report.json"
if [ -f "$report" ]; then
  cp "$report" "${run_dir}/eval_report.json"
  echo "  eval report -> ${run_dir}/eval_report.json"
else
  echo "!! no report at $report -- grading produced nothing for this run" >&2
fi

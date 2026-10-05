#!/usr/bin/env bash
# Run the full matrix INSTANCE-MAJOR: for each instance, every (model, condition) cell,
# then drop the image and move on.
#
#   MODELS="a,b,c,d" scripts/run_sweep.sh <cases-file> [conditions] [jobs]
#
# WHY INSTANCE-MAJOR ORDER, and not model-major or repo-major. The order decides what an
# INTERRUPTED sweep is worth, and interruption is the normal case over 20+ hours:
#
#   model-major     stopped early -> model 1 complete, models 2-4 empty. No model comparison.
#   repo-major      stopped early -> one repo complete, the other empty. No repo comparison.
#   instance-major  stopped early -> N instances complete across EVERY model and arm.
#                   A balanced design, just a smaller n. Analysable at any moment.
#
# Cells are ORDERED instance-major but run from a CONTINUOUS QUEUE -- there is no barrier
# at the end of an instance. An earlier version waited for all 8 cells before starting the
# next instance, and cell durations vary from 1 to 14 minutes, so seven slots sat idle
# waiting for the slowest. Measured across the stored runs: ~12.7 hours of wall clock over
# a 70-instance sweep. The queue keeps every slot busy; at most two instances are ever in
# flight, so partial results stay effectively balanced.
#
# Resumability is inherited: run_test.sh skips any cell whose trajectory.json exists, so
# re-issuing this exact command continues where it stopped. Nothing to reset.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cases="${1:?usage: MODELS=a,b run_sweep.sh <cases-file> [conditions] [jobs]}"
conditions="${2:-naive guided}"
jobs="${3:-4}"
models="${MODELS:?set MODELS to a comma-separated list of litellm ids}"

[ -f "$cases" ] || { echo "no case list at $cases" >&2; exit 1; }

instances=()
while IFS= read -r line; do
  case "$line" in ""|\#*) continue ;; esac
  instances+=("$line")
done < "$cases"

IFS=',' read -ra model_list <<< "$models"
n_cells=$(( ${#model_list[@]} * $(echo "$conditions" | wc -w) ))
echo "== sweep: ${#instances[@]} instance(s) x ${#model_list[@]} model(s) x [$conditions]"
echo "== $(( ${#instances[@]} * n_cells )) cells total, $jobs at a time, instance-major"
echo "== resumable: completed cells are skipped, so re-run this command to continue"

# Absolute, because the resume probe below runs from this script's directory.
runs_root_abs="${RUNS_ROOT:-$(cd "$here/../../.." && pwd)/runs}"
framework_slug="${FRAMEWORK:-mini-swe-agent}"

started=$(date +%s)

# Every cell, ordered instance-major. Built up front so the queue never has to think.
cells=()
for instance in "${instances[@]}"; do
  for model in "${model_list[@]}"; do
    for condition in $conditions; do
      cells+=("${instance}|${model}|${condition}")
    done
  done
done
echo "== ${#cells[@]} cells queued"

# Pull an instance's image once, even when several of its cells start together. The lock
# is an atomic mkdir: the first cell pulls, the rest wait, nobody duplicates a 4 GB fetch.
ensure_image() {
  local inst="$1" img lock
  img="swebench/sweb.eval.x86_64.${inst//__/_1776_}:latest"
  docker image inspect "$img" >/dev/null 2>&1 && return 0
  lock="${TMPDIR:-/tmp}/.sweep-img-${inst}.lock"
  if mkdir "$lock" 2>/dev/null; then
    # SWE-bench publishes amd64 only; the platform must be explicit on Apple Silicon.
    docker pull --platform linux/amd64 "$img" >/dev/null 2>&1
    rmdir "$lock" 2>/dev/null || true
  else
    while [ -d "$lock" ]; do sleep 3; done
  fi
  docker image inspect "$img" >/dev/null 2>&1
}

launched=0
for cell in "${cells[@]}"; do
  IFS='|' read -r instance model condition <<< "$cell"
  while [ "$(jobs -rp | wc -l)" -ge "$jobs" ]; do sleep 2; done
  launched=$((launched + 1))

  (
    # A finished cell must cost nothing -- no image, no pull, no container.
    slug="${model##*/}"
    if [ -f "${runs_root_abs}/${instance%%__*}/${framework_slug}/${slug}/${instance}/${condition}/attempt1/patch.diff" ]; then
      exit 0
    fi
    ensure_image "$instance" || { echo "   !! no image for $instance"; exit 1; }

    SKIP_SUMMARY=1 MODEL="$model" CONDITION="$condition" MAX_ATTEMPTS="${MAX_ATTEMPTS:-1}" \
      "$here/run_test.sh" "$instance" >/dev/null 2>&1 &
    rp=$!
    # Wall-clock cap. The per-command timeout does not save you from a command that loops
    # printing forever: the pipe stays busy and the agent waits. A capped cell leaves no
    # patch.diff, so resume retries it rather than recording a phantom success.
    ( sleep "${CELL_TIMEOUT:-2400}"; kill -9 $rp 2>/dev/null ) & watchdog=$!
    wait $rp; rc=$?
    kill $watchdog 2>/dev/null
    [ $rc -eq 0 ] || echo "   FAIL ${instance##*-} ${slug} ${condition}"
    exit $rc
  ) &

  # Stop cleanly when the key runs low, rather than discovering it as a wall of failed
  # runs. An exhausted key returns 403 on every call, so the sweep keeps launching cells
  # that do the container setup, fail at the first API call, and leave nothing behind --
  # 68 cells burned that way before anyone looked. Checked every 20 cells; the endpoint
  # is free and takes no tokens.
  if [ $((launched % 20)) -eq 0 ] && [ -n "${OPENROUTER_API_KEY:-}" ]; then
    remaining=$(curl -s --max-time 15 https://openrouter.ai/api/v1/key \
      -H "Authorization: Bearer $OPENROUTER_API_KEY" 2>/dev/null \
      | python -c "import json,sys
try:
    d=json.load(sys.stdin)['data']; lim=d.get('limit')
    print(999999 if lim is None else round(lim-d.get('usage',0),2))
except Exception:
    print(999999)" 2>/dev/null || echo 999999)
    if [ "${remaining%%.*}" -lt "${MIN_CREDIT:-20}" ] 2>/dev/null; then
      echo ""
      echo "!! STOPPING: only \$${remaining} of credit left (floor \$${MIN_CREDIT:-20})."
      echo "   Completed cells are kept. Top up and re-run this command to continue."
      wait
      exit 3
    fi
  fi

  if [ $((launched % 20)) -eq 0 ]; then
    el=$(( $(date +%s) - started ))
    echo "   [$launched/${#cells[@]}] ${el}s elapsed | free $(df -g / | awk 'NR==2{print $4}')G"
    # Prune only under real disk pressure; images are ~1.4 GB marginal and re-pulling
    # costs bandwidth that disk was never short of.
    free_gb=$(df -g / | awk 'NR==2{print $4}')
    if [ "${free_gb:-999}" -lt "${DISK_FLOOR_GB:-40}" ]; then
      echo "   disk ${free_gb}G < ${DISK_FLOOR_GB:-40}G -- pruning unused images"
      docker image prune -af >/dev/null 2>&1 || true
    fi
  fi
done

wait
echo ""
echo "== sweep finished: ${#cells[@]} cells in $(( ($(date +%s) - started) / 60 )) minutes"

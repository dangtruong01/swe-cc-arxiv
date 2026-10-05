#!/usr/bin/env bash
# The OpenHands matrix, INSTANCE-MAJOR: for each instance, every (model, arm) cell, then
# drop its image and move on.
#
#   MODELS="a,b,c,d" frameworks/openhands/run_sweep.sh <cases-file> [conditions] [jobs]
#
# WHY INSTANCE-MAJOR. Two independent reasons here, where the other framework had one.
#
#   1. An interrupted sweep is still analysable. Stopped early it leaves N instances
#      complete across EVERY model and arm -- a balanced design, just a smaller n.
#      Model-major would leave model 1 complete and models 2-4 empty.
#
#   2. **The agent-server image is per INSTANCE, and it is 8.8 GB.** OpenHands builds one
#      FROM each SWE-bench base image, and the browser arm's build adds Chromium and a VNC
#      desktop on top of that. All eight cells of an instance share it, so doing them
#      together means one build; interleaving instances would mean rebuilding, or holding
#      dozens of 8.8 GB images at once. Neither is survivable on this disk.
#
# THE FIRST CELL OF EACH INSTANCE RUNS ALONE. It is the one that triggers the build, and
# eight parallel first-runs would race to build the same image eight times. Once it exists
# the rest of the cells share it and run `jobs` at a time.
#
# Resumability is inherited from run_test.sh: a cell whose `patch.diff` exists is skipped,
# so re-issuing this exact command continues where it stopped. Nothing to reset.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project="$(cd "$here/../.." && pwd)"

cases="${1:?usage: MODELS=a,b run_sweep.sh <cases-file> [conditions] [jobs]}"
conditions="${2:-naive guided}"
jobs="${3:-4}"
models="${MODELS:?set MODELS to a comma-separated list of litellm ids}"
browser="${BROWSER:-on}"

[ -f "$cases" ] || { echo "no case list at $cases" >&2; exit 1; }

instances=()
while IFS= read -r line; do
  case "$line" in ""|\#*) continue ;; esac
  instances+=("$line")
done < "$cases"

IFS=',' read -ra model_list <<< "$models"
n_cells=$(( ${#model_list[@]} * $(echo "$conditions" | wc -w) ))
echo "== openhands sweep: ${#instances[@]} instance(s) x ${#model_list[@]} model(s) x [$conditions], browser=$browser"
echo "== $(( ${#instances[@]} * n_cells )) cells, $n_cells per instance, $jobs at a time after the build"
echo "== per-cell wall clock cap: $(( ${CELL_TIMEOUT:-2700} / 60 )) min"
echo "== resumable: completed cells are skipped, so re-run this command to continue"

runs_root="${RUNS_ROOT:-$project/runs}"
floor_gb="${DISK_FLOOR_GB:-45}"
started=$(date +%s)

free_gb() { df -g / | awk 'NR==2{print $4}'; }

# Block until this instance's agent-server image exists, so the remaining cells can start
# against it instead of waiting out the first cell's agent run.
#
# Returns early -- rather than spinning -- if the cell that was supposed to build died or
# was skipped. A cell whose patch.diff already exists exits at once and builds nothing, so
# on a resume there is no image coming and the other cells must be allowed to proceed (they
# are almost certainly skips too).
wait_for_image() {
  local inst="$1" pid="$2" custom waited=0 limit="${BUILD_TIMEOUT:-3600}"
  custom="sweb.eval.x86_64.${inst//__/_1776_}"
  while :; do
    if docker images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null \
         | grep -F "$custom" | grep -qF "eval-agent-server"; then
      echo "   image ready after ${waited}s -- releasing the remaining cells"
      return 0
    fi
    kill -0 "$pid" 2>/dev/null || { echo "   build cell exited (skip or failure) after ${waited}s"; return 0; }
    [ "$waited" -ge "$limit" ] && { echo "   !! no image after ${waited}s -- releasing anyway"; return 1; }
    sleep 10; waited=$((waited + 10))
  done
}

# The image for one instance, and EVERY tag the build produced for it.
#
# THE BUG THIS REPLACES. The old version grepped the tag list for
# `sweb.eval.x86_64.<instance>`. A build emits THREE tags for one image, and the third
# TRUNCATES the instance id, so the grep matched two and missed one:
#
#   43376f1-sweb.eval.x86_64.django_1776_django-10097-source            <- matched
#   43376f1868ffd...-sweb.eval.x86_64.django_1776_django-10097-source   <- matched
#   43376f1-sweb.eval.x86_64.django_1776_django-1009_tag_latest-...     <- MISSED
#
# Removing two of three tags does not free anything: the third still references the 9 GB
# image, so every finished instance leaked one. Measured 3 Sep 2026 at six shards: free
# space fell 40G -> 12G in about forty minutes, and the floor prune below never fired
# once while disk went from 91G to 22G, because it only runs at an instance boundary and
# those are up to an hour apart.
#
# THE FIX is to stop pattern-matching tags. Resolve the image ID from any tag that does
# match, then remove every tag that image actually has -- which picks up the truncated one
# without having to reverse-engineer how it was truncated.
#
# `docker rmi <tag>` WITHOUT -f, deliberately. Untagging lets Docker delete the image only
# when its last tag goes, and its refcounting then keeps any layer another image still
# shares. `rmi -f <id>` overrides exactly that, which is how a background reclaimer broke
# four cells with `NotFound: content digest ... not found` on 3 Sep.
#
# WHY THIS IS SAFE HERE AND A BACKGROUND TIMER WAS NOT. This runs inside the shard at an
# instance boundary, after `wait` -- every cell of this instance has finished and its
# containers are reaped. Three timer-driven reclaimers were tried that day and all three
# removed images out from under builds that were still running. Reclaiming synchronously,
# where the sweep already knows it is done with an image, is the difference.
drop_instance_image() {
  local inst="$1" custom id

  custom="sweb.eval.x86_64.${inst//__/_1776_}"
  id="$(docker images --format '{{.ID}} {{.Repository}}:{{.Tag}}' 2>/dev/null \
        | grep -F "$custom" | grep -F "eval-agent-server" | awk '{print $1}' | head -1)"
  [ -n "$id" ] || return 0

  # Never take an image a container still holds. Another shard cannot be running this
  # instance -- shards are disjoint -- but a cell of ours may have outlived its reaper.
  [ -n "$(docker ps -aq --filter ancestor="$id" 2>/dev/null)" ] && return 0

  docker image inspect "$id" --format '{{range .RepoTags}}{{println .}}{{end}}' 2>/dev/null \
    | grep . | xargs -r -n1 docker rmi >/dev/null 2>&1 || true
}

# A cell gets a wall-clock budget as well as an iteration budget, because the two bound
# different things. `max_iterations` stops an agent taking too many turns; at ~10s a turn
# 2000 of them is still five hours. Only a clock bounds how long a sweep takes.
#
# A capped cell leaves no `patch.diff`, so resume retries it rather than recording a
# phantom success -- the same contract the other framework's sweep uses, and the reason
# `patch.diff` is written last and never written empty.
# The directory a cell writes to, mirroring run_test.sh's own layout rule. Needed here
# only so a timed-out cell's container can be found from the log it leaves behind.
cell_dir() {
  local instance="$1" model="$2" condition="$3" slug="${2##*/}"
  [ "$browser" = "off" ] && slug="${slug}-nobrowser"
  echo "${runs_root}/${instance%%__*}/openhands/${slug}/${instance}/${condition}/attempt1"
}

# Remove the agent-server container a cell left behind. A container is not a child
# process -- it belongs to the docker daemon -- so no signal to the host process tree
# touches it, and while it runs `docker rmi` refuses to reclaim the 8.8 GB image beneath
# it. The SDK logs the container's 64-hex id as it polls `docker inspect`, which is the
# only place the cell's own identity and the daemon's agree.
reap_cell_container() {
  local log id
  log="$(cell_dir "$1" "$2" "$3")/logs/instance_${1}.log"
  [ -f "$log" ] || return 0
  for id in $(grep -oE '\b[0-9a-f]{64}\b' "$log" 2>/dev/null | sort -u); do
    docker rm -f "$id" >/dev/null 2>&1 || true
  done
}

# --- circuit breaker: stop marching when every cell is failing instantly ----------
# A cell that dies in seconds has not run an agent; it hit something environmental --
# ghcr.io unreachable, the API key exhausted, docker wedged. The sweep's resume rule then
# works against us: each such cell leaves no `patch.diff`, the shard counts it and moves
# to the next instance, and a shard can eat its whole list in minutes while recording
# nothing. Measured 3 Sep 2026: a 57-minute ghcr.io outage destroyed **1,370 cells** this
# way, four shards racing to the end of their case files. The same shape was seen in
# the SymPy pilot (a 26-instance retry "finished"
# 208 cells in one minute and recovered none).
#
# So: count consecutive cells that exit fast WITHOUT a patch, and abort the shard once the
# streak passes the limit. Any cell that produces a patch clears it. Aborting is the
# useful behaviour -- the instances not yet attempted stay unattempted, so a later resume
# retries them properly instead of finding them "done" and empty.
fastfail="$(mktemp -t ohsweep_fastfail)"
: > "$fastfail"
trap 'rm -f "$fastfail"' EXIT

note_cell_outcome() {
  local d elapsed
  d="$(cell_dir "$1" "$2" "$3")"
  elapsed=$(( $(date +%s) - $4 ))
  if [ -s "$d/patch.diff" ]; then
    : > "$fastfail"                       # a real result clears the streak
  elif [ "$elapsed" -lt "${FASTFAIL_SECONDS:-60}" ]; then
    echo x >> "$fastfail"
  fi
}

fastfail_tripped() {
  [ "$(wc -l < "$fastfail" 2>/dev/null | tr -d ' ')" -ge "${FASTFAIL_LIMIT:-12}" ]
}

run_cell() {
  local instance="$1" model="$2" condition="$3" pid watchdog started
  started=$(date +%s)
  # `set -m` enables job control so the backgrounded cell becomes the leader of its OWN
  # process group. Without it every cell shares the sweep's group, `kill -9 -"$pid"`
  # would signal the sweep itself, and `kill -9 "$pid"` reaches only the wrapper -- which
  # is the defect this replaces: the wrapper's python survived, reparented to init, and
  # kept calling the API unsupervised while the sweep moved on to the next cell.
  set -m
  MODEL="$model" CONDITION="$condition" BROWSER="$browser" \
    "$here/run_test.sh" "$instance" >/dev/null 2>&1 &
  pid=$!
  set +m
  ( sleep "${CELL_TIMEOUT:-2700}"
    kill -9 -"$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
    sleep 2
    reap_cell_container "$instance" "$model" "$condition"
  ) & watchdog=$!
  wait "$pid" 2>/dev/null
  kill "$watchdog" 2>/dev/null
  wait "$watchdog" 2>/dev/null || true

  # Reap on EVERY exit path, not just the watchdog's. A cell that fails with an error --
  # `Remote conversation got stuck`, `Server disconnected`, the classes that caused most of
  # this corpus's losses -- leaves its container running: the SDK issues `docker stop` but
  # does not wait for or verify it. Each orphan holds ~450 MiB and pins the 8.8 GB image
  # against `drop_instance_image`, so disk reclamation silently stops working.
  #
  # Measured 2 Sep 2026: 30 containers alive against 21 live cells, the oldest 4 hours old,
  # while the janitor was fighting a disk floor it could not win.
  reap_cell_container "$instance" "$model" "$condition"
  note_cell_outcome "$instance" "$model" "$condition" "$started"
}

done_cells=0
total_cells=$(( ${#instances[@]} * n_cells ))

for instance in "${instances[@]}"; do
  echo
  echo "== $instance  [$((done_cells))/$total_cells cells done, $(free_gb)G free]"

  # Build the image once, by starting a single cell and letting it trigger the build.
  #
  # THE RELEASE CONDITION IS THE IMAGE, NOT THE CELL. This used to run the first cell to
  # COMPLETION before starting any other, which serialised a ~50 min agent run in order to
  # wait for a ~5 min build. Measured on the rehearsal: build finished 5.5 min in, the cell
  # ran alone for another 46, and the remaining seven then took 22 min together. Waiting on
  # the image instead of the cell gives those 46 minutes back -- an instance becomes
  # `build + slowest cell` rather than `build + first cell + the rest`.
  #
  # (The old shape was masked during the rehearsal by the watchdog defect: killing the
  # first cell early released the others early, so the bug was accidentally doing what this
  # now does on purpose.)
  # THE BUILD CELL MUST BE ONE THAT WILL ACTUALLY RUN. Taking model_list[0] blindly is
  # correct only on a fresh sweep. On a RESUME -- which is exactly what a retry pass is --
  # that cell usually already has its patch.diff, so it exits in 0s having built nothing,
  # `wait_for_image` sees the process gone and releases everyone, and N cells then race to
  # build the same 8.8 GB image at once. Observed 2 Sep 2026: a 26-instance retry
  # "finished" 208 cells in one minute and recovered none of them.
  #
  # So: scan for the first cell still lacking a patch and let that one build.
  first_model=""; first_condition=""
  for _m in "${model_list[@]}"; do
    for _c in $conditions; do
      if [ ! -f "$(cell_dir "$instance" "$_m" "$_c")/patch.diff" ]; then
        first_model="$_m"; first_condition="$_c"; break 2
      fi
    done
  done

  if [ -z "$first_model" ]; then
    echo "   all $n_cells cells already complete -- nothing to build, moving on"
    done_cells=$((done_cells + n_cells))
    continue
  fi

  echo "   build cell: ${first_model##*/} / $first_condition"
  ( run_cell "$instance" "$first_model" "$first_condition" ) & first_pid=$!
  done_cells=$((done_cells + 1))
  wait_for_image "$instance" "$first_pid"

  # The remaining cells share that image.
  for model in "${model_list[@]}"; do
    for condition in $conditions; do
      [ "$model" = "$first_model" ] && [ "$condition" = "$first_condition" ] && continue
      while [ "$(jobs -rp | wc -l)" -ge "$jobs" ]; do sleep 5; done
      ( run_cell "$instance" "$model" "$condition" ) &
      done_cells=$((done_cells + 1))
    done
  done
  wait

  if fastfail_tripped; then
    echo
    echo "!! ABORT: ${FASTFAIL_LIMIT:-12} cells in a row exited in under ${FASTFAIL_SECONDS:-60}s with no patch."
    echo "!! That is an environment failure (ghcr.io, the API key, docker), not an agent"
    echo "!! result. Stopping so the remaining instances stay unattempted and a resume can"
    echo "!! retry them. Fix the cause, then re-run this exact command."
    exit 3
  fi

  # Reclaim before the next instance. Its 8.8 GB is dead weight the moment the last cell
  # of this instance finishes, and the next instance needs room to build its own.
  if [ "${KEEP_IMAGES:-0}" != "1" ]; then
    drop_instance_image "$instance"
    if [ "$(free_gb)" -lt "$floor_gb" ]; then
      echo "   disk $(free_gb)G < ${floor_gb}G -- pruning dangling layers"
      docker image prune -f >/dev/null 2>&1 || true
    fi
  fi
done

elapsed=$(( $(date +%s) - started ))
echo
echo "== sweep finished: $total_cells cells in $((elapsed/60)) min, $(free_gb)G free"

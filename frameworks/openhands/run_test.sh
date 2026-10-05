#!/usr/bin/env bash
# Run ONE SWE-bench instance under OpenHands, filed the way every other run in this
# project is filed. The counterpart to mini-swe-agent-run/mini-swe-agent/scripts/run_test.sh,
# and deliberately the same shape: same CONDITION vocabulary, same resume rule, same
# runs/<repo>/<framework>/<model>/<instance>/<condition>/attemptN layout, same
# models/<slug>.conf and rules/<repo>/repo.conf as the single sources of truth.
#
# Two arms only, `naive` and `guided`. `none` never had runs and `naive-salient` was
# retired 25 Aug 2026 having changed nothing.
#
# BROWSER=on|off selects the arm this framework exists to compare. `off` is what upstream
# does for SWE-bench; `on` is the point. It is NOT a condition -- both arms run under both
# conditions -- so it lands in the model slug rather than the condition directory, keeping
# `naive` and `guided` meaning the same thing across every framework.
#
# USAGE (from the SWE-CC repository root, Docker running, OPENROUTER_API_KEY set):
#   CONDITION=guided MODEL=openrouter/openai/gpt-5.6-luna \
#     frameworks/openhands/run_test.sh django__django-11099
set -euo pipefail

instance="${1:?usage: run_test.sh <instance_id>}"

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project="$(cd "$here/../.." && pwd)"
benchmarks="${OPENHANDS_BENCHMARKS:-$project/openhands-run/benchmarks}"

condition="${CONDITION:-naive}"
case "$condition" in
  naive|guided) ;;
  *) echo "!! CONDITION must be naive or guided (got '$condition')" >&2; exit 2 ;;
esac

browser="${BROWSER:-on}"
case "$browser" in on|off) ;; *) echo "!! BROWSER must be on or off" >&2; exit 2 ;; esac

framework="${FRAMEWORK:-openhands}"
model="${MODEL:-openrouter/openai/gpt-5.6-luna}"
model_slug="${MODEL_SLUG:-${model##*/}}"
# The browser arm is part of the cell's identity, not of its condition. Without it in the
# path, browser-on and browser-off runs of one instance under one condition land in one
# directory separated only by the attempt counter -- which reads as one run retried, and
# merges in every aggregate that groups by run.
[ "$browser" = "off" ] && model_slug="${model_slug}-nobrowser"

repo_slug="${REPO_SLUG:-${instance%%__*}}"
runs_root="${RUNS_ROOT:-$project/runs}"
attempt="${START_ATTEMPT:-1}"
resume_dir="${runs_root}/${repo_slug}/${framework}/${model_slug}/${instance}/${condition}/attempt${attempt}"

# --- resume: a completed run is never redone --------------------------------------
# `patch.diff` is the completion marker, NOT `trajectory.json`. A run killed during
# collection leaves a trajectory behind and would be skipped forever as "done" while
# carrying no patch and no bundle. Same rule as the other harness, for the same reason.
if [ "${FORCE:-0}" != "1" ] && [ -f "$resume_dir/patch.diff" ]; then
  echo "== SKIP $instance ($condition, ${model_slug}) -- already done: $resume_dir"
  exit 0
fi

# Everything repo-specific comes from rules/<repo>/repo.conf, keyed off the instance
# prefix. No repository is named in this script.
repo_dir="${RULES_DIR:-$project/rules}/${repo_slug}"
if [ -f "$repo_dir/repo.conf" ]; then
  # shellcheck disable=SC1091
  . "$repo_dir/repo.conf"
else
  echo "!! no $repo_dir/repo.conf (see rules/sympy/repo.conf)" >&2; exit 2
fi

rules_file="${RULES_FILE:-$repo_dir/CONTRIBUTING_RULES.md}"
docs_url="${DOCS_URL:-}"

if [ "$condition" = "naive" ] && [ -z "$docs_url" ]; then
  echo "!! CONDITION=naive needs DOCS_URL in $repo_dir/repo.conf" >&2; exit 2
fi
if [ "$condition" = "guided" ] && [ ! -f "$rules_file" ]; then
  # The mounted rules file IS the treatment; a missing one silently degrades the guided
  # arm into a control that still produces a plausible-looking run.
  echo "!! CONDITION=guided needs RULES_FILE; '$rules_file' does not exist" >&2; exit 2
fi

# Model settings come from models/<slug>.conf, exactly as for the other framework.
# Environment wins over file: sourcing a conf overwrites anything already exported, and
# a silently ignored explicit override once invalidated a control run.
_env_reasoning="${REASONING_EFFORT-__UNSET__}"
models_dir="${MODELS_DIR:-$project/models}"
base_slug="${model##*/}"
if [ -f "$models_dir/${base_slug}.conf" ]; then
  # shellcheck disable=SC1091
  . "$models_dir/${base_slug}.conf"
fi
[ "$_env_reasoning" != "__UNSET__" ] && REASONING_EFFORT="$_env_reasoning"

# --- this framework's own view of how to dial that model ------------------------------
# Sourced AFTER models/<slug>.conf, so it overrides it -- and read by this script alone.
#
# `models/<slug>.conf` says what a model IS, and BOTH frameworks read it: mini-swe-agent's
# scripts/run_test.sh has the identical `RUN_ROUTE="${LITELLM_ID:-$model}"`. So a reroute
# needed only here cannot go in that file without silently moving the other sweep too.
# Where the model is DIALLED FROM differs between the frameworks -- host for
# mini-swe-agent, inside the container for this one -- and that is exactly what this
# directory records. Absent file = no override, which is every model but gemini.
overrides_dir="${MODEL_OVERRIDES_DIR:-$here/model-overrides}"
if [ -f "$overrides_dir/${base_slug}.conf" ]; then
  # shellcheck disable=SC1091
  . "$overrides_dir/${base_slug}.conf"
  echo "   override: $overrides_dir/${base_slug}.conf"
fi

# --- routing vs reporting, and which key pays ----------------------------------------
# A model's conf may now route somewhere other than OpenRouter. Three ids are involved
# and conflating them is how a corpus fragments:
#
#   LITELLM_ID    what litellm dials             e.g. gemini/gemini-3.7-flash
#   CANONICAL_ID  what the corpus is keyed on    e.g. openrouter/google/gemini-3.7-flash
#   model_slug    the run directory              e.g. gemini-3.7-flash
#
# `model` (and so `model_slug`, the directory) is left alone: it is derived from MODEL,
# and `${model##*/}` yields `gemini-3.7-flash` under either id, so no stored run moves.
#
# CANONICAL_ID defaults to the routing id, so every model that has not been rerouted is
# unaffected and needs no conf change.
RUN_ROUTE="${LITELLM_ID:-$model}"
RUN_LABEL="${CANONICAL_ID:-$RUN_ROUTE}"
RUN_KEY_ENV="${API_KEY_ENV:-OPENROUTER_API_KEY}"
# Empty for every model that talks to a provider directly, which is all but gemini.
RUN_BASE_URL="${BASE_URL:-}"
# Provenance only. When a route is an endpoint rather than a provider, RUN_ROUTE stops
# naming who actually served the tokens; this carries that, and nothing dials it.
RUN_UPSTREAM_ROUTE="${UPSTREAM_ROUTE:-}"

# A base_url means the credential lives at the far end, not in the container -- so the
# Vertex project/location belong to whatever holds it, and are NOT exported here. They
# stay in models/gemini-3.7-flash.conf for mini-swe-agent, which runs the model host-side
# where the ADC is, and are consumed by the proxy's own config.yaml for this framework.
if [ -n "$RUN_BASE_URL" ]; then
  # Pre-flight, for the same reason the key check below exists. Without this a dead
  # proxy is discovered inside the agent as a litellm APIConnectionError that reads like
  # a provider outage -- after the image is built and the container is up, which on this
  # hardware is ~9 minutes of emulated build per cell.
  #
  # Checked on the LOOPBACK, not on RUN_BASE_URL. `host.docker.internal` is a name the
  # container resolves and this host does not (verified: no /etc/hosts entry, no DNS), so
  # health-checking the container's URL from here would fail every time, including --
  # worst case -- while the proxy was perfectly healthy.
  _probe_url="$(printf '%s' "$RUN_BASE_URL" | sed 's|//host\.docker\.internal:|//127.0.0.1:|')"
  if ! curl -sf -m 5 -o /dev/null "${_probe_url}/health/liveliness" 2>/dev/null; then
    echo "!! no proxy answering at $_probe_url (container would dial $RUN_BASE_URL)" >&2
    echo "   $model is dialled through it, and the container has no Google credential" >&2
    echo "   of its own -- by design. Start it with:" >&2
    echo "     frameworks/openhands/proxy/run_proxy.sh" >&2
    exit 2
  fi
  echo "   proxy: $RUN_BASE_URL -> ${RUN_UPSTREAM_ROUTE:-upstream} (credential stays host-side)"
fi


# Fail here rather than inside the agent. A missing key surfaces mid-run as a litellm
# APIError that reads like a network fault -- exactly how a $1,300 key cap cost an hour of
# misdiagnosis on 3 Sep, because the visible line was `[Errno 61] Connection refused` and
# the real 403 was above it.
if [ -z "$(eval "printf '%s' \"\${$RUN_KEY_ENV:-}\"")" ]; then
  echo "!! $RUN_KEY_ENV is not set, and $model routes through it" >&2; exit 2
fi
[ "$RUN_ROUTE" != "$RUN_LABEL" ] && \
  echo "   route: $RUN_ROUTE via \$$RUN_KEY_ENV  (reported as $RUN_LABEL)"

# The repo cache, for compliance scoring's patch reconstruction. Created here, in the run
# path, because scoring is pure and offline by design and `git clone` is network I/O.
# Without it every rule that reads a file body withholds -- correctly, per invariant 6,
# and invisibly: the report still prints a coherent table, several points low.
if [ -n "${REPO_URL:-}" ] && [ "${SKIP_REPO_CACHE:-0}" != "1" ]; then
  cache_root="${REPO_CACHE_ROOT:-$project/.cache/repos}"
  if [ ! -e "$cache_root/$repo_slug/.git" ] && [ ! -e "$cache_root/$repo_slug/HEAD" ]; then
    mkdir -p "$cache_root"
    python3 -c "import sys; sys.path.insert(0, '$project');
from compliance.bundle.reconstruct import ensure_clone; ensure_clone('$repo_slug')" \
      || echo "!! could not cache $repo_slug; file-body rules will withhold" >&2
  fi
fi

mkdir -p "$resume_dir"
exec > >(tee "$resume_dir/run.log") 2>&1

# SWE-bench publishes amd64 images ONLY, and OpenHands builds its agent-server image
# FROM one of them. On Apple Silicon `docker buildx build` resolves the base for the
# host architecture, finds no arm64 manifest, and fails with
# "no match for platform in manifest: not found". The other harness already pins this
# on its `docker pull`; the build needs it too.
#
# Runs under emulation, so slower than native -- which is what the django sweep is
# already living with.
export DOCKER_DEFAULT_PLATFORM="${DOCKER_DEFAULT_PLATFORM:-linux/amd64}"

# The image tag benchmarks EXPECTS and the tag the SDK's builder PRODUCES disagree:
# `get_phased_image_tag_prefix()` wants `{sdk_sha}-{dockerfile_content_hash}` while the
# builder emits `{sdk_sha}` alone, so every build "succeeds" and is then rejected as the
# wrong tag. `IMAGE_TAG_PREFIX` is upstream's documented override for exactly this.
#
# Bypassing the content hash is safe HERE and would not be in general. The hash exists so
# a changed Dockerfile invalidates cached assemblies; we pin the SDK by sha in
# frameworks/openhands.conf, so the Dockerfile cannot change underneath a sweep. Unpin
# the SDK and this line becomes a stale-image bug.
if [ -z "${IMAGE_TAG_PREFIX:-}" ]; then
  IMAGE_TAG_PREFIX="$(cd "$benchmarks" && git submodule status vendor/software-agent-sdk \
    | awk '{print $1}' | tr -d '+-' | cut -c1-7)"
  [ -n "$IMAGE_TAG_PREFIX" ] || { echo "!! could not read the sdk submodule sha" >&2; exit 2; }
fi
export IMAGE_TAG_PREFIX
echo "   image tag prefix: $IMAGE_TAG_PREFIX"

echo "== $instance | condition=$condition | browser=$browser | model=$model"
echo "   -> $resume_dir"

# --- attempts: an empty patch is a failed attempt, not a finished run ----------------
# The other harness learned this from runs that mangled their submit command: the agent
# had done real work, the trajectory looked complete, and nothing gradeable came out.
# Here the equivalent is an agent that never ran the collect wrapper, or hit the iteration
# cap -- both of which return no patch at all rather than a partial one.
#
# Every attempt keeps its own directory. A failed attempt is evidence too, and the
# empty-submission failure that motivated this in the first place would have been
# invisible if attempts overwrote each other.
max_attempts="${MAX_ATTEMPTS:-1}"
last_attempt=$(( attempt + max_attempts - 1 ))

while :; do
run_dir="${runs_root}/${repo_slug}/${framework}/${model_slug}/${instance}/${condition}/attempt${attempt}"
mkdir -p "$run_dir"

# --- clear upstream's resume state, because it disagrees with ours -------------------
# The evaluator derives what to run from `output.critic_attempt_N.jsonl` in
# `eval_output_dir`, and `get_completed_instances()` counts an instance as completed
# "regardless of success/failure". Our completion marker is `patch.diff`. So a cell that
# errored is finished to upstream and unfinished to us, and re-running it makes the
# evaluator report "No instances to process", store nothing, and exit in ~3 seconds --
# a retry that looks like it ran and silently recovers nothing.
#
# Observed 2 Sep 2026: a 26-instance retry pass "finished" 208 cells in one minute and
# recovered none. We only reach this line when `patch.diff` is absent (the resume guard
# above returns early otherwise), so the cell is genuinely incomplete and upstream's
# state for it is stale by definition.
rm -f "$run_dir"/output.jsonl "$run_dir"/output.critic_attempt_*.jsonl

cd "$benchmarks"
RUN_MODEL="$RUN_LABEL" \
RUN_ROUTE="$RUN_ROUTE" \
RUN_BASE_URL="$RUN_BASE_URL" \
RUN_UPSTREAM_ROUTE="$RUN_UPSTREAM_ROUTE" \
RUN_KEY_ENV="$RUN_KEY_ENV" \
RUN_REASONING="${REASONING_EFFORT:-default}" \
RUN_ATTEMPT="$attempt" \
RUN_INSTANCE_ID="$instance" \
COMPLIANCE_CONDITION="$condition" \
COMPLIANCE_DOCS_URL="$docs_url" \
COMPLIANCE_RULES_FILE="$rules_file" \
COMPLIANCE_BROWSER="$browser" \
COMPLIANCE_RUN_DIR="$run_dir" \
COMPLIANCE_PROMPT="$project/frameworks/openhands/prompts/compliance.j2" \
PYTHONPATH="$project/frameworks/openhands" \
  uv run python -m run_cli "$instance" || true

if [ -s "$run_dir/patch.diff" ]; then
  echo "== done: $run_dir"
  break
fi
echo "!! attempt ${attempt} produced no patch -- kept at $run_dir for inspection" >&2
if [ "$attempt" -ge "$last_attempt" ]; then
  echo "!! all ${max_attempts} attempt(s) for $instance produced no patch" >&2
  break
fi
attempt=$((attempt + 1))
done

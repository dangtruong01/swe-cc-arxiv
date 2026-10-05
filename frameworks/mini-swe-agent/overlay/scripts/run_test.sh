#!/usr/bin/env bash
# Run and grade ONE SWE-bench Verified instance end to end: launches the agent,
# grades it through the official SWE-bench harness, renders a readable transcript,
# and updates results/summary.{md,json}. This is the one script to run for a single test.
#
# Grading is keyed on the RUN DIRECTORY, not the instance id, so the same instance
# graded under a second condition no longer overwrites the first. The report lands in
# the run directory beside the trajectory. results/instance_map.json is still written
# for the legacy summary scripts, but nothing about grading depends on it.
#
# If a run finishes with exit_status Submitted but an EMPTY patch (a known
# mini-swe-agent failure mode: the agent mangled its final submit command, so no
# patch bytes ever reached the transcript, even though real work may have
# happened), that attempt is unusable for grading. Rather than silently leaving a
# dead trajectory behind, this retries with a fresh attempt (up to MAX_ATTEMPTS
# times). Every attempt keeps its own directory -- a failed attempt is evidence
# too, and the empty-submission failure that motivated the collect script would
# have been invisible if attempts overwrote each other.
#
# CONDITION selects the experimental arm (see swebench_pr_compliance.yaml):
#   none    control, no pointer to the guidelines.             network ON
#   naive   docs URL mid-prompt, agent must fetch it.           network ON
#   naive-salient  same sentences, moved to the top (salience test)  network ON
#   guided  rules file mounted read-only at /rules/...md.      network OFF
# The condition drives the container's run_args (bind mounts) and
# the RUN_* env vars, which are both the jinja switch for the prompt and the run
# metadata recorded in the trajectory and in /artifacts/probe.txt.
#
# USAGE (venv active, Docker running, OPENROUTER_API_KEY already configured):
#   scripts/run_test.sh <instance_id> [step_limit] [cost_limit]
#   e.g. CONDITION=guided scripts/run_test.sh sympy__sympy-12096
# Env overrides: CONFIG (agent yaml, defaults to swebench_pr_compliance.yaml at
# repo root), RUNS_ROOT (defaults to ../../../runs), MODEL, MAX_ATTEMPTS (default 3),
# CONDITION (default naive), FRAMEWORK (default mini-swe-agent), MODEL_SLUG (default:
# the last segment of MODEL), RULES_FILE (guided only), REPO_SLUG, RULES_DIR,
# START_ATTEMPT (default 1)
set -euo pipefail

instance="${1:?usage: run_test.sh <instance_id> [step_limit] [cost_limit]}"

# 0 disables the check (agents/default.py guards with `0 < step_limit`). Removed
# 27 Aug 2026, for the same reason the cost limit went: a run that hits the limit exits
# `LimitsExceeded` and submits NOTHING, so the whole run is lost rather than truncated --
# and because the loss leaves no `patch.diff`, every resume retries it and hits the same
# wall, forever.
#
# **This default silently overrode the config for two days.** The agent yaml said
# `step_limit: 0`, but this line passes `-c agent.step_limit=...` on every invocation, and
# a `-c` override beats the file. 3 of 604 runs in the sympy sweep died at exactly 250
# calls before it was spotted. If a runaway guard is ever wanted, put it in ONE place and
# make it auto-submit (config/benchmarks/programbench.yaml shows how), rather than in two
# places where the quieter one wins.
step_limit="${2:-0}"
# 0 disables the check (agents/default.py guards with `0 < cost_limit`). Removed
# 25 Aug 2026: a run that hits the limit submits NOTHING, then gets retried, so the
# limit converts an expensive run into three expensive runs and no data.
# The config sets it too; this is the
# positional-argument default, and both had to change.
cost_limit="${3:-0}"

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
config="${CONFIG:-$here/../swebench_pr_compliance.yaml}"
# Run data lives in the SWE-CC repository (runs/), not in this checkout. One directory per attempt:
#   runs/<repo>/<framework>/<model>/<instance>/<condition>/attemptN/
# See compliance/core/paths.py, which is the single source of truth for the layout.
#
# The (framework, model) cell is part of the path because it is part of a run's
# identity. Without it, four models scoring one instance under one condition land in one
# directory separated only by the attempt counter -- which reads as one run retried four
# times, and merges in every aggregate that groups by run.
runs_root="${RUNS_ROOT:-$here/../../../runs}"
model="${MODEL:-openrouter/google/gemini-2.5-flash}"

# Which scaffold is producing the run. Names frameworks/<slug>.conf in the SWE-CC repository,
# which in turn names the adapter that can read this trajectory format.
framework="${FRAMEWORK:-mini-swe-agent}"

# Directory-safe name for the model: the last segment of the litellm id, which is what
# models/<slug>.conf is named after. The full id still goes into the probe, so a run
# records exactly what it ran against and the slug is only ever a filing decision.
model_slug="${MODEL_SLUG:-${model##*/}}"
# Everything model-specific comes from models/<slug>.conf in the SWE-CC repository, the same
# way repo-specific settings come from rules/<slug>/repo.conf. Optional: a model with no
# conf still runs, it just gets no provider pin.
models_dir="${MODELS_DIR:-$here/../../../models}"

# Sourcing a conf OVERWRITES anything already in the environment, so an explicit
# `REASONING_EFFORT=... scripts/run_test.sh ...` would be silently ignored -- which
# invalidated a control run that appeared to work. Environment wins over file, matching
# how REPO_SLUG and RULES_DIR already behave. The sentinel distinguishes "set to empty
# on purpose" (a deliberate override, disabling the setting) from "not set at all".
_env_reasoning="${REASONING_EFFORT-__UNSET__}"
if [ -f "$models_dir/${model_slug}.conf" ]; then
  # shellcheck disable=SC1091
  . "$models_dir/${model_slug}.conf"
fi
if [ "$_env_reasoning" != "__UNSET__" ]; then
  REASONING_EFFORT="$_env_reasoning"
fi

# --- routing vs reporting -------------------------------------------------------------
# `$model` was used for BOTH what litellm dials and what the corpus is keyed on. Those
# stopped being the same thing on 4 Sep 2026, when gemini-3.7-flash moved off OpenRouter
# to Google's own API -- its OpenRouter key has a hard spend cap it had already exhausted,
# while the Gemini key carries its own budget. The OpenHands harness splits them the same
# way; this is that change here.
#
#   RUN_ROUTE  what litellm dials      gemini/gemini-3.7-flash
#   RUN_LABEL  what reports group by   openrouter/google/gemini-3.7-flash
#
# THE LABEL MUST NOT FOLLOW THE REROUTE. `compliance report` groups by the recorded
# litellm id, and 828+ stored gemini runs carry the OpenRouter string. Letting routing
# reach the label would split one model into two in every aggregate -- the
# `!! POOLING 2 CELLS` shape, a key that is not unique, losing data quietly.
#
# The run DIRECTORY is unaffected either way: `model_slug` is `${model##*/}`, which is
# `gemini-3.7-flash` under both ids.
#
# litellm resolves the key from the environment by provider prefix (GEMINI_API_KEY for
# `gemini/...`, OPENROUTER_API_KEY for `openrouter/...`), so no key is passed explicitly.
# Both variables default to `$model`, so a model that has not been rerouted is unchanged
# and needs no conf entry.
RUN_ROUTE="${LITELLM_ID:-$model}"
RUN_LABEL="${CANONICAL_ID:-$RUN_ROUTE}"
RUN_KEY_ENV="${API_KEY_ENV:-OPENROUTER_API_KEY}"

# Vertex AI needs its project and location in the CHILD's environment. Sourcing a conf
# only sets shell variables; litellm runs in a subprocess and reads them from the env.
# Auth is Application Default Credentials, so no API key is passed for this route.
if [ -n "${VERTEXAI_PROJECT:-}" ]; then
  export VERTEXAI_PROJECT VERTEXAI_LOCATION
  echo "   vertex: project=$VERTEXAI_PROJECT location=${VERTEXAI_LOCATION:-global} (ADC auth)"
fi


# Fail here rather than 25 minutes into an agent run. A missing or exhausted key surfaces
# mid-run as a litellm APIError that reads like a network fault -- that is how a capped
# key cost an hour of misdiagnosis on 3 Sep 2026.
if [ -z "$(eval "printf '%s' \"\${$RUN_KEY_ENV:-}\"")" ]; then
  echo "!! $RUN_KEY_ENV is not set, and $model routes through it" >&2; exit 2
fi
[ "$RUN_ROUTE" != "$RUN_LABEL" ] && \
  echo "   route: $RUN_ROUTE via \$$RUN_KEY_ENV  (reported as $RUN_LABEL)"

# Reasoning effort, when a model's conf sets one. Only Kimi K2.5 does, by explicit
# choice -- which means its runs carry a setting the other three do not, and any
# difference in its results is a statement about (model + effort), not the model alone.
# NOTE: expanded below as ${arr[@]+"${arr[@]}"}, not "${arr[@]}". macOS ships bash 3.2,
# where expanding an EMPTY array under `set -u` is an unbound-variable error -- it killed
# six runs instantly, and only the one model that sets REASONING_EFFORT survived, because
# its array was non-empty. Do not "simplify" it back.
# Prompt caching OFF for the Vertex route ONLY. The config sets `model.set_cache_control:
# default_end` for every model (a billing change -- see swebench_pr_compliance.yaml). On
# OpenRouter and Anthropic those markers are harmless, but litellm turns them into a Vertex
# `cachedContent` request, and Vertex then rejects the call:
#
#   400 Tool config, tools and system instruction should not be set in the request
#       when using cached content.
#
# It only fires once the cached prefix crosses Vertex's minimum-cache token threshold, so
# it is instance-specific and deterministic rather than random: 2 of 372 gemini cells
# (pytest-dev__pytest-7490, both arms) died at step 3 on every attempt, while the other 370
# never crossed the threshold and ran clean.
#
# SCOPE: this touches `vertex_ai/` routes only. OpenRouter, Anthropic, GPT, DeepSeek, Kimi
# and Qwen keep caching exactly as before -- the guard is the route prefix, not the model.
# Safe for the aggregate: caching is explicitly NOT a stage boundary (a cache hit requires
# a byte-identical prefix, so the model reads the same tokens either way), so cached and
# uncached runs stay poolable. The cost is a higher bill on this one route, not a fork in
# the experiment.
cache_args=()
case "$RUN_ROUTE" in
  vertex_ai/*)
    cache_args=(-c "model.set_cache_control=null")
    echo "   vertex: prompt caching disabled (Vertex rejects cachedContent alongside tools)"
    ;;
esac

reasoning_args=()
if [ -n "${REASONING_EFFORT:-}" ]; then
  reasoning_args=(-c "model.model_kwargs.reasoning={\"effort\":\"${REASONING_EFFORT}\"}")
  echo "   reasoning effort -> ${REASONING_EFFORT}"
fi

# Deliberately NOT pinning the upstream provider. OpenRouter load-balances per request,
# so a run can be served by several providers at different quantizations (fp4/fp8) and
# context windows (64k-164k observed for one model). That variation is accepted rather
# than controlled -- pinning with allow_fallbacks=false turns a provider outage into a
# failed run, and across 8,000 runs that trade was judged not worth it.
#
# It is recorded rather than ignored: every call stores its serving provider in the
# trajectory, and the per-run mix can be read back from it, so
# a result can always be checked against what actually served it.
#
# Caching does not depend on this. Measured: a provider switch costs ONE cold call, not
# the cache -- an unpinned qwen run still cached 96% across two providers.

manifest="results/instance_map.json"
max_attempts="${MAX_ATTEMPTS:-3}"
condition="${CONDITION:-naive}"

case "$condition" in
  none|naive|guided) ;;
  naive-salient)
    # Retired 25 Aug 2026. It answered its question -- moving the retrieval sentence to the
    # top changed nothing, retrieval still failed 5/5 -- and it is a variant of the control,
    # not a third arm, and is not part of the released study.
    # Set ALLOW_RETIRED=1 to run it anyway.
    if [ "${ALLOW_RETIRED:-0}" != "1" ]; then
      echo "!! CONDITION=naive-salient is retired and not part of the released study" >&2
      echo "   re-run it deliberately with ALLOW_RETIRED=1 if that is what you want" >&2
      exit 2
    fi
    ;;
  *) echo "!! CONDITION must be one of none|naive|guided (got '$condition')" >&2; exit 2 ;;
esac

# Everything repo-specific comes from rules/<slug>/repo.conf, keyed off the SWE-bench
# instance prefix (sympy__sympy-11618 -> sympy, django__django-11099 -> django). No
# repository is named anywhere in this script or in the agent config.
repo_slug="${REPO_SLUG:-${instance%%__*}}"

# --- resume: a completed run is never redone --------------------------------------
# A sweep of thousands of runs WILL be interrupted -- a laptop sleeps, a key expires, a
# provider 500s. Re-running the same command must continue rather than restart, so a run
# that already produced a trajectory is skipped and the batch moves on.
#
# `patch.diff` is the completion marker, NOT `trajectory.json`. The trajectory is written
# while the agent is still inside the container, so a cell killed during collection leaves
# one behind and would be skipped forever as "done" while carrying no patch, no bundle and
# no eval report. `patch.diff` is written by collect, after the agent has genuinely
# finished. Learned from a cell that hung on a runaway `print()` loop.
# FORCE=1 overrides, for deliberately re-running a cell.
resume_dir="${runs_root}/${repo_slug}/${framework}/${model_slug}/${instance}/${condition}/attempt${START_ATTEMPT:-1}"
if [ "${FORCE:-0}" != "1" ] && [ -f "$resume_dir/patch.diff" ]; then
  echo "== SKIP $instance ($condition, ${model_slug}) -- already done: $resume_dir"
  exit 0
fi

repo_dir="${RULES_DIR:-$here/../../../rules}/${repo_slug}"
if [ -f "$repo_dir/repo.conf" ]; then
  # shellcheck disable=SC1091
  . "$repo_dir/repo.conf"
elif [ "$condition" != "none" ]; then
  echo "!! no $repo_dir/repo.conf; condition '$condition' needs one (see rules/sympy/repo.conf)" >&2
  exit 2
fi
# --- the repo cache: preparation, not scoring ---------------------------------------
# Compliance scoring reconstructs post-patch file contents from `base_commit` + patch,
# reading base blobs out of a blobless clone at .cache/repos/<slug>. WITHOUT IT every rule
# that reads a file body withholds -- correctly, per invariant 6, and invisibly: the report
# still prints a coherent table, five points low. That cost one real batch.
#
# It is created HERE, in the run path, and not in the checker, because `git clone` is
# network I/O and compliance scoring is pure and offline by design -- that property is
# what makes re-scoring free and reproducible, and it is worth more than the convenience
# of self-repair. The run harness is already impure (Docker, the model API), so this is
# the natural place: any run that gets collected has its cache by construction.
#
# Cheap when present: ensure_clone returns immediately if the clone exists.
if [ -n "${REPO_URL:-}" ] && [ "${SKIP_REPO_CACHE:-0}" != "1" ]; then
  cache_root="${REPO_CACHE_ROOT:-$here/../../../.cache/repos}"
  # Mirrors ensure_clone's own test: `--no-checkout` still produces a normal repo with a
  # .git directory, so a top-level HEAD only exists for a bare clone. Checking one shape
  # only made this run a python process on every single run to be told "already there".
  if [ ! -e "$cache_root/$repo_slug/.git" ] && [ ! -e "$cache_root/$repo_slug/HEAD" ]; then
    # Atomic lock: with several runs launched in parallel the first one clones and the
    # others wait, rather than four `git clone` processes writing one directory.
    lock="$cache_root/.$repo_slug.lock"
    mkdir -p "$cache_root"
    if mkdir "$lock" 2>/dev/null; then
      trap 'rmdir "$lock" 2>/dev/null || true' EXIT
      echo "== caching $repo_slug for patch reconstruction (one-off)"
      python -c "import sys; sys.path.insert(0, '$here/../../..');
from compliance.bundle.reconstruct import ensure_clone; ensure_clone('$repo_slug')" \
        || echo "!! could not cache $repo_slug; file-body rules will withhold" >&2
      rmdir "$lock" 2>/dev/null || true
      trap - EXIT
    else
      while [ -d "$lock" ]; do sleep 2; done
    fi
  fi
fi

rules_file="${RULES_FILE:-$repo_dir/CONTRIBUTING_RULES.md}"
docs_url="${DOCS_URL:-}"

case "$condition" in naive|naive-salient) needs_docs=1 ;; *) needs_docs=0 ;; esac
if [ "$needs_docs" = "1" ] && [ -z "$docs_url" ]; then
  echo "!! CONDITION=naive needs DOCS_URL set in $repo_dir/repo.conf" >&2
  exit 2
fi

if [ "$condition" = "guided" ]; then
  # The mounted rules file is the entire treatment; a missing one would silently
  # degrade the guided arm into a no-guidelines control.
  [ -f "$rules_file" ] || { echo "!! CONDITION=guided needs RULES_FILE; '$rules_file' does not exist" >&2; exit 2; }
  rules_file="$(cd "$(dirname "$rules_file")" && pwd)/$(basename "$rules_file")"
  # Kept even though the network is now on: pulling mid-run costs time and makes the
  # environment differ between the first and later attempts.
  image="docker.io/swebench/sweb.eval.x86_64.$(echo "$instance" | sed 's/__/_1776_/'):latest"
  image="$(echo "$image" | tr '[:upper:]' '[:lower:]')"
  docker image inspect "$image" >/dev/null 2>&1 \
    || { echo "!! CONDITION=guided but image $image is not cached locally; run scripts/cache_images.sh first" >&2; exit 2; }
fi

export MSWEA_COST_TRACKING=ignore_errors

mkdir -p "$runs_root" results

# START_ATTEMPT lets a re-run sit beside an earlier one instead of overwriting it --
# needed when the treatment itself changed (e.g. the rules file is now delivered whole),
# because the earlier runs are evidence for the change, not a failed try.
attempt="${START_ATTEMPT:-1}"
patch_len=0
last_attempt=$(( attempt + max_attempts - 1 ))
while [ "$attempt" -le "$last_attempt" ]; do
  run_dir="${runs_root}/${repo_slug}/${framework}/${model_slug}/${instance}/${condition}/attempt${attempt}"
  mkdir -p "$run_dir"

  # Everything this attempt prints is also kept beside the run itself, so a run's console
  # output is filed by the same (repo, framework, model, instance, condition, attempt) key
  # as its data and cannot be confused with another run's. Written per attempt, so a
  # retry does not append to the attempt it replaced.
  #
  # This is what makes concurrency safe to read afterwards: with several runs interleaved
  # on one terminal, the only trustworthy record of what a given run did is the one
  # sitting in its own directory.
  exec > >(tee "$run_dir/run.log") 2>&1
  traj_path="${run_dir}/trajectory.json"
  artifact_dir="$run_dir"

  # run_args must be built here: the config loader does no ${VAR} expansion, so a
  # host path can only reach it through a command-line override.
  run_args="[\"--rm\",\"-v\",\"${artifact_dir}:/artifacts\""
  if [ "$condition" = "guided" ]; then
    # Network stays ON for guided as of 25 Aug 2026 (design decision).
    #
    # It was `--network none`, to make the mounted file the only possible source of the
    # guidelines. That worked, and bought a confound: a rule about installing a tool the
    # container lacks -- `ruff` is absent from every image -- was unanswerable for guided and
    # answerable for naive, so any such rule penalised the treatment arm for the sandbox
    # rather than for its behaviour. Two naive runs installed `pytest` unprompted; no guided
    # run could have.
    #
    # The treatment is the mounted file, not the absence of a network, and it is still
    # mounted. Guided runs from here are therefore NOT comparable to attempts 1-2 of the
    # pilot, which had no network.
    run_args="${run_args},\"-v\",\"${rules_file}:/rules/CONTRIBUTING_RULES.md:ro\""
  fi
  run_args="${run_args}]"

  echo "== running $instance (condition=${condition}, attempt ${attempt}/${max_attempts}) =="
  echo "   artifacts -> ${artifact_dir}"
  mini-extra swebench-single \
    --subset verified --split test \
    -i "$instance" \
    -m "$RUN_ROUTE" \
    -c "$config" \
    -c "agent.step_limit=${step_limit}" \
    -c "environment.run_args=${run_args}" \
    -c "environment.env.RUN_CONDITION=\"${condition}\"" \
    ${reasoning_args[@]+"${reasoning_args[@]}"} \
    ${cache_args[@]+"${cache_args[@]}"} \
    -c "environment.env.RUN_MODEL=\"${RUN_LABEL}\"" \
    -c "environment.env.RUN_ROUTE=\"${RUN_ROUTE}\"" \
    -c "environment.env.RUN_REASONING=\"${REASONING_EFFORT:-default}\"" \
    -c "environment.env.RUN_FRAMEWORK=\"${framework}\"" \
    -c "environment.env.RUN_ATTEMPT=\"${attempt}\"" \
    -c "environment.env.RUN_DOCS_URL=\"${docs_url}\"" \
    --cost-limit "$cost_limit" \
    -y --exit-immediately \
    -o "$traj_path"

  # info.submission is now the whole evidence bundle, so it is non-empty even when the
  # patch is not. Grade-ability is decided by the ===PATCH=== section alone.
  patch_len="$(python - "$traj_path" <<'PY'
import json, sys
s = json.load(open(sys.argv[1]))["info"].get("submission") or ""
print(len(s.split("===PATCH===", 1)[1].strip()) if "===PATCH===" in s else len(s.strip()))
PY
)"
  if [ "$patch_len" -gt 0 ]; then
    echo "  attempt ${attempt} captured a ${patch_len}-char patch"
    break
  fi
  exit_status="$(python -c "import json; print(json.load(open('${traj_path}'))['info'].get('exit_status'))")"
  echo "  attempt ${attempt} produced an EMPTY patch (exit_status=${exit_status}) -- ${traj_path} and ${artifact_dir} kept for inspection" >&2
  attempt=$((attempt + 1))
done

if [ "$patch_len" -gt 0 ]; then
  echo "  run stored at ${run_dir}"
else
  echo "!! all ${max_attempts} attempts for $instance produced an empty patch -- kept under" >&2
  echo "!! ${runs_root}/${repo_slug}/${instance}/${condition}/ ; registering the last one anyway" >&2
fi

# Split the bundle into named files beside the trajectory, so a run is inspectable
# without a JSON parser and archivable as a unit.
python - "$traj_path" "$run_dir" <<'PY' || true
import json, re, sys
from pathlib import Path
traj_path, run_dir = Path(sys.argv[1]), Path(sys.argv[2])
sub = (json.loads(traj_path.read_text()).get("info") or {}).get("submission") or ""
marks = list(re.finditer(r"^===([A-Z_]+)===$", sub, re.M))
names = {"PROBE": "probe.txt", "PATCH": "patch.diff", "PATCH_COMMITTED": "patch_committed.diff"}
if marks:
    (run_dir / "bundle.txt").write_text(sub)
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(sub)
        if name := names.get(m.group(1)):
            (run_dir / name).write_text(sub[m.end():end].strip("\n") + "\n")
elif sub:
    (run_dir / "patch.diff").write_text(sub)
PY

# results/instance_map.json is a read-modify-write on a SHARED, instance-keyed file,
# so concurrent runs corrupt it and the loser dies with `JSONDecodeError: Extra data`
# -- AFTER the agent has finished and the patch is already on disk. That is the worst
# place to fail: the expensive work is done, the cell counts as complete because
# `patch.diff` exists, and grading never runs.
#
# Legacy: nothing about grading or scoring reads it. Guarded by the same SKIP_SUMMARY
# as the other instance-keyed writers, which run_batch.sh and run_sweep.sh both set.
# Cost of having missed it: the django sweep went from a 0% to a 100% failure rate
# within two progress windows, once enough cells overlapped.
if [ "${SKIP_SUMMARY:-0}" != "1" ]; then
  echo "== registering trajectory =="
  python - "$manifest" "$instance" "$traj_path" <<'PY'
import json, os, sys
manifest, instance, traj_path = sys.argv[1:4]
data = json.load(open(manifest)) if os.path.exists(manifest) else {}
data[instance] = traj_path
json.dump(data, open(manifest, "w"), indent=2)
print(f"  {instance} -> {traj_path}")
PY
fi

# --- legacy, instance-keyed bookkeeping -------------------------------------------
# `cases.txt`, `results/instance_map.json` and `results/summary.json` are all keyed by
# instance alone, so they cannot represent the same instance under two conditions or two
# models, and every one of them is a read-modify-write on a shared path. Nothing about
# grading depends on them -- the trajectory, patch, probe and eval_report all live in
# $run_dir, which is unique per run.
#
# SKIP_SUMMARY=1 turns them off. Required when running batches in PARALLEL: concurrent
# json.load/json.dump on one file corrupts it, and a run would then fail *after* its real
# data was already safely on disk, which is the worst place to fail.
if [ "${SKIP_SUMMARY:-0}" != "1" ]; then
  grep -qxF "$instance" cases.txt 2>/dev/null || echo "$instance" >> cases.txt
fi

echo "== grading =="
"$here/evaluate.sh" "$instance" "$run_dir"

if [ "${SKIP_SUMMARY:-0}" = "1" ]; then
  echo "== skipping legacy summary (SKIP_SUMMARY=1) =="
  echo "$instance: run complete -> $run_dir"
  exit 0
fi

echo "== rendering trajectory =="
python "$here/render_trajectory.py" "$instance"

echo "== updating summary =="
python "$here/collect_results.py"

python - "$instance" <<'PY'
import json, sys
inst = sys.argv[1]
rows = json.load(open("results/summary.json"))
r = next(row for row in rows if row["instance_id"] == inst)
verdict = "RESOLVED" if r["resolved"] else ("not resolved" if r["graded"] else "ungraded")
print(f"\n{inst}: {verdict}  (steps={r['steps']}, cost=${r['cost_usd']})")
if r["fail_to_pass_failures"]:
    print("  FAIL_TO_PASS still failing:", ", ".join(r["fail_to_pass_failures"]))
if r["pass_to_pass_failures"]:
    print("  PASS_TO_PASS regressions:", ", ".join(r["pass_to_pass_failures"]))
PY

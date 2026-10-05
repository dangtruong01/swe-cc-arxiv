#!/usr/bin/env bash
# The evidence bundle: what the agent proposed, what it did, and the environment both
# happened in. Emitted on stdout AND to /artifacts/collect.txt, so a run whose submission
# is lost is still recoverable from the host bind mount.
#
# SHARED BY EVERY FRAMEWORK. The `===SECTION===` delimiters are ours, not any scaffold's,
# and the whole point of this file is that two frameworks produce byte-comparable bundles.
# `tests/test_harness_scripts.py` asserts the emit() body below still matches the copy
# embedded in mini-swe-agent's agent config; if they drift, runs from the two frameworks
# stop being comparable and nothing fails to say so.
#
# Always exits 0 so a submit sentinel is honoured.
#
# COLLECT_REPO_DIR is where the agent actually worked, and it is NOT the same everywhere:
# mini-swe-agent works in /testbed, while OpenHands copies /testbed to /workspace/<repo>
# and works there. Defaulting to /testbed and diffing the wrong directory would produce a
# clean, plausible, EMPTY patch for every run -- a total data loss that looks like an
# agent that changed nothing.
REPO_DIR="${COLLECT_REPO_DIR:-/testbed}"
# Must match the probe's HARNESS_DIR: that is where run_meta.sh and probe.txt were left,
# and an unreadable run_meta means an empty START_HEAD, which means an empty patch.
HARNESS_DIR="${HARNESS_DIR:-/opt}"
cd "$REPO_DIR" 2>/dev/null || true
START_HEAD=""
BASE_COMMIT=""
INSTANCE_ID=""
[ -f "$HARNESS_DIR/run_meta.sh" ] && . "$HARNESS_DIR/run_meta.sh"
# Three independent sources, because an empty START_HEAD would silently produce an
# empty patch -- the exact failure mode this script exists to eliminate.
START_HEAD_SOURCE=run_meta
if [ -z "$START_HEAD" ]; then
  START_HEAD="$BASE_COMMIT"; START_HEAD_SOURCE=run_meta_base_commit
fi
if [ -z "$START_HEAD" ]; then
  START_HEAD="$(sed -n 's/^start_head=//p' $HARNESS_DIR/probe.txt 2>/dev/null | head -1)"; START_HEAD_SOURCE=probe_start_head
fi
if [ -z "$START_HEAD" ]; then
  START_HEAD="$(sed -n 's/^base_commit=//p' $HARNESS_DIR/probe.txt 2>/dev/null | head -1)"; START_HEAD_SOURCE=probe_base_commit
fi
if [ -z "$START_HEAD" ]; then
  START_HEAD=HEAD; START_HEAD_SOURCE=fallback_head_uncommitted_only
fi

emit() {
  echo "===PROBE==="
  cat $HARNESS_DIR/probe.txt 2>/dev/null
  echo "===BRANCH==="
  echo "instance_id=${INSTANCE_ID}"
  echo "start_head=${START_HEAD}"
  echo "start_head_source=${START_HEAD_SOURCE}"
  echo "head=$(git rev-parse HEAD 2>/dev/null)"
  echo "branch=$(git branch --show-current 2>/dev/null || echo '(detached)')"
  echo "n_commits=$(git rev-list --count "${START_HEAD}..HEAD" 2>/dev/null || echo 0)"
  echo "===LOG==="
  git log --pretty=raw --stat "${START_HEAD}..HEAD" 2>/dev/null
  echo "===STATUS==="
  git status --porcelain=v1 2>/dev/null
  # What the agent PROPOSED: committed work only. Compliance scores this, because
  # deciding what belongs in a contribution is itself a graded behaviour.
  echo "===PATCH_COMMITTED==="
  git diff "${START_HEAD}..HEAD" 2>/dev/null
  # What the agent DID: committed work plus anything left in the tree. SWE-bench
  # grades this, so a forgotten commit is not scored as a failed fix. Must stay the
  # last section -- everything after the marker is taken as patch bytes.
  echo "===PATCH==="
  git add -A -- . ':(exclude)patch.txt' ':(exclude)*.orig' ':(exclude)*.rej' >/dev/null 2>&1 || git add -A >/dev/null 2>&1
  git diff "${START_HEAD}" 2>/dev/null
}

# Build once, then fan out -- never run emit twice (git add -A is not free of effect).
emit > /tmp/collect.txt 2>/dev/null
cp /tmp/collect.txt /artifacts/collect.txt 2>/dev/null || true
# Also beside the harness itself. /artifacts is a bind mount the other framework has and
# this one does not, and a bundle only on stdout is lost if the agent pipes it through
# `head` -- which one did, while trying to work out why the output looked empty.
cp /tmp/collect.txt "$HARNESS_DIR/collect.txt" 2>/dev/null || true
cat /tmp/collect.txt
exit 0

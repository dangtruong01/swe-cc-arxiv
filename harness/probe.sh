#!/usr/bin/env bash
# The startup probe: what the environment actually was, recorded before the agent runs.
#
# SHARED BY EVERY FRAMEWORK, and the reason it exists is auditability -- a run whose
# environment is not recorded cannot be checked afterwards, and the container is destroyed
# the moment the run ends. `rules_file_sha256` and `rules_file_chars` are what prove the
# guided arm received its treatment whole; `network_tcp` and `network_docs` are what prove
# the naive arm could have reached the docs it was pointed at. Without those, "the agent
# never fetched the guidelines" and "the guidelines were unreachable" are the same
# observation.
#
# mini-swe-agent carries its own copy inside swebench_pr_compliance.yaml, where the values
# come from jinja. This one takes them from the environment instead, so a framework with
# no template engine in its startup path can produce the identical key set.
# `tests/test_harness_scripts.py` asserts the two agree on which keys those are.
#
# Inputs, all optional -- an absent one is recorded as empty rather than failing, because
# a partial probe is still evidence and a failed startup is not:
#   PROBE_REPO_DIR    where the agent will work        (default /testbed)
#   PROBE_INSTANCE_ID PROBE_BASE_COMMIT PROBE_CREATED_AT
#   RUN_CONDITION RUN_MODEL RUN_FRAMEWORK RUN_REASONING RUN_ATTEMPT RUN_DOCS_URL
set -u

REPO_DIR="${PROBE_REPO_DIR:-/testbed}"
RULES_PATH="${PROBE_RULES_PATH:-/rules/CONTRIBUTING_RULES.md}"
# Where this run's own files live. NOT the same everywhere: mini-swe-agent runs as root
# and /opt is writable; OpenHands' agent-server runs as `USER openhands`, for which /opt
# is root-owned and every write there fails.
HARNESS_DIR="${HARNESS_DIR:-/opt}"
OUT="${PROBE_OUT:-$HARNESS_DIR/probe.txt}"

mkdir -p /artifacts "$HARNESS_DIR" 2>/dev/null || true
cd "$REPO_DIR" 2>/dev/null || true

PY=python3; command -v python3 >/dev/null 2>&1 || PY=python
TO="timeout 10"; command -v timeout >/dev/null 2>&1 || TO=""
CONDITION="${RUN_CONDITION:-none}"

# --- hook state, captured BEFORE we disable hooks ---------------------------------
HOOKS_DIR="$(git rev-parse --git-path hooks 2>/dev/null || true)"
HOOKS_INSTALLED=0
if [ -n "$HOOKS_DIR" ] && [ -d "$HOOKS_DIR" ]; then
  HOOKS_INSTALLED="$(find "$HOOKS_DIR" -maxdepth 1 -type f ! -name '*.sample' -perm -u+x 2>/dev/null | wc -l | tr -d ' ')"
fi
REPO_HOOKS_PATH="$(git config --local --get core.hooksPath 2>/dev/null || true)"
HOOK_CONFIG_PRESENT=no
[ -f "$REPO_DIR/.pre-commit-config.yaml" ] && HOOK_CONFIG_PRESENT=yes
PRECOMMIT_ON_PATH="$(command -v pre-commit 2>/dev/null || echo missing)"

# --- git identity + hooks off ------------------------------------------------------
# A working identity is what makes a real commit possible, and commit authorship is
# itself graded. Hooks are disabled so a repository's own pre-commit hook cannot make
# the agent look compliant for reasons the agent had nothing to do with.
git config --global user.name "${GIT_AUTHOR_NAME:-mini-swe-agent-bot}"
git config --global user.email "${GIT_AUTHOR_EMAIL:-mini-swe-agent-bot@example.com}"
git config --global core.hooksPath /dev/null

# --- tooling availability ----------------------------------------------------------
TOOL_RUFF="$(command -v ruff 2>/dev/null || echo missing)"
TOOL_FLAKE8="$(command -v flake8 2>/dev/null || echo missing)"
TOOL_BLACK="$(command -v black 2>/dev/null || echo missing)"
TOOL_ISORT="$(command -v isort 2>/dev/null || echo missing)"
TOOL_PYTEST="$(command -v pytest 2>/dev/null || echo missing)"

# --- network reachability ----------------------------------------------------------
# Two independent signals. NET_TCP names no repository and no DNS: it answers
# "is there any outbound network at all", which is what the guided arm must rule
# out. NET_DOCS answers "can the agent actually reach this repo's guidelines",
# which is the naive arm's precondition.
NET_TCP=unreachable
$TO "$PY" -c "import socket; socket.setdefaulttimeout(5); socket.create_connection(('1.1.1.1', 443)).close()" >/dev/null 2>&1 && NET_TCP=ok
NET_DOCS=skipped
if [ -n "${RUN_DOCS_URL:-}" ]; then
  NET_DOCS=unreachable
  $TO "$PY" -c "import os, urllib.request as u; u.urlopen(os.environ['RUN_DOCS_URL'], timeout=8).read(1)" >/dev/null 2>&1 && NET_DOCS=ok
fi

# --- guided-condition rules file ---------------------------------------------------
# The sha and the char count are the treatment's receipt. A guided run whose
# rules_file_chars does not match the file on the host received a different treatment
# from the one we think we administered.
RULES_PRESENT=no
RULES_SHA256=
RULES_CHARS=0
RULES_LINES=0
if [ -f "$RULES_PATH" ]; then
  RULES_PRESENT=yes
  RULES_SHA256="$(sha256sum "$RULES_PATH" 2>/dev/null | cut -d' ' -f1)"
  RULES_CHARS="$(wc -c < "$RULES_PATH" 2>/dev/null | tr -d ' ')"
  RULES_LINES="$(wc -l < "$RULES_PATH" 2>/dev/null | tr -d ' ')"
fi

START_HEAD="$(git rev-parse HEAD 2>/dev/null || true)"
START_BRANCH="$(git branch --show-current 2>/dev/null || true)"
[ -n "$START_BRANCH" ] || START_BRANCH="(detached)"

BASE_COMMIT="${PROBE_BASE_COMMIT:-}"

cat > "$OUT" <<EOF
probe_version=1
instance_id=${PROBE_INSTANCE_ID:-}
base_commit=${BASE_COMMIT}
base_commit_date=$(git show -s --format=%cI "${BASE_COMMIT}" 2>/dev/null || true)
dataset_created_at=${PROBE_CREATED_AT:-}
condition=${CONDITION}
model=${RUN_MODEL:-unknown}
framework=${RUN_FRAMEWORK:-unknown}
reasoning=${RUN_REASONING:-default}
attempt_n=${RUN_ATTEMPT:-1}
start_head=${START_HEAD}
start_branch=${START_BRANCH}
hooks_installed=${HOOKS_INSTALLED}
hooks_path=$(git config --get core.hooksPath 2>/dev/null || true)
repo_hooks_path=${REPO_HOOKS_PATH}
hook_config_present=${HOOK_CONFIG_PRESENT}
precommit_on_path=${PRECOMMIT_ON_PATH}
tool_ruff=${TOOL_RUFF}
tool_flake8=${TOOL_FLAKE8}
tool_black=${TOOL_BLACK}
tool_isort=${TOOL_ISORT}
tool_pytest=${TOOL_PYTEST}
network_tcp=${NET_TCP}
network_docs=${NET_DOCS}
docs_url=${RUN_DOCS_URL:-}
rules_file_present=${RULES_PRESENT}
rules_file_sha256=${RULES_SHA256}
rules_file_chars=${RULES_CHARS}
rules_file_lines=${RULES_LINES}
rules_file_path=${RULES_PATH}
git_user_name=$(git config --get user.name 2>/dev/null || true)
git_user_email=$(git config --get user.email 2>/dev/null || true)
python_version=$("$PY" -c "import sys; print(sys.version.split()[0])" 2>/dev/null || true)
git_version=$(git --version 2>/dev/null | awk '{print $3}')
EOF
cp "$OUT" /artifacts/probe.txt 2>/dev/null || true

# Baked-in values for collect.sh, which runs later with a quoted heredoc body and so
# cannot see anything from this shell.
cat > "$HARNESS_DIR/run_meta.sh" <<EOF
START_HEAD=${START_HEAD}
BASE_COMMIT=${BASE_COMMIT}
INSTANCE_ID=${PROBE_INSTANCE_ID:-}
EOF

cat "$OUT"
exit 0

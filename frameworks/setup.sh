#!/usr/bin/env bash
# Fetch both agent scaffolds at the commits the paper used, and apply our changes.
#
#   frameworks/setup.sh [mini-swe-agent|openhands|all]
#
# Functional grading (the SWE-bench harness) is installed with mini-swe-agent and is used
# for both scaffolds, so an OpenHands sweep needs `all`. OpenHands needs `uv` on PATH.
#
# We do not redistribute the scaffolds. Each is cloned from upstream at a pinned commit;
# our modifications (task prompt, run/collect/grade scripts, two small fixes) are copied
# or patched on top. Nothing else in either scaffold is changed.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
which="${1:-all}"

MSA_REPO="https://github.com/SWE-agent/mini-swe-agent.git"
MSA_PIN="40fa36522015a6bc6cf14411382b662b42083bf1"
source "$root/frameworks/openhands.conf"   # SOURCE, PIN_BENCHMARKS, PIN_SDK

if [[ "$which" == all || "$which" == mini-swe-agent ]]; then
  dest="$root/mini-swe-agent-run/mini-swe-agent"
  if [ ! -d "$dest/.git" ]; then
    git clone "$MSA_REPO" "$dest"
  fi
  git -C "$dest" checkout -q "$MSA_PIN"
  cp -R "$root/frameworks/mini-swe-agent/overlay/." "$dest/"
  # Its own venv: the agent, and the SWE-bench harness that grades BOTH scaffolds' runs
  # (tools/regrade.py and the inline grade call scripts/evaluate.sh from here).
  python3.11 -m venv "$dest/.venv"
  "$dest/.venv/bin/pip" install -q -e "$dest" "litellm==1.100.0" "swebench==4.1.0"
  echo "mini-swe-agent ready at $dest"
fi

if [[ "$which" == all || "$which" == openhands ]]; then
  dest="$root/openhands-run/benchmarks"
  if [ ! -d "$dest/.git" ]; then
    git clone "$SOURCE" "$dest"
  fi
  git -C "$dest" checkout -q "$PIN_BENCHMARKS"
  git -C "$dest" submodule update --init vendor/software-agent-sdk
  git -C "$dest/vendor/software-agent-sdk" checkout -q "$PIN_SDK"
  git -C "$dest" apply "$root/frameworks/openhands/patches/benchmarks-image-utils.patch"
  git -C "$dest/vendor/software-agent-sdk" apply "$root/frameworks/openhands/patches/sdk-file-editor-limit.patch"
  (cd "$dest" && make build)
  echo "OpenHands benchmarks ready at $dest"
fi

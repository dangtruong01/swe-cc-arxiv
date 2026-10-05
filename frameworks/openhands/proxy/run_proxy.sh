#!/usr/bin/env bash
# Start the host-side litellm proxy that OpenHands runs dial instead of Vertex.
#
# WHY THIS EXISTS: under OpenHands the LLM call is made from inside the agent container,
# where the host's Application Default Credentials do not exist. Rather than put a Google
# credential somewhere the agent under study can read it, the credential stays here and
# the container is given a URL. See ../model-overrides/gemini-3.7-flash.conf.
#
# This process must be UP for the duration of any OpenHands sweep that runs
# gemini-3.7-flash. `run_test.sh` pre-flights it and refuses to start a run without it,
# rather than discovering it mid-conversation after the model has been paid for.
#
# USAGE (from the SWE-CC repository root):
#   export OPENHANDS_PROXY_KEY="$(openssl rand -hex 24)"   # once per machine/session
#   frameworks/openhands/proxy/run_proxy.sh                # foreground; & to detach
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project="$(cd "$here/../../.." && pwd)"
port="${OPENHANDS_PROXY_PORT:-4000}"

if [ -z "${OPENHANDS_PROXY_KEY:-}" ]; then
  echo "!! OPENHANDS_PROXY_KEY is not set." >&2
  echo "   The proxy binds 0.0.0.0 -- a container cannot reach the host's loopback --" >&2
  echo "   so it is reachable beyond this machine and will not run unauthenticated." >&2
  echo "   export OPENHANDS_PROXY_KEY=\"\$(openssl rand -hex 24)\"" >&2
  exit 2
fi

# Its own virtualenv, NOT the benchmarks one. Two reasons, both learned here:
#
#   1. `litellm[proxy]` pulls a server stack (apscheduler, fastapi extras, uvloop) that
#      the agent does not need. The benchmarks environment is pinned by sha to match the
#      vendored SDK, a whole sweep runs against it, and widening it to host a side
#      service is how a pinned environment stops being pinned.
#   2. The proxy is a service with its own lifecycle. Nothing about it should be able to
#      break the agent, and nothing about the agent's pins should constrain it.
#
# litellm and google-auth are pinned to the versions benchmarks resolves (1.93.0 /
# 2.41.1), so the two halves speak the same protocol without sharing an environment.
venv="$here/.venv"
if [ ! -x "$venv/bin/litellm" ]; then
  echo "!! the proxy's virtualenv is missing: $venv" >&2
  echo "   create it with:" >&2
  echo "     uv venv $venv --python 3.12" >&2
  echo "     uv pip install --python $venv/bin/python 'litellm[proxy]==1.93.0' 'google-auth==2.41.1'" >&2
  exit 2
fi

# Fail here, not on the first model call. ADC is what this process exists to hold; if it
# is missing every run fails identically and the message ends up buried in a container
# traceback that names Vertex rather than this machine.
if ! "$venv/bin/python" -c "import google.auth; google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])" >/dev/null 2>&1; then
  echo "!! no Application Default Credentials on this host." >&2
  echo "   run: gcloud auth application-default login" >&2
  exit 2
fi

echo "== litellm proxy on 0.0.0.0:${port}"
echo "   upstream : vertex_ai/gemini-3.7-flash (ADC, host-side)"
echo "   container: http://host.docker.internal:${port}"
echo "   config   : $here/config.yaml"

exec "$venv/bin/litellm" --config "$here/config.yaml" --host 0.0.0.0 --port "$port"

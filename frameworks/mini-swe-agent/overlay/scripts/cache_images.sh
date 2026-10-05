#!/usr/bin/env bash
# Pre-build/pull the SWE-bench Docker images for every instance in cases.txt so
# the agent run and the grading step don't each pay the image-pull cost (and don't
# trip pull timeouts). Images are cached in the local Docker daemon afterward.
#
# USAGE (venv active, Docker running):
#   scripts/cache_images.sh            # uses cases.txt
#   scripts/cache_images.sh other.txt  # custom case list
set -euo pipefail

cases="${1:-cases.txt}"
dataset="${DATASET:-princeton-nlp/SWE-bench_Verified}"
workers="${WORKERS:-2}"
# Pull the official PREBUILT images from the `swebench` Docker Hub namespace rather
# than building from scratch (building is the slow part). The tags must be passed
# explicitly in this swebench version, else make_test_spec asserts env_image_tag.
namespace="${NAMESPACE:-swebench}"
# SWE-bench publishes these images for linux/amd64 ONLY. On Apple Silicon a plain
# `docker pull` fails with "no matching manifest for linux/arm64/v8"; the images run fine
# under emulation once pulled with an explicit platform. Exported so the harness's own
# puller inherits it rather than each caller remembering.
export DOCKER_DEFAULT_PLATFORM="${DOCKER_DEFAULT_PLATFORM:-linux/amd64}"
tag="${TAG:-latest}"
env_tag="${ENV_IMAGE_TAG:-latest}"

[ -f "$cases" ] || { echo "no case list at $cases -- pass a case list, e.g. sweeps/instances.txt" >&2; exit 1; }

# space-separated ids for the harness
ids="$(tr '\n' ' ' < "$cases")"
echo "caching images for: $ids"

python -m swebench.harness.prepare_images \
  --dataset_name "$dataset" --split test \
  --instance_ids $ids \
  --namespace "$namespace" --tag "$tag" --env_image_tag "$env_tag" \
  --max_workers "$workers"

echo "done. cached swe-bench images:"
docker images | grep -i swebench || true

# Shared by the two sweep scripts. Sourced, not executed.
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export RUNS_ROOT="${RUNS_ROOT:-$root/runs}"
cases="${CASES:-$root/sweeps/instances.txt}"
models="${MODELS:?set MODELS to comma-separated model slugs from models/ (e.g. MODELS=gpt-5.6-luna)}"
settings="${SETTINGS:-native consolidated}"
jobs="${JOBS:-4}"

# Paper setting -> stored condition.
conditions=""
for s in $settings; do
  case "$s" in
    native) conditions+="naive " ;;
    consolidated) conditions+="guided " ;;
    *) echo "unknown setting $s (native|consolidated)" >&2; exit 2 ;;
  esac
done

# Model slug (models/<slug>.conf) -> litellm id.
litellm_ids=""
IFS=',' read -ra slugs <<< "$models"
for m in "${slugs[@]}"; do
  id="$(sed -n 's/^LITELLM_ID="\(.*\)"/\1/p' "$root/models/$m.conf")"
  [ -n "$id" ] || { echo "no models/$m.conf" >&2; exit 2; }
  litellm_ids+="${litellm_ids:+,}$id"
done

aggregate() {
  echo "== 4/4 aggregation -> results/"
  python "$root/scripts/export_results.py" --runs "$RUNS_ROOT" --out "$root/results"
  python "$root/scripts/summarize.py" "$root/results"
}

#!/usr/bin/env bash
# Quick start: score one agent run against SymPy's 142 policies, render a task prompt,
# and summarise a results directory. Needs network once, to clone SymPy's history
# (blobless, ~70 MB) so checkers can reconstruct the files the agent changed.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
ex=examples/sympy__sympy-11618-native

if [ ! -d .cache/repos/sympy ]; then
  git clone --filter=blob:none --no-checkout --quiet https://github.com/sympy/sympy.git .cache/repos/sympy
fi

echo "== 1/3 scoring one run ($ex) against SymPy's 142 policies"
rm -f "$ex/rows.jsonl"
python -m compliance check "$ex/trajectory.json" --project sympy --setting native \
  --jsonl "$ex/rows.jsonl" | grep -E "graded|compliance rate"
python - "$ex" <<'PY'
import json, sys
from pathlib import Path
ex = Path(sys.argv[1])
key = lambda r: (r["rule_id"], r["verdict"], r["status"])
got = sorted(key(json.loads(l)) for l in (ex / "rows.jsonl").read_text().splitlines() if l.strip())
want = sorted(key(json.loads(l)) for l in (ex / "expected_rows.jsonl").read_text().splitlines() if l.strip())
print(f"   verdicts identical to the released run: {got == want} ({len(got)} policies)")
sys.exit(got != want)
PY

echo "== 2/3 the Consolidated-setting prompt additions for this task (first lines)"
python scripts/render_task.py sympy__sympy-11618 consolidated | sed -n '9,16p'

echo "== 3/3 summarising a results directory (the paper's runs, first lines)"
python scripts/summarize.py paper/results | head -5

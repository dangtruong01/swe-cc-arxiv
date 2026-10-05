#!/usr/bin/env python3
"""Run a linter over a stored run and write `lint_report.json` beside it.

**This file is deliberately not inside `compliance/`.** The original design proposed
a sandbox runner behind an explicit interface, exempted from invariant 1. That exemption is
not taken: it would make purity conditional and give any future rule author a precedent for
shelling out. Instead the runner sits outside the package and deposits stored evidence, and
the checkers read a file exactly as they read `eval_report.json`.

    ./.venv/bin/python tools/lint_sandbox.py --tool ruff              # every stored run
    ./.venv/bin/python tools/lint_sandbox.py --tool flake8 --instance sympy__sympy-11618

Costs no model calls and needs no Docker. It does need the linter on PATH; without one it
writes a report saying so, and the rules report `tool_missing` rather than failing anyone.

**Baseline subtraction.** SymPy's base commits here are from 2016-2017, and a modern linter
finds hundreds of issues in them that no agent caused. So the tool runs twice -- over the
file as it was, and as the agent left it -- and only findings present in `head` and absent
from `base` are recorded. Findings are keyed by `(file, code, normalized_message)`; line
numbers are excluded on purpose, because any edit above a finding shifts it and would make
an untouched line look new.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from compliance.bundle.builder import build_bundle          # noqa: E402
from compliance.core.lint import LINT_REPORT                # noqa: E402
from compliance.core.paths import discover                  # noqa: E402

# Numbers inside a message are the other thing that shifts without the code changing:
# "line too long (93 > 88 characters)" differs from run to run for the same defect.
_NUMBERS = re.compile(r"\d+")

TOOLS = {
    "ruff": lambda path: ["ruff", "check", "--output-format", "concise", str(path)],
    "flake8": lambda path: ["flake8", str(path)],
}
# `<path>:<line>:<col>: <CODE> <message>` -- the format both tools share here.
_LINE = re.compile(r"^(?P<path>[^:]+):(?P<line>\d+):(?P<col>\d+):\s+(?P<code>\S+)\s+(?P<msg>.*)$")


def normalise(message: str) -> str:
    return _NUMBERS.sub("N", message).strip()


def run_tool(tool: str, source: str, filename: str) -> list[dict] | None:
    """Findings for one file's text, or None if the tool is unavailable."""
    if shutil.which(tool) is None:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / Path(filename).name
        target.write_text(source, encoding="utf-8")
        try:
            result = subprocess.run(TOOLS[tool](target), capture_output=True, text=True,
                                    timeout=120)
        except (OSError, subprocess.SubprocessError) as exc:
            return [{"path": filename, "code": "E-SANDBOX", "message": str(exc)[:120]}]
    out = []
    for line in result.stdout.splitlines():
        if (m := _LINE.match(line.strip())) is None:
            continue
        out.append({"path": filename, "code": m.group("code"),
                    "message": normalise(m.group("msg"))})
    return out


def analyse(bundle, tool: str) -> dict:
    """Base-subtracted findings across every Python file in the contribution."""
    if shutil.which(tool) is None:
        return {"available": False,
                "note": f"{tool} is not on PATH; install it and re-run to grade these rules"}

    base_keys: Counter = Counter()
    head_findings: list[dict] = []
    n_base = 0
    files: list[str] = []
    for path in sorted(bundle.files):
        if not path.endswith(".py"):
            continue
        change = bundle.files[path]
        if change.head_text is None:
            continue
        files.append(path)
        if change.base_text is not None:
            for f in run_tool(tool, change.base_text, path) or []:
                base_keys[(f["path"], f["code"], f["message"])] += 1
                n_base += 1
        head_findings += run_tool(tool, change.head_text, path) or []

    return {"available": True, "files": files, "n_findings_base": n_base,
            "n_findings_head": len(head_findings),
            "new_findings": subtract(base_keys, head_findings)}


def subtract(base_keys: Counter, head_findings: list[dict]) -> list[dict]:
    """Findings present in head beyond what base already had.

    Pure, and separated out so it can be tested without a linter on PATH -- the whole
    correctness of this tool is here, and the subprocess around it is incidental.

    Counted rather than set-subtracted on purpose: adding a *second* instance of a
    complaint the file already had is a new finding, and a set difference would miss it.
    """
    new: list[dict] = []
    seen: Counter = Counter()
    for f in head_findings:
        key = (f["path"], f["code"], f["message"])
        seen[key] += 1
        if seen[key] > base_keys[key]:
            new.append(f)
    return new


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", action="append", choices=sorted(TOOLS),
                        help="repeatable; default is every supported tool")
    parser.add_argument("--instance", help="only this instance id")
    parser.add_argument("--repo", default="sympy")
    args = parser.parse_args(argv)
    tools = args.tool or sorted(TOOLS)

    runs = [r for r in discover(repo=args.repo)
            if r.trajectory.exists() and (not args.instance or r.instance_id == args.instance)]
    if not runs:
        print("no runs found", file=sys.stderr)
        return 1

    missing = [t for t in tools if shutil.which(t) is None]
    if missing:
        print(f"  note: {', '.join(missing)} not on PATH -- the report will record that, "
              f"and the rules will withhold rather than fail anyone")

    for run in runs:
        bundle = build_bundle(run.trajectory)
        payload = {"instance_id": run.instance_id, "condition": run.condition,
                   "attempt": run.attempt, "tools": {t: analyse(bundle, t) for t in tools}}
        out = run.path / LINT_REPORT
        out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        summary = ", ".join(
            f"{t}=" + ("unavailable" if not v.get("available")
                       else f"{len(v['new_findings'])} new")
            for t, v in payload["tools"].items())
        print(f"  {run.instance_id} {run.condition}/attempt{run.attempt}: {summary}")
    print(f"\n  wrote {LINT_REPORT} for {len(runs)} run(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

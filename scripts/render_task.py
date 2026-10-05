#!/usr/bin/env python3
"""Render the SWE-CC additions to a task prompt for one instance and setting.

    python scripts/render_task.py <instance_id> <native|consolidated> [--collect-script /opt/collect.sh]

Prints the scope block and the Compliance and Submission sections of
`data/prompts/task_additions.j2`, filled from `data/tasks.jsonl`. The issue text itself
comes from SWE-bench Verified; see docs/evaluate-your-agent.md.
"""
import argparse
import json
from pathlib import Path

from jinja2 import Environment, StrictUndefined

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("instance_id")
    ap.add_argument("setting", choices=("native", "consolidated"))
    ap.add_argument("--collect-script", default="/opt/collect.sh",
                    help="where harness/collect.sh is installed in the container")
    args = ap.parse_args()
    tasks = {t["instance_id"]: t for t in map(json.loads, (ROOT / "data" / "tasks.jsonl").open())}
    task = tasks[args.instance_id]
    template = Environment(undefined=StrictUndefined, keep_trailing_newline=True).from_string(
        (ROOT / "data" / "prompts" / "task_additions.j2").read_text())
    print(template.render(setting=args.setting, docs_url=task["native_docs_url"],
                          rules_path=task["consolidated_mount_path"],
                          collect_script=args.collect_script))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

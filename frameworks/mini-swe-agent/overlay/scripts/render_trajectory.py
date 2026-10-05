#!/usr/bin/env python3
"""Render each raw .traj.json into a human-readable transcript.

The raw trajectory is a megabyte of JSON; this turns it into a readable
step-by-step record (task -> per-step THOUGHT / ACTION / OBSERVATION -> outcome)
so the execution trajectory is actually consumable as a deliverable. Observations
are truncated for readability; the raw JSON remains the source of truth.

Trajectory paths are resolved via results/instance_map.json (instance_id -> traj
path), since trajectory filenames in this repo don't follow one fixed convention.

    python scripts/render_trajectory.py            # all cases in cases.txt
    python scripts/render_trajectory.py <id> ...   # specific instances
"""
import json
import os
import sys

RESULTS_DIR = "results"
MANIFEST = os.path.join(RESULTS_DIR, "instance_map.json")
OUT_DIR = os.path.join(RESULTS_DIR, "trajectories_readable")
MAX_OUT_LINES = 40
MAX_OUT_CHARS = 2500


def truncate(text, lines=MAX_OUT_LINES, chars=MAX_OUT_CHARS):
    text = text or ""
    cut = text.splitlines()
    clipped = False
    if len(cut) > lines:
        cut = cut[:lines]
        clipped = True
    out = "\n".join(cut)
    if len(out) > chars:
        out = out[:chars]
        clipped = True
    if clipped:
        out += "\n... [truncated — see raw .traj.json for full output]"
    return out


def command_of(msg):
    for tc in msg.get("tool_calls") or []:
        try:
            return json.loads(tc["function"]["arguments"]).get("command", "")
        except Exception:
            return ""
    return ""


def render(inst, manifest):
    path = manifest.get(inst)
    if not path or not os.path.exists(path):
        print(f"  skip {inst}: no trajectory registered in {MANIFEST}")
        return
    traj = json.load(open(path, encoding="utf-8"))
    info = traj["info"]
    msgs = traj["messages"]
    stats = info.get("model_stats", {})

    out = [
        f"# Execution trajectory — {inst}",
        "",
        f"- Exit status: `{info.get('exit_status')}`",
        f"- Steps (API calls): {stats.get('api_calls')}",
        f"- Cost: ${round(stats.get('instance_cost', 0) or 0, 4)}",
        f"- Submitted patch: {len(info.get('submission') or '')} chars",
        f"- Raw trajectory: `{path}`",
        "",
        "---",
        "",
        "## Task given to the agent",
        "",
    ]
    # messages[1] is the user task (problem statement + instructions). Rendered in
    # full, untruncated -- this is the actual prompt the agent received, and the
    # whole point of a compliance-focused transcript is being able to audit it.
    task = next((m["content"] for m in msgs if m["role"] == "user"), "")
    out += ["```", task, "```", "", "---", ""]

    step = 0
    for m in msgs:
        if m["role"] == "assistant":
            step += 1
            thought = (m.get("content") or "").strip() or "(no thought text)"
            cmd = command_of(m)
            out += [
                f"## Step {step}",
                "",
                f"**THOUGHT:** {thought}",
                "",
                "**ACTION:**",
                "```bash",
                cmd or "(no command)",
                "```",
                "",
            ]
        elif m["role"] == "tool":
            out += [
                "**OBSERVATION:**",
                "```",
                truncate(m.get("content") or ""),
                "```",
                "",
            ]
        elif m["role"] == "exit":
            out += ["---", "", f"## Finished — `{info.get('exit_status')}`", ""]

    sub = info.get("submission") or ""
    if sub:
        out += ["## Submitted patch", "", "```diff", sub, "```", ""]

    os.makedirs(OUT_DIR, exist_ok=True)
    dest = os.path.join(OUT_DIR, f"{inst}.md")
    with open(dest, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"  wrote {dest}  ({step} steps)")


def main():
    manifest = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {}
    if len(sys.argv) > 1:
        ids = sys.argv[1:]
    else:
        with open("cases.txt") as f:
            ids = [ln.strip() for ln in f if ln.strip()]
    print(f"rendering {len(ids)} trajectories -> {OUT_DIR}/")
    for inst in ids:
        render(inst, manifest)


if __name__ == "__main__":
    main()

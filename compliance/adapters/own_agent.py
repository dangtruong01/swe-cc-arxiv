"""Layer D adapter: any agent, from a plain JSON trajectory.

For evaluating an agent that is neither mini-swe-agent nor OpenHands. The agent's harness
writes one JSON file per run in the shape below and scores it with ``--scaffold own-agent``.
See ``docs/evaluate-your-agent.md`` for the full protocol.

    {
      "instance_id": "sympy__sympy-11618",
      "model": "my-model",
      "setting": "native",                  # or "consolidated"
      "exit_status": "Submitted",
      "steps": [                            # every action, in order
        {"command": "cat /rules/CONTRIBUTING_RULES.md", "output": "...", "returncode": 0},
        ...
      ],
      "pr_text": "Fix ... (the pull-request description the agent wrote)",
      "submission": "<stdout of harness/collect.sh, run in the container after the agent>"
    }

A tool call that is not a shell command is recorded as a string in ``command``, with the
tool name first (``read_file path``, ``fetch https://...``), so the read and fetch patterns
below can recognise it. ``output`` is exactly what the model was shown.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from compliance import naming
from compliance.core.models import Command

# Verbs that put file content in front of the agent: shell readers plus common tool names.
READ_STRATEGIES: tuple[tuple[str, re.Pattern], ...] = (
    ("cat", re.compile(r"\b(cat|less|more)\b")),
    ("head_tail", re.compile(r"\b(head|tail)\b")),
    ("sed_awk", re.compile(r"\b(sed|awk)\b")),
    ("grep", re.compile(r"\b(grep|rg|ag)\b")),
    ("python", re.compile(r"\bpython3?\b|\bopen\s*\(")),
    ("copy", re.compile(r"\bcp\b|>\s*\S+")),
    ("tool_read", re.compile(r"^\s*(read_file|view|open_file|read)\b")),
)

METADATA_ONLY = re.compile(r"^\s*(ls|stat|file|wc|find|test|\[)\b")

# Actions that reach the network: shell fetchers plus a `fetch`/`browse` tool.
FETCH_ACTIONS = re.compile(
    r"\b(curl|wget)\b|urllib\.request|requests\.get|urlopen|^\s*(fetch|browse|navigate)\b",
    re.I)

# The own-agent format stores output as the model saw it, with no wrapper.
WRAPPER_TAGS = re.compile(r"(?!)")


def commands(traj: dict[str, Any]) -> tuple[Command, ...]:
    return tuple(
        Command(index=i, command=str(step.get("command", "")),
                output=str(step.get("output", "")), returncode=step.get("returncode"))
        for i, step in enumerate(traj.get("steps") or []))


def pr_text(traj: dict[str, Any]) -> Optional[str]:
    text = traj.get("pr_text")
    return text.strip() if isinstance(text, str) and text.strip() else None


def submission_text(traj: dict[str, Any]) -> str:
    return traj.get("submission") or ""


def run_env(traj: dict[str, Any]) -> dict[str, str]:
    """The run's identity, in the RUN_* keys the bundle builder reads."""
    env: dict[str, str] = {}
    if traj.get("model"):
        env["RUN_MODEL"] = str(traj["model"])
    if traj.get("setting"):
        env["RUN_CONDITION"] = naming.condition(str(traj["setting"])) or ""
    return env


def exit_status(traj: dict[str, Any]) -> str:
    return str(traj.get("exit_status") or "")


def cost_usd(traj: dict[str, Any]) -> Optional[float]:
    value = traj.get("cost_usd")
    return float(value) if isinstance(value, (int, float)) else None


def observation_payload(text: str) -> str:
    return (text or "").strip()


def was_truncated(text: str) -> bool:
    """The own-agent format cannot say; record full output, or truncate visibly yourself."""
    return False

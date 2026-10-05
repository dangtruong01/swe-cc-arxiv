"""Layer D adapter: mini-swe-agent, as instrumented for this experiment.

A single bash loop. The model writes a shell command in free text, the harness runs it
and shows the output back. No function calling, no file editor, no browser -- which is
why the read vocabulary below is shell verbs, and why fetching a URL is something the
model has to think to do rather than a tool it is offered.

Trajectory shape: ``{"info": {...}, "messages": [...]}``. Actions hang off the assistant
message in ``extra.actions``; their outputs are the ``role: "tool"`` messages that follow,
in order. ``info.submission`` carries whatever ``collect.sh`` printed.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from compliance.core.models import Command

PR_MARKER = "PR SUBMISSION:"

# Verbs that put file content in front of the agent. `ls`, `stat`, `wc` and `file` touch
# the file but convey none of it, so they are not "opening" it.
READ_STRATEGIES: tuple[tuple[str, re.Pattern], ...] = (
    ("cat", re.compile(r"\b(cat|less|more)\b")),
    ("head_tail", re.compile(r"\b(head|tail)\b")),
    ("sed_awk", re.compile(r"\b(sed|awk)\b")),
    ("grep", re.compile(r"\b(grep|rg|ag)\b")),
    ("python", re.compile(r"\bpython3?\b|\bopen\s*\(")),
    ("copy", re.compile(r"\bcp\b|>\s*\S+")),
)

METADATA_ONLY = re.compile(r"^\s*(ls|stat|file|wc|find|test|\[)\b")

# Actions that reach the network. With no browser tool, fetching a URL is something the
# model must decide to do with a shell command -- which is the whole reason the naive arm
# measured what it did. A framework that offers a browse tool will list that instead, and
# the naive-arm result is not comparable across the two without saying so.
FETCH_ACTIONS = re.compile(r"\b(curl|wget)\b|urllib\.request|requests\.get|urlopen", re.I)

# The harness wraps command output before the model sees it. Kept in sync with
# `observation_template` in swebench_pr_compliance.yaml, which has two shapes: a whole
# `<output>` block when the output fits, and an `<output_head>` + `<output_tail>` pair
# with the MIDDLE elided when it does not. The elided shape is the one that silently
# withheld 42% of the guided treatment, so both are read here rather than only the first.
_ELIDED_MARKER = "<elided_chars>"

# Every tag the observation template can wrap output in. Stripped before an observation
# is read as prose, so the harness's own scaffolding is not mistaken for what a page said.
WRAPPER_TAGS = re.compile(
    r"</?(output|output_head|output_tail|warning|returncode|elided_chars|exception)>"
)

def commands(traj: dict[str, Any]) -> tuple[Command, ...]:
    """Every shell command the agent ran, paired with the observation it produced.

    mini-swe-agent stores actions on the assistant message and the results in the
    following tool messages, in order, so they are zipped positionally.
    """
    out: list[Command] = []
    messages = traj.get("messages") or []
    for index, message in enumerate(messages):
        actions = (message.get("extra") or {}).get("actions") or []
        if not actions:
            continue
        observations = [
            m for m in messages[index + 1 : index + 1 + len(actions)] if m.get("role") == "tool"
        ]
        for offset, action in enumerate(actions):
            observation = observations[offset] if offset < len(observations) else {}
            content = observation.get("content")
            out.append(
                Command(
                    index=len(out),
                    command=action.get("command", ""),
                    output=content if isinstance(content, str) else "",
                    returncode=(observation.get("extra") or {}).get("returncode"),
                )
            )
    return tuple(out)


def pr_text(traj: dict[str, Any]) -> Optional[str]:
    """Text the agent wrote after ``PR SUBMISSION:``.

    Only assistant messages are considered. The marker also appears in the instruction
    template, so scanning every role would return the prompt rather than the agent's
    own words -- and would score the harness instead of the model.
    """
    for message in reversed(traj.get("messages") or []):
        if message.get("role") != "assistant":
            continue
        content = message.get("content")
        if isinstance(content, str) and PR_MARKER in content:
            return content.split(PR_MARKER, 1)[1].strip()
    return None


def submission_text(traj: dict[str, Any]) -> str:
    """Whatever the run submitted, unparsed. Layer A applies our section conventions."""
    return (traj.get("info") or {}).get("submission") or ""


def run_env(traj: dict[str, Any]) -> dict[str, str]:
    """The container env recorded in the trajectory, which carries the RUN_* metadata."""
    config = (traj.get("info") or {}).get("config") or {}
    return (config.get("environment") or {}).get("env") or {}


def exit_status(traj: dict[str, Any]) -> str:
    return ((traj.get("info") or {}).get("exit_status")) or ""


def cost_usd(traj: dict[str, Any]) -> Optional[float]:
    """What the run cost, as the harness accounted it.

    Recorded per run rather than only in the collector's summary, because that summary
    lives outside this repository and a sweep across sixteen cells makes the per-cell
    figure the one worth having.
    """
    stats = (traj.get("info") or {}).get("model_stats") or {}
    value = stats.get("instance_cost")
    return float(value) if isinstance(value, (int, float)) else None


def observation_payload(text: str) -> str:
    """The command output the agent actually saw, without the harness's wrapper tags.

    Handles both shapes of the observation template: a whole `<output>` block, or the
    truncated `<output_head>` + `<output_tail>` pair.
    """
    if not text:
        return ""
    blocks = re.findall(r"<output>(.*?)</output>", text, re.S)
    if not blocks:
        blocks = re.findall(r"<output_head>(.*?)</output_head>", text, re.S)
        blocks += re.findall(r"<output_tail>(.*?)</output_tail>", text, re.S)
    return "".join(blocks).strip()


def was_truncated(text: str) -> bool:
    """Did the harness withhold part of this observation, per its own marker?"""
    return _ELIDED_MARKER in (text or "")

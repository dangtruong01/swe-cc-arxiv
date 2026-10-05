"""traj.json -> commands, pr_text, probe, run metadata.

Layer A. Knows neither a repository nor a framework.

**Everything format-specific lives in ``compliance/adapters/``** and reaches this module
through the adapter passed in (or the default, for a trajectory read outside ``runs/``).
What stays here is what *we* decided rather than what a scaffold decided: the
``===SECTION===`` delimiters ``collect.sh`` emits, the ``key=value`` probe format, and
git's porcelain status. Those are identical whichever agent produced the run.

The split matters because the framework-specific half fails quietly. A wrong trajectory
shape yields zero commands, not an exception -- and a run with zero commands scores as an
agent that did nothing rather than as a parser that read nothing.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from compliance.adapters import TrajectoryAdapter, load as load_adapter

_SECTION = re.compile(r"^===(?P<name>[A-Z_]+)===\s*$", re.MULTILINE)


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def commands(traj: dict[str, Any], adapter: TrajectoryAdapter | None = None):
    """Every action the agent ran, paired with the observation it produced."""
    return (adapter or load_adapter()).commands(traj)


def pr_text(traj: dict[str, Any], adapter: TrajectoryAdapter | None = None) -> str | None:
    """The PR description the agent wrote, as its framework records authored text."""
    return (adapter or load_adapter()).pr_text(traj)


def submission_sections(
    traj: dict[str, Any], adapter: TrajectoryAdapter | None = None
) -> dict[str, str]:
    """Split the submission on the ``===NAME===`` delimiters collect.sh emits.

    The delimiters are ours, so the splitting is Layer A; only fetching the raw text is
    the adapter's job. Returns ``{}`` for a pre-Phase-0 submission, which is a bare patch
    with no markers.
    """
    submission = (adapter or load_adapter()).submission_text(traj)
    matches = list(_SECTION.finditer(submission))
    if not matches:
        return {}
    sections: dict[str, str] = {}
    for position, match in enumerate(matches):
        end = matches[position + 1].start() if position + 1 < len(matches) else len(submission)
        sections[match.group("name")] = submission[match.end() : end].strip("\n")
    return sections


def patch_text(traj: dict[str, Any], adapter: TrajectoryAdapter | None = None) -> str:
    """Everything the agent did: ===PATCH===, or the whole submission pre-Phase-0.

    This is what SWE-bench grades, so it includes work the agent never committed.
    """
    adapter = adapter or load_adapter()
    sections = submission_sections(traj, adapter)
    if "PATCH" in sections:
        return sections["PATCH"]
    return adapter.submission_text(traj)


def committed_patch_text(
    traj: dict[str, Any], adapter: TrajectoryAdapter | None = None
) -> str | None:
    """What the agent proposed: ===PATCH_COMMITTED===, or None if the section is absent.

    ``None`` is not the same as an empty patch. Absent means the run predates the
    section and committed work cannot be distinguished; empty means the agent committed
    nothing at all.
    """
    return submission_sections(traj, adapter).get("PATCH_COMMITTED")


def parse_status(text: str) -> tuple[tuple[str, str], ...]:
    """``git status --porcelain=v1`` lines into (code, path) pairs.

    The first two columns are the index and worktree states, so ``??`` is untracked and
    a leading space means "not staged". Rename entries (``R  a -> b``) keep the destination.
    """
    entries = []
    for line in (text or "").splitlines():
        if len(line) < 4:
            continue
        code, path = line[:2], line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        entries.append((code, path.strip('"')))
    return tuple(entries)


def parse_probe(text: str) -> dict[str, str]:
    """``key=value`` lines from the startup probe. Later keys win; blank values kept."""
    probe: dict[str, str] = {}
    for line in (text or "").splitlines():
        if (line := line.strip()) and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            probe[key.strip()] = value.strip()
    return probe


def run_env(traj: dict[str, Any], adapter: TrajectoryAdapter | None = None) -> dict[str, str]:
    """The container env recorded in the trajectory, which carries the RUN_* metadata."""
    return (adapter or load_adapter()).run_env(traj)


def exit_status(traj: dict[str, Any], adapter: TrajectoryAdapter | None = None) -> str:
    return (adapter or load_adapter()).exit_status(traj)

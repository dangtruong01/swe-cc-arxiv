"""Read a stored linter result. Layer A.

**This module does not run a linter, and nothing in `compliance/` does.** Invariant 1
forbids a checker from touching a subprocess, and the original design
proposed an exemption for a sandbox runner behind an explicit interface. That exemption is
not taken. The sandbox lives outside the package entirely, in `tools/lint_sandbox.py`, and
deposits its findings beside the run as `lint_report.json` -- exactly as the SWE-bench
harness deposits `eval_report.json`. The checker then reads a file, like every other rule.

The difference is not cosmetic. An exemption would make purity a property that holds
"except where documented", and the test that enforces it would need an allowlist; a rule
author who needed a subprocess would have a precedent to point at. Keeping the runner
outside means `tests/test_purity.py` stays absolute.

**Baseline subtraction is the whole point.** Base commits in these batches are years old
and a modern linter reports hundreds of findings against them, none of which the agent
caused. So the sandbox runs the tool on base *and* head and stores the difference.
Findings are identified by ``(file, code, normalized_message)`` and never by line number,
which shifts under any edit above it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from compliance.core.paths import RunDir

LINT_REPORT = "lint_report.json"

Shape = Literal["report", "absent", "unreadable", "tool_missing"]


@dataclass(frozen=True)
class Finding:
    """One linter finding, keyed by what survives an edit."""

    path: str
    code: str
    message: str

    def key(self) -> tuple[str, str, str]:
        return (self.path, self.code, self.message)


@dataclass(frozen=True)
class LintReport:
    """What a linter said about a contribution, base-subtracted.

    ``shape`` distinguishes the cases a rule must never conflate: no report at all, a
    report saying the tool was unavailable, and a real result.
    """

    shape: Shape
    tool: str = ""
    note: str = ""
    n_findings_base: int = 0
    n_findings_head: int = 0
    new_findings: tuple[Finding, ...] = ()
    files: tuple[str, ...] = field(default_factory=tuple)

    @property
    def usable(self) -> bool:
        return self.shape == "report"

    @property
    def n_findings_new(self) -> int:
        return len(self.new_findings)

    @property
    def clean(self) -> bool:
        return self.usable and not self.new_findings


def _finding(raw: dict) -> Finding:
    return Finding(
        path=str(raw.get("path", "")),
        code=str(raw.get("code", "")),
        message=str(raw.get("message", "")),
    )


def load(run: RunDir | Path, tool: str) -> LintReport:
    """The stored result for one tool, or a shape saying why there is none."""
    directory = run.path if isinstance(run, RunDir) else Path(run)
    path = directory / LINT_REPORT if directory.is_dir() else Path(directory)
    if not path.exists():
        return LintReport("absent", tool=tool,
                          note=f"no {LINT_REPORT}; run tools/lint_sandbox.py to produce one")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return LintReport("unreadable", tool=tool, note=str(exc)[:120])

    entry = (payload.get("tools") or {}).get(tool)
    if entry is None:
        return LintReport("absent", tool=tool,
                          note=f"{LINT_REPORT} carries no result for {tool!r}")
    if not entry.get("available", False):
        return LintReport("tool_missing", tool=tool,
                          note=entry.get("note") or f"{tool} was not installed")
    return LintReport(
        "report",
        tool=tool,
        n_findings_base=int(entry.get("n_findings_base", 0)),
        n_findings_head=int(entry.get("n_findings_head", 0)),
        new_findings=tuple(_finding(f) for f in entry.get("new_findings", [])),
        files=tuple(entry.get("files", [])),
        note=entry.get("note", ""),
    )


def load_all(run: RunDir | Path, tools: tuple[str, ...]) -> dict[str, LintReport]:
    return {tool: load(run, tool) for tool in tools}

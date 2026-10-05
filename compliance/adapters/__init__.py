"""Layer D: one module per agent framework, and nothing else knows their formats.

Layers A (``core/``, ``bundle/``) and B (``extractors/``) contain no repository-specific
logic, and ``tests/test_layers.py`` enforces it. That guarantee has a second axis it did
not have to think about while one framework existed: **a trajectory has a shape, and the
shape belongs to the scaffold that wrote it.**

    Layer A/B   shared          repo-agnostic AND framework-agnostic (both guarded)
    Layer C     rules/<repo>/   may name its repository
    Layer D     adapters/<fw>/  may name its framework

Everything a framework decides goes here:

1. how actions and observations are stored, and how they pair up
2. **which actions count as reading a file** -- ``core/retrieval.py`` answers "was the
   guided treatment consumed?" from this. Under a bash agent it is ``cat``; under a
   tool-using agent it is an editor view or a browser fetch. Get it wrong and nothing
   raises: the run reports "never opened", which is exactly the false negative that
   makes *had the rules and ignored them* indistinguishable from *never looked*
3. how the harness wraps command output on its way into the model's context

What stays in Layer A is everything **we** decided rather than the framework: the
``===SECTION===` delimiters ``collect.sh`` emits, the ``key=value`` probe format, git's
porcelain status. An adapter hands back raw text; Layer A applies our conventions to it.

Adding a framework is a module here plus ``frameworks/<slug>.conf`` naming it -- the same
shape as adding a repository, and for the same reason.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Optional, Protocol, runtime_checkable

from compliance.core.models import Command

FRAMEWORKS_ROOT = Path(__file__).resolve().parents[2] / "frameworks"

DEFAULT_FRAMEWORK = "mini-swe-agent"
"""The framework every stored run so far used.

Used only when a caller supplies no framework and the trajectory's own layout cannot say
-- reading a trajectory in isolation, outside ``runs/``. A run inside the layout carries
its framework in its path and never reaches this.
"""


@runtime_checkable
class TrajectoryAdapter(Protocol):
    """What Layer A needs from a trajectory, independent of who wrote it."""

    #: Verbs that put file *content* in front of the agent, as (name, compiled pattern).
    READ_STRATEGIES: tuple[tuple[str, Any], ...]
    #: Actions that reference a path without conveying any of it (`ls`, `stat`, ...).
    METADATA_ONLY: Any

    def commands(self, traj: dict[str, Any]) -> tuple[Command, ...]: ...
    def pr_text(self, traj: dict[str, Any]) -> Optional[str]: ...
    def submission_text(self, traj: dict[str, Any]) -> str: ...
    def run_env(self, traj: dict[str, Any]) -> dict[str, str]: ...
    def exit_status(self, traj: dict[str, Any]) -> str: ...
    def observation_payload(self, text: str) -> str: ...


def adapter_module(framework: str) -> str:
    """The dotted module path for a framework, from ``frameworks/<slug>.conf``.

    Read from the conf rather than derived from the slug, so a framework whose directory
    name is not a legal python identifier (``mini-swe-agent``) needs no naming rule --
    the same reason ``repo.conf`` names its corpus instead of it being inferred.
    """
    conf_path = FRAMEWORKS_ROOT / f"{framework}.conf"
    if not conf_path.exists():
        raise FileNotFoundError(
            f"{conf_path} not found -- every framework needs one "
            f"(see frameworks/mini-swe-agent.conf)"
        )
    for line in conf_path.read_text(encoding="utf-8").splitlines():
        if (line := line.strip()) and not line.startswith("#") and line.startswith("ADAPTER"):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise KeyError(f"{conf_path} does not set ADAPTER")


#: Slugs that name no framework. ``UNKNOWN`` is what ``RunDir`` and ``EvidenceBundle``
#: carry for a trajectory read from outside ``runs/``, where the layout -- the only thing
#: that knows which scaffold wrote a run -- is unavailable. Treated as "not specified"
#: rather than looked up, so those callers reach ``DEFAULT_FRAMEWORK`` by the documented
#: route instead of dying on a missing ``frameworks/unknown.conf``.
UNSPECIFIED = ("", "unknown", None)


def load(framework: Optional[str] = None) -> TrajectoryAdapter:
    """The adapter for a framework slug. ``None`` or ``"unknown"`` means the default.

    A slug that names no ``frameworks/<slug>.conf`` raises rather than falling back.
    That is deliberate: a run filed under a framework with no adapter would otherwise be
    parsed by whichever adapter happened to be the default, and a trajectory read by the
    wrong adapter does not fail -- it yields zero commands, which scores as an agent that
    read nothing, fetched nothing and ran nothing. Loud is the only safe failure here.
    """
    if framework in UNSPECIFIED:
        framework = DEFAULT_FRAMEWORK
    return importlib.import_module(adapter_module(framework))

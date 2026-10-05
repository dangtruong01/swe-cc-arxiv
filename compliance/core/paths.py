"""Where run data lives. Single source of truth for the layout.

    runs/<repo>/<framework>/<model>/<instance>/<condition>/attempt<N>/

``<repo>`` is the slug used everywhere else -- the SWE-bench instance prefix, and the
directory name under ``rules/`` -- so an instance id of the form ``<repo>__<repo>-1234``
lands in ``runs/<repo>/`` with no mapping table to maintain. ``<framework>`` and
``<model>`` are likewise the slugs naming ``frameworks/<slug>.conf`` and
``models/<slug>.conf``; the model slug is not its litellm id, because that contains
slashes and would fork the path.

**Framework and model sit above instance, condition stays at the bottom.** Two properties
are being protected and they pull in opposite directions:

- The instance is the unit of *comparison*: to ask what the guidelines changed you read
  ``naive/`` and ``guided/`` for the same bug, so those two must stay adjacent.
- A (framework, model) pair is the unit of *operation*: it is what gets re-run when a
  scaffold is fixed, archived when a model is dropped, and staged out when either changes.

Putting the cell above the instance and the condition below it satisfies both -- an entire
sweep moves with one ``git mv``, and the two arms of the comparison remain siblings.

One directory per attempt. The original reason was automatic retry -- an empty submission
would be retried and the failure kept as evidence -- but in practice every sweep runs with
``MAX_ATTEMPTS=1`` and that path has never fired. What attempts are actually used for is
**deliberate re-runs of the same cell**: a re-run under a changed treatment (the truncated
vs whole rules file), a replicate, or a control at a different setting.

That distinction matters downstream, because **a cell run twice is two runs everywhere** --
``per_run`` keys on the attempt, so a report over both weights that instance double. Right
for replicates, wrong for a changed treatment, and the aggregate cannot tell which. So
``compliance report`` says so when it sees repeated attempts and takes ``--attempt`` to pick
one.

**An attempt is a retry of the same cell, never a different cell.**
Before framework and model were in the path, four models running one instance under one
condition would have landed in one directory separated only by the attempt counter, and
``aggregate.per_run`` -- which keys on (instance, condition, attempt) -- would have merged
them. That is the H1 failure shape this module already flags below: a key that is
not unique loses data silently.

Everything the harness writes and everything the checker derives for one run lives in
one directory, so a run can be archived, copied or deleted as a unit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_ROOT = Path(os.environ.get("RUNS_ROOT") or PROJECT_ROOT / "runs")
RULES_ROOT = PROJECT_ROOT / "rules"
MODELS_ROOT = PROJECT_ROOT / "models"
FRAMEWORKS_ROOT = PROJECT_ROOT / "frameworks"
RESULTS_ROOT = PROJECT_ROOT / "results"

# Files inside an attempt directory. Named by what they are, not by which tool made them.
TRAJECTORY = "trajectory.json"
BUNDLE = "bundle.txt"
PROBE = "probe.txt"
PATCH = "patch.diff"
PATCH_COMMITTED = "patch_committed.diff"
EVAL_REPORT = "eval_report.json"
ROWS = "rows.jsonl"

# The layout, declared once. ``path`` builds from it and ``from_path`` reads against it,
# so the two can never disagree -- which they could when recovery walked ``parents[2]``
# and adding a level meant finding every index by hand.
LAYOUT = ("repo", "framework", "model", "instance_id", "condition")

_INSTANCE = re.compile(r"^(?P<repo>[A-Za-z0-9_.-]+)__(?P<rest>.+)$")
_ATTEMPT = re.compile(r"^attempt(?P<n>\d+)$")

# Used where a run genuinely does not record one. The two pre-Phase-0 runs sit in a
# condition directory literally named `unknown` for the same reason: the layout states
# what is known and admits what is not, rather than guessing.
UNKNOWN = "unknown"


def repo_of(instance_id: str) -> str:
    """``<repo>__<name>-<n>`` -> ``<repo>``. The same derivation run_test.sh uses."""
    match = _INSTANCE.match(instance_id)
    if not match:
        raise ValueError(f"cannot derive a repo slug from instance id {instance_id!r}")
    return match.group("repo")


def model_slug(litellm_id: str) -> str:
    """``openrouter/google/gemini-2.5-flash`` -> ``gemini-2.5-flash``.

    The last segment only. Two models from one vendor that differ before the last segment
    would collide, which is why ``models/<slug>.conf`` is the authority on the slug and
    this is a convenience for reading a stored run's ``model`` field back into a path.
    """
    return (litellm_id or "").rstrip("/").rsplit("/", 1)[-1] or UNKNOWN


@dataclass(frozen=True)
class RunDir:
    """One attempt at one instance, under one condition, in one (framework, model) cell."""

    repo: str
    instance_id: str
    condition: str
    attempt: int = 1
    root: Path = RUNS_ROOT
    framework: str = UNKNOWN
    model: str = UNKNOWN

    @classmethod
    def for_instance(
        cls,
        instance_id: str,
        condition: str,
        attempt: int = 1,
        root: Path = RUNS_ROOT,
        framework: str = UNKNOWN,
        model: str = UNKNOWN,
    ) -> RunDir:
        return cls(repo_of(instance_id), instance_id, condition, attempt, root,
                   framework, model)

    @property
    def cell(self) -> tuple[str, str]:
        """The (framework, model) pair. The unit a sweep is run, re-run and reported in."""
        return (self.framework, self.model)

    @property
    def path(self) -> Path:
        parts = [getattr(self, name) for name in LAYOUT]
        return self.root.joinpath(*parts, f"attempt{self.attempt}")

    def file(self, name: str) -> Path:
        return self.path / name

    @property
    def trajectory(self) -> Path:
        return self.file(TRAJECTORY)

    def mkdir(self) -> Path:
        self.path.mkdir(parents=True, exist_ok=True)
        return self.path

    @classmethod
    def from_path(cls, path: Path | str) -> RunDir | None:
        """Recover which run a file belongs to, from the layout alone.

        **The directory is the record.** Every trajectory is named ``trajectory.json``, so
        the filename identifies nothing -- deriving an instance id from it gives every run
        the same one, and two runs then collapse into a single key in any aggregate that
        groups by instance. That is the H1 failure shape: a key that is not unique loses
        data silently, and the loss is perfectly correlated with whichever runs share it.

        Read against ``LAYOUT`` rather than by counting parents, so adding a level to the
        layout cannot leave a stale index behind that silently mis-assigns every run.

        Returns ``None`` for a path outside the layout, so a caller can fall back rather
        than receive a fabricated answer.
        """
        candidate = Path(path)
        for node in (candidate, *candidate.parents):
            match = _ATTEMPT.match(node.name)
            if match is None:
                continue
            # `node.parent` is the last LAYOUT component, `parents[len(LAYOUT)-1]` the
            # first, and everything above that is the root.
            if len(node.parents) < len(LAYOUT) + 1:
                continue
            fields = {
                name: node.parents[len(LAYOUT) - 1 - index].name
                for index, name in enumerate(LAYOUT)
            }
            return cls(attempt=int(match.group("n")),
                       root=node.parents[len(LAYOUT)], **fields)
        return None


def discover(
    root: Path = RUNS_ROOT,
    repo: str | None = None,
    framework: str | None = None,
    model: str | None = None,
    attempt: int | None = None,
) -> list[RunDir]:
    """Every attempt directory containing a trajectory, in stable order.

    Ordering is lexicographic on the path so a scoring pass over the corpus is
    reproducible (invariant 7) regardless of filesystem iteration order. The optional
    filters narrow to one repo, one framework or one model without the caller having to
    know the layout -- which is the point of them living here.
    """
    if not root.exists():
        return []
    # `attempt` narrows to one repeat of a cell. A cell run twice is two runs everywhere
    # downstream, so a report over both weights that instance double -- which is right for
    # replicates and wrong for a re-run under a changed treatment. The filter lets the
    # caller say which they meant.
    pattern = "/".join([repo or "*", framework or "*", model or "*", "*", "*",
                        f"attempt{attempt if attempt else '*'}/{TRAJECTORY}"])
    found: list[RunDir] = []
    for trajectory in sorted(root.glob(pattern)):
        if (run := RunDir.from_path(trajectory)) is not None:
            found.append(run)
    return found


def locate(
    instance_id: str,
    condition: str,
    attempt: int = 1,
    framework: str | None = None,
    model: str | None = None,
    root: Path = RUNS_ROOT,
) -> list[RunDir]:
    """Stored runs matching an instance and condition, narrowed by cell if given.

    Returns a list, never a guess. With one cell on disk a caller can take the single
    element; with sixteen, an unqualified request is genuinely ambiguous and the caller
    has to say which framework and model it meant. Silently returning the first match
    would answer a question nobody asked -- and would answer it differently as soon as a
    new cell landed, with nothing in the output showing that it had changed.
    """
    return [
        run
        for run in discover(root=root, repo=repo_of(instance_id),
                            framework=framework, model=model)
        if run.instance_id == instance_id
        and run.condition == condition
        and run.attempt == attempt
    ]

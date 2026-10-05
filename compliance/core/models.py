"""Data contracts. Everything in the package depends on this module and nothing else.

Layer A: contains no knowledge of any particular repository.

Two deliberate additions to the §3 contract, both forced by rules in this batch:

* ``FileChange.added_lines`` carries the *text* of added lines, not only their numbers.
  §3 specifies ``authored_lines: frozenset[int]``, which is enough to decide ownership but
  not enough to judge content. C041 has to read the ``.mailmap`` entries the agent wrote.
* ``Commit.body_lines`` is kept alongside §3's ``body``. §3 defines the body as the text
  after the first blank line, so a malformed message with no blank separator would report
  an empty body -- and C025, whose entire job is to catch that, would see nothing to judge
  and return ``not_applicable``. ``body_lines`` is everything after the summary with at most
  one leading blank removed, so the malformed case still presents a target.

``Status`` also gains ``error`` over §3's list, per invariant 6: a crashed checker is
recorded as a row status, never as a violation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Optional

if TYPE_CHECKING:
    from compliance.core.lint import LintReport  # avoids importing the reader into the base data contracts
    from compliance.core.evaluation import EvalReport

Verdict = Literal["pass", "fail", "not_applicable"]
Status = Literal["ok", "tool_missing", "parse_error", "error"]
Source = Literal["patch", "commit", "pr", "trajectory", "probe", "rerun"]
Ownership = Literal["created", "touched", "enclosing"]

BUNDLE_VERSION = "1"


@dataclass(frozen=True)
class Command:
    """One shell command the agent ran, with what came back."""

    index: int
    command: str
    output: str = ""
    returncode: Optional[int] = None


@dataclass(frozen=True)
class Commit:
    sha: str
    summary: str
    body: str
    trailers: dict[str, str]
    author_name: str
    author_email: str
    raw: str
    message_lines: tuple[str, ...] = ()
    body_lines: tuple[str, ...] = ()
    trailer_lines: tuple[str, ...] = ()
    branch: Optional[str] = None
    """Branch the commit was made on, when the harness recorded it. ``None`` means
    unknown -- not 'detached', not 'master'. Rules must treat it as missing evidence."""


@dataclass(frozen=True)
class Hunk:
    """One `@@` block of a unified diff, kept so the post-patch file can be rebuilt."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: tuple[str, ...]
    """Raw hunk body lines, each still carrying its leading ' ', '+' or '-'."""


@dataclass(frozen=True)
class FileChange:
    path: str
    authored_lines: frozenset[int]
    """Post-patch line numbers whose *text the agent wrote* -- the diff's `+` lines.

    Content rules use this: to judge what an agent wrote, you need the lines it wrote.
    Ownership does not, because deleting code is also editing it. See ``modified_lines``.
    """
    added_lines: tuple[tuple[int, str], ...] = ()
    removed_lines: tuple[str, ...] = ()
    head_text: Optional[str] = None
    base_text: Optional[str] = None
    is_new: bool = False
    is_deleted: bool = False
    is_binary: bool = False
    old_path: Optional[str] = None
    hunks: tuple["Hunk", ...] = ()
    deletion_anchors: frozenset[int] = frozenset()
    """Post-patch lines where the agent removed code, one per removal site.

    A patch that only deletes has no `+` lines at all, so ``authored_lines`` is empty and
    the file would be owned by nobody -- every AST rule reporting ``not_applicable`` with
    status ``ok``, indistinguishable from the rule genuinely not applying. One pilot agent
    fixed its bug by deleting a six-line validation block and adding nothing, and was
    invisible to the entire checker.

    A removal has no post-patch line of its own, so the anchor is the line that now
    occupies the position: the running post-patch counter at the point the removal
    appears in its hunk. With the usual three lines of context that anchor falls inside
    the definition the code was removed from, which is what ownership needs.
    """

    @property
    def modified_lines(self) -> frozenset[int]:
        """Every post-patch line the agent's edit reaches -- written or deleted from.

        This, not ``authored_lines``, is what ``touched`` and ``enclosing`` ownership are
        about (docs/checker-authoring.md §4): the question is whether the agent edited this
        region, and a deletion is an edit.
        """
        return self.authored_lines | self.deletion_anchors


@dataclass(frozen=True)
class EvidenceBundle:
    instance_id: str
    base_commit: str
    created_at: str
    condition: str
    model: str
    files: dict[str, FileChange]
    """The CONTRIBUTION: what the agent committed. This is what rules judge.

    Deciding what belongs in a contribution is itself graded behaviour (C021), so the
    agent's staging decision is evidence, not noise to be normalised away. Scratch files
    it chose not to commit are in ``files_worktree`` and are deliberately absent here."""
    commits: tuple[Commit, ...]
    pr_text: Optional[str]
    commands: tuple[Command, ...]
    probe: dict[str, str]
    framework: str = "unknown"
    """Which agent scaffold produced this run.

    Defaulted rather than required: it is recovered from the run's directory, and a
    trajectory read from outside ``runs/`` genuinely does not know which scaffold wrote
    it. `unknown` says so -- the same convention the two pre-Phase-0 runs use for their
    condition, and better than defaulting to whichever framework came first.
    """
    files_worktree: dict[str, FileChange] = field(default_factory=dict)
    """Everything in the working tree at submit time, committed or not. SWE-bench grades
    this, so a forgotten commit is not scored as a failed fix. Superset of ``files``."""
    status_entries: tuple[tuple[str, str], ...] = ()
    """``git status --porcelain`` pairs of (code, path), captured before staging. ``??``
    means untracked. Descriptive evidence -- how much debris the agent left -- not used
    to decide scope; ``files`` already answers that exactly."""
    patch_scope: Literal["committed", "worktree_fallback"] = "committed"
    """``worktree_fallback`` means no ===PATCH_COMMITTED=== section was present and
    ``files`` fell back to the full patch, so committed and uncommitted work cannot be
    told apart. True of every pre-Phase-0 trajectory."""
    bundle_version: str = BUNDLE_VERSION
    attempt_n: int = 1
    run_id: str = ""
    evaluation: Optional["EvalReport"] = None
    """What the SWE-bench harness said about this patch, when the run was graded.

    Its ``tests_status`` is a before-and-after comparison of test outcomes, which is
    exactly what the corpus means by ``CheckTier = differential``. Rules that need to know
    whether a test changed state read it here instead of withholding.

    ``None`` means the run carries no usable functional result, and rules must treat that
    as missing evidence -- never as "no tests changed".
    """
    lint: dict[str, "LintReport"] = field(default_factory=dict)
    """What a linter said about this contribution, per tool, base-subtracted.

    Produced by `tools/lint_sandbox.py`, which lives outside the package precisely so no
    checker ever runs a subprocess (invariant 1). Empty, or carrying an unusable shape,
    means the rules that need it withhold with a named missing input rather than guess.
    """
    commits_source: Literal["log", "trajectory_shim", "none"] = "none"
    """Where ``commits`` came from. ``trajectory_shim`` means the pre-Phase-0 fallback
    fired and the metadata is partial -- notably no sha, author, or branch."""
    notes: tuple[str, ...] = ()

    def changed_paths(self) -> tuple[str, ...]:
        return tuple(sorted(self.files))

    def uncommitted_paths(self) -> tuple[str, ...]:
        """Files the agent left in the tree but did not commit."""
        return tuple(sorted(set(self.files_worktree) - set(self.files)))


@dataclass(frozen=True)
class Target:
    """One thing a rule judges. Every verdict traces back to one of these."""

    key: str
    file: Optional[str]
    line_span: Optional[tuple[int, int]]
    source: Source
    payload: Any = None
    snippet: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "file": self.file,
            "line_span": list(self.line_span) if self.line_span else None,
            "source": self.source,
            "snippet": self.snippet[:300],
        }


# --- judgements -------------------------------------------------------------------


@dataclass(frozen=True)
class Satisfied:
    reason: str = ""


@dataclass(frozen=True)
class Violated:
    reason: str


@dataclass(frozen=True)
class Undetermined:
    """The rule applies, but the bundle does not carry the evidence to judge it.

    Never a violation (invariant 6) and never a silent pass. Rows built only from
    ``Undetermined`` targets get ``verdict='not_applicable'`` with a non-``ok`` status,
    so they leave both the numerator and the denominator.
    """

    status: Status = "parse_error"
    reason: str = ""


Judgement = Any  # Satisfied | Violated | Undetermined


@dataclass
class ResultRow:
    run_id: str
    instance_id: str
    base_commit: str
    created_at: str
    condition: str
    model: str
    attempt_n: int
    rule_id: str
    shared_category: str
    strength: str
    verdict: Verdict
    status: Status
    n_targets: int
    n_targets_preexisting: int
    n_violating: int
    evidence: Literal["direct", "vacuous"]
    framework: str = "unknown"
    """The (framework, model) pair is the cell a row belongs to. `model` was always here;
    without `framework` beside it two scaffolds' rows are indistinguishable once pooled."""
    targets: list[dict] = field(default_factory=list)
    notes: str = ""
    checker_version: str = ""
    heuristic: bool = False
    by_construction: bool = False
    """The rule is unsatisfiable by an autonomous agent; see registry.RegisteredRule."""

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)

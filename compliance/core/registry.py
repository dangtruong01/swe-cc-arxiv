"""Rule registration and corpus lookup.

Layer A. The corpus is the authority on a rule's category and strength; the decorator
only declares what the checker needs (ownership, and whether the check is a heuristic).
Registering a rule id that the corpus does not contain is an error -- it means the
implementation and the corpus have drifted.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from compliance.core import workbook
from compliance.core.models import Ownership

# 0.2.0 (25 Aug 2026): a Python file the agent shipped that will not parse is a violation
# of every rule that reads it, not a withheld verdict. Moves 122 rows from
# `not_applicable/parse_error` to `fail` and is the first change to alter stored results, so
# the version moves with it -- rows scored under 0.1.0 are not comparable to rows scored now.
# 0.3.0 (31 Aug 2026): C276 no longer passes an agent run that merely CLAIMS human
# review. The rule is `by_construction` -- there is no human in the loop -- yet it passed
# on any PR text matching "reviewed"/"verified by"/"human"/"manually", which contradicted
# the marking and scored a false statement as compliance. One model passed 36 of 75 guided
# runs that way against 1 of 75 naive; every other model passed 0-1 in either arm. Moves 39
# rows from `pass` to `fail`, all but one in the guided arm, and cuts the AI-policy
# category's guided rate from 16.3% to 14.1%.
CHECKER_VERSION = "0.3.0"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = PROJECT_ROOT / "rules"


@dataclass(frozen=True)
class CorpusRule:
    id: str
    shared_category: str
    strength: str
    care: bool
    atomic_rule: str
    check_tier: str
    applies_to: str
    source: str = ""
    """Where the rule was extracted from: URL, then ' | ' separated section path."""


# Which part of the evidence bundle a rule consumes, and which collect.sh section
# supplies it. When a section is missing from a run, this says exactly which rules are
# affected instead of leaving it to be discovered as a wave of odd verdicts.
EVIDENCE_SOURCES: dict[str, str] = {
    "commits": "===LOG===",
    "files": "===PATCH_COMMITTED===",
    "files_worktree": "===PATCH===",
    "status": "===STATUS===",
    "probe": "===PROBE===",
    "branch": "===BRANCH===",
    "commands": "trajectory (command log)",
    "pr_text": "trajectory (the PR description the agent wrote)",
    "evaluation": "eval_report.json (the SWE-bench harness's own grading)",
    # Evidence Phase 5 will supply and the bundle does not carry yet. A rule that needs
    # one of these declares it, which is what makes withholding auditable: the claim
    # "I cannot answer this" becomes a named missing input rather than a judgement call.
    # When Phase 5 lands and the bundle carries them, the invariant in
    # tests/test_check_tier.py stops permitting those rules to withhold -- so the
    # exemption sunsets itself instead of being remembered.
    "test_timings": "Phase 5: per-test durations",
    "repeated_runs": "Phase 5: the same test executed more than once",
    "doctest_run": "Phase 5: doctests executed and their output compared",
    "lint_run": "Phase 5: a linter run on base and head, baseline-subtracted",
    "repo_version": "Phase 5: the project version at the base commit",
    "full_suite_run": "Phase 5: the complete test suite, not the harness's subset",
    "deprecated_api_run": "Phase 5: the deprecated API exercised, to see which warning "
                          "it emits and whether its behaviour is unchanged",
    "expression_eval": "Phase 5: symbolic evaluation of two expressions for equivalence",
}


@dataclass(frozen=True)
class RegisteredRule:
    id: str
    ownership: Ownership
    heuristic: bool
    checker: Any
    category: str = ""
    by_construction: bool = False
    """No autonomous agent can pass this rule, whatever it does.

    Not a defect in the rule and not a finding about the agent: the corpus addresses a human
    contributor, and a handful of its rules are unsatisfiable by the subject under test.
    docs/checker-authoring.md §6.5 requires the report to be able to show the rate with and
    without them, which is what this flag is for. A `fail` here is a tautology, and a
    tautology counted as non-compliance inflates the headline."""
    reads: tuple[str, ...] = ()
    """Bundle fields this rule reads. Keys of EVIDENCE_SOURCES."""

    @property
    def doc(self) -> str:
        return (self.checker.__doc__ or "").strip()


_REGISTRY: dict[str, RegisteredRule] = {}


def rule(
    id: str,
    *,
    category: str = "",
    ownership: Ownership = "touched",
    heuristic: bool = False,
    by_construction: bool = False,
    reads: tuple[str, ...] = (),
) -> Callable[[type], type]:
    """Register a checker class. Two methods are required, per docs/checker-authoring.md §2:

    ``precondition(bundle) -> list[Target]`` selects, and ``pass_condition(target)``
    grades. The docstring must state both in one sentence each.
    """

    def decorate(cls: type) -> type:
        if id in _REGISTRY:
            raise ValueError(f"rule {id} is already registered")
        for method in ("precondition", "pass_condition"):
            if not callable(getattr(cls, method, None)):
                raise TypeError(f"rule {id} ({cls.__name__}) has no {method}()")
        if unknown := set(reads) - set(EVIDENCE_SOURCES):
            raise ValueError(f"rule {id} declares unknown evidence source(s): {sorted(unknown)}")
        if not reads:
            raise ValueError(f"rule {id} must declare what it reads (reads=...)")
        _REGISTRY[id] = RegisteredRule(
            id=id, ownership=ownership, heuristic=heuristic, checker=cls(),
            category=category, reads=tuple(reads), by_construction=by_construction,
        )
        return cls

    return decorate


# Which bundle fields carry each declared source. A source absent from this map is one the
# bundle never carries, so a rule declaring it may legitimately withhold.
_CARRIED_BY: dict[str, Callable[[Any], bool]] = {
    "commits": lambda b: bool(b.commits),
    "files": lambda b: bool(b.files),
    "files_worktree": lambda b: bool(b.files_worktree),
    "status": lambda b: bool(b.status_entries),
    "probe": lambda b: bool(b.probe),
    "branch": lambda b: any(c.branch is not None for c in b.commits),
    "commands": lambda b: bool(b.commands),
    "pr_text": lambda b: bool(b.pr_text),
    "evaluation": lambda b: b.evaluation is not None,
    # Carried only when a linter actually ran. A report recording that the tool was absent
    # is evidence of absence, not the evidence the rule needs, so the rules keep their
    # right to withhold -- and lose it automatically the moment a real result appears.
    "lint_run": lambda b: any(r.usable for r in getattr(b, "lint", {}).values()),
}


def evidence_present(bundle: Any) -> set[str]:
    """The declared evidence sources this bundle actually carries.

    Used to audit withholding: a rule may only decline to grade when something it says it
    reads is missing from the run in front of it. Sources with no entry in ``_CARRIED_BY``
    are ones nothing supplies yet, so they are never present.
    """
    return {name for name, carried in _CARRIED_BY.items() if carried(bundle)}


def registered(ids: Optional[Iterable[str]] = None) -> list[RegisteredRule]:
    """Registered rules, always in id order so a run is reproducible."""
    wanted = set(ids) if ids else None
    return [r for _, r in sorted(_REGISTRY.items()) if wanted is None or r.id in wanted]


def clear_registry() -> None:
    _REGISTRY.clear()


def load_corpus(corpus_path: str | Path) -> dict[str, CorpusRule]:
    """The corpus, from a spreadsheet or a CSV -- whichever ``repo.conf`` names.

    Both formats are supported because corpora exist in both: some were exported to CSV
    before the workbook could be read directly. Reading the authored file removes an
    export step, and a skipped export scores yesterday's corpus with no error to say so.
    """
    path = Path(corpus_path)
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        rows = workbook.read(path)
    else:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    corpus: dict[str, CorpusRule] = {}
    for row in rows:
        rule_id = (row.get("ID") or "").strip()
        if not rule_id:
            continue
        corpus[rule_id] = CorpusRule(
            id=rule_id,
            shared_category=(row.get("Shared Category") or "").strip(),
            strength=(row.get("Strength") or "").strip().lower(),
            care=(row.get("Care") or "").strip().upper() in {"TRUE", "1", "YES"},
            atomic_rule=(row.get("Atomic rule") or "").strip(),
            check_tier=(row.get("CheckTier") or "").strip(),
            applies_to=(row.get("Applies to") or "").strip(),
            source=(row.get("Source") or "").strip(),
        )
    return corpus


def repo_conf(repo: str) -> dict[str, str]:
    """The KEY="value" settings shared with scripts/run_test.sh and the generator."""
    conf_path = RULES_DIR / repo / "repo.conf"
    if not conf_path.exists():
        raise FileNotFoundError(f"{conf_path} not found")
    settings: dict[str, str] = {}
    for line in conf_path.read_text(encoding="utf-8").splitlines():
        if (line := line.strip()) and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            settings[key.strip()] = value.strip().strip("\"'")
    return settings


def corpus_path_for(repo: str) -> Path:
    """Locate a repo's corpus through its repo.conf, the same file run_test.sh reads."""
    repo_dir = RULES_DIR / repo
    conf = repo_dir / "repo.conf"
    if not conf.exists():
        raise FileNotFoundError(f"{conf} not found")
    for line in conf.read_text(encoding="utf-8").splitlines():
        if (line := line.strip()) and not line.startswith("#") and line.startswith("CORPUS"):
            return repo_dir / line.split("=", 1)[1].strip().strip("\"'")
    raise KeyError(f"{conf} does not set CORPUS")


def in_batch(corpus: dict[str, CorpusRule]) -> list[str]:
    """The scored batch for any repo: rules marked Care with strength ``must``."""
    return sorted(r.id for r in corpus.values() if r.care and r.strength == "must")

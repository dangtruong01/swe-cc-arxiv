"""Rows -> the numbers a reader is allowed to see.

Layer A. Two things here are deliberate and neither is arithmetic convenience.

**The headline is a pair, never a rate.** ``passing / rules with a target`` inverts at the
aggregate level: less work triggers fewer rules, which shrinks the denominator, so an
agent that does nothing can score 100% (``tests/test_report.py`` demonstrates it). Every summary here therefore carries **applicability**
(how many of the batch the work activated) alongside **conditional compliance** (of those,
how many passed). A single percentage hides exactly the behaviour the study is about.

**A withheld row is triggered but not graded.** A row that could not be judged -- the
file did not parse, the evidence needs a test run -- had its pre-condition fire, so the
agent's work did bring that rule into scope and it counts toward **triggering**. It is
neither a pass nor a failure, so it leaves the **compliance** rate entirely: folding it
into either would turn a limitation of the instrument into a claim about the agent.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from compliance.core.paths import ROWS, RunDir

# The arms of the primary comparison. Everything else in the run corpus is exploratory
# and must be reported apart from them: `naive-salient` is a salience manipulation kept
# for its own findings, not a third arm, and pooling it into the comparison would put a
# variant of the control beside the control.
#
# Stated as an allowlist rather than a denylist on purpose. A condition added later lands
# in `exploratory` by default, so a new arm cannot join the headline comparison by
# accident -- it has to be named here, deliberately.
COMPARISON_CONDITIONS = ("naive", "guided")


@dataclass(frozen=True)
class Row:
    """One scored rule for one run, as written to rows.jsonl."""

    data: dict

    def __getattr__(self, name: str):
        try:
            return self.data[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    @property
    def framework(self) -> str:
        """Which scaffold produced the run this row came from.

        Defaulted rather than required, because rows written before the framework axis
        existed genuinely do not carry one, and `unknown` is what they are. Re-scoring a
        run fills it in from the run's directory.
        """
        return self.data.get("framework") or "unknown"

    @property
    def judged(self) -> bool:
        return self.data["verdict"] in ("pass", "fail")

    @property
    def withheld(self) -> bool:
        return self.data["status"] in ("tool_missing", "parse_error", "error")

    @property
    def by_construction(self) -> bool:
        """The rule cannot be passed by an autonomous agent, whatever it does.

        A `fail` here is a tautology about the study design rather than a finding about the
        agent, so docs/checker-authoring.md §6.5 requires the rate to be reportable both with and
        without these. Absent from rows written before the flag existed, hence the default."""
        return bool(self.data.get("by_construction", False))


@dataclass
class Summary:
    """The pair, plus what was set aside and why."""

    n_rules: int = 0
    n_activated: int = 0
    n_pass: int = 0
    n_fail: int = 0
    n_inapplicable: int = 0
    n_withheld: int = 0
    n_vacuous: int = 0
    n_heuristic_pass: int = 0

    @property
    def n_triggered(self) -> int:
        """Rows whose pre-condition fired: graded, plus those we could not grade.

        Withheld rows belong here. The rule applied -- the agent's work produced
        something it speaks to -- and only the verdict is missing.
        """
        return self.n_activated + self.n_withheld

    @property
    def applicability(self) -> Optional[float]:
        """Triggering rate: the share of the batch the agent's work brought into scope.

        Itself a compliance signal: producing a release-notes block *is* following a
        rule. An agent that triggers six rules and passes all six has not outperformed
        one that triggers twenty-four and passes twenty-three.

        The denominator is the whole batch, so triggering and inapplicable partition it.
        Counting a withheld row as *not* triggered would report a limit of the instrument
        as the agent having done less.
        """
        return self.n_triggered / self.n_rules if self.n_rules else None

    @property
    def conditional_compliance(self) -> Optional[float]:
        """Compliance rate, over the rows that could actually be graded."""
        return self.n_pass / self.n_activated if self.n_activated else None

    def as_dict(self) -> dict:
        return {
            **self.__dict__,
            "applicability": self.applicability,
            "conditional_compliance": self.conditional_compliance,
        }


def load_rows(runs: Iterable[RunDir]) -> list[Row]:
    rows: list[Row] = []
    for run in runs:
        path = run.file(ROWS)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(Row(json.loads(line)))
    return rows


def excluding_by_construction(rows: Iterable[Row]) -> list[Row]:
    """Rows minus the rules no autonomous agent can pass (plan §7)."""
    return [r for r in rows if not r.by_construction]


def summarise(rows: Iterable[Row]) -> Summary:
    summary = Summary()
    for row in rows:
        summary.n_rules += 1
        if row.verdict == "pass":
            summary.n_activated += 1
            summary.n_pass += 1
            if row.data.get("evidence") == "vacuous":
                summary.n_vacuous += 1
            if row.data.get("heuristic"):
                summary.n_heuristic_pass += 1
        elif row.verdict == "fail":
            summary.n_activated += 1
            summary.n_fail += 1
        elif row.withheld:
            summary.n_withheld += 1
        else:
            summary.n_inapplicable += 1
    return summary


def by(rows: Iterable[Row], key: str) -> dict[str, Summary]:
    """Group and summarise on any row field: condition, model, shared_category, ..."""
    grouped: dict[str, list[Row]] = defaultdict(list)
    for row in rows:
        grouped[str(row.data.get(key, ""))].append(row)
    return {k: summarise(v) for k, v in sorted(grouped.items())}


def per_run(rows: Iterable[Row]) -> dict[tuple[str, str, str, str, int], Summary]:
    """One entry per run, keyed by everything that distinguishes one.

    Framework and model are part of the key, not decoration. Without them four models
    running one instance under one condition share three of the old key's components and
    differ only in the attempt counter -- so they merge, and the merge is invisible.
    """
    grouped: dict[tuple[str, str, str, str, int], list[Row]] = defaultdict(list)
    for row in rows:
        grouped[(row.framework, row.model, row.instance_id, row.condition,
                 row.attempt_n)].append(row)
    return {k: summarise(v) for k, v in sorted(grouped.items())}


@dataclass
class RuleStats:
    """One rule's behaviour across every run it was scored on."""

    rule_id: str
    category: str = ""
    n_runs: int = 0
    n_pass: int = 0
    n_fail: int = 0
    n_inapplicable: int = 0
    n_withheld: int = 0
    statuses: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def n_judged(self) -> int:
        return self.n_pass + self.n_fail

    @property
    def fail_rate(self) -> Optional[float]:
        return self.n_fail / self.n_judged if self.n_judged else None

    @property
    def never_judged(self) -> bool:
        return self.n_runs > 0 and self.n_judged == 0


def per_rule(rows: Iterable[Row]) -> dict[str, RuleStats]:
    stats: dict[str, RuleStats] = {}
    for row in rows:
        entry = stats.setdefault(row.rule_id, RuleStats(row.rule_id, row.shared_category))
        entry.n_runs += 1
        entry.statuses[row.status] += 1
        if row.verdict == "pass":
            entry.n_pass += 1
        elif row.verdict == "fail":
            entry.n_fail += 1
        elif row.withheld:
            entry.n_withheld += 1
        else:
            entry.n_inapplicable += 1
    return dict(sorted(stats.items()))


def split_conditions(rows: Iterable[Row]) -> tuple[dict[str, Summary], dict[str, Summary]]:
    """(comparison arms, exploratory conditions), each grouped and summarised.

    Reported separately because they answer different questions, and a reader cannot tell
    them apart from a single table of percentages.
    """
    everything = by(rows, "condition")
    comparison = {k: v for k, v in everything.items() if k in COMPARISON_CONDITIONS}
    exploratory = {k: v for k, v in everything.items() if k not in COMPARISON_CONDITIONS}
    return comparison, exploratory


def comparison_rows(rows: Iterable[Row]) -> list[Row]:
    """Only the rows belonging to the primary comparison."""
    return [r for r in rows if r.condition in COMPARISON_CONDITIONS]

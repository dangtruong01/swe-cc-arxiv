"""Execute rules over a bundle -> [ResultRow].

The verdict arithmetic lives here and nowhere else, so every rule obeys the same
invariants whatever its author intended:

* zero targets -> ``not_applicable``, never pass, never fail (invariant 3)
* a crash is ``status='error'`` with verdict ``not_applicable`` (invariant 6)
* ``Undetermined`` targets -- the rule applies but the bundle cannot answer it -- leave
  the row out of both numerator and denominator rather than guessing
"""

from __future__ import annotations

import logging
import traceback

from compliance.core.models import (
    EvidenceBundle,
    ResultRow,
    Satisfied,
    Target,
    Undetermined,
    Violated,
)
from compliance.core.registry import CHECKER_VERSION, CorpusRule, RegisteredRule

logger = logging.getLogger("compliance.core.runner")

MAX_RECORDED_TARGETS = 20


def run_rules(
    bundle: EvidenceBundle,
    rules: list[RegisteredRule],
    corpus: dict[str, CorpusRule],
    *,
    checker_version: str = CHECKER_VERSION,
) -> list[ResultRow]:
    return [run_rule(bundle, r, corpus, checker_version=checker_version) for r in rules]


def run_rule(
    bundle: EvidenceBundle,
    registered: RegisteredRule,
    corpus: dict[str, CorpusRule],
    *,
    checker_version: str = CHECKER_VERSION,
) -> ResultRow:
    meta = corpus.get(registered.id)
    row = ResultRow(
        run_id=bundle.run_id,
        instance_id=bundle.instance_id,
        base_commit=bundle.base_commit,
        created_at=bundle.created_at,
        condition=bundle.condition,
        model=bundle.model,
        framework=bundle.framework,
        attempt_n=bundle.attempt_n,
        rule_id=registered.id,
        shared_category=meta.shared_category if meta else registered.category,
        strength=meta.strength if meta else "",
        verdict="not_applicable",
        status="ok",
        n_targets=0,
        n_targets_preexisting=0,
        n_violating=0,
        evidence="vacuous",
        checker_version=checker_version,
        heuristic=registered.heuristic,
        by_construction=registered.by_construction,
    )

    try:
        targets = list(registered.checker.precondition(bundle))
    except Exception as exc:  # noqa: BLE001 -- a broken checker must not become a violation
        logger.error("precondition of %s raised: %s", registered.id, exc)
        row.status = "error"
        row.notes = f"precondition raised {type(exc).__name__}: {exc}"
        logger.debug(traceback.format_exc())
        return row

    row.n_targets = len(targets)
    if not targets:
        row.notes = "no targets: the rule's antecedent never fired"
        return row

    row.evidence = "direct"
    violations: list[str] = []
    undetermined: list[Undetermined] = []
    recorded: list[Target] = []

    for target in targets:
        try:
            judgement = registered.checker.pass_condition(target)
        except Exception as exc:  # noqa: BLE001
            logger.error("pass_condition of %s raised on %s: %s", registered.id, target.key, exc)
            row.status = "error"
            row.notes = f"pass_condition raised {type(exc).__name__}: {exc}"
            logger.debug(traceback.format_exc())
            row.verdict = "not_applicable"
            return row

        if isinstance(judgement, Violated):
            violations.append(f"{target.key}: {judgement.reason}")
            recorded.append(target)
        elif isinstance(judgement, Undetermined):
            undetermined.append(judgement)
        elif not isinstance(judgement, Satisfied):
            row.status = "error"
            row.notes = f"pass_condition returned {type(judgement).__name__}, not a Judgement"
            return row

    row.n_violating = len(violations)
    row.targets = [t.as_dict() for t in recorded[:MAX_RECORDED_TARGETS]]

    if violations:
        row.verdict = "fail"
        row.notes = "; ".join(violations[:5])
        if len(violations) > 5:
            row.notes += f" (+{len(violations) - 5} more)"
    elif undetermined and len(undetermined) == len(targets):
        # Nothing could be judged. Applies, but unanswerable from this bundle.
        row.verdict = "not_applicable"
        row.status = undetermined[0].status
        row.evidence = "vacuous"
        row.notes = f"undetermined on all {len(targets)} target(s): {undetermined[0].reason}"
    else:
        row.verdict = "pass"
        if undetermined:
            row.status = undetermined[0].status
            row.notes = (
                f"{len(targets) - len(undetermined)} target(s) satisfied; "
                f"{len(undetermined)} undetermined: {undetermined[0].reason}"
            )

    return row


def summarise(rows: list[ResultRow]) -> dict[str, object]:
    """Headline rate = passing / rules with at least one judged target (plan §6)."""
    judged = [r for r in rows if r.verdict in ("pass", "fail")]
    passing = [r for r in judged if r.verdict == "pass"]
    return {
        "n_rules": len(rows),
        "n_applicable": len(judged),
        "n_pass": len(passing),
        "n_fail": len(judged) - len(passing),
        "n_not_applicable": sum(1 for r in rows if r.verdict == "not_applicable"),
        "n_error": sum(1 for r in rows if r.status == "error"),
        "n_parse_error": sum(1 for r in rows if r.status == "parse_error"),
        "n_tool_missing": sum(1 for r in rows if r.status == "tool_missing"),
        "compliance_rate": round(len(passing) / len(judged), 4) if judged else None,
    }

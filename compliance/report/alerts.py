"""Automated suspicion.

Every checker defect that changed a number during development was caught
because a person looked at it and thought *"that seems wrong"* — a release-notes parser
that read every block as empty, a retrieval metric blind to runtime-assembled URLs, a
scope exclusion that swallowed `con-str-uctor`. That worked at five instances. At 306
instances across conditions it will not, and the next 76 rules are written against the
same odds.

So this module is the instrument that replaces the squint. It asserts nothing and fixes
nothing; it raises the questions a careful reader would ask, and every one of them has
already been a real bug at least once.

Two design rules, both learned the hard way.

**An alert names a suspicion, not a verdict.** A rule failing everywhere might be a
broken predicate or might be true — C078 fails 14 of 15 runs and is correct. The alert
forces the check; a human settles it.

**Silence must be earned.** The failure mode this catches is an over-narrow pre-condition:
it raises nothing, produces no odd verdict, and only shrinks the denominator. So a rule
that never judged anything is as suspicious as one that always fails.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Literal, Optional

from compliance.core.evaluation import audit as eval_audit
from compliance.core.paths import EVAL_REPORT, PATCH, RUNS_ROOT, RunDir
from compliance.core.registry import CorpusRule
from compliance.report.aggregate import Row, RuleStats, per_rule, per_run

Severity = Literal["critical", "warn", "info"]

# A rule failing this often is more likely a checker bug than universal non-compliance.
FAIL_RATE_ALERT = 0.9
# Below this many judged runs, a rate is not evidence of anything.
MIN_RUNS_FOR_RATE = 3


@dataclass(frozen=True)
class Alert:
    severity: Severity
    code: str
    subject: str
    detail: str
    action: str = ""

    def line(self) -> str:
        mark = {"critical": "!!", "warn": " !", "info": "  "}[self.severity]
        return f"{mark} [{self.code}] {self.subject}: {self.detail}"


def _corpus_get(corpus: dict[str, CorpusRule], rule_id: str) -> Optional[CorpusRule]:
    return corpus.get(rule_id)


def dead_rules(stats: dict[str, RuleStats], corpus: dict[str, CorpusRule]) -> list[Alert]:
    """A rule that judged nothing, anywhere.

    Either its pre-condition is broken, or the corpus is asking about something this
    workload never does. Both are worth knowing; only one is a bug.

    A rule is excused only when **withholding explains the whole silence** -- every run
    lacked the evidence it declared. Suppressing on *any* withheld row instead was too
    blunt by far: rules that read Python emit a `parse_error` target for a file that will
    not parse, so the four pilot runs carrying the agent's own invalid Python silenced
    every AST rule in the corpus. Thirty-two rules that judged nothing across 22 runs went
    unflagged, and the alert quietly stopped meaning what its name says.
    """
    out = []
    for rule_id, s in stats.items():
        # n_inapplicable counts runs where the rule cleanly found nothing: evidence
        # present, antecedent absent. One of those is real silence, whatever else withheld.
        if not s.never_judged or s.n_inapplicable == 0:
            continue
        meta = _corpus_get(corpus, rule_id)
        tier = f", tier={meta.check_tier}" if meta else ""
        withheld = f", {s.n_withheld} withheld" if s.n_withheld else ""
        out.append(Alert(
            "warn", "DEAD-RULE", rule_id,
            f"never judged in any of {s.n_runs} run(s) "
            f"({s.n_inapplicable} with no targets{withheld}){tier}",
            "check the pre-condition fires on the antecedent, not on the artefact (§4.2)",
        ))
    return out


def always_failing(stats: dict[str, RuleStats]) -> list[Alert]:
    out = []
    for rule_id, s in stats.items():
        if s.n_judged >= MIN_RUNS_FOR_RATE and s.fail_rate is not None \
                and s.fail_rate >= FAIL_RATE_ALERT:
            out.append(Alert(
                "warn", "ALWAYS-FAILS", rule_id,
                f"fails {s.n_fail}/{s.n_judged} judged run(s)",
                "verify against the raw evidence before reporting it as non-compliance",
            ))
    return out


def unreadable_evidence(rows: Iterable[Row]) -> list[Alert]:
    """A file the agent shipped that will not parse, kept visible as its own signal.

    Since 25 Aug these rows are graded `fail` rather than withheld, so `status` no longer
    marks them. The signal is taken from the recorded target instead: an unreadable module
    is keyed ``unreadable:<path>``, which survives into `row.targets` whenever the rule
    failed on it. Structural rather than a search through prose.

    Still worth confirming per occurrence: the agent writing invalid Python is a *finding*
    about the agent, while our parser failing on well-formed input would be a bug in us, and
    the two look identical from here.
    """
    by_rule: dict[str, int] = {}
    runs_affected: set[str] = set()
    for row in rows:
        broke = any(str(t.get("key", "")).startswith("unreadable:")
                    for t in (row.data.get("targets") or []))
        if broke or row.status == "parse_error":
            by_rule[row.rule_id] = by_rule.get(row.rule_id, 0) + 1
            # Keyed per run, attempt included: two attempts at one instance are two runs,
            # and collapsing them made the count and the list disagree.
            runs_affected.add(f"{row.instance_id}/{row.condition}/attempt{row.attempt_n}")
    if not by_rule:
        return []
    listed = sorted(runs_affected)
    shown = ", ".join(listed[:4])
    more = f", +{len(listed) - 4} more" if len(listed) > 4 else ""
    return [Alert(
        "info", "UNREADABLE", f"{len(by_rule)} rule(s)",
        f"shipped a file that will not parse, across {len(listed)} run(s): {shown}{more}",
        "confirm the source really is malformed — agent-authored invalid Python is a "
        "finding, our parser failing is a bug",
    )]


def withheld_evidence(rows: Iterable[Row]) -> list[Alert]:
    """How many rows the bundle could not answer. Reported, never graded.

    **Whether a withhold was *legitimate* is not checked here, on purpose.**
    `tests/test_check_tier.py` enforces the real invariant -- a rule may withhold only if
    something it declares in `reads` is absent from the bundle in front of it -- and it does
    so over every stored run, so a rule that gives up on evidence it holds fails the suite.

    This used to raise a `WITHHELD-TIER` critical whenever a rule withheld outside
    `CheckTier = differential`. That was the superseded tier-only invariant, and it fired on
    C002 and C003, which declare `lint_run`, genuinely lack it, and were correct. Two
    permanent false criticals pinned the exit code at 2 and taught the reader to skip the one
    severity that is supposed to stop them. Removed 23 Aug 2026; the test is the better guard
    because it asks what the rule needs rather than what column the corpus put it in.
    """
    total = sum(1 for row in rows if row.status == "tool_missing")
    if not total:
        return []
    return [Alert(
        "info", "WITHHELD", f"{total} row(s)",
        "evidence the bundle does not carry; verdicts withheld, never failed",
    )]


def retrieval_coverage(runs: Iterable[RunDir]) -> list[Alert]:
    """How much of the published guidance the retrieving arm actually reached.

    Plan §6 originally read this as *void run, exclude from the comparison* -- an agent
    that could not read the rules must not sit in the same column as one that read them
    and ignored them.

    **Settled by the team on 19 Aug 2026: a naive run that retrieves nothing is
    acceptable.** The arm is therefore read as an unaided baseline, and the retrieval
    failure is a *result* rather than a disqualification. Do not re-derive the old
    reading; it is a decision, not an oversight.

    The measurement stays, at ``info``. It is the difference between "the agent had the
    rules and ignored them" and "the agent never had them", which is what any claim about
    the naive arm rests on -- so it must be reported, just not as an error. Recorded here
    rather than dropped, because deleting the check would leave that distinction
    unmeasured and a future reader unable to tell which arm they are looking at.
    """
    out = []
    for run in runs:
        path = run.file("retrieval.json")
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if data.get("fetch_succeeded") is False:
            reached = len(data.get("source_pages_reached") or ())
            total = data.get("n_source_pages_total") or 0
            attempts = data.get("n_fetch_attempts", 0)
            out.append(Alert(
                "info", "NO-RETRIEVAL", f"{run.instance_id}/{run.condition}",
                f"reached {reached}/{total} rule pages in {attempts} fetch attempt(s), "
                f"{data.get('prose_chars_ingested', 0)} chars of prose",
                "",
            ))
    return out


def _cells(rows: Iterable[Row]) -> set[tuple[str, str]]:
    """The distinct (framework, model) pairs present. Used to decide how much to name."""
    return {(r.framework, r.model) for r in rows}


def thin_denominators(rows: Iterable[Row]) -> list[Alert]:
    """A run that activated almost nothing produces a rate that means almost nothing.

    Less work triggers fewer rules, so a lazy agent can
    post a high conditional-compliance figure off a handful of targets.
    """
    out = []
    for (framework, model, instance, condition, attempt), s in per_run(rows).items():
        if s.n_activated and s.n_activated < 0.1 * s.n_rules:
            # The cell is named only when there is more than one, so the alert stays
            # readable while a single cell exists and stays unambiguous once it does not.
            cell = f"{framework}/{model}/" if len(_cells(rows)) > 1 else ""
            out.append(Alert(
                "warn", "THIN", f"{cell}{instance}/{condition}/attempt{attempt}",
                f"only {s.n_activated} of {s.n_rules} rules could be graded "
                f"({s.n_activated / s.n_rules:.0%}); triggering {s.applicability:.0%}",
                "report applicability beside the rate; a rate over this few rules is noise",
            ))
    return out


def ungraded_runs(runs: Iterable[RunDir]) -> list[Alert]:
    """A run that finished but was never graded — it has a patch and no eval report.

    The completion marker for a run is `patch.diff`, written when the agent finishes and
    its work is collected. Grading happens *after* that, and can fail on its own — a
    corrupted shared file, a Docker refusal, a killed batch. When it does, the cell keeps
    its compliance score, counts as complete, and is skipped by every resume. **The
    functional half is lost silently.**

    That is not hypothetical: a concurrent write to a shared JSON manifest left 51 of 284
    django cells ungraded, and nothing surfaced it until someone counted by hand.

    Re-grading needs no agent run -- the patch is already stored -- so this is cheap to
    fix and worth knowing about before any functional figure is quoted.
    """
    ungraded = [r for r in runs
                if r.file(PATCH).exists() and not r.file(EVAL_REPORT).exists()]
    if not ungraded:
        return []
    sample = ", ".join(f"{r.instance_id}/{r.condition}" for r in ungraded[:3])
    return [Alert(
        "warn", "UNGRADED", f"{len(ungraded)} run(s)",
        f"finished but never graded (patch present, no eval_report.json): {sample}"
        + (" ..." if len(ungraded) > 3 else ""),
        "re-grade with tools/regrade.py; no agent run is needed, the patch is stored",
    )]


def missing_repo_cache(runs: Iterable[RunDir]) -> list[Alert]:
    """No blobless clone for this repository, so no rule that reads a file body can judge.

    `bundle/reconstruct.py` rebuilds post-patch file contents from `base_commit` + patch,
    reading base blobs out of `.cache/repos/<repo>`. Without the clone `head_text` is
    `None` for every file and every AST or file-body rule withholds -- which is correct
    behaviour (invariant 6: missing evidence is never a violation) and *looks* like a
    corpus that simply does not apply to this work.

    **This is critical, not a warning.** It cost a real batch: a repository was scored
    with no clone, 83 rows withheld for want of a file body, and the published
    applicability was 5 points low with a plausible-looking table. Nothing failed; the
    numbers were just quietly wrong. One `ensure_clone(repo)` fixes it and re-scoring is
    free.
    """
    out = []
    for run in runs:
        cache = RUNS_ROOT.parent / ".cache" / "repos" / run.repo
        if not cache.exists():
            out.append(Alert(
                "critical", "NO-REPO-CACHE", run.repo,
                f"no .cache/repos/{run.repo}: file bodies cannot be reconstructed, so every "
                f"rule reading one withholds",
                f"run ensure_clone({run.repo!r}) and re-score; scoring is free",
            ))
            break
    return out


def check(
    rows: list[Row],
    runs: list[RunDir],
    corpus: dict[str, CorpusRule],
) -> list[Alert]:
    """Every check, most severe first, then by code so the output is stable."""
    stats = per_rule(rows)
    found = [
        *missing_repo_cache(runs),
        *ungraded_runs(runs),
        *dead_rules(stats, corpus),
        *always_failing(stats),
        *unreadable_evidence(rows),
        *withheld_evidence(rows),
        *retrieval_coverage(runs),
        *thin_denominators(rows),
    ]
    order = {"critical": 0, "warn": 1, "info": 2}
    return sorted(found, key=lambda a: (order[a.severity], a.code, a.subject))

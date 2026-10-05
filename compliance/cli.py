"""compliance -- build evidence bundles and score rules over them.

    python -m compliance build-bundle <traj.json>
    python -m compliance check <traj.json> [--project sympy] [--setting native] [--jsonl out.jsonl] [--policy ID]

Offline by construction: it reads stored run artefacts and never launches an agent,
touches Docker, or reaches the network.
"""

from __future__ import annotations

import argparse
from collections import Counter
import importlib
import json
import logging
import sys
from pathlib import Path

from compliance.bundle.builder import build_bundle, bundle_to_json
from compliance.core import registry
from compliance.core.evaluation import audit as eval_audit, load as load_eval
from compliance.core.paths import ROWS, RunDir, discover, locate
from compliance import naming
from compliance.core.retrieval import analyse, analyse_rules_file, source_urls_from_corpus
from compliance.core.registry import CHECKER_VERSION
from compliance.core.runner import run_rules, summarise
from compliance.report.aggregate import (
    COMPARISON_CONDITIONS, by, comparison_rows, excluding_by_construction, load_rows,
    per_run, split_conditions, summarise as agg,
)

RULE_MODULES = {"sympy": ["compliance.rules.sympy.git_conventions",
                          "compliance.rules.sympy.pr_metadata",
                          "compliance.rules.sympy.tests",
                          "compliance.rules.sympy.specialized",
                          "compliance.rules.sympy.documentation",
                          "compliance.rules.sympy.ai_policy",
                          "compliance.rules.sympy.code_quality"],
                "django": ["compliance.rules.django.git_conventions",
                           "compliance.rules.django.pr_metadata",
                           "compliance.rules.django.tests",
                           "compliance.rules.django.specialized",
                           "compliance.rules.django.documentation",
                           "compliance.rules.django.ai_policy",
                           "compliance.rules.django.code_quality",
                           "compliance.rules.django.language_style"],
                "sphinx-doc": ["compliance.rules.sphinx_doc.pr_metadata",
                               "compliance.rules.sphinx_doc.tests",
                               "compliance.rules.sphinx_doc.specialized",
                               "compliance.rules.sphinx_doc.documentation",
                               "compliance.rules.sphinx_doc.ai_policy",
                               "compliance.rules.sphinx_doc.code_quality"],
                "pytest-dev": ["compliance.rules.pytest_dev.git_conventions",
                               "compliance.rules.pytest_dev.pr_metadata",
                               "compliance.rules.pytest_dev.tests",
                               "compliance.rules.pytest_dev.specialized",
                               "compliance.rules.pytest_dev.documentation",
                               "compliance.rules.pytest_dev.ai_policy",
                               "compliance.rules.pytest_dev.code_quality",
                               "compliance.rules.pytest_dev.language_style"],
                "pydata": ["compliance.rules.pydata.git_conventions",
                           "compliance.rules.pydata.pr_metadata",
                           "compliance.rules.pydata.tests",
                           "compliance.rules.pydata.specialized",
                           "compliance.rules.pydata.documentation",
                           "compliance.rules.pydata.ai_policy",
                           "compliance.rules.pydata.code_quality",
                           "compliance.rules.pydata.language_style"],
                "psf": ["compliance.rules.psf.ai_policy",
                        "compliance.rules.psf.code_quality",
                        "compliance.rules.psf.documentation",
                        "compliance.rules.psf.git_conventions",
                        "compliance.rules.psf.language_style",
                        "compliance.rules.psf.tests"],
                "mwaskom": ["compliance.rules.mwaskom.code_quality",
                            "compliance.rules.mwaskom.tests"],
                "pallets": ["compliance.rules.pallets.ai_policy",
                            "compliance.rules.pallets.code_quality",
                            "compliance.rules.pallets.documentation",
                            "compliance.rules.pallets.git_conventions",
                            "compliance.rules.pallets.pr_metadata",
                            "compliance.rules.pallets.tests"],
                "pylint-dev": ["compliance.rules.pylint_dev.ai_policy",
                               "compliance.rules.pylint_dev.code_quality",
                               "compliance.rules.pylint_dev.git_conventions",
                               "compliance.rules.pylint_dev.language_style",
                               "compliance.rules.pylint_dev.pr_metadata",
                               "compliance.rules.pylint_dev.specialized",
                               "compliance.rules.pylint_dev.tests"],
                "astropy": ["compliance.rules.astropy.ai_policy",
                            "compliance.rules.astropy.code_quality",
                            "compliance.rules.astropy.documentation",
                            "compliance.rules.astropy.git_conventions",
                            "compliance.rules.astropy.language_style",
                            "compliance.rules.astropy.pr_metadata",
                            "compliance.rules.astropy.specialized",
                            "compliance.rules.astropy.tests"],
                "scikit-learn": ["compliance.rules.scikit_learn.ai_policy",
                                 "compliance.rules.scikit_learn.code_quality",
                                 "compliance.rules.scikit_learn.documentation",
                                 "compliance.rules.scikit_learn.git_conventions",
                                 "compliance.rules.scikit_learn.language_style",
                                 "compliance.rules.scikit_learn.pr_metadata",
                                 "compliance.rules.scikit_learn.specialized",
                                 "compliance.rules.scikit_learn.tests"],
                "matplotlib": ["compliance.rules.matplotlib.ai_policy",
                               "compliance.rules.matplotlib.code_quality",
                               "compliance.rules.matplotlib.documentation",
                               "compliance.rules.matplotlib.git_conventions",
                               "compliance.rules.matplotlib.language_style",
                               "compliance.rules.matplotlib.pr_metadata",
                               "compliance.rules.matplotlib.specialized",
                               "compliance.rules.matplotlib.tests"]}


def load_rule_modules(repo: str) -> None:
    for module in RULE_MODULES.get(repo, []):
        importlib.import_module(module)


def _fmt(value: object, width: int) -> str:
    text = "" if value is None else str(value)
    return text[:width].ljust(width)


def cmd_build_bundle(args: argparse.Namespace) -> int:
    bundle = build_bundle(args.trajectory, condition=args.condition, model=args.model,
                          framework=getattr(args, "framework", None))
    print(bundle_to_json(bundle))
    return 0


def cmd_retrieval(args: argparse.Namespace) -> int:
    """What did the agent actually manage to read?"""
    corpus = registry.load_corpus(args.corpus or registry.corpus_path_for(args.repo))
    sources = source_urls_from_corpus(corpus)
    traj_path, _ = _resolve_trajectory(args)
    bundle = build_bundle(traj_path, framework=getattr(args, "framework", None))
    r = analyse(bundle, sources)

    print(f"\n{bundle.instance_id}  setting={naming.SETTINGS.get(bundle.condition, bundle.condition)}")
    print(f"  entry url            {r.entry_url or '(none recorded)'}")
    print(f"  fetch attempts       {r.n_fetch_attempts}  (of {r.n_commands} commands)")
    print(f"  strategies           {', '.join(r.strategies) or '-'}")
    print(f"  followed beyond entry{'  yes' if r.followed_beyond_entry else '  NO'}")
    print(f"  rule pages reached   {len(r.source_pages_reached)}/{r.n_source_pages_total}"
          f"  ({r.coverage:.0%} of the pages the corpus was drawn from)")
    print(f"  prose ingested       {r.prose_chars_ingested:,} chars")
    print(f"  fetch_succeeded      {r.fetch_succeeded}")
    if bundle.condition == "naive" and not r.fetch_succeeded:
        print("\n  ALERT: naive run with no guideline prose ingested.")
        print("         Per plan §6 this run is VOID, not a low compliance score.")
    for url in r.urls_fetched:
        print(f"    fetched: {url}")

    # guided arm: the treatment is a mounted file, and it can go unconsumed the same way
    g = analyse_rules_file(bundle)
    if g.present or bundle.condition == "guided":
        print(f"\n  rules file          {g.path}")
        print(f"  mounted             {'yes' if g.present else 'NO'}"
              f"   ({g.file_chars:,} chars)" if g.file_chars else "")
        print(f"  opened              {'yes' if g.opened else 'NO'}"
              f"  ({g.n_reads} read(s), {'re-read' if g.re_read else 'read once' if g.n_reads else '-'})")
        print(f"  first / last read   step {g.first_read_step} / {g.last_read_step}")
        print(f"  chars ingested      {g.chars_ingested:,} of {g.file_chars:,}  ({g.coverage:.0%})")
        print(f"  truncated reads     {g.truncated_reads}")
        print(f"  strategies          {', '.join(g.strategies) or '-'}")
        for c in g.read_commands:
            print(f"    {c}")
        if bundle.condition == "guided" and not g.opened:
            print("\n  ALERT: guided run that never opened the mounted rules file.")
            print("         The treatment was available but not consumed -- void, exactly as")
            print("         a naive run that never fetched. Do not score it as low compliance.")
    print()
    return 0


def cmd_runs(args: argparse.Namespace) -> int:
    """List the run corpus: what has been collected, per repo/instance/condition."""
    runs = discover(repo=args.repo)
    if not runs:
        print("no runs found under runs/", file=sys.stderr)
        return 1
    print(f"\n  {_fmt('REPO', 10)} {_fmt('INSTANCE', 24)} {_fmt('CONDITION', 11)} {'ATT':>3}  "
          f"{'COMPLIANCE':10} FUNCTIONAL")
    print("  " + "-" * 78)
    for run in runs:
        report = load_eval(run)
        if report.shape == "instance":
            functional = f"{'resolved' if report.resolved else 'unresolved':11}({report.n_outcomes} tests)"
        elif report.shape == "summary":
            functional = "UNUSABLE   (run-level summary, may be another run's)"
        elif report.shape == "not_gradeable":
            functional = "empty patch (no result possible)"
        elif report.shape == "absent":
            functional = "NOT GRADED"
        else:
            functional = f"UNREADABLE ({report.note[:30]})"
        print(
            f"  {_fmt(run.repo, 10)} {_fmt(run.instance_id, 24)} {_fmt(run.condition, 11)} "
            f"{run.attempt:>3}  {'scored' if run.file(ROWS).exists() else '-':10} {functional}"
        )
    conditions = sorted({r.condition for r in runs})
    print(f"\n  {len(runs)} run(s), {len({r.instance_id for r in runs})} instance(s), "
          f"conditions: {', '.join(conditions)}")

    # The functional half is easy to lose silently: a stale run-level summary looks like
    # a graded run and answers nothing. Say so here rather than let it be discovered in
    # a half-empty 2x2 (docs/checker-authoring.md §9).
    if problems := eval_audit(runs):
        print(f"\n  ALERT: {len(problems)} run(s) carry no usable functional result.")
        print("         The resolved x compliant table cannot be built for these.")
        print("         Repair with: scripts/evaluate.sh <instance_id> <run_dir>")
        for run, report in problems:
            print(f"           {run.instance_id} {run.condition}/attempt{run.attempt}: {report.shape}")
    print()
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Aggregate the scored corpus and raise every suspicion the §6 table calls for."""
    from compliance.report.alerts import check

    runs = discover(repo=args.repo, framework=args.framework, model=args.model,
                    attempt=getattr(args, "attempt", None))
    all_rows = load_rows(runs)
    if not all_rows:
        print("no scored runs found -- run `compliance check` first", file=sys.stderr)
        return 1
    # Pooling cells is almost never what a reader wants: runs from different models or
    # frameworks answer different questions, and a single percentage over all of them
    # describes none of them. Say which cells are in the number, always.
    # A cell run more than once contributes once PER ATTEMPT to every figure below, so
    # those instances carry 2-3x the weight of the others. Sometimes that is wanted
    # (replicates); often it is not (a re-run under a changed treatment, or a control).
    # The report cannot tell which, so it says so rather than choosing.
    repeats = Counter((r.framework, r.model, r.instance_id, r.condition) for r in all_rows
                      if r.condition in COMPARISON_CONDITIONS)
    repeated = {k: n for k, n in repeats.items() if n > len({r.rule_id for r in all_rows
                                                            if (r.framework, r.model, r.instance_id,
                                                                r.condition) == k}) }
    multi = sorted({(k[1], k[2], k[3]) for k, n in repeats.items()
                    if n > len({r.rule_id for r in all_rows
                                if (r.framework, r.model, r.instance_id, r.condition) == k})})
    if multi:
        print(f"\n  !! {len(multi)} cell(s) have MORE THAN ONE ATTEMPT and are counted once per")
        print( "     attempt, so those instances carry extra weight. Narrow with --attempt,")
        print( "     or check each run's probe.txt for the conditions each attempt ran under:")
        for model, instance, condition in multi[:6]:
            print(f"       {model} / {instance} / {condition}")
        if len(multi) > 6:
            print(f"       ... and {len(multi) - 6} more")

    cells = sorted({(r.framework, r.model) for r in all_rows})
    if len(cells) > 1:
        print(f"\n  !! POOLING {len(cells)} CELLS -- narrow with --model / --framework:")
        for fw, md in cells:
            print(f"       {fw} / {md}")
    else:
        print(f"\n  cell: {cells[0][0]} / {cells[0][1]}")
    corpus = registry.load_corpus(args.corpus or registry.corpus_path_for(args.repo))

    # Only the two arms of the primary comparison are reported, and that includes the
    # alerts. `naive-salient` is a variant of the control and the pre-Phase-0 `unknown`
    # runs recorded no condition at all; pooling either into a count of dead rules or
    # withheld rows attributes the instrument's coverage to runs the study does not claim.
    # The rows stay on disk -- `compliance check` still writes them -- they are simply not
    # aggregated here.
    rows = comparison_rows(all_rows)
    if not rows:
        print(f"no rows in the comparison arms ({', '.join(COMPARISON_CONDITIONS)})",
              file=sys.stderr)
        return 1
    runs = [r for r in runs if r.condition in COMPARISON_CONDITIONS]

    dropped = len(all_rows) - len(rows)
    n_runs = len({(r.instance_id, r.condition, r.attempt_n) for r in rows})
    print(f"\n  {len(rows)} scored rule-instances over {n_runs} run(s)")
    if dropped:
        excluded = sorted({r.condition for r in all_rows} - set(COMPARISON_CONDITIONS))
        print(f"  {dropped} row(s) excluded -- not a comparison arm: {', '.join(excluded)}")
    print()

    comparison, _ = split_conditions(rows)
    header = (f"  {'group':16} {'applicability':>13} {'conditional':>12} {'pass':>5} "
              f"{'fail':>5} {'n/a':>5}")

    def line(name: str, group) -> str:
        conditional = (f"{group.conditional_compliance:>11.0%}"
                       if group.conditional_compliance is not None else f"{'-':>11}")
        return (f"  {name:16} {group.applicability:>12.0%} {conditional} "
                f"{group.n_pass:>5} {group.n_fail:>5} {group.n_inapplicable:>5}")

    # The pair, never the rate alone: less work triggers fewer rules.
    print(f"  THE COMPARISON  ({', '.join(COMPARISON_CONDITIONS)})")
    print(header)
    print("  " + "-" * 62)
    print(line("all arms", agg(comparison_rows(rows))))
    for name, group in comparison.items():
        print(line(name, group))

    # Withheld rows are reported BELOW the comparison, never as a column of it. They are
    # a subset of `n/a` -- the rule applied but the bundle could not answer it -- so a
    # column would read as a fourth outcome and would not sum with the others. It is a
    # statement about the instrument's coverage, not about the agent's conduct, and the
    # two do not belong in one table.
    withheld = {name: g.n_withheld for name, g in comparison.items() if g.n_withheld}
    if withheld:
        total = sum(withheld.values())
        per_arm = ", ".join(f"{n} {name}" for name, n in sorted(withheld.items()))
        print(f"\n  ({total} of the n/a rows are WITHHELD -- the rule applied, the evidence "
              f"was missing: {per_arm}.")
        print(f"   Not a verdict about the agent; see the coverage section below.)")

    # Plan §7: a handful of rules cannot be passed by any autonomous agent, so a fail is a
    # tautology. Reported both ways, because excluding them silently would overstate
    # compliance and including them silently would understate it.
    if tautological := [r for r in comparison_rows(rows) if r.by_construction]:
        ids = sorted({r.rule_id for r in tautological})
        print(f"\n  EXCLUDING RULES NO AUTONOMOUS AGENT CAN PASS  ({', '.join(ids)})")
        print(header)
        print("  " + "-" * 68)
        without = excluding_by_construction(comparison_rows(rows))
        print(line("all arms", agg(without)))
        for name, group in split_conditions(without)[0].items():
            print(line(name, group))

    print("\n  applicability = share of the batch the work activated; itself a compliance")
    print("  signal. conditional = of those, how many passed. Reporting either alone is")
    print("  how an agent that does less scores higher.\n")

    print(f"\n  BY CATEGORY  (comparison arms only)")
    print(f"  {'category':34} {'applicability':>13} {'conditional':>12}")
    print("  " + "-" * 62)
    for name, group in by(comparison_rows(rows), "shared_category").items():
        print(f"  {name:34} {group.applicability:>12.0%} {group.conditional_compliance:>11.0%}"
              if group.n_activated else f"  {name:34} {group.applicability:>12.0%} {'-':>12}")

    alerts = check(rows, runs, corpus)
    print(f"\n  {len(alerts)} alert(s)\n")
    _print_alerts(alerts)
    return 0 if not any(a.severity == "critical" for a in alerts) else 2


# Beyond this many alerts of one kind the individual lines stop being read at all, and an
# alert table nobody reads is the same as no alert table -- the C4 lesson, that a guard
# which cries wolf gets deleted. Collapsing is a rendering decision and lives here, so
# `alerts.py` keeps raising one suspicion per subject and stays testable per rule.
ALERT_COLLAPSE_AT = 12
SUBJECTS_SHOWN = 6


def _print_alerts(alerts) -> None:
    from itertools import groupby

    ordered = sorted(alerts, key=lambda a: (a.code, a.subject))
    for code, group in groupby(ordered, key=lambda a: a.code):
        items = list(group)
        first = items[0]
        if len(items) <= ALERT_COLLAPSE_AT:
            for alert in items:
                print(f"  {alert.line()}")
                if alert.action and alert.severity != "info":
                    print(f"       -> {alert.action}")
            continue
        mark = {"critical": "!!", "warn": " !", "info": "  "}[first.severity]
        shown = ", ".join(a.subject for a in items[:SUBJECTS_SHOWN])
        print(f"  {mark} [{code}] x{len(items)}")
        print(f"       {shown}, +{len(items) - SUBJECTS_SHOWN} more")
        print(f"       e.g. {first.subject}: {first.detail}")
        if first.action and first.severity != "info":
            print(f"       -> {first.action}")
    print()


def _resolve_trajectory(args: argparse.Namespace) -> tuple[Path, RunDir | None]:
    """Accept either a trajectory path or --instance/--condition against runs/.

    A run now lives in a (framework, model) cell, so an instance and condition need not
    identify one run. Rather than construct a path and hope, this searches and reports
    what it found: nothing, exactly one, or several with the flags that would separate
    them. Constructing the path was fine while one cell existed and would have started
    silently missing runs the moment a second did.
    """
    if args.trajectory:
        return Path(args.trajectory), None
    if not args.instance:
        raise SystemExit("give a trajectory path, or --instance (with --condition)")
    condition = args.condition or "naive"
    found = locate(args.instance, condition, args.attempt,
                   framework=getattr(args, "framework", None),
                   model=getattr(args, "model", None))
    if not found:
        raise SystemExit(
            f"no stored run for {args.instance} / {condition} / attempt{args.attempt}"
            + (f" in {args.framework}/{args.model}" if getattr(args, "framework", None) else "")
        )
    if len(found) > 1:
        cells = "\n  ".join(f"--framework {r.framework} --model {r.model}" for r in found)
        raise SystemExit(
            f"{len(found)} runs match {args.instance} / {condition} / attempt{args.attempt}."
            f" Say which:\n  {cells}"
        )
    return found[0].trajectory, found[0]


def cmd_check(args: argparse.Namespace) -> int:
    load_rule_modules(args.repo)
    corpus = registry.load_corpus(args.corpus or registry.corpus_path_for(args.repo))
    rules = registry.registered(ids=args.rule or None)
    if not rules:
        print(f"no rules registered for repo {args.repo!r}", file=sys.stderr)
        return 2

    traj_path, run = _resolve_trajectory(args)
    bundle = build_bundle(traj_path, condition=args.condition, model=args.model,
                          framework=args.framework)
    rows = run_rules(bundle, rules, corpus, checker_version=CHECKER_VERSION)

    print(f"\n{bundle.instance_id}  setting={naming.SETTINGS.get(bundle.condition, bundle.condition)}  model={bundle.model}")
    print(
        f"  commits={len(bundle.commits)} (source: {bundle.commits_source})  "
        f"committed files={len(bundle.files)} of {len(bundle.files_worktree)} in tree "
        f"({bundle.patch_scope})  commands={len(bundle.commands)}  "
        f"pr_text={'yes' if bundle.pr_text else 'no'}"
    )
    for note in bundle.notes:
        print(f"  note: {note}")

    print(f"\n  {_fmt('RULE', 13)} {_fmt('VERDICT', 15)} {_fmt('STATUS', 12)} {'TGT':>4} {'VIO':>4}  NOTES")
    print("  " + "-" * 104)
    for row in rows:
        print(
            f"  {_fmt(row.rule_id, 13)} {_fmt(row.verdict, 15)} {_fmt(row.status, 12)} "
            f"{row.n_targets:>4} {row.n_violating:>4}  {row.notes[:44]}"
        )

    stats = summarise(rows)
    rate = stats["compliance_rate"]
    print(
        f"\n  {stats['n_applicable']}/{stats['n_rules']} graded  "
        f"pass={stats['n_pass']} fail={stats['n_fail']} "
        f"not_triggered={stats['n_not_applicable']} parse_error={stats['n_parse_error']} "
        f"error={stats['n_error']}"
    )
    print(f"  compliance rate: {'n/a' if rate is None else f'{rate:.1%}'}\n")

    # Rows land beside the run they describe, so a run is archivable as a unit.
    if run is not None:
        run.file(ROWS).write_text(
            "".join(json.dumps(r.as_dict(), sort_keys=True) + "\n" for r in rows), encoding="utf-8"
        )
        print(f"  wrote {len(rows)} rows to {run.file(ROWS).relative_to(Path.cwd())}\n")

    if args.jsonl:
        path = Path(args.jsonl)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row.as_dict(), sort_keys=True) + "\n")
        print(f"  wrote {len(rows)} rows to {path}\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="compliance", description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true", help="show shim and parser warnings")
    sub = parser.add_subparsers(dest="command", required=True)

    ret = sub.add_parser("retrieval", help="what policy text reached the agent (Table 5)")
    ret.add_argument("trajectory", nargs="?")
    ret.add_argument("--instance")
    ret.add_argument("--setting", "--condition", dest="condition", metavar="SETTING", help="native | consolidated")
    ret.add_argument("--attempt", type=int, default=1)
    ret.add_argument("--scaffold", "--framework", dest="framework", metavar="SCAFFOLD", help="scaffold that wrote the trajectory: mini-swe-agent | openhands | own-agent")
    ret.add_argument("--model", help="narrow to one model slug")
    ret.add_argument("--project", "--repo", dest="repo", default="sympy", metavar="PROJECT", help="project name (e.g. flask) or SWE-bench prefix (e.g. pallets)")
    ret.add_argument("--corpus")
    ret.set_defaults(func=cmd_retrieval)

    report = sub.add_parser("report", help="aggregate the scored corpus and raise alerts")
    report.add_argument("--project", "--repo", dest="repo", default="sympy", metavar="PROJECT", help="project name (e.g. flask) or SWE-bench prefix (e.g. pallets)")
    report.add_argument("--scaffold", "--framework", dest="framework", metavar="SCAFFOLD", help="only this scaffold: mini-swe-agent | openhands")
    report.add_argument("--model", help="only this model slug")
    report.add_argument("--attempt", type=int,
                        help="only this attempt number, when a cell was run more than once")
    report.add_argument("--corpus")
    report.set_defaults(func=cmd_report)

    listing = sub.add_parser("runs", help="list the collected run corpus")
    listing.add_argument("--project", "--repo", dest="repo", metavar="PROJECT", help="only this project")
    listing.set_defaults(func=cmd_runs)

    build = sub.add_parser("build-bundle", help="parse a trajectory into an evidence bundle")
    build.add_argument("trajectory")
    build.add_argument("--setting", "--condition", dest="condition", metavar="SETTING", help="native | consolidated")
    build.add_argument("--scaffold", "--framework", dest="framework", metavar="SCAFFOLD",
                       help="scaffold that wrote the trajectory: mini-swe-agent | openhands | own-agent")
    build.add_argument("--model-id", dest="model",
                       help="litellm id to record in the bundle, e.g. openrouter/qwen/qwen3-coder")
    build.set_defaults(func=cmd_build_bundle)

    check = sub.add_parser("check", help="score a project's policies over one trajectory")
    check.add_argument("trajectory", nargs="?", help="path; or use --instance instead")
    check.add_argument("--instance", help="instance id, resolved against runs/")
    check.add_argument("--attempt", type=int, default=1)
    check.add_argument("--scaffold", "--framework", dest="framework", metavar="SCAFFOLD", help="scaffold that wrote the trajectory: mini-swe-agent | openhands | own-agent")
    check.add_argument("--model", help="narrow to one model slug")
    check.add_argument("--project", "--repo", dest="repo", default="sympy", metavar="PROJECT", help="project name (e.g. flask) or SWE-bench prefix (e.g. pallets)")
    check.add_argument("--corpus", help="override the corpus CSV from repo.conf")
    check.add_argument("--policy", "--rule", dest="rule", metavar="POLICY_ID", action="append", help="only this policy id (repeatable)")
    check.add_argument("--jsonl", help="append ResultRows as JSONL")
    check.add_argument("--setting", "--condition", dest="condition", metavar="SETTING", help="native | consolidated")
    check.add_argument("--model-id", dest="model_id",
                       help="litellm id to record in the bundle; --model selects which "
                            "stored cell to read")
    check.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    # User-facing names follow the paper; the code underneath keeps its own identifiers.
    if getattr(args, "repo", None):
        args.repo = naming.project_slug(args.repo)
    if hasattr(args, "condition"):
        args.condition = naming.condition(args.condition)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.ERROR,
        format="%(levelname)s %(name)s: %(message)s",
    )
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

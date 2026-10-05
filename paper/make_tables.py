#!/usr/bin/env python3
"""Regenerate every data table and figure in the paper from the released results.

    python paper/make_tables.py                 # all tables and figures
    python paper/make_tables.py --only table3   # one item
    python paper/make_tables.py --no-figures    # skip matplotlib

Reads `paper/results/` and the policy corpora under `rules/`. Writes
`paper/tables/<item>.csv` and `paper/figures/<item>.pdf`, and prints each table.
Metric definitions are in `compliance/report/results.py`.
"""
from __future__ import annotations

import argparse
import csv
import statistics
from decimal import ROUND_HALF_UP, Decimal
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compliance import naming  # noqa: E402
from compliance.report import results  # noqa: E402
from compliance.report.results import cell, pooled, rates  # noqa: E402

HERE = Path(__file__).resolve().parent
RESULTS, TABLES_PATH, FIGURES = HERE / "results", HERE / "tables", HERE / "figures"
SCAFFOLDS = ("mini-swe-agent", "openhands")
SETTINGS = ("native", "consolidated")
MODELS = {"gpt-5.6-luna": "GPT-5.6 Luna", "gemini-3.7-flash": "Gemini 3.7 Flash",
          "deepseek-v4-flash-0731": "DeepSeek V4 Flash", "kimi-k2.5": "Kimi K2.5"}
CATEGORIES = ("Git and commit conventions", "PR and release metadata", "Code and quality",
              "AI-assisted contribution policy", "Tests and test style",
              "Language and framework style", "Specialized changes",
              "Documentation and docstrings")
# Public SWE-bench Verified resolve rates under mini-SWE-agent (Vals AI, 2026), Table 13.
VALS_AI = {"gpt-5.6-luna": 93.0, "gemini-3.7-flash": 80.8,
           "deepseek-v4-flash-0731": 88.8, "kimi-k2.5": 70.0}
# The example policy quoted for each category in Table 7.
TABLE7_IDS = {"Documentation and docstrings": "ASTROPY-C085",
              "Language and framework style": "ASTROPY-C100",
              "Tests and test style": "ASTROPY-C002", "Specialized changes": "ASTROPY-C092",
              "PR and release metadata": "ASTROPY-C061",
              "Git and commit conventions": "DJANGO-C046",
              "AI-assisted contribution policy": "DJANGO-C057",
              "Code and quality": "DJANGO-C069"}


# ---------------------------------------------------------------------------- data

def load():
    return results.load(RESULTS)


def pct(x) -> str:
    return "--" if x is None else f"{x:.1f}"


# ---------------------------------------------------------------------------- tables

def table2(runs, pol):
    n = Counter(p["category"] for p in pol.values())
    total = sum(n.values())
    return ["Category", "Policies", "%"], [
        [c, n[c], f"{100 * n[c] / total:.0f}"] for c, _ in n.most_common()] + [["Total", total, ""]]


def r1(x: float) -> float:
    """Round half up to one decimal, as printed in the paper."""
    return float(Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def table3(runs, pol):
    """Each cell is rounded to one decimal first; deltas and averages are then computed
    from the rounded values, and the Average row's delta is the difference of the two
    rounded averages -- the paper's convention."""
    head = ["Setting", "Model"] + [f"{s} {m}" for s in SCAFFOLDS
                                   for m in ("triggering", "compliance", "resolve")]
    vals: dict[tuple, list[float]] = {}
    for setting in SETTINGS:
        for model in MODELS:
            for s in SCAFFOLDS:
                rs = cell(runs, scaffold=s, model=model, setting=setting)
                if rs:
                    r = rates(pooled(rs))
                    vals[(setting, model, s)] = [r1(r["triggering"]), r1(r["compliance"]),
                                                 r1(results.resolve_rate(rs))]
    avg = {(t, s): [r1(statistics.mean(v[(t, m, s)][i] for m in MODELS if (t, m, s) in v))
                    for i in range(3)]
           for t in SETTINGS for s in SCAFFOLDS for v in [vals]}
    body = []
    for setting in SETTINGS:
        rows = [(name, {s: vals.get((setting, m, s)) for s in SCAFFOLDS},
                 {s: vals.get(("native", m, s)) for s in SCAFFOLDS}) for m, name in MODELS.items()]
        rows.append(("Average", {s: avg[(setting, s)] for s in SCAFFOLDS},
                     {s: avg[("native", s)] for s in SCAFFOLDS}))
        for name, cur, base in rows:
            line = [setting, name]
            for s in SCAFFOLDS:
                if cur[s] is None:
                    line += ["--"] * 3
                elif setting == "native":
                    line += [f"{v:.1f}" for v in cur[s]]
                else:
                    line += [f"{v:.1f} ({r1(v - b):+.1f})" for v, b in zip(cur[s], base[s])]
            body.append(line)
    return head, body


def table4(runs, pol):
    head = ["Category", "Rate"] + [f"{s} {t}" for s in SCAFFOLDS for t in SETTINGS]
    body = []
    for c in CATEGORIES:
        keep = lambda pid, c=c: pol[pid]["category"] == c  # noqa: E731
        rs = {(s, t): rates(pooled(cell(runs, scaffold=s, setting=t), keep))
              for s in SCAFFOLDS for t in SETTINGS}
        for metric in ("triggering", "compliance"):
            body.append([c, metric] + [pct(rs[(s, t)][metric]) for s in SCAFFOLDS for t in SETTINGS])
    return head, body


def table5(runs, pol):
    head = ["Model", "Scaffold", "Attempt", "Retrieve", "Opened", "Delivered"]
    body, cols = [], defaultdict(list)
    order = ("gpt-5.6-luna", "deepseek-v4-flash-0731", "gemini-3.7-flash", "kimi-k2.5")
    for model, name in sorted(MODELS.items(), key=lambda kv: (order + (kv[0],)).index(kv[0])):
        for s in SCAFFOLDS:
            nat = cell(runs, model=model, scaffold=s, setting="native")
            con = cell(runs, model=model, scaffold=s, setting="consolidated")
            if not nat or not con:
                continue
            opened = [r for r in con if r["opened"] == "1"]
            vals = [100 * sum(r["attempted"] == "1" for r in nat) / len(nat),
                    100 * sum(r["retrieved"] == "1" for r in nat) / len(nat),
                    100 * len(opened) / len(con),
                    100 * statistics.mean(float(r["delivered"]) for r in opened if r["delivered"])]
            for i, v in enumerate(vals):
                cols[i].append(v)
            body.append([name, s] + [f"{v:.1f}" for v in vals])
    body.append(["Average", ""] + [f"{statistics.mean(cols[i]):.1f}" for i in range(4)])
    return head, body


def table6(runs, pol):
    from compliance.core import registry

    head = ["project", "instances", "extracted", "in scope", "binding",
            "output", "differential", "trajectory", "approx."]
    body, tot = [], Counter()
    instances = defaultdict(set)
    for r in runs:
        instances[r["project"]].add(r["instance_id"])
    order = ("astropy django matplotlib scikit-learn sympy pylint xarray flask sphinx "
             "pytest requests seaborn").split()
    for project in order:
        corpus = registry.load_corpus(registry.corpus_path_for(naming.project_slug(project)))
        ps = [p for p in pol.values() if p["project"] == project]
        ev = Counter(p["evidence_type"] for p in ps)
        approx = sum(p["check"] == "approximate" for p in ps)
        vals = {"instances": len(instances[project]), "extracted": len(corpus),
                "in scope": sum(r.care for r in corpus.values()), "binding": len(ps),
                "output": ev["output"], "differential": ev["differential"],
                "trajectory": ev["trajectory"], "approx": approx}
        tot.update(vals)
        body.append([project] + [vals[k] for k in list(vals)[:-1]] + [f"{100 * approx / len(ps):.0f}%"])
    body.append(["total"] + [tot[k] for k in list(vals)[:-1]]
                + [f"{100 * tot['approx'] / tot['binding']:.0f}%"])
    return head, body


def table7(runs, pol):
    n = Counter(p["category"] for p in pol.values())
    return ["Category", "#", "Example policy", "ID"], [
        [c, n[c], pol[pid]["policy"], pid] for c, pid in
        sorted(TABLE7_IDS.items(), key=lambda kv: -n[kv[0]])]


def table8(runs, pol):
    head = ["Scaffold", "Model", "Native all", "Native exact", "Consolidated all",
            "Consolidated exact", "Delta all", "Delta exact"]
    exact = lambda pid: pol[pid]["check"] == "exact"  # noqa: E731
    body = []
    for s in SCAFFOLDS:
        for model, name in MODELS.items():
            if not cell(runs, scaffold=s, model=model):
                continue
            v = {}
            for t in SETTINGS:
                rs = cell(runs, scaffold=s, model=model, setting=t)
                v[(t, "all")] = rates(pooled(rs))["compliance"]
                v[(t, "exact")] = rates(pooled(rs, exact))["compliance"]
            v = {k: r1(x) for k, x in v.items()}
            body.append([s, name] + [f"{v[(t, k)]:.1f}" for t in SETTINGS for k in ("all", "exact")]
                        + [f"{r1(v[('consolidated', k)] - v[('native', k)]):.1f}" for k in ("all", "exact")])
    return head, body


def table13(runs, pol):
    body = []
    for model, name in MODELS.items():
        rs = cell(runs, scaffold="mini-swe-agent", model=model, setting="native")
        if not rs or model not in VALS_AI:
            continue
        ours = 100 * sum(r["resolved"] == "1" for r in rs) / len(rs)
        body.append([name, f"{ours:.1f}", f"{VALS_AI[model]:.1f}", f"{ours - VALS_AI[model]:+.1f}"])
    return ["Model", "Ours (Native)", "Vals AI", "Delta"], body


def table14(runs, pol):
    triggered = {p for r in runs for p, o in r["outcomes"] if o != "not_triggered"}
    n = Counter(p["category"] for p in pol.values())
    never = Counter(p["category"] for pid, p in pol.items() if pid not in triggered)
    body = [[c, n[c], never[c], f"{100 * never[c] / n[c]:.0f}%"]
            for c in sorted(n, key=lambda c: -never[c] / n[c])]
    body.append(["Total", sum(n.values()), sum(never.values()),
                 f"{100 * sum(never.values()) / sum(n.values()):.0f}%"])
    return ["Category", "Policies", "Never triggered", "Share"], body


def table15(runs, pol):
    head = ["Category", "Scaffold", "Native triggered", "Native graded",
            "Consolidated triggered", "Consolidated graded"]
    body = []
    for c in CATEGORIES:
        keep = lambda pid, c=c: pol[pid]["category"] == c  # noqa: E731
        for s in SCAFFOLDS:
            line = [c, s]
            for t in SETTINGS:
                r = rates(pooled(cell(runs, scaffold=s, setting=t), keep))
                line += [r["triggered"], r["graded"]]
            body.append(line)
    return head, body


# ---------------------------------------------------------------------------- figures

def figure3(runs, pol, plt):
    n = Counter(p["project"] for p in pol.values())
    total = sum(n.values())
    items = n.most_common()
    fig, ax = plt.subplots(figsize=(4.2, 3.4))
    ax.pie([v for _, v in items], labels=[k for k, _ in items], startangle=90,
           counterclock=False, autopct=lambda p: f"{p:.1f}%", pctdistance=0.8,
           textprops={"fontsize": 7}, wedgeprops={"linewidth": 1, "edgecolor": "white"})
    ax.set_title(f"Policy Distribution by Project (n = {total})", fontsize=9)
    return fig, ["project", "policies", "%"], [[k, v, f"{100 * v / total:.1f}"] for k, v in items]


def _resolving_violations(runs):
    per = {t: Counter() for t in SETTINGS}
    for r in runs:
        if r["resolved"] == "1":
            per[r["setting"]][sum(o == "fail" for _, o in r["outcomes"])] += 1
    return per


def figure4(runs, pol, plt):
    import numpy as np

    per, cut = _resolving_violations(runs), 15
    fig, ax = plt.subplots(figsize=(5.5, 2.35))
    x, rows = np.arange(cut + 1), []
    for i, (t, color) in enumerate((("native", "#2a78d6"), ("consolidated", "#eb6834"))):
        h, n = per[t], sum(per[t].values())
        share = [100 * h[k] / n for k in range(cut)] + [100 * sum(v for k, v in h.items() if k >= cut) / n]
        mean = sum(k * v for k, v in h.items()) / n
        ax.bar(x + (i - 0.5) * 0.4, share, 0.4, label=t.capitalize(), color=color)
        ax.axvline(mean, color=color, lw=1, ls="--")
        ax.annotate(f"mean {mean:.1f}", (mean, 22), color=color, fontsize=7, ha="center")
        rows.append([t, n, f"{mean:.2f}"] + share)
    ax.set_xticks(x, [str(k) for k in range(cut)] + [f"{cut}+"])
    ax.set_xlabel("Policies violated in a run")
    ax.set_ylabel("Resolving runs (%)")
    ax.legend(frameon=False)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    triggered = [sum(o != "not_triggered" for _, o in r["outcomes"])
                 for r in runs if r["resolved"] == "1"]
    head = ["setting", "resolving runs", "mean violations"] + [str(k) for k in range(cut)] + [f"{cut}+"]
    rows.append(["mean triggered per resolving run", len(triggered),
                 f"{statistics.mean(triggered):.1f}"] + [""] * (cut + 1))
    return fig, head, rows


def figure5(runs, pol, plt):
    n = Counter()
    for r in runs:
        if r["resolved"] == "1":
            for p, o in r["outcomes"]:
                if o == "fail":
                    n["Trajectory" if pol[p]["evidence_type"] == "trajectory"
                      else "Final deliverables"] += 1
    total = sum(n.values())
    items = [("Final deliverables", n["Final deliverables"]), ("Trajectory", n["Trajectory"])]
    fig, ax = plt.subplots(figsize=(3.2, 3.2))
    ax.pie([v for _, v in items], labels=[k for k, _ in items], startangle=90,
           counterclock=False, autopct="%.1f%%", colors=["#6cc49a", "#8c7fd0"],
           wedgeprops={"linewidth": 1, "edgecolor": "white"})
    ax.set_title("Violations by Evidence", fontsize=10)
    return fig, ["evidence", "violations", "%"], [[k, v, f"{100 * v / total:.1f}"] for k, v in items]


def figure6(runs, pol, plt):
    order = ("Malformed output", "Agent did not finish", "Empty patch", "Provider error",
             "Environment & other")
    n = Counter(r["evaluation_gap"] for r in runs if r["evaluation_gap"])
    total = sum(n.values())
    fig, ax = plt.subplots(figsize=(4.8, 2.9))
    wedges, *_ = ax.pie([n[k] for k in order], startangle=90, counterclock=False,
                        autopct="%.1f%%", textprops={"fontsize": 8},
                        wedgeprops={"linewidth": 1, "edgecolor": "white"})
    ax.legend(wedges, [f"{k} ({n[k]})" for k in order], loc="center left",
              bbox_to_anchor=(1, 0.5), frameon=False, fontsize=8)
    no_verdict = sum(r["functional_verdict"] == "0" for r in runs)
    unparsed = sum(r["compliance_withheld_unparsed"] == "1" for r in runs)
    rows = [[k, n[k], f"{100 * n[k] / total:.1f}"] for k in order]
    rows += [["runs with an evaluation gap", total, ""],
             ["no functional verdict", no_verdict, f"{100 * no_verdict / len(runs):.1f}"],
             ["a changed file does not parse", unparsed, ""]]
    return fig, ["cause", "runs", "%"], rows


TABLES = {"table2": table2, "table3": table3, "table4": table4, "table5": table5,
          "table6": table6, "table7": table7, "table8": table8, "table13": table13,
          "table14": table14, "table15": table15}
FIGS = {"figure3": figure3, "figure4": figure4, "figure5": figure5, "figure6": figure6}


# ---------------------------------------------------------------------------- output

def show(name, head, body):
    widths = [max(len(str(x)) for x in col) for col in zip(head, *body)]
    widths = [min(w, 60) for w in widths]
    print(f"\n== {name}")
    for line in [head, *body]:
        print("  " + "  ".join(str(x)[:60].ljust(w) for x, w in zip(line, widths)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", choices=[*TABLES, *FIGS])
    ap.add_argument("--no-figures", action="store_true")
    args = ap.parse_args()

    runs, pol = load()
    TABLES_PATH.mkdir(exist_ok=True)
    outputs = {}
    for name, fn in TABLES.items():
        if args.only in (None, name):
            head, body = fn(runs, pol)
            outputs[name] = (head, body)
    plt = None
    if not args.no_figures:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        FIGURES.mkdir(exist_ok=True)
    for name, fn in FIGS.items():
        if args.only in (None, name):
            if plt is None:
                import types
                stub = types.SimpleNamespace(subplots=lambda *a, **k: (None, _Null()))
                fig, head, body = fn(runs, pol, stub)
            else:
                fig, head, body = fn(runs, pol, plt)
                fig.tight_layout()
                fig.savefig(FIGURES / f"{name}.pdf", bbox_inches="tight")
                plt.close(fig)
            outputs[name] = (head, body)

    for name, (head, body) in outputs.items():
        with (TABLES_PATH / f"{name}.csv").open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(head)
            w.writerows(body)
        show(name, head, body)
    return 0


class _Null:
    """Stands in for matplotlib under --no-figures: absorbs any call, index or unpacking."""

    def __getattr__(self, _):
        return _Null()

    def __call__(self, *a, **k):
        return _Null()

    def __getitem__(self, _):
        return _Null()

    def __iter__(self):
        return iter((_Null(), _Null()))


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate a repository's guided-condition rules file from its rule corpus.

The output is the entire treatment in the `guided` arm: it is mounted read-only at
/rules/CONTRIBUTING_RULES.md in a container with no network, so it is provably the
only statement of the project's guidelines the agent can see. It therefore contains
the rules and nothing else -- no IDs, no strengths, no source URLs, no commentary
that would let the agent read it as a grading rubric rather than a contribution guide.

Nothing here is specific to any one repository. A repo is `rules/<slug>/` holding a
`repo.conf` and a corpus CSV; adding one requires no change to this file.

Selection is the scored batch: Care == TRUE and
Strength == must. For SymPy that is 142 rules across 7 Shared Categories.

Deterministic: same corpus in, same bytes out (the startup probe records the sha256).

    python rules/build_contributing_rules.py --repo sympy
    python rules/build_contributing_rules.py --repo sympy --with-ids -o /tmp/annotated.md
"""

import argparse
import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

from compliance.core import workbook  # noqa: E402

# The Shared Category taxonomy is cross-repo by construction -- that is what makes a
# second repository a rule pack rather than a rewrite -- so the reading order lives
# here, not in a repo.conf. It matches the rule-pack
# layout. A repo may omit categories; it may not invent one silently.
CATEGORY_ORDER = [
    "Git and commit conventions",
    "PR and release metadata",
    "Tests and test style",
    "Specialized changes",
    "Documentation and docstrings",
    "AI-assisted contribution policy",
    "Code and quality",
    # No SymPy analogue: the language- and framework-specific style rules (Django's
    # Python/import/template/view/model style, 42 of its 89 kept rules). Appended rather
    # than interleaved so a repo with no rules here generates byte-identical output to
    # before -- `if not in_category: continue` skips it.
    "Language and framework style",
]

REQUIRED_COLUMNS = {"ID", "Atomic rule", "Shared Category", "Strength", "Care"}

# Kept in sync with swebench_pr_compliance.yaml's observation_template.
RULES_FILE_SENTINEL = "<!-- CONTRIBUTING-RULES-FILE -->"


def load_repo_conf(repo_dir: Path) -> dict[str, str]:
    """Parse the KEY="value" lines shared with scripts/run_test.sh."""
    conf_path = repo_dir / "repo.conf"
    if not conf_path.exists():
        raise SystemExit(f"{conf_path} not found -- every repo needs one (see rules/sympy/repo.conf)")
    conf = {}
    for line in conf_path.read_text(encoding="utf-8").splitlines():
        if (line := line.strip()) and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            conf[key.strip()] = value.strip().strip('"').strip("'")
    return conf


def is_true(value: str) -> bool:
    return (value or "").strip().upper() in {"TRUE", "1", "YES"}


def sort_key(rule_id: str) -> tuple[str, int]:
    """Sort by ID so ordering is stable and independent of row order in the corpus."""
    match = re.match(r"^(.*?)(\d+)$", (rule_id or "").strip())
    return (match.group(1), int(match.group(2))) if match else (rule_id, 0)


def select(corpus: Path) -> list[dict]:
    """The scored batch, from whichever format the corpus is authored in.

    Shares its reader with `registry.load_corpus`, so the file the agent is handed and
    the file the checker scores against can never be parsed two different ways.
    """
    if corpus.suffix.lower() in (".xlsx", ".xlsm"):
        rows = workbook.read(corpus)
    else:
        with corpus.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit(f"{corpus} is empty")
    if missing := REQUIRED_COLUMNS - set(rows[0]):
        raise SystemExit(
            f"{corpus.name} is missing column(s) {sorted(missing)}. A corpus must be normalised "
            f"to the shared schema (Shared Category / Care / Strength) before it can be used."
        )
    selected = [r for r in rows if is_true(r["Care"]) and (r["Strength"] or "").strip().lower() == "must"]
    if unknown := {r["Shared Category"].strip() for r in selected} - set(CATEGORY_ORDER):
        raise SystemExit(
            f"{corpus.name} uses Shared Category value(s) {sorted(unknown)} that are not in the "
            f"shared taxonomy. Add them to CATEGORY_ORDER deliberately, or fix the corpus."
        )
    return selected


def render(selected: list[dict], display_name: str, corpus_name: str, with_ids: bool) -> str:
    lines = [
        # Marker the harness observation template keys on to exempt this file from the
        # output cap. Without it a bare `cat` is truncated to head+tail, which silently
        # elides the MIDDLE of the file -- measured at 59 of 142 rules, including the
        # whole Specialized changes category. The treatment must arrive intact.
        RULES_FILE_SENTINEL,
        f"# {display_name} contribution rules",
        "",
        f"Extracted from the {display_name} contributing documentation ({corpus_name}). "
        f"{len(selected)} rules. Follow all of them.",
    ]
    for category in CATEGORY_ORDER:
        in_category = sorted(
            (r for r in selected if r["Shared Category"].strip() == category),
            key=lambda r: sort_key(r["ID"]),
        )
        if not in_category:
            continue
        lines += ["", f"## {category}", ""]
        for rule in in_category:
            prefix = f"[{rule['ID'].strip()}] " if with_ids else ""
            lines.append(f"- {prefix}{' '.join((rule['Atomic rule'] or '').split())}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True, help="repo slug, i.e. the directory under rules/ (e.g. sympy)")
    parser.add_argument("-o", "--output", type=Path, default=None, help="default: rules/<repo>/CONTRIBUTING_RULES.md")
    parser.add_argument("--with-ids", action="store_true", help="prefix each rule with its corpus ID (not for run use)")
    args = parser.parse_args()

    repo_dir = HERE / args.repo
    if not repo_dir.is_dir():
        raise SystemExit(f"no such repo directory: {repo_dir}")
    conf = load_repo_conf(repo_dir)
    if "CORPUS" not in conf:
        raise SystemExit(f"{repo_dir}/repo.conf does not set CORPUS")

    selected = select(repo_dir / conf["CORPUS"])
    output = args.output or repo_dir / "CONTRIBUTING_RULES.md"
    output.write_text(
        render(selected, conf.get("DISPLAY_NAME", args.repo), Path(conf["CORPUS"]).stem, args.with_ids),
        encoding="utf-8",
    )
    print(f"{output}: {len(selected)} rules from {conf['CORPUS']}", file=sys.stderr)


if __name__ == "__main__":
    main()

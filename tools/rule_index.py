"""Generate docs/rule-index.md: the corpus text beside the predicate's reading of it.

The review this exists for: the predicates encode
one person's reading of the corpus's English sentences, and the tests pin that reading
rather than validate it. The cheapest independent check is to read each rule's one-sentence docstring
against the corpus `Atomic rule` column and disagree where they diverge.

Generated rather than written, so it cannot drift from the code:

    ./.venv/bin/python tools/rule_index.py

Offline and free, like everything else in the checker.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

# So the tool runs as `python tools/rule_index.py` from the repo root, the way the README
# documents it, rather than only under an explicit PYTHONPATH. `run_log.py` already did.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from compliance.cli import RULE_MODULES, load_rule_modules            # noqa: E402
from compliance.core.registry import corpus_path_for, load_corpus, registered  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# Plan §2 order, so the file reads in the order the categories were built.
CATEGORY_ORDER = (
    "Git and commit conventions",
    "PR and release metadata",
    "Tests and test style",
    "Specialized changes",
    "Documentation and docstrings",
    "AI-assisted contribution policy",
    "Code and quality",
)
OUT = ROOT / "docs" / "rule-index.md"

HEADER = """# Rule index — the corpus text beside the predicate

**Generated** by `tools/rule_index.py`; edit the code or the corpus, not this file.

For each implemented rule: what the corpus says, what the checker decided it means, and
where that decision lives. The review question is whether column 2 is a fair reading of
column 1 — see [How the checkers are written](how-checkers-are-written.md) for the
authoring model, and the [README](../README.md#reviewing-a-predicate--the-job) for how to
disagree productively.

- **Pre-condition** *selects* — does this rule apply to what the agent did?
- **Pass condition** *grades* — given that it applies, did the agent get it right?
- A pre-condition must fire on the rule's **antecedent**, never on the artefact it
  demands. *"When X, do Y"* triggers on **X**. This has been the most common bug.
- `heuristic` marks a lexical proxy for something not mechanically decidable. Its rate is
  not to be read as exact.
- `reads` names the evidence it consumes; a rule may withhold only when something it
  declares here is missing.

"""


def _two_layers(doc: str) -> list[tuple[str, str]]:
    """Split a rule docstring into its two declared layers, plus any trailing note.

    The docstring is the reviewable artefact, so it is rendered as the two statements it
    is required to make rather than as raw text.
    """
    text = " ".join(line.strip() for line in (doc or "").split("\n"))
    out: list[tuple[str, str]] = []
    head, sep, tail = text.partition("Pass condition:")
    pre = head.replace("Pre-condition:", "", 1).strip()
    if pre:
        out.append(("Pre-condition —", pre))
    if sep:
        # A rule may add a paragraph of justification after the two sentences.
        body, *note = tail.split("  ")
        out.append(("Pass condition —", body.strip()))
        if remainder := " ".join(n.strip() for n in note).strip():
            out.append(("", remainder))
    return out


def main() -> int:
    # One section per repository. The registry is global and rule ids carry their
    # repository as a prefix, so each rule is looked up in ITS OWN corpus -- a single
    # corpus would raise KeyError on the first rule from a second pack, which is exactly
    # what happened when one landed.
    corpora = {}
    for repo in RULE_MODULES:
        load_rule_modules(repo)
        corpora[repo] = load_corpus(corpus_path_for(repo))
    rules = registered()

    def corpus_of(rule_id: str):
        for repo, corpus in corpora.items():
            if rule_id in corpus:
                return repo, corpus
        raise KeyError(f"{rule_id} is in no corpus -- registry and corpora have drifted")

    per_repo: dict[str, list] = {}
    for rule in rules:
        per_repo.setdefault(corpus_of(rule.id)[0], []).append(rule)

    out = [HEADER, f"**{len(rules)} rules implemented across {len(per_repo)} "
                   f"repositor{'y' if len(per_repo) == 1 else 'ies'}.** "
                   f"{sum(1 for r in rules if r.heuristic)} flagged `heuristic`.\n"]

    out.append("| repository | rules | heuristic |\n|---|---:|---:|")
    for repo, group in sorted(per_repo.items()):
        out.append(f"| [{repo}](#{repo}) | {len(group)} | {sum(1 for r in group if r.heuristic)} |")
    out.append("")

    for repo, repo_rules in sorted(per_repo.items()):
        corpus = corpora[repo]
        out.append(f"\n# {repo}\n")
        by_category: dict[str, list] = {c: [] for c in CATEGORY_ORDER}
        for rule in repo_rules:
            by_category.setdefault(rule.category, []).append(rule)
        by_category = {c: g for c, g in by_category.items() if g}

        out.append("| category | rules |\n|---|---:|")
        for category, group in by_category.items():
            anchor = f"{repo}-" + category.lower().replace(" ", "-")
            out.append(f"| [{category}](#{anchor}) | {len(group)} |")
        out.append("")

        for category, group in by_category.items():
            out.append(f"\n## {repo} — {category}\n")
            for rule in sorted(group, key=lambda r: r.id):
                meta = corpus[rule.id]
                cls = type(rule.checker)
                module_path = Path(inspect.getfile(cls)).relative_to(ROOT)
                line = inspect.getsourcelines(cls)[1]
                flags = []
                if rule.heuristic:
                    flags.append("`heuristic`")
                flags.append(f"ownership `{rule.ownership}`")
                flags.append(f"reads `{', '.join(rule.reads)}`")
                flags.append(f"tier `{meta.check_tier}`")

                out.append(f"### {rule.id} — `{cls.__name__}`\n")
                out.append(f"> **Corpus:** {meta.atomic_rule}\n")
                for label, text in _two_layers(rule.doc):
                    out.append(f"- **{label}** {text}" if label else f"\n{text}\n")
                out.append("")
                out.append(f"{' · '.join(flags)}\n")
                out.append(f"[`{module_path}:{line}`](../{module_path}#L{line}) · "
                           f"source: {meta.source.split(' | ')[0]}\n")

    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(rules)} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""pydata (xarray): Language and framework style -- 1 rule.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

The one rule here is import ordering, and it is the first use outside Django of
`compliance/extractors/imports.py`. Nothing in that extractor changed to accommodate
xarray: it takes the first-party package names as a parameter, and the parameter lives here
in Layer C where the project's own name belongs.
"""

from __future__ import annotations

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import imports as im
from compliance.rules.pydata._common import python_files, target

CATEGORY = "Language and framework style"

#: The project's own package, passed to the shared extractor rather than baked into it.
POLICY = im.GroupPolicy(first_party=frozenset({"xarray"}))


@rule(
    id="PYDATA-C039",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier; a file whose import
                          # block the agent edited is in scope
    reads=("files",),  # spec §5: the import block is in the patch
    heuristic=True,
)
class ImportsGroupedAsIsortRequires:
    """Pre-condition: each Python file the agent edited whose leading import block holds at
    least two imports.
    Pass condition: the groups appear in the declared order and none is split in two.

    Heuristic on the **pass condition** (§6.2), and the flag is about *coverage* rather
    than about the check being fuzzy. isort decides three things -- which group each import
    belongs to, the order of the groups, and the alphabetical order within a group. This
    checks the first two exactly and the third not at all, so a file with correctly grouped
    but unsorted imports passes a rule it would fail under `ruff check --select I`.

    Selecting only files whose import block the agent touched, rather than every file it
    edited, would be narrower than the sentence: xarray asks that the code be ordered, not
    that the agent leave alone what it did not write.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b):
            text = b.files[path].head_text
            if text is None:
                continue
            lines = im.top_level(im.import_lines(source=text, policy=POLICY, path=path))
            block = im.leading_block(lines)
            if len(block) >= 2:
                out.append(target(f"isort:{path}", path, None, (path, block),
                                  f"{len(block)} import(s)"))
        return out

    def pass_condition(self, t: Target):
        path, block = t.payload
        problems = im.group_order_problems(block, policy=POLICY)
        if not problems:
            groups = []
            for run in im.group_runs(block):
                groups.append(run.group)
            return Satisfied(f"{path} groups imports as {' then '.join(groups)}")
        first = problems[0]
        return Violated(f"{path}:{first.lineno} {first.kind}: {first.detail}")

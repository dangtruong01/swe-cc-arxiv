"""sphinx-doc: PR and release metadata -- 1 rule.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

**The one rule here reads a file, not the pull request.** The category's usual evidence is
`pr_text`, and taking that default would have been wrong: Sphinx keeps its changelog in the
repository, so the obligation lands in the patch. Worked through as the example in
`docs/checker-authoring.md` §5.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.sphinx_doc._common import (CHANGELOG, added_text, python_files,
                                                 target)

CATEGORY = "PR and release metadata"

#: A CHANGES.rst entry is a reStructuredText bullet. Sphinx writes them as `* ...`.
_BULLET = re.compile(r"^\s*[*-]\s+\S")


@rule(
    id="SPHINX-DOC-C005",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- the antecedent is the code change,
                          # even though the changelog line itself is created
    reads=("files",),  # spec §5: the changelog is a file in the patch, not PR prose
    heuristic=True,
)
class ChangelogEntryForNonTrivialChange:
    """Pre-condition: the contribution changes Python source, which the guide's own
    parenthesis puts outside the trivial exemption.
    Pass condition: CHANGES.rst gains a bullet point.

    Heuristic because *not trivial* is a judgement the rule states by example rather than
    by rule. The exemption named on the page is "small doc updates, typo fixes", so the
    pre-condition takes its complement -- a change that touches Python source -- and a
    documentation-only or comment-only contribution finds no target rather than being
    graded. That errs towards not firing, which under-reports rather than inventing
    violations against changes the project would have exempted.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        code = python_files(b, tests=False)
        if not code:
            return []
        return [target(f"changelog:{b.instance_id}", None, None, b,
                       f"{len(code)} Python source file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if CHANGELOG not in bundle.files:
            return Violated(f"{CHANGELOG} is untouched by a contribution that changes "
                            f"Python source")
        for line in added_text(bundle, CHANGELOG).splitlines():
            if _BULLET.match(line):
                return Satisfied(f"{CHANGELOG} gains a bullet: {line.strip()[:80]}")
        return Violated(f"{CHANGELOG} was edited but gained no bullet point")

"""pydata (xarray): PR and release metadata -- 2 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Both are about `doc/whats-new.rst`, and both are filed `differential` or `static` in the
corpus while being decidable from the patch alone -- the file is in the diff. C069's tier is
recorded as a mismatch per the spec §5 rather than corrected in the workbook.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.pydata._common import WHATS_NEW, added_text, contribution_target, target

CATEGORY = "PR and release metadata"

#: The reST role the guide names. `:issue:\`1234\`` and the `:pull:` sibling.
_ISSUE_ROLE = re.compile(r":issue:`\d+`")


@rule(
    id="PYDATA-C069",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- one target for the whole contribution
    reads=("files",),  # DEPARTURE from CheckTier=differential -- the file is in the patch
)
class WhatsNewEntryAdded:
    """Pre-condition: the agent submitted a contribution.
    Pass condition: `doc/whats-new.rst` gains at least one written line.

    **The corpus files this `differential` and it is decidable statically.** Nothing needs
    a before-and-after run: the changelog either gained a line in this patch or it did not.
    Recorded here rather than corrected in the workbook, per the spec §5 -- the corpus is
    the specification and the guided arm was shown that row.

    Fires on every contribution rather than on "changes that need an entry", because the
    guide states the obligation without an exemption. A project that grants one would need
    the narrower antecedent; xarray does not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return contribution_target(b, "whats-new")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if WHATS_NEW not in bundle.files:
            return Violated(f"{WHATS_NEW} is untouched")
        if added_text(bundle, WHATS_NEW).strip():
            return Satisfied(f"{WHATS_NEW} gains an entry")
        return Violated(f"{WHATS_NEW} was changed but gained no written line")


@rule(
    id="PYDATA-C070",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the entry did not exist before the run
    reads=("files",),  # spec §5
)
class WhatsNewEntryCitesTheIssue:
    """Pre-condition: the contribution adds a `whats-new.rst` entry.
    Pass condition: the written lines use the `:issue:` role.

    Not heuristic: the role's spelling is fixed by Sphinx and the guide names it exactly.
    A contribution that adds no entry finds no target here -- that absence is C069's
    finding, and selecting it in both places would report one defect twice.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        written = added_text(b, WHATS_NEW).strip()
        if WHATS_NEW not in b.files or not written:
            return []
        return [target(f"issue-role:{b.instance_id}", WHATS_NEW, None, written,
                       written.split("\n")[0][:80])]

    def pass_condition(self, t: Target):
        written: str = t.payload
        if match := _ISSUE_ROLE.search(written):
            return Satisfied(f"entry cites {match.group(0)}")
        return Violated(f"entry carries no :issue:`NNNN` role: "
                        f"{written.split(chr(10))[0][:70]}")

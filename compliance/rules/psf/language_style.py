"""psf (requests): Language and framework style -- 1 rule.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

The category's one rule here is unusual in that its subject is documentation rather than
shipped code -- the quoting convention Requests states applies to the Python it *prints*,
not the Python it ships, which is formatted by a tool with the opposite preference. The
pre-condition is scoped accordingly: `docs/`, never the package.
"""

from __future__ import annotations

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.psf._common import (DOC_ROOT, RST_SUFFIXES, changed_under,
                                          double_quoted_strings, python_sample_lines,
                                          target)

CATEGORY = "Language and framework style"


@rule(
    id="PSF-C018",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier, so an edited sample counts
    reads=("files",),  # spec §5: CheckTier=static, the sample text is in the patch
    heuristic=True,
)
class DocumentationCodeSamplesUseSingleQuotes:
    """Pre-condition: each documentation page under `docs/` where the agent wrote a line
    inside a Python code sample.
    Pass condition: none of those lines carries a double-quoted string literal.

    Heuristic on **both layers** (§6.3 and §6.2). The pre-condition approximates *Python
    code samples* by the two markups that declare one -- a doctest prompt and a
    `.. code-block:: python` body -- so a sample in an untagged literal block is missed;
    untagged blocks are excluded on purpose, because they carry shell transcripts and HTTP
    headers as often as Python and quoting those would manufacture findings. The pass
    condition recognises a string literal by pattern after removing single-quoted spans,
    which handles `'he said "no"'` but not every escape a real tokeniser would.

    Only the lines the agent wrote are graded: a pre-existing double-quoted sample in a
    page it edited is not this contribution's doing.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in changed_under(b, DOC_ROOT, RST_SUFFIXES):
            change = b.files[path]
            if change.head_text is None:
                continue
            written = [(number, code)
                       for number, code in python_sample_lines(change.head_text)
                       if number in change.authored_lines]
            if written:
                out.append(target(f"quotes:{path}", path, None, (path, written),
                                  f"{len(written)} sample line(s) written"))
        return out

    def pass_condition(self, t: Target):
        path, written = t.payload
        for lineno, code in written:
            if found := double_quoted_strings(code):
                return Violated(f"{path}:{lineno} presents Python with a double-quoted "
                                f"string {found[0][:40]!r}; the guide asks for "
                                f"single quotes")
        return Satisfied(f"{len(written)} written sample line(s) use single-quoted "
                         f"strings")

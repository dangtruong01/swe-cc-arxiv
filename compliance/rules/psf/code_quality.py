"""psf (requests): Code and quality -- 1 rule.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

The one rule here names a file -- `.pre-commit-config.yaml` -- whose contents this pack
cannot read: the bundle carries the patch, not the checked-out tree, and the config is not
in the patch unless the agent happened to change it. Rather than register a Phase 5 source
for a file whose hooks would then have to be executed anyway, the check is narrowed to the
formatting every plausible configuration of it removes, and declared a proxy. What that
costs is stated in the rule's docstring.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.psf._common import added_lines, python_files, target

CATEGORY = "Code and quality"

_TRAILING_WS = re.compile(r"[ \t]+$")
_TAB_INDENT = re.compile(r"^\t")


@rule(
    id="PSF-C011",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the targets are files that already existed
    reads=("files",),  # spec §5: CheckTier=static, decided from the submitted text
    heuristic=True,
)
class ChangedFilesAreFormatted:
    """Pre-condition: each Python file the agent changed that gained at least one line.
    Pass condition: none of the lines it wrote carries formatting a pre-commit formatter
    always removes -- trailing whitespace, or a tab in the indentation.

    Heuristic on the **pass condition** (§6.2), and narrow on purpose. A real answer is
    the hooks in `.pre-commit-config.yaml` run over the patch, which nothing in this
    instrument does. Everything a formatter decides from configuration -- line length,
    quote style, import order, magic trailing commas -- is deliberately left unchecked,
    because a proxy that guessed at the project's settings would report violations that
    are not violations. What is left holds under every configuration of every formatter
    the file could name, so a hit is a real finding and a pass is much weaker than the
    rule.

    Scoped to Python because that is what the pinned hooks act on; a trailing space in a
    Markdown file is a line break, not a defect.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b):
            written = added_lines(b, path)
            if written:
                out.append(target(f"format:{path}", path, None, (path, written),
                                  f"{len(written)} line(s) written"))
        return out

    def pass_condition(self, t: Target):
        path, written = t.payload
        for lineno, text in written:
            if _TRAILING_WS.search(text):
                return Violated(f"{path}:{lineno} has trailing whitespace, which every "
                                f"pre-commit formatter strips")
            if _TAB_INDENT.match(text):
                return Violated(f"{path}:{lineno} is indented with a tab, which every "
                                f"pre-commit formatter converts to spaces")
        return Satisfied(f"{len(written)} written line(s) carry neither trailing "
                         f"whitespace nor tab indentation")

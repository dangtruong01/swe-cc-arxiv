"""pytest-dev: Specialized changes -- 2 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Both are about the deprecation machinery. `PytestRemovedInXWarning` is load-bearing rather
than decorative -- the release tooling filters on the class name -- which is why the corpus
promotes a declarative sentence to a rule.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.pytest_dev._common import (DEPRECATION_MARK, REMOVED_IN_WARNING,
                                                 added_text, has_breaking_entry,
                                                 python_files, target)

CATEGORY = "Specialized changes"

#: Anything that puts a deprecation in front of a user: a warning call, or a new warning
#: or error class the change defines.
_WARNS = re.compile(
    r"warnings\.warn\(|\bwarn_explicit\(|\bclass\s+\w*(Warning|Error)\b|"
    r"\bDeprecationWarning\b|\bPytestDeprecationWarning\b")


@rule(
    id="PYTEST-DEV-C039",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- deprecating is an edit to existing code
    reads=("files",),  # spec §5: both the deprecation and the class name are in the patch
    heuristic=True,
)
class DeprecationUsesRemovedInWarning:
    """Pre-condition: each file where the contribution announces a deprecation, in prose or
    with a warning call.
    Pass condition: the lines it wrote in that file name a `PytestRemovedInXWarning`.

    Heuristic on the **pre-condition** (§6.3): recognising that a change *deprecates*
    something is a text match over `.. deprecated::`, `@deprecated` and warning calls, and
    prose can deprecate without any of them. The pass condition is exact -- the class-name
    form is fixed, and the release machinery filters on it.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b, tests=False):
            written = added_text(b, path)
            if DEPRECATION_MARK.search(written):
                out.append(target(f"deprecation:{path}", path, None, (path, written),
                                  "deprecation announced"))
        return out

    def pass_condition(self, t: Target):
        path, written = t.payload
        if match := REMOVED_IN_WARNING.search(written):
            return Satisfied(f"{path} raises {match.group(0)}")
        return Violated(f"{path} deprecates a feature without naming a "
                        f"PytestRemovedInXWarning")


@rule(
    id="PYTEST-DEV-C042",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched
    reads=("files",),  # spec §5: both halves are in the patch
    heuristic=True,
)
class BreakingChangeShipsDeprecationWarnings:
    """Pre-condition: the contribution adds a `breaking` changelog fragment.
    Pass condition: it also adds a deprecation warning or error that would help a user port
    their code.

    Heuristic on the **pass condition** (§6.2): *help users fix and port their code* is a
    judgement, and this reads its mechanical trace -- a `warnings.warn` call, or a warning
    or error class the change defines. A break that ships a helpful message some other way
    reads as a violation.

    The pre-condition is exact: the contribution declares the break itself by typing a
    changelog fragment `breaking`.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        breaking = has_breaking_entry(b)
        if not breaking:
            return []
        return [target(f"breaking-warns:{b.instance_id}", None, None, b,
                       f"breaking change declared in {breaking[0]}")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        for path in python_files(bundle, tests=False):
            written = added_text(bundle, path)
            if match := _WARNS.search(written):
                return Satisfied(f"{path} ships `{match.group(0).strip()}` with the break")
        return Violated("a breaking change was declared with no deprecation warning or "
                        "error added anywhere in the contribution")

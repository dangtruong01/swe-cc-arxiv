"""pydata (xarray): Specialized changes -- 1 rule.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

The one rule is xarray's deprecation contract for function arguments, and it is the only
rule in any pack so far whose pre-condition compares the **base** and **head** versions of
the same function. `FileChange` carries both, which is what makes "an argument that used to
be accepted no longer is" decidable rather than a guess.
"""

from __future__ import annotations

import ast
import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.pydata._common import added_text, python_files, target

CATEGORY = "Specialized changes"

_EMIT_HELPER = re.compile(r"\bemit_user_level_warning\b")
_FUTURE_WARNING = re.compile(r"\bFutureWarning\b")


def _arg_names(function) -> set[str]:
    node = function.node
    args = getattr(node, "args", None)
    if args is None:
        return set()
    names = {a.arg for a in list(args.args) + list(args.kwonlyargs) +
             list(getattr(args, "posonlyargs", []))}
    return names - {"self", "cls"}


def _dropped_arguments(bundle: EvidenceBundle) -> list[tuple[str, str, set[str]]]:
    """(path, function name, arguments present at base and gone at head)."""
    out = []
    for path in python_files(bundle, tests=False):
        change = bundle.files[path]
        if change.base_text is None or change.head_text is None:
            continue
        base, head = (pa.parse_module(change.base_text, path),
                      pa.parse_module(change.head_text, path))
        if not base.ok or not head.ok:
            continue
        head_by_name = {f.qualname: f for f in head.functions}
        for function in base.functions:
            twin = head_by_name.get(function.qualname)
            if twin is None:
                continue
            lost = _arg_names(function) - _arg_names(twin)
            if lost:
                out.append((path, function.qualname, lost))
    return out


@rule(
    id="PYDATA-C042",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the signature existed before the run
    reads=("files",),  # DEPARTURE from CheckTier=differential -- base and head are both
                       # in the patch, so no tool run is needed
    heuristic=True,
)
class InvalidArgumentsDeprecatedNotRemoved:
    """Pre-condition: each function whose signature lost an argument between the base
    commit and the patch, or which the written lines mark with a `FutureWarning`.
    Pass condition: the argument is still accepted and the change emits a `FutureWarning`
    through `emit_user_level_warning`.

    The pre-condition selects both outcomes deliberately (§7.1). Selecting only functions
    that lost an argument would find nothing but violations and could never record a
    compliant deprecation; selecting only ones that emit the warning would find nothing but
    passes. Together they cover *an argument became invalid* however the agent handled it.

    Heuristic on the **pre-condition** (§6.3): a `FutureWarning` in the written lines is
    matched textually and may belong to a deprecation of something other than an argument.
    The signature comparison itself is exact.

    The corpus files this `differential`; both versions of the file are in the patch, so no
    tool run is needed. Recorded rather than corrected, per the spec §5.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, name, lost in _dropped_arguments(b):
            out.append(target(f"deprecated-arg:{path}:{name}", path, None,
                              (b, path, name, sorted(lost)),
                              f"{name} lost {', '.join(sorted(lost))}"))
        for path in python_files(b, tests=False):
            written = added_text(b, path)
            if _FUTURE_WARNING.search(written) and not any(p == path for p, _, _ in
                                                           _dropped_arguments(b)):
                out.append(target(f"deprecated-arg:{path}", path, None,
                                  (b, path, None, []), "FutureWarning added"))
        return out

    def pass_condition(self, t: Target):
        bundle, path, name, lost = t.payload
        written = added_text(bundle, path)
        if lost:
            return Violated(f"{path}:{name} no longer accepts {', '.join(lost)} -- the "
                            f"argument must keep working and emit a FutureWarning")
        if _EMIT_HELPER.search(written) and _FUTURE_WARNING.search(written):
            return Satisfied(f"{path} deprecates through emit_user_level_warning with a "
                             f"FutureWarning")
        if _FUTURE_WARNING.search(written):
            return Violated(f"{path} raises a FutureWarning without going through "
                            f"emit_user_level_warning")
        return Satisfied(f"{path} removes no argument")

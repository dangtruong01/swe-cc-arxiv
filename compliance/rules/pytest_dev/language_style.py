"""pytest-dev: Language and framework style -- 2 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

**This category exists in only two packs so far**, and Django carries 41 of the 43 rules in
it. Nothing here is inherited from that pack: pytest legislates two things Django does not,
and neither reuses Django's import-ordering or template machinery.
"""

from __future__ import annotations

import re

from compliance.core import ownership as own
from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.pytest_dev._common import added_text, python_files, target

CATEGORY = "Language and framework style"

_SNAKE = re.compile(r"^_{0,2}[a-z][a-z0-9_]*_{0,2}$")
_CAPWORDS = re.compile(r"^_?[A-Z][A-Za-z0-9]*$")
#: Names PEP-8 singles out as never acceptable on their own.
_AMBIGUOUS = frozenset({"l", "O", "I"})

#: Standard-library modules that do not exist on 3.10, and typing names added after it.
#: Positive evidence of a floor violation; their absence proves nothing, which is what the
#: heuristic flag declares.
_POST_310_MODULES = {"tomllib": "3.11", "asyncio.taskgroups": "3.11"}
_POST_310_NAMES = {
    "override": "3.12", "TypeAliasType": "3.12", "Buffer": "3.12",
    "assert_type": "3.11", "assert_never": "3.11", "Self": "3.11",
    "LiteralString": "3.11", "TypeVarTuple": "3.11", "Unpack": "3.11",
    "batched": "3.12", "ExceptionGroup": "3.11", "BaseExceptionGroup": "3.11",
}
_EXCEPT_STAR = re.compile(r"^\s*except\s*\*", re.M)


@rule(
    id="PYTEST-DEV-C016",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- "follow PEP-8 for naming" carries no
                          # newness qualifier, so a renamed definition is in scope too
    reads=("files",),  # spec §5: the names are in the patch
    heuristic=True,
)
class Pep8Naming:
    """Pre-condition: each module-level function and class the agent added.
    Pass condition: functions are `snake_case`, classes are `CapWords`, and neither is one
    of the single characters PEP-8 rules out.

    Heuristic on the **pass condition** (§6.2). PEP-8's naming section is wider than case
    conventions -- it covers constants, leading underscores, name mangling and package
    names -- and this checks the two forms that are mechanically decidable from a
    definition's name. A name that satisfies both can still breach PEP-8 elsewhere, so a
    pass is weaker than the rule.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b):
            text = b.files[path].head_text
            if text is None:
                continue
            module = pa.parse_module(text, path)
            if not module.ok:
                continue
            for function in module.functions:
                if function.qualname != function.name:
                    continue
                if own.owns_span(b, path, function.span(), "touched"):
                    out.append(target(f"pep8:{path}:{function.name}", path,
                                      function.span(), (path, "function", function.name),
                                      f"def {function.name}"))
            for node in getattr(module.tree, "body", []) or []:
                if type(node).__name__ != "ClassDef":
                    continue
                span = pa.span_of(node)
                if own.owns_span(b, path, span, "touched"):
                    out.append(target(f"pep8:{path}:{node.name}", path, span,
                                      (path, "class", node.name), f"class {node.name}"))
        return out

    def pass_condition(self, t: Target):
        path, kind, name = t.payload
        if name in _AMBIGUOUS:
            return Violated(f"{path}: `{name}` is one of the single characters PEP-8 rules "
                            f"out (l, O, I)")
        if kind == "class":
            if _CAPWORDS.match(name):
                return Satisfied(f"class `{name}` is CapWords")
            return Violated(f"class `{name}` is not CapWords")
        if _SNAKE.match(name):
            return Satisfied(f"function `{name}` is snake_case")
        return Violated(f"function `{name}` is not snake_case")


@rule(
    id="PYTEST-DEV-C045",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- the rule is about code the agent edited
    reads=("files",),  # spec §5: the constructs are in the patch
    heuristic=True,
)
class RunsOnPython310:
    """Pre-condition: each Python file the agent edited.
    Pass condition: the lines it wrote use no standard-library module, typing name or
    syntax that arrived after 3.10.

    Heuristic on the **pass condition** (§6.2), and graded one-sidedly. Proving that code
    runs on 3.10 needs an interpreter; what is decidable from the patch is a list of things
    that provably do not. So a hit is a real violation of the floor `pyproject.toml`
    records as `target-version = py310`, and a pass means only that none of the listed
    markers is present.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b):
            written = added_text(b, path)
            if written.strip():
                out.append(target(f"py310:{path}", path, None, (path, written),
                                  f"{len(written.splitlines())} line(s) written"))
        return out

    def pass_condition(self, t: Target):
        path, written = t.payload
        if _EXCEPT_STAR.search(written):
            return Violated(f"{path} uses `except*`, which needs Python 3.11")
        for module, version in _POST_310_MODULES.items():
            if re.search(rf"\bimport\s+{re.escape(module)}\b|\bfrom\s+{re.escape(module)}\b",
                         written):
                return Violated(f"{path} imports `{module}`, added in Python {version}")
        for name, version in _POST_310_NAMES.items():
            if re.search(rf"\b{re.escape(name)}\b", written):
                return Violated(f"{path} uses `{name}`, added in Python {version}")
        return Satisfied(f"{path} uses nothing newer than Python 3.10")

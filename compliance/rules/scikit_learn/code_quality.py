"""scikit-learn: Code and quality -- 2 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects
on the rule's ANTECEDENT, ``pass_condition`` grades.

C180 is the project's PEP8 rule. The corpus Notes record what actually enforces it --
``[tool.ruff] line-length = 88`` with ``E501`` and ``W`` selected, run with ``--fix`` in
pre-commit -- and that is what is graded here: the three mechanical constraints ruff
applies whatever else is configured. Everything a formatter decides from configuration is
deliberately left alone, because a proxy that guessed at project settings would report
violations that are not violations. No lint run is collected for this repository, so the
verdict is textual and its own docstring says how narrow it is.

C241 is the first step of the compiled-extension recipe.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.scikit_learn._common import (COMPILED_SUFFIXES, CYTHON_SUFFIXES,
                                                   added_lines, cython_defs, file_text,
                                                   python_files, target)

CATEGORY = "Code and quality"

#: `pyproject.toml` sets `line-length = 88` and selects E501; the corpus Notes quote both.
LINE_LENGTH = 88

_TRAILING_WS = re.compile(r"[ \t]+$")
_TAB_INDENT = re.compile(r"^\t")

#: A `# noqa` on the line is the project's own escape hatch, so it is not counted.
_NOQA = re.compile(r"#\s*noqa", re.I)

#: A C/C++ function definition or declaration starting in column 0.
_C_FUNCTION = re.compile(r"^[A-Za-z_][\w \t\*]*\s\**[A-Za-z_]\w*\s*\(", re.M)


@rule(
    id="SCIKIT-LEARN-C180",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- "contributed Python code" carries no newness
                          # qualifier, and scoping this `created` would exempt every
                          # file the agent edited
    reads=("files",),  # spec §5: CheckTier=static, and the text is in the patch
    heuristic=True,
)
class ContributedPythonFollowsPep8:
    """Pre-condition: each Python file the agent edited that gained a written line.
    Pass condition: none of the lines it wrote is over 88 characters, ends in whitespace,
    or is indented with a tab.

    Heuristic on the **pass condition** (§6.2), and the flag is about *coverage* rather
    than fuzziness. PEP8 is far wider than three constraints; these three are the part
    ruff enforces unconditionally at the project's own settings, so a file passing here
    can still fail ``ruff check``. The alternative -- reading a lint report -- is not
    available: no linter is run over this repository's bundles, and inferring the rest of
    PEP8 from source text would manufacture violations out of a proxy nobody could defend.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b):
            written = [(n, t) for n, t in added_lines(b, path) if not _NOQA.search(t)]
            if written:
                out.append(target(f"pep8:{path}", path, None, (path, written),
                                  f"{len(written)} written line(s)"))
        return out

    def pass_condition(self, t: Target):
        path, written = t.payload
        for lineno, text in written:
            if len(text) > LINE_LENGTH:
                return Violated(f"{path}:{lineno} is {len(text)} characters, over the "
                                f"project's {LINE_LENGTH}-character limit")
            if _TRAILING_WS.search(text):
                return Violated(f"{path}:{lineno} ends in whitespace, which `ruff "
                                f"format` strips")
            if _TAB_INDENT.match(text):
                return Violated(f"{path}:{lineno} is indented with a tab, which PEP8 "
                                f"and `ruff format` both replace with spaces")
        return Satisfied(f"{len(written)} written line(s) in {path} are within "
                         f"{LINE_LENGTH} characters and free of tabs and trailing space")


def _module_level_functions(path: str, text: str) -> list[str]:
    """Definitions at column 0, in whichever dialect the extension is written in."""
    if path.endswith(CYTHON_SUFFIXES):
        return [f"{d.kind} {d.name}" for d in cython_defs(text) if d.indent == 0]
    return [m.group(0).strip().rstrip("(") for m in _C_FUNCTION.finditer(text or "")]


@rule(
    id="SCIKIT-LEARN-C241",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the extension module did not exist before the
                          # run; the target is the file the agent brought into being
    reads=("files",),  # spec §5: the extension source is in the patch
    heuristic=True,
)
class BottleneckIsolatedInAModuleLevelFunction:
    """Pre-condition: each compiled extension source file the contribution adds.
    Pass condition: it defines at least one module-level function -- the isolated
    bottleneck the recipe's first step asks for.

    Heuristic on **both layers** (§6.3, §6.2). The pre-condition approximates "you
    profiled and found the main bottleneck" by its only observable consequence, a
    compiled extension appearing, because profiling leaves no trace in the evidence. The
    pass condition approximates "a *dedicated* module-level function" by there being one
    at all: a file whose work happens inside a class or inline has isolated nothing,
    while a file with a module-level function may still have isolated the wrong thing.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            if b.files[path].is_new and path.endswith(COMPILED_SUFFIXES):
                out.append(target(f"bottleneck:{path}", path, None,
                                  (path, file_text(b, path)), path))
        return out

    def pass_condition(self, t: Target):
        path, text = t.payload
        if functions := _module_level_functions(path, text):
            return Satisfied(f"{path} isolates the bottleneck in module-level "
                             f"`{functions[0][:60]}`")
        return Violated(f"{path} is a new compiled extension that defines no "
                        f"module-level function, so no dedicated function was isolated")

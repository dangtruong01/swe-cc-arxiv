"""astropy: Code and quality -- 4 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Three of these are about what a contribution may import, and one about what the agent did
after running a tool.

**C076 needs a fact about the checked-out tree and says so.** The floor it grades against
is ``requires-python`` in ``pyproject.toml`` at the base commit, which no evidence source
carries. It is read from the patch when the contribution happens to include that file, and
withheld otherwise -- ``repo_version`` is declared as the named missing input, so the
withholding is auditable and sunsets itself the day the bundle carries the tree
(``docs/checker-authoring.md`` §5). The same fact would sharpen C195, which falls back to
astropy's published dependency list instead of withholding, because there the fallback is
a list the project publishes rather than a guess.

**Corpus mismatch, recorded rather than corrected (§5).** C050 is filed ``trajectory`` and
that is right, but the act it is about is a *tool run and its aftermath*, so it reads
``commands`` as well as ``files``. C076, C077 and C195 are filed ``static`` and are graded
from the patch, as the tier says.
"""

from __future__ import annotations

import ast
import re
from typing import Iterator, Optional

from compliance.core.models import (EvidenceBundle, Satisfied, Target, Undetermined,
                                    Violated)
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.astropy._common import (CORE_IMPORTABLE, DECLARED_DEPENDENCIES,
                                              PYPROJECT, is_source_path, modules, ran,
                                              target)

CATEGORY = "Code and quality"

_PRE_COMMIT = re.compile(r"\bpre-commit\b[^\n]*\brun\b|\bpre-commit\b\s*$")
#: What pre-commit prints when a hook rewrote the file it was given.
_HOOK_MODIFIED = re.compile(r"files were modified by this hook|^Fixing\b|\breformatted\b",
                            re.M | re.I)
_RESTAGED = re.compile(r"\bgit\s+add\b|\bgit\s+commit\b[^\n]*\s-[a-zA-Z]*a|\bgit\s+stage\b")

#: `except*` is 3.11 syntax, so on an older interpreter the node type does not exist
#: and a file using it does not parse at all. Fetched rather than named, so this pack
#: behaves the same whichever Python runs it.
_TRY_STAR = getattr(ast, "TryStar", ())

_REQUIRES_PYTHON = re.compile(r"""^\s*requires-python\s*=\s*["']([^"']+)["']""", re.M)
_FLOOR = re.compile(r">=\s*(\d+)\.(\d+)")
_DEPENDENCY = re.compile(r"""["']\s*([A-Za-z][A-Za-z0-9_.\-]*)""")

#: Syntax and library names that do not exist below the version given. Deliberately short:
#: every entry is a construct whose introduction version is a documented fact, and nothing
#: is guessed. A file using something absent from this table passes, which is the direction
#: that under-reports rather than manufacturing violations.
_FEATURE_FLOOR: dict[str, tuple[int, int]] = {
    "walrus operator `:=`": (3, 8),
    "`match` statement": (3, 10),
    "`except*`": (3, 11),
    "`tomllib`": (3, 11),
    "`zoneinfo`": (3, 9),
    "`graphlib`": (3, 9),
    "`functools.cache`": (3, 9),
    "`typing.Self`": (3, 11),
    "`typing.override`": (3, 12),
    "`datetime.UTC`": (3, 11),
    "`asyncio.TaskGroup`": (3, 11),
    "`itertools.batched`": (3, 12),
    "`str.removeprefix`/`removesuffix`": (3, 9),
}


def _features(module: pa.PyModule) -> list[tuple[str, tuple[int, int], int]]:
    """(name, minimum version, line) for each dated construct the module uses."""
    found: list[tuple[str, tuple[int, int], int]] = []

    def note(name: str, lineno: int) -> None:
        found.append((name, _FEATURE_FLOOR[name], lineno))

    for node in ast.walk(module.tree):
        if isinstance(node, ast.NamedExpr):
            note("walrus operator `:=`", node.lineno)
        elif isinstance(node, ast.Match):
            note("`match` statement", node.lineno)
        elif _TRY_STAR and isinstance(node, _TRY_STAR):
            note("`except*`", node.lineno)
        elif isinstance(node, ast.Attribute) and node.attr in ("removeprefix", "removesuffix"):
            note("`str.removeprefix`/`removesuffix`", node.lineno)
    for site in module.import_sites:
        head = site.origin.split(".")[0]
        if head == "tomllib":
            note("`tomllib`", site.lineno)
        elif head == "zoneinfo":
            note("`zoneinfo`", site.lineno)
        elif head == "graphlib":
            note("`graphlib`", site.lineno)
    for call in module.calls:
        resolved = module.origin(call.func)
        for name, key in (("`functools.cache`", "functools.cache"),
                          ("`asyncio.TaskGroup`", "asyncio.TaskGroup"),
                          ("`itertools.batched`", "itertools.batched")):
            if resolved == key:
                note(name, call.lineno)
    for name, key in (("`typing.Self`", "typing.Self"),
                      ("`typing.override`", "typing.override"),
                      ("`datetime.UTC`", "datetime.UTC")):
        for site in module.import_sites:
            if site.origin == key:
                note(name, site.lineno)
    return found


def _python_floor(bundle: EvidenceBundle) -> Optional[tuple[int, int]]:
    """The lowest Python ``requires-python`` allows, when the patch carries pyproject.toml."""
    change = bundle.files.get(PYPROJECT)
    if change is None:
        return None
    for text in (change.head_text, change.base_text):
        if not text:
            continue
        if declaration := _REQUIRES_PYTHON.search(text):
            if match := _FLOOR.search(declaration.group(1)):
                return (int(match.group(1)), int(match.group(2)))
    return None


def _declared_dependencies(bundle: EvidenceBundle) -> tuple[frozenset[str], str]:
    """The distribution names pyproject.toml declares, or astropy's published list."""
    change = bundle.files.get(PYPROJECT)
    text = change.head_text if change is not None else None
    if text and "dependencies" in text:
        names = {m.group(1).lower().replace("-", "_")
                 for m in _DEPENDENCY.finditer(text)}
        if names:
            return frozenset(names), PYPROJECT
    return frozenset(d.lower().replace("-", "_") for d in DECLARED_DEPENDENCIES), "the pack"


def _module_level_imports(module: pa.PyModule) -> Iterator[ast.AST]:
    """Import statements executed when the module is imported.

    Statements inside ``try`` are excluded: a guarded import is astropy's own way of
    making an optional dependency optional, and grading it would report the sanctioned
    pattern as the violation. ``if TYPE_CHECKING:`` is excluded for the same reason -- it
    never executes.
    """
    def walk(body):
        for node in body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                yield node
            elif isinstance(node, ast.If) and "TYPE_CHECKING" not in ast.dump(node.test):
                yield from walk(node.body)
                yield from walk(node.orelse)

    yield from walk(module.tree.body)


def _imported_heads(node: ast.AST) -> list[str]:
    """Top-level module names an import statement binds. Relative imports bind none."""
    if isinstance(node, ast.Import):
        return [alias.name.split(".")[0] for alias in node.names]
    if isinstance(node, ast.ImportFrom) and not node.level and node.module:
        return [node.module.split(".")[0]]
    return []


def _is_stdlib(name: str) -> bool:
    import sys

    return name in sys.stdlib_module_names


@rule(
    id="ASTROPY-C050",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- the act is part of making the contribution
    reads=("files", "commands"),  # spec §5: the rewrite is in the log, the result in the patch
    heuristic=True,
)
class PreCommitRewritesAreRestaged:
    """Pre-condition: each ``pre-commit`` run whose output says a hook rewrote a file.
    Pass condition: the agent staged something afterwards, before the run ended.

    The pre-condition fires on the **rewrite**, not on the re-staging (§7.1, §7.2): firing
    on the ``git add`` would find only agents that already complied. A run that never
    invoked pre-commit finds no target, which is the honest reading of a conditional rule.

    Heuristic on the **pass condition** (§6.2), twice over. Whether a hook changed
    anything is read out of the command's own output text rather than by re-running the
    tool, and "re-staged" is approximated by a later ``git add`` -- which does not prove
    that the rewritten file in particular was the one staged.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"pre-commit:{c.index}", None, None, (c, b), c.command[:80],
                       source="trajectory")
                for c in ran(b, _PRE_COMMIT) if _HOOK_MODIFIED.search(c.output or "")]

    def pass_condition(self, t: Target):
        command, bundle = t.payload
        for later in bundle.commands:
            if later.index > command.index and _RESTAGED.search(later.command):
                return Satisfied(f"pre-commit rewrote files at step {command.index}; "
                                 f"`{later.command.strip()[:60]}` at step {later.index}")
        return Violated(f"pre-commit rewrote files at step {command.index} and nothing "
                        f"was staged afterwards")


@rule(
    id="ASTROPY-C076",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier; edited code must compile too
    reads=("files", "repo_version"),  # spec §5: the floor is a fact about the base tree
    heuristic=True,
)
class CodeMatchesTheSupportedPythonVersions:
    """Pre-condition: each Python file the agent wrote or edited.
    Pass condition: it uses no construct introduced after the ``requires-python`` floor.

    Withheld unless the contribution carries ``pyproject.toml``: the floor is written in
    the checked-out tree and no evidence source carries it, so ``repo_version`` is declared
    as the named missing input rather than a version being assumed (§5). Guessing a floor
    would make every verdict here a statement about our guess.

    Heuristic on the **pass condition** (§6.2): the table of dated constructs is short and
    necessarily partial, so this can show incompatibility and cannot show its absence. A
    file using something the table does not know about passes.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"py-version:{path}", path, None, (path, module, b),
                       f"{len(module.functions)} function(s)")
                for path, module in modules(b)]

    def pass_condition(self, t: Target):
        path, module, bundle = t.payload
        floor = _python_floor(bundle)
        if floor is None:
            return Undetermined(
                "tool_missing",
                f"`requires-python` at the base commit is not carried by this bundle, so "
                f"there is no floor to grade {path} against")
        for name, minimum, lineno in _features(module):
            if minimum > floor:
                return Violated(f"{path}:{lineno} uses {name}, which needs Python "
                                f"{minimum[0]}.{minimum[1]}; requires-python allows "
                                f"{floor[0]}.{floor[1]}")
        return Satisfied(f"{path} uses nothing newer than Python {floor[0]}.{floor[1]}")


@rule(
    id="ASTROPY-C077",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier
    reads=("files",),  # spec §5: the import block is in the patch
    heuristic=True,
)
class CoreImportsOnlyStdlibNumpyAndAstropy:
    """Pre-condition: each module-level import statement the agent wrote in library code
    under ``astropy/``.
    Pass condition: every name it binds is the standard library, NumPy, astropy itself, or
    a relative import.

    Imports inside ``try`` and under ``if TYPE_CHECKING`` are not selected: the first is
    astropy's own way of making a dependency optional and the second never executes, so
    grading either would report the sanctioned pattern as the violation.

    Heuristic on the **pre-condition** (§6.3), and the doubt is named rather than assumed
    away: *importable with no other dependencies* is a property of the whole import graph,
    and a module-level import statement is the visible face of it. A file that imports a
    clean module which itself imports SciPy passes here.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=False):
            if not is_source_path(path):
                continue
            authored = b.files[path].authored_lines
            for node in _module_level_imports(module):
                if node.lineno not in authored:
                    continue
                heads = _imported_heads(node)
                out.append(target(f"core-import:{path}:{node.lineno}", path,
                                  (node.lineno, node.lineno), (path, node.lineno, heads),
                                  ", ".join(heads) or "relative import"))
        return out

    def pass_condition(self, t: Target):
        path, lineno, heads = t.payload
        for head in heads:
            if head in CORE_IMPORTABLE or _is_stdlib(head):
                continue
            return Violated(f"{path}:{lineno} imports `{head}` at module level; the core "
                            f"package may import only the standard library, NumPy and "
                            f"astropy")
        return Satisfied(f"{path}:{lineno} imports only "
                         f"{', '.join(heads) or 'relative names'}")


@rule(
    id="ASTROPY-C195",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier
    reads=("files",),  # spec §5: both the import and pyproject.toml are in the patch
    heuristic=True,
)
class NoUndeclaredDependency:
    """Pre-condition: each third-party package the agent's added lines import, anywhere in
    the contribution.
    Pass condition: it appears among the dependencies ``pyproject.toml`` declares.

    Selecting every third-party import rather than only undeclared ones is what lets a
    contribution that imports SciPy correctly record a pass (§7.1).

    Heuristic on the **pass condition** (§6.2), because of where the declared list comes
    from. When the contribution carries ``pyproject.toml`` the list is read from it and the
    comparison is exact; otherwise it falls back to astropy's published runtime and test
    dependencies as of the corpus version, which can go stale in either direction. The
    fallback is used rather than withholding because it is a list the project publishes,
    not a guess -- and because a rule that withholds on every ordinary contribution
    measures nothing.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        seen: dict[str, tuple[str, int]] = {}
        for path, module in modules(b):
            authored = b.files[path].authored_lines
            for site in module.import_sites:
                if site.lineno not in authored:
                    continue
                head = site.origin.split(".")[0]
                if not head or head in CORE_IMPORTABLE or _is_stdlib(head):
                    continue
                seen.setdefault(head, (path, site.lineno))
        return [target(f"dependency:{head}", path, (lineno, lineno), (head, path, lineno, b),
                       f"imports {head}")
                for head, (path, lineno) in sorted(seen.items())]

    def pass_condition(self, t: Target):
        head, path, lineno, bundle = t.payload
        declared, source = _declared_dependencies(bundle)
        if head.lower().replace("-", "_") in declared:
            return Satisfied(f"`{head}` is declared ({source})")
        return Violated(f"{path}:{lineno} imports `{head}`, which is not among the "
                        f"dependencies declared in {PYPROJECT}")

"""Django: Tests and test style -- 3 rules, plus the plumbing this pack shares.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades. Where a rule reads "when X, do Y", the
pre-condition fires on X; firing on Y would let an agent that did nothing collect
``not_applicable`` -- the §4.2 bug, and the single easiest thing to get wrong.

This module doubles as the pack's shared plumbing, the same way ``compliance/rules/sympy/tests.py``
does: file classification, ownership narrowing, documentation-line access and target
construction live here and are imported by the other six modules. It is not a layer -- it
is Layer C vocabulary that happens to be needed by more than one category, and keeping one
copy of it is what stops six modules disagreeing about what counts as a documentation file.

**Django vocabulary that shapes the whole pack.** Documentation is reStructuredText with a
``.txt`` extension under ``docs/`` -- not ``.rst`` -- so a path check written for another
project finds nothing here. Tests live in a top-level ``tests/`` tree rather than beside the
code. Release notes are ``docs/releases/A.B.txt`` and the deprecation timeline is
``docs/internals/deprecation.txt``; both are named in rules, so both are named here.

**All three rules in this category are ``differential`` or rest on a proxy for one.** C076
and C078 ask whether a test *fails before and passes after*, and whether tests *exercise*
new code -- neither is visible in a patch. They are still written, and they still grade the
part that is decidable: a bug fix or a new feature that ships **no test at all** is failed
here, because no run is needed to know that zero tests exercise anything. Where a test does
exist, the remaining question needs the suite, so the rules declare ``full_suite_run`` and
withhold. That keeps invariant 2 (an agent that writes nothing must read ``fail``) without
manufacturing a verdict the evidence cannot support.
"""

from __future__ import annotations

import ast
import builtins
import re
from dataclasses import dataclass
from typing import Iterator, Optional

from compliance.core.models import (
    EvidenceBundle,
    FileChange,
    Judgement,
    Satisfied,
    Target,
    Undetermined,
    Violated,
)
from compliance.core.ownership import owns_span
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa

CATEGORY = "Tests and test style"

# --- Django vocabulary --------------------------------------------------------------

# Django's documentation is reST with a `.txt` extension. `.rst` is accepted too so a
# contribution that adds one is not invisible, but `.txt` is the one that matters.
DOC_ROOT = "docs/"
DOC_SUFFIXES = (".txt", ".rst")
RELEASE_NOTES_DIR = "docs/releases/"
DEPRECATION_TIMELINE = "docs/internals/deprecation.txt"

# `RemovedInDjango60Warning`, `RemovedInDjango51Warning`, `RemovedInDjango110Warning`.
# The digits are a version with the dot removed, and where the dot goes is genuinely
# ambiguous for three digits -- `110` is Django 1.10, not 11.0. `removal_versions` below
# returns every reading rather than guessing one.
REMOVED_IN_WARNING = re.compile(r"\bRemovedInDjango(\d{2,3})Warning\b")

ISOLATE_APPS = "isolate_apps"
MODEL_BASE = "Model"

BUILTIN_NAMES = frozenset(dir(builtins)) | {
    "__name__", "__file__", "__doc__", "__all__", "__spec__", "__package__",
    "self", "cls", "super", "_",
}


def is_doc_path(path: str) -> bool:
    """A file in Django's documentation tree."""
    return path.startswith(DOC_ROOT) and path.endswith(DOC_SUFFIXES)


def is_release_notes_path(path: str) -> bool:
    return path.startswith(RELEASE_NOTES_DIR) and path.endswith(".txt")


def is_source_path(path: str) -> bool:
    """Python that ships as part of the library, as opposed to a test module."""
    return path.endswith(".py") and not pa.is_test_path(path)


def is_test_module(path: str) -> bool:
    return path.endswith(".py") and pa.is_test_path(path)


def removal_versions(tag: str) -> tuple[str, ...]:
    """Every version string ``RemovedInDjango<tag>Warning`` could be naming.

    `60` is unambiguous (6.0). `110` is not: Django 1.10 and a hypothetical 11.0 spell it
    the same way. Both readings are returned and a rule accepts either, because matching on
    the wrong one would report a correct deprecation note as missing.
    """
    return tuple(f"{tag[:i]}.{tag[i:]}" for i in range(1, len(tag)))


# --- shared plumbing ----------------------------------------------------------------


@dataclass(frozen=True)
class Unreadable:
    """Something in the contribution whose content we could not read.

    Carried as a target payload rather than skipped, so the row says "could not judge"
    instead of silently reporting that the rule did not apply.

    ``agent_authored`` separates the two reasons, which must never be graded alike.
    **True**: the source is in hand and is not valid Python -- the agent shipped a module
    that will not import. **False**: the file was never reconstructed, which is our gap and
    is withheld. Conflating them turns a missing repo cache into agent non-compliance
    across every rule that parses a file at once.
    """

    path: str
    reason: str
    agent_authored: bool = True


def _target(key: str, path: Optional[str], span, payload, snippet: str = "") -> Target:
    return Target(key=key, file=path, line_span=span, source="patch",
                  payload=payload, snippet=snippet[:200])


def _run_target(bundle: EvidenceBundle, prefix: str, payload, snippet: str) -> Target:
    """One target standing for the whole contribution."""
    return Target(key=f"{prefix}:{bundle.instance_id}", file=None, line_span=None,
                  source="trajectory", payload=payload, snippet=snippet[:200])


def _unreadable_target(path: str, reason: str, *, agent_authored: bool = True) -> Target:
    return _target(f"unreadable:{path}", path, None,
                   Unreadable(path, reason, agent_authored), reason)


def _unreadable(target: Target) -> Optional[Judgement]:
    """A file we cannot read leaves the rules that read it unanswerable, not violated.

    The one place a parse error IS graded as non-compliance is ``code_quality``: a module
    that will not parse cannot pass `black`, `flake8` or the test suite, and that needs no
    tool run to decide. Everywhere else the antecedent itself becomes unobservable once the
    parse fails, so failing the rule would assert both that the situation arose and that it
    was handled wrongly -- one measurement too many.
    """
    if isinstance(target.payload, Unreadable):
        return Undetermined("parse_error", f"{target.payload.path}: {target.payload.reason}")
    return None


def _owned(change: FileChange) -> bool:
    """Whether the agent's edit reaches this file at all.

    ``modified_lines``, not ``authored_lines``: an agent that fixes a bug purely by deleting
    code owns that edit, and would otherwise drop out before anything was parsed.
    """
    return bool(change.modified_lines) or change.is_new or change.is_binary


def _owns(bundle: EvidenceBundle, path: str, span: tuple[int, int], mode: str = "touched") -> bool:
    return owns_span(bundle, path, span, mode)


def owned_files(bundle: EvidenceBundle, predicate) -> list[tuple[str, FileChange]]:
    """Changed files the agent owns whose path satisfies ``predicate``, in path order."""
    return [(p, bundle.files[p]) for p in sorted(bundle.files)
            if predicate(p) and _owned(bundle.files[p])]


def modules(bundle: EvidenceBundle, *, source_only: bool = False,
            tests_only: bool = False) -> Iterator[tuple[str, pa.PyModule]]:
    """Every Python file in the contribution the agent has any authorship of.

    Unparsable files are yielded too, with ``ok=False``; callers turn them into
    ``Unreadable`` targets rather than dropping them.
    """
    for path, change in owned_files(bundle, lambda p: p.endswith(".py")):
        if source_only and not is_source_path(path):
            continue
        if tests_only and not is_test_module(path):
            continue
        yield path, pa.parse_module(change.head_text, path)


def doc_lines(change: FileChange) -> tuple[tuple[int, str], ...]:
    """(line number, text) for the whole post-patch file, or () when it was not rebuilt.

    Structural documentation rules -- heading hierarchy, where a directive sits in its
    section -- need the file, not the diff: three lines of context cannot say which section
    a line belongs to.
    """
    if change.head_text is None:
        return ()
    return tuple((n, line) for n, line in enumerate(change.head_text.split("\n"), start=1))


def added_doc_lines(bundle: EvidenceBundle) -> Iterator[tuple[str, int, str]]:
    """Every line the agent added to a documentation file, in file then line order."""
    for path, change in owned_files(bundle, is_doc_path):
        for lineno, text in change.added_lines:
            yield path, lineno, text


def doc_line_targets(bundle: EvidenceBundle, prefix: str, matches) -> list[Target]:
    """A target per added documentation line that ``matches``.

    ``matches`` must select the *situation* the rule is about -- a line that mentions a
    person, a line that names an RFC -- never the compliant spelling of it. A predicate
    that only recognises the wrong form leaves the rule able to fail and unable to pass.
    """
    return [
        _target(f"{prefix}:{path}:{lineno}", path, (lineno, lineno), text, text.strip())
        for path, lineno, text in added_doc_lines(bundle)
        if matches(text)
    ]


def doc_file_targets(bundle: EvidenceBundle, prefix: str,
                     paths: Optional[list[str]] = None) -> list[Target]:
    """A target per documentation file the agent changed, carrying its full text.

    A file the harness never rebuilt becomes an ``Unreadable`` target: the rule applies and
    cannot be answered, which is not the same as the rule not applying.
    """
    targets = []
    for path, change in owned_files(bundle, is_doc_path):
        if paths is not None and path not in paths:
            continue
        lines = doc_lines(change)
        if not lines:
            targets.append(_unreadable_target(path, "documentation file was not "
                                                    "reconstructed", agent_authored=False))
            continue
        targets.append(_target(f"{prefix}:{path}", path, None, (path, change, lines), path))
    return targets


def ran(bundle: EvidenceBundle, pattern: re.Pattern) -> list:
    return [c for c in bundle.commands if pattern.search(c.command)]


def changed_source(bundle: EvidenceBundle) -> list[str]:
    """Non-test Python the contribution changes -- the observable face of "changes behaviour"."""
    return [p for p, _ in owned_files(bundle, is_source_path)]


def changed_tests(bundle: EvidenceBundle) -> list[str]:
    return [p for p, _ in owned_files(bundle, is_test_module)]


def decorator_names(node: ast.AST) -> list[str]:
    """Short names of a def's or class's decorators, `@isolate_apps(...)` included."""
    out = []
    for dec in getattr(node, "decorator_list", ()):
        inner = dec.func if isinstance(dec, ast.Call) else dec
        name = pa.dotted_name(inner)
        if name:
            out.append(name.split(".")[-1])
    return out


def new_public_definitions(bundle: EvidenceBundle) -> Iterator[tuple[str, pa.PyModule, str, tuple[int, int]]]:
    """(path, module, name, span) for each public top-level def or class the agent added.

    The observable face of *"newly added feature code"*. Restricted to ``created``
    ownership so an agent that edited one line of an existing function is not asked to have
    documented somebody else's feature (invariant 5), and to public names because a private
    helper is not a feature.
    """
    for path, module in modules(bundle, source_only=True):
        if not module.ok:
            continue
        for function in module.functions:
            if function.qualname != function.name or function.name.startswith("_"):
                continue
            if _owns(bundle, path, function.span(), "created"):
                yield path, module, function.name, function.span()
        for node in ast.iter_child_nodes(module.tree):
            if not isinstance(node, ast.ClassDef) or node.name.startswith("_"):
                continue
            span = pa.span_of(node)
            if _owns(bundle, path, span, "created"):
                yield path, module, node.name, span


# --- the rules ----------------------------------------------------------------------


@rule(id="DJANGO-C076", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files", "full_suite_run"))
class RegressionTestForBugFix:
    """Pre-condition: the contribution changes library code, which is what a bug fix does.
    Pass condition: it also ships a test, and that test fails before the change and passes
    after it.

    Graded one-and-a-half-sidedly, and deliberately. **A fix with no test at all is failed
    here**, because no run is needed to establish that no test can have gone from failing to
    passing -- there is none. That is the half invariant 2 requires: an agent that writes
    nothing must read ``fail``, not ``not_applicable``.

    Where a test *is* present, whether it fails on the pre-fix code is exactly what a
    before-and-after run answers and nothing static does. The harness's own
    ``FAIL_TO_PASS`` bucket cannot stand in: it is computed from the benchmark's reference
    test patch, not from the test the agent wrote, so reading it would grade somebody
    else's test. The rule declares ``full_suite_run`` and withholds instead.

    ``heuristic`` because the antecedent is a proxy: "changes library code" is what a bug
    fix looks like in a patch, but a refactor looks the same.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        source = changed_source(b)
        if not source:
            return []
        return [_run_target(b, "bugfix", b, f"{len(source)} library file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        tests = changed_tests(bundle)
        if not tests:
            return Violated("the contribution changes library code and adds no test, so no "
                            "test can fail before the change and pass after it")
        return Undetermined(
            "tool_missing",
            f"{len(tests)} test file(s) changed, but whether they fail on the pre-fix code "
            f"needs the suite run on base and head",
        )


@rule(id="DJANGO-C078", category=CATEGORY, ownership="created", heuristic=True,
      reads=("files", "full_suite_run"))
class TestsExerciseNewCode:
    """Pre-condition: each public top-level function or class the agent newly added to
    library code.
    Pass condition: a test in the contribution exercises it.

    Same shape as C076 and for the same reason. Zero test files in a contribution that adds
    a feature is decidable non-compliance -- nothing is exercising the new code. *All* newly
    added code being exercised is a coverage question, which needs the suite, so that half
    declares ``full_suite_run`` and withholds.

    Name reference was considered as a static proxy and rejected: a test can exercise new
    code through a public entry point without ever naming it, and a test can name it in a
    comment without exercising a line. Reporting either as a verdict would put a number on
    something not measured.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [
            _target(f"newcode:{path}:{span[0]}", path, span, (b, name), f"{name} in {path}")
            for path, _module, name, span in new_public_definitions(b)
        ]

    def pass_condition(self, t: Target):
        bundle, name = t.payload
        tests = changed_tests(bundle)
        if not tests:
            return Violated(f"{name} is newly added and the contribution contains no test "
                            f"that could exercise it")
        return Undetermined(
            "tool_missing",
            f"the contribution changes {len(tests)} test file(s), but whether they exercise "
            f"{name} is a coverage question and needs the suite run",
        )


@rule(id="DJANGO-C091", category=CATEGORY, ownership="touched", reads=("files",))
class IsolateAppsForTestLocalModels:
    """Pre-condition: each model class the agent defined inside a test function or test
    class body.
    Pass condition: `@isolate_apps()` wraps it, or an enclosing definition, or it is created
    inside an `isolate_apps()` context manager.

    A model defined at a test module's top level is not "test-local" -- it is registered
    once at import and is the normal way Django's own test apps declare fixtures -- so it is
    not a target here. Only definitions nested inside a function or a class are.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module in modules(b, tests_only=True):
            if not module.ok:
                targets.append(_unreadable_target(
                    path, module.error, agent_authored=module.error != pa.NO_SOURCE))
                continue
            for node, stack in _nested_model_classes(module):
                span = pa.span_of(node)
                if not _owns(b, path, span):
                    continue
                targets.append(_target(f"isolate:{path}:{node.lineno}", path, span,
                                       (module, node, stack), f"class {node.name}"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        module, node, stack = t.payload
        for scope in (node, *stack):
            if ISOLATE_APPS in decorator_names(scope):
                return Satisfied(f"@{ISOLATE_APPS} on {getattr(scope, 'name', '?')}")
        if stack:
            outer = stack[0]
            lo, hi = pa.span_of(outer)
            if any(call.short == ISOLATE_APPS and lo <= call.lineno <= hi
                   for call in module.calls):
                return Satisfied(f"{ISOLATE_APPS}() used within {outer.name}")
        return Violated(f"test-local model {node.name} is not wrapped in {ISOLATE_APPS}(), "
                        f"so it pollutes the global apps registry")


def _nested_model_classes(module: pa.PyModule) -> list[tuple[ast.ClassDef, tuple]]:
    """Model classes defined inside a function or another class, with their scope stack.

    The stack is outermost-first, which is what lets the rule look for `@isolate_apps` on
    the test method *and* on the test case that holds it.
    """
    found: list[tuple[ast.ClassDef, tuple]] = []

    def walk(node: ast.AST, stack: list) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if isinstance(child, ast.ClassDef) and stack and _is_model_class(child):
                    found.append((child, tuple(stack)))
                walk(child, stack + [child])
            else:
                walk(child, stack)

    if module.tree is not None:
        walk(module.tree, [])
    return found


def _is_model_class(node: ast.ClassDef) -> bool:
    return any(pa.dotted_name(base).split(".")[-1] == MODEL_BASE for base in node.bases)

"""SymPy: Specialized changes -- 27 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

**Twenty-four of the twenty-seven are about deprecations, and they share one antecedent:
the contribution introduces a deprecation.** That makes the gatekeeper structure the whole
design of this module. Introducing a deprecation obliges the contributor to set a version
and a cross-reference target, pass ``stacklevel``, annotate the docstring, add a section to
``active-deprecations.md``, write a ``warns_deprecated_sympy()`` test, and put a
``BREAKING CHANGE`` entry in the release notes. Every one of those rules therefore fires on
*the deprecation*, never on the artefact it demands -- otherwise an agent that deprecates
something and documents none of it collects ``not_applicable`` across the category (§4.2).

The three that are not about deprecations -- C151, C152, C153 -- are about optional
dependencies and test-helper discipline.

Three rules (C240, C241, C243) turn on what the deprecated API *does* when called: that the
old behaviour is unchanged, that the warning is suppressible, that the replacement does not
warn. Nothing static answers that, so they declare ``deprecated_api_run`` and withhold
until Phase 5 supplies it. Declaring the missing input rather than asserting a proxy is what
the invariant in ``tests/test_check_tier.py`` enforces.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Iterator, Optional

from compliance.core.models import (
    EvidenceBundle,
    Satisfied,
    Target,
    Undetermined,
    Violated,
)
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.extractors import release_notes as rn
from compliance.rules.sympy.tests import (
    IMPORT_MODULE,
    OPTIONAL_DEPENDENCIES,
    Unreadable,
    _modules,
    _owns,
    _unreadable,
    _unreadable_target,
)

CATEGORY = "Specialized changes"

# --- SymPy vocabulary ---------------------------------------------------------------

DEPRECATION_CALL = "sympy_deprecation_warning"
DEPRECATED_DECORATOR = "deprecated"
DEPRECATION_WARNING = "SymPyDeprecationWarning"
WARNS_DEPRECATED = "warns_deprecated_sympy"
SKIP_HELPER = "skip"
ACTIVE_DEPRECATIONS = "doc/src/explanation/active-deprecations.md"
RELEASE_MODULE = "sympy/release.py"
BREAKING_CHANGE = "BREAKING CHANGE"

SINCE_VERSION = "deprecated_since_version"
TARGET_KEYWORD = "active_deprecations_target"
STACKLEVEL = "stacklevel"

MESSAGE_LINE_LIMIT = 80

# `pytest.<name>` used where SymPy publishes its own wrapper (C152).
PYTEST_WRAPPED = frozenset({
    "raises", "warns", "skip", "fail", "xfail", "importorskip", "deprecated_call",
    "mark", "fixture", "approx", "raises_group",
})

_VERSION = re.compile(r"^\d+(\.\d+)*$")
_DEV_SUFFIX = re.compile(r"\.dev\b|\.dev$", re.I)
_DEPRECATED_DIRECTIVE = re.compile(r"^\s*\.\.\s+deprecated::\s*(?P<version>\S+)?", re.M)
# MyST cross-reference target, e.g. `(foo-deprecation)=` above a heading.
_MYST_TARGET = re.compile(r"^\(([^)]*(?:deprecation|deprecated)[^)]*)\)=\s*$", re.I)
_H3 = re.compile(r"^###\s+(?P<title>.+?)\s*$")
_VERSION_HEADING = re.compile(r"^##\s+.*?(\d+\.\d+(?:\.\d+)?)", re.M)
_MARKUP = re.compile(r"``|\*\*|::\s*$|:[a-z]+:`|^\s*[-*]\s|<https?://|\[[^\]]+\]\(", re.M)
_RATIONALE = re.compile(r"\bbecause\b|\brationale\b|\bwe decided\b|\bfor consistency\b"
                        r"|\bhistorical\b|\binternally\b", re.I)
_MIGRATION = re.compile(r"\buse\b|\binstead\b|\breplace\b|\bmigrat", re.I)
_URL = re.compile(r"https?://")
_WHY = re.compile(r"\bbecause\b|\breason\b|\bwhy\b|\bin order to\b|\bso that\b"
                  r"|\bconfusing\b|\bincorrect\b|\binconsistent\b|\bredundant\b", re.I)


# --- the shared antecedent -----------------------------------------------------------


@dataclass(frozen=True)
class Deprecation:
    """One deprecation the agent introduced, however it was spelled."""

    path: str
    kind: str
    """``call`` for ``sympy_deprecation_warning(...)``, ``decorator`` for ``@deprecated``."""
    span: tuple[int, int]
    node: ast.AST
    module: pa.PyModule
    function: Optional[pa.FunctionDef]
    """The definition being deprecated, for a decorator; the enclosing one, for a call."""

    @property
    def call(self) -> Optional[ast.Call]:
        return self.node if isinstance(self.node, ast.Call) else None

    def argument(self, index: int, name: str) -> Optional[ast.AST]:
        """A positional-or-keyword argument, whichever way it was written."""
        call = self.call
        if call is None:
            return None
        for keyword in call.keywords:
            if keyword.arg == name:
                return keyword.value
        return call.args[index] if len(call.args) > index else None

    def message(self) -> Optional[str]:
        node = self.argument(0, "message")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.JoinedStr):
            return "".join(v.value for v in node.values
                           if isinstance(v, ast.Constant) and isinstance(v.value, str))
        return None

    def keyword_literal(self, name: str) -> Optional[object]:
        node = self.argument(-1, name)
        if node is None:
            return None
        try:
            return ast.literal_eval(node)
        except (ValueError, SyntaxError):
            return _UNREADABLE_LITERAL

    def has_keyword(self, name: str) -> bool:
        call = self.call
        return call is not None and any(k.arg == name for k in call.keywords)

    def deprecated_name(self) -> str:
        """What is being deprecated, as far as the source says."""
        if self.kind == "decorator" and self.function is not None:
            return self.function.name
        return self.function.name if self.function is not None else self.path


_UNREADABLE_LITERAL = object()


def _deprecations(bundle: EvidenceBundle) -> Iterator[tuple[str, pa.PyModule, Optional[Deprecation]]]:
    """Every deprecation the agent introduced in library code.

    Yields ``None`` for a file that would not parse, so the caller turns it into an
    ``Unreadable`` target rather than silently reporting that no deprecation was added.
    """
    for path, module in _modules(bundle, docs=True):
        if not module.ok:
            yield path, module, None
            continue
        for call in module.calls:
            if call.short != DEPRECATION_CALL or not _owns(bundle, path, call.span()):
                continue
            yield path, module, Deprecation(
                path, "call", call.span(), call.node, module,
                module.enclosing_function(call.lineno))
        for function in module.functions:
            decorator = function.decorator(DEPRECATED_DECORATOR)
            if decorator is None or not _owns(bundle, path, function.span()):
                continue
            yield path, module, Deprecation(
                path, "decorator", (decorator.lineno, decorator.lineno),
                decorator.node, module, function)


def _deprecation_targets(bundle: EvidenceBundle, prefix: str = "depr") -> list[Target]:
    """The antecedent almost every rule here shares: a deprecation was introduced."""
    targets = []
    for path, module, dep in _deprecations(bundle):
        if dep is None:
            targets.append(_unreadable_target(path, module))
            continue
        targets.append(Target(
            key=f"{prefix}:{path}:{dep.span[0]}", file=path, line_span=dep.span,
            source="patch", payload=(dep, bundle),
            snippet=f"{dep.kind} deprecating {dep.deprecated_name()}",
        ))
    return targets


def _target(key, path, span, payload, snippet="") -> Target:
    return Target(key=key, file=path, line_span=span, source="patch",
                  payload=payload, snippet=snippet[:200])


def _added_lines(bundle: EvidenceBundle, path: str) -> tuple[tuple[int, str], ...]:
    change = bundle.files.get(path)
    return change.added_lines if change else ()


def _active_deprecations_added(bundle: EvidenceBundle) -> tuple[str, ...]:
    return tuple(text for _, text in _added_lines(bundle, ACTIVE_DEPRECATIONS))


def _paragraphs(text: str) -> list[str]:
    return [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


# --- optional dependencies and test helpers ------------------------------------------


@rule(id="SYMPY-C151", category=CATEGORY, ownership="touched", reads=("files",))
class LibraryOptionalDependencyImports:
    """Pre-condition: each reference the agent's library code makes to an optional
    dependency, by plain import or by `import_module()`.
    Pass condition: it goes through `sympy.external.import_module()`, so an absent
    dependency yields `None` rather than breaking the import."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _optional_dependency_targets(b, tests_only=False)

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        how, name = t.payload
        if how == "import_module":
            return Satisfied()
        return Violated(f"library code imports optional dependency `{name}` directly; "
                        f"use {IMPORT_MODULE}({name!r})")


def _optional_dependency_targets(b: EvidenceBundle, *, tests_only: bool) -> list[Target]:
    """Shared with C107, which asks the same question of test code."""
    targets = []
    for path, module in _modules(b, tests_only=tests_only, docs=not tests_only):
        if not module.ok:
            targets.append(_unreadable_target(path, module))
            continue
        for site in module.import_sites:
            head = (site.module or site.origin).split(".")[0]
            if head in OPTIONAL_DEPENDENCIES and _owns(b, path, (site.lineno, site.lineno)):
                targets.append(_target(f"optdep:{path}:{site.lineno}", path,
                                       (site.lineno, site.lineno), ("import", head),
                                       f"import {site.origin}"))
        for call in module.calls:
            if call.short != IMPORT_MODULE or not call.args:
                continue
            arg = call.args[0]
            if not (isinstance(arg, ast.Constant) and isinstance(arg.value, str)):
                continue
            if not _owns(b, path, call.span()):
                continue
            name = arg.value.split(".")[0]
            if name in OPTIONAL_DEPENDENCIES:
                targets.append(_target(f"optdep:{path}:{call.lineno}", path, call.span(),
                                       ("import_module", name),
                                       f"{IMPORT_MODULE}({name!r})"))
    return targets


@rule(id="SYMPY-C152", category=CATEGORY, ownership="touched", reads=("files",))
class TestsUseSympyPytestWrappers:
    """Pre-condition: each `pytest.<helper>` the agent used in a test module, where SymPy
    publishes its own wrapper.
    Pass condition: none -- the wrapper from `sympy.testing.pytest` must be used instead,
    so any direct use is the violation."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module in _modules(b, tests_only=True):
            if not module.ok:
                targets.append(_unreadable_target(path, module))
                continue
            for site in module.import_sites:
                if site.module.split(".")[0] == "pytest" and site.name in PYTEST_WRAPPED \
                        and _owns(b, path, (site.lineno, site.lineno)):
                    targets.append(_target(f"pytest-import:{path}:{site.lineno}", path,
                                           (site.lineno, site.lineno),
                                           ("import", site.name),
                                           f"from pytest import {site.name}"))
            for call in module.calls:
                head, _, rest = call.func.partition(".")
                if head != "pytest" or not rest:
                    continue
                if rest.split(".")[0] in PYTEST_WRAPPED and _owns(b, path, call.span()):
                    targets.append(_target(f"pytest-call:{path}:{call.lineno}", path,
                                           call.span(), ("call", call.func), call.func))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        how, name = t.payload
        verb = "imports" if how == "import" else "calls"
        return Violated(f"{verb} `{name}` from pytest directly; use the "
                        f"sympy.testing.pytest wrapper")


@rule(id="SYMPY-C153", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class OptionalDependencyTestsStaySkippable:
    """Pre-condition: each test module the agent wrote that needs an optional dependency.
    Pass condition: it can still be collected without that dependency, by calling
    `skip("<reason>")` or setting a module-level `skip = True`.

    "Needs an optional dependency" is read from the module's own imports and
    `import_module()` calls, which is a stand-in for actually requiring it -- hence the
    heuristic flag.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module in _modules(b, tests_only=True):
            if not module.ok:
                targets.append(_unreadable_target(path, module))
                continue
            deps = _dependencies_used(module)
            if deps and any(_owns(b, path, (n, n)) for n in _dependency_lines(module)):
                targets.append(_target(f"optdep-skip:{path}", path, None,
                                       (module, sorted(deps)), ", ".join(sorted(deps))))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        module, deps = t.payload
        if any(c.short == SKIP_HELPER for c in module.calls):
            return Satisfied("calls skip()")
        if _module_skip_flag(module):
            return Satisfied("sets module-level skip = True")
        return Violated(f"needs {deps[:3]} but neither calls skip() nor sets "
                        f"`skip = True`, so collection breaks without the dependency")


def _dependencies_used(module: pa.PyModule) -> set[str]:
    found = {(s.module or s.origin).split(".")[0] for s in module.import_sites}
    for call in module.calls:
        if call.short == IMPORT_MODULE and call.args:
            arg = call.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                found.add(arg.value.split(".")[0])
    return found & OPTIONAL_DEPENDENCIES


def _dependency_lines(module: pa.PyModule) -> list[int]:
    lines = [s.lineno for s in module.import_sites
             if (s.module or s.origin).split(".")[0] in OPTIONAL_DEPENDENCIES]
    lines += [c.lineno for c in module.calls if c.short == IMPORT_MODULE]
    return lines


def _module_skip_flag(module: pa.PyModule) -> bool:
    for node in ast.walk(module.tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "skip" for t in node.targets
        ):
            return True
    return False


# --- backwards-incompatible change ---------------------------------------------------


@rule(id="SYMPY-C239", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class BreakingChangeDocumentsMigration:
    """Pre-condition: each public definition the agent removed from library code.
    Pass condition: the contribution documents how users should update their code.

    Reading a removed public name as a backwards-incompatible change is a stand-in: some
    removals are internal refactors whose name merely looks public. Flagged accordingly.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module in _modules(b, docs=True):
            change = b.files[path]
            if change.base_text is None or change.head_text is None:
                continue
            base = pa.parse_module(change.base_text, path)
            if not (base.ok and module.ok):
                targets.append(_unreadable_target(path, module if not module.ok else base))
                continue
            for name in sorted(_public_names(base) - _public_names(module)):
                targets.append(_target(f"removed:{path}:{name}", path, None,
                                       (name, b), f"removed {name}"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        name, bundle = t.payload
        if _documents_migration(bundle, name):
            return Satisfied()
        return Violated(f"removed public `{name}` without documenting how users should "
                        f"update their code")


def _public_names(module: pa.PyModule) -> set[str]:
    names = {f.name for f in module.functions if not f.name.startswith("_")}
    for node in ast.walk(module.tree):
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            names.add(node.name)
    return names


def _documents_migration(bundle: EvidenceBundle, name: str) -> bool:
    """Migration guidance anywhere the contribution adds prose, or in the PR text."""
    word = re.compile(rf"\b{re.escape(name)}\b")
    for path in sorted(bundle.files):
        if path.endswith(".py") and not pa.is_test_path(path):
            continue
        for _, text in _added_lines(bundle, path):
            if word.search(text) and _MIGRATION.search(text):
                return True
    if bundle.pr_text and word.search(bundle.pr_text) \
            and _MIGRATION.search(bundle.pr_text):
        return True
    return False


# --- the deprecated API's behaviour: Phase 5 -----------------------------------------


@rule(id="SYMPY-C240", category=CATEGORY, ownership="touched",
      reads=("files", "deprecated_api_run"))
class OldApiKeepsWorking:
    """Pre-condition: each deprecation the agent introduced.
    Pass condition: the old API still behaves as before, changed only by a suppressible
    warning -- withheld, because that is only observable by calling it."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _deprecation_targets(b, "old-api")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        return Undetermined("tool_missing",
                            "unchanged behaviour needs the deprecated API called; Phase 5")


@rule(id="SYMPY-C241", category=CATEGORY, ownership="touched",
      reads=("files", "deprecated_api_run"))
class WarningIsAvoidable:
    """Pre-condition: each deprecation the agent introduced.
    Pass condition: the documented migration silences the warning and the replacement API
    does not itself warn -- withheld, because that needs both paths executed."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _deprecation_targets(b, "avoidable")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        return Undetermined("tool_missing",
                            "whether the replacement warns needs it called; Phase 5")


@rule(id="SYMPY-C243", category=CATEGORY, ownership="touched",
      reads=("files", "deprecated_api_run"))
class ReplacementAvailableSameVersion:
    """Pre-condition: each deprecation the agent introduced.
    Pass condition: a replacement usage exists in this same version that stops the
    warning -- withheld, because confirming it needs the replacement executed."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _deprecation_targets(b, "replacement")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        return Undetermined("tool_missing",
                            "a working replacement needs both paths run; Phase 5")


# --- the deprecation call itself -----------------------------------------------------


@rule(id="SYMPY-C246", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class InternalUsesMigratedFirst:
    """Pre-condition: each deprecation the agent introduced.
    Pass condition: the contribution leaves no use of the deprecated name outside the
    deprecation site itself.

    Only the patch is visible, so a use elsewhere in the repository cannot be seen; this
    checks what the contribution itself still calls, which is a lower bound.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _deprecation_targets(b, "migrate")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        dep, bundle = t.payload
        name = dep.deprecated_name()
        if not name or name == dep.path:
            return Undetermined("parse_error", "cannot tell what is being deprecated")
        stale = []
        for path, module in _modules(bundle):
            if not module.ok:
                continue
            for call in module.calls:
                if call.short != name:
                    continue
                if path == dep.path and dep.span[0] <= call.lineno <= dep.span[1]:
                    continue
                if dep.function is not None and path == dep.path \
                        and dep.function.lineno <= call.lineno <= dep.function.end_lineno:
                    continue  # the deprecated definition may still reference itself
                if _owns(bundle, path, call.span()):
                    stale.append(f"{path}:{call.lineno}")
        if stale:
            return Violated(f"still calls deprecated `{name}` at {stale[:5]}")
        return Satisfied()


@rule(id="SYMPY-C247", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class MessageNamesApiAndReplacement:
    """Pre-condition: each `sympy_deprecation_warning(...)` message the agent wrote.
    Pass condition: it names the deprecated API in context and its replacement.

    "Names the replacement" is judged by migration wording plus a second identifier, which
    is a proxy for meaning it.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _message_targets(b, "msg-api")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        dep, message = t.payload
        name = dep.deprecated_name()
        if name and name not in message:
            return Violated(f"message does not name the deprecated API `{name}`")
        if not _MIGRATION.search(message):
            return Violated("message states no replacement to migrate to")
        return Satisfied()


def _message_targets(b: EvidenceBundle, prefix: str) -> list[Target]:
    """Deprecations whose message is a readable string literal."""
    targets = []
    for target in _deprecation_targets(b, prefix):
        if isinstance(target.payload, Unreadable):
            targets.append(target)
            continue
        dep, _ = target.payload
        message = dep.message()
        if message is None:
            continue
        targets.append(_target(target.key, target.file, target.line_span,
                               (dep, message), message[:160]))
    return targets


@rule(id="SYMPY-C248", category=CATEGORY, ownership="touched", reads=("files",))
class DeprecationSetsSinceVersion:
    """Pre-condition: each deprecation the agent introduced.
    Pass condition: it sets `deprecated_since_version` to a release version with no
    `.dev` suffix.

    Whether that version equals the one in `sympy/release.py` is not checked: the release
    module is not part of the contribution, so the bundle does not carry it. The form is.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _deprecation_targets(b, "since")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        dep, _ = t.payload
        if not dep.has_keyword(SINCE_VERSION):
            return Violated(f"no {SINCE_VERSION}=")
        value = dep.keyword_literal(SINCE_VERSION)
        if value is _UNREADABLE_LITERAL:
            return Undetermined("parse_error", f"{SINCE_VERSION} is not a literal")
        text = str(value)
        if _DEV_SUFFIX.search(text):
            return Violated(f"{SINCE_VERSION}={text!r} carries a .dev suffix")
        if not _VERSION.match(text):
            return Violated(f"{SINCE_VERSION}={text!r} is not a release version")
        return Satisfied()


@rule(id="SYMPY-C249", category=CATEGORY, ownership="touched", reads=("files",))
class DeprecationSetsCrossReferenceTarget:
    """Pre-condition: each deprecation the agent introduced.
    Pass condition: it sets `active_deprecations_target`, and if the contribution also
    edits `active-deprecations.md`, that target is defined there."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _deprecation_targets(b, "xref")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        dep, bundle = t.payload
        if not dep.has_keyword(TARGET_KEYWORD):
            return Violated(f"no {TARGET_KEYWORD}=")
        value = dep.keyword_literal(TARGET_KEYWORD)
        if value is _UNREADABLE_LITERAL or not isinstance(value, str) or not value:
            return Violated(f"{TARGET_KEYWORD} is not a usable target name")
        added = _active_deprecations_added(bundle)
        if not added:
            return Satisfied(f"{TARGET_KEYWORD}={value!r}")
        defined = {m.group(1) for line in added if (m := _MYST_TARGET.match(line.strip()))}
        if value in defined:
            return Satisfied()
        return Violated(f"{TARGET_KEYWORD}={value!r} is defined nowhere in the "
                        f"active-deprecations section the contribution adds ({sorted(defined)})")


@rule(id="SYMPY-C250", category=CATEGORY, ownership="touched", reads=("files",))
class DeprecationSetsStacklevel:
    """Pre-condition: each `sympy_deprecation_warning(...)` the agent wrote.
    Pass condition: it passes `stacklevel`, so the warning points at the user's call."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [t for t in _deprecation_targets(b, "stacklevel")
                if isinstance(t.payload, Unreadable) or t.payload[0].kind == "call"]

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        dep, _ = t.payload
        if dep.has_keyword(STACKLEVEL):
            return Satisfied()
        return Violated(f"{DEPRECATION_CALL}(...) sets no {STACKLEVEL}")


@rule(id="SYMPY-C258", category=CATEGORY, ownership="touched", reads=("files",))
class NoDirectDeprecationWarning:
    """Pre-condition: each reference the agent's library code makes to
    `SymPyDeprecationWarning`.
    Pass condition: the warning is raised through `sympy_deprecation_warning(...)` or
    `@deprecated(...)`, not instantiated or emitted directly."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module in _modules(b, docs=True):
            if not module.ok:
                targets.append(_unreadable_target(path, module))
                continue
            for node in ast.walk(module.tree):
                if not isinstance(node, ast.Call):
                    continue
                name = pa.dotted_name(node.func).split(".")[-1]
                span = pa.span_of(node)
                if name == DEPRECATION_WARNING and _owns(b, path, span):
                    targets.append(_target(f"direct:{path}:{node.lineno}", path, span,
                                           ("instantiated", node.lineno),
                                           f"{DEPRECATION_WARNING}(...)"))
                elif name in ("warn", "warn_explicit") and _owns(b, path, span):
                    if any(pa.dotted_name(a).split(".")[-1] == DEPRECATION_WARNING
                           for a in node.args):
                        targets.append(_target(f"direct:{path}:{node.lineno}", path, span,
                                               ("warned", node.lineno),
                                               f"warn(..., {DEPRECATION_WARNING})"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        how, lineno = t.payload
        verb = "instantiates" if how == "instantiated" else "passes"
        return Violated(f"line {lineno} {verb} {DEPRECATION_WARNING} directly; use "
                        f"{DEPRECATION_CALL}(...) or @{DEPRECATED_DECORATOR}(...)")


@rule(id="SYMPY-C259", category=CATEGORY, ownership="touched", reads=("files",))
class MessageIsOneWrappedParagraph:
    """Pre-condition: each `sympy_deprecation_warning(...)` message the agent wrote.
    Pass condition: it is a single paragraph whose prose lines are within 80 characters."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _message_targets(b, "msg-wrap")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        _, message = t.payload
        if len(_paragraphs(message)) > 1:
            return Violated(f"message is {len(_paragraphs(message))} paragraphs, not one")
        long = [len(line) for line in message.split("\n")
                if len(line) > MESSAGE_LINE_LIMIT and " " in line.strip()]
        if long:
            return Violated(f"{len(long)} prose line(s) exceed {MESSAGE_LINE_LIMIT} "
                            f"characters (longest {max(long)})")
        return Satisfied()


@rule(id="SYMPY-C260", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class MessageExplainsMigrationOnly:
    """Pre-condition: each `sympy_deprecation_warning(...)` message the agent wrote.
    Pass condition: it explains migration and carries no rationale, version metadata or
    active-deprecations URL, all of which the call's own arguments already supply.

    Rationale is detected lexically, so this is a proxy rather than a decision.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _message_targets(b, "msg-scope")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        _, message = t.payload
        if _URL.search(message):
            return Violated("message contains a URL; active_deprecations_target supplies it")
        if re.search(r"\bversion\s+\d|\bsince\s+\d|\bdeprecated in \d", message, re.I):
            return Violated("message repeats version metadata that "
                            f"{SINCE_VERSION} already supplies")
        if _RATIONALE.search(message):
            return Violated("message explains rationale; it should only explain migration")
        if not _MIGRATION.search(message):
            return Violated("message explains no migration")
        return Satisfied()


@rule(id="SYMPY-C261", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class MessageIsPlainText:
    """Pre-condition: each `sympy_deprecation_warning(...)` message the agent wrote.
    Pass condition: it is plain text, with no RST or Markdown markup -- the message is
    printed to a console, not rendered.

    Markup is detected by its common spellings, so unusual constructs may pass.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _message_targets(b, "msg-plain")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        _, message = t.payload
        if match := _MARKUP.search(message):
            return Violated(f"message contains markup {match.group(0)!r}; it is printed "
                            f"to a console, not rendered")
        return Satisfied()


# --- docstring notes ------------------------------------------------------------------


@rule(id="SYMPY-C252", category=CATEGORY, ownership="touched", reads=("files",))
class DocstringCarriesDeprecatedNote:
    """Pre-condition: each deprecation the agent introduced on a documented definition.
    Pass condition: that definition's docstring carries a `.. deprecated:: <version>`
    note."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _docstring_deprecation_targets(b, "docnote")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        dep, docstring = t.payload
        if _DEPRECATED_DIRECTIVE.search(docstring.text):
            return Satisfied()
        return Violated(f"`{dep.deprecated_name()}` is deprecated but its docstring has "
                        f"no `.. deprecated::` note")


def _docstring_deprecation_targets(b: EvidenceBundle, prefix: str) -> list[Target]:
    """Deprecations whose definition has a docstring to annotate."""
    targets = []
    for target in _deprecation_targets(b, prefix):
        if isinstance(target.payload, Unreadable):
            targets.append(target)
            continue
        dep, _ = target.payload
        if dep.function is None:
            continue
        docstring = next((d for d in dep.module.docstrings
                          if d.def_span == dep.function.span()), None)
        if docstring is None:
            continue
        targets.append(_target(target.key, target.file, docstring.span(),
                               (dep, docstring), f"{docstring.owner} docstring"))
    return targets


@rule(id="SYMPY-C262", category=CATEGORY, ownership="touched", reads=("files",))
class DeprecatedDirectiveFollowsSummary:
    """Pre-condition: each `.. deprecated::` note in a docstring the agent deprecated.
    Pass condition: it sits immediately below the docstring's summary line."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [t for t in _docstring_deprecation_targets(b, "docpos")
                if isinstance(t.payload, Unreadable)
                or _DEPRECATED_DIRECTIVE.search(t.payload[1].text)]

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        dep, docstring = t.payload
        lines = docstring.text.split("\n")
        directive = next(i for i, line in enumerate(lines)
                         if _DEPRECATED_DIRECTIVE.match(line))
        # Immediately below the summary: the summary is line 0, then at most one blank.
        if directive <= 2 and all(not lines[i].strip() for i in range(1, directive)):
            return Satisfied()
        return Violated(f"`.. deprecated::` sits at line {directive + 1} of the docstring, "
                        f"not immediately below the summary")


@rule(id="SYMPY-C263", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class DeprecatedDirectiveIsOneParagraph:
    """Pre-condition: each `.. deprecated::` note in a docstring the agent deprecated.
    Pass condition: it is at most one paragraph and names both the deprecated feature and
    its replacement.

    "Names the replacement" is judged by migration wording, which is a proxy.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [t for t in _docstring_deprecation_targets(b, "docpara")
                if isinstance(t.payload, Unreadable)
                or _DEPRECATED_DIRECTIVE.search(t.payload[1].text)]

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        dep, docstring = t.payload
        body = _directive_body(docstring.text)
        if len(_paragraphs(body)) > 1:
            return Violated(f"the note runs to {len(_paragraphs(body))} paragraphs")
        if not _MIGRATION.search(body):
            return Violated("the note names no replacement")
        return Satisfied()


def _directive_body(text: str) -> str:
    """The indented block belonging to the first `.. deprecated::` directive."""
    lines = text.split("\n")
    start = next((i for i, line in enumerate(lines)
                  if _DEPRECATED_DIRECTIVE.match(line)), None)
    if start is None:
        return ""
    indent = len(lines[start]) - len(lines[start].lstrip())
    body = []
    for line in lines[start + 1:]:
        if line.strip() and (len(line) - len(line.lstrip())) <= indent:
            break
        body.append(line)
    return "\n".join(body).strip()


# --- active-deprecations.md ------------------------------------------------------------


@rule(id="SYMPY-C253", category=CATEGORY, ownership="touched", reads=("files",))
class AddsActiveDeprecationsSection:
    """Pre-condition: each deprecation the agent introduced.
    Pass condition: the contribution adds a section to `active-deprecations.md` under a
    version heading."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _deprecation_targets(b, "active-add")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        _, bundle = t.payload
        if ACTIVE_DEPRECATIONS not in bundle.files:
            return Violated(f"added a deprecation without touching {ACTIVE_DEPRECATIONS}")
        added = _active_deprecations_added(bundle)
        if not any(_H3.match(line) for line in added):
            return Violated(f"edited {ACTIVE_DEPRECATIONS} but added no section heading")
        return Satisfied()


def _active_section_targets(b: EvidenceBundle, prefix: str) -> list[Target]:
    """The antecedent for the content rules: an active-deprecations section was added."""
    added = _active_deprecations_added(b)
    if not added:
        return []
    return [_target(f"{prefix}:{ACTIVE_DEPRECATIONS}", ACTIVE_DEPRECATIONS, None,
                    (added, b), "\n".join(added)[:200])]


@rule(id="SYMPY-C254", category=CATEGORY, ownership="touched", reads=("files",))
class ActiveSectionDefinesTarget:
    """Pre-condition: the contribution adds lines to `active-deprecations.md`.
    Pass condition: a `(…deprecation…)=` cross-reference target is defined before the
    section's heading."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _active_section_targets(b, "active-target")

    def pass_condition(self, t: Target):
        added, _ = t.payload
        headings = [i for i, line in enumerate(added) if _H3.match(line)]
        if not headings:
            return Violated("no section heading was added")
        for index in headings:
            preceding = [line.strip() for line in added[:index] if line.strip()]
            if not preceding or not _MYST_TARGET.match(preceding[-1]):
                return Violated(f"the heading {added[index].strip()!r} has no "
                                f"`(...deprecation...)=` target immediately above it")
        return Satisfied()


@rule(id="SYMPY-C264", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class ActiveSectionExplainsTheChange:
    """Pre-condition: the contribution adds lines to `active-deprecations.md`.
    Pass condition: the section says what is deprecated, what replaces it, and why.

    All three are judged from wording, so this is a proxy for the content being adequate.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _active_section_targets(b, "active-explain")

    def pass_condition(self, t: Target):
        added, _ = t.payload
        text = "\n".join(added)
        missing = []
        if not any(_H3.match(line) for line in added):
            missing.append("what is deprecated (no heading)")
        if not _MIGRATION.search(text):
            missing.append("a replacement")
        if not _WHY.search(text):
            missing.append("why the change was made")
        if missing:
            return Violated(f"section does not state {', '.join(missing)}")
        return Satisfied()


@rule(id="SYMPY-C265", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class ActiveSectionUsesLevelThreeHeading:
    """Pre-condition: the contribution adds lines to `active-deprecations.md`.
    Pass condition: the entry is a level-3 heading named for the deprecated item.

    Whether the heading sits under the *corresponding* version cannot be seen from added
    lines alone when the version heading is pre-existing context, so only the level and a
    non-empty name are graded.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _active_section_targets(b, "active-heading")

    def pass_condition(self, t: Target):
        added, _ = t.payload
        headings = [line.strip() for line in added if line.strip().startswith("#")]
        if not headings:
            return Violated("no heading was added")
        wrong = [h for h in headings if not _H3.match(h)]
        if wrong:
            return Violated(f"heading(s) are not level 3: {wrong[:3]}")
        empty = [h for h in headings if not _H3.match(h).group("title").strip()]
        if empty:
            return Violated("a level-3 heading names nothing")
        return Satisfied()


@rule(id="SYMPY-C266", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class ActiveSectionNamesSubmodule:
    """Pre-condition: each deprecation the agent introduced outside a top-level export,
    for which an active-deprecations section was added.
    Pass condition: that section identifies the submodule the object is defined in.

    Whether an object is exported from top-level `sympy` is not visible in the patch, so
    the pre-condition fires on every added deprecation and the check looks for the
    defining module path anywhere in the section.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not _active_deprecations_added(b):
            return []
        targets = []
        for target in _deprecation_targets(b, "active-submodule"):
            if isinstance(target.payload, Unreadable):
                targets.append(target)
                continue
            dep, bundle = target.payload
            targets.append(_target(target.key, target.file, target.line_span,
                                   (dep, _active_deprecations_added(bundle)),
                                   dep.deprecated_name()))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        dep, added = t.payload
        text = "\n".join(added)
        module_path = dep.path.removesuffix(".py").replace("/", ".")
        parts = module_path.split(".")
        if any(p in text for p in parts[1:]) or module_path in text:
            return Satisfied()
        return Violated(f"section names no submodule for `{dep.deprecated_name()}`, "
                        f"defined in {module_path}")


# --- test and release notes ------------------------------------------------------------


@rule(id="SYMPY-C255", category=CATEGORY, ownership="touched", reads=("files",))
class DeprecationHasAWarnsTest:
    """Pre-condition: each deprecation the agent introduced.
    Pass condition: the contribution adds a test whose deprecated call sits inside
    `with warns_deprecated_sympy():` and which also checks the behaviour still holds."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _deprecation_targets(b, "depr-test")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        dep, bundle = t.payload
        for path, module in _modules(bundle, tests_only=True):
            if not module.ok:
                continue
            for node in ast.walk(module.tree):
                if not isinstance(node, ast.With):
                    continue
                if not any(_context_name(item) == WARNS_DEPRECATED for item in node.items):
                    continue
                if not _owns(bundle, path, pa.span_of(node)):
                    continue
                body = ast.dump(ast.Module(body=list(node.body), type_ignores=[]))
                function = module.enclosing_function(node.lineno)
                asserts = function is not None and bool(
                    module.asserts_within(function.span()))
                if not asserts:
                    return Violated(f"{path}: the {WARNS_DEPRECATED}() test asserts "
                                    f"nothing about continued behaviour")
                if dep.deprecated_name() and dep.deprecated_name() not in body:
                    continue
                return Satisfied(f"{path}:{node.lineno}")
        return Violated(f"no test wraps the deprecated call in "
                        f"`with {WARNS_DEPRECATED}():`")


def _context_name(item: ast.withitem) -> str:
    node = item.context_expr
    node = node.func if isinstance(node, ast.Call) else node
    return pa.dotted_name(node).split(".")[-1]


@rule(id="SYMPY-C256", category=CATEGORY, ownership="touched",
      reads=("files", "commands"))
class ValidatesDeprecationWithBinTest:
    """Pre-condition: each deprecation the agent introduced.
    Pass condition: `python bin/test` was run and reported no failure."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _deprecation_targets(b, "depr-validate")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        from compliance.rules.sympy.tests import BIN_TEST, _ran, _runner_verdict

        _, bundle = t.payload
        return _runner_verdict(_ran(bundle, BIN_TEST), "bin/test")


@rule(id="SYMPY-C268", category=CATEGORY, ownership="created",
      reads=("files", "pr_text"))
class BreakingChangeInReleaseNotes:
    """Pre-condition: the contribution introduces a deprecation or removes a public API.
    Pass condition: its release-notes block carries a `BREAKING CHANGE` entry."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = _deprecation_targets(b, "breaking")
        readable = [t for t in targets if not isinstance(t.payload, Unreadable)]
        if not readable:
            # No deprecation. A removal of a public name is the other way in.
            removals = [t for t in BreakingChangeDocumentsMigration().precondition(b)
                        if not isinstance(t.payload, Unreadable)]
            if not removals:
                return [t for t in targets if isinstance(t.payload, Unreadable)]
        return [_target(f"breaking:{b.instance_id}", None, None, b,
                        "deprecation or public removal")]

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        bundle: EvidenceBundle = t.payload
        pr = rn.parse(bundle.pr_text)
        if pr.is_empty:
            return Violated("no pull-request description, so no release-notes block")
        if not pr.release_notes.present:
            return Violated("no release-notes block to carry a BREAKING CHANGE entry")
        text = "\n".join(e.text for e in pr.release_notes.entries) or ""
        if BREAKING_CHANGE.lower() in text.lower():
            return Satisfied()
        return Violated(f"release-notes block has no {BREAKING_CHANGE} entry")

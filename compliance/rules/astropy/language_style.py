"""astropy: Language and framework style -- 16 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

**Six rules come out of one paragraph of codeguide.html** -- the one about standard output,
warnings and errors (C098, C099, C100, C101, C102, C103). They divide the same handful of
call sites between them, and each one's pre-condition therefore has to say which situation
it is about rather than which spelling it wants. C098 fires on every ``print`` the agent
wrote; C103 fires on informational output that is *not* the user-requested kind C098
permits. That exclusion is the §7.5 narrowing for this pack: read literally, a
user-requested ``print`` would violate C103, and the two rules would contradict each other
on the same line. It is pinned by a no-target test rather than remembered.

**Three rules name a tool.** C107 is graded from the stored lint report and withholds when
none exists. C105 and C106 are graded from the patch by narrow proxies, both declared:
formatting that ``ruff format`` always changes whatever the configuration, and the group
order ``isort`` imposes -- never the within-group alphabetical order, which is not checked
at all.

**C118 cannot be answered from a patch, and does not pretend to be.** Whether a parser
accepts its class's own ``__str__`` output is decided by running both; it declares
``full_suite_run`` and withholds, so the row keeps its applicability count without a
verdict being invented for it.
"""

from __future__ import annotations

import ast
import re
from typing import Iterator, Optional

from compliance.core import ownership as own
from compliance.core.models import (EvidenceBundle, Satisfied, Target, Undetermined,
                                    Violated)
from compliance.core.registry import rule
from compliance.extractors import imports as im
from compliance.extractors import python_ast as pa
from compliance.rules.astropy._common import (LICENSE_LINE, PACKAGE, added_lines,
                                              is_source_path, is_test_path, modules,
                                              python_files, target)

CATEGORY = "Language and framework style"

#: astropy is its own first party; the shared extractor takes the name as a parameter
#: rather than knowing it (§7.4).
POLICY = im.GroupPolicy(first_party=frozenset({"astropy"}))

#: Module names that say "general-purpose helpers" rather than "part of this sub-package".
_UTILITY_NAMES = ("utils", "util", "helpers", "helper", "misc", "common", "tools")

#: Functions whose whole purpose is output the user asked for. codeguide's own examples
#: are ``print_header(...)`` and ``list_catalogs(...)``.
_OUTPUT_FUNCTION = re.compile(
    r"^(print|list|show|display|report|dump|pprint|info|describe|summar)\w*$|"
    r"^(main|_main)$|_(print|report|summary)$", re.I)

_TRAILING_WS = re.compile(r"[ \t]+$")
_TAB_INDENT = re.compile(r"^\t")

_BUILTIN_WARNINGS = frozenset({
    "Warning", "UserWarning", "DeprecationWarning", "PendingDeprecationWarning",
    "SyntaxWarning", "RuntimeWarning", "FutureWarning", "ImportWarning",
    "UnicodeWarning", "BytesWarning", "ResourceWarning", "EncodingWarning",
})
_ASTROPY_USER_WARNING = "AstropyUserWarning"

_ACCESSOR = re.compile(r"^(get|set)_\w+$")
_PARSER_NAMES = ("parse", "from_string", "fromstring", "from_str", "read", "_parse")
_UNICODE_OUTPUT = "unicode_output"

_LOG_CALLS = ("log.info", "log.debug", "logger.info", "logger.debug",
              "logging.info", "logging.debug")
_ENCODING_LINE = re.compile(r"^#.*coding[:=]")


def _tail(name: str, n: int = 2) -> str:
    return ".".join(name.split(".")[-n:])


def _authored(bundle: EvidenceBundle, path: str) -> frozenset[int]:
    change = bundle.files.get(path)
    return change.authored_lines if change else frozenset()


def _library_modules(bundle: EvidenceBundle) -> list[tuple[str, pa.PyModule]]:
    """Parsed modules of the library code the agent touched -- tests excluded."""
    return [(p, m) for p, m in modules(bundle) if is_source_path(p)]


def _written_calls(bundle: EvidenceBundle, *, library_only: bool = True
                   ) -> Iterator[tuple[str, pa.PyModule, pa.CallSite]]:
    """Every call site on a line the agent wrote."""
    source = _library_modules(bundle) if library_only else modules(bundle)
    for path, module in source:
        authored = _authored(bundle, path)
        for call in module.calls:
            if call.lineno in authored:
                yield path, module, call


def _enclosing_name(module: pa.PyModule, lineno: int) -> str:
    function = module.enclosing_function(lineno)
    return function.name if function else ""


def _classes(module: pa.PyModule) -> Iterator[ast.ClassDef]:
    for node in ast.walk(module.tree):
        if isinstance(node, ast.ClassDef):
            yield node


def _methods(node: ast.ClassDef) -> Iterator[ast.AST]:
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield child


def _has_non_ascii_literal(node: ast.AST) -> Optional[str]:
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            if any(ord(ch) > 127 for ch in child.value):
                return child.value
    return None


def _mentions(node: ast.AST, name: str) -> bool:
    return name in ast.dump(node)


@rule(
    id="ASTROPY-C083",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a module the agent brought into
                          # existence, and placing it is the decision the rule is about
    reads=("files",),  # spec §5: the path is the whole question
    heuristic=True,
)
class GeneralUtilitiesLiveInAstropyUtils:
    """Pre-condition: each Python module the agent added under ``astropy/``.
    Pass condition: if it is a general-purpose utility module, it sits under
    ``astropy/utils/``.

    Heuristic on the **pass condition** (§6.2): *general utilities necessary for but not
    specific to the sub-package* is a judgement about what the code is for, approximated
    here by the names a contributor gives such a module -- ``utils``, ``helpers``,
    ``misc``, ``common``, ``tools``. A general-purpose helper filed under a descriptive
    name passes.

    Selecting every added module, rather than the misplaced ones, is what lets a correctly
    placed helper record a pass (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"utils:{path}", path, None, path, path)
                for path in python_files(b, mode="created")
                if path.startswith(PACKAGE) and not is_test_path(path)]

    def pass_condition(self, t: Target):
        path = t.payload
        stem = path.rsplit("/", 1)[-1][:-3]
        directory = path.rsplit("/", 1)[0] + "/"
        looks_general = stem in _UTILITY_NAMES or directory.rstrip("/").endswith(_UTILITY_NAMES)
        if looks_general and not directory.startswith(PACKAGE + "utils/"):
            return Violated(f"{path} is a general-purpose utility module outside "
                            f"astropy/utils/")
        return Satisfied(f"{path} is not a general-purpose utility module outside "
                         f"astropy/utils/")


@rule(
    id="ASTROPY-C098",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier; the line is inside library code
    reads=("files",),  # spec §5
    heuristic=True,
)
class PrintOnlyForRequestedOutput:
    """Pre-condition: each ``print()`` call the agent wrote in library code under
    ``astropy/``.
    Pass condition: it sits in a function whose job is output the user asked for.

    Heuristic on the **pass condition** (§6.2): *explicitly requested by the user* is an
    intention, approximated by the enclosing function's name -- codeguide's own examples
    are ``print_header`` and ``list_catalogs``. A ``print`` inside a differently-named
    public reporting function is reported as a violation and is not one.

    Test modules are excluded from the pre-condition: the rule is about what the library
    prints, and a print in a test is not library output.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, call in _written_calls(b):
            if call.func == "print":
                enclosing = _enclosing_name(module, call.lineno)
                out.append(target(f"print:{path}:{call.lineno}", path,
                                  (call.lineno, call.lineno), (path, call.lineno, enclosing),
                                  f"print() in {enclosing or 'module scope'}"))
        return out

    def pass_condition(self, t: Target):
        path, lineno, enclosing = t.payload
        if enclosing and _OUTPUT_FUNCTION.match(enclosing):
            return Satisfied(f"{path}:{lineno} prints from `{enclosing}`, which exists to "
                             f"produce output")
        return Violated(f"{path}:{lineno} calls print() from "
                        f"`{enclosing or 'module scope'}`, which is not a function the "
                        f"user asks for output from")


@rule(
    id="ASTROPY-C099",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ErrorsAreRaisedExceptionClasses:
    """Pre-condition: each place the agent's written code signals an error -- a ``raise``
    statement, ``sys.exit``, ``os._exit`` or an ``assert False``.
    Pass condition: it is a ``raise`` of a built-in or custom exception class.

    Heuristic on the **pre-condition** (§6.3): *an error condition* is not observable, so
    it is approximated by the ways code signals one. Selecting only ``raise`` statements
    would make the rule unfailable -- every target would already be the compliant form --
    which is §7.1 inverted in its subtler shape.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _library_modules(b):
            authored = _authored(b, path)
            for node in ast.walk(module.tree):
                if isinstance(node, ast.Raise) and node.lineno in authored:
                    out.append(target(f"error:{path}:{node.lineno}", path,
                                      (node.lineno, node.lineno), (path, node.lineno, node),
                                      "raise"))
                elif (isinstance(node, ast.Assert) and node.lineno in authored
                      and isinstance(node.test, ast.Constant) and not node.test.value):
                    out.append(target(f"error:{path}:{node.lineno}", path,
                                      (node.lineno, node.lineno), (path, node.lineno, node),
                                      "assert False"))
            for call in module.calls:
                if call.lineno in authored and _tail(module.origin(call.func)) in (
                        "sys.exit", "os._exit"):
                    out.append(target(f"error:{path}:{call.lineno}", path,
                                      (call.lineno, call.lineno),
                                      (path, call.lineno, call), call.func))
        return out

    def pass_condition(self, t: Target):
        path, lineno, node = t.payload
        if isinstance(node, ast.Raise):
            exc = node.exc
            if exc is None:
                return Satisfied(f"{path}:{lineno} re-raises the active exception")
            if isinstance(exc, ast.Constant):
                return Violated(f"{path}:{lineno} raises a literal rather than an "
                                f"exception class")
            return Satisfied(f"{path}:{lineno} raises "
                             f"{pa.dotted_name(exc.func if isinstance(exc, ast.Call) else exc)}")
        if isinstance(node, ast.Assert):
            return Violated(f"{path}:{lineno} signals an error with `assert False` rather "
                            f"than raising an exception class")
        return Violated(f"{path}:{lineno} signals an error with `{node.func}` rather than "
                        f"raising an exception class")


@rule(
    id="ASTROPY-C100",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class NoBareExceptionRaised:
    """Pre-condition: each ``raise`` of a named class the agent wrote.
    Pass condition: the class is not ``Exception`` itself.

    Not heuristic: the sentence names one token to avoid, the class raised is read off the
    syntax tree, and the comparison is exact. The corpus records the source's own hedge --
    "as much as possible" -- and the atomic rule drops it, so the hedge is not re-applied
    here.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _library_modules(b):
            authored = _authored(b, path)
            for node in ast.walk(module.tree):
                if not isinstance(node, ast.Raise) or node.lineno not in authored:
                    continue
                exc = node.exc
                if exc is None:
                    continue
                name = pa.dotted_name(exc.func if isinstance(exc, ast.Call) else exc)
                if name:
                    out.append(target(f"bare-exception:{path}:{node.lineno}", path,
                                      (node.lineno, node.lineno), (path, node.lineno, name),
                                      f"raise {name}"))
        return out

    def pass_condition(self, t: Target):
        path, lineno, name = t.payload
        if name.split(".")[-1] == "Exception":
            return Violated(f"{path}:{lineno} raises the nondescript `Exception` class")
        return Satisfied(f"{path}:{lineno} raises `{name}`")


@rule(
    id="ASTROPY-C101",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class WarningsGoThroughWarningsWarn:
    """Pre-condition: each place the agent's written code emits a warning, by whatever
    means.
    Pass condition: it is ``warnings.warn(message, warning_class)`` -- the call, with the
    class given.

    Heuristic on the **pre-condition** (§6.3): *emitting a warning* is approximated by the
    vocabulary of calls that do it -- ``warnings.warn``, a bare ``warn``, ``log.warning``,
    ``logger.warning``. A warning raised some other way is not selected. Selecting only
    ``warnings.warn`` calls would leave the rule unable to record the violation it exists
    to catch.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, call in _written_calls(b):
            resolved = module.origin(call.func)
            if _tail(resolved) == "warnings.warn" or resolved == "warn" or _tail(
                    resolved) in ("log.warning", "logger.warning", "logging.warning"):
                out.append(target(f"warn:{path}:{call.lineno}", path,
                                  (call.lineno, call.lineno),
                                  (path, call.lineno, resolved, call), call.func))
        return out

    def pass_condition(self, t: Target):
        path, lineno, resolved, call = t.payload
        if _tail(resolved) != "warnings.warn" and resolved != "warn":
            return Violated(f"{path}:{lineno} warns through `{call.func}` rather than "
                            f"`warnings.warn(message, warning_class)`")
        if len(call.args) < 2 and "category" not in call.keywords:
            return Violated(f"{path}:{lineno} calls warnings.warn without a warning class")
        return Satisfied(f"{path}:{lineno} uses warnings.warn(message, warning_class)")


@rule(
    id="ASTROPY-C102",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class WarningClassIsAstropyUserWarning:
    """Pre-condition: each ``warnings.warn`` call the agent wrote that names a warning
    class.
    Pass condition: that class is ``AstropyUserWarning`` or something inheriting from it.

    Heuristic on the **pass condition** (§6.2): inheritance cannot be resolved from a
    patch. A class defined in the contribution is followed one level to its bases; a name
    imported from ``astropy`` is accepted on the strength of where it comes from; a
    built-in warning class is a violation. A warning class defined elsewhere in the tree
    and not obviously astropy's is accepted, so this check shows the violation and cannot
    confirm the inheritance.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, call in _written_calls(b):
            if _tail(module.origin(call.func)) != "warnings.warn":
                continue
            node = call.args[1] if len(call.args) > 1 else call.keywords.get("category")
            if node is None:
                continue
            name = pa.dotted_name(node)
            if name:
                out.append(target(f"warning-class:{path}:{call.lineno}", path,
                                  (call.lineno, call.lineno),
                                  (path, call.lineno, name, module), name))
        return out

    def pass_condition(self, t: Target):
        path, lineno, name, module = t.payload
        short = name.split(".")[-1]
        if short == _ASTROPY_USER_WARNING:
            return Satisfied(f"{path}:{lineno} warns with {_ASTROPY_USER_WARNING}")
        if short in _BUILTIN_WARNINGS:
            return Violated(f"{path}:{lineno} warns with the built-in `{short}` rather "
                            f"than {_ASTROPY_USER_WARNING} or a subclass")
        for node in _classes(module):
            if node.name != short:
                continue
            bases = [pa.dotted_name(base).split(".")[-1] for base in node.bases]
            if _ASTROPY_USER_WARNING in bases:
                return Satisfied(f"{path}:{lineno} warns with `{short}`, defined here as a "
                                 f"subclass of {_ASTROPY_USER_WARNING}")
            if any(base in _BUILTIN_WARNINGS for base in bases):
                return Violated(f"{path}:{lineno} warns with `{short}`, defined here as a "
                                f"subclass of the built-in `{bases[0]}`")
        if module.origin(name).startswith("astropy"):
            return Satisfied(f"{path}:{lineno} warns with `{short}` from astropy")
        return Satisfied(f"{path}:{lineno} warns with `{short}`, which is not a built-in "
                         f"warning class")


@rule(
    id="ASTROPY-C103",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class InformationalMessagesGoThroughLog:
    """Pre-condition: each place the agent's written code emits an informational or
    debugging message that is not output the user asked for.
    Pass condition: it is ``log.info()`` or ``log.debug()``.

    The exclusion is the §7.5 narrowing this pack needs. C098 permits ``print`` for output
    the user explicitly requested; read literally, C103 would then fail the very same line.
    A ``print`` inside a function whose job is producing output is therefore not selected
    here, and a no-target test pins that resolution.

    Heuristic on the **pre-condition** (§6.3): *informational and debugging messages* is
    approximated by the calls that emit them -- ``print``, ``sys.stdout.write``, and the
    ``logging`` module's own info and debug entry points.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, call in _written_calls(b):
            resolved = module.origin(call.func)
            tail = _tail(resolved)
            enclosing = _enclosing_name(module, call.lineno)
            is_print = call.func == "print" or tail in ("sys.stdout.write", "stdout.write")
            if is_print and enclosing and _OUTPUT_FUNCTION.match(enclosing):
                continue  # C098 permits this line; grading it here would contradict it
            if is_print or tail in _LOG_CALLS:
                out.append(target(f"log:{path}:{call.lineno}", path,
                                  (call.lineno, call.lineno),
                                  (path, call.lineno, tail, call.func), call.func))
        return out

    def pass_condition(self, t: Target):
        path, lineno, tail, written = t.payload
        if tail in ("log.info", "log.debug"):
            return Satisfied(f"{path}:{lineno} uses `{tail}()`")
        return Violated(f"{path}:{lineno} emits an informational message through "
                        f"`{written}` rather than log.info() or log.debug()")


@rule(
    id="ASTROPY-C105",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- lines inside files that already existed
    reads=("files",),  # spec §5: decided from the submitted text
    heuristic=True,
)
class RuffFormatWouldChangeNothing:
    """Pre-condition: each Python file the agent wrote a line into.
    Pass condition: none of those lines carries formatting ``ruff format`` always removes
    -- trailing whitespace, or a tab in the indentation.

    Heuristic on the **pass condition** (§6.2), and narrow on purpose. The real answer is
    ``ruff format --diff``, which nothing in this instrument runs. Everything the formatter
    decides from configuration -- line length, quote style, magic trailing commas -- is
    deliberately not checked, because a proxy that guessed at project settings would report
    violations that are not violations. What is left holds under every configuration.
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
                return Violated(f"{path}:{lineno} has trailing whitespace, which "
                                f"`ruff format` removes")
            if _TAB_INDENT.match(text):
                return Violated(f"{path}:{lineno} is indented with a tab, which "
                                f"`ruff format` converts to spaces")
        return Satisfied(f"{len(written)} written line(s) carry neither trailing "
                         f"whitespace nor tab indentation")


@rule(
    id="ASTROPY-C106",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a file whose import block the agent edited
    reads=("files",),  # spec §5: the import block is in the patch
    heuristic=True,
)
class ImportsAreSorted:
    """Pre-condition: each Python file the agent edited whose leading import block holds at
    least two imports.
    Pass condition: the groups appear in the declared order and none is split in two.

    Heuristic on the **pass condition** (§6.2), and the flag is about *coverage* rather
    than about the check being fuzzy. isort decides three things -- which group each import
    belongs to, the order of the groups, and the alphabetical order within a group. This
    checks the first two exactly and the third not at all, so a file with correctly grouped
    but unsorted imports passes a rule ``ruff check --select I`` would fail.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b):
            text = b.files[path].head_text
            if text is None:
                continue
            lines = im.top_level(im.import_lines(source=text, policy=POLICY, path=path))
            block = im.leading_block(lines)
            if len(block) >= 2:
                out.append(target(f"isort:{path}", path, None, (path, block),
                                  f"{len(block)} import(s)"))
        return out

    def pass_condition(self, t: Target):
        path, block = t.payload
        problems = im.group_order_problems(block, policy=POLICY)
        if not problems:
            groups = [run.group for run in im.group_runs(block)]
            return Satisfied(f"{path} groups imports as {' then '.join(groups)}")
        first = problems[0]
        return Violated(f"{path}:{first.lineno} {first.kind}: {first.detail}")


@rule(
    id="ASTROPY-C107",
    category=CATEGORY,
    ownership="touched",  # spec §4.1
    reads=("files", "lint_run"),  # spec §5: graded from a tool run over base and head
)
class RuffChecksPass:
    """Pre-condition: the agent submitted Python code, which is what gets merged.
    Pass condition: ``ruff check`` reports no finding the base commit did not already have.

    Deliberately not "the agent ran ruff": the obligation is that the code passes, so a
    contribution that never ran the tool is judged rather than excused. A submitted module
    that will not parse fails here without any tool run, because invalid Python cannot pass
    a linter and no evidence beyond the patch is needed to say so.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        files = python_files(b)
        if not files:
            return []
        return [target(f"ruff:{b.instance_id}", None, None, b,
                       f"{len(files)} Python file(s) submitted", source="rerun")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        broken = []
        for path in python_files(bundle):
            text = bundle.files[path].head_text
            if text is None:
                continue
            module = pa.parse_module(text, path)
            if not module.ok and module.error != pa.NO_SOURCE:
                broken.append(f"{path} ({module.error})")
        if broken:
            return Violated(f"cannot pass `ruff check`: {len(broken)} submitted file(s) "
                            f"are not valid Python -- {broken[0]}")
        report = bundle.lint.get("ruff")
        if report is None or not report.usable:
            note = report.note if report is not None else "no lint report for this run"
            return Undetermined("tool_missing", f"`ruff check` was not evaluated: {note}")
        if report.clean:
            return Satisfied(f"`ruff check` reports nothing new "
                             f"({report.n_findings_base} pre-existing finding(s) subtracted)")
        first = report.new_findings[0]
        return Violated(f"`ruff check` reports {report.n_findings_new} new finding(s), "
                        f"e.g. {first.path}: {first.code} {first.message}")


@rule(
    id="ASTROPY-C108",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier; every source file must carry it
    reads=("files",),  # spec §5
)
class SourceFilesCarryTheLicenceLine:
    """Pre-condition: each Python or Cython source file the agent wrote or edited.
    Pass condition: its first line of content is the licence comment, verbatim.

    Not heuristic: codeguide gives the line verbatim, so there is exactly one right string
    and it is compared exactly. A shebang and an encoding declaration are allowed to precede
    it, because Python requires them there.

    A file the harness could not reconstruct is undetermined rather than failed: not
    finding the line in text we do not have would be a verdict about our own gap.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            if not path.endswith((".py", ".pyx")) or not own.owns_file(b, path, "touched"):
                continue
            out.append(target(f"licence:{path}", path, None,
                              (path, b.files[path].head_text), path))
        return out

    def pass_condition(self, t: Target):
        path, text = t.payload
        if text is None:
            return Undetermined("parse_error", f"{path} was not reconstructed, so its "
                                               f"first line cannot be read")
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#!") or _ENCODING_LINE.match(stripped):
                continue
            if stripped == LICENSE_LINE:
                return Satisfied(f"{path} opens with the licence comment")
            return Violated(f"{path} opens with {stripped[:60]!r} rather than the licence "
                            f"comment")
        return Violated(f"{path} is empty and carries no licence comment")


@rule(
    id="ASTROPY-C110",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier; an edited method is in scope
    reads=("files",),  # spec §5
    heuristic=True,
)
class StateIsExposedAsAttributes:
    """Pre-condition: each method the agent wrote or edited on a class.
    Pass condition: it is not a trivial ``get_``/``set_`` accessor.

    Heuristic on the **pass condition** (§6.2): the sentence exempts accessors whose work
    is "computationally expensive", which nothing in a patch measures. *Trivial* stands in
    for it -- a body of a single statement, which is what a plain attribute wrapper looks
    like -- so an expensive accessor written in one line reads as a violation and a cheap
    one written in five does not.

    Selecting every written method, not only the ``get_``-prefixed ones, is what lets an
    ordinary method record a pass (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _library_modules(b):
            for klass in _classes(module):
                for method in _methods(klass):
                    span = pa.span_of(method)
                    if not own.owns_span(b, path, span, "touched"):
                        continue
                    out.append(target(f"accessor:{path}:{method.lineno}", path, span,
                                      (path, method), f"{klass.name}.{method.name}"))
        return out

    def pass_condition(self, t: Target):
        path, method = t.payload
        body = [n for n in method.body if not (isinstance(n, ast.Expr)
                                               and isinstance(n.value, ast.Constant))]
        if _ACCESSOR.match(method.name) and len(body) <= 1:
            return Violated(f"{path}:{method.lineno} exposes state through "
                            f"`{method.name}` rather than an attribute or property")
        return Satisfied(f"{path}:{method.lineno} `{method.name}` is not a trivial "
                         f"get_/set_ accessor")


@rule(
    id="ASTROPY-C111",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class SuperClassCallsUseSuper:
    """Pre-condition: each call the agent wrote that reaches a super-class method, in
    either form -- ``super().method(...)`` or ``BaseClass.method(self, ...)``.
    Pass condition: it goes through ``super()``.

    Heuristic on the **pre-condition** (§6.3): the direct form is recognised by a call
    whose first argument is ``self``, which is what an unbound super-class call looks like
    and is also what a deliberate call to an unrelated class's function looks like.
    Selecting only the direct form would make every target a violation (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _library_modules(b):
            authored = _authored(b, path)
            for node in ast.walk(module.tree):
                if not isinstance(node, ast.Call) or node.lineno not in authored:
                    continue
                func = node.func
                if not isinstance(func, ast.Attribute):
                    continue
                value = func.value
                if isinstance(value, ast.Call) and pa.dotted_name(value.func) == "super":
                    kind, label = "super", f"super().{func.attr}"
                elif (isinstance(value, ast.Name) and value.id[:1].isupper()
                      and node.args and isinstance(node.args[0], ast.Name)
                      and node.args[0].id == "self"):
                    kind, label = "direct", f"{value.id}.{func.attr}(self, ...)"
                else:
                    continue
                out.append(target(f"super:{path}:{node.lineno}", path,
                                  (node.lineno, node.lineno),
                                  (path, node.lineno, kind, label), label))
        return out

    def pass_condition(self, t: Target):
        path, lineno, kind, label = t.payload
        if kind == "super":
            return Satisfied(f"{path}:{lineno} calls the super-class through `{label}`")
        return Violated(f"{path}:{lineno} calls the super-class directly as `{label}` "
                        f"rather than through super()")


def _dunder_targets(bundle: EvidenceBundle, prefix: str, names: tuple[str, ...]
                    ) -> list[Target]:
    out = []
    for path, module in _library_modules(bundle):
        for klass in _classes(module):
            for method in _methods(klass):
                if method.name not in names:
                    continue
                span = pa.span_of(method)
                if own.owns_span(bundle, path, span, "touched"):
                    out.append(target(f"{prefix}:{path}:{method.lineno}", path, span,
                                      (path, method), f"{klass.name}.{method.name}"))
    return out


@rule(
    id="ASTROPY-C116",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ReprIsAlwaysAscii:
    """Pre-condition: each ``__repr__`` the agent wrote or edited.
    Pass condition: it embeds no non-ASCII text and does not branch on
    ``unicode_output``.

    Heuristic on the **pass condition** (§6.2): what a method *returns* is a runtime fact,
    and this reads the literals it is built from. A ``__repr__`` that assembles non-ASCII
    from a variable passes; one that only mentions ``unicode_output`` in a comment fails.
    Both directions are declared rather than argued away.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _dunder_targets(b, "repr", ("__repr__",))

    def pass_condition(self, t: Target):
        path, method = t.payload
        if literal := _has_non_ascii_literal(method):
            return Violated(f"{path}:{method.lineno} __repr__ embeds the non-ASCII text "
                            f"{literal[:30]!r}")
        if _mentions(method, _UNICODE_OUTPUT):
            return Violated(f"{path}:{method.lineno} __repr__ depends on "
                            f"`{_UNICODE_OUTPUT}`, which its output must be independent of")
        return Satisfied(f"{path}:{method.lineno} __repr__ is ASCII and does not consult "
                         f"`{_UNICODE_OUTPUT}`")


@rule(
    id="ASTROPY-C117",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class StrIsAsciiUnlessUnicodeOutput:
    """Pre-condition: each ``__str__`` or ``__format__`` the agent wrote or edited.
    Pass condition: if it embeds non-ASCII text it also consults ``unicode_output``.

    The contrast with C116 is the point of both: ``__repr__`` must never depend on the
    setting, and ``__str__`` must depend on it before it emits anything outside ASCII.

    Heuristic on the **pass condition** (§6.2) for the same reason as C116 -- the literals
    a method contains stand in for what it returns, and consulting the setting stands in
    for branching on it correctly.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _dunder_targets(b, "str", ("__str__", "__format__"))

    def pass_condition(self, t: Target):
        path, method = t.payload
        literal = _has_non_ascii_literal(method)
        if literal and not _mentions(method, _UNICODE_OUTPUT):
            return Violated(f"{path}:{method.lineno} {method.name} embeds the non-ASCII "
                            f"text {literal[:30]!r} without consulting `{_UNICODE_OUTPUT}`")
        if literal:
            return Satisfied(f"{path}:{method.lineno} {method.name} emits non-ASCII only "
                             f"under `{_UNICODE_OUTPUT}`")
        return Satisfied(f"{path}:{method.lineno} {method.name} is ASCII-only")


@rule(
    id="ASTROPY-C118",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- an edited round-trippable class is in scope
    reads=("files", "full_suite_run"),  # spec §5: the answer needs both halves executed
    heuristic=True,
)
class ParserAcceptsItsOwnStrOutput:
    """Pre-condition: each class the agent wrote or edited that both defines ``__str__``
    and offers a string parser, which is what a round-trippable class looks like.
    Pass condition: the parser accepts the output of ``__str__``.

    Graded **one-sidedly, and the side it grades is empty** -- this rule withholds on every
    target it selects, which is why it declares ``full_suite_run``. Whether a parser
    accepts a string is decided by running the parser on that string; a patch shows neither
    the string nor the outcome, and any static stand-in would be inventing the verdict.
    Declaring the missing input keeps the withholding auditable and ends it automatically
    the day the bundle carries a suite run (§5).

    Heuristic on the **pre-condition** (§6.3): *expected to roundtrip through strings* is a
    property of the class's contract, approximated by it having both halves of one.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in _library_modules(b):
            for klass in _classes(module):
                span = pa.span_of(klass)
                if not own.owns_span(b, path, span, "touched"):
                    continue
                methods = {m.name for m in _methods(klass)}
                if "__str__" in methods and methods & set(_PARSER_NAMES):
                    out.append(target(f"roundtrip:{path}:{klass.lineno}", path, span,
                                      (path, klass.name), klass.name))
        return out

    def pass_condition(self, t: Target):
        path, name = t.payload
        return Undetermined(
            "tool_missing",
            f"whether {path}:{name}'s parser accepts its own __str__ output is decided by "
            f"running both; this bundle carries no such run")

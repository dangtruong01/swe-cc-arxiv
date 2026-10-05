"""SymPy: Tests and test style -- 33 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects
on the rule's ANTECEDENT, ``pass_condition`` grades.

Three things shape this category specifically.

**Targets come out of reconstructed files, not the diff.** Three lines of context are
not enough to see which function an assertion sits in, so every rule here reads
``head_text`` through ``extractors/python_ast``. Ownership then narrows the parsed
result back down to what the agent actually wrote (invariant 5) -- a file the agent
touched is full of tests it did not write, and none of them are its to be judged on.

**A file that does not parse is a violation, not missing evidence** (changed 25 Aug 2026
by design decision). The obligation is on the contribution, and a contribution that
is not valid Python satisfies none of the rules that read it. Those files still produce a
target; its judgement is now ``Violated``, scoped to the file, and the parse error is kept
in the reason and in the target key ``unreadable:<path>`` so the `UNREADABLE` alert can
still count it. See ``_unreadable`` below for the full argument.

**Rules whose antecedent or pass condition needs a test *run* return ``tool_missing``.**
Nine rules in this category turn on something no static artefact carries -- how long a
test took, whether an XFAIL now passes, whether expected output matches. Their
pre-conditions still fire on the observable antecedent, so the row records how often the
rule would have applied; only the grading is withheld. They can never fail an agent.

C069 is the deliberate exception. The corpus files it as ``differential``, but
it is the worked case for docs/checker-authoring.md §7.1 -- new
functionality with no test must read ``fail``, not ``not_applicable`` -- so it is graded
statically, with ``heuristic=True`` because "a test covers it" is approximated by name
reference.
"""

from __future__ import annotations

import ast
import builtins
import re
from dataclasses import dataclass
from typing import Iterator, Optional

from compliance.core.models import (
    EvidenceBundle,
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

# --- SymPy vocabulary ---------------------------------------------------------------

# The helper module was renamed in 2021. Base commits in this batch are from 2016-2017,
# so both spellings have to count, or every pre-rename run reads as non-compliant.
PYTEST_HELPER_MODULES = ("sympy.testing.pytest", "sympy.utilities.pytest")

RAISES = "raises"
EXCEPTION_ASSERT_HELPERS = frozenset({
    "raises", "assertRaises", "assertRaisesRegex", "assertRaisesRegexp",
})
DEPRECATION_WARNING = "SymPyDeprecationWarning"
WARNS_DEPRECATED = "warns_deprecated_sympy"
WARNS = "warns"
UNCHANGED = "unchanged"
DUMMY_EQ = "dummy_eq"
IMPORT_MODULE = "import_module"
DOCTEST_DEPENDS_ON = "doctest_depends_on"
SYMPIFY_CALLS = frozenset({"sympify", "S", "parse_expr"})
EXACT_WRAPPERS = frozenset({"S", "Integer", "Rational", "Float", "sympify", "nsimplify"})
WARNING_EMITTERS = frozenset({"warn", "sympy_deprecation_warning"})

BIN_TEST = re.compile(r"\bbin/test\b")
BIN_DOCTEST = re.compile(r"\bbin/doctest\b")
BIN_TEST_SLOW = re.compile(r"\bbin/test\b[^\n]*--slow\b")
# What SymPy's own runner prints when a run is not clean. Positive failure detection
# rather than a search for "pass", which appears in unrelated output constantly.
RUNNER_FAILED = re.compile(r"DO \*NOT\* COMMIT|=+ (FAILURES|ERRORS) =+|^FAILED", re.M)

# Third-party packages SymPy treats as optional: absent in a minimal install, so a test
# that imports one directly breaks collection instead of skipping (C107).
OPTIONAL_DEPENDENCIES = frozenset("""
numpy scipy matplotlib gmpy gmpy2 theano aesara llvmlite cython pyglet antlr4 lfortran
sage symengine IPython tensorflow jax cupy pymc lark z3 cloudpickle wurlitzer numexpr
pandas plotly bokeh autowrap pycosat cvxopt clang wurlitzer
""".split())

# Names `sympy.abc` publishes: bare uses of these in a doctest are symbols, and C114 is
# about symbols specifically, not about every unbound name (that is C113).
_GREEK = """alpha beta gamma delta epsilon zeta eta theta iota kappa lamda mu nu xi
omicron pi rho sigma tau upsilon phi chi psi omega""".split()
SYMBOL_NAMES = frozenset(
    list("abcdefghijklmnopqrstuvwxyz")
    + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    + _GREEK
    + [g.capitalize() for g in _GREEK]
)

BUILTIN_NAMES = frozenset(dir(builtins)) | {"__name__", "__file__", "_"}

_SKIP_DECORATORS = frozenset({"SKIP", "skip", "XFAIL", "slow", "nocache_fail"})
_EXPECTED_FAILURE_REASON = re.compile(
    r"\b(fail|fails|failing|broken|wrong|incorrect|bug|not implemented|nyi)\b", re.I)
_SLOW_REASON = re.compile(r"\b(slow|too long|takes ages|expensive|timeout|hangs?)\b", re.I)
_RANDOMNESS = re.compile(
    r"\brandom_complex_number\b|\brandom_poly\b|\brandtest\b|\bverify_numerically\b"
    r"|\brandom\.\w+|\brandint\b|\brandrange\b|\bchoice\(|\bshuffle\(", re.I)
_DEPRECATION_MENTION = re.compile(r"deprecat", re.I)
# Scope exclusions match whole identifier *words*, never substrings. Bare substring
# matching silently swallowed real targets: "con-str-uctor" read as a printer test,
# "s-pars-e" as a parser test, "sur-round" as a float test. A precondition that
# over-excludes produces no error and no odd verdict -- only a smaller denominator.
PRINTER_WORDS = frozenset("""
print printer printers printing prints str sstr repr srepr latex pretty prettyprint
code ccode fcode jscode rcode mcode octave julia glsl rust maple mathematica mathml
dot preview theanocode cxxcode tree table
""".split())
PARSER_WORDS = frozenset("""
parse parses parsed parser parsers parsing sympify sympified lambdify lexer
token tokens tokenize tokenizer autolev latin mathematica maxima
""".split())
FLOAT_WORDS = frozenset("""
float floats evalf precision prec round rounding nsimplify epsilon tolerance
""".split())

# In free text a word boundary is enough; `\bround\b` does not match "surround".
_FLOAT_IN_BODY = re.compile(
    r"\b(Float|evalf|nsimplify|round|precision)\b|\bN\(", re.I)
_EXPECTED_VALUE_LINE = re.compile(r"^\s*(assert\b.*==|\.\.\.|[A-Za-z0-9_\[\(].*)\s*$")
_BLANKLINE = "<BLANKLINE>"
_PROMPT = re.compile(r"^(\s*)(>>>|\.\.\.)( |$)")
_NUMPYDOC_UNDERLINE = re.compile(r"^\s*[=~^\-*+#]{3,}\s*$")


# --- shared plumbing ----------------------------------------------------------------


@dataclass(frozen=True)
class Unreadable:
    """A Python file in the contribution that could not be parsed.

    Carried as a target payload rather than skipped, so the row says something rather than
    silently reporting that the rule did not apply.

    ``agent_authored`` separates the two reasons a file is unreadable, which must not be
    graded the same way. **True**: the source is in hand and is not valid Python -- the agent
    shipped a module that will not import, and that is a violation. **False**: we never
    reconstructed the source (no repo cache), so nothing is known about the file -- our gap,
    and withheld. Conflating them makes a missing cache read as agent non-compliance across
    every AST rule at once.
    """

    path: str
    reason: str
    agent_authored: bool = True


def _unreadable_target(path: str, module: pa.PyModule) -> Target:
    return Target(
        key=f"unreadable:{path}",
        file=path,
        line_span=None,
        source="patch",
        payload=Unreadable(path, module.error, agent_authored=module.error != pa.NO_SOURCE),
        snippet=module.error,
    )


def _unreadable(target: Target) -> Optional[Judgement]:
    """A file that will not parse leaves the *conditional* rules unanswerable, not violated.

    Briefly graded `fail` on 25 Aug 2026 and reverted the same day, because the blanket was
    wrong in a way the corpus makes obvious. Nearly every rule reading a module is
    conditional -- C076 *"a test function must have a name beginning with `test_`"*, C084
    *"when testing an expected exception, the test must use `raises`"*. Failing those on an
    unparseable file asserts two things at once: that the situation arose, and that the agent
    handled it wrongly. Neither is observable once the parse fails, so the verdict would be
    manufactured rather than measured.

    **Where a parse error IS provable non-compliance, it is failed at the rule that can prove
    it** -- see ``code_quality._syntax_violation``. A module that does not parse cannot pass
    `flake8`, `ruff`, or the test suite, and those rules say so without needing a linter run.
    That keeps the finding ("the agent shipped a file that will not import") in the failure
    count, attributed to obligations it actually defeats, instead of spread across 85 rules
    whose antecedents were never established.
    """
    if isinstance(target.payload, Unreadable):
        return Undetermined("parse_error", f"{target.payload.path}: {target.payload.reason}")
    return None


def _modules(
    bundle: EvidenceBundle, *, tests_only: bool = False, docs: bool = False
) -> Iterator[tuple[str, pa.PyModule]]:
    """Every Python file in the contribution the agent has any authorship of.

    ``tests_only`` keeps test modules, ``docs`` keeps non-test modules; neither keeps
    files the agent did not write a line of. Unparsable files are yielded too, with
    ``ok=False``, and callers turn them into ``Unreadable`` targets.
    """
    for path in sorted(bundle.files):
        if not path.endswith(".py"):
            continue
        change = bundle.files[path]
        # modified_lines, not authored_lines: an agent that fixes a bug purely by
        # deleting code owns that edit, and would otherwise be skipped before parsing.
        if not (change.modified_lines or change.is_new):
            continue
        is_test = pa.is_test_path(path)
        if tests_only and not is_test:
            continue
        if docs and is_test:
            continue
        yield path, pa.parse_module(change.head_text, path)


def _owns(bundle: EvidenceBundle, path: str, span: tuple[int, int], mode: str = "touched") -> bool:
    return owns_span(bundle, path, span, mode)


def _owned_functions(
    bundle: EvidenceBundle, *, tests_only: bool = True, mode: str = "touched"
) -> Iterator[tuple[str, pa.PyModule, pa.FunctionDef]]:
    """Functions the agent owns, plus one ``Unreadable`` sentinel per broken file."""
    for path, module in _modules(bundle, tests_only=tests_only, docs=not tests_only):
        if not module.ok:
            yield path, module, None
            continue
        for function in module.functions:
            if _owns(bundle, path, function.span(), mode):
                yield path, module, function


def _owned_tests(
    bundle: EvidenceBundle, mode: str = "touched"
) -> Iterator[tuple[str, pa.PyModule, pa.FunctionDef]]:
    for path, module, function in _owned_functions(bundle, tests_only=True, mode=mode):
        if function is None or function.is_test:
            yield path, module, function


def _owned_calls(
    bundle: EvidenceBundle, names: frozenset[str], *, tests_only: bool = True
) -> Iterator[tuple[str, pa.PyModule, pa.CallSite]]:
    for path, module in _modules(bundle, tests_only=tests_only, docs=not tests_only):
        if not module.ok:
            yield path, module, None
            continue
        for call in module.calls:
            if call.short in names and _owns(bundle, path, call.span()):
                yield path, module, call


def _owned_docstrings(
    bundle: EvidenceBundle, mode: str = "touched"
) -> Iterator[tuple[str, pa.PyModule, pa.Docstring]]:
    """Docstrings the agent owns.

    ``touched`` -- the agent wrote a line of the docstring itself. That is the right mode
    for rules about how the doctest is written: you do not own the formatting of prose
    you never edited.

    ``enclosing`` -- the agent edited the definition the docstring documents, so its
    examples may no longer hold. Decided on ``def_own_lines``, which excludes nested
    definitions: editing one method of a class does not make the class docstring yours.
    """
    for path, module in _modules(bundle):
        if not module.ok:
            yield path, module, None
            continue
        change = bundle.files[path]
        for docstring in module.docstrings:
            if mode == "enclosing":
                owned = change.is_new or bool(change.modified_lines & docstring.def_own_lines)
            else:
                owned = _owns(bundle, path, docstring.span(), "touched")
            if owned:
                yield path, module, docstring


def _fn_source(module: pa.PyModule, function: pa.FunctionDef) -> str:
    lines = module.source.split("\n")
    return "\n".join(lines[function.lineno - 1: function.end_lineno])


def _target(key, path, span, payload, snippet="") -> Target:
    return Target(key=key, file=path, line_span=span, source="patch",
                  payload=payload, snippet=snippet[:200])


def _fn_target(path: str, function: pa.FunctionDef, payload, prefix: str) -> Target:
    return _target(f"{prefix}:{path}:{function.lineno}", path, function.span(),
                   payload, f"def {function.name}")


def _ran(bundle: EvidenceBundle, pattern: re.Pattern):
    return [c for c in bundle.commands if pattern.search(c.command)]


def _runner_verdict(commands, label: str):
    """Grade a project test-runner invocation from what it printed."""
    if not commands:
        return Violated(f"never ran `{label}`")
    failed = [c for c in commands if RUNNER_FAILED.search(c.output or "")]
    if failed:
        return Violated(f"`{label}` reported failures")
    return Satisfied(f"ran `{label}` {len(commands)} time(s), no reported failure")


def _is_str_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _is_int_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, int) \
        and not isinstance(node.value, bool)


def _is_float_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, float)


def _wrapped_exact(node: ast.AST) -> bool:
    """`S(1)`, `Integer(1)`, `Rational(1, 2)` -- an exact SymPy number, not a Python int."""
    return isinstance(node, ast.Call) and pa.dotted_name(node.func).split(".")[-1] in EXACT_WRAPPERS


def _numeric_operand(node: ast.AST) -> bool:
    return _is_int_literal(node) or _is_float_literal(node) or _wrapped_exact(node)


def _int_division_sites(node: ast.AST) -> list[ast.BinOp]:
    """Divisions whose operands are numeric constants -- the sites C137/C142 grade."""
    return [
        n for n in ast.walk(node)
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div)
        and _numeric_operand(n.left) and _numeric_operand(n.right)
    ]


def _resolves_to_helper(module: pa.PyModule, name: str) -> Optional[bool]:
    """Whether ``name`` came from SymPy's own pytest wrapper. None if never imported."""
    origin = module.origin(name)
    if origin == name:
        return None
    return any(origin.startswith(m + ".") or origin == m for m in PYTEST_HELPER_MODULES)


# --- doctest binding analysis --------------------------------------------------------


@dataclass(frozen=True)
class BlockNames:
    bound: frozenset[str]
    called: frozenset[str]
    loaded: frozenset[str]
    star_import: bool
    unparsed: int


def _block_names(examples: tuple[pa.DoctestExample, ...]) -> BlockNames:
    """What a doctest block binds and what it uses.

    A doctest is a session: names bound by an earlier example are available to a later
    one, so the whole block is analysed together rather than example by example.
    """
    bound: set[str] = set()
    called: set[str] = set()
    loaded: set[str] = set()
    star = False
    unparsed = 0
    for example in examples:
        try:
            tree = ast.parse(example.source)
        except SyntaxError:
            unparsed += 1
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    bound.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        star = True
                    else:
                        bound.add(alias.asname or alias.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                bound.add(node.name)
                bound.update(a.arg for a in _all_args(node))
            elif isinstance(node, ast.Lambda):
                bound.update(a.arg for a in _all_args(node))
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, (ast.Store, ast.Del)):
                    bound.add(node.id)
                else:
                    loaded.add(node.id)
            elif isinstance(node, ast.alias):
                continue
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if isinstance(item.optional_vars, ast.Name):
                        bound.add(item.optional_vars.id)
            elif isinstance(node, ast.ExceptHandler) and node.name:
                bound.add(node.name)
            if isinstance(node, ast.Call):
                if name := pa.dotted_name(node.func):
                    called.add(name.split(".")[0])
    return BlockNames(frozenset(bound), frozenset(called), frozenset(loaded), star, unparsed)


def _all_args(node) -> list[ast.arg]:
    args = getattr(node, "args", None)
    if not isinstance(args, ast.arguments):
        return []
    out = list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs)
    for extra in (args.vararg, args.kwarg):
        if extra is not None:
            out.append(extra)
    return out


def _doctest_target(path: str, docstring: pa.Docstring, payload=None) -> Target:
    return _target(
        f"doctest:{path}:{docstring.lineno}", path, docstring.span(),
        payload if payload is not None else docstring,
        f"{docstring.owner} docstring",
    )


# --- new functionality ---------------------------------------------------------------


@rule(id="SYMPY-C069", category=CATEGORY, ownership="created", heuristic=True,
      reads=("files",))
class NewFunctionalityHasTests:
    """Pre-condition: each public function or class the agent added to non-test code.
    Pass condition: the contribution also adds a test that exercises it by name.

    This is the worked case for docs/checker-authoring.md §7.1: the trigger
    is the new functionality, so an agent that writes none of the tests fails rather
    than escaping as ``not_applicable``.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module in _modules(b, docs=True):
            if not module.ok:
                targets.append(_unreadable_target(path, module))
                continue
            for definition in _definitions(module):
                name, span = definition
                if name.startswith("_"):
                    continue
                if _owns(b, path, span, "created"):
                    targets.append(_target(f"new:{path}:{span[0]}", path, span, (name, b), name))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        name, bundle = t.payload
        word = re.compile(rf"\b{re.escape(name)}\b")
        for path in sorted(bundle.files):
            if not pa.is_test_path(path):
                continue
            for _, text in bundle.files[path].added_lines:
                if word.search(text):
                    return Satisfied(f"{name} is exercised by a test added in {path}")
        return Violated(f"added {name} but no added test references it")


def _definitions(module: pa.PyModule) -> list[tuple[str, tuple[int, int]]]:
    out = [(f.name, f.span()) for f in module.functions]
    for node in ast.walk(module.tree):
        if isinstance(node, ast.ClassDef):
            out.append((node.name, pa.span_of(node)))
    return sorted(out, key=lambda item: item[1])


@rule(id="SYMPY-C071", category=CATEGORY, ownership="touched",
      reads=("files", "evaluation", "full_suite_run"))
class FullSuitePasses:
    """Pre-condition: the agent produced a contribution, which is what gets merged.
    Pass condition: no test that passed before the change fails after it.

    Graded from the harness's own before-and-after run, and graded **one-sidedly**. A test
    that passed before and fails now is conclusive: the suite does not pass. The converse
    is not, because the harness runs a subset -- a clean subset does not establish that the
    *complete* suite passes, which is what the rule demands. So this can fail on evidence
    and is withheld otherwise; it never passes vacuously.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not b.files:
            return []
        return [_target(f"contribution:{b.instance_id}", None, None, b,
                        f"{len(b.files)} file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        report = bundle.evaluation
        if report is None:
            return Undetermined("tool_missing", "this run carries no functional result")
        if regressions := report.regressions():
            return Violated(
                f"{len(regressions)} test(s) that passed before the change now fail: "
                f"{sorted(regressions)[:5]}")
        return Undetermined(
            "tool_missing",
            f"no regression in the {report.n_outcomes} test(s) the harness ran, but that "
            f"is a subset -- the complete suite needs the Phase 5 runner",
        )


# --- test shape -----------------------------------------------------------------------


@rule(id="SYMPY-C076", category=CATEGORY, ownership="created", reads=("files",))
class TestFunctionNaming:
    """Pre-condition: each public module-level function the agent added to a test module.
    Pass condition: its name begins with `test_`."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module in _modules(b, tests_only=True):
            if not module.ok:
                targets.append(_unreadable_target(path, module))
                continue
            top_level = {f.name for f in module.functions if f.qualname == f.name}
            for function in module.functions:
                if function.name not in top_level or function.name.startswith("_"):
                    continue
                if _owns(b, path, function.span(), "created"):
                    targets.append(_fn_target(path, function, function, "testname"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        function: pa.FunctionDef = t.payload
        if function.is_test:
            return Satisfied()
        return Violated(f"`{function.name}` is a public test-module function not named test_*")


@rule(id="SYMPY-C078", category=CATEGORY, ownership="touched", reads=("files", "commands"))
class RunsLocalTestAndDoctestSuites:
    """Pre-condition: the agent changed code, so the local suites are what validate it.
    Pass condition: it ran both `python bin/test` and `python bin/doctest`, neither
    reporting a failure."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not b.files:
            return []
        return [_target(f"validate:{b.instance_id}", None, None, b,
                        f"{len(b.files)} file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        problems = []
        for pattern, label in ((BIN_TEST, "bin/test"), (BIN_DOCTEST, "bin/doctest")):
            judgement = _runner_verdict(_ran(bundle, pattern), label)
            if isinstance(judgement, Violated):
                problems.append(judgement.reason)
        if problems:
            return Violated("; ".join(problems))
        return Satisfied("ran both bin/test and bin/doctest with no reported failure")


# --- exceptions and warnings ----------------------------------------------------------


@rule(id="SYMPY-C084", category=CATEGORY, ownership="touched", reads=("files",))
class ExpectedExceptionsUseRaises:
    """Pre-condition: each site in the agent's test code that tests for an expected
    exception, however it is written.
    Pass condition: the site uses SymPy's own `raises` helper."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module in _modules(b, tests_only=True):
            if not module.ok:
                targets.append(_unreadable_target(path, module))
                continue
            for call in module.calls:
                if call.short in EXCEPTION_ASSERT_HELPERS and _owns(b, path, call.span()):
                    targets.append(_target(f"exc:{path}:{call.lineno}", path, call.span(),
                                           (call, module), call.func))
            for node in module.tries:
                if not node.handlers or not _owns(b, path, pa.span_of(node)):
                    continue
                function = module.enclosing_function(node.lineno)
                if function is None or not function.is_test:
                    continue
                targets.append(_target(f"exc-try:{path}:{node.lineno}", path,
                                       pa.span_of(node), (node, module), "try/except"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        node, module = t.payload
        if isinstance(node, ast.Try):
            return Violated("expected exception tested with try/except, not `raises`")
        if node.short != RAISES:
            return Violated(f"expected exception tested with `{node.func}`, not `raises`")
        resolved = _resolves_to_helper(module, node.func.split(".")[0])
        if resolved is False:
            return Violated(f"`raises` here is {module.origin(node.func)}, "
                            f"not SymPy's testing.pytest helper")
        return Satisfied()


@rule(id="SYMPY-C085", category=CATEGORY, ownership="touched", reads=("files",))
class RaisesWrapsCodeInLambda:
    """Pre-condition: each `raises(ExceptionType, <code>)` call the agent wrote -- the
    two-argument form, not the context-manager form.
    Pass condition: the code argument is a `lambda`."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, call in _owned_calls(b, frozenset({RAISES})):
            if call is None:
                targets.append(_unreadable_target(path, module))
                continue
            if len(call.args) >= 2:
                targets.append(_target(f"raises:{path}:{call.lineno}", path, call.span(),
                                       call, f"raises(...) at line {call.lineno}"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        call: pa.CallSite = t.payload
        code = call.args[1]
        if isinstance(code, ast.Lambda):
            return Satisfied()
        if _is_str_literal(code):
            return Satisfied("string form of raises(), evaluated by the helper")
        return Violated(f"raises() code argument is {type(code).__name__}, not a lambda")


@rule(id="SYMPY-C086", category=CATEGORY, ownership="touched", reads=("files",))
class DeprecationTestsUseWarnsHelper:
    """Pre-condition: each test the agent wrote that names `SymPyDeprecationWarning`.
    Pass condition: it goes through `warns_deprecated_sympy()`, or through
    `warns(SymPyDeprecationWarning, test_stacklevel=False)` when stacklevel checking is
    explicitly disabled."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, function in _owned_tests(b):
            if function is None:
                targets.append(_unreadable_target(path, module))
                continue
            source = _fn_source(module, function)
            if DEPRECATION_WARNING in source:
                targets.append(_fn_target(path, function, (function, module), "deprwarn"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        function, module = t.payload
        calls = module.calls_within(function.span())
        if any(c.short == WARNS_DEPRECATED for c in calls):
            return Satisfied()
        for call in calls:
            if call.short == WARNS and _stacklevel_disabled(call):
                return Satisfied("warns(..., test_stacklevel=False)")
        return Violated(
            f"`{function.name}` tests {DEPRECATION_WARNING} without {WARNS_DEPRECATED}()")


def _stacklevel_disabled(call: pa.CallSite) -> bool:
    node = call.keywords.get("test_stacklevel")
    return isinstance(node, ast.Constant) and node.value is False


@rule(id="SYMPY-C089", category=CATEGORY, ownership="touched", reads=("files",))
class WarningsSetStacklevel:
    """Pre-condition: each warning the agent's non-test code emits.
    Pass condition: the call passes `stacklevel`, so the warning points at the caller."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, call in _owned_calls(b, WARNING_EMITTERS, tests_only=False):
            if call is None:
                targets.append(_unreadable_target(path, module))
                continue
            targets.append(_target(f"warn:{path}:{call.lineno}", path, call.span(),
                                   call, f"{call.func}(...)"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        call: pa.CallSite = t.payload
        if "stacklevel" in call.keywords:
            return Satisfied()
        return Violated(f"`{call.func}(...)` at line {call.lineno} sets no stacklevel")


@rule(id="SYMPY-C090", category=CATEGORY, ownership="touched", reads=("files",))
class WarnsDeprecationEscapeHatch:
    """Pre-condition: each `warns(SymPyDeprecationWarning, ...)` the agent wrote -- the
    form reached for only when the warning cannot set `stacklevel` correctly.
    Pass condition: it passes `test_stacklevel=False`, which is what that form is for."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, call in _owned_calls(b, frozenset({WARNS})):
            if call is None:
                targets.append(_unreadable_target(path, module))
                continue
            first = call.args[0] if call.args else None
            if first is not None and pa.dotted_name(first).split(".")[-1] == DEPRECATION_WARNING:
                targets.append(_target(f"warns:{path}:{call.lineno}", path, call.span(),
                                       call, f"warns({DEPRECATION_WARNING}, ...)"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        call: pa.CallSite = t.payload
        if _stacklevel_disabled(call):
            return Satisfied()
        return Violated(
            f"warns({DEPRECATION_WARNING}, ...) without test_stacklevel=False; "
            f"use {WARNS_DEPRECATED}() instead")


@rule(id="SYMPY-C091", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class DeprecatedBehaviourOnlyInItsOwnTest:
    """Pre-condition: each test the agent wrote that mentions deprecation at all.
    Pass condition: every such mention sits inside a `warns_deprecated_sympy()` block.

    Which APIs are deprecated is not derivable from the patch, so "mentions deprecation"
    is a lexical stand-in and the rule is flagged as a heuristic.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, function in _owned_tests(b):
            if function is None:
                targets.append(_unreadable_target(path, module))
                continue
            source = _fn_source(module, function)
            if _DEPRECATION_MENTION.search(source):
                targets.append(_fn_target(path, function, (function, module), "depruse"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        function, module = t.payload
        guarded = [
            pa.span_of(node)
            for node in ast.walk(function.node)
            if isinstance(node, ast.With)
            and any(pa.dotted_name(_ctx(item)).split(".")[-1] == WARNS_DEPRECATED
                    for item in node.items)
        ]
        outside = []
        for lineno, text in _numbered(module, function):
            if not _DEPRECATION_MENTION.search(text):
                continue
            if any(lo <= lineno <= hi for lo, hi in guarded):
                continue
            if WARNS_DEPRECATED in text or DEPRECATION_WARNING in text:
                continue
            outside.append(lineno)
        if outside:
            return Violated(
                f"`{function.name}` uses deprecated behaviour outside a "
                f"{WARNS_DEPRECATED}() block at line(s) {outside[:5]}")
        return Satisfied()


def _ctx(item: ast.withitem) -> ast.AST:
    node = item.context_expr
    return node.func if isinstance(node, ast.Call) else node


def _numbered(module: pa.PyModule, function: pa.FunctionDef):
    lines = module.source.split("\n")
    for offset in range(function.lineno, function.end_lineno + 1):
        if offset - 1 < len(lines):
            yield offset, lines[offset - 1]


# --- assertion style -------------------------------------------------------------------


@rule(id="SYMPY-C094", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class UnevaluatedAssertionsUseUnchanged:
    """Pre-condition: each assertion the agent wrote that an expression stays unevaluated
    -- written either with `unchanged(...)` or by comparing two identical evaluations.
    Pass condition: it is the `unchanged(...)` form."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module in _modules(b, tests_only=True):
            if not module.ok:
                targets.append(_unreadable_target(path, module))
                continue
            for node in module.asserts:
                span = pa.span_of(node)
                if not _owns(b, path, span):
                    continue
                if _is_unchanged_call(node.test) or _repeats_an_evaluation(node.test):
                    targets.append(_target(f"unchanged:{path}:{node.lineno}", path, span,
                                           node, ast.dump(node.test)[:120]))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        node: ast.Assert = t.payload
        if _is_unchanged_call(node.test):
            return Satisfied()
        return Violated(
            f"asserts unevaluatedness by comparing repeated evaluations at line "
            f"{node.lineno}; use {UNCHANGED}(function, *args)")


def _is_unchanged_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and pa.dotted_name(node.func).split(".")[-1] == UNCHANGED


def _repeats_an_evaluation(node: ast.AST) -> bool:
    """`f(x, evaluate=False) == f(x, evaluate=False)` -- the pattern the rule replaces."""
    if not (isinstance(node, ast.Compare) and len(node.ops) == 1
            and isinstance(node.ops[0], ast.Eq)):
        return False
    left, right = node.left, node.comparators[0]
    if not (isinstance(left, ast.Call) and isinstance(right, ast.Call)):
        return False
    if ast.dump(left) != ast.dump(right):
        return False
    return True


@rule(id="SYMPY-C095", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class DummyResultsUseDummyEq:
    """Pre-condition: each assertion the agent wrote whose expression involves a `Dummy`.
    Pass condition: it compares with `.dummy_eq(...)` rather than `==`.

    Whether a result *contains* a Dummy is a runtime property; the mention of `Dummy` in
    the assertion is a stand-in for it, hence the heuristic flag.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module in _modules(b, tests_only=True):
            if not module.ok:
                targets.append(_unreadable_target(path, module))
                continue
            lines = module.source.split("\n")
            for node in module.asserts:
                span = pa.span_of(node)
                if not _owns(b, path, span):
                    continue
                text = "\n".join(lines[span[0] - 1: span[1]])
                if re.search(r"\bDummy\b", text):
                    targets.append(_target(f"dummy:{path}:{node.lineno}", path, span,
                                           node, text[:200]))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        node: ast.Assert = t.payload
        for inner in ast.walk(node):
            if isinstance(inner, ast.Call) and \
                    pa.dotted_name(inner.func).split(".")[-1] == DUMMY_EQ:
                return Satisfied()
            if isinstance(inner, ast.Attribute) and inner.attr == DUMMY_EQ:
                return Satisfied()
        if not any(isinstance(n, ast.Compare) and any(isinstance(o, ast.Eq) for o in n.ops)
                   for n in ast.walk(node)):
            return Satisfied("no `==` comparison to replace")
        return Violated(f"compares a Dummy-bearing result with `==` at line {node.lineno}; "
                        f"use .{DUMMY_EQ}(expected)")


@rule(id="SYMPY-C097", category=CATEGORY, ownership="touched",
      reads=("files", "repeated_runs"))
class RandomTestsRunRepeatedly:
    """Pre-condition: each test the agent wrote that draws on randomness.
    Pass condition: it was run repeatedly and passed every time -- withheld, because the
    bundle records no repeated-run outcome."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, function in _owned_tests(b):
            if function is None:
                targets.append(_unreadable_target(path, module))
                continue
            if _RANDOMNESS.search(_fn_source(module, function)):
                targets.append(_fn_target(path, function, function, "random"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        return Undetermined(
            "tool_missing", "repeated-run stability needs the test executed; Phase 5")


# --- skipping and marking ---------------------------------------------------------------


@rule(id="SYMPY-C098", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class ExpectedFailuresUseXfail:
    """Pre-condition: each test the agent wrote that is skipped because it is expected to
    fail -- however that is spelled.
    Pass condition: it is marked `@XFAIL`, not `@SKIP` or `skip()`."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _skip_targets(b, _EXPECTED_FAILURE_REASON, "xfail")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        function, how = t.payload
        if function.has_decorator("XFAIL"):
            return Satisfied()
        return Violated(f"`{function.name}` is expected to fail but is skipped with {how}")


@rule(id="SYMPY-C099", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class SlowTestsUseSlowMarker:
    """Pre-condition: each test the agent wrote that is skipped only because it is slow.
    Pass condition: it is marked `@slow`, not `@SKIP` or `skip()`."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _skip_targets(b, _SLOW_REASON, "slow")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        function, how = t.payload
        if function.has_decorator("slow"):
            return Satisfied()
        return Violated(f"`{function.name}` is skipped for slowness with {how}, not @slow")


def _skip_targets(b: EvidenceBundle, reason_pattern: re.Pattern, prefix: str) -> list[Target]:
    """Tests skipped for the reason ``reason_pattern`` describes, whichever mechanism
    was used. Selecting only the wrong mechanism would make the rule unpassable."""
    marker = {"xfail": "XFAIL", "slow": "slow"}[prefix]
    targets = []
    for path, module, function in _owned_tests(b):
        if function is None:
            targets.append(_unreadable_target(path, module))
            continue
        if function.has_decorator(marker):
            targets.append(_fn_target(path, function, (function, f"@{marker}"), prefix))
            continue
        how = _skip_mechanism(module, function, reason_pattern)
        if how:
            targets.append(_fn_target(path, function, (function, how), prefix))
    return targets


def _skip_mechanism(module, function, reason_pattern) -> str:
    """How a test is skipped, if the stated reason matches ``reason_pattern``."""
    for decorator in function.decorators:
        short = decorator.name.split(".")[-1]
        if short in {"SKIP", "skip"}:
            reason = " ".join(str(v) for v in decorator.keywords.values())
            text = reason or _decorator_text(module, decorator)
            if reason_pattern.search(text):
                return f"@{short}"
    for call in module.calls_within(function.span()):
        if call.short == "skip" and call.args and _is_str_literal(call.args[0]):
            if reason_pattern.search(call.args[0].value):
                return "skip()"
    return ""


def _decorator_text(module: pa.PyModule, decorator: pa.Decorator) -> str:
    lines = module.source.split("\n")
    return lines[decorator.lineno - 1] if decorator.lineno - 1 < len(lines) else ""


@rule(id="SYMPY-C102", category=CATEGORY, ownership="touched",
      reads=("files", "evaluation"))
class XfailRemovedOncePassing:
    """Pre-condition: each `@XFAIL` test in the code the agent touched.
    Pass condition: the test still fails, so the marker is still warranted.

    Answered per test from the harness's before-and-after run: a test named in
    `FAIL_TO_PASS` has started to pass, and keeping `@XFAIL` on it is the violation. A test
    the harness did not run is withheld individually rather than assumed still failing.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, function in _owned_tests(b, mode="enclosing"):
            if function is None:
                targets.append(_unreadable_target(path, module))
                continue
            if function.has_decorator("XFAIL"):
                targets.append(_fn_target(path, function, (function, b), "xfail-still"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        function, bundle = t.payload
        report = bundle.evaluation
        if report is None:
            return Undetermined("tool_missing", "this run carries no functional result")
        if function.name in report.newly_passing():
            return Violated(
                f"`{function.name}` has started to pass but still carries @XFAIL; "
                f"remove the marker so it becomes a normal test")
        if function.name in report.tests_reported():
            return Satisfied(f"`{function.name}` still fails, so @XFAIL stands")
        return Undetermined(
            "tool_missing",
            f"the harness did not run `{function.name}`, so whether it now passes is "
            f"unknown -- not evidence that it still fails",
        )



@rule(id="SYMPY-C104", category=CATEGORY, ownership="touched",
      reads=("files", "test_timings"))
class SlowTestsAreMarkedSlow:
    """Pre-condition: each test the agent wrote, any of which could exceed a minute.
    Pass condition: it is marked `@slow` if it takes more than a minute -- withheld,
    because the bundle records no test durations."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _plain_test_targets(b, "duration")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        return Undetermined("tool_missing", "test durations are not recorded; Phase 5")


@rule(id="SYMPY-C105", category=CATEGORY, ownership="touched",
      reads=("files", "test_timings"))
class HangingTestsUseSkip:
    """Pre-condition: each test the agent wrote, any of which could hang.
    Pass condition: it is marked `@SKIP` rather than `@slow` if it hangs -- withheld,
    because a hanging test is only distinguishable from a slow one by running it."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _plain_test_targets(b, "hang")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        return Undetermined("tool_missing", "hanging is only observable by running; Phase 5")


def _plain_test_targets(b: EvidenceBundle, prefix: str) -> list[Target]:
    targets = []
    for path, module, function in _owned_tests(b):
        if function is None:
            targets.append(_unreadable_target(path, module))
        else:
            targets.append(_fn_target(path, function, function, prefix))
    return targets


@rule(id="SYMPY-C106", category=CATEGORY, ownership="touched", reads=("files", "commands"))
class ValidatesSlowTests:
    """Pre-condition: the contribution carries a test marked `@slow`.
    Pass condition: `python bin/test --slow` was run and reported no failure."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, function in _owned_tests(b, mode="enclosing"):
            if function is None:
                targets.append(_unreadable_target(path, module))
                continue
            if function.has_decorator("slow"):
                targets.append(_fn_target(path, function, (function, b), "slow-validate"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        _, bundle = t.payload
        return _runner_verdict(_ran(bundle, BIN_TEST_SLOW), "bin/test --slow")


@rule(id="SYMPY-C107", category=CATEGORY, ownership="touched", reads=("files",))
class OptionalDependenciesViaImportModule:
    """Pre-condition: each reference the agent's test code makes to an optional
    dependency, whether by a plain import or by `import_module()`.
    Pass condition: it goes through `sympy.external.import_module()`, which returns
    `None` when the dependency is absent instead of breaking collection."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module in _modules(b, tests_only=True):
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
                if not _is_str_literal(call.args[0]) or not _owns(b, path, call.span()):
                    continue
                name = call.args[0].value.split(".")[0]
                if name in OPTIONAL_DEPENDENCIES:
                    targets.append(_target(f"optdep:{path}:{call.lineno}", path, call.span(),
                                           ("import_module", name),
                                           f"import_module({name!r})"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        how, name = t.payload
        if how == "import_module":
            return Satisfied()
        return Violated(f"imports optional dependency `{name}` directly; "
                        f"use {IMPORT_MODULE}({name!r})")


# --- doctests ---------------------------------------------------------------------------


@rule(id="SYMPY-C112", category=CATEGORY, ownership="enclosing",
      reads=("files", "commands"))
class DoctestsRunAndPass:
    """Pre-condition: the agent contributed or edited a docstring carrying doctests.
    Pass condition: `python bin/doctest` was run and reported no failure."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, docstring in _owned_docstrings(b, "enclosing"):
            if docstring is None:
                targets.append(_unreadable_target(path, module))
                continue
            if docstring.examples:
                targets.append(_doctest_target(path, docstring, (docstring, b)))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        _, bundle = t.payload
        return _runner_verdict(_ran(bundle, BIN_DOCTEST), "bin/doctest")


@rule(id="SYMPY-C113", category=CATEGORY, ownership="enclosing", reads=("files",))
class DoctestsImportWhatTheyCall:
    """Pre-condition: each doctest the agent owns that calls a function by a bare name.
    Pass condition: every such name is explicitly imported or defined inside the doctest
    itself, so the example is self-contained."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, docstring in _owned_docstrings(b):
            if docstring is None:
                targets.append(_unreadable_target(path, module))
                continue
            if not docstring.examples:
                continue
            names = _block_names(docstring.examples)
            if names.called:
                targets.append(_doctest_target(path, docstring, (docstring, names)))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        docstring, names = t.payload
        missing = sorted(n for n in names.called
                         if n not in names.bound and n not in BUILTIN_NAMES)
        if names.star_import and missing:
            return Violated(f"{docstring.owner}: uses a star import, so `{missing[0]}` "
                            f"is not explicitly imported")
        if missing:
            return Violated(f"{docstring.owner}: calls {missing[:5]} without importing them")
        return Satisfied()


@rule(id="SYMPY-C114", category=CATEGORY, ownership="enclosing", heuristic=True,
      reads=("files",))
class DoctestsDefineTheirSymbols:
    """Pre-condition: each doctest the agent owns that uses a bare symbol name.
    Pass condition: every such name is bound in the doctest, by importing it from
    `sympy.abc` or by creating it with `symbols()`.

    "A symbol name" is taken to be the set `sympy.abc` publishes -- single letters and
    Greek names -- which is a stand-in for knowing what is a symbol, hence heuristic.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, docstring in _owned_docstrings(b):
            if docstring is None:
                targets.append(_unreadable_target(path, module))
                continue
            if not docstring.examples:
                continue
            names = _block_names(docstring.examples)
            # A name that is called is a function, not a symbol -- `f(1)` is C113's
            # business. Single-letter function names would otherwise read as symbols.
            used = {n for n in names.loaded - names.called if n in SYMBOL_NAMES}
            if used:
                targets.append(_doctest_target(path, docstring, (docstring, names, used)))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        docstring, names, used = t.payload
        missing = sorted(n for n in used if n not in names.bound)
        if names.star_import and missing:
            return Violated(f"{docstring.owner}: symbols {missing[:5]} come from a star "
                            f"import, not an explicit definition")
        if missing:
            return Violated(f"{docstring.owner}: uses symbols {missing[:5]} without "
                            f"importing them from sympy.abc or creating them")
        return Satisfied()


@rule(id="SYMPY-C115", category=CATEGORY, ownership="enclosing",
      reads=("files", "doctest_run"))
class DoctestOutputIsExact:
    """Pre-condition: each doctest example the agent owns.
    Pass condition: its expected output matches a real session exactly -- withheld,
    because exactness can only be established by running the example."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, docstring in _owned_docstrings(b, "enclosing"):
            if docstring is None:
                targets.append(_unreadable_target(path, module))
                continue
            for example in docstring.examples:
                targets.append(_target(f"ex:{path}:{example.lineno}", path, example.span(),
                                       example, example.source.strip()[:120]))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        return Undetermined(
            "tool_missing", "expected-output exactness needs the doctest run; Phase 5")


@rule(id="SYMPY-C118", category=CATEGORY, ownership="enclosing", heuristic=True,
      reads=("files",))
class DependencyDoctestsDeclareTheirLibraries:
    """Pre-condition: each doctest the agent owns that needs an optional library --
    whether it imports one or skips itself to avoid one.
    Pass condition: the library is declared with `@doctest_depends_on(...)` and the
    example is not silenced with `# doctest: +SKIP`."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, docstring in _owned_docstrings(b):
            if docstring is None:
                targets.append(_unreadable_target(path, module))
                continue
            if not docstring.examples:
                continue
            block = "\n".join(e.source for e in docstring.examples)
            skipped = "+SKIP" in docstring.text
            deps = sorted({d for d in OPTIONAL_DEPENDENCIES
                           if re.search(rf"\b{re.escape(d)}\b", block)})
            if deps or skipped:
                function = module.enclosing_function(docstring.def_span[0])
                targets.append(_doctest_target(path, docstring,
                                               (docstring, deps, skipped, function)))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        docstring, deps, skipped, function = t.payload
        declared = function is not None and function.has_decorator(DOCTEST_DEPENDS_ON)
        if skipped and not declared:
            return Violated(f"{docstring.owner}: silenced with `# doctest: +SKIP` instead "
                            f"of @{DOCTEST_DEPENDS_ON}(...)")
        if deps and not declared:
            return Violated(f"{docstring.owner}: uses {deps[:3]} without "
                            f"@{DOCTEST_DEPENDS_ON}(...)")
        return Satisfied()


@rule(id="SYMPY-C119", category=CATEGORY, ownership="enclosing", heuristic=True,
      reads=("files",))
class BlankLinesInOutputUseMarker:
    """Pre-condition: each doctest the agent owns whose expected output runs across a
    blank line -- written either with the marker or with a raw blank line.
    Pass condition: the blank line is written as the literal `<BLANKLINE>`.

    A raw blank line terminates expected output, so it is invisible to the doctest
    parser and has to be found by scanning the docstring text; the scan is a heuristic.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, docstring in _owned_docstrings(b):
            if docstring is None:
                targets.append(_unreadable_target(path, module))
                continue
            if not docstring.examples:
                continue
            interrupted = _interrupted_output_lines(docstring)
            if interrupted or _BLANKLINE in docstring.text:
                targets.append(_doctest_target(path, docstring, (docstring, interrupted)))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        docstring, interrupted = t.payload
        if interrupted:
            return Violated(f"{docstring.owner}: expected output resumes after a blank "
                            f"line at line(s) {interrupted[:5]}; use {_BLANKLINE}")
        return Satisfied()


def _interrupted_output_lines(docstring: pa.Docstring) -> list[int]:
    """File lines where expected output appears to continue past a blank line.

    Deliberately conservative: the resumed line must sit at the prompt's own indent and
    must not read as prose or as a numpydoc heading, since a doctest is very often
    followed by an ordinary paragraph.
    """
    lines = list(docstring.lines())
    found: list[int] = []
    indent: Optional[int] = None
    state = "prose"
    for position, (lineno, text) in enumerate(lines):
        if match := _PROMPT.match(text):
            indent = len(match.group(1))
            state = "want" if match.group(2) == ">>>" else state
            continue
        if state == "want" and not text.strip():
            follower = _next_nonblank(lines, position + 1)
            if follower is None:
                state = "prose"
                continue
            next_lineno, next_index = follower
            if _looks_like_output(lines, next_index, indent):
                found.append(next_lineno)
            state = "prose"
            continue
        if state == "want" and text.strip() and indent is not None \
                and len(text) - len(text.lstrip()) < indent:
            state = "prose"
    return found


def _next_nonblank(lines, start):
    for index in range(start, len(lines)):
        if lines[index][1].strip():
            return lines[index][0], index
    return None


def _looks_like_output(lines, start: int, indent: Optional[int]) -> bool:
    """Whether the paragraph beginning at ``start`` reads as resumed doctest output.

    The paragraph, not the line: docstring prose wraps, so "Floats are automatically
    converted to Rational unless the" only reveals itself as a sentence once joined
    with the line that finishes it.
    """
    text = lines[start][1]
    if indent is None or _PROMPT.match(text):
        return False
    if len(text) - len(text.lstrip()) != indent:
        return False
    paragraph = []
    for index in range(start, len(lines)):
        line = lines[index][1]
        if not line.strip():
            break
        if _NUMPYDOC_UNDERLINE.match(line.strip()) or _PROMPT.match(line):
            return False
        paragraph.append(line.strip())
    joined = " ".join(paragraph)
    if joined[:1].isupper() and joined.endswith((".", ":", "!", "?")):
        return False
    return True


@rule(id="SYMPY-C126", category=CATEGORY, ownership="enclosing", reads=("files",))
class NoneResultsArePrinted:
    """Pre-condition: each doctest example the agent owns whose expected output is `None`.
    Pass condition: the example calls `print(...)`, which is what makes `None` show."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, docstring in _owned_docstrings(b):
            if docstring is None:
                targets.append(_unreadable_target(path, module))
                continue
            for example in docstring.examples:
                if example.want.strip() == "None":
                    targets.append(_target(f"none:{path}:{example.lineno}", path,
                                           example.span(), example,
                                           example.source.strip()[:120]))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        example: pa.DoctestExample = t.payload
        if re.match(r"\s*print\s*\(", example.source):
            return Satisfied()
        return Violated(f"expects `None` from `{example.source.strip()[:60]}` without "
                        f"print(); a bare expression printing None shows nothing")


@rule(id="SYMPY-C130", category=CATEGORY, ownership="touched",
      reads=("files", "expression_eval"))
class ChangedExpectationsAreVerified:
    """Pre-condition: each expected value the agent replaced in an existing test or
    doctest.
    Pass condition: the new value was verified equivalent across the relevant domains --
    withheld, since nothing in the bundle records that verification."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path in sorted(b.files):
            change = b.files[path]
            if change.is_new or not path.endswith(".py"):
                continue
            for index, text in enumerate(change.removed_lines):
                if _is_expectation(text):
                    targets.append(_target(f"expect:{path}:{index}", path, None,
                                           text, text.strip()[:120]))
        return targets

    def pass_condition(self, t: Target):
        return Undetermined(
            "tool_missing",
            "equivalence of a replaced expectation needs evaluation; Phase 5")


def _is_expectation(text: str) -> bool:
    stripped = text.strip()
    if stripped.startswith(">>>") or stripped.startswith("#") or not stripped:
        return False
    if stripped.startswith("assert ") and "==" in stripped:
        return True
    # A doctest's expected-output line: indented, no prompt, not a statement keyword.
    return bool(text[:1].isspace() and not re.match(
        r"(assert|def|class|import|from|return|if|for|while|with|raise|print)\b", stripped))


# --- values and comparisons ---------------------------------------------------------------


@rule(id="SYMPY-C137", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class ExactValuesInTests:
    """Pre-condition: each numeric-constant division the agent wrote in a test that is
    not about floating point.
    Pass condition: at least one side is an exact SymPy number, so the value is `S(1)/2`
    rather than Python's `1/2`."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _division_targets(b, float_tests=False, prefix="exact")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        node, _ = t.payload
        if _wrapped_exact(node.left) or _wrapped_exact(node.right):
            return Satisfied()
        return Violated(f"line {node.lineno}: `{_render(node)}` is a Python float; "
                        f"use an exact SymPy value such as S(1)/2")


@rule(id="SYMPY-C142", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class FloatTestsUseFloatLiterals:
    """Pre-condition: each numeric constant the agent wrote in a test that does exercise
    floating-point behaviour.
    Pass condition: it is written as an explicit float literal, not as integer division."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _division_targets(b, float_tests=True, prefix="floatlit")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        node, _ = t.payload
        if isinstance(node, ast.Constant):
            return Satisfied()
        if _is_float_literal(node.left) or _is_float_literal(node.right):
            return Satisfied()
        return Violated(f"line {node.lineno}: float behaviour written as `{_render(node)}`; "
                        f"use an explicit float literal such as 0.5")


def _division_targets(b: EvidenceBundle, *, float_tests: bool, prefix: str) -> list[Target]:
    """Numeric-constant sites in owned tests, split by whether the test is about floats.

    C137 and C142 are complements over the same sites: the same `1/2` is a defect in an
    exact test and in a float test, but for opposite reasons, so each rule takes the
    half of the population the other excludes.
    """
    targets = []
    for path, module, function in _owned_tests(b):
        if function is None:
            targets.append(_unreadable_target(path, module))
            continue
        if _is_float_test(module, function) is not float_tests:
            continue
        sites: list[ast.AST] = list(_int_division_sites(function.node))
        if float_tests:
            sites += [n for n in ast.walk(function.node) if _is_float_literal(n)]
        for node in sorted(sites, key=lambda n: (n.lineno, n.col_offset)):
            span = pa.span_of(node)
            if _owns(b, path, span):
                targets.append(_target(f"{prefix}:{path}:{node.lineno}:{node.col_offset}",
                                       path, span, (node, function), _render(node)))
    return targets


def _words(text: str) -> frozenset[str]:
    """The identifier words in a name or path: `test_str_printing` -> {test, str, printing}."""
    return frozenset(w for w in re.split(r"[^a-z0-9]+", text.lower()) if w)


def _is_float_test(module: pa.PyModule, function: pa.FunctionDef) -> bool:
    if _words(function.name) & FLOAT_WORDS:
        return True
    return bool(_FLOAT_IN_BODY.search(_fn_source(module, function)))


def _render(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:  # noqa: BLE001 -- rendering is for the message only
        return type(node).__name__


@rule(id="SYMPY-C139", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class CompareExpressionsNotStrings:
    """Pre-condition: each equality assertion the agent wrote outside a printer test.
    Pass condition: neither side is the `str(...)` form of an expression."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module, function in _owned_tests(b):
            if function is None:
                targets.append(_unreadable_target(path, module))
                continue
            if _is_printer_context(path, function):
                continue
            for node in module.asserts_within(function.span()):
                if not isinstance(node.test, ast.Compare):
                    continue
                if not any(isinstance(o, (ast.Eq, ast.NotEq)) for o in node.test.ops):
                    continue
                span = pa.span_of(node)
                if _owns(b, path, span):
                    targets.append(_target(f"strcmp:{path}:{node.lineno}", path, span,
                                           node, _render(node.test)[:160]))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        node: ast.Assert = t.payload
        sides = [node.test.left, *node.test.comparators]
        for side in sides:
            name = pa.dotted_name(side.func).split(".")[-1] if isinstance(side, ast.Call) else ""
            if name in {"str", "repr", "sstr"}:
                return Violated(f"line {node.lineno}: compares `{_render(side)}` rather "
                                f"than the expression itself")
        return Satisfied()


def _is_printer_context(path: str, function: pa.FunctionDef) -> bool:
    return bool((_words(path) | _words(function.name)) & PRINTER_WORDS)


@rule(id="SYMPY-C140", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class ConstructExpressionsDirectly:
    """Pre-condition: each `sympify`/`S`/`parse_expr` call the agent wrote in a test that
    is not a parser test.
    Pass condition: its argument is not a string expression -- the input is constructed
    directly instead."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module in _modules(b, tests_only=True):
            if not module.ok:
                targets.append(_unreadable_target(path, module))
                continue
            if _words(path) & PARSER_WORDS:
                continue
            for call in module.calls:
                if call.short not in SYMPIFY_CALLS or not call.args:
                    continue
                function = module.enclosing_function(call.lineno)
                if function is None or not function.is_test:
                    continue
                if _words(function.name) & PARSER_WORDS or not _owns(b, path, call.span()):
                    continue
                targets.append(_target(f"sympify:{path}:{call.lineno}", path, call.span(),
                                       call, _render(call.node)[:160]))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        call: pa.CallSite = t.payload
        if _is_str_literal(call.args[0]):
            return Violated(f"line {call.lineno}: `{_render(call.node)[:60]}` sympifies a "
                            f"string; construct the expression directly")
        return Satisfied()


@rule(id="SYMPY-C141", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class AssumptionsComparedIdentically:
    """Pre-condition: each assertion the agent wrote that queries an assumption.
    Pass condition: it compares with `is True`, `is False` or `is None` rather than
    relying on truthiness."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path, module in _modules(b, tests_only=True):
            if not module.ok:
                targets.append(_unreadable_target(path, module))
                continue
            for node in module.asserts:
                span = pa.span_of(node)
                if not _owns(b, path, span) or not _queries_assumption(node):
                    continue
                targets.append(_target(f"assume:{path}:{node.lineno}", path, span,
                                       node, _render(node.test)[:160]))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        node: ast.Assert = t.payload
        test = node.test
        if isinstance(test, ast.Compare) and all(
            isinstance(op, (ast.Is, ast.IsNot)) for op in test.ops
        ) and all(
            isinstance(c, ast.Constant) and c.value in (True, False, None)
            for c in test.comparators
        ):
            return Satisfied()
        return Violated(f"line {node.lineno}: `{_render(test)[:60]}` relies on truthiness; "
                        f"compare with `is True`, `is False` or `is None`")


def _queries_assumption(node: ast.Assert) -> bool:
    """An `.is_<assumption>` access. Class predicates (`is_Symbol`, `is_Add`) are
    capitalised and are ordinary booleans, so they are excluded."""
    for inner in ast.walk(node):
        if isinstance(inner, ast.Attribute) and inner.attr.startswith("is_"):
            tail = inner.attr[3:]
            if tail and tail[0].islower():
                return True
        if isinstance(inner, ast.Call) and pa.dotted_name(inner.func).split(".")[-1] == "ask":
            return True
    return False

"""Django: Language and framework style -- the 23 rules that need no new extractor.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades. Where a rule reads "when X, do Y", the
pre-condition fires on X. Firing on Y is §4.2's bug -- it grades only the cases that were
already compliant, and an agent that never wrote the construct escapes as
``not_applicable``.

The category holds 41 rules and all 41 are here, in two batches. The first 23 are
answerable from the post-patch file text plus ``extractors/python_ast``. The other 18 --
import ordering (C019-C026, C039, C041) and Django templates (C002, C027-C033) -- waited
on ``extractors/imports`` and ``extractors/template_tags`` and are appended below, after
the JavaScript rules.

**Line-level rules judge the lines the agent added, never the whole file.** Invariant 5:
a style rule that scanned ``head_text`` would fail an agent for an 80-character line that
was in the file before it arrived. Every pre-condition below either selects
``FileChange.added_lines`` directly or requires the definition it judges to intersect
``authored_lines``.

**A file that will not parse.** Two rules here name a tool that provably rejects such a
file -- C001 (``black``) and C003 (``flake8``) -- and those return ``Violated``, following
``sympy.code_quality._syntax_violation``. The rest are conditional ("when you define a
model field, name it ..."), and on an unparseable file their antecedent cannot be
established at all, so they simply find no targets rather than manufacturing both the
situation and the violation. The purely lexical rules (C004, C005, C009, C042, C126,
C127, C130) never needed the AST and go on working.

**What "heuristic" means here.** Nineteen of the 41 are flagged. Three families dominate:
identifier-convention rules, where the lexical test is a proxy for a convention that has
framework-mandated exceptions (C010, C011, C127); the JavaScript rules, which are regexes
over text because the pack carries no JS parser (C126, C127, C130); and the rules whose
antecedent is an intent the source does not state -- "a string that may require
translation" (C007), "a boolean check" (C015), "a view function" (C034). Rules with an
exact, stated threshold -- C004's 88 characters, C005's 79, C042's trailing whitespace --
are not flagged, because there is one correct implementation of each.

The second batch adds five, from three more causes: a rule naming a tool nobody ran
(C019, isort, the same position C001 holds for black); a rule whose set is published in
Django's documentation and nowhere in its source (C026's convenience imports); and rules
whose sentence does not settle every case it covers (C002's HTML indentation, C032's
operator spacing, C039's "import time"). C020-C025, C027-C031, C033 and C041 are exact:
each names a form the extractor decides.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from typing import Iterator, Optional, Sequence

from compliance.core.models import (
    EvidenceBundle,
    FileChange,
    Satisfied,
    Target,
    Undetermined,
    Violated,
)
from compliance.core.registry import rule
from compliance.extractors import imports as im
from compliance.extractors import python_ast as pa
from compliance.extractors import template_tags as tt

CATEGORY = "Language and framework style"

# C004 is black's default line length, which is what Django configures. C005 is the
# older, tighter limit the coding-style page keeps for prose.
CODE_LINE_LIMIT = 88
PROSE_LINE_LIMIT = 79
# C126: .editorconfig sets indent_size = 4 for JavaScript.
JS_INDENT = 4

PY_SUFFIX = (".py",)
JS_SUFFIX = (".js",)
DOC_SUFFIX = (".txt", ".rst")

_TRAILING_WS = re.compile(r"[ \t]+$")
_FULL_LINE_COMMENT = re.compile(r"^\s*#")
_WE = re.compile(r"\bwe\b", re.IGNORECASE)
_CAMEL_HUMP = re.compile(r"[a-z0-9][A-Z]")
_PASCAL = re.compile(r"^_{0,2}[A-Z][A-Za-z0-9]*$")
_SNAKE_LOWER = re.compile(r"^[a-z_][a-z0-9_]*$")

# unittest and Django's own test API mandate these spellings, so a definition using one is
# following the framework rather than ignoring C010. Anything starting `assert` is a custom
# assertion method, which unittest requires be camelCase to sit beside its own.
_FRAMEWORK_CAMEL = frozenset({
    "setUp", "tearDown", "setUpClass", "tearDownClass", "setUpTestData", "runTest",
    "shortDescription", "addCleanup", "doCleanups", "subTest", "addTypeEqualityFunc",
    "maxDiff", "longMessage", "failureException", "databases", "fixtures",
})

# C007: the positions in which a string "may require translation". Not a decidable set --
# see the rule's docstring.
_GETTEXT = frozenset({
    "_", "gettext", "gettext_lazy", "gettext_noop", "ugettext", "ugettext_lazy",
    "ngettext", "ngettext_lazy", "ungettext", "ungettext_lazy",
    "pgettext", "pgettext_lazy", "npgettext", "npgettext_lazy",
})
_LOG_METHODS = frozenset({
    "debug", "info", "warning", "warn", "error", "exception", "critical", "log",
})
_LOGGER_NAMES = frozenset({"logger", "log", "logging", "_logger"})

# C035/C036/C037/C038: what counts as a model field declaration.
_RELATION_FIELDS = frozenset({
    "ForeignKey", "OneToOneField", "ManyToManyField", "ForeignObject",
    "GenericForeignKey", "GenericRelation",
})

# C013/C014/C015: the assertion families the three rules restrict.
_RAISE_ASSERTIONS = frozenset({
    "assertRaises", "assertWarns", "assertRaisesMessage", "assertWarnsMessage",
    "assertRaisesRegex", "assertWarnsRegex",
})
_BARE_RAISE_ASSERTIONS = frozenset({"assertRaises", "assertWarns"})
_REGEX_ASSERTIONS = frozenset({"assertRaisesRegex", "assertWarnsRegex"})
_BOOL_ASSERTIONS = frozenset({"assertTrue", "assertFalse"})
# Metacharacters whose presence means the pattern is doing regex work. `.` is excluded
# on purpose: it ends most English sentences, and treating that as "regex required" would
# pass every message that happens to be punctuated.
_REGEX_METACHARS = re.compile(r"[\\\[\](){}|*+?^$]")

# C016: the preambles the coding-style page tells you to drop. `that` is required, so a
# docstring opening with the noun "Test client ..." is not mistaken for one.
_DOCSTRING_PREAMBLE = re.compile(
    r"^\s*(?:this\s+(?:test|method|function)\b|"
    r"(?:tests?|testing|ensures?|ensuring|checks?|checking|verif(?:y|ies|ying)|"
    r"asserts?|confirms?|makes?\s+sure)\s+that\b)",
    re.IGNORECASE,
)

# C034: decorators that mark a plain function as a view, and the class-based-view methods
# that take `request` after `self`.
_VIEW_DECORATORS = frozenset({
    "require_http_methods", "require_GET", "require_POST", "require_safe",
    "login_required", "permission_required", "user_passes_test",
    "csrf_exempt", "csrf_protect", "requires_csrf_token", "ensure_csrf_cookie",
    "staff_member_required", "cache_page", "never_cache", "cache_control",
    "vary_on_headers", "vary_on_cookie", "xframe_options_exempt", "sensitive_post_parameters",
})
_HTTP_METHODS = frozenset({
    "get", "post", "put", "patch", "delete", "head", "options", "trace", "dispatch",
})

# C043: how a contributor signs their work in the source. `AUTHORS` is where the credit is
# supposed to go, so a change to it is the compliant behaviour and is never a target.
_SIGNATURE = re.compile(
    r"__author__\s*=|"
    r"@author\b|"
    r"\bauthors?\s*:\s*\S|"
    r"\b(?:written|contributed|authored|patch(?:ed)?|implemented)\s+by\s+[A-Z@]",
    re.IGNORECASE,
)
_AUTHORS_FILE = "AUTHORS"

# C127/C130: JavaScript, matched lexically because the pack carries no JS parser.
_JS_DECLARATION = re.compile(r"\b(?:var|let|const)\s+([A-Za-z_$][\w$]*)")
_JS_BLOCK_COMMENT_BODY = re.compile(r"^\s*\*")
_JS_ADD_LISTENER = re.compile(r"([\w$.\]\['\"]*)\.addEventListener\s*\(")
_JS_JQUERY_ON = re.compile(r"\.on\s*\(\s*(['\"])[^'\"]*\1\s*,\s*(['\"])")
_JS_ANY_ON = re.compile(r"\.on\s*\(")
_JS_DELEGATION_ROOTS = re.compile(
    r"\b(?:document|window|documentElement|body|container|wrapper|root|parent)\b",
    re.IGNORECASE,
)

# C129: the tool, and the hook runner that also runs it.
_BIOME = re.compile(r"\bbiome\b", re.IGNORECASE)
_PRE_COMMIT = re.compile(r"\bpre-commit\s+run\b")


# --- shared plumbing ----------------------------------------------------------------


def _target(key: str, path: Optional[str] = None, span=None, payload=None,
            snippet: str = "") -> Target:
    return Target(key=key, file=path, line_span=span, source="patch", payload=payload,
                  snippet=(snippet or "")[:200])


def _changed(bundle: EvidenceBundle, suffixes: tuple[str, ...]) -> Iterator[tuple[str, FileChange]]:
    """Text files of the given kind in the contribution, in stable path order."""
    for path in sorted(bundle.files):
        change = bundle.files[path]
        if change.is_binary or change.is_deleted:
            continue
        if path.endswith(suffixes):
            yield path, change


def _added(bundle: EvidenceBundle, suffixes: tuple[str, ...]) -> Iterator[tuple[str, int, str]]:
    """(path, line number, text) for every line the agent added to a file of this kind."""
    for path, change in _changed(bundle, suffixes):
        for lineno, text in change.added_lines:
            yield path, lineno, text


def _py_modules(bundle: EvidenceBundle) -> Iterator[tuple[str, FileChange, pa.PyModule]]:
    for path, change in _changed(bundle, PY_SUFFIX):
        yield path, change, pa.parse_module(change.head_text, path)


def _authored(change: FileChange, span: tuple[int, int]) -> bool:
    """Whether any line of ``span`` is one the agent wrote."""
    lo, hi = span
    return any(n in change.authored_lines for n in range(lo, hi + 1))


def _unparseable(bundle: EvidenceBundle) -> list[str]:
    """Python the agent shipped that is not valid Python.

    ``NO_SOURCE`` is excluded: a file we never reconstructed is our gap, not the
    contribution's, and must never be read as non-compliance.
    """
    broken = []
    for path, _, module in _py_modules(bundle):
        if not module.ok and module.error != pa.NO_SOURCE:
            broken.append(f"{path} ({module.error})")
    return broken


def _tokens(source: str) -> Optional[list[tokenize.TokenInfo]]:
    """Tokenised source, or None when it does not tokenise. Pure: no file is opened."""
    try:
        return list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, SyntaxError, IndentationError, ValueError):
        return None


def _comment_lines(change: FileChange, module: pa.PyModule) -> dict[int, str]:
    """Added lines that carry a comment, mapped to the comment text.

    Tokenised when the file tokenises, so a `#` inside a string is not mistaken for a
    comment; lexical otherwise, because a file that will not parse still has comments and
    withholding on it would lose real evidence.
    """
    out: dict[int, str] = {}
    tokens = _tokens(module.source) if module.source else None
    if tokens is not None:
        for token in tokens:
            if token.type == tokenize.COMMENT and token.start[0] in change.authored_lines:
                out[token.start[0]] = token.string
        return out
    for lineno, text in change.added_lines:
        if _FULL_LINE_COMMENT.match(text):
            out[lineno] = text.strip()
    return out


def _docstring_line_numbers(module: pa.PyModule) -> set[int]:
    numbers: set[int] = set()
    for doc in module.docstrings:
        numbers |= set(range(doc.lineno, doc.end_lineno + 1))
    return numbers


def _class_defs(module: pa.PyModule) -> Iterator[ast.ClassDef]:
    if module.tree is None:
        return
    for node in ast.walk(module.tree):
        if isinstance(node, ast.ClassDef):
            yield node


def _is_field_call(value: Optional[ast.AST]) -> bool:
    if not isinstance(value, ast.Call):
        return False
    name = pa.dotted_name(value.func).split(".")[-1]
    return name.endswith("Field") or name in _RELATION_FIELDS


def _assigned_name(stmt: ast.AST) -> Optional[str]:
    """The single name a class-body assignment binds, or None."""
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
        target = stmt.targets[0]
        return target.id if isinstance(target, ast.Name) else None
    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        return stmt.target.id
    return None


def _field_members(cls: ast.ClassDef) -> list[tuple[str, ast.AST]]:
    out = []
    for stmt in cls.body:
        name = _assigned_name(stmt)
        value = getattr(stmt, "value", None)
        if name is not None and _is_field_call(value):
            out.append((name, stmt))
    return out


def _is_model_class(cls: ast.ClassDef) -> bool:
    """A class Django would treat as a model: it inherits a Model, or declares fields."""
    for base in cls.bases:
        last = pa.dotted_name(base).split(".")[-1]
        if last == "Model" or last.endswith("Model"):
            return True
    return bool(_field_members(cls))


def _meta_class(cls: ast.ClassDef) -> Optional[ast.ClassDef]:
    for stmt in cls.body:
        if isinstance(stmt, ast.ClassDef) and stmt.name == "Meta":
            return stmt
    return None


def _blank_lines_above(source: str, lineno: int) -> int:
    lines = source.split("\n")
    count = 0
    index = lineno - 2  # 0-based index of the line above `lineno`
    while index >= 0 and not lines[index].strip():
        count += 1
        index -= 1
    return count


def _deferred_spans(tree: Optional[ast.AST]) -> list[tuple[int, int]]:
    """Line spans whose code runs when something calls it, not when the module is imported.

    A function's *body* is deferred; its decorators and its default arguments are not, and
    they are outside the spans returned here on purpose -- ``def f(x=settings.DEBUG)``
    reads settings at import time however it looks. A class body is not deferred either:
    it runs as the class is created, which is during the import.
    """
    spans: list[tuple[int, int]] = []
    if tree is None:
        return spans
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            spans.extend(pa.span_of(stmt) for stmt in node.body)
        elif isinstance(node, ast.Lambda):
            spans.append(pa.span_of(node.body))
    return spans


def _is_views_module(path: str) -> bool:
    return path.endswith("/views.py") or path == "views.py" or "/views/" in path


def _parameters(function: pa.FunctionDef) -> list[str]:
    args = function.node.args
    return [a.arg for a in (list(args.posonlyargs) + list(args.args))]


# --- formatting and line geometry ---------------------------------------------------


def _black_signals(source: str, authored: frozenset[int]) -> Optional[list[tuple[int, str]]]:
    """Constructs on the agent's lines that ``black`` would definitely have removed.

    Not a reimplementation of black -- see C001's docstring. Lines strictly inside a
    multi-line string are skipped, because black does not reformat string contents.
    """
    tokens = _tokens(source)
    if tokens is None:
        return None
    lines = source.split("\n")
    inside_string: set[int] = set()
    for token in tokens:
        if token.type == tokenize.STRING and token.end[0] > token.start[0]:
            inside_string |= set(range(token.start[0] + 1, token.end[0] + 1))

    signals: list[tuple[int, str]] = []
    for lineno in sorted(authored):
        if lineno < 1 or lineno > len(lines) or lineno in inside_string:
            continue
        text = lines[lineno - 1]
        if _TRAILING_WS.search(text):
            signals.append((lineno, "trailing whitespace"))
        indent = text[: len(text) - len(text.lstrip())]
        if "\t" in indent:
            signals.append((lineno, "tab indentation"))

    for token in tokens:
        if token.start[0] not in authored:
            continue
        if token.type == tokenize.OP and token.string == ";":
            signals.append((token.start[0], "`;` joining two statements"))
        elif token.type == tokenize.STRING:
            prefix_len = len(token.string) - len(token.string.lstrip("bBrRfFuU"))
            body = token.string[prefix_len:]
            if body.startswith("'") and not body.startswith("'''") and '"' not in body:
                signals.append((token.start[0],
                                f"single-quoted string {token.string[:32]}"))

    skipped = (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT,
               tokenize.COMMENT, tokenize.ENDMARKER)
    real = [t for t in tokens if t.type not in skipped]
    opens, closes = ("(", "[", "{"), (")", "]", "}")
    for left, right in zip(real, real[1:]):
        if left.end[0] != right.start[0] or right.start[1] == left.end[1]:
            continue
        if left.type == tokenize.OP and left.string in opens and right.string not in closes:
            if left.start[0] in authored:
                signals.append((left.start[0], f"space just inside `{left.string}`"))
        elif right.type == tokenize.OP and right.string in closes and left.string not in opens:
            if right.start[0] in authored:
                signals.append((right.start[0], f"space just inside `{right.string}`"))

    return sorted(set(signals))


@rule(id="DJANGO-C001", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class BlackFormatted:
    """Pre-condition: every Python file the agent added lines to.
    Pass condition: its added lines carry nothing black would have reformatted away.

    Lexical proxy, and flagged as one. Running black is forbidden (invariant 1) and
    comparing against black's output would need black itself, so this looks for
    constructs black provably eliminates -- tab indentation, trailing whitespace,
    semicolon-joined statements, single quotes on a string containing no double quote,
    and spaces just inside brackets. Passing means "no such construct", not "byte-identical
    to black's output".

    A file that does not parse fails: black refuses it, so the obligation is settled
    without needing to run anything.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        return [
            _target(f"black:{path}", path, None, (path, change, module), path)
            for path, change, module in _py_modules(bundle)
            if change.added_lines
        ]

    def pass_condition(self, target: Target):
        path, change, module = target.payload
        if not module.ok:
            if module.error == pa.NO_SOURCE:
                return Undetermined("parse_error", f"{path}: source not reconstructed")
            return Violated(f"black cannot format {path}: {module.error}")
        signals = _black_signals(module.source, change.authored_lines)
        if signals is None:
            return Violated(f"black cannot format {path}: it does not tokenise")
        if not signals:
            return Satisfied(f"{len(change.added_lines)} added line(s), no unformatted construct")
        shown = "; ".join(f"line {n}: {why}" for n, why in signals[:3])
        return Violated(f"{len(signals)} construct(s) black would have changed -- {shown}")


@rule(id="DJANGO-C003", category=CATEGORY, ownership="touched", reads=("files", "lint_run"))
class Pep8Conventions:
    """Pre-condition: the contribution contains Python to be merged.
    Pass condition: flake8, run under Django's own `.flake8` config, reports nothing new.

    The exclusions the rule names live in Django's `.flake8`, so the only faithful way to
    honour "except where the config excludes specific errors" is to let the configured tool
    decide. Invariant 1 forbids a checker from running it, so this reads the stored
    base-subtracted result the way `sympy.code_quality` does, and withholds by name when no
    linter ran. A submitted file that is not valid Python fails without needing the run --
    flake8 rejects it whatever the config says.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        paths = [path for path, _ in _changed(bundle, PY_SUFFIX)]
        if not paths:
            return []
        return [_target(f"pep8:{bundle.instance_id}", None, None, bundle,
                        f"{len(paths)} Python file(s) in the contribution")]

    def pass_condition(self, target: Target):
        bundle: EvidenceBundle = target.payload
        if broken := _unparseable(bundle):
            return Violated(f"cannot pass flake8: {len(broken)} submitted file(s) are not "
                            f"valid Python -- {'; '.join(broken[:3])}")
        report = bundle.lint.get("flake8")
        if report is None or not report.usable:
            note = report.note if report is not None else "no lint report for this run"
            return Undetermined("tool_missing", f"flake8 was not evaluated: {note}")
        if report.clean:
            return Satisfied(f"flake8 reports nothing new "
                             f"({report.n_findings_base} pre-existing finding(s) subtracted)")
        first = report.new_findings[0]
        return Violated(f"flake8 reports {report.n_findings_new} new finding(s), e.g. "
                        f"{first.path}: {first.code} {first.message}")


@rule(id="DJANGO-C004", category=CATEGORY, ownership="touched", reads=("files",))
class CodeLineLength:
    """Pre-condition: every line the agent added to a Python file.
    Pass condition: it is at most 88 characters long.

    88 is black's default and the limit Django configures, so the reading is "any line of
    Python", prose lines included -- C005 then applies its tighter 79 to the prose subset.
    Scoped to Python because the 88 comes from the formatter that only runs on Python.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        return [
            _target(f"line:{path}:{lineno}", path, (lineno, lineno), text, text)
            for path, lineno, text in _added(bundle, PY_SUFFIX)
        ]

    def pass_condition(self, target: Target):
        text: str = target.payload
        if len(text) > CODE_LINE_LIMIT:
            return Violated(f"line is {len(text)} chars, limit {CODE_LINE_LIMIT}")
        return Satisfied()


@rule(id="DJANGO-C005", category=CATEGORY, ownership="touched", reads=("files",))
class ProseLineLength:
    """Pre-condition: every documentation, comment or docstring line the agent added.
    Pass condition: it is at most 79 characters long.

    "Comment" is read as a whole line whose content is a comment, and "docstring" as a line
    of a docstring's body; a short statement with a long trailing comment is left to C004's
    88. Documentation means a `.txt` or `.rst` file under `docs/`, which is where Django's
    prose lives.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, lineno, text in _added(bundle, DOC_SUFFIX):
            if path.startswith("docs/") or "/docs/" in path:
                targets.append(_target(f"prose:{path}:{lineno}", path, (lineno, lineno),
                                       text, text))
        for path, change, module in _py_modules(bundle):
            comments = _comment_lines(change, module)
            docstrings = _docstring_line_numbers(module) if module.ok else set()
            for lineno, text in change.added_lines:
                whole_line_comment = lineno in comments and _FULL_LINE_COMMENT.match(text)
                if whole_line_comment or lineno in docstrings:
                    targets.append(_target(f"prose:{path}:{lineno}", path, (lineno, lineno),
                                           text, text))
        return targets

    def pass_condition(self, target: Target):
        text: str = target.payload
        if len(text) > PROSE_LINE_LIMIT:
            return Violated(f"prose line is {len(text)} chars, limit {PROSE_LINE_LIMIT}")
        return Satisfied()


@rule(id="DJANGO-C042", category=CATEGORY, ownership="touched", reads=("files",))
class NoTrailingWhitespace:
    """Pre-condition: every line the agent added to any text file in the contribution.
    Pass condition: it does not end in a space or a tab."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path in sorted(bundle.files):
            change = bundle.files[path]
            if change.is_binary or change.is_deleted:
                continue
            for lineno, text in change.added_lines:
                targets.append(_target(f"ws:{path}:{lineno}", path, (lineno, lineno),
                                       text, text))
        return targets

    def pass_condition(self, target: Target):
        text: str = target.payload
        if match := _TRAILING_WS.search(text):
            return Violated(f"line ends in {len(match.group(0))} whitespace char(s)")
        return Satisfied()


# --- comments and prose in code ------------------------------------------------------


@rule(id="DJANGO-C009", category=CATEGORY, ownership="touched", reads=("files",))
class NoWeInComments:
    """Pre-condition: every comment the agent added to a Python file.
    Pass condition: it does not use the word "we"."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, module in _py_modules(bundle):
            for lineno, text in sorted(_comment_lines(change, module).items()):
                targets.append(_target(f"comment:{path}:{lineno}", path, (lineno, lineno),
                                       text, text))
        return targets

    def pass_condition(self, target: Target):
        text: str = target.payload
        if match := _WE.search(text):
            return Violated(f"comment uses {match.group(0)!r}: {text.strip()[:60]!r}")
        return Satisfied()


@rule(id="DJANGO-C043", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class DoNotSignYourCode:
    """Pre-condition: every file the contribution changes other than `AUTHORS`.
    Pass condition: none of the lines the agent added signs the code with a name.

    Lexical proxy: an authorship signature is recognised by the forms it usually takes
    (`__author__ =`, `@author`, `Author:`, "written/contributed by <Name>"), which no
    pattern can enumerate. `AUTHORS` is excluded rather than judged, because it is exactly
    where the rule sends contributor credit.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path in sorted(bundle.files):
            change = bundle.files[path]
            if change.is_binary or change.is_deleted or not change.added_lines:
                continue
            if path.split("/")[-1] == _AUTHORS_FILE:
                continue
            targets.append(_target(f"sign:{path}", path, None, change, path))
        return targets

    def pass_condition(self, target: Target):
        change: FileChange = target.payload
        for lineno, text in change.added_lines:
            if _SIGNATURE.search(text):
                return Violated(f"line {lineno} signs the code: {text.strip()[:70]!r}")
        return Satisfied(f"{len(change.added_lines)} added line(s), no signature")


# --- naming --------------------------------------------------------------------------


def _bound_names(module: pa.PyModule) -> Iterator[tuple[str, int, str]]:
    """(name, line, kind) for every variable, function and method the module binds."""
    if module.tree is None:
        return
    for node in ast.walk(module.tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node.name, node.lineno, "function"
            args = node.args
            for arg in (list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs)):
                yield arg.arg, arg.lineno, "parameter"
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    yield target.id, target.lineno, "variable"
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            yield node.target.id, node.target.lineno, "variable"


@rule(id="DJANGO-C010", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class SnakeCaseNames:
    """Pre-condition: every variable, function or method name the agent introduced.
    Pass condition: it is not camelCase.

    The test is lexical -- a lowercase character immediately followed by an uppercase one
    -- and applied only to names that begin lowercase, so a variable holding a class
    (`MyModel = apps.get_model(...)`) is left to C011 rather than read as camelCase.
    Flagged heuristic for the exemptions: unittest mandates `setUp`, `tearDown` and
    `assert*` spellings, and a rule that failed those would be scoring the framework.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, module in _py_modules(bundle):
            if not module.ok:
                continue
            for name, lineno, kind in _bound_names(module):
                if lineno not in change.authored_lines:
                    continue
                if name in _FRAMEWORK_CAMEL or name.startswith("assert"):
                    continue
                if not (name[:1].islower() or name.startswith("_")):
                    continue
                targets.append(_target(f"name:{path}:{lineno}:{name}", path,
                                       (lineno, lineno), (name, kind), f"{kind} {name}"))
        return targets

    def pass_condition(self, target: Target):
        name, kind = target.payload
        if _CAMEL_HUMP.search(name):
            return Violated(f"{kind} {name!r} is camelCase, not snake_case")
        return Satisfied()


def _returns_a_class(function: ast.AST) -> bool:
    """Whether a function looks like it manufactures and returns a class."""
    local_classes = {n.name for n in ast.walk(function) if isinstance(n, ast.ClassDef)}
    for node in ast.walk(function):
        if not isinstance(node, ast.Return) or node.value is None:
            continue
        if isinstance(node.value, ast.Name) and node.value.id in local_classes:
            return True
        if isinstance(node.value, ast.Call):
            called = pa.dotted_name(node.value.func).split(".")[-1]
            if called in ("type", "ModelBase") or called in local_classes:
                return True
    return False


@rule(id="DJANGO-C011", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class PascalCaseClasses:
    """Pre-condition: every class the agent defined, and every function it wrote that
    returns a class.
    Pass condition: the name is PascalCase.

    Flagged heuristic for the second half of the antecedent: "class-returning factory
    function" is approximated by a `return` of a locally defined class or of `type(...)`,
    which neither catches every factory nor is certain about the ones it does catch. The
    PascalCase test itself is exact.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, module in _py_modules(bundle):
            if not module.ok:
                continue
            for node in ast.walk(module.tree):
                if isinstance(node, ast.ClassDef):
                    kind = "class"
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                        _returns_a_class(node):
                    kind = "class-returning function"
                else:
                    continue
                if node.lineno not in change.authored_lines:
                    continue
                targets.append(_target(f"pascal:{path}:{node.lineno}", path,
                                       pa.span_of(node), (node.name, kind),
                                       f"{kind} {node.name}"))
        return targets

    def pass_condition(self, target: Target):
        name, kind = target.payload
        if not _PASCAL.match(name):
            return Violated(f"{kind} {name!r} is not PascalCase")
        return Satisfied()


# --- translation ---------------------------------------------------------------------


def _translatable_strings(module: pa.PyModule) -> Iterator[tuple[ast.AST, str]]:
    """String expressions sitting where Django would expect a translatable message."""
    if module.tree is None:
        return
    for node in ast.walk(module.tree):
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
            exception = pa.dotted_name(node.exc.func).split(".")[-1] or "exception"
            for arg in node.exc.args[:1]:
                yield arg, f"message of raise {exception}"
        elif isinstance(node, ast.Call):
            dotted = pa.dotted_name(node.func)
            if not dotted:
                continue
            parts = dotted.split(".")
            short = parts[-1]
            if short in _GETTEXT:
                for arg in node.args:
                    yield arg, f"argument of {short}()"
            elif short in _LOG_METHODS and len(parts) > 1 and parts[-2] in _LOGGER_NAMES:
                for arg in node.args[:1]:
                    yield arg, f"message of {dotted}()"


@rule(id="DJANGO-C007", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class NoFStringForTranslatable:
    """Pre-condition: every string the agent wrote where a translation may be required --
    a gettext argument, an exception message, or a logging message.
    Pass condition: that string is not an f-string.

    Flagged heuristic because "may require translation" is a judgement no parser makes.
    The three positions above are the ones the rule names, so they are what the
    pre-condition fires on -- including the compliant plain-string cases, since selecting
    only f-strings would grade nothing but violations.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, module in _py_modules(bundle):
            if not module.ok:
                continue
            for node, where in _translatable_strings(module):
                if not isinstance(node, (ast.JoinedStr, ast.Constant)):
                    continue
                if isinstance(node, ast.Constant) and not isinstance(node.value, str):
                    continue
                lineno = getattr(node, "lineno", 0)
                if lineno not in change.authored_lines:
                    continue
                targets.append(_target(f"fstring:{path}:{lineno}", path,
                                       pa.span_of(node), (node, where), where))
        return targets

    def pass_condition(self, target: Target):
        node, where = target.payload
        if isinstance(node, ast.JoinedStr):
            return Violated(f"f-string used as the {where}")
        return Satisfied(f"plain string as the {where}")


# --- test assertion style ------------------------------------------------------------


def _assertion_calls(bundle: EvidenceBundle, names: frozenset[str]) -> Iterator[
        tuple[str, pa.CallSite]]:
    """Calls to one of ``names`` on a line the agent wrote."""
    for path, change, module in _py_modules(bundle):
        if not module.ok:
            continue
        for call in module.calls:
            if call.short in names and call.lineno in change.authored_lines:
                yield path, call


@rule(id="DJANGO-C013", category=CATEGORY, ownership="touched", reads=("files",))
class PreferAssertRaisesMessage:
    """Pre-condition: every assertion the agent wrote that an exception or warning is raised.
    Pass condition: it is not the bare `assertRaises()` / `assertWarns()`.

    The antecedent is the assertion, not the bare form, so a test that already uses
    `assertRaisesMessage` is graded and passes rather than disappearing. The `*Regex`
    variants pass here and are judged by C014, which is the rule that restricts them.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        return [
            _target(f"raises:{path}:{call.lineno}", path, call.span(), call.short,
                    f"{call.func}()")
            for path, call in _assertion_calls(bundle, _RAISE_ASSERTIONS)
        ]

    def pass_condition(self, target: Target):
        name: str = target.payload
        if name in _BARE_RAISE_ASSERTIONS:
            return Violated(f"{name}() used; prefer {name}Message()")
        return Satisfied(f"{name}()")


@rule(id="DJANGO-C014", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class RegexAssertionsOnlyWhenNeeded:
    """Pre-condition: every `assertRaisesRegex()` / `assertWarnsRegex()` the agent wrote.
    Pass condition: the expected pattern actually needs regex matching.

    "Needs regex matching" is proxied by the pattern containing a metacharacter, with `.`
    deliberately excluded -- it ends most English sentences, and counting it would pass
    every punctuated message. A pattern wrapped in `re.escape()` fails: escaping every
    metacharacter is a statement that no regex matching was wanted. A pattern that is not a
    literal is given the benefit of the doubt, because nothing in the file settles it.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        return [
            _target(f"regexassert:{path}:{call.lineno}", path, call.span(), call,
                    f"{call.func}()")
            for path, call in _assertion_calls(bundle, _REGEX_ASSERTIONS)
        ]

    def pass_condition(self, target: Target):
        call: pa.CallSite = target.payload
        pattern = call.args[1] if len(call.args) > 1 else None
        if isinstance(pattern, ast.Call) and \
                pa.dotted_name(pattern.func).split(".")[-1] == "escape":
            return Violated(f"{call.short}() with an re.escape()d pattern -- no regex "
                            f"matching is wanted, so use the Message variant")
        if not (isinstance(pattern, ast.Constant) and isinstance(pattern.value, str)):
            return Satisfied(f"{call.short}() pattern is not a literal; not decidable here")
        if _REGEX_METACHARS.search(pattern.value):
            return Satisfied("pattern uses regex metacharacters")
        return Violated(f"{call.short}() with the plain literal {pattern.value[:50]!r}; "
                        f"no regex matching is required")


@rule(id="DJANGO-C015", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class AssertIsForBooleans:
    """Pre-condition: every boolean assertion the agent wrote -- `assertTrue`,
    `assertFalse`, or `assertIs(x, True/False)`.
    Pass condition: it is the `assertIs(x, True/False)` form.

    Flagged heuristic because "for boolean checks" is not decidable from the call site:
    `assertTrue(qs.exists())` is a boolean check and `assertTrue(response.content)` is a
    truthiness check, and they are the same syntax. Every `assertTrue`/`assertFalse` is
    therefore treated as a boolean check, which is the stricter reading.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, call in _assertion_calls(bundle, _BOOL_ASSERTIONS | {"assertIs"}):
            if call.short == "assertIs":
                second = call.args[1] if len(call.args) > 1 else None
                if not (isinstance(second, ast.Constant) and second.value in (True, False)):
                    continue
            targets.append(_target(f"boolassert:{path}:{call.lineno}", path, call.span(),
                                   call.short, f"{call.func}()"))
        return targets

    def pass_condition(self, target: Target):
        name: str = target.payload
        if name in _BOOL_ASSERTIONS:
            return Violated(f"{name}() used for a boolean check; use assertIs(x, "
                            f"{'True' if name == 'assertTrue' else 'False'})")
        return Satisfied("assertIs(x, True/False)")


@rule(id="DJANGO-C016", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class TestDocstringIsDirect:
    """Pre-condition: every docstring the agent wrote on a test function.
    Pass condition: it opens with the behaviour itself, not a "Tests that ..." preamble.

    Flagged heuristic: the class of preambles is open-ended, so this matches the family the
    coding-style page names plus the obvious neighbours, and requires the following
    "that" so a docstring opening with the noun phrase "Test client redirects." is not
    mistaken for one.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, module in _py_modules(bundle):
            if not module.ok:
                continue
            for doc in module.docstrings:
                if doc.kind != "function":
                    continue
                if not doc.owner.split(".")[-1].startswith(pa.TEST_PREFIX):
                    continue
                if not _authored(change, doc.span()):
                    continue
                targets.append(_target(f"testdoc:{path}:{doc.lineno}", path, doc.span(),
                                       doc.text, doc.text[:120]))
        return targets

    def pass_condition(self, target: Target):
        text: str = target.payload
        if match := _DOCSTRING_PREAMBLE.match(text):
            return Violated(f"docstring opens with the preamble {match.group(0).strip()!r}")
        return Satisfied()


# --- framework idioms ----------------------------------------------------------------


@rule(id="DJANGO-C034", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class ViewFirstParameterIsRequest:
    """Pre-condition: every view function the agent wrote.
    Pass condition: its first parameter -- after `self`/`cls` on a method -- is named
    `request`.

    Flagged heuristic for the pre-condition: nothing in the source says "this is a view".
    A function counts as one when it carries a view decorator, lives at module level in a
    `views.py` / `views/` module, or is an HTTP-method handler on a class whose name ends
    in `View`. Private helpers (leading underscore) are excluded, which is where a
    `views.py` module keeps the functions that are not views.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, module in _py_modules(bundle):
            if not module.ok:
                continue
            for function in module.functions:
                if function.name.startswith("_") or function.lineno not in change.authored_lines:
                    continue
                parts = function.qualname.split(".")
                parent = parts[-2] if len(parts) > 1 else ""
                is_view = (
                    function.has_decorator(*_VIEW_DECORATORS)
                    or (_is_views_module(path) and not parent)
                    or (function.name in _HTTP_METHODS and parent.endswith("View"))
                )
                if not is_view:
                    continue
                targets.append(_target(f"view:{path}:{function.lineno}", path,
                                       function.span(), function, f"def {function.name}"))
        return targets

    def pass_condition(self, target: Target):
        function: pa.FunctionDef = target.payload
        params = _parameters(function)
        if params and params[0] in ("self", "cls"):
            params = params[1:]
        if not params:
            return Violated(f"view {function.name}() takes no request parameter")
        if params[0] != "request":
            return Violated(f"view {function.name}()'s first parameter is {params[0]!r}, "
                            f"not 'request'")
        return Satisfied()


@rule(id="DJANGO-C035", category=CATEGORY, ownership="touched", reads=("files",))
class ModelFieldNames:
    """Pre-condition: every model field the agent declared.
    Pass condition: its attribute name is lowercase snake_case.

    A field is a class-body assignment whose value calls something named `*Field` or one of
    Django's relation classes, which is what a field declaration is; the name test is the
    exact `[a-z_][a-z0-9_]*`.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, module in _py_modules(bundle):
            if not module.ok:
                continue
            for cls in _class_defs(module):
                for name, stmt in _field_members(cls):
                    if stmt.lineno not in change.authored_lines:
                        continue
                    targets.append(_target(f"field:{path}:{stmt.lineno}", path,
                                           pa.span_of(stmt), (cls.name, name),
                                           f"{cls.name}.{name}"))
        return targets

    def pass_condition(self, target: Target):
        class_name, name = target.payload
        if not _SNAKE_LOWER.match(name):
            return Violated(f"model field {class_name}.{name} is not lowercase snake_case")
        return Satisfied()


@rule(id="DJANGO-C036", category=CATEGORY, ownership="touched", reads=("files",))
class MetaAfterFields:
    """Pre-condition: every model class the agent edited that declares an inner `class Meta`.
    Pass condition: `Meta` comes after every field, with exactly one blank line before it.

    The blank-line half is judged only when the agent wrote the `class Meta` line itself:
    if `Meta` was already there and the agent only added a field, the whitespace above it
    is not the agent's, and only the ordering is.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, module in _py_modules(bundle):
            if not module.ok:
                continue
            for cls in _class_defs(module):
                meta = _meta_class(cls)
                if meta is None:
                    continue
                fields = _field_members(cls)
                touched = meta.lineno in change.authored_lines or any(
                    stmt.lineno in change.authored_lines for _, stmt in fields
                )
                if not touched:
                    continue
                payload = (cls, meta, fields, change, module.source)
                targets.append(_target(f"meta:{path}:{meta.lineno}", path,
                                       pa.span_of(meta), payload, f"{cls.name}.Meta"))
        return targets

    def pass_condition(self, target: Target):
        cls, meta, fields, change, source = target.payload
        after = [name for name, stmt in fields if stmt.lineno > meta.lineno]
        if after:
            return Violated(f"{cls.name}.Meta is declared before the field(s) "
                            f"{', '.join(after[:3])}")
        if meta.lineno not in change.authored_lines:
            return Satisfied(f"{cls.name}.Meta follows all {len(fields)} field(s)")
        if meta is cls.body[0]:
            return Satisfied(f"{cls.name}.Meta is the class's first member")
        blanks = _blank_lines_above(source, meta.lineno)
        if blanks != 1:
            return Violated(f"{blanks} blank line(s) before {cls.name}.Meta, expected 1")
        return Satisfied()


_MEMBER_ORDER = ("field", "manager", "Meta", "dunder method", "save()",
                 "get_absolute_url()", "custom method")


def _member_rank(stmt: ast.AST) -> Optional[int]:
    """Where a class member sits in C037's order, or None when the rule does not place it."""
    name = _assigned_name(stmt)
    if name is not None:
        value = getattr(stmt, "value", None)
        if _is_field_call(value):
            return 0
        called = pa.dotted_name(value.func).split(".")[-1] if isinstance(value, ast.Call) else ""
        if name == "objects" or called.endswith("Manager"):
            return 1
        return None
    if isinstance(stmt, ast.ClassDef) and stmt.name == "Meta":
        return 2
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if stmt.name.startswith("__") and stmt.name.endswith("__"):
            return 3
        if stmt.name == "save":
            return 4
        if stmt.name == "get_absolute_url":
            return 5
        return 6
    return None


@rule(id="DJANGO-C037", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class ModelMemberOrder:
    """Pre-condition: every model class the agent added a member to.
    Pass condition: its members appear in the prescribed order -- fields, managers, Meta,
    dunder methods, save(), get_absolute_url(), then custom methods.

    Flagged heuristic for one step of the classification: "manager attribute" is recognised
    as an assignment named `objects` or one calling a `*Manager`, which is the convention
    rather than a fact the source states. Members the rule does not place -- constants,
    nested non-Meta classes -- are skipped rather than guessed at.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, module in _py_modules(bundle):
            if not module.ok:
                continue
            for cls in _class_defs(module):
                if not _is_model_class(cls):
                    continue
                ranked = [(stmt, rank) for stmt in cls.body
                          if (rank := _member_rank(stmt)) is not None]
                if len(ranked) < 2:
                    continue
                if not any(stmt.lineno in change.authored_lines for stmt, _ in ranked):
                    continue
                targets.append(_target(f"order:{path}:{cls.lineno}", path, pa.span_of(cls),
                                       (cls.name, ranked), f"class {cls.name}"))
        return targets

    def pass_condition(self, target: Target):
        class_name, ranked = target.payload
        previous_rank, previous_stmt = ranked[0][1], ranked[0][0]
        for stmt, rank in ranked[1:]:
            if rank < previous_rank:
                return Violated(
                    f"{class_name}: {_MEMBER_ORDER[rank]} at line {stmt.lineno} comes after "
                    f"{_MEMBER_ORDER[previous_rank]} at line {previous_stmt.lineno}"
                )
            previous_rank, previous_stmt = rank, stmt
        return Satisfied(f"{len(ranked)} placed member(s) in order")


@rule(id="DJANGO-C038", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class ChoicesDeclaration:
    """Pre-condition: every `choices=` argument the agent wrote.
    Pass condition: it names an all-uppercase class attribute or a TextChoices /
    IntegerChoices enum, rather than an inline literal.

    Flagged heuristic: the "mapped to labels" half of the rule is about the shape of the
    referenced constant, which a `choices=STATUS_CHOICES` reference does not carry to the
    call site. What is decided here is the reference form -- an inline list or tuple, or a
    lowercase name, is a violation; a `SomeChoices.choices` attribute or an ALL_CAPS name
    passes; anything else is given the benefit of the doubt.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, module in _py_modules(bundle):
            if not module.ok:
                continue
            for node in ast.walk(module.tree):
                if not isinstance(node, ast.Call):
                    continue
                for keyword in node.keywords:
                    if keyword.arg != "choices":
                        continue
                    lineno = getattr(keyword.value, "lineno", node.lineno)
                    if lineno not in change.authored_lines:
                        continue
                    targets.append(_target(f"choices:{path}:{lineno}", path,
                                           (lineno, lineno), keyword.value,
                                           f"choices= at line {lineno}"))
        return targets

    def pass_condition(self, target: Target):
        value = target.payload
        if isinstance(value, (ast.List, ast.Tuple)):
            return Violated("choices= is an inline literal; use all-uppercase class "
                            "attributes or a TextChoices/IntegerChoices enum")
        if isinstance(value, ast.Name):
            if value.id.isupper() or _PASCAL.match(value.id):
                return Satisfied(f"choices={value.id}")
            return Violated(f"choices={value.id} is not an all-uppercase attribute "
                            f"and not a TextChoices/IntegerChoices enum")
        if isinstance(value, ast.Attribute):
            if value.attr == "choices" or value.attr.isupper():
                return Satisfied(f"choices={pa.dotted_name(value)}")
            return Violated(f"choices={pa.dotted_name(value)} is neither an all-uppercase "
                            f"attribute nor a `.choices` enum")
        return Satisfied("choices= form is not decidable from the call site")


# --- JavaScript ----------------------------------------------------------------------


@rule(id="DJANGO-C126", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class JavaScriptIndentation:
    """Pre-condition: every indented line the agent added to a JavaScript file.
    Pass condition: the indent is spaces, a multiple of the .editorconfig's 4.

    Flagged heuristic: the pack carries no JavaScript parser, so a continuation line
    aligned to an opening bracket is indistinguishable from a mis-indented statement. Block
    comment bodies (` * ...`) are excluded, since their extra space is the comment style.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, lineno, text in _added(bundle, JS_SUFFIX):
            if not text.strip() or _JS_BLOCK_COMMENT_BODY.match(text):
                continue
            indent = text[: len(text) - len(text.lstrip())]
            if not indent:
                continue
            targets.append(_target(f"jsindent:{path}:{lineno}", path, (lineno, lineno),
                                   indent, text))
        return targets

    def pass_condition(self, target: Target):
        indent: str = target.payload
        if "\t" in indent:
            return Violated("indented with a tab, not spaces")
        if len(indent) % JS_INDENT:
            return Violated(f"indented {len(indent)} spaces, not a multiple of {JS_INDENT}")
        return Satisfied()


@rule(id="DJANGO-C127", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class JavaScriptCamelCase:
    """Pre-condition: every JavaScript variable the agent declared.
    Pass condition: its name is camelCase, not snake_case.

    Flagged heuristic: declarations are found by regex over the added text, so a `var`
    inside a string or a comment is matched too. ALL_CAPS names pass, being the
    conventional spelling for a JavaScript constant, and PascalCase names pass, being the
    conventional spelling for a constructor.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, lineno, text in _added(bundle, JS_SUFFIX):
            for name in _JS_DECLARATION.findall(text):
                targets.append(_target(f"jsname:{path}:{lineno}:{name}", path,
                                       (lineno, lineno), name, text.strip()))
        return targets

    def pass_condition(self, target: Target):
        name: str = target.payload
        if name.isupper():
            return Satisfied(f"{name} is a constant")
        if "_" in name.strip("_"):
            return Violated(f"JavaScript variable {name!r} is snake_case, not camelCase")
        return Satisfied()


@rule(id="DJANGO-C129", category=CATEGORY, ownership="touched", reads=("files", "commands"))
class BiomeWasRun:
    """Pre-condition: the contribution changes JavaScript.
    Pass condition: Biome was run over it, directly or through pre-commit.

    The antecedent is the JavaScript change, not the Biome invocation: firing on the
    invocation would let an agent that changed JavaScript and checked nothing collect
    `not_applicable`.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        paths = [path for path, _ in _changed(bundle, JS_SUFFIX)]
        if not paths:
            return []
        return [_target(f"biome:{bundle.instance_id}", None, None, bundle,
                        f"{len(paths)} JavaScript file(s): {', '.join(paths[:3])}")]

    def pass_condition(self, target: Target):
        bundle: EvidenceBundle = target.payload
        for command in bundle.commands:
            if _BIOME.search(command.command):
                return Satisfied(f"ran `{command.command.strip()[:60]}`")
            if _PRE_COMMIT.search(command.command):
                return Satisfied(f"ran Biome via `{command.command.strip()[:60]}`")
        return Violated("changed JavaScript but never ran Biome or pre-commit")


@rule(id="DJANGO-C130", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class PreferEventDelegation:
    """Pre-condition: every event handler the agent bound in a JavaScript file.
    Pass condition: it is bound by delegation -- on a container or with a selector --
    rather than directly to an element.

    Flagged heuristic, and the most approximate rule in the pack: whether a binding
    survives a DOM change depends on what the receiver expression evaluates to, which no
    regex knows. Delegation is inferred from a container-ish receiver (`document`,
    `window`, `body`, a name containing `container`/`wrapper`/`root`/`parent`) or from
    jQuery's three-argument `.on(event, selector, handler)`.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, lineno, text in _added(bundle, JS_SUFFIX):
            if _JS_ADD_LISTENER.search(text) or _JS_ANY_ON.search(text):
                targets.append(_target(f"jsbind:{path}:{lineno}", path, (lineno, lineno),
                                       text, text.strip()))
        return targets

    def pass_condition(self, target: Target):
        text: str = target.payload
        if _JS_JQUERY_ON.search(text):
            return Satisfied("delegated: .on(event, selector, handler)")
        for match in _JS_ADD_LISTENER.finditer(text):
            receiver = match.group(1)
            if not _JS_DELEGATION_ROOTS.search(receiver):
                return Violated(f"handler bound directly to {receiver or '<expression>'}; "
                                f"delegate from a container instead")
            return Satisfied(f"delegated from {receiver}")
        if _JS_ANY_ON.search(text):
            return Violated("`.on(event, handler)` binds directly; pass a selector to "
                            "delegate")
        return Satisfied()


# ======================================================================================
# Imports (C019-C026, C039, C041) and Django templates (C002, C027-C033).
#
# These eighteen were held back until `extractors/imports` and `extractors/template_tags`
# existed. They follow the same two-layer shape as everything above and the same invariant
# 5 discipline: a rule here judges the import statements and the tags the *agent wrote*,
# never the ones it inherited from the file it opened.
# ======================================================================================


# --- the repository's own vocabulary --------------------------------------------------

# Layer C may name its repository; the extractor may not (`tests/test_layers.py`). This is
# the package whose absolute imports Django's coding-style page calls "other Django
# components" -- the fourth group -- as opposed to somebody else's library.
DJANGO_PACKAGES = frozenset({"django"})

# C020's declared order, in the extractor's vocabulary. `first_party` is "other Django
# component" and `local` is "local Django component". The sixth group the sentence names,
# try/except, is not a name-based group at all: it is a *position*, and C020 checks it
# separately.
DJANGO_GROUP_ORDER = (im.FUTURE, im.STDLIB, im.THIRD_PARTY, im.FIRST_PARTY, im.LOCAL)
IMPORT_POLICY = im.GroupPolicy(first_party=DJANGO_PACKAGES, order=DJANGO_GROUP_ORDER)

# What each group is called in the sentence the rule comes from, so a violation quotes the
# rule's own words rather than the extractor's identifiers.
_GROUP_LABEL = {
    im.FUTURE: "__future__",
    im.STDLIB: "standard library",
    im.THIRD_PARTY: "third-party",
    im.FIRST_PARTY: "other Django component",
    im.LOCAL: "local Django component",
}

# C022: Django allows `from .models import X` and forbids `from ..models import X`.
MAX_RELATIVE_DEPTH = 1
# C024: the continuation indent the coding-style page prescribes for a wrapped import.
IMPORT_CONTINUATION_INDENT = 4
# C002: 4 for Python, 2 for HTML.
PY_INDENT = 4
HTML_INDENT = 2

TEMPLATE_SUFFIX = tt.TEMPLATE_SUFFIXES

# C019: finds an import in a file that will not parse, where the extractor cannot.
_IMPORT_LINE = re.compile(r"^\s*(?:import|from)\s+[.\w]")

# C019/C020: the ordering fault the extractor does not report -- see `_module_order_problems`.
MODULES_UNSORTED = "modules_unsorted"
IMPORT_AFTER_GUARDED = "import_after_guarded"

# C026: internal module paths Django re-exports from a shorter, documented one. Not a map
# of Django's public API -- the source does not carry one -- so this is the family the
# coding-style page's own example (`from django.views import View`) belongs to. It
# under-reports by construction, which is the safe direction and why C026 is heuristic.
_DJANGO_INTERNAL = {
    "django.views.generic.base": "django.views.generic",
    "django.views.generic.detail": "django.views.generic",
    "django.views.generic.edit": "django.views.generic",
    "django.views.generic.list": "django.views.generic",
    "django.db.models.base": "django.db.models",
    "django.db.models.fields": "django.db.models",
    "django.db.models.fields.related": "django.db.models",
    "django.db.models.manager": "django.db.models",
    "django.db.models.query": "django.db.models",
    "django.forms.fields": "django.forms",
    "django.forms.forms": "django.forms",
    "django.forms.models": "django.forms",
    "django.forms.widgets": "django.forms",
    "django.http.request": "django.http",
    "django.http.response": "django.http",
    "django.template.base": "django.template",
    "django.template.context": "django.template",
    "django.urls.base": "django.urls",
    "django.urls.conf": "django.urls",
    "django.urls.resolvers": "django.urls",
    "django.utils.translation.trans_real": "django.utils.translation",
}

# C039: the module the lazy settings object lives in, and the name it is bound to.
_SETTINGS_MODULE = "django.conf"
_SETTINGS_NAME = "settings"

# C032: tokens the corpus sentence does not place. It names `.` and `|` as the two that
# stay tight and says nothing about the rest, but the tag syntax itself settles them: a
# filter argument (`|date:"Y"`), a keyword argument (`pk=1`) and a bracketed subscript are
# written flush in every example Django publishes. Listed here rather than in the
# extractor, because this is a reading of one project's sentence.
_FLUSH_AFTER = frozenset({":", "=", "(", "["})
_FLUSH_BEFORE = frozenset({":", "=", ",", ")", "]"})

# C029: `{% load x from lib %}` names one library and one tag, so the alphabetical
# requirement is not about its arguments.
_LOAD_FROM = "from"


# --- shared plumbing for the import rules ---------------------------------------------


def _import_lines(path: str, module: pa.PyModule) -> tuple[im.ImportLine, ...]:
    """Every import statement in a parsed module, classified under Django's policy."""
    return im.import_lines(module=module, policy=IMPORT_POLICY, path=path)


def _import_files(bundle: EvidenceBundle) -> Iterator[
        tuple[str, FileChange, pa.PyModule, tuple[im.ImportLine, ...], tuple[im.ImportLine, ...]]]:
    """(path, change, module, all imports, the ones the agent wrote) per Python file.

    A file that does not parse yields nothing: the extractor returns no imports for it,
    and every rule built on this one is conditional -- its antecedent is an import
    statement, which an unreadable file does not provide. C019 is the exception and finds
    its imports lexically, because the tool it names rejects such a file outright.
    """
    for path, change, module in _py_modules(bundle):
        if not module.ok:
            continue
        lines = _import_lines(path, module)
        authored = tuple(line for line in lines if _authored(change, line.span()))
        if authored:
            yield path, change, module, lines, authored


def _module_sort_key(line: im.ImportLine) -> tuple[int, str]:
    """How one import statement sorts against its neighbours in the same group."""
    return (line.level, line.module.lower())


def _module_order_problems(lines: Sequence[im.ImportLine]) -> list[im.Problem]:
    """Consecutive imports of the same kind in one group that are not alphabetical.

    The one ordering question `extractors/imports` does not answer. It sorts the names on
    a single line (`name_order_problems`) and the groups (`group_order_problems`), but
    nothing there orders the *statements* within a group, which is the second half of
    C020's sentence. Bands are `(group, plain-or-from)` so this never contradicts C021,
    which is the rule that puts `import x` before `from x import y`.
    """
    problems: list[im.Problem] = []
    previous: Optional[tuple[tuple[str, bool], tuple[int, str], str, int]] = None
    for line in lines:
        band = (line.group, line.is_from)
        key = _module_sort_key(line)
        if previous is not None and previous[0] == band and key < previous[1]:
            problems.append(im.Problem(
                MODULES_UNSORTED, line.lineno,
                f"{line.module or '.'} sorts before {previous[2]} on line {previous[3]}",
                previous[3],
            ))
        previous = (band, key, line.module or ".", line.lineno)
    return problems


def _guarded_position_problems(lines: Sequence[im.ImportLine]) -> list[im.Problem]:
    """Plain imports left below a `try:`-guarded one -- C020's sixth group, out of place."""
    guarded = [line for line in lines if line.context == "try"]
    if not guarded:
        return []
    first = min(line.context_lineno or line.lineno for line in guarded)
    return [
        im.Problem(IMPORT_AFTER_GUARDED, line.lineno,
                   f"{_GROUP_LABEL.get(line.group, line.group)} import follows the "
                   f"try/except imports", first)
        for line in im.top_level(lines) if line.lineno > first
    ]


def _on_authored_lines(problems: Sequence[im.Problem], change: FileChange) -> list[im.Problem]:
    """Only the problems reported against a line the agent wrote.

    Invariant 5 in one line. An agent that appends a stdlib import to an inherited block
    owns the line it added; it does not own the mis-grouped line that was already there,
    and a rule that reported the latter would be scoring the file's history.
    """
    return [p for p in problems if p.lineno in change.authored_lines]


def _first_line(text: str) -> str:
    return text.split("\n", 1)[0].strip()


# --- shared plumbing for the template rules -------------------------------------------


def _templates(bundle: EvidenceBundle) -> Iterator[tuple[str, FileChange, list[tt.TemplateNode]]]:
    """(path, change, lexed nodes) for every template file in the contribution."""
    for path, change in _changed(bundle, TEMPLATE_SUFFIX):
        if change.head_text is None:
            continue
        yield path, change, tt.tokenize(change.head_text)


def _wrote(change: FileChange, node: tt.TemplateNode) -> bool:
    return _authored(change, node.span)


def _extends_tag(nodes: Sequence[tt.TemplateNode]) -> Optional[tt.TemplateNode]:
    tags = tt.tags_named(nodes, "extends")
    return tags[0] if tags else None


def _contains(outer: tt.TagPair, inner: tt.TagPair) -> bool:
    """Whether `inner` sits inside `outer`'s body."""
    if outer is inner or not outer.is_closed:
        return False
    start = (outer.opener.lineno, outer.opener.col)
    end = (outer.closer.lineno, outer.closer.col)
    here = (inner.opener.lineno, inner.opener.col)
    return start < here < end


# --- imports: order ------------------------------------------------------------------


@rule(id="DJANGO-C019", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class ImportsAreSorted:
    """Pre-condition: every Python file the agent added an import statement to.
    Pass condition: nothing about the imports it added is something isort would move.

    A lexical proxy for a tool, exactly as C001 is for black. Running isort is forbidden
    (invariant 1), no stored isort run exists, and comparing against its output would need
    isort itself -- so this asks the three questions isort's Django profile answers:
    are the groups in the declared order, does `import x` precede `from x import y`, and
    are the names on each line alphabetised. Passing means "isort has nothing to move",
    not "byte-identical to isort's output". C020, C021 and C023 each own one facet and
    name it in their message; this is the aggregate the rule's sentence describes.

    A file that will not parse fails, because isort rejects it -- which is why the
    pre-condition finds imports with a regex rather than through the extractor.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, module in _py_modules(bundle):
            if not any(_IMPORT_LINE.match(text) for _, text in change.added_lines):
                continue
            targets.append(_target(f"isort:{path}", path, None, (path, change, module),
                                   path))
        return targets

    def pass_condition(self, target: Target):
        path, change, module = target.payload
        if not module.ok:
            if module.error == pa.NO_SOURCE:
                return Undetermined("parse_error", f"{path}: source not reconstructed")
            return Violated(f"isort cannot sort {path}: {module.error}")
        lines = _import_lines(path, module)
        top = im.top_level(lines)
        problems = _on_authored_lines(
            im.group_order_problems(top, IMPORT_POLICY)
            + _module_order_problems(top)
            + im.statement_order_problems(top)
            + im.name_order_problems(lines),
            change,
        )
        if not problems:
            return Satisfied(f"{len(lines)} import statement(s), none isort would move")
        shown = "; ".join(f"line {p.lineno}: {p.detail}" for p in problems[:3])
        return Violated(f"{len(problems)} import(s) isort would reorder -- {shown}")


@rule(id="DJANGO-C020", category=CATEGORY, ownership="touched", reads=("files",))
class ImportGroupOrder:
    """Pre-condition: every Python file the agent added an import statement to.
    Pass condition: its groups run future, standard library, third-party, other Django,
    local Django, then the try/except imports, alphabetically within each group.

    "Other Django component" is an absolute `django.*` import and "local Django component"
    is a relative one, which is how the coding-style page's own examples read. The sixth
    group is not a group of names at all -- a `try:`-guarded import can be of anything --
    so it is checked as a position: no plain import may follow one.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        return [
            _target(f"groups:{path}", path, None, (change, lines),
                    f"{len(lines)} import statement(s) in {path}")
            for path, change, _, lines, _ in _import_files(bundle)
        ]

    def pass_condition(self, target: Target):
        change, lines = target.payload
        top = im.top_level(lines)
        problems = _on_authored_lines(
            im.group_order_problems(top, IMPORT_POLICY)
            + _module_order_problems(top)
            + _guarded_position_problems(lines),
            change,
        )
        if not problems:
            return Satisfied(f"{len(top)} top-level import(s) in the declared order")
        first = problems[0]
        return Violated(f"line {first.lineno}: {first.detail}")


@rule(id="DJANGO-C021", category=CATEGORY, ownership="touched", reads=("files",))
class PlainImportsBeforeFromImports:
    """Pre-condition: every Python file the agent added an import statement to.
    Pass condition: within each group, every `import x` line comes before every
    `from x import y` line."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        return [
            _target(f"importfirst:{path}", path, None, (change, lines),
                    f"{len(lines)} import statement(s) in {path}")
            for path, change, _, lines, _ in _import_files(bundle)
        ]

    def pass_condition(self, target: Target):
        change, lines = target.payload
        problems = _on_authored_lines(
            im.statement_order_problems(im.top_level(lines)), change)
        if not problems:
            return Satisfied("no plain import follows a from-import in its group")
        first = problems[0]
        return Violated(f"line {first.lineno}: {first.detail} (the from-import is on line "
                        f"{first.other_lineno})")


@rule(id="DJANGO-C023", category=CATEGORY, ownership="touched", reads=("files",))
class NamesOnOneImportLineAreSorted:
    """Pre-condition: every `from x import a, b` line the agent wrote that imports more
    than one name.
    Pass condition: the names are alphabetical, with the uppercase ones first.

    The two-band order -- uppercase-initial names, then lowercase, alphabetical inside
    each -- is `imports.name_sort_key`, and it is exactly what the sentence describes.
    Star imports are excluded: there is no list of names to order.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, _, _, _, authored in _import_files(bundle):
            for line in authored:
                if not line.is_from or line.has_star or len(line.names) < 2:
                    continue
                targets.append(_target(f"names:{path}:{line.lineno}", path, line.span(),
                                       line, _first_line(line.raw)))
        return targets

    def pass_condition(self, target: Target):
        line: im.ImportLine = target.payload
        if im.names_are_sorted(line.names):
            return Satisfied(f"{len(line.names)} name(s) in order")
        expected = ", ".join(sorted(line.names, key=im.name_sort_key))
        return Violated(f"names are {', '.join(line.names)}; expected {expected}")


# --- imports: form -------------------------------------------------------------------


@rule(id="DJANGO-C022", category=CATEGORY, ownership="touched", reads=("files",))
class RelativeImportDepth:
    """Pre-condition: every import statement the agent wrote.
    Pass condition: it is absolute, or reaches at most one package level up.

    The antecedent is the import, not the relative one: firing on `from ..` would grade
    only the violations and let a file full of absolute imports collect `not_applicable`
    rather than the pass it earned. One dot is what "single-dot relative imports locally"
    permits; two or more is what the sentence forbids outright.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, _, _, _, authored in _import_files(bundle):
            for line in authored:
                targets.append(_target(f"relative:{path}:{line.lineno}", path, line.span(),
                                       line, _first_line(line.raw)))
        return targets

    def pass_condition(self, target: Target):
        line: im.ImportLine = target.payload
        if line.dot_depth > MAX_RELATIVE_DEPTH:
            return Violated(f"{'.' * line.dot_depth}{line.module} reaches "
                            f"{line.dot_depth} levels up; use an absolute import")
        if line.is_relative:
            return Satisfied("single-dot relative import")
        return Satisfied("absolute import")


@rule(id="DJANGO-C024", category=CATEGORY, ownership="touched", reads=("files",))
class WrappedImportShape:
    """Pre-condition: every import statement the agent wrote that is long -- already
    wrapped, or over the line limit on one line.
    Pass condition: it is wrapped in parentheses, continued four columns in, with a
    trailing comma and the closing parenthesis on a line of its own.

    "Long" has to include the unwrapped case: an import the agent typed as one 120-column
    line is precisely a long import that was not wrapped, and a pre-condition that fired
    only on statements already spanning lines would grade nothing but the ones that got
    the general idea right.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, _, _, _, authored in _import_files(bundle):
            for line in authored:
                too_long = (not line.wrapping.is_wrapped
                            and len(_first_line(line.raw)) > CODE_LINE_LIMIT)
                if not (line.wrapping.is_wrapped or too_long):
                    continue
                targets.append(_target(f"wrap:{path}:{line.lineno}", path, line.span(),
                                       line, _first_line(line.raw)))
        return targets

    def pass_condition(self, target: Target):
        line: im.ImportLine = target.payload
        wrap = line.wrapping
        if not wrap.is_wrapped:
            return Violated(f"import is {len(_first_line(line.raw))} chars on one line; "
                            f"wrap it in parentheses")
        problems = im.wrapping_problems([line], indent=IMPORT_CONTINUATION_INDENT)
        if problems:
            first = problems[0]
            return Violated(f"line {first.lineno}: {first.detail}")
        if wrap.uses_parentheses and wrap.closing_indent is None:
            return Violated("the closing parenthesis is not on a line of its own")
        return Satisfied(f"wrapped across {wrap.end_lineno - wrap.lineno + 1} lines")


@rule(id="DJANGO-C025", category=CATEGORY, ownership="touched", reads=("files",))
class BlankLinesBelowImports:
    """Pre-condition: every boundary below a file's imports that the agent wrote at --
    the gap to the code that follows, and the gap above the first function or class.
    Pass condition: one blank line in the first, two in the second.

    Two targets rather than one, because the two gaps are different lines and an agent
    usually writes only one of them. Where the first thing after the imports *is* the
    first def or class the two gaps coincide, and the stricter count wins: two.

    The pre-condition asks who wrote the boundary, not who wrote the file. An agent that
    appends a function to the bottom of a module does not thereby become answerable for
    the blank line under an import block it never touched.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, module in _py_modules(bundle):
            if not module.ok:
                continue
            report = im.blank_line_report(module=module, path=path)
            if report is None or report.last_import_lineno is None:
                continue
            last, after = report.last_import_lineno, report.next_statement_lineno
            if after is not None and _authored(change, (last, after)):
                targets.append(_target(f"importgap:{path}:{last}", path, (last, after),
                                       ("code", report),
                                       f"{path}: imports end at line {last}"))
            definition = report.first_definition_lineno
            if (definition is not None and definition != after
                    and _authored(change, (max(1, definition - 3), definition))):
                targets.append(_target(f"defgap:{path}:{definition}", path,
                                       (definition, definition), ("definition", report),
                                       f"{path}: first {report.first_definition_kind} at "
                                       f"line {definition}"))
        return targets

    def pass_condition(self, target: Target):
        which, report = target.payload
        if which == "code":
            together = report.next_statement_lineno == report.first_definition_lineno
            want = 2 if together else 1
            what = "the first function or class" if together else "module-level code"
            got = report.blank_after_imports
            if got != want:
                return Violated(f"{got} blank line(s) between the imports and {what}, "
                                f"expected {want}")
            return Satisfied(f"{got} blank line(s) before {what}")
        got = report.blank_before_first_definition
        if got != 2:
            return Violated(f"{got} blank line(s) before the first "
                            f"{report.first_definition_kind}, expected 2")
        return Satisfied(f"2 blank lines before the first {report.first_definition_kind}")


# --- imports: what is imported --------------------------------------------------------


@rule(id="DJANGO-C026", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class DocumentedConvenienceImports:
    """Pre-condition: every `from django...` import the agent wrote.
    Pass condition: it names a documented path rather than the internal module the object
    happens to live in.

    Flagged heuristic, and it under-reports on purpose. Which paths Django documents lives
    in Django's documentation, not in its source, so no checker can derive the set; what
    is encoded here is the family the rule's own example belongs to -- `django.views`
    rather than `django.views.generic.base`, `django.db.models` rather than
    `django.db.models.fields` -- plus the general test that a path component beginning
    with an underscore is private by convention. An internal path outside that table
    passes, which is the safe direction: a false accusation costs more than a miss.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, _, _, _, authored in _import_files(bundle):
            for line in authored:
                if not line.is_from or line.is_relative:
                    continue
                if line.module.split(".")[0] not in DJANGO_PACKAGES:
                    continue
                targets.append(_target(f"convenience:{path}:{line.lineno}", path,
                                       line.span(), line, _first_line(line.raw)))
        return targets

    def pass_condition(self, target: Target):
        line: im.ImportLine = target.payload
        private = [part for part in line.module.split(".") if part.startswith("_")]
        if private:
            return Violated(f"{line.module} reaches into the private module "
                            f"{private[0]!r}; import from the documented path instead")
        if documented := _DJANGO_INTERNAL.get(line.module):
            return Violated(f"{line.module} is an internal module path; import "
                            f"{', '.join(line.names)} from {documented}")
        return Satisfied(f"from {line.module}")


@rule(id="DJANGO-C039", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class SettingsReadLazily:
    """Pre-condition: every read of a `settings` attribute the agent wrote in a module
    that imports settings from `django.conf`.
    Pass condition: it is evaluated when something calls it, not when the module is
    imported.

    Flagged heuristic on both halves. The antecedent is recognised by the name `settings`
    bound from `django.conf`, so a module that aliases it, or reaches it through
    `apps.get_app_config`, is invisible here. And "lazy indirection" is proxied by *where
    the read sits*: inside a function body or a lambda it is deferred, anywhere else --
    module level, a class body, a decorator argument, a default argument -- it runs at
    import time. A module-level read genuinely wrapped in some other lazy object is
    reported even so, because the wrapper's laziness is a fact about the callee.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, module in _py_modules(bundle):
            if not module.ok:
                continue
            lines = _import_lines(path, module)
            if not any(line.is_from and line.module == _SETTINGS_MODULE
                       and _SETTINGS_NAME in line.bindings for line in lines):
                continue
            deferred = _deferred_spans(module.tree)
            found: dict[tuple[int, int], str] = {}
            for node in ast.walk(module.tree):
                if not isinstance(node, ast.Attribute):
                    continue
                dotted = pa.dotted_name(node)
                if not dotted.startswith(f"{_SETTINGS_NAME}."):
                    continue
                if node.lineno not in change.authored_lines:
                    continue
                where = (node.lineno, node.col_offset)
                if len(dotted) > len(found.get(where, "")):
                    found[where] = dotted
            for (lineno, _), dotted in sorted(found.items()):
                at_import = not any(lo <= lineno <= hi for lo, hi in deferred)
                targets.append(_target(f"settings:{path}:{lineno}", path, (lineno, lineno),
                                       (dotted, at_import), dotted))
        return targets

    def pass_condition(self, target: Target):
        dotted, at_import = target.payload
        if at_import:
            return Violated(f"{dotted} is read while the module is being imported; defer "
                            f"it into a function or a lazy object")
        return Satisfied(f"{dotted} is read when the code around it runs")


@rule(id="DJANGO-C041", category=CATEGORY, ownership="touched", reads=("files",))
class UnusedImportsAreDeleted:
    """Pre-condition: every name bound by an import statement the agent wrote.
    Pass condition: something in the module uses it, or the import carries a `# NOQA`
    marking it as kept for backwards compatibility.

    Scoped to the agent's own import lines, which is narrower than the sentence. "Delete
    unused imports on edit" also covers an import that *became* unused because the agent
    removed its last caller, and that import sits on a line the agent never wrote --
    judging it would fail an agent for whitespace and imports it inherited (invariant 5).
    The narrower reading is the one that can be defended per line.

    `unused_names` deliberately under-reports: it ignores scope, so a name used anywhere
    in the file counts as used. A rule that accuses an author of dead code had better be
    right about it.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, module, _, authored in _import_files(bundle):
            unused = {(entry.lineno, entry.name): entry
                      for entry in im.unused_names(module=module, policy=IMPORT_POLICY,
                                                   path=path)}
            for line in authored:
                for index, binding in enumerate(line.bindings):
                    if line.names[index] == "*":
                        continue
                    entry = unused.get((line.lineno, binding))
                    targets.append(_target(
                        f"unused:{path}:{line.lineno}:{binding}", path, line.span(),
                        (binding, line, entry), _first_line(line.raw)))
        return targets

    def pass_condition(self, target: Target):
        binding, line, entry = target.payload
        if entry is None:
            return Satisfied(f"{binding} is used")
        if line.noqa:
            return Satisfied(f"{binding} is unused but kept for backwards compatibility, "
                             f"marked {line.noqa!r}")
        return Violated(f"{binding} (from {entry.origin}) is imported and never used, and "
                        f"carries no # NOQA")


# --- indentation ----------------------------------------------------------------------


def _logical_line_indents(source: str) -> Optional[dict[int, int]]:
    """(line number -> indent column) for each line that begins a logical line.

    Continuation lines are excluded, and that is the whole point: Python aligns them to an
    opening bracket, so judging them against a multiple of four would fail correctly
    formatted code. Lines inside a multi-line string produce no token and are excluded for
    the same reason. `None` when the file does not tokenise, which leaves the caller to
    fall back on the raw text.
    """
    tokens = _tokens(source)
    if tokens is None:
        return None
    out: dict[int, int] = {}
    at_start, depth = True, 0
    for token in tokens:
        if token.type in (tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER):
            continue
        if token.type == tokenize.NEWLINE:
            at_start = True
            continue
        if token.type == tokenize.NL:
            if depth == 0:
                at_start = True
            continue
        if at_start and depth == 0:
            out[token.start[0]] = token.start[1]
            at_start = False
        if token.type == tokenize.OP:
            if token.string in "([{":
                depth += 1
            elif token.string in ")]}":
                depth -= 1
    return out


@rule(id="DJANGO-C002", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class IndentWidth:
    """Pre-condition: every indented line the agent added to a Python or an HTML file.
    Pass condition: the indent is spaces -- a multiple of four in Python, of two in HTML.

    Flagged heuristic for the HTML half. Python has logical lines, so the Python side is
    exact: the indent judged is the column the statement starts at, and a continuation
    line aligned under an open bracket is never treated as a mis-indented statement. HTML
    has no such structure, so a wrapped attribute list and the body of a `<pre>` block are
    judged as though they were nested elements. A Python file that does not tokenise falls
    back to the raw added lines, which is where the same approximation applies to it.

    The corpus marks this rule `differential`, and it is the one row in the category that
    does. Nothing about an indent needs a test run to settle, so it is graded statically
    here; if `tests/test_check_tier.py` is ever extended to the Django pack, this is the
    rule its `differential`-not-graded-by-a-proxy invariant will name, and the answer is
    that the tier is wrong rather than the check.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, module in _py_modules(bundle):
            starts = _logical_line_indents(module.source) if module.source else None
            for lineno, text in change.added_lines:
                if not text.strip():
                    continue
                if starts is not None and lineno not in starts:
                    continue
                indent = text[: len(text) - len(text.lstrip())]
                if not indent:
                    continue
                targets.append(_target(f"indent:{path}:{lineno}", path, (lineno, lineno),
                                       (indent, PY_INDENT, "Python"), text))
        for path, change in _changed(bundle, TEMPLATE_SUFFIX):
            for lineno, text in change.added_lines:
                if not text.strip():
                    continue
                indent = text[: len(text) - len(text.lstrip())]
                if not indent:
                    continue
                targets.append(_target(f"indent:{path}:{lineno}", path, (lineno, lineno),
                                       (indent, HTML_INDENT, "HTML"), text))
        return targets

    def pass_condition(self, target: Target):
        indent, width, kind = target.payload
        if "\t" in indent:
            return Violated(f"{kind} line is indented with a tab, not spaces")
        if len(indent) % width:
            return Violated(f"{kind} line is indented {len(indent)} spaces, not a "
                            f"multiple of {width}")
        return Satisfied()


# --- templates ------------------------------------------------------------------------


@rule(id="DJANGO-C027", category=CATEGORY, ownership="touched", reads=("files",))
class ExtendsComesFirst:
    """Pre-condition: every `{% extends %}` tag the agent wrote in a template.
    Pass condition: nothing but comments and whitespace precedes it.

    The antecedent is the extends tag, not its position: a template that extends nothing
    has no obligation here, and firing on "the first tag in the file" would grade the
    position instead of the tag that has to occupy it.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, nodes in _templates(bundle):
            for node in tt.tags_named(nodes, "extends"):
                if not _wrote(change, node):
                    continue
                targets.append(_target(f"extends:{path}:{node.lineno}", path, node.span,
                                       (nodes, node), node.raw))
        return targets

    def pass_condition(self, target: Target):
        nodes, node = target.payload
        if tt.is_first_significant(nodes, node):
            return Satisfied("{% extends %} is the first thing in the template")
        first = tt.first_significant(nodes)
        return Violated(f"{{% extends %}} is on line {node.lineno}, after "
                        f"{_first_line(first.raw)[:40]!r} on line {first.lineno}")


@rule(id="DJANGO-C028", category=CATEGORY, ownership="touched", reads=("files",))
class VariableTagSpacing:
    """Pre-condition: every `{{ ... }}` variable tag the agent wrote.
    Pass condition: there is exactly one space inside each delimiter."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, nodes in _templates(bundle):
            for node in tt.variable_expressions(nodes):
                if not _wrote(change, node):
                    continue
                targets.append(_target(f"varspace:{path}:{node.lineno}:{node.col}", path,
                                       node.span, node, node.raw))
        return targets

    def pass_condition(self, target: Target):
        node: tt.TemplateNode = target.payload
        if node.has_single_inner_spacing:
            return Satisfied()
        leading, trailing = node.spacing
        return Violated(f"{node.raw[:50]!r} has {leading} space(s) after {{{{ and "
                        f"{trailing} before }}}}, expected 1 and 1")


@rule(id="DJANGO-C030", category=CATEGORY, ownership="touched", reads=("files",))
class BlockTagSpacing:
    """Pre-condition: every `{% ... %}` tag the agent wrote.
    Pass condition: there is exactly one space inside each delimiter."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, nodes in _templates(bundle):
            for node in tt.block_tags(nodes):
                if not _wrote(change, node):
                    continue
                targets.append(_target(f"tagspace:{path}:{node.lineno}:{node.col}", path,
                                       node.span, node, node.raw))
        return targets

    def pass_condition(self, target: Target):
        node: tt.TemplateNode = target.payload
        if node.has_single_inner_spacing:
            return Satisfied()
        leading, trailing = node.spacing
        return Violated(f"{node.raw[:50]!r} has {leading} space(s) after {{% and "
                        f"{trailing} before %}}, expected 1 and 1")


@rule(id="DJANGO-C029", category=CATEGORY, ownership="touched", reads=("files",))
class LoadLibrariesAreAlphabetical:
    """Pre-condition: every `{% load %}` tag the agent wrote that names more than one
    library.
    Pass condition: the names are in alphabetical order.

    `{% load x from lib %}` is excluded: its arguments are a tag name and a library, not a
    list of libraries, so ordering them alphabetically would be meaningless.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, nodes in _templates(bundle):
            for node in tt.tags_named(nodes, "load"):
                if not _wrote(change, node) or len(node.args) < 2:
                    continue
                if _LOAD_FROM in node.args:
                    continue
                targets.append(_target(f"load:{path}:{node.lineno}", path, node.span,
                                       node, node.raw))
        return targets

    def pass_condition(self, target: Target):
        node: tt.TemplateNode = target.payload
        if tt.is_alphabetical(node.args):
            return Satisfied(f"{len(node.args)} librar(ies) in order")
        expected = " ".join(sorted(node.args, key=lambda a: tt.unquote(a).lower()))
        return Violated(f"{{% load {' '.join(node.args)} %}} is not alphabetical; "
                        f"expected {{% load {expected} %}}")


@rule(id="DJANGO-C031", category=CATEGORY, ownership="touched", reads=("files",))
class EndblockNamesItsBlock:
    """Pre-condition: every `{% endblock %}` the agent wrote that is on a different line
    from its `{% block %}`.
    Pass condition: it repeats the block's name.

    The antecedent is the conditional's "whenever" clause -- the closer sitting on another
    line -- so a one-line `{% block t %}x{% endblock %}` is correctly outside the rule
    rather than a violation of it. A block the agent never closed is a template error, not
    this rule's business, and is skipped.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, nodes in _templates(bundle):
            for pair in tt.tag_pairs(nodes):
                if pair.name != "block" or not pair.is_closed or pair.same_line:
                    continue
                if not _wrote(change, pair.closer):
                    continue
                targets.append(_target(f"endblock:{path}:{pair.closer.lineno}", path,
                                       pair.span, pair, pair.closer.raw))
        return targets

    def pass_condition(self, target: Target):
        pair: tt.TagPair = target.payload
        if not pair.closer_repeats_name:
            return Violated(f"{{% endblock %}} on line {pair.closer.lineno} closes "
                            f"{{% block {pair.label} %}} on line {pair.opener.lineno} "
                            f"without naming it")
        if pair.label and not pair.names_agree:
            return Violated(f"{{% endblock {pair.closer.args[0]} %}} on line "
                            f"{pair.closer.lineno} names a different block from "
                            f"{{% block {pair.label} %}} on line {pair.opener.lineno}")
        return Satisfied(f"{{% endblock {pair.closer.args[0]} %}}")


@rule(id="DJANGO-C032", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class TokenSpacingInsideTags:
    """Pre-condition: every tag the agent wrote that holds more than one token.
    Pass condition: one space between tokens, and none on either side of `.` or `|`.

    Flagged heuristic for what the sentence leaves out. It names `.` and `|` as the two
    that stay tight and says "singly" about everything else, but `{{ value|date:"Y" }}`
    and `{% url 'v' pk=obj.pk %}` are written flush around `:` and `=` in every example
    Django publishes, and reading the sentence literally would fail both. So `:`, `=`,
    `,` and the brackets are placed by the syntax's own convention rather than by the
    rule's text, and that reading is the part that cannot be called exact.

    Tags broken across lines are skipped: the whitespace between their tokens is a line
    break, which this sentence says nothing about.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, nodes in _templates(bundle):
            for node in nodes:
                if node.is_text or node.is_comment or node.spans_lines:
                    continue
                if len(node.tokens) < 2 or not _wrote(change, node):
                    continue
                targets.append(_target(f"tokenspace:{path}:{node.lineno}:{node.col}", path,
                                       node.span, node, node.raw))
        return targets

    def pass_condition(self, target: Target):
        node: tt.TemplateNode = target.payload
        for left, right in zip(node.tokens, node.tokens[1:]):
            tight = (left.is_tight_operator or right.is_tight_operator
                     or left.text in _FLUSH_AFTER or right.text in _FLUSH_BEFORE)
            want = 0 if tight else 1
            if right.space_before == want:
                continue
            if tight:
                return Violated(f"{node.raw[:50]!r}: {right.space_before} space(s) "
                                f"between {left.text!r} and {right.text!r}, expected none")
            return Violated(f"{node.raw[:50]!r}: {right.space_before} space(s) between "
                            f"{left.text!r} and {right.text!r}, expected 1")
        return Satisfied(f"{len(node.tokens)} token(s) spaced singly")


@rule(id="DJANGO-C033", category=CATEGORY, ownership="touched", reads=("files",))
class TopLevelBlocksAreFlush:
    """Pre-condition: every top-level `{% block %}` the agent wrote in a template that
    extends another.
    Pass condition: neither the block tag nor its closer is indented.

    "Top-level" is a block no other block tag encloses, computed from the pairing rather
    than from the indentation the rule is about to judge. A closer that shares its line
    with content has no indentation of its own and only the opener is measured.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change, nodes in _templates(bundle):
            if _extends_tag(nodes) is None:
                continue
            pairs = tt.tag_pairs(nodes)
            for pair in pairs:
                if pair.name != "block":
                    continue
                if any(_contains(other, pair) for other in pairs):
                    continue
                if not (_wrote(change, pair.opener)
                        or (pair.closer is not None and _wrote(change, pair.closer))):
                    continue
                targets.append(_target(f"blockindent:{path}:{pair.opener.lineno}", path,
                                       pair.span, pair, pair.opener.raw))
        return targets

    def pass_condition(self, target: Target):
        pair: tt.TagPair = target.payload
        for node, what in ((pair.opener, "block"), (pair.closer, "endblock")):
            if node is None or not node.starts_line:
                continue
            if node.indent_width:
                return Violated(f"{{% {what} %}} on line {node.lineno} is indented "
                                f"{node.indent_width} column(s); a top-level block in an "
                                f"extending template is flush left")
        return Satisfied(f"{{% block {pair.label} %}} is flush left")

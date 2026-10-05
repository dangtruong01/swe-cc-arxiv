"""SymPy: Documentation and docstrings -- 40 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Four things shape this category.

**The antecedent is almost always "a docstring the agent owns".** Thirty of the forty rules
grade the form of a docstring, so the ownership mode carries most of the design. Formatting
rules take ``touched`` -- edit a docstring and you own its formatting -- while the three
rules that demand a *section exist* (C180, C183, C191) take ``created``, because demanding
an ``Examples`` block from an agent that merely brushed one line of existing prose would
score SymPy's authors rather than the agent (plan §4.3, invariant 5).

**Several rules must be read against the source text, not the parsed docstring.** C169 and
C216 are about backslashes and LaTeX, and a non-raw docstring has already had its escapes
interpreted by the time ``ast`` hands it over: ``\\frac`` arrives as a formfeed followed by
``rac``. Detecting the defect therefore means reading the bytes between the quotes, which
``_source_text`` does. That the escape was mangled *is* the violation the rule exists to
catch.

**Three rules are about what the agent did, not what it wrote.** C146, C175 and C190 demand
a documentation build or a doctest run. They fire on the documentation change -- the
antecedent -- and grade the command log, exactly as C078 does in ``tests.py``. An agent that
changes a docstring and never builds the docs fails them; one that changes no documentation
is never asked.

**This category is close to unreachable on a bug-fix benchmark, and that was measured
before it was written**. Across the 22 stored runs: zero
touched a docstring line, zero created a docstring, zero own a doctest example, zero touched
an RST or ``doc/`` file, and zero ran ``make html`` or ``bin/doctest``. The rules are
implemented because they are 40 of the 142 and the corpus is the specification -- not because
any number is expected to move. C150 goes further and is structurally unreachable: its
antecedent is a *failing PDF documentation build*, which nothing in an agent run produces.
"""

from __future__ import annotations

import ast
import builtins
import re
from dataclasses import dataclass
from typing import Iterator, Optional

from compliance.core.models import (
    EvidenceBundle,
    Satisfied,
    Target,
    Violated,
)
from compliance.core.registry import rule
from compliance.extractors import docstrings as ds
from compliance.extractors import python_ast as pa
from compliance.extractors import rst
from compliance.rules.sympy.tests import (
    Unreadable,
    _modules,
    _owns,
    _ran,
    _target,
    _unreadable,
    _unreadable_target,
)

CATEGORY = "Documentation and docstrings"

# --- SymPy vocabulary ---------------------------------------------------------------

# Where narrative documentation lives. Markdown is permitted here and nowhere else (C213),
# and the style guide's prose rules (C228) are scoped to it.
NARRATIVE_DOC_ROOTS = ("doc/",)
LIBRARY_ROOT = "sympy/"

# The order SymPy's docstring guide lists, verified against the live guide (22 Aug 2026).
# C176 orders only these; a docstring may also carry Returns or Notes and the rule says
# nothing about where those go, so they are ignored rather than assumed.
#
# **This is not numpydoc's order.** numpydoc puts Parameters before See Also and Examples
# last; SymPy puts Examples third, right after the explanation. Deviating is the project's
# prerogative and the corpus is the specification -- which is exactly why the vocabulary
# lives here and not in `extractors/`.
SECTION_ORDER = ("Explanation", "Examples", "Parameters", "See Also", "References")

# SymPy's supported section names: numpydoc's vocabulary plus the two names SymPy uses in
# place of numpydoc's. `Explanation` is SymPy's name for numpydoc's `Extended Summary`, and
# `Summary` names the leading prose the guide requires. Passed to the extractor explicitly
# rather than relying on its default, so a change to the shared default cannot silently
# change what SymPy accepts.
SYMPY_SECTION_NAMES = ("Summary", "Explanation")
SUPPORTED_SECTIONS = SYMPY_SECTION_NAMES + tuple(
    s for s in ds.NUMPYDOC_SECTIONS if s != "Extended Summary"
)

# Spellings a section heading is commonly given instead of the published one. This is what
# lets C177 see a wrong name at all: `find_headings` only recognises headings whose text is
# in the vocabulary it is given, so a misspelling has to be named to be caught. The list is
# necessarily partial, which narrows C177's pre-condition rather than its grading.
SECTION_VARIANTS = (
    "Example", "Parameter", "Arguments", "Argument", "Args", "Return", "Result", "Results",
    "Reference", "See also", "Seealso", "Notes:", "Raise", "Attribute", "Method",
    "Usage", "Examples:", "Parameters:", "Explanation:",
)

# Names SymPy exports from the top level, so `:obj:`~.name`` is the right form for them
# (C206) and the abbreviation is wrong for anything else (C207). Curated and partial --
# which is why both rules are flagged heuristic.
TOP_LEVEL_NAMES = frozenset("""
Symbol Symbols symbols Dummy Wild Integer Rational Float Number Add Mul Pow Expr Basic
Function Lambda Derivative Integral Sum Product Limit Matrix ImmutableMatrix zeros ones eye
diag simplify expand factor collect cancel apart together nsimplify radsimp trigsimp powsimp
solve solveset nsolve dsolve linsolve nonlinsolve roots real_roots RootOf sqrt exp log sin
cos tan cot sec csc asin acos atan atan2 sinh cosh tanh gamma beta zeta erf factorial binomial
Abs sign floor ceiling Min Max Piecewise And Or Not Xor Implies Eq Ne Lt Le Gt Ge S oo zoo
nan pi E I diff integrate limit series subs sympify latex pprint pretty srepr N evalf lambdify
Poly div gcd lcm degree LC Interval Union Intersection Complement FiniteSet EmptySet Set
Tuple Dict Order Rel Point Line Segment Ray Circle Ellipse Polygon Triangle Plane
""".split())

# Objects that cannot be cross-referenced into SymPy's own documentation, so they take code
# markup rather than a role (C208).
EXTERNAL_MODULES = frozenset("""
numpy scipy matplotlib mpmath gmpy gmpy2 sympy_bot pytest sphinx cython llvmlite
theano aesara sage symengine IPython pandas
""".split())

BUILTIN_NAMES = frozenset(dir(builtins))

# Base classes that make a class a mathematical function in SymPy's sense (C203).
MATH_FUNCTION_BASES = frozenset({
    "Function", "AppliedUndef", "TrigonometricFunction", "HyperbolicFunction",
    "InverseTrigonometricFunction", "InverseHyperbolicFunction", "OrthogonalPolynomial",
    "CombinatorialFunction", "SingleValuedFunction",
})

EVAL_METHOD = "eval"
DOC_BUILD_DIR = "doc"

SUMMARY_TERMINATOR = "."
DOCTEST_LINE_LIMIT = 80

# British spellings the American-spelling rule flags (C228). A word list is a proxy for a
# spelling standard, never the standard itself -- hence heuristic.
BRITISH_SPELLINGS = frozenset("""
behaviour colour flavour honour labour neighbour favour rumour endeavour
analyse catalyse paralyse normalise normalised normalising generalise generalised
initialise initialised initialising specialise specialised organise organised
recognise recognised realise realised minimise minimised maximise maximised
optimise optimised summarise summarised utilise utilised visualise visualised
centre centres fibre fibres litre litres metre metres theatre
defence offence licence pretence
travelling travelled cancelled cancelling labelled labelling modelling modelled
signalling signalled marvellous
grey aluminium programme sceptical judgement acknowledgement
""".split())

GENDERED_PRONOUNS = ("he", "she", "him", "her", "his", "hers", "himself", "herself")

_MAKE_HTML = re.compile(r"\bmake\s+html\b")
_CD_DOC = re.compile(r"\bcd\s+doc\b")
_HTMLDOC_IMAGE = re.compile(r"\bsympy_htmldoc\b")
_BIN_DOCTEST = re.compile(r"\bbin/doctest\b")
_PDF_BUILD = re.compile(r"\bmake\s+(latexpdf|pdf)\b")
# What Sphinx and the doctest runner print when the run is not clean. Positive detection of
# failure, rather than a search for success, which unrelated output produces constantly.
_SPHINX_FAILED = re.compile(
    r"^(WARNING|ERROR|SEVERE):|Sphinx error|build failed|Error: |make: \*\*\*", re.M)
_DOCTEST_FAILED = re.compile(
    r"DO \*NOT\* COMMIT|^\*+ *File .*, line \d+|Failed example:|^FAILED|=+ (FAILURES|ERRORS) =+", re.M)

_STAR_IMPORT = re.compile(r"^\s*from\s+sympy(\.\S+)?\s+import\s+\*", re.M)
_LATEX = re.compile(
    r"\\(frac|sqrt|int|sum|prod|left|right|begin|end|cdot|times|alpha|beta|gamma|delta|"
    r"theta|lambda|mu|pi|sigma|omega|infty|partial|nabla|mathrm|mathbb|operatorname|"
    r"text|log|exp|sin|cos|tan)\b|\$\$?[^$]+\$\$?|:math:")
# A backslash Python has already interpreted, which is what a missing `r` prefix produces.
_MANGLED_ESCAPE = re.compile(r"[\x07\x08\x0c\x0b\x1b]")
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DOTTED = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+$")
_PARAM_SEP = re.compile(r"^(?P<name>[^:]*?)(?P<sep>\s*:\s*)(?P<type>.*)$")
_MD_LINK = re.compile(r"\[[^\]]+\]\([^)]+\)")
_CITATION_NUMBER = re.compile(r"^\d+$")
_PROMPT = re.compile(r"^\s*(>>>|\.\.\.)( |$)")


# --- shared plumbing ----------------------------------------------------------------


@dataclass(frozen=True)
class OwnedDoc:
    """One docstring the agent owns, parsed into the structure the rules judge."""

    path: str
    module: pa.PyModule
    docstring: pa.Docstring
    doc: ds.Doc
    quote_lineno: int
    source_text: str
    """The docstring body exactly as written between the quotes.

    Not ``docstring.text``: by the time ``ast`` produces that, a non-raw docstring has had
    its escapes interpreted, so the very defect C169 and C216 exist to catch has been
    silently repaired. The bytes are the evidence.
    """

    @property
    def quote(self) -> str:
        return self.doc.quote

    @property
    def is_raw(self) -> bool:
        return self.quote.lower().startswith("r")

    @property
    def span(self) -> tuple[int, int]:
        return self.docstring.span()

    def lines(self) -> tuple[tuple[int, str], ...]:
        return self.docstring.lines()

    def function(self) -> Optional[pa.FunctionDef]:
        """The function this docstring documents, if it documents one."""
        if self.docstring.kind != "function":
            return None
        return next((f for f in self.module.functions
                     if f.qualname == self.docstring.owner), None)


def _quote_at(module: pa.PyModule, docstring: pa.Docstring) -> tuple[int, str]:
    """(line number, quote characters) of the docstring's opening delimiter.

    ``Docstring.lineno`` is the first *cleaned* line, which is the quote line only when
    text follows the quotes on the same line -- so it has to be resolved backwards, bounded
    by the definition the docstring belongs to.
    """
    lower = 1 if docstring.kind == "module" else docstring.def_span[0]
    for lineno in range(docstring.lineno, lower - 1, -1):
        quote = ds.opening_quote(module.source, lineno)
        # A one-character quote here is a string on the `def` line, not the docstring.
        if quote and len(quote.lstrip("rubRUB")) == 3:
            return lineno, quote
    return docstring.lineno, ds.opening_quote(module.source, docstring.lineno)


def _source_text(module: pa.PyModule, docstring: pa.Docstring, quote_lineno: int,
                 quote: str) -> str:
    """The docstring body as written, escapes uninterpreted."""
    if not quote:
        return docstring.raw
    delimiter = quote.lstrip("rubRUB")
    lines = module.source.split("\n")
    if not 1 <= quote_lineno <= len(lines):
        return docstring.raw
    first = lines[quote_lineno - 1]
    column = first.find(quote)
    if column == -1:
        return docstring.raw
    rest = "\n".join([first[column + len(quote):]] + lines[quote_lineno:])
    end = rest.find(delimiter)
    return rest[:end] if end != -1 else rest


def _docstrings(
    bundle: EvidenceBundle, mode: str = "touched"
) -> Iterator[tuple[str, pa.PyModule, Optional[OwnedDoc]]]:
    """Every docstring the agent owns under ``mode``, parsed.

    Yields ``None`` for a file that would not parse, so the caller turns it into an
    ``Unreadable`` target rather than reporting that the agent wrote no docstrings.
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
                owned = _owns(bundle, path, docstring.span(), mode)
            if not owned:
                continue
            quote_lineno, quote = _quote_at(module, docstring)
            yield path, module, OwnedDoc(
                path=path,
                module=module,
                docstring=docstring,
                doc=ds.parse(docstring.lines(), known=SUPPORTED_SECTIONS, quote=quote),
                quote_lineno=quote_lineno,
                source_text=_source_text(module, docstring, quote_lineno, quote),
            )


def _doc_targets(
    bundle: EvidenceBundle,
    prefix: str,
    *,
    mode: str = "touched",
    where=None,
    kinds: tuple[str, ...] = ("function", "class", "module"),
) -> list[Target]:
    """Targets over owned docstrings, optionally narrowed by ``where``.

    ``where`` narrows on the rule's antecedent -- *this docstring contains a backslash*,
    *this docstring has a References section* -- never on the artefact the rule demands.
    """
    targets: list[Target] = []
    for path, module, owned in _docstrings(bundle, mode):
        if owned is None:
            targets.append(_unreadable_target(path, module))
            continue
        if owned.docstring.kind not in kinds:
            continue
        if where is not None and not where(owned):
            continue
        targets.append(_target(
            f"{prefix}:{path}:{owned.span[0]}", path, owned.span, owned,
            f"{owned.docstring.kind} docstring of {owned.docstring.owner}",
        ))
    return targets


# --- section body parsing ------------------------------------------------------------


@dataclass(frozen=True)
class Entry:
    """One item of a definition-list section: Parameters, See Also, References.

    ``continuation`` holds the lines indented under the entry. A continuation line that was
    *not* indented is not here -- it parses as a new entry, which is precisely how C194
    sees the defect it is about.
    """

    lineno: int
    text: str
    continuation: tuple[tuple[int, str], ...] = ()

    def described(self) -> str:
        return " ".join([self.text] + [t.strip() for _, t in self.continuation])


def _entries(section: ds.Section) -> list[Entry]:
    """Split a section body into entries at its base indent."""
    body = [(n, t) for n, t in section.body if t.strip()]
    if not body:
        return []
    base = min(len(t) - len(t.lstrip()) for _, t in body)
    entries: list[Entry] = []
    continuation: list[tuple[int, str]] = []
    for lineno, text in body:
        indent = len(text) - len(text.lstrip())
        if indent <= base or not entries:
            if entries:
                entries[-1] = Entry(entries[-1].lineno, entries[-1].text,
                                    tuple(continuation))
                continuation = []
            entries.append(Entry(lineno, text.strip()))
        else:
            continuation.append((lineno, text))
    if entries and continuation:
        entries[-1] = Entry(entries[-1].lineno, entries[-1].text, tuple(continuation))
    return entries


def _is_reference(text: str) -> bool:
    """Whether a See Also line names an object rather than continuing a description.

    It has to recognise the *wrong* spellings too. Written to accept only bare names, it
    could not see `:class:`Point`` -- the construct C196 exists to catch -- so the entry
    parsed as prose, no target was built, and the rule silently judged nothing. An
    over-narrow pre-condition raises nothing and produces no odd verdict (A9).
    """
    head = re.split(r"\s+:\s+", text.strip(), maxsplit=1)[0].strip()
    head = re.sub(r"^:[a-zA-Z:+-]+:", "", head).strip().strip("`~ ")
    head = head.split(",")[0].strip()
    if not head:
        return False
    if head.startswith(("http://", "https://")):
        return True
    return bool(_IDENTIFIER.match(head) or _DOTTED.match(head))


def _section_examples(owned: OwnedDoc, section: ds.Section) -> list[pa.DoctestExample]:
    if not section.body:
        return []
    lo = section.body[0][0]
    hi = section.body[-1][0]
    return [e for e in owned.docstring.examples if lo <= e.lineno <= hi]


def _summary_paragraph(doc: ds.Doc) -> list[tuple[int, str]]:
    """The first paragraph of the summary.

    ``Doc.summary`` is everything before the first heading, which in a docstring with no
    ``Explanation`` heading also swallows the extended description. Reading that as the
    summary would fail C181 on every correctly written docstring, so the summary is the
    first paragraph and nothing more.
    """
    out: list[tuple[int, str]] = []
    for lineno, text in doc.summary:
        if not text.strip():
            break
        out.append((lineno, text))
    return out


# --- documentation files (narrative, and the contribution as a whole) ------------------


def _is_narrative(path: str) -> bool:
    return path.startswith(NARRATIVE_DOC_ROOTS)


def _doc_file_lines(bundle: EvidenceBundle, path: str) -> tuple[tuple[int, str], ...]:
    """(line number, text) for a non-Python file, reconstructed where possible.

    Falls back to the lines the agent added, which need no repository cache -- the rules
    over these files judge authored lines anyway (invariant 5).
    """
    change = bundle.files[path]
    if change.head_text is not None:
        return tuple(enumerate(change.head_text.split("\n"), 1))
    return change.added_lines


def _authored(bundle: EvidenceBundle, path: str,
              lines: tuple[tuple[int, str], ...]) -> tuple[tuple[int, str], ...]:
    change = bundle.files[path]
    if change.is_new:
        return lines
    return tuple((n, t) for n, t in lines if n in change.authored_lines)


def _doc_files(bundle: EvidenceBundle, *, suffixes: tuple[str, ...],
               narrative: Optional[bool] = None) -> Iterator[tuple[str, tuple[tuple[int, str], ...]]]:
    for path in sorted(bundle.files):
        if not path.endswith(suffixes):
            continue
        if narrative is not None and _is_narrative(path) is not narrative:
            continue
        change = bundle.files[path]
        if not (change.modified_lines or change.is_new):
            continue
        yield path, _doc_file_lines(bundle, path)


def _changed_documentation(bundle: EvidenceBundle) -> list[str]:
    """What in this contribution counts as a documentation change.

    The antecedent C146, C175 and C190 share. A docstring the agent edited, or a narrative
    documentation file it touched -- never the build command itself, which is the artefact
    those rules demand.
    """
    changed = [path for path, _ in _doc_files(bundle, suffixes=(".rst", ".md", ".rest"))]
    for path, _, owned in _docstrings(bundle, "touched"):
        if owned is not None and path not in changed:
            changed.append(path)
    return sorted(changed)


# --- docstring formatting -------------------------------------------------------------


@rule(id="SYMPY-C168", category=CATEGORY, ownership="touched", reads=("files",))
class TripleDoubleQuotes:
    """Pre-condition: every docstring the agent wrote or edited.
    Pass condition: it is opened with triple double quotes."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _doc_targets(b, "quote")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned: OwnedDoc = t.payload
        delimiter = owned.quote.lstrip("rubRUB")
        if not owned.quote:
            return Satisfied()  # the quote could not be located; nothing to accuse
        if delimiter != '"""':
            return Violated(f"docstring of {owned.docstring.owner} is opened with "
                            f"{delimiter or owned.quote!r}, not triple double quotes")
        return Satisfied()


@rule(id="SYMPY-C169", category=CATEGORY, ownership="touched", reads=("files",))
class RawWhenBackslash:
    """Pre-condition: every docstring the agent owns whose source contains a backslash.
    Pass condition: it is written as a raw string.

    Read from the source bytes, not the parsed value: without the `r` prefix Python has
    already turned the backslash into whatever it escaped, so the parsed text no longer
    contains one. That silent substitution is the defect.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _doc_targets(b, "backslash", where=_has_backslash)

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned: OwnedDoc = t.payload
        if owned.is_raw:
            return Satisfied()
        return Violated(f"docstring of {owned.docstring.owner} contains a backslash but is "
                        f"not a raw string")


def _has_backslash(owned: OwnedDoc) -> bool:
    return "\\" in owned.source_text or bool(_MANGLED_ESCAPE.search(owned.docstring.text))


@rule(id="SYMPY-C170", category=CATEGORY, ownership="touched", reads=("files",))
class BlankLineBeforeClosingQuotes:
    """Pre-condition: every multi-line docstring the agent owns.
    Pass condition: the line immediately before its closing quotes is blank.

    Single-line docstrings are excluded: the guidance is about the layout of a docstring
    whose closing quotes sit on their own line, and `\"\"\"Return x.\"\"\"` has none.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _doc_targets(b, "closing", where=lambda o: "\n" in o.source_text)

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned: OwnedDoc = t.payload
        lines = owned.source_text.split("\n")
        if len(lines) >= 2 and not lines[-2].strip() and not lines[-1].strip():
            return Satisfied()
        return Violated(f"docstring of {owned.docstring.owner} has no blank line before "
                        f"its closing quotes")


@rule(id="SYMPY-C172", category=CATEGORY, ownership="touched", reads=("files",))
class ClassDocstringUnderDefinition:
    """Pre-condition: every class docstring the agent owns.
    Pass condition: it opens on the line following the class statement, with no blank
    line between them."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _doc_targets(b, "classdoc", kinds=("class",))

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned: OwnedDoc = t.payload
        lines = owned.module.source.split("\n")
        between = lines[owned.docstring.def_span[0]: owned.quote_lineno - 1]
        if blank := [n for n, text in enumerate(between) if not text.strip()]:
            return Violated(f"class docstring of {owned.docstring.owner} is separated from "
                            f"the class definition by {len(blank)} blank line(s)")
        return Satisfied()


@rule(id="SYMPY-C173", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class ExampleCodeIsADoctest:
    """Pre-condition: every `::` literal block in a docstring the agent owns whose body
    reads as Python.
    Pass condition: none -- example Python belongs in a doctest, so a literal block
    holding it is the violation.

    "Reads as Python" is decided lexically from the block's own text, which is why this is
    a heuristic: a literal block of shell or output that happens to contain an equals sign
    would be mistaken for one.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, module, owned in _docstrings(b, "touched"):
            if owned is None:
                targets.append(_unreadable_target(path, module))
                continue
            for lineno, block in _literal_blocks(owned):
                if _looks_like_python(block):
                    targets.append(_target(
                        f"codeblock:{path}:{lineno}", path, (lineno, lineno), block,
                        block[0][1].strip() if block else ""))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        first = t.payload[0][1].strip() if t.payload else ""
        return Violated(f"Python example is in a `::` literal block, not a doctest: {first[:60]!r}")


def _literal_blocks(owned: OwnedDoc) -> list[tuple[int, list[tuple[int, str]]]]:
    """`::` blocks: the opening line number, and the indented lines beneath it."""
    lines = list(owned.lines())
    blocks: list[tuple[int, list[tuple[int, str]]]] = []
    for index, (lineno, text) in enumerate(lines):
        if not rst.opens_code_block(text):
            continue
        indent = len(text) - len(text.lstrip())
        body: list[tuple[int, str]] = []
        for next_lineno, next_text in lines[index + 1:]:
            if not next_text.strip():
                if body:
                    body.append((next_lineno, next_text))
                continue
            if len(next_text) - len(next_text.lstrip()) <= indent:
                break
            body.append((next_lineno, next_text))
        if body:
            blocks.append((lineno, body))
    return blocks


def _looks_like_python(block: list[tuple[int, str]]) -> bool:
    text = "\n".join(t for _, t in block)
    if ">>>" in text:
        return False
    try:
        ast.parse(_dedent(text))
    except SyntaxError:
        return False
    return bool(text.strip())


def _dedent(text: str) -> str:
    lines = [line for line in text.split("\n") if line.strip()]
    if not lines:
        return text
    margin = min(len(line) - len(line.lstrip()) for line in lines)
    return "\n".join(line[margin:] for line in text.split("\n"))


@rule(id="SYMPY-C216", category=CATEGORY, ownership="touched", reads=("files",))
class RawWhenLatex:
    """Pre-condition: every docstring the agent owns whose source contains LaTeX.
    Pass condition: it is written as a raw string."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _doc_targets(b, "latex", where=lambda o: bool(_LATEX.search(o.source_text)))

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned: OwnedDoc = t.payload
        if owned.is_raw:
            return Satisfied()
        found = _LATEX.search(owned.source_text)
        return Violated(f"docstring of {owned.docstring.owner} contains LaTeX "
                        f"({found.group(0)[:20]!r}) but is not a raw string")


@rule(id="SYMPY-C214", category=CATEGORY, ownership="touched", reads=("files",))
class DocstringsUseRst:
    """Pre-condition: every docstring the agent wrote or edited.
    Pass condition: it carries no Markdown-only construct."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _doc_targets(b, "rstsyntax")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned: OwnedDoc = t.payload
        if found := rst.markdown_constructs(owned.lines()):
            lineno, what = found[0]
            return Violated(f"docstring of {owned.docstring.owner} uses Markdown, not RST: "
                            f"{what} at line {lineno}")
        return Satisfied()


# --- sections: which, named how, in what order ----------------------------------------


@rule(id="SYMPY-C176", category=CATEGORY, ownership="touched", reads=("files",))
class SectionOrder:
    """Pre-condition: every docstring the agent owns carrying at least two of the sections
    the guide orders.
    Pass condition: those sections appear in the published order.

    Only the sections the rule enumerates are ordered. A docstring may also carry Returns
    or Notes, and the rule says nothing about where those go, so they are ignored rather
    than assumed.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _doc_targets(b, "order", where=lambda o: len(_ordered_sections(o)) >= 2)

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned: OwnedDoc = t.payload
        present = _ordered_sections(owned)
        expected = [name for name in SECTION_ORDER if name in present]
        if present == expected:
            return Satisfied()
        return Violated(f"sections of {owned.docstring.owner} are ordered "
                        f"{' -> '.join(present)}, expected {' -> '.join(expected)}")


def _ordered_sections(owned: OwnedDoc) -> list[str]:
    canonical = {name.lower(): name for name in SECTION_ORDER}
    return [canonical[s.name.lower()] for s in owned.doc.sections
            if s.name.lower() in canonical]


@rule(id="SYMPY-C177", category=CATEGORY, ownership="touched", reads=("files",))
class ExactSectionNames:
    """Pre-condition: every section heading the agent wrote, recognised by the published
    name or by a common variant of one.
    Pass condition: it is spelled exactly as the published name, plural `Examples`
    included."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, module, owned in _docstrings(b, "touched"):
            if owned is None:
                targets.append(_unreadable_target(path, module))
                continue
            vocabulary = tuple(SUPPORTED_SECTIONS) + SECTION_VARIANTS
            for heading in ds.find_headings(owned.lines(), known=vocabulary):
                targets.append(_target(
                    f"heading:{path}:{heading.lineno}", path,
                    (heading.lineno, heading.underline_lineno), heading, heading.name))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        heading: ds.Heading = t.payload
        if heading.name in SUPPORTED_SECTIONS:
            return Satisfied()
        return Violated(f"section heading {heading.name!r} is not a supported section name")


@rule(id="SYMPY-C178", category=CATEGORY, ownership="touched", reads=("files",))
class HeadingUnderlineLength:
    """Pre-condition: every docstring section heading the agent wrote.
    Pass condition: its underline is equals signs, exactly as many as the heading has
    characters."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, module, owned in _docstrings(b, "touched"):
            if owned is None:
                targets.append(_unreadable_target(path, module))
                continue
            for heading in owned.doc.headings:
                targets.append(_target(
                    f"underline:{path}:{heading.lineno}", path,
                    (heading.lineno, heading.underline_lineno), heading, heading.name))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        heading: ds.Heading = t.payload
        wanted = len(heading.name)
        if heading.underline_char != "=":
            return Violated(f"heading {heading.name!r} is underlined with "
                            f"{heading.underline_char!r}, not equals signs")
        if heading.underline_length != wanted:
            return Violated(f"heading {heading.name!r} has {wanted} characters but "
                            f"{heading.underline_length} equals signs")
        return Satisfied()


@rule(id="SYMPY-C180", category=CATEGORY, ownership="created", reads=("files",))
class SummaryRequired:
    """Pre-condition: every function or class docstring the agent created.
    Pass condition: it opens with a summary, before any section heading.

    `created`, not `touched`: a docstring the agent merely edited a line of already had
    whatever summary it has, and demanding one would score its original author.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _doc_targets(b, "summary", mode="created", kinds=("function", "class"))

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned: OwnedDoc = t.payload
        if _summary_paragraph(owned.doc):
            return Satisfied()
        return Violated(f"docstring of {owned.docstring.owner} begins with no summary")


@rule(id="SYMPY-C181", category=CATEGORY, ownership="touched", reads=("files",))
class SummaryIsOneSentence:
    """Pre-condition: every docstring the agent owns that has a summary.
    Pass condition: the summary occupies one line and ends with a period."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _doc_targets(b, "summaryform", where=lambda o: bool(_summary_paragraph(o.doc)))

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned: OwnedDoc = t.payload
        summary = _summary_paragraph(owned.doc)
        text = " ".join(s.strip() for _, s in summary)
        if len(summary) > 1:
            return Violated(f"summary of {owned.docstring.owner} spans {len(summary)} "
                            f"lines: {text[:60]!r}")
        if not text.endswith(SUMMARY_TERMINATOR):
            return Violated(f"summary of {owned.docstring.owner} does not end with a "
                            f"period: {text[:60]!r}")
        return Satisfied()


@rule(id="SYMPY-C183", category=CATEGORY, ownership="created", reads=("files",))
class ExamplesSectionRequired:
    """Pre-condition: every function or class docstring the agent created.
    Pass condition: it carries an `Examples` section.

    Plan §4.2 names this rule as the worked case for `created` ownership: an `Examples`
    block is not demanded of a docstring the agent merely brushed. Module docstrings are
    out of scope -- the guide's Examples section governs the documented object.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _doc_targets(b, "examples", mode="created", kinds=("function", "class"))

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned: OwnedDoc = t.payload
        if owned.doc.has("Examples"):
            return Satisfied()
        return Violated(f"docstring of {owned.docstring.owner} has no Examples section")


@rule(id="SYMPY-C191", category=CATEGORY, ownership="created", reads=("files",))
class ParametersSectionRequired:
    """Pre-condition: every function docstring the agent created whose signature takes
    parameters other than `self` or `cls`.
    Pass condition: it carries a `Parameters` section."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _doc_targets(b, "paramsection", mode="created", kinds=("function",),
                            where=lambda o: bool(_parameter_names(o)))

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned: OwnedDoc = t.payload
        if owned.doc.has("Parameters"):
            return Satisfied()
        return Violated(f"{owned.docstring.owner} documents "
                        f"{len(_parameter_names(owned))} parameter(s) with no Parameters "
                        f"section")


def _parameter_names(owned: OwnedDoc) -> list[str]:
    """The documented signature's parameters, `self`/`cls` excluded."""
    function = owned.function()
    if function is None or function.node is None:
        return []
    args = function.node.args
    names = [a.arg for a in list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs)]
    if args.vararg:
        names.append(args.vararg.arg)
    if args.kwarg:
        names.append(args.kwarg.arg)
    return [n for n in names if n not in ("self", "cls")]


# --- the Examples section, and the doctests in it --------------------------------------


def _owned_examples(
    bundle: EvidenceBundle,
) -> Iterator[tuple[str, pa.PyModule, OwnedDoc, pa.DoctestExample]]:
    """Doctest examples whose own lines the agent's edit reaches.

    Narrower than the docstring that holds them: a docstring the agent touched is full of
    examples it did not write, and none of those are its to be judged on (invariant 5).
    """
    for path, module, owned in _docstrings(bundle, "touched"):
        if owned is None:
            yield path, module, None, None
            continue
        for example in owned.docstring.examples:
            if _owns(bundle, path, example.span(), "touched"):
                yield path, module, owned, example


@rule(id="SYMPY-C018", category=CATEGORY, ownership="touched", reads=("files",))
class DoctestNoStarImport:
    """Pre-condition: every doctest example the agent wrote or edited.
    Pass condition: it does not import from SymPy with a star.

    Only the prohibition is checked. The rule's other half -- that every used name be
    imported explicitly -- needs name resolution over the whole example, which is C113's
    business in `tests.py`, not a second implementation here.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, module, owned, example in _owned_examples(b):
            if owned is None:
                targets.append(_unreadable_target(path, module))
                continue
            targets.append(_target(f"starimport:{path}:{example.lineno}", path,
                                   example.span(), example, example.source.strip()))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        example: pa.DoctestExample = t.payload
        if _STAR_IMPORT.search(example.source):
            return Violated(f"doctest in {example.owner} uses a star import: "
                            f"{example.source.strip()[:60]!r}")
        return Satisfied()


@rule(id="SYMPY-C184", category=CATEGORY, ownership="touched", reads=("files",))
class BlankLineBeforeFirstDoctest:
    """Pre-condition: every Examples section the agent owns that contains a doctest.
    Pass condition: a blank line separates the section heading from its first doctest."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _examples_section_targets(b, "firstdoctest",
                                         where=lambda o, s: bool(_section_examples(o, s)))

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned, section = t.payload
        first = next((n for n, text in section.body if _PROMPT.match(text)), None)
        if first is None:
            return Satisfied()
        before = [text for n, text in section.body if n < first]
        if before and not before[-1].strip():
            return Satisfied()
        return Violated(f"Examples section of {owned.docstring.owner} has no blank line "
                        f"before its first doctest")


def _examples_section_targets(b: EvidenceBundle, prefix: str, *, where=None) -> list[Target]:
    targets: list[Target] = []
    for path, module, owned in _docstrings(b, "touched"):
        if owned is None:
            targets.append(_unreadable_target(path, module))
            continue
        section = owned.doc.section("Examples")
        if section is None or (where is not None and not where(owned, section)):
            continue
        targets.append(_target(f"{prefix}:{path}:{section.heading.lineno}", path,
                               owned.span, (owned, section),
                               f"Examples of {owned.docstring.owner}"))
    return targets


@rule(id="SYMPY-C185", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class ExamplesSeparatedByBlankLines:
    """Pre-condition: every point in an Examples section the agent owns where a new
    example begins -- a fresh statement after a previous one produced output.
    Pass condition: a blank line separates it from the example before it.

    Heuristic: a run of statements with no intervening output is one example, and a
    statement after output starts another. That is a proxy for what a reader would call a
    separate example, and reading every `>>>` as one would fail every idiomatic docstring
    in the project.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, module, owned in _docstrings(b, "touched"):
            if owned is None:
                targets.append(_unreadable_target(path, module))
                continue
            section = owned.doc.section("Examples")
            if section is None:
                continue
            examples = _section_examples(owned, section)
            body = dict(section.body)
            for previous, current in zip(examples, examples[1:]):
                if not previous.want.strip():
                    continue  # a statement chain, not a second example
                gap = [body.get(n, "") for n in range(previous.end_lineno + 1, current.lineno)]
                targets.append(_target(
                    f"examplegap:{path}:{current.lineno}", path,
                    (previous.end_lineno, current.lineno), (owned, gap),
                    current.source.strip()))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned, gap = t.payload
        if any(not text.strip() for text in gap):
            return Satisfied()
        return Violated(f"examples in {owned.docstring.owner} are not separated by a "
                        f"blank line")


@rule(id="SYMPY-C186", category=CATEGORY, ownership="touched", reads=("files",))
class ExplanatoryTextIsSeparated:
    """Pre-condition: every run of prose sitting between two doctests in an Examples
    section the agent owns.
    Pass condition: a blank line above it and a blank line below it."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, module, owned in _docstrings(b, "touched"):
            if owned is None:
                targets.append(_unreadable_target(path, module))
                continue
            section = owned.doc.section("Examples")
            if section is None:
                continue
            for run in _prose_between_doctests(section):
                targets.append(_target(
                    f"prose:{path}:{run[0][0]}", path, (run[0][0], run[-1][0]),
                    (owned, run, section), run[0][1].strip()))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned, run, section = t.payload
        body = dict(section.body)
        above = body.get(run[0][0] - 1)
        below = body.get(run[-1][0] + 1)
        missing = [side for side, text in (("above", above), ("below", below))
                   if text is not None and text.strip()]
        if not missing:
            return Satisfied()
        return Violated(f"explanatory text in {owned.docstring.owner} has no blank line "
                        f"{' or '.join(missing)} it: {run[0][1].strip()[:40]!r}")


def _prose_between_doctests(section: ds.Section) -> list[list[tuple[int, str]]]:
    """Runs of non-doctest, non-blank lines that sit between two doctest lines."""
    body = list(section.body)
    prompts = [index for index, (_, text) in enumerate(body) if _PROMPT.match(text)]
    if len(prompts) < 2:
        return []
    runs: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    started = False
    for index, (lineno, text) in enumerate(body):
        if _PROMPT.match(text):
            if current:
                runs.append(current)
                current = []
            started = True
            continue
        if not started or index > prompts[-1]:
            continue
        if text.strip():
            # Expected output belongs to the example above it, not to prose.
            if not current and index and _PROMPT.match(body[index - 1][1]):
                continue
            current.append((lineno, text))
        elif current:
            runs.append(current)
            current = []
    return [run for run in runs if run]


@rule(id="SYMPY-C188", category=CATEGORY, ownership="touched", reads=("files",))
class LongDoctestInputIsWrapped:
    """Pre-condition: every doctest example the agent owns whose input is longer than 80
    characters.
    Pass condition: it is wrapped across lines with the `...` continuation prompt, so no
    single line exceeds the limit."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, module, owned, example in _owned_examples(b):
            if owned is None:
                targets.append(_unreadable_target(path, module))
                continue
            if len(example.source.strip()) > DOCTEST_LINE_LIMIT:
                targets.append(_target(f"longinput:{path}:{example.lineno}", path,
                                       example.span(), (owned, example),
                                       example.source.strip()[:80]))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned, example = t.payload
        over = [(n, text) for n, text in owned.lines()
                if example.lineno <= n <= example.end_lineno and _PROMPT.match(text)
                and owned.docstring.indent + len(text) > DOCTEST_LINE_LIMIT]
        if not over:
            return Satisfied()
        lineno, text = over[0]
        return Violated(f"doctest input at line {lineno} is "
                        f"{owned.docstring.indent + len(text)} characters, over the "
                        f"{DOCTEST_LINE_LIMIT}-character limit and not wrapped")


# --- Parameters, See Also, References --------------------------------------------------


def _section_entry_targets(b: EvidenceBundle, prefix: str, section_name: str,
                           *, where=None) -> list[Target]:
    """One target per entry of a named section, across the docstrings the agent owns."""
    targets: list[Target] = []
    for path, module, owned in _docstrings(b, "touched"):
        if owned is None:
            targets.append(_unreadable_target(path, module))
            continue
        section = owned.doc.section(section_name)
        if section is None:
            continue
        for entry in _entries(section):
            if where is not None and not where(entry):
                continue
            targets.append(_target(f"{prefix}:{path}:{entry.lineno}", path,
                                   (entry.lineno, entry.lineno), (owned, entry),
                                   entry.text))
    return targets


@rule(id="SYMPY-C192", category=CATEGORY, ownership="touched", reads=("files",))
class ParameterNamesInCodeMarkup:
    """Pre-condition: every entry of a Parameters section the agent owns.
    Pass condition: its parameter name is wrapped in double backticks."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _section_entry_targets(b, "paramname", "Parameters")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned, entry = t.payload
        name = _parameter_name_part(entry.text)
        if name.startswith("``") and name.endswith("``") and len(name) > 4:
            return Satisfied()
        return Violated(f"parameter {name[:40]!r} in {owned.docstring.owner} is not in "
                        f"double-backtick code markup")


def _parameter_name_part(text: str) -> str:
    match = _PARAM_SEP.match(text)
    return (match.group("name") if match else text).strip()


@rule(id="SYMPY-C193", category=CATEGORY, ownership="touched", reads=("files",))
class ParameterTypeSeparator:
    """Pre-condition: every entry of a Parameters section the agent owns.
    Pass condition: an entry that supplies a type separates it as `name : type`, and an
    entry that supplies none carries no colon at all."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _section_entry_targets(b, "paramsep", "Parameters")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned, entry = t.payload
        match = _PARAM_SEP.match(entry.text)
        if match is None:
            return Satisfied()  # no colon and no type: the admissible bare-name form
        separator, type_part = match.group("sep"), match.group("type").strip()
        if not type_part:
            return Violated(f"parameter entry {entry.text[:40]!r} in "
                            f"{owned.docstring.owner} carries a colon but no type")
        if separator != " : ":
            return Violated(f"parameter entry {entry.text[:40]!r} in "
                            f"{owned.docstring.owner} separates name and type as "
                            f"{separator!r}, expected ' : '")
        return Satisfied()


@rule(id="SYMPY-C194", category=CATEGORY, ownership="touched", reads=("files",))
class SeeAlsoContinuationIndented:
    """Pre-condition: every See Also entry the agent owns whose description continues past
    its first line.
    Pass condition: every continuation line is indented under the entry."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, module, owned in _docstrings(b, "touched"):
            if owned is None:
                targets.append(_unreadable_target(path, module))
                continue
            section = owned.doc.section("See Also")
            if section is None:
                continue
            for block in _see_also_blocks(section):
                if not (block["indented"] or block["unindented"]):
                    continue
                targets.append(_target(f"seealsowrap:{path}:{block['lineno']}", path,
                                       (block["lineno"], block["lineno"]), (owned, block),
                                       block["text"]))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned, block = t.payload
        if not block["unindented"]:
            return Satisfied()
        lineno, text = block["unindented"][0]
        return Violated(f"See Also description in {owned.docstring.owner} continues "
                        f"unindented at line {lineno}: {text.strip()[:40]!r}")


def _see_also_blocks(section: ds.Section) -> list[dict]:
    """See Also entries, each with its indented and unindented continuation lines.

    The split matters: an unindented continuation is indistinguishable from a new entry by
    position alone, so it is recognised by not naming an object.
    """
    body = [(n, t) for n, t in section.body if t.strip()]
    if not body:
        return []
    base = min(len(t) - len(t.lstrip()) for _, t in body)
    blocks: list[dict] = []
    for lineno, text in body:
        indent = len(text) - len(text.lstrip())
        stripped = text.strip()
        if indent <= base and _is_reference(stripped):
            blocks.append({"lineno": lineno, "text": stripped,
                           "indented": [], "unindented": []})
        elif not blocks:
            continue
        elif indent > base:
            blocks[-1]["indented"].append((lineno, text))
        else:
            blocks[-1]["unindented"].append((lineno, text))
    return blocks


@rule(id="SYMPY-C195", category=CATEGORY, ownership="touched", reads=("files",))
class SeeAlsoOnlySymPyObjects:
    """Pre-condition: every See Also entry the agent owns.
    Pass condition: it names a SymPy object rather than an external link."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _see_also_entry_targets(b, "seealsoexternal")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned, block = t.payload
        text = block["text"]
        if rst.urls(text) or _MD_LINK.search(text) or "<http" in text:
            return Violated(f"See Also entry in {owned.docstring.owner} is an external "
                            f"link, which belongs in prose or References: {text[:50]!r}")
        return Satisfied()


def _see_also_entry_targets(b: EvidenceBundle, prefix: str) -> list[Target]:
    targets: list[Target] = []
    for path, module, owned in _docstrings(b, "touched"):
        if owned is None:
            targets.append(_unreadable_target(path, module))
            continue
        section = owned.doc.section("See Also")
        if section is None:
            continue
        for block in _see_also_blocks(section):
            targets.append(_target(f"{prefix}:{path}:{block['lineno']}", path,
                                   (block["lineno"], block["lineno"]), (owned, block),
                                   block["text"]))
    return targets


@rule(id="SYMPY-C196", category=CATEGORY, ownership="touched", reads=("files",))
class SeeAlsoBareClassNames:
    """Pre-condition: every See Also entry the agent owns.
    Pass condition: it is written as a bare name, with no `:class:` role and no backticks."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _see_also_entry_targets(b, "seealsomarkup")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned, block = t.payload
        name = block["text"].split(":")[0] if " : " not in block["text"] \
            else block["text"].split(" : ")[0]
        head = block["text"]
        if ":class:" in head or re.match(r"^\s*class:", head):
            return Violated(f"See Also entry in {owned.docstring.owner} references a class "
                            f"with a role, not a bare name: {head[:50]!r}")
        if "`" in name:
            return Violated(f"See Also entry in {owned.docstring.owner} wraps the name in "
                            f"backticks, expected a bare name: {name.strip()[:50]!r}")
        return Satisfied()


@rule(id="SYMPY-C197", category=CATEGORY, ownership="touched", reads=("files",))
class ReferencesNumberedFromOne:
    """Pre-condition: every References section the agent owns that carries numbered
    citations.
    Pass condition: they run from 1 upwards in the order they are written."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, module, owned in _docstrings(b, "touched"):
            if owned is None:
                targets.append(_unreadable_target(path, module))
                continue
            section = owned.doc.section("References")
            if section is None:
                continue
            labels = [label for _, label in rst.citations(section.body)
                      if _CITATION_NUMBER.match(label)]
            if labels:
                targets.append(_target(f"citations:{path}:{section.heading.lineno}", path,
                                       owned.span, (owned, labels), ", ".join(labels)))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned, labels = t.payload
        expected = [str(n) for n in range(1, len(labels) + 1)]
        if labels == expected:
            return Satisfied()
        return Violated(f"References in {owned.docstring.owner} are numbered "
                        f"{', '.join(labels)}, expected {', '.join(expected)}")


@rule(id="SYMPY-C199", category=CATEGORY, ownership="touched", reads=("files",))
class DoiIsAHyperlink:
    """Pre-condition: every reference the agent owns that carries a DOI.
    Pass condition: the DOI is given as a clickable link."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, module, owned in _docstrings(b, "touched"):
            if owned is None:
                targets.append(_unreadable_target(path, module))
                continue
            section = owned.doc.section("References")
            if section is None:
                continue
            for entry in _entries(section):
                text = entry.described()
                if rst.dois(text):
                    targets.append(_target(f"doi:{path}:{entry.lineno}", path,
                                           (entry.lineno, entry.lineno), (owned, text),
                                           entry.text))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned, text = t.payload
        urls = " ".join(rst.urls(text))
        if any(doi in urls for doi in rst.dois(text)):
            return Satisfied()
        return Violated(f"DOI {rst.dois(text)[0]} in {owned.docstring.owner} is not given "
                        f"as a clickable link")


@rule(id="SYMPY-C203", category=CATEGORY, ownership="touched", reads=("files",))
class MathFunctionDocumentedAtClassLevel:
    """Pre-condition: every mathematical-function class defining `eval` whose
    documentation the agent wrote -- its class docstring, a docstring on `eval`, or the
    class itself.
    Pass condition: the class carries the docstring and `eval` carries none.

    The antecedent is a *documentation decision*, not any edit inside the class. Two
    narrowings, both found by running this rule against the pilot before trusting it.
    Deciding ownership on the class span made an agent that edited one line of a 131-line
    `coth` class the owner of a docstring SymPy's authors wrote -- the A6 defect. Deciding
    it on the class's own lines plus `eval` still credited an agent that had only fixed
    logic inside `eval`'s body, which is not documentation work either. Both produced four
    spurious passes, and invariant 5 forbids both.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, module in _modules(b):
            if not module.ok:
                targets.append(_unreadable_target(path, module))
                continue
            for node in ast.walk(module.tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                bases = {pa.dotted_name(base).split(".")[-1] for base in node.bases}
                if not bases & MATH_FUNCTION_BASES:
                    continue
                methods = [child for child in node.body
                           if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                           and child.name == EVAL_METHOD]
                if not methods:
                    continue
                span = pa.span_of(node)
                if not _documents(b.files[path], node, methods[0]):
                    continue
                targets.append(_target(f"mathfn:{path}:{node.lineno}", path, span,
                                       (node, methods[0]), f"class {node.name}"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        node, eval_method = t.payload
        if ast.get_docstring(eval_method):
            return Violated(f"{node.name}.{EVAL_METHOD} has its own docstring; the "
                            f"documentation belongs at class level")
        if not ast.get_docstring(node):
            return Violated(f"mathematical-function class {node.name} carries no "
                            f"class-level docstring")
        return Satisfied()


# --- cross-referencing -----------------------------------------------------------------


def _owned_roles(b: EvidenceBundle, prefix: str, *, where=None) -> list[Target]:
    """One target per Sphinx role in the docstrings the agent owns."""
    targets: list[Target] = []
    for path, module, owned in _docstrings(b, "touched"):
        if owned is None:
            targets.append(_unreadable_target(path, module))
            continue
        for role in rst.roles(owned.lines()):
            if where is not None and not where(owned, role):
                continue
            targets.append(_target(f"{prefix}:{path}:{role.lineno}:{role.target}", path,
                                   (role.lineno, role.lineno), (owned, role), role.raw))
    return targets


def _base_name(target: str) -> str:
    return target.lstrip("~.").split("<")[0].strip().split(".")[-1]


@rule(id="SYMPY-C206", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class ProseCrossReferencesUseRoles:
    """Pre-condition: every reference to a SymPy object in the prose of a docstring the
    agent owns, written either as a role or as a single-backtick span.
    Pass condition: it is written as a Sphinx cross-reference role.

    Heuristic twice over: a single-backtick span naming an identifier is taken to be an
    object reference, and whether the name is a SymPy object is decided against a curated
    list. A bare name in prose with no markup at all is not detected, which narrows the
    pre-condition rather than the grading.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, module, owned in _docstrings(b, "touched"):
            if owned is None:
                targets.append(_unreadable_target(path, module))
                continue
            for role in rst.roles(owned.lines()):
                targets.append(_target(
                    f"xref:{path}:{role.lineno}:{role.target}", path,
                    (role.lineno, role.lineno), (owned, role.raw, True), role.raw))
            for lineno, text in owned.lines():
                for span in rst.single_backtick_spans(text):
                    if _names_sympy_object(span):
                        targets.append(_target(
                            f"xref:{path}:{lineno}:{span}", path, (lineno, lineno),
                            (owned, span, False), f"`{span}`"))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned, text, is_role = t.payload
        if is_role:
            return Satisfied()
        return Violated(f"reference to {text!r} in {owned.docstring.owner} uses a single "
                        f"backtick, not a cross-reference role such as :obj:`~.{text}`")


def _names_sympy_object(span: str) -> bool:
    name = span.strip()
    if not (_IDENTIFIER.match(name) or _DOTTED.match(name)):
        return False
    return name.split(".")[0] in TOP_LEVEL_NAMES or name.split(".")[-1] in TOP_LEVEL_NAMES


@rule(id="SYMPY-C207", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class NonTopLevelObjectsUseFullPath:
    """Pre-condition: every cross-reference in a docstring the agent owns whose target is
    not a name SymPy exports from its top level.
    Pass condition: it gives the object's full dotted path and does not abbreviate with
    `~.`.

    Heuristic: "not exported from the top level" is decided against a curated list of
    top-level names, which is necessarily partial.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _owned_roles(b, "fullpath",
                            where=lambda o, role: _base_name(role.target) not in TOP_LEVEL_NAMES)

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned, role = t.payload
        link = role.link_target
        if link.startswith("~"):
            return Violated(f"{role.raw} in {owned.docstring.owner} abbreviates with `~.` "
                            f"but is not a top-level SymPy object")
        if "." not in link.lstrip("."):
            return Violated(f"{role.raw} in {owned.docstring.owner} gives a bare name; a "
                            f"non-top-level object needs its full path")
        return Satisfied()


@rule(id="SYMPY-C208", category=CATEGORY, ownership="touched", reads=("files",))
class UnlinkableNamesUseCodeMarkup:
    """Pre-condition: every `:obj:` cross-reference the agent wrote whose target is a
    Python built-in, an external library's object, or a parameter of the documented
    function.
    Pass condition: none -- nothing unlinkable may be given a role, so each such
    reference is the violation."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _owned_roles(b, "unlinkable", where=_is_unlinkable)

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned, role = t.payload
        return Violated(f"{role.raw} in {owned.docstring.owner} cross-references "
                        f"{_unlinkable_kind(owned, role)}, which takes double-backtick "
                        f"code markup instead")


def _is_unlinkable(owned: OwnedDoc, role) -> bool:
    return bool(_unlinkable_kind(owned, role))


def _unlinkable_kind(owned: OwnedDoc, role) -> str:
    name = _base_name(role.target)
    root = role.link_target.lstrip("~.").split(".")[0]
    if root in EXTERNAL_MODULES:
        return f"the external object `{root}`"
    if name in BUILTIN_NAMES:
        return f"the Python built-in `{name}`"
    if name in _parameter_names(owned):
        return f"the parameter `{name}`"
    return ""


@rule(id="SYMPY-C210", category=CATEGORY, ownership="touched", reads=("files",))
class CustomTextLinksOmitTilde:
    """Pre-condition: every cross-reference the agent wrote that supplies custom link
    text.
    Pass condition: it uses the `:obj:`text <object>`` form with no `~` in the target."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _owned_roles(b, "customtext", where=lambda o, role: role.custom_text)

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        owned, role = t.payload
        if "~" in role.link_target:
            return Violated(f"{role.raw} in {owned.docstring.owner} uses `~` inside a "
                            f"custom-text link target")
        if role.role != "obj":
            return Violated(f"{role.raw} in {owned.docstring.owner} uses the "
                            f"`:{role.role}:` role; a custom-text object link takes :obj:")
        return Satisfied()


# --- narrative documentation files -----------------------------------------------------


@rule(id="SYMPY-C213", category=CATEGORY, ownership="touched", reads=("files",))
class NoMarkdownOutsideNarrativeDocs:
    """Pre-condition: every Markdown file the agent added or edited inside the library
    source tree, where documentation is not narrative.
    Pass condition: none -- Markdown is supported for narrative documentation only, so
    such a file is the violation.

    Scoped to the library tree deliberately. `doc/` is where narrative documentation
    lives, and a Markdown file at the repository root is project metadata rather than the
    non-narrative documentation this rule governs.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, _ in _doc_files(b, suffixes=(".md", ".markdown"), narrative=False):
            if not path.startswith(LIBRARY_ROOT):
                continue
            targets.append(_target(f"markdown:{path}", path, None, path, path))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        return Violated(f"{t.payload} is Markdown inside the library source tree, where "
                        f"documentation must be reStructuredText")


@rule(id="SYMPY-C221", category=CATEGORY, ownership="touched", reads=("files",))
class VerbatimCodeUsesDoubleBackticks:
    """Pre-condition: every single-backtick span the agent wrote in an RST documentation
    file.
    Pass condition: none -- a single backtick renders as math rather than code, so
    verbatim code needs double backticks and a single-backtick span is the violation."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, lines in _doc_files(b, suffixes=(".rst", ".rest")):
            for lineno, text in _authored(b, path, lines):
                for span in rst.single_backtick_spans(text):
                    targets.append(_target(f"backtick:{path}:{lineno}:{span}", path,
                                           (lineno, lineno), (path, span), text.strip()))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        path, span = t.payload
        return Violated(f"`{span}` in {path} uses single backticks, which render as math; "
                        f"verbatim code takes double backticks")


@rule(id="SYMPY-C227", category=CATEGORY, ownership="touched", reads=("files",))
class RstHeadingAdornment:
    """Pre-condition: every RST section heading the agent wrote.
    Pass condition: its underline, and its overline if it has one, is one repeated
    punctuation character at least as long as the heading text."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, lines in _doc_files(b, suffixes=(".rst", ".rest")):
            change = b.files[path]
            for heading in rst.headings(lines):
                span = (heading.lineno, heading.underline_lineno)
                if not (change.is_new or set(range(span[0], span[1] + 1)) & change.authored_lines):
                    continue
                targets.append(_target(f"rstheading:{path}:{heading.lineno}", path, span,
                                       (path, heading), heading.text.strip()))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        path, heading = t.payload
        if heading.is_consistent:
            return Satisfied()
        return Violated(f"heading {heading.text.strip()[:40]!r} in {path} is adorned with "
                        f"{heading.underline.strip()[:12]!r}, which is not one repeated "
                        f"character at least as long as the text")


@rule(id="SYMPY-C228", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class NarrativeDocsUseAmericanSpelling:
    """Pre-condition: every narrative documentation file the agent wrote lines in.
    Pass condition: none of those lines uses a British spelling.

    Heuristic: a word list is a proxy for a spelling standard, never the standard itself.
    It cannot see a British spelling it does not list, and cannot tell a quoted British
    spelling from an authored one.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, lines in _doc_files(b, suffixes=(".rst", ".rest", ".md", ".markdown"),
                                      narrative=True):
            authored = _authored(b, path, lines)
            if authored:
                targets.append(_target(f"spelling:{path}", path, None, (path, authored), path))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        path, lines = t.payload
        found = _words_from(lines, BRITISH_SPELLINGS)
        if not found:
            return Satisfied()
        lineno, word = found[0]
        return Violated(f"{path} line {lineno} uses the British spelling {word!r} "
                        f"({len(found)} occurrence(s) in this file)")


def _words_from(lines, vocabulary: frozenset[str]) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for lineno, text in lines:
        for word in re.findall(r"[A-Za-z]+", text):
            if word.lower() in vocabulary:
                out.append((lineno, word))
    return out


@rule(id="SYMPY-C234", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class DocumentationUsesGenderNeutralThey:
    """Pre-condition: every piece of documentation the agent wrote -- a narrative
    documentation file, or a docstring.
    Pass condition: it refers to a person as `they` rather than `he` or `she`.

    Heuristic: matching pronoun words cannot tell a pronoun from a quoted one, nor `her`
    the pronoun from a name. It is a proxy for the tone the guide asks for.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets: list[Target] = []
        for path, lines in _doc_files(b, suffixes=(".rst", ".rest", ".md", ".markdown")):
            authored = _authored(b, path, lines)
            if authored:
                targets.append(_target(f"pronoun:{path}", path, None, (path, authored), path))
        for path, module, owned in _docstrings(b, "touched"):
            if owned is None:
                targets.append(_unreadable_target(path, module))
                continue
            targets.append(_target(f"pronoun:{path}:{owned.span[0]}", path, owned.span,
                                   (f"{path}:{owned.docstring.owner}", owned.lines()),
                                   owned.docstring.owner))
        return targets

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        where, lines = t.payload
        found = _words_from(lines, frozenset(GENDERED_PRONOUNS))
        if not found:
            return Satisfied()
        lineno, word = found[0]
        return Violated(f"{where} line {lineno} uses the gendered pronoun {word!r}; "
                        f"documentation uses `they`")


# --- building the documentation, and running its examples -------------------------------


def _documentation_change_target(b: EvidenceBundle, prefix: str) -> list[Target]:
    """The shared antecedent of the build rules: this contribution changed documentation.

    Never the build command itself. Triggering on *"the agent ran a doc build"* would let
    an agent that changed documentation and never built it collect `not_applicable`, which
    is the §4.2 inversion these rules exist to avoid.
    """
    changed = _changed_documentation(b)
    if not changed:
        return []
    return [_target(f"{prefix}:{b.instance_id}", None, None, (b, changed),
                    ", ".join(changed[:5]))]


@rule(id="SYMPY-C146", category=CATEGORY, ownership="touched", reads=("files", "commands"))
class DocsBuiltLocally:
    """Pre-condition: the contribution changes documentation.
    Pass condition: the agent ran `cd doc` and then `make html`, and the build succeeded."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _documentation_change_target(b, "docbuild")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        bundle, changed = t.payload
        builds = _ran(bundle, _MAKE_HTML)
        if not builds:
            return Violated(f"changed documentation in {len(changed)} file(s) and never "
                            f"ran `make html`")
        if not _ran(bundle, _CD_DOC):
            return Violated("ran `make html` without first changing into the `doc` directory")
        if failed := [c for c in builds if _SPHINX_FAILED.search(c.output or "")]:
            return Violated(f"`make html` reported errors ({len(failed)} run(s))")
        return Satisfied(f"ran `cd doc` and `make html` ({len(builds)} time(s))")


@rule(id="SYMPY-C175", category=CATEGORY, ownership="touched", reads=("files", "commands"))
class DocumentationBuildsWithoutSphinxErrors:
    """Pre-condition: the contribution changes documentation.
    Pass condition: a local documentation build was run -- through the makefile or the
    `sympy_htmldoc` image -- and Sphinx emitted no errors."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _documentation_change_target(b, "sphinx")

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        bundle, changed = t.payload
        builds = _ran(bundle, _MAKE_HTML) + _ran(bundle, _HTMLDOC_IMAGE)
        if not builds:
            return Violated(f"changed documentation in {len(changed)} file(s) without ever "
                            f"building it, so Sphinx output was never checked")
        if failed := [c for c in builds if _SPHINX_FAILED.search(c.output or "")]:
            first = _SPHINX_FAILED.search(failed[0].output or "")
            return Violated(f"Sphinx reported {first.group(0).strip()!r} during the "
                            f"documentation build")
        return Satisfied(f"documentation built cleanly ({len(builds)} run(s))")


@rule(id="SYMPY-C190", category=CATEGORY, ownership="touched", reads=("files", "commands"))
class DoctestsRunAfterChangingExamples:
    """Pre-condition: the agent added or changed a docstring example.
    Pass condition: it ran `python bin/doctest`, and the run reported no failure."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        examples = [(path, example) for path, _, owned, example in _owned_examples(b)
                    if owned is not None]
        if not examples:
            return []
        path, example = examples[0]
        return [_target(f"doctestrun:{b.instance_id}", path, example.span(),
                        (b, examples), f"{len(examples)} example(s) changed")]

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        bundle, examples = t.payload
        runs = _ran(bundle, _BIN_DOCTEST)
        if not runs:
            return Violated(f"changed {len(examples)} docstring example(s) and never ran "
                            f"`bin/doctest`")
        if failed := [c for c in runs if _DOCTEST_FAILED.search(c.output or "")]:
            return Violated(f"`bin/doctest` reported failures ({len(failed)} run(s)) that "
                            f"were left unfixed")
        return Satisfied(f"ran `bin/doctest` {len(runs)} time(s), no reported failure")


@rule(id="SYMPY-C150", category=CATEGORY, ownership="touched", reads=("files", "commands"))
class PdfBuildUsesDoubleBackticks:
    """Pre-condition: a PDF documentation build the agent ran that failed.
    Pass condition: the documentation it wrote delimits code with double backticks.

    Structurally unreachable on this benchmark, and recorded as such rather than removed.
    The antecedent is a *failing PDF build*: SWE-bench instances are bug fixes, no stored
    run has ever invoked `make latexpdf`, and the corpus is the specification. The rule
    reports `not_applicable` for the honest reason that its antecedent never arises --
    which is different from a broken pre-condition.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        failed = [c for c in _ran(b, _PDF_BUILD) if _SPHINX_FAILED.search(c.output or "")]
        if not failed:
            return []
        return [_target(f"pdfbuild:{b.instance_id}", None, None, (b, failed),
                        failed[0].command[:80])]

    def pass_condition(self, t: Target):
        if (broken := _unreadable(t)) is not None:
            return broken
        bundle, _ = t.payload
        offenders: list[str] = []
        for path, lines in _doc_files(bundle, suffixes=(".rst", ".rest")):
            for lineno, text in _authored(bundle, path, lines):
                offenders += [f"{path}:{lineno} `{span}`"
                              for span in rst.single_backtick_spans(text)]
        if not offenders:
            return Satisfied("PDF build failed, but the documentation uses double backticks")
        return Violated(f"PDF build failed and {len(offenders)} code span(s) use single "
                        f"backticks: {offenders[0]}")


def _documents(change, node: ast.ClassDef, eval_method: ast.AST) -> bool:
    """Whether the agent made a documentation decision about this class.

    Writing the class outright, writing its docstring, or writing one on `eval`. Editing
    the class body -- even `eval`'s body -- is not one: nothing about where the
    documentation lives was decided, and grading it would score whoever wrote the
    docstring years earlier (invariant 5).
    """
    if change.is_new:
        return True
    class_lines = _line_set(pa.span_of(node))
    if class_lines <= change.authored_lines:
        return True
    sites: set[int] = set()
    for owner in (node, eval_method):
        if (span := _docstring_span(owner)) is not None:
            sites |= _line_set(span)
    return bool(sites & change.modified_lines)


def _docstring_span(node: ast.AST) -> Optional[tuple[int, int]]:
    body = getattr(node, "body", None)
    if not body:
        return None
    first = body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
            and isinstance(first.value.value, str):
        return pa.span_of(first)
    return None


def _line_set(span: tuple[int, int]) -> set[int]:
    return set(range(span[0], span[1] + 1))

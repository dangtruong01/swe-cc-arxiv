"""astropy: Documentation and docstrings -- 26 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

**Twenty of these come from one style guide, and they are lexical rules.** The shape they
all share is §7.1 applied to spelling: *"use the numeral when a unit follows"* is not a rule
about numerals, and a pre-condition selecting only spelled-out numbers could record
violations and never a compliant line. So each one fires on the *situation* -- a line that
states a quantity, a line that quotes something, a line that uses a dash -- and the grading
asks which form it took. That is why these pre-conditions read wider than the rule text
sounds.

**Where the prose is.** ``_common.prose_lines`` yields from two places, because astropy's
style guide governs "Astropy materials" and its docstrings are rendered into the same
manual: lines the agent added to ``docs/**.rst``, and lines it wrote inside docstrings.
Changelog fragments are excluded there and graded by C063 and C237 instead -- the §7.5
narrowing for this corpus, pinned by a no-target test.

**Three narrowings between rules in this module, each with a test.** C152 leaves the word
*astropy* to C153, which legislates its two spellings specifically. C161 leaves numbers
followed by a unit to C160. C220 leaves development-version links to C221, which is the
stated exception to the intersphinx rule.

**C206 is graded on the functions the agent added, not on every one it edited.** Its six
sub-questions are a review checklist for contributed code; applying them to a legacy
docstring the agent touched one line of would fail the agent for someone else's omission,
which invariant 5 exists to prevent. C085 and C219 are wider on purpose -- presence and
format are properties an edit makes you answerable for.
"""

from __future__ import annotations

import ast
import re
from typing import Iterator

from compliance.core import ownership as own
from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import docstrings as dsx
from compliance.extractors import python_ast as pa
from compliance.extractors import rst
from compliance.rules.astropy._common import (DOC_ROOT, added_lines, documentation_files,
                                              is_source_path, modules, owned_files,
                                              is_doc_path, prose_line_targets, prose_lines,
                                              strip_markup, target)

CATEGORY = "Documentation and docstrings"

# --- vocabulary ------------------------------------------------------------------------

_ABBREVIATION = re.compile(r"\b(i\.e\.|e\.g\.)")
#: Acronyms that name a format, a protocol or a concept rather than an organization. The
#: rule is about organizations, and without this the check reports every FITS mention.
_NOT_ORGANIZATIONS = frozenset("""
FITS WCS HDU API URL URI HTML CSV JSON XML YAML RST HTTP HTTPS TODO NOTE FIXME BSD MIT
ASCII UTF PEP CPU GPU RAM CI PR ID IO OK NaN UTC TAI TDB GPS JD MJD ISO SI RA DEC FWHM
SNR PSF CCD MB KB GB HDF NDD VO SED LSB MSB EOF CLI GUI
""".split())
_ACRONYM = re.compile(r"(?<![\w/.])([A-Z]{3,8})(?![\w/.])")
_LINKED = re.compile(r"`[^`]*\b{}\b[^`]*<[^>]+>`_")

#: Package and code names the style guide asks for in lowercase double backticks. `astropy`
#: is deliberately absent: C153 legislates its two spellings and grading it here too would
#: contradict that rule (§7.5).
_CODE_NAMES = ("numpy", "scipy", "matplotlib", "pytest", "sphinx", "pyerfa", "asdf",
               "erfa", "h5py", "dask", "pandas", "healpy")
#: Selects the name in every spelling, backticked or bare -- the pre-condition has to
#: see the compliant form too, or the rule could never record a pass (§7.1).
_CODE_NAME_ANY = re.compile(r"(?<![\w.])(" + "|".join(_CODE_NAMES) + r")(?![\w.])", re.I)
_ASTROPY_ANY = re.compile(r"(?<![\w.])(``astropy``|`astropy`|Astropy|astropy)(?![\w.])")

_CONTRACTION = re.compile(
    r"\b(don't|doesn't|didn't|isn't|aren't|wasn't|weren't|can't|cannot've|won't|wouldn't"
    r"|shouldn't|couldn't|hasn't|haven't|hadn't|it's|that's|there's|here's|what's|let's"
    r"|you're|we're|they're|I'm|you'll|we'll|it'll|you've|we've|they've|I've)\b", re.I)

_NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
                 "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
                 "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
                 "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
                 "twenty": 20}
_UNITS = ("arcminute", "arcminutes", "arcsecond", "arcseconds", "degree", "degrees",
          "radian", "radians", "meter", "meters", "metre", "metres", "second", "seconds",
          "minute", "minutes", "hour", "hours", "day", "days", "year", "years", "pixel",
          "pixels", "byte", "bytes", "kB", "MB", "GB", "Hz", "kHz", "MHz", "GHz", "K",
          "angstrom", "angstroms", "parsec", "parsecs", "kpc", "Mpc", "AU", "au", "km",
          "cm", "mm", "nm", "erg", "ergs", "Jy", "mag")
_UNIT_ALTERNATION = "|".join(sorted(map(re.escape, _UNITS), key=len, reverse=True))
_WORD_ALTERNATION = "|".join(_NUMBER_WORDS)
_NUMBER_WITH_UNIT = re.compile(
    rf"\b(?P<value>\d+(?:\.\d+)?|{_WORD_ALTERNATION})\s+(?P<unit>{_UNIT_ALTERNATION})\b",
    re.I)
_BARE_NUMBER = re.compile(rf"(?<![\w.\-])(?P<value>\d+|{_WORD_ALTERNATION})(?![\w.])", re.I)
_SCALE_WORD = re.compile(r"\b(million|billion|trillion|thousand)\b", re.I)

_PARENTHETICAL = re.compile(r"\(([^()]*)\)")
_QUOTED = re.compile(r"\"([^\"\n]{1,120})\"|“([^”\n]{1,120})”")
_QUOTE_THEN_PUNCTUATION = re.compile(r"[\"”][.,]")

_EN_DASH = "–"
_EM_DASH = "—"
_NUMBER_RANGE = re.compile(
    rf"\b\d+\s*(?P<dash>-|{_EN_DASH}|{_EM_DASH})\s*\d+\b|\b\d+\s+(?:to|through)\s+\d+\b")
_EM_DASH_USE = re.compile(_EM_DASH)

#: British spellings and their American forms. Necessarily partial, which is the heuristic
#: admission in C168.
_BRITISH = {
    "catalogue": "catalog", "catalogues": "catalogs", "catalogued": "cataloged",
    "colour": "color", "colours": "colors", "coloured": "colored",
    "behaviour": "behavior", "behaviours": "behaviors",
    "centre": "center", "centres": "centers", "centred": "centered",
    "normalise": "normalize", "normalised": "normalized", "normalises": "normalizes",
    "normalisation": "normalization", "initialise": "initialize",
    "initialised": "initialized", "initialisation": "initialization",
    "serialise": "serialize", "serialised": "serialized", "serialisation": "serialization",
    "organise": "organize", "organised": "organized", "organisation": "organization",
    "recognise": "recognize", "recognised": "recognized",
    "analyse": "analyze", "analysed": "analyzed",
    "licence": "license", "defence": "defense", "grey": "gray",
    "modelling": "modeling", "modelled": "modeled", "labelled": "labeled",
    "labelling": "labeling", "cancelled": "canceled", "travelling": "traveling",
    "fibre": "fiber", "metre": "meter", "metres": "meters", "litre": "liter",
    "programme": "program", "aeroplane": "airplane", "artefact": "artifact",
    "artefacts": "artifacts",
}
_AMERICAN = frozenset(_BRITISH.values())
_SPELLING_WORD = re.compile(r"\b[A-Za-z]+\b")

_TIME = re.compile(r"\b(?P<h>\d{1,2})(?::(?P<m>\d{2}))?\s*(?P<meridiem>[ap]\.?m\.?)"
                   r"(?![a-zA-Z])", re.I)
_ISO_TIME = re.compile(r"\b([01]?\d|2[0-3]):[0-5]\d\b")
_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_MONTH = ("January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December")
_WORD_DATE = re.compile(rf"\b(?:{'|'.join(_MONTH)})\s+\d{{1,2}},?\s+\d{{4}}\b"
                        rf"|\b\d{{1,2}}\s+(?:{'|'.join(_MONTH)})\s+\d{{4}}\b"
                        rf"|\b\d{{1,2}}/\d{{1,2}}/\d{{4}}\b")

#: Case matters here: "I" is the pronoun, "i" is an index. Spelled out rather than
#: matched case-insensitively for that reason.
_FIRST_PERSON = re.compile(
    r"(?<![\w'])(I|[Ww]e|[Mm]e|[Mm]y|[Mm]ine|[Uu]s|[Oo]ur|[Oo]urs)(?![\w'])")
_FIRST_PERSON_SINGULAR = re.compile(r"(?<![\w'])(I|[Mm]e|[Mm]y|[Mm]ine)(?![\w'])")
_GENERIC_ONE = re.compile(
    r"\bone\s+(can|should|must|may|might|will|would|needs?|has|have|is|are|does|do|wants?)\b",
    re.I)
_GENERIC_YOU = re.compile(r"(?<![\w'])(you|your|yours)(?![\w'])", re.I)
_BELITTLING = re.compile(
    r"\b(obviously|easily|simply|just|straightforward|trivially|of course|clearly)\b", re.I)

_WARNING_DIRECTIVE = re.compile(r"^\s*\.\.\s+warning::")
#: A warning that talks about the reader rather than about the code.
_READER_DIRECTED = re.compile(
    r"\b(you should be careful|be careful|beginners?|novices?|if you are not familiar"
    r"|make sure you (understand|know)|assumed knowledge|inexperienced|non-experts?)\b",
    re.I)

_SPHINX_FIELD = re.compile(r"^\s*:(param|type|returns|rtype|raises)\b", re.M)
_GOOGLE_SECTION = re.compile(r"^\s*(Args|Returns|Raises|Attributes|Yields):\s*$", re.M)
_NUMPY_SECTION = re.compile(
    r"^\s*(Parameters|Returns|Raises|Examples|References|See Also|Yields|Notes)\s*\n\s*-{3,}\s*$",
    re.M)

_ROLE = re.compile(r":(?P<role>[a-zA-Z:+-]+):`(?P<target>[^`]+)`")
_ANY_URL = re.compile(r"https?://\S+")
_ASTROPY_DOC_URL = re.compile(r"https?://docs\.astropy\.org/\S*")
#: A link that names the development version, in a URL path or in a role target.
_DEV_VERSION = re.compile(r"(?:^|[/:])(latest|dev|devdocs)(?:/|$|\b)")
_CITATION_HINT = re.compile(r"\b(doi|arXiv|bibcode|ADS|et al\.?|\d{4}(?:A&A|ApJ|MNRAS))\b",
                            re.I)


# --- shared selection -------------------------------------------------------------------


def _keep_links(text: str) -> str:
    """Prose with roles and inline literals removed but hyperlink text left in place.

    ``strip_markup`` drops a whole reST hyperlink construct, which is exactly what C151
    needs to see: the acronym it is about lives inside the link text.
    """
    without_roles = re.sub(r":[a-zA-Z:+-]+:`[^`]+`", " ", text)
    return re.sub(r"``[^`]*``", " ", without_roles)


def _authored(bundle: EvidenceBundle, path: str) -> frozenset[int]:
    change = bundle.files.get(path)
    return change.authored_lines if change else frozenset()


def _owned_docstrings(bundle: EvidenceBundle) -> list[tuple[str, str, pa.Docstring]]:
    """(path, module path, docstring) for each docstring the agent wrote or edited."""
    out = []
    for path, module in modules(bundle):
        for doc in module.docstrings:
            if own.owns_span(bundle, path, doc.span(), "touched"):
                out.append((path, module, doc))
    return out


def _definitions(module: pa.PyModule) -> Iterator[tuple[str, ast.AST, tuple[int, int]]]:
    """(kind, node, span) for every class, function and method in a module."""
    for node in ast.walk(module.tree):
        if isinstance(node, ast.ClassDef):
            yield "class", node, pa.span_of(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield "function", node, pa.span_of(node)


def _own_lines(node: ast.AST, span: tuple[int, int]) -> set[int]:
    """A definition's own lines: its span minus anything nested inside it.

    Without this, editing one method of a 900-line class would make the agent the owner of
    the class's docstring, which it plainly is not.
    """
    lines = set(range(span[0], span[1] + 1))
    for child in ast.walk(node):
        if child is node or not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                                   ast.ClassDef)):
            continue
        start, end = pa.span_of(child)
        lines -= set(range(start, end + 1))
    return lines


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def _new_public_definitions(bundle: EvidenceBundle):
    """(path, module, kind, node, span) for each public definition the agent added."""
    for path, module in modules(bundle):
        if not is_source_path(path):
            continue
        for kind, node, span in _definitions(module):
            if _is_public(node.name) and own.owns_span(bundle, path, span, "created"):
                yield path, module, kind, node, span


def _doc_file_lines(bundle: EvidenceBundle):
    """(path, change, all lines) for each documentation page the agent changed."""
    for path, change in owned_files(bundle, is_doc_path):
        if change.head_text is None:
            continue
        yield path, change, [(n, line) for n, line
                             in enumerate(change.head_text.split("\n"), start=1)]


def _added_doc_lines(bundle: EvidenceBundle):
    """Every line the agent added to a documentation page, markup included."""
    for path in documentation_files(bundle):
        for lineno, text in added_lines(bundle, path):
            yield path, lineno, text


# =========================================================================== docstrings


@rule(
    id="ASTROPY-C085",
    category=CATEGORY,
    ownership="enclosing",  # spec §4.1 -- the target is the definition the agent modified,
                            # not the modification; the definition itself is not new
    reads=("files",),  # spec §5: the docstring is in the patch
)
class PublicDefinitionsHaveDocstrings:
    """Pre-condition: each public class, method and function the agent's edit reaches.
    Pass condition: it carries a docstring.

    Not heuristic: *public* is decided by the leading underscore convention the project
    uses, and presence of a docstring is read off the syntax tree. Both are exact.

    ``enclosing`` rather than ``touched``: the thing judged is the definition, which the
    agent did not create, and the edit that makes it answerable is somewhere inside it.
    Ownership is decided on the definition's **own** lines -- its span minus anything
    nested in it -- so editing one method does not make the agent answerable for its
    class's docstring.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b):
            if not is_source_path(path):
                continue
            modified = b.files[path].modified_lines
            for kind, node, span in _definitions(module):
                if not _is_public(node.name):
                    continue
                if not (_own_lines(node, span) & modified):
                    continue
                out.append(target(f"docstring:{path}:{node.lineno}", path, span,
                                  (path, kind, node.name, node.lineno,
                                   ast.get_docstring(node)), f"{kind} {node.name}"))
        return out

    def pass_condition(self, t: Target):
        path, kind, name, lineno, docstring = t.payload
        if docstring and docstring.strip():
            return Satisfied(f"{path}:{lineno} public {kind} `{name}` has a docstring")
        return Violated(f"{path}:{lineno} public {kind} `{name}` has no docstring")


@rule(
    id="ASTROPY-C219",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier; editing a docstring makes
                          # the agent answerable for its form
    reads=("files",),  # spec §5
    heuristic=True,
)
class DocstringsUseNumpydocFormat:
    """Pre-condition: each docstring the agent wrote or edited.
    Pass condition: it carries no section header belonging to a competing format.

    Heuristic on the **pass condition** (§6.2), graded one-sidedly. A docstring with no
    sections at all is perfectly numpydoc-compatible, so confirming the format is not
    possible; a reST field list or a Google ``Args:`` header is positive evidence of the
    wrong one. Where a numpydoc section *is* present that is reported as satisfying, which
    is stronger evidence than mere absence.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"numpydoc:{path}:{doc.lineno}", path, doc.span(), (path, doc),
                       doc.text.strip().split("\n")[0][:80])
                for path, _, doc in _owned_docstrings(b) if doc.text.strip()]

    def pass_condition(self, t: Target):
        path, doc = t.payload
        if match := _SPHINX_FIELD.search(doc.text):
            return Violated(f"{path}:{doc.lineno} uses a reST field list "
                            f"(`{match.group(0).strip()}`), not the numpydoc format")
        if match := _GOOGLE_SECTION.search(doc.text):
            return Violated(f"{path}:{doc.lineno} uses a Google-style section "
                            f"(`{match.group(1)}:`), not the numpydoc format")
        if match := _NUMPY_SECTION.search(doc.text):
            return Satisfied(f"{path}:{doc.lineno} uses a numpydoc `{match.group(1)}` "
                             f"section")
        return Satisfied(f"{path}:{doc.lineno} carries no competing format marker")


@rule(
    id="ASTROPY-C206",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the six sub-questions are a review checklist for
                          # code the agent contributed, not for docstrings it edited
    reads=("files",),  # spec §5
    heuristic=True,
)
class NewFunctionsCarryAFullNumpydocDocstring:
    """Pre-condition: each public function the agent added to library code.
    Pass condition: its docstring has a summary, an ``Examples`` section, and the sections
    its signature calls for -- ``Parameters`` when it takes arguments, ``Returns`` when it
    returns a value, ``Raises`` when it raises.

    Heuristic on the **pass condition** (§6.2). Section presence stands in for the
    checklist's six questions: whether a ``Parameters`` section really describes *the format
    of the inputs* is not decidable from a header. The sixth question -- references to the
    original algorithm -- is left to C190, which is the rule about exactly that; grading it
    here as well would fail the same omission twice (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, kind, node, span in _new_public_definitions(b):
            if kind != "function":
                continue
            out.append(target(f"numpydoc-full:{path}:{node.lineno}", path, span,
                              (path, node), node.name))
        return out

    def pass_condition(self, t: Target):
        path, node = t.payload
        text = ast.get_docstring(node) or ""
        if not text.strip():
            return Violated(f"{path}:{node.lineno} `{node.name}` has no docstring to "
                            f"describe what it does")
        lines = tuple((n, line) for n, line in enumerate(text.split("\n"), start=1))
        doc = dsx.parse(lines)
        required = ["Examples"]
        arguments = [a.arg for a in node.args.args + node.args.kwonlyargs
                     if a.arg not in ("self", "cls")]
        if arguments:
            required.append("Parameters")
        if any(isinstance(n, ast.Return) and n.value is not None
               for n in ast.walk(node)):
            required.append("Returns")
        if any(isinstance(n, ast.Raise) for n in ast.walk(node)):
            required.append("Raises")
        missing = [name for name in required if not doc.has(name)]
        if missing:
            return Violated(f"{path}:{node.lineno} `{node.name}` documents nothing under "
                            f"{', '.join(missing)}")
        return Satisfied(f"{path}:{node.lineno} `{node.name}` documents "
                         f"{', '.join(required)}")


@rule(
    id="ASTROPY-C190",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the algorithm the agent implemented is new code
    reads=("files",),  # spec §5
    heuristic=True,
)
class ImplementedAlgorithmsCiteTheirSource:
    """Pre-condition: each public function the agent added to library code, read as an
    implemented algorithm.
    Pass condition: its docstring names an origin -- a ``References`` section, a citation,
    a DOI or a URL.

    Heuristic on **both layers** (§6.1). *An algorithm you implement* is approximated by a
    new public function, which over-fires on plumbing that implements no algorithm at all.
    And "cites the origin source" is approximated by the forms a citation takes, so a
    reference written as bare prose -- "following the method of Smith" -- reads as missing.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"citation:{path}:{node.lineno}", path, span, (path, node),
                       node.name)
                for path, module, kind, node, span in _new_public_definitions(b)
                if kind == "function"]

    def pass_condition(self, t: Target):
        path, node = t.payload
        text = ast.get_docstring(node) or ""
        lines = tuple((n, line) for n, line in enumerate(text.split("\n"), start=1))
        if text.strip() and dsx.parse(lines).has("References"):
            return Satisfied(f"{path}:{node.lineno} `{node.name}` has a References section")
        if rst.dois(text) or rst.urls(text) or _CITATION_HINT.search(text):
            return Satisfied(f"{path}:{node.lineno} `{node.name}` cites a source in its "
                             f"docstring")
        return Violated(f"{path}:{node.lineno} `{node.name}` cites no origin source for "
                        f"the algorithm it implements")


@rule(
    id="ASTROPY-C220",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier
    reads=("files",),  # spec §5
    heuristic=True,
)
class DocstringCrossReferencesUseIntersphinx:
    """Pre-condition: each cross-reference the agent wrote in a docstring, in either form
    -- a Sphinx role, or a URL into the documentation.
    Pass condition: it is a role rather than a URL.

    Links to the *development* version are excluded: C221 makes a direct URL the right form
    for those, and grading them here would have the two rules contradict each other on one
    line (§7.5). A no-target test pins the exclusion.

    Heuristic on the **pre-condition** (§6.3): "a cross-reference" is approximated by these
    two spellings, and a reference written some third way is not selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _, doc in _owned_docstrings(b):
            for lineno, text in doc.lines():
                for match in _ROLE.finditer(text):
                    out.append(target(f"xref:{path}:{lineno}:{match.start()}", path,
                                      (lineno, lineno), (path, lineno, "role",
                                                         match.group(0)), text.strip()))
                for match in _ASTROPY_DOC_URL.finditer(text):
                    if _DEV_VERSION.search(match.group(0)):
                        continue  # C221 asks for a direct URL here
                    out.append(target(f"xref:{path}:{lineno}:{match.start()}", path,
                                      (lineno, lineno), (path, lineno, "url",
                                                         match.group(0)), text.strip()))
        return out

    def pass_condition(self, t: Target):
        path, lineno, kind, written = t.payload
        if kind == "role":
            return Satisfied(f"{path}:{lineno} cross-references with `{written}`")
        return Violated(f"{path}:{lineno} links into the documentation with the URL "
                        f"{written} rather than an intersphinx role")


@rule(
    id="ASTROPY-C221",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a line the agent wrote
    reads=("files",),  # spec §5
    heuristic=True,
)
class DevelopmentVersionLinksAreDirectUrls:
    """Pre-condition: each link the agent wrote that points at the development version of
    the documentation, in either form.
    Pass condition: it is a direct URL.

    Heuristic on the **pre-condition** (§6.3): *linking to the development version* is
    approximated by the link naming ``latest`` or ``dev``, which is how those URLs and
    roles are spelled. A role that resolves to the development version without saying so is
    not selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        sources = [(path, lineno, text) for path, lineno, text in prose_lines(b)]
        sources += [(path, lineno, text) for path, lineno, text in _added_doc_lines(b)]
        seen = set()
        for path, lineno, text in sources:
            if (path, lineno) in seen:
                continue
            seen.add((path, lineno))
            for match in _ROLE.finditer(text):
                if _DEV_VERSION.search(match.group("target")):
                    out.append(target(f"devlink:{path}:{lineno}:{match.start()}", path,
                                      (lineno, lineno),
                                      (path, lineno, "role", match.group(0)), text.strip()))
            for match in _ANY_URL.finditer(text):
                if _DEV_VERSION.search(match.group(0)):
                    out.append(target(f"devlink:{path}:{lineno}:{match.start()}", path,
                                      (lineno, lineno),
                                      (path, lineno, "url", match.group(0)), text.strip()))
        return out

    def pass_condition(self, t: Target):
        path, lineno, kind, written = t.payload
        if kind == "url":
            return Satisfied(f"{path}:{lineno} links to the development documentation with "
                             f"a direct URL")
        return Violated(f"{path}:{lineno} links to the development documentation with the "
                        f"role `{written}` rather than a direct URL")


# =========================================================================== style guide


@rule(
    id="ASTROPY-C146",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a line the agent wrote
    reads=("files",),  # spec §5
    heuristic=True,
)
class AbbreviationsSitInParenthesesWithAComma:
    """Pre-condition: each written line using ``i.e.`` or ``e.g.``.
    Pass condition: each use opens a parenthetical and is followed by a comma.

    Heuristic on the **pass condition** (§6.2): "within parentheses" is checked by looking
    for the opening bracket immediately before the abbreviation, which misses a
    parenthetical that opens earlier in the sentence and reports it as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return prose_line_targets(b, "abbreviation",
                                  lambda text: _ABBREVIATION.search(strip_markup(text)))

    def pass_condition(self, t: Target):
        text = strip_markup(t.payload)
        for match in _ABBREVIATION.finditer(text):
            before = text[:match.start()].rstrip()
            after = text[match.end():]
            if not before.endswith("("):
                return Violated(f"`{match.group(0)}` is not inside parentheses: "
                                f"{t.payload.strip()[:70]!r}")
            if not after.startswith(","):
                return Violated(f"`{match.group(0)}` is not followed by a comma: "
                                f"{t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C151",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class OrganizationAcronymsAreHyperlinked:
    """Pre-condition: each written line naming what looks like an organization by its
    acronym.
    Pass condition: the line hyperlinks it.

    Heuristic on **both layers** (§6.1). An organization acronym cannot be told from any
    other capitalised abbreviation, so the pre-condition selects runs of capitals and
    excludes a list of formats, protocols and concepts astropy's prose is full of -- FITS,
    WCS, HDU, API. The list cannot be complete, so the check both over- and under-fires.
    The grading is looser still: any hyperlink on the line counts, not specifically one
    around the acronym.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        def names_an_acronym(text: str) -> bool:
            return any(m.group(1) not in _NOT_ORGANIZATIONS
                       for m in _ACRONYM.finditer(_keep_links(text)))

        return prose_line_targets(b, "acronym", names_an_acronym)

    def pass_condition(self, t: Target):
        text = t.payload
        acronyms = [m.group(1) for m in _ACRONYM.finditer(_keep_links(text))
                    if m.group(1) not in _NOT_ORGANIZATIONS]
        if rst.urls(text) or "`_" in text:
            return Satisfied(f"{acronyms[0]} is written with a hyperlink")
        return Violated(f"the acronym {acronyms[0]} is written with no hyperlink to a "
                        f"reference: {text.strip()[:70]!r}")


@rule(
    id="ASTROPY-C152",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class CodeNamesAreLowercaseInDoubleBackticks:
    """Pre-condition: each written line naming a package or code name, in any casing and
    with or without markup.
    Pass condition: every such name is lowercase inside double backticks.

    The word *astropy* is deliberately outside this rule's vocabulary: C153 legislates its
    two spellings, and grading it here as well would have the two rules disagree on
    "Astropy" (§7.5). A no-target test pins that.

    Heuristic on the **pre-condition** (§6.3): the rule's antecedent is *a proper noun or a
    code name*, and only the second half is enumerable. The check therefore says nothing
    about proper nouns generally and grades the package names astropy's documentation
    actually uses.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return prose_line_targets(b, "code-name",
                                  lambda text: _CODE_NAME_ANY.search(text))

    def pass_condition(self, t: Target):
        text = t.payload
        for match in _CODE_NAME_ANY.finditer(text):
            name = match.group(1)
            before = text[max(0, match.start() - 2):match.start()]
            after = text[match.end():match.end() + 2]
            if before.endswith("``") and after.startswith("``"):
                if name.islower():
                    continue
                return Violated(f"``{name}`` should be lowercase: {text.strip()[:70]!r}")
            return Violated(f"the code name {name!r} is not written in double backticks: "
                            f"{text.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C153",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class AstropyIsSpelledForWhatItMeans:
    """Pre-condition: each written line mentioning astropy, in any spelling.
    Pass condition: the mention is ``astropy`` in lowercase double backticks, or Astropy
    capitalised in plain prose.

    Heuristic on the **pass condition** (§6.2): the rule ties each spelling to a meaning --
    the core package against the Project -- and which one a sentence means is not
    mechanically decidable. What is graded is that the spelling is one of the two sanctioned
    forms, so a sentence about the Project written as ``astropy`` passes here and should
    not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        def mentions(text: str) -> bool:
            return bool(_ASTROPY_ANY.search(re.sub(r":[a-zA-Z:+-]+:`[^`]+`", " ", text)))

        return prose_line_targets(b, "astropy-name", mentions)

    def pass_condition(self, t: Target):
        text = re.sub(r":[a-zA-Z:+-]+:`[^`]+`", " ", t.payload)
        for match in _ASTROPY_ANY.finditer(text):
            written = match.group(1)
            if written == "``astropy``" or written == "Astropy":
                continue
            if written == "`astropy`":
                return Violated(f"`astropy` uses single backticks; the core package is "
                                f"``astropy``: {t.payload.strip()[:70]!r}")
            return Violated(f"bare lowercase {written!r} outside double backticks: "
                            f"{t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C156",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class NoContractionsInDocumentation:
    """Pre-condition: each line of documentation prose the agent wrote.
    Pass condition: it uses no contraction.

    A prohibition, so the pre-condition selects the permitted form as well as the forbidden
    one (§7.1): every prose line is judged, and a line with no contraction records a pass.

    Heuristic on the **pass condition** (§6.2): the list of contractions is necessarily
    partial, and a contraction inside quoted example output is the example's, not the
    documentation's.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return prose_line_targets(b, "contraction", lambda text: True)

    def pass_condition(self, t: Target):
        if match := _CONTRACTION.search(strip_markup(t.payload)):
            return Violated(f"contraction {match.group(0)!r}: {t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C160",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class NumbersWithUnitsAreNumerals:
    """Pre-condition: each written line stating a quantity -- a number, spelled out or not,
    followed by a unit.
    Pass condition: the number is written as a numeral.

    Selecting on *the quantity* rather than on the spelled-out form is what lets "1
    arcminute" record a pass (§7.1).

    Heuristic on the **pre-condition** (§6.3): "followed by a unit or part of a name" is
    approximated by a list of the units astropy's documentation uses; the *part of a name*
    half -- "Gaia data release 2" -- is not detected at all, so the check under-fires there.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return prose_line_targets(b, "unit-number",
                                  lambda text: _NUMBER_WITH_UNIT.search(strip_markup(text)))

    def pass_condition(self, t: Target):
        text = strip_markup(t.payload)
        for match in _NUMBER_WITH_UNIT.finditer(text):
            value = match.group("value")
            if not value[0].isdigit():
                return Violated(f"{value!r} is followed by the unit "
                                f"{match.group('unit')!r} and should be a numeral: "
                                f"{t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C161",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class SmallNumbersAreSpelledOut:
    """Pre-condition: each written line stating a whole number that is not followed by a
    unit, in either form.
    Pass condition: one through nine are spelled out and 10 upwards are numerals.

    Numbers followed by a unit are excluded and left to C160, which requires the opposite
    form for them; without that exclusion the two rules would contradict each other on "1
    arcminute" (§7.5). Lines using a numeral-word combination -- "2 billion stars" -- are
    excluded too, because the sentence sanctions that form explicitly.

    Heuristic on the **pre-condition** (§6.3): version strings, identifiers and casual
    expressions are hard to tell from whole numbers, and the source's own exception --
    "for casual expressions, spell out the number" -- is not detectable at all.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        def states_a_number(text: str) -> bool:
            prose = strip_markup(text)
            if _SCALE_WORD.search(prose):
                return False
            spans = [m.span() for m in _NUMBER_WITH_UNIT.finditer(prose)]
            for match in _BARE_NUMBER.finditer(prose):
                if not any(lo <= match.start() < hi for lo, hi in spans):
                    return True
            return False

        return prose_line_targets(b, "number", states_a_number)

    def pass_condition(self, t: Target):
        prose = strip_markup(t.payload)
        spans = [m.span() for m in _NUMBER_WITH_UNIT.finditer(prose)]
        for match in _BARE_NUMBER.finditer(prose):
            if any(lo <= match.start() < hi for lo, hi in spans):
                continue
            written = match.group("value")
            if written[0].isdigit():
                if int(written) < 10:
                    return Violated(f"{written!r} is below ten and should be spelled out: "
                                    f"{t.payload.strip()[:70]!r}")
            else:
                value = _NUMBER_WORDS[written.lower()]
                if value >= 10:
                    return Violated(f"{written!r} is ten or more and should be a numeral: "
                                    f"{t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C164",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class ParentheticalPunctuationGoesInside:
    """Pre-condition: each written line containing a parenthetical.
    Pass condition: where the parenthetical is a sentence of its own, its full stop is
    inside the closing bracket.

    Heuristic on the **pass condition** (§6.2), and narrowed to the one case the sentence's
    two exceptions leave decidable. A parenthetical *inside* another sentence keeps its
    period outside, and a comma after one is explicitly allowed, so only a stand-alone
    parenthetical -- one that opens the sentence -- is graded.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return prose_line_targets(b, "parenthetical",
                                  lambda text: _PARENTHETICAL.search(strip_markup(text)))

    def pass_condition(self, t: Target):
        text = strip_markup(t.payload).strip()
        for match in _PARENTHETICAL.finditer(text):
            standalone = match.start() == 0
            inner = match.group(1).strip()
            after = text[match.end():match.end() + 1]
            if standalone and after == "." and not inner.endswith((".", "!", "?")):
                return Violated(f"the stand-alone parenthetical ends its sentence outside "
                                f"the bracket: {t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C165",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class PunctuationGoesInsideQuotationMarks:
    """Pre-condition: each written line containing a quoted span.
    Pass condition: no period or comma follows the closing quotation mark.

    Heuristic on the **pre-condition** (§6.3): a double quote in astropy's documentation is
    as often a string literal in prose as it is a quotation, and the check cannot tell them
    apart. Inline literals are stripped first, which removes the commonest of those.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return prose_line_targets(b, "quotation",
                                  lambda text: _QUOTED.search(strip_markup(text)))

    def pass_condition(self, t: Target):
        text = strip_markup(t.payload)
        if match := _QUOTE_THEN_PUNCTUATION.search(text):
            return Violated(f"{match.group(0)!r} puts the punctuation outside the closing "
                            f"quotation mark: {t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C166",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class NumberRangesUseAnUnspacedEnDash:
    """Pre-condition: each written line stating a number range, however it is written.
    Pass condition: the range uses an unspaced en dash.

    Selecting every range, rather than the hyphenated ones, is what lets "chapters
    14–18" record a pass (§7.1).

    Heuristic on the **pre-condition** (§6.3): two numbers separated by a hyphen are also
    how a version, an identifier or a date fragment is written, and the check cannot tell
    those from a range.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return prose_line_targets(b, "range",
                                  lambda text: _NUMBER_RANGE.search(strip_markup(text)))

    def pass_condition(self, t: Target):
        text = strip_markup(t.payload)
        for match in _NUMBER_RANGE.finditer(text):
            written = match.group(0)
            if _EN_DASH in written and not re.search(rf"\s{_EN_DASH}|{_EN_DASH}\s", written):
                continue
            return Violated(f"{written!r} is a number range written without an unspaced "
                            f"en dash: {t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C167",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
)
class EmDashesAreSpaced:
    """Pre-condition: each written line using an em dash.
    Pass condition: it has a space on either side.

    Not heuristic: the character is exact, the spacing is exact, and both are read off the
    line. The source's permission -- an em dash "can be used" -- governs whether to use one
    at all, which is why the pre-condition fires on the use and not on the absence.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return prose_line_targets(b, "em-dash",
                                  lambda text: _EM_DASH in strip_markup(text))

    def pass_condition(self, t: Target):
        text = strip_markup(t.payload)
        for match in _EM_DASH_USE.finditer(text):
            before = text[match.start() - 1:match.start()]
            after = text[match.end():match.end() + 1]
            if before != " " or after != " ":
                return Violated(f"the em dash is not spaced on both sides: "
                                f"{t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C168",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class SpellingIsAmerican:
    """Pre-condition: each written line containing a word that has both a British and an
    American spelling, in either form.
    Pass condition: it is the American one.

    Selecting on the alternation rather than on the British spelling is what lets "catalog"
    record a pass (§7.1).

    Heuristic on the **pass condition** (§6.2): the word list is necessarily partial, so a
    British spelling outside it passes, and a word that only looks British -- a surname, a
    quoted string -- is reported.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        def alternating(text: str) -> bool:
            words = {w.lower() for w in _SPELLING_WORD.findall(strip_markup(text))}
            return bool(words & (set(_BRITISH) | _AMERICAN))

        return prose_line_targets(b, "spelling", alternating)

    def pass_condition(self, t: Target):
        for word in _SPELLING_WORD.findall(strip_markup(t.payload)):
            if word.lower() in _BRITISH:
                return Violated(f"British spelling {word!r}; astropy uses "
                                f"{_BRITISH[word.lower()]!r}: {t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C169",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class ExactTimesUseTheTwentyFourHourClock:
    """Pre-condition: each written line stating an exact time, in either system.
    Pass condition: it is numerals on the 24-hour clock.

    Heuristic on the **pre-condition** (§6.3): a bare ``12:30`` is also how a duration or a
    coordinate is written, and "3 pm" is recognised only in the spellings the pattern
    knows. Selecting only the a.m./p.m. form would make every target a violation (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        def states_a_time(text: str) -> bool:
            prose = strip_markup(text)
            return bool(_TIME.search(prose) or _ISO_TIME.search(prose))

        return prose_line_targets(b, "time", states_a_time)

    def pass_condition(self, t: Target):
        prose = strip_markup(t.payload)
        if match := _TIME.search(prose):
            return Violated(f"{match.group(0)!r} states a time on the 12-hour clock: "
                            f"{t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C170",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class SpecificDatesAreIso8601:
    """Pre-condition: each written line stating a specific date, in any format.
    Pass condition: it is written year-month-day.

    Heuristic on the **pre-condition** (§6.3): the alternative formats are recognised from
    a list of spellings -- a month name with a year, or a slashed numeric date -- so a date
    written some other way is not selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        def states_a_date(text: str) -> bool:
            prose = strip_markup(text)
            return bool(_ISO_DATE.search(prose) or _WORD_DATE.search(prose))

        return prose_line_targets(b, "date", states_a_date)

    def pass_condition(self, t: Target):
        prose = strip_markup(t.payload)
        if match := _WORD_DATE.search(prose):
            return Violated(f"{match.group(0)!r} is not ISO 8601 year-month-day: "
                            f"{t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C172",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class FirstPersonIsInclusivePlural:
    """Pre-condition: each written line using a first-person pronoun, singular or plural.
    Pass condition: it is the inclusive plural -- we, us, our.

    Heuristic on the **pre-condition** (§6.3): "I" is also a variable, a matrix and a Roman
    numeral, and inline literals are stripped before the search to remove most of those.
    Selecting only the singular would make every target a violation (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return prose_line_targets(b, "voice",
                                  lambda text: _FIRST_PERSON.search(strip_markup(text)))

    def pass_condition(self, t: Target):
        if match := _FIRST_PERSON_SINGULAR.search(strip_markup(t.payload)):
            return Violated(f"first-person singular {match.group(0)!r} where the inclusive "
                            f"plural belongs: {t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C173",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class GenericPronounIsYou:
    """Pre-condition: each written line using a generic pronoun, in either form.
    Pass condition: it is "you".

    The generic "one" is recognised by the verb that follows it, because "one" is far more
    often the number. Selecting only lines containing "one" would make every target a
    violation and could never record a compliant line (§7.1), which is why "you" is in the
    pre-condition too.

    Heuristic on the **pre-condition** (§6.3): the verb list is partial, so a generic "one"
    followed by something else is missed.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        def generic_pronoun(text: str) -> bool:
            prose = strip_markup(text)
            return bool(_GENERIC_ONE.search(prose) or _GENERIC_YOU.search(prose))

        return prose_line_targets(b, "pronoun", generic_pronoun)

    def pass_condition(self, t: Target):
        prose = strip_markup(t.payload)
        if match := _GENERIC_ONE.search(prose):
            return Violated(f"generic {match.group(0)!r} where \"you\" belongs: "
                            f"{t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C174",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class NoBelittlingWords:
    """Pre-condition: each line of documentation prose the agent wrote.
    Pass condition: it uses none of the belittling words the style guide names.

    A prohibition with a closed list, so the grading is a lookup rather than a judgement.
    Heuristic all the same (§6.6): "just" and "clearly" have senses that belittle nobody --
    "just below the header" -- and the check cannot tell which sense is meant.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return prose_line_targets(b, "belittling", lambda text: True)

    def pass_condition(self, t: Target):
        if match := _BELITTLING.search(strip_markup(t.payload)):
            return Violated(f"belittling word {match.group(0)!r}: "
                            f"{t.payload.strip()[:70]!r}")
        return Satisfied()


@rule(
    id="ASTROPY-C177",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the directive is a line the agent wrote
    reads=("files",),  # spec §5
    heuristic=True,
)
class WarningsNoteLimitationsInTheCode:
    """Pre-condition: each ``.. warning::`` directive the agent added to the documentation.
    Pass condition: its text does not address the reader's skill or knowledge.

    Heuristic on the **pass condition** (§6.2): "a limitation in the code" against "an
    implied limitation in the reader" is a distinction about meaning, approximated by the
    vocabulary reader-directed warnings use. A condescending warning phrased outside that
    vocabulary passes.

    Selected separately from the other prose rules because a directive line is markup, and
    ``prose_lines`` filters markup out.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, change, lines in _doc_file_lines(b):
            authored = change.authored_lines
            for index, (lineno, text) in enumerate(lines):
                if not _WARNING_DIRECTIVE.match(text) or lineno not in authored:
                    continue
                body = " ".join(line for _, line in lines[index + 1:index + 8])
                out.append(target(f"warning:{path}:{lineno}", path, (lineno, lineno),
                                  (path, lineno, body), text.strip()))
        return out

    def pass_condition(self, t: Target):
        path, lineno, body = t.payload
        if match := _READER_DIRECTED.search(body):
            return Violated(f"{path}:{lineno} the warning addresses the reader "
                            f"({match.group(0)!r}) rather than a limitation in the code")
        return Satisfied(f"{path}:{lineno} the warning notes a limitation in the code")


@rule(
    id="ASTROPY-C179",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the heading is a line the agent wrote
    reads=("files",),  # spec §5
)
class HeadingUnderlinesMatchTheirText:
    """Pre-condition: each reStructuredText heading the agent wrote in a documentation
    page.
    Pass condition: its underline is exactly as long as the heading text.

    Not heuristic: both lengths are counted off the file. The file's whole text is read
    rather than the diff, because an underline three lines of context away is still the
    underline; ownership is then narrowed back to headings the agent actually wrote.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, change, lines in _doc_file_lines(b):
            authored = change.authored_lines
            for heading in rst.headings(lines):
                if not ({heading.lineno, heading.underline_lineno} & authored):
                    continue
                out.append(target(f"heading:{path}:{heading.lineno}", path,
                                  (heading.lineno, heading.underline_lineno),
                                  (path, heading), heading.text.strip()))
        return out

    def pass_condition(self, t: Target):
        path, heading = t.payload
        text_length = len(heading.text.rstrip())
        underline_length = len(heading.underline.rstrip())
        if text_length != underline_length:
            return Violated(f"{path}:{heading.underline_lineno} the underline is "
                            f"{underline_length} characters for a {text_length}-character "
                            f"heading: {heading.text.strip()[:50]!r}")
        return Satisfied(f"{path}:{heading.lineno} the underline matches the heading text")


@rule(
    id="ASTROPY-C185",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the new functionality is what the agent added
    reads=("files",),  # spec §5: the narrative pages are in the patch
    heuristic=True,
)
class NewFunctionalityIsDescribedInTheNarrativeDocs:
    """Pre-condition: the contribution adds a public function or class to library code,
    which is what adding new functionality looks like.
    Pass condition: it also changes a page under ``docs/``.

    Heuristic on **both layers** (§6.1). *New functionality* is approximated by a new
    public definition, which over-fires on a refactor that merely renames one and
    under-fires on a new keyword argument to an existing function. And "a description in
    the main documentation" is approximated by any change under ``docs/``, which does not
    check that the change describes the new thing.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        added = [(path, node.name) for path, _, _, node, _ in _new_public_definitions(b)]
        if not added:
            return []
        return [target(f"narrative-doc:{b.instance_id}", added[0][0], None, (b, added),
                       f"{len(added)} new public definition(s), e.g. {added[0][1]}")]

    def pass_condition(self, t: Target):
        bundle, added = t.payload
        pages = documentation_files(bundle)
        if pages:
            return Satisfied(f"the contribution describes it in {pages[0]}")
        return Violated(f"`{added[0][1]}` is new public functionality and no page under "
                        f"{DOC_ROOT} is changed to describe it")

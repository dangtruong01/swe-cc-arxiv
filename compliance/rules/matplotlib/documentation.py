"""matplotlib: Documentation and docstrings -- 80 rules, the largest category in the pack.

Layer C. Every rule is two layers (`docs/checker-authoring.md` §2): ``precondition``
selects on the rule's ANTECEDENT, ``pass_condition`` grades.

Four families, and their evidence differs.

* **reStructuredText pages** (C001--C021, C140--C142, C276) read pages under
  :file:`doc/` through ``extractors/rst``.
* **Docstrings** (C023--C047, C145, C158, C159, C219--C234, C248) read docstrings the
  agent wrote or edited through ``extractors/python_ast`` and ``extractors/docstrings``.
  None of these sentences carries a newness qualifier unless it says *new*, so most are
  ``touched`` per §4.3 -- editing a docstring makes the agent answerable for its form.
* **Gallery examples and plot types** (C049--C075, C136--C138, C272, C277--C283) read the
  executable sources under :file:`galleries/`.
* **Expository language** (C126--C131) reads prose, through ``_common.prose_lines``.

**Nine §7.5 narrowings, every one pinned by a no-target test.** They are listed here
because a reader checking the pack for double-counting should not have to find them:

#. **C006 / C007 / C008** partition by markup form. C006 takes parameter mentions that are
   bare or emphasised and asks for emphasis; C007 takes default-role spans and C008
   double-backtick literals, each asking whether what is marked up is a parameter at all.
   No mention is graded by two of them.
#. **C003 / C004** partition by adornment. C004 owns ``#``; C003 skips it.
#. **C013 / C014** -- C014 fires only on labels whose form C013 already accepts, so a
   malformed label is one violation.
#. **C025 / C158** would otherwise contradict: one forbids putting API reference material
   in a :file:`doc/api` page, the other requires an API page for a new module. C025
   excludes contributions that add a module, which is what C158 is about.
#. **C033 / C034** split by section: parameter types are C033's, return types C034's.
#. **C039 / C041** -- C039 skips parameters whose default is ``None``, the case C041
   legislates.
#. **C047 / C145** would otherwise contradict: an inherited docstring is *absent* by
   design. C145 accepts the ``# docstring inherited`` marker as satisfying it.
#. **C221 / C222 / C223** partition versioning directives by where they sit: prose pages,
   a docstring outside its Parameters section, and inside it.
#. **C141 / C142** -- C142 owns Markdown tables and ``csv-table``; C141 fires only on
   tables that are neither, and asks whether they are ASCII tables.
#. **C127 / C129** split prose sentences: a directive sentence is C127's, an explanatory
   one C129's.
#. **C051 / C052 / C053** split sample data three ways: citing a public dataset, writing
   it inline, and where an inlinable-no-longer file goes.
#. **C054 / C056** -- C056 fires only where the References admonition C054 asks for
   already exists.
#. **C280 / C281** -- C281 fires only on tags that already carry a subcategory.

**Corpus mismatches, recorded rather than corrected in the workbook (§0).**

* C001 names the *generated* pages -- :file:`doc/gallery`, :file:`doc/tutorials` -- while
  the tree carries the sources under :file:`galleries/`. It is coded against the paths its
  own sentence names, which is also the correct reading: the generated pages are what must
  not be edited. See ``_common``'s module docstring.
* C020 is filed ``differential`` and is decidable from the patch: a page that moved shows
  as a deletion or a rename in the diff, and the redirect is a directive in it.
"""

from __future__ import annotations

import ast
import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import docstrings as ds
from compliance.rules.matplotlib._common import (API_CHANGE_ROOT, DOC_ROOT, DOC_SUFFIXES,
                                                 GALLERY_SOURCE_ROOTS, PLOT_TYPES_ROOTS,
                                                 ParamEntry, added_lines, added_text,
                                                 doc_pages, gallery_examples,
                                                 is_gallery_path, is_package_path, modules,
                                                 new_public_defs,
                                                 numpydoc, owned_docstrings, page_lines,
                                                 parameter_entries, parameter_names,
                                                 prose_lines, python_files, strip_markup,
                                                 target, titles_of)

CATEGORY = "Documentation and docstrings"

# --- reStructuredText vocabulary ------------------------------------------------------------

#: The five trees C001 forbids editing, and the one exception it names.
GENERATED_DOC_TREES = ("doc/plot_types/", "doc/gallery/", "doc/tutorials/",
                       "doc/users/explain/", "doc/api/")
DOC_TREE_EXCEPTION = "doc/api/api_changes/"

#: The heading adornments, deepest last, as the style guide lists them.
HEADING_LEVELS = ("*", "=", "-", "^", '"')
MAIN_TITLE_ADORNMENT = "#"
INDEX_PAGE = "index.rst"

_ADORNMENT = re.compile(r'^\s*([*=\-^"~+#`\':.])\1{1,}\s*$')
_DIRECTIVE = re.compile(r"^\s*\.\.\s+(?P<name>[\w-]+)::\s*(?P<argument>.*)$")
_LABEL = re.compile(r"^\s*\.\.\s+_(?P<name>[^:]+):\s*$")
_ROLE = re.compile(r":(?P<role>[a-zA-Z:+-]+):`(?P<target>[^`]+)`")
_DEFAULT_ROLE = re.compile(r"(?<![`:\w])`(?!`)(?P<target>[^`\n]+?)`(?!`|_)")
_LITERAL = re.compile(r"``(?P<target>[^`\n]+?)``")
_EMPHASIS = re.compile(r"(?<![*\w])\*(?!\*)(?P<target>[^*\n]+?)\*(?!\*)")
_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")

#: LaTeX that is doing mathematics, which is what C009 and C010 are about.
_INLINE_MATH = re.compile(r"(?<!\$)\$(?!\$)[^$\n]+\$(?!\$)|\\(?:frac|sqrt|alpha|beta|"
                          r"gamma|sigma|sum|int|pi|theta|mathrm|mathbf)\b")
_DISPLAY_MATH = re.compile(r"\$\$|\\begin\{(?:equation|align|eqnarray|gather)\*?\}")
_MATH_ROLE = re.compile(r":math:`")
_MATH_DIRECTIVE = re.compile(r"^\s*\.\.\s+math::")

#: A link to another documentation page written some other way than with `:doc:`.
_PAGE_LINK = re.compile(r"`[^`]*<(?P<t>[^>]*\.(?:rst|html))>`_|(?<![\w/])(?P<p>[\w./-]+"
                        r"\.(?:rst|html))(?![\w/])")

#: A matplotlib code element named in prose.
_MPL_DOTTED = re.compile(r"\b(?:matplotlib|mpl_toolkits)(?:\.[A-Za-z_]\w*)+\b")
#: Names the project defines on both the Axes and the pyplot side, so an abbreviated
#: reference to one of them is ambiguous (C018).
DUAL_API_NAMES = frozenset({
    "plot", "scatter", "bar", "barh", "hist", "hist2d", "boxplot", "violinplot", "pie",
    "imshow", "pcolormesh", "pcolor", "contour", "contourf", "errorbar", "fill_between",
    "stackplot", "step", "stem", "quiver", "streamplot", "text", "annotate", "legend",
    "grid", "axis", "title", "xlabel", "ylabel", "xlim", "ylim", "subplots", "figure",
    "colorbar", "clf", "cla", "close", "show", "savefig",
})

_RC_KEY_IN_PROSE = re.compile(r"rcParams\s*\[\s*[\"'](?P<key>[^\"']+)[\"']\s*\]"
                              r"|(?<![\w.:`])(?P<bare>[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+)"
                              r"(?![\w.`])")
_RC_ROLE = re.compile(r":rc:`")
#: The rcParam namespaces, so a dotted lower-case word is not mistaken for one.
RC_NAMESPACES = ("axes", "figure", "font", "lines", "patch", "text", "xtick", "ytick",
                 "legend", "grid", "savefig", "image", "hatch", "boxplot", "date",
                 "errorbar", "animation", "backend", "keymap", "markers", "mathtext",
                 "pcolor", "pdf", "pgf", "polaraxes", "ps", "scatter", "svg", "webagg")


def _rst_lines(bundle: EvidenceBundle, path: str):
    return page_lines(bundle, path)


def _headings(lines) -> list[tuple[int, str, str]]:
    """(line number, title text, adornment character) for each reST section heading."""
    rows = list(lines)
    out = []
    for index, (number, text) in enumerate(rows):
        if index + 1 >= len(rows) or not text.strip() or _ADORNMENT.match(text):
            continue
        below = rows[index + 1][1]
        if _ADORNMENT.match(below) and len(below.strip()) >= len(text.strip()) - 1:
            out.append((number, text.strip(), below.strip()[0]))
    return out


def _directives(lines, name: str) -> list[tuple[int, str]]:
    out = []
    for number, text in lines:
        match = _DIRECTIVE.match(text)
        if match and match.group("name").lower() == name:
            out.append((number, match.group("argument").strip()))
    return out


def _prose_pages(bundle: EvidenceBundle, *, mode: str = "touched") -> list[str]:
    """Pages a rule about page conventions may grade: reST under `doc/`, minus the
    release-note trees, which are a changelog rather than documentation (§7.5)."""
    return [p for p in doc_pages(bundle, mode=mode)
            if not p.startswith(API_CHANGE_ROOT)]


# --- reStructuredText pages ---------------------------------------------------------------


@rule(
    id="MATPLOTLIB-C001",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the pages existed before the run
    reads=("files",),  # spec §5: the path is the whole question
)
class GeneratedDocumentationPagesAreNotEdited:
    """Pre-condition: each reST page under :file:`doc/` the agent edited.
    Pass condition: it is not in one of the five generated trees, or it is under
    :file:`doc/api/api_changes/`, the exception the sentence names.

    §7.1: a prohibition, so the pre-condition selects *editing a documentation page*, the
    permitted act, and the pass condition asks which tree it was in. Not heuristic (§6.2):
    the five prefixes and the exception are paths the rule states, and the check compares
    against them.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"generated-page:{path}", path, None, path, f"{path} edited")
                for path in doc_pages(b)]

    def pass_condition(self, t: Target):
        path: str = t.payload
        if path.startswith(DOC_TREE_EXCEPTION):
            return Satisfied(f"{path} is under {DOC_TREE_EXCEPTION}, which the rule "
                             f"exempts")
        for tree in GENERATED_DOC_TREES:
            if path.startswith(tree):
                return Violated(f"{path} is a generated page under {tree}; the source it "
                                f"is built from is what should be edited")
        return Satisfied(f"{path} is a hand-written page, not a generated one")


@rule(
    id="MATPLOTLIB-C002",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property every title must have
    reads=("files",),  # spec §5: the title is in the patch
    heuristic=True,
)
class SectionTitlesAreSentenceCase:
    """Pre-condition: each section title the agent wrote on a documentation page.
    Pass condition: only its first word is capitalised.

    Heuristic on the **pass condition** (§6.2): "sentence case" allows proper nouns and
    code names, which cannot be told from title case mechanically, so a word is excused
    only when it is a known project name, an acronym, or carries markup. A title naming an
    unlisted proper noun reads as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _prose_pages(b):
            authored = b.files[path].authored_lines
            for number, text, _char in _headings(_rst_lines(b, path)):
                if number not in authored:
                    continue
                out.append(target(f"title-case:{path}:{number}", path, (number, number),
                                  (path, number, text), text[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, text = t.payload
        words = strip_markup(text).split()
        offenders = [w for w in words[1:]
                     if w[:1].isupper() and not w.isupper()
                     and w.strip(".,:;()").lower() not in ALLOWED_CAPITALS]
        if offenders:
            return Violated(f"{path}:{number} is not sentence case -- "
                            f"{', '.join(offenders[:3])} capitalised mid-title")
        return Satisfied(f"{path}:{number} is written in sentence case")


#: Words a sentence-case title may still capitalise: the project's own names and the
#: proper nouns its pages actually use.
ALLOWED_CAPITALS = frozenset({
    "matplotlib", "python", "numpy", "sphinx", "github", "figure", "axes", "artist",
    "axis", "pyplot", "api", "rst", "restructuredtext", "linux", "macos", "windows",
    "unix", "bsd", "mit", "psf", "gnu", "agg", "qt", "gtk", "tk", "wx", "cairo", "pdf",
    "svg", "png", "eps", "ps", "latex", "tex", "html", "css", "json", "yaml", "toml",
    "i", "matlab", "jupyter", "ipython", "conda", "pip", "meson", "cpython",
})


@rule(
    id="MATPLOTLIB-C003",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of the markup, no newness qualifier
    reads=("files",),  # spec §5: the adornment is in the patch
    heuristic=True,
)
class HeadingsUseTheListedAdornmentForTheirLevel:
    """Pre-condition: each section heading the agent wrote on a documentation page, other
    than one adorned with ``#``.
    Pass condition: its adornment is the character the style guide gives that depth --
    ``*`` for chapters, ``=`` for sections, ``-`` for subsections, ``^`` for
    subsubsections, ``"`` for paragraphs.

    ``#`` is excluded and left to C004, which is the rule about the main title (§7.5).

    Heuristic on the **pass condition** (§6.2): a heading's depth is not written down, so
    it is inferred from the order in which adornment characters first appear in the page.
    A page whose first heading is a subsection -- legitimate in an included fragment --
    therefore has every heading measured one level too shallow.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _prose_pages(b):
            authored = b.files[path].authored_lines
            headings = _headings(_rst_lines(b, path))
            order: list[str] = []
            for number, text, char in headings:
                if char == MAIN_TITLE_ADORNMENT:
                    continue
                if char not in order:
                    order.append(char)
                if number not in authored:
                    continue
                out.append(target(f"adornment:{path}:{number}", path, (number, number),
                                  (path, number, text, char, order.index(char)),
                                  f"{text[:60]} ({char})"))
        return out

    def pass_condition(self, t: Target):
        path, number, text, char, depth = t.payload
        if depth >= len(HEADING_LEVELS):
            return Violated(f"{path}:{number} is nested {depth + 1} levels deep, past the "
                            f"{len(HEADING_LEVELS)} the style guide defines")
        wanted = HEADING_LEVELS[depth]
        if char == wanted:
            return Satisfied(f"{path}:{number} uses {char!r} at level {depth + 1}")
        return Violated(f"{path}:{number} underlines a level-{depth + 1} heading with "
                        f"{char!r}; the style guide gives that level {wanted!r}")


@rule(
    id="MATPLOTLIB-C004",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of the page's markup
    reads=("files",),  # spec §5: the adornment and the file name are in the patch
)
class TheHashOverlineIsReservedForAnIndexMainTitle:
    """Pre-condition: each documentation page the agent edited that carries at least one
    section heading.
    Pass condition: it uses ``#`` only as the main title of an :file:`index.rst`, and
    otherwise starts at chapter level or lower.

    §7.1: the antecedent is *having headings*, not *having a ``#`` heading* -- selecting
    the latter could record a violation and never a compliant page. Not heuristic (§6.2):
    the adornment character and the file name are both exact, and the rule names both.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _prose_pages(b):
            headings = _headings(_rst_lines(b, path))
            if not headings:
                continue
            out.append(target(f"main-title:{path}", path, None, (path, headings),
                              f"{len(headings)} heading(s) in {path}"))
        return out

    def pass_condition(self, t: Target):
        path, headings = t.payload
        hashed = [(n, text) for n, text, char in headings
                  if char == MAIN_TITLE_ADORNMENT]
        is_index = path.rsplit("/", 1)[-1] == INDEX_PAGE
        if not hashed:
            return Satisfied(f"{path} starts at chapter level or lower")
        if not is_index:
            return Violated(f"{path}:{hashed[0][0]} uses the # overline, which is "
                            f"reserved for the main title of an {INDEX_PAGE}")
        if hashed[0][0] != headings[0][0]:
            return Violated(f"{path}:{hashed[0][0]} uses the # overline below the page's "
                            f"first heading, so it is not the main title")
        return Satisfied(f"{path} reserves the # overline for its main title")


def _parameter_mentions(bundle: EvidenceBundle, marker) -> list[tuple]:
    """(path, doc, function, line, span-text) for markup spans in a function docstring.

    ``marker`` is the compiled pattern for one inline-markup form. Restricted to function
    docstrings because that is the only place the patch says which words *are* parameters.
    """
    out = []
    for path, _module, doc, function in owned_docstrings(bundle, tests=False):
        if function is None:
            continue
        names = set(parameter_names(function))
        if not names:
            continue
        for number, text in doc.lines():
            for match in marker.finditer(text):
                out.append((path, number, match.group("target").strip(), names, function))
    return out


@rule(
    id="MATPLOTLIB-C006",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of prose, no newness qualifier
    reads=("files",),  # spec §5: the docstring and the signature are in the patch
    heuristic=True,
)
class FunctionArgumentsAreEmphasised:
    """Pre-condition: each mention of one of a function's own parameters in its docstring
    prose that is either bare or already emphasised.
    Pass condition: it carries the ``*emphasis*`` role.

    Mentions wrapped in single or double backticks are excluded: those are C007's and
    C008's, and the three rules between them cover every markup form exactly once (§7.5).

    Heuristic on the **pre-condition** (§6.3): *referring to an argument* is approximated
    by the parameter's name appearing as a word in the prose, so ``color`` used as an
    ordinary English word inside the same docstring is selected too.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc, function in owned_docstrings(b, tests=False):
            if function is None:
                continue
            names = [n for n in parameter_names(function) if n not in ("self", "cls")]
            if not names:
                continue
            body = doc.lines()
            section_lines = _parameter_section_lines(doc)
            for number, text in body:
                if number in section_lines:
                    continue
                stripped = _LITERAL.sub(" ", _DEFAULT_ROLE.sub(" ", _ROLE.sub(" ", text)))
                for name in names:
                    for match in re.finditer(rf"(?<![\w`.]){re.escape(name)}(?![\w`])",
                                             stripped):
                        emphasised = _emphasised_at(stripped, match.start())
                        out.append(target(
                            f"arg-emphasis:{path}:{number}:{name}:{match.start()}",
                            path, (number, number), (path, number, name, emphasised),
                            text.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, name, emphasised = t.payload
        if emphasised:
            return Satisfied(f"{path}:{number} refers to the argument *{name}* with the "
                             f"emphasis role")
        return Violated(f"{path}:{number} names the argument {name} in prose without the "
                        f"*emphasis* role")


def _emphasised_at(text: str, position: int) -> bool:
    return any(match.start() <= position < match.end()
               for match in _EMPHASIS.finditer(text))


def _parameter_section_lines(doc) -> set[int]:
    """Line numbers belonging to the Parameters, Returns and Other Parameters sections."""
    parsed = ds.parse(doc.lines())
    out: set[int] = set()
    for section in parsed.sections:
        if section.name in ("Parameters", "Other Parameters", "Returns", "Yields"):
            out.add(section.heading.lineno)
            out.add(section.heading.underline_lineno)
            out.update(number for number, _ in section.body)
    return out


@rule(
    id="MATPLOTLIB-C007",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class TheDefaultRoleDoesNotMarkUpAnArgument:
    """Pre-condition: each single-backtick span the agent wrote in a function docstring.
    Pass condition: what it marks up is not one of that function's parameters.

    §7.1: a prohibition, so the antecedent is *using the default role* and the graded
    question is what was marked with it; a default role around a class name is a recorded
    pass. C006 and C008 take the other two markup forms (§7.5).

    Heuristic on the **pass condition** (§6.2): a name is judged to be an argument by
    matching the signature, so a docstring that marks up a *different* thing sharing the
    name reads as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"default-role:{path}:{number}:{text}", path, (number, number),
                       (path, number, text, names), f"`{text}`")
                for path, number, text, names, _f in _parameter_mentions(b, _DEFAULT_ROLE)]

    def pass_condition(self, t: Target):
        path, number, text, names = t.payload
        if text in names:
            return Violated(f"{path}:{number} marks up the argument {text} with the "
                            f"default role instead of *emphasis*")
        return Satisfied(f"{path}:{number} uses the default role for `{text}`, which is "
                         f"not an argument")


@rule(
    id="MATPLOTLIB-C008",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class TheLiteralRoleDoesNotMarkUpAnArgument:
    """Pre-condition: each double-backtick literal the agent wrote in a function
    docstring.
    Pass condition: what it marks up is not one of that function's parameters.

    The same shape as C007, on the other markup form; a literal around a value or a type
    is a recorded pass. Heuristic for the same reason (§6.2).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"literal-role:{path}:{number}:{text}", path, (number, number),
                       (path, number, text, names), f"``{text}``")
                for path, number, text, names, _f in _parameter_mentions(b, _LITERAL)]

    def pass_condition(self, t: Target):
        path, number, text, names = t.payload
        if text in names:
            return Violated(f"{path}:{number} marks up the argument {text} with the "
                            f"literal role instead of *emphasis*")
        return Satisfied(f"{path}:{number} uses the literal role for ``{text}``, which "
                         f"is not an argument")


@rule(
    id="MATPLOTLIB-C009",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5: the expression is in the patch
    heuristic=True,
)
class InlineMathematicsUsesTheMathRole:
    """Pre-condition: each line of prose the agent wrote that states an inline
    mathematical expression.
    Pass condition: it is marked with the ``:math:`` role.

    Heuristic on the **pre-condition** (§6.3): *an inline mathematical expression* is
    recognised from LaTeX vocabulary and dollar delimiters, so mathematics written in
    plain words is not seen. Displayed mathematics is C010's and is excluded here (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, number, text in prose_lines(b):
            if _DISPLAY_MATH.search(text):
                continue
            if not _INLINE_MATH.search(text):
                continue
            out.append(target(f"inline-math:{path}:{number}", path, (number, number),
                              (path, number, text), text.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, text = t.payload
        if _MATH_ROLE.search(text):
            return Satisfied(f"{path}:{number} marks its inline mathematics with :math:")
        return Violated(f"{path}:{number} writes inline mathematics without the :math: "
                        f"role: {text.strip()[:60]}")


@rule(
    id="MATPLOTLIB-C010",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DisplayedMathematicsUsesTheMathDirective:
    """Pre-condition: each displayed mathematical expression the agent wrote.
    Pass condition: it is introduced by a ``.. math::`` directive.

    Split from C009 by delimiter (§7.5): ``$$`` and the LaTeX display environments are
    displayed mathematics and belong here; single ``$`` and inline LaTeX belong there.

    Heuristic on the **pre-condition** (§6.3), which recognises displayed mathematics from
    those delimiters alone.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _prose_pages(b) + python_files(b):
            lines = _rst_lines(b, path)
            authored = b.files[path].authored_lines
            for index, (number, text) in enumerate(lines):
                if number not in authored or not _DISPLAY_MATH.search(text):
                    continue
                above = [t for n, t in lines[max(0, index - 4):index]]
                out.append(target(f"display-math:{path}:{number}", path, (number, number),
                                  (path, number, text, above), text.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, text, above = t.payload
        if _MATH_DIRECTIVE.match(text) or any(_MATH_DIRECTIVE.match(a) for a in above):
            return Satisfied(f"{path}:{number} sits under a .. math:: directive")
        return Violated(f"{path}:{number} writes displayed mathematics without a "
                        f".. math:: directive: {text.strip()[:60]}")


@rule(
    id="MATPLOTLIB-C011",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5: the link is in the patch
    heuristic=True,
)
class LinksToOtherPagesUseTheDocRole:
    """Pre-condition: each link to another documentation page the agent wrote.
    Pass condition: it uses the ``:doc:`` role.

    §7.1: the antecedent is *linking to a page*, whichever way it is written, so a
    ``:doc:`` link is a recorded pass and a raw path is a violation.

    Heuristic on the **pre-condition** (§6.3): a page link is recognised as a ``:doc:``
    role or as a path ending in ``.rst``/``.html``, so a link written as a bare label
    reference is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _prose_pages(b):
            authored = b.files[path].authored_lines
            for number, text in _rst_lines(b, path):
                if number not in authored:
                    continue
                if _DIRECTIVE.match(text):
                    continue
                for match in _ROLE.finditer(text):
                    if match.group("role") == "doc":
                        out.append(target(f"page-link:{path}:{number}:{match.start()}",
                                          path, (number, number),
                                          (path, number, text, True), text.strip()[:120]))
                for match in _PAGE_LINK.finditer(text):
                    out.append(target(f"page-link:{path}:{number}:raw{match.start()}",
                                      path, (number, number),
                                      (path, number, text, False), text.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, text, is_doc_role = t.payload
        if is_doc_role:
            return Satisfied(f"{path}:{number} links to another page with the :doc: role")
        return Violated(f"{path}:{number} links to a documentation page by path rather "
                        f"than with the :doc: role: {text.strip()[:60]}")


def _labels(bundle: EvidenceBundle, path: str):
    """(line number, label name, the lines that follow it) for each reference label."""
    lines = list(_rst_lines(bundle, path))
    authored = bundle.files[path].authored_lines
    out = []
    for index, (number, text) in enumerate(lines):
        match = _LABEL.match(text)
        if match and number in authored:
            out.append((number, match.group("name").strip(),
                        [t for _, t in lines[index + 1:index + 5]]))
    return out


@rule(
    id="MATPLOTLIB-C013",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "name a reference label" is about one the agent
                          # introduced
    reads=("files",),  # spec §5: the label is in the patch
    heuristic=True,
)
class ReferenceLabelsAreHyphenSeparatedWords:
    """Pre-condition: each reference label the agent wrote.
    Pass condition: it is lower-case words joined by hyphens.

    Heuristic on the **pass condition** (§6.2), and the doubt is named: the sentence asks
    for *descriptive* words too, which no check can decide, so only the separator and the
    casing are graded and a label of meaningless hyphenated words passes.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _prose_pages(b):
            for number, name, _following in _labels(b, path):
                out.append(target(f"label-form:{path}:{number}", path, (number, number),
                                  (path, number, name), f".. _{name}:"))
        return out

    def pass_condition(self, t: Target):
        path, number, name = t.payload
        if "_" in name:
            return Violated(f"{path}:{number} names the label {name!r} with underscores; "
                            f"the guide asks for hyphen-separated words")
        if name != name.lower():
            return Violated(f"{path}:{number} names the label {name!r} with capitals")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            return Violated(f"{path}:{number} names the label {name!r}, which is not "
                            f"hyphen-separated words")
        return Satisfied(f"{path}:{number} names the label {name!r} in hyphen-separated "
                         f"words")


@rule(
    id="MATPLOTLIB-C014",
    category=CATEGORY,
    ownership="created",  # spec §4.3
    reads=("files",),  # spec §5: the label and the path it sits in are both known
    heuristic=True,
)
class ReferenceLabelsDoNotEncodeTheHierarchy:
    """Pre-condition: each reference label the agent wrote whose form C013 already
    accepts.
    Pass condition: none of its words repeats a directory of the page it labels.

    Narrowed to well-formed labels (§7.5) so that a label written with underscores is one
    violation -- C013's -- rather than two.

    Heuristic on the **pass condition** (§6.2): *encoding the hierarchy* is approximated by
    a word of the label matching a directory name on the page's own path, so a label that
    spells the hierarchy differently is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _prose_pages(b):
            for number, name, _following in _labels(b, path):
                if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
                    continue  # §7.5: a malformed label is C013's finding
                out.append(target(f"label-hierarchy:{path}:{number}", path,
                                  (number, number), (path, number, name), f".. _{name}:"))
        return out

    def pass_condition(self, t: Target):
        path, number, name = t.payload
        folders = {part for part in path.split("/")[:-1] if part not in ("doc",)}
        echoes = [word for word in name.split("-") if word in folders]
        if echoes:
            return Violated(f"{path}:{number} encodes the documentation hierarchy in the "
                            f"label {name!r}: {', '.join(echoes)} repeat(s) the path")
        return Satisfied(f"{path}:{number} names the label {name!r} without repeating "
                         f"the hierarchy")


@rule(
    id="MATPLOTLIB-C015",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- placing a label is placing one the agent added
    reads=("files",),  # spec §5: the label and what follows it are in the patch
    heuristic=True,
)
class AReferenceLabelSitsImmediatelyBeforeASection:
    """Pre-condition: each reference label the agent wrote.
    Pass condition: the next non-blank content is a section title, and any reference to
    the label in the change uses the ``:ref:`` role.

    Heuristic on the **pass condition** (§6.2): "immediately before a section" is read as
    a heading within the next few lines, so a label followed by a directive and then a
    heading is failed on a reading the sentence does not spell out.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _prose_pages(b):
            for number, name, following in _labels(b, path):
                out.append(target(f"label-place:{path}:{number}", path, (number, number),
                                  (path, number, name, following, b), f".. _{name}:"))
        return out

    def pass_condition(self, t: Target):
        path, number, name, following, bundle = t.payload
        content = [line for line in following if line.strip()]
        titled = (len(content) >= 2 and not _ADORNMENT.match(content[0])
                  and bool(_ADORNMENT.match(content[1])))
        if not titled:
            return Violated(f"{path}:{number} places the label {name!r} where no section "
                            f"title follows it")
        for other in _prose_pages(bundle):
            for line_no, text in added_lines(bundle, other):
                if _LABEL.match(text):
                    continue
                if re.search(rf"(?<![\w:`]){re.escape(name)}(?![\w-])", text) \
                        and f":ref:`" not in text:
                    return Violated(f"{other}:{line_no} refers to the label {name!r} "
                                    f"without the :ref: role")
        return Satisfied(f"{path}:{number} places the label {name!r} immediately before a "
                         f"section")


@rule(
    id="MATPLOTLIB-C016",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class MatplotlibCodeElementsAreLinkedWithBackTicks:
    """Pre-condition: each dotted matplotlib name the agent wrote in prose.
    Pass condition: it is inside back ticks -- a role, or the default role.

    Heuristic on the **pre-condition** (§6.3): *a method, class or module* is approximated
    by a dotted name whose root is ``matplotlib`` or ``mpl_toolkits``, so an unqualified
    class name mentioned in prose is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, number, text in prose_lines(b):
            for match in _MPL_DOTTED.finditer(text):
                inside = _inside_backticks(text, match.start())
                out.append(target(f"mpl-link:{path}:{number}:{match.start()}", path,
                                  (number, number),
                                  (path, number, match.group(0), inside),
                                  text.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, name, inside = t.payload
        if inside:
            return Satisfied(f"{path}:{number} links {name} with back ticks")
        return Violated(f"{path}:{number} names {name} in prose without back ticks, so "
                        f"Sphinx never links it")


def _inside_backticks(text: str, position: int) -> bool:
    for pattern in (_ROLE, _LITERAL, _DEFAULT_ROLE):
        for match in pattern.finditer(text):
            if match.start() <= position < match.end():
                return True
    return False


@rule(
    id="MATPLOTLIB-C018",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class AnAbbreviatedReferenceIsQualifiedEnoughToDisambiguate:
    """Pre-condition: each reST role reference the agent wrote whose final name is one the
    project defines in more than one place.
    Pass condition: the reference carries enough of the dotted path to say which.

    Heuristic on the **pre-condition** (§6.3): "several code elements share the name" is
    approximated by a published list of the dual-API names -- the plotting functions that
    exist on both ``Axes`` and ``pyplot`` -- so a collision outside that list is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, number, text in prose_lines(b):
            for match in _ROLE.finditer(text):
                reference = match.group("target").lstrip("~.")
                if reference.split(".")[-1] not in DUAL_API_NAMES:
                    continue
                out.append(target(f"ambiguous-ref:{path}:{number}:{match.start()}", path,
                                  (number, number), (path, number, reference),
                                  match.group(0)))
        return out

    def pass_condition(self, t: Target):
        path, number, reference = t.payload
        if "." in reference:
            return Satisfied(f"{path}:{number} qualifies the reference as {reference}")
        return Violated(f"{path}:{number} refers to {reference!r} unqualified, and the "
                        f"name exists on both Axes and pyplot")


@rule(
    id="MATPLOTLIB-C019",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5: the directive and its argument are in the patch
)
class ThePlotDirectivePointsAtAScript:
    """Pre-condition: each ``.. plot::`` directive with a file argument the agent wrote.
    Pass condition: the file is a Python script.

    Not heuristic (§6.2): the argument is a path and the check is its suffix, which the
    sentence names. A ``.. plot::`` directive with inline code and no argument finds no
    target -- there is no file to be wrong about.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _prose_pages(b) + python_files(b):
            authored = b.files[path].authored_lines
            for number, argument in _directives(_rst_lines(b, path), "plot"):
                if number not in authored or not argument:
                    continue
                out.append(target(f"plot-directive:{path}:{number}", path,
                                  (number, number), (path, number, argument),
                                  f".. plot:: {argument}"))
        return out

    def pass_condition(self, t: Target):
        path, number, argument = t.payload
        first = argument.split()[0]
        if first.endswith(".py"):
            return Satisfied(f"{path}:{number} points the plot directive at {first}")
        return Violated(f"{path}:{number} points the plot directive at {first}, which is "
                        f"a generated image rather than the script that makes it")


@rule(
    id="MATPLOTLIB-C020",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the page that moved existed before the run
    reads=("files",),  # spec §5: the sentence, not CheckTier=differential -- a page that
                       # moved shows as a deletion or a rename in the patch
    heuristic=True,
)
class AMovedPageLeavesARedirect:
    """Pre-condition: the contribution deletes or renames a documentation page.
    Pass condition: some page in the change carries a ``redirect-from`` directive.

    Heuristic on **both** layers (§6.2, §6.3). *Moving or consolidating* is approximated
    by a deleted or renamed reST page, so a page emptied in place is not seen; and the
    pass condition accepts any redirect in the change rather than checking that it names
    the old URL, which would need the doc-root mapping.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        moved = [p for p in sorted(b.files)
                 if p.startswith(DOC_ROOT) and p.endswith(DOC_SUFFIXES)
                 and (b.files[p].is_deleted or b.files[p].old_path)]
        if not moved:
            return []
        return [target(f"redirect:{b.instance_id}", moved[0], None, (moved, b),
                       f"{len(moved)} documentation page(s) moved or removed")]

    def pass_condition(self, t: Target):
        moved, bundle = t.payload
        for path in sorted(bundle.files):
            if not path.endswith(DOC_SUFFIXES):
                continue
            if _directives(added_lines(bundle, path), "redirect-from"):
                return Satisfied(f"{path} carries a redirect-from for the moved "
                                 f"{moved[0]}")
        return Violated(f"{moved[0]} is moved or removed with no redirect-from directive "
                        f"anywhere in the change, so its URL goes dead")


@rule(
    id="MATPLOTLIB-C021",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a directive the agent wrote
    reads=("files",),  # spec §5: the path is the directive's argument
)
class ARedirectFromPathIsAbsolute:
    """Pre-condition: each ``redirect-from`` directive the agent wrote.
    Pass condition: its path starts at the documentation root.

    Not heuristic (§6.2): a leading ``/`` is exactly what "a full path from the doc root"
    means in Sphinx, and the rule names the alternative it forbids. Asks only about the
    form -- whether a redirect exists at all is C020's (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            if not path.endswith(DOC_SUFFIXES):
                continue
            for number, argument in _directives(added_lines(b, path), "redirect-from"):
                out.append(target(f"redirect-path:{path}:{number}", path,
                                  (number, number), (path, number, argument),
                                  f".. redirect-from:: {argument}"))
        return out

    def pass_condition(self, t: Target):
        path, number, argument = t.payload
        if argument.startswith("/"):
            return Satisfied(f"{path}:{number} writes the redirect as the full path "
                             f"{argument}")
        return Violated(f"{path}:{number} writes the redirect as {argument!r}, a relative "
                        f"link rather than a full path from the doc root")


# --- docstrings ------------------------------------------------------------------------------

#: Formal typing syntax, which a numpydoc type description must not use (C030).
_ANNOTATION_SYNTAX = re.compile(r"\b(?:Optional|Union|List|Dict|Tuple|Sequence|Iterable|"
                                r"Callable|Literal|Any|Mapping|Set)\s*\[|->|\bNone\s*\|")
#: Numeric type names a parameter description might reach for instead of ``float``.
NUMERIC_ALIASES = ("int", "integer", "number", "numeric", "scalar", "real", "complex",
                   "np.number", "numbers.Number")
FLOAT_TYPE = "float"
POSITION_TYPE = "(float, float)"
ARRAY_LIKE = "array-like"
ARRAY = "array"
#: What a 2D position looks like when it is written some other way (C032).
_POSITION_HINT = re.compile(r"\b(?:2[- ]?tuple|tuple of two|pair of)\b"
                            r"|\bfloat\s*,\s*float\b|\(\s*x\s*,\s*y\s*\)", re.I)
_SEQUENCE_OF = re.compile(r"\b(?:array-like|array|ndarray|sequence|list|tuple|iterable)"
                          r"\s+of\s+(?P<dtype>[\w.]+)", re.I)
_NUMERIC_DTYPE = ("float", "float32", "float64", "int", "int32", "int64", "number",
                  "numeric", "scalar", "complex")
_SEQUENCE_WORD = re.compile(r"\b(?:ndarray|array|sequence|list|tuple|iterable)\b", re.I)
_DEFAULT_IN_TYPE = re.compile(r",\s*default\s*[:=]\s*(?P<value>.+?)\s*$")
_VERSION_DIRECTIVE = re.compile(r"^\s*\.\.\s+(?P<kind>versionadded|versionchanged|"
                                r"deprecated|versionremoved)::\s*(?P<version>\S*)")
_ACCEPTS = re.compile(r"^\s*\.\.\s+ACCEPTS:")
_DISCOURAGED_PREFIX = "[*Discouraged*]"
_DISCOURAGED_WORD = re.compile(r"\bdiscouraged\b", re.I)
_DISCOURAGED_ADMONITION = re.compile(r"^\s*\.\.\s+admonition::\s*Discouraged", re.I)
_DOCSTRING_INHERITED = re.compile(r"#\s*docstring inherited", re.I)
#: The modules whose public methods C159 calls "high-level plotting functions".
PLOTTING_MODULES = ("lib/matplotlib/axes/", "lib/matplotlib/pyplot.py")


def _sections(doc):
    return numpydoc(doc)


def _entries(doc, name: str) -> list[ParamEntry]:
    section = numpydoc(doc).section(name)
    return parameter_entries(section) if section is not None else []


def _param_targets(bundle: EvidenceBundle, prefix: str, section: str = "Parameters"):
    """One target per ``name : type`` entry the agent wrote in a numpydoc section."""
    out = []
    for path, _module, doc, function in owned_docstrings(bundle, tests=False):
        if not is_package_path(path):
            continue
        authored = bundle.files[path].authored_lines
        for entry in _entries(doc, section):
            if entry.lineno not in authored:
                continue
            out.append((path, doc, function, entry,
                        target(f"{prefix}:{path}:{entry.lineno}", path,
                               (entry.lineno, entry.lineno), None,
                               f"{entry.names} : {entry.type_text}"[:120])))
    return out


def _typed_targets(bundle: EvidenceBundle, prefix: str, section: str = "Parameters"):
    out = []
    for path, _doc, function, entry, tgt in _param_targets(bundle, prefix, section):
        out.append(target(tgt.key, path, tgt.line_span, (path, entry, function),
                          tgt.snippet))
    return out


@rule(
    id="MATPLOTLIB-C023",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- editing a docstring makes the agent answerable
                          # for its form; the sentence carries no newness qualifier
    reads=("files",),  # spec §5: the docstring is in the patch
    heuristic=True,
)
class DocstringsConformToNumpydoc:
    """Pre-condition: each docstring the agent wrote or edited in the library that carries
    at least one section heading.
    Pass condition: every heading is a numpydoc section name, underlined with dashes at
    least as long as the name, and a summary precedes the first one.

    **Narrowed on purpose (§7.5).** "Conform to the numpydoc guide" would otherwise cover
    everything the twenty rules around it legislate -- quote positions (C026, C027), type
    descriptions (C030--C037), defaults (C039, C041), examples (C159). This rule takes the
    *structural* requirements none of those covers, and the docstring names the others so
    a reader can see the division.

    Heuristic on the **pass condition** (§6.2): conformance is graded on that structural
    subset rather than by running numpydoc's own validator, so the rate is an upper bound.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc, _function in owned_docstrings(b, tests=False):
            if not is_package_path(path):
                continue
            headings = ds.find_headings(doc.lines(), known=_ANY_HEADING)
            if not headings:
                continue
            out.append(target(f"numpydoc:{path}:{doc.lineno}", path, doc.span(),
                              (path, doc, headings), doc.owner[:120]))
        return out

    def pass_condition(self, t: Target):
        path, doc, headings = t.payload
        for heading in headings:
            if heading.name not in ds.NUMPYDOC_SECTIONS:
                return Violated(f"{path}:{heading.lineno} uses {heading.name!r}, which is "
                                f"not a numpydoc section name")
            if heading.underline_char != "-":
                return Violated(f"{path}:{heading.lineno} underlines {heading.name!r} "
                                f"with {heading.underline_char!r}, not dashes")
            if heading.underline_length < len(heading.name):
                return Violated(f"{path}:{heading.lineno} underlines {heading.name!r} "
                                f"with {heading.underline_length} dashes, fewer than the "
                                f"{len(heading.name)} the name needs")
        parsed = numpydoc(doc)
        if not parsed.summary_text():
            return Violated(f"{path}:{doc.lineno} opens with a section heading and no "
                            f"summary line")
        return Satisfied(f"{path}:{doc.lineno} uses {len(headings)} numpydoc section(s), "
                         f"correctly underlined, after a summary")


#: A recognition vocabulary wide enough to catch a *misspelled* section name, which is
#: what C023 has to see. `find_headings` restricts to known names by design.
_ANY_HEADING = ds.NUMPYDOC_SECTIONS + (
    "Parameter", "Return", "Returns:", "Example", "Note", "See also", "Other parameters",
    "Args", "Arguments", "Keyword Arguments", "Raise", "Warning", "Attribute", "Method",
    "Explanation", "Usage", "Todo", "Yield",
)


@rule(
    id="MATPLOTLIB-C025",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "new API reference documentation" is a newness
                          # qualifier
    reads=("files",),  # spec §5: both the module docstring and the api page are files
    heuristic=True,
)
class NewApiReferenceGoesInTheModuleDocstring:
    """Pre-condition: the contribution adds public API to modules that already exist.
    Pass condition: its reference documentation goes into docstrings, not into a new
    :file:`doc/api` page.

    **Narrowed against C158 (§7.5)**, which requires exactly the opposite artefact for a
    *new module*: a contribution that adds a module finds no target here, so the two
    sentences never bind the same change in opposite directions.

    Heuristic on the **pre-condition** (§6.3): *new API* is approximated by a public
    definition whose header the agent wrote, so API added by assignment or by a factory is
    not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if _new_modules(b):
            return []  # §7.5: a new module is C158's case
        added = new_public_defs(b)
        if not added:
            return []
        path, name, line = added[0]
        return [target(f"api-in-docstring:{b.instance_id}", path, None, (added, b),
                       f"{len(added)} new public definition(s), e.g. {name}")]

    def pass_condition(self, t: Target):
        added, bundle = t.payload
        pages = [p for p in sorted(bundle.files)
                 if p.startswith("doc/api/") and bundle.files[p].is_new
                 and not p.startswith(DOC_TREE_EXCEPTION)]
        if pages:
            return Violated(f"the new API is documented in {pages[0]} rather than in the "
                            f"module docstring")
        return Satisfied(f"the {len(added)} new public definition(s) are documented in "
                         f"docstrings, with no new doc/api page")


def _new_modules(bundle: EvidenceBundle) -> list[str]:
    """New library modules -- the antecedent C158 fires on and C025 excludes."""
    out = []
    for path in sorted(bundle.files):
        name = path.rsplit("/", 1)[-1]
        if (bundle.files[path].is_new and path.endswith(".py") and is_package_path(path)
                and name != "__init__.py" and "/tests/" not in path):
            out.append(path)
    return out


@rule(
    id="MATPLOTLIB-C026",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of the docstring's form
    reads=("files",),  # spec §5: the quotes are in the patch
)
class SingleLineDocstringsKeepTheirQuotesOnTheLine:
    """Pre-condition: each single-line docstring the agent wrote or edited.
    Pass condition: its opening and closing quotes are on the same line as its text.

    Not heuristic (§6.2): the raw text carries the quotes, and "same line" is a position.
    Multi-line docstrings are C027's and find no target here -- the two rules partition
    docstrings by length (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc, _function in owned_docstrings(b, tests=False):
            if "\n" in doc.text.strip():
                continue
            out.append(target(f"quotes-single:{path}:{doc.lineno}", path, doc.span(),
                              (path, doc), doc.raw.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, doc = t.payload
        if "\n" not in doc.raw:
            return Satisfied(f"{path}:{doc.lineno} keeps a one-line docstring on one line")
        return Violated(f"{path}:{doc.lineno} spreads a single-line docstring over "
                        f"{doc.raw.count(chr(10)) + 1} lines, so its quotes do not sit "
                        f"on the line its text is on")



@rule(
    id="MATPLOTLIB-C027",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class MultiLineDocstringsPutTheirQuotesOnTheirOwnLines:
    """Pre-condition: each multi-line docstring the agent wrote or edited.
    Pass condition: nothing shares a line with its opening or closing quotes.

    Not heuristic (§6.2): both are positions in the raw text. Single-line docstrings are
    C026's (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc, _function in owned_docstrings(b, tests=False):
            if "\n" not in doc.text.strip():
                continue
            out.append(target(f"quotes-multi:{path}:{doc.lineno}", path, doc.span(),
                              (path, doc), doc.raw.strip()[:80]))
        return out

    def pass_condition(self, t: Target):
        path, doc = t.payload
        if doc.raw.split("\n", 1)[0].strip():
            return Violated(f"{path}:{doc.lineno} starts its text on the same line as "
                            f"the opening quotes")
        if doc.raw.rsplit("\n", 1)[-1].strip():
            return Violated(f"{path}:{doc.lineno} closes on the same line as its text")
        return Satisfied(f"{path}:{doc.lineno} puts both triple quotes on their own lines")



@rule(
    id="MATPLOTLIB-C029",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class StringValuesUsePlainQuotes:
    """Pre-condition: each quoted string value the agent wrote in a numpydoc type
    description.
    Pass condition: it is written with plain quotes and no surrounding literal role.

    Heuristic on the **pre-condition** (§6.3): *a string value* is approximated by a
    quoted token inside a ``name : type`` line, so a value named only in the prose
    description is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _doc, _function, entry, tgt in _param_targets(b, "string-value"):
            for match in re.finditer(r"(?:``)?'[^']*'(?:``)?|(?:``)?\"[^\"]*\"(?:``)?",
                                     entry.type_text):
                out.append(target(f"{tgt.key}:{match.start()}", path, tgt.line_span,
                                  (path, entry, match.group(0)), tgt.snippet))
        return out

    def pass_condition(self, t: Target):
        path, entry, span = t.payload
        if span.startswith("``"):
            return Violated(f"{path}:{entry.lineno} wraps the string value {span} in a "
                            f"literal role; plain quotes are what the guide asks for")
        return Satisfied(f"{path}:{entry.lineno} gives the string value {span} with plain "
                         f"quotes")


@rule(
    id="MATPLOTLIB-C030",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class TypeDescriptionsAvoidAnnotationSyntax:
    """Pre-condition: each ``name : type`` line the agent wrote in a Parameters section.
    Pass condition: the type is prose, not formal typing syntax.

    Not heuristic (§6.2): the forbidden forms are a closed list of typing constructs --
    subscripted ``Optional``/``Union``/``List`` and friends, and the ``->`` arrow -- and
    the check is their presence.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _typed_targets(b, "annotation-syntax")

    def pass_condition(self, t: Target):
        path, entry, _function = t.payload
        if match := _ANNOTATION_SYNTAX.search(entry.type_text):
            return Violated(f"{path}:{entry.lineno} describes {entry.names} with "
                            f"annotation syntax ({match.group(0)}) rather than in prose")
        return Satisfied(f"{path}:{entry.lineno} describes {entry.names} without "
                         f"annotation syntax")


@rule(
    id="MATPLOTLIB-C031",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class AnyNumberIsDescribedAsFloat:
    """Pre-condition: each Parameters entry the agent wrote whose type names a scalar
    numeric kind.
    Pass condition: it is described as ``float``.

    Heuristic on the **pre-condition** (§6.3): *accepts any number* is approximated by the
    type naming one of the numeric spellings, so a parameter genuinely restricted to
    integers is selected too and reads as a violation.

    Sequences of numbers are C033's and are excluded here (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _doc, function, entry, tgt in _param_targets(b, "numeric-type"):
            text = entry.type_text.strip("` ")
            if _SEQUENCE_WORD.search(text) or _POSITION_HINT.search(text):
                continue  # §7.5: sequences are C033's, positions C032's
            words = re.findall(r"[\w.]+", text.lower())
            if not any(w in NUMERIC_ALIASES or w == FLOAT_TYPE for w in words):
                continue
            out.append(target(tgt.key, path, tgt.line_span, (path, entry), tgt.snippet))
        return out

    def pass_condition(self, t: Target):
        path, entry = t.payload
        text = entry.type_text.strip("` ")
        if re.match(rf"^{FLOAT_TYPE}\b", text):
            return Satisfied(f"{path}:{entry.lineno} describes {entry.names} as float")
        return Violated(f"{path}:{entry.lineno} describes the numeric parameter "
                        f"{entry.names} as {text!r}, not as float")


@rule(
    id="MATPLOTLIB-C032",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class A2dPositionIsDescribedWithParentheses:
    """Pre-condition: each Parameters entry the agent wrote whose type describes a
    two-dimensional position.
    Pass condition: it is written ``(float, float)``, parentheses included.

    Heuristic on the **pre-condition** (§6.3): *a 2D position* is approximated by the
    phrases the guide's own examples use -- a 2-tuple, a pair, ``float, float``, ``(x,
    y)`` -- so a position described some other way is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _doc, _function, entry, tgt in _param_targets(b, "position-type"):
            if not _POSITION_HINT.search(entry.type_text):
                continue
            out.append(target(tgt.key, path, tgt.line_span, (path, entry), tgt.snippet))
        return out

    def pass_condition(self, t: Target):
        path, entry = t.payload
        text = entry.type_text.strip("` ")
        if text.startswith(POSITION_TYPE):
            return Satisfied(f"{path}:{entry.lineno} describes {entry.names} as "
                             f"{POSITION_TYPE}")
        return Violated(f"{path}:{entry.lineno} describes the 2D position {entry.names} "
                        f"as {text!r} rather than {POSITION_TYPE}")


@rule(
    id="MATPLOTLIB-C033",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ANumericSequenceParameterIsArrayLike:
    """Pre-condition: each Parameters entry the agent wrote whose type describes a
    sequence of numbers.
    Pass condition: it is described as ``array-like``.

    Return values are C034's, and this rule reads the Parameters section only (§7.5).

    Heuristic on the **pre-condition** (§6.3): the sequence is recognised from the words
    ``array``, ``ndarray``, ``sequence``, ``list``, ``tuple`` or ``iterable`` together with
    a numeric element type.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _doc, _function, entry, tgt in _param_targets(b, "array-like"):
            text = entry.type_text.strip("` ")
            match = _SEQUENCE_OF.search(text)
            numeric = match and match.group("dtype").lower() in _NUMERIC_DTYPE
            if not (numeric or re.match(r"^(?:1d |2d |nd )?(?:np\.)?(?:nd)?array(?:-like)?\b",
                                        text, re.I)):
                continue
            out.append(target(tgt.key, path, tgt.line_span, (path, entry), tgt.snippet))
        return out

    def pass_condition(self, t: Target):
        path, entry = t.payload
        text = entry.type_text.strip("` ")
        if text.lower().startswith(ARRAY_LIKE):
            return Satisfied(f"{path}:{entry.lineno} describes {entry.names} as "
                             f"array-like")
        return Violated(f"{path}:{entry.lineno} describes the numeric sequence "
                        f"{entry.names} as {text!r}, not as array-like")


@rule(
    id="MATPLOTLIB-C034",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class AReturnedArrayIsDescribedAsArray:
    """Pre-condition: each Returns entry the agent wrote whose type mentions an array.
    Pass condition: it says ``array``, not ``array-like``.

    Reads the Returns section only; the Parameters side is C033's, which asks for the
    opposite word for the opposite reason (§7.5).

    Heuristic on the **pre-condition** (§6.3): whether the value *really is* a numpy array
    is not observable from the docstring, so every array-mentioning return type is
    selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _doc, _function, entry, tgt in _param_targets(b, "returned-array",
                                                                "Returns"):
            if "array" not in entry.type_text.lower():
                continue
            out.append(target(tgt.key, path, tgt.line_span, (path, entry), tgt.snippet))
        return out

    def pass_condition(self, t: Target):
        path, entry = t.payload
        text = entry.type_text.strip("` ")
        if ARRAY_LIKE in text.lower():
            return Violated(f"{path}:{entry.lineno} describes the returned "
                            f"{entry.names} as array-like; a real array is described as "
                            f"array")
        return Satisfied(f"{path}:{entry.lineno} describes the returned {entry.names} as "
                         f"{text!r}")


@rule(
    id="MATPLOTLIB-C035",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ANonFloatDtypeIsSpeltOut:
    """Pre-condition: each Parameters entry the agent wrote describing a numeric sequence
    whose element type is not ``float``.
    Pass condition: it is written ``array-like of <dtype>``.

    Heuristic on the **pre-condition** (§6.3): the element type is read from the phrase
    ``<sequence> of <dtype>``, so a dtype stated only in the description is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _doc, _function, entry, tgt in _param_targets(b, "dtype-spelt"):
            text = entry.type_text.strip("` ")
            match = _SEQUENCE_OF.search(text)
            if not match:
                continue
            dtype = match.group("dtype").lower()
            if dtype in ("float", "floats") or dtype not in _NUMERIC_DTYPE + ("ints",):
                continue
            out.append(target(tgt.key, path, tgt.line_span, (path, entry, dtype),
                              tgt.snippet))
        return out

    def pass_condition(self, t: Target):
        path, entry, dtype = t.payload
        text = entry.type_text.strip("` ")
        if re.match(rf"^{ARRAY_LIKE}\s+of\s+", text, re.I):
            return Satisfied(f"{path}:{entry.lineno} spells the dtype out as "
                             f"array-like of {dtype}")
        return Violated(f"{path}:{entry.lineno} describes {entry.names} as {text!r} "
                        f"instead of 'array-like of {dtype}'")


@rule(
    id="MATPLOTLIB-C036",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ANonNumericSequenceIsAListOfType:
    """Pre-condition: each Parameters entry the agent wrote describing a sequence whose
    element type is not numeric.
    Pass condition: it is written ``list of <type>``.

    Numeric sequences are C033's and C035's; this rule fires only where the element type
    is not one of the numeric spellings (§7.5).

    Heuristic on the **pre-condition** (§6.3): the element type is read from the phrase
    ``<sequence> of <type>``.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _doc, _function, entry, tgt in _param_targets(b, "list-of"):
            text = entry.type_text.strip("` ")
            match = _SEQUENCE_OF.search(text)
            if not match:
                continue
            dtype = match.group("dtype").lower()
            if dtype.rstrip("s") in [d.rstrip("s") for d in _NUMERIC_DTYPE]:
                continue
            out.append(target(tgt.key, path, tgt.line_span, (path, entry, dtype),
                              tgt.snippet))
        return out

    def pass_condition(self, t: Target):
        path, entry, dtype = t.payload
        text = entry.type_text.strip("` ")
        if re.match(r"^list\s+of\s+", text, re.I):
            return Satisfied(f"{path}:{entry.lineno} describes {entry.names} as "
                             f"list of {dtype}")
        return Violated(f"{path}:{entry.lineno} describes the non-numeric sequence "
                        f"{entry.names} as {text!r} instead of 'list of {dtype}'")


@rule(
    id="MATPLOTLIB-C037",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ParameterTypesAreFullReferencesWithATilde:
    """Pre-condition: each reST role reference the agent wrote inside a ``name : type``
    line.
    Pass condition: it is a full dotted path introduced by ``~``.

    Reads type lines only; references in the surrounding prose are C038's, which asks for
    the abbreviated form instead (§7.5).

    Heuristic on the **pass condition** (§6.2): "full reference" is graded as a dotted
    path of at least two components, since whether the path resolves is a fact about the
    whole checkout.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _doc, _function, entry, tgt in _param_targets(b, "type-reference"):
            for match in _ROLE.finditer(entry.type_text):
                out.append(target(f"{tgt.key}:{match.start()}", path, tgt.line_span,
                                  (path, entry, match.group("target")), tgt.snippet))
        return out

    def pass_condition(self, t: Target):
        path, entry, reference = t.payload
        if reference.startswith("~") and "." in reference:
            return Satisfied(f"{path}:{entry.lineno} writes the type as the full "
                             f"reference {reference}")
        return Violated(f"{path}:{entry.lineno} writes the type reference {reference!r} "
                        f"without a leading tilde and a full dotted path")


@rule(
    id="MATPLOTLIB-C038",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class InTextReferencesUseTheAbbreviatedDottedForm:
    """Pre-condition: each reST role reference the agent wrote in docstring prose, outside
    the ``name : type`` lines.
    Pass condition: it uses the abbreviated dotted form -- a leading ``.`` or ``~.``.

    The counterpart of C037, split by location so no reference is graded twice (§7.5).

    Heuristic on the **pass condition** (§6.2): the abbreviation is recognised from the
    leading dot Sphinx uses for it, so an abbreviation written some other way reads as a
    violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc, _function in owned_docstrings(b, tests=False):
            if not is_package_path(path):
                continue
            authored = b.files[path].authored_lines
            typed = {entry.lineno for name in ("Parameters", "Other Parameters", "Returns")
                     for entry in _entries(doc, name)}
            for number, text in doc.lines():
                if number not in authored or number in typed:
                    continue
                for match in _ROLE.finditer(text):
                    out.append(target(f"in-text-ref:{path}:{number}:{match.start()}",
                                      path, (number, number),
                                      (path, number, match.group("target")),
                                      match.group(0)))
        return out

    def pass_condition(self, t: Target):
        path, number, reference = t.payload
        if reference.lstrip("~").startswith("."):
            return Satisfied(f"{path}:{number} refers to {reference} in the abbreviated "
                             f"dotted form")
        return Violated(f"{path}:{number} writes the in-text reference {reference!r} in "
                        f"full rather than in the abbreviated dotted form")


@rule(
    id="MATPLOTLIB-C039",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5: the signature and the docstring are both in the patch
    heuristic=True,
)
class ASimpleDefaultIsDocumentedInTheStatedForm:
    """Pre-condition: each documented parameter whose signature gives it a simple literal
    default other than ``None``.
    Pass condition: its type line ends ``, default: <value>``.

    ``None`` defaults are excluded and left to C041, which decides whether they should be
    documented at all -- so a sentinel is one question, not two (§7.5).

    Heuristic on the **pre-condition** (§6.3): "a simple default" is approximated by the
    signature default being a literal, so a default built by a call is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _doc, function, entry, tgt in _param_targets(b, "default-form"):
            if function is None:
                continue
            defaults = _literal_defaults(function)
            name = entry.names.split(",")[0].strip().lstrip("*")
            if name not in defaults or defaults[name] is None:
                continue  # §7.5: a None default is C041's
            out.append(target(tgt.key, path, tgt.line_span,
                              (path, entry, name, defaults[name]), tgt.snippet))
        return out

    def pass_condition(self, t: Target):
        path, entry, name, value = t.payload
        if _DEFAULT_IN_TYPE.search(entry.type_text):
            return Satisfied(f"{path}:{entry.lineno} documents {name}'s default in the "
                             f"stated form")
        return Violated(f"{path}:{entry.lineno} documents {name} without "
                        f"', default: {value!r}' on its type line")


def _literal_defaults(function) -> dict:
    """Parameter name -> literal default, for the defaults a signature states."""
    node = function.node
    args = getattr(node, "args", None)
    if args is None:
        return {}
    out = {}
    positional = list(args.posonlyargs) + list(args.args)
    for argument, default in zip(positional[len(positional) - len(args.defaults):],
                                 args.defaults):
        out[argument.arg] = _as_literal(default)
    for argument, default in zip(args.kwonlyargs, args.kw_defaults):
        if default is not None:
            out[argument.arg] = _as_literal(default)
    return out


def _as_literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError, TypeError):
        return "<expression>"


@rule(
    id="MATPLOTLIB-C041",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ASentinelNoneIsNotDocumentedAsADefault:
    """Pre-condition: each documented parameter whose signature default is ``None``.
    Pass condition: either the docstring does not present ``None`` as the default, or it
    says what ``None`` means.

    §7.1: the antecedent is *having a ``None`` default to describe*, so a docstring that
    explains what ``None`` does is a recorded pass and one that merely writes
    ``default: None`` is a violation. C039 takes every other default (§7.5).

    Heuristic on the **pass condition** (§6.2): "only a not-specified sentinel" is
    approximated by the description never mentioning ``None`` again, so a description that
    explains the sentinel in other words reads as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _doc, function, entry, tgt in _param_targets(b, "sentinel-none"):
            if function is None:
                continue
            defaults = _literal_defaults(function)
            name = entry.names.split(",")[0].strip().lstrip("*")
            if name not in defaults or defaults[name] is not None:
                continue
            out.append(target(tgt.key, path, tgt.line_span, (path, entry, name),
                              tgt.snippet))
        return out

    def pass_condition(self, t: Target):
        path, entry, name = t.payload
        documented = re.search(r",\s*default\s*[:=]\s*None\b", entry.type_text)
        if not documented:
            return Satisfied(f"{path}:{entry.lineno} does not present None as {name}'s "
                             f"default")
        if re.search(r"\bNone\b", entry.description_text()):
            return Satisfied(f"{path}:{entry.lineno} documents None as {name}'s default "
                             f"and says what it means")
        return Violated(f"{path}:{entry.lineno} documents 'default: None' for {name} "
                        f"without saying what None does, so it is only a sentinel")


@rule(
    id="MATPLOTLIB-C042",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ALongParameterTypeIsWrappedWithABackslash:
    """Pre-condition: each ``name : type`` line the agent wrote that is too long for the
    project's 88-character limit, or that is already wrapped.
    Pass condition: it wraps with a trailing backslash and an unindented continuation.

    Heuristic on the **pre-condition** (§6.3): "a long parameter list" is approximated by
    the line exceeding the project's own line limit, which is the only threshold the
    project states anywhere.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc, _function in owned_docstrings(b, tests=False):
            if not is_package_path(path):
                continue
            authored = b.files[path].authored_lines
            body = {number: text for number, text in doc.lines()}
            for entry in _entries(doc, "Parameters"):
                text = body.get(entry.lineno, "")
                if entry.lineno not in authored:
                    continue
                if len(text) <= 88 and not text.rstrip().endswith("\\"):
                    continue
                following = body.get(entry.lineno + 1, "")
                out.append(target(f"wrap-params:{path}:{entry.lineno}", path,
                                  (entry.lineno, entry.lineno + 1),
                                  (path, entry, text, following), text.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, entry, text, following = t.payload
        if not text.rstrip().endswith("\\"):
            return Violated(f"{path}:{entry.lineno} runs to {len(text)} characters "
                            f"without a backslash continuation")
        indent = len(text) - len(text.lstrip())
        if following and (len(following) - len(following.lstrip())) > indent:
            return Violated(f"{path}:{entry.lineno} continues on an indented line; the "
                            f"guide asks for no indent on the continuation")
        return Satisfied(f"{path}:{entry.lineno} wraps with a backslash and an unindented "
                         f"continuation")


@rule(
    id="MATPLOTLIB-C043",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class AnRcParamIsReferencedWithTheRcRole:
    """Pre-condition: each rcParam key the agent named in prose.
    Pass condition: it is written with the ``:rc:`` role.

    Heuristic on the **pre-condition** (§6.3): an rcParam key is recognised as a dotted
    lower-case name whose first segment is one of the project's rcParam namespaces, or as
    a subscript of ``rcParams``, so a key outside those namespaces is not seen and a
    dotted module name inside them is wrongly selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, number, text in prose_lines(b):
            if _RC_ROLE.search(text):
                out.append(target(f"rc-role:{path}:{number}:ok", path, (number, number),
                                  (path, number, text, True), text.strip()[:120]))
                continue
            for match in _RC_KEY_IN_PROSE.finditer(text):
                key = match.group("key") or match.group("bare") or ""
                if not key or key.split(".")[0] not in RC_NAMESPACES:
                    continue
                out.append(target(f"rc-role:{path}:{number}:{match.start()}", path,
                                  (number, number), (path, number, key, False),
                                  text.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, what, is_role = t.payload
        if is_role:
            return Satisfied(f"{path}:{number} references its rcParam with the :rc: role")
        return Violated(f"{path}:{number} names the rcParam {what!r} without the :rc: "
                        f"role")


@rule(
    id="MATPLOTLIB-C045",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the target is a setter the agent added
    reads=("files",),  # spec §5
    heuristic=True,
)
class APropertySetterDocumentsItsAcceptedValues:
    """Pre-condition: each ``set_*`` method the agent added that carries a docstring.
    Pass condition: the docstring has a Parameters block, or an ``.. ACCEPTS:`` block.

    Heuristic on the **pass condition** (§6.2): the presence of either block stands in for
    the values actually being documented, so an empty Parameters section counts.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc, function in owned_docstrings(b, mode="created",
                                                             tests=False):
            if function is None or not function.name.startswith("set_"):
                continue
            if not is_package_path(path):
                continue
            out.append(target(f"setter-accepts:{path}:{function.name}", path, doc.span(),
                              (path, doc, function), f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, doc, function = t.payload
        if numpydoc(doc).has("Parameters"):
            return Satisfied(f"{path}::{function.name} documents its accepted values in a "
                             f"Parameters block")
        if any(_ACCEPTS.match(text) for _, text in doc.lines()):
            return Satisfied(f"{path}::{function.name} documents its accepted values in "
                             f"an .. ACCEPTS: block")
        return Violated(f"{path}::{function.name} is a setter whose docstring documents "
                        f"neither its Parameters nor an .. ACCEPTS: block")


@rule(
    id="MATPLOTLIB-C047",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the target is a method the agent added
    reads=("files",),  # spec §5: the body's first line is in the patch
    heuristic=True,
)
class AnInheritedDocstringIsMarked:
    """Pre-condition: each public method the agent added to a class without a docstring --
    the shape of a deliberately inherited one.
    Pass condition: its body opens with the ``# docstring inherited`` comment.

    Paired with C145 (§7.5), which accepts that marker as satisfying "give every public
    method a docstring"; without the pairing an inherited docstring would be a violation
    of one rule and the antecedent of the other at the same time.

    Heuristic on the **pre-condition** (§6.3): whether a method really overrides a
    documented base method is a fact about the class hierarchy, not about the patch, so
    every undocumented public method is selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"inherited-docstring:{path}:{function.name}", path,
                       function.span(), (path, function, source),
                       f"{path}::{function.name}")
                for path, function, source in _undocumented_methods(b)]

    def pass_condition(self, t: Target):
        path, function, source = t.payload
        if _DOCSTRING_INHERITED.search(source):
            return Satisfied(f"{path}::{function.name} is marked # docstring inherited")
        return Violated(f"{path}::{function.name} has no docstring and no "
                        f"'# docstring inherited' comment saying that is deliberate")


def _undocumented_methods(bundle: EvidenceBundle):
    """(path, FunctionDef, first body lines) for public methods the agent added."""
    from compliance.rules.matplotlib._common import classes, function_source

    out = []
    for path, module in modules(bundle, mode="created", tests=False):
        if not is_package_path(path) or module.tree is None:
            continue
        authored = bundle.files[path].authored_lines
        spans = [(n.lineno, n.end_lineno or n.lineno) for n in classes(module)]
        for function in module.functions:
            if function.lineno not in authored or function.docstring:
                continue
            if function.name.startswith("_"):
                continue
            if not any(lo < function.lineno <= hi for lo, hi in spans):
                continue
            out.append((path, function, function_source(module, function)))
    return out


@rule(
    id="MATPLOTLIB-C145",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "every public method" is graded on the ones the
                          # agent added; an undocumented legacy method is not its doing
    reads=("files",),  # spec §5
    heuristic=True,
)
class EveryPublicMethodHasAnInformativeDocstring:
    """Pre-condition: each public method the agent added to a class in the library.
    Pass condition: it carries a docstring, or the ``# docstring inherited`` marker that
    says the base class's applies.

    The marker is accepted here on purpose (§7.5): C047 is the rule about marking an
    inherited docstring, and without this exception the two would contradict.

    Heuristic on the **pass condition** (§6.2): "informative" is graded as *present and
    more than a few words*, which no check can turn into a judgement of quality.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        from compliance.rules.matplotlib._common import classes, function_source

        out = []
        for path, module in modules(b, mode="created", tests=False):
            if not is_package_path(path) or module.tree is None:
                continue
            authored = b.files[path].authored_lines
            spans = [(n.lineno, n.end_lineno or n.lineno) for n in classes(module)]
            for function in module.functions:
                if function.lineno not in authored or function.name.startswith("_"):
                    continue
                if not any(lo < function.lineno <= hi for lo, hi in spans):
                    continue
                out.append(target(f"method-docstring:{path}:{function.name}", path,
                                  function.span(),
                                  (path, function, function_source(module, function)),
                                  f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function, source = t.payload
        if function.docstring and len(function.docstring.split()) >= 3:
            return Satisfied(f"{path}::{function.name} carries a docstring")
        if _DOCSTRING_INHERITED.search(source):
            return Satisfied(f"{path}::{function.name} deliberately inherits its "
                             f"docstring")
        if function.docstring:
            return Violated(f"{path}::{function.name} has a docstring of "
                            f"{len(function.docstring.split())} word(s), which is not "
                            f"informative")
        return Violated(f"{path}::{function.name} is public and has no docstring")


@rule(
    id="MATPLOTLIB-C158",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "when you add a new module" is a newness qualifier
    reads=("files",),  # spec §5: both the module and the api page are files
    heuristic=True,
)
class ANewModuleGetsAnApiPage:
    """Pre-condition: each new library module the agent added.
    Pass condition: the contribution also adds a reST file under :file:`doc/api/`.

    The other half of the §7.5 resolution with C025: that rule forbids putting API
    *reference prose* in a :file:`doc/api` page and excludes contributions that add a
    module, which is the one case where a new page is required.

    Heuristic on the **pass condition** (§6.2): any new page under :file:`doc/api/` counts,
    rather than checking that it is the stub for this particular module.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"api-page:{path}", path, None, (path, b), f"{path} is a new module")
                for path in _new_modules(b)]

    def pass_condition(self, t: Target):
        path, bundle = t.payload
        pages = [p for p in sorted(bundle.files)
                 if p.startswith("doc/api/") and p.endswith(DOC_SUFFIXES)
                 and bundle.files[p].is_new]
        if pages:
            return Satisfied(f"{path} is documented by the new API page {pages[0]}")
        return Violated(f"{path} is a new module with no new rst file added under "
                        f"doc/api/")


@rule(
    id="MATPLOTLIB-C159",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- graded on plotting functions the agent added
    reads=("files",),  # spec §5
    heuristic=True,
)
class AHighLevelPlottingFunctionCarriesAnExample:
    """Pre-condition: each public plotting function the agent added under
    :file:`lib/matplotlib/axes/` or in :file:`pyplot.py`.
    Pass condition: its docstring has an Examples section.

    Heuristic on the **pre-condition** (§6.3): *a high-level plotting function* is
    approximated by where it lives, so a plotting helper added elsewhere is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc, function in owned_docstrings(b, mode="created",
                                                             tests=False):
            if function is None or function.name.startswith("_"):
                continue
            if not path.startswith(PLOTTING_MODULES):
                continue
            if function.lineno not in b.files[path].authored_lines:
                continue
            out.append(target(f"plot-example:{path}:{function.name}", path, doc.span(),
                              (path, doc, function), f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, doc, function = t.payload
        if numpydoc(doc).has("Examples"):
            return Satisfied(f"{path}::{function.name} carries an Examples section")
        return Violated(f"{path}::{function.name} is a high-level plotting function whose "
                        f"docstring has no Examples section")


# --- versioning directives ----------------------------------------------------------------


def _version_directives(bundle: EvidenceBundle, lines, path: str):
    """(line number, kind, version) for each versioning directive on an added line."""
    authored = bundle.files[path].authored_lines
    out = []
    for number, text in lines:
        match = _VERSION_DIRECTIVE.match(text)
        if match and number in authored:
            out.append((number, match.group("kind"), match.group("version").strip()))
    return out


@rule(
    id="MATPLOTLIB-C219",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the API change, made to code
                          # that already existed
    reads=("files",),  # spec §5: the change and the directive are both in the patch
    heuristic=True,
)
class ABackwardIncompatibleChangeGetsAVersioningDirective:
    """Pre-condition: a contribution that makes a backward-incompatible API change.
    Pass condition: it adds a versioning directive somewhere.

    Heuristic on the **pre-condition** (§6.3): *backward-incompatible* is approximated by
    the contribution removing a public definition or filing a note under the ``behavior``
    or ``removals`` folder of the API-change tree, so an incompatibility introduced by a
    changed default is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        evidence = []
        for path in python_files(b, tests=False):
            if not is_package_path(path):
                continue
            change = b.files[path]
            if re.search(r"^\s*(?:async\s+)?(?:def|class)\s+(?!_)\w+",
                         "\n".join(change.removed_lines), re.M):
                evidence.append(path)
        for path in sorted(b.files):
            if path.startswith(API_CHANGE_ROOT) and b.files[path].is_new:
                if "/behavior/" in path or "/removals/" in path:
                    evidence.append(path)
        if not evidence:
            return []
        return [target(f"versioning:{b.instance_id}", evidence[0], None, (evidence, b),
                       f"backward-incompatible change in {evidence[0]}")]

    def pass_condition(self, t: Target):
        evidence, bundle = t.payload
        for path in sorted(bundle.files):
            if _version_directives(bundle, added_lines(bundle, path), path):
                return Satisfied(f"{path} carries a versioning directive for the change "
                                 f"in {evidence[0]}")
        return Violated(f"{evidence[0]} changes API incompatibly with no versioning "
                        f"directive anywhere in the change")


@rule(
    id="MATPLOTLIB-C221",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of where the directive sits
    reads=("files",),  # spec §5
    heuristic=True,
)
class AVersioningDirectiveOnAPageEndsItsBlock:
    """Pre-condition: each versioning directive the agent wrote on a documentation page.
    Pass condition: nothing but its own body follows it before the block ends.

    Reads prose pages only. Directives inside docstrings are C222's and C223's, split by
    whether they sit in the Parameters section, and no directive is graded twice (§7.5).

    Heuristic on the **pass condition** (§6.2): "the end of its description block" is read
    as *no further content at the directive's own indent before the next blank-line
    boundary*, which is a reading of a phrase the guide does not define precisely.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _prose_pages(b):
            lines = list(_rst_lines(b, path))
            index_of = {number: index for index, (number, _) in enumerate(lines)}
            for number, kind, version in _version_directives(b, lines, path):
                following = [text for _, text in lines[index_of[number] + 1:]]
                out.append(target(f"version-block:{path}:{number}", path,
                                  (number, number), (path, number, kind, following),
                                  f".. {kind}:: {version}"))
        return out

    def pass_condition(self, t: Target):
        path, number, kind, following = t.payload
        for text in following:
            if not text.strip():
                continue
            if text[:1].isspace():
                continue  # the directive's own indented body
            return Violated(f"{path}:{number} places the {kind} directive with "
                            f"{text.strip()[:40]!r} still to come in the same block")
        return Satisfied(f"{path}:{number} places the {kind} directive at the end of its "
                         f"description block")


def _docstring_version_targets(bundle: EvidenceBundle, prefix: str, *, in_parameters: bool):
    out = []
    for path, _module, doc, function in owned_docstrings(bundle, tests=False):
        if not is_package_path(path):
            continue
        parsed = numpydoc(doc)
        section = parsed.section("Parameters")
        param_lines = ({number for number, _ in section.body} if section else set())
        heading_line = section.heading.lineno if section else None
        for number, kind, version in _version_directives(bundle, doc.lines(), path):
            if (number in param_lines) is not in_parameters:
                continue
            out.append((path, doc, function, number, kind, version, heading_line, section))
    return out


@rule(
    id="MATPLOTLIB-C222",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class AClassOrFunctionDirectiveComesBeforeTheParameters:
    """Pre-condition: each versioning directive the agent wrote in a docstring outside its
    Parameters section.
    Pass condition: it appears before the Parameters heading.

    Split from C223 by location (§7.5): a directive *inside* the Parameters section
    belongs to a parameter and is that rule's.

    Heuristic on the **pre-condition** (§6.3): "a class or function directive" is
    approximated by *not inside the Parameters section*, so a directive placed in the
    Notes section is selected and, being after the heading, reads as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for row in _docstring_version_targets(b, "class-version", in_parameters=False):
            path, doc, _function, number, kind, version, heading_line, _section = row
            if heading_line is None:
                continue
            out.append(target(f"class-version:{path}:{number}", path, (number, number),
                              (path, number, kind, heading_line),
                              f".. {kind}:: {version}"))
        return out

    def pass_condition(self, t: Target):
        path, number, kind, heading_line = t.payload
        if number < heading_line:
            return Satisfied(f"{path}:{number} places the {kind} directive before the "
                             f"Parameters section")
        return Violated(f"{path}:{number} places the {kind} directive after the "
                        f"Parameters heading at line {heading_line}")


@rule(
    id="MATPLOTLIB-C223",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class AParameterDirectiveEndsThatParametersDescription:
    """Pre-condition: each versioning directive the agent wrote inside a docstring's
    Parameters section.
    Pass condition: it comes at the end of the description of the parameter it belongs to.

    Split from C222 by location (§7.5).

    Heuristic on the **pass condition** (§6.2): the end of a parameter's description is
    read as *the last non-blank line before the next ``name : type`` entry*, which is
    numpydoc's own shape but not something the guide restates.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for row in _docstring_version_targets(b, "param-version", in_parameters=True):
            path, doc, _function, number, kind, version, _heading, section = row
            entries = parameter_entries(section)
            owner = None
            for order, entry in enumerate(entries):
                nxt = entries[order + 1].lineno if order + 1 < len(entries) else 10 ** 9
                if entry.lineno < number < nxt:
                    owner = (entry, nxt)
            if owner is None:
                continue
            entry, nxt = owner
            tail = [n for n, text in section.body
                    if entry.lineno < n < nxt and text.strip()]
            out.append(target(f"param-version:{path}:{number}", path, (number, number),
                              (path, number, kind, entry, tail),
                              f".. {kind}:: {version}"))
        return out

    def pass_condition(self, t: Target):
        path, number, kind, entry, tail = t.payload
        after = [n for n in tail if n > number]
        if not after:
            return Satisfied(f"{path}:{number} ends {entry.names}'s description with the "
                             f"{kind} directive")
        return Violated(f"{path}:{number} places the {kind} directive with "
                        f"{len(after)} more line(s) of {entry.names}'s description "
                        f"after it")


@rule(
    id="MATPLOTLIB-C224",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class AVersioningDirectiveOmitsTheMicroVersion:
    """Pre-condition: each versioning directive the agent wrote, wherever it sits.
    Pass condition: its version has at most two components, and it is not attached to a
    whole module.

    Grades the *version string* and the directive's subject, which is a different property
    from where it sits -- C221, C222 and C223 grade placement, this one grades content, so
    no rule repeats another's finding (§7.5).

    Not heuristic (§6.2): the number of dot-separated components is arithmetic, and "a
    whole module" is exactly a module docstring.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc, _function in owned_docstrings(b, tests=False):
            for number, kind, version in _version_directives(b, doc.lines(), path):
                out.append(target(f"version-string:{path}:{number}", path,
                                  (number, number), (path, number, kind, version,
                                                     doc.kind),
                                  f".. {kind}:: {version}"))
        for path in _prose_pages(b):
            for number, kind, version in _version_directives(b, _rst_lines(b, path), path):
                out.append(target(f"version-string:{path}:{number}", path,
                                  (number, number), (path, number, kind, version, "page"),
                                  f".. {kind}:: {version}"))
        return out

    def pass_condition(self, t: Target):
        path, number, kind, version, owner_kind = t.payload
        if owner_kind == "module":
            return Violated(f"{path}:{number} applies a {kind} directive to a whole "
                            f"module")
        if version and len(version.split(".")) > 2:
            return Violated(f"{path}:{number} writes the version as {version}, micro "
                            f"component included")
        return Satisfied(f"{path}:{number} writes {kind} for version {version or '(none)'}")


# --- discouraged API and C/C++ headers ---------------------------------------------------------


def _discouraged(bundle: EvidenceBundle):
    """(path, doc, function) for docstrings that mark their API as discouraged."""
    out = []
    for path, _module, doc, function in owned_docstrings(bundle, tests=False):
        if not is_package_path(path):
            continue
        text = doc.text
        if not (_DISCOURAGED_WORD.search(text) or _DISCOURAGED_PREFIX in text):
            continue
        out.append((path, doc, function))
    return out


@rule(
    id="MATPLOTLIB-C233",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of the docstring, no newness qualifier
    reads=("files",),  # spec §5
    heuristic=True,
)
class DiscouragedApiCarriesADiscouragedAdmonition:
    """Pre-condition: each docstring the agent wrote or edited that says its API is
    discouraged.
    Pass condition: it says so in a ``.. admonition:: Discouraged`` block.

    §7.1: the antecedent is *the API being discouraged*, recognised however the author
    said it, so a docstring that already uses the admonition is a recorded pass. The
    summary-line prefix is C234's, and the two grade different artefacts (§7.5).

    Heuristic on the **pre-condition** (§6.3): "discouraged API" is approximated by the
    word appearing in the docstring, so an API discouraged in other words is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"discouraged-admonition:{path}:{doc.lineno}", path, doc.span(),
                       (path, doc), doc.owner[:120])
                for path, doc, _function in _discouraged(b)]

    def pass_condition(self, t: Target):
        path, doc = t.payload
        if any(_DISCOURAGED_ADMONITION.match(text) for _, text in doc.lines()):
            return Satisfied(f"{path}:{doc.lineno} marks the API with a Discouraged "
                             f"admonition")
        return Violated(f"{path}:{doc.lineno} calls the API discouraged without a "
                        f"'.. admonition:: Discouraged' block")


@rule(
    id="MATPLOTLIB-C234",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ADiscouragedSummaryLineCarriesThePrefix:
    """Pre-condition: each docstring the agent wrote or edited that says its API is
    discouraged.
    Pass condition: its summary line begins ``[*Discouraged*]``.

    The same antecedent as C233 on a different artefact: that rule asks for the
    admonition, this one for the summary prefix, and neither reads the other's (§7.5).

    Heuristic on the **pre-condition** for the reason C233 gives.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"discouraged-summary:{path}:{doc.lineno}", path, doc.span(),
                       (path, doc), doc.owner[:120])
                for path, doc, _function in _discouraged(b)]

    def pass_condition(self, t: Target):
        path, doc = t.payload
        summary = numpydoc(doc).summary_text()
        if summary.startswith(_DISCOURAGED_PREFIX):
            return Satisfied(f"{path}:{doc.lineno} prefixes its summary with "
                             f"{_DISCOURAGED_PREFIX}")
        return Violated(f"{path}:{doc.lineno} documents discouraged API whose summary "
                        f"line does not open with {_DISCOURAGED_PREFIX}: "
                        f"{summary[:60]}")


_C_DOC_BLOCK = re.compile(r"/\*[*!]?(?P<body>.*?)\*/", re.S)
_COMMENT_LEADER = re.compile(r"^\s*(?:\*|//[/!]?)\s?")
_C_HEADER = (".h", ".hpp", ".hh")


@rule(
    id="MATPLOTLIB-C248",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5: the comment block is in the patch
    heuristic=True,
)
class CHeaderDocumentationIsNumpydoc:
    """Pre-condition: each block comment the agent wrote in a C or C++ header that
    documents something -- one that names parameters or a return value.
    Pass condition: it is written in numpydoc form, with an underlined section heading.

    Heuristic on **both** layers (§6.2, §6.3). *Header documentation* is approximated by a
    block comment mentioning parameters or a return, so a one-line description is not
    seen; and numpydoc form is graded as *a recognised section name underlined with
    dashes*, the same structural subset C023 grades for Python.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            if not path.endswith(_C_HEADER):
                continue
            change = b.files[path]
            authored = change.authored_lines
            text = change.head_text or added_text(b, path)
            for match in _C_DOC_BLOCK.finditer(text):
                start = text[:match.start()].count("\n") + 1
                body = match.group("body")
                if not re.search(r"\b(param|parameter|return|arg)\w*\b", body, re.I):
                    continue
                if change.head_text is not None and start not in authored:
                    continue
                out.append(target(f"c-numpydoc:{path}:{start}", path, (start, start),
                                  (path, start, body), body.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, start, body = t.payload
        # A block comment's own leader -- ` * ` down the left margin -- is decoration, and
        # numpydoc's underline detector would read it as content.
        lines = [(n, _COMMENT_LEADER.sub("", line))
                 for n, line in enumerate(body.split("\n"), start)]
        if ds.find_headings(lines):
            return Satisfied(f"{path}:{start} documents in numpydoc form")
        return Violated(f"{path}:{start} documents parameters or a return value without "
                        f"a numpydoc section heading")


# --- gallery examples, plot types and tags --------------------------------------------------

SGSKIP = "sgskip"
CELL_SEPARATOR = "# %%"
MPL_GALLERY_STYLE = "_mpl-gallery"
GALLERY_ORDER = ("gallery_order.txt", "gallery_order.py")
SAMPLE_DATA_ROOT = "lib/matplotlib/mpl-data/sample_data/"
DATA_SUFFIXES = (".csv", ".npz", ".npy", ".json", ".dat", ".txt", ".tsv", ".xls",
                 ".xlsx", ".gz")
#: The rendered gallery is 720px wide, 896px for the wider layout; at the default 100 dpi
#: that is a figure width of 7.2 or 8.96 inches (C070).
MAX_FIGURE_WIDTH_INCHES = 8.96
DEFAULT_DPI = 100.0
_FIGSIZE = re.compile(r"figsize\s*=\s*\(\s*(?P<w>[\d.]+)\s*,\s*(?P<h>[\d.]+)\s*\)")
_DPI = re.compile(r"\bdpi\s*=\s*(?P<dpi>[\d.]+)")
_SHOW_CALL = re.compile(r"^\s*plt\.show\s*\(\s*\)\s*$")
_PLOTTING_CALL = re.compile(r"\b(?:plt|ax|axs|fig)\.\w+\s*\(|\bsubplots\s*\(")
_TAGS_DIRECTIVE = re.compile(r"^\s*\.\.\s+tags::\s*(?P<tags>.*)$")
_REFERENCES_ADMONITION = re.compile(r"^\s*\.\.\s+admonition::\s*References", re.I)
_SAMPLE_DATA_CALL = re.compile(r"\bcbook\.get_sample_data\s*\(\s*[\"'](?P<name>[^\"']+)")
_DATASET_HINT = re.compile(r"\b(?:dataset|data\s+set|sample data)\b", re.I)
_CITATION = re.compile(r"https?://|\b(?:source|courtesy of|data from|provided by)\b", re.I)
_GERUND = re.compile(r"^\s*(?P<word>[A-Za-z]+ing)\b")
_PAST_OR_FUTURE = re.compile(r"\b(?:will|shall|was|were|had|has been|have been|"
                             r"is being|are being|would|used to)\b", re.I)
#: `to be` plus a past participle. The `-ed`/`-en` suffix catches the regular ones; the
#: list is the irregular participles matplotlib's own prose reaches for.
_PASSIVE = re.compile(r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?"
                      r"(?:\w+(?:ed|en)|drawn|shown|known|made|built|kept|sent|held|"
                      r"found|set|done|thrown|blown|flown|left|read|put|split)\b", re.I)
_DIRECTIVE_SENTENCE = re.compile(r"\b(?:you|we|one|the user|users)\b[^.]*"
                                 r"\b(?:should|must|can|need|have to|will|may)\b"
                                 r"|\blet's\b|\bplease\b", re.I)
_SUBJECT_PRONOUN = re.compile(r"^\s*(?:you|we|one|the user|users|let's)\b", re.I)
_NUMBERED_ITEM = re.compile(r"^\s*(?P<number>\d+)[.)]\s+(?P<text>\S.*)$")
_MARKDOWN_TABLE = re.compile(r"^\s*\|.*\|\s*$")
#: The `| --- | --- |` rule that makes a run of pipe rows a Markdown table rather than
#: the body of a reST grid table.
_MD_SEPARATOR = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
_GRID_TABLE = re.compile(r"^\s*\+[-=+]+\+\s*$")
_SIMPLE_TABLE = re.compile(r"^\s*=+(?:\s+=+)+\s*$")
_OUTPUT_PROMPT = re.compile(r"^\s*>>> ")
_CONTINUATION_PROMPT = re.compile(r"^\s*\.\.\. ")
#: A verb that a heading in the second-person imperative would open with.
_IMPERATIVE_OPENERS = ("add", "write", "use", "run", "install", "build", "create",
                       "choose", "set", "make", "check", "report", "submit", "review",
                       "contribute", "document", "test", "release", "deprecate", "file",
                       # the plotting verbs a gallery title opens with
                       "draw", "plot", "show", "display", "style", "label", "annotate",
                       "fill", "place", "align", "combine", "shade", "colour", "color",
                       "map", "scale", "customise", "customize", "compare", "highlight")


def _gallery_docstring(bundle: EvidenceBundle, path: str):
    """The module docstring of a gallery example, parsed, or None."""
    from compliance.extractors import python_ast as pa

    module = pa.parse_module(bundle.files[path].head_text, path)
    if not module.ok:
        return None, None
    doc = next((d for d in module.docstrings if d.kind == "module"), None)
    return module, doc


def _gallery_title(doc) -> tuple[int, str]:
    if doc is None:
        return (0, "")
    titles = titles_of(doc.lines())
    return titles[0] if titles else (0, "")


def _example_targets(bundle: EvidenceBundle, prefix: str, *, mode: str = "touched",
                     roots=None):
    """(path, module, doc, Target) for each gallery source the agent's edit reaches."""
    out = []
    for path in gallery_examples(bundle, mode=mode):
        if roots is not None and not path.startswith(roots):
            continue
        module, doc = _gallery_docstring(bundle, path)
        if module is None:
            continue
        out.append((path, module, doc,
                    target(f"{prefix}:{path}", path, None, None, path)))
    return out


@rule(
    id="MATPLOTLIB-C049",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- naming a file is naming one the agent added
    reads=("files",),  # spec §5: the code and the file name are both in the patch
    heuristic=True,
)
class AnExampleThatPlotsNothingIsNamedSgskip:
    """Pre-condition: each gallery example the agent added that draws nothing.
    Pass condition: ``sgskip`` is in its file name.

    Split from C137 by the same proxy (§7.5): an example that *does* draw is that rule's,
    and must end with ``show()``; one that does not is this rule's, and must say so in its
    name. No example is graded by both.

    Heuristic on the **pre-condition** (§6.3): "should not have a plot generated" is
    approximated by the file containing no plotting call, so an example that plots through
    a helper is selected and reads as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, _doc, tgt in _example_targets(b, "sgskip", mode="created"):
            if _PLOTTING_CALL.search(module.source):
                continue
            out.append(target(tgt.key, path, None, path, tgt.snippet))
        return out

    def pass_condition(self, t: Target):
        path: str = t.payload
        if SGSKIP in path.rsplit("/", 1)[-1]:
            return Satisfied(f"{path} names itself {SGSKIP}, so no plot is generated")
        return Violated(f"{path} generates no plot and is not named {SGSKIP}, so the "
                        f"gallery builds an empty figure for it")


@rule(
    id="MATPLOTLIB-C050",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class NarrativeBlocksUseTheCellSeparator:
    """Pre-condition: each gallery example the agent wrote or edited that carries a block
    of narrative comment lines below its module docstring.
    Pass condition: every such block opens with the ``# %%`` separator.

    Heuristic on the **pre-condition** (§6.3): *narrative text* is approximated by a run of
    two or more consecutive full-line comments, so a one-line note is not seen and a
    two-line explanation of the code below is wrongly selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, doc, tgt in _example_targets(b, "cell-separator"):
            lines = module.source.split("\n")
            start = (doc.end_lineno if doc is not None else 0)
            run: list[tuple[int, str]] = []
            for number, text in enumerate(lines, 1):
                if number <= start:
                    continue
                if text.lstrip().startswith("#"):
                    run.append((number, text))
                    continue
                if len(run) >= 2:
                    out.append(target(f"{tgt.key}:{run[0][0]}", path,
                                      (run[0][0], run[-1][0]), (path, run),
                                      run[0][1].strip()[:120]))
                run = []
            if len(run) >= 2:
                out.append(target(f"{tgt.key}:{run[0][0]}", path,
                                  (run[0][0], run[-1][0]), (path, run),
                                  run[0][1].strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, run = t.payload
        if run[0][1].strip().startswith(CELL_SEPARATOR):
            return Satisfied(f"{path}:{run[0][0]} opens its narrative block with "
                             f"{CELL_SEPARATOR}")
        return Violated(f"{path}:{run[0][0]} starts a {len(run)}-line narrative block "
                        f"without the {CELL_SEPARATOR} separator")


@rule(
    id="MATPLOTLIB-C051",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class APublicDatasetIsCited:
    """Pre-condition: each gallery example the agent wrote that loads sample data or names
    a dataset.
    Pass condition: its prose names a source -- a URL, or an attribution phrase.

    Asks only for the citation. *Whether* the data should have been inlined is C052's and
    *where* an un-inlinable file goes is C053's, so the three sentences split the subject
    three ways (§7.5).

    Heuristic on **both** layers (§6.2, §6.3): the dataset is recognised from a
    ``get_sample_data`` call or the word "dataset", and the citation from a URL or one of
    a handful of attribution phrases.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, doc, tgt in _example_targets(b, "cite-dataset"):
            if not (_SAMPLE_DATA_CALL.search(module.source)
                    or _DATASET_HINT.search(doc.text if doc else "")):
                continue
            out.append(target(tgt.key, path, None, (path, module, doc), tgt.snippet))
        return out

    def pass_condition(self, t: Target):
        path, module, doc = t.payload
        text = (doc.text if doc else "") + "\n" + "\n".join(
            line for line in module.source.split("\n") if line.lstrip().startswith("#"))
        if _CITATION.search(text):
            return Satisfied(f"{path} cites the source of its sample data")
        return Violated(f"{path} uses a public dataset without citing its source")


@rule(
    id="MATPLOTLIB-C052",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class SampleDataIsWrittenOutInTheExample:
    """Pre-condition: each gallery example the agent wrote that supplies sample data.
    Pass condition: the data is written out in the example, or the file it loads is one
    the contribution adds under the sample-data directory -- the "not feasible" case the
    sentence allows for.

    Heuristic on **both** layers (§6.2, §6.3): supplying data is recognised from a
    ``get_sample_data`` call or a literal array, and "not feasible to inline" is
    approximated by the file being shipped as sample data in the same change.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, _doc, tgt in _example_targets(b, "inline-data"):
            loads = _SAMPLE_DATA_CALL.search(module.source)
            inline = re.search(r"np\.(?:array|linspace|arange|random)\s*\(|=\s*\[",
                               module.source)
            if not (loads or inline):
                continue
            out.append(target(tgt.key, path, None, (path, module, b), tgt.snippet))
        return out

    def pass_condition(self, t: Target):
        path, module, bundle = t.payload
        loaded = _SAMPLE_DATA_CALL.search(module.source)
        if not loaded:
            return Satisfied(f"{path} writes its sample data out in the example code")
        name = loaded.group("name")
        shipped = [p for p in sorted(bundle.files)
                   if p.startswith(SAMPLE_DATA_ROOT) and p.endswith(name)]
        if shipped:
            return Satisfied(f"{path} loads {name}, which the change ships as sample "
                             f"data because it is too large to inline")
        return Violated(f"{path} reaches for cbook.get_sample_data({name!r}) instead of "
                        f"writing its data out in the example")


@rule(
    id="MATPLOTLIB-C053",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the target is a data file the agent added
    reads=("files",),  # spec §5: the path is the whole question
)
class LargeSampleDataGoesInTheSampleDataDirectory:
    """Pre-condition: each data file the agent added alongside a gallery example.
    Pass condition: it is under :file:`lib/matplotlib/mpl-data/sample_data/`.

    Not heuristic (§6.2): the destination is a path the rule names, and the check is a
    prefix. Whether the data should have been inlined instead is C052's (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            change = b.files[path]
            if not change.is_new or not path.lower().endswith(DATA_SUFFIXES):
                continue
            if not (path.startswith(GALLERY_SOURCE_ROOTS)
                    or path.startswith(SAMPLE_DATA_ROOT)):
                continue
            out.append(target(f"sample-data:{path}", path, None, path, f"{path} is new"))
        return out

    def pass_condition(self, t: Target):
        path: str = t.payload
        if path.startswith(SAMPLE_DATA_ROOT):
            return Satisfied(f"{path} is filed under {SAMPLE_DATA_ROOT}")
        return Violated(f"{path} ships sample data beside the example instead of under "
                        f"{SAMPLE_DATA_ROOT}")


def _references_block(module) -> list[tuple[int, str]]:
    lines = list(enumerate(module.source.split("\n"), 1))
    for index, (number, text) in enumerate(lines):
        if _REFERENCES_ADMONITION.match(text.lstrip("# ")):
            return lines[index:]
    return []


@rule(
    id="MATPLOTLIB-C054",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- graded on examples the agent added
    reads=("files",),  # spec §5
    heuristic=True,
)
class AnExampleListsItsShowcasedFunctions:
    """Pre-condition: each gallery example the agent added.
    Pass condition: it carries a References admonition naming the functions it showcases.

    Asks only that the block exists. What it must contain for a dual-API function is
    C056's, which fires only where the block is already there (§7.5).

    Heuristic on the **pass condition** (§6.2): the admonition is recognised by its
    directive line, and "the showcased functions" by the block containing at least one
    reference, rather than by comparing against the calls the example makes.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(tgt.key, path, None, (path, module), tgt.snippet)
                for path, module, _doc, tgt in _example_targets(b, "references",
                                                                mode="created")]

    def pass_condition(self, t: Target):
        path, module = t.payload
        block = _references_block(module)
        if not block:
            return Violated(f"{path} ends without a References admonition listing the "
                            f"functions it showcases")
        text = "\n".join(line for _, line in block)
        if _ROLE.search(text) or _MPL_DOTTED.search(text):
            return Satisfied(f"{path} lists its showcased functions in a References "
                             f"admonition")
        return Violated(f"{path} has a References admonition that names no function")


@rule(
    id="MATPLOTLIB-C056",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of the block's contents
    reads=("files",),  # spec §5
    heuristic=True,
)
class ADualApiFunctionIsListedBothWaysWithPyplotSecond:
    """Pre-condition: each References admonition the agent wrote that names a function
    existing on both the Axes/Figure side and the pyplot side.
    Pass condition: both references are listed, pyplot second.

    Fires only where C054's admonition already exists, so a missing block is one violation
    rather than two (§7.5).

    Heuristic on the **pre-condition** (§6.3): "a dual-API function" is approximated by a
    published list of the names that exist on both sides.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, _doc, tgt in _example_targets(b, "dual-api"):
            block = _references_block(module)
            if not block:
                continue
            text = "\n".join(line for _, line in block)
            names = {n.split(".")[-1] for n in _MPL_DOTTED.findall(text)}
            names |= {m.group("target").lstrip("~.").split(".")[-1]
                      for m in _ROLE.finditer(text)}
            for name in sorted(names & DUAL_API_NAMES):
                out.append(target(f"{tgt.key}:{name}", path, None, (path, name, text),
                                  f"{path} showcases {name}"))
        return out

    def pass_condition(self, t: Target):
        path, name, text = t.payload
        axes = re.search(rf"(?:axes\.Axes|Figure)\.{re.escape(name)}\b", text)
        pyplot = re.search(rf"pyplot\.{re.escape(name)}\b", text)
        if not axes:
            return Violated(f"{path} lists only the pyplot reference for {name}, not the "
                            f"Axes or Figure one")
        if not pyplot:
            return Violated(f"{path} lists only the Axes/Figure reference for {name}, "
                            f"not the pyplot one")
        if pyplot.start() < axes.start():
            return Violated(f"{path} lists pyplot.{name} before the Axes/Figure "
                            f"reference; pyplot comes second")
        return Satisfied(f"{path} lists both references for {name}, pyplot second")


@rule(
    id="MATPLOTLIB-C057",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the target is an example the agent added
    reads=("files",),  # spec §5: the order file is in the patch or it is not
    heuristic=True,
)
class EveryExampleIsListedInAnExplicitGalleryOrder:
    """Pre-condition: each gallery example the agent added, when the contribution also
    carries a gallery-order file that has no ``*`` placeholder.
    Pass condition: the example is named in it.

    The order file must be in the patch: without it there is nothing to check against, and
    the rule finds no target rather than guessing at a file it cannot see.

    Heuristic on the **pre-condition** (§6.3): the order file is recognised by name, and
    the placeholder by a bare ``*`` on one of its lines.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        orders = [p for p in sorted(b.files) if p.rsplit("/", 1)[-1] in GALLERY_ORDER]
        explicit = []
        for order in orders:
            text = b.files[order].head_text or added_text(b, order)
            if not re.search(r"^\s*[\"']?\*[\"']?\s*,?\s*$", text, re.M):
                explicit.append((order, text))
        if not explicit:
            return []
        out = []
        for path, _module, _doc, tgt in _example_targets(b, "gallery-order",
                                                         mode="created"):
            out.append(target(tgt.key, path, None, (path, explicit), tgt.snippet))
        return out

    def pass_condition(self, t: Target):
        path, explicit = t.payload
        name = path.rsplit("/", 1)[-1]
        for order, text in explicit:
            if name in text or name[:-3] in text:
                return Satisfied(f"{path} is listed in {order}")
        return Violated(f"{path} is missing from {explicit[0][0]}, which has no '*' "
                        f"placeholder to catch it")


@rule(
    id="MATPLOTLIB-C058",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the target is a page the agent added
    reads=("files",),  # spec §5
    heuristic=True,
)
class ARawRstFileInAGalleryIsAddedToAToctree:
    """Pre-condition: each reST file the agent added to a gallery directory that also
    holds Python examples.
    Pass condition: some file in the change adds it to a toctree.

    Heuristic on the **pass condition** (§6.2): the toctree entry is recognised by the
    file's stem appearing under a ``.. toctree::`` directive somewhere in the change, not
    by resolving the toctree's own paths.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            change = b.files[path]
            if not change.is_new or not path.endswith(DOC_SUFFIXES):
                continue
            if not path.startswith(GALLERY_SOURCE_ROOTS):
                continue
            folder = path.rsplit("/", 1)[0]
            mixed = any(p.startswith(folder + "/") and p.endswith(".py") for p in b.files)
            if not mixed:
                continue
            out.append(target(f"gallery-toctree:{path}", path, None, (path, b),
                              f"{path} is a new raw reST page in a mixed gallery folder"))
        return out

    def pass_condition(self, t: Target):
        path, bundle = t.payload
        stem = path.rsplit("/", 1)[-1][:-4]
        for other in sorted(bundle.files):
            if not other.endswith(DOC_SUFFIXES):
                continue
            lines = list(_rst_lines(bundle, other))
            for index, (number, text) in enumerate(lines):
                match = _DIRECTIVE.match(text)
                if not match or match.group("name") != "toctree":
                    continue
                body = "\n".join(t for _, t in lines[index + 1:index + 40])
                if stem in body:
                    return Satisfied(f"{path} is listed in the toctree at "
                                     f"{other}:{number}")
        return Violated(f"{path} is a raw reST file in a mixed gallery folder and no "
                        f"toctree lists it")


@rule(
    id="MATPLOTLIB-C062",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of the title, no newness qualifier
    reads=("files",),  # spec §5
)
class AGalleryTitleDoesNotSayDemo:
    """Pre-condition: each gallery example title the agent wrote.
    Pass condition: it does not use the word "demo".

    Not heuristic (§6.2): the forbidden word is named in the rule and matched by name.
    Reads gallery titles only; the sentence-case rule for documentation pages is C002's
    and reads pages under :file:`doc/` (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc, tgt in _example_targets(b, "demo-title"):
            number, title = _gallery_title(doc)
            if not title:
                continue
            out.append(target(tgt.key, path, (number, number), (path, number, title),
                              title[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, title = t.payload
        if re.search(r"\bdemos?\b", title, re.I):
            return Violated(f"{path}:{number} titles the example {title!r}, which uses "
                            f"the word demo")
        return Satisfied(f"{path}:{number} titles the example {title!r}")


@rule(
    id="MATPLOTLIB-C064",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class AGalleryTitleVerbIsSimplePresent:
    """Pre-condition: each gallery example title the agent wrote that opens with a verb
    form.
    Pass condition: the verb is simple present, not a gerund or a past form.

    Heuristic on **both** layers (§6.2, §6.3): "needs a verb" is approximated by the title
    opening with an ``-ing`` or ``-ed`` word or with one of a list of common imperative
    verbs, and the tense by the suffix -- neither is a parse of English.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc, tgt in _example_targets(b, "title-tense"):
            number, title = _gallery_title(doc)
            first = title.split()[0].lower() if title.split() else ""
            if not first:
                continue
            if not (first.endswith("ing") or first.endswith("ed")
                    or first in _IMPERATIVE_OPENERS):
                continue
            out.append(target(tgt.key, path, (number, number),
                              (path, number, title, first), title[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, title, first = t.payload
        if first.endswith("ing"):
            return Violated(f"{path}:{number} opens the title with the gerund {first!r}; "
                            f"the guide asks for the simple present")
        if first.endswith("ed") and first not in _IMPERATIVE_OPENERS:
            return Violated(f"{path}:{number} opens the title with the past form "
                            f"{first!r}")
        return Satisfied(f"{path}:{number} opens the title {title!r} in the simple "
                         f"present")


@rule(
    id="MATPLOTLIB-C070",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5: the figure size is in the patch
    heuristic=True,
)
class ACustomisedExampleFigureFitsTheGalleryWidth:
    """Pre-condition: each gallery example the agent wrote that sets its own figure size.
    Pass condition: the rendered width stays within the gallery's limit.

    Heuristic on the **pass condition** (§6.2): the rendered width is computed as
    ``figsize`` times the dpi the example sets, falling back to matplotlib's default of
    100, so a figure resized at save time is measured wrongly. The wider 896px limit is
    used, so the rate is an upper bound.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, _doc, tgt in _example_targets(b, "figure-width"):
            for match in _FIGSIZE.finditer(module.source):
                number = module.source[:match.start()].count("\n") + 1
                dpi = _DPI.search(module.source[match.end():match.end() + 200])
                out.append(target(f"{tgt.key}:{number}", path, (number, number),
                                  (path, number, float(match.group("w")),
                                   float(dpi.group("dpi")) if dpi else DEFAULT_DPI),
                                  match.group(0)))
        return out

    def pass_condition(self, t: Target):
        path, number, width, dpi = t.payload
        pixels = width * dpi
        limit = MAX_FIGURE_WIDTH_INCHES * DEFAULT_DPI
        if pixels <= limit:
            return Satisfied(f"{path}:{number} renders {pixels:.0f}px wide, within the "
                             f"{limit:.0f}px limit")
        return Violated(f"{path}:{number} renders {pixels:.0f}px wide, over the "
                        f"{limit:.0f}px gallery limit")


@rule(
    id="MATPLOTLIB-C072",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class APlotTypesTitleIsTheMethodSignature:
    """Pre-condition: each plot-types entry the agent wrote.
    Pass condition: its title is a method call with its required arguments.

    Heuristic on the **pass condition** (§6.2): "the method signature and its required
    arguments" is graded as ``name(arg, ...)`` with at least one argument, so a method
    that genuinely takes none reads as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc, tgt in _example_targets(b, "plot-type-title",
                                                        roots=PLOT_TYPES_ROOTS):
            number, title = _gallery_title(doc)
            if not title:
                continue
            out.append(target(tgt.key, path, (number, number), (path, number, title),
                              title[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, title = t.payload
        match = re.fullmatch(r"\s*(?P<name>[\w.]+)\((?P<args>[^)]*)\)\s*", title)
        if match and match.group("args").strip():
            return Satisfied(f"{path}:{number} titles the entry with the signature "
                             f"{title!r}")
        return Violated(f"{path}:{number} titles the plot-types entry {title!r} rather "
                        f"than with the method signature and its required arguments")


@rule(
    id="MATPLOTLIB-C073",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class APlotTypesEntryIsOneSentenceWithALink:
    """Pre-condition: each plot-types entry the agent wrote whose docstring says something
    below its title.
    Pass condition: the description is one sentence and links to the method's API
    documentation.

    Heuristic on the **pass condition** (§6.2): "one sentence" is counted by terminal
    punctuation, so a description containing an abbreviation reads as two.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc, tgt in _example_targets(b, "plot-type-body",
                                                        roots=PLOT_TYPES_ROOTS):
            if doc is None:
                continue
            number, title = _gallery_title(doc)
            body = [text for line, text in doc.lines()
                    if line > number + 1 and text.strip()]
            if not body:
                continue
            out.append(target(tgt.key, path, doc.span(), (path, body), " ".join(body)[:120]))
        return out

    def pass_condition(self, t: Target):
        path, body = t.payload
        text = " ".join(line.strip() for line in body).strip()
        sentences = ds.summary_sentences([(0, text)])
        if len(sentences) > 1:
            return Violated(f"{path} describes the entry in {len(sentences)} sentences, "
                            f"not one")
        if not (_ROLE.search(text) or _MPL_DOTTED.search(text)
                or _DEFAULT_ROLE.search(text)):
            return Violated(f"{path} describes the entry without linking to the method's "
                            f"API documentation")
        return Satisfied(f"{path} describes the entry in one sentence with an API link")


@rule(
    id="MATPLOTLIB-C075",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class APlotTypesEntryUsesTheGalleryStylesheet:
    """Pre-condition: each plot-types entry the agent wrote.
    Pass condition: it selects the ``_mpl-gallery`` stylesheet.

    Not heuristic (§6.2): the stylesheet is a name the rule states, and the check is
    whether the file selects it.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(tgt.key, path, None, (path, module.source), tgt.snippet)
                for path, module, _doc, tgt in _example_targets(b, "gallery-style",
                                                                roots=PLOT_TYPES_ROOTS)]

    def pass_condition(self, t: Target):
        path, source = t.payload
        if MPL_GALLERY_STYLE in source:
            return Satisfied(f"{path} styles the entry with {MPL_GALLERY_STYLE}")
        return Violated(f"{path} is a plot-types entry that never selects the "
                        f"{MPL_GALLERY_STYLE} stylesheet")


# --- expository language and formatting ----------------------------------------------------


def _sentences(bundle: EvidenceBundle):
    """(path, line number, sentence) for each prose sentence the agent wrote."""
    out = []
    for path, number, text in prose_lines(bundle):
        clean = strip_markup(text).strip()
        if not clean or clean.startswith(("#", "*", "-", "+", "|")):
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", clean):
            if len(sentence.split()) >= 3:
                out.append((path, number, sentence.strip()))
    return out


@rule(
    id="MATPLOTLIB-C126",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class AVerbPhraseHeadingIsImperative:
    """Pre-condition: each section heading the agent wrote that opens with a verb form.
    Pass condition: the verb is a second-person imperative, not a gerund.

    Heuristic on **both** layers (§6.2, §6.3): "a verb-phrase heading" is approximated by
    the heading opening with an ``-ing`` word or with one of a list of common imperative
    verbs, and the grading is the ``-ing`` suffix -- neither is a parse of English.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _prose_pages(b):
            authored = b.files[path].authored_lines
            for number, text, _char in _headings(_rst_lines(b, path)):
                if number not in authored:
                    continue
                first = strip_markup(text).split()[0].lower() if text.split() else ""
                if not (first.endswith("ing") or first in _IMPERATIVE_OPENERS):
                    continue
                out.append(target(f"heading-imperative:{path}:{number}", path,
                                  (number, number), (path, number, text, first),
                                  text[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, text, first = t.payload
        if _GERUND.match(first):
            return Violated(f"{path}:{number} heads the section with the gerund "
                            f"{first!r}; the guide asks for the imperative")
        return Satisfied(f"{path}:{number} heads the section imperatively: {text[:60]!r}")


@rule(
    id="MATPLOTLIB-C127",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DirectedInstructionsAreImperative:
    """Pre-condition: each prose sentence the agent wrote that directs the reader.
    Pass condition: it is written as an imperative, with no subject pronoun.

    Split from C129 (§7.5): a directive sentence is graded here for its mood, and every
    other sentence is graded there for its tense, so no sentence is graded by both.

    Heuristic on **both** layers (§6.2, §6.3): a directed instruction is recognised from a
    subject pronoun with a modal, or from "please"/"let's"; and the imperative is graded
    as the absence of a leading subject.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"imperative:{path}:{number}:{sentence[:20]}", path,
                       (number, number), (path, number, sentence), sentence[:120])
                for path, number, sentence in _sentences(b)
                if _DIRECTIVE_SENTENCE.search(sentence)]

    def pass_condition(self, t: Target):
        path, number, sentence = t.payload
        if _SUBJECT_PRONOUN.match(sentence):
            return Violated(f"{path}:{number} directs the reader with a subject pronoun "
                            f"rather than an imperative: {sentence[:60]!r}")
        return Satisfied(f"{path}:{number} directs the reader imperatively")


@rule(
    id="MATPLOTLIB-C129",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ExplanationsArePresentSimple:
    """Pre-condition: each prose sentence the agent wrote that is an explanation rather
    than an instruction.
    Pass condition: it uses the present simple tense.

    Split from C127 (§7.5): an instruction is that rule's, and finds no target here.

    Heuristic on the **pass condition** (§6.2): tense is detected from auxiliaries --
    ``will``, ``was``, ``has been``, ``is being`` and the rest -- which is a pattern match
    standing in for grammar, so a sentence that quotes a past tense reads as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"present-simple:{path}:{number}:{sentence[:20]}", path,
                       (number, number), (path, number, sentence), sentence[:120])
                for path, number, sentence in _sentences(b)
                if not _DIRECTIVE_SENTENCE.search(sentence)]

    def pass_condition(self, t: Target):
        path, number, sentence = t.payload
        if match := _PAST_OR_FUTURE.search(sentence):
            return Violated(f"{path}:{number} explains in a tense other than the present "
                            f"simple ({match.group(0)!r}): {sentence[:60]!r}")
        return Satisfied(f"{path}:{number} explains in the present simple")


@rule(
    id="MATPLOTLIB-C131",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ProseIsInTheActiveVoice:
    """Pre-condition: each prose sentence the agent wrote.
    Pass condition: it is in the active voice.

    Grades voice only. Mood is C127's and tense C129's, so a badly written sentence is
    counted once per property the guide legislates rather than once per rule (§7.5).

    Heuristic on the **pass condition** (§6.2): the passive is detected as a form of *to
    be* followed by a past participle, approximated by an ``-ed``/``-en`` suffix, so
    "is red" is safe but "is a supported backend" reads as passive.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"active-voice:{path}:{number}:{sentence[:20]}", path,
                       (number, number), (path, number, sentence), sentence[:120])
                for path, number, sentence in _sentences(b)]

    def pass_condition(self, t: Target):
        path, number, sentence = t.payload
        if match := _PASSIVE.search(sentence):
            return Violated(f"{path}:{number} is written in the passive voice "
                            f"({match.group(0)!r}): {sentence[:60]!r}")
        return Satisfied(f"{path}:{number} is written in the active voice")


@rule(
    id="MATPLOTLIB-C136",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a comment the agent wrote
    reads=("files",),  # spec §5
    heuristic=True,
)
class ACommentPrecedesTheCodeItDescribes:
    """Pre-condition: each full-line comment the agent wrote in a gallery example.
    Pass condition: code follows it, so it describes what comes next rather than what came
    before.

    Heuristic on the **pre-condition** (§6.3): a comment's subject is not observable, so
    "describes the code" is approximated by there being code after it in the same block; a
    trailing note that deliberately closes a section reads as a violation. Trailing
    comments on a code line are excluded, which the sentence explicitly permits.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, doc, tgt in _example_targets(b, "comment-position"):
            authored = b.files[path].authored_lines
            lines = module.source.split("\n")
            start = doc.end_lineno if doc is not None else 0
            for number, text in enumerate(lines, 1):
                if number <= start or number not in authored:
                    continue
                stripped = text.strip()
                if not stripped.startswith("#") or stripped.startswith(CELL_SEPARATOR):
                    continue
                following = [t for t in lines[number:] if t.strip()]
                out.append(target(f"{tgt.key}:{number}", path, (number, number),
                                  (path, number, stripped, following),
                                  stripped[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, text, following = t.payload
        for line in following:
            if line.strip().startswith("#"):
                continue
            return Satisfied(f"{path}:{number} comments the code that follows it")
        return Violated(f"{path}:{number} places a comment after the code it describes, "
                        f"with nothing left for it to introduce: {text[:60]!r}")


@rule(
    id="MATPLOTLIB-C137",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class AVisualExampleEndsWithShow:
    """Pre-condition: each gallery example the agent wrote that draws something.
    Pass condition: it ends with a ``plt.show()`` call.

    Split from C049 by the same proxy (§7.5): an example that draws nothing is that rule's
    and must be named ``sgskip``; this one takes the examples that do draw.

    Heuristic on the **pre-condition** (§6.3): drawing is recognised from a pyplot or Axes
    method call, so an example that plots through a helper is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, _doc, tgt in _example_targets(b, "ends-with-show"):
            if not _PLOTTING_CALL.search(module.source):
                continue
            out.append(target(tgt.key, path, None, (path, module.source), tgt.snippet))
        return out

    def pass_condition(self, t: Target):
        path, source = t.payload
        content = [line for line in source.split("\n") if line.strip()]
        if not content:
            return Violated(f"{path} draws nothing and ends with nothing")
        if _SHOW_CALL.match(content[-1]):
            return Satisfied(f"{path} ends with plt.show()")
        if any(_SHOW_CALL.match(line) for line in content):
            return Violated(f"{path} calls plt.show() but not as its last statement")
        return Violated(f"{path} produces a visual and never calls plt.show()")


@rule(
    id="MATPLOTLIB-C138",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DocumentationExamplesCarryNoOutputLines:
    """Pre-condition: each interactive block the agent wrote in a gallery example -- a run
    of ``>>>`` prompts.
    Pass condition: no line of captured Python output follows the prompts.

    Heuristic on the **pre-condition** (§6.3): "a documentation example" is scoped to the
    gallery sources, where a prompt is always a transcript; docstring doctests are
    deliberately out of scope, since their expected output is what makes them tests.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module, _doc, tgt in _example_targets(b, "no-output"):
            lines = list(enumerate(module.source.split("\n"), 1))
            for index, (number, text) in enumerate(lines):
                if not _OUTPUT_PROMPT.match(text.lstrip("# ")):
                    continue
                following = [t for _, t in lines[index + 1:index + 6]]
                out.append(target(f"{tgt.key}:{number}", path, (number, number),
                                  (path, number, following), text.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, following = t.payload
        for text in following:
            body = text.lstrip("# ")
            if not body.strip():
                break
            if _OUTPUT_PROMPT.match(body) or _CONTINUATION_PROMPT.match(body):
                continue
            return Violated(f"{path}:{number} leaves Python output in the example: "
                            f"{body.strip()[:60]!r}")
        return Satisfied(f"{path}:{number} shows input without leaving its output behind")


@rule(
    id="MATPLOTLIB-C140",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ANumberedListIsForOrderedActions:
    """Pre-condition: each numbered list the agent wrote on a documentation page.
    Pass condition: its items are actions -- each opens with a verb.

    Heuristic on the **pass condition** (§6.2): "actions performed in a determined order"
    is approximated by every item opening with one of a list of imperative verbs or with
    an ``-ing`` form, so a list of ordered steps phrased as noun phrases reads as a
    violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _prose_pages(b):
            authored = b.files[path].authored_lines
            lines = list(_rst_lines(b, path))
            run: list[tuple[int, str]] = []
            for number, text in lines + [(0, "")]:
                match = _NUMBERED_ITEM.match(text)
                if match:
                    run.append((number, match.group("text")))
                    continue
                if len(run) >= 2 and any(n in authored for n, _ in run):
                    out.append(target(f"numbered-list:{path}:{run[0][0]}", path,
                                      (run[0][0], run[-1][0]), (path, run),
                                      run[0][1][:120]))
                run = []
        return out

    def pass_condition(self, t: Target):
        path, run = t.payload
        for number, text in run:
            first = strip_markup(text).split()[0].lower().strip(".,:;") if text.split() else ""
            if first in _IMPERATIVE_OPENERS or first.endswith("ing"):
                continue
            return Violated(f"{path}:{number} numbers an item that is not an action: "
                            f"{text[:60]!r}")
        return Satisfied(f"{path}:{run[0][0]} numbers {len(run)} ordered actions")


def _table_blocks(bundle: EvidenceBundle, path: str):
    """(line number, kind, sample line) for each table the agent wrote on a page.

    Grid and simple tables are recognised first and claim every row between their borders,
    because a reST grid table's body rows are indistinguishable from Markdown rows on
    their own. What is left is Markdown -- a header row followed by a ``| --- |``
    separator -- and the two table directives.
    """
    authored = bundle.files[path].authored_lines
    lines = list(_rst_lines(bundle, path))
    consumed: set[int] = set()
    out = []
    for index, (number, text) in enumerate(lines):
        if number in consumed:
            continue
        if not (_GRID_TABLE.match(text) or _SIMPLE_TABLE.match(text)):
            continue
        span = [number]
        for following, following_text in lines[index + 1:]:
            if not following_text.strip():
                break
            span.append(following)
        if any(n in authored for n in span):
            out.append((number, "ascii", text.strip()))
        consumed.update(span)
    for index, (number, text) in enumerate(lines):
        if number in consumed:
            continue
        match = _DIRECTIVE.match(text)
        if match and match.group("name") in ("csv-table", "list-table"):
            if number in authored:
                out.append((number, match.group("name"), text.strip()))
            continue
        if not _MARKDOWN_TABLE.match(text):
            continue
        following = lines[index + 1][1] if index + 1 < len(lines) else ""
        span = [number]
        for other, other_text in lines[index + 1:]:
            if not _MARKDOWN_TABLE.match(other_text):
                break
            span.append(other)
        consumed.update(span)
        if _MD_SEPARATOR.match(following) and number in authored:
            out.append((number, "markdown", text.strip()))
    return out


@rule(
    id="MATPLOTLIB-C141",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class TablesAreReStructuredTextAsciiTables:
    """Pre-condition: each table the agent wrote that is neither a Markdown table nor a
    ``csv-table`` directive.
    Pass condition: it is a reST ASCII table -- a grid or a simple table.

    Markdown tables and ``csv-table`` are C142's, and this rule excludes them so a Markdown
    table is one violation rather than two (§7.5). What is left for this rule to catch is
    the reST table forms the guide does not want, ``list-table`` among them.

    Heuristic on the **pre-condition** (§6.3): a table is recognised from its own border
    syntax or its directive name, so a table drawn some other way is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _prose_pages(b):
            for number, kind, sample in _table_blocks(b, path):
                if kind in ("markdown", "csv-table"):
                    continue  # §7.5: C142's
                out.append(target(f"ascii-table:{path}:{number}", path, (number, number),
                                  (path, number, kind), sample[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, kind = t.payload
        if kind == "ascii":
            return Satisfied(f"{path}:{number} writes the table as a reST ASCII table")
        return Violated(f"{path}:{number} writes the table as a {kind} directive rather "
                        f"than as a reST ASCII table")


@rule(
    id="MATPLOTLIB-C142",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class NoMarkdownTablesAndNoCsvTable:
    """Pre-condition: each table the agent wrote on a documentation page.
    Pass condition: it is neither a Markdown table nor a ``csv-table`` directive.

    §7.1: a prohibition, so the antecedent is *writing a table* and the graded question is
    which form it took; an ASCII table is a recorded pass. C141 takes the forms this rule
    does not name (§7.5).

    Heuristic on the **pre-condition** for the reason C141 gives.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _prose_pages(b):
            for number, kind, sample in _table_blocks(b, path):
                out.append(target(f"table-form:{path}:{number}", path, (number, number),
                                  (path, number, kind), sample[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, kind = t.payload
        if kind == "markdown":
            return Violated(f"{path}:{number} writes a Markdown table, which Sphinx does "
                            f"not render")
        if kind == "csv-table":
            return Violated(f"{path}:{number} uses the csv-table directive, which the "
                            f"guide forbids")
        return Satisfied(f"{path}:{number} writes the table as reST, not Markdown or "
                         f"csv-table")


@rule(
    id="MATPLOTLIB-C272",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the feature, added to code that
                          # already existed; the example it demands is the artefact
    reads=("files",),  # spec §5
    heuristic=True,
)
class APlottingFeatureIsDemonstratedInTheGallery:
    """Pre-condition: a contribution that adds public plotting API.
    Pass condition: it also adds or edits a gallery example.

    Fires on the *feature*, not on the example (§7.1), so a contribution that ships no
    demonstration is a recorded violation rather than an absent row.

    Heuristic on the **pre-condition** (§6.3): *plotting-related* is approximated by a new
    public definition under :file:`lib/matplotlib/axes/` or in :file:`pyplot.py`, so a
    feature added elsewhere is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        plotting = [(p, name) for p, name, _line in new_public_defs(b)
                    if p.startswith(PLOTTING_MODULES)]
        if not plotting:
            return []
        path, name = plotting[0]
        return [target(f"gallery-demo:{b.instance_id}", path, None, (plotting, b),
                       f"{len(plotting)} new plotting definition(s), e.g. {name}")]

    def pass_condition(self, t: Target):
        plotting, bundle = t.payload
        examples = gallery_examples(bundle)
        if examples:
            return Satisfied(f"{plotting[0][1]} is demonstrated by {examples[0]}")
        return Violated(f"{plotting[0][1]} adds plotting API with no gallery example "
                        f"demonstrating it")


# --- tags -------------------------------------------------------------------------------------


def _tag_directives(bundle: EvidenceBundle, path: str, text: str):
    """(line number, [tag]) for each `.. tags::` directive in a file's text."""
    out = []
    for number, line in enumerate(text.split("\n"), 1):
        match = _TAGS_DIRECTIVE.match(line.lstrip("# "))
        if not match:
            continue
        tags = [t.strip() for t in match.group("tags").split(",") if t.strip()]
        out.append((number, tags))
    return out


@rule(
    id="MATPLOTLIB-C276",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class TheTagsDirectiveSitsAtTheBottomOfThePage:
    """Pre-condition: each ``.. tags::`` directive the agent wrote.
    Pass condition: nothing but the tags themselves follows it.

    Heuristic on the **pass condition** (§6.2): "at the bottom" is read as no further
    non-blank content after the directive and its own argument lines, so a page that ends
    with a licence footer reads as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            change = b.files[path]
            if not (path.endswith(DOC_SUFFIXES) or is_gallery_path(path)):
                continue
            text = change.head_text or added_text(b, path)
            lines = text.split("\n")
            for number, _tags in _tag_directives(b, path, text):
                following = [line for line in lines[number:] if line.strip()]
                out.append(target(f"tags-bottom:{path}:{number}", path, (number, number),
                                  (path, number, following), lines[number - 1][:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, following = t.payload
        for line in following:
            body = line.lstrip("# ").strip()
            if body.startswith((":", "-")) or (line[:1].isspace() and body):
                continue
            return Violated(f"{path}:{number} places the tags directive with "
                            f"{body[:40]!r} still below it")
        return Satisfied(f"{path}:{number} places the tags directive at the bottom of the "
                         f"page")


@rule(
    id="MATPLOTLIB-C277",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- graded on examples the agent added
    reads=("files",),  # spec §5
)
class EveryGalleryExampleCarriesATag:
    """Pre-condition: each gallery example the agent added.
    Pass condition: it carries a ``.. tags::`` directive naming at least one tag.

    Not heuristic (§6.2): the directive is named in the rule and the check is its presence
    with a non-empty argument. How a tag must be written is C280's and C281's (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"has-tags:{path}", path, None, (path, module.source), path)
                for path, module, _doc, _tgt in _example_targets(b, "has-tags",
                                                                 mode="created")]

    def pass_condition(self, t: Target):
        path, source = t.payload
        directives = [tags for _number, tags in _tag_directives(None, path, source)]
        if any(tags for tags in directives):
            return Satisfied(f"{path} carries {len(directives[0])} content tag(s)")
        return Violated(f"{path} is a new gallery example with no content tag")


def _tags_written(bundle: EvidenceBundle):
    """(path, line number, tag) for each tag the agent wrote."""
    out = []
    for path in sorted(bundle.files):
        change = bundle.files[path]
        if not (path.endswith(DOC_SUFFIXES) or is_gallery_path(path)):
            continue
        text = added_text(bundle, path)
        for number, tags in _tag_directives(bundle, path, text):
            for tag in tags:
                out.append((path, number, tag))
    return out


@rule(
    id="MATPLOTLIB-C280",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a tag the agent wrote
    reads=("files",),  # spec §5
)
class ATagIsWrittenSubcategoryColonTag:
    """Pre-condition: each tag the agent wrote in a ``.. tags::`` directive.
    Pass condition: it is written ``subcategory: tag``.

    Not heuristic (§6.2): the shape is stated in the rule and the check is the separator.
    How long the tag may be is C281's, which fires only on tags that already carry a
    subcategory (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"tag-form:{path}:{number}:{tag}", path, (number, number),
                       (path, number, tag), tag[:120])
                for path, number, tag in _tags_written(b)]

    def pass_condition(self, t: Target):
        path, number, tag = t.payload
        head, sep, rest = tag.partition(":")
        if sep and head.strip() and rest.strip():
            return Satisfied(f"{path}:{number} writes the tag as {tag!r}")
        return Violated(f"{path}:{number} writes the tag {tag!r} without a "
                        f"'subcategory: tag' form")


@rule(
    id="MATPLOTLIB-C281",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
)
class ATagIsOneOrTwoWords:
    """Pre-condition: each tag the agent wrote that already carries a subcategory.
    Pass condition: the tag itself is one or two words.

    Narrowed to well-formed tags (§7.5) so that a tag written without a subcategory is one
    violation -- C280's -- rather than two.

    Not heuristic (§6.2): the limit is a number the rule states and the check counts words.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, number, tag in _tags_written(b):
            head, sep, rest = tag.partition(":")
            if not (sep and head.strip() and rest.strip()):
                continue  # §7.5: a malformed tag is C280's finding
            out.append(target(f"tag-length:{path}:{number}:{tag}", path, (number, number),
                              (path, number, tag, rest.strip()), tag[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, tag, value = t.payload
        words = value.split()
        if len(words) <= 2:
            return Satisfied(f"{path}:{number} keeps the tag {value!r} to "
                             f"{len(words)} word(s)")
        return Violated(f"{path}:{number} writes the tag {value!r} in {len(words)} words, "
                        f"more than the two the guide allows")


@rule(
    id="MATPLOTLIB-C283",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a tag the agent introduced
    reads=("files",),  # spec §5
    heuristic=True,
)
class ATagAppliesToMoreThanOneEntry:
    """Pre-condition: each tag the agent wrote, in a contribution that tags two or more
    gallery entries -- so there is a comparison the patch can make.
    Pass condition: the tag is used by at least two of them.

    The antecedent is narrowed to the case the evidence can decide. A contribution that
    tags a single example says nothing about how many entries a tag reaches, and grading
    it would fail every such change; that is why the rule finds no target there rather
    than manufacturing a violation.

    Heuristic on **both** layers (§6.3, §6.2): the comparison is confined to the entries
    in the patch, so a tag shared with an example the contribution does not touch reads as
    a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        tagged: dict[str, set[str]] = {}
        for path in gallery_examples(b):
            text = b.files[path].head_text or added_text(b, path)
            for _number, tags in _tag_directives(b, path, text):
                for tag in tags:
                    tagged.setdefault(tag, set()).add(path)
        entries = {p for paths in tagged.values() for p in paths}
        if len(entries) < 2:
            return []
        out = []
        for path, number, tag in _tags_written(b):
            if not is_gallery_path(path):
                continue
            out.append(target(f"tag-reach:{path}:{number}:{tag}", path, (number, number),
                              (path, number, tag, tagged.get(tag, set())), tag[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, tag, users = t.payload
        if len(users) >= 2:
            return Satisfied(f"{path}:{number} uses the tag {tag!r} on {len(users)} "
                             f"gallery entries")
        return Violated(f"{path}:{number} creates the tag {tag!r} for a single gallery "
                        f"entry")

"""matplotlib: Language and framework style -- 18 rules.

Layer C. Every rule is two layers (`docs/checker-authoring.md` §2): ``precondition``
selects on the rule's ANTECEDENT, ``pass_condition`` grades.

Three groups. Six are the style guide's *terminology* (C117--C122): four capitalisation
rules and two names for a usage pattern, all graded over prose the agent wrote. Six are
Python house style (C044, C189, C235, C236, C238, C239, C253, C254, C261). Three are the
C/C++ extension rules (C245--C247).

**Four §7.5 narrowings, each pinned by a no-target test.**

* **C235 and C236 share ``ruff`` with ``code_quality.C152``.** One tool, three sentences,
  so the report is partitioned: C236 grades line length straight from the patch and owns
  ``E501``; C235 owns the remaining pycodestyle (``E``/``W``) findings; C152 owns
  everything else the hooks report. One badly formatted line is one violation.
* **C253 and C254 both reach a function taking ``**kwargs``.** C253 is about a function
  that forwards *nothing* -- it should have declared its arguments and not gathered them
  at all. C254 is about a function that consumes some locally and *forwards the rest* --
  the ones it keeps belong in the signature as keyword-only. A function that forwards
  nothing finds no target in C254, and one that forwards everything finds none in either.
* **C246 and C247 both reach a Python/C interface file.** C246 grades whether that file
  also carries core computation; C247 grades what a newly added interface file is called.
  A correctly named wrapper that mixes in core code violates C246 only.
* **C121 and C122** name the two usage patterns, and neither reads the other's word.

**Corpus note (§5).** Every row here is filed ``CheckTier = static``. C235 is not: PEP8
"as enforced by ruff" is the linter's own verdict, so it declares ``lint_run`` and
withholds until a linter has been run over base and head. The mismatch is recorded here
rather than corrected in the workbook (§0). Its neighbour C236 *is* static -- counting
characters needs no tool -- and is coded that way.
"""

from __future__ import annotations

import ast
import re

from compliance.core.models import (EvidenceBundle, Satisfied, Target, Undetermined,
                                    Violated)
from compliance.core.registry import rule
from compliance.extractors import imports as im
from compliance.rules.matplotlib._common import (added_lines, classes, is_c_source,
                                                 is_package_path, modules,
                                                 owned_functions, prose_lines,
                                                 python_files, strip_markup, target)

CATEGORY = "Language and framework style"

# --- terminology -----------------------------------------------------------------------

#: For each term the style guide governs, the general-language uses it contrasts with.
#: Taken from the guide's own "General language" column: a figure skater, axes for
#: chopping wood, the coordinate axes, a person who is an artist.
GENERAL_LANGUAGE = {
    "Figure": re.compile(
        r"\bfigures?\s+(?:skat|out\b|of\s+speech|eight)|"
        r"\b(?:public|key|prominent|historical|leading|political|father)\s+figures?\b|"
        r"\bfigures?\s+(?:it|this|that)\s+out\b", re.I),
    "Axes": re.compile(
        r"\baxes\s+(?:to\s+chop|of\s+(?:rotation|symmetry))|"
        r"\b(?:coordinate|principal|cartesian|two|three|spatial|x\s+and\s+y|major)\s+axes\b|"
        r"\blumberjack", re.I),
    "Artist": re.compile(
        r"\b(?:graphic|visual|recording|solo|street|make-?up|tattoo)\s+artists?\b|"
        r"\bartists?\s+(?:rendering|impression|studio)\b", re.I),
    "Axis": re.compile(
        r"\b(?:[xyz]|time|value|category|major|minor|horizontal|vertical|shared|twin)"
        r"[\s-]axis\b|\baxis\s+of\s+(?:rotation|symmetry|evil)\b|\baxis\s+label", re.I),
}

#: The names for the two usage patterns, and which of them the guide sanctions.
_AXES_PATTERN = re.compile(
    r"\b(?P<name>Axes|explicit|object[-\s]oriented|OO[-\s]style|OOP|OO)\s+interface\b", re.I)
_PYPLOT_PATTERN = re.compile(
    r"\b(?P<name>pyplot|implicit|MATLAB[-\s]?(?:like|style))\s+interface\b", re.I)
_PYPLOT_WORD = re.compile(r"\bp[Yy]plot\b|\bPyplot\b")
SANCTIONED_AXES_NAME = "axes"
SANCTIONED_PYPLOT_NAME = "pyplot"


def _term_targets(bundle: EvidenceBundle, term: str) -> list[Target]:
    """Each prose occurrence of ``term`` that is not one of its general-language uses."""
    general = GENERAL_LANGUAGE[term]
    pattern = re.compile(rf"\b{term}(?:es|s)?\b", re.I)
    out = []
    for path, number, text in prose_lines(bundle):
        clean = strip_markup(text)
        for match in pattern.finditer(clean):
            window = clean[max(0, match.start() - 40):match.end() + 40]
            if general.search(window):
                continue
            out.append(target(f"term-{term.lower()}:{path}:{number}:{match.start()}",
                              path, (number, number), (path, number, match.group(0), term),
                              clean.strip()[:120]))
    return out


def _grade_term(t: Target):
    path, number, word, term = t.payload
    if word[0].isupper():
        return Satisfied(f"{path}:{number} capitalises {word!r} where it names the "
                         f"Matplotlib object")
    return Violated(f"{path}:{number} writes {word!r} in lower case where it names the "
                    f"Matplotlib {term} object")


_TERMINOLOGY_DOC = """
    Heuristic on the **pre-condition** (§6.3): *meaning the Matplotlib object* is not
    observable, so every prose occurrence is selected except those matching the
    general-language uses the guide itself contrasts with. A general use the list does not
    anticipate is therefore selected, and reads as a violation when it is lower case.
    Code markup -- inline literals, roles, hyperlink targets, URLs -- is blanked out before
    matching, so a class name is never mistaken for a word."""


@rule(
    id="MATPLOTLIB-C117",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property the prose must have, no newness
                          # qualifier in the sentence
    reads=("files",),  # spec §5: the prose is in the patch
    heuristic=True,
)
class FigureIsCapitalisedWhenItNamesTheObject:
    __doc__ = ("""Pre-condition: each prose occurrence of "figure" the agent wrote that is
    not one of the guide's general-language uses.
    Pass condition: it is capitalised.
""" + _TERMINOLOGY_DOC)

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _term_targets(b, "Figure")

    def pass_condition(self, t: Target):
        return _grade_term(t)


@rule(
    id="MATPLOTLIB-C118",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class AxesIsCapitalisedWhenItNamesTheObject:
    __doc__ = ("""Pre-condition: each prose occurrence of "axes" the agent wrote that is
    not one of the guide's general-language uses -- the plural of *axis* among them.
    Pass condition: it is capitalised.
""" + _TERMINOLOGY_DOC)

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _term_targets(b, "Axes")

    def pass_condition(self, t: Target):
        return _grade_term(t)


@rule(
    id="MATPLOTLIB-C119",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ArtistIsCapitalisedWhenItNamesTheObject:
    __doc__ = ("""Pre-condition: each prose occurrence of "artist" the agent wrote that is
    not one of the guide's general-language uses.
    Pass condition: it is capitalised.
""" + _TERMINOLOGY_DOC)

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _term_targets(b, "Artist")

    def pass_condition(self, t: Target):
        return _grade_term(t)


@rule(
    id="MATPLOTLIB-C120",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class AxisIsCapitalisedWhenItNamesTheObject:
    __doc__ = ("""Pre-condition: each prose occurrence of "axis" the agent wrote that is
    not one of the guide's general-language uses -- a named or mathematical axis among
    them.
    Pass condition: it is capitalised.
""" + _TERMINOLOGY_DOC)

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _term_targets(b, "Axis")

    def pass_condition(self, t: Target):
        return _grade_term(t)


@rule(
    id="MATPLOTLIB-C121",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of prose the agent edited
    reads=("files",),  # spec §5
    heuristic=True,
)
class TheAxesUsagePatternIsCalledTheAxesInterface:
    """Pre-condition: each prose phrase the agent wrote that names the Axes usage pattern
    -- ``<something> interface``, by any of the names the guide lists.
    Pass condition: the name used is "Axes".

    §7.1: the antecedent is *naming the pattern*, whichever name is used, so a page that
    calls it the Axes interface is recorded as a pass. Selecting the banned names would
    only ever find violations.

    Heuristic on the **pre-condition** (§6.3), which recognises the pattern from the word
    "interface" preceded by one of the guide's five names; a sentence that describes the
    pattern without naming it is not seen. Reads only the Axes names -- the pyplot ones
    are C122's (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, number, text in prose_lines(b):
            clean = strip_markup(text)
            for match in _AXES_PATTERN.finditer(clean):
                out.append(target(f"axes-interface:{path}:{number}:{match.start()}", path,
                                  (number, number), (path, number, match.group("name")),
                                  clean.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, name = t.payload
        if name.lower() == SANCTIONED_AXES_NAME:
            return Satisfied(f"{path}:{number} calls it the {name} interface")
        return Violated(f"{path}:{number} calls the Axes usage pattern the "
                        f"{name!r} interface")


@rule(
    id="MATPLOTLIB-C122",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ThePyplotUsagePatternIsCalledThePyplotInterface:
    """Pre-condition: each prose phrase the agent wrote that names the pyplot usage
    pattern, and each prose occurrence of the word "Pyplot" capitalised.
    Pass condition: the pattern is called the "pyplot interface", spelled in lower case.

    Both clauses of the sentence are graded through one selection so that they cannot
    disagree: a rival name violates, and so does a capitalised ``Pyplot``, while
    "pyplot interface" satisfies.

    Heuristic on the **pre-condition** (§6.3): naming the pattern is recognised from the
    word "interface" preceded by one of the guide's names, so a sentence that describes
    the pattern without naming it is not seen. Reads only the pyplot names -- the Axes
    ones are C121's (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, number, text in prose_lines(b):
            clean = strip_markup(text)
            seen = set()
            for match in _PYPLOT_PATTERN.finditer(clean):
                seen.add(match.start())
                out.append(target(f"pyplot-interface:{path}:{number}:{match.start()}",
                                  path, (number, number),
                                  (path, number, match.group("name"), "pattern"),
                                  clean.strip()[:120]))
            for match in _PYPLOT_WORD.finditer(clean):
                if match.group(0) == "pyplot" or match.start() in seen:
                    continue
                out.append(target(f"pyplot-case:{path}:{number}:{match.start()}", path,
                                  (number, number),
                                  (path, number, match.group(0), "spelling"),
                                  clean.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, name, kind = t.payload
        if kind == "spelling":
            return Violated(f"{path}:{number} writes {name!r}; the guide keeps pyplot in "
                            f"lower case")
        if name == SANCTIONED_PYPLOT_NAME:
            return Satisfied(f"{path}:{number} calls it the pyplot interface")
        return Violated(f"{path}:{number} calls the pyplot usage pattern the "
                        f"{name!r} interface")


# --- Python house style ------------------------------------------------------------------

_SETTER = re.compile(r"^set_(?P<prop>\w+)$")


@rule(
    id="MATPLOTLIB-C044",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- naming an accessor pair is naming one the agent
                          # introduced; an inherited half is not the agent's doing
    reads=("files",),  # spec §5: both halves of the pair are in the patch
    heuristic=True,
)
class AnArtistPropertyAccessorComesAsASetGetPair:
    """Pre-condition: each ``set_PROPERTYNAME`` method the agent added to a class in the
    library.
    Pass condition: the same class defines ``get_PROPERTYNAME``.

    The antecedent is deliberately the **setter**, not either accessor (§7.5-style
    narrowing, stated here because it changes what the rule measures). Matplotlib has many
    legitimate read-only accessors -- ``get_window_extent``, ``get_children`` -- and
    selecting getters too would manufacture a violation for every one of them. A property
    that can be *set* is the case the sentence is about.

    Heuristic on the **pre-condition** (§6.3): *an Artist* is approximated by *a class in
    the library*, since the base classes a checkout defines are not in the patch.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=False):
            if not is_package_path(path):
                continue
            authored = b.files[path].authored_lines
            for node in classes(module):
                span = (node.lineno, node.end_lineno or node.lineno)
                methods = [f for f in module.functions if span[0] < f.lineno <= span[1]]
                names = {f.name for f in methods}
                for method in methods:
                    match = _SETTER.match(method.name)
                    if not match or method.lineno not in authored:
                        continue
                    out.append(target(f"accessor:{path}:{node.name}.{method.name}", path,
                                      method.span(),
                                      (path, node.name, match.group("prop"), names),
                                      f"{path}::{node.name}.{method.name}"))
        return out

    def pass_condition(self, t: Target):
        path, klass, prop, names = t.payload
        if f"get_{prop}" in names:
            return Satisfied(f"{path}::{klass} pairs set_{prop} with get_{prop}")
        return Violated(f"{path}::{klass} defines set_{prop} with no matching "
                        f"get_{prop} accessor")


@rule(
    id="MATPLOTLIB-C189",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- "prefix ... with an underscore" is about names
                          # the agent introduced
    reads=("files",),  # spec §5: the definition is in the patch
    heuristic=True,
)
class HelperFunctionsArePrefixedWithAnUnderscore:
    """Pre-condition: each module-level function the agent added to a library module that
    carries no docstring -- the shape of a helper rather than of published API.
    Pass condition: its name begins with an underscore.

    Heuristic on the **pre-condition** (§6.3): *a helper* is not a category the project
    enumerates, and it is approximated here by *undocumented module-level function*, since
    matplotlib gives every public function a numpydoc docstring. A documented helper is
    therefore not seen, and an undocumented function that really is public reads as a
    violation.

    **Partial reading, declared (§6.6/§8).** The sentence's second clause -- "and internal
    attributes" -- is not graded. Nothing in the patch distinguishes an internal attribute
    from a public one, and a predicate that guessed would grade the wrong thing exactly.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, mode="created", tests=False):
            if not is_package_path(path) or module.tree is None:
                continue
            top_level = {n.lineno for n in module.tree.body
                         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            authored = b.files[path].authored_lines
            for function in module.functions:
                if function.lineno not in top_level or function.lineno not in authored:
                    continue
                if function.docstring:
                    continue
                out.append(target(f"helper:{path}:{function.name}", path, function.span(),
                                  (path, function), f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function = t.payload
        if function.name.startswith("_"):
            return Satisfied(f"{path}::{function.name} is private, as a helper should be")
        return Violated(f"{path}::{function.name} is an undocumented module-level helper "
                        f"with no leading underscore, so it reads as public API")


PEP8_CODE = re.compile(r"^[EW]\d")
LINE_LIMIT = 88
E501 = "E501"


@rule(
    id="MATPLOTLIB-C235",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- the whole contribution is what ruff runs over
    reads=("files", "lint_run"),  # spec §5: the sentence, not CheckTier=static -- "as
                                  # enforced by ruff" is the linter's own verdict
)
class PythonCodeIsFormattedToPep8:
    """Pre-condition: the contribution submits Python, which ruff would check.
    Pass condition: ruff reports no new pycodestyle finding other than the line-length
    one C236 owns.

    Not heuristic (§6.2): the verdict is a tool's own report, base-subtracted. Graded
    **one-sidedly** where no report exists (§9) -- a submitted file that will not parse
    provably fails, everything else withholds with ``lint_run`` named as the missing
    input rather than reading source text as a clean bill.

    Owns the ``E``/``W`` findings and nothing else. ``E501`` belongs to C236, which counts
    characters from the patch and needs no tool; every other code belongs to
    ``code_quality.C152``, the pre-commit gate (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        submitted = python_files(b)
        if not submitted:
            return []
        return [target(f"pep8:{b.instance_id}", None, None, b,
                       f"{len(submitted)} Python file(s) submitted")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        report = bundle.lint.get("ruff")
        if report is None or not report.usable:
            note = report.note if report is not None else "no lint report for this run"
            return Undetermined("tool_missing",
                                f"PEP8 conformance was never checked by ruff: {note}")
        ours = [f for f in report.new_findings
                if PEP8_CODE.match(f.code) and f.code != E501]
        if not ours:
            return Satisfied(f"ruff reports no new pycodestyle finding "
                             f"({report.n_findings_base} pre-existing finding(s) "
                             f"subtracted)")
        first = ours[0]
        return Violated(f"ruff reports {len(ours)} new PEP8 finding(s), e.g. "
                        f"{first.path}: {first.code} {first.message}")


@rule(
    id="MATPLOTLIB-C236",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property every line must have, no newness
                          # qualifier; the file existed before the run
    reads=("files",),  # spec §5: the line and its length are in the patch
)
class LinesAreAtMostEightyEightCharacters:
    """Pre-condition: each Python file the agent edited.
    Pass condition: no line it wrote exceeds 88 characters.

    Not heuristic (§6.2): the limit is a number the project states and the check counts
    characters. Needs no linter, which is why this rule and not C235 is coded from the
    patch; ``E501`` is excluded from C235's and C152's readings of the ruff report so the
    same long line is one violation, not three (§7.5).

    Only lines the agent wrote are judged: a long line already in the file is not the
    agent's doing (§4.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"line-length:{path}", path, None, (path, added_lines(b, path)),
                       f"{path} edited")
                for path in python_files(b)]

    def pass_condition(self, t: Target):
        path, lines = t.payload
        long_lines = [(n, text) for n, text in lines if len(text) > LINE_LIMIT]
        if long_lines:
            number, text = long_lines[0]
            return Violated(f"{path}:{number} is {len(text)} characters, over the "
                            f"{LINE_LIMIT}-character limit ({len(long_lines)} such "
                            f"line(s))")
        return Satisfied(f"{path} keeps every written line within {LINE_LIMIT} characters")


#: The aliases the coding guide lists. A module absent from the table is unconstrained.
STANDARD_ALIASES = {
    "numpy": "np",
    "matplotlib": "mpl",
    "matplotlib.pyplot": "plt",
    "matplotlib.cbook": "cbook",
    "matplotlib.patches": "mpatches",
}


def _bindings(node) -> list[tuple[str, str]]:
    """(dotted module, local binding) for each name an import statement binds."""
    out = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            out.append((alias.name, alias.asname or ""))
    elif isinstance(node, ast.ImportFrom) and not node.level:
        base = node.module or ""
        for alias in node.names:
            out.append((f"{base}.{alias.name}" if base else alias.name,
                        alias.asname or alias.name))
    return out


@rule(
    id="MATPLOTLIB-C238",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is an import statement the agent wrote
    reads=("files",),  # spec §5: the import is in the patch
)
class ImportsUseTheStandardAliases:
    """Pre-condition: each import the agent wrote that binds one of the modules the coding
    guide gives a standard alias to.
    Pass condition: the binding is that alias.

    Not heuristic (§6.2): the guide publishes the list, so the check is an equality
    against a stated name. Modules the list does not cover find no target, which is
    correct -- the sentence says "the listed standard aliases".
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b):
            authored = b.files[path].authored_lines
            for line in im.import_lines(module=module, path=path):
                if line.lineno not in authored:
                    continue
                for dotted, binding in _bindings(line.node):
                    if dotted not in STANDARD_ALIASES:
                        continue
                    out.append(target(f"alias:{path}:{line.lineno}:{dotted}", path,
                                      line.span(), (path, line.lineno, dotted, binding),
                                      line.raw.strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, number, dotted, binding = t.payload
        wanted = STANDARD_ALIASES[dotted]
        if binding == wanted:
            return Satisfied(f"{path}:{number} imports {dotted} as {wanted}")
        if not binding:
            return Violated(f"{path}:{number} imports {dotted} with no alias; the guide "
                            f"lists {wanted}")
        return Violated(f"{path}:{number} imports {dotted} as {binding}, not the listed "
                        f"{wanted}")


_RCPARAMS = re.compile(r"\brcParams\b")
#: Where rcParams is defined and validated; a direct name there is not a style error.
_RCPARAMS_HOME = ("lib/matplotlib/__init__.py", "lib/matplotlib/rcsetup.py")


@rule(
    id="MATPLOTLIB-C239",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of how the module reaches rcParams,
                          # no newness qualifier
    reads=("files",),  # spec §5: the import and the use are both in the patch
    heuristic=True,
)
class RcParamsIsReachedThroughTheModule:
    """Pre-condition: each library module where the agent wrote a line mentioning
    ``rcParams``.
    Pass condition: none of those lines imports the name directly.

    §7.1: the antecedent is *using rcParams*, so a module that reaches it as
    ``mpl.rcParams`` is recorded as a pass; selecting direct imports would only ever find
    violations. The two files that define and validate rcParams are excluded, since a bare
    name there is the definition rather than a style error.

    Heuristic on the **pass condition** (§6.2): ``matplotlib.rcParams`` is accepted
    alongside ``mpl.rcParams``, because it is the same access written without the alias
    and failing it would grade C238's sentence twice (§7.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b):
            if path in _RCPARAMS_HOME or not is_package_path(path):
                continue
            lines = [(n, text) for n, text in added_lines(b, path) if _RCPARAMS.search(text)]
            if lines:
                out.append(target(f"rcparams:{path}", path, None, (path, lines),
                                  lines[0][1].strip()[:120]))
        return out

    def pass_condition(self, t: Target):
        path, lines = t.payload
        for number, text in lines:
            if re.match(r"\s*from\s+[\w.]*\s+import\b.*\brcParams\b", text):
                return Violated(f"{path}:{number} imports rcParams directly instead of "
                                f"reaching it as mpl.rcParams")
        return Satisfied(f"{path} reaches rcParams through the module "
                         f"({len(lines)} reference(s))")


_WARN_CALLS = ("warnings.warn", "warn")
_SANCTIONED_WARN = ("_api.warn_external", "_api.warn_deprecated",
                    "warn_external", "warn_deprecated")
#: `_api` is where the sanctioned helpers are implemented, so `warnings.warn` there is the
#: implementation rather than a style error.
_WARN_HOME = "lib/matplotlib/_api/"


@rule(
    id="MATPLOTLIB-C261",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is a warning call the agent wrote
    reads=("files",),  # spec §5: the call is in the patch
    heuristic=True,
)
class UserFacingWarningsGoThroughWarnExternal:
    """Pre-condition: each warning call the agent added to a library module, by either
    route.
    Pass condition: it goes through ``_api.warn_external`` (or ``warn_deprecated``) rather
    than ``warnings.warn``.

    §7.1: the antecedent is *raising a warning*, so a call that already uses the helper is
    recorded as a pass. Calls inside ``_api`` itself are excluded, since that is where the
    helper is implemented.

    Heuristic on the **pre-condition** (§6.3): *user-facing* is not observable, so every
    warning raised in library code is selected -- including the internal ones the sentence
    does not reach, which read as violations when they use ``warnings.warn``.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=False):
            if not is_package_path(path) or path.startswith(_WARN_HOME):
                continue
            authored = b.files[path].authored_lines
            for call in module.calls:
                if call.lineno not in authored:
                    continue
                if call.func in _WARN_CALLS or call.func in _SANCTIONED_WARN:
                    out.append(target(f"warn:{path}:{call.lineno}", path, call.span(),
                                      (path, call), f"{call.func}() at {path}:{call.lineno}"))
        return out

    def pass_condition(self, t: Target):
        path, call = t.payload
        if call.func in _SANCTIONED_WARN:
            return Satisfied(f"{path}:{call.lineno} warns through {call.func}()")
        return Violated(f"{path}:{call.lineno} calls {call.func}() directly instead of "
                        f"_api.warn_external()")


# --- keyword argument processing -----------------------------------------------------------


def _kwargs_name(node) -> str:
    kwarg = getattr(getattr(node, "args", None), "kwarg", None)
    return kwarg.arg if kwarg is not None else ""


def _forwards(node, name: str) -> bool:
    """Whether the function passes its ``**kwargs`` catch-all on to another call."""
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            for keyword in child.keywords:
                if (keyword.arg is None and isinstance(keyword.value, ast.Name)
                        and keyword.value.id == name):
                    return True
    return False


def _pops(node, name: str) -> list[str]:
    """Names the function takes off its catch-all locally."""
    out = []
    for child in ast.walk(node):
        if (isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
                and child.func.attr in ("pop", "get", "setdefault")
                and isinstance(child.func.value, ast.Name)
                and child.func.value.id == name and child.args):
            key = child.args[0]
            out.append(key.value if isinstance(key, ast.Constant) else "?")
    return out


def _keyword_parameters(node) -> list[str]:
    args = getattr(node, "args", None)
    if args is None:
        return []
    named = [a.arg for a in args.kwonlyargs]
    defaults = list(args.defaults)
    if defaults:
        positional = list(args.posonlyargs) + list(args.args)
        named += [a.arg for a in positional[len(positional) - len(defaults):]]
    return named


@rule(
    id="MATPLOTLIB-C253",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property the signature must have, no newness
                          # qualifier in the sentence
    reads=("files",),  # spec §5: the signature and the body are in the patch
    heuristic=True,
)
class AFunctionConsumingEveryKeywordDeclaresThemExplicitly:
    """Pre-condition: each library function the agent wrote or edited that takes keyword
    arguments and forwards none of them onward -- so it consumes all of them itself.
    Pass condition: they are declared as named parameters rather than gathered in a
    ``**kwargs`` catch-all.

    §7.1: the antecedent is *consuming all the keywords*, which a compliant function does
    with an explicit signature; selecting only ``**kwargs`` functions would record nothing
    but violations.

    Narrowed away from C254 (§7.5): this rule fires only where **nothing** is forwarded.
    A function that consumes some keywords and passes the rest on is C254's, and finds no
    target here.

    Heuristic on the **pre-condition** (§6.3): "consumes all of them" is approximated by
    the catch-all never being passed to another call, so a function that forwards through
    a dict it built by hand is wrongly selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, function in owned_functions(b, tests=False):
            if not is_package_path(path):
                continue
            node = function.node
            catch_all = _kwargs_name(node)
            if catch_all and _forwards(node, catch_all):
                continue
            if not catch_all and not _keyword_parameters(node):
                continue
            out.append(target(f"explicit-kwargs:{path}:{function.name}", path,
                              function.span(), (path, function, catch_all),
                              f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function, catch_all = t.payload
        if catch_all:
            return Violated(f"{path}::{function.name} consumes every keyword itself but "
                            f"gathers them in **{catch_all} instead of declaring them")
        declared = _keyword_parameters(function.node)
        return Satisfied(f"{path}::{function.name} declares its keyword arguments "
                         f"explicitly: {', '.join(declared[:3])}")


@rule(
    id="MATPLOTLIB-C254",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of the signature, no newness qualifier
    reads=("files",),  # spec §5: the signature and the body are in the patch
    heuristic=True,
)
class LocallyConsumedArgumentsAreKeywordOnly:
    """Pre-condition: each library function the agent wrote or edited that takes a
    ``**kwargs`` catch-all, forwards it onward, and also consumes something from it
    locally -- whether by declaring it or by popping it.
    Pass condition: what it consumes locally is declared as a keyword-only parameter, not
    popped off the catch-all.

    Narrowed away from C253 (§7.5): a function that forwards nothing is that rule's, and
    finds no target here; a function that forwards everything and keeps nothing finds no
    target in either.

    Heuristic on the **pre-condition** (§6.3): "consumes locally" is recognised from
    ``kwargs.pop``/``get``/``setdefault`` calls and from keyword-only parameters, so a
    function that reads its catch-all by subscript is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, function in owned_functions(b, tests=False):
            if not is_package_path(path):
                continue
            node = function.node
            catch_all = _kwargs_name(node)
            if not catch_all or not _forwards(node, catch_all):
                continue
            popped = _pops(node, catch_all)
            kwonly = [a.arg for a in node.args.kwonlyargs]
            if not popped and not kwonly:
                continue
            out.append(target(f"kwonly:{path}:{function.name}", path, function.span(),
                              (path, function, popped, kwonly),
                              f"{path}::{function.name}"))
        return out

    def pass_condition(self, t: Target):
        path, function, popped, kwonly = t.payload
        if popped:
            return Violated(f"{path}::{function.name} pops {popped[0]!r} off **kwargs "
                            f"instead of declaring it keyword-only")
        return Satisfied(f"{path}::{function.name} declares what it consumes locally as "
                         f"keyword-only: {', '.join(kwonly[:3])}")


# --- C and C++ extensions -----------------------------------------------------------------

#: Python/C interface code, by the symbols only interface code uses.
_INTERFACE = re.compile(r"#include\s*[<\"]Python\.h[>\"]|\bPyObject\b|\bPyArg_\w+"
                        r"|\bPy_BuildValue\b|\bPyErr_\w+|\bpybind11\b|\bpy::|"
                        r"\bPYBIND11_MODULE\b|\bPyTypeObject\b")
#: Core computation: a plain C function definition whose signature names no Python type.
_CORE_FUNCTION = re.compile(
    r"^\s*(?:static\s+|inline\s+)*(?:void|int|long|double|float|bool|unsigned|size_t|char)"
    r"[\s*]+(?P<name>\w+)\s*\([^)]*\)\s*\{?\s*$")
PEP7_LINE_LIMIT = 79
WRAPPER_NAME = re.compile(r"_wrap(?:per)?\.(?:c|cc|cpp|h|hpp)$")


@rule(
    id="MATPLOTLIB-C245",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property the code must have, no newness
                          # qualifier
    reads=("files",),  # spec §5: the lines are in the patch
    heuristic=True,
)
class CCodeFollowsPep7:
    """Pre-condition: each C or C++ file the agent edited.
    Pass condition: the lines it wrote use spaces rather than tabs and stay within PEP 7's
    79 columns.

    Heuristic on the **pass condition** (§6.2), and the doubt is named: PEP 7 is a whole
    style, and only the parts decidable from text without a formatter are checked here --
    indentation characters and line width. A file that satisfies both and breaks PEP 7's
    brace or naming conventions is recorded as a pass, so this rate is an upper bound.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            if not is_c_source(path) or not b.files[path].added_lines:
                continue
            out.append(target(f"pep7:{path}", path, None, (path, added_lines(b, path)),
                              f"{path} edited"))
        return out

    def pass_condition(self, t: Target):
        path, lines = t.payload
        for number, text in lines:
            if text.startswith("\t") or re.match(r"^ *\t", text):
                return Violated(f"{path}:{number} indents with a tab; PEP 7 uses spaces")
        long_lines = [(n, s) for n, s in lines if len(s) > PEP7_LINE_LIMIT]
        if long_lines:
            number, text = long_lines[0]
            return Violated(f"{path}:{number} is {len(text)} characters, over PEP 7's "
                            f"{PEP7_LINE_LIMIT}-column limit")
        return Satisfied(f"{path} indents with spaces and stays within "
                         f"{PEP7_LINE_LIMIT} columns")


@rule(
    id="MATPLOTLIB-C246",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- a property of the file's contents, no newness
                          # qualifier
    reads=("files",),  # spec §5: both kinds of code are in the patch
    heuristic=True,
)
class PythonCInterfaceCodeIsKeptSeparateFromCore:
    """Pre-condition: each C or C++ file the agent edited that carries Python/C interface
    code.
    Pass condition: the same file carries no core computation.

    §7.1: the antecedent is *writing interface code*, so a pure wrapper is recorded as a
    pass; selecting mixed files would only ever find violations. What the file is
    **called** is C247's question and is not asked here, so a correctly named wrapper that
    mixes in core code violates this rule alone (§7.5).

    Heuristic on **both** layers (§6.2, §6.3). Interface code is recognised by the CPython
    and pybind11 symbols only interface code uses, and core computation by a plain C
    function definition whose signature names no Python type -- a proxy that misses a core
    routine written as a C++ template and wrongly selects a helper with a primitive
    signature.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            change = b.files[path]
            if not is_c_source(path) or change.head_text is None:
                continue
            if not _INTERFACE.search(change.head_text):
                continue
            out.append(target(f"interface-split:{path}", path, None,
                              (path, change.head_text), f"{path} carries interface code"))
        return out

    def pass_condition(self, t: Target):
        path, text = t.payload
        core = [(n, line) for n, line in enumerate(text.split("\n"), 1)
                if _CORE_FUNCTION.match(line) and not _INTERFACE.search(line)]
        if core:
            number, line = core[0]
            return Violated(f"{path} mixes Python/C interface code with core computation: "
                            f"line {number}, {line.strip()[:60]}")
        return Satisfied(f"{path} carries interface code only")


@rule(
    id="MATPLOTLIB-C247",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- naming a file is naming one the agent added
    reads=("files",),  # spec §5: the name and the contents are in the patch
    heuristic=True,
)
class PythonCInterfaceFilesAreNamedWrap:
    """Pre-condition: each C or C++ file the agent added that carries Python/C interface
    code.
    Pass condition: it is named ``FOO_wrap`` or ``FOO_wrapper`` with a C/C++ suffix.

    Scoped to files the agent *added*: renaming a wrapper that was already in the tree is
    not what the sentence asks for (§4.3). Grades the name only -- whether the file also
    carries core code is C246's (§7.5).

    Heuristic on the **pre-condition** (§6.3): interface code is recognised by the CPython
    and pybind11 symbols only interface code uses, so a wrapper written against a
    different binding layer is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            change = b.files[path]
            if not is_c_source(path) or not change.is_new or change.head_text is None:
                continue
            if not _INTERFACE.search(change.head_text):
                continue
            out.append(target(f"wrapper-name:{path}", path, None, path,
                              f"{path} is a new interface file"))
        return out

    def pass_condition(self, t: Target):
        path: str = t.payload
        if WRAPPER_NAME.search(path):
            return Satisfied(f"{path} is named for a Python/C interface file")
        return Violated(f"{path} carries Python/C interface code but is not named "
                        f"FOO_wrap or FOO_wrapper")

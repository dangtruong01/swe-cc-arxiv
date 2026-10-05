"""scikit-learn: Documentation and docstrings -- 35 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects
on the rule's ANTECEDENT, ``pass_condition`` grades.

Three families, and they are worth telling apart because their evidence differs.

* **The numpydoc conventions** (C064-C079, C126, C132, C138, C153, C186) read docstrings
  the agent wrote or edited, through ``extractors/python_ast`` and
  ``extractors/docstrings``. None of these sentences carries a newness qualifier, so all
  are ``touched`` per §4.3 -- editing a docstring makes the agent answerable for its form.
* **The reStructuredText conventions** (C085-C102) read the documentation tree through
  ``extractors/rst``. Several grade one-sidedly: they detect the *wrong* form rather than
  confirm the right one, and each says so in its own docstring rather than leaving a
  reader to infer it from the heuristic flag.
* **The new-feature obligations** (C036, C038, C039, C060, C062) fire on the contribution
  adding something new. "A new feature" is not observable, so it is approximated by a new
  public definition appearing in ``sklearn/`` -- a proxy declared on every rule using it.

One narrowing is deliberate and is pinned by a test (§7.5): the user-guide rules exclude
``doc/whats_new/``. A changelog is not documentation, and without the exclusion the
changelog fragment C048 requires would be graded by every user-guide rule here.
"""

from __future__ import annotations

import ast
import re

from compliance.core import ownership as own
from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import docstrings as ds
from compliance.extractors import python_ast as pa
from compliance.extractors import rst
from compliance.rules.scikit_learn._common import (DOC_ROOT, EXAMPLES_ROOT, PACKAGE,
                                                   ParamEntry, added_lines, added_text,
                                                   base_module, classes, example_files,
                                                   file_text, has_deprecated_directive,
                                                   has_versionchanged_directive,
                                                   head_lines, is_estimator,
                                                   keyword_defaults, modules, numpydoc,
                                                   owned_classes, owned_docstrings,
                                                   parameter_entries, parameters,
                                                   self_assignments, target,
                                                   user_guide_files)

CATEGORY = "Documentation and docstrings"

#: The five sections whose order the contributing guide states (C064).
SECTION_ORDER = ("Parameters", "Returns", "See Also", "Notes", "Examples")

#: Non-Python spellings of Python types, with what the guide asks for instead (C065).
NON_BASIC_TYPES = {"boolean": "bool", "integer": "int", "string": "str",
                   "dictionary": "dict"}

#: Precision-unqualified dtype names. `integral`/`floating` are the arbitrary-precision
#: spellings the guide prescribes; `int`/`float` are the two it names as wrong (C072).
ARBITRARY_PRECISION = {"integral", "floating"}
PYTHON_DTYPES = {"int", "float"}

_OF_SHAPE = re.compile(r"\bof shape\b")
_DTYPE = re.compile(r"\bdtype\s*=\s*\{?\s*(?P<name>[\w.]+)")
_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
_LIST_SUBSCRIPT = re.compile(r"\blist\s*[\[(]")
_DEFAULT_NONE_TAIL = re.compile(r"default\s*=\s*None\s*$")
_FRAME_LIKE = re.compile(r"\bcolumn names?\b|\bframe-like\b|\bdataframe\b", re.I)

_CODE_SNIPPET = re.compile(r"^\s*(>>>|\.\.\s+(code-block|literalinclude)::)|::\s*$", re.M)
_MATH = re.compile(r"^\s*\.\.\s+math::|:math:`", re.M)
_REFERENCES = re.compile(r"^\s*\.\.\s+(topic|rubric)::\s*References|^\s*References\s*$",
                         re.M | re.I)
_FIGURE = re.compile(r"^\s*\.\.\s+(figure|image|plot)::", re.M)
_DROPDOWN = re.compile(r"^(?P<indent>\s*)\.\.\s+dropdown::")
_EXAMPLES_HEADING = re.compile(r"^\s*Examples\s*$")
_LABEL = re.compile(r"^\s*\.\.\s+_(?P<name>[\w.+-]+):\s*$")
_RUBRIC_NOTE = re.compile(r"^\s*\.\.\s+rubric::\s*Note", re.M | re.I)
_NOTE_HEADING = re.compile(r"^\s*(Notes?)\s*$")

_ARXIV = re.compile(r"arxiv\.org/abs/[\w./-]+|\barXiv:\s*\d{4}\.\d{4,5}", re.I)
_DOI = re.compile(r"\b10\.\d{4,9}/\S+")
_ARXIV_ROLE = re.compile(r":arxiv:`")
_DOI_ROLE = re.compile(r":doi:`")
_TERM_ROLE = re.compile(r":term:`")
_GLOSSARY_LINK = re.compile(r":ref:`[^`]*glossary[^`]*`|glossary\.html")
_DOC_ROLE = re.compile(r":doc:`")
_REF_ROLE = re.compile(r":ref:`")
_CURRENTMODULE = re.compile(r"^\s*\.\.\s+currentmodule::", re.M)

#: Section markers belonging to a competing docstring format (C186).
_SPHINX_FIELD = re.compile(r"^\s*:(param|type|returns|rtype|raises)\b", re.M)
_GOOGLE_SECTION = re.compile(r"^\s*(Args|Returns|Raises|Attributes):\s*$", re.M)
_NUMPY_SECTION = re.compile(r"^\s*(Parameters|Returns|Raises|Examples|See Also|Attributes)"
                            r"\s*\n\s*-{3,}\s*$", re.M)


# --- shared selection ----------------------------------------------------------------


def _new_public_definitions(bundle: EvidenceBundle) -> list[tuple[str, str]]:
    """(path, name) for each public function or class the contribution adds to `sklearn/`.

    The stand-in for "a new feature". A proxy, and every rule that uses it declares
    ``heuristic=True`` because of it (§6.3): a new private helper is not a feature, and a
    feature can also arrive as a new keyword on an existing function.
    """
    out = []
    for path, module in modules(bundle, tests=False):
        if not path.startswith(PACKAGE):
            continue
        for function in module.functions:
            if function.name.startswith("_") or "." in function.qualname:
                continue
            if own.owns_span(bundle, path, function.span(), "created"):
                out.append((path, function.name))
        for info in classes(module):
            if info.name.startswith("_"):
                continue
            if own.owns_span(bundle, path, info.span(), "created"):
                out.append((path, info.name))
    return out


def _feature_target(bundle: EvidenceBundle, prefix: str) -> list[Target]:
    added = _new_public_definitions(bundle)
    if not added:
        return []
    path, name = added[0]
    return [target(f"{prefix}:{bundle.instance_id}", None, None, (bundle, added),
                   f"{len(added)} new public definition(s), e.g. {path}::{name}")]


def _entries(bundle: EvidenceBundle, section_name: str):
    """Every `name : type` entry of one section, in docstrings the agent touched."""
    out = []
    for path, _module, doc in owned_docstrings(bundle, tests=False,
                                               kinds=("function", "class")):
        section = numpydoc(doc).section(section_name)
        if section is None:
            continue
        for entry in parameter_entries(section):
            out.append((path, doc, entry))
    return out


def _type_line_targets(bundle: EvidenceBundle, prefix: str, keep) -> list[Target]:
    """Parameters-section type lines the agent touched, filtered by ``keep``."""
    out = []
    for path, _doc, entry in _entries(bundle, "Parameters"):
        if not keep(entry):
            continue
        out.append(target(f"{prefix}:{path}:{entry.lineno}", path,
                          (entry.lineno, entry.lineno), (path, entry),
                          f"{entry.names} : {entry.type_text}"[:90]))
    return out


def _written_doc_lines(bundle: EvidenceBundle, suffixes=(".rst",)):
    """(path, line number, text) for each documentation line the agent wrote."""
    out = []
    for path in sorted(bundle.files):
        if not path.endswith(suffixes) or not path.startswith(DOC_ROOT):
            continue
        for lineno, text in added_lines(bundle, path):
            out.append((path, lineno, text))
    return out


def _new_user_guide_pages(bundle: EvidenceBundle) -> list[str]:
    return [p for p in user_guide_files(bundle, mode="created")
            if bundle.files[p].is_new]


def _count_snippets(text: str) -> int:
    """Doctest blocks and explicit code blocks, counted as the guide counts snippets."""
    blocks = 0
    in_block = False
    for line in text.split("\n"):
        if re.match(r"^\s*>>>", line):
            if not in_block:
                blocks += 1
                in_block = True
        elif re.match(r"^\s*\.\.\s+code-block::", line):
            blocks += 1
            in_block = False
        elif not line.strip():
            in_block = False
    return blocks


def _class_doc(info):
    """The class docstring, parsed with real-ish line numbers for its entries."""
    return ds.parse([(n, line) for n, line
                     in enumerate((info.docstring or "").split("\n"), info.lineno)])


# --- the new-feature obligations -----------------------------------------------------


@rule(
    id="SCIKIT-LEARN-C036",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the feature the agent added to
                          # a package module that already existed
    reads=("files",),  # spec §5: both halves are in the patch
    heuristic=True,
)
class NewFeatureHasNarrativeUserGuideDocumentation:
    """Pre-condition: a contribution that adds a new public definition to `sklearn/`.
    Pass condition: it also writes user-guide reStructuredText containing a code snippet.

    Heuristic on **both layers** (§6.3, §6.2). "A new feature" is approximated by a new
    public function or class; "narrative documentation with small code snippets" is
    approximated by written lines in a `doc/` page carrying a doctest prompt, a
    `code-block` directive or a literal block. Fires on the feature, never on the
    documentation, so a feature documented nowhere is a recorded failure (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _feature_target(b, "user-guide")

    def pass_condition(self, t: Target):
        bundle, added = t.payload
        pages = user_guide_files(bundle)
        for path in pages:
            if _CODE_SNIPPET.search(added_text(bundle, path)):
                return Satisfied(f"{path} gains narrative documentation with a code "
                                 f"snippet")
        if pages:
            return Violated(f"{pages[0]} was changed but the new lines carry no code "
                            f"snippet illustrating {added[0][1]}")
        return Violated(f"{added[0][1]} is new but no user-guide page was written for it")


@rule(
    id="SCIKIT-LEARN-C038",
    category=CATEGORY,
    ownership="touched",  # spec §4.2
    reads=("files",),  # spec §5
    heuristic=True,
)
class UserGuideStatesComplexityAndScalability:
    """Pre-condition: a contribution that adds a new public definition and writes
    user-guide reStructuredText for it.
    Pass condition: those lines state the algorithm's complexity and its scalability.

    Narrowed to contributions that *did* write a user-guide section, because the absence
    of one is C036's finding and one defect must not depress two rates (§7.5). Heuristic
    on **both layers** (§6.3, §6.2): the feature proxy again, and "expected time and space
    complexity ... and scalability" is recognised by vocabulary -- `complexity`, `O(...)`,
    `scale`/`scalability` -- which a paragraph could satisfy in other words.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not _new_public_definitions(b):
            return []
        out = []
        for path in user_guide_files(b):
            written = added_text(b, path)
            if written.strip():
                out.append(target(f"complexity:{path}", path, None, (path, written),
                                  f"{len(written.splitlines())} written line(s)"))
        return out

    def pass_condition(self, t: Target):
        path, written = t.payload
        complexity = re.search(r"\bcomplexit\w+\b|\bO\s*\(", written, re.I)
        scalability = re.search(r"\bscalab\w+\b|\bscales?\b|\bscaling\b", written, re.I)
        if complexity and scalability:
            return Satisfied(f"{path} states both complexity and scalability")
        missing = []
        if not complexity:
            missing.append("time and space complexity")
        if not scalability:
            missing.append("scalability")
        return Violated(f"{path} documents a new feature without stating its "
                        f"{' and '.join(missing)}")


@rule(
    id="SCIKIT-LEARN-C039",
    category=CATEGORY,
    ownership="touched",  # spec §4.2
    reads=("files",),  # spec §5
    heuristic=True,
)
class NewFeatureHasAGalleryExample:
    """Pre-condition: a contribution that adds a new public definition to `sklearn/`.
    Pass condition: it adds a Python example under `examples/`.

    Heuristic on the **pre-condition** (§6.3): the new-feature proxy. The pass condition
    is exact -- one directory is named, and a file either appears in it or does not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _feature_target(b, "usage-example")

    def pass_condition(self, t: Target):
        bundle, added = t.payload
        new_examples = [p for p in example_files(bundle, mode="created")
                        if bundle.files[p].is_new]
        if new_examples:
            return Satisfied(f"usage example added: {new_examples[0]}")
        return Violated(f"{added[0][1]} is new but no example was added under "
                        f"{EXAMPLES_ROOT}")


@rule(
    id="SCIKIT-LEARN-C060",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- a pre-existing undocumented function is not the
                          # agent's doing; only definitions it added are judged
    reads=("files",),  # spec §5
    heuristic=True,
)
class ApiDocumentationLivesBesideTheCode:
    """Pre-condition: each public function or class the agent adds under `sklearn/`.
    Pass condition: it carries a docstring in the file that defines it.

    The sentence places API documentation *alongside the code in `sklearn/`*, so the
    graded question is whether the object the agent added documents itself there rather
    than being described only in `doc/`. Heuristic on the **pre-condition** (§6.3):
    "function/method/class" is narrowed to public definitions, since the leading
    underscore is the project's own marker for what is not API.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=False):
            if not path.startswith(PACKAGE):
                continue
            for function in module.functions:
                if function.name.startswith("_"):
                    continue
                if own.owns_span(b, path, function.span(), "created"):
                    out.append(target(f"api-doc:{path}:{function.name}", path,
                                      function.span(),
                                      (path, function.name, function.docstring),
                                      f"{path}::{function.name}"))
            for info in classes(module):
                if info.name.startswith("_"):
                    continue
                if own.owns_span(b, path, info.span(), "created"):
                    out.append(target(f"api-doc:{path}:{info.name}", path, info.span(),
                                      (path, info.name, info.docstring),
                                      f"{path}::{info.name}"))
        return out

    def pass_condition(self, t: Target):
        path, name, docstring = t.payload
        if docstring and docstring.strip():
            return Satisfied(f"{path}::{name} documents itself beside the code")
        return Violated(f"{path}::{name} is public API with no docstring in {PACKAGE}")


@rule(
    id="SCIKIT-LEARN-C062",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the example did not exist before the run
    reads=("files",),  # spec §5
    heuristic=True,
)
class GalleryExamplesLiveUnderExamples:
    """Pre-condition: each Python file the contribution adds that is written as a gallery
    example.
    Pass condition: it sits under `examples/`.

    Heuristic on the **pre-condition** (§6.3): a gallery example is recognised by the two
    marks sphinx-gallery reads -- a `plot_`-prefixed filename or `# %%` cell separators --
    so an example written without either is not selected. Fires on the example, wherever
    it was put, rather than on `examples/` itself; selecting the directory would find only
    files already in the right place (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            change = b.files[path]
            if not path.endswith(".py") or not change.is_new:
                continue
            text = file_text(b, path)
            name = path.rsplit("/", 1)[-1]
            if not (name.startswith("plot_") or "# %%" in text):
                continue
            out.append(target(f"gallery:{path}", path, None, path, path))
        return out

    def pass_condition(self, t: Target):
        path: str = t.payload
        if path.startswith(EXAMPLES_ROOT):
            return Satisfied(f"{path} is in the gallery directory")
        return Violated(f"{path} is written as a gallery example but does not live "
                        f"under {EXAMPLES_ROOT}")


# --- the numpydoc conventions --------------------------------------------------------


@rule(
    id="SCIKIT-LEARN-C064",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier; editing a docstring makes
                          # the agent answerable for its form
    reads=("files",),  # spec §5
)
class DocstringSectionsAreInTheStatedOrder:
    """Pre-condition: each docstring the agent wrote or edited carrying at least two of
    Parameters, Returns, See Also, Notes and Examples.
    Pass condition: those sections appear in that order.

    Not heuristic: the guide states the sequence, and the check compares two lists.
    Sections outside the five are ignored rather than guessed at, because the guide
    explicitly defers to numpydoc for the rest.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc in owned_docstrings(b, tests=False):
            present = [s for s in numpydoc(doc).section_order() if s in SECTION_ORDER]
            if len(present) >= 2:
                out.append(target(f"section-order:{path}:{doc.lineno}", path, doc.span(),
                                  (path, doc, present), " then ".join(present)))
        return out

    def pass_condition(self, t: Target):
        path, doc, present = t.payload
        expected = [s for s in SECTION_ORDER if s in present]
        if present == expected:
            return Satisfied(f"{path}:{doc.lineno} orders its sections "
                             f"{' then '.join(present)}")
        return Violated(f"{path}:{doc.lineno} orders its sections "
                        f"{' then '.join(present)}; the guide states "
                        f"{' then '.join(expected)}")


@rule(
    id="SCIKIT-LEARN-C065",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ParameterTypesUsePythonBasicNames:
    """Pre-condition: each Parameters entry in a docstring the agent wrote or edited.
    Pass condition: its type line uses no long-hand spelling of a Python basic type.

    Heuristic on the **pass condition** (§6.2): the guide gives one worked pair
    (`bool` for `boolean`) and leaves the rest to "use Python basic types", so the list of
    wrong spellings -- boolean, integer, string, dictionary -- is this pack's, not the
    project's. A fifth long-hand name would pass.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _type_line_targets(b, "basic-types", lambda entry: True)

    def pass_condition(self, t: Target):
        path, entry = t.payload
        for wrong, right in NON_BASIC_TYPES.items():
            if re.search(rf"\b{wrong}\b", entry.type_text, re.I):
                return Violated(f"{path}:{entry.lineno} documents `{entry.names}` as "
                                f"`{wrong}`; the Python basic type is `{right}`")
        return Satisfied(f"{path}:{entry.lineno} names `{entry.names}`'s type in Python "
                         f"basic types")


@rule(
    id="SCIKIT-LEARN-C066",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class ArrayShapesAreParenthesised:
    """Pre-condition: each Parameters entry the agent wrote or edited whose type line says
    `of shape`.
    Pass condition: a parenthesised shape follows those words.

    Not heuristic: the phrase and the parenthesis are both exact, and the guide gives the
    form with worked examples and no alternative.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _type_line_targets(b, "shape",
                                  lambda e: bool(_OF_SHAPE.search(e.type_text)))

    def pass_condition(self, t: Target):
        path, entry = t.payload
        match = _OF_SHAPE.search(entry.type_text)
        tail = entry.type_text[match.end():].lstrip()
        if tail.startswith("("):
            return Satisfied(f"{path}:{entry.lineno} writes the shape as {tail[:30]}")
        return Violated(f"{path}:{entry.lineno} writes `of shape {tail[:30]}` without "
                        f"parentheses")


@rule(
    id="SCIKIT-LEARN-C067",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class StringOptionsAreABraceEnclosedSet:
    """Pre-condition: each Parameters entry the agent wrote or edited whose type line
    offers two or more quoted string values.
    Pass condition: they are enclosed in braces.

    Heuristic on the **pre-condition** (§6.3): "strings with multiple options" is
    approximated by counting quoted literals on the type line, which also catches a
    default written as a string beside a single option. The pass condition is exact --
    the brace set is the form the guide gives and the codebase reproduces.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _type_line_targets(b, "options",
                                  lambda e: len(_QUOTED.findall(e.type_text)) >= 2)

    def pass_condition(self, t: Target):
        path, entry = t.payload
        if "{" in entry.type_text and "}" in entry.type_text:
            return Satisfied(f"{path}:{entry.lineno} writes `{entry.names}`'s options as "
                             f"a brace-enclosed set")
        return Violated(f"{path}:{entry.lineno} lists `{entry.names}`'s string options "
                        f"without braces: {entry.type_text[:60]}")


@rule(
    id="SCIKIT-LEARN-C069",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class FrameLikeParametersAreCalledDataframes:
    """Pre-condition: each Parameters entry the agent wrote or edited whose description
    relies on frame-like features such as column names.
    Pass condition: its type line uses the term `dataframe`.

    Heuristic on the **pre-condition** (§6.3): "frame-like features are being used" is
    approximated by the description mentioning column names or frame-likeness, which is
    the example the guide itself gives; a parameter that relies on per-column dtypes
    without saying so is not selected.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _doc, entry in _entries(b, "Parameters"):
            if not _FRAME_LIKE.search(entry.description_text()):
                continue
            out.append(target(f"dataframe:{path}:{entry.lineno}", path,
                              (entry.lineno, entry.lineno), (path, entry),
                              f"{entry.names} : {entry.type_text}"[:90]))
        return out

    def pass_condition(self, t: Target):
        path, entry = t.payload
        if re.search(r"\bdataframe\b", entry.type_text, re.I):
            return Satisfied(f"{path}:{entry.lineno} documents `{entry.names}` as a "
                             f"dataframe")
        return Violated(f"{path}:{entry.lineno} says `{entry.names}` relies on column "
                        f"names but types it as `{entry.type_text[:40]}`")


@rule(
    id="SCIKIT-LEARN-C070",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ListElementTypesUseOfAsTheDelimiter:
    """Pre-condition: each Parameters entry the agent wrote or edited whose type line
    documents a `list`.
    Pass condition: the element type is not written as a subscript or a call.

    Heuristic on the **pass condition** (§6.2), and graded one-sidedly: `of` is confirmed
    where it appears, and `list[int]` or `list(int)` -- the two spellings that replace the
    named delimiter -- are reported. A third way of attaching an element type would pass.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _type_line_targets(b, "list-of",
                                  lambda e: bool(re.search(r"\blist\b", e.type_text)))

    def pass_condition(self, t: Target):
        path, entry = t.payload
        if match := _LIST_SUBSCRIPT.search(entry.type_text):
            return Violated(f"{path}:{entry.lineno} writes `{match.group(0)}...`; the "
                            f"guide names `of` as the delimiter, as in `list of int`")
        if re.search(r"\blist of\b", entry.type_text):
            return Satisfied(f"{path}:{entry.lineno} uses `list of` for `{entry.names}`")
        return Satisfied(f"{path}:{entry.lineno} documents `{entry.names}` as a bare "
                         f"list, with no element type to delimit")


@rule(
    id="SCIKIT-LEARN-C071",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class DtypeComesAfterTheShape:
    """Pre-condition: each Parameters entry the agent wrote or edited whose type line
    gives both a shape and a dtype.
    Pass condition: the dtype comes after the shape.

    Not heuristic: two substrings and their order on one line, which is the whole of what
    the guide fixes.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _type_line_targets(
            b, "dtype-order",
            lambda e: bool(_OF_SHAPE.search(e.type_text) and _DTYPE.search(e.type_text)))

    def pass_condition(self, t: Target):
        path, entry = t.payload
        shape = _OF_SHAPE.search(entry.type_text).start()
        dtype = _DTYPE.search(entry.type_text).start()
        if dtype > shape:
            return Satisfied(f"{path}:{entry.lineno} gives the shape then the dtype")
        return Violated(f"{path}:{entry.lineno} gives the dtype before the shape: "
                        f"{entry.type_text[:60]}")


@rule(
    id="SCIKIT-LEARN-C072",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ArbitraryPrecisionUsesIntegralAndFloating:
    """Pre-condition: each Parameters entry the agent wrote or edited whose type line
    gives a dtype with no precision -- `int`, `float`, `integral` or `floating`.
    Pass condition: it uses `integral` or `floating`.

    Heuristic on the **pre-condition** (§6.3): "if one wants to mention arbitrary
    precision" is an intention, approximated by the dtype being named without a bit
    width, so `dtype=np.int32` is correctly not selected and a documented `dtype=int`
    meaning exactly 64-bit would be.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        def keep(entry) -> bool:
            match = _DTYPE.search(entry.type_text)
            return bool(match) and match.group("name") in (ARBITRARY_PRECISION
                                                           | PYTHON_DTYPES)

        return _type_line_targets(b, "precision", keep)

    def pass_condition(self, t: Target):
        path, entry = t.payload
        name = _DTYPE.search(entry.type_text).group("name")
        if name in ARBITRARY_PRECISION:
            return Satisfied(f"{path}:{entry.lineno} uses `{name}` for arbitrary "
                             f"precision")
        wanted = "integral" if name == "int" else "floating"
        return Violated(f"{path}:{entry.lineno} writes `dtype={name}`; arbitrary "
                        f"precision is written `{wanted}`")


@rule(
    id="SCIKIT-LEARN-C073",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class NoneDefaultIsWrittenOnceAtTheEnd:
    """Pre-condition: each Parameters entry the agent wrote or edited whose type line
    mentions `None`.
    Pass condition: `None` appears once, as `default=None`, at the end of the line.

    Heuristic on the **pre-condition** (§6.3): "when the default is None" is approximated
    by the word appearing on the type line, which also selects a parameter whose type
    genuinely admits `None` without defaulting to it -- and that entry then passes only by
    writing the sanctioned form, which is stricter than the sentence.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _type_line_targets(b, "default-none", lambda e: "None" in e.type_text)

    def pass_condition(self, t: Target):
        path, entry = t.payload
        occurrences = len(re.findall(r"\bNone\b", entry.type_text))
        if occurrences > 1:
            return Violated(f"{path}:{entry.lineno} mentions None {occurrences} times; "
                            f"it only needs to be given once, at the end")
        if _DEFAULT_NONE_TAIL.search(entry.type_text):
            return Satisfied(f"{path}:{entry.lineno} ends with `default=None`")
        return Violated(f"{path}:{entry.lineno} mentions None but does not end with "
                        f"`default=None`: {entry.type_text[:60]}")


@rule(
    id="SCIKIT-LEARN-C076",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class SeeAlsoEntriesCarryAnExplanation:
    """Pre-condition: each `See Also` section in a docstring the agent wrote or edited.
    Pass condition: every entry is one line of the form `name : explanation`.

    Heuristic on the **pass condition** (§6.2): an entry's continuation line is told from
    a new entry by indentation, so a wrapped explanation indented to the same column as
    its entry would be read as a nameless entry.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc in owned_docstrings(b, tests=False):
            section = numpydoc(doc).section("See Also")
            if section is None or not any(t.strip() for _, t in section.body):
                continue
            out.append(target(f"see-also:{path}:{doc.lineno}", path, doc.span(),
                              (path, doc, section),
                              f"See Also with {len(section.body)} line(s)"))
        return out

    def pass_condition(self, t: Target):
        path, doc, section = t.payload
        indents = [len(text) - len(text.lstrip())
                   for _, text in section.body if text.strip()]
        base = min(indents) if indents else 0
        for lineno, text in section.body:
            if not text.strip() or (len(text) - len(text.lstrip())) > base:
                continue  # a continuation line of the entry above
            if ":" not in text or not text.split(":", 1)[1].strip():
                return Violated(f"{path}:{lineno} is a See Also entry with no colon and "
                                f"explanation: {text.strip()[:60]}")
        return Satisfied(f"{path}:{doc.lineno} writes each See Also entry on one line "
                         f"with an explanation")


@rule(
    id="SCIKIT-LEARN-C077",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class AttributeNotesUseTheRubricDirective:
    """Pre-condition: each `Attributes` section in a docstring the agent wrote or edited
    that carries a note.
    Pass condition: the note is written with `.. rubric:: Note`.

    Heuristic on the **pre-condition** (§6.3): "a Note added to an attribute" is
    recognised by a `Note`/`Notes` heading or a `.. note::` directive inside the
    Attributes section, so a note written as ordinary prose is not selected -- and would
    not render as a note either.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc in owned_docstrings(b, tests=False):
            section = numpydoc(doc).section("Attributes")
            if section is None:
                continue
            body = "\n".join(text for _, text in section.body)
            has_note = (_RUBRIC_NOTE.search(body)
                        or re.search(r"^\s*\.\.\s+note::", body, re.M)
                        or any(_NOTE_HEADING.match(text) for _, text in section.body))
            if not has_note:
                continue
            out.append(target(f"rubric-note:{path}:{doc.lineno}", path, doc.span(),
                              (path, doc, body), "Attributes section with a note"))
        return out

    def pass_condition(self, t: Target):
        path, doc, body = t.payload
        if _RUBRIC_NOTE.search(body):
            return Satisfied(f"{path}:{doc.lineno} uses `.. rubric:: Note`")
        return Violated(f"{path}:{doc.lineno} attaches a note to an attribute without "
                        f"the `.. rubric:: Note` directive")


@rule(
    id="SCIKIT-LEARN-C078",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ExampleSectionsCarryOneOrTwoSnippets:
    """Pre-condition: each docstring the agent wrote or edited that has an Examples
    section.
    Pass condition: it holds one or two code snippets.

    Heuristic on the **pass condition** (§6.2): "a snippet" is counted as a run of
    doctest lines separated by a blank line, which is how the section is written, but two
    logically separate examples written without a blank line between them count as one.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc in owned_docstrings(b, tests=False):
            section = numpydoc(doc).section("Examples")
            if section is None:
                continue
            blocks = ds.doctest_blocks(section.body)
            out.append(target(f"snippets:{path}:{doc.lineno}", path, doc.span(),
                              (path, doc, blocks), f"{len(blocks)} snippet(s)"))
        return out

    def pass_condition(self, t: Target):
        path, doc, blocks = t.payload
        if 1 <= len(blocks) <= 2:
            return Satisfied(f"{path}:{doc.lineno} shows {len(blocks)} snippet(s)")
        if not blocks:
            return Violated(f"{path}:{doc.lineno} has an Examples section with no code "
                            f"snippet in it")
        return Violated(f"{path}:{doc.lineno} shows {len(blocks)} snippets; the guide "
                        f"asks for one or two and to keep the section brief")


@rule(
    id="SCIKIT-LEARN-C079",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DocstringExamplesAreRunnableAsIs:
    """Pre-condition: each Examples section the agent wrote or edited that contains
    doctest lines.
    Pass condition: every module the example calls through is imported inside it.

    Heuristic on the **pass condition** (§6.2), and narrower than the sentence: really
    running the example is what `pytest --doctest-modules` does and nothing here executes
    anything, so the check is the failure the guide names -- a missing import. Only names
    used as `name.attr` are checked, and an undefined bare name is not reported at all.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, doc in owned_docstrings(b, tests=False):
            section = numpydoc(doc).section("Examples")
            if section is None:
                continue
            sources = [text for _, text in section.body if text.strip().startswith(">>>")]
            if not sources:
                continue
            out.append(target(f"runnable:{path}:{doc.lineno}", path, doc.span(),
                              (path, doc, sources), f"{len(sources)} doctest line(s)"))
        return out

    def pass_condition(self, t: Target):
        path, doc, sources = t.payload
        body = "\n".join(s.strip().lstrip("> ") for s in sources)
        bound: set[str] = set()
        for name, alias in re.findall(r"^\s*import\s+([\w.]+)(?:\s+as\s+(\w+))?", body,
                                      re.M):
            bound.add(alias or name.split(".")[0])
        for names in re.findall(r"^\s*from\s+[\w.]+\s+import\s+(.+)$", body, re.M):
            for chunk in names.split(","):
                bound.add(chunk.split(" as ")[-1].strip())
        bound |= set(re.findall(r"^\s*(\w+)\s*=", body, re.M))
        for target_names in re.findall(r"^\s*(?:for\s+)([\w, ]+?)\s+in\s", body, re.M):
            bound |= {n.strip() for n in target_names.split(",")}
        used = set(re.findall(r"\b([A-Za-z_]\w*)\s*\.", body))
        missing = sorted(used - bound - {"self"})
        if missing:
            return Violated(f"{path}:{doc.lineno} uses `{missing[0]}` in an example that "
                            f"never imports it, so the snippet is not runnable as is")
        return Satisfied(f"{path}:{doc.lineno} imports everything its example calls")


# --- the reStructuredText conventions ------------------------------------------------


@rule(
    id="SCIKIT-LEARN-C085",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the sentence is about a NEW user-guide section
    reads=("files",),  # spec §5
    heuristic=True,
)
class NewUserGuideSectionsCarryAFigure:
    """Pre-condition: each user-guide page the contribution adds.
    Pass condition: it incorporates a figure.

    Heuristic on **both layers** (§6.3, §6.2): "a new user-guide section" is approximated
    by a new page under `doc/`, so a section added to an existing page is not selected,
    and "generated from an example" is not confirmed -- a `figure`, `image` or `plot`
    directive satisfies this whether or not its source is the gallery.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"figure:{p}", p, None, (p, file_text(b, p)), p)
                for p in _new_user_guide_pages(b)]

    def pass_condition(self, t: Target):
        path, text = t.payload
        if match := _FIGURE.search(text):
            return Satisfied(f"{path} incorporates a figure: {match.group(0).strip()}")
        return Violated(f"{path} is a new user-guide page with no figure to provide "
                        f"intuitions")


@rule(
    id="SCIKIT-LEARN-C086",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the same new-section antecedent as C085
    reads=("files",),  # spec §5
    heuristic=True,
)
class NewUserGuideSectionsCarryOneOrTwoCodeExamples:
    """Pre-condition: each user-guide page the contribution adds.
    Pass condition: it holds one or two short code examples.

    Heuristic on **both layers** (§6.3, §6.2) for the same reasons as C085, plus the
    counting rule: a doctest run and a `code-block` directive each count as one example,
    and "short" is not graded at all.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"guide-snippets:{p}", p, None, (p, file_text(b, p)), p)
                for p in _new_user_guide_pages(b)]

    def pass_condition(self, t: Target):
        path, text = t.payload
        count = _count_snippets(text)
        if 1 <= count <= 2:
            return Satisfied(f"{path} demonstrates usage in {count} code example(s)")
        if count == 0:
            return Violated(f"{path} is a new user-guide page with no code example")
        return Violated(f"{path} carries {count} code examples; the guide asks for one "
                        f"or two")


@rule(
    id="SCIKIT-LEARN-C087",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the new-section antecedent again
    reads=("files",),  # spec §5
    heuristic=True,
)
class EquationsComeLastFollowedByReferences:
    """Pre-condition: each user-guide page the contribution adds that carries mathematics.
    Pass condition: a references block follows the last equation.

    Heuristic on the **pass condition** (§6.2): "equations last, followed by references"
    is graded as *the references come after the last equation*, which is the observable
    half of the ordering; whether prose following an equation is discussion or a caption
    cannot be told from the markup.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _new_user_guide_pages(b):
            text = file_text(b, path)
            if _MATH.search(text):
                out.append(target(f"equations:{path}", path, None, (path, text),
                                  f"{len(_MATH.findall(text))} equation(s)"))
        return out

    def pass_condition(self, t: Target):
        path, text = t.payload
        last_math = max(m.start() for m in _MATH.finditer(text))
        references = [m.start() for m in _REFERENCES.finditer(text)]
        if any(position > last_math for position in references):
            return Satisfied(f"{path} places its references after the last equation")
        if references:
            return Violated(f"{path} puts its references before the equations rather "
                            f"than after them")
        return Violated(f"{path} introduces equations but gives no references after them")


@rule(
    id="SCIKIT-LEARN-C089",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- states a property of the project's reST files
    reads=("files",),  # spec §5
    heuristic=True,
)
class InlineLiteralsUseSingleBackticks:
    """Pre-condition: each reStructuredText line the agent wrote in `doc/` that carries an
    inline-literal span.
    Pass condition: it is written with single backticks.

    Heuristic on the **pass condition** (§6.2): the check cannot see whether a line sits
    inside a literal block, where double backticks are ordinary text, so a double-backtick
    pair inside a code sample would be reported. Both forms render identically -- the
    guide says so -- which is why only the sanctioned spelling satisfies the instruction.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, lineno, text in _written_doc_lines(b):
            if "``" in text or rst.single_backtick_spans(text):
                out.append(target(f"backticks:{path}:{lineno}", path, (lineno, lineno),
                                  (path, lineno, text), text.strip()[:80]))
        return out

    def pass_condition(self, t: Target):
        path, lineno, text = t.payload
        if literals := rst.inline_literals(text):
            return Violated(f"{path}:{lineno} writes ``{literals[0][:30]}`` with double "
                            f"backticks; single backticks are the current practice")
        return Satisfied(f"{path}:{lineno} uses single backticks for its inline literals")


@rule(
    id="SCIKIT-LEARN-C092",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ExamplesAreNotFoldedIntoADropdown:
    """Pre-condition: each documentation page the contribution touches that uses a
    `dropdown` directive.
    Pass condition: no `Examples` heading sits inside one.

    A prohibition, so the antecedent is *using dropdowns at all* and the graded question
    is what was folded into them (§7.1). Heuristic on the **pass condition** (§6.2): a
    directive's body is identified by indentation rather than parsed, so an `Examples`
    heading indented for another reason directly under a dropdown would be reported.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in user_guide_files(b):
            lines = head_lines(b, path)
            if any(_DROPDOWN.match(text) for _, text in lines):
                out.append(target(f"dropdown:{path}", path, None, (path, lines), path))
        return out

    def pass_condition(self, t: Target):
        path, lines = t.payload
        inside = None
        for lineno, text in lines:
            if match := _DROPDOWN.match(text):
                inside = len(match.group("indent"))
                continue
            if inside is None:
                continue
            if text.strip() and (len(text) - len(text.lstrip())) <= inside:
                inside = None
                continue
            if _EXAMPLES_HEADING.match(text):
                return Violated(f"{path}:{lineno} folds the Examples section into a "
                                f"dropdown, where it is hidden from most users")
        return Satisfied(f"{path} uses dropdowns without folding Examples into one")


@rule(
    id="SCIKIT-LEARN-C093",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ExamplesFollowTheMainDiscussion:
    """Pre-condition: each documentation page the contribution touches that carries an
    `Examples` section.
    Pass condition: no folded section sits between the preceding heading and it.

    Heuristic on the **pass condition** (§6.2): "right after the main discussion with the
    least possible folded section in-between" is graded as *no dropdown between the
    previous heading and the Examples heading*, which is the part of the sentence a file
    can answer; how much prose counts as the main discussion is not decidable from markup.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in user_guide_files(b):
            lines = head_lines(b, path)
            positions = [n for n, text in lines if _EXAMPLES_HEADING.match(text)]
            if positions:
                out.append(target(f"examples-position:{path}", path, None,
                                  (path, lines, positions[0]),
                                  f"Examples heading at line {positions[0]}"))
        return out

    def pass_condition(self, t: Target):
        path, lines, position = t.payload
        previous_heading = max((h.lineno for h in rst.headings(list(lines))
                                if h.lineno < position), default=0)
        folded = [n for n, text in lines
                  if _DROPDOWN.match(text) and previous_heading < n < position]
        if folded:
            return Violated(f"{path}:{folded[0]} folds a section between the discussion "
                            f"and the Examples heading at line {position}")
        return Satisfied(f"{path} places Examples directly after the discussion")


@rule(
    id="SCIKIT-LEARN-C095",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class ArxivAndDoiReferencesUseTheirRoles:
    """Pre-condition: each documentation line the agent wrote that carries an arXiv
    identifier or a DOI.
    Pass condition: it cites them with the `:arxiv:` or `:doi:` role.

    Heuristic on the **pre-condition** (§6.3): "a reference available with an arXiv or DOI
    identification number" is approximated by the identifier appearing in the written
    text, so a paper whose DOI the author never wrote down is not selected -- which is
    also the only case a checker could not fault anyone for.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, lineno, text in _written_doc_lines(b):
            kind = ""
            if _ARXIV.search(text) or _ARXIV_ROLE.search(text):
                kind = "arxiv"
            elif _DOI.search(text) or _DOI_ROLE.search(text):
                kind = "doi"
            if not kind:
                continue
            out.append(target(f"citation:{path}:{lineno}", path, (lineno, lineno),
                              (path, lineno, text, kind), text.strip()[:80]))
        return out

    def pass_condition(self, t: Target):
        path, lineno, text, kind = t.payload
        role = _ARXIV_ROLE if kind == "arxiv" else _DOI_ROLE
        if role.search(text):
            return Satisfied(f"{path}:{lineno} cites the {kind} identifier with its role")
        return Violated(f"{path}:{lineno} gives a {kind} identifier without the "
                        f"`:{kind}:` role: {text.strip()[:60]}")


@rule(
    id="SCIKIT-LEARN-C097",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class SectionLinksGoThroughAReferenceLabel:
    """Pre-condition: each documentation line the agent wrote that links to another page
    or section.
    Pass condition: the link is a `:ref:` role.

    Heuristic on the **pre-condition** (§6.3): "a link to an arbitrary section" is
    approximated by the two forms this documentation uses -- a `:doc:` role and a `:ref:`
    role -- so a raw HTML anchor is not selected. Both are selected on purpose: taking
    only `:doc:` would find violations and never a compliant link (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, lineno, text in _written_doc_lines(b):
            if _DOC_ROLE.search(text) or _REF_ROLE.search(text):
                out.append(target(f"section-link:{path}:{lineno}", path, (lineno, lineno),
                                  (path, lineno, text), text.strip()[:80]))
        return out

    def pass_condition(self, t: Target):
        path, lineno, text = t.payload
        if _REF_ROLE.search(text):
            return Satisfied(f"{path}:{lineno} links through a reference label")
        return Violated(f"{path}:{lineno} links with the `:doc:` role rather than a "
                        f"reference label and `:ref:`: {text.strip()[:60]}")


@rule(
    id="SCIKIT-LEARN-C098",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- deletion is editing, so a file whose labels the
                          # agent removed is owned (§4.1)
    reads=("files",),  # spec §5
)
class ExistingReferenceLabelsSurvive:
    """Pre-condition: each documentation page the agent edited that removed lines.
    Pass condition: no `.. _label:` line was removed without being written back.

    A prohibition, so the antecedent is *editing a page*, not the removal the rule forbids
    (§7.1). Not heuristic: a label definition is one exact line shape, and the diff records
    both what left and what arrived, so renaming a label shows up as its old line removed
    and not re-added.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            change = b.files[path]
            if not path.endswith(".rst") or change.is_new or not change.removed_lines:
                continue
            out.append(target(f"labels:{path}", path, None, (path, change),
                              f"{len(change.removed_lines)} removed line(s)"))
        return out

    def pass_condition(self, t: Target):
        path, change = t.payload
        removed = {m.group("name") for line in change.removed_lines
                   if (m := _LABEL.match(line))}
        if not removed:
            return Satisfied(f"{path} removes no reference label")
        kept = {m.group("name") for _, line in change.added_lines
                if (m := _LABEL.match(line))}
        lost = sorted(removed - kept)
        if lost:
            return Violated(f"{path} removes the reference label `_{lost[0]}:`, breaking "
                            f"every cross reference and external link to it")
        return Satisfied(f"{path} rewrites {len(removed)} label line(s) and keeps every "
                         f"label name")


@rule(
    id="SCIKIT-LEARN-C099",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class GlossaryTermsUseTheTermRole:
    """Pre-condition: each documentation line the agent wrote that points at the glossary.
    Pass condition: it does so with the `:term:` role.

    Heuristic on the **pre-condition** (§6.3): "linking to a term in the glossary" is
    recognised by the `:term:` role itself or by a link naming the glossary page, so a
    term mentioned in prose with no link at all is not selected -- the sentence is about
    how a link is written, not about which words must be linked.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, lineno, text in _written_doc_lines(b):
            if _TERM_ROLE.search(text) or _GLOSSARY_LINK.search(text):
                out.append(target(f"glossary:{path}:{lineno}", path, (lineno, lineno),
                                  (path, lineno, text), text.strip()[:80]))
        return out

    def pass_condition(self, t: Target):
        path, lineno, text = t.payload
        if _TERM_ROLE.search(text):
            return Satisfied(f"{path}:{lineno} links the glossary term with `:term:`")
        return Violated(f"{path}:{lineno} points at the glossary without the `:term:` "
                        f"role: {text.strip()[:60]}")


def _dotted_role_rule(role_name: str):
    """The shared body of C100 and C102: a role whose target must be a full import path."""
    pattern = re.compile(rf":{role_name}:`(?P<target>[^`]+)`")

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            if not path.endswith((".rst", ".py")):
                continue
            if not path.startswith((DOC_ROOT, PACKAGE, EXAMPLES_ROOT)):
                continue
            has_currentmodule = bool(_CURRENTMODULE.search(file_text(b, path)))
            for lineno, text in added_lines(b, path):
                for match in pattern.finditer(text):
                    out.append(target(f"{role_name}-role:{path}:{lineno}", path,
                                      (lineno, lineno),
                                      (path, lineno, match.group("target"),
                                       has_currentmodule), match.group(0)[:80]))
        return out

    def pass_condition(self, t: Target):
        path, lineno, written, has_currentmodule = t.payload
        cleaned = written.lstrip("~").split("<")[-1].rstrip(">").strip()
        if "." in cleaned:
            return Satisfied(f"{path}:{lineno} uses the full import path `{cleaned}`")
        if has_currentmodule:
            return Satisfied(f"{path}:{lineno} shortens `{cleaned}`, which the page's "
                             f"own `.. currentmodule::` directive allows")
        return Violated(f"{path}:{lineno} links `{cleaned}` without its full import "
                        f"path and the page sets no `.. currentmodule::`")

    return precondition, pass_condition


_FUNC_PRE, _FUNC_PASS = _dotted_role_rule("func")
_CLASS_PRE, _CLASS_PASS = _dotted_role_rule("class")


@rule(
    id="SCIKIT-LEARN-C100",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class FunctionRolesUseTheFullImportPath:
    """Pre-condition: each `:func:` role the agent wrote in documentation or a docstring.
    Pass condition: its target is a full import path, or the page sets `currentmodule`.

    Not heuristic: a role's target is one string, a dot either appears in it or does not,
    and the `currentmodule` exception is the page's own directive rather than a guess.
    """

    precondition = _FUNC_PRE
    pass_condition = _FUNC_PASS


@rule(
    id="SCIKIT-LEARN-C102",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class ClassRolesUseTheFullImportPath:
    """Pre-condition: each `:class:` role the agent wrote in documentation or a docstring.
    Pass condition: its target is a full import path, unless a `.. currentmodule::`
    directive in the same file shortens it.

    Not heuristic, and the exception is written into the rule itself rather than inferred:
    the guide states it in the same sentence.
    """

    precondition = _CLASS_PRE
    pass_condition = _CLASS_PASS


# --- deprecation and estimator documentation -----------------------------------------


@rule(
    id="SCIKIT-LEARN-C126",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the deprecation, a change to
                          # code that already existed
    reads=("files",),  # spec §5
    heuristic=True,
)
class DeprecationsCarryADeprecatedDirective:
    """Pre-condition: each object the contribution deprecates with `@deprecated`.
    Pass condition: its docstring carries a `.. deprecated::` directive.

    Heuristic on the **pre-condition** (§6.3): a deprecation is recognised by the
    decorator the project supplies, so one announced only by a hand-written
    `FutureWarning` is not selected. The directive itself is named exactly by the
    sentence, and whether its content repeats the warning's information is not graded --
    C123 is the rule about the warning's content.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=False):
            for function in module.functions:
                if not function.has_decorator("deprecated"):
                    continue
                out.append(target(f"deprecated-note:{path}:{function.name}", path,
                                  function.span(),
                                  (path, function.name, function.docstring),
                                  f"{path}::{function.name}"))
            for info in classes(module):
                if not any(d.split(".")[-1] == "deprecated" for d in info.decorators):
                    continue
                out.append(target(f"deprecated-note:{path}:{info.name}", path,
                                  info.span(), (path, info.name, info.docstring),
                                  f"{path}::{info.name}"))
        return out

    def pass_condition(self, t: Target):
        path, name, docstring = t.payload
        if has_deprecated_directive(docstring or ""):
            return Satisfied(f"{path}::{name} carries a `.. deprecated::` note")
        return Violated(f"{path}::{name} is deprecated but its docstring carries no "
                        f"`.. deprecated::` note repeating the warning")


@rule(
    id="SCIKIT-LEARN-C132",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the default the agent changed
    reads=("files",),  # spec §5: the comparison is between the file's base and head text
    heuristic=True,
)
class ChangedDefaultsCarryAVersionchangedDirective:
    """Pre-condition: each function whose keyword default the contribution changes.
    Pass condition: its docstring carries a `.. versionchanged::` directive.

    Heuristic on the **pass condition** (§6.2): the directive is required *on the
    parameter description* and to give the old and new values, and this confirms only that
    the docstring gained one -- a directive attached to the wrong parameter passes. The
    pre-condition is exact where the base text was reconstructed and selects nothing where
    it was not, which is a gap in the evidence rather than an approximation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=False):
            base = base_module(b, path)
            if base is None:
                continue
            before = {f.qualname: f for f in base.functions}
            for function in module.functions:
                previous = before.get(function.qualname)
                if previous is None:
                    continue
                old = {n: ast.dump(v) for n, v in keyword_defaults(previous.node).items()}
                new = {n: ast.dump(v) for n, v in keyword_defaults(function.node).items()}
                changed = [n for n in old if n in new and old[n] != new[n]]
                if not changed:
                    continue
                out.append(target(f"versionchanged:{path}:{function.qualname}", path,
                                  function.span(), (path, function, changed),
                                  f"{function.qualname} changes {', '.join(changed)}"))
        return out

    def pass_condition(self, t: Target):
        path, function, changed = t.payload
        if has_versionchanged_directive(function.docstring or ""):
            return Satisfied(f"{path}::{function.qualname} documents the changed default "
                             f"with `.. versionchanged::`")
        return Violated(f"{path}::{function.qualname} changes the default of "
                        f"`{changed[0]}` with no `.. versionchanged::` directive giving "
                        f"the old and new values")


@rule(
    id="SCIKIT-LEARN-C138",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- states where constructor arguments belong, with
                          # no newness qualifier
    reads=("files",),  # spec §5
    heuristic=True,
)
class ConstructorArgumentsAreDocumentedUnderParameters:
    """Pre-condition: each estimator class the agent wrote or edited whose docstring has
    an Attributes section and whose `__init__` takes arguments.
    Pass condition: no constructor argument is documented as an attribute.

    Heuristic on the **pre-condition** (§6.3): "estimator" is approximated by the class
    defining `fit` or inheriting a scikit-learn base, since nothing in the source marks
    one. The pass condition is exact -- two named sections, and an argument name either
    appears as an entry of the wrong one or does not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            initialiser = info.method("__init__")
            if initialiser is None or not is_estimator(info) or not info.docstring:
                continue
            arguments = [p for p in parameters(initialiser) if p != "self"]
            section = _class_doc(info).section("Attributes")
            if not arguments or section is None:
                continue
            out.append(target(f"init-doc:{path}:{info.name}", path, info.span(),
                              (path, info, arguments, section),
                              f"{info.name}.__init__({', '.join(arguments)})"[:80]))
        return out

    def pass_condition(self, t: Target):
        path, info, arguments, section = t.payload
        documented = {name.strip() for entry in parameter_entries(section)
                      for name in entry.names.split(",")}
        misplaced = sorted(set(arguments) & documented)
        if misplaced:
            return Violated(f"{path}::{info.name} documents the constructor argument "
                            f"`{misplaced[0]}` under Attributes rather than Parameters")
        return Satisfied(f"{path}::{info.name} keeps its {len(arguments)} constructor "
                         f"argument(s) out of the Attributes section")


@rule(
    id="SCIKIT-LEARN-C153",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class LearnedAttributesAreDocumentedUnderAttributes:
    """Pre-condition: each class the agent wrote or edited that sets a public
    trailing-underscore attribute outside `__init__`.
    Pass condition: every one of them appears in the docstring's Attributes section.

    Heuristic on the **pre-condition** (§6.3): a learned attribute is recognised by the
    trailing underscore the project reserves for it, assigned in a method other than the
    constructor, so one set indirectly -- through `setattr` or a helper -- is not seen.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, _module, info in owned_classes(b, tests=False):
            learned = set()
            for name, node in info.methods.items():
                if name == "__init__":
                    continue
                learned |= {a for a in self_assignments(node)
                            if a.endswith("_") and not a.startswith("_")}
            if not learned or not info.docstring:
                continue
            out.append(target(f"attributes-doc:{path}:{info.name}", path, info.span(),
                              (path, info, sorted(learned)),
                              f"{info.name} learns {', '.join(sorted(learned))}"[:80]))
        return out

    def pass_condition(self, t: Target):
        path, info, learned = t.payload
        section = _class_doc(info).section("Attributes")
        if section is None:
            return Violated(f"{path}::{info.name} learns {', '.join(learned)} but its "
                            f"docstring has no Attributes section")
        documented = {name.strip() for entry in parameter_entries(section)
                      for name in entry.names.split(",")}
        missing = [name for name in learned if name not in documented]
        if missing:
            return Violated(f"{path}::{info.name} sets `{missing[0]}` at fit time but "
                            f"does not document it under Attributes")
        return Satisfied(f"{path}::{info.name} documents all {len(learned)} learned "
                         f"attribute(s)")


@rule(
    id="SCIKIT-LEARN-C186",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- "in all your docstrings", no newness qualifier
    reads=("files",),  # spec §5
    heuristic=True,
)
class DocstringsFollowTheNumpydocStandard:
    """Pre-condition: each docstring the agent wrote or edited.
    Pass condition: it carries no section marker belonging to a competing format.

    Heuristic on the **pass condition** (§6.2), and graded one-sidedly: a docstring with
    no sections at all is perfectly numpydoc-compatible, so the standard cannot be
    confirmed, while a reST field list or a Google `Args:` header is positive evidence of
    another format. Where a numpydoc section is present that is reported as satisfying,
    which is stronger evidence than mere absence.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"numpydoc:{path}:{doc.lineno}", path, doc.span(), (path, doc),
                       doc.text.strip().split("\n")[0][:80])
                for path, _module, doc in owned_docstrings(b, tests=False)]

    def pass_condition(self, t: Target):
        path, doc = t.payload
        if match := _SPHINX_FIELD.search(doc.text):
            return Violated(f"{path}:{doc.lineno} uses a reST field list "
                            f"(`{match.group(0).strip()}`), not the numpydoc standard")
        if match := _GOOGLE_SECTION.search(doc.text):
            return Violated(f"{path}:{doc.lineno} uses a Google-style section "
                            f"(`{match.group(1)}:`), not the numpydoc standard")
        if match := _NUMPY_SECTION.search(doc.text):
            return Satisfied(f"{path}:{doc.lineno} uses a numpydoc `{match.group(1)}` "
                             f"section")
        return Satisfied(f"{path}:{doc.lineno} carries no competing format marker")

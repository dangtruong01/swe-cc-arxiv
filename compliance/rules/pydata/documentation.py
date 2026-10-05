"""pydata (xarray): Documentation and docstrings -- 6 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Four of these are reStructuredText orthography, and all four grade one-sidedly: they detect
the *wrong* form rather than confirm the right one, because "written in the NumPy format"
and "marked up with the published section characters" are broader than anything a pattern
can confirm. Every one says so in its own docstring rather than leaving the reader to infer
it from the heuristic flag.

None of the docstring rules carries a newness qualifier, so all are `touched` per the spec
v1.3 §4.3 -- editing a docstring makes the agent answerable for its form.
"""

from __future__ import annotations

import re

from compliance.core import ownership as own
from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.pydata._common import (API_DOC, IMAGE_SUFFIXES, added_text,
                                             documentation_files, modules, python_files,
                                             target)

CATEGORY = "Documentation and docstrings"

#: numpydoc marks a section with an underline of dashes; the two competing formats mark
#: theirs with a reST field list or a Google-style header.
_NUMPY_SECTION = re.compile(r"^\s*(Parameters|Returns|Raises|Examples|See Also)\s*\n\s*-{3,}\s*$", re.M)
_SPHINX_FIELD = re.compile(r"^\s*:(param|type|returns|rtype|raises)\b", re.M)
_GOOGLE_SECTION = re.compile(r"^\s*(Args|Returns|Raises|Attributes):\s*$", re.M)

#: Executable code in a documentation page, in any of the three forms xarray's docs use.
_EXECUTABLE = re.compile(
    r"^\s*(>>>|```\s*python|```\{(code-cell|jupyter-execute)\}"
    r"|\.\. (jupyter-execute|ipython|code-block):: *python)", re.M)
_CODE_CELL = re.compile(r"```\{code-cell\}")

#: The published section-marker order: overlined `*` for chapters, then = - ^ "
_SECTION_ORDER = ("*", "=", "-", "^", '"')
_UNDERLINE = re.compile(r'^([*=\-^"~+#`])\1{2,}\s*$')

#: reST bold. `__text__` is an anonymous hyperlink, and HTML is not markup reST reads.
_WRONG_BOLD = re.compile(r"(?<!\w)__[^_\s][^_]*__(?!\w)|</?(b|strong)>", re.I)

_IMAGE_DIRECTIVE = re.compile(r"^\s*\.\.\s+(image|figure)::", re.M)


def _owned_docstrings(bundle: EvidenceBundle) -> list[tuple[str, pa.Docstring]]:
    """Docstrings the agent wrote or edited (spec §4.3)."""
    out = []
    for path, module in modules(bundle):
        for doc in module.docstrings:
            if own.owns_span(bundle, path, doc.span(), "touched"):
                out.append((path, doc))
    return out


@rule(
    id="PYDATA-C024",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier in the sentence
    reads=("files",),  # spec §5: the text is in the patch
    heuristic=True,
)
class DocstringsUseNumpyFormat:
    """Pre-condition: each docstring the agent wrote or edited.
    Pass condition: it carries no section header belonging to a competing format.

    Heuristic on the **pass condition** (§6.2), graded one-sidedly. A docstring with no
    sections at all is perfectly numpydoc-compatible, so confirming the format is not
    possible; a reST field list or a Google `Args:` header is positive evidence of the
    wrong one. Where a numpydoc section *is* present that is reported as satisfying,
    which is stronger evidence than mere absence.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"numpydoc:{path}:{doc.lineno}", path, doc.span(), (path, doc),
                       doc.text.strip().split("\n")[0][:80])
                for path, doc in _owned_docstrings(b) if doc.text.strip()]

    def pass_condition(self, t: Target):
        path, doc = t.payload
        if match := _SPHINX_FIELD.search(doc.text):
            return Violated(f"{path}:{doc.lineno} uses a reST field list "
                            f"(`{match.group(0).strip()}`), not the NumPy format")
        if match := _GOOGLE_SECTION.search(doc.text):
            return Violated(f"{path}:{doc.lineno} uses a Google-style section "
                            f"(`{match.group(1)}:`), not the NumPy format")
        if match := _NUMPY_SECTION.search(doc.text):
            return Satisfied(f"{path}:{doc.lineno} uses a numpydoc `{match.group(1)}` "
                             f"section")
        return Satisfied(f"{path}:{doc.lineno} carries no competing format marker")


@rule(
    id="PYDATA-C026",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- documentation pages already exist
    reads=("files",),  # spec §5
    heuristic=True,
)
class ExecutableDocsAreMystCodeCells:
    """Pre-condition: each documentation page the contribution changes that contains
    executable code.
    Pass condition: the page is MyST Markdown and the code sits in a `{code-cell}` block.

    Heuristic on the **pre-condition** (§6.3): *contains executable code* is recognised by
    the forms xarray's docs actually use -- doctest prompts, fenced Python, MyST
    `{code-cell}` and `{jupyter-execute}` blocks, and the `jupyter-execute`, `ipython` and
    `code-block:: python` directives -- and a page can carry runnable code in a shape none
    of those matches.

    **The `{code-cell}` form is in that list deliberately.** Leaving it out made the
    pre-condition select only pages written the wrong way, so the rule could record a
    violation and never a compliant page -- §7.1 inverted, and caught by the satisfying
    test rather than by review.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in documentation_files(b):
            text = b.files[path].head_text or added_text(b, path)
            if _EXECUTABLE.search(text or ""):
                out.append(target(f"code-cell:{path}", path, None, (path, text), path))
        return out

    def pass_condition(self, t: Target):
        path, text = t.payload
        if not path.endswith(".md"):
            return Violated(f"{path} carries executable code but is not a MyST Markdown "
                            f"page")
        if _CODE_CELL.search(text or ""):
            return Satisfied(f"{path} uses `{{code-cell}}` blocks")
        return Violated(f"{path} is Markdown but its executable code is not in a "
                        f"`{{code-cell}}` block")


@rule(
    id="PYDATA-C027",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the sentence is about public methods added
    reads=("files",),  # DEPARTURE from CheckTier=differential -- api.rst is in the patch
    heuristic=True,
)
class PublicApiListedInApiDoc:
    """Pre-condition: each public module-level function the agent added to the package.
    Pass condition: its name appears in the lines added to `doc/api.rst`.

    Heuristic on the **pre-condition** (§6.3): *public method* is approximated by a
    module-level function whose name does not begin with an underscore, which misses
    methods added to existing classes and over-fires on helpers that are public by accident
    of naming.

    The corpus files this `differential` and it needs no tool run -- `doc/api.rst` is in the
    diff. Recorded rather than corrected in the workbook, per the spec §5.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=False):
            for function in module.functions:
                if function.qualname != function.name or function.name.startswith("_"):
                    continue
                if own.owns_span(b, path, function.span(), "created"):
                    out.append(target(f"api:{path}:{function.name}", path,
                                      function.span(), (b, function.name),
                                      f"def {function.name}"))
        return out

    def pass_condition(self, t: Target):
        bundle, name = t.payload
        if API_DOC in bundle.files and name in added_text(bundle, API_DOC):
            return Satisfied(f"`{name}` is listed in {API_DOC}")
        return Violated(f"`{name}` is new and public but is not listed in {API_DOC}")


@rule(
    id="PYDATA-C030",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the file already existed
    reads=("files",),  # spec §5
    heuristic=True,
)
class SectionMarkersFollowTheScheme:
    """Pre-condition: each reStructuredText page the contribution changes that carries at
    least two section markers.
    Pass condition: the marker characters appear in the published order -- `*` for
    chapters, then `=`, `-`, `^`, `"`.

    Heuristic on the **pass condition** (§6.2). Nesting depth is not recoverable from a
    flat scan, so this checks the weaker property the scheme implies: the characters are
    drawn from the published set and appear for the first time in the published order. A
    page that skips a level in a way the guide would accept still passes, and one that
    nests unusually but consistently may not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in documentation_files(b):
            if not path.endswith(".rst"):
                continue
            text = b.files[path].head_text or ""
            markers = [m.group(1) for m in
                       (_UNDERLINE.match(line) for line in text.split("\n")) if m]
            if len(markers) >= 2:
                out.append(target(f"sections:{path}", path, None, (path, markers), path))
        return out

    def pass_condition(self, t: Target):
        path, markers = t.payload
        unknown = [c for c in markers if c not in _SECTION_ORDER]
        if unknown:
            return Violated(f"{path} marks a section with `{unknown[0]}`, outside the "
                            f"published set {' '.join(_SECTION_ORDER)}")
        seen: list[str] = []
        for char in markers:
            if char not in seen:
                seen.append(char)
        expected = [c for c in _SECTION_ORDER if c in seen]
        if seen != expected:
            return Violated(f"{path} introduces section markers in the order "
                            f"{' '.join(seen)}, not {' '.join(expected)}")
        return Satisfied(f"{path} uses {' '.join(seen)} in the published order")


@rule(
    id="PYDATA-C031",
    category=CATEGORY,
    ownership="touched",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class BoldIsDoubleAsterisk:
    """Pre-condition: each documentation page the contribution changes.
    Pass condition: the lines it wrote use no markup that means bold somewhere else --
    `__text__`, or an HTML bold tag.

    Heuristic on the **pass condition** (§6.2), graded one-sidedly. Confirming that every
    bold span uses `**` would need to know which spans were meant to be bold; what is
    decidable is the presence of the two forms an author reaches for by habit from
    Markdown or HTML. In reST `__text__` is an anonymous hyperlink, so this is a real
    defect rather than a style preference.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in documentation_files(b):
            written = added_text(b, path)
            if written.strip():
                out.append(target(f"bold:{path}", path, None, (path, written), path))
        return out

    def pass_condition(self, t: Target):
        path, written = t.payload
        if match := _WRONG_BOLD.search(written):
            return Violated(f"{path} uses `{match.group(0)[:30]}` where reST bold is "
                            f"`**text**`")
        return Satisfied(f"{path} carries no Markdown or HTML bold markup")


@rule(
    id="PYDATA-C033",
    category=CATEGORY,
    ownership="touched",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class ImagesUseTheImageDirective:
    """Pre-condition: each documentation page the contribution changes whose written lines
    name an image file.
    Pass condition: the page uses an `image::` or `figure::` directive.

    Heuristic on the **pre-condition** (§6.3): *includes an image file* is recognised by a
    filename with an image extension appearing in the written lines, which also matches a
    page that merely mentions one in prose. `figure::` is accepted alongside `image::`
    because it is the same directive family with a caption, and reporting it would be a
    false violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in documentation_files(b):
            written = added_text(b, path)
            if any(suffix in written for suffix in IMAGE_SUFFIXES):
                out.append(target(f"image:{path}", path, None, (path, written), path))
        return out

    def pass_condition(self, t: Target):
        path, written = t.payload
        if _IMAGE_DIRECTIVE.search(written):
            return Satisfied(f"{path} includes its image with a directive")
        return Violated(f"{path} names an image file without an `image::` or `figure::` "
                        f"directive")

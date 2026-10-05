"""scikit-learn: Specialized changes -- 8 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects
on the rule's ANTECEDENT, ``pass_condition`` grades.

Seven of the eight are Cython rules and the eighth is about the CI configuration. Cython
is not Python, so ``ast`` cannot read it and none of the shared extractors applies: the
predicates below read the ``.pyx``/``.pxd`` text through the small scanner in
``_common`` (``cython_defs``, ``cython_classes``, ``memoryview_names``). That is why
every Cython rule here declares ``heuristic=True`` on at least one layer -- a text
scanner recognises a construct, it does not parse one. Spec §7.4 would make this a shared
extractor once a second project legislates Cython; today it is one project's vocabulary
and stays in Layer C.

**C216 and C217 overlap and are narrowed apart** (§7.5). C217 is about where an OpenMP
routine is *imported from*; C216 is about whether a *call* to one is protected. A file
that cimports from ``sklearn.utils._openmp_helpers`` satisfies both, a file with an
``omp_`` call and no cimport at all is C216's finding only, and one that cimports from
the library directly is C217's.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.scikit_learn._common import (added_lines, ci_files, code_lines,
                                                   cython_classes, cython_defs,
                                                   cython_files, file_text,
                                                   memoryview_names, target)

CATEGORY = "Specialized changes"

#: The module that supplies protected OpenMP routines (C216, C217).
OPENMP_HELPERS = "sklearn.utils._openmp_helpers"

_OMP_CALL = re.compile(r"\bomp_[a-z_]+\s*\(")
_CIMPORT = re.compile(r"^\s*(from\s+(?P<module>[\w.]+)\s+)?cimport\s+(?P<names>.+)$")
_NOGIL_DEF = re.compile(r"\bnogil\b")
_WITH_NOGIL = re.compile(r"\bwith\s+nogil\b")
_PRANGE_NOGIL = re.compile(r"\bprange\s*\([^)]*\bnogil\s*=\s*True")
#: Cython's compile-time conditional, and the C preprocessor guard used in `.pxd` shims.
_BUILD_GUARD = re.compile(r"^\s*(IF\s+SKLEARN_OPENMP_PARALLELISM_ENABLED|#\s*if(n?def)?"
                          r"[^\n]*_OPENMP)", re.M)
_FSTRING = re.compile(r"\bf(['\"])")
#: The self-documenting expression Cython's parser rejects (C220).
_FSTRING_EQ = re.compile(r"\{\s*[\w.\[\]()]+\s*=\s*[:!}]")
_GLOBAL_SEED_VAR = re.compile(r"SKLEARN_TESTS_GLOBAL_RANDOM_SEED")


def _cython_sources(bundle: EvidenceBundle):
    """(path, text) for each Cython file the agent edited whose text is available."""
    for path in cython_files(bundle):
        text = file_text(bundle, path)
        if text.strip():
            yield path, text


def _split_params(params: str) -> list[str]:
    """Split a parameter list on top-level commas."""
    out, depth, current = [], 0, ""
    for char in params:
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        if char == "," and depth <= 0:
            out.append(current)
            current = ""
        else:
            current += char
    if current.strip():
        out.append(current)
    return [p.strip() for p in out if p.strip()]


def _is_typed(param: str) -> bool:
    """A Cython parameter is typed when something precedes its name, or it is annotated."""
    head = param.split("=", 1)[0].strip()
    if ":" in head:  # `x: int`, the Python annotation form Cython also accepts
        return True
    head = head.lstrip("*&")
    return len(head.split()) > 1 or "[" in head


@rule(
    id="SCIKIT-LEARN-C210",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier; a Cython file the agent
                          # edited is in scope
    reads=("files",),  # spec §5: the source is in the patch
    heuristic=True,
)
class MemoryviewsAreNotSliced:
    """Pre-condition: each Cython file the agent edited that declares a typed memoryview.
    Pass condition: no declared memoryview is subscripted with a slice.

    A prohibition, so the pre-condition selects the situation that invokes it -- Cython
    code that has memoryviews to slice -- and never the slices themselves (§7.1).
    Heuristic on **both layers** (§6.3, §6.2): declarations and slice subscripts are
    recognised textually, so a memoryview obtained from a function's return value is not
    tracked, and a slice of a NumPy array sharing a name with a memoryview is reported.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, text in _cython_sources(b):
            names = memoryview_names(text)
            if names:
                out.append(target(f"memoryview:{path}", path, None, (path, text, names),
                                  f"{len(names)} memoryview(s)"))
        return out

    def pass_condition(self, t: Target):
        path, text, names = t.payload
        declaration_lines = set(names.values())
        for lineno, line in code_lines(text):
            if lineno in declaration_lines:
                continue  # the declaration itself carries the `[::1]` shape
            for name in names:
                if re.search(rf"\b{re.escape(name)}\s*\[[^\]]*:[^\]]*\]", line):
                    return Violated(f"{path}:{lineno} slices the memoryview `{name}`: "
                                    f"{line.strip()[:70]}")
        return Satisfied(f"{path} uses {len(names)} memoryview(s) without slicing any")


@rule(
    id="SCIKIT-LEARN-C211",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- the sentence states a property of Cython classes
                          # and methods, with no newness qualifier
    reads=("files",),  # spec §5
    heuristic=True,
)
class FinalCythonClassesCarryFinal:
    """Pre-condition: each `cdef class` in a Cython file the agent edited that nothing in
    that file subclasses.
    Pass condition: it is decorated `@final`.

    Heuristic on the **pre-condition** (§6.3): *final* means nothing anywhere subclasses
    the type, and only the files in the contribution are visible, so finality is
    approximated by "not subclassed in the file that defines it". The pass condition is
    exact -- one named decorator, present or absent.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, text in _cython_sources(b):
            defined = cython_classes(text)
            subclassed = {base for info in defined for base in info.bases}
            for info in defined:
                if info.name in subclassed:
                    continue
                out.append(target(f"final:{path}:{info.name}", path,
                                  (info.lineno, info.lineno), (path, info),
                                  f"cdef class {info.name}"))
        return out

    def pass_condition(self, t: Target):
        path, info = t.payload
        if any(d.split(".")[-1] == "final" for d in info.decorators):
            return Satisfied(f"{path}:{info.lineno} `cdef class {info.name}` is @final")
        return Violated(f"{path}:{info.lineno} `cdef class {info.name}` is never "
                        f"subclassed but is not decorated @final")


@rule(
    id="SCIKIT-LEARN-C214",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class GilIsReleasedExplicitly:
    """Pre-condition: each Cython file the agent edited that declares a `nogil` function.
    Pass condition: the file releases the GIL explicitly, with `with nogil` or
    `prange(..., nogil=True)`.

    The antecedent is the declaration, which the page states does nothing by itself; the
    graded artefact is the explicit release. Heuristic on the **pre-condition** (§6.3),
    which recognises a `nogil` declaration textually, and on the **pass condition**,
    which asks the question per file rather than per declared function -- a file with two
    `nogil` functions and one `with nogil` block passes.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, text in _cython_sources(b):
            declared = [d for d in cython_defs(text) if _NOGIL_DEF.search(d.line)]
            if declared:
                out.append(target(f"nogil:{path}", path, None, (path, text, declared),
                                  f"{len(declared)} nogil declaration(s)"))
        return out

    def pass_condition(self, t: Target):
        path, text, declared = t.payload
        if match := _WITH_NOGIL.search(text):
            return Satisfied(f"{path} releases the GIL with `{match.group(0)}`")
        if _PRANGE_NOGIL.search(text):
            return Satisfied(f"{path} releases the GIL with `prange(..., nogil=True)`")
        return Violated(f"{path} declares {len(declared)} nogil function(s) "
                        f"(`{declared[0].name}`) but never releases the GIL with "
                        f"`with nogil` or `prange(nogil=True)`")


@rule(
    id="SCIKIT-LEARN-C216",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class DirectOpenMpCallsAreProtected:
    """Pre-condition: each Cython file the agent edited that calls an OpenMP routine.
    Pass condition: the file takes its routines from `sklearn.utils._openmp_helpers`, or
    guards them so the code still builds without OpenMP.

    Heuristic on **both layers** (§6.3, §6.2): an OpenMP call is recognised by the
    `omp_` prefix, and "protected" is accepted in either of the two forms the page shows
    -- the helper module, which supplies protected versions, or a build-time guard. A
    third way of protecting a call would read as a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, text in _cython_sources(b):
            calls = [(n, line) for n, line in code_lines(text) if _OMP_CALL.search(line)]
            if calls:
                out.append(target(f"openmp-guard:{path}", path, None, (path, text, calls),
                                  f"{len(calls)} direct OpenMP call(s)"))
        return out

    def pass_condition(self, t: Target):
        path, text, calls = t.payload
        if OPENMP_HELPERS in text:
            return Satisfied(f"{path} takes its OpenMP routines from {OPENMP_HELPERS}, "
                             f"which supplies protected versions")
        if _BUILD_GUARD.search(text):
            return Satisfied(f"{path} guards its OpenMP calls for builds without OpenMP")
        lineno, line = calls[0]
        return Violated(f"{path}:{lineno} calls OpenMP directly with neither the "
                        f"{OPENMP_HELPERS} module nor a build guard: {line.strip()[:60]}")


@rule(
    id="SCIKIT-LEARN-C217",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class OpenMpRoutinesAreCimportedFromTheHelpers:
    """Pre-condition: each `cimport` of an OpenMP routine in a Cython file the agent
    edited.
    Pass condition: it names `sklearn.utils._openmp_helpers` as the module.

    Not heuristic: the page names one module as the source and forbids the library, and a
    cimport statement names its module exactly. `prange` is deliberately not selected --
    the page exempts it, being already protected by Cython itself.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, text in _cython_sources(b):
            for lineno, line in code_lines(text):
                match = _CIMPORT.match(line)
                if not match:
                    continue
                names = match.group("names")
                module = match.group("module") or names.strip().split(",")[0].strip()
                if "omp_" not in names and "openmp" not in module:
                    continue
                out.append(target(f"omp-cimport:{path}:{lineno}", path, (lineno, lineno),
                                  (path, lineno, module, line.strip()),
                                  line.strip()[:80]))
        return out

    def pass_condition(self, t: Target):
        path, lineno, module, line = t.payload
        if module == OPENMP_HELPERS:
            return Satisfied(f"{path}:{lineno} cimports from {OPENMP_HELPERS}")
        return Violated(f"{path}:{lineno} cimports OpenMP routines from `{module}` "
                        f"rather than from {OPENMP_HELPERS}: {line[:60]}")


@rule(
    id="SCIKIT-LEARN-C218",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
    heuristic=True,
)
class CythonCodeDeclaresExplicitTypes:
    """Pre-condition: each function defined in a Cython file the agent edited that takes
    a parameter other than `self`.
    Pass condition: every one of those parameters carries a type.

    Heuristic on the **pass condition** (§6.2): a parameter is read as typed when
    something precedes its name -- a type token, a memoryview shape, or a Python
    annotation -- which is how Cython declares one; a `cdef` block declaring types on
    separate lines inside the body is not seen, and neither is a return type. The
    sentence covers all explicit typing, and this checks the signature.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, text in _cython_sources(b):
            for definition in cython_defs(text):
                params = [p for p in _split_params(definition.params)
                          if p not in ("self", "cls") and not p.startswith(("*", "**"))]
                if params:
                    out.append(target(f"cy-types:{path}:{definition.lineno}", path,
                                      (definition.lineno, definition.lineno),
                                      (path, definition, params),
                                      definition.line.strip()[:80]))
        return out

    def pass_condition(self, t: Target):
        path, definition, params = t.payload
        untyped = [p for p in params if not _is_typed(p)]
        if untyped:
            return Violated(f"{path}:{definition.lineno} `{definition.name}` declares no "
                            f"type for {', '.join(untyped[:3])}")
        return Satisfied(f"{path}:{definition.lineno} `{definition.name}` types all "
                         f"{len(params)} parameter(s)")


@rule(
    id="SCIKIT-LEARN-C220",
    category=CATEGORY,
    ownership="touched",  # spec §4.3
    reads=("files",),  # spec §5
)
class NoSelfDocumentingFstringsInCython:
    """Pre-condition: each Cython file the agent edited that contains an f-string.
    Pass condition: none of them uses the `{var=}` form.

    A prohibition, so the antecedent is *using f-strings at all* and the graded question
    is whether the rejected form appears (§7.1). Not heuristic: the rule names the
    construct exactly, and Cython's parser -- not a matter of taste -- is what rejects it.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, text in _cython_sources(b):
            lines = [(n, line) for n, line in code_lines(text) if _FSTRING.search(line)]
            if lines:
                out.append(target(f"fstring:{path}", path, None, (path, lines),
                                  f"{len(lines)} f-string line(s)"))
        return out

    def pass_condition(self, t: Target):
        path, lines = t.payload
        for lineno, line in lines:
            if _FSTRING_EQ.search(line):
                return Violated(f"{path}:{lineno} uses a `{{var=}}` f-string, which "
                                f"Cython cannot parse: {line.strip()[:60]}")
        return Satisfied(f"{len(lines)} f-string line(s) in {path} use no `{{var=}}` "
                         f"expression")


@rule(
    id="SCIKIT-LEARN-C235",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- the CI configuration already existed
    reads=("files",),  # spec §5
    heuristic=True,
)
class PullRequestCiDoesNotSetTheGlobalSeed:
    """Pre-condition: each pull-request CI configuration file the contribution edits.
    Pass condition: none of the lines the agent wrote sets
    `SKLEARN_TESTS_GLOBAL_RANDOM_SEED`.

    A prohibition, so the pre-condition selects *editing the CI configuration* -- the
    permitted act -- rather than the setting the rule forbids (§7.1); the corpus Notes
    state the trigger the same way. Heuristic on the **pre-condition** (§6.3): which
    files are "the pull-request CI configuration" is approximated by the workflow, build
    tools and pipeline paths in ``_common.CI_PATHS``, since nothing in the patch says
    which configuration a given file belongs to.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in ci_files(b):
            written = added_lines(b, path)
            if written:
                out.append(target(f"ci-seed:{path}", path, None, (path, written),
                                  f"{len(written)} written line(s) in {path}"))
        return out

    def pass_condition(self, t: Target):
        path, written = t.payload
        for lineno, line in written:
            if _GLOBAL_SEED_VAR.search(line):
                return Violated(f"{path}:{lineno} sets SKLEARN_TESTS_GLOBAL_RANDOM_SEED "
                                f"in the pull-request CI: {line.strip()[:60]}")
        return Satisfied(f"{path} leaves SKLEARN_TESTS_GLOBAL_RANDOM_SEED unset")

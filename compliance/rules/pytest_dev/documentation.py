"""pytest-dev: Documentation and docstrings -- 6 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Four of the six are docstring rules taken from the worked example the contributing page
prints, so their pass conditions are orthographic and read straight off the text. The other
two (C044, C057) hang off the project's own changelog **type** -- `breaking` and `feature`
-- which is a declaration the contribution makes about itself rather than a category this
pack has to infer. That is why their pre-conditions are exact where sphinx-doc's equivalent
had to approximate "a new feature".
"""

from __future__ import annotations

import re

from compliance.core import ownership as own
from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import docstrings as ds
from compliance.extractors import python_ast as pa
from compliance.rules.pytest_dev._common import (DOC_ROOT, changed_under,
                                                 changelog_entries, entry_type,
                                                 has_breaking_entry, python_files, ran,
                                                 target)

CATEGORY = "Documentation and docstrings"

DEPRECATIONS_DOC = "doc/en/deprecations.rst"

_TOX_DOCS = re.compile(r"\btox\b[^\n]*-e\s*[^\s]*\bdocs\b")
#: Section headers of the two formats pytest does not use. Their presence is positive
#: evidence of a competing format; their absence is not proof of Sphinx style.
_NUMPY_SECTION = re.compile(r"^\s*(Parameters|Returns|Raises)\s*\n\s*-{3,}\s*$", re.M)
_GOOGLE_SECTION = re.compile(r"^\s*(Args|Returns|Raises|Attributes):\s*$", re.M)


def _owned_docstrings(bundle: EvidenceBundle) -> list[tuple[str, pa.Docstring]]:
    """Docstrings the agent wrote or edited, in files it submitted.

    ``touched`` rather than ``created`` per the spec §4.3: none of the three docstring
    rules carries a newness qualifier, and scoping them to added docstrings only would
    exempt every docstring the agent rewrote.
    """
    out = []
    for path in python_files(bundle):
        text = bundle.files[path].head_text
        if text is None:
            continue
        module = pa.parse_module(text, path)
        if not module.ok:
            continue
        for doc in module.docstrings:
            if own.owns_span(bundle, path, doc.span(), "touched"):
                out.append((path, doc))
    return out


def _doc_targets(bundle: EvidenceBundle, prefix: str) -> list[Target]:
    return [target(f"{prefix}:{path}:{doc.lineno}", path, doc.span(), (path, doc),
                   doc.text.strip().split("\n")[0][:80])
            for path, doc in _owned_docstrings(bundle)]


@rule(
    id="PYTEST-DEV-C003",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- the rule is about documentation edited
    reads=("files", "commands"),  # spec §5: CheckTier=trajectory, building is an act
)
class DocumentationBuiltWithTox:
    """Pre-condition: the contribution changes a documentation source under `doc/en/`.
    Pass condition: a tox invocation naming the `docs` environment appears in the command
    log.

    Fires on the edit, not on the build (§7.1). The note names one command and offers no
    alternative build path, so the pass condition is that command rather than any
    `sphinx-build` invocation the agent might have improvised.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        touched = changed_under(b, DOC_ROOT)
        if not touched:
            return []
        return [target(f"docs-build:{b.instance_id}", None, None, b,
                       f"{len(touched)} documentation source(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if runs := ran(bundle, _TOX_DOCS):
            return Satisfied(f"documentation built: {runs[0].command.strip()[:80]}")
        return Violated("documentation changed but `tox -e docs` never ran")


@rule(
    id="PYTEST-DEV-C004",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- the sentence carries no newness qualifier
    reads=("files",),  # spec §5: the text is in the patch
    heuristic=True,
)
class DocstringsUseSphinxFormat:
    """Pre-condition: each docstring the agent added.
    Pass condition: it carries no section header belonging to a competing docstring format.

    Heuristic on the **pass condition** (§6.2). "In the Sphinx format" is broader than
    anything a pattern can confirm: a docstring with no field list at all is perfectly
    Sphinx-formatted. So this is graded one-sidedly on its complement -- a numpydoc
    underline or a Google `Args:` header is positive evidence of the wrong format, and
    their absence is evidence of nothing in particular.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _doc_targets(b, "sphinx-format")

    def pass_condition(self, t: Target):
        path, doc = t.payload
        if match := _NUMPY_SECTION.search(doc.text):
            return Violated(f"{path}:{doc.lineno} uses a numpydoc section "
                            f"(`{match.group(1)}` with an underline), not the Sphinx format")
        if match := _GOOGLE_SECTION.search(doc.text):
            return Violated(f"{path}:{doc.lineno} uses a Google-style section "
                            f"(`{match.group(1)}:`), not the Sphinx format")
        return Satisfied(f"{path}:{doc.lineno} carries no competing format marker")


@rule(
    id="PYTEST-DEV-C005",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- the sentence carries no newness qualifier
    reads=("files",),  # spec §5
    heuristic=True,
)
class DocstringSentencesArePunctuated:
    """Pre-condition: each docstring the agent added that carries text.
    Pass condition: its subject line starts with a capital letter and ends with a period.

    Heuristic on the **pass condition** (§6.2): the rule says *sentences*, and the subject
    line is used as the unit because splitting docstring prose into sentences is a proxy
    that misfires on abbreviations, code spans and reST roles. Both halves the guide names
    -- an initial capital and a terminating period -- are checked exactly on that line.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [t for t in _doc_targets(b, "docstring-sentence")
                if t.payload[1].text.strip()]

    def pass_condition(self, t: Target):
        path, doc = t.payload
        subject = doc.text.strip().split("\n")[0].strip()
        if not subject:
            return Satisfied(f"{path}:{doc.lineno} has no subject line to grade")
        if not subject[0].isupper():
            return Violated(f"{path}:{doc.lineno} subject line does not start with a "
                            f"capital: {subject[:60]}")
        if not ds.ends_with_terminator(subject):
            return Violated(f"{path}:{doc.lineno} subject line does not end with a "
                            f"period: {subject[:60]}")
        return Satisfied(f"{path}:{doc.lineno} subject line is a proper sentence")


@rule(
    id="PYTEST-DEV-C008",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- the sentence carries no newness qualifier
    reads=("files",),  # spec §5: the layout is in the patch
)
class DocstringDetailIsASeparateParagraph:
    """Pre-condition: each docstring the agent added that carries detail beyond its subject
    line.
    Pass condition: a blank line separates the subject line from that detail.

    Not heuristic: the worked example fixes one exact layout, and a blank second line is
    read straight off the text. A single-line docstring has no detail to separate and finds
    no target rather than passing vacuously.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for t in _doc_targets(b, "docstring-blank"):
            lines = t.payload[1].text.rstrip().split("\n")
            if len([line for line in lines[1:] if line.strip()]) > 0:
                out.append(t)
        return out

    def pass_condition(self, t: Target):
        path, doc = t.payload
        lines = doc.text.rstrip().split("\n")
        if lines[1].strip() == "":
            return Satisfied(f"{path}:{doc.lineno} separates subject line from detail")
        return Violated(f"{path}:{doc.lineno} runs detail straight on from the subject "
                        f"line: {lines[1].strip()[:60]}")


@rule(
    id="PYTEST-DEV-C044",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- deprecations.rst is an existing file
    reads=("files",),  # spec §5: both the declaration and the file are in the patch
)
class BreakingChangeDocumentedInDeprecations:
    """Pre-condition: the contribution adds a `breaking` changelog fragment.
    Pass condition: `doc/en/deprecations.rst` is among the files it changes.

    Not heuristic on either layer. The antecedent is the project's own declaration -- a
    fragment typed `breaking` -- rather than an inference about what the patch does, and
    the acceptance-list bullet names one tracked file the diff either touches or does not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        breaking = has_breaking_entry(b)
        if not breaking:
            return []
        return [target(f"breaking-doc:{b.instance_id}", None, None, b,
                       f"breaking change declared in {breaking[0]}")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if DEPRECATIONS_DOC in bundle.files:
            return Satisfied(f"{DEPRECATIONS_DOC} documents the break")
        return Violated(f"a breaking change was declared but {DEPRECATIONS_DOC} is "
                        f"untouched")


@rule(
    id="PYTEST-DEV-C057",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- documentation sources already exist
    reads=("files",),  # spec §5: both halves are in the patch
    heuristic=True,
)
class NewFeatureShipsWithDocumentation:
    """Pre-condition: the contribution adds a `feature` changelog fragment.
    Pass condition: it also changes a documentation source under `doc/en/`.

    Heuristic on the **pass condition** (§6.2): a changed documentation file is evidence
    that the feature was documented, not proof that it documents *this* feature.

    The pre-condition, by contrast, is exact, and deliberately so. The equivalent
    sphinx-doc rule had to approximate "a new feature" from new public definitions; here
    the contribution declares it by typing its own changelog fragment `feature`, which is
    the project's own category rather than this pack's inference.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        features = [p for p in changelog_entries(b, created_only=False)
                    if entry_type(p) == "feature"]
        if not features:
            return []
        return [target(f"feature-doc:{b.instance_id}", None, None, b,
                       f"feature declared in {features[0]}")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if docs := changed_under(bundle, DOC_ROOT):
            return Satisfied(f"documentation changed alongside the feature: {docs[0]}")
        return Violated(f"a feature was declared but nothing under {DOC_ROOT} changed")

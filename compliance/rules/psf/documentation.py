"""psf (requests): Documentation and docstrings -- 2 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

**Repository metadata is not documentation** (spec §7.5). Read literally, "place
documentation changes under `docs/`" prohibits editing `HISTORY.md`, `README.md` or
`AUTHORS.rst` -- files written in the same markup, kept at the top level on purpose, and
which Requests' own release process requires changing. The corpus sentence comes from the
*Documentation Contributions* section, whose subject is the prose documentation Sphinx
builds, so ``_common.is_meta_path`` excludes the top level and `.github/` from the
selection. ``test_c013_finds_no_target_for_the_changelog`` pins that exclusion.

Both rules are ``touched``: neither sentence carries a newness qualifier (§4.3), and
scoping them to files the agent created would exempt every documentation page it rewrote.
"""

from __future__ import annotations

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import rst
from compliance.rules.psf._common import (DOC_ROOT, DOC_SUFFIXES, RST_SUFFIXES,
                                          added_lines, changed_under, documentation_files,
                                          target)

CATEGORY = "Documentation and docstrings"


@rule(
    id="PSF-C013",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier; an edited page is in scope
    reads=("files",),  # spec §5: the path is the whole question; CheckTier=static agrees
    heuristic=True,
)
class DocumentationChangesLiveUnderDocs:
    """Pre-condition: each documentation source the contribution changes, wherever it sits.
    Pass condition: its path is under `docs/`.

    Heuristic on the **pre-condition** (§6.3): the project publishes no list of what counts
    as documentation, so this approximates it as reStructuredText and Markdown minus the
    repository metadata named in the module docstring. That will misfile a documentation
    page someone chose to keep at the top level, and will miss one written in a markup
    this does not recognise.

    The selection is deliberately *not* scoped to `docs/`. Selecting only the files already
    in the right place is §7.1 inverted -- it could never record a violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"docpath:{path}", path, None, path, path)
                for path in documentation_files(b)]

    def pass_condition(self, t: Target):
        path: str = t.payload
        if path.startswith(DOC_ROOT):
            return Satisfied(f"{path} is under {DOC_ROOT}")
        return Violated(f"documentation changed in {path}, outside {DOC_ROOT}")


@rule(
    id="PSF-C014",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier
    reads=("files",),  # spec §5: the markup is in the patch; CheckTier=static agrees
    heuristic=True,
)
class DocumentationIsReStructuredText:
    """Pre-condition: each documentation file the contribution changes under `docs/`.
    Pass condition: it is a reStructuredText file and the lines the agent wrote carry no
    construct that belongs to Markdown rather than reST.

    The first half is exact -- the extension either is `.rst` or it is not, and the Sphinx
    toolchain the sentence names would not build anything else. Heuristic on the **pass
    condition** (§6.2) because of the second half: a `.rst` file whose new prose is written
    in Markdown satisfies the extension test and defeats the rule, so Markdown-only
    constructs are treated as positive evidence of the wrong markup. Their absence proves
    nothing, which is the direction this errs in.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"docmarkup:{path}", path, None, (path, added_lines(b, path)), path)
                for path in changed_under(b, DOC_ROOT, DOC_SUFFIXES)]

    def pass_condition(self, t: Target):
        path, written = t.payload
        if not path.endswith(RST_SUFFIXES):
            return Violated(f"{path} is not reStructuredText; Sphinx builds `.rst`, and "
                            f"nothing in the guide sanctions another markup")
        if found := rst.markdown_constructs(list(written)):
            lineno, what = found[0]
            return Violated(f"{path}:{lineno} is written with a {what}, which is Markdown "
                            f"and not reStructuredText")
        return Satisfied(f"{path} is reStructuredText and its new lines carry no Markdown "
                         f"construct")

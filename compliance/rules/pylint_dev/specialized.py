"""pylint-dev: Specialized changes -- 1 rule.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

The one rule is the extension arm of pylint's three enforced placement exceptions; its two
siblings, the initial-letter directory (C053) and the regression directories (C055), sit in
`tests.py`. All three would otherwise claim the same file, so C053 excludes anything under
`functional/ext/` with a comment naming this rule, and a test here pins that the exclusion
holds (spec §7.5).
"""

from __future__ import annotations

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.pylint_dev._common import (EXTENSIONS_ROOT, EXT_FUNCTIONAL,
                                                 functional_relpath, functional_tests,
                                                 stem_of, target)

CATEGORY = "Specialized changes"


def extension_names(bundle: EvidenceBundle) -> list[str]:
    """The extension modules the contribution touches, by module name."""
    return sorted({stem_of(p) for p in bundle.files
                   if p.startswith(EXTENSIONS_ROOT) and p.endswith(".py")
                   and not p.endswith("__init__.py")})


@rule(
    id="PYLINT-DEV-C054",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- where a file lives is fixed when it is added; a
                          # functional test that already sat somewhere was not placed by
                          # the agent, so `touched` would judge someone else's choice
    reads=("files",),  # spec §5: both the extension module and the test are in the patch
    heuristic=True,
)
class ExtensionFunctionalTestUnderItsOwnDirectory:
    """Pre-condition: each functional test file the agent added in a contribution that
    also changes a module under `pylint/extensions/`.
    Pass condition: it sits under `tests/functional/ext/<extension name>/`.

    Heuristic on the **pre-condition** (§6.3). *The functional test for an extension
    checker* is not observable directly: what the patch shows is that an extension module
    changed and that functional tests were added, and the association between the two is
    inferred. A contribution that changed both an extension and a core checker would have
    its core tests selected here too, which over-fires; the alternative -- requiring the
    test's name to match the extension's -- would beg C052's question.

    Corpus: Put the functional test for an extension checker under the extension's own
    directory.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        names = extension_names(b)
        if not names:
            return []
        return [target(f"ext-test:{path}", path, None, (path, names), path)
                for path in functional_tests(b, mode="created")]

    def pass_condition(self, t: Target):
        path, names = t.payload
        relative = functional_relpath(path)
        if not relative.startswith(EXT_FUNCTIONAL):
            return Violated(f"{path} is a functional test for an extension "
                            f"({', '.join(names)}) but does not sit under "
                            f"functional/{EXT_FUNCTIONAL}")
        directory = relative[len(EXT_FUNCTIONAL):].split("/")[0]
        if directory in names:
            return Satisfied(f"{path} sits under the `{directory}` extension's own "
                             f"directory")
        return Violated(f"{path} sits under functional/{EXT_FUNCTIONAL}{directory}/, "
                        f"which is not one of the extensions the change touches "
                        f"({', '.join(names)})")

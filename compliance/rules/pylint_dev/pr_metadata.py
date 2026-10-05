"""pylint-dev: PR and release metadata -- 2 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

**DEPARTURE from the category prior on ``reads``.** The prior for this category is
``("pr_text",)``. Neither rule here is about PR prose: a towncrier fragment is a file, it
lands in the diff, and the `check-newsfragments` pre-commit hook reads it off the tree.
`("files",)` per the spec §5, whose worked example is this exact mistake.

The two split the way the spec §7.1 asks. C006 is about a fragment *existing*, so its
target is the contribution -- selecting the fragment would make the rule unable to record
the one thing it exists to catch. C007 is about a fragment's *type*, so its target is the
fragment, and a contribution that adds none finds no target.
"""

from __future__ import annotations

from compliance.core import ownership as own
from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.pylint_dev._common import (FRAGMENT_NAME, FRAGMENT_TYPES,
                                                 FRAGMENTS_ROOT, PACKAGE, changed_under,
                                                 python_files, target)

CATEGORY = "PR and release metadata"


def _fragments(bundle: EvidenceBundle, *, mode: str = "touched") -> list[str]:
    """Fragments the contribution carries, excluding towncrier's own `_template.rst`,
    which the project's pre-commit hook excludes by the same rule."""
    return [p for p in changed_under(bundle, FRAGMENTS_ROOT)
            if not p[len(FRAGMENTS_ROOT):].startswith("_")
            and own.owns_file(bundle, p, mode)]


@rule(
    id="PYLINT-DEV-C006",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- a whole-contribution rule: the antecedent is the
                          # change, even though the fragment itself is created
    reads=("files",),  # spec §5, and see the module docstring: a fragment is a file
    heuristic=True,
)
class NewsFragmentForTheChange:
    """Pre-condition: the contribution changes Python source under `pylint/`, which is
    the complement of the trivial change the guide's `skipnews` label exempts.
    Pass condition: it adds a file under `doc/whatsnew/fragments/` whose name begins with
    an issue number.

    Heuristic on **both layers** (§6.3, §6.2). The sentence begins *Otherwise*, and what
    it is otherwise to is a maintainer's judgement that a change is trivial; nothing in
    the patch settles that, so the complement is used and a documentation-only or
    test-only contribution finds no target rather than being graded. The pass condition
    reads *named after the issue number* as *the name starts with a number*: which issue
    a task corresponds to is a fact about the benchmark, not about the contribution, so
    the digits cannot be checked against anything.

    Corpus: Create a towncrier news fragment named after the issue number for the change.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        source = [p for p in python_files(b) if p.startswith(PACKAGE)]
        if not source:
            return []
        return [target(f"newsfragment:{b.instance_id}", None, None, b,
                       f"{len(source)} file(s) changed under {PACKAGE}")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        fragments = _fragments(bundle)
        if not fragments:
            return Violated(f"a change under {PACKAGE} with no news fragment under "
                            f"{FRAGMENTS_ROOT}")
        for path in fragments:
            if FRAGMENT_NAME.match(path[len(FRAGMENTS_ROOT):]):
                return Satisfied(f"news fragment {path} is named for an issue number")
        return Violated(f"{fragments[0]} is not named `<issue number>.<type>`")


@rule(
    id="PYLINT-DEV-C007",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the fragment did not exist before the run
    reads=("files",),  # spec §5, and see the module docstring
)
class NewsFragmentTypeFromTheDeclaredList:
    """Pre-condition: each news fragment the agent added whose name parses as
    `<issue number>.<type>`.
    Pass condition: its type is one of the twelve `towncrier.toml` declares.

    Not heuristic: the list is one the project publishes in its own configuration, and
    membership of a closed list is exact (§6.2). A fragment whose name does not parse at
    all is C006's finding, not this rule's -- selecting it here would report the same
    defect twice and depress both rates.

    Corpus: Give the news fragment one of the fragment types declared in towncrier.toml.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in _fragments(b, mode="created"):
            match = FRAGMENT_NAME.match(path[len(FRAGMENTS_ROOT):])
            if match:
                out.append(target(f"fragment-type:{path}", path, None,
                                  match.group("type"), path))
        return out

    def pass_condition(self, t: Target):
        kind = t.payload
        if kind in FRAGMENT_TYPES:
            return Satisfied(f"`{kind}` is one of the twelve types towncrier.toml declares")
        return Violated(f"`{kind}` is not a type towncrier.toml declares "
                        f"({', '.join(FRAGMENT_TYPES)})")

"""astropy: PR and release metadata -- 5 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

**Corpus mismatch, recorded here rather than corrected (§0, §5).** The category prior puts
``reads=("pr_text",)`` on all five of these, and all five are wrong about it: astropy's
changelog is not a section of the pull request body, it is a file added under
``docs/changes/``. Every rule in this module therefore declares ``("files",)``. This is the
worked example in §5 -- the category tells you which module, only the sentence tells you
what the predicate reads.

**One antecedent, four gradings.** C062, C063, C237 and C240 all fire on a changelog
fragment the agent wrote and disagree only about what they then look at: its name, its
markup, its prose, its directory. C061 is the outlier -- it fires on the *change*, because
its subject is the fragment's absence.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import rst
from compliance.rules.astropy._common import (CHANGES_DIR, FRAGMENT_NAME, FRAGMENT_TYPES,
                                              added_text, fragment_files, is_doc_path,
                                              is_test_path, target)

CATEGORY = "PR and release metadata"

_ROLE = re.compile(r":[a-zA-Z:+-]+:`[^`]*`")
#: A fragment is one short paragraph of reST; sentences are what C237 is about.
_TERMINATOR = ("." , "!", "?")


def _is_library_change(bundle: EvidenceBundle) -> list[str]:
    """Changed paths that are neither documentation nor tests.

    The observable face of *a change that needs a changelog entry*: CONTRIBUTING exempts
    "minor documentation or test updates", so a contribution consisting only of those does
    not invoke C061.
    """
    return [p for p in sorted(bundle.files)
            if not is_doc_path(p) and not is_test_path(p)
            and not p.startswith(CHANGES_DIR)]


def _fragment_targets(bundle: EvidenceBundle, prefix: str, *, mode: str = "touched"):
    return [target(f"{prefix}:{path}", path, None, path, path)
            for path in fragment_files(bundle, mode=mode)]


@rule(
    id="ASTROPY-C061",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- one target for the whole contribution
    reads=("files",),  # spec §5: the fragment is a file in the patch, not PR prose
    heuristic=True,
)
class ChangelogFragmentAdded:
    """Pre-condition: the contribution changes something that is neither documentation nor
    a test, which is what a change needing a changelog entry looks like.
    Pass condition: it adds a file under ``docs/changes/``.

    Heuristic on the **pre-condition** (§6.3). CONTRIBUTING exempts "minor documentation or
    test updates" and "fixes to bugs introduced in the developer version". The first
    exemption is decidable from the patch and is applied; the second is a fact about when
    the bug was introduced, which nothing in the bundle carries, so a fix to an unreleased
    regression is selected here and should not be.

    Firing on the fragment instead of on the change would be §7.1 inverted: a contribution
    that adds no fragment would find no target and be recorded as compliant.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        changed = _is_library_change(b)
        if not changed:
            return []
        return [target(f"changelog:{b.instance_id}", None, None, b,
                       f"{len(changed)} non-documentation file(s) changed, e.g. {changed[0]}")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        added = fragment_files(bundle, mode="created")
        if added:
            return Satisfied(f"changelog fragment added: {added[0]}")
        if touched := fragment_files(bundle):
            return Satisfied(f"changelog fragment written: {touched[0]}")
        return Violated("the contribution changes code and adds no changelog fragment "
                        "under docs/changes/")


@rule(
    id="ASTROPY-C062",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- naming is a decision made when the file is added
    reads=("files",),  # spec §5
)
class ChangelogFragmentIsNamedCorrectly:
    """Pre-condition: each changelog fragment the agent added under ``docs/changes/``.
    Pass condition: its file name is ``<PR number>.<feature|api|bugfix|perf|other>.rst``.

    Not heuristic: the corpus sentence enumerates the five types and the pre-commit
    ``changelogs-rst`` hook encodes the same pattern, so there is exactly one right shape
    and it is compared against exactly. Scoped ``created`` because naming a file is a
    decision taken when it is brought into existence; a fragment that was already in the
    tree is not the agent's naming.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _fragment_targets(b, "fragment-name", mode="created")

    def pass_condition(self, t: Target):
        path = t.payload
        name = path.rsplit("/", 1)[-1]
        if FRAGMENT_NAME.match(name):
            return Satisfied(f"{name} is <PR number>.<type>.rst")
        return Violated(f"{name} is not <PR number>.<type>.rst with <type> one of "
                        f"{', '.join(FRAGMENT_TYPES)}")


@rule(
    id="ASTROPY-C063",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- the sentence carries no newness qualifier
    reads=("files",),  # spec §5
    heuristic=True,
)
class NoSingleBackticksInChangelogFragments:
    """Pre-condition: each changelog fragment the agent wrote or edited.
    Pass condition: the text it added carries no single-backtick span.

    Heuristic on the **pass condition** (§6.2): the sentence prohibits single backticks
    used *as API reference links*, and a single-backtick span is a proxy for that intent --
    reST's default role would render one as a reference, but a fragment could in principle
    use it for something else. Explicit roles are stripped before the search, because
    ``:class:`~astropy.table.Table``` is the sanctioned form and matching its backticks
    would report the correct spelling as the violation.

    Selecting fragments rather than fragments-containing-backticks is what lets a
    well-written fragment record a pass (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"backticks:{path}", path, None, (path, added_text(b, path)), path)
                for path in fragment_files(b)]

    def pass_condition(self, t: Target):
        path, text = t.payload
        spans = rst.single_backtick_spans(_ROLE.sub(" ", text))
        if spans:
            return Violated(f"{path} makes an API reference with single backticks: "
                            f"`{spans[0]}`")
        return Satisfied(f"{path} uses no single-backtick spans")


@rule(
    id="ASTROPY-C237",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier; editing a fragment is writing it
    reads=("files",),  # spec §5
    heuristic=True,
)
class ChangelogFragmentsAreFullSentences:
    """Pre-condition: each changelog fragment the agent wrote or edited that has text.
    Pass condition: every paragraph in the text it added opens with a capital letter and
    closes with a terminator.

    Heuristic on the **pass condition** (§6.2): case and final punctuation stand in for
    "full sentences with correct case and punctuation", which is a property of the grammar
    and not of the first and last character. A paragraph opening with an inline literal --
    ```Quantity`` now supports ...`` -- is accepted rather than judged, because its case is
    fixed by the code name and not by the writer.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in fragment_files(b):
            text = added_text(b, path).strip()
            if text:
                out.append(target(f"sentences:{path}", path, None, (path, text), text[:80]))
        return out

    def pass_condition(self, t: Target):
        path, text = t.payload
        for paragraph in [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]:
            flat = " ".join(paragraph.split())
            if flat[0].isalpha() and flat[0].islower():
                return Violated(f"{path}: paragraph opens in lower case: {flat[:60]!r}")
            if not flat.endswith(_TERMINATOR):
                return Violated(f"{path}: paragraph does not end in a full stop: "
                                f"{flat[-60:]!r}")
        return Satisfied(f"{path} reads as full sentences")


@rule(
    id="ASTROPY-C240",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- where a file goes is decided when it is added
    reads=("files",),  # spec §5
)
class OtherFragmentsLiveInTheRootDirectory:
    """Pre-condition: each ``other``-type changelog fragment the agent added.
    Pass condition: it sits directly in ``docs/changes/`` and not in a sub-directory.

    Not heuristic: the type is in the file name and the directory is in the path, so both
    halves are read off the patch exactly. The pre-condition selects on the type, which is
    the situation the prohibition speaks to -- a fragment of any other type is simply not
    what the sentence is about, and finds no target here.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in fragment_files(b, mode="created"):
            name = path.rsplit("/", 1)[-1]
            match = FRAGMENT_NAME.match(name)
            if match and match.group(2) == "other":
                out.append(target(f"other-fragment:{path}", path, None, path, path))
        return out

    def pass_condition(self, t: Target):
        path = t.payload
        remainder = path[len(CHANGES_DIR):]
        if "/" in remainder:
            return Violated(f"{path} is an `other` fragment in the sub-directory "
                            f"{remainder.rsplit('/', 1)[0]}/, which is not allowed")
        return Satisfied(f"{path} sits in the root {CHANGES_DIR} directory")

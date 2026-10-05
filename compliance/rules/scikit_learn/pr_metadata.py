"""scikit-learn: PR and release metadata -- 6 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects
on the rule's ANTECEDENT, ``pass_condition`` grades.

Five of the six are about one artefact: the towncrier news fragment under
``doc/whats_new/upcoming_changes/``. The category's ``reads`` prior is ``pr_text``, and
it is wrong for all five -- a fragment is a **file in the patch**, so they read ``files``
(spec §5's worked example, in this pack's own words). Only C042, which grades the pull
request's title, goes anywhere near ``pr_text``.

The five split so that one defect is reported once (§7.5): C048 asks whether a fragment
exists at all, and C268-C271 each take *a fragment was added* as their antecedent and
grade one property of it. A contribution with no fragment therefore finds no target in
those four, and its absence is C048's finding alone.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.scikit_learn._common import (CHANGELOG_DIR, FRAGMENT_TOPIC_FOLDERS,
                                                   FRAGMENT_TYPES, PACKAGE, added_text,
                                                   changelog_fragments, cython_files,
                                                   source_files, target)

CATEGORY = "PR and release metadata"

#: `Fix #1234` and nothing else -- the title the guide names as *not* a good one.
_BARE_FIX = re.compile(r"^\s*(\[?[A-Z]{3,4}\]?\s+)?(fix(es|ed)?|close[sd]?|resolve[sd]?)"
                       r"\s*[:#-]?\s*(#|gh-)\d+\s*\.?\s*$", re.I)

#: `<PULL REQUEST>.<TYPE>.rst`, the shape towncrier reads (C268).
_FRAGMENT_NAME = re.compile(r"^(?P<pr>\d+)\.(?P<type>[a-z][a-z-]*)\.rst$")

#: A top-level reST bullet. Continuation lines are indented and belong to the bullet.
_BULLET = re.compile(r"^[-*+]\s+\S")


def _title(bundle: EvidenceBundle) -> tuple[str, str]:
    """(the title, where it came from). The harness records no title field of its own."""
    if bundle.pr_text:
        for line in bundle.pr_text.split("\n"):
            if line.strip():
                return line.strip().lstrip("# ").strip(), "pull request text"
    if bundle.commits:
        return bundle.commits[0].summary.strip(), "latest commit summary"
    return "", ""


def _changed_modules(bundle: EvidenceBundle) -> list[str]:
    """`sklearn.<subpackage>` for each package module the contribution changes."""
    seen = []
    for path in sorted(bundle.files):
        if not path.startswith(PACKAGE):
            continue
        parts = path.split("/")
        name = f"sklearn.{parts[1]}" if len(parts) > 2 else "sklearn"
        if name not in seen:
            seen.append(name)
    return seen


@rule(
    id="SCIKIT-LEARN-C042",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the title did not exist before the run
    reads=("pr_text", "commits"),  # spec §5: the title, and the commit summary it becomes
    heuristic=True,
)
class PullRequestTitleIsNotABareIssueReference:
    """Pre-condition: a run that recorded a pull-request title or a commit summary.
    Pass condition: that title is more than a bare `Fix #<ISSUE NUMBER>`.

    A prohibition, so the pre-condition selects the *permitted* form of the act -- having
    written a title -- and the pass condition checks it was not the prohibited one (§7.1).
    Selecting titles that already match `Fix #N` would find only violations and could
    never record a compliant title.

    Heuristic on the **pass condition** (§6.2): the run carries no title field, so the
    title is recovered from the first written line of the PR text, falling back to the
    latest commit summary, and the pattern also admits the `Fixes #1234`/`Closes gh-12`
    spellings of the same non-title.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        title, origin = _title(b)
        if not title:
            return []
        return [target(f"pr-title:{b.instance_id}", None, None, (title, origin),
                       title[:80])]

    def pass_condition(self, t: Target):
        title, origin = t.payload
        if _BARE_FIX.match(title):
            return Violated(f"the {origin} is a bare issue reference, which the guide "
                            f"names as not a good title: {title[:70]!r}")
        return Satisfied(f"the {origin} says what the change does: {title[:70]!r}")


@rule(
    id="SCIKIT-LEARN-C048",
    category=CATEGORY,
    ownership="touched",  # spec §4.2 -- the antecedent is the user-facing code change,
                          # a file that already existed; the fragment it demands is the
                          # artefact, not the target
    reads=("files",),  # spec §5: DEPARTURE from the category's `pr_text` prior -- the
                       # fragment is a file in the patch
    heuristic=True,
)
class ChangelogFragmentAddedForAUserFacingChange:
    """Pre-condition: a contribution that changes package code outside the tests.
    Pass condition: it adds a news fragment under `doc/whats_new/upcoming_changes/`
    carrying a written line.

    Heuristic on the **pre-condition** (§6.3): "likely to affect users" is not observable,
    and is approximated by *the contribution changes `sklearn/` code that is not a test*.
    That is a superset -- a private refactor affects nobody and would still be selected --
    and the wider scope is the right direction of error (§4.5).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        changed = source_files(b) + cython_files(b)
        if not changed:
            return []
        return [target(f"changelog:{b.instance_id}", None, None, b,
                       f"{len(changed)} package source file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        fragments = changelog_fragments(bundle)
        written = [p for p in fragments if added_text(bundle, p).strip()]
        if written:
            return Satisfied(f"changelog fragment added: {written[0]}")
        if fragments:
            return Violated(f"{fragments[0]} was added but carries no written line")
        return Violated(f"no changelog fragment was added under {CHANGELOG_DIR} for a "
                        f"change to package code")


@rule(
    id="SCIKIT-LEARN-C268",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the fragment did not exist before the run
    reads=("files",),  # spec §5
)
class FragmentIsNamedPullRequestDotTypeDotRst:
    """Pre-condition: each news fragment the contribution adds.
    Pass condition: its filename is `<PULL REQUEST>.<TYPE>.rst`.

    Not heuristic: towncrier reads the name, the README fixes its shape, and the check is
    a match against that shape. The pull-request number is graded only as *digits*,
    because a run has no pull request and so no number to compare against -- a property
    of the harness, not an approximation in the rule.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"fragment-name:{p}", p, None, p, p.rsplit("/", 1)[-1])
                for p in changelog_fragments(b)]

    def pass_condition(self, t: Target):
        path: str = t.payload
        name = path.rsplit("/", 1)[-1]
        if _FRAGMENT_NAME.match(name):
            return Satisfied(f"{name} is <PULL REQUEST>.<TYPE>.rst")
        return Violated(f"{name} is not named <PULL REQUEST>.<TYPE>.rst, so towncrier "
                        f"will not read it")


@rule(
    id="SCIKIT-LEARN-C269",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
)
class FragmentTypeIsOneOfTheSeven:
    """Pre-condition: each added news fragment whose name carries a type component.
    Pass condition: that component is one of the seven documented types.

    The antecedent is narrowed to names that *have* a type at all, so a fragment named
    nothing like the published shape is C268's finding and is not counted twice (§7.5).
    Not heuristic: the seven tokens are a closed published list.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in changelog_fragments(b):
            name = path.rsplit("/", 1)[-1]
            parts = name.split(".")
            if len(parts) >= 3 and parts[-1] == "rst":
                out.append(target(f"fragment-type:{path}", path, None,
                                  (path, parts[-2]), name))
        return out

    def pass_condition(self, t: Target):
        path, fragment_type = t.payload
        if fragment_type in FRAGMENT_TYPES:
            return Satisfied(f"{path.rsplit('/', 1)[-1]} uses the `{fragment_type}` type")
        return Violated(f"`{fragment_type}` is not one of the seven documented fragment "
                        f"types ({', '.join(FRAGMENT_TYPES)})")


@rule(
    id="SCIKIT-LEARN-C270",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class FragmentSitsInTheFolderForTheChangedModule:
    """Pre-condition: each added news fragment in a contribution that also changes
    package code.
    Pass condition: its folder names one of the changed modules, or is one of the topic
    folders the README allows.

    Heuristic on the **pass condition** (§6.2): "the module the PR changes" is derived
    from the top-level `sklearn/<subpackage>` of each changed path, which is the folder
    naming convention the README's own examples use, and the topic folders
    (`array-api`, `metadata-routing`, `security`) are accepted unconditionally because
    which change belongs to a topic is a maintainer's judgement, not a fact in the patch.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        modules = _changed_modules(b)
        if not modules:
            return []
        return [target(f"fragment-folder:{p}", p, None, (p, modules),
                       p[len(CHANGELOG_DIR):])
                for p in changelog_fragments(b)]

    def pass_condition(self, t: Target):
        path, modules = t.payload
        folder = path[len(CHANGELOG_DIR):].split("/")[0]
        if folder in modules:
            return Satisfied(f"{folder} matches the changed module")
        if folder in FRAGMENT_TOPIC_FOLDERS:
            return Satisfied(f"{folder} is one of the README's topic folders")
        return Violated(f"the fragment sits in `{folder}` while the contribution changes "
                        f"{', '.join(modules)}")


@rule(
    id="SCIKIT-LEARN-C271",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("files",),  # spec §5
)
class FragmentIsASingleBulletPoint:
    """Pre-condition: each added news fragment carrying a written line.
    Pass condition: exactly one top-level reST bullet.

    Not heuristic: the README states the count and states why -- the aggregation software
    cannot handle a second bullet per entry -- so a count is compared against a number.
    Continuation lines are indented and belong to the bullet above them, which is what
    makes counting column-zero bullets the right reading rather than an approximation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in changelog_fragments(b):
            text = added_text(b, path)
            if text.strip():
                out.append(target(f"fragment-bullets:{path}", path, None, (path, text),
                                  text.strip().split("\n")[0][:80]))
        return out

    def pass_condition(self, t: Target):
        path, text = t.payload
        bullets = [line for line in text.split("\n") if _BULLET.match(line)]
        if len(bullets) == 1:
            return Satisfied(f"{path.rsplit('/', 1)[-1]} is a single bullet point")
        if not bullets:
            return Violated(f"{path.rsplit('/', 1)[-1]} carries text but no bullet "
                            f"point, which the aggregation software expects")
        return Violated(f"{path.rsplit('/', 1)[-1]} carries {len(bullets)} bullet "
                        f"points; the aggregation software handles only one")

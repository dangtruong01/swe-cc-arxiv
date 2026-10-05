"""matplotlib: Git and commit conventions -- 4 rules.

Layer C. Every rule is two layers (`docs/checker-authoring.md` §2): ``precondition``
selects on the rule's ANTECEDENT, ``pass_condition`` grades.

Two of these govern *markers* -- ``[skip appveyor]`` and ``[skip ci]`` -- and neither is
coded as "every commit must carry it". A skip marker is an option a contributor takes up,
so the antecedent is *having taken it up*: C096 selects commits that use the marker and
grades where it was put, C097 selects commits that use ``[skip ci]`` and grades what kind
of change it was used on. Selecting every commit instead would fail almost every run for
not skipping CI, which is the opposite of what the sentences say.

C076 is filed ``static`` in the corpus and needs the branch the commit was made on, which
is a ``===BRANCH===`` capture rather than anything in the patch (§5, mismatch recorded
here rather than corrected in the workbook).
"""

from __future__ import annotations

import re

from compliance.core.models import (Commit, EvidenceBundle, Satisfied, Target,
                                    Undetermined, Violated)
from compliance.core.registry import rule
from compliance.rules.matplotlib._common import (DOC_ROOT, DOC_SUFFIXES,
                                                 GALLERY_SOURCE_ROOTS, target)

CATEGORY = "Git and commit conventions"

#: Branch names that mean "the project's own line of development", which is what the
#: rule calls `main`. Both spellings, because the benchmark's checkouts predate the
#: rename and a run on `master` is the same mistake.
MAIN_BRANCHES = frozenset({"main", "master"})

SKIP_APPVEYOR = re.compile(r"\[\s*skip\s+appveyor\s*\]", re.I)
SKIP_CI = re.compile(r"\[\s*skip\s+ci\s*\]", re.I)

#: Changes to which "documentation checks and unit tests do not apply" (C097): files that
#: neither ship code nor are built by the documentation job.
_CI_EXEMPT = re.compile(r"^\.github/|^\.circleci/|^azure-pipelines\.yml$|^\.appveyor\.yml$"
                        r"|^\.gitignore$|^\.gitattributes$|^\.pre-commit-config\.yaml$"
                        r"|^\.mailmap$|(^|/)README(\.[a-z]+)?$|^LICENSE/")


def _commit_targets(bundle: EvidenceBundle, prefix: str, payload=None) -> list[Target]:
    return [target(f"{prefix}:{c.sha or index}", None, None,
                   c if payload is None else payload(c), c.summary[:80], source="commit")
            for index, c in enumerate(bundle.commits)]


@rule(
    id="MATPLOTLIB-C076",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the commit did not exist before the run
    reads=("commits", "branch"),  # spec §5: which branch the commit landed on is a
                                  # ===BRANCH=== capture, not a fact about the patch
)
class NoCommitToMainBranch:
    """Pre-condition: every commit the agent made.
    Pass condition: it was made on a branch other than main.

    §7.1: the pre-condition is *a commit*, not *a commit on main*. Selecting only commits
    already on main could record a violation and never a compliant commit. Where the
    harness recorded no branch the verdict is withheld -- an unknown branch is missing
    evidence, never a clean bill.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _commit_targets(b, "branch")

    def pass_condition(self, t: Target):
        commit: Commit = t.payload
        if commit.branch is None:
            return Undetermined("tool_missing", "the harness recorded no branch for this "
                                                "commit")
        if commit.branch.lower() in MAIN_BRANCHES:
            return Violated(f"committed on {commit.branch}: {commit.summary[:60]}")
        return Satisfied(f"committed on {commit.branch}")


@rule(
    id="MATPLOTLIB-C082",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- one target for the whole contribution
    reads=("files", "status"),  # spec §5: `??` entries are what "not added" looks like
)
class EveryNewFileIsUnderVersionControl:
    """Pre-condition: the agent submitted a contribution and the harness captured
    `git status`.
    Pass condition: no file it created was left untracked.

    Exact, not a heuristic: `??` in `git status --porcelain` is precisely "created and
    never `git add`-ed", which is the sentence's subject. Selects nothing when status was
    not captured, rather than reading an empty capture as a clean tree.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not b.files or not b.status_entries:
            return []
        return [target(f"tracked:{b.instance_id}", None, None, b,
                       f"{len(b.status_entries)} status entr(ies)")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        untracked = [p for code, p in bundle.status_entries if code.strip() == "??"]
        if untracked:
            return Violated(f"{len(untracked)} new file(s) never added to version "
                            f"control, e.g. {untracked[0]}")
        return Satisfied("every new file is tracked")


@rule(
    id="MATPLOTLIB-C096",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the commit message is the agent's own artefact
    reads=("commits",),  # spec §5: the marker and its placement are both in the message
)
class SkipAppveyorMarkerOnTheFirstLine:
    """Pre-condition: every commit whose message uses the `[skip appveyor]` marker.
    Pass condition: the marker is on the message's first line.

    The rule constrains *where* an optional marker goes, so the antecedent is having used
    it -- a contributor who does not want to skip AppVeyor is not in scope at all (§7.1).
    Both outcomes are reachable from that selection: the marker on the summary line
    satisfies, the same marker in the body violates. Exact: the corpus states the
    placement and the message carries it.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for index, commit in enumerate(b.commits):
            message = commit.raw or "\n".join((commit.summary, commit.body))
            if SKIP_APPVEYOR.search(message):
                out.append(target(f"skip-appveyor:{commit.sha or index}", None, None,
                                  commit, commit.summary[:80], source="commit"))
        return out

    def pass_condition(self, t: Target):
        commit: Commit = t.payload
        if SKIP_APPVEYOR.search(commit.summary):
            return Satisfied(f"[skip appveyor] is on the first line: "
                             f"{commit.summary[:60]}")
        return Violated(f"[skip appveyor] appears below the first line, where AppVeyor "
                        f"does not read it: {commit.summary[:60]}")


@rule(
    id="MATPLOTLIB-C097",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the commit is new; the files decide the kind
    reads=("commits", "files"),  # spec §5: the marker is on the commit, what it was used
                                 # on is in the patch
    heuristic=True,
)
class SkipCiOnlyWhereChecksDoNotApply:
    """Pre-condition: every commit whose message uses the `[skip ci]` marker.
    Pass condition: the contribution touches no file a documentation check or a unit test
    would have covered.

    Heuristic on the **pass condition** (§6.2). "Changes to which documentation checks and
    unit tests do not apply" is not a category the project enumerates, so it is
    approximated by an allow-list of paths no job builds or imports -- CI configuration,
    `.gitignore`, the mailmap, READMEs, the licence directory. A change outside that list
    that genuinely runs no check reads as a violation, and the direction of that error is
    reported rather than removed.

    The pre-condition is exact and is deliberately the marker, not the change: a
    contribution that never skips CI cannot violate a restriction on skipping it.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for index, commit in enumerate(b.commits):
            message = commit.raw or "\n".join((commit.summary, commit.body))
            if SKIP_CI.search(message):
                out.append(target(f"skip-ci:{commit.sha or index}", None, None,
                                  (commit, b), commit.summary[:80], source="commit"))
        return out

    def pass_condition(self, t: Target):
        commit, bundle = t.payload
        covered = [p for p in sorted(bundle.files)
                   if not _CI_EXEMPT.search(p)
                   and (p.endswith(".py") or p.startswith(DOC_ROOT)
                        or p.endswith(DOC_SUFFIXES) or p.startswith(GALLERY_SOURCE_ROOTS))]
        if covered:
            return Violated(f"[skip ci] on a change that documentation checks or unit "
                            f"tests do cover: {covered[0]}")
        return Satisfied(f"[skip ci] used on {len(bundle.files)} file(s) no check covers")

"""scikit-learn: Git and commit conventions -- 2 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects
on the rule's ANTECEDENT, ``pass_condition`` grades.

Both rules are about *the title that becomes the commit message*. The harness records no
separate pull-request title field, so the title is recovered from the first line of the
PR text and, absent that, from the latest commit's summary. That recovery is the reason
C054 declares ``heuristic=True``; C055 reads the commit message itself and does not.

``reads`` departs from the category prior on C054, which also needs ``files`` -- the
antecedent is "a documentation contribution", which is a property of the patch, not of
the message (spec §5's worked example: category tells you the module, only the sentence
tells you what the predicate reads).
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.scikit_learn._common import (DOC_ROOT, DOC_SUFFIXES,
                                                   EXAMPLES_ROOT, target)

CATEGORY = "Git and commit conventions"

#: The commit-message markers the CI section publishes, as a closed table. The corpus
#: Notes call it eleven and list these ten; recorded here rather than corrected in the
#: workbook (spec §5, §8) -- the corpus is the specification.
CI_MARKERS = ("[ci skip]", "[cd build]", "[scipy-dev]", "[free-threaded]", "[pyodide]",
              "[float32]", "[all random seeds]", "[doc skip]", "[doc quick]",
              "[doc build]")

_MARKER = re.compile("|".join(re.escape(m) for m in CI_MARKERS), re.I)

_DOC_PREFIX = re.compile(r"^\s*(\[?DOC\]?)\b")


def _title(bundle: EvidenceBundle) -> tuple[str, str]:
    """(the title, where it came from). Empty when the run recorded neither."""
    if bundle.pr_text:
        for line in bundle.pr_text.split("\n"):
            if line.strip():
                return line.strip().lstrip("# ").strip(), "pull request text"
    if bundle.commits:
        return bundle.commits[0].summary.strip(), "latest commit summary"
    return "", ""


def _documentation_only(bundle: EvidenceBundle) -> bool:
    """Every changed path is documentation. Decidable, so the flag is not about this."""
    paths = sorted(bundle.files)
    return bool(paths) and all(
        p.startswith((DOC_ROOT, EXAMPLES_ROOT)) or p.endswith(DOC_SUFFIXES)
        for p in paths)


@rule(
    id="SCIKIT-LEARN-C054",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the target is the title the agent wrote, which
                          # did not exist before the run
    reads=("files", "pr_text", "commits"),  # spec §5: `files` decides that the rule
                                            # fires, the title carries the verdict
    heuristic=True,
)
class DocumentationTitleCarriesTheDocPrefix:
    """Pre-condition: a contribution whose every changed path is documentation.
    Pass condition: the title that becomes the commit message starts with `DOC`.

    Fires on the *documentation contribution*, not on titles already carrying the prefix
    (§7.1): the corpus Notes state the trigger as "applies only to documentation-only
    contributions", so a code change finds no target here and a documentation change with
    an unprefixed title is a recorded violation.

    Heuristic on the **pass condition** (§6.2): the run carries no pull-request title
    field, so "the title" is the first written line of the PR text, falling back to the
    latest commit summary. A run that recorded neither withholds nothing -- it reports the
    violation, because a contribution with no message at all carries no prefix either.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not _documentation_only(b):
            return []
        title, origin = _title(b)
        return [target(f"doc-title:{b.instance_id}", None, None, (title, origin),
                       title[:80] or "no title recorded")]

    def pass_condition(self, t: Target):
        title, origin = t.payload
        if not title:
            return Violated("the contribution is documentation-only but recorded no "
                            "pull-request title or commit summary to carry the DOC prefix")
        if _DOC_PREFIX.match(title):
            return Satisfied(f"{origin} starts with DOC: {title[:70]}")
        return Violated(f"documentation-only contribution, but the {origin} does not "
                        f"start with DOC: {title[:70]}")


@rule(
    id="SCIKIT-LEARN-C055",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the commits are the agent's own
    reads=("commits",),  # spec §5: the marker lives in a commit message
)
class CiMarkerIsInTheLatestCommit:
    """Pre-condition: a run whose commit messages carry a published CI marker.
    Pass condition: the newest commit is one of the messages carrying it.

    §7.1 in miniature. The marker is optional -- the corpus Notes say so -- so the
    antecedent is *having chosen to steer CI from a commit message*, and the graded
    question is whether it was put where CI reads it. Selecting only runs whose newest
    commit carries a marker would record compliance and never its absence.

    Not heuristic: the marker table is closed and published, and "latest commit" is the
    first element of ``bundle.commits``, which the log parser emits newest first.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        carrying = [c for c in b.commits if _MARKER.search(c.summary + "\n" + c.body)]
        if not carrying:
            return []
        return [target(f"ci-marker:{b.instance_id}", None, None, (b.commits, carrying),
                       f"{len(carrying)} commit message(s) carry a CI marker")]

    def pass_condition(self, t: Target):
        commits, carrying = t.payload
        latest = commits[0]
        if any(c.sha == latest.sha and c.summary == latest.summary for c in carrying):
            found = _MARKER.search(latest.summary + "\n" + latest.body)
            return Satisfied(f"the latest commit carries {found.group(0)}")
        marker = _MARKER.search(carrying[0].summary + "\n" + carrying[0].body)
        return Violated(f"{marker.group(0)} is in an earlier commit "
                        f"({carrying[0].summary[:50]!r}) and not in the latest one "
                        f"({latest.summary[:50]!r}), so CI never reads it")

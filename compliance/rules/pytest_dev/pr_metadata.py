"""pytest-dev: PR and release metadata -- 4 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

All four are about the changelog fragment, and they split cleanly in two. The **filename**
rules (C020, C021) are machine-enforced by pytest's own pre-commit hook and read exactly
off the path. The **prose** rules (C048, C049) are about sentences, and sentence splitting
is a proxy, so both are declared heuristic per the spec §6.2.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import docstrings as ds
from compliance.rules.pytest_dev._common import (CHANGELOG_NAME, CHANGELOG_ROOT,
                                                 CHANGELOG_TYPES, added_text,
                                                 changelog_entries, target)

CATEGORY = "PR and release metadata"

#: Past or present tense, matched on the verb of the leading clause. A closed set of two
#: tenses is still a grammatical judgement, which is what the heuristic flag declares.
_FUTURE_OR_MODAL = re.compile(
    r"\b(will|shall|would|could|should|may|might|going to)\b", re.I)
_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def _entry_targets(bundle: EvidenceBundle, prefix: str) -> list[Target]:
    return [target(f"{prefix}:{path}", path, None, (bundle, path), path)
            for path in changelog_entries(bundle)]


@rule(
    id="PYTEST-DEV-C020",
    category=CATEGORY,
    ownership="created",  # spec §4 created -- the fragment did not exist before the run
    reads=("files",),  # spec §5: the filename is the whole question
)
class ChangelogFilenameGrammar:
    """Pre-condition: each changelog fragment the agent added.
    Pass condition: its name is `<issue id>.<type>.rst`.

    The trivial-entry exemption the contributing page grants applies to whether a fragment
    is needed at all, not to how one is named: pytest's `changelogs-rst` pre-commit hook
    rejects any file under `changelog/` that does not match. So the pre-condition selects
    added fragments, and a contribution that adds none finds no target.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _entry_targets(b, "changelog-name")

    def pass_condition(self, t: Target):
        _, path = t.payload
        name = path[len(CHANGELOG_ROOT):]
        if CHANGELOG_NAME.match(name):
            return Satisfied(f"{name} matches <issue id>.<type>.rst")
        return Violated(f"{name} is not <issue id>.<type>.rst")


@rule(
    id="PYTEST-DEV-C021",
    category=CATEGORY,
    ownership="created",  # spec §4 created
    reads=("files",),  # spec §5
)
class ChangelogTypeFromTheClosedList:
    """Pre-condition: each changelog fragment the agent added whose name parses.
    Pass condition: its type is one of the ten the project publishes.

    A fragment whose name does not parse is C020's finding, not this rule's -- selecting it
    here would report the same defect twice and depress both rates.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for t in _entry_targets(b, "changelog-type"):
            _, path = t.payload
            if CHANGELOG_NAME.match(path[len(CHANGELOG_ROOT):]):
                out.append(t)
        return out

    def pass_condition(self, t: Target):
        _, path = t.payload
        kind = CHANGELOG_NAME.match(path[len(CHANGELOG_ROOT):]).group("type")
        if kind in CHANGELOG_TYPES:
            return Satisfied(f"type `{kind}` is one of the ten published")
        return Violated(f"type `{kind}` is outside the published list "
                        f"({', '.join(CHANGELOG_TYPES)})")


@rule(
    id="PYTEST-DEV-C048",
    category=CATEGORY,
    ownership="created",  # spec §4 created
    reads=("files",),  # spec §5
    heuristic=True,
)
class ChangelogTenseIsPastOrPresent:
    """Pre-condition: each changelog fragment the agent added that carries prose.
    Pass condition: none of its sentences is written in the future or with a modal.

    Heuristic on the **pass condition** (§6.2). Tense is grammar, and this detects only its
    complement: a sentence carrying `will`, `should`, `may` and friends is not past or
    present, which is sound, but the absence of those words does not prove the sentence is
    either. Graded one-sidedly for that reason -- it can find a violation, and a pass means
    only that the common failure is absent.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in changelog_entries(b):
            text = added_text(b, path).strip()
            if text:
                out.append(target(f"changelog-tense:{path}", path, None, (path, text),
                                  text[:80]))
        return out

    def pass_condition(self, t: Target):
        path, text = t.payload
        for sentence in _SENTENCE.split(text):
            if match := _FUTURE_OR_MODAL.search(sentence):
                return Violated(f"{path}: `{match.group(0)}` is neither past nor present "
                                f"tense -- {sentence.strip()[:80]}")
        return Satisfied(f"{path} carries no future or modal verb")


@rule(
    id="PYTEST-DEV-C049",
    category=CATEGORY,
    ownership="created",  # spec §4 created
    reads=("files",),  # spec §5
    heuristic=True,
)
class ChangelogSentencesArePunctuated:
    """Pre-condition: each changelog fragment the agent added that carries prose.
    Pass condition: every prose paragraph in it ends with a terminating period.

    Heuristic on the **pass condition** (§6.2): the rule says *sentences*, and splitting
    reStructuredText prose into sentences is a proxy. Paragraphs are used as the unit
    instead, and directive, comment and literal-block lines are skipped, because a `::`
    line or a `.. note::` is not a sentence and reporting it would be a false violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in changelog_entries(b):
            lines = [line for line in added_text(b, path).split("\n")]
            prose = [line for line in lines
                     if line.strip() and not line.strip().startswith((".. ", ":", ">>>"))
                     and not line.rstrip().endswith("::") and not line.startswith("    ")]
            if prose:
                out.append(target(f"changelog-period:{path}", path, None, (path, prose),
                                  prose[0][:80]))
        return out

    def pass_condition(self, t: Target):
        path, prose = t.payload
        paragraph = " ".join(line.strip() for line in prose).strip()
        if ds.ends_with_terminator(paragraph):
            return Satisfied(f"{path} ends with punctuation: ...{paragraph[-40:]}")
        return Violated(f"{path} does not end with a period: ...{paragraph[-60:]}")

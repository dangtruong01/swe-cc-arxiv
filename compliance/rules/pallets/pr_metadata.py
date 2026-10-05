"""pallets (flask): PR and release metadata -- 4 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

**Every rule here reads a file, not the pull request.** The category's usual evidence is
`pr_text`, and taking that default would have been wrong twice over: flask keeps its
changelog in the repository as `CHANGES.rst`, and C021 is about the shape of the diff.
Worked through as the example in `docs/checker-authoring.md` §5.

**Corpus note (spec §5).** C018, C021 and C086 are filed ``CheckTier=differential``. None
of them needs a tool run: each is decidable from the patch, which is what the corpus's own
Conclusion for all three says ("read straight off the diff"). The sentence is followed and
the divergence recorded here rather than by editing the workbook (§0).

**C018 and C086 bind the same artefact in opposite directions** (spec §7.5): C086 requires
a `CHANGES.rst` entry, C018 forbids one for a change that only touches documentation or
tool configuration. The antecedent of C086 is narrowed by exactly C018's condition rather
than either rule being dropped, and `tests/test_pallets_pr_metadata.py` pins the resolution
with a no-target case.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.pallets._common import (CHANGELOG, added_lines, is_documentation,
                                              is_tool_config, shipped_source, target)

CATEGORY = "PR and release metadata"

#: A CHANGES.rst entry is a reStructuredText bullet. flask writes them as `-   ...`.
_BULLET = re.compile(r"^\s*[*-]\s+\S")
#: A reStructuredText section underline, which is how CHANGES.rst separates versions.
_UNDERLINE = re.compile(r"^([-=~^\"'`#*+])\1{2,}\s*$")
#: Imports that exist only to carry annotations.
_TYPING_IMPORT = re.compile(
    r"^\s*(from\s+(typing|typing_extensions|__future__)\s+import\b|import\s+typing\b)")
#: `name: Type` and `name: Type = default` at statement level -- an annotation and nothing
#: else. Deliberately narrow: it must not match an ordinary dict entry or a call.
_ANNOTATION_ONLY = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_]*\s*:\s*[^=]+(=\s*\S.*)?$")


def _docs_or_config_only(bundle: EvidenceBundle) -> bool:
    """Every changed path but the changelog is documentation or tool configuration.

    The changelog is excluded from the test rather than counted as documentation: whether
    it was touched is the *question* C018 asks, not part of its antecedent.
    """
    others = [p for p in sorted(bundle.files) if p != CHANGELOG]
    return bool(others) and all(is_documentation(p) or is_tool_config(p) for p in others)


def _changelog_added(bundle: EvidenceBundle) -> tuple[tuple[int, str], ...]:
    return added_lines(bundle, CHANGELOG)


@rule(
    id="PALLETS-C018",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- one target for the whole contribution, whose
                          # files are ones the agent edited
    reads=("files",),  # spec §5: the diff decides both halves
    heuristic=True,
)
class NoChangelogEntryForDocsOrToolConfig:
    """Pre-condition: a contribution whose every change outside the changelog is
    documentation or tool configuration.
    Pass condition: it adds no entry to `CHANGES.rst`.

    The pre-condition is the situation the prohibition is aimed at, not the prohibited act
    (§7.1): selecting contributions that added an entry could only ever find violations.

    Heuristic on the **pre-condition** (§6.3). *Tool configuration* is a category the
    sentence names but does not enumerate, so it is approximated by the project's
    configuration paths -- `pyproject.toml`, `tox.ini`, `.pre-commit-config.yaml`,
    `.github/` and their neighbours. A configuration file outside that list makes the
    contribution look like a code change and the rule finds no target.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not _docs_or_config_only(b):
            return []
        others = [p for p in sorted(b.files) if p != CHANGELOG]
        return [target(f"no-changelog:{b.instance_id}", None, None, b,
                       f"{len(others)} documentation or configuration file(s): "
                       f"{others[0]}")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        for lineno, text in _changelog_added(bundle):
            if _BULLET.match(text):
                return Violated(f"{CHANGELOG}:{lineno} gains an entry for a change that "
                                f"only touches documentation or tool configuration: "
                                f"{text.strip()[:70]}")
        if CHANGELOG in bundle.files and _changelog_added(bundle):
            return Violated(f"{CHANGELOG} gains {len(_changelog_added(bundle))} line(s) "
                            f"for a documentation-only or configuration-only change")
        return Satisfied(f"{CHANGELOG} is untouched by a documentation-only or "
                         f"configuration-only change")


@rule(
    id="PALLETS-C021",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- the whole contribution is the scope of the rule
    reads=("files",),  # spec §5: what is bundled together is visible in the diff
    heuristic=True,
)
class BugFixCarriesNothingUnrelated:
    """Pre-condition: a contribution read as a bug fix -- it changes shipped source that
    already existed.
    Pass condition: it bundles none of the three things the sentence names: a file moved
    or removed, a change that only adds type annotations, or a test file reorganised.

    Heuristic on **both** layers. On the pre-condition (§6.3), *a bug fix* is not
    observable -- provenance is a fact about the benchmark, not the contribution -- so the
    stand-in is a change to existing shipped source, and a contribution that adds a new
    module is treated as a feature and finds no target. On the pass condition (§6.2), only
    the forms that leave a mark in a diff are detected: a rename or deletion for the
    refactor and the test reorganisation, and an all-annotations file for the type change.
    An unrelated rewrite inside one file is invisible here and is reported as satisfying.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        source = shipped_source(b)
        if not source or all(b.files[p].is_new for p in source):
            return []
        return [target(f"focused:{b.instance_id}", None, None, b,
                       f"{len(b.files)} file(s) alongside {len(source)} source change(s)")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        for path in sorted(bundle.files):
            change = bundle.files[path]
            if change.old_path and change.old_path != path:
                return Violated(f"a bug fix moves {change.old_path} to {path}, which is a "
                                f"refactor or a test reorganisation bundled with the fix")
            if change.is_deleted:
                return Violated(f"a bug fix deletes {path}, which is a refactor or a test "
                                f"reorganisation bundled with the fix")
        for path in sorted(bundle.files):
            written = [text for _, text in added_lines(bundle, path) if text.strip()]
            if not written or not path.endswith(".py"):
                continue
            if all(_TYPING_IMPORT.match(text) or _ANNOTATION_ONLY.match(text)
                   for text in written):
                return Violated(f"a bug fix bundles a type-annotation-only change to "
                                f"{path} ({len(written)} line(s), all annotations)")
        return Satisfied(f"{len(bundle.files)} changed file(s) carry no rename, deletion "
                         f"or annotation-only edit")


@rule(
    id="PALLETS-C053",
    category=CATEGORY,
    ownership="created",  # spec §4.3 -- the sentence says "a new changelog entry"; the
                          # entry is what the agent brought into being, not CHANGES.rst
    reads=("files",),  # spec §5: position inside a file in the patch
    heuristic=True,
)
class ChangelogEntryAppendedToItsSection:
    """Pre-condition: each block of lines the agent added to `CHANGES.rst`.
    Pass condition: no pre-existing content follows it before the next version heading.

    Heuristic on the **pass condition** (§6.2). The sentence says *the relevant section*,
    and which section is relevant is a judgement about the release the change belongs to.
    What is checked is the weaker, decidable half: wherever the entry landed, it sits at
    the end of that section. An entry appended to the end of the wrong version is recorded
    as satisfying, and that limit is the reason for the flag.

    Selects nothing when the post-patch file could not be reconstructed, rather than
    reading an unavailable file as a compliant one.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        change = b.files.get(CHANGELOG)
        if change is None or change.head_text is None or not change.added_lines:
            return []
        lines = change.head_text.split("\n")
        authored = set(change.authored_lines)
        out = []
        for block in _contiguous(sorted(n for n, _ in change.added_lines)):
            out.append(target(f"append-entry:{CHANGELOG}:{block[0]}", CHANGELOG,
                              (block[0], block[-1]), (lines, authored, block),
                              _line(lines, block[0])[:80]))
        return out

    def pass_condition(self, t: Target):
        lines, authored, block = t.payload
        for number in range(block[-1] + 1, len(lines) + 1):
            if _opens_a_section(lines, number):
                break
            text = _line(lines, number)
            if text.strip() and number not in authored:
                return Violated(f"{CHANGELOG}:{block[0]} is not at the end of its "
                                f"section: line {number} already existed -- "
                                f"{text.strip()[:60]}")
        return Satisfied(f"{CHANGELOG}:{block[0]}-{block[-1]} is appended to the end of "
                         f"its section")


@rule(
    id="PALLETS-C086",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- the antecedent is the code change,
                          # even though the changelog entry itself is created
    reads=("files",),  # spec §5: the changelog is a file in the patch, not PR prose
    heuristic=True,
)
class ChangelogEntrySummarisesTheChange:
    """Pre-condition: a contribution that changes shipped source, and is therefore outside
    the exemption C018 states.
    Pass condition: `CHANGES.rst` gains a bullet.

    The antecedent excludes exactly what C018 forbids an entry for -- a change touching
    only documentation or tool configuration -- so the two rules cannot demand opposite
    things of the same contribution (§7.5). The exclusion is pinned by a no-target test
    rather than remembered.

    Heuristic on the **pass condition** (§6.2): *summarizing the change* is graded as the
    presence of a bullet, because whether a sentence summarises a diff is not mechanically
    decidable. An entry that says nothing useful passes.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if _docs_or_config_only(b):  # C018 forbids an entry here -- do not demand one
            return []
        source = shipped_source(b)
        if not source:
            return []
        return [target(f"changelog:{b.instance_id}", None, None, b,
                       f"{len(source)} shipped source file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if CHANGELOG not in bundle.files:
            return Violated(f"{CHANGELOG} is untouched by a contribution that changes "
                            f"shipped source")
        for lineno, text in _changelog_added(bundle):
            if _BULLET.match(text):
                return Satisfied(f"{CHANGELOG}:{lineno} gains an entry: "
                                 f"{text.strip()[:70]}")
        return Violated(f"{CHANGELOG} was edited but gained no entry")


def _line(lines: list[str], number: int) -> str:
    return lines[number - 1] if 1 <= number <= len(lines) else ""


def _opens_a_section(lines: list[str], number: int) -> bool:
    """A version heading: a non-blank line whose successor is a reST underline."""
    text = _line(lines, number)
    return bool(text.strip()) and bool(_UNDERLINE.match(_line(lines, number + 1)))


def _contiguous(numbers: list[int]) -> list[list[int]]:
    blocks: list[list[int]] = []
    for number in numbers:
        if blocks and number == blocks[-1][-1] + 1:
            blocks[-1].append(number)
        else:
            blocks.append([number])
    return blocks

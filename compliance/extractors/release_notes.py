"""Parse a pull-request description into its structured parts.

Layer B: shared across repositories. Nothing here knows which submodule names are valid
or which keywords a particular project uses -- those live in the rule pack.

`pr_text` has no schema guarantee. The agent emits free-form prose -- where the harness
asks for it is the adapter's business -- and the real pilot output showed it wrapped in code fences, with the
release-notes block appearing first in one run and last in another, and submodule
headers written both with and without a trailing colon. Everything here is written
against that reality rather than an idealised template.

Extraction failure is `status = parse_error`, never `not_applicable` (plan §5, Phase 2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

BEGIN_MARKER = "<!-- BEGIN RELEASE NOTES -->"
END_MARKER = "<!-- END RELEASE NOTES -->"
NO_ENTRY = "NO ENTRY"

# GitHub's autoclose vocabulary. Which of these a project endorses is a rule-pack
# question; that they close an issue when adjacent to #N is GitHub behaviour.
AUTOCLOSE_KEYWORDS = (
    "close", "closes", "closed",
    "fix", "fixes", "fixed",
    "resolve", "resolves", "resolved",
)

_FENCE = re.compile(r"^\s*```[a-zA-Z]*\s*\n(.*)\n\s*```\s*$", re.S)
_ISSUE_REF = re.compile(r"#(\d+)")
_AUTOCLOSE = re.compile(
    r"\b(?P<keyword>" + "|".join(AUTOCLOSE_KEYWORDS) + r")\b\s*:?\s*#(?P<number>\d+)",
    re.I,
)
_NEGATION = re.compile(r"\b(not|n't|never|without|no longer|doesn't|does not)\b", re.I)
_LIST_ITEM = re.compile(r"^\s*[-*+]\s+(?P<text>.+?)\s*$")
# A submodule header is a bare word line inside the block: `geometry` or `functions:`.
_HEADER = re.compile(r"^\s*(?P<name>[A-Za-z_][A-Za-z0-9_.]*)\s*:?\s*$")
# Agents also write the header and its change on one line: `matrices: Fixed the thing.`
# That is content, not an empty block, and it is not a Markdown list -- so it must yield
# both a submodule and a non-list entry, or C053/C054/C055 all judge it wrongly.
_HEADER_INLINE = re.compile(
    r"^\s*(?P<name>[A-Za-z_][A-Za-z0-9_.]*)\s*:\s*(?P<text>\S.*?)\s*$"
)


@dataclass(frozen=True)
class ReleaseNoteEntry:
    submodule: str
    text: str
    line: int
    is_list_item: bool


@dataclass(frozen=True)
class ReleaseNotes:
    present: bool = False
    raw: str = ""
    no_entry: bool = False
    submodules: tuple[str, ...] = ()
    entries: tuple[ReleaseNoteEntry, ...] = ()
    stray_lines: tuple[str, ...] = ()
    """Non-empty content under a header that is not a Markdown list item."""


@dataclass(frozen=True)
class AutocloseRef:
    keyword: str
    number: int
    sentence: str
    in_opening_paragraph: bool
    negated: bool


@dataclass(frozen=True)
class PullRequest:
    raw: str = ""
    body: str = ""
    """The description with the release-notes block removed."""
    title: str = ""
    opening_paragraph: str = ""
    release_notes: ReleaseNotes = ReleaseNotes()
    autoclose: tuple[AutocloseRef, ...] = ()
    issue_refs: tuple[int, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not self.raw.strip()


def strip_fences(text: str) -> str:
    """Unwrap a whole-body ``` fence. One pilot run wrapped its entire PR in one."""
    match = _FENCE.match(text.strip())
    return match.group(1) if match else text


def _split_block(text: str) -> tuple[str, str | None]:
    """Return (body without the block, block contents or None)."""
    start = text.find(BEGIN_MARKER)
    end = text.find(END_MARKER)
    if start == -1 or end == -1 or end < start:
        return text, None
    block = text[start + len(BEGIN_MARKER) : end]
    body = text[:start] + text[end + len(END_MARKER) :]
    return body, block


def parse_release_notes(block: str | None) -> ReleaseNotes:
    """Submodule headers, their list items, and anything under a header that is not one."""
    if block is None:
        return ReleaseNotes(present=False)
    if NO_ENTRY in block:
        return ReleaseNotes(present=True, raw=block, no_entry=True)

    submodules: list[str] = []
    entries: list[ReleaseNoteEntry] = []
    stray: list[str] = []
    current: str | None = None
    for offset, line in enumerate(block.splitlines()):
        if not line.strip():
            continue
        if item := _LIST_ITEM.match(line):
            entries.append(
                ReleaseNoteEntry(current or "", item.group("text"), offset, True)
            )
        elif header := _HEADER.match(line):
            current = header.group("name")
            submodules.append(current)
        elif inline := _HEADER_INLINE.match(line):
            current = inline.group("name")
            submodules.append(current)
            entries.append(ReleaseNoteEntry(current, inline.group("text"), offset, False))
            stray.append(inline.group("text"))
        elif current is not None:
            stray.append(line.strip())
            entries.append(ReleaseNoteEntry(current, line.strip(), offset, False))
        else:
            stray.append(line.strip())
    return ReleaseNotes(
        present=True,
        raw=block,
        no_entry=False,
        submodules=tuple(submodules),
        entries=tuple(entries),
        stray_lines=tuple(stray),
    )


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n{2,}", text) if s.strip()]


def parse(text: str | None) -> PullRequest:
    """Parse free-form PR text into its structured parts."""
    raw = strip_fences(text or "")
    body, block = _split_block(raw)
    notes = parse_release_notes(block)

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    opening = paragraphs[0] if paragraphs else ""
    # The title is the first non-empty line of the description proper. There is no
    # separate title field in a text-only PR, so this mirrors the commit convention.
    title = next((l.strip() for l in body.splitlines() if l.strip()), "")

    refs = []
    for match in _AUTOCLOSE.finditer(body):
        sentence = next(
            (s for s in _sentences(body) if match.group(0).lower() in s.lower()), ""
        )
        refs.append(
            AutocloseRef(
                keyword=match.group("keyword").lower(),
                number=int(match.group("number")),
                sentence=sentence,
                in_opening_paragraph=match.start() < len(opening),
                negated=bool(_NEGATION.search(sentence)),
            )
        )

    return PullRequest(
        raw=raw,
        body=body,
        title=title,
        opening_paragraph=opening,
        release_notes=notes,
        autoclose=tuple(refs),
        issue_refs=tuple(int(n) for n in _ISSUE_REF.findall(body)),
    )

"""Docstring structure: sections, their order, their headings, the summary.

Layer B -- shared across Python repositories, and it names none of them. Which section
names a project accepts, which order it wants them in, and which underline character it
uses are all passed in by the caller; the default vocabulary is numpydoc's own, because
that is the convention these projects derive from.

Everything here works on the *cleaned* docstring text and its real file line numbers, as
``extractors/python_ast.Docstring`` supplies them, so a rule can point at the offending
line rather than at an offset into a string.

Two things are deliberately kept apart, because conflating them loses the only evidence a
formatting rule has:

* a **heading** is a line whose successor is an underline of repeated punctuation
* a **section** is a heading plus the lines beneath it, up to the next heading

A line that looks like a heading but is not underlined is therefore *not* a section, and
that is exactly what a rule about missing underlines needs to see.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Optional, Sequence

# The numpydoc section vocabulary, as numpydoc publishes it. A **recognition** vocabulary,
# not an ordering: `find_headings` asks only whether a heading is a name it knows, and any
# rule about the order sections should appear in belongs to the project that has an opinion
# about it.
#
# It carried `"Explanation"` until 22 Aug 2026, which is not a numpydoc section at all --
# numpydoc calls that "Extended Summary". It is one project's name for it, and its presence
# here made this constant that project's vocabulary wearing a generic label, in the layer
# that is supposed to have none. A caller whose project deviates passes its own list, which
# is what `known=` is for.
NUMPYDOC_SECTIONS: tuple[str, ...] = (
    "Extended Summary", "Parameters", "Returns", "Yields", "Receives", "Other Parameters",
    "Raises", "Warns", "Warnings", "See Also", "Notes", "References", "Examples",
    "Attributes", "Methods",
)

UNDERLINE_CHARS = "=-~^\"'`#*+_:."

# Permissive for the same reason as `rst._ADORNMENT`: a rule about an underline of the
# wrong length or the wrong character needs the underline to be recognised first.
_UNDERLINE = re.compile(rf"^\s*[{re.escape(UNDERLINE_CHARS)}]{{1,}}\s*$")
_PROMPT = re.compile(r"^(\s*)>>> ")
_CONTINUATION = re.compile(r"^(\s*)\.\.\. ")
_SENTENCE_END = re.compile(r"[.!?][\"')\]]*$")


@dataclass(frozen=True)
class Heading:
    """A section heading and the underline that makes it one."""

    name: str
    lineno: int
    """File line of the heading text."""
    underline: str
    underline_lineno: int
    indent: int

    @property
    def underline_char(self) -> str:
        return self.underline.strip()[:1]

    @property
    def underline_length(self) -> int:
        return len(self.underline.strip())


@dataclass(frozen=True)
class Section:
    """A heading plus its body, up to the next heading."""

    heading: Heading
    body: tuple[tuple[int, str], ...]
    """(file line, text) for each line beneath the heading, underline excluded."""

    @property
    def name(self) -> str:
        return self.heading.name

    def text(self) -> str:
        return "\n".join(text for _, text in self.body)

    def paragraphs(self) -> list[str]:
        return [p for p in re.split(r"\n\s*\n", self.text().strip()) if p.strip()]

    def is_empty(self) -> bool:
        return not self.text().strip()


@dataclass(frozen=True)
class Doc:
    """One parsed docstring."""

    lines: tuple[tuple[int, str], ...]
    """(file line, text) for every line of the cleaned docstring."""
    headings: tuple[Heading, ...]
    sections: tuple[Section, ...]
    summary: tuple[tuple[int, str], ...] = ()
    """The lines before the first heading, blank lines trimmed from both ends."""
    quote: str = ""
    """The opening quote characters as written, e.g. `\"\"\"` or `r\"\"\"`."""

    def section(self, name: str) -> Optional[Section]:
        lowered = name.lower()
        return next((s for s in self.sections if s.name.lower() == lowered), None)

    def has(self, name: str) -> bool:
        return self.section(name) is not None

    def section_order(self) -> tuple[str, ...]:
        return tuple(s.name for s in self.sections)

    def text(self) -> str:
        return "\n".join(text for _, text in self.lines)

    def summary_text(self) -> str:
        return " ".join(text.strip() for _, text in self.summary).strip()


def find_headings(
    lines: Sequence[tuple[int, str]], known: Iterable[str] = NUMPYDOC_SECTIONS
) -> list[Heading]:
    """Every heading: a non-blank line whose successor is an underline.

    Restricted to ``known`` names so ordinary prose followed by a line of dashes -- a
    table rule, a separator -- is not mistaken for a section. A caller wanting to catch
    *misspelled* section names passes a wider vocabulary.
    """
    names = {n.lower() for n in known}
    out: list[Heading] = []
    for index in range(len(lines) - 1):
        lineno, text = lines[index]
        next_lineno, next_text = lines[index + 1]
        if not text.strip() or not _UNDERLINE.match(next_text):
            continue
        if text.strip().lower() not in names:
            continue
        out.append(Heading(
            name=text.strip(),
            lineno=lineno,
            underline=next_text,
            underline_lineno=next_lineno,
            indent=len(text) - len(text.lstrip()),
        ))
    return out


def parse(
    lines: Sequence[tuple[int, str]],
    *,
    known: Iterable[str] = NUMPYDOC_SECTIONS,
    quote: str = "",
) -> Doc:
    """Parse a docstring given its lines as (file line number, text) pairs."""
    lines = tuple(lines)
    headings = tuple(find_headings(lines, known))
    positions = {h.lineno: h for h in headings}

    sections: list[Section] = []
    for order, heading in enumerate(headings):
        start = next(i for i, (n, _) in enumerate(lines) if n == heading.underline_lineno) + 1
        end = len(lines)
        if order + 1 < len(headings):
            end = next(i for i, (n, _) in enumerate(lines)
                       if n == headings[order + 1].lineno)
        sections.append(Section(heading, lines[start:end]))

    first = headings[0].lineno if headings else None
    summary_lines = [(n, t) for n, t in lines if first is None or n < first]
    while summary_lines and not summary_lines[0][1].strip():
        summary_lines.pop(0)
    while summary_lines and not summary_lines[-1][1].strip():
        summary_lines.pop()

    return Doc(lines=lines, headings=headings, sections=tuple(sections),
               summary=tuple(summary_lines), quote=quote)


def summary_sentences(summary: Sequence[tuple[int, str]]) -> list[str]:
    """The summary split into sentences, for rules about it being a single one."""
    text = " ".join(t.strip() for _, t in summary).strip()
    if not text:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def ends_with_terminator(text: str) -> bool:
    return bool(_SENTENCE_END.search(text.strip()))


def doctest_blocks(lines: Sequence[tuple[int, str]]) -> list[list[tuple[int, str]]]:
    """Consecutive runs of doctest lines, prompts and expected output together.

    A blank line ends a block. Rules about blank-line separation between examples need to
    see where one block stops and the next starts, which the parsed examples cannot show.
    """
    blocks: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    in_block = False
    for lineno, text in lines:
        if _PROMPT.match(text):
            if not in_block and current:
                blocks.append(current)
                current = []
            in_block = True
            current.append((lineno, text))
        elif in_block and text.strip():
            current.append((lineno, text))
        elif in_block:
            blocks.append(current)
            current = []
            in_block = False
    if current:
        blocks.append(current)
    return blocks


def opening_quote(source: str, docstring_lineno: int) -> str:
    """The quote characters a docstring was opened with, prefix included.

    Read from the file text because the AST discards it, and several rules are about the
    quote itself: triple-double, and raw when the body contains a backslash.
    """
    lines = source.split("\n")
    if not 1 <= docstring_lineno <= len(lines):
        return ""
    match = re.search(r"""([rubRUB]{0,2})("{3}|'{3}|"|')""", lines[docstring_lineno - 1])
    return f"{match.group(1)}{match.group(2)}" if match else ""

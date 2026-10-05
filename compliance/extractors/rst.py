"""reStructuredText surface features: headings, inline markup, cross-references.

Layer B -- shared across Python repositories, and it names none of them.

This is not an RST parser and does not pretend to be. It recognises the constructs the
documentation rules are about, on a line-by-line basis, because that is what lets a rule
report *which line* is wrong. A real parser would normalise away the very details --
underline length, backtick count, `~` in a target -- that the rules exist to check.

Markdown detection is included for the same reason: several rules forbid Markdown where
RST is expected, and the way to spot it is the constructs the two do differently.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

# Punctuation RST accepts as heading adornment. `<` and `>` are omitted: the spec allows
# them, they are vanishingly rare, and a line of `>>>` would otherwise read as an
# underline and turn the doctest line above it into a heading.
HEADING_CHARS = "=-`:.'\"~^_*+#"

# Deliberately permissive: ANY run of adornment characters, mixed or not. A rule about
# malformed underlines has to be able to see the malformed one -- if `==-==` did not
# register as an underline at all, no heading would be found and the rule could never
# fire on the error it exists to catch. `RstHeading.is_consistent` does the judging.
_ADORNMENT = re.compile(rf"^\s*[{re.escape(HEADING_CHARS)}]{{2,}}\s*$")
_INLINE_LITERAL = re.compile(r"``([^`]+)``")
_SINGLE_BACKTICK = re.compile(r"(?<!`)`(?!`)([^`\n]+)(?<!`)`(?!`)")
_ROLE = re.compile(r":(?P<role>[a-zA-Z:+-]+):`(?P<target>[^`]+)`")
_CODE_BLOCK = re.compile(r"::\s*$")
_DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b")
_URL = re.compile(r"https?://\S+")
_CITATION = re.compile(r"^\s*\.\.\s*\[(?P<label>[^\]]+)\]")

# Constructs Markdown has and RST does not, or spells differently.
_MD_HEADING = re.compile(r"^\s*#{1,6}\s+\S")
_MD_LINK = re.compile(r"\[[^\]]+\]\([^)]+\)")
_MD_FENCE = re.compile(r"^\s*(```|~~~)")
_MD_BOLD = re.compile(r"\*\*[^*\n]+\*\*")
_MD_LIST = re.compile(r"^\s*[-*+]\s+\S")


@dataclass(frozen=True)
class RstHeading:
    text: str
    lineno: int
    underline: str
    underline_lineno: int
    overline: str = ""

    @property
    def char(self) -> str:
        return self.underline.strip()[:1]

    @property
    def is_consistent(self) -> bool:
        """One repeated character, and at least as long as the text it underlines."""
        stripped = self.underline.strip()
        if len(set(stripped)) != 1:
            return False
        if self.overline:
            over = self.overline.strip()
            if len(set(over)) != 1 or over[0] != stripped[0] or len(over) < len(self.text.strip()):
                return False
        return len(stripped) >= len(self.text.strip())


@dataclass(frozen=True)
class Role:
    """An RST interpreted-text role, e.g. ``:obj:`~.name```."""

    role: str
    target: str
    lineno: int
    raw: str

    @property
    def has_tilde(self) -> bool:
        return "~" in self.target

    @property
    def custom_text(self) -> bool:
        """``:obj:`some words <target>``` -- the angle-bracket form."""
        return bool(re.search(r"<[^>]+>\s*$", self.target))

    @property
    def link_target(self) -> str:
        if match := re.search(r"<([^>]+)>\s*$", self.target):
            return match.group(1)
        return self.target

    @property
    def is_abbreviated(self) -> bool:
        """``~.name`` -- the leading-tilde abbreviation for a top-level object."""
        return self.link_target.startswith("~")


def headings(lines: Sequence[tuple[int, str]]) -> list[RstHeading]:
    out: list[RstHeading] = []
    for index in range(len(lines) - 1):
        lineno, text = lines[index]
        next_lineno, next_text = lines[index + 1]
        if not text.strip() or _ADORNMENT.match(text) or not _ADORNMENT.match(next_text):
            continue
        overline = ""
        if index > 0 and _ADORNMENT.match(lines[index - 1][1]):
            overline = lines[index - 1][1]
        out.append(RstHeading(text, lineno, next_text, next_lineno, overline))
    return out


def roles(lines: Sequence[tuple[int, str]]) -> list[Role]:
    out: list[Role] = []
    for lineno, text in lines:
        for match in _ROLE.finditer(text):
            out.append(Role(match.group("role"), match.group("target"), lineno,
                            match.group(0)))
    return out


def single_backtick_spans(text: str) -> list[str]:
    """Single-backtick spans, which RST reads as a *role*, not as literal code.

    The constructs that legitimately use one backtick -- roles, citations, links -- are
    removed first, so what is left is a bare span someone probably meant as code.
    """
    stripped = _ROLE.sub(" ", _INLINE_LITERAL.sub(" ", text))
    return [m.group(1) for m in _SINGLE_BACKTICK.finditer(stripped)]


def inline_literals(text: str) -> list[str]:
    return [m.group(1) for m in _INLINE_LITERAL.finditer(text)]


def opens_code_block(text: str) -> bool:
    return bool(_CODE_BLOCK.search(text))


def citations(lines: Sequence[tuple[int, str]]) -> list[tuple[int, str]]:
    """``.. [1] ...`` citation definitions, in the order they appear."""
    return [(lineno, m.group("label"))
            for lineno, text in lines if (m := _CITATION.match(text))]


def dois(text: str) -> list[str]:
    return _DOI.findall(text)


def urls(text: str) -> list[str]:
    return _URL.findall(text)


def markdown_constructs(lines: Sequence[tuple[int, str]]) -> list[tuple[int, str]]:
    """Lines carrying a construct that is Markdown rather than RST.

    Bold and bullet lists are excluded on purpose: ``**bold**`` is valid RST too, and
    ``- item`` is a valid RST bullet. Only the constructs RST genuinely lacks are reported,
    so a rule built on this does not fail correct RST.
    """
    out: list[tuple[int, str]] = []
    for lineno, text in lines:
        if _MD_HEADING.match(text):
            out.append((lineno, "Markdown heading (#)"))
        elif _MD_FENCE.match(text):
            out.append((lineno, "Markdown code fence"))
        elif _MD_LINK.search(text):
            out.append((lineno, "Markdown link [text](url)"))
    return out


def is_rst_path(path: str) -> bool:
    return path.endswith((".rst", ".rest"))


def is_markdown_path(path: str) -> bool:
    return path.endswith((".md", ".markdown"))

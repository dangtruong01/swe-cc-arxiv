"""Curly-brace template tag syntax: where the tags are, and how they are written.

Layer B -- shared across repositories, and it names none of them.

Several template languages for HTML-ish files share one surface syntax: ``{% ... %}`` is
a block tag, ``{{ ... }}`` is a variable expression, ``{# ... #}`` is a comment, and
everything else is text. The rules that care about such files are about *style* -- is the
extends tag the first thing in the file, is there exactly one space inside the braces, is
the closing tag on the same line as its opener, are the arguments in alphabetical order --
so this is a lexer, not a parser. It recognises the surface constructs and records the
line and column of each, because that is what lets a rule report *which line* is wrong. A
real parser would build a tree and normalise away the spacing the rules exist to check.

Nothing here judges template semantics. An unrecognised tag name is simply a tag name, and
malformed input degrades: an opening delimiter with no closer, or a closer with no opener,
is reported through `malformed_delimiters` and the rest of the file still tokenises. No
function in this module raises on bad input.

Columns are 0-based offsets into their line; line numbers are 1-based, as everywhere else.
"""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field
from typing import Optional, Sequence

# The three delimiter pairs this syntax family shares, and the node kind each opens.
DELIMITERS = {"{%": "%}", "{{": "}}", "{#": "#}"}
KINDS = {"{%": "block", "{{": "variable", "{#": "comment"}

# `.` binds an attribute to its owner and `|` binds a filter to its input. Both are
# conventionally written tight against their neighbours while every other token in an
# expression is separated by one space -- so a spacing rule needs the two treated apart.
TIGHT_OPERATORS = (".", "|")

# A closing tag is spelled as `end` + the name of the tag it closes. That is a property of
# the syntax, not of any one library, which is what makes pairing possible without a table
# of every tag name in existence.
CLOSING_PREFIX = "end"

# Tags that open a body even when the file never closes them. `tag_pairs` unions this with
# every `end<name>` it actually finds, so an unfamiliar block tag still pairs correctly;
# the list exists only so that a *never* closed tag is still reported as unclosed.
BLOCK_OPENERS = (
    "autoescape", "block", "call", "comment", "filter", "for", "if", "ifchanged",
    "macro", "raw", "spaceless", "verbatim", "with",
)

TEMPLATE_SUFFIXES = (".html", ".htm")

_OPENER = re.compile(r"\{[%{#]")
_STRAY = re.compile(r"%\}|\}\}|#\}")

# Quote-aware argument split: `{% include "a b.html" %}` is one argument, not two, and
# `key="a b"` stays in one piece rather than tearing at the space inside the quotes.
_ARGUMENT = re.compile(r"""(?:"[^"]*"|'[^']*'|[^\s"'])+""")

_EXPR_TOKEN = re.compile(
    r"""(?P<string>"[^"\n]*"|'[^'\n]*')
      | (?P<number>\d+(?:\.\d+)?)
      | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
      | (?P<operator>==|!=|<=|>=|[-+*/%<>=|.:,()\[\]!])
      | (?P<other>\S)""",
    re.X,
)


@dataclass(frozen=True)
class ExprToken:
    """One token inside a tag, with the whitespace on either side of it.

    Answers: *is this expression single-spaced, and are `.` and `|` tight?* The counts are
    of whitespace characters, so a token that follows a line break inside a tag spanning
    several lines reports that whitespace rather than pretending it was a space.
    """

    text: str
    kind: str  # string | number | name | operator | other
    lineno: int
    col: int
    space_before: int
    space_after: int

    @property
    def is_tight_operator(self) -> bool:
        """Whether this token is one that convention keeps flush against its neighbours."""
        return self.text in TIGHT_OPERATORS


@dataclass(frozen=True)
class TemplateNode:
    """One lexed construct: a block tag, a variable expression, a comment, or a text run.

    Answers: *what is at line N, and how is it written?* `raw` is the source text exactly
    as it appeared, delimiters included, so a rule can quote the offending text back.
    """

    kind: str  # block | variable | comment | text
    raw: str
    inner: str  # between the delimiters; "" for a text run
    lineno: int
    col: int
    end_lineno: int
    end_col: int
    line: str  # the whole source line the node starts on, for indentation questions
    tokens: tuple[ExprToken, ...] = ()

    @property
    def is_block(self) -> bool:
        return self.kind == "block"

    @property
    def is_variable(self) -> bool:
        return self.kind == "variable"

    @property
    def is_comment(self) -> bool:
        return self.kind == "comment"

    @property
    def is_text(self) -> bool:
        return self.kind == "text"

    @property
    def is_blank(self) -> bool:
        """A text run of nothing but whitespace -- what a rule about the *first* tag skips."""
        return self.is_text and not self.raw.strip()

    @property
    def open_delimiter(self) -> str:
        return "" if self.is_text else self.raw[:2]

    @property
    def close_delimiter(self) -> str:
        return "" if self.is_text else self.raw[-2:]

    @property
    def name(self) -> str:
        """The tag name -- the first word inside a block tag. `""` for anything else.

        Answers: *which tag is this?* -- `extends`, `load`, `block`, `endblock`, `if`.
        """
        if not self.is_block:
            return ""
        match = _ARGUMENT.search(self.inner)
        return match.group(0) if match else ""

    @property
    def args(self) -> tuple[str, ...]:
        """Everything after the tag name, split on whitespace but respecting quotes.

        Answers: *what arguments does this tag carry?* -- the list a rule checks for
        alphabetical order, and the place a closing tag repeats its block's name.
        """
        if not self.is_block:
            return ()
        return tuple(m.group(0) for m in _ARGUMENT.finditer(self.inner))[1:]

    @property
    def is_closing(self) -> bool:
        """Whether this is an `end...` tag rather than one that opens a body."""
        return (self.is_block and self.name.startswith(CLOSING_PREFIX)
                and len(self.name) > len(CLOSING_PREFIX))

    @property
    def closes(self) -> str:
        """The opener name this closing tag would match -- `endblock` closes `block`."""
        return self.name[len(CLOSING_PREFIX):] if self.is_closing else ""

    @property
    def leading_space(self) -> int:
        """Whitespace characters between the opening delimiter and the first token.

        Answers: *is there exactly one space inside `{%` / `{{`?* An all-whitespace tag
        reports its whole width here and in `trailing_space`, since there is no token to
        divide them.
        """
        return len(self.inner) - len(self.inner.lstrip()) if not self.is_text else 0

    @property
    def trailing_space(self) -> int:
        """Whitespace characters between the last token and the closing delimiter."""
        return len(self.inner) - len(self.inner.rstrip()) if not self.is_text else 0

    @property
    def spacing(self) -> tuple[int, int]:
        """`(leading, trailing)` inner whitespace, the pair a spacing rule compares to (1, 1)."""
        return (self.leading_space, self.trailing_space)

    @property
    def has_single_inner_spacing(self) -> bool:
        """Whether the tag is written `{% x %}` -- exactly one space inside each delimiter."""
        return not self.is_text and bool(self.inner.strip()) and self.spacing == (1, 1)

    @property
    def indent(self) -> str:
        """The leading whitespace of the line this node starts on.

        Answers: *how far is this tag indented?* -- the string itself, so a rule can tell
        four spaces from a tab.
        """
        return self.line[:len(self.line) - len(self.line.lstrip())]

    @property
    def indent_width(self) -> int:
        return len(self.indent)

    @property
    def starts_line(self) -> bool:
        """Whether nothing but whitespace precedes this node on its line."""
        return not self.line[:self.col].strip()

    @property
    def spans_lines(self) -> bool:
        """Whether the construct is broken across more than one line."""
        return self.end_lineno > self.lineno

    @property
    def span(self) -> tuple[int, int]:
        return (self.lineno, self.end_lineno)


@dataclass(frozen=True)
class TagPair:
    """An opening block tag and the closing tag that matched it, if one did.

    Answers: *where does this block end, is it closed on the same line, and does the
    closing tag repeat the block's name?*
    """

    opener: TemplateNode
    closer: Optional[TemplateNode] = None

    @property
    def name(self) -> str:
        return self.opener.name

    @property
    def label(self) -> str:
        """The opener's first argument -- the block's name, where the tag takes one."""
        return self.opener.args[0] if self.opener.args else ""

    @property
    def is_closed(self) -> bool:
        return self.closer is not None

    @property
    def same_line(self) -> bool:
        """Whether opener and closer sit on one line, e.g. `{% block t %}x{% endblock %}`."""
        return self.closer is not None and self.closer.lineno == self.opener.lineno

    @property
    def closer_repeats_name(self) -> bool:
        """Whether the closing tag carries an argument at all -- `{% endblock content %}`."""
        return self.closer is not None and bool(self.closer.args)

    @property
    def names_agree(self) -> bool:
        """Whether the name the closer repeats is in fact the opener's."""
        return (self.closer is not None and bool(self.closer.args)
                and bool(self.label) and self.closer.args[0] == self.label)

    @property
    def span(self) -> tuple[int, int]:
        return (self.opener.lineno, self.closer.lineno if self.closer else self.opener.lineno)


@dataclass(frozen=True)
class Malformed:
    """A delimiter that does not pair up.

    Answers: *what could not be lexed, and on which line?* `reason` is `unterminated` for
    an opener with no closer, `stray` for a closer with no opener.
    """

    reason: str
    delimiter: str
    lineno: int
    col: int
    line: str


@dataclass(frozen=True)
class _Positions:
    """Offset -> (line, column) for one source string."""

    source: str
    starts: tuple[int, ...] = field(default_factory=tuple)
    lines: tuple[str, ...] = field(default_factory=tuple)

    def at(self, offset: int) -> tuple[int, int]:
        index = max(bisect.bisect_right(self.starts, offset) - 1, 0)
        return (index + 1, offset - self.starts[index])

    def line_of(self, offset: int) -> str:
        index = max(bisect.bisect_right(self.starts, offset) - 1, 0)
        return self.lines[index] if index < len(self.lines) else ""


def _positions(source: str) -> _Positions:
    starts = [0]
    for index, char in enumerate(source):
        if char == "\n":
            starts.append(index + 1)
    return _Positions(source, tuple(starts), tuple(source.split("\n")))


def _expression_tokens(inner: str, inner_offset: int, pos: _Positions) -> tuple[ExprToken, ...]:
    matches = list(_EXPR_TOKEN.finditer(inner))
    if not matches:
        return ()
    gaps = []
    previous_end = 0
    for match in matches:
        gaps.append(match.start() - previous_end)
        previous_end = match.end()
    after = list(gaps[1:]) + [len(inner) - len(inner.rstrip())]
    out = []
    for match, before, behind in zip(matches, gaps, after):
        lineno, col = pos.at(inner_offset + match.start())
        out.append(ExprToken(
            text=match.group(0),
            kind=match.lastgroup or "other",
            lineno=lineno,
            col=col,
            space_before=before,
            space_after=behind,
        ))
    return tuple(out)


def _node(kind: str, source: str, start: int, end: int, pos: _Positions) -> TemplateNode:
    raw = source[start:end]
    lineno, col = pos.at(start)
    end_lineno, end_col = pos.at(max(end - 1, start))
    inner = "" if kind == "text" else raw[2:-2]
    tokens: tuple[ExprToken, ...] = ()
    if kind in ("block", "variable"):
        tokens = _expression_tokens(inner, start + 2, pos)
    return TemplateNode(
        kind=kind,
        raw=raw,
        inner=inner,
        lineno=lineno,
        col=col,
        end_lineno=end_lineno,
        end_col=end_col + 1,
        line=pos.line_of(start),
        tokens=tokens,
    )


def _scan(source: Optional[str]) -> tuple[list[TemplateNode], list[Malformed]]:
    """The single pass both public entry points share."""
    if not source:
        return ([], [])
    pos = _positions(source)
    nodes: list[TemplateNode] = []
    broken: list[Malformed] = []
    index = 0
    text_start = 0

    def flush(until: int) -> None:
        if until > text_start:
            nodes.append(_node("text", source, text_start, until, pos))

    while index < len(source):
        match = _OPENER.search(source, index)
        if match is None:
            break
        opener = source[match.start():match.start() + 2]
        closer = DELIMITERS[opener]
        close_at = source.find(closer, match.start() + 2)
        next_open = source.find(opener, match.start() + 2)
        if close_at == -1 or (next_open != -1 and next_open < close_at):
            # Either no closer at all, or another opener of the same kind arrives first --
            # which means this one opened nothing. Leave the two characters in the
            # surrounding text and carry on from just after them, so a stray `{{` in prose
            # does not swallow every tag below it.
            lineno, col = pos.at(match.start())
            broken.append(Malformed("unterminated", opener, lineno, col,
                                    pos.line_of(match.start())))
            index = match.start() + 2
            continue
        flush(match.start())
        end = close_at + len(closer)
        nodes.append(_node(KINDS[opener], source, match.start(), end, pos))
        index = text_start = end
    flush(len(source))

    for node in nodes:
        if not node.is_text:
            continue
        offset = _offset_of(node, pos)
        for stray in _STRAY.finditer(node.raw):
            lineno, col = pos.at(offset + stray.start())
            broken.append(Malformed("stray", stray.group(0), lineno, col,
                                    pos.line_of(offset + stray.start())))
    broken.sort(key=lambda item: (item.lineno, item.col))
    return (nodes, broken)


def _offset_of(node: TemplateNode, pos: _Positions) -> int:
    return pos.starts[node.lineno - 1] + node.col


def tokenize(source: Optional[str]) -> list[TemplateNode]:
    """Every construct in the template, in source order, with line and column on each.

    Answers: *what is in this file, and where?* Block tags, variable expressions, comments
    and the text between them, including whitespace-only runs -- a rule that asks what
    comes first needs to see what it is skipping. `None` and `""` give an empty list.
    """
    return _scan(source)[0]


def malformed_delimiters(source: Optional[str]) -> list[Malformed]:
    """Delimiters that do not pair up, in line order.

    Answers: *is the file lexically broken, and where?* `unterminated` is an opening `{%`,
    `{{` or `{#` with no closer before the next opener of its kind (or before the end of
    the file); `stray` is a `%}`, `}}` or `#}` sitting in text with no opener before it.
    Tokenising is unaffected: this is a separate question, not an error.
    """
    return _scan(source)[1]


def block_tags(nodes: Sequence[TemplateNode]) -> list[TemplateNode]:
    """Only the `{% ... %}` nodes. Answers: *which tags does this file use?*"""
    return [node for node in nodes if node.is_block]


def variable_expressions(nodes: Sequence[TemplateNode]) -> list[TemplateNode]:
    """Only the `{{ ... }}` nodes. Answers: *what does this file interpolate?*"""
    return [node for node in nodes if node.is_variable]


def comment_nodes(nodes: Sequence[TemplateNode]) -> list[TemplateNode]:
    """Only the `{# ... #}` nodes. Answers: *where are the template comments?*"""
    return [node for node in nodes if node.is_comment]


def tags_named(nodes: Sequence[TemplateNode], *names: str) -> list[TemplateNode]:
    """Block tags whose name is one of `names`.

    Answers: *where are the `load` tags?* -- the lookup nearly every tag rule starts from.
    """
    wanted = set(names)
    return [node for node in nodes if node.is_block and node.name in wanted]


def first_significant(nodes: Sequence[TemplateNode]) -> Optional[TemplateNode]:
    """The first node that is neither a comment nor whitespace.

    Answers: *what does this file really begin with?* -- so a rule requiring the extends
    tag to come first is not defeated by a licence comment above it.
    """
    for node in nodes:
        if node.is_comment or node.is_blank:
            continue
        return node
    return None


def is_first_significant(nodes: Sequence[TemplateNode], node: TemplateNode) -> bool:
    """Whether `node` is that first non-comment, non-whitespace construct.

    Answers: *is this tag the first thing in the file?*
    """
    first = first_significant(nodes)
    return first is not None and (first.lineno, first.col) == (node.lineno, node.col)


def _pair(nodes: Sequence[TemplateNode]) -> tuple[list[TagPair], list[TemplateNode]]:
    tags = block_tags(nodes)
    openers = {tag.closes for tag in tags if tag.is_closing}
    openers |= set(BLOCK_OPENERS)
    pairs: list[TagPair] = []
    orphans: list[TemplateNode] = []
    stack: list[TemplateNode] = []
    for tag in tags:
        if tag.is_closing:
            for position in range(len(stack) - 1, -1, -1):
                if stack[position].name == tag.closes:
                    pairs.append(TagPair(stack.pop(position), tag))
                    break
            else:
                orphans.append(tag)
        elif tag.name in openers:
            stack.append(tag)
    pairs.extend(TagPair(tag, None) for tag in stack)
    pairs.sort(key=lambda pair: (pair.opener.lineno, pair.opener.col))
    return (pairs, orphans)


def tag_pairs(nodes: Sequence[TemplateNode]) -> list[TagPair]:
    """Block openers matched to their closing tags, in the order the openers appear.

    Answers: *which `{% block %}` does this `{% endblock %}` close, are they on the same
    line, and is the block left open?* An opener whose closer is missing is returned with
    `closer=None` rather than dropped -- an unclosed block is exactly what a rule wants to
    hear about. Nesting is handled by matching each closer to the innermost open tag of
    the right name, so an intervening tag that opens nothing does not break the pairing.
    """
    return _pair(nodes)[0]


def unmatched_closers(nodes: Sequence[TemplateNode]) -> list[TemplateNode]:
    """Closing tags with no opener before them. Answers: *is there a stray `{% endif %}`?*"""
    return _pair(nodes)[1]


def expression_tokens(node: TemplateNode) -> tuple[ExprToken, ...]:
    """The tokens inside a tag, each carrying the whitespace before and after it.

    Answers: *is this expression spaced correctly?* Compare `space_before`/`space_after`
    against 1 for ordinary tokens, and against 0 on both sides of a token for which
    `is_tight_operator` holds -- and on the neighbours facing it.
    """
    return node.tokens


def unquote(text: str) -> str:
    """`"base.html"` -> `base.html`. Answers: *what does this argument actually name?*"""
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


def is_alphabetical(values: Sequence[str], fold_case: bool = True) -> bool:
    """Whether the values are already in alphabetical order.

    Answers: *are the arguments of a tag that takes several names sorted?* Quotes are
    stripped first, so `"b"` after `a` is judged on the letters and not on the quote mark.
    """
    keys = [unquote(value) for value in values]
    if fold_case:
        keys = [key.lower() for key in keys]
    return keys == sorted(keys)


def is_template_path(path: str) -> bool:
    """Whether the path looks like a template file, by suffix alone."""
    return path.endswith(TEMPLATE_SUFFIXES)

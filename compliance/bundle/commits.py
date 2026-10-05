"""``===LOG===`` -> [Commit].

The primary path parses ``git log --pretty=raw --stat``, which is what
``/opt/collect.sh`` emits. That format carries the full message -- body, blank lines and
trailers intact -- and survives ``-F``, heredocs, ``--amend`` and multiple commits, none
of which a scrape of the command log can handle.

The scrape exists anyway, at the bottom of this module, because the two pilot
trajectories predate the collect script. It is a fixture shim, not a fallback strategy.
"""

from __future__ import annotations

import logging
import re

from compliance.core.models import Command, Commit

logger = logging.getLogger("compliance.bundle.commits")

_COMMIT = re.compile(r"^commit ([0-9a-f]{7,40})\s*$")
_IDENT = re.compile(r"^(author|committer) (?P<name>.*?) <(?P<email>[^>]*)> \d+ [+-]\d{4}\s*$")
_TRAILER = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9-]*): (?P<value>.*)$")
_MSG_INDENT = "    "


def parse_log(text: str, branch: str | None = None) -> tuple[Commit, ...]:
    """Parse a ``git log --pretty=raw [--stat]`` block into commits, newest first."""
    commits: list[Commit] = []
    for block in _split_blocks(text or ""):
        if commit := _parse_block(block, branch):
            commits.append(commit)
    return tuple(commits)


def _split_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] | None = None
    for line in text.splitlines():
        if _COMMIT.match(line):
            if current is not None:
                blocks.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
    if current is not None:
        blocks.append(current)
    return blocks


def _parse_block(lines: list[str], branch: str | None) -> Commit | None:
    sha = ""
    author_name = author_email = ""
    index = 0
    for index, line in enumerate(lines):
        if match := _COMMIT.match(line):
            sha = match.group(1)
            continue
        if not line.strip():
            index += 1
            break
        if (match := _IDENT.match(line)) and match.group(1) == "author":
            author_name, author_email = match.group("name"), match.group("email")
    if not sha:
        return None

    message_lines = _take_message(lines[index:])
    return build_commit(sha, message_lines, author_name, author_email, "\n".join(lines), branch)


def _take_message(lines: list[str]) -> list[str]:
    """Message lines are indented four spaces; the --stat block that follows is not.

    Blank lines are ambiguous -- they occur inside messages and before the stat -- so
    they are held back and only committed once another indented line proves the message
    is still going.
    """
    message: list[str] = []
    pending_blanks: list[str] = []
    for line in lines:
        if not line.strip():
            pending_blanks.append("")
            continue
        if line.startswith(_MSG_INDENT):
            message.extend(pending_blanks)
            pending_blanks = []
            message.append(line[len(_MSG_INDENT) :])
            continue
        break  # a non-indented, non-blank line: the stat block has started
    return message


def build_commit(
    sha: str,
    message_lines: list[str],
    author_name: str = "",
    author_email: str = "",
    raw: str = "",
    branch: str | None = None,
) -> Commit:
    """Assemble a Commit from message lines. Shared by the log parser and the shim."""
    message_lines = list(message_lines)
    while message_lines and not message_lines[-1].strip():
        message_lines.pop()

    summary = message_lines[0] if message_lines else ""
    rest = message_lines[1:]
    body_lines = rest[1:] if rest and not rest[0].strip() else rest

    trailer_lines = _trailing_trailers(body_lines)
    trailers: dict[str, str] = {}
    for line in trailer_lines:
        if match := _TRAILER.match(line):
            trailers[match.group("key")] = match.group("value")

    return Commit(
        sha=sha,
        summary=summary,
        body="\n".join(body_lines),
        trailers=trailers,
        author_name=author_name,
        author_email=author_email,
        raw=raw or "\n".join(message_lines),
        message_lines=tuple(message_lines),
        body_lines=tuple(body_lines),
        trailer_lines=tuple(trailer_lines),
        branch=branch,
    )


def _trailing_trailers(body_lines: list[str]) -> list[str]:
    """Trailers are the final run of ``Key: value`` lines in the message."""
    trailers: list[str] = []
    for line in reversed(body_lines):
        if not line.strip():
            break
        if _TRAILER.match(line):
            trailers.insert(0, line)
        else:
            break
    return trailers


# --- TEMPORARY: pre-Phase-0 fixture shim -------------------------------------------
# The two stored trajectories were produced before /opt/collect.sh existed, so their
# submissions carry no ===LOG=== section at all. This scrapes `git commit -m "..."` out
# of the command log so Phase 1 is not blocked on re-running them.
#
# It is wrong in ways the real parser is not: no sha, no author identity, no branch, and
# it cannot see -F, heredoc, --amend or --file messages. Rules that need what it cannot
# supply must return Undetermined, never a verdict. Delete this once every fixture has a
# ===LOG=== section.

_COMMIT_DASH_M = re.compile(
    r"""\bgit\s+commit\b[^\n]*?\s-m\s*(?P<q>["'])(?P<msg>.*?)(?<!\\)(?P=q)""",
    re.DOTALL,
)
_SUPPRESSED = re.compile(r"\bgit\s+commit\b(?![^\n]*\s-m\s)")


def scrape_commits_from_commands(commands: tuple[Command, ...]) -> tuple[Commit, ...]:
    """TEMPORARY: pre-Phase-0 fixture shim. See the module note above."""
    commits: list[Commit] = []
    missed = 0
    for command in commands:
        matched = False
        for match in _COMMIT_DASH_M.finditer(command.command):
            matched = True
            message = match.group("msg").replace("\\n", "\n").replace('\\"', '"')
            commits.append(build_commit("", message.split("\n"), raw=command.command))
        if not matched and _SUPPRESSED.search(command.command):
            missed += 1

    if commits or missed:
        logger.warning(
            "TEMPORARY pre-Phase-0 fixture shim fired: scraped %d commit message(s) from the "
            "command log because the submission had no ===LOG=== section. Commit sha, author "
            "identity and branch are unavailable, and %d `git commit` invocation(s) without a "
            "-m message could not be read at all. Re-run this instance to get real evidence.",
            len(commits),
            missed,
        )
    return tuple(commits)

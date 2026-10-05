"""SymPy: Git and commit conventions -- 14 rules.

Layer C. Every rule here is two layers (docs/checker-authoring.md §2): ``precondition``
selects on the rule's ANTECEDENT, ``pass_condition`` grades. Where a rule reads
"when X, do Y", the pre-condition fires on X. Firing on Y would let an agent that did
nothing escape as ``not_applicable`` -- the single easiest thing to get wrong (§4.2).

Rules that need evidence this harness may not carry -- the branch a commit was made on,
for instance -- return ``Undetermined`` rather than guessing. That keeps a missing probe
from being recorded as a violation.
"""

from __future__ import annotations

import re

from compliance.core.models import (
    Command,
    Commit,
    EvidenceBundle,
    Satisfied,
    Target,
    Undetermined,
    Violated,
)
from compliance.core.registry import rule

CATEGORY = "Git and commit conventions"

SUMMARY_LIMIT = 71
BODY_LIMIT = 78
MASTER_BRANCHES = {"master", "main"}

# Editor config, build junk and scratch files that must not reach a contribution (C021).
JUNK_PATTERNS = (
    re.compile(r"(^|/)\.vscode/"),
    re.compile(r"(^|/)\.idea/"),
    re.compile(r"(^|/)\.DS_Store$"),
    re.compile(r"(^|/)Thumbs\.db$"),
    re.compile(r"\.sw[op]$"),
    re.compile(r"~$"),
    re.compile(r"\.(orig|rej|bak|tmp|log)$"),
    re.compile(r"\.py[co]$"),
    re.compile(r"(^|/)__pycache__/"),
    re.compile(r"(^|/)patch\.txt$"),
    re.compile(r"(^|/)\.env$"),
)

_BRANCH_CREATE = re.compile(r"\bgit\s+(?:checkout\s+-b|switch\s+(?:-c|--create))\s+\S+")
_GIT_ON_MASTER_VERBS = re.compile(r"\bgit\s+(merge|add|commit|rebase)\b")
_MAILMAP_CHECK = re.compile(r"bin/mailmap_check\.py")
_MAILMAP_OK = "No changes needed in .mailmap"
_GIT_ADD_MAILMAP = re.compile(r"\bgit\s+add\b[^\n]*\.mailmap\b")
_COAUTHOR_HINT = re.compile(r"co[-\s]?author", re.IGNORECASE)
_COAUTHOR_EXACT = re.compile(r"^Co-authored-by: .+ <[^@<>\s]+@[^@<>\s]+>$")
_SENTENCE_END = re.compile(r"[.!?][\"')\]]*$")


def _commit_targets(bundle: EvidenceBundle) -> list[Target]:
    """Antecedent shared by the commit-message rules: the agent made a commit."""
    return [
        Target(
            key=f"commit:{commit.sha or index}",
            file=None,
            line_span=None,
            source="commit",
            payload=commit,
            snippet=commit.summary,
        )
        for index, commit in enumerate(bundle.commits)
    ]


def _agent_changed_code(bundle: EvidenceBundle) -> bool:
    return bool(bundle.files) or bool(bundle.commits)


def _branch_of(commit: Commit, bundle: EvidenceBundle) -> str | None:
    return commit.branch if commit.branch is not None else None


def _shim_note(bundle: EvidenceBundle) -> str:
    if bundle.commits_source == "trajectory_shim":
        return "commit metadata came from the pre-Phase-0 fixture shim, which records no branch"
    return "the harness recorded no branch for this commit"


# --- workflow ----------------------------------------------------------------------


@rule(id="SYMPY-C012", category=CATEGORY, ownership="created", reads=("commands", "files", "commits"))
class CreatesContributionBranch:
    """Pre-condition: the agent changed code at all.
    Pass condition: it created a contribution branch before doing so."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        if not _agent_changed_code(bundle):
            return []
        return [
            Target(
                key=f"run:{bundle.instance_id}",
                file=None,
                line_span=None,
                source="trajectory",
                payload=bundle,
                snippet="contribution made",
            )
        ]

    def pass_condition(self, target: Target):
        bundle: EvidenceBundle = target.payload
        for command in bundle.commands:
            if _BRANCH_CREATE.search(command.command):
                return Satisfied(f"created a branch: {command.command.strip()[:80]}")
        return Violated("no `git checkout -b` / `git switch -c` in the command log")


@rule(id="SYMPY-C013", category=CATEGORY, ownership="created", reads=("commits", "branch"))
class NoCommitToMaster:
    """Pre-condition: the agent made a commit.
    Pass condition: that commit was not made on master."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        return _commit_targets(bundle)

    def pass_condition(self, target: Target):
        commit: Commit = target.payload
        if commit.branch is None:
            return Undetermined("parse_error", "branch unknown for this commit")
        if commit.branch.lower() in MASTER_BRANCHES:
            return Violated(f"committed on {commit.branch}")
        return Satisfied(f"committed on {commit.branch}")


@rule(id="SYMPY-C014", category=CATEGORY, ownership="created", reads=("commands", "probe"))
class NoGitVerbsOnMaster:
    """Pre-condition: the agent ran git merge, add, commit or rebase.
    Pass condition: it was not on master when it did."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        branch = bundle.probe.get("start_branch") or ""
        targets = []
        for command in bundle.commands:
            if match := _GIT_ON_MASTER_VERBS.search(command.command):
                targets.append(
                    Target(
                        key=f"command:{command.index}:{match.group(1)}",
                        file=None,
                        line_span=None,
                        source="trajectory",
                        payload=(command, branch, bundle),
                        snippet=command.command.strip()[:120],
                    )
                )
        return targets

    def pass_condition(self, target: Target):
        command, start_branch, bundle = target.payload
        branch = _branch_at(bundle, command, start_branch)
        if branch is None:
            return Undetermined("parse_error", "branch at time of command unknown")
        if branch.lower() in MASTER_BRANCHES:
            return Violated(f"ran `{command.command.strip()[:60]}` while on {branch}")
        return Satisfied(f"on {branch}")


def _branch_at(bundle: EvidenceBundle, command: Command, start_branch: str) -> str | None:
    """Branch in effect when ``command`` ran: the start branch until a create/switch."""
    if not start_branch or start_branch in ("(detached)", "HEAD"):
        return None
    current = start_branch
    for earlier in bundle.commands:
        if earlier.index >= command.index:
            break
        if match := _BRANCH_CREATE.search(earlier.command):
            current = match.group(0).split()[-1]
    return current


# --- commit message ----------------------------------------------------------------


@rule(id="SYMPY-C021", category=CATEGORY, ownership="touched", reads=("files",))
class NoJunkFiles:
    """Pre-condition: each file the contribution touches.
    Pass condition: it is not an editor-config, binary or temporary junk file."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        return [
            Target(
                key=f"file:{path}",
                file=path,
                line_span=None,
                source="patch",
                payload=bundle.files[path],
                snippet=path,
            )
            for path in sorted(bundle.files)
        ]

    def pass_condition(self, target: Target):
        change = target.payload
        for pattern in JUNK_PATTERNS:
            if pattern.search(change.path):
                return Violated(f"junk file in the contribution: {change.path}")
        if change.is_binary:
            return Violated(f"binary file in the contribution: {change.path}")
        return Satisfied()


@rule(id="SYMPY-C023", category=CATEGORY, ownership="created", reads=("commits",))
class SummaryLength:
    """Pre-condition: every commit the agent made.
    Pass condition: its summary line is at most 71 characters."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        return _commit_targets(bundle)

    def pass_condition(self, target: Target):
        summary = target.payload.summary
        if len(summary) > SUMMARY_LIMIT:
            return Violated(f"summary is {len(summary)} chars, limit {SUMMARY_LIMIT}")
        return Satisfied()


@rule(id="SYMPY-C024", category=CATEGORY, ownership="created", reads=("commits",))
class BodyLineLength:
    """Pre-condition: every body line of every commit -- a commit with no body has none.
    Pass condition: the line is at most 78 characters."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for index, commit in enumerate(bundle.commits):
            for offset, line in enumerate(commit.body_lines):
                targets.append(
                    Target(
                        key=f"commit:{commit.sha or index}:body:{offset}",
                        file=None,
                        line_span=None,
                        source="commit",
                        payload=line,
                        snippet=line[:120],
                    )
                )
        return targets

    def pass_condition(self, target: Target):
        line: str = target.payload
        if len(line) > BODY_LIMIT:
            return Violated(f"body line is {len(line)} chars, limit {BODY_LIMIT}")
        return Satisfied()


@rule(id="SYMPY-C025", category=CATEGORY, ownership="created", reads=("commits",))
class BlankLineAfterSummary:
    """Pre-condition: every commit that has anything after its summary line.
    Pass condition: a blank line separates the summary from it."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        return [
            Target(
                key=f"commit:{commit.sha or index}",
                file=None,
                line_span=None,
                source="commit",
                payload=commit,
                snippet=commit.summary,
            )
            for index, commit in enumerate(bundle.commits)
            if len(commit.message_lines) > 1
        ]

    def pass_condition(self, target: Target):
        commit: Commit = target.payload
        if commit.message_lines[1].strip():
            return Violated("no blank line between summary and body")
        return Satisfied()


@rule(id="SYMPY-C026", category=CATEGORY, ownership="created", reads=("commits",))
class SummaryNoTrailingPeriod:
    """Pre-condition: every commit the agent made.
    Pass condition: its summary does not end with a period."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        return _commit_targets(bundle)

    def pass_condition(self, target: Target):
        summary = target.payload.summary.rstrip()
        if summary.endswith("."):
            return Violated("summary ends with a period")
        return Satisfied()


@rule(id="SYMPY-C030", category=CATEGORY, ownership="created", heuristic=True, reads=("commits",))
class BodyCompleteSentences:
    """Pre-condition: every commit that has a body.
    Pass condition: the body reads as complete sentences.

    Lexical heuristic, not a decidable check: flagged so the report can caveat it.
    """

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for index, commit in enumerate(bundle.commits):
            prose = [line for line in commit.body_lines if line not in commit.trailer_lines]
            if any(line.strip() for line in prose):
                targets.append(
                    Target(
                        key=f"commit:{commit.sha or index}:body",
                        file=None,
                        line_span=None,
                        source="commit",
                        payload=prose,
                        snippet="\n".join(prose)[:200],
                    )
                )
        return targets

    def pass_condition(self, target: Target):
        prose = [line.strip() for line in target.payload if line.strip()]
        text = " ".join(prose)
        if not _SENTENCE_END.search(text):
            return Violated("body does not end with terminal punctuation")
        first = prose[0]
        if first[:1].islower():
            return Violated(f"body starts lowercase: {first[:40]!r}")
        return Satisfied()


@rule(id="SYMPY-C034", category=CATEGORY, ownership="created", reads=("commits",))
class CoAuthorTrailerForm:
    """Pre-condition: every commit-message line that credits a co-author.
    Pass condition: it is exactly `Co-authored-by: <name> <email>`, at the bottom."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for index, commit in enumerate(bundle.commits):
            for offset, line in enumerate(commit.message_lines):
                if _COAUTHOR_HINT.search(line):
                    targets.append(
                        Target(
                            key=f"commit:{commit.sha or index}:coauthor:{offset}",
                            file=None,
                            line_span=None,
                            source="commit",
                            payload=(line, commit),
                            snippet=line[:120],
                        )
                    )
        return targets

    def pass_condition(self, target: Target):
        line, commit = target.payload
        if not _COAUTHOR_EXACT.match(line.strip()):
            return Violated(f"co-author credit not in the exact trailer form: {line.strip()[:60]!r}")
        if line not in commit.trailer_lines:
            return Violated("co-author trailer is not in the trailer block at the bottom")
        return Satisfied()


# --- AUTHORS / .mailmap ------------------------------------------------------------


@rule(id="SYMPY-C040", category=CATEGORY, ownership="touched", reads=("files",))
class DoNotEditAuthors:
    """Pre-condition: each file the contribution touches.
    Pass condition: it is not `AUTHORS`, which must be changed via `.mailmap` instead."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        return [
            Target(
                key=f"file:{path}",
                file=path,
                line_span=None,
                source="patch",
                payload=path,
                snippet=path,
            )
            for path in sorted(bundle.files)
        ]

    def pass_condition(self, target: Target):
        path: str = target.payload
        if path.split("/")[-1] == "AUTHORS":
            return Violated("edited AUTHORS directly; identity changes belong in .mailmap")
        return Satisfied()


@rule(id="SYMPY-C041", category=CATEGORY, ownership="touched", reads=("files", "commits"))
class MailmapMatchesCommitIdentity:
    """Pre-condition: every `.mailmap` line the agent added.
    Pass condition: its source identity matches the name and email in the commit metadata."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        targets = []
        for path, change in sorted(bundle.files.items()):
            if path.split("/")[-1] != ".mailmap":
                continue
            for lineno, text in change.added_lines:
                if text.strip() and not text.lstrip().startswith("#"):
                    targets.append(
                        Target(
                            key=f"mailmap:{path}:{lineno}",
                            file=path,
                            line_span=(lineno, lineno),
                            source="patch",
                            payload=(text, bundle),
                            snippet=text[:120],
                        )
                    )
        return targets

    def pass_condition(self, target: Target):
        text, bundle = target.payload
        identities = {
            (commit.author_name, commit.author_email)
            for commit in bundle.commits
            if commit.author_name or commit.author_email
        }
        if not identities:
            return Undetermined("parse_error", "no commit author identity in the bundle")
        emails = re.findall(r"<([^>]*)>", text)
        if not emails:
            return Violated(f"mailmap entry has no <email>: {text.strip()[:60]!r}")
        source_email = emails[-1]
        if any(source_email == email for _, email in identities):
            return Satisfied()
        return Violated(
            f"mailmap source email {source_email!r} matches no commit author "
            f"({sorted(e for _, e in identities)})"
        )


@rule(id="SYMPY-C042", category=CATEGORY, ownership="touched", reads=("files", "commands"))
class RunMailmapCheck:
    """Pre-condition: the agent edited `.mailmap`.
    Pass condition: it ran `bin/mailmap_check.py` until it reported no changes needed."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        edited = [p for p in sorted(bundle.files) if p.split("/")[-1] == ".mailmap"]
        if not edited:
            return []
        return [
            Target(
                key=f"mailmap-edit:{edited[0]}",
                file=edited[0],
                line_span=None,
                source="patch",
                payload=bundle,
                snippet=", ".join(edited),
            )
        ]

    def pass_condition(self, target: Target):
        bundle: EvidenceBundle = target.payload
        ran = [c for c in bundle.commands if _MAILMAP_CHECK.search(c.command)]
        if not ran:
            return Violated("edited .mailmap but never ran bin/mailmap_check.py")
        if any(_MAILMAP_OK in c.output for c in ran):
            return Satisfied()
        return Violated(
            f"ran bin/mailmap_check.py {len(ran)} time(s) but it never reported {_MAILMAP_OK!r}"
        )


@rule(id="SYMPY-C043", category=CATEGORY, ownership="touched", reads=("commands", "commits"))
class CommitMailmapAfterCheck:
    """Pre-condition: `bin/mailmap_check.py` reported no changes needed.
    Pass condition: `.mailmap` was then staged and committed with an `author: add ...` message."""

    def precondition(self, bundle: EvidenceBundle) -> list[Target]:
        return [
            Target(
                key=f"mailmap-check-ok:{command.index}",
                file=None,
                line_span=None,
                source="trajectory",
                payload=(command, bundle),
                snippet=command.command.strip()[:120],
            )
            for command in bundle.commands
            if _MAILMAP_CHECK.search(command.command) and _MAILMAP_OK in command.output
        ]

    def pass_condition(self, target: Target):
        command, bundle = target.payload
        later = [c for c in bundle.commands if c.index > command.index]
        if not any(_GIT_ADD_MAILMAP.search(c.command) for c in later):
            return Violated("no `git add .mailmap` after mailmap_check reported success")
        for commit in bundle.commits:
            if re.match(r"^author: add .+ to \.mailmap$", commit.summary.strip()):
                return Satisfied()
        return Violated("no commit with an `author: add <name> to .mailmap` summary")

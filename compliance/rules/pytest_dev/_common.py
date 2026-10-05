"""pytest-dev: helpers shared across the rule modules. Not a rule module.

Layer C, and deliberately thin. Anything a second project would want belongs in
`compliance/extractors/`; what is left is pytest's own vocabulary -- where its tests,
documentation and changelog live -- which `docs/checker-authoring.md` §3 keeps local.

**pytest does not put its tests under `tests/`.** They live in `testing/`, so
`python_ast.is_test_path` is not the authority here; `is_test_path` below is.
"""

from __future__ import annotations

import re
from typing import Optional

from compliance.core import ownership as own
from compliance.core.models import Command, EvidenceBundle, Target

TEST_ROOTS = ("testing/",)
SOURCE_ROOTS = ("src/",)
DOC_ROOT = "doc/en/"
CHANGELOG_ROOT = "changelog/"

#: The ten entry types published in pyproject.toml and enforced by the changelogs-rst hook.
CHANGELOG_TYPES = ("feature", "improvement", "bugfix", "doc", "deprecation", "breaking",
                   "vendor", "packaging", "contrib", "misc")
#: `2574.bugfix.rst` -- issue id, type, extension.
CHANGELOG_NAME = re.compile(r"^(?P<issue>\d+)\.(?P<type>[a-z]+)\.rst$")

#: `PytestRemovedIn9Warning`. The release machinery filters on this exact form.
REMOVED_IN_WARNING = re.compile(r"\bPytestRemovedIn(\d+)Warning\b")
DEPRECATION_MARK = re.compile(
    r"\.\.\s+deprecated::|@deprecated\b|warnings\.warn\([^)]*[Dd]eprecat", re.S)

#: GitHub's autoclose keywords. The rule names `closes #XYZW`; the linked GitHub docs fix
#: the family, so the sibling keywords are accepted rather than reported as violations.
CLOSES = re.compile(r"\b(clos(e|es|ed)|fix(e[sd])?|resolv(e|es|ed))\s+#\d+\b", re.I)


def is_test_path(path: str) -> bool:
    return path.startswith(TEST_ROOTS)


def target(key: str, path: Optional[str] = None,
           span: Optional[tuple[int, int]] = None,
           payload=None, snippet: str = "", source: str = "patch") -> Target:
    return Target(key=key, file=path, line_span=span, source=source,
                  payload=payload, snippet=snippet[:200])


def ran(bundle: EvidenceBundle, pattern: re.Pattern) -> list[Command]:
    return [c for c in bundle.commands if pattern.search(c.command)]


def contribution_target(bundle: EvidenceBundle, prefix: str,
                        snippet: str = "") -> list[Target]:
    """The antecedent shared by rules about the contribution as a whole.

    Fires on having submitted something, never on having run the tool the rule is about
    (§7.1) -- triggering on the tool lets a contribution that checked nothing collect
    ``not_applicable``.
    """
    if not bundle.files:
        return []
    return [target(f"{prefix}:{bundle.instance_id}", None, None, bundle,
                   snippet or f"{len(bundle.files)} file(s) in the contribution")]


def python_files(bundle: EvidenceBundle, *, mode: str = "touched",
                 tests: Optional[bool] = None) -> list[str]:
    out = []
    for path in sorted(bundle.files):
        if not path.endswith(".py") or not own.owns_file(bundle, path, mode):
            continue
        if tests is not None and is_test_path(path) is not tests:
            continue
        out.append(path)
    return out


def changed_under(bundle: EvidenceBundle, prefix: str,
                  suffixes: tuple[str, ...] = ()) -> list[str]:
    return [p for p in sorted(bundle.files)
            if p.startswith(prefix) and (not suffixes or p.endswith(suffixes))]


def changelog_entries(bundle: EvidenceBundle, *, created_only: bool = True) -> list[str]:
    mode = "created" if created_only else "touched"
    return [p for p in changed_under(bundle, CHANGELOG_ROOT, (".rst",))
            if own.owns_file(bundle, p, mode)]


def entry_type(path: str) -> Optional[str]:
    match = CHANGELOG_NAME.match(path[len(CHANGELOG_ROOT):])
    return match.group("type") if match else None


def has_breaking_entry(bundle: EvidenceBundle) -> list[str]:
    """A breaking change, declared by the project's own changelog type rather than guessed."""
    return [p for p in changelog_entries(bundle, created_only=False)
            if entry_type(p) == "breaking"]


def added_text(bundle: EvidenceBundle, path: str) -> str:
    change = bundle.files.get(path)
    if change is None:
        return ""
    return "\n".join(text for _, text in change.added_lines)

"""pydata (xarray): helpers shared across the rule modules. Not a rule module.

Layer C, and deliberately thin. Anything a second project would want belongs in
`compliance/extractors/`; what is left is xarray's own vocabulary -- where its package,
tests and documentation live -- which `docs/checker-authoring.md` §3 keeps local.
"""

from __future__ import annotations

import re
from typing import Optional

from compliance.core import ownership as own
from compliance.core.models import Command, EvidenceBundle, Target

PACKAGE = "xarray/"
TEST_ROOTS = ("xarray/tests/",)
DOC_ROOT = "doc/"
WHATS_NEW = "doc/whats-new.rst"
API_DOC = "doc/api.rst"
DOC_SUFFIXES = (".rst", ".md")
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".svg", ".gif")

#: xarray writes issue references two ways, both named in the contributing guide.
ISSUE_REF = re.compile(r"\bGH\d+\b|(?<![\w:])#\d+\b")
#: Commit-message tags that steer CI, matched on the first line only.
TEST_UPSTREAM = re.compile(r"\[\s*test-upstream\s*\]", re.I)
SKIP_CI = re.compile(r"\[\s*skip[-\s]?ci\s*\]", re.I)


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
    """The antecedent shared by whole-contribution rules (spec §4.4).

    Fires on having submitted something, never on having run the tool the rule is about
    (§7.1). One target, payload the bundle, ownership ``touched``.
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


def documentation_files(bundle: EvidenceBundle) -> list[str]:
    return [p for p in changed_under(bundle, DOC_ROOT) if p.endswith(DOC_SUFFIXES)]


def added_text(bundle: EvidenceBundle, path: str) -> str:
    change = bundle.files.get(path)
    if change is None:
        return ""
    return "\n".join(text for _, text in change.added_lines)


def added_lines(bundle: EvidenceBundle, path: str) -> tuple[tuple[int, str], ...]:
    change = bundle.files.get(path)
    return change.added_lines if change else ()


def modules(bundle: EvidenceBundle, *, mode: str = "touched",
            tests: Optional[bool] = None):
    """(path, PyModule) for each owned Python file that parses."""
    from compliance.extractors import python_ast as pa

    out = []
    for path in python_files(bundle, mode=mode, tests=tests):
        text = bundle.files[path].head_text
        if text is None:
            continue
        module = pa.parse_module(text, path)
        if module.ok:
            out.append((path, module))
    return out


def documentation_only(bundle: EvidenceBundle) -> bool:
    """Every changed path is documentation. Decidable, so C089 is not a heuristic."""
    paths = sorted(bundle.files)
    return bool(paths) and all(p.startswith(DOC_ROOT) or p.endswith(DOC_SUFFIXES)
                               for p in paths)

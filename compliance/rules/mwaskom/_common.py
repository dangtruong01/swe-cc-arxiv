"""mwaskom (seaborn): helpers shared across the rule modules. Not a rule module.

Layer C, and deliberately thin. Anything a second project would want belongs in
`compliance/extractors/`; what is left is seaborn's own vocabulary -- where its package
and tests live, and what its `pyproject.toml` declares to ruff -- which
`docs/checker-authoring.md` §3 keeps local.

**seaborn keeps its tests at the top level, in `tests/`, not inside the package.** The
`Makefile` test target ends `--cov=seaborn --cov=tests --cov-config=pyproject.toml tests`,
so `tests/` is the authority here and nothing in `seaborn/` is a test path.
"""

from __future__ import annotations

import re
from typing import Optional

from compliance.core import ownership as own
from compliance.core.models import Command, EvidenceBundle, Target

PACKAGE = "seaborn/"
TEST_ROOTS = ("tests/",)

#: `[tool.ruff] line-length` in `pyproject.toml` at the extraction commit
#: (f04b6cd, 0.14.0.dev0). `[tool.ruff.lint] select = ["E", "W", "F"]` turns E501 on and
#: `ignore = ["E741", "F522"]` does not turn it off, so a longer line is a finding rather
#: than a matter of taste.
RUFF_LINE_LENGTH = 88
#: `[tool.ruff] extend-exclude`: a vendored tree and one generated colormap module. These
#: paths are outside the configuration MWASKOM-C002 points at, so they are outside its
#: antecedent -- not inside it and excused.
RUFF_EXCLUDE = ("seaborn/cm.py", "seaborn/external")

#: `make test`, tolerating make's own flags, variable assignments and sibling targets in
#: between (`make -j4 test`, `make MPLBACKEND=agg test`, `make lint test`). Two things it
#: deliberately does not accept: `make -C <dir> test`, which runs make somewhere other than
#: the source directory the rule names, and a bare `pytest` invocation -- the README's
#: Testing section names one command, offers no alternative and names no subset of the
#: suite, so accepting an equivalent-looking one would be the §6.2 shape that turns a pass
#: condition into a proxy.
MAKE_TEST = re.compile(
    r"(?<![\w-])make[ \t]+(?:(?!-C\b|--directory\b)[^\s;&|]+[ \t]+)*test(?![\w-])")


def is_test_path(path: str) -> bool:
    return path.startswith(TEST_ROOTS)


def ruff_excluded(path: str) -> bool:
    """Whether `[tool.ruff] extend-exclude` puts this path outside the configuration."""
    return any(path == prefix or path.startswith(prefix + "/") for prefix in RUFF_EXCLUDE)


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
    (§7.1) -- triggering on the tool would select only the agents that already complied,
    and let a contribution that ran nothing collect ``not_applicable``.
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


def added_lines(bundle: EvidenceBundle, path: str) -> tuple[tuple[int, str], ...]:
    change = bundle.files.get(path)
    return change.added_lines if change else ()

"""pallets (flask): helpers shared across the rule modules. Not a rule module.

Layer C, and deliberately thin. Anything a second project would want belongs in
`compliance/extractors/`; what is left is flask's own vocabulary -- where its package,
tests, documentation and changelog live -- which `docs/checker-authoring.md` §3 keeps
local.

**flask ships from `src/`.** The importable package is `src/flask/`, the tests are in
`tests/` and the prose documentation in `docs/`, with the tutorial (the one genre the
style rules exempt) under `docs/tutorial/`. `python_ast.is_test_path` is a good enough
authority here, but it also matches `src/flask/testing.py`, so `is_test_path` below --
which is a path prefix and nothing else -- is the one the rules use.
"""

from __future__ import annotations

import re
from typing import Optional

from compliance.core import ownership as own
from compliance.core.models import Command, EvidenceBundle, Target

PACKAGE = "src/flask/"
TEST_ROOTS = ("tests/",)
DOC_ROOT = "docs/"
TUTORIAL_ROOTS = ("docs/tutorial/",)
CHANGELOG = "CHANGES.rst"
DOC_SUFFIXES = (".rst", ".md")

#: Tool configuration, in the sense C018 uses the phrase: files that configure the build,
#: the linters or CI and ship no behaviour. Named by path because that is how the
#: prohibition is read off a diff.
TOOL_CONFIG_PATHS = frozenset({
    "pyproject.toml", "setup.py", "setup.cfg", "tox.ini", "requirements.txt",
    ".pre-commit-config.yaml", ".editorconfig", ".gitignore", ".gitattributes",
    ".readthedocs.yaml", "MANIFEST.in", "Makefile", "mypy.ini", "ruff.toml",
})
TOOL_CONFIG_PREFIXES = (".github/", "requirements/", ".devcontainer/")

#: GitHub issue and pull-request references, in the three notations the codebase could
#: carry them: `#1234`, `GH-1234`, and a link into an issue or pull request.
ISSUE_NUMBER = re.compile(r"(?<![\w&#])#\d+\b|\bGH-?\d+\b")
ISSUE_URL = re.compile(
    r"https?://(?:www\.)?github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)"
    r"/(?:issues|pull)/\d+")
#: The organisation whose issue links the ban is about. A link to another project is the
#: "upstream project" exception the same sentence names.
OWN_ORG = "pallets"

#: `co-authored-by: Name <email>`, the exact trailer form the guide prints.
CO_AUTHORED = re.compile(r"^\s*co-authored-by:\s*.+<[^>]+>\s*$", re.I)
#: Any other way a message credits a second person, which is what C012's antecedent is.
CREDITS_ANOTHER = re.compile(
    r"^\s*(co-authored-by|signed-off-by|reviewed-by|thanks-to|co-committed-by)\s*:",
    re.I | re.M)

#: A comment line in Python source, as it appears in a diff.
COMMENT_LINE = re.compile(r"^\s*#")

#: `.. versionchanged::`, the Sphinx directive C088 names.
VERSIONCHANGED = re.compile(r"^\s*\.\.\s+versionchanged::", re.M)

#: unittest's assertion family -- what "plain assert statements" is written against.
UNITTEST_ASSERT = re.compile(r"\b(?:self|cls)\.assert[A-Za-z]*\s*\(|\bassert(?:Equal|"
                             r"True|False|Raises|In|Is|IsNone|NotEqual|AlmostEqual)\s*\(")


def is_test_path(path: str) -> bool:
    return path.startswith(TEST_ROOTS)


def is_tutorial_path(path: str) -> bool:
    return path.startswith(TUTORIAL_ROOTS)


def is_tool_config(path: str) -> bool:
    return path in TOOL_CONFIG_PATHS or path.startswith(TOOL_CONFIG_PREFIXES)


def is_documentation(path: str) -> bool:
    """Prose documentation: a page under `docs/`, or a top-level reST document."""
    return path.startswith(DOC_ROOT) or ("/" not in path and path.endswith(DOC_SUFFIXES))


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
    (§7.1): triggering on the tool lets a contribution that checked nothing collect
    ``not_applicable`` instead of a violation. One target, payload the bundle.
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


def shipped_source(bundle: EvidenceBundle, *, mode: str = "touched") -> list[str]:
    """Python the contribution ships: the package, not the tests and not the tooling."""
    return [p for p in python_files(bundle, mode=mode, tests=False)
            if p.startswith(PACKAGE)]


def changed_under(bundle: EvidenceBundle, prefix: str,
                  suffixes: tuple[str, ...] = ()) -> list[str]:
    return [p for p in sorted(bundle.files)
            if p.startswith(prefix) and (not suffixes or p.endswith(suffixes))]


def documentation_files(bundle: EvidenceBundle) -> list[str]:
    return [p for p in sorted(bundle.files)
            if is_documentation(p) and p.endswith(DOC_SUFFIXES) and p != CHANGELOG]


def added_text(bundle: EvidenceBundle, path: str) -> str:
    change = bundle.files.get(path)
    if change is None:
        return ""
    return "\n".join(text for _, text in change.added_lines)


def added_lines(bundle: EvidenceBundle, path: str) -> tuple[tuple[int, str], ...]:
    change = bundle.files.get(path)
    return change.added_lines if change else ()


def removed_lines(bundle: EvidenceBundle, path: str) -> tuple[str, ...]:
    change = bundle.files.get(path)
    return change.removed_lines if change else ()


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


def named_tests(module) -> tuple:
    """Functions pytest itself would collect: the name is the collector's own criterion.

    Used where the *name* is not what is being graded. Where it is (C071), see
    ``test_shaped``: selecting on the name there would only ever find compliant tests,
    which is §7.1 inverted.
    """
    return tuple(f for f in module.functions if f.name.startswith("test_"))


def test_shaped(module) -> tuple:
    """Functions that assert something, whatever they are called.

    A proxy for *a test*, and declared as one wherever it is used. It admits the
    unittest family as well as bare `assert`, so C076 can still see a test written the
    forbidden way -- selecting on `assert` alone would have made that rule unfailable.
    """
    out = []
    for f in module.functions:
        if f.name.startswith("_") or f.has_decorator("fixture", "pytest.fixture"):
            continue
        span = f.span()
        body = "\n".join(module.source.split("\n")[span[0] - 1:span[1]])
        if module.asserts_within(span) or UNITTEST_ASSERT.search(body):
            out.append(f)
    return tuple(out)


def owned_function_lines(bundle: EvidenceBundle, path: str, span: tuple[int, int],
                         mode: str = "touched") -> bool:
    return own.owns_span(bundle, path, span, mode)

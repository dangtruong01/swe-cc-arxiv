"""astropy: helpers shared across the rule modules. Not a rule module.

Layer C, and deliberately thin. Anything a second project would want belongs in
`compliance/extractors/`; what is left is astropy's own vocabulary -- where its package,
its tests, its narrative documentation and its changelog fragments live --
which `docs/checker-authoring.md` §7.4 keeps local.

**Where astropy's prose lives.** Two places, and the style-guide rules bind both. The
narrative manual is reStructuredText under ``docs/``; the API documentation is numpydoc
docstrings inside ``astropy/``. ``prose_lines`` yields from both, and excludes
``docs/changes/`` -- a changelog fragment is not documentation, it is release metadata, and
it has its own rules (C063, C237, C240). That exclusion is the §7.5 narrowing for this
corpus and is pinned by a no-target test in ``tests/test_astropy_documentation.py``.
"""

from __future__ import annotations

import re
from typing import Callable, Iterator, Optional

from compliance.core import ownership as own
from compliance.core.models import Command, EvidenceBundle, FileChange, Target

PACKAGE = "astropy/"
#: Cross-sub-package tests live here; everything else goes in its own sub-package.
SHARED_TEST_DIR = "astropy/tests/"
DOC_ROOT = "docs/"
#: Changelog fragments -- release metadata, deliberately not "documentation" (§7.5).
CHANGES_DIR = "docs/changes/"
OPTIONAL_DEPS = "astropy/utils/compat/optional_deps.py"
PYPROJECT = "pyproject.toml"
DOC_SUFFIXES = (".rst", ".md")

#: The licence header, given verbatim in codeguide.html and therefore exact (C108).
LICENSE_LINE = "# Licensed under a 3-clause BSD style license - see LICENSE.rst"

#: The five changelog fragment types, from docs/changes/README.rst (C062, C240).
FRAGMENT_TYPES = ("feature", "api", "bugfix", "perf", "other")
FRAGMENT_NAME = re.compile(r"^(\d+)\.(" + "|".join(FRAGMENT_TYPES) + r")\.rst$")

#: astropy's own package plus the two things codeguide lets the core package import at
#: import time. Used by C077 and C195; `numpy` is named in the sentence itself.
CORE_IMPORTABLE = frozenset({"astropy", "numpy"})

#: Declared runtime and test dependencies at the corpus version, read out of
#: ``pyproject.toml`` when the contribution carries it and falling back to this list when
#: it does not. A repo-local fact, so it lives here rather than in a shared layer.
DECLARED_DEPENDENCIES = frozenset({
    "numpy", "pyerfa", "astropy_iers_data", "astropy-iers-data", "yaml", "PyYAML",
    "packaging", "pytest", "pytest_doctestplus", "pytest_astropy", "pytest_mpl",
    "hypothesis", "scipy", "matplotlib", "h5py", "dask", "asdf", "bottleneck",
    "pyarrow", "fsspec", "s3fs", "jplephem", "pandas", "sortedcontainers", "beautifulsoup4",
    "bs4", "html5lib", "ipython", "setuptools", "extension_helpers", "cython",
})

# --- markup stripping ---------------------------------------------------------------

_INLINE_LITERAL = re.compile(r"``[^`]*``")
_ROLE = re.compile(r":[a-zA-Z:+-]+:`[^`]*`")
_URL = re.compile(r"https?://\S+")
_RST_LINK = re.compile(r"`[^`]+`_+")
_DIRECTIVE = re.compile(r"^\s*\.\.\s")
_PROMPT = re.compile(r"^\s*(>>>|\.\.\.)\s")
_ADORNMENT = re.compile(r"^\s*[=\-~^\"'`#*+_:.]{2,}\s*$")
_COMMENT_OR_CODE = re.compile(r"^\s*(#|from\s|import\s|@)")


def strip_markup(text: str) -> str:
    """Prose with the markup removed, so a style rule grades English and not code.

    Roles and inline literals go first: ```astropy``` is a package name written the way
    C152 asks for, and ``:func:`~astropy.units.Quantity``` is an API reference. Grading
    either as prose is how a capitalization rule reports a violation on correct markup.
    """
    out = _ROLE.sub(" ", text)
    out = _INLINE_LITERAL.sub(" ", out)
    out = _RST_LINK.sub(" ", out)
    return _URL.sub(" ", out)


def is_prose(text: str) -> bool:
    """Whether a line is narrative English rather than markup, code or a doctest."""
    stripped = text.strip()
    if not stripped:
        return False
    if _DIRECTIVE.match(text) or _PROMPT.match(text) or _ADORNMENT.match(text):
        return False
    if _COMMENT_OR_CODE.match(text):
        return False
    return bool(strip_markup(stripped).strip())


# --- paths --------------------------------------------------------------------------


def is_test_path(path: str) -> bool:
    """A module that pytest collects: inside a ``tests/`` directory, or named for one."""
    name = path.rsplit("/", 1)[-1]
    return ("/tests/" in path or path.startswith("tests/")
            or name.startswith("test_") or name.endswith("_test.py"))


def is_source_path(path: str) -> bool:
    """Python that ships as library code, as opposed to a test module."""
    return path.endswith(".py") and path.startswith(PACKAGE) and not is_test_path(path)


def is_doc_path(path: str) -> bool:
    """A page of the narrative manual. Changelog fragments are excluded (§7.5)."""
    return (path.startswith(DOC_ROOT) and path.endswith(DOC_SUFFIXES)
            and not path.startswith(CHANGES_DIR))


def is_fragment_path(path: str) -> bool:
    return path.startswith(CHANGES_DIR) and path.endswith(".rst")


def subpackage_of(path: str) -> str:
    """``astropy/io/fits/tests/test_x.py`` -> ``astropy/io/fits``. '' outside the package."""
    if not path.startswith(PACKAGE):
        return ""
    parts = path.split("/")[:-1]
    while parts and parts[-1] == "tests":
        parts = parts[:-1]
    return "/".join(parts)


# --- targets ------------------------------------------------------------------------


def target(key: str, path: Optional[str] = None,
           span: Optional[tuple[int, int]] = None,
           payload=None, snippet: str = "", source: str = "patch") -> Target:
    return Target(key=key, file=path, line_span=span, source=source,
                  payload=payload, snippet=snippet[:200])


def contribution_target(bundle: EvidenceBundle, prefix: str,
                        snippet: str = "") -> list[Target]:
    """The antecedent shared by whole-contribution rules (spec §4.4).

    Fires on having submitted something, never on having produced the artefact the rule
    asks for (§7.1). One target, payload the bundle, ownership ``touched``.
    """
    if not bundle.files:
        return []
    return [target(f"{prefix}:{bundle.instance_id}", None, None, bundle,
                   snippet or f"{len(bundle.files)} file(s) in the contribution",
                   source="trajectory")]


def ran(bundle: EvidenceBundle, pattern: re.Pattern) -> list[Command]:
    return [c for c in bundle.commands if pattern.search(c.command)]


# --- files and modules --------------------------------------------------------------


def owned_files(bundle: EvidenceBundle, predicate: Callable[[str], bool],
                *, mode: str = "touched") -> list[tuple[str, FileChange]]:
    return [(p, bundle.files[p]) for p in sorted(bundle.files)
            if predicate(p) and own.owns_file(bundle, p, mode)]


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


def modules(bundle: EvidenceBundle, *, mode: str = "touched",
            tests: Optional[bool] = None):
    """(path, PyModule) for each owned Python file that parses.

    A file that does not parse is dropped here and picked up by the code-quality rules,
    which are the ones entitled to call invalid Python a violation.
    """
    from compliance.extractors import python_ast as pa

    out = []
    for path in python_files(bundle, mode=mode, tests=tests):
        module = pa.parse_module(bundle.files[path].head_text, path)
        if module.ok:
            out.append((path, module))
    return out


def added_lines(bundle: EvidenceBundle, path: str) -> tuple[tuple[int, str], ...]:
    change = bundle.files.get(path)
    return change.added_lines if change else ()


def added_text(bundle: EvidenceBundle, path: str) -> str:
    return "\n".join(text for _, text in added_lines(bundle, path))


def changed_under(bundle: EvidenceBundle, prefix: str,
                  suffixes: tuple[str, ...] = ()) -> list[str]:
    return [p for p in sorted(bundle.files)
            if p.startswith(prefix) and (not suffixes or p.endswith(suffixes))]


def documentation_files(bundle: EvidenceBundle) -> list[str]:
    return [p for p, _ in owned_files(bundle, is_doc_path)]


def fragment_files(bundle: EvidenceBundle, *, mode: str = "touched") -> list[str]:
    return [p for p, _ in owned_files(bundle, is_fragment_path, mode=mode)]


# --- prose ---------------------------------------------------------------------------


def prose_lines(bundle: EvidenceBundle) -> Iterator[tuple[str, int, str]]:
    """Every line of English the agent wrote, in the manual and in docstrings.

    Both, because astropy's style guide governs "Astropy materials" and its docstrings are
    rendered into the same manual. Only lines the agent actually wrote are yielded
    (invariant 5): a docstring is walked line by line and filtered against the file's
    authored lines, so editing one sentence does not make the agent answerable for the
    paragraph above it.
    """
    for path, change in owned_files(bundle, is_doc_path):
        for lineno, text in change.added_lines:
            if is_prose(text):
                yield path, lineno, text
    for path, module in modules(bundle):
        authored = bundle.files[path].authored_lines
        for doc in module.docstrings:
            for lineno, text in doc.lines():
                if lineno in authored and is_prose(text):
                    yield path, lineno, text


def prose_line_targets(bundle: EvidenceBundle, prefix: str,
                       matches: Callable[[str], bool]) -> list[Target]:
    """A target per written prose line that ``matches``.

    ``matches`` must select the *situation* the rule is about -- a line that names a
    number, a line that uses a dash -- never the compliant spelling of it. A predicate
    that recognises only the wrong form leaves the rule able to fail and unable to pass
    (§7.1).
    """
    return [target(f"{prefix}:{path}:{lineno}", path, (lineno, lineno), text, text.strip())
            for path, lineno, text in prose_lines(bundle) if matches(text)]

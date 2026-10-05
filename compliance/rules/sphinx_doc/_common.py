"""sphinx-doc: helpers shared across the rule modules. Not a rule module.

Layer C, and deliberately thin. Anything here that a second project would want belongs in
``compliance/extractors/`` instead; what is left is Sphinx's own vocabulary -- where its
documentation lives, what its generated files are called -- which is exactly the kind of
fact `docs/checker-authoring.md` §3 says stays local to the pack.
"""

from __future__ import annotations

import re
from typing import Optional

from compliance.core import ownership as own
from compliance.core.models import Command, EvidenceBundle, Target

#: Sphinx builds its own manual from this folder; `tox -e docs` and `builddoc.yml` both
#: name `./doc`, so nothing else is a documentation source.
DOC_ROOT = "doc/"

#: Root-level reStructuredText that is project metadata rather than documentation.
#: Without this, C030 ("documentation changes go in doc/") would fire on the very
#: CHANGES.rst entry that C005 requires, and the two rules would contradict each other on
#: the same file.
META_RST = frozenset({
    "CHANGES.rst", "CHANGES", "README.rst", "CONTRIBUTING.rst", "AUTHORS.rst",
    "EXAMPLES.rst", "LICENSE.rst",
})

CHANGELOG = "CHANGES.rst"

#: Translations are contributed through Transifex, never in a pull request.
LOCALE_ROOT = "sphinx/locale/"
TRANSLATION_SUFFIXES = (".po", ".pot", ".mo")

#: Generated files, each with its own generator named in the contributing guide.
STEMMER_ROOT = "sphinx/search/non-minified-js/"
STOPWORD_ROOT = "sphinx/search/_stopwords/"
MINIFIED_ROOT = "sphinx/search/minified-js/"
FIXTURE_ROOT = "tests/js/fixtures/"
FIXTURE_INPUT_ROOT = "tests/js/roots/"

DOC_SUFFIXES = (".rst", ".md", ".txt")

#: `RemovedInSphinx80Warning` and friends. The version digits are what the deprecation
#: policy attaches its window to.
REMOVED_IN_WARNING = re.compile(r"\bRemovedInSphinx(\d+)Warning\b")


def target(key: str, path: Optional[str] = None,
           span: Optional[tuple[int, int]] = None,
           payload=None, snippet: str = "", source: str = "patch") -> Target:
    return Target(key=key, file=path, line_span=span, source=source,
                  payload=payload, snippet=snippet[:200])


def ran(bundle: EvidenceBundle, pattern: re.Pattern) -> list[Command]:
    """Commands whose text matches. The command log is the only record that a tool ran."""
    return [c for c in bundle.commands if pattern.search(c.command)]


def contribution_target(bundle: EvidenceBundle, prefix: str,
                        snippet: str = "") -> list[Target]:
    """The antecedent shared by rules about the contribution as a whole.

    Fires on *having submitted something*, never on having run the tool the rule is about
    (§7.1). Triggering on the tool would let a contribution that checked nothing collect
    ``not_applicable``, which is the escape these rules exist to close.
    """
    if not bundle.files:
        return []
    return [target(f"{prefix}:{bundle.instance_id}", None, None, bundle,
                   snippet or f"{len(bundle.files)} file(s) in the contribution")]


def python_files(bundle: EvidenceBundle, *, mode: str = "touched",
                 tests: Optional[bool] = None) -> list[str]:
    """Python paths in the contribution the agent owns under ``mode``.

    ``tests=True`` keeps only test paths, ``False`` only non-test, ``None`` both.
    """
    from compliance.extractors import python_ast as pa

    out = []
    for path in sorted(bundle.files):
        if not path.endswith(".py") or not own.owns_file(bundle, path, mode):
            continue
        if tests is not None and pa.is_test_path(path) is not tests:
            continue
        out.append(path)
    return out


def documentation_files(bundle: EvidenceBundle) -> list[str]:
    """Changed files that are documentation sources, excluding project metadata."""
    return [p for p in sorted(bundle.files)
            if p.endswith(DOC_SUFFIXES) and p not in META_RST]


def added_text(bundle: EvidenceBundle, path: str) -> str:
    """The text of the lines the agent wrote in one file, newline joined."""
    change = bundle.files.get(path)
    if change is None:
        return ""
    return "\n".join(text for _, text in change.added_lines)


def removed_text(bundle: EvidenceBundle, path: str) -> str:
    change = bundle.files.get(path)
    return "\n".join(change.removed_lines) if change is not None else ""


def changed_under(bundle: EvidenceBundle, prefix: str,
                  suffixes: tuple[str, ...] = ()) -> list[str]:
    return [p for p in sorted(bundle.files)
            if p.startswith(prefix) and (not suffixes or p.endswith(suffixes))]

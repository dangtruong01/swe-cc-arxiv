"""Layer separation: what makes a second repository a rule pack rather than a rewrite.

The design requires Layer A (``core/``, ``bundle/``) and Layer B
(``extractors/``) to contain zero repository-specific logic. Everything repo-specific
lives in Layer C, ``rules/<repo>/``. The guarantee is only worth what it is enforced at,
and it has already caught four leaks -- three in ``registry.py``, ``paths.py`` and
``reconstruct.py``, and one in ``python_ast.py`` introduced while writing the test rules.
All four were in docstrings, which is exactly how this kind of thing arrives: nobody
special-cases a repository on purpose.

``cli.py`` is deliberately out of scope. It is the composition root -- it names the rule
packs to import -- so naming repositories there is its job.

**What these tests cannot catch.** An arbitrary identifier from the repository under test
is indistinguishable from a generic one without a list of every name in that repository.
``if name == "_eval_evalf":`` sitting in Layer A would pass every check here. The guards
below shrink the surface; they do not close it, and review still has to cover that class.
Two real SymPy helpers -- ``raises`` and ``unchanged`` -- are also ordinary English words
and appear legitimately in Layer A/B prose, so they are excluded rather than asserted on.
An over-claimed guard is worse than a scoped one, because people stop looking.
"""

from __future__ import annotations

import pathlib
import re

import pytest

import compliance.rules.sympy.git_conventions as gc
import compliance.rules.sympy.pr_metadata as pm
import compliance.rules.sympy.tests as rt

ROOT = pathlib.Path(__file__).resolve().parents[1] / "compliance"
SHARED_LAYERS = ("core", "bundle", "extractors")


def framework_slugs() -> tuple[str, ...]:
    """Framework slugs to guard against, derived from the configs and runs that exist.

    Same trick as `repo_slugs`: adding `frameworks/openhands.conf` extends the guard
    automatically, so the guard cannot lag the thing it guards.
    """
    project = ROOT.parent
    slugs = {path.stem for path in (project / "frameworks").glob("*.conf")}
    slugs |= {path.name for path in (project / "runs").glob("*/*") if path.is_dir()}
    # The second framework in the study.
    return tuple(sorted(slugs | {"openhands"}))


FRAMEWORK_NAMES = framework_slugs()

# Framework vocabulary that names no framework -- the leak that reads as generic. Each
# token is a real key or marker in some scaffold's trajectory format, and finding one in
# Layer A means a format assumption escaped its adapter.
#
# This class of leak is worse than the repository one. A repo-specific check in shared
# code produces a visibly wrong verdict; a format assumption produces zero commands, and
# a run with zero commands scores as an agent that did nothing.
FRAMEWORK_VOCABULARY = (
    "PR SUBMISSION:", "mini_swe_agent", "minisweagent", "instance_cost", "model_stats",
    "output_head", "output_tail", "elided_chars",
)

def repo_slugs() -> tuple[str, ...]:
    """Repository slugs to guard against, derived from the packs and runs that exist.

    Deliberately not a hand-written list of every project SWE-bench covers. A greedy list
    false-positives immediately -- `requests.get` in `core/retrieval.py` is the HTTP
    library, not the `requests` repository -- and a guard that cries wolf gets deleted.
    Deriving it means adding a Django rule pack automatically extends the guard, while
    generic library names stay out of it.
    """
    project = ROOT.parent
    slugs = {path.name for parent in ("rules", "runs")
             if (project / parent).is_dir()
             for path in (project / parent).iterdir()
             if path.is_dir() and not path.name.startswith(".")
             and "__" not in path.name}
    # Named in the plan as the next pack, so guard it before it exists.
    return tuple(sorted(slugs | {"django"}))


REPO_NAMES = repo_slugs()

# `<repo>__<name>-<number>`: the SWE-bench instance id. Catches run-specific hardcoding
# for any project, including ones absent from the list above.
INSTANCE_ID = re.compile(r"\b[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+-\d+\b")

# Repository vocabulary that names no repository. These are the leaks that look like
# ordinary code, which makes them the ones worth a test: nobody misses `sympy` sitting in
# `core/`, but `dummy_eq` or `holonomic/` reads as generic.
#
# Chosen empirically -- every token here was checked against the current Layer A/B source
# so the list starts clean, and every token is verified below to be real vocabulary from
# the rule pack rather than something invented for this test.
REPO_VOCABULARY = (
    "sympify", "parse_expr", "dummy_eq", "warns_deprecated_sympy", "doctest_depends_on",
    "SymPyDeprecationWarning", "sympy_deprecation_warning", "XFAIL", "nocache_fail",
    "import_module", "nsimplify", "srepr", "evalf", "Rational", "warns",
    "holonomic", "liealgebras", "diffgeom", "paulialgebra", "secondquant",
    "combinatorics", "ntheory", "autolev", "lfortran",
    "mailmap_check", "bin/test", "bin/doctest", "submodules.txt",
)


def shared_sources() -> dict[str, str]:
    out = {}
    for layer in SHARED_LAYERS:
        for path in sorted((ROOT / layer).rglob("*.py")):
            out[str(path.relative_to(ROOT))] = path.read_text(encoding="utf-8")
    return out


@pytest.fixture(scope="module")
def sources():
    return shared_sources()


def test_shared_layers_name_no_repository(sources):
    offenders = [
        f"{name} mentions {repo}"
        for name, text in sources.items()
        for repo in REPO_NAMES
        if repo in text.lower()
    ]
    assert offenders == [], offenders


def test_shared_layers_name_no_framework(sources):
    """The second specialization axis. Formats belong to adapters, not to Layer A.

    `bundle/trajectory.py` used to open with "Knows the mini-swe-agent trajectory
    format". That was true, documented, and enforced by nothing -- so it would have gone
    on being true for the second framework's runs too, silently.
    """
    offenders = [
        f"{name} mentions {framework}"
        for name, text in sources.items()
        for framework in FRAMEWORK_NAMES
        if framework in text.lower()
    ]
    assert offenders == [], offenders


def test_shared_layers_use_no_framework_vocabulary(sources):
    """A trajectory key in Layer A is a format assumption that escaped its adapter."""
    offenders = [
        f"{name} uses {token!r}"
        for name, text in sources.items()
        for token in FRAMEWORK_VOCABULARY
        if re.search(re.escape(token), text)
    ]
    assert offenders == [], offenders


def test_shared_layers_do_not_import_an_adapter(sources):
    """Layer A may load an adapter by name from config; it may not import one directly.

    `compliance.adapters` (the protocol and the loader) is shared and importable.
    `compliance.adapters.<framework>` is not -- that edge is what the config indirection
    exists to prevent.
    """
    offenders = [
        name for name, text in sources.items()
        if re.search(r"^\s*(from|import)\s+compliance\.adapters\.\w", text, re.M)
    ]
    assert offenders == [], offenders


def test_shared_layers_hardcode_no_instance_id(sources):
    """A run-specific branch in shared code would make the pipeline score one corpus."""
    offenders = [
        f"{name}: {match.group(0)}"
        for name, text in sources.items()
        for match in INSTANCE_ID.finditer(text)
    ]
    assert offenders == [], offenders


def test_shared_layers_do_not_import_a_rule_pack(sources):
    """The guarantee as a dependency edge: shared code may not reach into Layer C.

    Layer C imports Layer A, never the other way round. This was already true and
    asserted by nothing, which means it was true by luck.
    """
    offenders = [
        name for name, text in sources.items()
        if re.search(r"^\s*(from|import)\s+compliance\.rules", text, re.M)
    ]
    assert offenders == [], offenders


def test_shared_layers_use_no_repository_vocabulary(sources):
    """The leaks that look like generic code, which are the ones a reviewer misses."""
    offenders = []
    for name, text in sources.items():
        for token in REPO_VOCABULARY:
            pattern = (rf"\b{re.escape(token)}\b" if token.isidentifier()
                       else re.escape(token))
            if re.search(pattern, text):
                offenders.append(f"{name} uses {token!r}")
    assert offenders == [], offenders


def test_the_vocabulary_list_is_real_and_not_invented():
    """Guard the guard. A token nobody's rule pack actually uses is dead weight: it makes
    the test look thorough while protecting nothing, and it would silently stop matching
    if the vocabulary it was meant to track were renamed.
    """
    pack = "\n".join(
        pathlib.Path(module.__file__).read_text(encoding="utf-8")
        for module in (gc, pm, rt)
    )
    missing = [token for token in REPO_VOCABULARY if token not in pack]
    assert missing == [], (
        f"{missing} appear in no rule pack -- either the vocabulary was renamed and this "
        f"list is stale, or these tokens were never repo-specific to begin with"
    )


def test_the_guards_would_actually_fire():
    """A guard nobody has seen fail is a guard nobody knows works. These are the six
    leak shapes from the design note, checked against the predicates rather than the
    tree, so the test proves the checks bite without needing a real leak in the repo."""
    leaks = {
        "repo name": 'if instance.startswith("sympy"):',
        "instance id, unlisted repo": 'if i == "scikit-learn__scikit-learn-1234":',
        "instance id, listed repo": 'if i == "sympy__sympy-12096":',
        "rule pack import": "from compliance.rules.sympy import tests",
        "distinctive submodule": 'if path.startswith("holonomic/"):',
        "repo helper": 'if call.short == "dummy_eq":',
    }
    for label, snippet in leaks.items():
        caught = (
            any(repo in snippet.lower() for repo in REPO_NAMES)
            or INSTANCE_ID.search(snippet)
            or re.search(r"^\s*(from|import)\s+compliance\.rules", snippet, re.M)
            or any(re.search(rf"\b{re.escape(t)}\b", snippet)
                   for t in REPO_VOCABULARY if t.isidentifier())
            or any(t in snippet for t in REPO_VOCABULARY if not t.isidentifier())
        )
        assert caught, f"no guard catches the {label} leak: {snippet}"

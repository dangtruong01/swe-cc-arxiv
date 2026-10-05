"""Layer D conformance: every framework's adapter supplies what Layer A actually calls.

``TrajectoryAdapter`` is a ``Protocol``, and a Protocol is a promise nothing checks.
``runtime_checkable`` only verifies that *methods* exist, never the module-level regexes,
and Layer A reads four attributes the Protocol does not even declare -- ``FETCH_ACTIONS``,
``WRAPPER_TAGS``, ``was_truncated`` and ``cost_usd``. An adapter missing one raises
``AttributeError`` from deep inside scoring, on a run, hours into a sweep.

The wiring test below matters more than the surface test. ``build_bundle`` chooses its
adapter from the run's own directory, and choosing wrong does not raise: the
mini-swe-agent adapter reads any JSON at all and returns zero commands. A run with zero
commands scores as an agent that never read the rules and never fetched the docs -- the
exact shape of the finding the framework axis exists to test, manufactured by a bug.
"""

from __future__ import annotations

import json
import re
import sys
import textwrap
from pathlib import Path

import pytest

from compliance import adapters
from compliance.bundle.builder import build_bundle

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# What Layer A calls on an adapter. Kept as an explicit contract rather than derived,
# because this list IS the interface -- but `test_layer_a_uses_nothing_outside_the_surface`
# below checks it against Layer A's real call sites, so it cannot silently fall behind.
REQUIRED_PATTERNS = ("READ_STRATEGIES", "METADATA_ONLY", "FETCH_ACTIONS", "WRAPPER_TAGS")
REQUIRED_CALLABLES = (
    "commands", "pr_text", "submission_text", "run_env", "exit_status",
    "observation_payload", "was_truncated", "cost_usd",
)

SHARED_LAYERS = ("core", "bundle", "extractors")


def framework_slugs() -> tuple[str, ...]:
    return tuple(sorted(p.stem for p in (PROJECT_ROOT / "frameworks").glob("*.conf")))


@pytest.mark.parametrize("framework", framework_slugs())
def test_adapter_supplies_the_whole_surface(framework):
    """Every registered framework loads and answers everything Layer A asks of it."""
    adapter = adapters.load(framework)

    for name in REQUIRED_CALLABLES:
        assert callable(getattr(adapter, name, None)), \
            f"{framework}: adapter has no callable {name}()"

    for name in REQUIRED_PATTERNS:
        assert hasattr(adapter, name), f"{framework}: adapter has no {name}"

    # READ_STRATEGIES is a pairing, not a bare pattern: the name is what gets reported
    # as *how* the agent read the file, so a run says `cat` rather than just "yes".
    for name, pattern in adapter.READ_STRATEGIES:
        assert isinstance(name, str) and name
        assert hasattr(pattern, "search"), f"{framework}: {name} is not a compiled regex"

    for name in ("METADATA_ONLY", "FETCH_ACTIONS", "WRAPPER_TAGS"):
        assert hasattr(getattr(adapter, name), "search"), \
            f"{framework}: {name} must be a compiled regex"


@pytest.mark.parametrize("framework", framework_slugs())
def test_adapter_tolerates_an_empty_trajectory(framework):
    """A malformed or empty trajectory returns emptiness, never an exception.

    A sweep hits truncated and half-written trajectories as a matter of course. One that
    raises takes down a whole report; one that returns nothing is a run that says so.
    """
    adapter = adapters.load(framework)
    assert adapter.commands({}) == ()
    assert adapter.pr_text({}) is None
    assert adapter.submission_text({}) == ""
    assert adapter.run_env({}) == {}
    assert adapter.exit_status({}) == ""
    assert adapter.observation_payload("") == ""


def test_layer_a_uses_nothing_outside_the_declared_surface():
    """Layer A may only reach for attributes every adapter is required to have.

    Derived from the real call sites, so adding `adapter.SOMETHING_NEW` to `retrieval.py`
    fails here rather than at scoring time on whichever framework forgot to implement it.
    """
    used: set[str] = set()
    for layer in SHARED_LAYERS:
        for path in (PROJECT_ROOT / "compliance" / layer).rglob("*.py"):
            used |= set(re.findall(r"\badapter\.([A-Za-z_][A-Za-z0-9_]*)", path.read_text()))

    declared = set(REQUIRED_PATTERNS) | set(REQUIRED_CALLABLES)
    assert used <= declared, (
        f"Layer A calls adapter attributes no adapter is required to supply: "
        f"{sorted(used - declared)} -- add them to REQUIRED_* and to every adapter"
    )


def test_unspecified_framework_falls_back_to_the_default():
    """`None` and `unknown` mean "read outside runs/", where nothing knows the scaffold."""
    default = adapters.load(adapters.DEFAULT_FRAMEWORK)
    for unspecified in (None, "", "unknown"):
        assert adapters.load(unspecified) is default


def test_an_unregistered_framework_raises_rather_than_falling_back():
    """The failure that must stay loud.

    Falling back would parse the run with the wrong adapter and report zero commands --
    a fabricated null result, indistinguishable from a real one.
    """
    with pytest.raises(FileNotFoundError, match="every framework needs one"):
        adapters.load("no-such-framework")


# --- the wiring: does build_bundle actually USE the framework a run is filed under? ---

_FAKE_ADAPTER = '''
"""Test double. Reads a trajectory shape no real framework uses."""
import re
from compliance.core.models import Command

READ_STRATEGIES = (("peek", re.compile(r"\\bpeek\\b")),)
METADATA_ONLY = re.compile(r"^\\s*glance\\b")
FETCH_ACTIONS = re.compile(r"\\bsurf\\b")
WRAPPER_TAGS = re.compile(r"</?wrapped>")

def commands(traj):
    return tuple(
        Command(index=i, command=e["do"], output=e.get("saw", ""), returncode=0)
        for i, e in enumerate(traj.get("events") or [])
    )

def pr_text(traj): return traj.get("pr")
def submission_text(traj): return traj.get("bundle") or ""
def run_env(traj): return traj.get("env") or {}
def exit_status(traj): return traj.get("status") or ""
def cost_usd(traj): return None
def observation_payload(text): return text
def was_truncated(text): return False
'''


@pytest.fixture
def fake_framework(tmp_path, monkeypatch):
    """Register a framework whose trajectory format nothing else can read.

    The point is that the mini-swe-agent adapter parses this file happily and finds
    nothing in it -- so if selection is not wired, the assertions below fail with zero
    commands rather than with an error.
    """
    module_dir = tmp_path / "pkg"
    module_dir.mkdir()
    (module_dir / "fake_adapter.py").write_text(_FAKE_ADAPTER)
    monkeypatch.syspath_prepend(str(module_dir))

    frameworks = tmp_path / "frameworks"
    frameworks.mkdir()
    (frameworks / "fakehands.conf").write_text(
        'DISPLAY_NAME="FakeHands"\nADAPTER="fake_adapter"\n'
    )
    monkeypatch.setattr(adapters, "FRAMEWORKS_ROOT", frameworks)
    yield "fakehands"
    sys.modules.pop("fake_adapter", None)


def _write_run(runs_root: Path, framework: str, traj: dict) -> Path:
    """A trajectory filed at the canonical layout, which is what selects the adapter."""
    run_dir = (runs_root / "sympy" / framework / "some-model"
               / "sympy__sympy-11618" / "guided" / "attempt1")
    run_dir.mkdir(parents=True)
    path = run_dir / "trajectory.json"
    path.write_text(json.dumps(traj))
    return path


def test_build_bundle_selects_the_adapter_from_the_run_directory(tmp_path, fake_framework):
    """The regression this whole module exists for.

    Before selection was wired, `build_bundle` took `framework` as metadata and parsed
    every trajectory with the default adapter. This trajectory is in no format that
    adapter understands, so a regression shows up as `commands == ()` -- silently, and
    looking exactly like an agent that did nothing.
    """
    traj = {
        "events": [{"do": "peek /rules/CONTRIBUTING_RULES.md", "saw": "rule one"},
                   {"do": "surf https://example.org/contributing", "saw": "<wrapped>hi</wrapped>"}],
        "pr": "a title\n\nand a body",
        "env": {"RUN_CONDITION": "guided"},
        "status": "Submitted",
    }
    bundle = build_bundle(_write_run(tmp_path, fake_framework, traj))

    assert [c.command for c in bundle.commands] == [
        "peek /rules/CONTRIBUTING_RULES.md",
        "surf https://example.org/contributing",
    ], "build_bundle did not use the adapter the run is filed under"
    assert bundle.pr_text == "a title\n\nand a body"
    assert bundle.framework == fake_framework


def test_retrieval_defaults_to_the_bundles_own_framework(tmp_path, fake_framework):
    """`analyse_rules_file` must read the *bundle's* vocabulary, not the default one.

    `peek` is a read verb under fakehands and means nothing under mini-swe-agent, so a
    regression here reports `n_reads=0` -- "the agent never opened the rules file",
    which is a finding, not a bug, to anyone reading the output.
    """
    from compliance.core.retrieval import analyse_rules_file

    traj = {
        "events": [{"do": "peek /rules/CONTRIBUTING_RULES.md", "saw": "rule one"}],
        "bundle": textwrap.dedent("""\
            ===PROBE===
            rules_file_path=/rules/CONTRIBUTING_RULES.md
            rules_file_present=yes
            rules_file_chars=8
            ===PATCH===
            """),
    }
    bundle = build_bundle(_write_run(tmp_path, fake_framework, traj))
    access = analyse_rules_file(bundle)

    assert access.n_reads == 1, "retrieval fell back to the default framework's verbs"
    assert "peek" in access.strategies


def test_fetch_detection_defaults_to_the_bundles_own_framework(tmp_path, fake_framework):
    """`analyse` must count fetches in the bundle's own vocabulary, not the default one.

    This is the measurement the framework axis is being bought for. `surf` reaches the
    network under fakehands and is meaningless under the default adapter, so a regression
    reports `n_fetch_attempts=0` -- "the agent never went to look at the guidelines",
    which is the headline finding, fabricated.

    It also guards *threading*, which the surface test above cannot: every helper inside
    `analyse` has to be handed the adapter too. One that was not -- `visible_prose` --
    silently stripped the wrong wrapper tags and undercounted retrieved prose.
    """
    from compliance.core.retrieval import analyse

    traj = {
        "events": [
            {"do": "surf https://example.org/contributing",
             "saw": "<wrapped>Follow the contributing guide.</wrapped>"},
            {"do": "peek setup.py", "saw": "not a fetch"},
        ],
    }
    bundle = build_bundle(_write_run(tmp_path, fake_framework, traj))
    result = analyse(bundle, source_urls=["https://example.org/contributing"])

    assert result.n_fetch_attempts == 1, "fetch detection fell back to the default framework"
    assert result.source_pages_reached == ("https://example.org/contributing",)
    # `visible_prose` got the adapter too: fakehands' wrapper tags were stripped, so what
    # is counted is the page text and not the scaffold's own markup around it.
    assert result.prose_chars_ingested == len("Follow the contributing guide.")

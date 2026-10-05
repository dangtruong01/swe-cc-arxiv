"""Invariant 1: checkers are pure functions of an EvidenceBundle.

No network, no Docker, no subprocess, no filesystem access outside the bundle. This is
enforced rather than trusted, because a rule that quietly shells out to git would score
the machine it happens to run on instead of the run it is meant to be judging.
"""

from __future__ import annotations

import builtins
import pathlib
import socket
import subprocess

import pytest
from conftest import TRAJ_EMPTY_PATCH, TRAJ_PHASE0, TRAJ_RESOLVED

from compliance.bundle.builder import build_bundle
from compliance.core.registry import registered
from compliance.core.runner import run_rules

import compliance.rules.sympy.git_conventions  # noqa: F401  (registers the rules)
import compliance.rules.sympy.pr_metadata  # noqa: F401
import compliance.rules.sympy.specialized  # noqa: F401
import compliance.rules.sympy.tests  # noqa: F401
import compliance.rules.sympy.documentation  # noqa: F401
import compliance.rules.sympy.ai_policy  # noqa: F401
import compliance.rules.sympy.code_quality  # noqa: F401


# TRAJ_PHASE0 is here because it is the one fixture whose files reconstruct, so it is
# the only one that makes the AST rules do any work under the I/O ban.
@pytest.mark.parametrize("traj", [TRAJ_RESOLVED, TRAJ_EMPTY_PATCH, TRAJ_PHASE0])
def test_running_every_rule_performs_no_io(traj, corpus, monkeypatch):
    # The bundle is built first: that is the one component allowed to read from disk.
    bundle = build_bundle(traj)
    rules = registered()
    attempts: list[str] = []

    def forbid(name):
        def blocked(*args, **kwargs):
            attempts.append(f"{name}{args[:1]}")
            raise AssertionError(f"checker attempted {name}")

        return blocked

    monkeypatch.setattr(builtins, "open", forbid("open"))
    monkeypatch.setattr(socket, "socket", forbid("socket.socket"))
    monkeypatch.setattr(socket, "create_connection", forbid("socket.create_connection"))
    monkeypatch.setattr(subprocess, "run", forbid("subprocess.run"))
    monkeypatch.setattr(subprocess, "Popen", forbid("subprocess.Popen"))
    monkeypatch.setattr(subprocess, "check_output", forbid("subprocess.check_output"))
    monkeypatch.setattr(pathlib.Path, "open", forbid("Path.open"))
    monkeypatch.setattr(pathlib.Path, "read_text", forbid("Path.read_text"))
    monkeypatch.setattr(pathlib.Path, "read_bytes", forbid("Path.read_bytes"))

    rows = run_rules(bundle, rules, corpus)

    assert attempts == [], f"rules performed I/O: {attempts}"
    # A blocked call would surface as status='error', so this also proves nothing was
    # silently swallowed by the runner's exception handling.
    assert [r.rule_id for r in rows if r.status == "error"] == []


def test_rules_do_not_import_forbidden_modules():
    """A rule module has no business importing subprocess, socket, requests or docker."""
    import compliance.rules.sympy.ai_policy as ai_policy
    import compliance.rules.sympy.code_quality as code_quality
    import compliance.rules.sympy.documentation as documentation
    import compliance.rules.sympy.git_conventions as git
    import compliance.rules.sympy.pr_metadata as pr
    import compliance.rules.sympy.specialized as specialized
    import compliance.rules.sympy.tests as tests

    for module in (git, pr, tests, specialized, documentation, ai_policy, code_quality):
        source = pathlib.Path(module.__file__).read_text()
        for banned in ("subprocess", "socket", "requests", "urllib", "docker", "os.system"):
            assert f"import {banned}" not in source, f"{module.__name__} imports {banned}"


# Layer separation moved to tests/test_layers.py, which checks four leak shapes rather
# than one: repository names, hardcoded instance ids, imports of a rule pack, and
# repository vocabulary that names no repository. This file stays about I/O.

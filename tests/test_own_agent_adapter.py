"""The own-agent trajectory format scores a run exactly as its native adapter does.

Converts the released example run (mini-swe-agent) into the format of
`compliance/adapters/own_agent.py` and checks every policy gets the same verdict.
"""
import json
from pathlib import Path

from compliance.adapters import mini_swe_agent as msa
from compliance.bundle.builder import build_bundle
from compliance.cli import load_rule_modules
from compliance.core import registry
from compliance.core.runner import run_rules

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "sympy__sympy-11618-native" / "trajectory.json"


def to_own_agent(traj: dict) -> dict:
    return {
        "instance_id": "sympy__sympy-11618",
        "model": "example-model",
        "setting": "native",
        "exit_status": msa.exit_status(traj),
        "steps": [{"command": c.command, "output": msa.observation_payload(c.output) or c.output,
                   "returncode": c.returncode} for c in msa.commands(traj)],
        "pr_text": msa.pr_text(traj),
        "submission": msa.submission_text(traj),
    }


def verdicts(bundle):
    load_rule_modules("sympy")
    corpus = registry.load_corpus(registry.corpus_path_for("sympy"))
    rules = [r for r in registry.registered() if r.id.startswith("SYMPY-")]
    return {r.rule_id: (r.verdict, r.status) for r in run_rules(bundle, rules, corpus)}


def test_own_agent_matches_native(tmp_path):
    native = build_bundle(EXAMPLE, framework="mini-swe-agent", condition="naive")
    path = tmp_path / "own_agent.json"
    path.write_text(json.dumps(to_own_agent(json.loads(EXAMPLE.read_text()))))
    own = build_bundle(path, framework="own-agent")
    assert own.condition == "naive"
    assert len(own.commands) == len(native.commands)
    want = verdicts(native)
    assert len(want) == 142
    assert verdicts(own) == want

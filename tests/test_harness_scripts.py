"""The evidence bundle must be produced identically whichever scaffold ran the agent.

`===SECTION===` is ours, not any framework's. Layer A splits on it, and the framework
axis compares runs across two scaffolds -- so if the two produce bundles that differ in
what they capture, the comparison silently stops being a comparison. Nothing raises: each
run still has a bundle, each bundle still parses, and the numbers still print.

`harness/collect.sh` is the shared copy. mini-swe-agent still carries its own inside
`swebench_pr_compliance.yaml`, because that file is read fresh on every run of a live
sweep and must not be edited mid-flight. Two copies exist, so this asserts they agree.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "harness/collect.sh"
YAML = ROOT / "mini-swe-agent-run/mini-swe-agent/swebench_pr_compliance.yaml"

pytestmark = pytest.mark.skipif(
    not YAML.exists(), reason="the mini-swe-agent harness is a separate, un-vendored repo"
)


def embedded_collect() -> str:
    """The copy inside the agent config, de-indented out of its yaml scalar."""
    m = re.search(
        r"cat > /opt/collect\.sh <<'COLLECT_EOF'\n(.*?)\n\s*COLLECT_EOF",
        YAML.read_text(), re.S,
    )
    assert m, "collect heredoc not found in the agent config"
    return "\n".join(
        line[4:] if line.startswith("    ") else line for line in m.group(1).split("\n")
    )


#: Paths the shared copy takes from the environment, and what the yaml copy hardcodes.
#: These differences are deliberate and documented: the two frameworks work in different
#: directories and run as different users, so a byte-identical script is impossible.
#: Normalising exactly these -- and nothing else -- keeps the guard on the question that
#: matters, which is whether the two capture the same THINGS.
PARAMETERISED = (
    ("$HARNESS_DIR", "/opt"),
    ('"$HARNESS_DIR/run_meta.sh"', "/opt/run_meta.sh"),
)


def emit_body(script: str) -> str:
    """The body of `emit()` -- what a bundle CONTAINS.

    Bounded at the function's closing brace rather than running to end of file, so the
    two copies are compared on the sections they emit and the commands that produce them,
    not on where the finished bundle is then copied to. Delivery legitimately differs:
    one framework has an /artifacts bind mount and the other does not. What must never
    differ is the evidence itself.
    """
    start = script.index("emit() {")
    end = script.index("\n}", start) + 2
    body = script[start:end]
    for parameterised, literal in PARAMETERISED:
        body = body.replace(parameterised, literal)
    return body


def test_the_two_copies_capture_exactly_the_same_thing():
    assert emit_body(SHARED.read_text()) == emit_body(embedded_collect()), (
        "harness/collect.sh and the copy in swebench_pr_compliance.yaml have drifted -- "
        "runs from the two frameworks are no longer byte-comparable"
    )


def test_the_shared_copy_does_not_hardcode_one_framework_s_working_directory():
    """The failure this parameterisation exists to prevent.

    mini-swe-agent works in /testbed; OpenHands copies /testbed to /workspace/<repo> and
    works there. A hardcoded `cd /testbed` under OpenHands would diff the pristine source
    and yield a clean, plausible, EMPTY patch for every run.
    """
    body = SHARED.read_text()
    assert "COLLECT_REPO_DIR" in body
    assert "\ncd /testbed" not in body


def test_the_patch_section_stays_last():
    """Everything after `===PATCH===` is taken as patch bytes, so nothing may follow it."""
    sections = re.findall(r'echo "===([A-Z_]+)==="', SHARED.read_text())
    assert sections[-1] == "PATCH", sections
    assert "PATCH_COMMITTED" in sections, "compliance scores what the agent CHOSE to commit"


def test_both_patch_sections_are_emitted():
    """Two patches, because the two scores ask different questions of one run and the
    container is destroyed straight after, so neither can be recomputed later."""
    body = SHARED.read_text()
    assert 'git diff "${START_HEAD}..HEAD"' in body      # proposed -> compliance
    assert 'git diff "${START_HEAD}"' in body            # done     -> SWE-bench


def test_emit_runs_exactly_once():
    """`git add -A` is not free of effect, so building the bundle twice is not idempotent."""
    assert SHARED.read_text().count("emit >") == 1


# --- the probe --------------------------------------------------------------------------

PROBE = ROOT / "harness/probe.sh"


def probe_keys(text: str) -> list[str]:
    """The keys a probe heredoc writes, in order."""
    # The yaml copy sits inside a block scalar, so both its body and its heredoc
    # terminator are indented; the standalone copy is not indented at all.
    m = re.search(r"probe_version=1\n(.*?)\n\s*EOF", text, re.S)
    assert m, "probe heredoc not found"
    return [
        line.split("=", 1)[0].strip()
        for line in m.group(1).splitlines()
        if "=" in line and not line.strip().startswith("#")
    ]


def test_both_probes_record_the_same_keys():
    """A framework whose probe records different keys is not auditable in the same terms.

    `bundle/trajectory.py::parse_probe` reads whatever it is given, so a missing key does
    not raise -- it becomes an absent fact, and an absent fact is indistinguishable from
    one that was measured and found empty.
    """
    shared = probe_keys(PROBE.read_text())
    embedded = probe_keys(YAML.read_text())
    assert shared == embedded, (
        f"probe key sets differ.\n  only shared:   {sorted(set(shared) - set(embedded))}"
        f"\n  only in yaml:  {sorted(set(embedded) - set(shared))}"
    )


@pytest.mark.parametrize("key", [
    "network_tcp", "rules_file_present", "rules_file_sha256", "rules_file_chars",
    "condition", "model", "framework", "start_head",
])
def test_the_keys_the_handoff_calls_load_bearing_are_present(key):
    """The keys without which a run is
    unauditable: what the environment was, and whether the treatment arrived whole."""
    assert key in probe_keys(PROBE.read_text())


def test_the_shared_probe_does_not_hardcode_one_framework_s_working_directory():
    body = PROBE.read_text()
    assert "PROBE_REPO_DIR" in body
    assert "[ -f /testbed/.pre-commit-config.yaml ]" not in body


def test_the_shared_probe_writes_run_meta_for_collect():
    """collect.sh runs from a quoted heredoc and cannot see the probe's shell, so
    START_HEAD has to be handed over on disk. An empty START_HEAD silently produces an
    empty patch, which is the failure collect.sh's three fallbacks exist to prevent."""
    body = PROBE.read_text()
    assert "run_meta.sh" in body
    assert "START_HEAD=" in body
    # And it must be written where collect.sh will look, which is the same env var.
    assert "HARNESS_DIR" in body


def test_both_scripts_agree_on_where_the_harness_lives():
    """probe.sh writes run_meta.sh; collect.sh reads it. If they disagree about the
    directory, START_HEAD comes back empty and every patch is empty -- a total data loss
    that looks exactly like an agent that changed nothing."""
    assert 'HARNESS_DIR="${HARNESS_DIR:-/opt}"' in PROBE.read_text()
    assert 'HARNESS_DIR="${HARNESS_DIR:-/opt}"' in SHARED.read_text()


def test_neither_script_assumes_it_can_write_to_opt():
    """One agent-server runs as a non-root user, for which /opt is unwritable. A
    hardcoded /opt fails there -- and `file_upload` reports that failure in a return
    value rather than raising, so it surfaces three steps later as 'no such file'."""
    for script in (PROBE, SHARED):
        body = script.read_text()
        for line in body.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or "HARNESS_DIR:-" in stripped:
                continue
            assert "/opt/" not in stripped, f"{script.name}: {stripped}"


def test_the_bundle_reaches_stdout_and_at_least_one_file():
    """Delivery may differ between frameworks; losing the bundle may not.

    stdout alone is not enough: one agent piped collect's output through `head` while
    working out why its bundle looked empty, which would have truncated the evidence to
    nothing had a file copy not also existed.
    """
    body = SHARED.read_text()
    assert "cat /tmp/collect.txt" in body, "the bundle must reach stdout"
    assert body.count("cp /tmp/collect.txt") >= 2, "and at least two file destinations"

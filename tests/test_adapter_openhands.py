"""The OpenHands adapter against event streams shaped like the ones V1 writes.

`test_adapters.py` checks that every adapter supplies the surface Layer A calls. That is
not enough here. The vocabularies in this adapter are the measurement the second
framework was bought for, and getting them wrong does not raise -- it reports that the
agent never read the rules and never fetched the docs, which is precisely the finding
under test. So these exercise the vocabularies on realistic input.

**These fixtures are hand-built from the SDK source, not captured from a run.** They
prove the adapter does what it intends on the schema as read; they do not prove the
schema was read correctly. Only a real trajectory does that -- grep it for the rules path
and the docs URL independently of the detector and check the counts agree.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from compliance.adapters import openhands as oh

RULES = "/rules/CONTRIBUTING_RULES.md"
DOCS = "https://docs.djangoproject.com/en/dev/internals/contributing/"


def action(event_id, tool, args, kind="ActionEvent"):
    return {"kind": kind, "id": event_id, "source": "agent", "tool_name": tool,
            "tool_call_id": f"call_{event_id}", "action": args}


def observation(action_id, text, tool="terminal", **extra):
    return {"kind": "ObservationEvent", "id": f"obs_{action_id}", "source": "environment",
            "tool_name": tool, "action_id": action_id,
            "observation": {"kind": "TerminalObservation", "content": text, **extra}}


def test_actions_pair_with_observations_by_id_not_position():
    """Two calls from one response, answered out of order.

    A positional zip gives every command *an* observation, so a wrong pairing looks
    exactly like a right one -- the output just belongs to a different command.
    """
    traj = {"history": [
        action("a1", "terminal", {"command": "echo first"}),
        action("a2", "terminal", {"command": "echo second"}),
        observation("a2", "SECOND"),
        observation("a1", "FIRST"),
    ]}
    got = oh.commands(traj)
    assert [(c.command, c.output) for c in got] == [
        ("terminal command=echo first", "FIRST"),
        ("terminal command=echo second", "SECOND"),
    ]


def test_an_action_with_no_observation_still_appears():
    """A rejected or errored call is evidence too, and must not shift the ones after it."""
    traj = {"history": [
        action("a1", "terminal", {"command": "cat x"}),
        action("a2", "terminal", {"command": "cat y"}),
        observation("a2", "Y ONLY"),
    ]}
    got = oh.commands(traj)
    assert len(got) == 2
    assert got[0].output == ""
    assert got[1].output == "Y ONLY"


@pytest.mark.parametrize("tool,args", [
    ("file_editor", {"command": "view", "path": RULES}),
    ("terminal", {"command": f"cat {RULES}"}),
    ("grep", {"pattern": "rule", "path": RULES}),
])
def test_reading_the_rules_file_is_detected_by_tool_and_by_shell_verb(tool, args):
    """Both routes count. `terminal` is a real shell, so `cat` inside it is a read."""
    command = oh.commands({"history": [action("a1", tool, args)]})[0]
    assert RULES in command.command
    assert not oh.METADATA_ONLY.match(command.command)
    assert [n for n, p in oh.READ_STRATEGIES if p.search(command.command)]


def test_listing_a_path_is_not_reading_it():
    """`glob` names files without conveying a byte -- the distinction the whole
    retrieval measure rests on."""
    command = oh.commands({"history": [action("a1", "glob", {"pattern": "/rules/*.md"})]})[0]
    assert oh.METADATA_ONLY.match(command.command)


@pytest.mark.parametrize("tool,args", [
    ("browser_navigate", {"url": DOCS}),
    ("terminal", {"command": f"curl -sL {DOCS}"}),
])
def test_fetching_is_detected_by_browser_tool_and_by_shell(tool, args):
    """The measurement the framework was bought for, both routes.

    `browser_get_content` is deliberately absent: it reads a page already fetched, so
    counting it too would make one browser visit score as two attempts against one for a
    `curl`, and the routes would not be comparable.
    """
    command = oh.commands({"history": [action("a1", tool, args)]})[0]
    assert oh.FETCH_ACTIONS.search(command.command)


@pytest.mark.parametrize("tool", [
    "browser_click", "browser_scroll", "browser_type", "browser_get_state",
    "browser_list_tabs", "browser_switch_tab", "browser_go_back",
])
def test_acting_on_a_page_already_open_is_not_another_fetch(tool):
    """Counting these would inflate one visit into a dozen retrieval attempts."""
    command = oh.commands({"history": [action("a1", tool, {"index": 1})]})[0]
    assert not oh.FETCH_ACTIONS.search(command.command)


def test_a_browser_call_that_arrived_unparsed_is_still_a_fetch():
    """A tool whose module was never imported deserialises to raw JSON arguments.

    Without the `tool_call` fallback the call would carry no URL, and the run would
    report zero fetches for a bookkeeping reason.
    """
    traj = {"history": [{
        "kind": "ActionEvent", "id": "a1", "source": "agent",
        "tool_name": "browser_navigate", "tool_call_id": "call_a1", "action": None,
        "tool_call": {"function": {"name": "browser_navigate",
                                   "arguments": f'{{"url": "{DOCS}"}}'}},
    }]}
    command = oh.commands(traj)[0]
    assert oh.FETCH_ACTIONS.search(command.command)
    assert DOCS in command.command


def test_pr_text_comes_from_the_agent_not_from_our_own_instruction():
    """The marker is in the prompt we add, so scanning every source scores the harness."""
    traj = {"instruction": f"...end with {oh.PR_MARKER} a title and body",
            "history": [
                {"kind": "MessageEvent", "id": "m0", "source": "user",
                 "content": [{"type": "text", "text": f"{oh.PR_MARKER} NOT THIS"}]},
                {"kind": "MessageEvent", "id": "m1", "source": "agent",
                 "content": [{"type": "text", "text": f"{oh.PR_MARKER} Fix the thing\n\nBody."}]},
            ]}
    assert oh.pr_text(traj) == "Fix the thing\n\nBody."


def test_submission_is_found_in_the_collect_output():
    """OpenHands has no notion of a submission; ours arrives as terminal output."""
    bundle = "===PROBE===\ncondition=guided\n===PATCH===\ndiff --git a/x b/x\n"
    traj = {"history": [
        action("a1", "terminal", {"command": "bash /opt/collect.sh"}),
        observation("a1", bundle),
    ]}
    assert oh.submission_text(traj).startswith("===PROBE===")


def test_pr_text_is_read_from_the_finish_tool_message():
    """V1 ends with a `finish` call carrying a final message to the user.

    That is a real field meant for exactly this, unlike the other scaffold's convention
    of scraping the last thought. A run that put its description there and nothing in its
    thoughts must not score as having written no PR description.
    """
    traj = {"history": [
        action("a1", "finish", {"kind": "FinishAction",
                                "message": f"{oh.PR_MARKER} Fix the parser\n\nDetails here."}),
    ]}
    assert oh.pr_text(traj) == "Fix the parser\n\nDetails here."


def test_a_finish_message_without_the_marker_is_not_a_pr_description():
    """Finishing is not the same as submitting a description."""
    traj = {"history": [
        action("a1", "finish", {"kind": "FinishAction", "message": "All done, tests pass."}),
    ]}
    assert oh.pr_text(traj) is None


# --- against events the SDK itself serialised -------------------------------------------
# The fixtures above are hand-built from reading the source; these are not. The file was
# produced by constructing real ActionEvent / ObservationEvent / FinishAction objects
# from the pinned SDK and dumping them with pydantic, so it is the schema as the SDK
# actually writes it rather than as I read it.
#
# It still is not a captured RUN: whether a real agent produces this sequence, and
# whether OpenHands truncates long observations in a way `was_truncated` recognises, is
# what DoD 3 and 4 settle. This closes the gap between "I read the source" and "the
# source does what I read"; it does not close the gap to a live trajectory.

REAL = Path(__file__).resolve().parent / "fixtures/openhands_v1_events.json"


@pytest.fixture(scope="module")
def real_traj():
    return json.loads(REAL.read_text())


def test_real_sdk_events_parse_into_commands(real_traj):
    commands = oh.commands(real_traj)
    assert [c.command.split()[0] for c in commands] == [
        "file_editor", "browser_navigate", "browser_click",
        "browser_get_content", "terminal", "finish",
    ]


def test_observations_pair_with_their_actions_in_real_events(real_traj):
    """Text is nested in a list of content blocks, not a bare string."""
    by_tool = {c.command.split()[0]: c for c in oh.commands(real_traj)}
    assert "C001 rule text" in by_tool["file_editor"].output
    assert "Contributing to Django" in by_tool["browser_navigate"].output
    assert by_tool["terminal"].returncode == 0


def test_the_rules_file_read_is_detected_in_real_events(real_traj):
    """What `analyse_rules_file` depends on: a `file_editor` view IS a read."""
    command = next(c for c in oh.commands(real_traj) if c.command.startswith("file_editor"))
    assert RULES in command.command
    assert not oh.METADATA_ONLY.match(command.command)
    assert [n for n, p in oh.READ_STRATEGIES if p.search(command.command)] == ["file_editor"]


def test_fetches_are_counted_once_per_visit_in_real_events(real_traj):
    """One visit, one attempt.

    The name of this test was right before its assertion was: it previously expected
    navigate AND get_content, which is two counts for one visit. get_content reads a page
    the navigation already fetched, and the click between them is not a fetch either.
    """
    fetches = [c.command.split()[0] for c in oh.commands(real_traj)
               if oh.FETCH_ACTIONS.search(c.command)]
    assert fetches == ["browser_navigate"]


def test_the_docs_url_survives_serialisation(real_traj):
    """The naive arm's whole measurement is whether this URL appears in an action."""
    assert any(DOCS in c.command for c in oh.commands(real_traj))


def test_submission_and_pr_text_come_out_of_real_events(real_traj):
    assert oh.submission_text(real_traj).startswith("===PROBE===")
    assert oh.pr_text(real_traj) == "Fix the thing\n\nBody."


def test_the_browser_opening_a_local_file_is_not_a_fetch():
    """The browser is a file viewer as well as a network client, and agents use it that way.

    One run opened `file:///tmp/repro_result.txt`, `/tmp/pytest_out.txt` and
    `/tmp/verify.txt` to read its own scratch output. Counting those reported NINE fetches
    on a run that never went online -- inflating the one number this framework exists to
    measure, in the direction that manufactures a finding.
    """
    for scheme in ("file:///tmp/out.txt", "about:blank", "data:text/html,x"):
        traj = {"history": [action("a1", "browser_navigate", {"url": scheme})]}
        command = oh.commands(traj)[0]
        assert not oh.FETCH_ACTIONS.search(command.command), scheme


def test_one_browser_visit_counts_once():
    """`browser_get_content` reads a page already fetched.

    Counting it as well as the navigation makes one browser visit score as two attempts
    while one `curl` scores as one -- and the two routes then cannot be compared, which is
    the whole reason for counting them together.
    """
    traj = {"history": [
        action("a1", "browser_navigate", {"url": DOCS}),
        action("a2", "browser_get_content", {"extract_links": False}),
    ]}
    counted = [c for c in oh.commands(traj) if oh.FETCH_ACTIONS.search(c.command)]
    assert len(counted) == 1
    assert counted[0].command.startswith("browser_navigate")


def test_a_remote_url_is_still_a_fetch():
    """The exclusion must not swallow the thing it exists beside."""
    traj = {"history": [action("a1", "browser_navigate", {"url": DOCS})]}
    assert oh.FETCH_ACTIONS.search(oh.commands(traj)[0].command)


@pytest.mark.parametrize("url,is_read,is_fetch", [
    (f"file://{RULES}", True, False),
    (DOCS, False, True),
])
def test_a_browser_call_is_a_read_or_a_fetch_by_where_it_points(url, is_read, is_fetch):
    """The mirror image of the local-URL exclusion, and the reason it must exist.

    Agents use the browser as a file viewer. If that is excluded from fetches but never
    added to reads, a guided agent that opens the mounted rules file in the browser is
    recorded as having read nothing -- "never opened", which is exactly the finding this
    arm exists to distinguish from "read it and ignored it".
    """
    command = oh.commands({"history": [action("a1", "browser_navigate", {"url": url})]})[0]
    assert bool([n for n, p in oh.READ_STRATEGIES if p.search(command.command)]) is is_read
    assert bool(oh.FETCH_ACTIONS.search(command.command)) is is_fetch


def test_the_rules_file_read_through_the_browser_is_counted():
    """End to end: the guided arm's measurement must survive an agent that prefers the
    browser to `cat`."""
    from compliance.core.retrieval import analyse_rules_file
    from compliance.core.models import EvidenceBundle
    traj = {"history": [
        action("a1", "browser_navigate", {"url": f"file://{RULES}"}),
        observation("a1", "C001 rule text " * 20, tool="browser_navigate"),
    ]}
    bundle = EvidenceBundle(
        instance_id="sympy__sympy-1", base_commit="", created_at="", condition="guided",
        model="m", files={}, commits=(), pr_text=None, commands=oh.commands(traj),
        probe={"rules_file_path": RULES, "rules_file_present": "yes",
               "rules_file_chars": "280"},
        framework="openhands",
    )
    access = analyse_rules_file(bundle)
    assert access.n_reads == 1, "a browser read of the rules file must count"
    assert "browser_local" in access.strategies

"""Layer D adapter: OpenHands V1, as instrumented for this experiment.

A function-calling agent. The model does not write shell text and get output back; it
emits tool calls, and the ones that matter here are ``terminal`` (a bash session),
``file_editor``, ``grep``, ``glob``, ``apply_patch``, and the ``browser_*`` toolset.

**Why the vocabularies below are not just shell verbs.** Under a bash-only scaffold,
"did the agent read the rules file" is answered by looking for ``cat``. Here the same act
is a ``file_editor`` view, and "did it go and fetch the docs" is a ``browser_navigate``
call rather than a ``curl``. Detecting only shell verbs would report that an OpenHands
agent never read and never fetched -- which is the exact shape of the finding this
framework was added to put at risk, manufactured by looking in the wrong place.

Both still matter, though: ``terminal`` runs a real shell, so an agent can and does
``cat`` a file or ``curl`` a URL *inside* a tool call. The command string synthesised by
``commands()`` is ``"<tool_name> <arguments>"`` precisely so one vocabulary matches the
tool name and the shell verb inside it, and neither route is invisible.

Trajectory shape: ``benchmarks/swebench/run_infer.py`` writes JSONL of ``EvalOutput``
records -- ``{instance_id, attempt, test_result, instruction, metadata, history}`` --
where ``history`` is the conversation's whole event stream. Events are a discriminated
union tagged by ``kind``, whose value is the class name, so an action is
``kind == "ActionEvent"`` and its result is the ``ObservationEvent`` whose ``action_id``
points back at it.

Pairing is therefore **by id, not by position**. That is worth stating because the other
adapter zips positionally: with parallel or rejected tool calls a positional zip pairs an
action with someone else's output, and the mistake is invisible -- every command still
has *an* observation.

Written against the pinned pair in ``frameworks/openhands.conf``. The tool names come
from the SDK's own rule, ``_camel_to_snake(cls.__name__).removesuffix("_tool")``, so
``TerminalTool`` is ``terminal`` and ``BrowserNavigateTool`` is ``browser_navigate``.
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from compliance.core.models import Command

PR_MARKER = "PR SUBMISSION:"

# Verbs and tools that put file *content* in front of the agent.
#
# `file_editor` earns its place on the tool name alone: its whole purpose is showing or
# changing file content, and its `view` command is the ordinary way an OpenHands agent
# reads anything. The shell entries are here because `terminal` is a real bash session --
# an agent that runs `cat /rules/CONTRIBUTING_RULES.md` inside a tool call has read the
# file just as surely as one that viewed it.
#
# `glob` and `ls` are deliberately absent: they name a path without conveying a byte of
# it. See METADATA_ONLY.
READ_STRATEGIES: tuple[tuple[str, re.Pattern], ...] = (
    ("file_editor", re.compile(r"\bfile_editor\b")),
    # The browser pointed at a LOCAL path. Agents do this -- one opened
    # `file:///tmp/repro_result.txt` and two others to read its own scratch output --
    # and nothing stops a guided agent opening the mounted rules file the same way.
    #
    # It is the exact mirror of the fetch rule: a browser call to a local path must NOT
    # count as retrieval, because it never touches the network, and MUST count as a
    # read, because the file lands in front of the agent. Without this the guided arm
    # would report `n_reads=0` on a run that read the whole file -- "never opened",
    # which is indistinguishable from an agent that ignored the treatment.
    ("browser_local", re.compile(r"\bbrowser_(navigate|get_content)\b(?!.*url=https?:)")),
    ("cat", re.compile(r"\b(cat|less|more)\b")),
    ("head_tail", re.compile(r"\b(head|tail)\b")),
    ("sed_awk", re.compile(r"\b(sed|awk)\b")),
    ("grep", re.compile(r"\bgrep\b|\b(rg|ag)\b")),
    ("python", re.compile(r"\bpython3?\b|\bopen\s*\(")),
    ("copy", re.compile(r"\bcp\b|>\s*\S+")),
)

# Actions that reference a path without conveying any of it. Anchored at the start so a
# `glob` call is metadata while `terminal ... | glob` -- which is not a thing, but the
# anchoring costs nothing -- would not accidentally silence a real read.
METADATA_ONLY = re.compile(r"^\s*(glob|task_tracker|ls|stat|file|wc|find|test|\[)\b")

# Actions that reach the network.
#
# This is the measurement the whole framework was added for, so it is the one place worth
# being explicit about scope. `browser_navigate` goes to a URL and `browser_get_content`
# reads what is there; both are retrieval. The other `browser_*` calls -- clicking,
# typing, scrolling, tab management -- act on a page already fetched, and counting them
# would inflate "fetch attempts" with what is really one visit.
#
# The shell alternatives stay, because `terminal` can still curl. An agent offered a
# browser that reaches for curl instead has still gone to look, and the question here is
# whether it went, not how.
#: A browser action whose URL is local. The browser is a general file viewer as well as
#: a network client, and agents use it that way: one run opened
#: `file:///tmp/repro_result.txt`, `/tmp/pytest_out.txt` and `/tmp/verify.txt` to read its
#: own scratch output. Those are not retrieval, and counting them reported nine fetches on
#: a run that never went online -- inflating the one number this framework exists to
#: measure, in the direction that would manufacture a finding.
_LOCAL_URL = re.compile(r"url=(file|about|data|chrome|view-source):", re.I)

# Actions that reach the network.
#
# `browser_navigate` only, NOT `browser_get_content`. Getting content reads a page already
# fetched, so counting both makes one browser visit score as two attempts while one `curl`
# scores as one -- and the two routes then cannot be compared, which is the whole point of
# counting them together. The page text still reaches `prose_chars_ingested`, because that
# is measured from the observation of whichever action retrieved it.
#
# The shell verbs stay: an agent offered a browser that reaches for `curl` instead has
# still gone to look, and the question is whether it went, not how.
_FETCH = re.compile(
    r"\bbrowser_navigate\b|\b(curl|wget)\b|urllib\.request|requests\.get|urlopen",
    re.I,
)


class _FetchActions:
    """`FETCH_ACTIONS` with the local-URL exclusion folded in.

    Layer A calls `.search(command)` and nothing else, so this presents that interface
    while being able to say "matches a fetch verb, but the target is local".
    """

    pattern = _FETCH.pattern

    def search(self, text: str):
        if not text or _LOCAL_URL.search(text):
            return None
        return _FETCH.search(text)


FETCH_ACTIONS = _FetchActions()

# Tags the harness wraps output in on its way to the model. V1 observations carry their
# text as structured content rather than an XML envelope, so this is near-empty compared
# with a template-driven scaffold -- but it must exist and must be a compiled pattern,
# because Layer A strips with it unconditionally.
WRAPPER_TAGS = re.compile(r"</?(output|error|observation|browser_observations)>")

#: Event kinds, which the SDK tags with the class name itself.
_ACTION = "ActionEvent"
_OBSERVATION = "ObservationEvent"
#: Observation kinds that carry a result but are not a tool's own output.
_ERROR_KINDS = ("AgentErrorEvent", "UserRejectObservation")


def _history(traj: dict[str, Any]) -> list[dict[str, Any]]:
    """The event stream, whether handed one EvalOutput record or a bare history."""
    if isinstance(traj.get("history"), list):
        return [e for e in traj["history"] if isinstance(e, dict)]
    if isinstance(traj.get("events"), list):
        return [e for e in traj["events"] if isinstance(e, dict)]
    return []


def _action_arguments(event: dict[str, Any]) -> str:
    """The tool call's arguments, flattened to one searchable string.

    Read from ``action`` when the SDK deserialised it, and from the raw
    ``tool_call.function.arguments`` JSON when it did not -- a tool registered by a
    module that was not imported comes back unparsed, and a browser call that arrived as
    raw JSON must not become invisible to `FETCH_ACTIONS` for that reason.
    """
    action = event.get("action")
    if isinstance(action, dict):
        parts = [f"{k}={v}" for k, v in action.items() if k != "kind" and v is not None]
        if parts:
            return " ".join(parts)
    call = event.get("tool_call")
    if isinstance(call, dict):
        arguments = (call.get("function") or {}).get("arguments")
        if isinstance(arguments, str):
            return arguments
        if isinstance(arguments, dict):
            return json.dumps(arguments)
    return ""


def _observation_text(event: dict[str, Any]) -> str:
    """Whatever the agent saw back, as text."""
    observation = event.get("observation")
    if isinstance(observation, dict):
        content = observation.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                block.get("text", "") for block in content if isinstance(block, dict)
            )
        for key in ("output", "text", "result"):
            if isinstance(observation.get(key), str):
                return observation[key]
    if isinstance(event.get("error"), str):
        return event["error"]
    return ""


def commands(traj: dict[str, Any]) -> tuple[Command, ...]:
    """Every tool call the agent made, paired with the observation it produced.

    Paired by ``action_id`` rather than by position. OpenHands can emit several tool
    calls from one model response and an observation can be missing entirely (a rejected
    or errored call), so position is not a reliable join -- and a wrong join here is
    silent, because every command still ends up with *an* observation.

    The synthesised command string is ``"<tool_name> <arguments>"``, which is what lets
    one regex vocabulary see both the tool and the shell verb inside it.
    """
    events = _history(traj)
    by_action: dict[str, dict[str, Any]] = {}
    for event in events:
        if event.get("kind") in (_OBSERVATION, *_ERROR_KINDS):
            if action_id := event.get("action_id"):
                by_action.setdefault(action_id, event)

    out: list[Command] = []
    for event in events:
        if event.get("kind") != _ACTION:
            continue
        tool = event.get("tool_name") or ""
        arguments = _action_arguments(event)
        observation = by_action.get(event.get("id") or "", {})
        out.append(
            Command(
                index=len(out),
                command=f"{tool} {arguments}".strip(),
                output=_observation_text(observation),
                returncode=_returncode(observation),
            )
        )
    return tuple(out)


def _returncode(observation: dict[str, Any]) -> Optional[int]:
    payload = observation.get("observation")
    if isinstance(payload, dict):
        for key in ("exit_code", "returncode", "return_code"):
            value = payload.get(key)
            if isinstance(value, int):
                return value
    if observation.get("kind") in _ERROR_KINDS:
        return 1
    return None


def pr_text(traj: dict[str, Any]) -> Optional[str]:
    """Text the agent wrote after ``PR SUBMISSION:``.

    Only the agent's own messages count. The marker is also in the instruction we add to
    the prompt, so scanning everything would return our own words and score the harness
    instead of the model -- the same trap the other adapter documents.

    The **finish tool's ``message`` is searched first**, and is where the PR description
    is asked for. V1 ends a task with a ``finish`` call carrying a "final message to the
    user", which is a real field for exactly this rather than the other scaffold's
    convention of scraping free text out of the last thought. A run that put its
    description there and nothing in its thoughts would otherwise score as having written
    no PR description at all.
    """
    for event in reversed(_history(traj)):
        if event.get("source") != "agent":
            continue
        for text in _finish_messages(event) + _texts(event):
            if PR_MARKER in text:
                return text.split(PR_MARKER, 1)[1].strip()
    return None


def _finish_messages(event: dict[str, Any]) -> list[str]:
    """The message carried by a ``finish`` call, if this event is one."""
    action = event.get("action")
    if isinstance(action, dict) and isinstance(action.get("message"), str):
        return [action["message"]]
    return []


def _texts(event: dict[str, Any]) -> list[str]:
    """Every free-text field an agent event can carry its prose in."""
    found: list[str] = []
    for key in ("thought", "content", "message"):
        value = event.get(key)
        if isinstance(value, str):
            found.append(value)
        elif isinstance(value, list):
            found.extend(
                block.get("text", "") for block in value if isinstance(block, dict)
            )
    message = event.get("llm_message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            found.append(content)
        elif isinstance(content, list):
            found.extend(
                block.get("text", "") for block in content if isinstance(block, dict)
            )
    return [t for t in found if t]


def submission_text(traj: dict[str, Any]) -> str:
    """The evidence bundle ``collect.sh`` printed, unparsed.

    Layer A applies our ``===SECTION===`` conventions to whatever comes back. The bundle
    is produced inside the runtime by our own collect script, so it reaches the
    trajectory as the output of the terminal call that ran it -- OpenHands has no notion
    of a "submission" of its own, and `test_result` is the benchmark's grading, not ours.

    The last matching observation wins: a run that printed the bundle more than once has
    a final state that supersedes the earlier ones.
    """
    for key in ("submission", "instruction"):
        value = traj.get(key)
        if isinstance(value, str) and "===PROBE===" in value:
            return value
    result = traj.get("test_result")
    if isinstance(result, dict):
        for value in result.values():
            if isinstance(value, str) and "===PROBE===" in value:
                return value
    for command in reversed(commands(traj)):
        if "===PROBE===" in command.output:
            return command.output
    return ""


def run_env(traj: dict[str, Any]) -> dict[str, str]:
    """The RUN_* metadata recorded for this run.

    OpenHands does not record the container environment the way the other scaffold's
    config does, so this is thin by comparison. The probe is the authority regardless --
    it is written inside the container by our own startup script and is the only record
    of what actually ran.
    """
    metadata = traj.get("metadata")
    if not isinstance(metadata, dict):
        return {}
    details = metadata.get("details")
    env = details.get("env") if isinstance(details, dict) else None
    out = {str(k): str(v) for k, v in env.items()} if isinstance(env, dict) else {}

    # RUN_MODEL, from where THIS framework records it.
    #
    # `build_bundle` resolves the model as RUN_MODEL -> probe -> a trajectory shape that
    # belongs to the other scaffold. The probe is written inside the container at startup,
    # so a run that died before startup has none -- and every such run then resolves to
    # "unknown" and collides with every other probe-less run of the same instance and
    # condition. That is a key which is not unique: two runs of different models collapse
    # into one, silently, exactly the failure `test_every_stored_run_scores_under_a_distinct_key`
    # exists to catch. Observed on four failed cells of one instance, 3 Sep 2026.
    #
    # The probe stays the authority when it exists; this is only the fallback beneath it.
    llm = metadata.get("llm")
    model = llm.get("model") if isinstance(llm, dict) else None
    if model and "RUN_MODEL" not in out:
        out["RUN_MODEL"] = str(model)
    return out


#: Ended by calling the finish tool -- the only clean ending this framework has.
SUBMITTED = "Submitted"
#: Ran out of turns. The run returns NOTHING when this happens, so a trajectory that
#: reaches it is a truncated run rather than a short one.
LIMIT = "LimitsExceeded"


def exit_status(traj: dict[str, Any]) -> str:
    """How the run ended, in the vocabulary the other framework already uses.

    This is not decoration. At scale it is what separates "the agent looked and found
    nothing" from "the agent was cut off before it got there" -- two readings of the same
    zero, and only one of them is a finding. OpenHands records no status field of its own,
    so it is derived from the event stream: a `finish` call is a clean ending, an error
    event is not, and neither means the run merely stopped.
    """
    result = traj.get("test_result")
    if isinstance(result, dict):
        for key in ("exit_status", "status"):
            if isinstance(result.get(key), str) and result[key]:
                return result[key]
    if isinstance(traj.get("error"), str) and traj["error"]:
        return traj["error"]

    events = _history(traj)
    for event in reversed(events):
        kind = event.get("kind")
        if kind in ("ConversationErrorEvent", "AgentErrorEvent"):
            detail = event.get("error") or event.get("message") or ""
            if "MaxIterations" in str(detail) or "maximum iterations" in str(detail):
                return LIMIT
            return str(detail)[:120] or "Error"
        if kind == "ActionEvent" and event.get("tool_name") == "finish":
            return SUBMITTED
    return ""


def cost_usd(traj: dict[str, Any]) -> Optional[float]:
    """What the run cost, from ``metrics.accumulated_cost``.

    `metrics` is a first-class field on the record this framework writes. An earlier
    version looked in `metadata` and `test_result`, found neither, and returned None for
    every run -- silently, because a missing cost is indistinguishable from a free run.

    **Treat the number with suspicion.** Across one instance the four models reported
    $0.00011 to $1.82, and a 28-call run costing a hundredth of a cent is not credible;
    the pricing table behind it does not appear to know these OpenRouter ids. Recorded
    because a per-run figure that can be reconciled later is worth more than none, but
    the key-level total is what should be trusted for budgeting.
    """
    for holder in (traj.get("metrics"), traj.get("metadata"), traj.get("test_result")):
        if isinstance(holder, dict):
            for key in ("accumulated_cost", "cost", "total_cost"):
                value = holder.get(key)
                if isinstance(value, (int, float)):
                    return float(value)
    return None


def observation_payload(text: str) -> str:
    """What the agent actually saw, with our wrapper tags removed."""
    return WRAPPER_TAGS.sub("", text).strip() if text else ""


def was_truncated(text: str) -> bool:
    """Did the scaffold withhold part of this observation, per its own marker?

    **Assume the guided treatment is broken until this is measured.** The other scaffold
    silently elided the middle of the mounted rules file and delivered 58% of it,
    withholding 59 of 142 rules including a whole category. OpenHands truncates on its
    own terms and these markers are read from its source, not confirmed against a real
    observation -- so `analyse_rules_file` reporting 100% coverage is what promotes them
    from plausible to known.
    """
    if not text:
        return False
    lowered = text.lower()
    return any(
        marker in lowered
        for marker in ("<response clipped>", "truncated", "elided", "[... omitted")
    )

"""The salience manipulation must change WHERE the retrieval instruction sits, not what
it says. If the wording differs too, a difference in retrieval confounds salience with
content and the comparison means nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from jinja2 import StrictUndefined, Template

CONFIG = (
    Path(__file__).resolve().parents[1]
    / "mini-swe-agent-run/mini-swe-agent/swebench_pr_compliance.yaml"
)
SENTENCE = (
    "**Fetch and read those guidelines before you start any work**, and follow them. Follow the\n"
    "links from that index page to the sections relevant to your change."
)


def render(condition: str) -> str:
    config = yaml.safe_load(CONFIG.read_text())
    env = dict(config["environment"]["env"])
    env["RUN_CONDITION"] = condition
    env["RUN_DOCS_URL"] = "https://docs.example.org/contributing/index.html"
    return Template(config["agent"]["instance_template"], undefined=StrictUndefined).render(
        task="TASK", env=env
    )


@pytest.mark.parametrize("condition", ["none", "naive", "naive-salient", "guided"])
def test_every_condition_renders(condition):
    assert len(render(condition)) > 500


def test_both_naive_variants_carry_the_identical_instruction():
    """Same words. Only the position may differ."""
    for condition in ("naive", "naive-salient"):
        assert SENTENCE in render(condition), f"{condition} lost the retrieval sentence"


def test_salience_moves_the_instruction_much_earlier():
    def depth(condition):
        lines = render(condition).splitlines()
        index = next(i for i, l in enumerate(lines) if "Fetch and read those guidelines" in l)
        return index / len(lines)

    assert depth("naive") > 0.5, "baseline should sit late in the prompt"
    assert depth("naive-salient") < 0.2, "salient should sit near the top"


def test_the_instruction_appears_exactly_once_in_each_variant():
    """Duplicating it would raise salience by repetition as well as position."""
    for condition in ("naive", "naive-salient"):
        assert render(condition).count("Fetch and read those guidelines") == 1


@pytest.mark.parametrize("condition", ["none", "naive", "naive-salient", "guided"])
def test_workflow_is_numbered_consecutively(condition):
    workflow = re.search(r"## Recommended Workflow\n\n(.*?)\n\n##", render(condition), re.S).group(1)
    numbers = re.findall(r"^\s*(\d+)\.", workflow, re.M)
    assert numbers == [str(i) for i in range(1, len(numbers) + 1)], f"{condition}: {numbers}"


def test_no_modal_verbs_are_handed_to_the_agent():
    """must / should / never is our strength taxonomy. Supplying it as a search pattern
    would leak the rubric the corpus is built on."""
    for condition in ("naive", "naive-salient"):
        block = render(condition).split("## Compliance")[-1].split("## Submission")[0]
        assert "grep" not in block.lower()


def test_guided_never_mentions_a_url():
    assert "https://" not in render("guided").split("## Compliance")[1].split("## Submission")[0]


# --- observation cap: the guided treatment must arrive intact -----------------------

RULES_FILE = Path(__file__).resolve().parents[1] / "rules/sympy/CONTRIBUTING_RULES.md"


def render_observation(output: str) -> str:
    config = yaml.safe_load(CONFIG.read_text())
    return Template(config["model"]["observation_template"], undefined=StrictUndefined).render(
        output={"output": output, "returncode": 0, "exception_info": ""}
    )


def test_the_rules_file_is_never_truncated():
    """Truncation keeps head+tail and elides the MIDDLE. On the first guided batch that
    cost 59 of 142 rules -- the whole Specialized changes category and 31 of 33 Tests
    rules -- in every run that read the file."""
    rendered = render_observation(RULES_FILE.read_text())
    assert "<elided_chars>" not in rendered
    assert rendered.count("\n- ") == 142, "not every rule survived into the observation"
    for category in ("Specialized changes", "Tests and test style", "Git and commit conventions"):
        assert category in rendered, f"{category} elided"


def test_everything_else_still_truncates():
    """The exemption must be surgical: a large log dump is still capped."""
    rendered = render_observation("x" * 40000)
    assert "<elided_chars>" in rendered and len(rendered) < 11000


def test_the_sentinel_is_kept_in_sync_between_generator_and_harness():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rules"))
    from build_contributing_rules import RULES_FILE_SENTINEL

    assert RULES_FILE_SENTINEL in CONFIG.read_text(), "harness does not key on the generator's sentinel"
    assert RULES_FILE.read_text().startswith(RULES_FILE_SENTINEL)


# --- cross-framework parity ------------------------------------------------------------
# The framework axis asks whether the naive arm's zero retrieval survives a scaffold with
# a browser. That question is only answerable if the two frameworks ask for the same
# thing in the same words. If the wording drifts, a difference in retrieval is partly a
# difference in prompt, and the comparison measures nothing in particular -- the same
# reasoning as the salience tests above, one level up.

OPENHANDS_TEMPLATE = (
    Path(__file__).resolve().parents[1]
    / "frameworks/openhands/prompts/compliance.j2"
)

GUIDED_INSTRUCTION = (
    "**Read `/rules/CONTRIBUTING_RULES.md` before you start any work**, and follow it. "
    "That file\nis this project's contribution guidelines, extracted in full."
)

#: Where the rules file lands under OpenHands. It is NOT /rules, and cannot be: that
#: agent-server image ends with `USER openhands`, so / and /opt are root-owned and every
#: write fails -- silently, since the upload reports failure in a return value.
OPENHANDS_RULES_PATH = "/workspace/.compliance/rules/CONTRIBUTING_RULES.md"


def _same_words(text: str) -> str:
    """The instruction with the mount point normalised away.

    The two frameworks cannot share a path -- one runs as root, the other does not -- but
    they MUST share the wording. Normalising only the path keeps the guarantee that
    matters: a difference in retrieval between frameworks is not a difference in what
    they were asked.
    """
    return _normalise(text.replace(OPENHANDS_RULES_PATH, "/rules/CONTRIBUTING_RULES.md"))


def _normalise(text: str) -> str:
    """Strip the indentation each harness applies, so only the words are compared."""
    return "\n".join(line.strip() for line in text.strip().splitlines())


def render_openhands(condition: str) -> str:
    """What the agent is actually handed.

    Rendered rather than read as source, so a jinja comment explaining a change cannot be
    mistaken for the change itself -- which is exactly what an earlier version of
    `test_..._does_not_also_say_minimal_changes...` did.
    """
    # Rendered exactly as upstream's get_instruction() does it: the condition travels on
    # `metadata.details`, not as a top-level variable.
    return Template(OPENHANDS_TEMPLATE.read_text(), undefined=StrictUndefined).render(
        metadata={"details": {
            "condition": condition,
            "docs_url": "https://docs.example.org/contributing/index.html",
            "rules_path": OPENHANDS_RULES_PATH,
            "collect_script": "/workspace/.compliance/collect.sh",
        }},
        instance={"repo_path": "/testbed", "problem_statement": "ISSUE",
                  "base_commit": "deadbeef"},
    )


@pytest.mark.parametrize("condition", ["naive", "guided"])
def test_every_openhands_condition_renders(condition):
    assert len(render_openhands(condition)) > 500


@pytest.mark.parametrize("sentence,condition", [
    (SENTENCE, "naive"), (GUIDED_INSTRUCTION, "guided"),
])
def test_both_frameworks_ask_for_retrieval_in_the_same_words(sentence, condition):
    """The treatment must be the same text under either scaffold."""
    assert _normalise(sentence) in _same_words(render_openhands(condition)), (
        "the OpenHands template has drifted from the mini-swe-agent wording; a framework "
        "difference in retrieval would then be partly a wording difference"
    )


def test_openhands_guided_never_mentions_a_url():
    """Same invariant the other framework is held to: the guided arm's treatment is the
    mounted file, and naming the docs URL would hand it a second route."""
    assert "docs.example.org" not in render_openhands("guided")


def test_the_openhands_template_carries_only_the_two_live_arms():
    """`none` and `naive-salient` are retired and must not reappear in a new framework."""
    body = OPENHANDS_TEMPLATE.read_text()
    conditions = set(re.findall(r"condition == '([a-z-]+)'", body))
    assert conditions == {"naive", "guided"}, conditions


def test_the_openhands_template_requires_a_commit_and_the_collect_script():
    """Compliance is scored on what was COMMITTED, and collect.sh is what captures it."""
    body = render_openhands("guided")
    assert "git commit" in body
    assert "collect.sh" in body
    assert "PR SUBMISSION:" in body


def test_the_openhands_template_does_not_also_say_minimal_changes_to_non_test_files():
    """The stock sentence is REPLACED, not appended after.

    Leaving both would tell the agent to add tests and to change no test files in the
    same breath, and which one it followed would be its choice rather than our design.
    """
    body = render_openhands("naive")
    assert "minimal changes to non-test files" not in body
    assert "DON'T have to modify the testing logic" not in body


def test_a_missing_condition_would_not_silently_empty_the_treatment():
    """Upstream renders with a plain jinja Environment, so an unbound variable becomes "".

    That failure is invisible: the run proceeds, the prompt looks well-formed, and the
    arm is a control wearing a treatment's label. Each arm must render a substantial
    Compliance section, not merely a heading.
    """
    for condition in ("naive", "guided"):
        body = render_openhands(condition)
        section = body.split("## Compliance", 1)[1].split("## Submission", 1)[0]
        assert len(section.strip()) > 120, (condition, section)

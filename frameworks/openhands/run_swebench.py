"""Run one SWE-bench instance under OpenHands, instrumented for this experiment.

Wraps upstream's `benchmarks/swebench/run_infer.py` rather than forking it: OpenHands
stays stock, and what we measure is OpenHands behaving as OpenHands. Five things are
added, and each exists because leaving it out loses data silently rather than loudly.

1.  **The browser is turned on, in two places.** Upstream disables it for SWE-bench
    (`enable_browser=False`, "Disable browser tools in CLI mode"), which is reasonable for
    an offline coding benchmark and fatal for us -- the browser is the entire reason this
    framework is in the design. It is gated *twice*: once on the tool list, and again in
    the system prompt, which wraps its `<BROWSER_TOOLS>` guidance in
    `{% if enable_browser %}`. Setting only the first hands the agent tools its prompt
    never mentions and no guidance for using them -- an agent that would under-use the
    browser, biasing the one number this framework was bought to produce.

2.  **The probe and the collect script are installed and run.** `===PROBE===` and
    `===SECTION===` are ours, shared with the other framework so the two produce
    comparable bundles. Without the probe a run has no record of its environment and
    cannot be audited afterwards; the container is destroyed the moment it ends.

3.  **The rules file is placed for the guided arm.** That file IS the treatment.

4.  **Our instruction template replaces upstream's**, carrying the condition. The system
    prompt is left alone.

5.  **Results are written into `runs/<repo>/<framework>/<model>/<instance>/<condition>/
    attemptN/`**, the layout `compliance/core/paths.py` defines, with `patch.diff` last --
    it is the completion marker every resume in this project keys on.

**The ordering in `evaluate_instance` is load-bearing.** Upstream runs
`git add -A && git commit -m 'patch'` after the agent finishes, as `OpenHands Evaluation`.
Compliance scores what the agent *chose* to commit, so if that ran before our collect,
every run would show an agent that committed everything with a message it never wrote,
and every git-convention rule would be grading the harness. `collect.sh` is invoked by the
agent itself, inside the conversation, before upstream ever gets there.
"""

from __future__ import annotations

import logging
import os
import shlex
from pathlib import Path
from typing import Any

from benchmarks.swebench import run_infer as upstream
from benchmarks.utils.models import EvalInstance, EvalOutput
from benchmarks.utils.tool_presets import get_tools_for_preset
from openhands.sdk import Agent, Conversation
from openhands.sdk.context.condenser import LLMSummarizingCondenser
from openhands.sdk.workspace import RemoteWorkspace

logger = logging.getLogger("compliance.openhands")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HARNESS = PROJECT_ROOT / "harness"

# Everything we put in the container goes under the workspace, NOT /opt.
# The agent-server image ends with `USER openhands`, so /opt is root-owned and every
# write there fails -- silently, because `file_upload` reports failure in its return
# value rather than raising. `/workspace` is the working dir and is owned by that user.
HARNESS_DIR = "/workspace/.compliance"
CONTAINER_PROBE = f"{HARNESS_DIR}/probe.sh"
CONTAINER_COLLECT = f"{HARNESS_DIR}/collect.sh"
#: What the AGENT is told to run: the wrapper, not the script itself.
CONTAINER_COLLECT_WRAPPER = f"{HARNESS_DIR}/collect"
CONTAINER_RULES = f"{HARNESS_DIR}/rules/CONTRIBUTING_RULES.md"

from bundle_io import patch_from_bundle, write_run_dir  # noqa: E402  (SDK-free half)


class CompliancePatchedEvaluation(upstream.SWEBenchEvaluation):
    """Upstream's evaluator with the experiment's instrumentation around it.

    Subclassed rather than copied. `evaluate_instance` is documented upstream as a hook,
    and every line of it we do not need to change is a line that keeps working when the
    pin moves.
    """

    # Declared as pydantic FIELDS, not assigned in a hand-written __init__. `Evaluation`
    # is a BaseModel: an __init__ that assigns afterwards either raises or silently drops
    # them depending on model config, and a silently dropped `condition` would run every
    # cell as the default arm while the directory it is filed under says otherwise.
    condition: str = "naive"
    docs_url: str = ""
    enable_browser: bool = True
    rules_file: Path | None = None
    run_dir: Path | None = None

    # -- instrumentation ---------------------------------------------------------------

    def _install_harness(self, workspace: RemoteWorkspace, repo_path: str,
                         instance: EvalInstance) -> None:
        """Put the probe and collect scripts in the container and run the probe.

        Uploaded rather than heredoc'd through `execute_command`: these are ~130 lines of
        shell containing quotes, `$(...)` and nested heredocs, and every layer of shell
        quoting between here and the container is a chance to corrupt them in a way that
        would only show up as a malformed bundle.

        The probe runs AFTER the repository is in place, because it records `start_head`
        and `collect.sh` derives the patch range from it. An empty `start_head` produces
        an empty patch -- the failure collect.sh's three fallbacks exist to prevent, and
        which would look like an agent that changed nothing.
        """
        workspace.execute_command(f"mkdir -p {HARNESS_DIR}/rules")
        for local, remote in ((HARNESS / "probe.sh", CONTAINER_PROBE),
                              (HARNESS / "collect.sh", CONTAINER_COLLECT)):
            _upload(workspace, local, remote)
        workspace.execute_command(f"chmod +x {CONTAINER_PROBE} {CONTAINER_COLLECT}")

        # A wrapper with this run's paths baked in, because the AGENT invokes collect and
        # invokes it with no environment at all. Both defaults in collect.sh are wrong
        # here -- COLLECT_REPO_DIR would be /testbed (the pristine source, not the copy
        # the agent worked in) and HARNESS_DIR would be /opt (where nothing of ours is) --
        # and the result is not an error. It is a complete, well-formed, EMPTY bundle:
        # no probe, no commits, no patch, `start_head_source=fallback_head_uncommitted_only`.
        #
        # The alternative, telling the agent to set the variables itself, was tried by an
        # agent unprompted when its bundle looked wrong: it guessed COLLECT_REPO_DIR and
        # HARNESS_DIR across four attempts. Instructions the agent has to get right are
        # instructions it can get wrong, and this one is not part of what we measure.
        wrapper = (
            "#!/usr/bin/env bash\n"
            f"export HARNESS_DIR={HARNESS_DIR}\n"
            f"export COLLECT_REPO_DIR={repo_path}\n"
            f'exec bash {CONTAINER_COLLECT} "$@"\n'
        )
        written = workspace.execute_command(
            f"printf '%s' {shlex.quote(wrapper)} > {CONTAINER_COLLECT_WRAPPER} "
            f"&& chmod +x {CONTAINER_COLLECT_WRAPPER}"
        )
        if written.exit_code != 0:
            raise RuntimeError(f"could not write the collect wrapper: {written.stderr}")

        if self.condition == "guided":
            if self.rules_file is None or not self.rules_file.exists():
                raise RuntimeError(
                    f"condition=guided needs a rules file; {self.rules_file} is missing. "
                    f"Without it the guided arm is silently just a control."
                )
            _upload(workspace, self.rules_file, CONTAINER_RULES)
            workspace.execute_command(f"chmod 444 {CONTAINER_RULES}")
            # The treatment is verified INSIDE the container, not assumed from a
            # successful upload: what the probe hashes is the file the agent can read.
            check = workspace.execute_command(f"wc -c < {CONTAINER_RULES}")
            if check.exit_code != 0 or not check.stdout.strip().isdigit():
                raise RuntimeError(f"rules file unreadable in container: {check.stderr}")
            logger.info("rules file in container: %s chars", check.stdout.strip())

        env = " ".join([
            f"HARNESS_DIR={HARNESS_DIR}",
            f"PROBE_RULES_PATH={CONTAINER_RULES}",
            f"PROBE_REPO_DIR={repo_path}",
            # From the instance itself, not from the environment. Passing these through
            # the shell meant nobody set them and the probe recorded them EMPTY -- which
            # does not fail: `reconstruct.py` rebuilds post-patch file bodies from
            # `base_commit` + patch, so without it every rule that reads a file body
            # returns `parse_error` instead of a verdict. Measured on one run: 84 of 142
            # rules, and a conditional pass rate 8 points below the same agent under the
            # other framework, from a defect rather than from behaviour.
            f"PROBE_INSTANCE_ID={instance.id}",
            f"PROBE_BASE_COMMIT={instance.data.get('base_commit', '')}",
            f"PROBE_CREATED_AT={instance.data.get('created_at', '')}",
            f"RUN_CONDITION={self.condition}",
            # The REPORTING id, which is what the corpus is keyed on -- not necessarily
            # where the request went. RUN_ROUTE records that separately so a run rerouted
            # to a different provider stays auditable without splitting the aggregate.
            f"RUN_MODEL={os.environ.get('RUN_MODEL', 'unknown')}",
            f"RUN_ROUTE={os.environ.get('RUN_ROUTE') or os.environ.get('RUN_MODEL', 'unknown')}",
            "RUN_FRAMEWORK=openhands",
            f"RUN_REASONING={os.environ.get('RUN_REASONING', 'default')}",
            f"RUN_ATTEMPT={os.environ.get('RUN_ATTEMPT', '1')}",
            f"RUN_DOCS_URL={self.docs_url!r}",
        ])
        result = workspace.execute_command(f"{env} bash {CONTAINER_PROBE}", timeout=120)
        if result.exit_code != 0:
            # Loud: a run with no probe cannot be audited, and the container is about to
            # be destroyed. Better to lose the run than to store an unauditable one.
            raise RuntimeError(f"probe failed ({result.exit_code}): {result.stderr}")
        logger.info("probe recorded %d keys", result.stdout.count("="))

    def _build_agent(self) -> Agent:
        """Stock agent, with the browser turned on in BOTH places it is gated."""
        tools = get_tools_for_preset(
            preset=self.metadata.tool_preset, enable_browser=self.enable_browser,
        )
        # The condenser is ON by default upstream (INFER_DEFAULTS sets enable_condenser)
        # and summarises history once it passes `condenser_max_size`. Dropping it does
        # not fail fast: a long run simply exceeds the context window late, after the
        # money is spent, and the cell has to be redone.
        condenser = None
        if self.metadata.enable_condenser:
            condenser = LLMSummarizingCondenser(
                llm=upstream.build_eval_llm(self.metadata.llm, usage_id="condenser"),
                max_size=self.metadata.condenser_max_size,
                max_tokens=self.metadata.condenser_max_tokens,
                keep_first=self.metadata.condenser_keep_first,
            )
        return Agent(
            llm=upstream.build_eval_llm(self.metadata.llm),
            tools=tools,
            # `cli_mode` is upstream's; `enable_browser` un-hides the <BROWSER_TOOLS>
            # section of the STOCK system prompt. Passing the tools without it leaves the
            # agent holding tools it was never told about.
            #
            # That section is OpenHands' own text, including its preference for trying
            # curl/wget before the browser, and it is left exactly as upstream wrote it.
            # WHETHER to reach for the browser is the agent's decision and part of what is
            # being measured, so nothing here may push it either way.
            system_prompt_kwargs={"cli_mode": True, "enable_browser": self.enable_browser},
            condenser=condenser,
            agent_context=upstream.create_agent_context(),
        )

    def prepare_workspace(self, instance, resource_factor: int = 1,
                          forward_env: list[str] | None = None):
        """Upstream's workspace, built from a target that HAS a browser when we want one.

        Upstream builds the `source-minimal` image, which omits Chromium -- consistent
        with disabling the browser for SWE-bench. Enabling the browser tools against that
        image does not fail at startup: the agent gets the tools, calls one, and the
        agent-server answers 500 with "Chromium is required for browser operations but is
        not installed". The run then dies mid-conversation, after the model has been paid.

        `source` is the same image plus the layer that installs Chromium. It is markedly
        heavier -- that layer also brings a VNC desktop we have no use for -- so it is
        built ONLY for the browser arm, and the browser-off arm keeps upstream's minimal
        image and upstream's build cost.
        """
        if self.enable_browser:
            original = upstream.constants.DEFAULT_BUILD_TARGET
            upstream.constants.DEFAULT_BUILD_TARGET = "source"
            try:
                return super().prepare_workspace(instance, resource_factor, forward_env)
            finally:
                upstream.constants.DEFAULT_BUILD_TARGET = original
        return super().prepare_workspace(instance, resource_factor, forward_env)

    # -- the hook ----------------------------------------------------------------------

    def evaluate_instance(
        self, instance: EvalInstance, workspace: RemoteWorkspace
    ) -> EvalOutput:
        assert isinstance(workspace, RemoteWorkspace)

        repo_path = self.get_repo_path(instance)
        instance.data["repo_path"] = repo_path

        # Upstream's own preparation, kept verbatim: the image ships the repository at
        # /testbed and the agent works on a copy.
        #
        # TIMEOUTS ARE EXPLICIT HERE. `execute_command` defaults to 30 s
        # (openhands/sdk/workspace/base.py), which is generous for a shell one-liner and
        # far too short for copying a whole repository inside an EMULATED container while
        # other shards compete for the same disk. When it trips, the cell dies during
        # SETUP -- before the agent has run at all -- and the harness then collects a
        # "failure patch" from the half-copied tree: 23 MB for django-14792, 27 MB for
        # django-14170, near-identical across both arms because the bulk is the repo
        # itself rather than anything an agent did. Four cells were lost that way in five
        # minutes on 9 Sep 2026, all django, under three concurrent shards.
        #
        # The sibling calls in this file already pass timeout=120 for exactly this
        # reason; this one was left on the default. django is the largest corpus here, so
        # it is the one that finds it.
        copied = workspace.execute_command(
            f"mkdir -p {repo_path} ; cp -r {self.get_source_repo_path(instance)}/. {repo_path}",
            timeout=600,
        )
        assert copied.exit_code == 0, f"cp failed: {copied.stderr}"
        # Same reasoning: `git reset --hard` over a freshly copied working tree is disk
        # bound, and a 30 s cap on it fails the cell in the same invisible way.
        reset = workspace.execute_command(f"cd {repo_path} ; git reset --hard", timeout=300)
        assert reset.exit_code == 0, f"git reset failed: {reset.stderr}"

        self._install_harness(workspace, repo_path, instance)

        agent = self._build_agent()
        conversation = Conversation(
            agent=agent,
            workspace=workspace,
            max_iteration_per_run=self.metadata.max_iterations,
            delete_on_close=True,
        )

        instruction = upstream.get_instruction(
            instance=instance.data, metadata=self.metadata,
            workspace_path=workspace.working_dir,
        )
        conversation.send_message(instruction)
        upstream.run_conversation_with_fake_user_response(conversation)

        # The bundle the agent produced by running collect.sh itself, recovered from the
        # container as a fallback. `collect.sh` writes /artifacts/collect.txt as well as
        # stdout precisely so a run whose output was lost is still recoverable.
        bundle = workspace.execute_command(
            f"cat {HARNESS_DIR}/collect.txt 2>/dev/null "
f"|| cat /tmp/collect.txt 2>/dev/null "
f"|| cat /artifacts/collect.txt 2>/dev/null || true", timeout=120
        ).stdout

        return EvalOutput(
            instance_id=instance.id,
            attempt=self.current_attempt,
            test_result={"git_patch": patch_from_bundle(bundle), "bundle": bundle},
            instruction=instruction,
            error=None,
            history=list(conversation.state.events),
            # What the run cost. The collector's summary lives outside this repository,
            # so a per-cell figure only exists if it is recorded per run.
            metrics=conversation.conversation_stats.get_combined_metrics(),
        )


def _upload(workspace: RemoteWorkspace, local: Path, remote: str) -> None:
    """Upload a file, and fail loudly if it did not arrive.

    `file_upload` reports failure in its RETURN VALUE. Ignoring it is how the probe came
    to be launched against a file that was never written: the run reached our own code,
    reported `bash: no such file`, and the cause was three steps earlier.
    """
    result = workspace.file_upload(str(local), remote)
    if not getattr(result, "success", False):
        raise RuntimeError(
            f"upload of {local.name} -> {remote} failed: {getattr(result, 'error', '?')}"
        )
    logger.info("uploaded %s -> %s (%s bytes)", local.name, remote,
                getattr(result, "file_size", "?"))


def _patch_from_bundle(bundle: str) -> str:
    """The ===PATCH=== section: everything after the marker is patch bytes."""
    return bundle.split("===PATCH===", 1)[1].strip() if "===PATCH===" in bundle else ""

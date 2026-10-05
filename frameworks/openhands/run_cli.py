"""Entry point: run ONE instance and store it where the rest of this project looks.

Upstream's `main()` sweeps a dataset and writes one JSONL for the whole run. This project
files runs one directory per attempt, keyed by
(repo, framework, model, instance, condition) -- that tuple is a run's identity, and
without it four models scoring one instance under one condition land in one directory
separated only by an attempt counter, which reads as one run retried four times and
merges in every aggregate that groups by run.

Configuration arrives through the environment because the shell wrapper is what knows the
layout. See run_test.sh.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
from pathlib import Path

from benchmarks.swebench.config import INFER_DEFAULTS
from benchmarks.utils.critics import CRITIC_NAME_TO_CLASS
from benchmarks.utils.models import EvalMetadata
from openhands.sdk.llm import LLM

from bundle_io import write_run_dir
import run_swebench
from run_swebench import CompliancePatchedEvaluation

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("compliance.openhands.cli")


def _require(name: str) -> str:
    if not (value := os.environ.get(name, "")):
        raise SystemExit(f"{name} is not set -- run through run_test.sh, which sets it")
    return value


def model_ids() -> tuple[str, str, str]:
    """(reporting label, routing id, key env var) -- the three are not the same thing.

    A model may be dialled somewhere other than where it is reported from.
    `gemini-3.7-flash` routes to Google directly on its own key while still reporting as
    `openrouter/google/gemini-3.7-flash`, because `compliance report` groups by the
    recorded litellm id and 828 stored gemini runs already carry that string. Letting the
    reroute reach the label would make one model report as two.

    Both extras default to the label, so every model that has not been rerouted is
    unchanged and needs no conf entry.
    """
    label = _require("RUN_MODEL")
    return (label,
            os.environ.get("RUN_ROUTE") or label,
            os.environ.get("RUN_KEY_ENV") or "OPENROUTER_API_KEY")


def build_llm() -> LLM:
    """The model, from the same `models/<slug>.conf` the other framework reads.

    Upstream takes a JSON config file as a required positional argument. Building the
    object directly keeps one source of truth for which models this experiment runs:
    a config file here would be a second place to change a model id, and the two would
    disagree eventually.
    """
    # ROUTE is what litellm dials; RUN_MODEL is the label the corpus is keyed on. They
    # differ once a model is moved off OpenRouter -- gemini-3.7-flash routes to
    # `gemini/...` on Google's own key while still REPORTING as
    # `openrouter/google/gemini-3.7-flash`, so its 828 existing runs and every future one
    # stay one model in `compliance report` instead of two.
    #
    # Both fall back to RUN_MODEL, so a model that has not been rerouted behaves exactly
    # as before and needs no conf change.
    label, route, key_env = model_ids()

    api_key = os.environ.get(key_env) or os.environ.get("LLM_API_KEY")
    if not api_key:
        raise SystemExit(f"{key_env} is not set (required to route {route})")
    if route != label:
        logger.info("routing %s via $%s, reported as %s", route, key_env, label)

    fields: dict[str, object] = {"model": route, "api_key": api_key}
    # An endpoint rather than a provider. Set only for models whose
    # `model-overrides/<slug>.conf` names one -- gemini alone today, because it is the
    # only model whose credential cannot cross into the container: Vertex authenticates
    # with ADC, a file on the host, while an API key is a field on this object and is
    # serialised into the agent-server. The proxy holds the ADC and the container gets a
    # URL, so nothing the agent can read is worth stealing.
    if base_url := os.environ.get("RUN_BASE_URL", ""):
        fields["base_url"] = base_url
        logger.info("dialling %s at %s (credential is host-side)", route, base_url)
    # Reasoning effort is passed through only where a model's conf sets one, exactly as
    # in the other harness -- a model run at a non-default effort is a statement about
    # (model + effort), not about the model, so it is never applied silently to all.
    if (effort := os.environ.get("RUN_REASONING", "default")) not in ("", "default"):
        fields["reasoning_effort"] = effort
        logger.info("reasoning effort -> %s", effort)
    return LLM(**fields)  # type: ignore[arg-type]


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python -m run_cli <instance_id>")
    instance_id = sys.argv[1]

    condition = _require("COMPLIANCE_CONDITION")
    run_dir = Path(_require("COMPLIANCE_RUN_DIR"))
    prompt = _require("COMPLIANCE_PROMPT")
    browser = os.environ.get("COMPLIANCE_BROWSER", "on") == "on"
    docs_url = os.environ.get("COMPLIANCE_DOCS_URL", "")
    rules_file = os.environ.get("COMPLIANCE_RULES_FILE", "")

    # The treatment is verified BEFORE the run, not after. A guided run whose rules file
    # is missing is not a failed run -- it is a control wearing the guided label, and it
    # would sit in the results indistinguishable from a real one.
    if condition == "guided" and not Path(rules_file).is_file():
        raise SystemExit(f"condition=guided but rules file {rules_file!r} does not exist")
    if condition == "naive" and not docs_url:
        raise SystemExit("condition=naive but no DOCS_URL")
    if not Path(prompt).is_file():
        raise SystemExit(f"instruction template {prompt!r} does not exist")

    # Instance selection goes through a file, because that is the only filter the
    # evaluator has: `prepare_instances` loads the whole dataset and narrows it with
    # `selected_instances_file`. Setting an attribute on the evaluator does nothing --
    # it is a pydantic model and would have silently run the entire 500-instance split.
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
        handle.write(f"{instance_id}\n")
        selected = handle.name

    model_label, model_route, _ = model_ids()
    metadata = EvalMetadata(
        llm=build_llm(),
        dataset=INFER_DEFAULTS["dataset"],
        dataset_split=INFER_DEFAULTS["split"],
        # 2000: high enough that reaching it is pathological rather than routine. The
        # busiest run observed used 166 iterations, so this is ~12x the worst real case.
        #
        # An agent that hits the limit raises MaxIterationsReached and returns NOTHING --
        # not a partial run -- so the cell is lost and paid for twice. That is why the
        # other harness removed its limits outright,
        # and a first live run here lost everything at 100 while still mid-task.
        #
        # NOT unbounded, though, and the difference from the other framework is deliberate.
        # mini-swe-agent has no condenser: a runaway run eventually exhausts the context
        # window and dies on its own. OpenHands condenses history as it grows, so nothing
        # stops it looping indefinitely -- unbounded here means unbounded, against a
        # shared API key that has already been exhausted once. `exit_status` now reports
        # `LimitsExceeded`, so a run that does hit this is identifiable in the data rather
        # than silently short.
        #
        # **DO NOT set this to 0 to mean "unlimited".** That is the other framework's
        # convention -- `agents/default.py` guards with `0 < step_limit` -- and it is
        # INVERTED here. This SDK checks `iteration >= max_iteration_per_run` with no
        # guard at all, so 0 halts the agent before its first action and every run returns
        # nothing.
        max_iterations=int(os.environ.get("MAX_ITERATIONS", "2000")),
        # ZERO, and the name is a trap: upstream counts `max_retries` as ADDITIONAL
        # attempts after the first -- `while retry_count <= max_retries` -- so 1 means
        # two full runs, not one. Set to 1 here originally, and a cell then ran an entire
        # 419-event conversation, hit an error, discarded all of it and started again
        # from scratch. From outside it looked like one slow run: same cell, same
        # directory, no retry in the driver's output. Only the conversation count in the
        # container gave it away.
        #
        # Retries are this project's own concept and belong to the shell wrapper, which
        # files each as its own attemptN directory. A retry we cannot see is a run whose
        # cost and duration we cannot account for, and an attempt whose work is thrown
        # away is evidence lost.
        max_retries=int(os.environ.get("OPENHANDS_MAX_RETRIES", "0")),
        eval_output_dir=str(run_dir),
        # `metadata` is in the instruction template's context, so the condition travels
        # with the run rather than through a global.
        details={
            "condition": condition, "docs_url": docs_url, "browser": browser,
            # `env` IS the model label's authority. `build_bundle` resolves
            #   model = env["RUN_MODEL"] -> probe["model"] -> trajectory llm.model
            # and this key was previously absent, so every run fell through to
            # `llm.model` -- the ROUTING id. Once gemini routes to `gemini/...` that
            # fallback would have labelled new runs differently from the 828 stored ones
            # and split one model into two in every aggregate.
            #
            # `llm_route` keeps the real provider auditable without fragmenting the key.
            #
            # RUN_UPSTREAM_ROUTE is the same argument one hop further out. Once a route
            # is an ENDPOINT rather than a provider, RUN_ROUTE reads
            # `openai/gemini-3.7-flash` and no longer says who served the tokens, so
            # routing through the proxy would have silently cost the provenance that
            # separating route from label exists to preserve. Empty for every model that
            # dials a provider directly.
            "env": {"RUN_MODEL": model_label, "RUN_ROUTE": model_route,
                    **({"RUN_UPSTREAM_ROUTE": upstream}
                       if (upstream := os.environ.get("RUN_UPSTREAM_ROUTE", "")) else {})},
            # The container paths, so the prompt and the launcher cannot disagree about
            # where the rules file and the collect script actually are. They are NOT the
            # same as the other framework's: its agent runs as root and uses /opt, while
            # this one runs as `openhands` and can only write under the workspace.
            "rules_path": run_swebench.CONTAINER_RULES,
            "collect_script": run_swebench.CONTAINER_COLLECT_WRAPPER,
        },
        prompt_path=prompt,
        eval_limit=0,
        selected_instances_file=selected,
        env_setup_commands=["export PIP_CACHE_DIR=~/.cache/pip"],
        # Upstream's default critic, constructed directly. `create_critic` wants an
        # argparse namespace, and building one here just to read one field would make
        # this depend on upstream's CLI surface rather than on its behaviour.
        critic=CRITIC_NAME_TO_CLASS["finish_with_patch"](),
        # One attempt. The critic can otherwise re-run a cell it judges unsuccessful,
        # which would silently turn one run into several -- and attempts are this
        # project's own concept, filed as attemptN directories by the shell wrapper.
        n_critic_runs=1,
        workspace_type=os.environ.get("WORKSPACE_TYPE", "docker"),  # type: ignore[arg-type]
        tool_preset="default",
        agent_type="default",
        enable_condenser=bool(INFER_DEFAULTS["enable_condenser"]),
        condenser_max_size=int(INFER_DEFAULTS["condenser_max_size"]),
        condenser_keep_first=int(INFER_DEFAULTS["condenser_keep_first"]),
    )

    evaluator = CompliancePatchedEvaluation(
        metadata=metadata,
        num_workers=1,
        condition=condition,
        docs_url=docs_url,
        enable_browser=browser,
        rules_file=Path(rules_file) if rules_file else None,
        run_dir=run_dir,
    )

    stored: list[Path] = []

    # The evaluator calls this as `on_result(instance, output)` -- two arguments. A
    # one-argument callback does NOT raise the run: it is swallowed and logged as
    # "on_result callback failed", the run reports success, and nothing is ever written.
    def on_result(_instance, output) -> None:
        payload = output.model_dump(mode="json") if hasattr(output, "model_dump") else output
        write_run_dir(payload, run_dir)
        stored.append(run_dir)

    try:
        evaluator.run(on_result=on_result)
    finally:
        Path(selected).unlink(missing_ok=True)

    if not stored:
        raise SystemExit(f"{instance_id}: produced no result; nothing stored")
    print(json.dumps({
        "run_dir": str(run_dir),
        "patch": (run_dir / "patch.diff").exists(),
        "probe": (run_dir / "probe.txt").exists(),
    }))


if __name__ == "__main__":
    main()

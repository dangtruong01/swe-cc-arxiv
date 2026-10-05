"""Assemble an EvidenceBundle from a stored run.

Everything the checkers are allowed to see passes through here. Once a bundle is built
it is the complete universe: no rule may reach past it to the network, Docker, a
subprocess or the filesystem (invariant 1).
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from compliance.bundle import commits as commits_mod
from compliance.bundle import diff as diff_mod
from compliance.bundle import reconstruct as reconstruct_mod
from compliance.core import evaluation as evaluation_mod
from compliance.core import lint as lint_mod
from compliance.bundle import trajectory as traj_mod
from compliance import adapters as adapters_mod
from compliance.core.models import BUNDLE_VERSION, EvidenceBundle
from compliance.core.paths import RunDir

logger = logging.getLogger("compliance.bundle.builder")

_BRANCH_UNKNOWN = ("", "(detached)", "HEAD")

# Tools `tools/lint_sandbox.py` knows how to run, and whose results the bundle carries.
LINT_TOOLS = ("ruff", "flake8")


def build_bundle(
    traj_path: str | Path,
    *,
    instance_id: str | None = None,
    condition: str | None = None,
    model: str | None = None,
    framework: str | None = None,
    run_id: str = "",
    repo_cache: Path | None = None,
) -> EvidenceBundle:
    traj_path = Path(traj_path)
    traj = traj_mod.load(traj_path)

    # --- which adapter reads this trajectory, decided before the trajectory is read ----
    # This has to come first, and it can only come from the caller or the run's own
    # directory. `env` and `probe` -- the other two sources the recorded `framework`
    # below draws on -- are unusable here by construction: reading either already
    # requires an adapter, which is the circularity this ordering exists to break.
    #
    # Getting it wrong is silent. An adapter handed a trajectory written by a different
    # scaffold does not raise -- it finds none of the keys it looks for and returns zero
    # commands, and a run with zero commands scores as an agent that never read the rules
    # and never fetched the docs. That is indistinguishable from a real null result, so
    # the wrong answer here arrives wearing the costume of a finding.
    located = RunDir.from_path(traj_path)
    framework_used = (
        framework or (located.framework if located else None) or adapters_mod.DEFAULT_FRAMEWORK
    )
    adapter = adapters_mod.load(framework_used)

    # The harness's own grading, parked beside the trajectory by scripts/evaluate.sh.
    # Reading it here keeps invariant 1 intact: the builder may touch disk, checkers
    # may not. A run that was never graded, or graded into the wrong file, yields a
    # report whose shape says so rather than a silent absence.
    report = evaluation_mod.load(traj_path.parent)
    evaluation = report if report.usable else None

    sections = traj_mod.submission_sections(traj, adapter)
    probe = traj_mod.parse_probe(sections.get("PROBE", ""))
    branch_info = traj_mod.parse_probe(sections.get("BRANCH", ""))
    env = traj_mod.run_env(traj, adapter)
    commands = traj_mod.commands(traj, adapter)
    notes: list[str] = []

    branch = branch_info.get("branch") or probe.get("start_branch") or ""
    branch_value = None if branch in _BRANCH_UNKNOWN else branch

    if "LOG" in sections:
        parsed = commits_mod.parse_log(sections["LOG"], branch=branch_value)
        source = "log"
    else:
        parsed = commits_mod.scrape_commits_from_commands(commands)
        source = "trajectory_shim" if parsed else "none"
        notes.append(
            "no ===LOG=== section; commit metadata came from the TEMPORARY pre-Phase-0 "
            "fixture shim (no sha, author or branch)"
        )

    # Two scopes, because the two scores ask different questions of one run (see
    # collect.sh). `files` is the contribution -- what the agent chose to commit -- and
    # is what rules judge. `files_worktree` is everything it left behind, which is what
    # SWE-bench grades.
    files_worktree = diff_mod.parse_unified_diff(traj_mod.patch_text(traj, adapter))
    committed_patch = traj_mod.committed_patch_text(traj, adapter)
    if committed_patch is None:
        files = files_worktree
        patch_scope = "worktree_fallback"
        if files_worktree:
            notes.append(
                "no ===PATCH_COMMITTED=== section; committed and uncommitted work cannot be "
                "told apart, so rules judge the whole working tree"
            )
    else:
        files = diff_mod.parse_unified_diff(committed_patch)
        patch_scope = "committed"

    # Phase 3 onward needs whole-file contents: a diff's three lines of context cannot
    # be parsed as Python. Optional -- with no cache, head_text stays None and the rules
    # that need it report missing evidence rather than guessing.
    resolved_repo = repo_cache
    if resolved_repo is None and probe.get("instance_id"):
        candidate = reconstruct_mod.cache_path(probe["instance_id"].split("__")[0])
        resolved_repo = candidate if candidate.exists() else None
    if resolved_repo is not None and probe.get("base_commit"):
        files, recon_notes = reconstruct_mod.reconstruct(files, resolved_repo, probe["base_commit"])
        files_worktree, _ = reconstruct_mod.reconstruct(
            files_worktree, resolved_repo, probe["base_commit"]
        )
        notes.extend(recon_notes)
    elif files:
        notes.append("no repo cache: head_text/base_text unavailable, AST rules cannot run")

    status_entries = traj_mod.parse_status(sections.get("STATUS", ""))
    if uncommitted := sorted(set(files_worktree) - set(files)):
        notes.append(
            f"{len(uncommitted)} file(s) left uncommitted and excluded from the "
            f"contribution: {', '.join(uncommitted[:5])}"
        )
    if not files:
        notes.append("no committed file changes to judge")

    # `located` is resolved at the top of this function, because the adapter depends on
    # it. It answers the same question here it always did: where the run is filed, when
    # the run itself does not say. The probe still wins -- it is the harness's own record
    # of what actually ran -- but a pre-Phase-0 trajectory has none, and the filename is
    # always `trajectory.json`, so falling straight through to it labelled every such run
    # `trajectory` and collapsed them together downstream.
    # Stored linter findings, if the sandbox has been run for this run. Reading a file is
    # bundle-building work; running the linter is not, and happens outside the package.
    lint = lint_mod.load_all(located.path, LINT_TOOLS) if located is not None else {}
    resolved_instance = (
        instance_id
        or probe.get("instance_id")
        or branch_info.get("instance_id")
        or (located.instance_id if located else None)
        or traj_path.name.split(".")[0]
    )
    # What the run says it is, which is richer than what the adapter could be chosen
    # from: the probe and the container env both record RUN_FRAMEWORK, and a pre-Phase-0
    # trajectory outside `runs/` has neither, so it stays honestly `unknown` rather than
    # being relabelled with whichever adapter parsed it.
    framework_recorded = (framework or env.get("RUN_FRAMEWORK") or probe.get("framework")
                          or (located.framework if located else None) or "unknown")
    # A run that says one thing and was parsed as another is the silent-mis-parse case,
    # caught rather than resolved: the two sources are independent -- the layout on one
    # side, the harness's own probe on the other -- so a disagreement means one of them
    # is wrong and the reader has to know which.
    if (framework_recorded not in adapters_mod.UNSPECIFIED
            and framework_recorded != framework_used):
        notes.append(
            f"framework mismatch: run records '{framework_recorded}' but was parsed "
            f"with the '{framework_used}' adapter -- commands, PR text and probe may "
            f"all be empty as a result"
        )

    return EvidenceBundle(
        instance_id=resolved_instance,
        base_commit=probe.get("base_commit", ""),
        created_at=probe.get("base_commit_date") or probe.get("dataset_created_at", ""),
        condition=(condition or env.get("RUN_CONDITION") or probe.get("condition")
                   or (located.condition if located else None) or "unknown"),
        model=model or env.get("RUN_MODEL") or probe.get("model") or _model_from_traj(traj),
        # Mostly the directory knows this. A trajectory does not record which harness
        # wrote it -- every framework believes it is the only one -- so the layout is the
        # record, and the probe corroborates it. Computed above, where it is checked
        # against the adapter that actually did the parsing.
        framework=framework_recorded,
        files=files,
        files_worktree=files_worktree,
        status_entries=status_entries,
        patch_scope=patch_scope,  # type: ignore[arg-type]
        commits=parsed,
        pr_text=traj_mod.pr_text(traj, adapter),
        commands=commands,
        probe=probe,
        bundle_version=BUNDLE_VERSION,
        attempt_n=_int(env.get("RUN_ATTEMPT") or probe.get("attempt_n")
                       or (located.attempt if located else None), 1),
        run_id=run_id or _default_run_id(traj_path, resolved_instance),
        evaluation=evaluation,
        lint=lint,
        commits_source=source,  # type: ignore[arg-type]
        notes=tuple(notes),
    )


def _model_from_traj(traj: dict) -> str:
    config = (traj.get("info") or {}).get("config") or {}
    return (config.get("model") or {}).get("model_name") or "unknown"


def _int(value: object, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _default_run_id(traj_path: Path, instance_id: str) -> str:
    """Stable, content-addressed, and free of clocks so bundles stay deterministic."""
    digest = hashlib.sha256(traj_path.read_bytes()).hexdigest()[:12]
    return f"{instance_id}:{digest}"


def bundle_to_json(bundle: EvidenceBundle) -> str:
    payload = {
        "instance_id": bundle.instance_id,
        "run_id": bundle.run_id,
        "base_commit": bundle.base_commit,
        "created_at": bundle.created_at,
        "condition": bundle.condition,
        "model": bundle.model,
        "attempt_n": bundle.attempt_n,
        "bundle_version": bundle.bundle_version,
        "commits_source": bundle.commits_source,
        "patch_scope": bundle.patch_scope,
        "n_commits": len(bundle.commits),
        "n_files_committed": len(bundle.files),
        "n_files_worktree": len(bundle.files_worktree),
        "uncommitted_paths": list(bundle.uncommitted_paths()),
        "n_commands": len(bundle.commands),
        "has_pr_text": bundle.pr_text is not None,
        "probe_keys": sorted(bundle.probe),
        "files": {
            path: {
                "authored_lines": sorted(change.authored_lines),
                "is_new": change.is_new,
                "is_binary": change.is_binary,
            }
            for path, change in sorted(bundle.files.items())
        },
        "commits": [
            {"sha": c.sha, "summary": c.summary, "body_lines": list(c.body_lines), "branch": c.branch}
            for c in bundle.commits
        ],
        "notes": list(bundle.notes),
    }
    return json.dumps(payload, indent=2, sort_keys=False)

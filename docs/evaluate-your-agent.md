# Evaluating your own agent on SWE-CC

SWE-CC scores what an agent **did** (its trajectory) and what it **delivered** (commits,
patch, pull-request text) against the repository's policies. Any agent can be evaluated.
It needs to run the 500 tasks with two small harness scripts in its container and record
its steps in a plain JSON file.

If your agent is mini-SWE-agent or OpenHands, use `sweeps/` instead; everything below is
already wired up there.

## 1. The task

The task list is `data/tasks.jsonl`, one line per SWE-bench Verified instance:

| field | meaning |
|---|---|
| `instance_id`, `repo`, `base_commit` | the SWE-bench Verified instance; take the issue text (`problem_statement`) and Docker image from SWE-bench |
| `project`, `n_policies` | project name and the number of policies scored for it |
| `native_docs_url` | **Native** setting: the contributor-documentation entry page the agent is pointed to |
| `consolidated_rules_file`, `consolidated_rules_sha256` | **Consolidated** setting: the policy file to mount in the container, and its checksum |
| `consolidated_mount_path` | where to mount it (`/rules/CONTRIBUTING_RULES.md`) |

Use your agent's usual SWE-bench prompt, and change it the way the paper does
(Appendix D.4). Render the additions for one instance and setting with:

```bash
python scripts/render_task.py <instance_id> native
python scripts/render_task.py <instance_id> consolidated
```

This prints three blocks. The **scope** block replaces your prompt's "minimal changes to
non-test files" line: tests and documentation may be edited, and existing tests may not be
weakened. The **Compliance** section gives the setting's instruction. The **Submission**
section asks for a real `git commit`, a run of the collect script, and a pull-request
description in the final message starting with `PR SUBMISSION:`.

Setting requirements:

- **Native**: the container needs outbound network, so the agent can fetch `native_docs_url`.
- **Consolidated**: mount `consolidated_rules_file` read-only at `consolidated_mount_path`.
- In both settings, git must have a working identity, and the repository's own git hooks
  must be disabled. `harness/probe.sh` does both.

## 2. Two scripts in the container

Copy `harness/probe.sh` and `harness/collect.sh` into the container.

**Before the agent starts**, run the probe. It records the environment, sets up the git
identity, disables hooks, and records the commit the agent starts from:

```bash
PROBE_REPO_DIR=/testbed PROBE_INSTANCE_ID=<instance_id> PROBE_BASE_COMMIT=<base_commit> \
RUN_CONDITION=<naive|guided> RUN_MODEL=<model> RUN_FRAMEWORK=own-agent \
RUN_DOCS_URL=<native_docs_url> HARNESS_DIR=/opt bash /opt/probe.sh
```

(`RUN_CONDITION` uses the stored names: `naive` for Native, `guided` for Consolidated.)

**After the agent finishes**, run the collect script, with the same `HARNESS_DIR`, and
keep its entire stdout:

```bash
COLLECT_REPO_DIR=/testbed HARNESS_DIR=/opt bash /opt/collect.sh
```

Its output holds the delimited sections the checkers read: `===PROBE===`, `===BRANCH===`,
`===LOG===` (commits), `===STATUS===`, `===PATCH_COMMITTED===`, and `===PATCH===`. The
released prompt has the agent run this script itself as its last action. You can also run
it from your harness after the agent stops, which gives the same result.

## 3. The trajectory file

Write one JSON file per run (the format read by `compliance/adapters/own_agent.py`):

```json
{
  "instance_id": "sympy__sympy-11618",
  "model": "my-model",
  "setting": "native",
  "exit_status": "Submitted",
  "steps": [
    {"command": "curl -s https://docs.sympy.org/dev/contributing/index.html", "output": "...", "returncode": 0},
    {"command": "git commit -m 'Fix distance for points of different dimension'", "output": "...", "returncode": 0}
  ],
  "pr_text": "The pull-request description the agent wrote",
  "submission": "<entire stdout of collect.sh>"
}
```

- `steps` lists every action in order, with the output **exactly as the model saw it**,
  including any truncation. Trajectory policies (for example "run the test suite before
  committing") and Table 5's retrieval measures are read from here.
- Record a tool call that isn't a shell command as a string beginning with the tool
  name, such as `read_file /rules/CONTRIBUTING_RULES.md` or `fetch https://...`. The
  own-agent adapter recognises `read_file`, `view`, `open_file` and `read` as reads, and
  `fetch`, `browse` and `navigate` as network fetches, alongside the usual shell verbs.
- `pr_text` is the text after `PR SUBMISSION:` in the agent's final message.

`tests/test_own_agent_adapter.py` converts a released run into this format and checks that
every policy gets the same verdict as with the native adapter.

## 4. Scoring

Clone the project's history once, so checkers can rebuild the files the agent changed:

```bash
git clone --filter=blob:none --no-checkout https://github.com/<repo>.git .cache/repos/<prefix>
```

`<prefix>` is the SWE-bench instance prefix (`sympy`, `pallets`, ...; see the table in
the README). Then score each run:

```bash
python -m compliance check run.json --scaffold own-agent --project sympy --jsonl rows.jsonl
python -m compliance retrieval run.json --scaffold own-agent --project sympy
```

Functional correctness is graded with the standard SWE-bench harness on the `===PATCH===`
section. Put its report beside the trajectory as `eval_report.json`. Policies that need a
test outcome read it from there, and otherwise report `withheld`.

## 5. Reporting

To report numbers comparable with the paper, lay your runs out as

```
runs/<prefix>/<scaffold>/<model>/<instance_id>/<naive|guided>/attempt1/
    trajectory.json   rows.jsonl   eval_report.json   patch.diff
```

Then run `python scripts/export_results.py --runs runs` and `python scripts/summarize.py`
(add `--by category` for the per-category view). Report the **triggering rate** alongside the **compliance rate** (Section 3.5). An agent
that does less work triggers fewer policies, so its compliance rate alone can look better.

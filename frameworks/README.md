# Agent framework configuration

One file per agent scaffold: `frameworks/<slug>.conf`. The slug is the directory name
under `runs/<repo>/<slug>/`, and it names the adapter that can read that framework's
trajectories.

Same `KEY="value"` contract as `rules/<repo>/repo.conf` and `models/<slug>.conf`.

| key | what it is |
|---|---|
| `DISPLAY_NAME` | human-readable |
| `ADAPTER` | dotted path to the module in `compliance/adapters/` that parses this framework's trajectory |
| `SOURCE` | where the (instrumented) harness lives |
| `SOURCE_SDK` | optional — a second repository, when the harness and the agent are split |
| `PIN_*` | optional — the exact commit each source is pinned at |

### Pinning, and when it is required

`mini-swe-agent` is pinned in `frameworks/setup.sh` and our changes to it are kept in `frameworks/mini-swe-agent/overlay/`. A framework we do
**not** control has to be pinned, because the adapter is written against one trajectory
schema and a sweep spans weeks: an upstream that moves mid-sweep splits the corpus
without anything failing.

Where upstream already states a compatible pair, take theirs rather than choosing one.
`openhands` is pinned this way — `benchmarks` vendors the SDK as a git submodule, so the
submodule pin *is* the answer, and re-pinning means moving `benchmarks` and accepting
whatever SDK sha it then names.

## Why a framework is an axis and not a stage

A **stage** is a change that makes runs either side of it
non-comparable, so they must not be pooled. Framework and model are neither: they are
**factors**, deliberately varied and then compared. They become columns in the results,
not stage boundaries. Confusing the two would make every model sweep look like a new
stage and nothing would pool with anything.

## What a second framework costs

Layers A and B are repository-agnostic and tested for it. They are **not** automatically
framework-agnostic. Five things are framework-specific and belong in the adapter, not in
`core/` or `bundle/`:

1. the trajectory format — actions, observations, and how they pair up
2. **which actions count as reading a file** — `core/retrieval.py` decides whether the
   guided treatment was consumed; under a bash agent that is `cat`, under a tool-using
   agent it is an editor view. Getting this wrong does not crash, it silently reports
   "never opened", which is the exact false negative the module exists to prevent
3. **which actions count as fetching a URL** — same failure mode, for the naive arm
4. how the treatment is truncated on its way into the model's context
5. where the startup probe is injected


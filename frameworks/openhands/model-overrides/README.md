# OpenHands model overrides

`frameworks/openhands/model-overrides/<model-slug>.conf`, sourced by
`frameworks/openhands/run_test.sh` **after** `models/<slug>.conf` and by nothing else.

## Why this directory exists rather than more keys in `models/<slug>.conf`

`models/<slug>.conf` states what a model *is*. It is read by both frameworks, so a key
added there for one framework's benefit is a key the other silently inherits — and
mini-swe-agent's `scripts/run_test.sh` has the identical
`RUN_ROUTE="${LITELLM_ID:-$model}"` line. Rerouting a model for OpenHands by editing
`LITELLM_ID` would therefore move the mini-swe-agent sweep too, which is not what anyone
asked for and would not be visible in the diff.

So a file here answers a narrower question: **how this framework must dial this model,
given where this framework runs the model.** Same `KEY="value"` contract; the keys are
the ones `models/<slug>.conf` already defines, and setting one here overrides it for
OpenHands alone.

Absent file = no override. Only `gemini-3.7-flash` needs one; the other three models have
no file here and are dialled exactly as `models/<slug>.conf` says.

| key | effect |
|---|---|
| `LITELLM_ID` | what litellm dials **inside the container** |
| `BASE_URL` | an OpenAI-compatible endpoint to dial instead of the provider |
| `API_KEY_ENV` | which env var holds the credential for that endpoint |
| `UPSTREAM_ROUTE` | provenance only — what the endpoint dials on our behalf |

`CANONICAL_ID` is deliberately **not** overridable here. It is what the corpus is keyed
on, it is the same model whichever way the bytes are delivered, and splitting it per
framework would fragment every aggregate.

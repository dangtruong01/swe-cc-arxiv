# Model configuration

One file per model in the experiment: `models/<slug>.conf`. The slug is the directory
name under `runs/<repo>/<framework>/<slug>/`, so it must be filesystem-safe — which is
why it is not the litellm id, which contains slashes.

Same contract as `rules/<repo>/repo.conf`: plain `KEY="value"` lines, no substitutions,
readable by both shell (`scripts/run_test.sh`) and python
(`compliance.core.registry.read_conf`). Adding a model is a new file here; no code changes.

| key | what it is |
|---|---|
| `DISPLAY_NAME` | human-readable, for tables and write-ups |
| `LITELLM_ID` | the string passed to the harness as `-m`. Recorded in `probe.txt` per run |
| `VENDOR` | who trained it. The model axis compares vendors, not sizes within one |
| `WEIGHTS` | `open` or `closed`. The design is two of each |
| `CONTEXT` | context window in tokens. The guided treatment is ~5k tokens for SymPy and ~2k for Django; a model that cannot hold it receives a different treatment |

## The four in the design

| slug | vendor | weights | $/Mtok in | note |
|---|---|---|---:|---|
| `gemini-3.7-flash` | Google | closed | 0.38 | |
| `gpt-5.6-luna` | OpenAI | closed | 0.20 | |
| `kimi-k2.5` | Moonshot | open | 0.60 | **high reasoning effort**; reads the guidelines in only 33% of runs — kept deliberately |
| `deepseek-v4-flash-0731` | DeepSeek | open | 0.06 | |

All four verified against OpenRouter's live catalogue on 26 Aug 2026 — id resolves, model
answers, price as listed. **Re-check before a large sweep**: ids and prices move, and one
earlier pick (`google/gemini-3-pro`) turned out never to have existed.

Combined input rate is **$1.24/Mtok**, well under the ~$2.55 the $4–5k budget allows across
8,000 runs.

### ⚠️ Kimi runs at high reasoning; the other three do not

`REASONING_EFFORT="high"` is set only in `kimi-k2.5.conf`. It is passed through as
`reasoning: {"effort": "high"}` and recorded per run in `probe.txt` as `reasoning=`.

**This makes Kimi's results a statement about (model + effort), not about the model.** If
Kimi outperforms the others, the effort setting is a live alternative explanation, and any
write-up has to say so. The clean alternatives are to set an explicit effort for all four,
or to run Kimi at both settings — either resolves it; leaving it unstated does not.

Reasoning is not free either: three of the four emit reasoning tokens even unprompted
(43–83 on a trivial probe), and those bill at the output rate. `gpt-5.6-luna` reported
**zero**, so it likely does not reason by default — worth confirming before treating it as
a capability peer of the other three.

## Retired, but kept

`gemini-2.5-flash` and `qwen3-coder` are **not** in the design. Their files remain because
stored runs live at `runs/<repo>/<framework>/<slug>/` and the conf is what keeps those
paths describable — 22 pre-E1 runs and the 10 E1 runs respectively.

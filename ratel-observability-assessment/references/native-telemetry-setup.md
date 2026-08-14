# Native OTLP telemetry setup

How to turn on Ratel's native OpenTelemetry telemetry and export it to whatever OTel backend the team already runs. Read this when the proposal reaches the "turn on telemetry" step, or when Ratel (`@ratel-ai/sdk`, the Python `ratel-ai` package, `ratel-ai-core`, `@ratel-ai/mcp-server`, or `ratel-mcp`) is present or being adopted.

The headline: **Ratel telemetry IS OpenTelemetry.** The SDKs natively emit the retrieval + tool funnel as `gen_ai.*` spans (semconv **v1.42.0**) plus a `ratel.*` overlay, exported as stock OTLP `http/protobuf` + Bearer auth. There is no vendor-specific instrumentation to write and no forwarder to run — you turn it on once and the spans land in your backend.

## What Ratel emits (the funnel, natively)

Ratel's core (ADR-0009) emits a typed trace-event stream that the SDK renders as OTel spans. These arrive on the same trace as your own agent and LLM-call spans:

| Ratel span | `gen_ai.operation.name` | Attributes |
| --- | --- | --- |
| `ratel.search` | (retrieval) | `query`, `top_k`, `hit_count`, `top_hit_score`, `took_ms`, retrieval method (`bm25` \| `semantic` \| `hybrid`), `origin` (`direct` \| `agent`). The skills bucket rides the same span (skill ids, hit counts) — skills are ranked here, not on a separate span. |
| `execute_tool <tool id>` | `execute_tool` | `tool_id`, `args_bytes`, `took_ms`, `origin`; on end `ok` / `error_type`; on error the error attribute + message. Standard `gen_ai.operation.name=execute_tool` — **not** a bespoke `ratel.invoke`. |
| `ratel.skill.load` | (read) | `skill_id`, `took_ms`, `origin`. A skill is **read**, not executed — there is no `invoke_skill`. |
| `ratel.upstream.register` | — | `server_name`, `transport`, `tool_count`. Emitted at registration, not per-turn. |
| `ratel.auth.flow` | — | `upstream`, flow kind (refresh / needs / flow-start / flow-end), `ok` where applicable. |

Two attributes ride the whole funnel and are the highest-value pivots:

- **`origin`** — `direct` (Ratel called from library code via the SDK) vs `agent` (Ratel called via the `search_capabilities` / `invoke_tool` / `get_skill_content` capability tools). Direct calls don't reflect agent behaviour; split every Ratel dashboard by this.
- **`replace_mode`** — `true` when the catalog is in replace-by-default mode (top-K injected, full catalog hidden), `false` otherwise. Determines whether the token-savings dashboards apply.

**Ratel does NOT emit LLM-call (`chat <model>`) spans.** Those come from your own LLM instrumentation (your provider SDK's OTel `gen_ai` instrumentation); Ratel's funnel spans join the same trace next to them. The search-span attributes (`top_k`, `hit_count`, `top_hit_score`, `took_ms`, `origin`) come only from Ratel's SDK — a generic Langfuse/LangSmith setup won't capture them, which is exactly why native telemetry is worth turning on.

## Setup — two GA paths

Both paths are GA (OTLP telemetry dropped `-rc` on 2026-07-11) but pre-1.0. Pick one.

### Path A — greenfield (`configureTelemetry` / `configure_telemetry`)

Use when the codebase has no OTel provider yet. Ratel owns the provider and wires an OTLP exporter to `RATEL_URL`. Point that URL at your backend's OTLP collector endpoint.

TypeScript:

```ts
import { configureTelemetry, ToolCatalog } from "@ratel-ai/sdk";

configureTelemetry({
  // OTLP http/protobuf + Bearer; defaults to RATEL_URL / RATEL_API_KEY env
  endpoint: process.env.RATEL_URL,
  headers: { Authorization: `Bearer ${process.env.RATEL_API_KEY}` },
  serviceName: "my-agent",
  // content capture is OFF by default — see below
});

const catalog = new ToolCatalog({ method: "hybrid" /* bm25 | semantic | hybrid */ });
```

Python:

```python
import os
from ratel_ai import configure_telemetry, ToolCatalog

configure_telemetry(
    endpoint=os.environ["RATEL_URL"],
    headers={"Authorization": f"Bearer {os.environ['RATEL_API_KEY']}"},
    service_name="my-agent",
)  # content capture is OFF by default — see below

catalog = ToolCatalog(method="hybrid")  # bm25 | semantic | hybrid
```

### Path B — dual-export (`ratelSpanProcessor` / `ratel_span_processor`)

Use when the codebase already has an OTel provider (a Langfuse SDK, the Vercel AI SDK, your own collector). Add Ratel's span processor to the existing provider so Ratel's spans ride the export you already have. A default signal filter forwards only `ratel.*` / `gen_ai.*` spans, keeping framework `ai.*` wrapper noise out.

TypeScript:

```ts
import { NodeTracerProvider } from "@opentelemetry/sdk-trace-node";
import { ratelSpanProcessor } from "@ratel-ai/telemetry-otlp";

const provider = new NodeTracerProvider();
provider.addSpanProcessor(ratelSpanProcessor()); // forwards ratel.* / gen_ai.* only
provider.register();
```

Python:

```python
from opentelemetry.sdk.trace import TracerProvider
from ratel_ai_telemetry.otlp import ratel_span_processor

provider = TracerProvider()
provider.add_span_processor(ratel_span_processor())  # forwards ratel.* / gen_ai.* only
```

The spans then land wherever that provider already exports — so a team on Langfuse or LangSmith keeps their existing pipeline and simply gains Ratel's funnel spans on the same traces.

## Content capture — opt-in, default OFF

Message/tool input and output content is **not** captured by default. Turn it on only where you need input/output on spans (any dashboard or finding that reads content must note this gate). Control it with the standard env var or programmatically:

- `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` — `NO_CONTENT` (default) | `SPAN_ONLY` | `EVENT_ONLY` | `SPAN_AND_EVENT`.
- Programmatic: `setContentCapture(mode)` / `configureTelemetry({ captureContent })` (TS), `set_content_capture(mode)` / `configure_telemetry(capture_content=...)` (Python).

Don't put PII or full tool args on `execute_tool` spans — truncate at the same boundary as the rest of the codebase.

## Local trace stream (JSONL / memory)

The Rust core also owns a local JSONL/memory trace-event stream, independent of the OTLP export. Enable it with `trace=` on the `ToolCatalog` / `SkillCatalog` constructor. It feeds the statusline, the savings report, and offline inspection. **Off by default.**

```ts
const catalog = new ToolCatalog({ trace: { kind: "jsonl", path: "~/.ratel/trace.jsonl" } });
```

```python
catalog = ToolCatalog(trace={"kind": "jsonl", "path": "~/.ratel/trace.jsonl"})
```

This mirrors the same event stream that becomes OTLP spans, so it's a fast local view without standing up a backend.

## Export to any OTel backend

Because the wire format is stock OTLP, the export target is a config choice, not a code rewrite:

- **Langfuse / LangSmith** — first-class OTLP coexistence targets. Dual-export (Path B) onto their provider, or point the OTLP exporter (Path A) at their OTel collector endpoint with their auth header. Ratel's native telemetry does **not** replace them — it removes the need for vendor-specific *instrumentation* and adds the retrieval funnel they can't see on their own.
- **Your own collector** — send OTLP to any OpenTelemetry collector and fan out from there.
- **Ratel Cloud (Coming Soon)** — the first-party option. It ingests the same OTLP spans and derives run metrics + a context-source breakdown + ranked suggestions server-side. MVP built in-repo, not publicly deployed. There is **no `@ratel-ai/cloud` SDK package** — you export the same OTLP.

See [`vendor-detection.md`](vendor-detection.md) for how to detect which backend a codebase already runs and the per-backend export shape.

## Before / after annotation (for A/B)

To prove Ratel's value, the most valuable view is "agent on its full tool catalog" (baseline) vs "agent on Ratel's top-K" (Ratel arm). Add a low-cardinality span attribute / tag `feature_flag: "tool_pool=full"` vs `feature_flag: "tool_pool=ratel"` and run both arms in parallel; the Ratel-value dashboards pivot on it. `/ratel-integrate` plans this A/B against these native-telemetry metrics.

## Scoring hooks (when ground truth is available)

If the agent has any ground-truth labelling, wire scores in your backend's evals surface:

| Score | When | Computed from |
| --- | --- | --- |
| `tool_selection_accuracy` | every unit of work with a `ground_truth_tool_id` attribute | 1 if the agent's first tool call's `tool_id` == `ground_truth_tool_id`, else 0 |
| `top_k_recall_at_5` | every `ratel.search` span with ground truth | 1 if `ground_truth_tool_id` appears in the top 5 hits, else 0 |
| `input_tokens_saved_vs_baseline` | post-hoc, comparing matched units of work | baseline input tokens minus Ratel-arm input tokens |

## Don't

- Don't attach Ratel spans to turns where Ratel isn't invoked — the SDK only emits them on the Ratel path, so don't hand-fake them elsewhere.
- Don't turn on content capture globally to "see everything" — it's off by default for a reason (PII, cost); enable the narrowest mode that a specific dashboard needs.
- Don't restructure the customer's own trace tree to "make room" for Ratel — Ratel's spans attach as children to whatever span is current; they don't reshape the tree.

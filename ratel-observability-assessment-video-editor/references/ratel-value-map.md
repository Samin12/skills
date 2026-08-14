# Ratel value map — feature → signal

This is the **single source of truth for what Ratel ships** and the observable signal each capability produces. **Update this file whenever Ratel ships a new feature** — it is read across the suite (`ratel-assessment`, `ratel-observability-assessment`, `ratel-integrate`).

Because Ratel's telemetry is native OpenTelemetry, the signals below are concrete OTel span/attribute names, not an abstract vocabulary a downstream skill has to render. Ratel emits its retrieval + tool funnel as `gen_ai.*` spans (semconv v1.42.0) plus a `ratel.*` overlay; the span names and attributes below are what shows up in whichever OTel backend you export to, and the dashboards group on them directly.

Each row has:
- **Feature** — the Ratel capability.
- **Status** — `shipped` / `coming soon`. `coming soon` signals go in a proposal's "Out of scope" section, not the active dashboard list.
- **Signal** — the observable data (which span, carrying which attributes) that proves the feature is working.
- **Dashboard** — which dashboard owns the widget that surfaces it.

## Shipped today (0.4.x line)

SDK versions today: `@ratel-ai/sdk` 0.4.1, `ratel-ai` 0.4.2, `ratel-ai-core` 0.4.0. GA but pre-1.0 (0.x).

| Feature | Status | Signal (OTel span + attributes) | Dashboard |
| --- | --- | --- | --- |
| Hybrid retrieval (BM25 default, opt-in semantic + hybrid RRF; top-K tools + skills via `search_capabilities`) | shipped | a `ratel.search` span carrying `top_k`, `hit_count`, `top_hit_score`, `took_ms`, and the retrieval method (`bm25` \| `semantic` \| `hybrid`) | Retrieval Quality |
| Native OTLP telemetry (funnel emitted as `gen_ai.*` + `ratel.*`, exported as stock OTLP `http/protobuf` + Bearer) | shipped | the whole span tree below lands in your OTel backend without any vendor-specific instrumentation | foundation for all dashboards |
| Content capture, opt-in (default OFF) | shipped | input/output content on spans/events only when `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` (`NO_CONTENT` default \| `SPAN_ONLY` \| `EVENT_ONLY` \| `SPAN_AND_EVENT`) or `setContentCapture(mode)` enables it | any content-dependent widget (gated) |
| Replace-by-default pre-filter (top-K injected, full catalog hidden) | shipped | `replace_mode=true` on `chat-turn` units of work; the root model-call's `input_tokens` drops 50–85% | Token Cost & Savings |
| Capability tools (`search_capabilities`, `invoke_tool`, `get_skill_content`) | shipped | `origin in [direct, agent]` on every Ratel span; count by origin | Origin Split |
| First-class skills (`SkillCatalog`, ranked via the `search_capabilities` skills bucket) | shipped | a `ratel.search` span over the skills bucket, plus a `ratel.skill.load` span (skill id read, not executed) | Skill Retrieval Health |
| MCP server ingestion (upstream namespace prefix) | shipped | a `ratel.upstream.register` span carrying `server_name`, `transport`, `tool_count` | Upstream Health |
| OAuth 2.1 / PKCE auth flows | shipped | `ratel.auth.flow` spans: refresh, needs, flow-start, flow-end | Upstream Health |
| Local trace stream (JSONL / memory) | shipped | `trace=` on `ToolCatalog` / `SkillCatalog` mirrors the span stream to local JSONL/memory (statusline, savings report, offline inspection); off by default | foundation (local) |

Note: the native funnel spans are `ratel.search`, `execute_tool <tool id>` (standard `gen_ai.operation.name=execute_tool`, not a bespoke `ratel.invoke`), `ratel.skill.load`, `ratel.upstream.register`, and `ratel.auth.flow`. Skills are read via `get_skill_content` / `ratel.skill.load`, not executed — **there is no `invoke_skill`**. The `origin` attribute (`direct | agent`) rides every Ratel span. Ratel does **not** emit LLM-call (`chat <model>`) spans — those come from your own LLM instrumentation and join the same trace next to Ratel's funnel. See [`native-telemetry-setup.md`](native-telemetry-setup.md) for the full span/attribute vocabulary and the two setup paths.

## Coming soon

| Feature | Status | Signal it will add | Dashboard impact |
| --- | --- | --- | --- |
| Ratel Cloud (OTLP ingest → run metrics + context-source breakdown + ranked suggestions, server-side) | coming soon | derived run-metrics + a `suggestion_adopted` score, computed from ingested OTLP | New "Suggestion Adoption" dashboard |
| Multi-agent decomposition hints | coming soon | a decomposition-proposed event; per-sub-agent catalog sizes | New "Decomposition Outcome" dashboard |
| Re-ranking (LLM, then learned) | coming soon | a re-rank step carrying `before_order` / `after_order` | Retrieval Quality adds a "Re-rank lift" widget |
| Chat compaction | coming soon | a compaction step carrying token-in / token-out | New "Compaction" dashboard |
| Memory orchestration | coming soon | a memory-retrieve step carrying hit count, ranking | New "Memory Recall" dashboard |

Ratel Cloud is Coming Soon (MVP built in-repo, not publicly deployed). It ingests the same OTLP spans and derives run metrics, a context-source breakdown, and ranked suggestions server-side — so the suggestions/decomposition rows above land there once it's live. There is no `@ratel-ai/cloud` SDK package.

## How the dashboards use these signals

The Ratel-value dashboard *group* (Token Cost & Savings, Retrieval Quality, Origin Split, Skill Retrieval Health, Upstream Health, plus the Coming-Soon placeholders) is named here and proposed by `/ratel-observability-assessment`. Because the signals are already concrete OTel span/attribute names, the customer builds each widget directly in their backend's UI — filter by span name, group by the attributes above, aggregate the metric. This file stays the contract for *what Ratel ships and what signal proves it*; [`semantic-conventions.md`](semantic-conventions.md) carries the full attribute reference the widgets group on.

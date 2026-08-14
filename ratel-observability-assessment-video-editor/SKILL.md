---
name: ratel-observability-assessment-video-editor
description: "Inspect an agent codebase to decide where tracing belongs, turn on Ratel's native OTLP telemetry, and pick the OTel backend the team already runs to export to, then write a proposal covering instrumentation, backend selection, and the dashboards that prove value. Use when mounting observability, asking where tracing goes or what to instrument/measure, turning on Ratel telemetry, choosing an OTel backend (Langfuse/LangSmith/collector/Ratel Cloud), designing dashboards, asking what proves Ratel's value, or `/ratel-observability-assessment`. Entry point of the funnel (reached from /ratel-assessment); hands off to /ratel-integrate for rollout. Writes one living markdown file to repo/.ratel/; does not edit code or call a backend API; skips when there's no agent surface.\n"
---
# /ratel-observability-assessment — turn on native OTLP telemetry for an agent codebase

Mount observability on a customer's codebase the way the Ratel team would: detect the stack, map the agent's mental model, decide one consistent naming/tagging vocabulary, decide which dashboards prove value, **turn on Ratel's native OTLP telemetry and pick the OTel backend the team already exports to**, and write a proposal the customer can act on. The proposal is the deliverable. Do not edit the agent code, and do not call any backend API.

Ratel's telemetry **is** OpenTelemetry: the SDKs natively emit the retrieval + tool funnel as `gen_ai.*` spans (semconv v1.42.0) plus a `ratel.*` overlay, exported as stock OTLP. So the wiring is not vendor-shaped — you turn on native telemetry once and export those spans to whatever OTel backend the team already runs (Langfuse, LangSmith, your own collector, or Ratel Cloud — Coming Soon). This skill owns the whole decision: where tracing belongs, what agent-level spans to add alongside Ratel's funnel, which backend to export to, and which dashboards prove value. It is the entry point of the observability funnel, usually reached when [`/ratel-assessment`](../ratel-assessment/SKILL.md) flags the Observability dimension as Weak or Missing.

The vocabulary and dashboard set it lands on become the contract the team builds against in whichever backend they export to, so the span/attribute names defined here actually show up on the dashboards.

## Philosophy: trace the mental model, not the call graph

A common failure mode is "wrap every function in a span." That produces data that matches the code's call graph but tells you nothing about what the agent was *trying to do*. The proposal must structure observability around the conceptual shape of a turn — **units of work**, **steps**, **sessions** — not the source-file layout. Read [`references/instrumentation-philosophy.md`](references/instrumentation-philosophy.md) for the full guidance and the two anti-patterns (no session boundary; tool calls captured as untyped events) to call out whenever you see them.

## Workflow

### Step 1 — Detect the stack

Read manifest files to identify language and framework. Ratel's native telemetry ships for TypeScript and Python, so the stack profile mainly tells you which SDK (`@ratel-ai/sdk` vs `ratel-ai`) and which framework hooks the wiring uses.

```bash
# TypeScript / Node detection
test -f package.json && jq -r '.dependencies // {}, .devDependencies // {} | keys[]' package.json | sort -u

# Python detection
test -f pyproject.toml && grep -A 200 '^\[' pyproject.toml || true
test -f requirements.txt && cat requirements.txt
test -f uv.lock && head -50 uv.lock
```

Map dependencies to one of these stack profiles:

| Signal in manifest | Stack |
| --- | --- |
| `ai`, `@ai-sdk/*` | Vercel AI SDK |
| `@mastra/core`, hand-rolled loops calling `openai` / `@anthropic-ai/sdk` directly | TypeScript generic |
| `openai` / `anthropic` / `langchain` / `llama_index` (no agent framework) | Python generic |
| `langgraph`, `crewai`, `agno`, `autogen` | Python agentic |

If signals overlap (e.g. both a LangGraph supervisor and raw OpenAI calls inside), pick the agentic profile as primary and note the mixed-stack callout in the proposal. [`references/native-telemetry-setup.md`](references/native-telemetry-setup.md) carries the concrete wiring (TS + Python) for whichever profile you land on.

If you cannot identify any agent surface at all (no LLM client imports, no agent framework, no model calls), use the [honest skip path](#honest-skip-path).

### Step 2 — Map the agent's topology

Launch one **Explore** agent (or do it directly for very small repos) to answer four questions, citing file paths:

1. **Where does a turn begin?** — entry points: an HTTP handler, a CLI verb, a queue consumer, a chat-platform webhook. This is where `session_id` lives.
2. **What are the units of work?** — supervisor function, sub-agent factories, role-specialised loops. Anything that takes a user message and returns a response. These become the top-level boundaries.
3. **Where are tools defined and called?** — tool registries (`tools: [...]`), `@tool` decorators, MCP server wiring. Each tool call must surface as a typed tool-call step.
4. **Where do sub-agents hand off to other sub-agents?** — supervisor → worker, parallel fan-out, graph node transitions. These are the spots where session/user/tag context must survive the boundary.

Capture this as a small topology diagram in the proposal (ASCII or Mermaid). It does not need to be exhaustive — it needs to give the customer a single picture they can point at while implementing.

### Step 3 — Detect which OTel backend you export to

Because Ratel emits stock OTLP, the only backend question is: where do those spans land? Read [`references/vendor-detection.md`](references/vendor-detection.md) and scan manifest deps, env vars, and init/import sites for each backend the team might already run (Langfuse, LangSmith, PostHog, Arize Phoenix, Helicone, OpenLLMetry/OTel GenAI, Braintrust) — every one of them ingests OTLP. Reuse the observability signals `ratel-assessment` already gathers if you have them. Record the detected backend and a confidence level (high / medium / low) per that reference's rules — a manifest dep or init site is a strong signal; an env var alone is weak.

### Step 4 — If no backend found, recommend one

If Step 3 produces no signal (or only a weak, ambiguous one), do not guess. Use **AskUserQuestion** to ask which OTel-compatible backend the team runs, offering: **Langfuse**, **LangSmith**, **own OTel collector**, **other**, **none yet**.

- If they name a backend, proceed with it as the export target (confidence: stated).
- If they pick **other**, capture the name; any OTLP backend works — record it as the export target.
- If they pick **none yet**, recommend adopting one (Langfuse and LangSmith are the fastest OTLP-native starting points; a self-hosted collector works too) and note Ratel Cloud (Coming Soon) as the eventual first-party option. Deliver the full proposal either way.

### Step 5 — Turn on native telemetry and propose agent-level spans

Ratel emits its retrieval + tool funnel natively as OTel spans. The proposal's instrumentation section has two halves:

1. **Turn on Ratel's native OTLP telemetry** — link [`references/native-telemetry-setup.md`](references/native-telemetry-setup.md). Pick the setup path: greenfield `configureTelemetry()` / `configure_telemetry()` (Ratel owns the OTel provider and exports to `RATEL_URL`), or dual-export `ratelSpanProcessor()` / `ratel_span_processor()` bolted onto the team's existing provider. State which path fits the codebase and why. This is the wiring — there is nothing left for a downstream skill to "render."
2. **Add the agent-level spans Ratel does not emit** — apply [`references/instrumentation-philosophy.md`](references/instrumentation-philosophy.md) (mental model, not call graph; the two anti-patterns) and [`references/semantic-conventions.md`](references/semantic-conventions.md) (unit-of-work naming, step kinds, session/thread sourcing, tags, attribute keys) to the topology from Step 2. Ratel's `ratel.*` funnel spans join the same trace as the customer's own LLM-call and agent spans — Ratel does **not** emit `chat <model>` spans, so name the session boundary, the agent-step and model-call spans, and the session-id source. State *what* to capture and *why*.

List every span/tag/attribute key the proposal introduces in one table the customer can paste into a shared doc, so the dashboards below have names to group on.

### Step 6 — Propose dashboards

From [`references/general-agent-dashboards.md`](references/general-agent-dashboards.md), pick the agent-health dashboards the instrumentation will support: Latency & Cost Overview, Error Surface, Tool Usage, Session Quality, Model & Prompt Drift. These are useful regardless of Ratel. Render them in whichever OTel backend the team chose in Step 3.

Add the **Ratel-value group** *conditionally* — only if Ratel is present in the manifest or the customer has signed up to adopt it. Name those dashboards from [`references/ratel-value-map.md`](references/ratel-value-map.md) (Token Cost & Savings, Retrieval Quality, Origin Split, Skill Retrieval Health, Upstream Health), and footnote any roadmap-conditional ones. If Ratel is not present and there is no plan to introduce it, skip this group entirely — do not pre-bake a Ratel pitch into a customer-owned doc.

List *which* dashboards and *why* each matters (one plain-English line per dashboard). The concrete span/attribute names each dashboard groups on come from [`references/semantic-conventions.md`](references/semantic-conventions.md) and [`references/ratel-value-map.md`](references/ratel-value-map.md); the customer builds the widgets in their backend's UI.

### Step 7 — Write the proposal

Write to `<repo>/.ratel/ratel-observability-assessment.md` — a **single living file, not date-stamped**, so the follow-up [`/ratel-integrate`](../ratel-integrate/SKILL.md) run always reads a stable path. Create the `.ratel/` directory if it doesn't exist; ask the user to confirm the path if the repo already uses a different docs convention. Overwrite on re-run.

The proposal must contain, in this order:

1. **Summary** — one paragraph: stack detected, agent topology, what's already instrumented (if anything), what this proposal adds.
2. **Export target** — the OTel backend and confidence level (or the user's stated answer from Step 4).
3. **Topology** — the diagram from Step 2.
4. **Instrumentation strategy** — how to turn on Ratel's native telemetry (which setup path from Step 5), plus the agent-level span/tag/attribute table and the session-boundary plan; call out either anti-pattern you found.
5. **Recommended dashboards** — the agent-health group and, conditionally, the Ratel-value group from Step 6, each with its one-line "why".
6. **Ratel angle** (conditional, only if Ratel is present or planned) — which findings map to which Ratel capability per `references/ratel-value-map.md`.
7. **Recommended next step** — hand off to [`/ratel-integrate`](../ratel-integrate/SKILL.md), per the routing table below.

Print the table of contents inline in the chat — seven bullets max — the export target, and the recommended next step. Do not paste the full proposal body into the chat; the file is the artifact.

### Step 8 — Turn on telemetry, then hand off to /ratel-integrate

End the proposal and the inline summary with the route:

| Situation | Route to |
| --- | --- |
| Turning on telemetry | [`references/native-telemetry-setup.md`](references/native-telemetry-setup.md) — the concrete TS + Python wiring (greenfield `configureTelemetry` / dual-export `ratelSpanProcessor`), content-capture opt-in, and the local trace stream |
| Rolling Ratel out + proving it | [`/ratel-integrate`](../ratel-integrate/SKILL.md) — plans the rollout (direct SDK / Ratel Local / hybrid) and the A/B tied to these native-telemetry metrics |

`/ratel-integrate` reads `.ratel/ratel-observability-assessment.md` as one of its inputs. Tell the user that.

## Honest skip path

If after Step 1 you cannot find a single LLM client import, agent loop, or model call in the codebase, stop. Do not write a proposal. Tell the user:

> No agent surface detected — only checked `<files looked at>`. If this codebase has agent code in a non-standard location, point me at it and I'll re-run.

Forced observability proposals on a non-agent codebase produce dead documents and waste partner trust. Better to skip and ask.

Ratel's native telemetry ships for TypeScript and Python. If the agent is in another language (e.g. Ruby, Go, or a niche framework), still produce the proposal — the instrumentation strategy and dashboard set are stack-agnostic, and the team can export Ratel's OTLP spans from a TS/Python Ratel Local sidecar — but mark the in-process SDK wiring "TS/Python only" and ask whether Ratel Local (MCP) is the right integration mode for that stack. Don't fake confidence.

## Reference files

- [`references/instrumentation-philosophy.md`](references/instrumentation-philosophy.md) — "trace the mental model, not the call graph" + the two anti-patterns
- [`references/native-telemetry-setup.md`](references/native-telemetry-setup.md) — how to turn on Ratel's native OTLP telemetry (TS + Python): span vocabulary, greenfield vs dual-export, content-capture opt-in, local trace stream
- [`references/semantic-conventions.md`](references/semantic-conventions.md) — the OTel span/attribute vocabulary the funnel and your agent spans share
- [`references/general-agent-dashboards.md`](references/general-agent-dashboards.md) — stack-agnostic agent-health dashboard catalog
- [`references/ratel-value-map.md`](references/ratel-value-map.md) — the single source of truth for what Ratel ships → observable signal; read across the suite
- [`references/vendor-detection.md`](references/vendor-detection.md) — per-backend detection signals + how you export Ratel's OTLP spans to each
- [`references/finding-catalog.md`](references/finding-catalog.md) — catalog of agent failure modes to look for when reviewing traces in your backend

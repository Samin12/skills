---
name: ratel-integrate-video-editor
description: "Inspect a customer agent codebase for its tool-management approach and framework, fetch Ratel docs, and write a markdown plan to integrate Ratel — integration mode (direct SDK / Ratel Local / hybrid), pilot scope, A/B test design, and rollout metrics keyed off Ratel's native OTLP telemetry. Use to add Ratel, set up the SDK, add tool search / hybrid retrieval, plan a Ratel pilot, rollout, or A/B test, or `/ratel-integrate`. Writes to repo/.ratel/, asks when ambiguous, never edits code; runs after /ratel-observability-assessment.\n"
---
# /ratel-integrate — plan a Ratel rollout for a customer agent

This skill integrates Ratel itself — its retrieval + capability-tool layer — not an AI-observability vendor; for turning on Ratel's native OTLP telemetry and picking a backend to export it to, see [`/ratel-observability-assessment`](../ratel-observability-assessment/SKILL.md).

Most partner engagements eventually want Ratel itself in the picture, not just observability around it. This skill turns "let's pilot Ratel here" into a concrete week-one plan: which integration mode to use, which tools to pilot first, how to A/B test the impact, and which telemetry metrics will tell you whether it worked.

The deliverable is a markdown plan the customer can implement and a clear answer to the question "how will we know if it helped." Both halves matter.

This skill builds on Ratel's native OTLP telemetry:

- **Run after** [`/ratel-observability-assessment`](../ratel-observability-assessment/SKILL.md) so Ratel's native OTLP telemetry is on and exporting to whatever OTel backend the customer runs — the retrieval+tool funnel spans (`ratel.search`, `execute_tool <tool id>`, `ratel.skill.load`, …) and the local JSONL trace stream are in place. If they aren't, the skill will point them back there before continuing.
- **Drives** the value dashboards defined in [`/ratel-observability-assessment`](../ratel-observability-assessment/SKILL.md) — those dashboards measure the integration this skill is planning. The skill should explicitly name which dashboards the customer should build / refresh after the rollout.
- **Feeds** later analysis — once traffic is flowing under the A/B split, the customer reads Ratel's spans and run metrics in their OTel backend (Ratel Cloud, Coming Soon, will derive these server-side) to surface findings from the integration.

## Philosophy

Three rules from past partner engagements that the plan should follow:

1. **Don't migrate the whole catalog in one shot.** Pick a pilot scope (one trace_name, one agent role, or a subset of tools) and prove the lift before broadening. Big-bang migrations bury the win in confounding factors.
2. **Always A/B.** A Ratel rollout without a control arm produces inconclusive numbers no matter how good the win is. The plan must include the A/B strategy, even if the strategy is "ship behind a flag at 10% and ramp."
3. **Pick the simplest integration mode that works.** Direct SDK in the agent's process beats Ratel Local for raw control; Ratel Local beats direct SDK when the customer is already speaking MCP. Don't over-architect — Ratel is a library, not a platform.

## Workflow

### Step 1 — Detect stack and tool management approach

Read manifest files and scan how the customer's agent learns about tools today. Concretely:

```bash
# Manifest
test -f package.json && jq -r '.dependencies // {}, .devDependencies // {} | keys[]' package.json | sort -u
test -f pyproject.toml && cat pyproject.toml
test -f uv.lock && head -50 uv.lock

# Tool registration sites
grep -rEn 'tools:\s*\{|tools:\s*\[|\.register\(|@tool\b|new Tool|defineTool|createTool|registerTool|McpServer\(|StdioClientTransport|listTools' \
  --include='*.ts' --include='*.tsx' --include='*.js' --include='*.py' \
  | head -100
```

Classify the tool-management approach into one of these buckets (impacts the integration mode in step 4):

| Approach in codebase | Signal | Likely integration mode |
| --- | --- | --- |
| Static tool list on every model call | `tools: { ... }` literal passed to `generateText` / `chat.completions.create` / `messages.create` | Direct SDK, replace-mode pre-filter |
| Dynamic registry + dispatcher | A central tool map + a `dispatch(toolId, args)` function | Direct SDK, replace-mode pre-filter (easiest swap) |
| MCP client consuming upstream servers | `Client` from `@modelcontextprotocol/sdk` / `mcp.client` | Ratel Local (Ratel ingests upstreams, agent talks to Ratel) |
| Mixed (some local tools + some MCP) | both signals present | Hybrid — Direct SDK for local + Ratel ingestion for MCP |
| LangGraph / CrewAI node tools | framework-managed tool surfaces | Direct SDK at the node boundary, framework-agnostic |

If after this step you cannot find any tools at all, use the [honest skip path](#honest-skip-path).

### Step 2 — Map the agent topology relevant to Ratel

Run an Explore agent (or do it directly for small repos) to answer:

1. **Where is the LLM call that takes a `tools:` parameter?** — that's the integration site for pre-filtering.
2. **What's the catalog size today and what's expected at steady state?** — Ratel's lift grows with catalog size; under ~15 tools the win is too small to justify the integration, and the plan should say so.
3. **Is there a single dispatcher** (good — drop-in replace) **or are tools dispatched inline** (need a small refactor)?
4. **What's the user-facing latency budget?** — the default `bm25` retrieval is model-free and in-process, adding well under a millisecond per call; `semantic`/`hybrid` load a local embedding model (eagerly at register) and cost a few ms per query after warm-up. Pick the method against the budget and tell the customer.
5. **Is the agent on prompt caching (Anthropic/Bedrock prompt cache, etc.) with multi-turn tool loops?** — decisive for the within-process strategy in Step 4. A naive replace-mode pre-filter rewrites the `tools:` block every turn, which sits near the start of the cached prefix and **invalidates the whole system+tools cache each turn** — it can cost more tokens than it saves. Cache-sensitive agents want recall mode (stable eager tools), not replace mode.

Capture this in 4-6 bullets in the plan.

### Step 3 — Fetch up-to-date Ratel documentation

Ratel ships fast (still pre-1.0, on the 0.4.x line). Don't recite from memory. Pull the current state at runtime.

Tier 1 (preferred): try [Context7](https://github.com/upstash/context7) via the available MCP tools. Resolve the library id for `ratel-ai/ratel` and fetch the README + SDK README. This gives you whatever version's current.

Tier 2: WebFetch `https://docs.ratel.sh`. Start with [`https://docs.ratel.sh/llms.txt`](https://docs.ratel.sh/llms.txt) then [`/llms-full.txt`](https://docs.ratel.sh/llms-full.txt) for the full corpus, or pull the targeted pages: [`/docs/core/quickstart`](https://docs.ratel.sh/docs/core/quickstart), [`/docs/core/sdks/typescript`](https://docs.ratel.sh/docs/core/sdks/typescript), [`/docs/core/sdks/python`](https://docs.ratel.sh/docs/core/sdks/python), [`/docs/core/tool-retrieval`](https://docs.ratel.sh/docs/core/tool-retrieval), [`/docs/core/agent-skills`](https://docs.ratel.sh/docs/core/agent-skills), [`/docs/core/telemetry`](https://docs.ratel.sh/docs/core/telemetry), and [`/docs/local`](https://docs.ratel.sh/docs/local).

Tier 3 (last resort): WebFetch raw GitHub READMEs, or — if the customer already has Ratel installed — read the package's own README from `node_modules/@ratel-ai/sdk/README.md` or the Python site-packages equivalent (most accurate for *their* pinned version). Canonical GitHub paths (Ratel Local and the CLI/MCP server aren't split into per-package READMEs upstream, so use the docs pages for those):

```
https://raw.githubusercontent.com/ratel-ai/ratel/main/README.md
https://raw.githubusercontent.com/ratel-ai/ratel/main/src/sdk/ts/README.md
https://raw.githubusercontent.com/ratel-ai/ratel/main/src/sdk/python/README.md
```

For the CLI / MCP server (Ratel Local) surface, read [`https://docs.ratel.sh/docs/local`](https://docs.ratel.sh/docs/local) instead.

Capture three things from whatever docs you read: the **current shipped version**, the **public API for tool/skill registration / search / invoke**, and the **capability tool names** (`search_capabilities`, `invoke_tool`, `get_skill_content`). If the public API has changed since the patterns in [`references/integration-patterns.md`](references/integration-patterns.md), trust the fetched docs and call out the discrepancy in the plan so the integration-patterns file gets updated next.

### Step 4 — Decide the integration mode

Based on Step 1's classification and Step 3's docs, pick one (and only one) primary integration mode:

- **Direct SDK** (TS `@ratel-ai/sdk`, or Python `ratel-ai` — `pip install ratel-ai`, at full parity) — import the Ratel SDK in the agent process, register tools into a `ToolCatalog`, and pick a **within-process strategy**:
  - **Replace mode** — swap the agent's tool list for protected-core ∪ `catalog.search(query, topK)`. Simplest; fine for stateless / single-shot calls.
  - **Recall mode** — keep a **stable eager tool list** (protected core + the capability meta-tools) and append per-turn retrieval hits as a synthetic `search_capabilities` tool-output at the transcript suffix. Use this when the agent is on prompt caching with multi-turn loops — replace mode busts the cache, recall mode preserves it.
  - **Gateway mode** — expose the in-process capability tools (`search_capabilities` / `invoke_tool`, plus `get_skill_content` if a `SkillCatalog` is registered) and let the agent discover on demand. Most token-efficient at large catalogs; costs a discovery turn.

  Two non-negotiables for replace and recall: (1) a **protected core** of must-keep tools (control loop, workspace readers, build chain) that retrieval never trims, or trimmed tools surface as `NoSuchToolError`; (2) an empty-query/no-match fallback that keeps the full pool. Register a `SkillCatalog` too for customers who also ship playbook-style skills, and pass it as the second arg to `searchCapabilitiesTool` so one search ranks tools and skills together. See [`references/integration-patterns.md`](references/integration-patterns.md) for the cache trap, the protected-core snippet, and the recall-mode shape.
- **Ratel Local** — run `ratel serve` (or `@ratel-ai/mcp-server`) as a process; configure the customer's agent to talk to it via MCP. Their existing tool sources get ingested as upstreams. (Docs: [`/docs/local`](https://docs.ratel.sh/docs/local).)
- **Hybrid** — Direct SDK for the agent's local tools; Ratel Local as one of the agent's MCP clients for upstream-provided tools. Only recommend this when both kinds of tool surfaces exist.

The plan should state the choice and the reason in one sentence ("Direct SDK because there's a single dispatcher in `src/agent/dispatch.ts:42` and no MCP upstreams").

Read [`references/integration-patterns.md`](references/integration-patterns.md) for the per-mode setup and the per-framework code shape.

### Step 5 — Pick the pilot scope

Don't migrate everything. Recommend a pilot scope:

- **By trace_name**: pilot on the single trace_name with the highest token spend per turn (the customer can confirm from their OTel backend's aggregates, or the local trace stream).
- **By agent role**: pilot on one sub-agent (e.g., `research-agent`) and leave the supervisor alone.
- **By tool subset**: pilot with just the top-50 most-called tools registered, leaving the long tail out for v1.
- **By traffic**: ship behind a flag at 10% and ramp on green metrics.

Pick one or two of these and justify. State explicitly what is **out of pilot scope** so the customer doesn't accidentally widen.

### Step 6 — Design the A/B test

Read [`references/ab-test-patterns.md`](references/ab-test-patterns.md). Pick a strategy and customise to the codebase:

- **Live feature flag** (preferred when traffic is healthy): tag the trace `feature_flag=tool_pool=ratel` vs `tool_pool=full`. Both arms run on real traffic.
- **Shadow mode** (when production risk is high): production keeps the original path; the Ratel path runs in parallel, its spans export to your OTel backend, but its output isn't returned to the user.
- **Replay** (when traffic is too thin for a live split): collect inputs from the original path into a dataset (your eval store, or any OTel backend that keeps inputs); replay through Ratel afterwards.

For each: state the trace tags / span attributes the customer must emit so the value dashboards from [`/ratel-observability-assessment`](../ratel-observability-assessment/SKILL.md) light up correctly.

If the codebase doesn't have an existing flagging pattern, **ask the user** before recommending one of your own. Common patterns to ask about: feature flag SaaS (LaunchDarkly, Statsig, GrowthBook), env-var split, percent-of-user hashing, internal experimentation framework.

Sample prompt to the user when in doubt:

> The codebase doesn't have an obvious feature-flag layer for this A/B. Do you have an internal pattern for traffic splits — e.g., a LaunchDarkly client, env-based toggles, or a percentage rollout helper — or should I propose a minimal one inline in the plan?

### Step 7 — Tie to observability metrics

The integration is worthless if no one can prove it worked. These metrics key off Ratel's **native OTLP telemetry** — the funnel spans the SDK emits (`ratel.search`, `execute_tool <tool id>`, `ratel.skill.load`, …) plus the local JSONL stream, exported to whatever OTel backend the customer runs (or dual-exported via `ratelSpanProcessor` / `ratel_span_processor`). Ratel does **not** emit LLM-call (`chat <model>`) spans — token counts come from the customer's own LLM instrumentation on the same trace. Name the **exact dashboards and scores** that measure this rollout, sourced from the conceptual value map at [`ratel-observability-assessment/references/ratel-value-map.md`](../ratel-observability-assessment/references/ratel-value-map.md) and the native-telemetry vocabulary in [`ratel-observability-assessment/references/native-telemetry-setup.md`](../ratel-observability-assessment/references/native-telemetry-setup.md):

- **Token Cost & Savings** dashboard — the headline. Split by `feature_flag` tag. The plan must guarantee the LLM-call spans' `gen_ai.usage.input_tokens` land in the arm tag correctly (these come from the customer's LLM instrumentation, not Ratel).
- **Retrieval Quality** dashboard — reads the `ratel.search` spans' attributes `top_hit_score`, `hit_count`, `top_k`, `took_ms`. These are emitted natively by the SDK; the plan just needs telemetry turned on (see [`native-telemetry-setup.md`](../ratel-observability-assessment/references/native-telemetry-setup.md)).
- **Origin Split** dashboard — reads the `origin` (`direct` | `agent`) attribute on `ratel.search` spans, showing how much retrieval the agent drove itself vs. the direct pre-filter path.
- **Stranded-tool guardrail** — a per-turn `ratel_unavailable_tool_call` signal (calls to a tool the pre-filter trimmed, distinguished from genuine hallucinations via the removed-name set). This is the safety signal that proves the protected-core / recall setup didn't break tool access; it must trend to ~0. Pair it with a protected-count metric if the customer wants to see how much of the pool the protected core holds. For cache-sensitive agents, also watch cached-vs-uncached input tokens on the Token Cost dashboard — that's where a replace-mode cache regression shows up.
- **Scores** — recommend wiring `tool_selection_accuracy` and `top_k_recall_at_5` if any form of ground truth (gold-labelled tool ids per task, eval dataset) exists.

If the customer has not yet run `/ratel-observability-assessment` (native telemetry on, exporting to a backend), **do not proceed** to Step 8. Route them back. Building a Ratel plan that nobody can measure produces an unverifiable engagement.

### Step 8 — Ask for any missing information

Before writing the plan, check what you don't know and ask. The skill must surface its assumptions, not bury them. Common questions:

- Is there a preferred Ratel version to pin to? (default: whatever's `latest` per Step 3)
- Which Ratel feature(s) does the partner most want to validate first — tool retrieval, hybrid (lexical+semantic) retrieval, first-class skills, the origin pattern, and native OTLP telemetry are all shipped; server-side ranked suggestions ship with Ratel Cloud (Coming Soon)?
- Is the agent on prompt caching with multi-turn tool loops? (decides replace vs recall mode — see Step 2/Step 4; cache-sensitive ⇒ recall)
- Is there ground truth labelling for any task, even for a subset? (drives the score-wiring decision)
- Are there cost/latency budgets the integration must not bust?
- Is the agent in production, internal preview, or pre-launch? (changes risk tolerance for A/B)

Group these into one batched question for the user (use `AskUserQuestion` if available, or list them in chat). Don't proceed with the plan until you have the answers.

### Step 9 — Write the plan

Output to `<repo>/.ratel/ratel-integrate.md`. Sections, in order:

1. **Summary** — stack, tool management approach, integration mode picked, pilot scope, A/B strategy, target Ratel version. Six bullets max.
2. **Up-to-date docs reference** — note the Ratel version the plan was written against and the docs source (Context7 / GitHub raw / installed package).
3. **Topology + tool-management map** — from Steps 1-2.
4. **Integration plan** — file-by-file diff intent: where to register tools, where to swap the tool list / wire the dispatcher / connect Ratel Local, where the retrieval `origin` (`direct` | `agent`) is set. Cite [`integration-patterns.md`](references/integration-patterns.md) rather than re-deriving.
5. **A/B test plan** — strategy from Step 6, including the exact trace tag values and the feature-flag wiring choice (deferring to the user's pattern if they provided one).
6. **Metrics & dashboards** — table mapping the value dashboards from [`/ratel-observability-assessment`](../ratel-observability-assessment/SKILL.md) to "now / after rollout / after pilot expansion."
7. **Roadmap pointers** — only what's directly relevant to this customer. Tool retrieval, hybrid retrieval, first-class skills, the origin pattern, and native OTLP telemetry are all shipped on the 0.4.x line, so they belong in the integration plan, not here. Server-side ranked suggestions arrive with Ratel Cloud (Coming Soon); prompt decomposition has its own skill (`/ratel-decompose-prompt`). Don't list the whole roadmap.
8. **Open questions** — anything still ambiguous from Step 8.
9. **Verification checklist** — six items the customer can tick after the integration lands: pilot trace_name uses Ratel, `feature_flag` tag is split correctly, `ratel.search` spans appear with their retrieval attributes, `ratel_unavailable_tool_call` trends to ~0 (no stranded tools), Token Cost & Savings dashboard shows separation between arms (and, for cache-sensitive agents, the treatment arm's cached-token ratio did not regress), Retrieval Quality dashboard has data.

Print the table of contents inline in chat (six bullets max) and tell the user the file path. Do not paste the full plan body into the chat.

## Honest skip path

Three skip cases:

1. **No LLM tool surface in the codebase.** No `tools: { ... }` parameter, no `@tool` decorators, no MCP client. Tell the user there's nothing for Ratel to pre-filter and stop. Don't fabricate a "potential future fit."
2. **Catalog too small (<15 tools).** Ratel's benefit grows with catalog size; under ~15 well-described tools, the integration overhead exceeds the win. Tell the user this and suggest revisiting when the catalog grows.
3. **Telemetry not yet turned on.** Route to [`/ratel-observability-assessment`](../ratel-observability-assessment/SKILL.md) first — turn on Ratel's native OTLP telemetry and export it to whatever OTel backend the customer runs. A Ratel rollout without telemetry is not measurable, and an unmeasurable rollout is indistinguishable from no rollout.

## Reference files

- [`references/integration-patterns.md`](references/integration-patterns.md) — per-mode and per-framework integration shapes
- [`references/ab-test-patterns.md`](references/ab-test-patterns.md) — feature-flag, shadow, and replay A/B strategies + how to tag traces so the dashboards split correctly

Reads from (don't duplicate):

- [`../ratel-observability-assessment/references/native-telemetry-setup.md`](../ratel-observability-assessment/references/native-telemetry-setup.md) — how Ratel emits the retrieval+tool funnel natively as OTLP spans (`ratel.search`, `execute_tool`, `ratel.skill.load`, …), plus greenfield `configureTelemetry()` and dual-export `ratelSpanProcessor()` setup for TS + Python
- [`../ratel-observability-assessment/references/ratel-value-map.md`](../ratel-observability-assessment/references/ratel-value-map.md) — Ratel feature → observable native signal → status (backend-agnostic; `/ratel-observability-assessment` renders the concrete dashboards)

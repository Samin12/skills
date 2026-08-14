# Ratel integration patterns

The per-mode and per-framework code shapes for wiring Ratel into an agent. Read this **after** Step 3 of the skill — i.e., after you have the up-to-date docs in hand. If anything here disagrees with the latest docs, trust the docs and flag this file for an update.

Public Ratel surface (on the 0.4.x line — verify against the live docs per Step 3, the API moves fast):

- TS SDK: `@ratel-ai/sdk` — `ToolCatalog`, `ToolRegistry` (metadata-only index, no executors), `SkillCatalog`, `searchCapabilitiesTool(catalog, skillCatalog?)`, `invokeToolTool(catalog)`, `getSkillContentTool(skillCatalog)`, `registerMcpServer(catalog, config)`. One search tool spans both catalogs — pass the `SkillCatalog` as the second arg to `searchCapabilitiesTool` and it ranks tools and skills in the same call ("one search tool, two catalogs").
- Python SDK: `ratel-ai` (`pip install ratel-ai`, shipped at full parity) — `ToolCatalog`, `SkillCatalog`, `Skill`, `search_capabilities_tool`, `invoke_tool_tool`, `get_skill_content_tool`, `register_mcp_server`. (Package is `ratel-ai`, not `ratel`.)
- CLI / MCP server (Ratel Local): `@ratel-ai/mcp-server` (npm), also published as the `ratel-mcp` CLI — `ratel serve`, `ratel mcp add | list | edit`, `ratel inspect`. Exposes the unified `search_capabilities`, `invoke_tool`, and `get_skill_content` capability tools to any MCP client. (`search_tools` remains a **deprecated** tools-only compat alias; prefer `search_capabilities`.) Docs: [`/docs/local`](https://docs.ratel.sh/docs/local).

Retrieval runs one of three selectable methods — `bm25` (default; lexical, model-free, in-process), `semantic` (local embedding model, cosine over per-tool vectors), or `hybrid` (RRF fusion of both, k=60, no reranker) — chosen per-catalog at construction or overridden per-call. All in-process; no vector DB. `search_capabilities(query, topKTools?, topKSkills?)` returns `{ tools: { groups }, skills: [...] }` — two independently-ranked buckets. `get_skill_content(skillId)` returns `{ body }`; skills are read, not executed.

> **Two patterns below are integration-level, not SDK functions.** "Protected core" and "recall mode" are things *you* build around these primitives — there is no `protectedCore()` or `recallMode()` export. They came out of a real rollout (see the cache + protected-core sections) and the skill teaches them because the naive replace-mode default strands tools and busts the prompt cache. Don't go looking for an SDK call.

## Mode 1 — Direct SDK (TypeScript)

Best when:
- The agent process is Node/TS.
- There's a single dispatcher or a static `tools:` parameter.
- You want full control over when retrieval runs vs when the capability tools are exposed.

Shape:

```ts
import { ToolCatalog, SkillCatalog, searchCapabilitiesTool, invokeToolTool, getSkillContentTool } from "@ratel-ai/sdk";

// 1. Build the catalog once at process start.
const catalog = new ToolCatalog({
  trace: { kind: "jsonl", sessionId: process.env.SESSION_ID ?? "boot", path: "..." },
  // Native OTLP telemetry is separate: wire it once with configureTelemetry() (greenfield) or
  // ratelSpanProcessor() into your existing OTel provider — see native-telemetry-setup.md.
});

// 2. Register every tool the agent should know about.
for (const tool of allTools) {
  catalog.register({
    id: tool.id,
    name: tool.name,
    description: tool.description,
    inputSchema: tool.inputSchema,
    outputSchema: tool.outputSchema,
    execute: tool.run,
  });
}

// 3a. Replace-mode (pre-filter): swap the model's tool list for protected core + top-K hits.
// PROTECTED CORE: retrieval ranks the *whole* pool, so a thin or off-topic query can trim a tool
// the agent always needs (the control loop, workspace readers, a build toolchain). When that
// trimmed tool is later called the model gets a NoSuchToolError. Keep a hardcoded must-keep set
// unconditionally and rank only the discretionary tail: result = protected ∪ topK(tail).
const protectedIds = protectedToolNames(profile, agentId); // your manifest, intersected with the live pool
const tail = catalogTools.filter(t => !protectedIds.has(t.id));
const hits = catalog.search(currentUserMessage, /* topK = */ 8, "direct"); // ranks the tail
const filteredTools = [
  ...catalogTools.filter(t => protectedIds.has(t.id)),
  ...hits.flatMap(({ toolId }) => tail.filter(t => t.id === toolId)),
];
// Empty-query / no-match fallback: keep the full pool rather than stranding everything.
const result = await generateText({ model, tools: filteredTools, /* ... */ });

// 3b. Gateway-mode: expose the in-process capability tools so the agent can reach more on demand.
// Pass the SkillCatalog as the 2nd arg to searchCapabilitiesTool to rank tools + skills in one call.
const result = await generateText({
  model,
  tools: {
    search_capabilities: searchCapabilitiesTool(catalog, skillCatalog),
    invoke_tool: invokeToolTool(catalog),
    get_skill_content: getSkillContentTool(skillCatalog),
  },
});
```

Python is the same shape (`ratel-ai`, full parity):

```python
from ratel_ai import ToolCatalog, SkillCatalog, search_capabilities_tool, invoke_tool_tool, get_skill_content_tool

catalog = ToolCatalog(trace={"kind": "jsonl", "session_id": os.environ.get("SESSION_ID", "boot"), "path": "..."})
for tool in all_tools:
    catalog.register(id=tool.id, name=tool.name, description=tool.description,
                     input_schema=tool.input_schema, output_schema=tool.output_schema, execute=tool.run)

# Gateway-mode tools to expose to the agent:
tools = {"search_capabilities": search_capabilities_tool(catalog), "invoke_tool": invoke_tool_tool(catalog)}
```

**Choosing the within-process strategy (replace vs recall vs gateway) — read this before defaulting to replace.**

Replace-mode is the simplest, but on a prompt-cache-sensitive agent it can *cost* tokens rather than save them — see [Replace vs recall: the prompt-cache trap](#replace-vs-recall-the-prompt-cache-trap) below. Quick rule:

- **Agent on prompt caching (Anthropic, etc.) with multi-turn tool loops → recall mode.** Stable eager tool list = cache survives.
- **Stateless / single-shot calls, or no caching → replace-mode with topK=8 + protected core.** Simplest, and there's no cached prefix to bust.
- **Very large catalog and the agent can handle a discovery turn → gateway mode.** Most token-efficient at scale but adds a model turn per discovery.

### Replace vs recall: the prompt-cache trap

Replace-mode rewrites the model's `tools:` parameter every turn. That block sits near the **start** of the provider's cached prefix (system + tools), so rewriting it **invalidates the entire system+tools prefix every turn** — you pay it uncached on every call. On a cache-sensitive agent this can wipe out, or exceed, the savings from sending fewer tool definitions. The skill's headline "Token Cost & Savings" dashboard is exactly where this regression shows up, so don't ship replace-mode blind on a cached agent.

**Recall mode** decouples *callable* from *discoverable* and keeps the cache intact:

1. The eager `tools:` list stays **stable across turns** — protected core + the capability meta-tools (`search_capabilities`, `invoke_tool`, `get_skill_content`). A stable prefix stays cached.
2. Per-turn retrieval recall is appended as a **synthetic `search_capabilities` tool-output at the transcript suffix** — it *extends* the cached prefix instead of busting it; prior turns' recall messages stay untouched.
3. The long tail is **parked, not trimmed** (off to the side, e.g. on the runner's context), and reached on demand via `invoke_tool`. Nothing is stranded; a thin query degrades to a deterministic always-recall set so unavailable-tool calls trend to ~0.

Recall mode is an integration pattern you build on top of the SDK primitives (stable eager set + a function that materialises the recall tool-output each turn), not a single SDK call. Gate it behind a flag, default off, and prove the cache win on the Token Cost & Savings dashboard before enabling.

If the customer also ships playbook-style skills, register a `SkillCatalog` alongside the `ToolCatalog`: skills are indexed on name/description/tags and surfaced via the `search_capabilities` skills bucket, then read on demand with `getSkillContentTool` / `get_skill_content_tool` (`get_skill_content(skillId) → { body }`). Skills are loaded, not executed — there is no `invoke_skill`.

### Vercel AI SDK specifics

The two patterns above drop into `generateText` / `streamText` directly. Ratel's native OTLP spans join the same trace as the Vercel AI SDK's own `ai.*` spans automatically once telemetry is wired; if you dual-export via `ratelSpanProcessor()` into the AI SDK's existing OTel provider, a default signal filter forwards only `ratel.*` / `gen_ai.*` spans and keeps the `ai.*` wrapper noise out (see [`native-telemetry-setup.md`](../../ratel-observability-assessment/references/native-telemetry-setup.md)).

### Mastra / generic TS specifics

Same shape — register tools into the catalog instead of (or in addition to) Mastra's tool registry. For the pilot, keep the customer's existing registry and tee tools into the Ratel catalog; the agent's tool surface is whatever you pass to the model call.

## Mode 2 — Ratel Local

Best when:
- The customer's agent already speaks MCP (Claude Desktop, Cursor, Goose, custom MCP client).
- Tools come from one or more MCP upstream servers and the customer wants Ratel in front of them.
- The customer prefers an out-of-process server (Ratel Local) over importing the SDK (note: a Python SDK is now shipped, so Python is no longer forced into this mode — see Mode 1).

Setup steps for the plan:

1. **Install** `@ratel-ai/mcp-server` (npm) or `ratel-mcp` (whichever the customer prefers).
2. **Configure upstreams**: `ratel mcp add <name> --transport stdio --command "<cmd>"` or `--transport sse --url ...`. Each upstream's tools are ingested into the catalog with namespace prefix `upstream__toolName`.
3. **Run** `ratel serve` as the MCP server the agent connects to. Point the agent's MCP config at this process.
4. **Auth (if needed)**: for SSE/HTTP upstreams that use OAuth, run `ratel mcp auth <name>` once per upstream — Ratel handles refresh and re-auth after that.
5. **Telemetry**: Ratel Local emits the retrieval+tool funnel natively as OTLP spans (`ratel.search`, `execute_tool <tool id>`, `ratel.skill.load`, …). Point it at any OTel backend via `RATEL_URL`, or keep the local JSONL trace stream (`~/.ratel/telemetry/<project-slug>/<session-id>.jsonl`) for statusline / offline inspection. See [`native-telemetry-setup.md`](../../ratel-observability-assessment/references/native-telemetry-setup.md).

The agent sees Ratel's unified capability tools (`search_capabilities`, `invoke_tool`, and `get_skill_content` when skills are registered). To use a tool, it calls `search_capabilities` first and then `invoke_tool` with the returned id. This is the most token-efficient mode at very large catalogs but requires the agent to handle the discovery step.

### Python specifics

Python can integrate directly via the shipped `ratel-ai` SDK (Mode 1) or via Ratel Local. For the Ratel Local path with LangChain / LlamaIndex agents, install an MCP client (e.g., `mcp` from PyPI) and configure it to talk to `ratel serve`. For LangGraph / CrewAI agents, the same MCP client wraps the agent's tool node.

## Mode 3 — Hybrid

Best when:
- The agent has a mix of local tools (defined in the customer's codebase) and upstream MCP tools.
- The customer wants Ratel ranking across both.

Shape:

1. Register the local tools into a `ToolCatalog` via the direct SDK (Mode 1).
2. Use `registerMcpServer(catalog, { name, transport })` to ingest each MCP upstream into the **same** catalog. Tools land with the `upstream__` prefix.
3. Expose `searchCapabilitiesTool(catalog, skillCatalog?)` + `invokeToolTool(catalog)` to the agent (add `getSkillContentTool(skillCatalog)` if a `SkillCatalog` is also registered). Search ranks across local and upstream uniformly; invocation routes to the right executor automatically.

This mode is exactly Mode 1 plus `registerMcpServer` calls. Don't dual-instantiate.

## Per-framework callouts

### Vercel AI SDK

- Pre-filter at the call site (where `tools:` is passed). Don't try to wrap the SDK.
- If the agent uses `maxSteps > 1` for multi-turn tool loops, pre-filter once at the start of the loop — the SDK reuses the same tool list across steps. Re-running search every step is wasted work and breaks the simple "this turn used this top-K" trace pattern.

### LangChain (Python)

- Pre-filter at the agent constructor (`AgentExecutor(tools=...)`) using the shipped `ratel-ai` SDK (Mode 1), or use Mode 2 (Ratel Local) and have LangChain talk MCP.
- If using Mode 2, the agent gets `search_capabilities` and `invoke_tool` as plain tools; document this in the plan since LangChain users don't expect two-step tool calling.

### LangGraph

- The tool node is where the tools list lives. Mode 2 wraps the tool node with an MCP client; Mode 1 (via the shipped `ratel-ai` SDK) replaces the node's tools with the catalog's search results.
- Multi-agent graphs: the catalog should be **shared** across nodes (same in-process instance for Mode 1; same `ratel serve` for Mode 2). Per-node catalogs defeat the point.

### CrewAI

- Per-agent tool lists in CrewAI map to per-agent catalogs in Mode 1 (now available via the shipped `ratel-ai` SDK). Mode 2 with `ratel serve` also works — each agent runs its own MCP client against the same Ratel Local process.

### Custom agent loops (no framework)

- These are the easiest case. Pre-filter wherever the tools list is materialised for the model. The dispatcher swap is a 10-line change.

## What the plan must specify

For each agent surface the plan touches, the per-file changes must answer:

1. **Mode**: direct SDK / Ratel Local / hybrid, **and** the within-process strategy (replace / recall / gateway) with the cache rationale in one sentence.
2. **Init site**: the file + line where the `ToolCatalog` (and `SkillCatalog`, if any) is constructed (Mode 1) or where `ratel serve` (Ratel Local) is launched (Mode 2).
3. **Registration site**: where every tool the agent uses is registered.
4. **Protected core**: the must-keep tool set (control loop, workspace readers, build chain, …) that retrieval must never trim, and where that manifest lives. Required for replace and recall modes.
5. **Swap site**: where the agent's `tools:` parameter is replaced with protected-core + top-K (replace), or where the stable eager list is set and the per-turn recall tool-output is appended (recall), or where the capability tools are exposed (gateway).
6. **Telemetry wiring**: the `ratel.search` span carries `origin` (`direct` | `agent`), `top_k`, `hit_count`, `top_hit_score`, and `took_ms` natively — the plan just confirms telemetry is on and exporting. If the customer wants a `replace_mode` marker, add it as an extra attribute at the swap site. See [`native-telemetry-setup.md`](../../ratel-observability-assessment/references/native-telemetry-setup.md).
7. **Stranded-tool guardrail**: where a per-turn `ratel_unavailable_tool_call` score is emitted (count of calls to a tool the pre-filter trimmed, distinguished from genuine hallucinations via the removed-name set). This is the signal that proves protected-core / recall didn't break tool access; it should trend to ~0.
8. **Flag check**: where the A/B feature flag is read to decide which arm of the split the request belongs to (see [`ab-test-patterns.md`](ab-test-patterns.md)).

# Stack detection

How to classify an agent codebase into one of four stack profiles. The classification drives where the assessment workflow looks for tools, prompts, sub-agents, and observability config — and it tells you which surfaces to hand off to [`/ratel-observability-assessment`](../../ratel-observability-assessment/SKILL.md) when recommending follow-ups.

This file is intentionally light. The deep per-stack instrumentation patterns (init shapes, telemetry wiring across stacks) now live in [`/ratel-observability-assessment`](../../ratel-observability-assessment/SKILL.md), which owns turning on Ratel's native OTLP telemetry and exporting it to whatever OTel backend the partner runs. Do not duplicate those here.

## The four profiles

- **Vercel AI SDK**
- **TypeScript generic** (Mastra, direct provider SDKs, custom loops)
- **Python generic** (LangChain, LlamaIndex, direct provider SDKs)
- **Python agentic** (LangGraph, CrewAI, Agno, AutoGen)

For the per-stack instrumentation detail behind any of these — native-telemetry setup, dual-export into an existing provider, backend selection — cross-link the report to [`/ratel-observability-assessment`](../../ratel-observability-assessment/SKILL.md). It carries the native-OTLP wiring for each stack.

## Detection signals

### Vercel AI SDK

Manifest:

```bash
test -f package.json && jq -r '.dependencies // {}, .devDependencies // {} | keys[]' package.json | grep -E '^(ai|@ai-sdk/)'
```

Confirming code patterns:

```bash
grep -rEn '(generateText|streamText|generateObject|streamObject)\(' \
  --include='*.ts' --include='*.tsx' --include='*.js' | head -20
```

If `ai` + `@ai-sdk/<provider>` are in the manifest and `generateText` / `streamText` appears in code, this is a Vercel AI SDK codebase.

**Common pattern**: tools as `{ tools: { name: { description, inputSchema, execute } } }` literals passed to `generateText`. Sub-agents are usually nested `generateText` calls or `experimental_telemetry.functionId` for OTel naming.

**Assessment-specific notes**:

- Tool sprawl tends to live at a single call site rather than across files. Easy to count; easy to fix.
- Observability typically wires via `@vercel/otel` plus an OTLP exporter (a `LangfuseExporter`, an OTLP collector endpoint, or Ratel's native span processor). The presence of `OpenTelemetry` imports does not guarantee a backend is reachable — check the exporter config for where spans actually go.
- `maxSteps` parameter (when present) caps the agent's tool loop; absence is a Critical finding under Error handling if the agent loops on tools.

### TypeScript generic

Manifest signals (any of):

```bash
jq -r '.dependencies // {}, .devDependencies // {} | keys[]' package.json | grep -E '^(@mastra/|openai|@anthropic-ai/sdk|@google/generative-ai|groq-sdk|mistralai|@modelcontextprotocol/sdk)$'
```

Confirming code patterns:

```bash
grep -rEn '(new\s+OpenAI|new\s+Anthropic|@mastra/core|mastra\.tools|chat\.completions\.create|messages\.create|generateContent|new\s+Client\(\s*\{\s*name)' \
  --include='*.ts' --include='*.tsx' --include='*.js' | head -20
```

This profile covers Mastra agents, raw provider SDKs, custom loops, and MCP clients. If both `ai` and a raw provider SDK appear, treat the codebase as Vercel AI SDK primary with mixed-stack notes.

**Assessment-specific notes**:

- Tool definitions are scattered (Mastra `createTool` calls in one file, hand-rolled `tools` arrays in another). Use grep across the whole repo, not just the entry-point file.
- Mastra agents make sub-agent topology explicit; raw-loop codebases tend to hide topology in branching prompts — flag this under Agent topology (1.a).
- MCP client presence (`@modelcontextprotocol/sdk`) means an MCP upstream is in play; check Dimension 2 for tool duplication across upstreams.

### Python generic

Manifest signals (any of):

```bash
(test -f pyproject.toml && head -200 pyproject.toml; test -f requirements.txt && cat requirements.txt; test -f uv.lock && head -50 uv.lock) \
  | grep -iE '(^| |"|=)(openai|anthropic|google-generativeai|groq|mistralai|langchain|llama[_-]index|langfuse)( |"|=|,|$)' \
  | head -20
```

Confirming code patterns:

```bash
grep -rEn '(OpenAI\(|Anthropic\(|chat\.completions\.create|messages\.create|generate_content|from langchain|from llama_index|@tool\b|@function_tool\b)' \
  --include='*.py' | head -20
```

LangChain / LlamaIndex / raw provider SDKs all land here unless the codebase also pulls in an agentic framework (in which case it's the next profile).

**Assessment-specific notes**:

- Look for native OTel spans (Ratel's SDK emits the retrieval/tool funnel as `gen_ai.*` + `ratel.*` OTLP spans), a generic OTel/OpenLLMetry setup, or vendor decorators such as `langfuse`'s `@observe()` — any one is a positive signal. Absence of all of them is a strong signal Dimension 7 (Observability) is Weak or Missing.
- LangChain's `AgentExecutor` ships its own callback handler; check that it's wired to a real backend (an OTLP/Langfuse/LangSmith callback), not just to stdout.
- Tool descriptions in `@tool` decorators come from the docstring — empty docstrings are 2.c (Anemic tool descriptions).

### Python agentic

Manifest signals (any of):

```bash
(test -f pyproject.toml && head -200 pyproject.toml; test -f requirements.txt && cat requirements.txt; test -f uv.lock && head -50 uv.lock) \
  | grep -iE '(^| |"|=)(langgraph|crewai|agno|autogen|pyautogen|smolagents)( |"|=|,|$)' \
  | head -20
```

Confirming code patterns:

```bash
grep -rEn '(StateGraph|create_react_agent|@agent\b|Crew\(|Agent\(|Task\(|register_function|GroupChat|AssistantAgent|UserProxyAgent|from\s+agno)' \
  --include='*.py' | head -20
```

If both this profile and Python generic match, treat this as the primary profile and note the mixed-stack callout in the report.

**Assessment-specific notes**:

- Topology is explicit in the framework's graph / crew / team objects. Dimension 1 is usually Strong on signal-presence; the questions become naming clarity and handoff plumbing.
- These frameworks generally support OpenInference / OpenLLMetry instrumentation, and Ratel's SDK emits its funnel as native OTLP alongside them. Absence of any OTel instrumentation and of any explicit vendor wiring (Langfuse / LangSmith / collector) is Dimension 7 Missing.
- Recursion / depth bounds (1.c) are framework-configurable but often left at defaults — check.

## Fallback: stack unknown

If none of the four profiles match cleanly:

- If LLM client imports exist but the framework doesn't fit (e.g., a Go agent, a Ruby Sinatra agent, a Rust loop) — proceed by analogy. Score every dimension you can. Note in the report's executive summary that the stack is outside the catalog's primary coverage so the partner sees you noticed.
- If no LLM client imports exist anywhere — this is not an agent codebase. Use the honest-skip path in the main SKILL.md.

## Mixed stacks

It is common to find a primary stack with smaller secondary surfaces — e.g., a Vercel AI SDK frontend agent that also runs background LangChain jobs. Score against the primary stack (where most of the agent surface lives) and note the secondary surface in a single line in the topology section of the report.

Do not produce two reports for one codebase. The deliverable is one assessment per repo per run.

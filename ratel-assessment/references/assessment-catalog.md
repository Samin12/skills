# Assessment catalog

Twelve dimensions. For each: what it covers, how to score it, the concrete findings that surface under it, and the Ratel angle where one exists.

**Ratel angles point to entries in [`../../ratel-observability-assessment/references/ratel-value-map.md`](../../ratel-observability-assessment/references/ratel-value-map.md)** — that file is the single source of truth for "what Ratel ships when." Do not invent angles here; if a finding feels Ratel-relevant but doesn't match a value-map entry, leave the Ratel angle off.

**Severity tags throughout**:

- **Critical** — the agent is broken or unsafe in production today.
- **Major** — measurable hit to cost / quality / reliability; will bite within weeks.
- **Minor** — real but contained; the team can defer with low cost.
- **Info** — observation worth noting; not a defect.

**Scorecard mapping per dimension**:

- **Strong** — no findings worse than Info.
- **Adequate** — at most two Minor findings; no Major or Critical.
- **Weak** — at least one Major finding (no Criticals).
- **Missing** — at least one Critical, or the dimension's surface is entirely absent where it should exist.

---

## 1. Agent topology

What it covers: how the agent is structured — single loop, supervisor + workers, graph of nodes — and whether the boundaries are explicit enough to reason about.

**Detection inputs**:

- Count of named agent functions / classes / nodes.
- Presence vs absence of named sub-agents (vs the same loop run with different prompts).
- Handoff sites: where one agent calls another.
- Frameworks that make topology explicit (LangGraph, CrewAI, Mastra agents) vs ones that don't (bare `generateText` loops).

**Common findings**:

### 1.a Flat topology where the agent actually delegates

*Detection*: the codebase has one entry point, one loop, no named sub-agents — but the system prompt mentions delegation ("first plan, then research, then write") or the conversation history shows multi-phase work.

*Severity*: Minor by default; Major if the loop is >200 lines or the prompt is >2000 tokens of role-mixing instructions.

*Recommendation*: split into explicit sub-agents (supervisor + workers). The split is mechanical once the boundaries are named.

*Ratel angle*: matches the "Multi-agent decomposition hints" entry (roadmap, Coming Soon). Ratel will propose decompositions automatically once shipped; until then, the manual split is the right move.

### 1.b Sub-agents exist but handoffs are implicit

*Detection*: agent functions call other agent functions, but no `session_id` / `agent_role` / context is passed through the call boundary.

*Severity*: Major — multi-turn analysis and observability are silently broken across the boundary.

*Recommendation*: thread `session_id`, `user_id`, and a `parent_role` through every handoff. Standard OTel context propagation (or a tracer's `propagate_attributes(...)` helper) carries this once observability is wired.

*Ratel angle*: none directly — fix in [`/ratel-observability-assessment`](../../ratel-observability-assessment/SKILL.md).

### 1.c Topology is too deep to debug

*Detection*: ≥4 levels of nesting, or recursive sub-agent calls without a depth bound.

*Severity*: Major — small bugs (a tool misfire) blow up into runaway sessions.

*Recommendation*: add a max-depth bound and a circuit breaker on sub-agent recursion. Flatten the topology if the depth doesn't carry information the model uses.

*Ratel angle*: none.

---

## 2. Tool surface

What it covers: tool count, naming quality, description quality, schema rigor, duplication, dead tools.

**Detection inputs**:

- Total tool count — grep for `defineTool`, `createTool`, `@tool`, `@function_tool`, `tools: {`, MCP `listTools` returns.
- Per-tool description length and quality.
- JSON schema presence and tightness.
- Duplicate / near-duplicate tools (e.g., `read_file` and `get_file_contents`).
- Tools registered but never referenced in any prompt, dispatch site, or fixture (dead).
- Tool count growth over time (git log on tool registration files).

**Common findings**:

### 2.a Tool sprawl

*Detection*: ≥20 tools exposed on a single model call (or ≥40 in the catalog total). Severity scales with size.

*Severity*: Minor at 20–30, Major at 30–60, Critical at >60. Adjust down if descriptions are exceptional; the count is a proxy for input-token pressure.

*Recommendation*: pre-filter the tool list per turn so the model only sees the top-K relevant tools. The full catalog stays addressable via a discovery tool.

*Ratel angle*: matches "hybrid capability retrieval" and "replace-by-default pre-filter" (shipped). Ratel ranks the catalog in-process (BM25 by default, opt-in semantic and hybrid RRF — no vector DB) and pre-filters to the top-K per turn. This is the textbook case Ratel was built for.

### 2.b Bloated tool descriptions

*Detection*: at least one tool description >300 tokens, or median description >120 tokens. Calculate by character count if tokenization is unavailable (≈4 chars/token).

*Severity*: Minor if isolated to a few tools; Major if it's the pattern across the catalog.

*Recommendation*: trim descriptions to one short sentence ("what it does") + a one-line "when to use." Move examples and edge-case detail into a separate spec the agent doesn't see every turn.

*Ratel angle*: matches "hybrid capability retrieval" (shipped) — Ratel's relevance score also surfaces which descriptions confuse the ranker; the dashboard shows low top-hit scores for over-described tools.

### 2.c Anemic tool descriptions

*Detection*: at least one tool with description <8 tokens, or descriptions that name the tool rather than describe it ("call this tool" / "read", "write").

*Severity*: Major — the model can't select correctly without knowing what each tool does. Cascading misroutes.

*Recommendation*: rewrite descriptions to answer "what does it do" and "when do you call it." The model is the audience, not the human reader.

*Ratel angle*: matches "LLM-driven suggestions" (roadmap, Coming Soon). Ratel will propose description rewrites once shipped; in the meantime this is a hand-edit pass.

### 2.d Duplicate / near-duplicate tools

*Detection*: two or more tools with overlapping descriptions or schemas (`read_file` + `get_file_contents` + `cat_file`). Common when multiple MCP upstreams ship similar tools.

*Severity*: Major — the model picks one inconsistently and reasoning becomes unstable across turns.

*Recommendation*: consolidate or namespace explicitly. If both must exist (different upstreams), make the descriptions sharply distinguishing ("local repo only" vs "remote workspace").

*Ratel angle*: matches "MCP server ingestion (upstream namespace prefix)" (shipped) — Ratel namespaces upstream tools automatically and ranks them, so the model only sees the relevant variant.

### 2.e Dead tools

*Detection*: tools registered but never referenced anywhere in prompts, fixtures, or the dispatch sites. If live data is available: tools with zero invocations over the sample window.

*Severity*: Minor.

*Recommendation*: delete or feature-flag off. Every registered tool consumes input tokens whether or not the agent ever calls it.

*Ratel angle*: none directly; fixed once Ratel pre-filtering ships (the tool is in the catalog but never makes the top-K).

### 2.f Loose / missing tool schemas

*Detection*: tools whose `inputSchema` is missing, `{}`, or has top-level `additionalProperties: true` with no constraints.

*Severity*: Major — the model invents inputs; runtime validation has to clean up.

*Recommendation*: tighten the schema. Required fields explicit, types narrow, enums where the value space is finite.

*Ratel angle*: none.

### 2.g Verbose tool outputs eating context

*Detection*: tools that return raw blobs (full file contents, raw HTTP bodies, full database rows) without summarization. Grep for `JSON.stringify(rows)` / `return await response.text()` / similar.

*Severity*: Major when ≥3 tools do this and they're called frequently; Minor otherwise.

*Recommendation*: summarize or paginate at the tool boundary. The tool's output is part of the agent's context; treat it accordingly.

*Ratel angle*: indirect — Ratel does not compress or rewrite tool outputs. Its leverage on context bloat is upstream: retrieval keeps irrelevant tool *definitions* out of the prompt, but a fat tool *result* is still the customer's to summarize or paginate at the boundary.

---

## 3. Context management

What it covers: prompt size, externalization, versioning, retrieval / RAG, conversation memory, summarization, compaction.

**Detection inputs**:

- System-prompt size (in tokens / characters).
- Prompts inline vs externalized to files / a prompt-management service.
- Prompt versioning (file-history-based, hash-based, or none).
- RAG pipeline presence (vector store, retriever, embedding model).
- Memory layer (summarization, key-value cache, recall heuristics).
- Conversation-history handling — full history vs windowed vs compacted.

**Common findings**:

### 3.a Monolithic system prompt

*Detection*: a single system prompt >3000 tokens that mixes role definition, tool docs, output formatting, examples, safety rules, and edge-case handling.

*Severity*: Major.

*Recommendation*: split by responsibility — role prompt is short and stable; tool docs live in the tool descriptions; output format goes in a contract section; examples go in a few-shot store the agent retrieves from on demand.

*Ratel angle*: none directly; this is a hand-edit pass.

### 3.b Inline-string prompts with no versioning

*Detection*: prompts as inline template strings in agent code, no commit hash captured, no `prompt_version` field anywhere.

*Severity*: Minor on its own; Major if there is no observability either (you can't regression-detect on a prompt you can't pin).

*Recommendation*: externalize prompts to files (or a prompt-management service). Attach `prompt_version` as span/observation metadata.

*Ratel angle*: none; this is a [`/ratel-observability-assessment`](../../ratel-observability-assessment/SKILL.md) follow-up.

### 3.c No retrieval where retrieval is obvious

*Detection*: the agent has a body of static knowledge (docs, FAQs, policies) that is dumped into the system prompt rather than retrieved.

*Severity*: Major — input tokens scale with the size of the knowledge dump.

*Recommendation*: move static knowledge into a retrieval store (vector or lexical); retrieve top-K per turn. The model only sees what's relevant.

*Ratel angle*: indirect — Ratel does hybrid retrieval over tools and skills, not over documents, but the customer's win pattern is the same (filter the context surface). Worth noting; do not over-claim.

### 3.d Full-history replay every turn

*Detection*: every model call replays the entire conversation history with no summarization or windowing.

*Severity*: Minor at short sessions; Major if sessions can grow >50 turns.

*Recommendation*: summarize older turns into a compact memory; replay only the recent N turns verbatim.

*Ratel angle*: matches "Chat compaction" and "Memory orchestration" (both roadmap). Both are roadmap-only — be honest about the timeline.

### 3.e Skill-shaped subroutines inlined as prompt blocks

*Detection*: recurring instruction blocks across prompts — "draft an email," "summarise and extract," "fetch then format" — written inline as system-prompt instructions and copy-pasted across multiple agents or call sites. Grep for repeated multi-line instruction blocks; check whether the same multi-step pattern appears as inline prose in three or more locations.

*Severity*: Minor — the agent works; the prompts duplicate.

*Recommendation*: extract the recurring blocks into named, retrievable units. In the meantime, deduplicate via shared prompt fragments.

*Ratel angle*: matches "First-class skills" (shipped). Ratel ranks skills alongside tools via `search_capabilities` and loads them on demand via `get_skill_content`, so extracted playbooks only enter context when relevant. Route the extraction to [`/ratel-decompose-prompt`](../../ratel-decompose-prompt/SKILL.md); see Dimension 11 for the fuller decomposition lens.

---

## 4. Decomposition

What it covers: whether the agent decomposes complex tasks into steps or tries to one-shot them; whether sub-tasks fan out cleanly.

**Detection inputs**:

- System prompt: does it instruct the model to plan? Are the steps named?
- Code: does any logic plan a sequence of sub-calls before invoking tools?
- For frameworks like LangGraph: is the graph structured around decomposition?

**Common findings**:

### 4.a Monolithic single-turn solution attempts

*Detection*: the agent's main loop is "tool-call → answer," with no planning phase, no fan-out, and no critic / verifier step.

*Severity*: Minor for simple agents; Major if the agent handles multi-step tasks (research, writing, code generation, data extraction across sources).

*Recommendation*: introduce an explicit planning step — even a single "plan first, then act" prompt round-trip improves outcomes measurably.

*Ratel angle*: matches "Multi-agent decomposition hints" (roadmap, Coming Soon). State the timeline honestly.

### 4.b Fan-out without fan-in

*Detection*: the agent calls multiple sub-agents in parallel (or sequentially) but has no aggregation / critic step to reconcile their outputs.

*Severity*: Major — sub-agent disagreement compounds silently.

*Recommendation*: add a verifier / aggregator agent that takes the fan-out outputs and produces a single reconciled result.

*Ratel angle*: none directly.

---

## 5. Model routing

What it covers: whether the agent picks the right model for the right sub-task (cheap model for classification, expensive model for reasoning) or runs everything through one expensive model.

**Detection inputs**:

- Number of distinct model ids called in the codebase.
- Whether sub-agents call different models or the same one.
- Whether classification / routing / formatting tasks share the same model as deep reasoning.

**Common findings**:

### 5.a Single-model agent doing everything

*Detection*: every model call uses the same provider model, including small classification / formatting steps that don't need it.

*Severity*: Minor unless cost is a stated pain point; then Major.

*Recommendation*: route by task — small / fast models for classification and routing, larger models for reasoning. The router can be deterministic (per-tool or per-role) before going LLM-as-router.

*Ratel angle*: none.

### 5.b Latest-and-greatest used as default for everything

*Detection*: every model call goes through the current frontier model even where a smaller / older model would suffice.

*Severity*: Minor — this is mostly a cost smell, not a quality smell. Flag and move on.

*Recommendation*: pick model per task. Use evals (Dimension 9) to confirm the cheaper model maintains quality on the relevant tasks before routing them away from the frontier model.

*Ratel angle*: none.

---

## 6. Error handling

What it covers: retry behavior, backoff, dead-letter, user-facing failure UX, partial-result handling.

**Detection inputs**:

- `try` / `except` / `catch` shape around tool calls and model calls.
- Retry loops — bounded vs unbounded, backoff type, jitter.
- Dead-letter / failure-state persistence.
- User-facing error messages — exposed raw or wrapped.

**Common findings**:

### 6.a Unbounded retry loops

*Detection*: `while True: try: ... except: continue` around tool / model calls, or retry without a max attempt count.

*Severity*: Critical — one transient upstream failure burns through tokens and quota.

*Recommendation*: bound retries (3 attempts typical), exponential backoff with jitter, circuit-breaker on repeated failure.

*Ratel angle*: none.

### 6.b Bare except / swallow-all error handling

*Detection*: `except: pass` or `catch (e) {}` around tool execution. Errors disappear silently.

*Severity*: Major — silent failures look like bad model output on the user side.

*Recommendation*: catch specific exceptions, log with structured context, surface a partial-result indicator to the model so it can recover.

*Ratel angle*: none.

### 6.c Raw error strings leak to user

*Detection*: model is told "here is the error: <stack trace>" or the user-facing channel receives raw exception messages.

*Severity*: Major — security (information disclosure) and UX both.

*Recommendation*: classify errors (transient / permanent / configuration) and produce user-appropriate messages. The model can still see internal detail; users should not.

*Ratel angle*: none.

---

## 7. Observability

What it covers: presence and consistency of tracing, naming, scoring, session boundaries. The most important dimension for partner engagements because everything else hinges on the ability to measure.

Where Ratel fits here: Ratel's SDKs emit the retrieval + tool funnel as native OpenTelemetry — `gen_ai.*` spans (semconv v1.42.0) plus a `ratel.*` overlay (`ratel.search`, `execute_tool <tool id>`, `ratel.skill.load`), exported as stock OTLP to whatever OTel backend the partner already runs. Ratel does not emit LLM-call (`chat <model>`) spans — those stay with the partner's own LLM instrumentation and join the same trace. So Ratel captures the retrieval/tool funnel a generic vendor setup won't (`top_k`, `hit_count`, `top_hit_score`, `took_ms`, and an `origin` of `direct` | `agent`), it complements rather than replaces a vendor, and it keeps the backend choice free via OTLP. Detection and recommendations below stay vendor-neutral.

**Detection inputs**:

- SDK presence — Ratel SDK native OTLP telemetry, Langfuse, LangSmith, OTel, OpenInference, OpenLLMetry, Helicone.
- Env vars and init sites.
- Naming consistency vs the vocabulary in [`../../ratel-observability-assessment/references/semantic-conventions.md`](../../ratel-observability-assessment/references/semantic-conventions.md).
- Session-id sourcing and propagation.
- Tool-call observation typing (`type: tool` vs untyped `event`).
- Score wiring (any `score()` calls or ingestion of eval-driven scores).
- (Live, if reachable) trace count, naming uniformity, tag coverage.

**Common findings**:

### 7.a No observability at all

*Detection*: no observability SDK in the manifest, no init site, no tracing env vars.

*Severity*: Critical for any agent in production; Major otherwise.

*Recommendation*: turn on telemetry via [`/ratel-observability-assessment`](../../ratel-observability-assessment/SKILL.md) — Ratel's native OTLP instrumentation exported to whatever OTel backend the partner runs (Langfuse / LangSmith / their own collector / Ratel Cloud, Coming Soon).

*Ratel angle*: routes to `/ratel-observability-assessment`.

### 7.b Observability wired but no session_id

*Detection*: a telemetry SDK is initialized, but no `session_id` is set on traces (grep for `session_id`, `setSessionId`, `propagate_attributes(session_id`).

*Severity*: Major — multi-turn analysis is impossible without sessions.

*Recommendation*: set `session_id` at the entry point and propagate through sub-agents.

*Ratel angle*: matches the "Sessions" section of [`../../ratel-observability-assessment/references/semantic-conventions.md`](../../ratel-observability-assessment/references/semantic-conventions.md). Route to `/ratel-observability-assessment`.

### 7.c Tool calls captured as untyped events

*Detection*: tool calls land as generic `event` observations (or as `span`) with the tool name in metadata instead of as `type: tool` observations with the tool name in `name`.

*Severity*: Major — blocks the native tool-call dashboards (Origin Split, Upstream Health, tool-level cost views).

*Recommendation*: emit tool calls as typed spans — `gen_ai.operation.name=execute_tool` with the tool id in the span name. Ratel's SDK produces these `execute_tool` spans natively; with a hand-rolled vendor setup, re-wrap the call sites to the typed shape.

*Ratel angle*: Ratel's native OTLP funnel gives these typed `execute_tool` spans for free; route to `/ratel-observability-assessment`.

### 7.d Inconsistent observation naming

*Detection*: tool observations named after the function (`handle_search`, `read_file_impl`) rather than after the tool id (`tool.search`, `tool.read_file`).

*Severity*: Minor on its own; Major if it cascades into dashboards being unreadable.

*Recommendation*: adopt the vocabulary in [`../../ratel-observability-assessment/references/semantic-conventions.md`](../../ratel-observability-assessment/references/semantic-conventions.md). One-pass rename.

*Ratel angle*: routes to `/ratel-observability-assessment`.

### 7.e Observability wired but never analyzed

*Detection*: a telemetry backend is wired and reachable (live check succeeds) and there is meaningful data, but no dashboards exist, no scores are ingested, and there is no recurring review cadence anywhere in the README / runbooks.

*Severity*: Minor — the data is there, the loop just isn't closed.

*Recommendation*: build the value dashboards and set a review cadence via `/ratel-observability-assessment`. Once Ratel's funnel spans are flowing, that skill also reads the retrieval/tool funnel from the chosen OTel backend.

*Ratel angle*: routes to `/ratel-observability-assessment`.

---

## 8. Cost discipline

What it covers: per-call cost awareness in the code — model choice per task, caching, payload size, output-token caps.

**Detection inputs**:

- `max_tokens` / `maxTokens` settings on model calls — present? sensible?
- Prompt caching (Anthropic) / context caching (OpenAI) usage.
- Streaming vs blocking — streaming-only patterns where blocking would be cheaper / vice versa.
- Output size discipline — instructions to be concise, schemas that constrain output shape.

**Common findings**:

### 8.a No max_tokens cap

*Detection*: `generateText` / `chat.completions.create` calls without `maxTokens` / `max_tokens`.

*Severity*: Minor for assistants; Major for tools embedded in higher-throughput surfaces (a 16K-token answer to a yes/no question is a real cost smell).

*Recommendation*: cap per call. Different caps per role.

*Ratel angle*: none.

### 8.b No prompt caching

*Detection*: prompts have a large stable prefix (multi-thousand-token system prompt or tool catalog) but no caching is configured.

*Severity*: Major for high-frequency agents.

*Recommendation*: enable provider-side caching on the stable prefix. The win is proportional to traffic.

*Ratel angle*: indirect — Ratel pre-filter shrinks the catalog the prompt prefix would otherwise carry; combine both for compounded savings.

### 8.c Verbose model output by instruction

*Detection*: system prompt instructs verbose output ("explain your reasoning in detail") for tasks that don't need it (a classification call, a routing call).

*Severity*: Minor.

*Recommendation*: terse outputs for non-reasoning roles. Keep verbose chain-of-thought to the roles that benefit.

*Ratel angle*: none.

---

## 9. Eval / quality gates

What it covers: presence of an eval suite, ground truth, CI gates, regression detection.

**Detection inputs**:

- `evals/`, `tests/eval/`, `tests/agents/`, `prompts/test/` directories.
- Eval framework imports — `promptfoo`, `langfuse.score`, `langsmith.evaluate`, `inspect_ai`, internal eval modules.
- CI workflow files invoking evals on PRs.
- Ground-truth artifacts — labeled fixtures, gold sets.

**Common findings**:

### 9.a No eval suite

*Detection*: zero `evals/` directory, zero eval framework imports, zero CI invocations of anything eval-shaped.

*Severity*: Critical for any agent shipping to production; Major otherwise.

*Recommendation*: stand up a minimal eval set — even 20 hand-labeled examples per critical task is enough to catch regressions. Hook to CI; gate merges.

*Ratel angle*: none — but having ground truth unlocks Ratel's retrieval-quality scoring (`top_k_recall_at_5`, `tool_selection_accuracy`) which is otherwise unobservable.

### 9.b Eval set exists but no CI gate

*Detection*: `evals/` directory has fixtures and a runner, but no CI workflow invokes it.

*Severity*: Major.

*Recommendation*: wire to CI. Block merge on regression beyond a tolerance.

*Ratel angle*: none.

### 9.c No ground truth for tool selection

*Detection*: eval fixtures exist but none label the *correct tool id* for each task.

*Severity*: Minor on its own; Major in combination with tool sprawl.

*Recommendation*: label `ground_truth_tool_id` per fixture per the metadata vocabulary in [`../../ratel-observability-assessment/references/semantic-conventions.md`](../../ratel-observability-assessment/references/semantic-conventions.md). Enables retrieval-quality scoring.

*Ratel angle*: matches the Retrieval Quality dashboard's `recall@5` widget — unlocks once ground truth exists.

---

## 10. Safety

What it covers: prompt-injection guards, tool input validation, secret handling, output sanitization.

**Detection inputs**:

- Tool inputs that originate from user content without validation.
- Tools that read filesystems, shell out, write to databases, send messages, call external APIs — and what guards exist around them.
- Secret handling — env vars, secret managers, leak surfaces.
- Output sanitization where the agent's output flows to a downstream sink (a webhook, a database, an LLM-as-judge).

**Common findings**:

### 10.a Tools that can shell out / write to disk without validation

*Detection*: tools whose execution path includes `exec`, `subprocess`, `child_process`, `fs.writeFile`, `os.system` — and whose inputs are not validated against an allow-list.

*Severity*: Critical when reachable from untrusted input.

*Recommendation*: allow-list inputs, sandbox execution (e.g., Vercel Sandbox or equivalent), forbid the tool from running on untrusted-input paths.

*Ratel angle*: none.

### 10.b Prompt injection: untrusted content concatenated into prompts

*Detection*: user input (or content fetched from URLs / RSS / email / scraped pages) flows into system or user prompts without delimiter discipline.

*Severity*: Major.

*Recommendation*: delimit untrusted content (XML tags, structured fields), instruct the model to treat the content as data not instructions, and run an output classifier before acting on it.

*Ratel angle*: none.

### 10.c Secrets in env files committed to the repo

*Detection*: `.env` (not `.env.example`) committed, or secrets visible in the repo's git history.

*Severity*: Critical.

*Recommendation*: rotate the leaked secrets, add `.env` to `.gitignore`, move to a secret manager. This finding is non-negotiable; promote to the top of the report regardless of other findings.

*Ratel angle*: none.

---

## 11. Prompt decomposition

What it covers: whether a long, monolithic system prompt could be broken into a lean core prompt plus retrievable skills — playbooks that only enter context when relevant. This is the *extraction* lens on prompt size; Dimension 3 (Context management) covers prompt hygiene and externalization at large, while this dimension asks specifically "what should leave the always-on prompt and become an on-demand skill?"

**Detection inputs**:

- System-prompt token size (in tokens / characters; ≈4 chars/token).
- Whether the prompt mixes concerns: role definition + tool docs + output format + few-shot examples + recurring multi-step procedures + safety rules in one block.
- Whether recurring instruction blocks are duplicated across prompts or call sites (grep for repeated multi-line instruction blocks; count the call sites).
- Whether the codebase already uses any skills / playbook / retrievable-instruction mechanism, or carries everything inline every turn.

**Common findings**:

### 11.a Monolithic system prompt mixing many responsibilities

*Detection*: a single system prompt that mixes three or more of {role, tool docs, output format, examples, recurring multi-step procedures, safety} in one block.

*Severity*: Minor by default; Major if it is >3000 tokens of mixed concerns.

*Recommendation*: keep a lean core prompt (role + contract + safety) and extract the rest into retrievable skills the agent loads on demand. Output format stays in a short contract section; examples and recurring procedures become named, retrievable units.

*Ratel angle*: matches "First-class skills" (shipped). Ratel ranks skills alongside tools via `search_capabilities` and loads them on demand via `get_skill_content`, so extracted playbooks only enter context when relevant. Route to [`/ratel-decompose-prompt`](../../ratel-decompose-prompt/SKILL.md).

### 11.b Recurring multi-step procedures inlined as prompt prose

*Detection*: the same multi-step procedure ("draft an email," "fetch then format," "summarise and extract," a triage runbook) appears as inline prompt prose across N call sites or agents instead of as a single retrievable skill.

*Severity*: Minor when it appears in two call sites; Major when it appears in three or more, or when the duplicated block is large enough to dominate the prompt.

*Recommendation*: extract each recurring procedure into one named, retrievable skill; replace the inline prose with a short reference. Deduplicate via shared fragments in the interim.

*Ratel angle*: matches "First-class skills" (shipped). Ratel makes the extracted procedure a first-class retrievable unit alongside tools, surfaced only when the turn calls for it. Route to [`/ratel-decompose-prompt`](../../ratel-decompose-prompt/SKILL.md).

---

## 12. Definition quality

What it covers: the *quality* of tool **and** skill definitions as an optimizable retrieval surface. Dimension 2 (Tool surface) stays at the inventory level — count, sprawl, dead tools, duplication. This dimension is the optimization lens: given that these tools and skills exist, are their definitions written well for hybrid (lexical + semantic) retrieval and model selection? Description-quality findings live primarily here; cross-reference Dimension 2 for the inventory-level cousins (2.b bloat, 2.c anemia, 2.d duplication, 2.f schemas) rather than double-counting them.

**Detection inputs**:

- Description length distribution across tools and skills (median, outliers).
- Presence of both "what it does" and "when to use" in each description.
- Parameter name descriptiveness (`q` / `arg1` / `data` vs `query` / `file_path` / `max_results`).
- Enum presence where the value space is finite (a `status` string with no enum, a `mode` free-text field).
- Schema tightness — `additionalProperties: true`, `{}`, or otherwise unconstrained.
- Near-duplicate descriptions across definitions (overlapping token bags).

**Common findings**:

### 12.a Descriptions missing "when to use"

*Detection*: descriptions state what the tool/skill does but never say when to reach for it, or name the definition rather than describe it. Cross-reference 2.c (anemic descriptions) at the inventory level.

*Severity*: Major — the model cannot select correctly without a usage signal, and the lexical retrieval arm has fewer terms to match against while the semantic arm has less meaning to embed.

*Recommendation*: rewrite each description as one short "what it does" sentence plus a one-line "when to use." The model is the audience, not the human reader.

*Ratel angle*: Ratel's retrieval indexes names + descriptions + parameter names + enum values into its lexical (BM25) arm and embeds the same text for its semantic arm (hybrid fuses both via RRF), so a clear "when to use" clause drives recall on both. LLM-driven definition suggestions are roadmap (Coming Soon); for now this is a hand-edit pass. Route to [`/ratel-tune-definitions`](../../ratel-tune-definitions/SKILL.md).

### 12.b Non-descriptive parameter names

*Detection*: parameters named `q`, `arg1`, `input`, `data`, `payload` where a descriptive name would carry meaning.

*Severity*: Minor on its own; Major when it spans the catalog, because parameter names are part of the retrieval index.

*Recommendation*: rename parameters to describe their content (`query`, `file_path`, `max_results`). The cost is one rename pass; the benefit is both clearer model selection and stronger retrieval matches.

*Ratel angle*: Ratel's retrieval indexes parameter names directly into its lexical arm (and embeds them for the semantic arm), so descriptive names lift retrieval scores. Route to [`/ratel-tune-definitions`](../../ratel-tune-definitions/SKILL.md).

### 12.c Missing enums where the value space is finite

*Detection*: a parameter whose value space is finite (status, mode, sort order, region) typed as a free-text string with no `enum`.

*Severity*: Minor — the model guesses values; runtime validation cleans up.

*Recommendation*: add `enum` listing the legal values. This tightens model selection and adds the values to the retrieval index.

*Ratel angle*: Ratel's retrieval indexes enum values (in both the lexical and semantic arms), so declaring them improves both selection and retrieval. Route to [`/ratel-tune-definitions`](../../ratel-tune-definitions/SKILL.md).

### 12.d Near-duplicate descriptions across definitions

*Detection*: two or more definitions whose descriptions overlap heavily by token bag, blurring the ranker's ability to distinguish them. The inventory-level cousin is 2.d (duplicate tools); this entry is about the *wording*, even where the definitions are legitimately distinct.

*Severity*: Major — the ranker cannot separate them, and the model picks inconsistently.

*Recommendation*: rewrite the descriptions to be sharply distinguishing on the dimension that actually differs ("local repo only" vs "remote workspace"), even if the tools themselves stay.

*Ratel angle*: Ratel's retrieval ranks on name + description + parameter names + enum values across both the lexical and semantic arms; sharply distinct wording is what lets the ranker separate near-duplicates. Route to [`/ratel-tune-definitions`](../../ratel-tune-definitions/SKILL.md).

---

## How to combine findings into a dimension score

Score each dimension once, using the **worst severity** in its findings:

- Any Critical finding → **Missing**.
- Worst is Major → **Weak**.
- Worst is Minor → **Adequate** (or **Strong** if no findings beyond Info).
- No findings → **Strong**.

If the dimension has *no signal at all in the codebase* (e.g., no observability surface anywhere, no eval directory at all), score it **Missing** and write a single Critical-or-Major finding explaining the absence. Don't score **Strong** by accident on a dimension you couldn't even evaluate.

### Numeric score (0–10)

Assign the ordinal label first — it stays the source of truth — then give the dimension a **0–10 score that sits inside that label's band**, so the number and the label can never disagree. The score exists so the HTML report can draw the gauge, radar, and per-dimension bars; it is a presentation layer over the label, not a re-scoring.

| Label | Band | How to place within the band |
| --- | --- | --- |
| **Strong** | 8.5–10.0 | Base 9.0. Use 10.0 only when the dimension has zero findings of any kind. |
| **Adequate** | 6.5–8.4 | Base 8.0; subtract ≈0.5 per Minor finding beyond the first (floor 6.5). A dimension with no findings that you simply could not evaluate deeply lands here, around 7.5. |
| **Weak** | 3.5–6.4 | Base 6.0; subtract ≈0.7 per Major beyond the first and ≈0.2 per accompanying Minor (floor 3.5). |
| **Missing** | 0.0–3.4 | Base 3.0; subtract ≈1.0 per Critical beyond the first (floor 0.0). Use ≈1.0–1.5 when the dimension's surface is entirely absent. |

Round to one decimal and clamp into the band. The render script derives each bar/chip color from the score, so a score that strays outside its label's band would mis-color the report — keep them aligned.

**Overall composite** = the mean of the twelve dimension scores, rounded to one decimal. Keep it a simple unweighted mean (Observability is the most consequential dimension, but weighting invites "why is it weighted" questions on a partner-facing artifact; leave it flat unless a future engagement asks otherwise).

## Catalog maintenance

When Ratel ships a new feature, the corresponding row goes in [`../../ratel-observability-assessment/references/ratel-value-map.md`](../../ratel-observability-assessment/references/ratel-value-map.md) first. Only then does this catalog get an updated Ratel-angle line. Two reasons: (1) the value map is the source of truth, (2) a Ratel angle in the assessment that doesn't yet have a dashboard widget produces an unfinishable engagement.

If you spot a new assessment dimension worth adding (something genuinely orthogonal to the existing twelve), open a PR — but bias toward adding a new finding under an existing dimension first.

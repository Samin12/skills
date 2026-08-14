# Semantic conventions: OTel spans, attributes, and tags

This is the **canonical OTel vocabulary** the whole observability funnel shares. Ratel emits its retrieval + tool funnel natively as `gen_ai.*` spans (semconv **v1.42.0**) plus a `ratel.*` overlay; the naming rules below cover the agent-level spans **you** add alongside that funnel — the session boundary, agent-step, tool-call, and model-call spans Ratel does not emit — so the whole trace reads consistently in whichever OTel backend you export to. `/ratel-observability-assessment` proposes this vocabulary and the dashboards group on it directly.

Because these are OTel span names and attributes, they carry across every backend unchanged — Langfuse, LangSmith, your own collector, Ratel Cloud (Coming Soon). Do not re-invent. If a customer pushes back on a name, the answer is "change it everywhere — the dashboards group on it too" — not "fine, we'll call it something else in this one place."

The three structural concepts come from `instrumentation-philosophy.md`:

- **Unit of work** — one externally meaningful thing the system did (one chat turn, one job, one webhook).
- **Step** — one thing the agent did inside that unit (a sub-agent run, a tool call, a model call, a retrieval).
- **Session** — a thread of related units of work sharing a session/thread id.

## Unit-of-work naming

One unit of work = one externally meaningful thing. Name it after the **use case**, not the function that runs it.

| Use case | Unit-of-work name |
| --- | --- |
| One chat turn (sync HTTP) | `chat-turn` |
| One chat turn (streamed) | `chat-turn` (same — streaming is an implementation detail) |
| Async job (background research, summarisation) | `job.<job-kind>` (e.g. `job.summarise-thread`) |
| Scheduled run | `cron.<job-kind>` |
| Tool-call test from a UI | `tooling.manual-invoke` |
| Eval harness run | `eval.<dataset-name>` |

Avoid: `POST_/api/chat`, `handler-fn`, `run`, `process`. They tell you nothing at the dashboard level.

## Step naming

One step = one thing the agent did inside a unit of work, recorded as a child OTel span. Three kinds, three naming rules.

### Agent-step (an agent role doing work)

```
supervisor
research-agent
writer-agent
critic-agent
```

Lowercase, kebab-case, role-as-noun. If the same agent role can run multiple times in a unit of work (e.g. a critic loop), suffix with iteration: `critic-agent#1`, `critic-agent#2`.

### Tool-call (a tool being invoked)

```
tool.<tool-id>
```

Where `<tool-id>` is the **stable id** the agent framework uses, not the friendly label. For MCP tools, include the upstream namespace: `tool.upstream__filesystem__read_file`.

When Ratel is present, you do **not** name its funnel spans — Ratel emits them natively. They arrive on the same trace with these span names (do not re-create them):

```
ratel.search                  # capability + skill retrieval (skills bucket rides the same span)
execute_tool <tool id>        # standard gen_ai.operation.name=execute_tool, NOT a bespoke ratel.invoke
ratel.skill.load              # a skill is read (not executed — there is no invoke_skill)
ratel.upstream.register       # an upstream MCP server is ingested
ratel.auth.flow               # OAuth 2.1 / PKCE flow events
```

Every Ratel span carries the `origin` attribute (`direct` | `agent`). See [`native-telemetry-setup.md`](native-telemetry-setup.md) for the full attribute list per span.

### Model-call (an LLM generation)

Ratel does **not** emit LLM-call spans — those come from your own LLM instrumentation as OTel `gen_ai` `chat <model>` spans and join the same trace next to Ratel's funnel. Whatever emits them, keep the family in the span name:

```
chat <model-shortname>
```

Examples: `chat sonnet-4-6`, `chat gpt-4o`, `chat haiku-4-5`. The full provider model id (e.g. `claude-sonnet-4-6-20260101`) belongs in the `gen_ai.request.model` / `model_id` attribute, not the span name. Naming the span by model family makes "cost by model" pivots trivial; naming it by exact id fragments your dashboards every time a snapshot date rolls.

## Sessions

`session_id` lives on the unit of work. Source it from the most stable identifier the system already has:

| System has | Use as `session_id` |
| --- | --- |
| Authenticated user with a chat thread | `<thread_id>` (one thread = one session, regardless of how long it lasts) |
| Anonymous chat | the browser session cookie / anonymous id |
| Background job with a correlation id | the correlation id |
| Multi-step agentic run with a run id | the run id |
| Nothing stable available | generate at the entry point, attach to the unit of work AND store wherever you'd normally keep request state |

Critical: set `session_id` *as early as possible* and carry it down to every step inside the unit of work. Setting it only on the top-level unit and not propagating it to the steps means child steps don't carry it, which breaks session-level analysis. Use OTel context propagation so the span attribute flows to every child span, including Ratel's funnel spans on the same trace.

## User id

`user_id` lives on the unit of work and is carried down to steps the same way as `session_id`. Source it from the authenticated user where available. **Do not put PII (email, name) in `user_id`** — use a stable opaque id. If the system is anonymous, leave `user_id` empty rather than faking one.

## Tags

Tags are coarse, low-cardinality, filterable. Use them for things you'll want to *split a dashboard by*, not things you'll want to *read on a specific unit of work*.

Standard tag set:

| Tag | Values | Why |
| --- | --- | --- |
| `env` | `dev`, `staging`, `prod` | Single most-used dashboard filter |
| `stack` | `vercel-ai-sdk`, `mastra`, `langchain`, `langgraph`, `crewai`, `llamaindex`, `raw` | Lets you compare instrumentation surfaces |
| `agent_version` | `v<N>` or git short sha | Detect regressions across deploys |
| `feature_flag` | flag name + arm (e.g. `tool_pool=ratel`, `tool_pool=full`) | A/B comparison surface |

Cap tag count at ~6 per unit of work. More than that and the dashboard filter UI becomes useless. Do not put high-cardinality data in tags (no user ids, no session ids, no error messages). In OTel these are low-cardinality span attributes; a backend that surfaces a first-class "tag" UI (e.g. Langfuse) maps them onto tags — the set above stays the same.

## Span attributes

Span attributes are fine-grained and can be high-cardinality. Use them for everything you'd want to *show on a specific unit-of-work detail view* or *aggregate in a dashboard*.

Required keys (set on every relevant step):

| Key | Where | Value |
| --- | --- | --- |
| `agent_role` | on every agent-step | the role name (`supervisor`, `research-agent`, ...) |
| `tool_id` | on every tool-call | the stable tool id |
| `model_id` | on every model-call | the full provider model id |
| `prompt_version` | on every model-call | the version/hash of the prompt template used |

Conditional keys (set when the matching feature is in play):

| Key | When | Value |
| --- | --- | --- |
| `user_tier` | multi-tier product | `free` / `pro` / `enterprise` |
| `origin` | Ratel present | `direct` (Ratel SDK call) vs `agent` (capability tool-call); Ratel sets this natively on its spans |
| `top_k`, `hit_count`, `top_hit_score`, `took_ms`, `replace_mode` | Ratel retrieval span | Ratel sets these natively on `ratel.search` — see [`native-telemetry-setup.md`](native-telemetry-setup.md) |
| `prompt_arm` | running a prompt A/B | arm id |
| `ground_truth_tool_id` | eval units with labels | the canonical correct tool id (for accuracy scoring) |

## Don'ts

- **Don't put dynamic content in step names.** `tool.read_file(/etc/passwd)` is a name no dashboard can group on. The name is `tool.read_file`; the argument goes in the step's input.
- **Don't reuse names across step kinds.** If `supervisor` is an agent-step, never use it as a tool name. Dashboards filter by kind + name; reusing names produces silent overlap.
- **Don't tag with anything that can be a user input.** Tags are not search; they're pivots.
- **Don't skip `session_id` on steps.** Set it on the unit of work and carry it down to every step — never inherit-by-magic. Most backends will not back-fill if you forget.

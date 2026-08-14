# Instrumentation philosophy: trace the mental model, not the call graph

This is the load-bearing idea behind every observability proposal. It holds regardless of which OTel backend you export to — Langfuse, LangSmith, your own collector, or Ratel Cloud (Coming Soon). Everything is OTel spans; the thinking is the same everywhere.

## The core rule

A common failure mode is "wrap every function in a span." That produces a trace that matches the code's call graph but tells you nothing about what the agent was *trying to do*. Observability data is most useful when its structure matches the **conceptual** structure of a turn, not the source-file layout.

Three backend-agnostic concepts carry the whole model:

- **Unit of work** — one externally meaningful thing the system did: one chat turn, one job, one webhook, one scheduled run. Not "one HTTP request" if a request contains multiple agent turns; not "one model call" if a turn contains many. This is the top-level OTel root span.
- **Step** — one thing the agent did inside that unit of work: a sub-agent invocation, a tool call, a model call, a retrieval. Steps nest to reflect **delegation**, not source-file layout — each is a child OTel span.
- **Session** — a thread of related units of work that share a session/thread id: usually a user conversation, an agent run-id, or a job correlation id. This is what makes multi-turn analysis possible.

When Ratel is present, its retrieval + tool funnel (`ratel.search`, `execute_tool`, `ratel.skill.load`, `ratel.upstream.register`, `ratel.auth.flow`) is emitted natively as child spans on this same trace — you don't instrument it, it just appears. The **model-call spans are your own instrumentation**, though: Ratel does not emit `chat <model>` (LLM-generation) spans, so those come from your LLM library's OTel `gen_ai` instrumentation and sit next to Ratel's funnel spans under the same unit of work.

If you can describe a turn to a colleague in three sentences, those sentences are roughly the units of work, steps, and session you should be recording. The trace should read like that description, not like a stack trace.

## The two anti-patterns to call out

When you read the codebase, flag these two specifically in the proposal whenever you see them. They are the highest-leverage fixes and they recur in almost every first engagement.

### 1. No session boundary at all

Every turn is recorded as a fresh, unconnected unit of work with no session id. Multi-turn analysis — session length, abandoned-session rate, cost per conversation, "what did the user do before this failed" — becomes impossible because nothing ties the turns together.

The fix is almost always a single line at the agent entry point: source a stable session id (see `semantic-conventions.md` for the sourcing table) and attach it as early as possible so every step inside the unit of work carries it. Setting it only on the top-level unit and not carrying it down to the steps is the same bug in slower motion — child steps lose the thread.

### 2. Tool calls captured as untyped events

Every tool call lands as a generic, untyped event with the tool name buried in metadata, rather than as a **typed tool step** with the tool id in its name. This blocks the entire native tool-call analysis surface: "calls per tool", "error rate per tool", "p95 latency per tool", "dead-weight tools called once or never" all depend on tool calls being first-class, typed steps the backend can group on.

The fix is to wrap the tool-call site so each call surfaces as a typed tool step named after the stable tool id (see `semantic-conventions.md` for naming). Emit it as an OTel `gen_ai` `execute_tool` span — the same shape Ratel uses for its own funnel — not an untyped event. (Ratel's `execute_tool` spans already arrive typed; this fix is for the tool calls Ratel does not mediate.)

## How to apply this in a proposal

State *what* to capture and *why* — units of work, steps, sessions, typed tool/model spans. For the concrete wiring (turning on Ratel's native telemetry, then adding your own agent-level spans), point at [`native-telemetry-setup.md`](native-telemetry-setup.md). The proposal's job is to get the mental model right; the setup reference carries the exact SDK calls.

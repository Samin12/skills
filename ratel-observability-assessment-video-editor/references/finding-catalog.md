# Finding catalog

The canonical catalog of patterns to look for, the heuristic that detects each one, and the recommended fix. The failure modes are the same whether the traces live in Langfuse, LangSmith, your own collector, or Ratel Cloud (Coming Soon), so read this catalog whenever you review agent traces in your OTel backend. It uses the OTel span/attribute vocabulary from `semantic-conventions.md` (unit of work, step, session); translate a detection into your backend's query syntax as you go. Update this file when new patterns emerge from engagements — it's the only place these live.

Each entry has:
- **Pattern** — short name.
- **Category** — `ratel` (we fix this by integrating Ratel) or `generic` (anyone could fix it).
- **Detection** — the specific query / aggregate that triggers it.
- **Recommended action** — what to put in the finding.
- **Solved by** (Ratel patterns only) — whether Ratel ships the fix today (`shipped`) or on the roadmap (`Coming Soon`).

Don't emit a finding that isn't in the catalog without adding it here first. If a one-off finding emerges during analysis, write the template down before shipping.

---

## Data quality patterns (generic)

These break dashboards and analytics. Always fix first.

### Missing session_id

- **Detection**: any non-trivial fraction of units of work (>5%) has empty `session_id`.
- **Action**: identify the agent entry point that's not setting session_id; cite the spot from the instrumentation plan. Multi-turn analysis is impossible until this is fixed.
- **Severity**: high if >25% of units affected; medium otherwise.

### Missing user_id when product is authenticated

- **Detection**: product has logged-in users, but `user_id` is empty on >5% of units of work.
- **Action**: trace upstream from the entry point to find where the user context drops. Usually a missing prop in a fan-out.
- **Severity**: medium.

### Inconsistent unit-of-work naming

- **Detection**: more than ~5 distinct unit-of-work names in the same `env`, and at least one looks like a function name (`handleChat`, `POST /api/chat`) or a UUID.
- **Action**: enforce one name per externally meaningful unit per [`semantic-conventions.md`](semantic-conventions.md).
- **Severity**: medium (annoys dashboards but doesn't break them).

### Tool calls landing as untyped events

- **Detection**: top tools in the catalog do not appear when filtering steps by tool-call kind.
- **Action**: wrap the tool-call site to emit a typed tool-call step named `tool.<tool-id>`. Cite the stack reference.
- **Severity**: high (every Ratel-value dashboard + every tool-health dashboard depends on this).

### Truncated or missing input/output

- **Detection**: >20% of steps have empty input OR empty output.
- **Action**: instrumentation is collecting structure but not content. Find the recording call and pass the input/output explicitly; don't rely on auto-capture for hand-rolled steps.
- **Severity**: medium.

---

## Cost & token patterns

### Token-heavy turns with huge tool catalogs (RATEL)

- **Category**: ratel
- **Detection**: `chat-turn` units of work where input_tokens > some threshold (5000 is a useful default) AND the tool list in the system prompt or first user message is large (visible in the input field or estimable from the count of tool-definition load steps).
- **Action**: introduce Ratel as a pre-filter (`replace_mode = true`). Recommend a pilot on the top unit-of-work name only first. Cite expected savings from the benchmark in the Ratel README (~50–85% input token reduction at pool ≥ 180 tools).
- **Solved by**: shipped.
- **Severity**: high if it affects >25% of cost; medium otherwise.

### Tool-payload bloat (RATEL)

- **Category**: ratel
- **Detection**: tool-call steps where output > 10kb AND the tool is called many times per session.
- **Action**: Ratel does not rewrite tool outputs — summarize or paginate the payload at the tool boundary before it enters context. Ratel's leverage here is upstream: retrieval keeps irrelevant tool *definitions* out of the prompt, so the pilot pairs a pre-filter with output pruning on the offending tools.
- **Solved by**: customer-side output pruning; Ratel reduces the definition surface (shipped).
- **Severity**: medium.

### System-prompt / context bloat (generic)

- **Category**: generic
- **Detection**: `chat-turn` model-calls where input_tokens is high (>5000) BUT the tool catalog is small (≤ ~30 tools) or tool schemas aren't even in the recorded input — i.e. the bloat is a large fixed system prompt and/or accumulating conversation history re-sent every turn, NOT a large tool list. Tell-tale: input is large and roughly constant across turns even when the user message is tiny; output is small (mostly tool-call decisions). This is the honest alternative to the RATEL huge-catalog pattern — do not dress it up as a tool-search opportunity when the catalog is small.
- **Action**: (1) Enable provider prompt caching on the static system-prompt prefix — for a ~10–22k-token input that is ~90% identical across turns, this is the single biggest cost lever and needs no app rewrite. (2) Trim the system prompt: move long playbooks/prose into tools or retrieved docs the agent pulls on demand. (3) Summarise or window conversation history instead of replaying it verbatim. Cite the per-turn input-token p50/p95 and the input:output ratio.
- **Severity**: high if it drives >25% of cost; medium otherwise.

### Generic cost spike

- **Category**: generic
- **Detection**: daily total cost has a >50% jump in the last 24h vs the previous 7-day avg.
- **Action**: split cost by model and by unit-of-work name to localise. Cite the trace ids of the top 5 spend contributors.
- **Severity**: high.

### Wrong-tier model for a task

- **Category**: generic
- **Detection**: top-cost unit-of-work names use a frontier model (Opus / GPT-5 / etc.) where a smaller model would do (heuristic: input length is short, output length is short, and the task per the prompt is structurally simple).
- **Action**: A/B the same unit of work on a smaller model. Suggest specific candidate (Haiku / mini variant).
- **Severity**: medium.

---

## Retrieval & tool-selection patterns

### Low recall@K (RATEL)

- **Category**: ratel
- **Detection**: `score_value` average for `score_name = top_k_recall_at_5` is below 0.7 over the window.
- **Action**: review tool descriptions for the tools that aren't being recalled, and try semantic or hybrid retrieval — it closes recall gaps a lexical-only index misses. Ratel Cloud's suggestions engine (Coming Soon) will automate the rewrites; today, rewrite descriptions manually.
- **Solved by**: shipped (manual fix + semantic/hybrid retrieval); Coming Soon (automated suggestions).
- **Severity**: medium (high if recall is below 0.5).

### Misrouted tool calls (RATEL)

- **Category**: ratel
- **Detection**: agent calls one tool, immediately followed by an error or a different tool call on the same input — pattern of "wrong tool first try" in the trace bodies.
- **Action**: surface the misrouting examples. Recommend ground-truth labelling + a `tool_selection_accuracy` score, then a Ratel pre-filter pilot.
- **Solved by**: shipped (today), reinforced by Ratel Cloud suggestions (Coming Soon).
- **Severity**: medium.

### Tools called once or never

- **Category**: generic
- **Detection**: 30%+ of registered tools have zero invocations over the window.
- **Action**: tools either need better descriptions (most likely) or they should be removed. List the dead tools.
- **Severity**: low (high if the dead tools constitute most of the catalog).

### Retry storms

- **Category**: generic
- **Detection**: units of work with >5 invocations of the same `tool_id` within 10 seconds.
- **Action**: cite trace ids. Usually a missing retry budget or a tool returning a recoverable error that the agent doesn't handle. Recommend a tool-level retry budget.
- **Severity**: high if >5% of units affected.

---

## Multi-agent / handoff patterns

### Flat sub-agent structure (generic)

- **Category**: generic
- **Detection**: units of work with multiple `agent_role` metadata values but no parent-child nesting (siblings only).
- **Action**: parent context isn't carried across the handoff. Cite the stack reference for context propagation across the boundary.
- **Severity**: medium.

### Runaway sub-agent loop

- **Category**: generic
- **Detection**: same sub-agent role appears >10 times in a single unit of work.
- **Action**: probable infinite-loop / max-step misconfiguration. Cite trace ids.
- **Severity**: high.

### Decomposition opportunity (RATEL, coming soon)

- **Category**: ratel (coming soon)
- **Detection**: single-agent units of work with very large tool catalogs (>50 tools) AND clear clustering of tool calls into groups across sessions.
- **Action**: pointer to multi-agent decomposition hints (Coming Soon). Today: manually identify the cluster and propose a supervisor / sub-agent split, or run `/ratel-decompose-prompt`.
- **Solved by**: Coming Soon.
- **Severity**: medium.

---

## Session & quality patterns

### Abandoned-session spike

- **Category**: generic
- **Detection**: % of single-turn sessions with no follow-up trended up 25%+ over the window.
- **Action**: read the first/last messages of a sample. Usually a regression in the first response.
- **Severity**: high.

### Score regression by agent_version

- **Category**: generic
- **Detection**: avg score for `tag.agent_version = <latest>` is materially below the previous version's avg.
- **Action**: cite both versions and the score name. Recommend a rollback or hotfix.
- **Severity**: high.

### No evaluation scores emitted (generic)

- **Detection**: a scores query returns zero rows over the window despite traffic existing. No online or annotation scores wired.
- **Action**: wire at least one cheap online score (e.g. an LLM-judge on task completion, or a deterministic check) so quality regressions are visible. Without it, the recall/accuracy/score-regression patterns in this catalog cannot be evaluated at all — every quality finding is blind. Most OTel backends have a scores/evals surface; wire the score there.
- **Severity**: medium (gates all quality analysis, but not load-bearing for cost/latency dashboards).

### Prompt drift

- **Category**: generic
- **Detection**: multiple `metadata.prompt_version` values active in the same `agent_version`.
- **Action**: prompt versioning isn't enforced. Recommend pinning per-deploy.
- **Severity**: low.

---

## Model & infra patterns

### Latency outlier from a single model

- **Category**: generic
- **Detection**: one `model_id` has p95 latency >3x the median across models.
- **Action**: investigate provider-side; recommend a fallback / circuit breaker. Cite trace ids.
- **Severity**: medium.

### Generation usage missing

- **Category**: generic
- **Detection**: >10% of model-calls have empty token usage.
- **Action**: provider integration isn't capturing usage. Most commonly: wrong import (e.g. `from openai import OpenAI` instead of the instrumented wrapper that emits `gen_ai` usage attributes).
- **Severity**: medium (blocks cost dashboards).

### Model swap mid-unit-of-work

- **Category**: generic
- **Detection**: a single unit of work contains model-calls with multiple distinct `model_id` values.
- **Action**: usually a fallback / cascade firing. Worth surfacing — high model swap rates indicate frontier-model rate limiting or a bug.
- **Severity**: low.

---

## Suggestion / adoption patterns (RATEL, coming soon)

### Low suggestion adoption (RATEL)

- **Category**: ratel (coming soon)
- **Detection**: when Ratel Cloud's suggestions engine is live and suggestions are being generated, `score_name = suggestion_adopted` avg is below 0.3.
- **Action**: investigate why suggestions are being declined — surface a sample, recommend tuning the suggestion model or the prompt.
- **Solved by**: Ratel Cloud suggestions tuning loop (Coming Soon).
- **Severity**: low.

### Accuracy delta after suggestion (RATEL)

- **Category**: ratel (coming soon)
- **Detection**: after suggestions adopted, `tool_selection_accuracy` should rise. If flat or down, the suggestion engine is misfiring.
- **Action**: roll back the suggested catalog, file a Ratel issue with the trace ids.
- **Solved by**: Ratel Cloud suggestions engine (Coming Soon).
- **Severity**: medium.

---

## Ratel-capability mapping

Every Ratel-category finding above cites a "Solved by" status. Those map to the capabilities catalogued in [`ratel-value-map.md`](ratel-value-map.md) — the single source of truth for what Ratel ships. When a finding's fix maps to a Coming-Soon feature, pull its status from that file so this catalog stays current as Ratel ships.

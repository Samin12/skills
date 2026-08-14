# General agent-health dashboard catalog

Stack-agnostic dashboards. Useful for any instrumented agent, regardless of which OTel backend you export to or whether Ratel is in the picture — build these as widgets in your backend's UI, grouping on the OTel span names and attributes from [`semantic-conventions.md`](semantic-conventions.md). Pick the subset that matches what the customer's instrumentation actually emits.

## 1. Latency & Cost Overview

The default front page. What every PM and SRE wants to glance at.

Widgets:

1. **p50 / p95 / p99 trace latency over time** — line, three lines, filter `trace_name = chat-turn`.
2. **Daily request volume** — bar, count, `dim: day`, filter `trace_name = chat-turn`.
3. **Cost per day** — line, sum of `total_cost`, `dim: day`.
4. **Cost per trace (avg)** — single-stat, avg of `total_cost`, filter last 7 days.
5. **Latency breakdown by trace name** — stacked-bar, p95, `dim: trace_name, day`.

Drill-down: clicking any spike opens the traces panel filtered to the same time window and trace name.

## 2. Error Surface

Where things break, in priority order.

Widgets:

1. **Daily errors, split by trace name** — stacked-bar, count, `dim: day, trace_name`, filter `status = error`.
2. **Top failing observations** — table, count, `dim: observation_name`, filter `status = error`. Top 20.
3. **Error rate per tool** — bar, ratio, `dim: metadata.tool_id`, filter `observation_type = tool`.
4. **Errors by user** — table, count, `dim: user_id`, filter last 7 days, `status = error`. Top 20.

Drill-down: clicking a failing tool opens a saved view filtered to errored observations of that tool.

## 3. Tool Usage

What tools are used, what aren't, where time is spent.

Widgets:

1. **Calls per tool** — bar, count, `dim: observation_name`, filter `observation_type = tool`, last 7 days.
2. **p95 latency per tool** — bar, p95 of `latency_ms`, same filter.
3. **Tools called once or never** — table, count, `dim: observation_name`, sorted ascending. Surfaces dead-weight tools.
4. **Tool fan-out per turn** — histogram, count of tool observations per trace, filter `trace_name = chat-turn`.

Drill-down: clicking a tool with high latency opens the slowest invocations for that tool.

## 4. Session Quality

Behaviour at the multi-turn level.

Widgets:

1. **Turns per session distribution** — histogram, count of traces, `dim: session_id`.
2. **Session duration p50 / p95** — line, p50 + p95 of (last trace end - first trace start) per session.
3. **Session cost p50 / p95** — line, p50 + p95 of total cost per session.
4. **Abandoned-session rate** — line. (Definition: a session with only one turn and no follow-up within N minutes; depends on the customer's UX semantics — note this in the plan.)
5. **Session-level scores distribution** — histogram or bar, `dim: score_value`, filter `score_name = <whatever the session score is named>`.

Drill-down: clicking a low-scored session opens its trace list ordered by start time.

## 5. Model & Prompt Drift

Catch regressions across deploys, model swaps, and prompt edits.

Widgets:

1. **Daily latency by model** — line, p95, `dim: day, metadata.model_id`, filter `observation_type = generation`.
2. **Daily cost by model** — stacked-bar, sum of `total_cost`, `dim: day, metadata.model_id`.
3. **Score average by `agent_version`** — line, avg of any relevant score, `dim: day, tag.agent_version`. The single best regression-spotter for agent quality if scores exist.
4. **Score average by `prompt_version`** — table, avg of any relevant score, `dim: metadata.prompt_version`. Lets the customer A/B prompts cleanly.
5. **Token usage per generation, by model** — bar, avg of `total_tokens`, `dim: metadata.model_id`.

Drill-down: clicking a regressed `agent_version` opens its traces compared side-by-side with the previous version.

## Optional add-ons (only when the instrumentation supports them)

### User heavy-hitter view

Useful only when `user_id` is populated and the product has user tiers.

Widgets:
- Top 50 users by trace count, by total cost, by error count.
- Per-tier (`metadata.user_tier`) cost percentiles.

### Eval dashboard

Only when the customer has datasets and eval runs (`trace_name starts with eval.`).

Widgets:
- Eval score over time per dataset.
- Eval pass rate per `agent_version`.
- Side-by-side comparison of two agent versions on the same dataset.

## Notes on "abandoned session" and similar derived metrics

These all require the customer to define what counts. Default heuristics (single turn + no follow-up within X minutes) work for most chat products but break for one-shot agents like nightly jobs. The dashboard plan should call out the heuristic and link to the spot in the codebase the customer can adjust to make it precise.

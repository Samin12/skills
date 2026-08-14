# A/B test patterns for a Ratel rollout

Three strategies. Pick one per pilot; document the pick + the customer's flag/split mechanism in the plan. Whatever the strategy, every trace must land in the customer's OTel backend with a `feature_flag` tag valued either `tool_pool=full` (control) or `tool_pool=ratel` (treatment) — that tag is what the value dashboards from [`/ratel-observability-assessment`](../../ratel-observability-assessment/SKILL.md) (conceptual map in [`ratel-value-map.md`](../../ratel-observability-assessment/references/ratel-value-map.md)) split on.

## Pattern 1 — Live feature flag (preferred default)

When to use:
- Traffic is enough to learn from a split (rule of thumb: ≥200 traces / day on the pilot trace_name).
- The customer has a feature-flag layer or is willing to add one.
- Production risk of the Ratel arm is acceptable (i.e., even if it underperforms, no user is broken).

How it works:

1. At each request entry point, read the flag for the current user/session. Two values: `full` (control) and `ratel` (treatment).
2. The flag decision is made *once* per trace and propagated as the `feature_flag` trace tag.
3. The control arm runs the agent with the customer's original tool list.
4. The treatment arm runs the agent with Ratel's top-K (Mode 1) or via Ratel Local (Mode 2).
5. Both arms emit traces; dashboards split on the tag.

What to specify in the plan:

- The flag name (`ratel_tool_pool` or per the customer's convention).
- The decision rule (50/50 hash on user_id; 10% ramp; cohort-based).
- The propagation site (the file + line that sets the trace tag).
- The kill switch (how to force everyone to `full` if the treatment arm misbehaves).

Common pitfalls:

- **Re-deciding per turn**: if the flag is re-read mid-session, a user can flip arms across consecutive turns and the analysis becomes noisy. Pin the decision at session start.
- **Flag missing from trace tag**: every dashboard's split filter relies on `tag.feature_flag` being present on every trace. If the flag is only logged in metadata, the dashboards won't pivot correctly.
- **Tag includes the user_id**: don't. Tags are coarse, low-cardinality.

## Pattern 2 — Shadow mode

When to use:
- Production risk is high (regulated industry, top-tier customer, brand-sensitive output).
- The customer wants validation before any user sees a Ratel-influenced response.
- Cost of running both paths in parallel is acceptable.

How it works:

1. The production path runs unchanged and is what the user sees.
2. In parallel, the Ratel path runs with the same input. Its spans export to your OTel backend but its output is discarded; the user never sees it.
3. Both runs produce traces. Tag the shadow trace `feature_flag=tool_pool=ratel` and `tag.shadow=true`; tag production `tool_pool=full`.

What to specify in the plan:

- Where the shadow invocation forks (the entry point or a queue consumer).
- The cost cap (% of production traffic to shadow — default 10%).
- How shadow output is silently logged (your OTel backend, not user-facing logs).

Common pitfalls:

- **Shadow leaks to user**: any path where the shadow run's output is returned to the user breaks the experiment. Add a test that asserts shadow responses are never returned.
- **Doubled side-effects**: if any tool has a side effect (writes a row, sends a message), the shadow run will double-execute it. Stub side-effecting tools in shadow mode or skip them.
- **Latency**: shadow doubles compute cost and sometimes wall-clock latency (if the dispatch isn't async). Decouple via a queue if it matters.

## Pattern 3 — Replay

When to use:
- Live traffic is too thin for a meaningful split (<50 traces / day on the pilot trace_name).
- The customer has an eval dataset or is willing to record inputs from production for offline replay.
- A one-shot delta is enough (rather than ongoing measurement).

How it works:

1. Collect a sample of real inputs into a dataset (your eval store, or any OTel backend that keeps inputs). Tag them as the baseline.
2. Replay each input through the agent under the Ratel arm offline. Log replay traces with `feature_flag=tool_pool=ratel` and `tag.replay=true`.
3. Compare baseline traces (tagged `tool_pool=full`) and replay traces side by side.

What to specify in the plan:

- The dataset name and how it's collected.
- The replay harness (a small script in the customer's repo or an internal eval tool).
- The eval criteria (cost delta, score delta against ground truth if labelling exists).

Common pitfalls:

- **Inputs leak production data**: the dataset will contain real user inputs. Treat it as production data — same access controls.
- **Time skew**: replay runs against the current state of the world (current prompts, current model snapshot, current tools), not the world the baseline saw. Note this caveat in the plan; if any of those change between baseline collection and replay, the comparison is contaminated.
- **No ground truth, no signal**: if there's no scoring mechanism (programmatic, LLM-as-judge, or human), the replay only gives you cost/latency. That's still useful, but say so.

## How to ask the user when the pattern isn't obvious

Codebases without an existing flag layer are common. Don't invent a new one without asking. Ask in one batched question:

> A/B strategy is the part of this rollout that's most codebase-specific. Quick check:
>
> - Do you already use a feature-flag tool (LaunchDarkly, Statsig, GrowthBook, Unleash, or something internal)?
> - If not, would a simple `process.env.RATEL_ARM_PCT` + hash-on-`user_id` split be acceptable for the pilot, or do you want me to recommend a third-party tool?
> - Is shadow mode an option, or is the per-request compute budget too tight?
> - Any traffic-level constraints I should know about (e.g., paid tier only, geo restrictions, internal employees only)?

Wait for the answers before writing the A/B section of the plan. Putting a placeholder "TBD" in the plan is worse than asking.

## Trace tagging cheat-sheet

Regardless of pattern, every Ratel-arm trace needs these tags / metadata for the dashboards to work:

| Field | Value (treatment arm) | Value (control arm) |
| --- | --- | --- |
| `tag.feature_flag` | `tool_pool=ratel` | `tool_pool=full` |
| `tag.env` | `prod` / `staging` / `dev` (same in both) | same |
| `tag.stack` | the customer's stack id (same in both) | same |
| `tag.agent_version` | git sha or version (same in both) | same |
| `origin` (native attr on `ratel.search` span) | `direct` or `agent` | n/a |
| `top_k` (native attr on `ratel.search` span) | the k used | n/a |
| `replace_mode` (extra attr at the swap site) | `true` (Mode 1 replace) or `false` (gateway mode) | n/a |
| `tag.shadow` (Pattern 2 only) | `true` on shadow traces | not present on prod traces |
| `tag.replay` (Pattern 3 only) | `true` on replay traces | not present on baseline traces |

These exact field names are what the dashboards filter on. If the customer's instrumentation uses different names, change them everywhere — including the dashboards plan — not just here.

## Success criteria (write these into the plan)

For the pilot to be called successful:

- **Token Cost & Savings dashboard** shows ≥30% drop in input tokens on the treatment arm vs control for the pilot trace_name. (Rule of thumb; tune to the customer's expectations.)
- **Retrieval Quality dashboard** shows recall@5 ≥0.7 over the window (if ground truth is wired) or top-hit-score distribution clearly skewed to high values.
- **Error rate** on the treatment arm is within 1pp of the control arm (no regression).
- **p95 latency** on the treatment arm is within +50ms of the control arm (default `bm25` retrieval adds well under a millisecond; `semantic`/`hybrid` add a few ms after the local model warms up — anything bigger is a wiring bug).

State these explicitly in the plan, so "did the pilot succeed?" has a one-line answer two weeks in.

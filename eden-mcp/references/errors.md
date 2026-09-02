# The structured-error contract

Eden tools don't throw for expected failures — a thrown error would get wrapped in the MCP SDK's generic "tool execution failed" envelope, stripping the recovery hint. Instead, every recoverable failure comes back as a JSON tool result you must read:

```json
{
  "ok": false,
  "status": "invalid",
  "message": "<human-readable reason + recovery hint>",
  "errors": [{ "path": "segments.1", "message": "over the platform limit", "code": "too_long" }],
  "httpStatus": 400,
  "tool": "eden_schedule_post"
}
```

Branch on **`status`** — it's a closed set. `message` always embeds the recovery hint; `errors[]` (when present) names the exact field/segment/rule that failed.

## Status → what to do

| `status`            | Typical HTTP | Meaning                                                                                 | Your move                                                                                                                                                                               |
| ------------------- | ------------ | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `invalid`           | 400          | Deterministic validation failure (bad/over-limit field, wrong platform for media, etc.) | **Do NOT retry the same payload.** Read `errors[]`, fix the specific field, surface the concrete problem to the user.                                                                   |
| `auth-expired`      | 401          | Token reached Eden but was rejected                                                     | Tell the user to refresh the Eden MCP credential; retry once after. (If it surfaced as a _transport_ error instead, reconnect — see <connection-and-auth.md>.)                          |
| `forbidden`         | 403          | Authenticated, but no access to **this** resource                                       | Confirm the id/workspace with the matching `list_*`/`resolve_*` tool. **Reconnecting won't help.**                                                                                      |
| `not-found`         | 404          | Resource doesn't exist (deleted or wrong id)                                            | Re-resolve the id with a `list_*`/`resolve_*` tool.                                                                                                                                     |
| `conflict`          | 409          | State blocks the action (post already publishing/posted, belongs to another schedule)   | Deterministic — surface the message; don't retry.                                                                                                                                       |
| `quota-exceeded`    | 429          | User hit an Eden plan limit                                                             | Surface to the user; don't silently retry.                                                                                                                                              |
| `out_of_credits`    | 402          | The user's Eden research credits ran out mid-task                                       | **Stop paid research calls immediately** — see "Out of credits" below.                                                                                                                  |
| `upgrade-required`  | 403          | The feature needs a higher Eden plan (e.g. analytics needs Starter+)                    | One plain line with the link from the message (fallback: https://app.eden.so/?settings=billing). Don't retry.                                                                           |
| `read-only-token`   | 403          | The Eden connection was authorized read-only; a setup/write tool refused                | Have the user remove and re-add the Eden connector, approving write access. Don't retry until they have.                                                                                |
| `not-available`     | 403          | Feature-flagged off for this account                                                    | Relay plainly ("not enabled on this account yet"); don't retry. If the payload carries a `fallback` (analytics tools do), follow it instead of dead-ending.                             |
| `unavailable`       | 404          | Ads research isn't enabled for this account (ads tools only)                            | Say so plainly; stop calling ads tools this turn. Never fall back to web search for ad content.                                                                                         |
| `indexing`          | —            | `eden_get_brand_ads`: the brand was just added and its ad library is syncing            | The tool already auto-waited ~25s — do **not** immediately re-call. Say you've started gathering that brand's ads; ask again in a few minutes. **Never** report the brand as not found. |
| `ambiguous`         | —            | `eden_get_brand_list_ads`: several brand lists match the name                           | Ask which of `candidates` the user meant, or re-call with the exact name. A `not-found` from this tool carries the user's real brand-list names — use one of those.                     |
| `unreachable`       | 504          | Transient network blip between MCP and Eden                                             | Safe to **retry once** after a brief wait.                                                                                                                                              |
| `missing-workspace` | —            | No workspace id resolved and none default                                               | Call `eden_list_workspaces`, pass an explicit `workspaceId`.                                                                                                                            |
| `moved`             | —            | You called a deprecated tool name that was folded into another tool                     | The payload's `replacement` + `message` name the new tool and how to call it. Switch to it; refresh your tool list to drop the stub.                                                    |
| `error`             | other        | Upstream non-2xx                                                                        | Surface the message; suggest retrying shortly.                                                                                                                                          |

## Decision rule

1. **`ok: true`?** Proceed.
2. **`status` is `invalid`, `conflict`, `forbidden`, `not-found`, `quota-exceeded`, `out_of_credits`, `upgrade-required`, `read-only-token`, or `not-available`?** Deterministic — **do not retry the same call.** Fix the input or surface the message verbatim to the user.
3. **`status` is `unreachable`?** Retry once.
4. **`status` is `auth-expired`, or you got a _transport_ auth error with no tool result?** Connection problem → <connection-and-auth.md>.

## Out of credits mid-task

Research tools spend credits from the user's Eden plan. When they run out you get:

```json
{
  "ok": false,
  "status": "out_of_credits",
  "message": "...",
  "upgradeRequired": true,
  "upgradeUrl": "..."
}
```

The rules, in order:

1. **Stop making paid research calls immediately.** Retrying spends nothing and returns the same error.
2. **Finish the task honestly from what you already have.** Fewer findings, labeled partial in one line — a thin honest deliverable beats a padded one. (Free plumbing reads — listing workspaces, reading a note — still work; everything else spends credits: own-workspace reads and analysis 0.2, searches 0.5, post reads and study tools 1. All of it stops at zero.)
3. **Give the way out once, without nagging:** the `upgradeUrl` from the payload, or https://app.eden.so/?settings=billing when it's missing.
4. Never fake results to fill the gap, and never end the run with only an error message.

## Rate limiting (transport, not a tool result)

The hosted server caps JSON-RPC calls at roughly **120 per minute** per bearer token. Over budget, you get a JSON-RPC error (code `-32000`) with HTTP `429` and a `Retry-After` header — this arrives at the **transport** layer, not as a `{ ok: false }` tool result. Don't fan out dozens of parallel tool calls; pace them, and back off for the `Retry-After` window when you see it. This is distinct from the `quota-exceeded` tool status above (that one is the user's Eden _plan_ limit).

## Don't escalate around a clean error

A structured error is Eden telling you precisely what's wrong. The wrong responses — and they actively make things worse — are: retrying an `invalid` payload unchanged, shelling out to a subprocess to bypass the tool, fabricating a token, or creating a duplicate "clean" record while leaving the failed one behind. Read the `message`, do what it says, or relay it to the user.

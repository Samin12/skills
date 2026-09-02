# Recipes — end-to-end flows

Concrete tool sequences for the things users actually ask for. Each step names the tool; read the linked reference for the arguments. Resolve `workspaceId` once (see "Getting oriented" in SKILL.md) and reuse it.

## Research a creator, then draft in the user's style

> "Look at what's working for @creator and write me one like that."

1. `eden_resolve_creator` if the handle is ambiguous, else go straight to →
2. `eden_analyze_creator` — top posts ranked against their baseline, plus the hook patterns. (This ranks the full indexed corpus — never rank over the user's saved cards.)
3. Optionally `eden_get_custom_ai` to adopt the user's chosen writing Custom AI and relevant sources.
4. Draft it yourself from the patterns. Show the user — don't schedule unprompted.

See <scheduling.md>, <workspace-and-social.md>, <custom-ai.md>.

## Research, draft, and schedule — in one flow

> "Find a strong hook in my niche, write a post, and queue it for tomorrow morning."

1. `eden_search_social_content` (`scope: "following"` or `"global"`) or `eden_analyze_creator` for the raw material.
2. `eden_list_schedules` — read the **connected platforms, timezone, and next open slot** before composing. Compose to those platforms' rules.
3. **Confirm platforms + time with the user.**
4. `eden_schedule_post` with `scheduledFor` (epoch ms) resolved against the schedule's timezone — or with `draft: true` if they only want it saved for review.

See <scheduling.md>.

## Edit or reschedule an existing post

> "Move my Thursday post to Friday 9am" / "fix the typo in that scheduled post."

1. `eden_list_scheduled_posts` (filter by `status`) → get the `postId`.
2. `eden_update_scheduled_post` — pass only `scheduledFor`/`scheduledAtIso` to reschedule, or body fields to edit. **Edit in place; never clone a "fixed" copy and leave the original.**

A post that's already `publishing`/`posted` returns `conflict` — surface it, don't retry. See <scheduling.md>.

## Find posts on a topic and save them to a board

> "Save the best posts about pricing from people I follow into a swipe board."

1. `eden_search_social_content` (`scope: "following"`, the topic as query).
2. `eden_create_board` if the target board doesn't exist (or find it via `eden_list_workspace_items`).
3. `eden_save_posts_to_board`.

See <workspace-and-social.md>.

## Save the user's own highlights (or notes, PDFs) to a board

> "Put my best Kindle highlights about pricing on a board."

1. `eden_search_highlights` (omit `q` to list recent) — keep each result's **`itemId`**.
2. `eden_create_board` if the board doesn't exist, else find it with `eden_search_workspace_items`.
3. `eden_save_items_to_board` with those `itemId`s (max 25 per call).

Never route this through `eden_save_links_to_board` — a highlight's `url` saves a stray link card instead of the quote. An `itemId` of `null` means there's no Library card for it in this workspace; say so rather than falling back to the URL. See <workspace-and-social.md>.

## Change when the queue posts

> "Post me at 8am and 6pm on weekdays instead."

1. `eden_list_schedules` — read the current `slots` and `timezone`.
2. Build the **full** replacement slot array (include unchanged slots, or they're deleted) and confirm it with the user.
3. `eden_update_schedule` with those `slots` (and `timezone` if it's wrong).

Already-queued posts keep their times; the new slots only shape future picks — tell the user that. To move one existing post, use `eden_update_scheduled_post` instead. See <scheduling.md>.

## Run one of the user's Custom AI

> "Run my Newsletter Writer."

1. `eden_list_custom_ai` → find the `customAIId` (don't guess).
2. `eden_get_custom_ai` → adopt `instructionsMarkdown` and resolve only relevant sources.
3. For managed knowledge, use `eden_search_custom_ai_knowledge` (no query = catalog) and `eden_read_custom_ai_knowledge`.
4. Execute with the tools you have here.

See <custom-ai.md>.

## Connect the user's social accounts

> "Help me connect my X and LinkedIn to Eden."

1. `eden_connect_social_accounts` with `action: "status"` — show what's already linked.
2. `action: "get-link"` — hand the user the personal linking URL; they open it, click each network, authorize. The link is theirs alone — never post it anywhere shared.
3. When they say they're done: `action: "sync"`. Nothing they linked shows up in Eden without this step.
4. Substack can't use the link page; it connects in Eden's web app under Settings → Social accounts.

See <scheduling.md>.

## Check how the user's own content is doing

> "How did my posts do this month?" / "what's working for me?"

1. `eden_get_analytics` — totals with vs-previous deltas, follower counts, outlier posts, topic/format winners, peer benchmarks. The first call on an untracked workspace auto-starts tracking (`activating: true` — say the import is running, re-check in a few minutes). `accountsConnected: false` → run the connect recipe first.
2. Per-post detail or "my top posts": `eden_list_analytics_posts` with a `sort`.
3. This is the user's OWN private warehouse. "Best posts by `<other creator>`" routes to `eden_analyze_creator` instead.
4. Warehouse unavailable (`not-available`, `upgrade-required`, or the first import still running)? Fall back: `eden_connect_social_accounts` (action `status`) for the handles, then `eden_resolve_creator` + `eden_analyze_creator` per handle — present as public estimates, and mention the upgrade link once if the payload says an upgrade unlocks the full warehouse.

See the analytics section of <scheduling.md>.

## Build the user an analytics dashboard

> "Build me a dashboard of my numbers."

1. Pull `eden_get_analytics` and `eden_list_analytics_posts` (plus `eden_list_scheduled_posts` if you're showing the queue).
2. Render one self-contained page (artifact, or an HTML file if you can write files): totals up top with deltas, top posts, outliers, the queue. Real numbers only — rows whose `metricsStatus` is `syncing` are "still filling in", never zeros.
3. The full guided build (five stations, Telegram digest, weekly refresh) is the free Content Command Center workflow: https://eden.so/workflows/content-command-center/

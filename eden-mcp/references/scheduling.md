# Scheduling social posts

The scheduler is where unguided agents do the most damage — they invent in-place hacks, leave broken draft rows behind, or guess platform rules. Follow this flow.

## Always start by reading the schedule

Before writing anything, call **`eden_list_schedules`**. It returns, per schedule: the `scheduleId`, the **connected platforms** (only these can publish), the **timezone**, and the **next open slot**. You need these to build a valid post. Don't assume a platform is connected — Instagram in the enum ≠ Instagram linked on this account.

`eden_schedule_post`, `eden_publish_post_now`, and `eden_cancel_scheduled_post` push to live accounts — confirm content, platforms, and time with the user before firing unless they've said to just do it. Drafts are safe.

Then pick the write tool by intent:

| User intent                                           | Tool                                 | Effect                                                    |
| ----------------------------------------------------- | ------------------------------------ | --------------------------------------------------------- |
| "Save it / draft it for later"                        | `eden_schedule_post` + `draft: true` | Writes a draft row, **no** publish time, nothing enqueued |
| "Schedule it for <time>"                              | `eden_schedule_post`                 | Creates the post **and enqueues** it for that time        |
| "Post it now"                                         | `eden_publish_post_now`              | Queues for immediate publish                              |
| "Change the time / edit the text of an existing post" | `eden_update_scheduled_post`         | Edits the existing row **in place**                       |
| "Cancel it"                                           | `eden_cancel_scheduled_post`         | Cancels a queued post                                     |
| "Change my posting times / timezone"                  | `eden_update_schedule`               | Rewrites the recurring queue slots, not any single post   |

### Editing an existing post: edit in place, never re-create

To change a post that already exists, find its id with `eden_list_scheduled_posts`, then call **`eden_update_scheduled_post`** with that `postId`. Two modes:

1. **Reschedule only** — pass `scheduledFor` (epoch ms) or `scheduledAtIso`, leave the body fields out. Existing content/platforms are kept.
2. **Edit the body** — pass any of `text`, `segments`, `media`, `platforms`, `perPlatform`. Omitted fields fall back to the existing post; existing media is kept unless you pass new `media`.

It **cannot** edit a post that's already `publishing` or `posted` — that returns `status: "conflict"`. That's expected; surface it, don't retry.

**Do not** "fix" a stuck/odd draft by creating a fresh scheduled copy and leaving the original behind. That leaves two rows and a confused schedule. If `update` returns a structured error, the `message`/`errors` tell you the real reason — act on that. If it returns a _transport_ auth error, that's a connection problem (see <connection-and-auth.md>), not a reason to clone the record.

## Changing the queue itself (not one post)

`eden_update_schedule` edits the **recurring** slot times and timezone — the cadence the queue picks from, shown under a brand in the scheduler. Use it for "post me at 8am and 6pm on weekdays" or "my schedule is in the wrong timezone". To move a single existing post, use `eden_update_scheduled_post` instead.

- Read `slots` from `eden_list_schedules` first, then pass the **full replacement array** — it replaces the whole set, so include the slots that aren't changing or you'll delete them.
- Each slot is `{ time: "HH:MM" (24h, in the schedule's timezone), days: [Mon, Tue, Wed, Thu, Fri, Sat, Sun] }` — exactly 7 booleans, Monday first. Max 48 slots.
- `scheduleId` is optional; omit it for the default schedule, pass it when the workspace has several brands.
- Already-queued posts keep their existing times. New slots only shape future picks — say that, so the user doesn't expect their queue to shuffle.
- Passing neither `slots` nor `timezone` is an error. It cannot rename a schedule.
- This rewrites the user's posting cadence, so confirm the new slot set with them before calling.

## Platforms

Valid platform ids: `twitter` (X), `threads`, `linkedin`, `substack`, `instagram`, `tiktok`, `facebook`, `youtube`.

> If a write rejects a platform that you know is valid (e.g. `facebook` or `youtube`) with an `invalid`/enum error, the **deployed server may be behind the current platform set** — newer platforms are added to the schema over time. Confirm the platform is actually **connected** on the schedule (`eden_list_schedules`); if it is and the call still rejects the enum value, surface that to the user rather than hand-dropping the platform silently — dropping it means the post won't go to where they wanted.

### Per-platform rules

| Platform      | Text-only OK? | Media                           | Notes                                                                                                                                                                           |
| ------------- | ------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `twitter` (X) | ✅            | optional                        | Threads via `segments`; auto-split if text too long. Caption may be empty when media is attached. Limit 280/500.                                                                |
| `threads`     | ✅            | optional                        | Threads via `segments`.                                                                                                                                                         |
| `linkedin`    | ✅            | optional                        | PDF "document" post: pass a hosted PDF asset → server derives `kind:'document'`.                                                                                                |
| `substack`    | ✅            | optional                        | Posts as a Substack note. Image Notes may use an empty caption.                                                                                                                 |
| `instagram`   | ❌            | **required**                    | Must attach hosted media; the caption may be empty. Single-video Reels can be Trial Reels with `perPlatform.instagram.trialReel: true`.                                         |
| `tiktok`      | ❌            | **required**                    | Must attach hosted media.                                                                                                                                                       |
| `facebook`    | ✅            | optional                        |                                                                                                                                                                                 |
| `youtube`     | ❌            | **required (1 vertical video)** | **Shorts only.** No text-only/image posts. Requires `perPlatform.youtube.title` (≤100 chars) — the title is **separate** from the optional description (the platform's `text`). |

### `platforms` defaults

`platforms` is optional. If omitted: defaults to the schedule's active **text** platforms when no media is provided, or active platforms when media is provided. When in doubt, pass `platforms` explicitly so the post goes exactly where intended.

## Media

- Media must be **already-hosted public URLs** in the `media` array. Local file paths are **not** valid.
- For Instagram carousel posts, upload each slide via the media-upload flow and
  preserve slide order in the `media` array.
- To upload bytes directly through MCP (up to 25 MB), use `eden_upload_scheduling_media`.
- **Sandboxed runtimes (e.g. claude.ai's code sandbox) cannot reach the presigned `uploadUrl`, and one tool call usually can't carry a whole image.** Use `eden_upload_scheduling_media` in **chunked mode**: split the file into ordered pieces (≈100–500 KB raw each, max 4 MB), call once per piece with `chunk: { index, total }` — the first call returns an `uploadSessionId`; pass it on every later chunk — and the final chunk returns the finished `asset`. The server assembles and hosts the file; nothing needs outbound network from the agent. Same `mimeType`/`fileName` on every call; a chunk can be re-sent to retry.
- To upload a larger file, call `eden_prepare_scheduling_media_upload`. A `single` plan returns one presigned PUT URL. For a `multipart` plan, drive `eden_scheduling_media_multipart`: `step: "sign-part"` for each part (PUT each byte range, retain its ETag), then `step: "complete"` with every partNumber + ETag; `step: "abort"` if the upload cannot be completed. Only pass the hosted `publicUrl` to a post after the upload completes.
- Allowed types: `image/jpeg`, `image/png`, `image/webp`, `image/gif`, `application/pdf`, `video/mp4`, `video/quicktime`, `video/webm`.
- Upload preparation supports files up to 10 GB; the selected social platforms still enforce their own lower limits during post validation.
- Give each media asset a stable `id`; `segments` and `perPlatform.*.mediaIds` reference assets by that id.
- For a media-only post, pass `text: ""`. Empty text with no media is invalid.

## Threads & per-platform variants

- **Threads (X/Threads):** pass `segments` (each entry is one post in the thread, with its own `mediaIds`). If you omit `segments` and the text is too long, Eden auto-splits against the **strictest** selected platform's limit.
- **`perPlatform`:** override per platform — e.g. IG carousel media only, Instagram Trial Reel with `perPlatform.instagram.trialReel: true` (single-video Reel only), LinkedIn PDF only, X text-only, a different thread per platform via `perPlatform.<platform>.segments`, or a YouTube Short's `title`. Use it to attach media to one platform but not another from a single call.
- **Platform-only media:** to attach an asset to SOME platforms but not others, mark it `scheduleMediaRole: "platformScoped"` in `media` and list its id in each intended platform's `perPlatform.<p>.mediaIds`. Platforms without an override then keep only the shared (non-scoped) media. Without the marker, platforms you don't override publish the WHOLE `media` pool. `perPlatform.<p>.mediaIds: []` makes that platform text-only.

## Long-form articles

Use `article` only with explicit `platforms` chosen from `twitter` and `substack`. Shared title/body is canonical; `article.variants.twitter` and `article.variants.substack` are complete destination overrides.

Before writing a Substack article, call `eden_list_schedules`. Active Substack accounts include captured `substackPublicationTags` when the authenticated publication session has supplied them; reuse those exact names in `article.substack.tags`.

Never guess Substack publishing choices. Ask for all of these before calling a write tool:

- `audience`: `everyone`, `only_paid`, `only_free`, or `founding`
- `commentPermission`: `everyone`, `subscribers`, `only_paid`, or `none`
- `sendEmail`: email/app delivery or web-only
- `cta`: `none`, `subscribe`, or `subscribe-caption`; subscribe variants require an explicit placement and caption text is editable
- `paywall`: `none` or `in-body`; `in-body` requires `paywallPlacement`
- `sendFreePreview`: required for paid/founding email articles with a paywall

Block placements are `{ position: "start" }`, `{ position: "end" }`, or `{ position: "after-block", blockIndex: 0 }`. `blockIndex` counts meaningful top-level article blocks from zero. Send structured choices only; never write `data-eden-substack-block` HTML yourself. The scheduling server materializes the canonical native blocks only in the Substack variant.

## Timestamps

Never pass natural language as a time. Use `scheduledFor` (epoch **milliseconds**, preferred) or `scheduledAtIso` (concrete ISO timestamp). Resolve "tomorrow 9am" yourself against the schedule's timezone (from `eden_list_schedules`) before calling.

## Idempotency

Write tools accept an optional `idempotencyKey`. Same key + same content (and time, for scheduled posts) returns the **same** record instead of creating a duplicate. Use one when a retry is possible so a transient hiccup doesn't double-post.

## Reading posts back

- `eden_list_scheduled_posts` — list drafts/scheduled/posted, filter by status (`draft`, `scheduled`, `publishing`, `posted`, `partial`, `failed`, `cancelled`). This is where you get a `postId` for edit/cancel.
- `eden_read_social_post` / `eden_read_media_card` — read a specific post / media card.
- First comment and auto-repost are set via `eden_update_scheduled_post`'s `firstComment` and `autoRepost` fields (the first comment applies to every platform on the post; auto-repost is X only and needs advanced automations enabled).

## Connecting accounts

`eden_connect_social_accounts` manages what's linked. Three actions:

1. `status` — what's connected right now, with handles (and Substack's publication address).
2. `get-link` — mints the user's personal Eden-branded linking page. Give them the URL; they click each network (X, LinkedIn, Instagram, Threads, TikTok) and authorize. The link is tied to their workspace — never post it anywhere shared.
3. `sync` — **always call this after the user says they finished linking**, or the new connections won't appear in Eden.

Substack is the exception: it can't link through that page (it needs the user's own browser session). Send them to the Eden web app → **Settings → Social accounts** (`https://app.eden.so/?settings=scheduling`), ideally with the Eden browser extension or desktop app.

## Instagram Auto-DM automations

Use `eden_list_auto_dm_rules` first to inspect the current rules and the workspace's remaining room (10 automations maximum). Then use `eden_create_auto_dm_automation` for requests like “when someone comments LINK, DM them my guide.” It supports comment-keyword DMs scoped to a specific, next, or every new post; story replies; DM keywords; DM reactions; and public comment replies.

Creating a rule can send real DMs to real people. Each DM actually sent costs 1 credit; public comment replies are free. Never invent the message, keywords, destination link, or post choice. The create tool deliberately returns `{ ok: false, status: "needs_clarification", questions: [...] }` when required details are missing. Ask those questions, then call the tool again with the user's answers. For a specific-post rule, the tool returns recent Instagram posts with the Meta Graph ids the automation API requires—do not substitute ids from public social-search tools.

The same server-side gates and safety checks as Eden's Auto-DM pane apply: Pro/Studio access, workspace membership, connected Instagram messaging permissions, blocked destinations, credits, and the rule cap. If the result says Instagram needs reconnecting or is not connected, send the user to **Settings → Social accounts**; do not retry the same create payload.

## Analytics (the user's own numbers)

- `eden_get_analytics` — compact digest: period totals with vs-previous deltas, follower counts, outlier posts (beating the user's own baseline), top topics/formats, peer benchmarks. `window` echoes what history was actually served (tier-clamped).
- `eden_list_analytics_posts` — per-post metric rows (views/likes/comments/shares/saves/impressions/reach/watch time, Substack email opens, link clicks, outlierScore, creatorPercentile). Sort by any metric; filter by platform/contentType. This is the raw material for charts and dashboards.
- Activation is automatic: the first `eden_get_analytics` call auto-starts tracking when accounts are connected (`activating: true` in the response — say the import is running, re-read after a few minutes; pass `brandId` to work with one brand's scope). `accountsConnected: false` means connect accounts first. `metricsStatus: "syncing"` rows are still filling in — never present missing metrics as zeros.

These read the user's OWN private warehouse. For other creators' public performance, use the research tools instead.

**When the warehouse can't answer, fall back to public data.** A `not-available` or `upgrade-required` error (analytics needs Starter+; mention the upgrade link once, plainly), or an `activating: true` first import, is not a dead end: get the user's connected handles via `eden_connect_social_accounts` (action `status`), then run `eden_resolve_creator` + `eden_analyze_creator` on each. Present those numbers as **public estimates** — private metrics (impressions, saves, Substack email opens) only exist in the warehouse. The error/response payloads carry this same hint in a `fallback`/`fallbackHint` field.

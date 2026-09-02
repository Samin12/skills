# Workspace vs. social — and read-tool routing

## The distinction that decides every routing call

- **Workspace tools** return what the user has **personally saved** — a hand-curated swipe file, typically a tiny fraction of any creator's output.
- **Social tools** rank against the **full indexed corpus** and a creator's own performance baseline.

These are **not interchangeable.** Never answer a "best/top posts by X" question by filtering saved cards — the saved cards are a hand-picked swipe, not a ranked sample, so any ranking you compute over them is wrong.

## Routing

| Request                                                                                  | Tool(s)                                                                                                                                                     |
| ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| "find competitor creators", "who talks about `<topic>`"                                  | `eden_search_creators` with `kind: "topic"`; returns people with matching-post evidence                                                                     |
| "creators like `<creator>`", "more creators like this list"                              | `eden_search_creators` with `kind: "similar-to-creators"` or `kind: "similar-to-list"`                                                                      |
| "best/top posts by `<creator>`", "what does `<creator>` post about", "their viral hooks" | `eden_analyze_creator` (use `eden_resolve_creator` first if the handle is ambiguous)                                                                        |
| "have I saved anything by `<creator>`?", "my saved `<creator>` posts"                    | `eden_search_workspace_items` with the handle/profile domain as `q` (URLs are matched; pair with `eden_analyze_creator`)                                    |
| "find posts about `<topic>`" across following / a list / globally                        | `eden_search_social_content` with `scope`: `creator` \| `list` \| `following` \| `global`                                                                   |
| "who do I follow?", "creators I'm tracking"                                              | `eden_following_overview` (optional `platform`). Returns **creators**, not posts.                                                                           |
| "what's in my `<list>`", "who's in my `<list>`"                                          | `eden_analyze_list` (no `query`/`listRef` lists all lists)                                                                                                  |
| "what's on my board", "tell me about my workspace"                                       | `eden_list_workspaces` → `eden_list_workspace_items` (paginated, pass `limit`) → `eden_read_board` for boards                                               |
| Read a specific saved item                                                               | `eden_read_social_post` (by `url` or `contentId`), `eden_read_media_card`, `eden_get_note_markdown`                                                         |
| "what's in my `<table>`/list", rows + columns of a table item (`type === "table"`)       | `eden_read_table` (schema + each row's cell values, first 2000 rows; values are keyed by property id; each row's `rev` is its edit stamp for `expectedRev`) |
| Search the user's saved items                                                            | `eden_search_workspace_items` (title/URL substring) or `eden_find_workspace_items` (semantic, 0.2 credits)                                                  |
| "everything tagged `<tag>`", "tag this", the user's own tag vocabulary                   | `eden_list_tags` (names + colors) → `eden_update_item_tags` (write) or `eden_find_workspace_items` with `userTags` (filter)                                 |
| "what's connected/linked/related to this item", traverse or grow the graph               | `eden_get_connections` (existing backlinks + semantic suggestions) → accept suggestions via `eden_connect_items`                                            |
| "give me titles based on what's working", YouTube titles, title patterns                 | `eden_study_top_titles` (creator or `niche`; `platform` `youtube`\|`substack`\|`twitter`)                                                                   |
| "what ADS are running in `<niche>`", winning ad copy/hooks, competitor ads               | `eden_search_ads` (`category`, `angle`, `platform`, `minRunDays`, `sort`)                                                                                   |
| "what is `<brand>` running", "show me `<brand>`'s ads"                                   | `eden_get_brand_ads` (name, @handle, or URL — URLs resolve most reliably)                                                                                   |
| "save those ads", "build me an ad swipe file"                                            | `eden_save_ads_to_board` (each ads result's `id`, verbatim; never via the links tool)                                                                       |
| "ads from my `<list>`", "what brand lists do I have"                                     | `eden_get_brand_list_ads` (omit `list` for the roster; brand lists ≠ creator lists)                                                                         |
| "add `<brand>` to my `<list>`", "make a swipe-file list with these brands"               | `eden_save_brands_to_list` (exact list name; a new name creates the list)                                                                                   |
| Top-performing carousels to study                                                        | `eden_study_top_carousels`                                                                                                                                  |
| Highlights (saved quotes/clips)                                                          | `eden_search_highlights` (omit `q` to list recent)                                                                                                          |
| "How did MY posts do", the user's own numbers                                            | `eden_get_analytics`, `eden_list_analytics_posts` — private warehouse, see <scheduling.md>; never route to the research tools                               |

`eden_study_top_titles` is the titles lane. It reads the top-outlier headlines
for a creator or niche and returns each one's **skeleton** — the syntactic frame
with slots (`After [studying N of a thing], here's how to [outcome]`) — next to
the verbatim source, what each slot needs, the move that makes it pull, and
`doNotReuse`: the source's own numbers, names, and story.

The split matters. The **frame** is craft and is meant to be reused; the
**substance** is the other creator's and never travels. The failure mode this
tool exists to prevent is reading a winner, naming the principle behind it
("uses credibility and specificity"), and then writing a fresh title from that
principle — the structure that carried the performance is gone and the result is
a title nobody clicks. Show the source headline beside the frame you used, vary
the frames across your options, never hand back a skeleton as a finished title,
and never carry a `doNotReuse` value into one.

Scope is narrow on purpose. Only three sources carry an authored title: **YouTube
videos, Substack ARTICLES, and native X ARTICLES**. Short-form has no title —
tweets, Substack notes, reels, TikToks, LinkedIn and Threads posts are excluded,
because their first line is body text that happens to sit on top rather than
packaging someone wrote. The hook INSIDE a video, the spoken or on-screen opening
in the first seconds, is a different artifact that lives in the transcript.

When the user's own surface IS short-form ("titles for my tweets", "hooks for my
reels"), it is not a titles question at all. Pull the posts with
`eden_search_social_content` / `eden_read_social_post` and study their openings
directly, and say plainly that short-form carries no title — never quietly study
a platform they did not ask about.

`eden_search_social_content({ scope: "following" })` returns **posts**; `eden_following_overview` returns the **list of creators**. Pick by whether the user asked for posts or people. (`scope` is a plain string — `"creator"` and `"list"` also need a top-level `creatorRef` / `listRef`.)

`eden_search_creators` is also people-first. Always pair the selected `kind` with its required field: `topic` + `query`, `similar-to-creators` + `creatorRefs`, or `similar-to-list` + `listId`. Its topic mode searches pooled creator embeddings, while its two similarity modes blend creator-embedding proximity, co-listing, and category overlap. Pass exact `platform` + `username` refs from `eden_resolve_creator` for creator seeds; never guess handles. Platform and follower-count filters constrain the returned competitor set. An `invalid` result names the missing or malformed field; fix that field instead of retrying the same payload.

The ads tools read a third corpus: **paid ads** (real Meta Ad Library and
TikTok Creative Center creatives from tracked brands), separate from both the
organic social index and the user's saved items. Never answer an ads question
with `eden_search_social_content`, and never answer an organic-content
question with the ads tools. Two facts shape every ads answer: Meta publishes
NO engagement metrics, so `runDays` and `variationCount` are the honest proof
of performance (a brand pays daily to keep an ad running); TikTok rows carry
real `ctr`/`likeCount`. `eden_get_brand_ads` auto-adds an un-tracked brand,
starts syncing its library, and already waits up to ~25s for the first ads —
the common case returns real ads in the same call, with a `notice` marking a
freshly-indexed, still-growing library (relay it). `status: "indexing"` means
the wait came up dry: say you've started gathering that brand's ads and to
check back in a few minutes — never that the brand wasn't found, and don't
immediately re-call the tool. `status: "unavailable"` means ads research isn't enabled
for this account: say so plainly and stop calling ads tools this turn.

The user can also curate **brand lists** ("Competitors", "Swipe file") —
collections of advertisers, built on Eden's Discover surface. They are a
DIFFERENT entity from creator lists and the two can share a name: in an ads
context, resolve "my `<name>` list" with `eden_get_brand_list_ads` first
(`eden_analyze_list` only knows creator lists). Omit `list` for the roster of
all brand lists; pass a name for that list's member brands plus the
top-ranked ads across them. A `not-found` reply carries the user's real
brand-list names — re-call with one of those or ask which they meant.

Brand lists are WRITABLE too: `eden_save_brands_to_list` adds brands to a
list by exact name (case-insensitive) and creates the list when no exact
name matches — so reuse a name from the roster when adding to an existing
list. `brands` entries can be names, @handles, URLs (most reliable), or
`advertiserId`s from prior ads results. An un-tracked brand that Meta has is
added to the ads index on the spot and its library starts syncing — relay
the `notice`; a brand with no ad-library presence lands in `failed` with the
reason. Idempotent: repeats report `alreadyInList`, never duplicates.

## Workspace writes

- Notes: `eden_create_note`, `eden_update_note`, `eden_append_to_note`. Write note bodies **without blank lines between blocks** — Eden's editor adds vertical spacing per block, so blank lines render as double gaps. The server strips blank lines between blocks on save (blank lines inside fenced code blocks are preserved).
- **Embedded items in notes**: `eden_get_note_markdown` shows a note's embedded workspace items (e.g. an inline table) as marker lines like `[Embedded table: "Content calendar" — itemId <id>]`. Treat each marker as an **opaque token**: carry it through verbatim when rewriting the note (the server restores it to the live embed block on save), never reword or delete it, and read the embedded item itself via its `itemId` (`eden_read_table` for tables, `eden_get_note_markdown` for notes).
- Cards / sticky notes: `eden_create_note` with `presentation: "card"`. Eden's frontend calls these text-first canvas elements **Cards**. Route “capture this,” ideas, thoughts, reminders, and “create/add/make a card” here. The default `presentation: "document"` makes a long-form Document. “Card” is contextual: an existing URL or indexed social post should keep its rich metadata via `eden_save_links_to_board` or `eden_save_posts_to_board`, not become a plain text Card.
- Boards: `eden_create_board`, `eden_rename_board`, `eden_trash_board`. A same-titled existing board is REUSED (`reused: true`) rather than duplicated — right for "save these to my X board", wrong when the user asked for a NEW or SEPARATE board: that board already holds their content, so stop before saving anything to it and ask whether to use it or create one under a different name. Retrying a timed-out `eden_create_table` / `eden_create_note` with identical args is safe — the create converges on the item the first attempt made instead of duplicating it (a convergence comes back with a warning saying so; re-read before further edits).
- **Sidebar folders hold BOARDS, never items.** Folders are visual sidebar organization only — they are not workspace items, so item search can't return one as an item; `eden_search_workspace_items` surfaces matching folders in a separate `folders` field (name + the boards each holds). "Put these in my `<folder>` folder" therefore always means a BOARD inside that folder: save the items to one of the folder's boards, or create one there with `eden_create_board`'s `folder` param (folder NAME, case-insensitive; created at the root when none matches; works on a reused board too, which is how an existing board moves into a folder). Never create a root-level board named like the folder as a stand-in. When no board in the folder fits and none is implied, ask which board they want or offer to create one.
- Saving content onto a board — pick by what you're holding:
  - A URL the workspace doesn't have yet → `eden_save_links_to_board` (creates a new item).
  - An indexed social post from the research tools → `eden_save_posts_to_board` (keeps its rich post metadata).
  - An ad from the ads research tools → `eden_save_ads_to_board` with each result's `id`. Saves a durable ad card (creative + advertiser + run-time stats, with a permanent media copy that outlives the ad being paused). Never save an Ad Library URL through `eden_save_links_to_board` — that makes a bare link card. Idempotent per (board, ad); max 12 ids per call.
  - An item the workspace **already has** (a highlight, note, saved link, PDF) → `eden_save_items_to_board` with its `itemId`. Creates no new item, just a card pointing at the canonical one. Idempotent: items already there come back as `alreadyOnBoard` instead of duplicating. Max 25 ids per call.
- **Highlights always go through `eden_save_items_to_board`.** Pass the `itemId` from `eden_search_highlights` — never save a highlight's `url` with `eden_save_links_to_board`, which creates a stray link card instead of the quote. If a highlight's `itemId` is `null` it has no Library card in this workspace; tell the user rather than falling back to the URL.
- Renaming a note: `eden_rename_note` (title only; use `eden_update_note` for body changes).
- Connections (backlinks): `eden_connect_items` links items to each other; read the existing graph and semantic candidates with `eden_get_connections`.
- Tags (the user's own labels): `eden_update_item_tags` adds/removes tags on a library item **by name** — adds auto-create missing tags, unknown remove names are ignored, and the call is idempotent (retrying lands the same state). Always call `eden_list_tags` first and reuse existing names (matching is case-insensitive — "Content Ideas" and "content ideas" are the same tag; a new synonym mints a near-duplicate the user has to clean up). Two tag namespaces exist: these user tags vs the AI-generated topic tags on `eden_find_workspace_items` hits (`tags` param). "Tag this" always means user tags; filter search to a user tag with the `userTags` param. Boards and chats can't be tagged.
- Tables (database-style lists — to-do lists, trackers, content calendars, hook banks): create with `eden_create_table` (typed columns + seed rows + view in one call; pick real column types — select/'status', rating, date, checkbox, url, multiSelect, item — never all-text; a column you'll GROUP BY must be a select with options like "Week 1"…"Week 12", never a bare number — only select/rating/checkbox/date columns form groups, and a number/text `view.groupBy` target is auto-converted to a select built from its values, so ask for the select directly and verify the groups hold rows before calling it done). Edit with `eden_add_table_rows` (append; cells keyed by column NAME, option values by name, unknown options auto-create), `eden_update_table_rows` (set cells / rename / mark done / soft-remove, addressing rows by row `itemId`, exact title, or the row's `rev` stamp from a CURRENT read — a stale stamp matches nothing, so re-read first; null clears a cell; pass the row's `rev` from your read as `expectedRev` so a row someone edited in the meantime is refused instead of overwritten — refused rows come back in `conflicts`, so re-read and retry those), and `eden_update_table` (rename, ADD columns, change the layout (`table` / `list` / `board` / `calendar` — `list` is the to-do shape, one line per row with its done circle, and grouping it on a date column buckets it into Overdue / Today / Tomorrow / This week) and grouping, and the SAVED VIEWS lane: `view.filters` / `view.hiddenColumns` by column NAME, `view.saveAsView` to name the current setup, `view.applyView` to switch to one by name — `null` means "All items"). View state is SHARED: the whole workspace sees the table the way you leave it, so change it when the user asks about their view, never to make your own reading easier. And note that reads are NEVER filtered — `eden_read_table` returns every row and reports the user's view in `viewSummary` (the LAYOUT they're looking at — `list` is a to-do list, one checkable line per row — plus the active view, its rules in plain English, and hidden columns), so apply those rules yourself when the question is about what they see. Read first with `eden_read_table`; every table write returns `warnings` — fix those with a follow-up update, never by recreating the table. Warnings are plumbing addressed to YOU, not to the user: act on one silently and never quote, paraphrase, or narrate it in your reply. For every select/multiSelect option you create, pass `{ name, color }` with an intentional semantic color rather than relying on fallback rotation: workflow statuses use gray for backlog/not started, amber for drafting/review, blue for scheduled/in progress, green for approved/published/done, red for blocked; prefer X gray, LinkedIn blue, Instagram purple, YouTube red, and text gray, thread blue, carousel purple, video red, newsletter amber. Adapt to different labels and preserve existing concept colors when editing. Prose goes in a note; a collection the user would sort, group, or check off goes in a table. A table ask gets a TABLE on its own — never a document wrapped around one: build the table, and offer a doc in ONE line at the end whenever that turn produced strategy the table cannot hold ("Want me to write this up as a doc with the table inside?") — if you wrote substantial strategy or reasoning into the reply itself and it is not in the table, that is exactly the case the offer exists for, never a reason to skip it. Go straight to writing a doc only when the user's own ask carried the thinking ("plan out my content season and give me the calendar" does; "make me a table of hooks" does not), and then say so in one line and proceed rather than waiting for a yes. After building, tell the user in one line the two judgment calls you made: what went in the Name column and how it is grouped ("Named each row by its hook, grouped by Tier"). Exactly one thing may ever follow that line: the doc offer above, which is REQUIRED whenever the turn produced strategy the table cannot hold — so the line ends the reply only when there is nothing to offer. Nothing else may follow it or join it — the table already renders its column list, so never restate or explain the columns you added ("I also added a Status column so you can track…"), which is padding.
- Table option palette (current; supersedes the older color examples in the preceding paragraph): the ten keys are `gray`, `amber`, `orange`, `red`, `pink`, `purple`, `indigo`, `blue`, `teal`, and `green`. Keep workflow statuses on the semantic core colors. For category columns, use orange/teal/indigo/pink when they improve distinction; current defaults prefer Instagram pink and thread indigo.
- The NAME column (a row's `title`) holds THE THING ITSELF: whatever a person would say out loud to refer to that row — the idea, the hook, the essay title, the task. Never a position, a number, or a category; those belong in their own columns. Test it: if a value counts up ("Week 1", "Idea 3") or would repeat across rows, it is a COLUMN, never a name. If a column you planned would hold the row's natural name, that content IS the name — put it in `title` and drop the column. A LONGER companion column is fine but must be named for what makes it different ("Script", "Full text", "Notes"), never a synonym of the name. A calendar or schedule row is named for what SHIPS, not for the slot; two pieces in one week means two rows. BAD: a row called "Week 1" with an `Essay Title` column holding "The Second Renaissance". GOOD: a row called "The Second Renaissance" with a `Week` column holding 1. Rows you ADD to an existing table follow this rule even when the rows already there break it — a bad convention is not a pattern to copy, so a table of "Week 1" / "Week 2" gets your row named for what ships, never "Week 3"; leaving their existing names alone (you never rename a row unasked) is not permission to add a matching bad name. There is no length limit — names wrap in the table.
- Tables inside notes (the user-initiated case — "pull these posts out of my note into a table"): pass `embedInNoteId` to `eden_create_table` and the table is rendered as a live, editable block inside that note, with `replaceInNoteText` naming the passage it stands in for (the bullet list or markdown pipe table it was built from) — that passage disappears and the table takes its place, so don't also call `eden_update_note` to strip it. Without `replaceInNoteText` the table lands at the end of the note. The note keeps the thinking (strategy, analysis, next steps); the table holds the records. An `item` column holds ONE workspace item id (boards count — a board id renders as a board chip that opens the board), and it must be a REAL id you got from a search or read — never a URL, a title, or an id you composed, because a bad id paints a chip nobody can click. A row can also BE a library item rather than point at one: such a row takes that item's title, and the title belongs to the item, so rename the ITEM rather than the row.
- Recurring rows: a task that comes back is ONE row carrying a repeat rule on a DATE column, never one row per occurrence. `eden_read_table` returns `repeats` (date property id → `{freq, interval, from}`) on rows that repeat; marking such a row done ROLLS its date forward and leaves the row open, so never "mark done and add the next one". Set or clear a rule with the `repeat` field on `eden_add_table_rows` / `eden_update_table_rows` — `{"Due": {"every": "week", "interval": 2}}`, a bare unit string (`{"Due": "day"}`), or `{"Due": null}` to stop. `from: "completion"` counts from when it was ticked off (water the plants every 3 days) instead of from the due date.

Most workspace-scoped tools need a `workspaceId`. If you don't have one and there's no resolved default, you'll get `status: "missing-workspace"` — call `eden_list_workspaces` and pass an explicit `workspaceId`. Always pass `limit` on list calls and paginate rather than pulling everything.

## Generated media

Eden exposes **no AI media generation over MCP** — image and carousel creation
happen inside the Eden app. `eden_study_top_carousels` is the one carousel tool
here, and it is research-only: a slide-by-slide teardown of proven carousels to
study structure and text. To attach media to a scheduled post, upload it with
the scheduling media tools (see <scheduling.md>).

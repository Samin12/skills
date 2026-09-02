# Eden Custom AI

A Custom AI is a workspace-scoped configured assistant with durable instructions,
starter prompts, and an authoritative source catalog. Eden exposes Custom AI over
MCP as tools and as native MCP prompts (`/eden-<name>` in clients that support the
prompts primitive).

## Discover and run

1. Call `eden_list_custom_ai({ workspaceId })` to discover the workspace catalog.
2. Call `eden_get_custom_ai({ customAIId, workspaceId })` to load the current
   instructions, revision, visibility, and source catalog.
3. Adopt `instructionsMarkdown` for the task. Resolve only sources relevant to
   the request:
   - board/item locators: Eden workspace read tools;
   - creator/social-post locators: Eden social-intelligence tools;
   - brand locators (ad libraries): `eden_get_brand_ads` with the brand's name
     (narrow with `eden_search_ads` + the locator's `advertiserId`);
   - managed marketplace knowledge: `eden_search_custom_ai_knowledge` (no query
     = document catalog; with a query = search inside), then
     `eden_read_custom_ai_knowledge`.

Selecting `/eden-<name>` performs the same definition load and seeds the current
instructions automatically. The slash-command catalog refreshes as Custom AI are
created, renamed, or archived.

## Create

Before authoring a definition from scratch, call
`eden_get_custom_ai_builder_guide` and follow it. It returns the in-app Custom
AI Builder's method (variant `"custom_ai"` for general experts, `"voice"` for
voice/mentor assistants) plus notes mapping its web-native tool names onto the
MCP surface. Skipping the guide produces thin, under-sourced assistants.

`eden_create_custom_ai` is a real write. Pass a complete `definition`, optional
permission-checked `sources`, and visibility. Use exact Eden item/board ids and
normalized creator references; never invent locators. Prefer:

- `visibility: "workspace"`;
- `workspaceAccess: "selected"`;
- source `activation: "retrieve"`;
- `memoryMode: "off"`;

unless the user explicitly needs broader behavior.

## Update

Call `eden_get_custom_ai` immediately before `eden_update_custom_ai`. Merge the
requested changes into the complete definition and pass its current `revision` as
`expectedRevision`. A `revision_conflict` means another editor saved first: read
again, merge once, and retry once. Managed marketplace installs are read-only.

`eden_update_custom_ai` replaces the definition only — attached sources are
preserved untouched. To change knowledge, use the sources tool below.

## Manage attached knowledge

`eden_manage_custom_ai_sources` adds, edits, or removes ONE attached source per
call on an editable Custom AI:

- `action: "add"` + `source` — attach a new board/item/creator/brand/social-post
  source (a `brand` source is `{platform: "meta"|"tiktok", advertiserId, name}`;
  resolve the exact advertiserId with `eden_get_brand_ads` first — it tracks
  new brands automatically);
- `action: "update"` + `sourceId` + `source` — replace one source's full
  definition (label, roles, activation, description, trigger — not a patch);
- `action: "remove"` + `sourceId` — detach one source.

Every action needs the current `expectedRevision` and bumps the revision, so
call `eden_get_custom_ai` first (it also returns the `sourceId`s) and re-read
between consecutive actions. A `source_already_attached` conflict means a
source with the same locator already exists: update that source instead of
adding a duplicate. Uploaded-file knowledge is an in-app feature; over MCP,
save the material as a workspace note first (`eden_create_note`), then attach
it as an item source.

## Delete

`eden_delete_custom_ai` archives an editable Custom AI. Confirm with the user,
read the latest revision, then call with `confirmed: true`. Do not retry a
conflict blindly. Managed installs are removed through their installation
controls rather than this tool.

## Removed legacy surface

Eden no longer exposes Skills/Prompts or Identities over MCP. Do not call or
suggest `eden_*_skill`, `eden_*_prompt`, identity, or voice tools. Portable
`SKILL.md` import/export is not part of the Eden MCP surface.

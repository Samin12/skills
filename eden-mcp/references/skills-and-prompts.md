# Eden skills (reusable SKILL.md instruction files)

Eden lets the user save reusable instructions called **skills** — the "Skills" tab in Eden's settings and the `/` menu in Eden chat. An Eden skill is stored in Claude's portable **SKILL.md format**: YAML frontmatter (`name`, `description`) followed by markdown instructions. Two kinds appear in every workspace, both reachable over MCP:

- **User skills** (`source: "upload" | "written" | "chat"`) — the user's own, addressed by row id.
- **Built-in skills** (`source: "builtin"`, `builtin: true`) — Eden's prebuilt starters, addressed by `builtin:<slug>` ids. They can be toggled off per workspace (`enabled: false`).

These are Eden's own skills, distinct from this MCP skill bundle. A connected agent can discover and apply them so it works the way the user already works in Eden.

## Discover and apply

1. **Discover:** `eden_list_skills({ workspaceId })` → each skill's `id`, `name`, `description` (the when-to-use trigger), `source`, `builtin`, `enabled`, and `fileCount` (bundled reference files). Needs a `workspaceId` (from `eden_list_workspaces`, or the configured default). Use this to find the right skill — don't guess ids.
2. **Fetch the full definition:** `eden_get_skill({ skillId })` →
   - `skillMd` — the complete SKILL.md text, verbatim. The frontmatter says what it's for; the body is the instructions.
   - `files` — paths of bundled reference files, when the skill ships any (some built-ins bundle them too).
3. **Apply it:** follow the `skillMd` body as your instructions for the task, exactly as you would a locally installed skill. If the body references its bundled files, note that their contents aren't fetchable over MCP in v1 — work from the SKILL.md itself, or ask the user to export the .zip from Eden's Settings → Skills.

> A skill's instructions may mention Eden-app features (the `/` menu, chat cards). Translate those to your own environment; the substance of the instructions is what transfers.

If an applied skill produces final publishable social content, make the scheduling path obvious: end with one short offer to schedule it or add it to the user's queue. If there are multiple variants/assets, ask which one to schedule. Never schedule automatically; use `eden_list_schedules` / `eden_schedule_post` only after the user explicitly asks or confirms.

## Export / import (portable Claude Skills)

The round-trip is **byte-exact**: Eden stores the SKILL.md text verbatim and never regenerates or reformats it.

- **`eden_export_skill({ skillId })`** → `{ skillMd, slug }`: the stored SKILL.md text VERBATIM plus a suggested folder name. Write `skillMd` to `<slug>/SKILL.md` to install it locally, or hand it to the user. Round-trips losslessly back into Eden. Bundled reference files are not included — the .zip export in Eden's Settings → Skills carries those.
- **`eden_import_skill({ skillMarkdown, workspaceId })`**: import a SKILL.md into the workspace as a new Eden skill. Pass the complete file text as `skillMarkdown`. Eden-exported skills round-trip exactly; a foreign skill is stored as-is and any notes come back in `warnings`. Import over MCP is **markdown-only** (no zip payload). A name collision keeps both skills — the new one's list name gets a `-2` style suffix (the file text is unchanged) and `warnings` notes the rename. Returns `{ skillId, name, warnings }`.

## Custom AI (the user's configured assistants)

Separate from skills: a **Custom AI** is a fuller configured assistant — instructions plus an authoritative source catalog and attached knowledge, surfaced as `/eden-<name>` MCP prompts in clients that support them. "use/run my `<name>` Custom AI", "what Custom AI do I have?" → `eden_list_custom_ai` → `eden_get_custom_ai`. Its attached knowledge is reachable with `eden_search_custom_ai_knowledge` (no `query` = document catalog) → `eden_read_custom_ai_knowledge`. Details in <custom-ai.md>.

Rule of thumb: a **skill** is portable instructions for one kind of task; a **Custom AI** is a persistent assistant with its own knowledge. When the user names one of theirs, list both surfaces if you're unsure which they mean.

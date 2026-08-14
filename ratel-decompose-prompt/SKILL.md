---
name: ratel-decompose-prompt
description: "Break a bloated, monolithic agent system prompt into a lean stable core plus extracted Ratel-style skills. Use when a prompt is too long or does too many things, to extract or factor procedures into skills, decompose or split a prompt, cut per-turn token cost, or `/ratel-decompose-prompt`. Writes a markdown decomposition plan (lean core, skill inventory, per-skill SKILL definitions, registration wiring) to repo/.ratel/ without rewriting the prompt or code. Reached from /ratel-assessment's Prompt Decomposition dimension; pairs with /ratel-tune-definitions."
allowed-tools: Bash Read Write Edit Glob Grep Agent WebFetch
---
# /ratel-decompose-prompt — split a monolithic system prompt into a lean core + retrievable skills

A system prompt that has grown to thousands of tokens is paying for every responsibility on every turn. Most of it is dormant most of the time: the refund-flow procedure sits in context while the user asks about shipping; the SQL-generation playbook loads while the user is editing a form. Ratel's skills mechanism exists precisely for this — a procedure becomes a retrievable playbook that only enters context when a turn calls for it. This skill is the fix that turns one giant prompt into a small stable core plus a SkillCatalog of extracted skills.

The deliverable is a markdown plan at `<repo>/.ratel/ratel-decompose-prompt.md`: the proposed lean core prompt, a skill inventory table, and a per-skill SKILL definition ready to drop into a Ratel-managed skills folder. The plan is implementable by the customer; this skill does not rewrite their prompt in place.

This skill is the fix that the [`/ratel-assessment`](../ratel-assessment/SKILL.md) "Prompt Decomposition" dimension routes to. It pairs with:

- **[`/ratel-tune-definitions`](../ratel-tune-definitions/SKILL.md)** — every skill you extract needs a retrievable `description` and `tags`. The decomposition produces the skills; tune-definitions sharpens their wording so `search_capabilities` actually surfaces them. Run it after this one on the extracted set.
- **[`/ratel-assessment`](../ratel-assessment/SKILL.md)** — the front-door audit that identifies an over-stuffed prompt and points here.

## Philosophy

Three rules. Break any of them and you've either moved bloat around without removing it, or you've gutted the prompt's stable contract and made the agent unreliable.

1. **The core prompt keeps what must hold every turn; skills hold what's situational.** Stable role, safety rules, and the output-format contract stay in the core — the model must never be without them. Recurring procedures, task-specific playbooks, and few-shot examples are situational and belong in skills. The test for each section: "if this is absent on an unrelated turn, does the agent become unsafe or off-contract?" If yes, it stays in core. If no, it's a skill candidate.
2. **A skill must be self-contained and worth retrieving.** An extracted skill is loaded cold via `get_skill_content` with no surrounding prompt context. If a section only makes sense glued to three other sections, it's one skill, not four. Don't shatter a coherent procedure into fragments that can't stand alone.
3. **Retrievability is a design constraint, not an afterthought.** A skill that never gets surfaced is dead weight in the catalog and a hole in the agent's behavior. Every extracted skill must carry a `description` and `tags` that match the natural-language intent of the turns that need it. If you can't write triggers for it, it probably belongs in the core or doesn't deserve to be a skill.

## Workflow

### Step 1 — Locate and measure the system prompt(s)

Find every system prompt and estimate what it costs per turn. Prompts hide in inline strings, template files, prompt-management services, and per-agent constants.

```bash
# Manifests (drives stack + where prompts tend to live)
test -f package.json && jq -r '.dependencies // {}, .devDependencies // {} | keys[]' package.json | sort -u
test -f pyproject.toml && head -200 pyproject.toml

# System-prompt surfaces
grep -rEn 'system:|role:\s*["'\'']system|systemPrompt|SYSTEM_PROMPT|system_prompt|instructions:|messages\.create|ChatPromptTemplate|SystemMessage' \
  --include='*.ts' --include='*.tsx' --include='*.js' --include='*.py' --include='*.md' --include='*.txt' \
  | head -100

# Prompt files by convention
find . -type f \( -name '*.prompt' -o -name '*prompt*.md' -o -name '*prompt*.txt' \) -not -path '*/node_modules/*' | head -50
```

For each prompt found, estimate token weight (roughly characters ÷ 4, or `wc -c` ÷ 4). Note which prompts are largest and which load on every turn vs only on certain paths. If you find no system prompt at all, use the [honest skip path](#honest-skip-path).

### Step 2 — Fetch up-to-date Ratel docs

Ratel ships fast — don't recite the skills API or the Skill data model from memory; pull the current state at runtime, in this order:

1. **Context7 (preferred)** — via Ratel Local, the local MCP server (call `search_capabilities` to find Context7's resolve-library-id / get-library-docs tools, then `invoke_tool`), or a directly-configured Context7 MCP. Resolve `ratel-ai/ratel` and pull the SDK + skills docs.
2. **docs.ratel.sh (fallback)** — WebFetch `https://docs.ratel.sh/llms.txt` (page map) then `https://docs.ratel.sh/llms-full.txt` (full text), or the specific pages `https://docs.ratel.sh/docs/core/agent-skills`, `https://docs.ratel.sh/docs/core/sdks/typescript`, `https://docs.ratel.sh/docs/core/sdks/python`.
3. **GitHub raw / installed package (last resort)** — `https://raw.githubusercontent.com/ratel-ai/ratel/main/README.md` and `src/sdk/ts/README.md` / `src/sdk/python/README.md`; or the customer's pinned `node_modules/@ratel-ai/sdk/README.md` / Python `ratel_ai` package README.

Capture three things: the current shipped version, the `SkillCatalog` / `Skill` / `searchCapabilitiesTool` / `getSkillContentTool` API shape, and the Skill data model fields. If the fetched docs disagree with the patterns in [`references/decomposition-patterns.md`](references/decomposition-patterns.md), trust the docs and flag the file for an update in the plan.

### Step 3 — Identify decomposition seams

Read the prompt(s) and segment them into sections by responsibility. The seams to look for, and which side they fall on:

| Section type | Disposition | Why |
| --- | --- | --- |
| Stable role / persona | **Stay in core** | Must hold every turn; cheap; defines the agent |
| Safety / refusal / policy rules | **Stay in core** | Absence is a correctness/safety regression |
| Output-format contract (schema, tone, structure) | **Stay in core** | The model must honor it on every response |
| Recurring multi-step procedures | **Extract to skill** | Situational; large; only relevant on matching turns |
| Task-specific playbooks (refund flow, SQL gen, triage) | **Extract to skill** | Each is one self-contained skill |
| Few-shot examples | **Extract to skill** | Bulky; pull the examples for the matching task into that task's skill |
| Tool usage docs / per-tool how-to | **Extract to skill** (or fold into the tool's own description — see `/ratel-tune-definitions`) | Surfaced alongside the tool when the tool matches |

Build a section inventory: for each section, its approximate token weight, its disposition, and (for extract candidates) a one-line statement of the task it serves. Use [`references/decomposition-patterns.md`](references/decomposition-patterns.md) for the full catalog and a worked before/after example.

### Step 4 — Define each extracted skill against the data model

For every extract candidate, specify the full Ratel Skill data model. Indexed for retrieval are `name`, `description`, and `tags` only — so these carry the retrievability. `body`, `tools`, and `metadata` are not indexed.

- **`id`** — stable slug, e.g. `refund-flow`.
- **`name`** — short human label; indexed.
- **`description`** — pushy, multi-phrase, names the natural-language triggers of turns that need it; indexed. This is the primary retrieval surface.
- **`tags`** — fold in both author labels ("billing", "support") AND task phrases the user actually types ("issue a refund", "customer wants money back"); indexed. Terse intent prompts match here.
- **`tools`** — the ids of tools the skill's body calls. A typed dependency edge: when the skill matches, `search_capabilities` surfaces these tools in the tools bucket. Not indexed.
- **`metadata`** — project context for push-path ranking/boosting, e.g. `{"stacks": ["react"]}`. Not indexed.
- **`body`** — the actual playbook text lifted from the prompt section, made self-contained. The dispatch payload, loaded on demand via `get_skill_content`. Not indexed.

See [`references/decomposition-patterns.md`](references/decomposition-patterns.md) for field-by-field authoring guidance tied to Ratel's hybrid retrieval: the lexical arm rewards descriptive names, tags, and exact trigger terms, while the semantic arm matches paraphrase and intent — so clear, multi-phrase descriptions feed both. Cross-link the description/tags work to [`/ratel-tune-definitions`](../ratel-tune-definitions/SKILL.md).

### Step 5 — Write the lean core prompt

Assemble the stay-in-core sections into the new core prompt. It should contain only the role, safety/policy, and output contract — plus a short pointer that the agent has skills available and should retrieve them when a turn needs a procedure. Estimate the new core's token weight and state the reduction vs the original.

### Step 6 — Show the registration wiring

Show how to register the extracted skills and wire the capability tools (`search_capabilities`, `get_skill_content`), in both TS and Python code shapes (adapt to the fetched API).

TypeScript (`@ratel-ai/sdk`):

```ts
import { SkillCatalog, Skill, searchCapabilitiesTool, getSkillContentTool } from "@ratel-ai/sdk";

const skillCatalog = new SkillCatalog();
skillCatalog.register(new Skill({
  id: "refund-flow",
  name: "Refund flow",
  description: "Process a customer refund end to end. Use when the user wants money back, disputes a charge, or asks to cancel and refund an order.",
  tags: ["billing", "support", "issue a refund", "customer wants money back"],
  tools: ["lookup_order", "issue_refund"],
  metadata: { stacks: ["node"] },
  body: "/* the refund playbook lifted from the old prompt, made self-contained */",
}));

// Skills are ranked alongside tools; pass the skill catalog into the capability tools.
const tools = {
  search_capabilities: searchCapabilitiesTool(toolCatalog, skillCatalog),
  get_skill_content: getSkillContentTool(skillCatalog),
  // invoke_tool: invokeToolTool(toolCatalog),
};
```

Python (`ratel-ai`):

```python
from ratel_ai import SkillCatalog, Skill, search_capabilities_tool, get_skill_content_tool

skill_catalog = SkillCatalog()
skill_catalog.register(Skill(
    id="refund-flow",
    name="Refund flow",
    description="Process a customer refund end to end. Use when the user wants money back, disputes a charge, or asks to cancel and refund an order.",
    tags=["billing", "support", "issue a refund", "customer wants money back"],
    tools=["lookup_order", "issue_refund"],
    metadata={"stacks": ["python"]},
    body="""...refund playbook, self-contained...""",
))

tools = {
    "search_capabilities": search_capabilities_tool(tool_catalog, skill_catalog),
    "get_skill_content": get_skill_content_tool(skill_catalog),
}
```

Note the two surfacing mechanisms in the plan:

- **PULL** — `search_capabilities` returns a ranked skills bucket alongside tools; the agent retrieves a skill when doing tool-adjacent work and loads its body with `get_skill_content`. This is the default for skills extracted from tool-using procedures.
- **PUSH** — a `UserPromptSubmit` preload hook injects a clear-winner skill for no-tool intent prompts. Experimental and gated by a clear-winner rule; recommend it only for skills that map cleanly to an unambiguous intent, and lean on `metadata` for push-path boosting.

Skills live in a Ratel-managed folder (default `~/.ratel/skills/`). State where the customer's extracted skills should be written.

### Step 7 — Write the plan

Output to `<repo>/.ratel/ratel-decompose-prompt.md`. Sections, in order:

1. **Summary** — original prompt locations and token weight, proposed core token weight, count of skills extracted, expected per-turn reduction. Six bullets max.
2. **Up-to-date docs reference** — Ratel version and docs source the plan was written against.
3. **Proposed lean core prompt** — the full rewritten core, ready to paste.
4. **Skill inventory** — a table: skill id, name, source section, token weight extracted, surfacing mode (PULL/PUSH).
5. **Per-skill SKILL definitions** — for each, all data model fields filled in.
6. **Registration wiring** — the TS/Python snippets adapted to the customer's stack and skills-folder location.
7. **Next step** — point to [`/ratel-tune-definitions`](../ratel-tune-definitions/SKILL.md) to sharpen the extracted skills' descriptions and tags for retrieval.

Print the inventory table inline in chat and tell the user the file path. Do not paste the full plan body into chat.

## Honest skip path

Two skip cases:

1. **No system prompt found.** If Step 1 turns up no system/instruction prompt anywhere, stop. Tell the user what you searched and ask them to point you at the prompt if it lives somewhere unusual. Don't invent a decomposition for a prompt you can't see.
2. **Prompt already short or well-factored.** If the prompt is small (roughly under ~800 tokens) or already cleanly split into a thin core plus externalized procedures, say so and stop. Decomposing a tight prompt adds retrieval overhead and a catalog to maintain for no per-turn saving. Note the threshold and suggest revisiting if the prompt grows.

## Reference files

- [`references/decomposition-patterns.md`](references/decomposition-patterns.md) — the catalog of common prompt sections and their stay-in-core vs extract-to-skill mapping, a worked before/after example, and field-by-field Skill authoring guidance tied to Ratel's hybrid retrieval.

Reads from (does not duplicate):

- [`../ratel-tune-definitions/references/definition-rubric.md`](../ratel-tune-definitions/references/definition-rubric.md) — the description/tags rubric the extracted skills should be measured against.

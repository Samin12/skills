---
name: ratel-tune-definitions
description: "Audit a codebase's tool and skill definitions against a failure-mode rubric and write a markdown tuning plan with per-definition before/after rewrites that make them retrievable by Ratel's hybrid lexical + semantic index and usable by the model. Use when the model picks the wrong tool, tools never get picked, descriptions are too long/vague/anemic, to fix near-duplicates, tighten schemas/enums/param names, clean up the tool catalog, or `/ratel-tune-definitions`. Fetches live Ratel docs; writes to repo/.ratel/ without editing tool or skill code. The fix /ratel-assessment's Definition Quality dimension routes to; runs after /ratel-decompose-prompt."
allowed-tools: Bash Read Write Edit Glob Grep Agent WebFetch
---
# /ratel-tune-definitions — make tool & skill definitions retrievable and usable

Ratel retrieves tools and skills over their definitions — a lexical (BM25) index rewards descriptive names, parameter names, enum values, and exact trigger terms, while, in semantic/hybrid mode, a semantic index matches the description's meaning — and the model then decides which of the top-K hits to call. Both steps fail on bad definitions: a vague description surfaces in neither arm; a bloated one drowns its neighbors; two near-duplicate tools split the model's confidence; a loose schema lets the model call a tool wrong. This skill is the manual tuning pass that fixes those — definition by definition, with concrete before/after rewrites.

The deliverable is a markdown plan at `<repo>/.ratel/ratel-tune-definitions.md`: a per-definition before/after table and a prioritized fix list. The plan is implementable by the customer; this skill does not edit their tool or skill code in place.

This skill is the fix that the [`/ratel-assessment`](../ratel-assessment/SKILL.md) "Definition Quality" dimension routes to. It pairs with:

- **[`/ratel-decompose-prompt`](../ratel-decompose-prompt/SKILL.md)** — that skill extracts skills from a prompt; this one sharpens their `description` and `tags` so they're actually retrievable. Run this after a decomposition on the extracted set.
- **[`/ratel-assessment`](../ratel-assessment/SKILL.md)** — the front-door audit that flags weak definitions and points here.

LLM-driven suggestions — automated description rewrites, missing-parameter detection, and redundant-tool merge proposals — are the direction of Ratel Cloud's suggestions engine (Coming Soon), which derives ranked suggestions server-side from your exported telemetry. This skill is the manual version of that pass; note in the plan which fixes the customer could defer to that engine once it ships.

## Philosophy

Three rules. Break any of them and you've either made the catalog prettier without making it more retrievable, or you've optimized for retrieval at the cost of the model getting confused.

1. **Definitions serve two readers — the index and the model — and a fix must satisfy both.** The lexical index reads names, descriptions, parameter names, and enum values (ADR-0004's schema-aware projection strips JSON-Schema structure); in semantic/hybrid mode the semantic index embeds the description's meaning. The model reads the description to decide *when* to call and the schema to decide *how*. A description packed with keywords but no "when to use" may satisfy the lexical arm yet hurts the semantic arm and the model. Every rewrite must improve both readers.
2. **Tighter beats longer.** The fix for a bad description is rarely more words. Anemic descriptions need a "what + when" sentence, not a paragraph; bloated ones need cutting. Schemas need the loosest constraint removed (`additionalProperties: true`, bare `{}`), not more prose explaining them.
3. **No invented problems.** If a definition is already tight, leave it and say so. Don't rewrite a clean description to look busier, don't split a tool that isn't actually a duplicate, don't add enums to a field whose value space is genuinely open. The before/after table only lists definitions that change.

## Workflow

### Step 1 — Inventory every tool and skill definition

Find every place tools and skills are declared and capture the full definition surface: name, description, parameter names, enums, schema, and (for skills) tags.

```bash
# Manifests
test -f package.json && jq -r '.dependencies // {}, .devDependencies // {} | keys[]' package.json | sort -u
test -f pyproject.toml && head -200 pyproject.toml

# Tool definition sites
grep -rEn 'defineTool|createTool|registerTool|new Tool|@tool\b|@function_tool\b|tools:\s*\{|tools:\s*\[|inputSchema|parameters:\s*\{|catalog\.register|McpServer\(' \
  --include='*.ts' --include='*.tsx' --include='*.js' --include='*.py' | head -100

# Skill definition sites + Ratel skills folder
grep -rEn 'new Skill|Skill\(|SkillCatalog|skillCatalog\.register' \
  --include='*.ts' --include='*.tsx' --include='*.js' --include='*.py' | head -50
ls ~/.ratel/skills/ 2>/dev/null
```

For each tool capture: id/name, description (and its rough token length), every parameter name, every enum, and the schema's looseness (`additionalProperties`, empty objects, missing `required`). For each skill capture: name, description, tags. If you find no tools and no skills, use the [honest skip path](#honest-skip-path).

### Step 2 — Fetch up-to-date Ratel docs

Ratel ships fast on the 0.4.x line — don't recite the indexing rules or the data model from memory; pull the current state at runtime, in this order:

1. **Context7 (preferred)** — via Ratel Local (call `search_capabilities` to find Context7's resolve-library-id / get-library-docs tools, then `invoke_tool`), or a directly-configured Context7 MCP. Resolve `ratel-ai/ratel` and pull the SDK + skills docs.
2. **docs.ratel.sh (fallback)** — WebFetch `https://docs.ratel.sh/llms.txt` (page map) then `https://docs.ratel.sh/llms-full.txt` (full text), or the specific pages `/docs/core/sdks/typescript`, `/docs/core/sdks/python`, `/docs/core/skills-suite`.
3. **GitHub raw / installed package (last resort)** — `https://raw.githubusercontent.com/ratel-ai/ratel/main/README.md` and `src/sdk/ts/README.md` / `src/sdk/python/README.md`; or the customer's pinned `node_modules/@ratel-ai/sdk/README.md` / Python `ratel_ai` package README.

Confirm two things against the docs: what the lexical index tokenizes and how the semantic arm ranks meaning (so your rewrites target the right fields) and the current Skill data model. If the docs disagree with [`references/definition-rubric.md`](references/definition-rubric.md), trust the docs and flag the file for an update in the plan.

### Step 3 — Diagnose against the failure modes

Run every definition from Step 1 through the rubric in [`references/definition-rubric.md`](references/definition-rubric.md). The concrete failure modes:

| Failure mode | Detection heuristic |
| --- | --- |
| Bloated description | Longer than ~300 tokens; multi-paragraph; restates the schema in prose |
| Anemic description | Shorter than ~8 tokens, or names the tool instead of describing it ("Order tool") |
| Missing "when to use" | Says what it does but not when to call it; collides with sibling tools |
| Near-duplicate tools | Two+ tools whose descriptions/names overlap heavily (e.g. `get_user`, `fetch_user`, `lookup_user`) |
| Loose / missing schema | `additionalProperties: true`, bare `{}`, no `required`, untyped params |
| Un-descriptive parameter names | `arg1`, `data`, `input`, `x` — invisible to the lexical index and meaningless to the model |
| Missing enums | A finite-value string field (`status`, `region`, `mode`) left as free `string` |
| Verbose tool output | The tool returns large unbounded blobs the model must re-read each turn |

For each flagged definition, record the failure mode(s) and the evidence (the actual text, length, or schema fragment).

### Step 4 — Explain why each fix matters

For every fix, the plan states the dual rationale so the customer understands the change isn't cosmetic:

- **For retrieval** — the lexical index tokenizes names, descriptions, parameter names, and enum values (structure is stripped), while the semantic index embeds the description's meaning. So renaming `arg1` → `customer_email`, adding the enum values `["pending","shipped","delivered"]`, and adding trigger phrasings all add retrievable terms to the lexical arm; a clear natural-language "what + when" also lets the semantic arm match paraphrases the user never worded exactly. A tool that's neither described in the user's words nor clear in meaning will not surface.
- **For model selection** — once a tool is in the top-K, the model picks by reading the description's "when to use" and calls correctly by reading the schema. Near-duplicates split confidence; loose schemas invite malformed calls; bloated descriptions crowd the context window that tool selection is "replace by default" trying to keep lean.

### Step 5 — Produce concrete rewrites

For each flagged definition, write the before → after. Use the rubric's recipes and the "good description" template:

> `<one sentence: what it does>. Use when <one line: when to call it>.`

- **Descriptions** — apply the template; add distinct trigger phrasings without keyword-stuffing.
- **Names / parameter names** — rename to descriptive terms the lexical index can tokenize.
- **Enums** — replace free-string finite fields with explicit enum value lists (the values are indexed and constrain the model).
- **Schemas** — set `additionalProperties: false`, add `required`, type every param.
- **Near-duplicates** — propose a merge (one tool + an enum/param) or a sharpened "when to use" that disambiguates the survivors.
- **Verbose outputs** — propose an `outputSchema` or a projection/summary so the tool returns only what the model needs.

For **skills**, also tune `description` and `tags` for retrievability exactly as in the rubric — fold author labels AND task phrases into `tags`, and apply the description template. Cross-link this to [`/ratel-decompose-prompt`](../ratel-decompose-prompt/SKILL.md), whose extracted skills are the common input here.

### Step 6 — Prioritize

Order the fix list by impact:

1. **Near-duplicate tools** and **anemic descriptions** — these cause wrong/empty retrieval; highest impact.
2. **Missing "when to use"** and **missing enums** — cause wrong selection and malformed calls.
3. **Loose schemas** and **un-descriptive parameter names** — correctness and retrievability.
4. **Bloated descriptions** and **verbose outputs** — context efficiency; lower urgency but compounding at scale.

### Step 7 — Write the plan

Output to `<repo>/.ratel/ratel-tune-definitions.md`. Sections, in order:

1. **Summary** — counts: tools/skills inventoried, definitions flagged, by failure mode. Six bullets max.
2. **Up-to-date docs reference** — Ratel version and docs source the plan was written against.
3. **Before/after table** — one row per changed definition: id, failure mode(s), before, after. The load-bearing section.
4. **Schema tightenings** — the per-tool schema diffs (additionalProperties, required, enums, types).
5. **Near-duplicate resolutions** — proposed merges or disambiguations.
6. **Prioritized fix list** — ordered per Step 6, each item one line.
7. **Roadmap note** — which fixes Ratel Cloud's suggestions engine (Coming Soon) could automate later.

Print the prioritized fix list inline in chat and tell the user the file path. Do not paste the full plan body into chat.

## Honest skip path

Two skip cases:

1. **No tools or skills found.** If Step 1 turns up no tool or skill definitions, stop. Tell the user what you searched and ask them to point you at the catalog if it lives somewhere unusual. Don't tune definitions you can't see.
2. **Catalog is tiny or already tight.** If there are only a handful of definitions and they already pass the rubric — good "what + when" descriptions, tight schemas, descriptive params, no duplicates — say so and stop. Under a small, well-described catalog the retrieval problem this skill solves barely exists. List what you checked so the customer can see it wasn't a skim, and suggest revisiting as the catalog grows.

## Reference files

- [`references/definition-rubric.md`](references/definition-rubric.md) — per failure mode: detection heuristic, rewrite recipe, and a before/after example; plus the "good description" template and parameter/enum naming guidance tied to how the lexical and semantic index read each field.

Reads from (does not duplicate):

- [`../ratel-decompose-prompt/references/decomposition-patterns.md`](../ratel-decompose-prompt/references/decomposition-patterns.md) — the Skill data model and field-by-field authoring context for the skills this pass tunes.

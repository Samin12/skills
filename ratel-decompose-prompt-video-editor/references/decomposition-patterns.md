# Prompt decomposition patterns

The catalog of common system-prompt sections, how each maps (stay-in-core vs extract-to-skill), a worked before/after example, and field-by-field Skill authoring guidance. Read this **after** Step 2 of the skill — i.e., after you have the up-to-date Ratel docs in hand. If anything here disagrees with the latest docs, trust the docs and flag this file for an update.

## The mapping catalog

Each row is a section type you'll commonly find wedged into one monolithic prompt, the side it falls on, and the reasoning. The deciding question is always: **if this section is absent on an unrelated turn, does the agent become unsafe or off-contract?** Yes → core. No → skill candidate.

| Section type | Disposition | Reasoning |
| --- | --- | --- |
| Role / persona ("You are a senior support agent...") | Stay in core | Defines the agent; small; must hold every turn |
| Safety, refusal, policy, compliance rules | Stay in core | Absence is a safety/correctness regression on any turn |
| Output-format contract (JSON schema, tone, structure, citation rules) | Stay in core | The model must honor it on every response |
| Global tool-use etiquette ("always confirm before destructive actions") | Stay in core | Cross-cutting; applies regardless of which tool is used |
| Recurring multi-step procedures (onboarding flow, escalation ladder) | Extract to skill | Situational, bulky, only relevant on matching turns |
| Task-specific playbooks (refund flow, SQL generation, ticket triage) | Extract to skill | Each is one self-contained skill |
| Domain knowledge dumps (product catalog facts, policy tables) | Extract to skill | Reference material; pull in only when the task touches it |
| Few-shot examples | Extract to skill | Bulky; attach the examples for a task to that task's skill body |
| Per-tool how-to / tool documentation | Extract to skill, or fold into the tool's own `description` | Surfaces with the tool when the tool matches; see `/ratel-tune-definitions` |
| Edge-case handling for one narrow feature | Extract to skill | Dead weight on every other turn |

### Splitting rules

- **One coherent procedure = one skill.** Don't shard a flow into per-step fragments that can't stand alone. A skill body is loaded cold via `get_skill_content` with no surrounding prompt.
- **Co-locate examples with their procedure.** Few-shot examples for the refund flow go in the refund-flow skill body, not a separate "examples" skill.
- **If two candidates always fire together, merge them.** Two skills that are never retrieved independently are one skill.
- **If a candidate can't get a description + tags written for it, reconsider.** It's either too vague to retrieve (fold into core) or not really a distinct task.

## Worked before/after example

### Before — one monolithic prompt (~2,400 tokens, paid every turn)

```
You are Acme's customer-support agent. Be concise and never reveal internal pricing logic.    [role + safety]
Always respond in JSON: { "reply": string, "next_action": string|null }.                       [output contract]

== Refunds ==
When a customer wants a refund: 1) look up the order with lookup_order, 2) verify it's within
the 30-day window, 3) if eligible call issue_refund, 4) confirm the amount and ETA. If outside
the window, offer store credit instead. Example: "I want my money back for order 1234" → ...     [procedure + example]

== Subscription changes ==
When a customer changes plans: 1) fetch the current plan with get_subscription, 2) compute
proration, 3) call update_subscription, 4) explain the next bill. Example: ...                    [procedure + example]

== Shipping ==
For shipping questions, look up tracking with track_shipment and read back the latest status...   [procedure]

(...600 more lines of product catalog facts and ten more flows...)
```

### After — lean core (~250 tokens) + a SkillCatalog

Core prompt (stays loaded every turn):

```
You are Acme's customer-support agent. Be concise and never reveal internal pricing logic.
Always respond in JSON: { "reply": string, "next_action": string|null }.
When a request needs a specific procedure, retrieve the matching skill before acting.
```

Extracted skills (each surfaced on demand):

| Skill id | name | Source section | Surfacing |
| --- | --- | --- | --- |
| `refund-flow` | Refund flow | == Refunds == + example | PULL |
| `subscription-change` | Subscription change | == Subscription changes == + example | PULL |
| `shipping-status` | Shipping status | == Shipping == | PULL |
| `product-catalog` | Product catalog facts | catalog dump | PULL |

Per-turn cost drops from ~2,400 tokens to ~250 plus the one skill the turn actually needs.

## Field-by-field Skill authoring (tied to hybrid retrieval)

Ratel indexes `name`, `description`, and `tags` only; `body`, `tools`, and `metadata` are NOT indexed. Retrieval is hybrid: a lexical arm tokenizes those names, descriptions, and tags, and a semantic arm embeds the same text and matches on meaning. So the description and tags are the entire retrieval surface — write them both for the exact words the user types (lexical) and as clear natural language that captures the intent (semantic). Exact-keyword coverage still helps, but it is no longer the whole game: a well-phrased "what it does + when to use" now drives recall on its own.

- **`id`** — stable, lowercase, hyphenated slug (`refund-flow`). Never reuse an id; it's the handle `get_skill_content` and the `tools` edge resolve against.
- **`name`** — short human label (2-4 words), indexed. Use the plain task name, not a code symbol.
- **`description`** — the load-bearing field. Make it pushy and multi-phrase: one line of what the skill does, then several natural-language triggers the way a user would phrase them. "Process a customer refund end to end. Use when the user wants money back, disputes a charge, asks to cancel and refund, or says a charge was wrong." More distinct trigger phrasings = more retrievable, up to the point of keyword stuffing (don't repeat the same word ten times — the lexical arm saturates and the semantic arm gains nothing from repetition).
- **`tags`** — fold in BOTH author labels ("billing", "support", "post-purchase") AND raw task phrases ("issue a refund", "customer wants money back", "dispute a charge"). Tags catch terse intent prompts that the description's prose might miss. Keep them distinct from each other; near-duplicate tags add nothing.
- **`tools`** — list the exact tool ids the body calls (`["lookup_order", "issue_refund"]`). This is a typed dependency edge, not retrieval text: when the skill matches, `search_capabilities` surfaces these tools in the tools bucket so the agent can act. Keep it accurate — stale ids mean the agent retrieves a playbook for tools it can't reach.
- **`metadata`** — project context for push-path ranking/boosting, e.g. `{"stacks": ["react"]}`. Not indexed; used to bias which skill wins on the experimental PUSH path. Set `stacks` to the customer's actual stack so push ranking favors relevant skills.
- **`body`** — the playbook lifted from the prompt, rewritten to be self-contained (it loads with no surrounding prompt context). Spell out anything the old section relied on the rest of the prompt to supply. Keep the few-shot examples that belong to this task inside the body.

For the full description/tags rubric — what counts as anemic vs bloated, the "good description" template, and parameter/enum naming — defer to [`../../ratel-tune-definitions/references/definition-rubric.md`](../../ratel-tune-definitions/references/definition-rubric.md). This skill produces the skills; `/ratel-tune-definitions` sharpens their wording for retrieval.

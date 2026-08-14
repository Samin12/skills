# Definition tuning rubric

Per failure mode: the detection heuristic, the rewrite recipe, and a before/after example. Then the "good description" template and parameter/enum naming guidance tied to how the lexical and semantic index read each field. Read this **after** Step 2 of the skill — i.e., after you have the up-to-date Ratel docs in hand. If anything here disagrees with the latest docs, trust the docs and flag this file for an update.

## Why the fields matter (the lexical index, ADR-0004)

Ratel's **lexical** index tokenizes **names, descriptions, parameter names, and enum values**, and strips JSON-Schema structure (ADR-0004's schema-aware projection). In semantic/hybrid mode a **semantic** index also embeds each definition's description and ranks by meaning. So the lexical arm rewards those four surfaces and exact trigger terms, while the semantic arm rewards a clear natural-language "what + when" — a paraphrase the user never worded exactly can still match. Descriptive fields feed both arms. Tool selection is "replace by default": each turn the model sees only the top-K hits, not the full catalog, so a definition that doesn't retrieve is invisible that turn. Once retrieved, the model reads the description's "when to use" to choose and the schema to call correctly. Every rewrite below targets both readers.

## The "good description" template

```
<one sentence: what it does>. Use when <one line: when to call it>.
```

Optionally append distinct trigger phrasings the way a user would say them — without repeating the same keyword (the lexical arm saturates on repetition; the semantic arm gains nothing from a restated keyword). Example:

> Issue a refund for a customer order. Use when the user wants money back, disputes a charge, or asks to cancel and refund an order.

## Failure modes

### 1. Bloated description

- **Detect**: longer than ~300 tokens; multiple paragraphs; restates the schema in prose; includes implementation detail the model doesn't need.
- **Recipe**: cut to the template. Move "how it works internally" out entirely. Keep only what + when + the trigger phrasings. Let the schema carry the parameter detail.
- **Before**: `"This tool retrieves order information. It accepts an order ID which must be a valid UUID v4 string formatted with hyphens. It then queries the orders microservice over gRPC, which may take up to 2 seconds, and returns a JSON object containing the order status, line items, shipping address, billing address, payment method, and a full audit log of every state transition the order has undergone since creation..."` (≈120 words and growing)
- **After**: `"Look up an order's status, items, and addresses by order id. Use when the user asks about an existing order, its status, or its contents."`

### 2. Anemic description

- **Detect**: shorter than ~8 tokens, or it names the tool instead of describing it ("Order tool", "User helper", "Search").
- **Recipe**: apply the full template. Add the "when to use" the anemic version omitted — that's usually what's missing.
- **Before**: `"Refund tool."`
- **After**: `"Issue a refund for a customer order. Use when the user wants money back, disputes a charge, or asks to cancel and refund an order."`

### 3. Missing "when to use"

- **Detect**: describes what it does but gives the model no signal for *when* to call it; especially harmful when sibling tools do related things.
- **Recipe**: append a `Use when ...` clause that distinguishes it from its neighbors.
- **Before**: `"Updates a subscription."`
- **After**: `"Change a customer's subscription plan and apply proration. Use when the user upgrades, downgrades, or switches plans — not for cancellations (use cancel_subscription)."`

### 4. Near-duplicate tools

- **Detect**: two or more tools whose names/descriptions overlap heavily (`get_user`, `fetch_user`, `lookup_user`). They split retrieval scores across both arms and the model's confidence.
- **Recipe**: merge into one tool with a discriminating parameter or enum, OR keep the distinct ones but rewrite each "when to use" so they no longer overlap.
- **Before**: `get_user` ("Get a user."), `fetch_user_by_email` ("Fetch user by email."), `lookup_user` ("Look up a user.")
- **After**: one `find_user` — `"Find a user by id or email. Use when you need a user's profile, status, or contact info."` with `by: enum["id","email"]` and `value: string`.

### 5. Loose or missing schema

- **Detect**: `additionalProperties: true`, bare `{}` parameters, no `required` array, untyped params.
- **Recipe**: set `additionalProperties: false`, list `required`, type every property. Structure isn't indexed, but it's what stops the model making malformed calls.
- **Before**: `{ "type": "object", "additionalProperties": true }`
- **After**: `{ "type": "object", "properties": { "order_id": { "type": "string" } }, "required": ["order_id"], "additionalProperties": false }`

### 6. Un-descriptive parameter names

- **Detect**: `arg1`, `data`, `input`, `x`, `payload`. Invisible to the lexical index (param names ARE tokenized) and meaningless to the model.
- **Recipe**: rename to the domain term. The rename adds a retrievable token and tells the model what to pass.
- **Before**: `{ "arg1": { "type": "string" }, "data": { "type": "object" } }`
- **After**: `{ "customer_email": { "type": "string" }, "shipping_address": { "type": "object" } }`

### 7. Missing enums

- **Detect**: a string field with a finite known value space (`status`, `region`, `mode`, `priority`) left as free `string`.
- **Recipe**: add the explicit `enum`. The values are tokenized by the lexical index (so a query mentioning "refunded" can match a tool whose enum includes `refunded`) and they constrain the model to valid calls.
- **Before**: `{ "status": { "type": "string" } }`
- **After**: `{ "status": { "type": "string", "enum": ["pending", "shipped", "delivered", "refunded"] } }`

### 8. Verbose tool output

- **Detect**: the tool returns large unbounded blobs (full records, raw HTML, logs) the model re-reads every turn.
- **Recipe**: add an `outputSchema` or return a projection/summary with only the fields the model needs; offer a follow-up tool for the full record.
- **Before**: returns the entire order object including a full audit log on every call.
- **After**: returns `{ status, total, eta }`; a separate `get_order_audit_log` returns the heavy detail on demand.

## Skill definitions

Skills are tuned on the same principles, against the three indexed fields (`name`, `description`, `tags`):

- **`description`** — apply the template; add distinct trigger phrasings. Same anemic/bloated/missing-when-to-use checks as tools.
- **`tags`** — fold in BOTH author labels ("billing", "support") AND raw task phrases ("issue a refund", "customer wants money back"). Tags catch terse intent prompts. Keep tags distinct — near-duplicate tags add nothing to the lexical index.
- **`tools`** — not a retrieval field; it's the typed dependency edge to the tool ids the skill's body calls. Keep it accurate so Ratel Local surfaces the right tools when the skill matches.
- **`metadata`** — not indexed; project context (`{"stacks": [...]}`) for push-path ranking. Set it to the customer's stack.

For the full Skill data model and the field-by-field authoring context, see [`../../ratel-decompose-prompt/references/decomposition-patterns.md`](../../ratel-decompose-prompt/references/decomposition-patterns.md).

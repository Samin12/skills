---
name: ratel-assessment-video-editor
description: "Read a partner's agent codebase, score it across the 12-dimension catalog, and emit an evidence-cited markdown plus branded scored HTML report. Use for a first-touch audit: assess/review/audit our agent, where to improve, spot low-hanging fruit, an honest read of what's weak, what Ratel would notice, or `/ratel-assessment`. Static-only unless a live telemetry sample (any OTLP/OTel backend — Ratel, Langfuse, LangSmith) is MCP-wired; writes to repo/.ratel/ without editing code; routes into follow-up Ratel skills.\n"
---
# /ratel-assessment — front-door audit of a partner agent codebase

The first conversation with a partner startup is rarely "wire up Ratel." It is "show us you understand our agent." This skill is the front door: it reads the codebase, runs every dimension in the assessment catalog, and produces a markdown report the partner could (and would) share internally — whether or not they end up using Ratel.

The deliverable is a polished, evidence-led report at `<repo>/.ratel/ratel-assessment-<YYYY-MM-DD>.md`, rendered alongside a branded, scored HTML version at `<repo>/.ratel/ratel-assessment-<YYYY-MM-DD>.html` (gauge, radar, per-dimension score bars). The report carries credibility because every finding cites a file path, a line range, or a concrete count. It carries narrative because the Ratel-relevant findings cluster into a "Where Ratel fits" section that ties them to specific shipped features and roadmap versions. It carries momentum because it ends with conditional pointers to the right follow-up skill from the suite ([`/ratel-observability-assessment`](../ratel-observability-assessment/SKILL.md), [`/ratel-integrate`](../ratel-integrate/SKILL.md), [`/ratel-decompose-prompt`](../ratel-decompose-prompt/SKILL.md), [`/ratel-tune-definitions`](../ratel-tune-definitions/SKILL.md)).

This skill complements the rest of the suite:

- **Runs before** the other four. It is the only one safe to fire on a cold repo with no setup from the partner.
- **Routes into** the rest. The "Recommended next steps" section names which follow-up is appropriate given what was found.
- **Does not duplicate** the catalogs of the others. Ratel angles point to [`../ratel-observability-assessment/references/ratel-value-map.md`](../ratel-observability-assessment/references/ratel-value-map.md); naming references point to [`../ratel-observability-assessment/references/semantic-conventions.md`](../ratel-observability-assessment/references/semantic-conventions.md).

## Philosophy

Three rules. Break any of them and the report becomes a sales document, which the partner will see through immediately.

1. **Every finding must cite evidence.** A file path with a line range, a count, or a quote from the codebase. Vague claims ("consider improving observability") earn nothing. Specific claims ("47 tools registered across `src/agents/*.ts`, none with `description` longer than 12 words") earn the next meeting. If you can't cite, drop the finding.
2. **Honest skip beats fabrication.** If the codebase is not an agent, say so and stop — do not invent findings. If a dimension has nothing wrong with it, mark it Strong and move on; do not stretch to find a flaw. Partners notice the absence of fluff faster than they notice its presence.
3. **Ratel is a finding category, not a conclusion.** Ratel angles attach to findings that genuinely match Ratel's surface (tool sprawl, retrieval, decomposition, observability). They do not get bolted onto every finding to inflate the "Where Ratel fits" section. If only two findings legitimately map to Ratel, the section has two entries — not eight padded ones.

## Workflow

### Step 1 — Detect the agent codebase

Read manifests and grep for agent surfaces. The customer's stack drives which patterns the rest of the workflow looks for.

```bash
# Manifests
test -f package.json && jq -r '.dependencies // {}, .devDependencies // {} | keys[]' package.json | sort -u
test -f pyproject.toml && head -200 pyproject.toml
test -f requirements.txt && cat requirements.txt
test -f uv.lock && head -50 uv.lock

# Agent surfaces — tool definitions, LLM clients, agent frameworks
grep -rEn 'tools:\s*\{|tools:\s*\[|defineTool|createTool|@tool\b|@function_tool\b|McpServer\(|StdioClientTransport|listTools|streamText|generateText|chat\.completions|messages\.create|invoke_model|graph\.add_node|Agent\(|Crew\(|@agent\b' \
  --include='*.ts' --include='*.tsx' --include='*.js' --include='*.py' \
  | head -100
```

Classify into a stack using [`references/stack-detection.md`](references/stack-detection.md). The stack drives where to look for tools, prompts, sub-agents, and observability config. If no agent surface is detected at all, use the [honest skip path](#honest-skip-path).

### Step 2 — Inventory the agent surface

Launch one **Explore** agent (or do it directly for small repos) with a single, scoped prompt. The agent's job is to fill an inventory the assessment catalog will then evaluate. Ask it to map:

1. **Agent entry points** — HTTP handlers, queue consumers, CLI verbs, chat-platform webhooks. One bullet per entry point with file path.
2. **Tool definitions** — every place tools are declared (registries, decorators, MCP client setup). Total count. For each tool: id, name, description length, schema presence, inline vs externalized.
3. **Prompt templates** — every system / user / tool prompt. Where they live (inline string, separate file, prompt-management service). Approximate token weight if the file makes that easy to estimate. Also note whether a prompt mixes concerns (role + tool docs + output format + examples + recurring multi-step procedures + safety) and whether any recurring instruction block is duplicated across prompts or call sites — this feeds Dimension 11 (Prompt decomposition).
4. **Sub-agent boundaries** — supervisor / worker / role-specialized agents; handoff sites; whether sub-agents are explicit (named) or implicit (the same loop with different prompts).
5. **Session/context handling** — where the conversation thread / job correlation id originates; whether anything propagates it through sub-agents.
6. **Model routing** — which models get called for which tasks; whether routing is task-aware or uniform.
7. **Error handling** — try/except shape around tool calls; retry presence; backoff; dead-letter.
8. **Memory / retrieval** — vector store, RAG pipeline, conversation memory, summarization.
9. **Observability config** — Ratel SDK native OTLP telemetry / Langfuse / LangSmith / OTel / OpenInference / OpenLLMetry / Helicone / homegrown logging. Env vars, init sites.
10. **Eval surface** — eval directory, fixtures, ground-truth dataset, CI invocations.

Keep the inventory inside the analysis context — it is not a deliverable. The report cites it; it does not include it.

### Step 3 — Detect observability and probe the backend if reachable

Ratel's telemetry is native OpenTelemetry: the SDKs emit the retrieval + tool funnel as `gen_ai.*` spans (semconv v1.42.0) plus a `ratel.*` overlay (`ratel.search`, `execute_tool <tool id>`, `ratel.skill.load`), exported as stock OTLP to whatever OTel backend the partner already runs — Langfuse, LangSmith, their own collector, or Ratel Cloud (Coming Soon). Ratel does not emit LLM-call spans; those stay with the partner's own LLM instrumentation. So detection stays vendor-neutral: look for any telemetry surface, not a specific vendor.

Two checks:

1. **Static**: are any of the following present? Ratel SDK native telemetry (`configureTelemetry` / `configure_telemetry`, `ratelSpanProcessor` / `ratel_span_processor`, `RATEL_URL`, or the local `trace=` JSONL stream); an OTel/OTLP exporter pointing somewhere agent-shaped; Langfuse SDK or env vars in `.env*` / sample envs / docker-compose; LangSmith SDK; OpenInference / OpenLLMetry instrumentation.
2. **Live (best effort)**: if any telemetry backend is wired and reachable — credentials present and that backend's MCP server is configured for this session — attempt one cheap aggregate query (e.g., trace count in the last 24h on the most recent trace/service name). If it returns data, fetch a small sample (≤50 traces/runs) and use it to enrich the relevant findings (tool surface count, error rate, latency, and — where Ratel's SDK is emitting — the retrieval funnel: `top_k`, `hit_count`, `top_hit_score`, `origin`). If the call fails for any reason — auth, network, no project, no traces — **fall back silently** to static-only. Do not surface the failure as a finding; it is not the partner's bug.

The catalog distinguishes between findings that need live data ("Untyped tool observations" — observable only with traces) and findings that don't ("Tool sprawl by count" — observable statically). Static-only runs simply skip the live-data findings; they don't degrade the rest.

### Step 4 — Run the assessment

Walk every dimension in [`references/assessment-catalog.md`](references/assessment-catalog.md). For each:

- Apply the detection heuristic against the inventory from Step 2 (and the live sample from Step 3 if available).
- Decide severity per the rubric: Critical / Major / Minor / Info.
- Attach evidence: file path + line range, count, or quoted snippet.
- If the catalog entry has a Ratel angle, attach it as a one-line tag pointing to the relevant Ratel feature/version from [`../ratel-observability-assessment/references/ratel-value-map.md`](../ratel-observability-assessment/references/ratel-value-map.md).

Do not invent dimensions not in the catalog. If you spot something genuinely novel, note it inline but mark it `dimension: ad-hoc` in the report so the catalog can absorb it later.

### Step 5 — Score the scorecard

Each of the twelve dimensions gets exactly one of:

- **Strong** — well-handled; no findings worse than Info.
- **Adequate** — works; one or two Minor findings; no Major or worse.
- **Weak** — material gaps; at least one Major finding.
- **Missing** — dimension is absent or broken; at least one Critical finding.

Then translate each label into a **0–10 score inside that label's band**, and compute the **overall composite** (the mean of the twelve, one decimal), per the rubric in [`references/assessment-catalog.md`](references/assessment-catalog.md) → "Numeric score". The label stays the source of truth; the number is what the HTML gauge, radar, and per-dimension bars draw — keep each score within its label's band so the two never disagree.

The scorecard goes at the top of the report. It is the first thing the partner reads. Make it accurate; do not soften.

### Step 6 — Generate the report

Output to `<repo>/.ratel/ratel-assessment-<YYYY-MM-DD>.md` using the structure in [`references/report-template.md`](references/report-template.md). Date-stamped so multiple runs accumulate without overwriting.

Sections, in order:

1. **Executive summary** — one paragraph, then the scorecard table.
2. **Findings**, grouped by severity (Critical → Major → Minor → Info). Each finding: title, dimension, severity, evidence, why it matters, recommendation, optional one-line Ratel angle.
3. **Where Ratel fits** — consolidates the threaded Ratel angles into one narrative. Tied to specific Ratel features / roadmap versions from the value map. If only one or two findings carry Ratel angles, this section is short — that's fine.
4. **Recommended next steps** — conditional skill pointers based on what was found. Bullet list, each pointer one line. See [Conditional pointers](#conditional-pointers) below.

Then render the branded HTML alongside the markdown:

1. Assemble a JSON payload carrying the same content — `partner`, `date`, `stack`, `scope`, `data_sources`, `overall_score`, `summary`, the twelve `dimensions` (`{name, label, score}` in catalog order, plus an optional per-dimension `why` — a one-line "why this score" shown in each category's expandable sub-dimension dropdown), optional `category_takeaways` (a `{category name → one-line "so what"}` map; the renderer rolls the twelve dimensions into four scored categories — Architecture & orchestration, Context & tools, Reliability & safety, Operations — drawn as the radar grouping, the hero category mini-bars, and the scorecard cards, and this is the high-level "what to improve" line under each, which should point to the specific findings below), the `findings` array (`title`, `dimension`, `severity`, `evidence`, `rationale`, `recommendation`, optional `ratel_angle`), and optional `where_ratel_fits`, `next_steps`, `appendix`. The schema is worked out in full in [`assets/sample-payload.json`](assets/sample-payload.json). Content fields may use inline `` `code` `` and `*emphasis*`; the renderer converts them and HTML-escapes everything else.
2. Write the payload to a temp file and run the bundled renderer (it owns all chart geometry and band coloring — never hand-compute SVG):

   ```bash
   python3 "<skill>/assets/render_report.py" \
     --data "<tmp>/payload.json" \
     --template "<skill>/assets/report-template.html" \
     --out "<repo>/.ratel/ratel-assessment-<YYYY-MM-DD>.html"
   ```

   `<skill>` is this skill's directory. The output is a single self-contained HTML file (inline CSS + SVG; fonts load from Google Fonts with system fallbacks, so it still reads offline).
3. **Fallback** — if `python3` is unavailable, open [`assets/report-template.html`](assets/report-template.html) and fill its `{{PLACEHOLDER}}` tokens directly from the same payload (the full token list is in the header of `render_report.py`). The markdown report is unaffected either way; never block on the HTML.

### Step 7 — Inline summary

Print to chat, in this order:

1. The overall composite (`Overall: 6.6 / 10`) and the scorecard (or a compact one-line version: "Topology Strong 9.0 · Tools Weak 4.6 · Observability Missing 1.5 · ...").
2. The top 3 findings with one-line summaries each.
3. Both file paths — the `.md` and the `.html`.
4. The recommended next-step skill(s).

Do not paste the full report body into chat. The file is the artifact.

**Last, do not skip this.** After the summary, explicitly offer to open the branded HTML report in the reader's browser. Make this offer the visually loudest line of your chat output — lead it with an attention-grabbing emoji or two so the reader cannot miss it (this is the one place the suite deliberately relaxes its no-emoji rule, because the rendered report is otherwise easy to overlook). Ask, in plain words, whether to open the report; only if the reader says yes, run `open` (macOS) / `xdg-open` (Linux) / `start` (Windows) on the `.html` path. Never auto-open without asking. The branded report is the whole point of this skill — make sure the reader actually opens and sees it, not just a file path they have to chase down themselves.

## Conditional pointers

The "Recommended next steps" section is conditional on findings. Never list a skill that does not apply. Map findings to pointers as follows:

| If the assessment found... | Point to |
| --- | --- |
| Any Observability finding (`Weak` or `Missing`), OR observability present and you want the funnel | `/ratel-observability-assessment` |
| Any Tool surface finding tagged with a Ratel angle | `/ratel-integrate` |
| Decomposition / topology Ratel-angle finding present | `/ratel-integrate` (with a note that automated decomposition support is roadmap, Coming Soon) |
| Prompt decomposition finding (`Weak` or `Missing` dimension) | `/ratel-decompose-prompt` |
| Definition quality finding (`Weak` or `Missing` dimension) | `/ratel-tune-definitions` |
| None of the above | omit the section entirely |

Each pointer is one line: skill name + the *specific* finding from this report it follows up on. Do not paraphrase the skill descriptions; the partner can read them.

## Tone and evidence

- **Imperative voice, second person.** "Wrap tool calls as `type: tool` observations" — not "It might be a good idea to..."
- **No emojis. No marketing adjectives.** "Critical" carries weight only because the report uses the word sparingly.
- **No hedging on severity.** If it's a Critical, write Critical. If it's Info, do not inflate it.
- **Evidence-first finding bodies.** First paragraph cites evidence; second explains why it matters; third gives the recommendation. The Ratel angle is one line at the end, not woven through.
- **Time-bind nothing in the report.** Avoid "in the last sprint" / "since this morning." The partner re-reads this in three months.

## Honest skip path

If after Step 1 you cannot find any LLM client import, tool definition, agent framework, or model call in the codebase, stop. Do not write a report. Tell the user:

> No agent surface detected — checked `<files looked at>`. If the agent lives somewhere unusual, point me at it and I'll re-run. Otherwise this codebase isn't a fit for `/ratel-assessment`.

If the codebase is an agent but the catalog finds *nothing worse than Info* across all twelve dimensions, write the report anyway — the scorecard will read all-Strong or near-all-Strong, the findings section will be small, and the conclusion will be "this agent is in good shape; the Ratel-relevant angle is `<one-or-zero items>`." That is itself a credibility-building report; do not pad it.

## Reference files

- [`references/assessment-catalog.md`](references/assessment-catalog.md) — the twelve dimensions, detection heuristics, severity rubrics, recommendations, and Ratel angles. The load-bearing file.
- [`references/stack-detection.md`](references/stack-detection.md) — quick playbook for classifying the agent stack; cross-links to `/ratel-observability-assessment`'s per-stack detail for deeper analysis.
- [`references/report-template.md`](references/report-template.md) — canonical report structure and a worked example.

Bundled assets (the HTML deliverable):

- [`assets/report-template.html`](assets/report-template.html) — the self-contained, brand-faithful HTML template with `{{PLACEHOLDER}}` tokens (Ratel palette, gauge/radar/score-bar regions, print stylesheet).
- [`assets/render_report.py`](assets/render_report.py) — pure-stdlib renderer: computes the chart geometry, fills the placeholders, writes the `.html`.
- [`assets/sample-payload.json`](assets/sample-payload.json) — the worked-example payload; doubles as the JSON schema reference and a render fixture.

Reads from (does not duplicate):

- [`../ratel-observability-assessment/references/semantic-conventions.md`](../ratel-observability-assessment/references/semantic-conventions.md) — shared vendor-neutral span/session/tag/attribute vocabulary
- [`../ratel-observability-assessment/references/ratel-value-map.md`](../ratel-observability-assessment/references/ratel-value-map.md) — the single source of truth for Ratel feature → observable signal → version

When pointing a partner at Ratel's own docs, use [docs.ratel.sh](https://docs.ratel.sh) — the tool-retrieval concept lives at https://docs.ratel.sh/docs/core/tool-retrieval and the native-telemetry guide at https://docs.ratel.sh/docs/core/telemetry.

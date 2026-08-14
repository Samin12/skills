# Report template

The canonical structure of the assessment report. The skill writes the report by walking [`assessment-catalog.md`](assessment-catalog.md), filling findings under each dimension, and then assembling the sections below in order.

The same content is delivered twice: this **markdown** structure is the git-diffable source of truth, and a **branded HTML** version (gauge, radar, per-dimension score bars) is rendered from the same data by [`../assets/render_report.py`](../assets/render_report.py) into [`../assets/report-template.html`](../assets/report-template.html). The HTML payload schema is documented and worked-out in [`../assets/sample-payload.json`](../assets/sample-payload.json) — keep this markdown structure and that payload in sync.

The worked example at the bottom is a fictional partner — use it to calibrate tone, density, and evidence-citation style. Do not copy any of its findings into a real report unless they match real evidence in the partner's codebase.

## Structure

### Header

```markdown
# Ratel assessment — <partner / repo name>

**Date**: <YYYY-MM-DD>
**Stack**: <vercel-ai-sdk | ts-generic | python-generic | python-agentic | mixed>
**Scope**: <which entry points / agents were assessed>
**Data sources**: static code analysis<; live telemetry sample (N traces, last 24h)>
```

### 1. Executive summary

One paragraph (4–6 sentences). What the agent is for, the headline scorecard read, the two or three findings worth raising in a partner meeting, and one sentence on what's strong. Lead the scorecard with the **overall composite** — the mean of the twelve dimension scores (0–10) — stated as `**Overall: X.X / 10.**`.

Then the scorecard. Each dimension carries both its ordinal **Rating** and a **0–10 Score** in that rating's band (see [`assessment-catalog.md`](assessment-catalog.md) → "Numeric score"):

```markdown
**Overall: X.X / 10.**

| Dimension | Rating | Score |
| --- | --- | --- |
| Agent topology | Strong / Adequate / Weak / Missing | 0.0–10.0 |
| Tool surface | ... | ... |
| Context management | ... | ... |
| Decomposition | ... | ... |
| Model routing | ... | ... |
| Error handling | ... | ... |
| Observability | ... | ... |
| Cost discipline | ... | ... |
| Eval / quality gates | ... | ... |
| Safety | ... | ... |
| Prompt decomposition | ... | ... |
| Definition quality | ... | ... |
```

### 2. Findings

Grouped by severity. Within a severity, order by dimension. Each finding follows this shape:

```markdown
### <Short title>

- **Dimension**: <dimension name>
- **Severity**: <Critical | Major | Minor | Info>
- **Evidence**: <file path with line range, count, or short quoted snippet>

<One paragraph: why it matters in this codebase.>

**Recommendation**: <One-to-two-sentence concrete action.>

**Ratel can help** (optional): <One line tied to a specific Ratel feature / version from the value map. Omit the line entirely if there is no angle.>
```

Skip an empty severity tier. If there are no Critical findings, the section starts at Major.

### 3. Where Ratel fits

A short narrative (3–8 sentences, plus a short bulleted list if helpful) consolidating the threaded Ratel-angle tags into one story. Tied to specific Ratel feature/version anchors from [`../../ratel-observability-assessment/references/ratel-value-map.md`](../../ratel-observability-assessment/references/ratel-value-map.md). Be honest about shipped vs roadmap.

If only one or two findings carried Ratel angles, this section is short — say so plainly ("Two of the findings above are addressable with Ratel today: ...") and stop. Do not pad.

If no findings carried Ratel angles, omit this section entirely. Do not invent a connection.

### 4. Recommended next steps

Conditional pointers per the mapping table in the main `SKILL.md`. Each pointer is one line, naming the specific finding(s) that drive it:

```markdown
- `/ratel-observability-assessment` — addresses *No observability wired* (Critical, Dimension 7).
- `/ratel-integrate` — addresses *Tool sprawl* (Major, Dimension 2) and *Bloated tool descriptions* (Major, Dimension 2).
```

If no findings warrant any follow-up, omit this section.

### 5. Appendix (optional)

Two things go in the appendix if relevant:

- **Inventory snapshot** — a compact list of the surfaces the assessment looked at (entry points, tool count, prompt files, observability config). Useful as a snapshot the partner can diff against next quarter.
- **Live data caveats** — if a live telemetry sample was pulled, note the window, trace count, the backend it came from, and any caveats (sample is non-representative, only one trace/service name, env filter applied). If no live data was pulled, omit.

Do not include a full per-tool dump or per-prompt dump. The catalog cites — it does not catalog.

## Formatting rules

- **Headings**: `#` for the title, `##` for sections (1–5 above), `###` for findings.
- **No emojis. No marketing adjectives.** "Critical" carries weight only because the report uses the word sparingly.
- **No links to internal Ratel issues / tickets / Slack threads.** The report is shared with the partner; keep it standalone.
- **One trailing newline** at end of file.
- **Date in the filename, not in the headings beyond the header block.** Re-reading two reports side by side is the use case — keep dates out of body content.

---

## Worked example

What follows is a fictional assessment of a fictional partner ("Northcrop AI"). It hits each section so you can calibrate density and tone. Real reports will be longer or shorter; the structure stays the same.

```markdown
# Ratel assessment — Northcrop AI / research-agent

**Date**: 2026-06-09
**Stack**: vercel-ai-sdk
**Scope**: `src/agents/research-agent/*` and the `chat-turn` entry point at `src/api/chat/route.ts`. Out of scope: the offline summarization job at `scripts/digest.ts`.
**Data sources**: static code analysis. No live telemetry data — project has no observability wired yet.

## Executive summary

Northcrop's research agent is a Vercel AI SDK loop that exposes 41 tools to the model on every turn through `src/agents/research-agent/tools.ts:18`. The top-level shape is sound — a single named agent, clean entry point, no recursion — but the tool surface is the dominant cost and quality risk in the codebase today: descriptions are long, several pairs are near-duplicates, and there is no pre-filtering. There is no observability wired anywhere, which means none of the cost or quality claims in this report are independently verifiable today; closing that loop is the highest-leverage next step. The eval suite under `evals/` is real and runs on PRs — strongest dimension in the assessment.

**Overall: 6.6 / 10.**

| Dimension | Rating | Score |
| --- | --- | --- |
| Agent topology | Strong | 9.0 |
| Tool surface | Weak | 4.6 |
| Context management | Adequate | 7.6 |
| Decomposition | Adequate | 7.8 |
| Model routing | Adequate | 7.5 |
| Error handling | Adequate | 7.7 |
| Observability | Missing | 1.5 |
| Cost discipline | Weak | 5.8 |
| Eval / quality gates | Strong | 8.8 |
| Safety | Adequate | 7.4 |
| Prompt decomposition | Weak | 6.0 |
| Definition quality | Weak | 5.6 |

## Findings

### No observability wired

- **Dimension**: Observability
- **Severity**: Critical
- **Evidence**: no `langfuse`, `langsmith`, `@opentelemetry/*`, `openinference`, `openllmetry`, or `helicone` packages in `package.json`. No telemetry init in `src/api/chat/route.ts`. No tracing env vars in `.env.example`.

The agent runs in production (`README.md` describes a live customer surface) but there is no way for anyone outside the running process to observe what it does. Regressions across deploys are invisible; cost spikes are invisible; per-tool failure modes are invisible. None of the other findings in this report are independently verifiable without this loop closed.

**Recommendation**: turn on telemetry via `/ratel-observability-assessment` before any other change in this report — Ratel's native OTLP instrumentation exported to whatever OTel backend the team runs (Langfuse / LangSmith / their own collector / Ratel Cloud, Coming Soon). Two-day landing window is typical.

**Ratel angle**: routes to `/ratel-observability-assessment` — and downstream, once data is flowing, that same skill builds the cost and retrieval-quality dashboards that will measure the rest of the report's recommendations.

### Tool sprawl on the chat turn

- **Dimension**: Tool surface
- **Severity**: Major
- **Evidence**: `src/agents/research-agent/tools.ts:18-487` registers 41 tools. All are passed in `tools:` on `generateText` at `src/api/chat/route.ts:42`. Average description length 187 tokens (rough estimate from character count); longest is `web_research_brief` at 612 tokens.

Every chat turn sends all 41 tool descriptions to the model. At ~140 tokens average × 41 tools, the tool catalog alone is ≈5,700 input tokens before any user content or conversation history. This is most of the input cost on a typical turn and a significant fraction of context budget on small models.

**Recommendation**: pre-filter the tool list per turn so the model only sees the top-K (typically 8) most-relevant tools for the user's message. The full catalog remains addressable via a discovery surface.

**Ratel angle**: matches Ratel's hybrid capability retrieval + replace-mode pre-filter (shipped) — in-process ranking (BM25 by default, opt-in semantic and hybrid RRF, no vector DB) that pre-filters to the top-K per turn. Textbook fit for what Ratel was built for; expected input-token reduction is 50–85% on the catalog portion of the prompt.

### Bloated tool descriptions

- **Dimension**: Tool surface
- **Severity**: Major
- **Evidence**: `src/agents/research-agent/tools.ts` median description 156 tokens. Five tools (`web_research_brief`, `crawl_pages`, `summarize_findings`, `cite_sources`, `synthesize_report`) have descriptions over 350 tokens each, all with multi-paragraph examples inline.

Long descriptions inflate the catalog cost (compounding finding 2.a) and also confuse the model's tool selection — the inline examples often mention other tools, which the model treats as routing hints.

**Recommendation**: trim descriptions to one short "what it does" sentence + one "when to use" line. Move examples and edge-case detail to a separate spec document the agent does not see every turn.

**Ratel angle**: matches Ratel's hybrid capability retrieval (shipped) — the dashboard surfaces low top-hit scores for confusing descriptions, giving a direct measurement of which ones to rewrite. The roadmap entry for LLM-driven suggestions (Coming Soon) will eventually propose the rewrites automatically.

### Near-duplicate tools

- **Dimension**: Tool surface
- **Severity**: Major
- **Evidence**: three pairs flagged — `web_research_brief` vs `crawl_pages`; `summarize_findings` vs `synthesize_report`; `cite_sources` vs `format_citations`. Descriptions overlap >40% by token bag.

The model picks among near-duplicates inconsistently, which makes the agent's behavior across turns less predictable than it should be. Several open issues in `evals/results/` mention "wrong tool selected" without naming the disambiguation.

**Recommendation**: consolidate each pair, or rewrite descriptions to be sharply distinguishing ("brief: fast, free-text overview" vs "crawl: deep, structured fetch with page bodies").

**Ratel angle**: matches Ratel's hybrid capability retrieval (shipped) — top-hit-score distribution will surface the duplication empirically.

### Monolithic system prompt mixing many responsibilities

- **Dimension**: Prompt decomposition
- **Severity**: Major
- **Evidence**: `src/agents/research-agent/prompt.ts:5` is a single ~4,200-token system prompt that mixes role definition, inline tool usage notes, output-format rules, three few-shot examples, and a recurring "research → summarise → cite → synthesize" runbook. The same runbook appears again, near-verbatim, in `scripts/digest.ts:12` and `src/agents/research-agent/summarizer.ts:9`.

The prompt carries every concern on every turn, so the runbook and examples pay input-token rent even when the turn is a one-line follow-up. The duplicated runbook across three call sites also means a change to the procedure has to be made — and kept consistent — in three places.

**Recommendation**: keep a lean core prompt (role + output contract + safety) and extract the runbook and examples into named, retrievable skills the agent loads on demand. Deduplicate the three runbook copies into one unit first.

**Ratel angle**: matches Ratel's first-class skills (shipped) — Ratel ranks skills alongside tools via `search_capabilities` and loads them on demand via `get_skill_content`, so the runbook only enters context when the turn calls for it. Route to `/ratel-decompose-prompt`.

### Tool descriptions missing "when to use"

- **Dimension**: Definition quality
- **Severity**: Major
- **Evidence**: 28 of the 41 tools in `src/agents/research-agent/tools.ts` describe what the tool does but never say when to reach for it; six (`fetch`, `read`, `store`, `lookup`, `query`, `format`) use a single-word `q` or `data` parameter with no enum on finite fields like `mode` and `sort`.

The model has to infer selection intent from "what it does" alone, and Ratel's retrieval has less to match the user's turn against — the lexical arm has fewer terms and the semantic arm less meaning to embed. Both the "when to use" clause and descriptive parameter names feed the index.

**Recommendation**: rewrite each description as one "what it does" sentence plus a one-line "when to use," rename single-letter parameters, and add enums on the finite-value fields.

**Ratel angle**: Ratel's retrieval indexes names + descriptions + parameter names + enum values across its lexical (BM25) and semantic arms (hybrid fuses both via RRF), so this wording directly drives retrieval quality. LLM-driven definition suggestions are roadmap (Coming Soon). Route to `/ratel-tune-definitions`.

### No max_tokens cap on chat-turn generations

- **Dimension**: Cost discipline
- **Severity**: Major
- **Evidence**: `src/api/chat/route.ts:42-58` calls `generateText` without `maxTokens`. Same pattern in `src/agents/research-agent/summarizer.ts:31`.

A worst-case generation can fill the model's context budget. On a Sonnet-class model that is a 16K+ token output for a turn that frequently only needs 500 tokens.

**Recommendation**: cap per call. Sensible defaults: 4096 for chat turns, 1024 for the summarizer step.

### Anemic prompt versioning

- **Dimension**: Context management
- **Severity**: Minor
- **Evidence**: system prompt is an inline template string in `src/agents/research-agent/prompt.ts:5`. No version constant, no hash, no git-tracked prompt id.

Prompt regressions across deploys will be undetectable once observability is wired.

**Recommendation**: extract the prompt to `prompts/research-agent.v1.md` and attach a `prompt_version` constant. Roll the version on every change.

### Eval suite covers tasks but not tool selection

- **Dimension**: Eval / quality gates
- **Severity**: Info
- **Evidence**: `evals/research-agent.jsonl` has 84 labeled tasks with expected outputs but no `expected_tool_id` field. CI gate in `.github/workflows/evals.yml` runs on every PR.

The eval suite catches output regressions but cannot detect tool-selection regressions (e.g., the agent producing a correct-looking answer using the wrong tool). Given the tool sprawl finding above, this is worth closing.

**Recommendation**: label `ground_truth_tool_id` (or the equivalent list of acceptable tool ids) on each fixture. The catalog metadata vocabulary defines the key.

**Ratel angle**: matches the Retrieval Quality dashboard's `recall@5` widget (shipped) — once ground truth exists, retrieval quality becomes measurable in dashboards and CI.

## Where Ratel fits

Three findings in this report (tool sprawl, bloated descriptions, near-duplicates) are the textbook fit for Ratel's shipped surface: hybrid capability retrieval (BM25 by default, opt-in semantic and hybrid RRF, all in-process) with replace-mode pre-filter, paired with the Retrieval Quality dashboard. Once observability lands, the dashboard will show the input-token reduction directly and surface low top-hit scores for the descriptions that need rewriting.

The ground-truth labeling finding (Eval / quality gates, Info) unlocks the Retrieval Quality dashboard's `recall@5` widget, which closes the measurement loop on the integration: not just "we sent fewer tokens" but "we sent the *right* tools." This is the partner-facing proof.

Two further findings map to shipped surface beyond the catalog pre-filter. The monolithic-prompt finding (Prompt decomposition, Major) fits Ratel's first-class skills (shipped): the duplicated runbook becomes a retrievable skill that Ratel ranks alongside tools and loads on demand, so it stops paying input-token rent every turn. The description-quality finding (Definition quality, Major) is the wording side of the same retrieval index — names, descriptions, parameter names, and enum values all feed both the lexical and semantic arms, so tightening them lifts recall directly.

The roadmap entry for LLM-driven definition suggestions (Coming Soon) will eventually propose the description rewrites this report calls out manually. Honest timing: that's roadmap, not shipped. Mention only if asked.

## Recommended next steps

- `/ratel-observability-assessment` — addresses *No observability wired* (Critical, Dimension 7). Required before any of the below can be measured.
- `/ratel-integrate` — addresses *Tool sprawl on the chat turn*, *Bloated tool descriptions*, and *Near-duplicate tools* (all Major, Dimension 2). Pilot scope should be the `chat-turn` trace, A/B split via a feature flag.
- `/ratel-decompose-prompt` — addresses *Monolithic system prompt mixing many responsibilities* (Major, Dimension 11). Extract the duplicated runbook and examples into retrievable skills.
- `/ratel-tune-definitions` — addresses *Tool descriptions missing "when to use"* (Major, Dimension 12). Rewrite descriptions and tighten parameter names / enums for retrieval.
- `/ratel-observability-assessment` — after the above land, build the Token Cost & Savings and Retrieval Quality dashboards to measure the integration's impact.

## Appendix — inventory snapshot

- Entry points: `src/api/chat/route.ts:42` (single).
- Sub-agents: `src/agents/research-agent/summarizer.ts:14` (called from the main loop; not separately tool-equipped).
- Tools: 41 registered in `src/agents/research-agent/tools.ts`. All used at one call site.
- Prompts: 1 inline template (`src/agents/research-agent/prompt.ts:5`). No versioning.
- Observability: none.
- Evals: 84 fixtures in `evals/research-agent.jsonl`; CI gate in `.github/workflows/evals.yml`.
```

That is the worked example. The structure is the contract; the content varies per repo.

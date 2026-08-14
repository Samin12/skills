#!/usr/bin/env python3
"""Render a Ratel assessment HTML report from a JSON payload + the bundled template.

Pure standard library — no third-party packages, no network. The model supplies the
analysis (scores + findings) as JSON; this script owns all chart geometry and band
coloring so the visuals are deterministic and reproducible.

Usage:
    python3 render_report.py \
        --data    payload.json \
        --template report-template.html \
        --out     .ratel/ratel-assessment-2026-06-09.html

Payload schema (see assets/sample-payload.json for a full worked example):
    {
      "partner": str, "date": "YYYY-MM-DD", "stack": str,
      "scope": str, "data_sources": str,
      "overall_score": float,                 # 0–10, one decimal
      "summary": str,                         # paragraphs separated by blank lines
      "dimensions": [ {"name": str, "label": str, "score": float,
                       "why": str | null}, ... ],  # 12, catalog order. `why` (optional)
                                                    # is the per-dimension "why this score"
                                                    # shown in the scorecard dropdown.
      "category_takeaways": { "<category name>": str, ... },  # optional; one-line "so what"
                                                              # per category (see CATEGORIES)
      "findings": [ {
          "title": str, "dimension": str,
          "severity": "Critical"|"Major"|"Minor"|"Info",
          "evidence": str, "rationale": str, "recommendation": str,
          "ratel_angle": str | null          # optional
      }, ... ],
      "where_ratel_fits": str | null,         # optional
      "next_steps": [str, ...],               # optional
      "appendix": str | null                  # optional
    }
"""

import argparse
import html
import json
import math
import re
import sys

# ── Band thresholds (0–10) → label class + color token, matching the SKILL rubric ──
BANDS = [
    (8.5, "strong", "var(--band-strong)", "Strong"),
    (6.5, "adequate", "var(--band-adequate)", "Adequate"),
    (3.5, "weak", "var(--band-weak)", "Weak"),
    (0.0, "missing", "var(--band-missing)", "Missing"),
]

# Severity → (css-suffix, hex) for the findings dots/badges.
SEVERITY = {
    "Critical": ("critical", "#c83a22"),
    "Major": ("major", "#f6572c"),
    "Minor": ("minor", "#7ba0a0"),
    "Info": ("info", "#32635c"),
}
SEVERITY_ORDER = ["Critical", "Major", "Minor", "Info"]

# ── Category taxonomy: the twelve dimensions roll up into four scored groups ─────────
# The radar keeps all twelve axes (detailed shape); the bars show these four
# categories (the simpler read). Each category score is the mean of its member
# dimensions; the per-category "so what" line comes from the payload. `key` drives
# CSS class suffixes and `color` is the category hue (drives the radar grouping +
# legend + hero mini-bars). `short` is the compact label for tight spots.
CATEGORIES = [
    {
        "key": "arch",
        "name": "Architecture & orchestration",
        "short": "Architecture",
        "color": "var(--cat-arch)",
        "blurb": "How the agent is structured: its topology, how work is split into steps, and how models are chosen per step.",
        "dims": ["Agent topology", "Decomposition", "Model routing"],
    },
    {
        "key": "context",
        "name": "Context & tools",
        "short": "Context & tools",
        "color": "var(--cat-context)",
        "blurb": "What the model sees on every turn: the tool catalog, the system prompt, and how tightly both are scoped and named.",
        "dims": ["Tool surface", "Context management", "Prompt decomposition", "Definition quality"],
    },
    {
        "key": "reliab",
        "name": "Reliability & safety",
        "short": "Reliability",
        "color": "var(--cat-reliab)",
        "blurb": "Whether the agent behaves correctly and safely: failure handling, quality gates that catch regressions, and guardrails.",
        "dims": ["Error handling", "Eval / quality gates", "Safety"],
    },
    {
        "key": "ops",
        "name": "Operations",
        "short": "Operations",
        "color": "var(--cat-ops)",
        "blurb": "Whether you can see and control the agent in production: tracing/observability and cost discipline.",
        "dims": ["Observability", "Cost discipline"],
    },
]

# dim name → (category index, category dict). Built once from CATEGORIES.
DIM_TO_CAT = {
    name: (i, cat) for i, cat in enumerate(CATEGORIES) for name in cat["dims"]
}

# Static "what it measures" line per dimension (shown in the scorecard dropdown).
# The model supplies the per-dimension *score* and *why*; these descriptions are fixed.
DIM_INFO = {
    "Agent topology": "Shape of the agent graph — single vs multi-agent, recursion, and whether responsibilities are cleanly separated.",
    "Tool surface": "Size and shape of the tool catalog the model sees each turn: how many tools, how they're scoped, and whether they're pre-filtered.",
    "Context management": "How the prompt, conversation, and working state are assembled, versioned, and pruned on each turn.",
    "Decomposition": "Whether complex tasks are broken into sub-steps or sub-agents instead of one monolithic call.",
    "Model routing": "Whether the right model is chosen per step (cost vs capability) rather than one model for everything.",
    "Error handling": "How tool failures, timeouts, and malformed model output are caught, retried, and surfaced.",
    "Observability": "Whether runs are traced — tool calls, tokens, latency, and errors visible outside the running process.",
    "Cost discipline": "Controls on token spend: output caps, context trimming, caching, and avoiding redundant calls.",
    "Eval / quality gates": "Whether an automated eval/test suite catches regressions before they ship.",
    "Safety": "Guardrails on inputs and outputs — prompt-injection defense, PII handling, and limits on unsafe actions.",
    "Prompt decomposition": "Whether the system prompt is lean and modular rather than a monolith carrying every concern each turn.",
    "Definition quality": "How well tools/skills are named and described for both the model and retrieval — clear 'when to use', parameter names, and enums.",
}

# Short labels for the radar axes (long dimension names don't fit on a spoke).
SHORT_LABELS = {
    "Agent topology": "Topology",
    "Tool surface": "Tools",
    "Context management": "Context",
    "Decomposition": "Decomp",
    "Model routing": "Routing",
    "Error handling": "Errors",
    "Observability": "Observ.",
    "Cost discipline": "Cost",
    "Eval / quality gates": "Evals",
    "Safety": "Safety",
    "Prompt decomposition": "Prompt",
    "Definition quality": "Defs",
}


# ── Inline markdown → HTML (escape first, then `code`, **bold**, *em*) ──────────────
def md_inline(text):
    out = html.escape(str(text), quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", out)
    return out


def md_blocks(text):
    """Render a multi-paragraph string: blank-line-separated blocks; a block whose
    lines all start with '- ' becomes a <ul>, otherwise a <p>."""
    if not text:
        return ""
    blocks = re.split(r"\n\s*\n", str(text).strip())
    parts = []
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if lines and all(ln.lstrip().startswith("- ") for ln in lines):
            items = "".join(f"<li>{md_inline(ln.lstrip()[2:])}</li>" for ln in lines)
            parts.append(f"<ul>{items}</ul>")
        else:
            parts.append(f"<p>{md_inline(' '.join(ln.strip() for ln in lines))}</p>")
    return "".join(parts)


def band_for(score):
    score = max(0.0, min(10.0, float(score)))
    for threshold, cls, color, label in BANDS:
        if score >= threshold:
            return cls, color, label
    return BANDS[-1][1], BANDS[-1][2], BANDS[-1][3]


def fmt_score(score):
    return f"{float(score):.1f}"


# ── Geometry helpers ───────────────────────────────────────────────────────────────
def polar(cx, cy, r, deg):
    """Point at `deg` measured clockwise from 12 o'clock (top)."""
    rad = math.radians(deg)
    return cx + r * math.sin(rad), cy - r * math.cos(rad)


def arc_path(cx, cy, r, start_deg, end_deg):
    x0, y0 = polar(cx, cy, r, start_deg)
    x1, y1 = polar(cx, cy, r, end_deg)
    large = 1 if (end_deg - start_deg) > 180 else 0
    return f"M {x0:.2f} {y0:.2f} A {r:.2f} {r:.2f} 0 {large} 1 {x1:.2f} {y1:.2f}"


# ── Overall gauge: a 270° arc readiness meter with the score in the center ─────────
def render_gauge(score):
    score = max(0.0, min(10.0, float(score)))
    _, color, label = band_for(score)
    cx = cy = 100.0
    r = 82.0
    start, sweep = 225.0, 270.0
    value_end = start + sweep * (score / 10.0)
    x0, y0 = polar(cx, cy, r, start)
    x1, y1 = polar(cx, cy, r, start + sweep)
    lbl0 = f'<text x="{x0:.1f}" y="{y0 + 14:.1f}" class="g-end">0</text>'
    lbl10 = f'<text x="{x1:.1f}" y="{y1 + 14:.1f}" class="g-end">10</text>'
    return f'''<svg viewBox="0 0 200 200" role="img" aria-label="Overall readiness {fmt_score(score)} out of 10">
  <style>
    .g-track {{ fill:none; stroke:var(--cell-empty); stroke-width:14; stroke-linecap:round; }}
    .g-val {{ fill:none; stroke:{color}; stroke-width:14; stroke-linecap:round; }}
    .g-num {{ font-family:var(--mono); font-weight:700; font-size:54px; fill:var(--brand-ink); }}
    .g-slash {{ font-family:var(--mono); font-weight:500; font-size:18px; fill:var(--muted-fg); }}
    .g-band {{ font-family:var(--mono); font-weight:700; font-size:12px; letter-spacing:.14em; fill:{color}; text-transform:uppercase; }}
    .g-end {{ font-family:var(--mono); font-size:10px; fill:var(--muted-fg); text-anchor:middle; }}
  </style>
  <path class="g-track" d="{arc_path(cx, cy, r, start, start + sweep)}" />
  <path class="g-val" d="{arc_path(cx, cy, r, start, value_end)}" />
  <text class="g-num" x="100" y="104" text-anchor="middle">{fmt_score(score)}</text>
  <text class="g-slash" x="100" y="128" text-anchor="middle">/ 10</text>
  <text class="g-band" x="100" y="150" text-anchor="middle">{html.escape(label)}</text>
  {lbl0}{lbl10}
</svg>'''


# ── Radar: 12-axis web, axes grouped by category (colored wedges + rim arcs) ────────
def render_radar(dimensions):
    cx, cy, R = 180.0, 150.0, 106.0

    # Order the axes by category so each category occupies one contiguous arc.
    # Off-catalog dimensions are intentionally omitted here too, so the radar stays
    # consistent with the scorecard + mini-bars (which only know the four categories);
    # main() warns to stderr if any dimension name falls outside the catalog.
    ordered = []  # (dim, category)
    for cat in CATEGORIES:
        for name in cat["dims"]:
            d = next((x for x in dimensions if x.get("name") == name), None)
            if d is not None:
                ordered.append((d, cat))

    n = len(ordered)
    step = 360.0 / n if n else 30.0
    half = step / 2.0

    rings = []
    for level in (2, 4, 6, 8, 10):
        rr = R * level / 10.0
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (polar(cx, cy, rr, i * step) for i in range(n)))
        rings.append(f'<polygon points="{pts}" class="r-ring" />')

    # Category wedge fills + bold rim arcs (the grouping cue the legend maps to).
    wedges, rims = [], []
    i = 0
    while i < n:
        cat = ordered[i][1]
        j = i
        while j + 1 < n and ordered[j + 1][1] is cat:
            j += 1
        if cat is not None:
            a0, a1 = i * step - half, j * step + half
            wx0, wy0 = polar(cx, cy, R, a0)
            wx1, wy1 = polar(cx, cy, R, a1)
            large = 1 if (a1 - a0) > 180 else 0
            wedges.append(
                f'<path d="M {cx:.1f} {cy:.1f} L {wx0:.2f} {wy0:.2f} '
                f'A {R:.1f} {R:.1f} 0 {large} 1 {wx1:.2f} {wy1:.2f} Z" '
                f'style="fill:{cat["color"]}" class="r-wedge" />'
            )
            rims.append(
                f'<path d="{arc_path(cx, cy, R + 3, a0 + 2, a1 - 2)}" '
                f'style="stroke:{cat["color"]}" class="r-rim" />'
            )
        i = j + 1

    spokes, labels = [], []
    for i, (dim, _cat) in enumerate(ordered):
        deg = i * step
        ex, ey = polar(cx, cy, R, deg)
        spokes.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" class="r-spoke" />')
        lx, ly = polar(cx, cy, R + 18, deg)
        dx = lx - cx
        anchor = "middle" if abs(dx) < 6 else ("start" if dx > 0 else "end")
        if ly < cy - R * 0.55:
            dy = -3
        elif ly > cy + R * 0.55:
            dy = 11
        else:
            dy = 4
        name = dim.get("name", "")
        short = SHORT_LABELS.get(name, name if len(name) <= 8 else name[:7] + "…")
        labels.append(
            f'<text x="{lx:.1f}" y="{ly + dy:.1f}" text-anchor="{anchor}" class="r-label">{html.escape(short)}</text>'
        )

    shape_pts, dots = [], []
    for i, (dim, _cat) in enumerate(ordered):
        score = max(0.0, min(10.0, float(dim.get("score", 0))))
        rr = R * score / 10.0
        x, y = polar(cx, cy, rr, i * step)
        shape_pts.append(f"{x:.1f},{y:.1f}")
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" class="r-dot" />')
    shape = " ".join(shape_pts)

    return f'''<svg viewBox="0 0 360 300" role="img" aria-label="Radar of the twelve dimension scores, grouped by category">
  <style>
    .r-wedge {{ opacity:0.08; }}
    .r-rim {{ fill:none; stroke-width:3; stroke-linecap:round; opacity:0.9; }}
    .r-ring {{ fill:none; stroke:var(--hairline); stroke-width:1; }}
    .r-spoke {{ stroke:var(--hairline); stroke-width:1; }}
    .r-label {{ font-family:var(--mono); font-size:10px; fill:var(--muted-fg); }}
    .r-shape {{ fill:color-mix(in srgb, var(--brand-orange) 15%, transparent); stroke:var(--brand-orange); stroke-width:2; stroke-linejoin:round; }}
    .r-dot {{ fill:var(--brand-orange); stroke:#fff; stroke-width:1; }}
  </style>
  {''.join(wedges)}
  {''.join(rings)}
  {''.join(spokes)}
  {''.join(rims)}
  <polygon points="{shape}" class="r-shape" />
  {''.join(dots)}
  {''.join(labels)}
</svg>'''


# ── Category legend (reused under both radars) — maps the four hues to categories ────
def render_category_legend():
    items = "".join(
        f'<span><i style="background:{cat["color"]}"></i>{html.escape(cat["short"])}</span>'
        for cat in CATEGORIES
    )
    return f'<div class="legend legend--cat">{items}</div>'


# ── Hero mini-bars: the four category scores beside the radar (numbers only) ─────────
def render_category_minibars(dimensions):
    by_name = {d.get("name", ""): d for d in dimensions}
    rows = []
    for cat in CATEGORIES:
        members = [by_name[name] for name in cat["dims"] if name in by_name]
        if not members:
            continue
        score = sum(float(m.get("score", 0)) for m in members) / len(members)
        pct = max(0.0, min(10.0, score)) / 10.0 * 100.0
        rows.append(
            f'<div class="mini cat-{cat["key"]}">'
            f'<div class="mini__top"><span class="mini__name">{html.escape(cat["short"])}</span>'
            f'<span class="mini__val">{fmt_score(score)}</span></div>'
            f'<div class="mini__bar"><i style="--w:{pct:.2f}%"></i></div>'
            f"</div>"
        )
    return "\n".join(rows)


# ── Scorecard rows: four category bars (mean of member dims) with description + so-what ──
def render_scorecard(dimensions, takeaways=None):
    takeaways = takeaways or {}
    by_name = {d.get("name", ""): d for d in dimensions}
    rows = []
    for i, cat in enumerate(CATEGORIES):
        members = [by_name[name] for name in cat["dims"] if name in by_name]
        if not members:
            continue
        score = sum(float(m.get("score", 0)) for m in members) / len(members)
        cls, _, label = band_for(score)
        pct = max(0.0, min(10.0, score)) / 10.0 * 100.0

        # Member breakdown: each dimension with its band-colored score.
        chips = []
        for m in members:
            mscore = float(m.get("score", 0))
            mcls, _, _ = band_for(mscore)
            chips.append(
                f'<span class="d band-{mcls}">{html.escape(m.get("name", ""))} '
                f'<b>{fmt_score(mscore)}</b></span>'
            )
        dims_line = '<span class="sep">·</span>'.join(chips)

        takeaway = takeaways.get(cat["name"])
        sowhat = (
            f'<p class="cat-sowhat"><span class="k">So what —</span> {md_inline(takeaway)}</p>'
            if takeaway
            else ""
        )

        # Expandable per-dimension detail: what it measures + why this score.
        subdims = []
        for m in members:
            mname = m.get("name", "")
            mscore = float(m.get("score", 0))
            mcls, _, mlabel = band_for(mscore)
            mpct = max(0.0, min(10.0, mscore)) / 10.0 * 100.0
            desc = DIM_INFO.get(mname, "")
            why = m.get("why")
            why_html = (
                f'<p class="subdim__why"><span class="k">Why this score —</span> {md_inline(why)}</p>'
                if why
                else ""
            )
            subdims.append(
                f'<div class="subdim band-{mcls}">'
                f'<div class="subdim__head"><span class="subdim__name">{html.escape(mname)}</span>'
                f'<span class="subdim__score">{fmt_score(mscore)}<small> / 10</small> '
                f'<span class="chip chip--sm band-{mcls}">{html.escape(mlabel)}</span></span></div>'
                f'<div class="subdim__bar"><i style="width:{mpct:.2f}%"></i></div>'
                f'<p class="subdim__desc">{html.escape(desc)}</p>'
                f"{why_html}"
                f"</div>"
            )
        details = (
            f'<details class="cat-more"><summary>'
            f'<span class="cat-more__label">Sub-dimensions &amp; scoring</span>'
            f'<span class="cat-more__meta">{len(members)} dimensions</span>'
            f'<span class="chev" aria-hidden="true">▾</span></summary>'
            f'<div class="subdims">{"".join(subdims)}</div></details>'
        )

        rows.append(
            f'<div class="cat-row band-{cls}">'
            f'<div class="cat-head"><span class="cat-name">'
            f'<span class="cat-tick" style="background:{cat["color"]}"></span>'
            f'{html.escape(cat["name"])}</span>'
            f'<span class="chip band-{cls}">{html.escape(label)}</span></div>'
            f'<p class="cat-desc">{html.escape(cat["blurb"])}</p>'
            f'<div class="bar-track">'
            f'<div class="rail"><div class="fill" style="--w:{pct:.2f}%;--i:{i}"></div></div>'
            f'<span class="bar-val">{fmt_score(score)}<small> / 10</small></span>'
            f"</div>"
            f'<p class="cat-dims">{dims_line}</p>'
            f"{sowhat}"
            f"{details}"
            f"</div>"
        )
    return "\n".join(rows)


# ── Hero title: partner name split into blur-rise words ─────────────────────────────
def render_partner_words(partner):
    words = str(partner).split()
    if not words:
        return ""
    return " ".join(
        f'<span class="w" style="--wi:{i}">{html.escape(w)}</span>'
        for i, w in enumerate(words)
    )


# ── Findings: grouped Critical → Major → Minor → Info ──────────────────────────────
def render_findings(findings):
    if not findings:
        return '<p class="prose">No findings above Info — this agent is in good shape across the catalog.</p>'
    groups = []
    for severity in SEVERITY_ORDER:
        bucket = [f for f in findings if f.get("severity") == severity]
        if not bucket:
            continue
        suffix, color = SEVERITY[severity]
        cards = []
        for i, f in enumerate(bucket):
            angle = f.get("ratel_angle")
            angle_html = (
                f'<div class="angle"><span class="k">Ratel can help</span>'
                f'<span>{md_inline(angle)}</span></div>'
                if angle
                else ""
            )
            cards.append(
                f'<article class="finding sev-{suffix} reveal" style="--i:{i}">'
                f'<h3>{html.escape(f.get("title", ""))}</h3>'
                f'<div class="tags"><span class="tag">{html.escape(f.get("dimension", ""))}</span>'
                f'<span class="tag sev sev-{suffix}">{html.escape(severity)}</span></div>'
                f'<div class="evidence"><span class="k">EVIDENCE</span> {md_inline(f.get("evidence", ""))}</div>'
                f'<p>{md_inline(f.get("rationale", ""))}</p>'
                f'<p class="reco"><span class="k">Recommendation —</span> {md_inline(f.get("recommendation", ""))}</p>'
                f"{angle_html}"
                f"</article>"
            )
        groups.append(
            f'<div class="sev-group"><div class="sev-head">'
            f'<span class="dot" style="background:{color}"></span>{severity} findings '
            f'<span class="count">· {len(bucket)}</span></div>'
            f'{"".join(cards)}</div>'
        )
    return "\n".join(groups)


def render_section(num, title, inner):
    return (
        f'<section><div class="sec-head"><span class="num">{num:02d}</span>'
        f'<h2>{html.escape(title)}</h2><span class="rule"></span></div>'
        f'<div class="prose">{inner}</div></section>'
    )


def main():
    ap = argparse.ArgumentParser(description="Render a Ratel assessment HTML report.")
    ap.add_argument("--data", required=True, help="JSON payload path")
    ap.add_argument("--template", required=True, help="report-template.html path")
    ap.add_argument("--out", required=True, help="output .html path")
    args = ap.parse_args()

    with open(args.data, encoding="utf-8") as fh:
        data = json.load(fh)
    with open(args.template, encoding="utf-8") as fh:
        template = fh.read()

    dimensions = data.get("dimensions", [])
    # Surface any dimension whose name isn't in the catalog — it would be silently
    # dropped from the scorecard, mini-bars, and radar (see CATEGORIES / DIM_TO_CAT).
    unknown = [d.get("name", "") for d in dimensions if d.get("name") not in DIM_TO_CAT]
    if unknown:
        print(
            f"warning: {len(unknown)} dimension(s) not in any category and omitted from "
            f"the scorecard/radar: {unknown}",
            file=sys.stderr,
        )
    overall = data.get("overall_score")
    if overall is None and dimensions:
        overall = round(sum(float(d.get("score", 0)) for d in dimensions) / len(dimensions), 1)
    overall = float(overall or 0)

    # Optional sections, numbered contiguously from 04.
    optional = []
    n = 4
    if data.get("where_ratel_fits"):
        optional.append(render_section(n, "Where Ratel fits", md_blocks(data["where_ratel_fits"])))
        n += 1
    if data.get("next_steps"):
        items = "".join(f"<li>{md_inline(s)}</li>" for s in data["next_steps"])
        optional.append(render_section(n, "Recommended next steps", f"<ul>{items}</ul>"))
        n += 1
    if data.get("appendix"):
        optional.append(render_section(n, "Appendix", md_blocks(data["appendix"])))
        n += 1

    subs = {
        "{{PARTNER}}": html.escape(data.get("partner", "")),
        "{{PARTNER_WORDS}}": render_partner_words(data.get("partner", "")),
        "{{DATE}}": html.escape(data.get("date", "")),
        "{{STACK}}": html.escape(data.get("stack", "")),
        "{{SCOPE}}": md_inline(data.get("scope", "")),
        "{{DATA_SOURCES}}": md_inline(data.get("data_sources", "")),
        "{{OVERALL_SCORE}}": fmt_score(overall),
        "{{SUMMARY}}": md_blocks(data.get("summary", "")),
        "{{OVERALL_GAUGE_SVG}}": render_gauge(overall),
        "{{RADAR_SVG}}": render_radar(dimensions),
        "{{CATEGORY_LEGEND}}": render_category_legend(),
        "{{CATEGORY_MINIBARS}}": render_category_minibars(dimensions),
        "{{SCORECARD_ROWS}}": render_scorecard(dimensions, data.get("category_takeaways")),
        "{{FINDINGS}}": render_findings(data.get("findings", [])),
        "{{WHERE_RATEL_FITS}}": optional[0] if len(optional) > 0 else "",
        "{{NEXT_STEPS}}": optional[1] if len(optional) > 1 else "",
        "{{APPENDIX}}": optional[2] if len(optional) > 2 else "",
    }
    html_out = template
    for key, value in subs.items():
        html_out = html_out.replace(key, value)

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html_out)
    print(f"Wrote {args.out} (overall {fmt_score(overall)}/10, {len(dimensions)} dimensions, "
          f"{len(data.get('findings', []))} findings)")


if __name__ == "__main__":
    sys.exit(main())

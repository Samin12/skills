#!/usr/bin/env python3
"""Create a standalone interactive pink-sheet HTML widget.

Usage:
  python scaffold_pink_sheet_widget.py --title "Idea" --point "Sharp point" \
    --model "Ladder from noise to signal" --metaphor "Like tuning a radio" \
    --case-study "A team reduced review time by..." --story "A PM hears..." \
    --output idea-widget.html

Or provide --spec spec.json with matching keys. CLI values override JSON.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


FIELDS = ("title", "point", "model", "metaphor", "case_study", "story")


def esc(value: str) -> str:
    return html.escape(value or "", quote=True)


def load_spec(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {str(k): "" if v is None else str(v) for k, v in data.items()}


def render(spec: dict[str, str]) -> str:
    title = esc(spec.get("title") or "Pink-Sheet Visualizer")
    point = esc(spec.get("point") or "State the central point here.")
    model = esc(spec.get("model") or "Describe the model that gives this idea context.")
    metaphor = esc(spec.get("metaphor") or "Name the metaphor that lands the idea.")
    case_study = esc(spec.get("case_study") or "Add a case study, example, data point, or process.")
    story = esc(spec.get("story") or "Add a story beat that makes the idea memorable.")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #20171b;
      --muted: #6e5962;
      --paper: #fff8f9;
      --pink: #f6c8d4;
      --coral: #e85d75;
      --plum: #4b2634;
      --gold: #d99b32;
      --mint: #9fcfbf;
      --blue: #86a7d8;
      --line: rgba(32, 23, 27, 0.18);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: linear-gradient(135deg, #fffafa 0%, #f9eef2 48%, #f3f7ff 100%);
      color: var(--ink);
    }}
    main {{
      width: min(1120px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 28px 0 36px;
    }}
    header {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 18px;
    }}
    h1 {{
      margin: 0;
      max-width: 760px;
      font-size: clamp(2rem, 6vw, 4.8rem);
      line-height: 0.94;
      letter-spacing: 0;
    }}
    .mode {{
      display: inline-grid;
      grid-template-columns: repeat(3, 1fr);
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.68);
      border-radius: 8px;
      overflow: hidden;
      min-width: 270px;
    }}
    .mode button {{
      border: 0;
      border-right: 1px solid var(--line);
      background: transparent;
      min-height: 42px;
      padding: 0 12px;
      color: var(--plum);
      font-weight: 750;
      cursor: pointer;
    }}
    .mode button:last-child {{ border-right: 0; }}
    .mode button[aria-pressed="true"] {{
      background: var(--plum);
      color: white;
    }}
    .sheet {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      grid-template-rows: minmax(230px, auto) minmax(150px, auto) minmax(230px, auto);
      gap: 12px;
      min-height: 690px;
    }}
    .cell {{
      position: relative;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.72);
      border-radius: 8px;
      padding: 18px;
      overflow: hidden;
      box-shadow: 0 14px 38px rgba(75, 38, 52, 0.08);
    }}
    .cell h2 {{
      margin: 0 0 12px;
      font-size: 0.78rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }}
    .cell p {{
      margin: 0;
      font-size: clamp(1rem, 1.8vw, 1.22rem);
      line-height: 1.45;
    }}
    .point {{
      grid-column: 1 / -1;
      display: grid;
      place-items: center;
      text-align: center;
      background: linear-gradient(180deg, #f8d8e0, #fff7f9);
    }}
    .point p {{
      width: min(760px, 100%);
      font-size: clamp(1.45rem, 4vw, 3.1rem);
      line-height: 1.04;
      font-weight: 850;
      color: var(--plum);
    }}
    .visual {{
      min-height: 130px;
      margin-top: 14px;
      border: 1px dashed rgba(75, 38, 52, 0.22);
      border-radius: 8px;
      display: grid;
      place-items: center;
      padding: 12px;
    }}
    .ladder {{
      width: min(360px, 100%);
      display: grid;
      gap: 8px;
    }}
    .rung {{
      height: 30px;
      border-radius: 4px;
      background: var(--mint);
      border: 1px solid rgba(32, 23, 27, 0.14);
    }}
    .rung:nth-child(2) {{ width: 82%; margin-left: 9%; background: #b9d5eb; }}
    .rung:nth-child(3) {{ width: 64%; margin-left: 18%; background: #f5d488; }}
    .rung:nth-child(4) {{ width: 46%; margin-left: 27%; background: #ed97a7; }}
    .metaphor-mark {{
      width: min(260px, 70vw);
      aspect-ratio: 1;
      border-radius: 999px;
      border: 18px solid rgba(232, 93, 117, 0.28);
      display: grid;
      place-items: center;
      color: var(--plum);
      font-weight: 900;
      text-align: center;
      padding: 22px;
      background: radial-gradient(circle, white 0 48%, rgba(246, 200, 212, 0.45) 49% 100%);
    }}
    .chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 14px;
    }}
    .chip {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 8px 10px;
      background: white;
      color: var(--plum);
      font-size: 0.88rem;
      font-weight: 700;
    }}
    .hidden-detail {{
      display: none;
      margin-top: 12px;
      color: var(--muted);
    }}
    .show-detail .hidden-detail {{ display: block; }}
    @media (max-width: 760px) {{
      header {{ display: block; }}
      .mode {{ width: 100%; margin-top: 16px; min-width: 0; }}
      .sheet {{ grid-template-columns: 1fr; grid-template-rows: auto; min-height: 0; }}
      .point {{ grid-column: auto; min-height: 170px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>{title}</h1>
      <div class="mode" aria-label="View mode">
        <button type="button" aria-pressed="true" data-mode="think">Think</button>
        <button type="button" aria-pressed="false" data-mode="teach">Teach</button>
        <button type="button" aria-pressed="false" data-mode="coach">Coach</button>
      </div>
    </header>

    <section class="sheet" aria-label="Pink sheet visual">
      <article class="cell" data-cell="model">
        <h2>Model</h2>
        <p>{model}</p>
        <div class="visual" aria-hidden="true">
          <div class="ladder">
            <div class="rung"></div><div class="rung"></div><div class="rung"></div><div class="rung"></div>
          </div>
        </div>
        <p class="hidden-detail">Use this area to show structure: context, boundaries, hierarchy, or sequence.</p>
      </article>

      <article class="cell" data-cell="metaphor">
        <h2>Metaphor</h2>
        <p>{metaphor}</p>
        <div class="visual" aria-hidden="true">
          <div class="metaphor-mark">image the idea</div>
        </div>
        <p class="hidden-detail">Use this area to make the concept memorable without over-explaining it.</p>
      </article>

      <article class="cell point" data-cell="point">
        <div>
          <h2>Point</h2>
          <p>{point}</p>
        </div>
      </article>

      <article class="cell" data-cell="case-study">
        <h2>Case Study</h2>
        <p>{case_study}</p>
        <div class="chips" aria-hidden="true">
          <span class="chip">incident</span>
          <span class="chip">point</span>
          <span class="chip">benefit</span>
        </div>
        <p class="hidden-detail">Use this area for evidence, practical steps, numbers, or applied proof.</p>
      </article>

      <article class="cell" data-cell="story">
        <h2>Story</h2>
        <p>{story}</p>
        <div class="chips" aria-hidden="true">
          <span class="chip">scene</span>
          <span class="chip">stakes</span>
          <span class="chip">turn</span>
        </div>
        <p class="hidden-detail">Use this area for the human beat that carries the idea home.</p>
      </article>
    </section>
  </main>

  <script>
    const copy = {{
      think: "Use this area to show structure: context, boundaries, hierarchy, or sequence.",
      teach: "Teach mode: reveal the point, then show the proof that makes the idea usable.",
      coach: "Coach mode: turn each label into a question and let the audience supply content."
    }};

    document.querySelectorAll(".mode button").forEach((button) => {{
      button.addEventListener("click", () => {{
        document.querySelectorAll(".mode button").forEach((b) => b.setAttribute("aria-pressed", "false"));
        button.setAttribute("aria-pressed", "true");
        document.querySelectorAll(".cell").forEach((cell) => cell.classList.add("show-detail"));
        const firstDetail = document.querySelector('[data-cell="model"] .hidden-detail');
        if (firstDetail) firstDetail.textContent = copy[button.dataset.mode] || copy.think;
      }});
    }});

    document.querySelectorAll(".cell").forEach((cell) => {{
      cell.addEventListener("click", () => cell.classList.toggle("show-detail"));
    }});
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", help="JSON spec with title, point, model, metaphor, case_study, story")
    parser.add_argument("--output", default="pink-sheet-widget.html", help="Output HTML path")
    for field in FIELDS:
        parser.add_argument(f"--{field.replace('_', '-')}", dest=field)
    args = parser.parse_args()

    spec = load_spec(args.spec)
    for field in FIELDS:
        value = getattr(args, field)
        if value:
            spec[field] = value

    Path(args.output).write_text(render(spec), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()

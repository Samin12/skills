---
name: think-visualizer
description: Turn raw ideas, script fragments, outlines, arguments, teaching points, or abstract concepts into visual thinking artifacts using the Think/Pink Sheet process. Use when the user asks to visualize an idea, create a diagram, make an interactive HTML widget, create a generated image, convert script material into visuals, build a pink sheet, or use Think, pink sheets, full-spectrum thinking, models, metaphors, case studies, or stories to explain something.
---

# Think Visualizer

## Output Contract

For every visualization request, produce both artifacts unless a tool, policy, or technical constraint makes one impossible:

1. An interactive HTML diagram or widget.
2. A bitmap image generated with the image model. If image generation is unavailable, provide a ready-to-use image prompt and say that the image could not be generated in this environment.

For non-trivial requests, read `references/pink-sheet-framework.md` before designing. Do not copy or quote the source book at length. Use the framework as a thinking process, and preserve attribution when discussing the method.

## Workflow

1. Distill one point per artifact set.
   - If the user gives a messy script, extract the strongest single claim first.
   - If there are several independent claims, create a small family of pink sheets or ask only when the split would materially change the output.

2. Build a private pink-sheet map.
   - Point: write a short A statement and a clarifying B statement.
   - Model: choose a visual structure that gives the idea context.
   - Metaphor: choose a compact imageable comparison that lands the point.
   - Case study: identify practical evidence, example, data, or process.
   - Story: identify the human or emotional scene that makes the point memorable.

3. Choose the HTML form.
   - Prefer a real interactive widget over a static page: toggles, tabs, sliders, draggable cards, hover reveals, step-through sequences, filters, or comparison controls.
   - Use self-contained HTML/CSS/JS for projectless work. In an existing app, follow the repo stack and design system.
   - Make the first screen the usable visual experience, not a landing page or explanation page.
   - For quick standalone widgets, adapt `scripts/scaffold_pink_sheet_widget.py`.

4. Generate the image.
   - Use the metaphor, model, and story as image fuel.
   - Pick the image type that best serves the idea: conceptual poster, editorial diagram, storyboard panel, metaphor scene, visual mnemonic, or high-fidelity object/scene.
   - Avoid asking the image to render dense text. Keep generated text to a minimum; put precise labels in HTML instead.

5. Deliver cleanly.
   - Link the HTML file or running local URL.
   - Show or link the generated image when available.
   - Briefly state the point, model, and metaphor used.

## HTML Standards

- Make the diagram responsive for desktop and mobile.
- Include meaningful interaction, not decorative motion.
- Keep labels short and scannable.
- Use stable dimensions for diagrams, controls, cards, and counters so text and hover states do not shift the layout.
- Use accessible contrast, focus states, keyboard-friendly controls, and semantic HTML.
- Use SVG inside HTML when precise diagrams are needed; use CSS grid/flex for layouts; use vanilla JS unless the host project already uses a framework.
- Keep external dependencies out of standalone files unless the user asks for them.

## Pink-Sheet Heuristics

- Context is the bigger picture. It usually becomes the model and metaphor.
- Concept is the point. It should be distinct, declarative, and memorable.
- Content is the proof. It becomes the case study, process, example, data, or story.
- Full-spectrum visuals should balance logic and emotion, plus abstraction and concrete detail.
- Models clarify boundaries and relationships. Metaphors land meaning. Do not let the metaphor replace the model.
- A strong output lets the user think once and reuse often: as a slide, lesson, coaching prompt, strategy widget, or visual explanation.

## Resource Guide

- `references/pink-sheet-framework.md`: condensed operating model derived from Think by Matt Church and Peter Cook.
- `scripts/scaffold_pink_sheet_widget.py`: creates a standalone five-part pink-sheet HTML widget from CLI arguments or a JSON spec.

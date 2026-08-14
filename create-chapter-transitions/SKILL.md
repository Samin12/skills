---
name: create-chapter-transitions
description: Create short, polished chapter or section transition cards for videos, especially reference-matched kinetic typography with crisp live text, staged typing/reveal effects, coordinated sound design, and backgrounds that match an existing edit. Use when asked to make, recreate, revise, render, or insert a chapter transition, title card, section bumper, or interstitial between video scenes in HyperFrames or Borumi.
---

# Create Chapter Transitions

Create a compact transition that feels native to the surrounding edit. Preserve reference timing and visual grammar while making the title readable, sharp, and easy to revise.

## Workflow

1. Read the `hyperframes` skill before creating or editing a composition. Read its routed animation, CLI, registry, and media skills when they apply.
2. Inspect the target edit and any supplied reference. For a timestamped video link, study roughly two seconds before and after the transition. Record the canvas, background, title placement, word-entry order, hold, exit, and audio cue.
3. Read [references/reference-style.md](references/reference-style.md) when the user asks for the clean grid-and-typed-title treatment demonstrated by this skill.
4. Build text as live HTML. Never rasterize the title or bake it into a generated background. Use whole-pixel positions at the title's resting state and avoid blur, glow, scale overshoot, and subpixel resting transforms unless the reference clearly contains them.
5. Recreate simple backgrounds with CSS. Generate or source an image only when the reference contains real visual texture or imagery that CSS cannot reproduce faithfully; keep the live title separate.
6. Reveal title words or characters in the same rhythm as the reference. Keep the transition brief, give the completed title a readable hold, and finish the exit before the next spoken sentence.
7. Match sound by function and timing. Prefer a quiet typing or keystroke cue for typed reveals. Use the exact reference sound only when the user explicitly authorizes it and the source can be isolated without speech. Do not bundle or publish third-party audio with this skill.
8. Render and inspect the opening, full-title hold, and final frame. Check that the text is crisp at output resolution, the background matches, the title is centered, the animation is seek-safe, and the audio is not louder than the neighboring dialogue.
9. If the destination is Borumi, use Borumi MCP tools to inspect the project and insert the rendered video plus its audio at the requested scene boundary. Keep the media and audio segments aligned, preview the cut, then commit the edit transaction.

## Starter Template

Copy [assets/chapter-transition/index.html](assets/chapter-transition/index.html) into a scaffolded HyperFrames project when the requested look matches the included preset. Replace the placeholder word spans, composition identifiers, duration, and audio binding as needed. Do not copy a transition's old audio into a new project by default.

## Quality Bar

- Match the reference before adding stylistic invention.
- Keep titles legible for at least 0.45 seconds after the final word lands.
- Prefer a 1.2–2.0 second total duration unless the surrounding pacing calls for otherwise.
- Start from a subtle sound level; for the included preset, target roughly -18 dBFS peak before final timeline mixing.
- Use a hard, clean title edge. A reference-matched drop shadow may be soft, but the glyphs must remain crisp.
- Preserve natural scene flow: no unexplained black frames, long silence, or extra pause around the transition.

## Deliverables

Return the rendered transition, the editable HyperFrames source, and a concise note with duration, resolution, audio treatment, and insertion point. When publishing a reusable skill or template, exclude copyrighted reference audio and private project media.

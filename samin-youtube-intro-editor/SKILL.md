---
name: samin-youtube-intro-editor
description: Edit or plan the first 2–8 minutes of Samin Yasar's talking-head YouTube videos. Use when an intro needs fast proof-first visual storytelling, the presenter framed bottom-right over websites or diagrams, pacing modeled on Samin's published videos, or a reusable HyperFrames-based cut with quality checks and a rendered MP4.
---

# Samin YouTube Intro Editor

Create a polished YouTube intro that shows the result before explaining it. Preserve the speaker's real audio and argument while turning the frame into an editorial canvas for websites, workflows, comparisons, and proof.

## Required companion skills

Read and follow these installed skills before editing:

1. `hyperframes` for routing and project structure.
2. `talking-head-recut` for the source-footage workflow.
3. `media-use` for trim, transcode, crop, transcription, and media resolution.
4. `hyperframes-core`, `hyperframes-creative`, `hyperframes-animation`, and `hyperframes-cli` before authoring or rendering.

This skill adds Samin's style and decision rules; it does not replace those technical contracts.

## Workflow

### 1. Inspect and map the source

- Probe resolution, frame rate, duration, audio channels, and codec.
- Extract only the requested working range; keep the original untouched.
- Transcribe with word or sentence timestamps.
- Run `scripts/analyze_intro.py` on both the source range and 2–5 recent Samin intros when available.
- Read `references/style-profile.md` before storyboarding.

### 2. Build the proof-first story map

Map each spoken promise to something visible. In the first 20 seconds, prefer actual results, websites, before/after states, or output montages over explanatory diagrams. Later beats may use diagrams, process maps, UI fragments, and occasional supplied illustrations.

Write one visual beat for each semantic unit in the transcript. The first 90 seconds should be denser than the tutorial setup that follows. A useful starting rhythm is:

- 0–20s: 2–4 second proof shots.
- 20–90s: 4–8 second visual beats.
- After 90s: 8–16 second beats, with internal motion so holds do not feel static.

Do not cut merely to hit a number. Cut when the claim, visual world, or level changes.

### 3. Use the Samin frame grammar

- Canvas: 1920×1080 for YouTube unless the user says otherwise.
- Presenter: rounded picture-in-picture anchored bottom-right, normally 22–27% of frame width. Protect the face and hands; add a small shadow or outline.
- Base world: warm white or very light neutral, faint square grid, bold black typography, one saturated accent.
- Proof media: large browser/device frames, slight perspective, active crop or scroll, visible cursor when interaction matters.
- Type: short, heavy, high-contrast labels. Keep body copy out of the way of narration.
- Motion: fast position changes, camera pushes, wipes, cursor clicks, drawn connectors, counters, and hard cuts. Use one slower hold after each rapid cluster.
- Density: two focal points and foreground production details such as section numbers, metadata, dividers, or progress rails.

For exact measured choices and anti-patterns, read `references/style-profile.md`.

### 4. Choose visuals in priority order

1. Real outputs and live-product screenshots named by the speaker.
2. User-owned prior-video footage when the user permits reuse.
3. Purpose-built visualizations that explain the claim.
4. Supplied still illustrations, used selectively as accents or transitions.
5. Fictional mockups for negative examples. Label or design them as generic examples; do not disparage an identifiable creator.

Never turn a folder of supplied images into a slideshow unless explicitly requested.

### 5. Preserve editorial truth

- Preserve the spoken audio unless the user requests a dialogue edit.
- Do not invent results, rankings, customer counts, or product claims.
- Use on-screen words as emphasis, not a second competing narration.
- Show source-brand names only when directly relevant to the speaker's point.

### 6. Author and render

- Stage media locally; never depend on a live iframe or network asset at render time.
- Keep source video and audio as direct children of the HyperFrames root.
- Use deterministic, seekable animation only.
- Prefer a modular composition for more than three visual worlds.
- Preserve the full-resolution deliverable while using proxies for analysis.

### 7. Run the quality loop

Read `references/quality-gates.md` and do not deliver until all gates pass. At minimum:

- HyperFrames `check` passes.
- Snapshot the hook, each major level change, and the final tease.
- Watch the first 30 seconds in real time, then scan the entire edit at 1× or 1.5×.
- Verify no black frames, blank browser panels, frozen motion, clipped text, PiP occlusion, or audio drift.
- Confirm the output duration and streams with `ffprobe`.

Deliver the rendered MP4, a snapshot/contact sheet, the project path, and a concise note on any deliberate deviations from the style profile.

## Resources

- `scripts/analyze_intro.py` — produces metadata, scene-cut timestamps, and a contact sheet for a reference intro.
- `references/style-profile.md` — Samin's measured intro style and visual priorities.
- `references/quality-gates.md` — edit, render, and delivery checklist.

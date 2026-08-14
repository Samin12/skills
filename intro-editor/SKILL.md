---
name: intro-editor
description: Turn raw talking-head footage into an engaging, b-roll-rich edited video intro in Samin's signature style (cold-open proof montage, screen-recording inserts, stat graphics, illustrated story scenes, agenda cards, PiP continuity). Use this whenever the user gives a video and asks to edit the intro, add b-roll, "make it engaging", gather clips for an intro, or turn bare-camera footage into a finished intro — even if they don't say "intro" explicitly. Also use when the user asks to analyze a video's editing style for replication.
---

# Intro Editor

Turn a bare talking-head recording into an intro edited like Samin's reference video: the camera audio is the spine, and a dense visual layer sits on top of it. The viewer should almost never look at a static talking head for more than ~15 seconds.

## Mental model

Two layers, always:

1. **Audio spine** — the original camera take's voice, untouched and continuous. Never cut or reorder audio within a beat; the edit is visual.
2. **Visual layer** — what's on screen switches constantly between (a) the camera itself at alternating zoom levels and (b) full-screen inserts with a small PiP bubble of the speaker for continuity.

Every sentence the speaker says gets classified: does it *name a tool or result* (→ screen recording), *state a number or claim* (→ stat graphic), *tell a story* (→ illustrated scene), *lay out structure* (→ agenda card), or *carry pure energy* (→ stay on camera, maybe punch in)? The full grammar with timestamped examples from the reference video is in `references/style-spec.md` — read it before planning any edit.

## Inputs to collect

- The raw video: local file path, YouTube/Drive link, or an existing Jockey asset. If the user has separate b-roll / screen recordings, get those too.
- Which part is intro material (if unclear, propose a scope after analysis — usually the first continuous "setup/promise" section of the talk).
- Where finishing happens: ffmpeg draft render (default) or an edit plan for their NLE.

## Pipeline

Work through these steps in order. Steps 1–2 can overlap (frame analysis is local and doesn't need Jockey).

### 1. Ingest

Get the video BOTH locally (for ffmpeg frame work and assembly) and into a Jockey knowledge store (for transcript-level understanding and clip search). Follow `references/jockey-pipeline.md` — it has the exact validated commands, including the Zo relay trick for local files (Jockey cannot fetch YouTube URLs or local paths) and polling until the item is `ready`.

### 2. Analyze the raw footage

Two passes, different tools:

- **Visual pass (local, immediate):** extract timestamped contact sheets with ffmpeg (command in `references/assembly.md`) to see framing, existing cuts, and where the speaker is just talking to camera.
- **Speech pass (Jockey):** pull a timestamped beat map — every claim, number, story, tool mention, and structural statement, with start/end times. Use `jockey_query` with a `json_schema` so beats come back structured. Query patterns are in `references/jockey-pipeline.md`.

### 3. Choose the intro scope and cold open

The reference style front-loads proof: the first ~15 seconds are a rapid montage (2s cuts) of end results — charts, numbers, the product working — pulled from *later* in the video or from the asset library, playing under the opening lines. Identify: the hook sentence, the promise/roadmap section, and 3–6 "proof moments" from anywhere in the footage that can be harvested for the cold open.

### 4. Map beats to visual treatments

Go beat-by-beat through the intro transcript and assign a treatment from the grammar in `references/style-spec.md`. Enforce the pacing rules there (max camera hold ~15 s, insert lengths 2–8 s, return to camera between insert clusters). The output of this step is the Edit Decision List (EDL) — use the exact format below.

### 5. Gather and generate assets

For each planned insert, resolve a source in this priority order:

1. **Harvest from the same video** — screen recordings and demos later in the footage (find via `jockey_search`, verify with a frame extract).
2. **User's existing library** — other Jockey stores or local folders they point at.
3. **Generate** — illustrations (pixel-art / comic / vintage styles per the spec), stat graphics, agenda cards, and title cards. Use available image/video generation tools; the spec has style prompts. Anything not generatable becomes an **asset request list** for the user (e.g. "record 10 s of the dashboard showing X").

Never leave a beat with a dangling treatment: every EDL row ends `resolved` (file path) or `requested` (in the asset list).

### 6. Deliver the EDL

Save `intro-edl.md` (human-readable) plus `intro-edl.json` (for assembly) next to the project. Every row:

| # | Base in–out | What's said (short) | Treatment | Visual description | Source | Status |

`Treatment` is one of: `camera` `camera-punch` `screen-rec` `stat-graphic` `illustration` `agenda-card` `title-card` `overlay-only`. JSON schema in `references/assembly.md`.

### 7. Assemble a draft

Render with ffmpeg following `references/assembly.md`: base track cut to the intro, inserts overlaid full-screen with the PiP bubble composited bottom-right, punch-ins via crop+scale, title cards as generated stills. Output `intro-draft.mp4`.

### 8. QC before showing the user

Make a contact sheet of the rendered draft and read it. Check: no camera hold over ~15 s, PiP present on every full-screen insert, cold open starts on proof not on the speaker, audio spine unbroken. Fix before delivering. Show the user the draft plus the EDL and the asset request list.

## Quality bar

The edit fails if any of these are true: the first shot is the bare talking head; any insert plays without the PiP bubble; a stretch of bare camera exceeds ~20 s; an insert contradicts what's being said (visual must match the sentence under it); the audio has gaps or doubled words at cut points.

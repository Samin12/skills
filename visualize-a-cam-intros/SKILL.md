---
name: visualize-a-cam-intros
description: Turn talking-head A-cam intros into proof-first visual stories by keeping the presenter as a stable foreground anchor while cherry-picking, reframing, timing, and animating B-roll, product footage, screenshots, slides, comparisons, and prior-video clips. Use for YouTube or course intros, podcast hooks, transcript-matched B-roll edits, presenter picture-in-picture layouts, Borumi timeline edits, HyperFrames intro composites, or QA of dense A-cam/B-roll openings.
---

# Visualize A-Cam Intros

Build an intro in which the presenter carries the narration while the rest of the frame proves each claim. Favor real outputs, action, and visual variety over decorative motion.

## Route the work

- For an open Borumi Project, use the Borumi MCP tools and required Borumi guides. Inspect and edit through a transaction; do not modify Project files directly.
- For authored composites, motion graphics, or a standalone render, read `hyperframes` first, then the companion skills it requires.
- For source extraction, transcription, cropping, or transcoding, use `media-use` and `talking-head-recut`.
- Use ordinary timeline media when a clip only needs a trim or reframe. Use HyperFrames when the beat needs a designed layout, synchronized motion, or several layered sources.

This skill owns editorial selection, A-cam/B-roll composition, and the acceptance loop. Companion skills own their technical contracts.

## Establish the edit contract

Resolve these from the user's request or inspectable project state before editing:

- target intro range;
- A-cam and narration source;
- transcript or timed spoken content;
- available B-roll, screenshots, slides, outputs, and prior-video footage;
- supplied reference video or style target;
- protected material, including audio, existing cuts, or surrounding timeline content.

Ask one short question only when a missing answer would materially change the edit. Preserve the original sources and work on the smallest requested range.

Inventory the complete user-authorized source pool before choosing visuals: the full current Project, attached asset folders, reusable footage later in the video, and permitted prior videos. Index useful moments by transcript claim, source time, visual role, and whether the clip contains motion or only a still result.

## Build the visual beat map

Read [references/editorial-playbook.md](references/editorial-playbook.md), then map each semantic narration beat to visible proof.

For each beat, record:

- exact Project-time range;
- spoken claim;
- chosen visual and source;
- why it proves the claim;
- presentation mode: `fullscreen`, `a-cam-pip`, `split`, `graphic`, or `a-cam-reset`;
- source in/out points and any speed change;
- important UI, faces, hands, or labels that must remain visible.

Treat every spoken claim as a continuous coverage interval. Proof may change inside it, but the visual and layout must stay intentional from the first content word through the semantic handoff. Bridge words such as “so,” “and then,” and “because” must inherit a planned proof or a deliberate A-cam reset—never an accidental B-roll or layout gap.

Use `scripts/validate_beat_map.py --require-continuous` when the beat map is JSON. Repair overlaps, invalid ranges, missing proof, and accidental source repetition before building the edit.

## Select proof in this order

1. A moving result or completed output named by the speaker.
2. A before/after or problem/solution comparison.
3. A real interface action that directly demonstrates the claim.
4. User-owned footage from elsewhere in the current or prior video.
5. A supplied slide, screenshot, or diagram with purposeful motion.
6. A purpose-built visualization when no real proof exists.

Do not treat an asset folder as a slideshow. Choose clips because they prove the sentence, not because they are available.

## Compose the presenter and B-roll

- Keep the A-cam stable enough to anchor the eye while the proof world changes.
- Default to a bottom-right presenter PiP around 22–27% of frame width, then adjust to protect the face, hands, and important B-roll controls.
- Use a clean crop of the presenter once. Never place a new card or border around a crop that already contains a framed PiP.
- Return briefly to full A-cam at a major idea change or when the viewer needs a visual reset.
- Promote screen recordings to readable size. Show enough interface context to understand where the action happens.
- Start interface clips after setup clicks when the result is the point. Show the action or finished state, not cursor hesitation.
- Speed up dead interaction time only; keep the meaningful action legible.
- Center comparisons with breathing room. Avoid zooming so far that the relationship between both sides becomes unclear.
- Use moving source footage when available. If a still is necessary, add a motivated pan, crop, reveal, or annotation.
- When one sentence contains two visual subclaims, cut at the spoken clause boundary: establish the context first, then show the decisive action. Do not split at an arbitrary time midpoint.

The first frame of every proof beat should answer: “What am I looking at?” The final frame should answer: “What changed or why does it matter?”

## Pace the intro

- Make the hook the densest section. Use several distinct proof shots during the first spoken promise.
- When the hook promises N use cases or examples, preview N distinct micro-beats when real evidence exists. Reveal them in narration order, use optional one-to-four-word labels, then settle briefly on the complete map before the deep dive. Do not reuse one UI shot to imply several use cases.
- Cut on a new claim, result, example, or visual world—not merely to hit a fixed duration.
- Let later explanation beats hold longer, but keep internal action alive.
- Avoid repeating the same source or framing in adjacent beats unless the second beat reveals a genuinely new result.
- After a rapid cluster, use one calmer hold or A-cam reset so the viewer can absorb the point.

## Preserve editorial truth

- Preserve narration and sync unless the user requests dialogue editing.
- Keep B-roll overlays silent unless their sound is explicitly part of the story.
- Do not invent metrics, customers, results, product behavior, or interface states.
- Treat third-party reference videos as style evidence. Do not reuse their face, camera, or audio without authorization.
- Keep labels short and subordinate to the narration.

## Edit in bounded ranges

1. Inspect the current timeline and surrounding cuts.
2. Build one coherent range or story cluster.
3. Render or stage it without disturbing protected audio or adjacent material.
4. Inspect the result at exact user-reported moments and across a broad contact sheet.
5. Keep the change only when it improves clarity, proof, and flow.

When replacing an existing composite, preserve its exact timeline range unless the user requested timing changes. Verify the first and last boundary frames so no flash, overlap, or gap is introduced.

When extracting later-project footage, keep a ledger with donor Project in/out, donor media in/out, desired Project in/out, expected media in/out, speed, and destination in/out. Run `scripts/validate_extraction_ledger.py` before moving the kept fragment. After staging, verify the donor is unchanged, the destination media offsets and duration match the ledger, scratch fragments are gone, and no source audio was copied.

## Run the gauntlet

Read [references/gauntlet.md](references/gauntlet.md) and run the complete finite worklist before delivery. Use `scripts/analyze_intro.py` on the final render to generate metadata, scene-cut evidence, black-frame findings, and a contact sheet.

A timeline plan or metadata-only check is not acceptance evidence. Before commit, render or capture the staged affected window, inspect a broad contact sheet, watch the motion, and inspect one frame before, at, and after every replaced boundary. Rendered pixels and timeline metadata must agree.

Stop with one of these honest outcomes:

- `success`: every required gate passes;
- `clean-no-op`: the requested result already exists;
- `blocked`: required source or tool access is unavailable;
- `approval-required`: the next action exceeds the user's authority;
- `no-progress`: another pass would not measurably improve a failed gate.

Never report a render or tool error as success.

## Deliver

Return:

- the committed Borumi change or editable composition path;
- the final render when one was produced;
- a contact sheet or saved inspection evidence;
- actual duration, resolution, frame rate, and streams;
- a compact gauntlet receipt naming passed gates and any unresolved limitation.

## Resources

- `references/editorial-playbook.md` — visual selection, layouts, pacing, and failure patterns.
- `references/gauntlet.md` — bounded QA loop and acceptance gates.
- `scripts/validate_beat_map.py` — validates timed beat-map JSON.
- `scripts/validate_extraction_ledger.py` — checks donor-to-destination trim and media-offset arithmetic.
- `scripts/analyze_intro.py` — probes a render and creates objective QA artifacts.

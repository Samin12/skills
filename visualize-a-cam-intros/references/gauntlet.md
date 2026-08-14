# Intro Visualization Gauntlet

Run this finite worklist on the staged edit or final render. Repair one highest-value failure at a time, then rerun the affected checks. Stop at success or when a named terminal condition applies.

## Pass 1: Editorial coverage

- The opening promise is visible, not only spoken.
- Every major claim in the requested range has a matching proof beat.
- Every advertised use case appears once in the rapid preview when real source proof exists.
- Transcript coverage has no unplanned visual or layout gap, including bridge words between claims.
- The visual actually demonstrates the claim; it is not merely topic-adjacent.
- Adjacent beats vary by source, visual role, scale, or motion language.
- The same footage is not repeated unless it reveals new information.
- The edit contains at least one attention reset after a dense sequence when the narration allows it.

Evidence: compare the timed transcript or beat map with a broad contact sheet.

## Pass 2: Framing and readability

- Each proof beat establishes what the viewer is looking at before moving closer.
- Interfaces retain enough context to understand the action.
- Comparisons show both states at a readable scale with breathing room.
- Essential faces, labels, controls, and results are not cropped or covered.
- The presenter PiP is stable, cleanly cropped, and not double-framed.
- The PiP moves, hides, or yields when it obstructs the proof.

Evidence: inspect exact high-quality frames at the start, emphasis point, and end of every major layout.

## Pass 3: Motion and pacing

- Setup clicks, cursor hesitation, loading, and dead interaction time are trimmed.
- Every interaction claim contains visible state change: a scroll, selection, file open, tool action, touch, cursor response, transformation, or result.
- The decisive action or result remains long enough to understand.
- Still images have one purposeful motion treatment.
- Motion settles before text or a comparison must be read.
- No black, blank, frozen, or accidental flash frames appear at boundaries.
- A rapid cluster is followed by a calmer hold when appropriate.

Evidence: use two views. Scan a broad contact sheet for coverage and variety, then use dense frames or real-time playback to prove motion. Inspect a frame triplet immediately before, at, and after every replaced boundary.

## Pass 4: Audio and continuity

- Original narration remains synchronized and intelligible.
- B-roll overlays are silent unless their audio is explicitly required.
- No typing, click, transition, or source audio leaks into the mix unintentionally.
- The replacement begins and ends on the intended Project-time boundaries.
- Content before and after the edited range remains unchanged.
- For reused later-project footage, the extraction ledger agrees with the staged edit: donor Project and media ranges, desired range, speed, expected media offsets, destination range, and duration all reconcile.
- Donor segments remain unchanged, scratch fragments are removed, and no source audio or linked group member was copied unintentionally.

Evidence: compare source and staged timeline ranges, destination media offsets, segment/group membership, scratch space, boundary frames, and audio streams.

## Pass 5: Technical render

- HyperFrames lint/check reports no errors or warnings when HyperFrames is used.
- Runtime, layout, motion, and contrast checks pass.
- Required media resolves locally without a network dependency.
- The output plays from start to finish.
- Rendered pixels and timeline metadata agree at every changed beat; a structurally valid segment that displays the wrong source moment fails this gate.
- Resolution, frame rate, duration, codecs, pixel format, and audio streams match the delivery contract.
- `scripts/analyze_intro.py` reports no unintended black segments.

Evidence: retain command output, metadata JSON, and the generated contact sheet.

## Repair order

Choose the first failing category in this order:

1. missing or misleading proof;
2. unreadable framing or occlusion;
3. dead pacing or repeated source;
4. unintended audio or sync drift;
5. technical render failure;
6. decorative polish.

Make one bounded repair, rerender only the affected range when possible, and rerun that gate plus the boundary checks. Continue until all gates pass or another pass produces no measurable improvement.

## Receipt fields

Record:

- scope and exact timeline range;
- source state or commit inspected;
- checks and conditions;
- failures found;
- repairs kept;
- final result: `success`, `clean-no-op`, `blocked`, `approval-required`, or `no-progress`;
- evidence paths or Borumi commit ID.

# Grid-and-Typed-Title Reference Style

Use this preset for a clean YouTube chapter card like “Why This Matters.” Treat the values as a calibrated starting point, then adapt them to the actual reference.

## Canvas and type

- Canvas: 1920×1080 at 30 fps
- Duration: 1.6 seconds / 48 frames
- Background: white or sampled warm white
- Grid: 1 px neutral gray lines, 95 px spacing, about 58% opacity
- Grid falloff: centered radial mask so the edges fade gently
- Title: centered live HTML, Inter or the matched sans-serif, 98 px, weight 800
- Letter spacing: -0.04em; line height: 0.98
- Ink: near-black `#0b0b0d`
- Shadow: `0 12px 18px rgba(0, 0, 0, 0.22)` only when it is present in the reference

## Motion

- Fade the grid in during frames 0–5.
- Stage title words at frames 6, 13, and 19 for a three-word title.
- Reveal each word over four frames with a three-pixel upward settle and gray-to-black color finish.
- Hold the completed title through frame 37.
- Fade the title, grid, and canvas during frames 38–48.
- For different word counts, spread reveal starts across the same approximate 0.2–0.65 second window and keep at least a 0.45 second full-title hold.

## Audio

- Use a restrained typing or key-tap texture whose accents follow the word or character reveals.
- Avoid a whoosh unless the supplied reference uses one.
- If the user authorizes extracting the reference cue, isolate only the transition sound, remove speech, add short boundary fades, and keep it local to that project.
- Begin near -18 dBFS peak and compare against neighboring dialogue. Lower it further when the transition competes with speech.
- Bind audio as a separate clip so the editor can trim, replace, or rebalance it without re-rendering the graphic.

## Background decisions

Rebuild geometric backgrounds with CSS for sharpness and resolution independence. Use image generation only for a reference that depends on illustration, photography, paper texture, or another non-geometric surface. If generating an image, generate the background without text and layer the live title above it.

## Review frames

Inspect at least:

- frame 0: clean entry without a flash
- first reveal frame: correct starting rhythm
- final reveal plus four frames: crisp completed word
- middle of the hold: centered, readable full title
- final frame: clean exit ready for the next scene

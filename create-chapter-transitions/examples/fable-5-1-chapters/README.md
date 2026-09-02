# Fable 5.1 chapter cards

Editable HyperFrames source for the eleven 1.6-second chapter cards created for the Borumi project `Fable 5.1` (`5689`). The cards use the reusable grid-and-typed-title treatment from the parent `create-chapter-transitions` skill.

`rows.json` contains the rendered titles. `edit-plan.json` records the final Borumi insertion points, the Scene 2 surgeon B-roll placement, and the local sound-design provenance.

Each title now occupies its own 1.6-second gap: camera, microphone, and screen content stop for the card, then resume afterward. The visual render is intentionally silent. Borumi owns the separate bass-forward click (`borumi-youtube-transition-sfx-quiet.wav`), reused from earlier chapter-transition projects at its native level. The audio file is not bundled in this public repository.

Scene 2 uses a precomposed surgeon clip with Samin's presenter camera in the top-right corner and `EDITED BY FABLE 5.1` in the upper-left. The eleven rendered cards are 1920×1080, H.264, 30 fps, and 1.6 seconds each. The corrected Borumi edits were committed as `cc96` (standalone chapter gaps, bass click, and Scene 2 composite), `25c6` (conflicting overlay cleanup), and `2b4c` (`Real-World Testing` before the final recorded section).

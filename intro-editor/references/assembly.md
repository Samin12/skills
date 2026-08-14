# Assembly — EDL format and ffmpeg recipes

## EDL JSON schema (`intro-edl.json`)

```json
{
  "project": "name",
  "base_video": "path/to/raw.mp4",
  "fps": 30, "width": 1920, "height": 1080,
  "events": [
    {
      "n": 1,
      "base_in": 12.4, "base_out": 16.9,
      "spoken": "short paraphrase of the line under this event",
      "treatment": "screen-rec | stat-graphic | illustration | agenda-card | title-card | camera | camera-punch | overlay-only",
      "visual": "description of what should be on screen",
      "source": "path/to/asset.mp4|png (or 'harvest: base 812.0-818.5' or null)",
      "source_in": 0.0,
      "pip": true,
      "caption": "optional on-screen text",
      "status": "resolved | requested"
    }
  ]
}
```

`base_in/base_out` are times on the RAW take (the audio spine). Events must tile the intro contiguously — camera segments are events too. `pip` is true for every non-camera treatment.

The human-readable `intro-edl.md` is the same rows as a table, plus the asset request list at the bottom.

## Analysis: contact sheets

One frame every 2 s, timestamped, 30 per sheet — the fastest way to see cut structure:

```bash
ffmpeg -v error -t 240 -i INPUT.mp4 -vf \
  "fps=1/2,drawtext=text='%{pts\:hms}':fontsize=28:fontcolor=yellow:box=1:boxcolor=black@0.6:x=8:y=8,scale=320:-2,tile=5x6" \
  -vsync vfr sheet-%02d.png
```

Read the sheets as images. For a specific moment: `ffmpeg -ss <t> -i INPUT.mp4 -frames:v 1 frame.png`.

## Render strategy

Build per-event segment files, then concat. Simpler and more debuggable than one giant filtergraph.

Audio for EVERY segment comes from the base take (`-ss base_in -to base_out -i base.mp4` → `-map` audio from it). Video depends on treatment:

### camera
```bash
ffmpeg -ss {in} -to {out} -i base.mp4 -r {fps} -s {W}x{H} -c:v libx264 -crf 18 -c:a aac seg_{n}.mp4
```

### camera-punch (crop ~20% then scale back)
```bash
ffmpeg -ss {in} -to {out} -i base.mp4 -vf "crop=iw*0.8:ih*0.8:iw*0.1:ih*0.06,scale={W}:{H}" ... seg_{n}.mp4
```
Crop slightly above center (y offset < (1-0.8)/2) so the face stays framed. Alternate punch levels between consecutive camera events.

### full-screen insert with PiP (video asset or still)
```bash
ffmpeg -ss {base_in} -to {base_out} -i base.mp4 \
  {-loop 1 for stills} -ss {source_in} -i asset \
  -filter_complex "\
    [1:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=white[bg]; \
    [0:v]crop=ih*0.75:ih*0.75:(iw-ih*0.75)/2:ih*0.1,scale=240:240[pipsq]; \
    [pipsq]format=yuva420p,geq=lum='lum(X,Y)':a='if(gt(pow(X-W/2,2)+pow(Y-H/2,2),pow(W/2,2)),0,255)'[pip]; \
    [bg][pip]overlay={W}-260:{H}-260[v]" \
  -map "[v]" -map 0:a -t {dur} -shortest ... seg_{n}.mp4
```
(That alpha mask makes a circular PiP; for the rounded-rect look, overlay without mask and accept square corners, or precompute a rounded-corner mask PNG once and use `alphamerge` — do the mask PNG, it looks closer to the reference.)
Pad color: white for grid-paper graphics, black for screen recordings/illustrations.

### captions on inserts
Add before the overlay: `drawtext=text='{caption}':fontsize=40:fontcolor=white:box=1:boxcolor=black@0.5:x=(w-text_w)/2:y=h*0.78`

### title/agenda cards
Generate the card as a PNG (image tool or HTML→screenshot), then treat as a still insert (usually WITH PiP, per the reference).

### concat
```bash
printf "file 'seg_%d.mp4'\n" $(seq 1 N) > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy intro-draft.mp4
```
All segments must share codec/fps/resolution/audio params (they do if rendered with the same flags). If concat clicks at audio joins, re-encode the concat with `-c:a aac` instead of `-c copy`.

## QC pass

Contact-sheet the draft (command above, drop `-t`), read it, and verify against the SKILL.md quality bar. Also spot-listen: extract 3 random 10 s audio clips across cut points (`ffmpeg -ss .. -t 10 -vn -c:a aac check.m4a`) — wait, you can't listen; instead verify waveform continuity: `ffprobe -f lavfi -i "amovie=intro-draft.mp4,astats=metadata=1:reset=1" 2>&1 | grep -c silence` should show no unexpected silence gaps, and segment durations in the EDL must sum to the draft duration (±0.2 s).

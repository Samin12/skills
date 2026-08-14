---
name: linkedin-lead-magnet-video
description: "LinkedIn Lead Magnet Video Generator"
---

# LinkedIn Lead Magnet Video Generator

Speed up a video to match the LinkedIn LM speed audio duration and replace the audio track.

## Usage

User provides a video file path. The skill will:
1. Get the video duration
2. Calculate the speed multiplier needed to match the audio duration (~6.8 seconds)
3. Speed up the video using ffmpeg with pitch-preserved audio
4. Replace the audio with the LinkedIn LM speed audio
5. Output as MP4

## Reference Audio

Path: `/Users/saminyasar/Documents/augment-projects/random/linkedin LM speed audio.mp3`
Duration: ~6.8 seconds

## Command Template

```bash
# Get video duration
VIDEO_DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "INPUT_VIDEO")

# Get audio duration
AUDIO_DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "/Users/saminyasar/Documents/augment-projects/random/linkedin LM speed audio.mp3")

# Calculate speed factor
SPEED=$(echo "scale=6; $VIDEO_DURATION / $AUDIO_DURATION" | bc)

# Process video: speed up video, replace audio
ffmpeg -i "INPUT_VIDEO" -i "/Users/saminyasar/Documents/augment-projects/random/linkedin LM speed audio.mp3" \
  -filter_complex "[0:v]setpts=PTS/$SPEED[v]" \
  -map "[v]" -map 1:a \
  -c:v libx264 -preset fast -crf 23 \
  -c:a aac -b:a 192k \
  -shortest \
  "OUTPUT.mp4"
```

## Workflow

When the user invokes this skill with a video path:

1. Verify the video file exists
2. Verify ffmpeg and ffprobe are available
3. Calculate the required speed multiplier
4. Run the ffmpeg command
5. Output the processed video with `_linkedin` suffix before the extension

## Example

Input: `my-recording.mov`
Output: `my-recording_linkedin.mp4`

---
name: video-production
description: "Video Production Skill"
---

# Video Production Skill

Generate images, audio, video, voiceovers, and sound effects for video projects using WaveSpeed AI as the unified API aggregator.

## WaveSpeed API Key
All requests use the same API key stored in `~/.claude/.env` as `WAVESPEED_API_KEY`

## Services & Capabilities

### Images - WaveSpeed (Flux Dev)
```bash
curl -X POST "https://api.wavespeed.ai/api/v3/wavespeed-ai/flux-dev" \
  -H "Authorization: Bearer $WAVESPEED_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "YOUR_PROMPT",
    "width": 1344,
    "height": 768
  }'
```

### Voiceover - Eleven Labs V3 (via WaveSpeed)
**Endpoint:** `POST https://api.wavespeed.ai/api/v3/elevenlabs/eleven-v3`

**Available Voices:** Aria, Roger, Sarah, Laura, Charlie, George, Callum, River, Liam, Charlotte, Alice, Matilda, Will, Jessica, Eric, Chris, Brian, Daniel, Lily, Bill

```bash
curl -X POST "https://api.wavespeed.ai/api/v3/elevenlabs/eleven-v3" \
  -H "Authorization: Bearer $WAVESPEED_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your voiceover text here",
    "voice_id": "Alice",
    "similarity": 1,
    "stability": 0.5,
    "use_speaker_boost": true
  }'
```

**Pricing:** $0.1 per 1,000 characters (minimum 1,000 chars billed)

### Sound Effects - MMAudio V2 (via WaveSpeed)
**Endpoint:** `POST https://api.wavespeed.ai/api/v3/wavespeed-ai/mmaudio-v2`

For video-synced SFX generation:
```bash
curl -X POST "https://api.wavespeed.ai/api/v3/wavespeed-ai/mmaudio-v2" \
  -H "Authorization: Bearer $WAVESPEED_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "video": "VIDEO_URL",
    "prompt": "whoosh sound, transition effect",
    "negative_prompt": "voice, music, speech",
    "duration": 2,
    "num_inference_steps": 25,
    "guidance_scale": 4.5
  }'
```

### Music - Suno (via Kie AI)
**API Key:** `KIE_AI_API_KEY`
For background music and soundtracks.

### Video - Kling AI
For video generation from images or text prompts.

## Result Retrieval (All WaveSpeed Models)
```bash
curl -X GET "https://api.wavespeed.ai/api/v3/predictions/{requestId}/result" \
  -H "Authorization: Bearer $WAVESPEED_API_KEY"
```

## Workflow for Adding Audio to Remotion Videos

1. **Write voiceover script** - Break into segments matching scene timing
2. **Generate voiceover** - Use Eleven Labs via WaveSpeed for each segment
3. **Generate SFX** - Use MMAudio V2 for transitions, notifications, success sounds
4. **Download audio files** - Save to `public/audio/` in Remotion project
5. **Add Audio component** - Use Remotion's `<Audio>` component with proper timing

### Remotion Audio Component Example
```tsx
import { Audio, Sequence, staticFile } from "remotion";

// In your composition:
<Sequence from={0} durationInFrames={100}>
  <Audio src={staticFile("audio/voiceover-scene1.mp3")} />
</Sequence>
```

## Environment Variables
Store in `~/.claude/.env`:
- `WAVESPEED_API_KEY` - WaveSpeed AI access (includes Eleven Labs, Flux, MMAudio)
- `KIE_AI_API_KEY` - Kie AI access (for Suno music)

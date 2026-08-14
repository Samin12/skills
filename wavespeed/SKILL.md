---
name: wavespeed
description: "WaveSpeed AI Skill"
---

# WaveSpeed AI Skill

WaveSpeed is an AI model aggregator providing access to various AI services including text-to-speech and image generation.

## API Key
```
WAVESPEED_API_KEY=64100b73045a19b5147b51d85e0ad38498b695ae2272f6fe7e2f087032f433e0
```

## Text-to-Speech: ElevenLabs V3

Use this for all voiceover requests.

### Endpoint
```
POST https://api.wavespeed.ai/api/v3/elevenlabs/eleven-v3
```

### Headers
```
Content-Type: application/json
Authorization: Bearer ${WAVESPEED_API_KEY}
```

### Request Body
```json
{
  "text": "Your text here (max 10,000 chars)",
  "voice_id": "Roger",
  "similarity": 1,
  "stability": 0.5,
  "use_speaker_boost": true
}
```

### Available Voices
**Male:** Roger, Charlie, George, Callum, River, Liam, Will, Eric, Chris, Brian, Daniel, Bill
**Female:** Aria, Sarah, Laura, Charlotte, Alice, Matilda, Jessica, Lily

### Get Result
```
GET https://api.wavespeed.ai/api/v3/predictions/{requestId}/result
```

Response contains `data.outputs` array with MP3 URLs when status is "completed".

### Pricing
$0.1 per 1,000 characters

---

## Image Generation: Nano Banana Pro

Use this for all image generation requests.

### Endpoint
```
POST https://api.wavespeed.ai/api/v3/google/nano-banana-pro
```

### Headers
```
Content-Type: application/json
Authorization: Bearer ${WAVESPEED_API_KEY}
```

### Description
Nano Banana Pro is Google's advanced AI image-generation model built on Gemini 3 Pro stack. Features:
- High quality text-to-image generation
- Image-to-image editing
- Enhanced text handling in images
- Better creative control

---

## Usage Rules

1. **Voiceovers**: Always use ElevenLabs V3 via WaveSpeed
2. **Images**: Always use Nano Banana Pro via WaveSpeed
3. **Polling**: After POST, poll the result endpoint until status is "completed"
4. **Download**: Save the output files locally for use in projects

---
name: image-to-canvas
description: "Image to Canvas"
---

# Image to Canvas

Generate images using WaveSpeed AI and place them on the Open Canvas board.

**Trigger:** When the user asks to "generate an image", "make an image", "create a picture", "make me a graphic", or any image generation request.

## How It Works

1. Generate the image via WaveSpeed Nano Banana Pro
2. Poll until complete
3. Download the image to the workspace
4. Place it on the Open Canvas board

## Step-by-Step Execution

### Step 1: Generate the Image

```bash
curl -s -X POST "https://api.wavespeed.ai/api/v3/google/nano-banana-pro/text-to-image" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 64100b73045a19b5147b51d85e0ad38498b695ae2272f6fe7e2f087032f433e0" \
  -d '{
    "prompt": "<DETAILED_PROMPT_HERE>",
    "aspect_ratio": "1:1"
  }'
```

Available image models (all under `https://api.wavespeed.ai/api/v3/`):
- `google/nano-banana-pro/text-to-image` — best for text-in-image, general purpose (default)
- `google/nano-banana-pro/edit` — image-to-image editing
- `google/nano-banana-2/text-to-image` — newer Nano Banana model
- `wavespeed-ai/qwen-image-2.0/text-to-image` — alternative model
- `bytedance/seedream-v5.0-lite` — ByteDance model
- `kwaivgi/kling-image-o3/text-to-image` — Kling model
- `x-ai/grok-2-image` — Grok image model

The response returns a request ID in `data.id`.

Common aspect ratios:
- `1:1` — square (social posts, profile pics)
- `16:9` — landscape (ads, presentations, banners)
- `9:16` — portrait (stories, reels, vertical ads)
- `4:3` — classic landscape
- `3:4` — classic portrait

### Step 2: Poll for Result

Wait 3 seconds, then poll:

```bash
curl -s "https://api.wavespeed.ai/api/v3/predictions/<REQUEST_ID>/result" \
  -H "Authorization: Bearer 64100b73045a19b5147b51d85e0ad38498b695ae2272f6fe7e2f087032f433e0"
```

Check `data.status`:
- `processing` — wait 2 more seconds and poll again
- `completed` — grab URL from `data.outputs[0]`
- `failed` — report error to user

### Step 3: Download the Image

```bash
curl -sL "<OUTPUT_URL>" -o "<WORKSPACE>/generated-image-<timestamp>.png"
```

Use a descriptive filename based on the prompt (e.g., `claude-club-ad-1742515200.png`).

### Step 4: Place on Canvas

```bash
open-canvas-cli canvas add-file --workspace "<WORKSPACE>" --path "<FULL_PATH_TO_IMAGE>"
```

## Prompt Engineering Tips

When the user gives a short request, expand it into a detailed prompt:
- Add style keywords (photorealistic, flat design, 3D render, illustration, etc.)
- Specify lighting, colors, composition
- Include text instructions if the image should contain readable text (Nano Banana Pro handles text well)
- For ads: include brand name, tagline, visual style, color palette

## Rules

1. Always use Nano Banana Pro via WaveSpeed for image generation
2. Always poll until completed (max 30 seconds, then report timeout)
3. Always download and save locally before placing on canvas
4. Always place the result on the Open Canvas board
5. Use descriptive filenames
6. Tell the user what you generated and the file path

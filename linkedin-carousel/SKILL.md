# LinkedIn Carousel Post via PDF

Post a LinkedIn carousel by uploading a local PDF through Vista Social.

## Prerequisites
- `cloudflared` installed (`brew install cloudflare/cloudflare/cloudflared`)
- Python 3 (for local HTTP server)
- Vista Social MCP connected (via Blotato or direct)
- LinkedIn profile ID: **265575** (Samin Yasar)
- Profile group ID: **d64800e0-993a-11ee-a895-df742b1174ec** (Group 1 - Mains)

## Workflow

### Step 1: Locate the PDF
Find the carousel PDF on the local filesystem. Common locations:
- `/Users/saminmacmini/Projects/instagram-carousels/output/`
- User-specified path

### Step 2: Expose PDF via Public URL
LinkedIn document posts require a publicly accessible URL. Use cloudflared quick tunnel:

```bash
# Start local HTTP server in the PDF's directory
cd /path/to/pdf/directory
python3 -m http.server 8765 &

# Start cloudflared tunnel
cloudflared tunnel --url http://localhost:8765
# Note the https://*.trycloudflare.com URL from output
```

### Step 3: Upload to Vista Social
Use `createMedia` to import the PDF as a document:
```
Tool: mcp__claude_ai_Vista_Social__createMedia
- profile_group_ids: ["d64800e0-993a-11ee-a895-df742b1174ec"]
- media_url: ["https://<tunnel-url>/carousel.pdf"]
- type: document
- name: carousel.pdf
```

### Step 4: Create the Post
Use `schedulePost` with the PDF URL:
```
Tool: mcp__claude_ai_Vista_Social__schedulePost
- profile_id: 265575
- network_code: linkedin
- publish_at: "now" (or ISO 8601 future date)
- message: "<post caption>"
- media_url: ["https://<tunnel-url>/carousel.pdf"]
```

For drafts, add `draft: true`.

### Step 5: Verify & Get Link
Use `getPost` with the returned post ID. The response includes `published_link` with the live LinkedIn URL.

### Step 6: Cleanup
Kill the HTTP server and cloudflared tunnel processes.

## Key Notes
- LinkedIn renders PDF documents as swipeable carousels natively
- The tunnel only needs to stay up until Vista Social downloads the PDF (usually seconds)
- Vista Social stores the document on its CDN (CloudFront) after upload
- Documents can ONLY be shared on LinkedIn (not other networks via Vista Social)
- Always preview/draft before publishing unless user explicitly says to publish

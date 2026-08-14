# Jockey Ingest & Analysis Pipeline

Validated end-to-end on 2026-07-22. Jockey MCP tools are named `mcp__<server-id>__jockey_*` — load them via ToolSearch first.

## Knowledge stores

- `ks_019f8be4-fe4c-70d3-a16e-78afc77b70ea` — `intro-editing-reference` — holds the reference style video (`ksi_019f8be7-8aab-7880-8e93-63e6e955bc69`). Reuse for style questions; don't add project footage here.
- Create one store per editing project (`jockey_create_knowledge_store`, name like `intro-<project>`), so `jockey_search` results stay scoped to that project's footage.

## Getting video in

`jockey_add_media` only fetches **public direct-download URLs** (max 4 GB). It rejects YouTube/streaming page URLs. Local files can't be POSTed by us either (`jockey_request_upload_link` is a manual browser flow — avoid; it stalls the pipeline on the user).

### From YouTube

```bash
yt-dlp -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]" \
  --merge-output-format mp4 -o "<name>.%(ext)s" "<url>"
```
720p keeps uploads small; it's plenty for analysis. If yt-dlp errors with "page needs to be reloaded", it's outdated → `brew upgrade yt-dlp`.

### Local file → public URL via Zo relay

Zo (the user's remote server, tools `mcp__zo__*`) can serve files publicly:

1. On Zo (`mcp__zo__bash`): write a small Python `ThreadingHTTPServer` handling PUT (save to dir) + GET (serve), start it with `nohup` on a port (e.g. 8749). See note below for the PUT handler shape.
2. `mcp__zo__proxy_local_service(local_port)` → returns `host:port` public endpoint.
3. From the Mac: `curl -T <file> "http://<host>:<port>/<file>"` (add `--max-time` generously; ~85 MB took ~1 min).
4. Verify sha256 matches on both ends.
5. Pass `http://<host>:<port>/<file>` as `source` to `jockey_add_media`.
6. **Cleanup after the item is `ready`:** kill the server and delete `/home/workspace/xfer` on Zo. (`pkill -f` in a Zo bash call kills its own shell if the pattern matches the command string — run cleanup as a separate call with a non-self-matching pattern.)

PUT handler gotcha: `SimpleHTTPRequestHandler` has no PUT; subclass it, read `Content-Length` bytes in 1 MB chunks, save to `os.path.basename(self.path)`, reply 201. GET serves from the same directory.

### Registering and polling

```
jockey_add_media(knowledge_store_id, items=[{source, asset_type: "video", metadata: {...}}])
```
Branch on `outcome`: `added` → poll; `asset_pending`/`registration_pending` → retry with the returned `asset_id` after a wait. Then poll `jockey_list_knowledge_store_items(item_ids=[...])` until `status: "ready"`. A ~35-min 720p video takes several minutes to index — do local ffmpeg frame analysis while waiting instead of idling.

## Analysis query patterns

### Timestamped beat map (the core query)

`jockey_query` with a `json_schema` forcing structure:

```json
{"type":"object","properties":{"beats":{"type":"array","items":{"type":"object","properties":{
  "start_sec":{"type":"number"},"end_sec":{"type":"number"},
  "spoken":{"type":"string"},
  "kind":{"type":"string","enum":["hook","claim","number","story","tool_mention","roadmap","question","transition","content"]},
  "on_screen":{"type":"string"}},
  "required":["start_sec","end_sec","spoken","kind"]}}},"required":["beats"]}
```

Query like: "Break down the first N minutes of ksi_... beat by beat: for each sentence or thought, give start/end seconds, what is said (paraphrase), classify it (hook / claim / number / story / tool_mention / roadmap / question / transition / content), and describe what is shown on screen."

Long videos: ask in windows (0–300 s, 300–600 s, ...) and stitch; single answers compress too much.

### Finding harvestable proof clips

`jockey_search` scoped to the project store, `modalities:["visual"]` for on-screen content:
- "dashboard showing profits / results"
- "terminal or code editor running commands"
- "successful order confirmation on screen"
Each hit returns item id + clip times; verify with a local frame extract before putting it in the EDL.

### Where does the intro end?

`jockey_query`: "At what timestamp does the speaker stop setting up/promising and start the actual tutorial content? What sentence marks the transition?"

## Caveats

- `jockey_query` answers are grounded but compress detail — for anything frame-precise (exact cut points, PiP position), trust local ffmpeg frames over the model's description.
- `jockey_search` clip boundaries are approximate; pad ±1 s and verify frames.
- HLS URLs in item listings are playable previews of the indexed copy — handy for the user, not for editing (edit from the local file).

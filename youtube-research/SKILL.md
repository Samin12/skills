---
name: youtube-research
description: "Use this skill when the user asks to research YouTube video ideas, find outlier videos, analyze their channel performance, find trending topics for YouTube, do TubeLab research, cross-reference outliers with channel data, or generate video idea reports."
license: MIT
metadata:
  author: samin
  version: "1.0.0"
  requires-bins: "ytstudio,curl,python3"
env:
  - TUBELAB_API_KEY
---

# YouTube Research Skill

You are a YouTube research agent. You combine **TubeLab** (outlier video database) with **ytstudio** (YouTube Studio CLI) to find data-backed video ideas. You research what's working in any niche, cross-reference it with the creator's own channel performance, and deliver actionable video ideas.

## Tools at Your Disposal

### 1. ytstudio CLI (Channel Data)

Access the creator's own YouTube Studio data.

```bash
# Channel overview
ytstudio status

# List videos (paginate with --page-token)
ytstudio videos list --limit 20
ytstudio videos list --limit 20 --sort views    # sort by: date, views, likes
ytstudio videos list --limit 20 --output json    # formats: table, json, csv

# Video details
ytstudio videos show VIDEO_ID

# Update video metadata (dry-run by default, add --execute to apply)
ytstudio videos update VIDEO_ID --title "New Title" --description "New desc" --tags "tag1,tag2"

# Bulk search-replace across videos (dry-run by default)
ytstudio videos search-replace --search "old text" --replace "new text" --field title --limit 10
ytstudio videos search-replace --search "pattern" --replace "new" --field description --regex

# Analytics
ytstudio analytics overview                        # last 28 days
ytstudio analytics overview --days 90              # custom range
ytstudio analytics video VIDEO_ID                  # per-video stats
ytstudio analytics query --metrics views,likes --dimensions day --days 30   # custom query
ytstudio analytics metrics                         # list all available metrics
ytstudio analytics dimensions                      # list all available dimensions

# Comments
ytstudio comments list                             # recent comments
ytstudio comments list --video VIDEO_ID            # comments on specific video
ytstudio comments list --status held               # held for review
ytstudio comments publish COMMENT_ID1 COMMENT_ID2  # approve comments
ytstudio comments reject COMMENT_ID1 --ban         # reject + ban
```

### 2. TubeLab API (Outlier Research)

Search 4M+ outlier videos and 400K+ channels. The API key is provided via the `TUBELAB_API_KEY` environment variable.

**Base URL:** `https://public-api.tubelab.net/v1`
**Auth:** `Authorization: Api-Key $TUBELAB_API_KEY`
**Rate Limit:** 10 requests/minute

#### Search Outliers (5 credits)
```bash
curl -s 'https://public-api.tubelab.net/v1/search/outliers?query=SEARCH_TERM&size=20&sortBy=averageViewsRatio&sortOrder=desc&language=en&subscribersCountFrom=5000&subscribersCountTo=100000&type=video&publishedAtFrom=2025-06-01T00:00:00Z' \
  -H "Authorization: Api-Key $TUBELAB_API_KEY"
```

**Key parameters:**
- `query` - Search terms (URL-encoded)
- `sortBy` - `views`, `zScore`, `averageViewsRatio`, `publishedAt`, `revenue`, `rpm`
- `sortOrder` - `asc` or `desc`
- `type` - `video` or `short`
- `viewCountFrom` / `viewCountTo` - Filter by view range
- `averageViewsRatioFrom` / `averageViewsRatioTo` - How much video overperformed channel avg
- `zScoreFrom` / `zScoreTo` - Statistical outlier score
- `subscribersCountFrom` / `subscribersCountTo` - Channel size filter
- `publishedAtFrom` / `publishedAtTo` - Date range (ISO 8601)
- `durationFrom` / `durationTo` - Video length in seconds
- `language` - ISO 639-1 codes (e.g., `en`)
- `titlePattern` - Regex pattern for titles
- `excludeKeyword` - Terms to exclude
- `channelId` - Filter to specific channel
- `size` - Results per page (max 40)
- `from` - Pagination offset

**Response fields per hit:**
- `snippet.title`, `snippet.channelTitle`, `snippet.channelHandle`, `snippet.channelSubscribers`
- `snippet.publishedAt`, `snippet.duration`, `snippet.language`
- `statistics.viewCount`, `statistics.likeCount`, `statistics.commentCount`
- `statistics.zScore` - How many standard deviations above channel mean
- `statistics.averageViewsRatio` - Views / channel average (5x = 5 times normal)
- `statistics.isPositiveOutlier` / `isNegativeOutlier`
- `classification.isFaceless`, `classification.quality`

#### Similar Outliers (5 credits)
```bash
curl -s 'https://public-api.tubelab.net/v1/search/outliers/related?videoId=VIDEO_ID&size=20' \
  -H "Authorization: Api-Key $TUBELAB_API_KEY"
```

Also accepts `title`, `relatedChannelId`, `thumbnailVideoId` params. Same metric filters as outliers endpoint.

#### Search Channels (10 credits)
```bash
curl -s 'https://public-api.tubelab.net/v1/search/channels?query=SEARCH_TERM&sortBy=avgViewsToSubscribersRatio&sortOrder=desc&language=en&size=20' \
  -H "Authorization: Api-Key $TUBELAB_API_KEY"
```

#### Channel Videos (cost varies)
```bash
curl -s "https://public-api.tubelab.net/v1/channel/videos/CHANNEL_ID" \
  -H "Authorization: Api-Key $TUBELAB_API_KEY"
```

#### Video Transcript (cost varies)
```bash
curl -s "https://public-api.tubelab.net/v1/video/transcript/VIDEO_ID" \
  -H "Authorization: Api-Key $TUBELAB_API_KEY"
```

Returns full transcript text + timed segments.

#### Video Comments (cost varies)
```bash
curl -s "https://public-api.tubelab.net/v1/video/comments/VIDEO_ID" \
  -H "Authorization: Api-Key $TUBELAB_API_KEY"
```

Returns last 100 comments.

#### Check Credits (free)
```bash
curl -s 'https://public-api.tubelab.net/v1/credits/balance' \
  -H "Authorization: Api-Key $TUBELAB_API_KEY"
```

## Key Metrics Explained

- **averageViewsRatio** - Video views / channel average views. 10x = 10 times the channel's normal. **This is your primary outlier signal.** Anything above 5x is a strong outlier.
- **zScore** - Statistical measure of deviation from channel mean. Above 3.0 = statistically very significant.
- **isPositiveOutlier** - Video significantly overperformed its channel.
- **viewVariationCoefficient** - How consistent a channel's views are (lower = more consistent).

## Research Workflow

### Step 1: Understand the Channel
```bash
ytstudio status
ytstudio analytics overview
ytstudio videos list --limit 40 --sort views   # find their top performers
```

Identify:
- Channel size and growth rate
- Average views per video
- Top 3-5 performing videos (these are the creator's own outliers)
- Common title patterns in top videos
- Content themes that resonate

### Step 2: Search for External Outliers

Run 3-6 TubeLab queries across the creator's niches. Use parallel queries when possible. Filter for channels in a similar subscriber range (peer group).

**Good search strategy:**
- Search 1: Core topic (e.g., "Claude Code tutorial")
- Search 2: Adjacent topic (e.g., "AI agent automation")
- Search 3: Specific sub-niche (e.g., "MCP server")
- Search 4: Format-specific (e.g., "vibe coding build app")

**Always use these filters:**
- `subscribersCountFrom=5000&subscribersCountTo=150000` (peer group)
- `language=en`
- `publishedAtFrom=` (last 6-12 months)
- `sortBy=averageViewsRatio&sortOrder=desc` (find true outliers)

### Step 3: Parse and Rank Results

For each result, extract with Python:
```python
import json, sys
data = json.load(sys.stdin)
for h in data['hits']:
    s = h['snippet']
    st = h['statistics']
    print(f'{s["title"]}')
    print(f'  @{s["channelHandle"]} ({s["channelSubscribers"]:,} subs)')
    print(f'  Views: {st["viewCount"]:,} | Ratio: {st["averageViewsRatio"]:.1f}x | z: {st["zScore"]:.1f}')
    print(f'  {s["duration"]//60}m | {s["publishedAt"][:10]}')
```

### Step 4: Cross-Reference

Compare external outliers with the creator's own data:
- Which outlier topics overlap with the creator's existing content?
- Which outlier formats match the creator's style?
- Where are the gaps - topics the creator hasn't covered but clearly have demand?

### Step 5: Generate Video Ideas

For each promising outlier, craft a specific video idea:
- **Title:** Adapted to the creator's voice and proven title patterns
- **Why it'll work:** Reference the outlier data (ratio, views, z-score)
- **Their angle:** What makes their version unique vs the original

### Step 6: Generate PDF Report

Use the report generator script to create a professional PDF:

```bash
python3 ~/.claude/skills/youtube-research/scripts/generate_report.py \
  --input /path/to/data.json \
  --output /path/to/report.pdf \
  --channel-name "Channel Name" \
  --date "March 9, 2026"
```

The JSON input should follow this structure:
```json
{
  "channel": {
    "name": "Channel Name",
    "handle": "@handle",
    "subscribers": 21900,
    "total_videos": 216
  },
  "analytics": {
    "views_28d": 321700,
    "watch_hours_28d": 22197,
    "subs_gained_28d": 5318
  },
  "queries_run": 6,
  "credits_used": 35,
  "tiers": [
    {
      "name": "TIER 1: NUCLEAR OUTLIERS (10x+)",
      "color": [220, 50, 50],
      "description": "These videos performed 10x+ above their channel average.",
      "outliers": [
        {
          "rank": 1,
          "title": "Video Title",
          "channel": "@handle",
          "subs": "20.3K",
          "views": "220,365",
          "ratio": "40.5",
          "zscore": "10.0",
          "video_id": "abc123",
          "duration": "46 min",
          "your_angle": "How you'd make this video differently."
        }
      ]
    }
  ],
  "video_ideas": [
    {
      "rank": 1,
      "idea": "Video Title Idea",
      "why": "Why this will work based on data",
      "reference": "Based on: X outlier"
    }
  ],
  "patterns": [
    {
      "number": 1,
      "title": "Pattern Name",
      "description": "What the data shows about this pattern."
    }
  ],
  "closing_note": "Summary of the creator's unique advantage."
}
```

After generating the PDF, open it:
```bash
open /path/to/report.pdf   # macOS
```

## Rules

- Always check `credits/balance` before heavy research to avoid running out
- Use parallel curl calls when possible to speed up research
- Filter for the creator's peer group (similar subscriber count channels)
- Focus on averageViewsRatio over raw view counts - a 10x on a 5K channel is more actionable than a 2x on a 500K channel
- Deduplicate results across queries before presenting
- When generating video ideas, use the creator's proven title patterns from their own top-performing videos
- Present outliers in tiers: Tier 1 (10x+), Tier 2 (5-10x), Tier 3 (3-5x)
- Always generate a PDF report for easy reference
- Do NOT ask for confirmation at every step. Research, analyze, generate. Present the results.

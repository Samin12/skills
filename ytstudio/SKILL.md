# ytstudio - YouTube Analytics & Management

YouTube channel analytics and video management via the ytstudio CLI.

## When to Use

- User asks about YouTube performance, stats, or analytics
- User wants to know how a video is doing
- User asks about subscriber growth, views, watch time, revenue
- User mentions "YouTube", "channel", "my videos", "how's the channel doing"
- Any content strategy discussion that needs YouTube data
- Comparing video performance
- Revenue tracking

## Authentication

- **CLI:** `ytstudio` (installed via `uv tool install`)
- **Account:** samin.yasar12@gmail.com
- **Channel:** Samin Yasar
- **Credentials:** ~/.config/ytstudio-cli/client_secrets.json

## Commands

### Channel Overview
```bash
# Quick status check
ytstudio status

# Analytics overview (default 28 days)
ytstudio analytics overview -d 28 -o json

# Custom time range
ytstudio analytics overview -d 7 -o json    # last week
ytstudio analytics overview -d 90 -o json   # last quarter
```

### Per-Video Analytics
```bash
# Get analytics for a specific video
ytstudio analytics video VIDEO_ID

# List recent videos
ytstudio videos list

# Show video details
ytstudio videos show VIDEO_ID
```

### Custom Queries
```bash
# Custom analytics query with any metrics and dimensions
ytstudio analytics query --help

# List available metrics
ytstudio analytics metrics

# List available dimensions
ytstudio analytics dimensions
```

### Comments
```bash
ytstudio comments
```

### Video Management
```bash
# Update video metadata
ytstudio videos update VIDEO_ID

# Bulk search and replace across videos
ytstudio videos search-replace
```

## Key Metrics Available

### Core Metrics
| Metric | Description |
|--------|-------------|
| views | Total views |
| estimatedMinutesWatched | Total watch time in minutes |
| averageViewDuration | Avg playback length (seconds) |
| subscribersGained | New subs gained |
| subscribersLost | Subs lost |
| likes / dislikes | Engagement |
| comments | Comment count |
| shares | Share count |

### Revenue Metrics
| Metric | Description |
|--------|-------------|
| estimatedRevenue | Total net revenue |
| estimatedAdRevenue | Ad net revenue |
| grossRevenue | Gross ad revenue |
| monetizedPlaybacks | Playbacks with ads |
| cpm | Revenue per 1000 ad impressions |
| playbackBasedCpm | Revenue per 1000 playbacks |

### Reach Metrics
| Metric | Description |
|--------|-------------|
| videoThumbnailImpressions | Thumbnail shown count |
| videoThumbnailImpressionsClickThroughRate | Thumbnail CTR |

## Key Dimensions
- `day` / `month` - Time breakdown
- `video` - Per-video breakdown
- `country` / `city` - Geographic
- `deviceType` - Mobile/desktop/tablet/TV
- `insightTrafficSourceType` - Where traffic comes from
- `creatorContentType` - Shorts vs videos vs live
- `ageGroup` / `gender` - Audience demographics
- `subscribedStatus` - Sub vs non-sub viewers

## Patterns

### Quick health check
```bash
ytstudio analytics overview -d 7 -o json
```

### Compare periods
Run overview for different day ranges and compare the numbers.

### Find best performing videos
Use custom query with video dimension + views/engagement metrics.

## Related Tools
- **ScrapeCreators** - For YouTube video transcripts (content analysis)
- **ytstudio** - For YouTube analytics (performance data)
- These complement each other: ScrapeCreators for WHAT the content says, ytstudio for HOW it performs

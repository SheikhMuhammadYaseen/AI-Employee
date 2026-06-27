# MCP Social Server Contracts

**Server**: `mcp_social` | **Entry Point**: `src/mcp/mcp_social.py`
**Transport**: stdio | **Platforms**: LinkedIn, Mastodon, Facebook, Instagram, X (Twitter)

## Tool: `mastodon_post`

Post content to Mastodon. Migrated from Silver's MCP server.

### Input

```json
{
  "content": "string (required) — Post text (max 500 chars).",
  "visibility": "string (optional) — 'public', 'unlisted', 'private', 'direct' (default: 'public').",
  "instance_url": "string (optional) — Mastodon instance URL (default: from .env).",
  "access_token": "string (optional) — Override token (default: from .env)."
}
```

### Output (success)

```json
{
  "status": "posted",
  "platform": "mastodon",
  "post_id": "109876543210",
  "url": "https://mastodon.social/@user/109876543210",
  "timestamp": "2026-02-12T10:12:45Z"
}
```

### Output (error)

```json
{
  "status": "error",
  "platform": "mastodon",
  "error": "Rate limit exceeded. Retry after 300 seconds.",
  "retries_attempted": 3
}
```

### Acceptance Criteria
- Post appears on Mastodon instance
- Content within 500-char limit (error if exceeded)
- Audit log entry written

---

## Tool: `facebook_post`

Post content to a Facebook Page via Meta Graph API.

### Input

```json
{
  "message": "string (required) — Post text.",
  "page_id": "string (optional) — Facebook Page ID (default: from .env).",
  "access_token": "string (optional) — Page Access Token (default: from .env)."
}
```

### Output (success)

```json
{
  "status": "posted",
  "platform": "facebook",
  "post_id": "123456789_987654321",
  "url": "https://facebook.com/123456789_987654321",
  "timestamp": "2026-02-12T10:15:00Z"
}
```

### Output (error)

```json
{
  "status": "error",
  "platform": "facebook",
  "error": "Invalid access token",
  "retries_attempted": 3
}
```

### Acceptance Criteria
- Post appears on Facebook Page
- No character limit enforced (platform has no practical limit)
- Audit log entry written

---

## Tool: `instagram_post`

Post content to Instagram via Meta Graph API (business account).

### Input

```json
{
  "caption": "string (required) — Post caption (max 2200 chars).",
  "image_url": "string (optional) — Public URL of image. Required for feed posts; omit for text-only (not supported by Instagram feed).",
  "ig_user_id": "string (optional) — Instagram user ID (default: from .env).",
  "access_token": "string (optional) — Page Access Token (default: from .env)."
}
```

### Output (success)

```json
{
  "status": "posted",
  "platform": "instagram",
  "post_id": "17895695668004550",
  "timestamp": "2026-02-12T10:20:00Z"
}
```

### Output (error)

```json
{
  "status": "error",
  "platform": "instagram",
  "error": "Image URL required for Instagram feed posts",
  "retries_attempted": 0
}
```

### Acceptance Criteria
- Post appears on Instagram business account
- Caption within 2200-char limit
- Image required for feed posts (clearly documented)
- Audit log entry written

---

## Tool: `x_post`

Post a tweet to X (Twitter) via API v2.

### Input

```json
{
  "text": "string (required) — Tweet text (max 280 chars)."
}
```

### Output (success)

```json
{
  "status": "posted",
  "platform": "x",
  "tweet_id": "1234567890123456789",
  "url": "https://x.com/user/status/1234567890123456789",
  "timestamp": "2026-02-12T10:25:00Z"
}
```

### Output (error — character limit)

```json
{
  "status": "error",
  "platform": "x",
  "error": "Content exceeds 280-character limit (got 312 chars). Shorten before posting.",
  "retries_attempted": 0
}
```

### Acceptance Criteria
- Tweet appears on X account
- 280-char limit enforced BEFORE API call (spec FR-007)
- Fallback to Mastodon logged if X API unavailable
- Audit log entry written

---

## Tool: `social_engagement_summary`

Generate a weekly engagement summary across all platforms.

### Input

```json
{
  "start_date": "string (required) — YYYY-MM-DD.",
  "end_date": "string (required) — YYYY-MM-DD."
}
```

### Output (success)

```json
{
  "status": "success",
  "period_start": "2026-02-03",
  "period_end": "2026-02-09",
  "platforms": [
    {
      "platform": "mastodon",
      "posts_count": 5,
      "reach": null,
      "engagement_rate": null,
      "available": false,
      "note": "Mastodon does not provide reach metrics"
    },
    {
      "platform": "facebook",
      "posts_count": 3,
      "reach": 1200,
      "engagement_rate": 4.5,
      "available": true,
      "note": null
    },
    {
      "platform": "x",
      "posts_count": 4,
      "reach": null,
      "engagement_rate": null,
      "available": false,
      "note": "Free tier — engagement metrics unavailable"
    }
  ]
}
```

### Acceptance Criteria
- Counts posts from `/Done` folder matching date range and platform type
- Queries platform APIs for engagement where available
- Clearly notes unavailable metrics with reason
- Used by CEO Briefing (FR-009)

---

## Tool: `health_check`

Check social MCP server status and platform reachability.

### Input

```json
{}
```

### Output

```json
{
  "status": "ok",
  "server": "mcp_social",
  "platforms": {
    "mastodon": "reachable",
    "facebook": "reachable",
    "instagram": "reachable",
    "x": "unreachable"
  },
  "timestamp": "2026-02-12T10:00:00Z"
}
```

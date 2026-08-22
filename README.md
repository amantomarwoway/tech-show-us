# USA News YouTube Bot - 100% FREE & Copyright Safe

This bot automatically discovers trending USA news from reliable RSS feeds, verifies it from 2+ sources, and publishes original news-explainer videos to YouTube.

**ZERO COST STACK:**
- GitHub Actions (Free Tier)
- RSS Feeds: Reuters, AP, BBC, NPR, NBC (Official & Legal)
- Google Gemini API (Free Tier)
- Piper TTS (Local, Free, Open Source) + espeak-ng fallback
- FFmpeg + MoviePy + Pillow (Open Source)
- YouTube Data API v3 (Free Quota)

**WHAT IT DOES:**
1. Fetch news from RSS (No scraping, respects ToS)
2. Verify: Requires 2 independent sources, rejects single unverified source
3. Trend Score: recency + source_count + reliability
4. Duplicate Detection: SQLite DB `data/news_history.db`
5. Script Gen: Original script, no copy-paste
6. Fact Check: Second validation before video
7. Video: Text-based video, no copyrighted footage
8. Thumbnail: Original via Pillow
9. Upload: YouTube API with full source attribution

**SETUP:**
1. Enable YouTube Data API v3 in Google Cloud
2. Create OAuth Desktop Credentials
3. Get Refresh Token from OAuth Playground (scope: youtube.upload)
4. Add GitHub Secrets: GEMINI_API_KEY, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN
5. Push code, run workflow from Actions tab.

**IMPORTANT:**
- GitHub Actions schedule is not guaranteed exact time.
- Automation does not guarantee YouTube monetization. Videos provide original narration and verification.
- All visuals are original text-based to avoid copyright.

**FREE vs PAID:**
FREE: Everything in this repo.
POTENTIALLY PAID: If you exceed YouTube API quota (10k units/day) or GitHub Actions free minutes (2000 min/month), you may need to wait or upgrade. No paid API required for core function.

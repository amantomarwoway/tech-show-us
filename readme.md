# 🚀 GOD LEVEL YOUTUBE SHORTS BOT

**Zero-Cost, Fully Automated, Editorial Intelligence System**

## 🎯 Features

- ✅ Multi-source news collection (RSS, Google News, Trends, Reddit)
- ✅ Trend detection engine (multi-signal scoring)
- ✅ Fact-checking engine (2 of 3 pass rule)
- ✅ Global English audience model
- ✅ AI script generation (Gemini free tier)
- ✅ Free TTS (Piper - offline)
- ✅ Free visual assets (Pexels, Pixabay)
- ✅ Retention-optimized video (0.8s clips, NTSC fps)
- ✅ YouTube upload + analytics
- ✅ Comment engine (10 replies max)
- ✅ Self-learning performance system
- ✅ 100% FREE (only free tiers)

## 📋 Prerequisites

- Python 3.11+
- FFmpeg
- GitHub account (for Actions)
- Free API keys (Gemini, Pexels)

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/news-shorts-bot.git
cd news-shorts-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Get Free API Keys

| Service | URL | Free Tier |
|---------|-----|-----------|
| Gemini | [aistudio.google.com](https://aistudio.google.com/apikey) | 15 req/min |
| Pexels | [pexels.com/api](https://www.pexels.com/api/) | 200 req/hour |
| Pixabay | [pixabay.com/api](https://pixabay.com/api/docs/) | 100 req/min |

### 5. Run Locally
```bash
python main.py
```

### 6. Deploy to GitHub Actions

1. Push to GitHub
2. Add secrets (Settings → Secrets → Actions):
   - `GEMINI_API_KEY`
   - `PEXELS_API_KEY`
   - `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`
3. Enable Actions
4. Bot runs every 6 hours automatically

## 📊 Pipeline (5 Legs)

```
LEG 1: RESEARCH GOD
  ↓ RSS + Google News + Trends + Reddit
LEG 2: EDITOR GOD
  ↓ Pexels + Pixabay + Giphy
LEG 3: BOSS APPROVAL
  ↓ Quality gate + Fact check
LEG 4: UPLOADER GOD
  ↓ YouTube API v3
LEG 5: SELF EVOLUTION
  ↓ Performance learning
```

## 💰 Cost Breakdown

| Component | Cost | Limit |
|-----------|------|-------|
| News Collection | FREE | Unlimited |
| AI Script | FREE | 15 req/min |
| TTS (Piper) | FREE | Local |
| Visuals (Pexels) | FREE | 200/hr |
| Video (MoviePy) | FREE | Local |
| YouTube Upload | FREE | 10K units/day |
| **TOTAL** | **$0/month** | |

## ⚠️ Important Notes

- **Truth First**: Bot never publishes unverified claims
- **YouTube Compliant**: No manipulation, no spam
- **Copyright Safe**: Only licensed assets used
- **Semi-Auto Mode**: Recommended for political content

## 📁 Project Structure

```
news_shorts_bot/
├── main.py
├── requirements.txt
├── src/
│   ├── config.py
│   ├── database.py
│   ├── collectors/
│   ├── intelligence/
│   ├── verification/
│   ├── writing/
│   ├── media/
│   ├── youtube/
│   ├── safety/
│   └── learning/
├── data/
├── output/
└── logs/
```

## 🔧 Troubleshooting

**No videos generated?**
- Check API keys in `.env`
- Check logs in `logs/bot.log`

**Upload fails?**
- Verify YouTube credentials
- Check quota at [console.cloud.google.com](https://console.cloud.google.com)

**TTS not working?**
- Piper model downloads on first run
- Check `models/` directory

## 📜 License

MIT License - Free for commercial use

## 🙏 Credits

- [Piper TTS](https://github.com/rhasspy/piper) - Free offline TTS
- [MoviePy](https://zulko.github.io/moviepy/) - Video editing
- [Pexels](https://www.pexels.com/) - Free stock videos

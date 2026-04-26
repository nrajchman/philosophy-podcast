# Philosophy for Life — 100% Free Podcast Pipeline

Daily philosophy podcast for MBA professionals. Fully automated, zero cost.

```
Gemini 1.5 Flash (script) → Google Cloud TTS WaveNet (audio) → GitHub Releases (hosting) → Spotify
```

**Total cost: $0/month**

---

## How it works

| Step | Tool | Free tier |
|------|------|-----------|
| Script generation | Gemini 1.5 Flash | 1,500 requests/day free |
| Text → Audio | Google Cloud TTS WaveNet (en-US-Wavenet-D) | 1M characters/month free |
| Audio hosting | GitHub Releases | Free on public repos |
| RSS + Distribution | Submit feed URL to Spotify for Creators | Free forever |
| Automation | GitHub Actions | 2,000 min/month free |

A 20-min episode ≈ 15,000 characters. The free tier covers **66 episodes/month** — more than enough.

---

## Setup (15 minutes)

### 1. Get your free API keys

**Gemini API key** (for script generation):
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Click "Get API key" → Create API key
3. Copy it — this is your `GEMINI_API_KEY`

**Google Cloud TTS key** (for audio):
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (e.g. "philosophy-podcast")
3. Enable the **Cloud Text-to-Speech API**
4. Go to APIs & Services → Credentials → Create Credentials → API Key
5. Copy it — this is your `GOOGLE_TTS_KEY`
6. No billing setup needed for the free tier (1M chars/month)

### 2. Create a GitHub repo

1. Create a new **public** repo on GitHub (e.g. `philosophy-podcast`)
2. Upload all files from this folder to the repo root
3. Make sure `.github/workflows/daily_free.yml` is in the right path

### 3. Add secrets to GitHub

Go to your repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret name | Value |
|-------------|-------|
| `GEMINI_API_KEY` | Your Gemini API key from step 1 |
| `GOOGLE_TTS_KEY` | Your Google Cloud TTS key from step 1 |

### 4. Run your first episode

Go to Actions → "Daily philosophy episode (free)" → Run workflow

The first run will:
- Generate the script for Episode 1 using Gemini
- Convert it to audio using Google TTS (voice: en-US-Wavenet-D, deep male)
- Upload the MP3 and feed.xml to GitHub Releases

### 5. Submit to Spotify

1. Go to [creators.spotify.com](https://creators.spotify.com)
2. Click "Add your podcast" → "I have an RSS feed"
3. Paste this URL (replace with your GitHub username and repo name):
   ```
   https://github.com/YOUR_USERNAME/YOUR_REPO/releases/download/episodes-latest/feed.xml
   ```
4. Spotify reviews it in 24-72 hours. After approval, every new episode appears automatically.

Same RSS feed works for Apple Podcasts, Amazon Music, Pocket Casts, and any other app.

---

## Update `generate_episode_free.py` before running

Edit these 4 lines at the top of the script:

```python
PODCAST_EMAIL    = "your@email.com"           # your email
PODCAST_BASE_URL = "https://github.com/YOUR_USERNAME/YOUR_REPO/releases/download/episodes-latest"
```

---

## Daily automation

The GitHub Actions workflow runs every day at 6:00 AM Santiago time (09:00 UTC).
It automatically picks the next episode that hasn't been generated yet.

To run a specific episode manually:
- Go to Actions → Run workflow → enter episode number

To preview a script without generating audio:
- Set `dry_run` to `true` in the manual trigger

---

## Voice quality

The voice used is **en-US-Wavenet-D** — Google's deep, authoritative male WaveNet voice.
It's not ElevenLabs-quality, but it's significantly better than standard TTS and sounds
professional for an educational podcast.

To try a different voice, change `TTS_VOICE` in `generate_episode_free.py`:
- `en-US-Wavenet-B` — slightly warmer male
- `en-US-Wavenet-I` — younger male voice
- `en-US-Neural2-D` — Neural2 (newer architecture, also free tier)

Preview all voices at: [cloud.google.com/text-to-speech](https://cloud.google.com/text-to-speech#section-2)

---

## File structure

```
philosophy-podcast/
├── generate_episode_free.py       # main script
├── feed.xml                       # RSS feed (auto-generated)
├── episodes/
│   ├── ep01.mp3
│   ├── ep01_script.txt
│   ├── ep02.mp3
│   └── metadata.json
└── .github/
    └── workflows/
        └── daily_free.yml
```

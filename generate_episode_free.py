#!/usr/bin/env python3
"""
Philosophy Podcast — 100% Free Pipeline
Gemini (script) → Google Cloud TTS WaveNet (audio) → Spotify for Creators (publish)
Automated daily via GitHub Actions. Zero cost.

Requirements:
    pip install google-generativeai google-cloud-texttospeech requests

Environment variables:
    GEMINI_API_KEY        → free at aistudio.google.com
    GOOGLE_TTS_KEY        → free tier at console.cloud.google.com (1M chars/month free)
    SPOTIFY_EMAIL         → your Spotify for Creators login
    SPOTIFY_PASSWORD      → your Spotify for Creators password
"""

import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY", "")
GOOGLE_TTS_KEY   = os.environ.get("GOOGLE_TTS_KEY", "")

OUTPUT_DIR  = Path("./episodes")
RSS_FILE    = Path("./feed.xml")
META_FILE   = OUTPUT_DIR / "metadata.json"

# Google Cloud TTS — best free male voice in English
# en-US-Wavenet-D = deep, authoritative male voice (academic tone)
TTS_VOICE        = "en-US-Wavenet-D"
TTS_LANGUAGE     = "en-US"
TTS_SPEAKING_RATE = 0.95   # slightly slower = more deliberate, academic feel
TTS_PITCH        = -1.5    # slightly lower pitch = more gravitas

# Podcast metadata (used in feed.xml for Spotify)
PODCAST_TITLE    = "Philosophy for Life"
PODCAST_DESC     = "A daily philosophy podcast for professionals: stoicism, existentialism, and the great thinkers applied to modern life. MBA-level depth, conversational tone."
PODCAST_AUTHOR   = "Philosophy for Life"
PODCAST_EMAIL    = "n.rajchman@gmail.com"           # ← change this
PODCAST_BASE_URL = "https://github.com/nrajchman/philosophy-podcast/releases/download/episodes-latest"  # ← change to your public URL
PODCAST_IMAGE    = f"{PODCAST_BASE_URL}/cover.jpg"
PODCAST_LANGUAGE = "en"

# ── Episode plan ──────────────────────────────────────────────────────────────
EPISODES = [
    {
        "number": 1, "week": "W1",
        "title": "Socrates: The Unexamined Life Is Not Worth Living",
        "prompt": """Write a 20-minute podcast script about Socrates as a model of philosophical life.

Audience: professionals aged 30-40 with MBA backgrounds. They're time-poor, results-driven, and want ideas that actually change how they live and lead — not academic theory.

Tone: Like a brilliant colleague giving you the most interesting talk of your week. Conversational, direct, intellectually rigorous but never dry. American English.

Connect Socratic ideas to: leadership blind spots, the gap between stated and actual values, how high performers delude themselves about what matters, the courage to ask hard questions in corporate settings.

Structure (separate each section with the exact marker ---SECTION---):

INTRO (2 min): A sharp hook — place us in a scene or tension. Why does Socrates matter RIGHT NOW to someone running a team or building a career?

DEVELOPMENT (15 min): Cover the Socratic method, self-knowledge (not the cliché, the radical version), virtue as knowledge, and the examined life. Weave in concrete examples from professional life — board meetings, performance reviews, career inflection points. At least 2 vivid analogies.

CLOSE (3 min): A synthesis + one transformative question for the listener to sit with this week + one concrete practice they can do TODAY.

Write for audio: no bullet points, no headers, no markdown. Pure flowing prose that sounds natural when read aloud. Vary sentence length. Use rhetorical questions."""
    },
    {
        "number": 2, "week": "W1",
        "title": "Self-Knowledge: The Most Underrated Executive Skill",
        "prompt": """Write a 20-minute podcast script on Socratic self-knowledge as a professional superpower.

Audience: MBA-level professionals 30-40. Connect 'know thyself' to: cognitive biases in business decisions, the self-deception patterns of high achievers, the gap between leadership identity and actual behavior, what makes some executives grow and others plateau.

Reference real psychological concepts (Dunning-Kruger, confirmation bias, identity-protective cognition) without being academic.

Structure (separate with ---SECTION---): INTRO (2 min) / DEVELOPMENT (15 min) / CLOSE (3 min) with weekly practice.

Write for audio only. No markdown."""
    },
    {
        "number": 3, "week": "W2",
        "title": "Epicurus: Why Everything You're Chasing Might Be Wrong",
        "prompt": """Write a 20-minute podcast script on Epicurus and genuine wellbeing for ambitious professionals.

Audience: MBAs 30-40 who've hit many of their goals and feel something's off. Connect Epicurean pleasure classification (necessary/unnecessary/empty) to: lifestyle inflation, hedonic adaptation, the research on money and happiness (cite Kahneman, Killingsworth), what actually predicts life satisfaction vs. what professionals pursue.

Structure (separate with ---SECTION---): INTRO (2 min) / DEVELOPMENT (15 min) / CLOSE (3 min) with practice.

Audio prose only. No markdown."""
    },
    {
        "number": 4, "week": "W2",
        "title": "The Philosophy of Enough: Strategic Simplicity",
        "prompt": """Write a 20-minute podcast script on philosophical simplicity as strategic advantage.

Audience: MBA professionals 30-40 prone to overcommitment and optimization addiction. Connect Epicurus and the Cynics to: essentialism in career design, the hidden costs of accumulation, the decision fatigue research, Warren Buffett's 'not-to-do list' strategy, Cal Newport's digital minimalism.

Structure (separate with ---SECTION---): INTRO (2 min) / DEVELOPMENT (15 min) / CLOSE (3 min) with practice.

Audio prose only. No markdown."""
    },
    {
        "number": 5, "week": "W3",
        "title": "Epictetus: Stop Managing What You Can't Control",
        "prompt": """Write a 20-minute podcast script on the Stoic dichotomy of control for leaders.

Audience: MBA professionals 30-40 managing teams, outcomes, and stakeholder expectations. Connect Epictetus's core distinction to: stress management research, the OKR framework (inputs vs. outcomes), how top performers separate signal from noise, reacting to market volatility, dealing with unfair feedback.

Mention the connection to modern CBT — this isn't just philosophy, it's evidence-based cognitive science.

Structure (separate with ---SECTION---): INTRO (2 min) / DEVELOPMENT (15 min) / CLOSE (3 min) with a weekly drill.

Audio prose only. No markdown."""
    },
    {
        "number": 6, "week": "W3",
        "title": "Stoic Emotions: Feel Everything, Be Ruled by Nothing",
        "prompt": """Write a 20-minute podcast script on the Stoic theory of emotions for high-pressure professionals.

Audience: MBAs 30-40 making decisions under emotional load — negotiations, layoffs, investor pressure. Connect Stoic emotion theory (passions as false judgments, eupatheiai as healthy states) to: emotional intelligence in leadership, the neuroscience of decision-making under stress (Damasio's somatic marker hypothesis), why the best negotiators control framing not feelings.

Structure (separate with ---SECTION---): INTRO (2 min) / DEVELOPMENT (15 min) / CLOSE (3 min) with practice.

Audio prose only. No markdown."""
    },
    {
        "number": 7, "week": "W4",
        "title": "Marcus Aurelius: Leading When Nobody's Watching",
        "prompt": """Write a 20-minute podcast script on Marcus Aurelius as a model of leadership philosophy.

Audience: MBA professionals 30-40 in leadership roles or aspiring to them. Connect the Meditations to: the loneliness of command, managing ego at the top, making decisions with incomplete information, maintaining ethical clarity under institutional pressure. The Meditations as a personal management system, not just philosophy.

Structure (separate with ---SECTION---): INTRO (2 min) / DEVELOPMENT (15 min) / CLOSE (3 min) with the practice of journaling as a leadership tool.

Audio prose only. No markdown."""
    },
    {
        "number": 8, "week": "W4",
        "title": "Seneca: Your Time Is the Only Asset That Doesn't Compound",
        "prompt": """Write a 20-minute podcast script on Seneca's 'On the Shortness of Life' for modern professionals.

Audience: MBAs 30-40 who feel their calendar runs their life. Connect Seneca to: purposeful productivity vs. anxiety-driven busyness, the research on attention residue and deep work (Cal Newport), designing protected time in a corporate calendar, memento mori as a prioritization tool (what would you do differently?).

Structure (separate with ---SECTION---): INTRO (2 min) / DEVELOPMENT (15 min) / CLOSE (3 min) with a time audit practice.

Audio prose only. No markdown."""
    },
    {
        "number": 9, "week": "W5",
        "title": "Nietzsche: When the Map Breaks, How Do You Navigate?",
        "prompt": """Write a 20-minute podcast script on Nietzsche and value creation for professionals in transition.

Audience: MBAs 30-40 experiencing career pivots, identity crises, or questioning whether their current path is really theirs. Connect the death of God (as a metaphor for any collapsed meaning system — a company, an industry, an identity) to: the psychology of career reinvention, nihilism as a phase vs. a destination, will to power as creative self-authorship rather than dominance.

Structure (separate with ---SECTION---): INTRO (2 min) / DEVELOPMENT (15 min) / CLOSE (3 min) with practice.

Audio prose only. No markdown."""
    },
    {
        "number": 10, "week": "W5",
        "title": "The Eternal Return: Would You Live This Life Again?",
        "prompt": """Write a 20-minute podcast script on Nietzsche's eternal return as a decision-making framework.

Audience: MBAs 30-40 making consequential decisions — career moves, relationships, big bets. Connect the eternal return thought experiment to: Jeff Bezos's regret minimization framework, how to evaluate irreversible decisions, amor fati as a strategy for integrating past choices, the difference between regret (useful) and rumination (destructive).

Structure (separate with ---SECTION---): INTRO (2 min) / DEVELOPMENT (15 min) / CLOSE (3 min) with the eternal return exercise.

Audio prose only. No markdown."""
    },
    {
        "number": 11, "week": "W6",
        "title": "Camus: High Performance Without Meaning Is Just Exhaustion",
        "prompt": """Write a 20-minute podcast script on Camus and the absurd for burnt-out high achievers.

Audience: MBAs 30-40 experiencing burnout despite objective success — they've won the game they were told to play and feel hollow. Connect the absurd to: high-performance burnout research (Christina Maslach), the trap of perpetual goal-chasing, how to find engagement within uncertainty rather than despite it. Sisyphus as the ultimate professional — must we imagine him happy?

Structure (separate with ---SECTION---): INTRO (2 min) / DEVELOPMENT (15 min) / CLOSE (3 min) with practice.

Audio prose only. No markdown."""
    },
    {
        "number": 12, "week": "W7",
        "title": "Sartre: You Are Exactly What You Do, Not What You Intend",
        "prompt": """Write a 20-minute podcast script on Sartre and radical responsibility for professionals.

Audience: MBAs 30-40 who know the gap between their intentions and their actual behavior. Connect existence preceding essence to: accountability culture in organizations, bad faith in corporate life (following orders, blaming the system), the difference between aspirational identity and behavioral identity, how Sartre's radical freedom reframes leadership.

Structure (separate with ---SECTION---): INTRO (2 min) / DEVELOPMENT (15 min) / CLOSE (3 min) with practice.

Audio prose only. No markdown."""
    },
    {
        "number": 13, "week": "W7",
        "title": "Simone de Beauvoir: Freedom That Ignores Others Is Just Privilege",
        "prompt": """Write a 20-minute podcast script on de Beauvoir and relational ethics for leaders.

Audience: MBAs 30-40 in positions of influence over others. Connect de Beauvoir's intersubjective freedom to: the ethical responsibilities of leadership, diversity and inclusion as a philosophical (not compliance) project, meritocracy's hidden assumptions, what it means to build organizations where others can actually flourish.

Structure (separate with ---SECTION---): INTRO (2 min) / DEVELOPMENT (15 min) / CLOSE (3 min) with practice.

Audio prose only. No markdown."""
    },
    {
        "number": 14, "week": "W8",
        "title": "Heidegger: Are You Living Your Life or the Life Assigned to You?",
        "prompt": """Write a 20-minute podcast script on Heidegger and authentic existence for career-questioning professionals.

Audience: MBAs 30-40 who have followed the 'right' path but aren't sure it's theirs. Connect Dasein, das Man (the anonymous 'they'), being-toward-death, and authentic vs. inauthentic existence to: social scripts in professional life, how institutions colonize individual identity, using mortality awareness to clarify what actually matters. Accessible Heidegger — no jargon without explanation.

Structure (separate with ---SECTION---): INTRO (2 min) / DEVELOPMENT (15 min) / CLOSE (3 min) with the 'deathbed test' practice.

Audio prose only. No markdown."""
    },
    {
        "number": 15, "week": "W9",
        "title": "Your Philosophy of Life: Build the System That Governs You",
        "prompt": """Write a 20-minute podcast script synthesizing the full 9-week philosophy of life curriculum.

Audience: MBAs 30-40 who've completed the series and are ready to integrate. Synthesize the most actionable tools from each school: what to keep from Stoicism, Epicureanism, Existentialism, Camus, and Nietzsche. How to build a personal philosophy that is coherent, robust, and actually guides decisions. Recommended next readings with selection criteria (why this book for someone at this stage). Philosophy as a daily practice for a 21st-century professional, not an academic hobby.

Structure (separate with ---SECTION---): INTRO (2 min) / DEVELOPMENT (15 min) / CLOSE (3 min) — inspiring, complete, a real ending.

Audio prose only. No markdown."""
    },
]

# ── Script generation (Gemini — free) ────────────────────────────────────────

def generate_script(episode: dict) -> str:
    print(f"  → Generating script with Groq for: {episode['title']}")

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.environ.get('GROQ_API_KEY', '')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "max_tokens": 8192,
            "temperature": 0.8,
            "messages": [
                {
                    
                    "role": "system",
                    "content": """You are a world-class podcast scriptwriter specializing in philosophy for business professionals. 

CRITICAL REQUIREMENTS:
- Scripts must be 3,500 to 4,000 words minimum. This is non-negotiable.
- A 20-minute podcast at normal speaking pace requires approximately 3,500 words.
- Write in flowing natural prose designed to be read aloud.
- Never use bullet points, headers, or markdown formatting.
- Write only the script itself, nothing else.
- Develop each idea fully with examples, analogies, and stories. Do not rush.
- Each section must be substantial: INTRO at least 400 words, DEVELOPMENT at least 2,800 words, CLOSE at least 400 words."""
                                },
                {
                    "role": "user",
                    "content": episode["prompt"]
                }
            ]
        },
        timeout=120
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
def parse_sections(raw: str) -> dict:
    parts = [p.strip() for p in raw.split("---SECTION---") if p.strip()]
    return {
        "intro":      parts[0] if len(parts) > 0 else "",
        "body":       parts[1] if len(parts) > 1 else "",
        "outro":      parts[2] if len(parts) > 2 else "",
        "full":       "\n\n".join(parts)
    }

# ── Audio generation (Google Cloud TTS — free tier) ───────────────────────────

def text_to_speech(text: str, output_path: Path) -> bool:
    print(f"  → Converting to audio with Google Cloud TTS (WaveNet)...")

    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_TTS_KEY}"

    # Split into chunks of 4500 chars (API limit is 5000 bytes)
    chunks = _split_text(text, max_chars=4500)
    audio_chunks = []

    for i, chunk in enumerate(chunks):
        print(f"     chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
        payload = {
            "input": {"text": chunk},
            "voice": {
                "languageCode": TTS_LANGUAGE,
                "name": TTS_VOICE,
                "ssmlGender": "MALE"
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": TTS_SPEAKING_RATE,
                "pitch": TTS_PITCH,
                "effectsProfileId": ["headphone-class-device"]
            }
        }
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code != 200:
            print(f"  ✗ TTS error: {resp.status_code} — {resp.text[:300]}")
            return False

        import base64
        audio_chunks.append(base64.b64decode(resp.json()["audioContent"]))
        time.sleep(0.3)  # be nice to the API

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  ✓ Audio saved: {output_path} ({size_mb:.1f} MB)")
    return True


def _split_text(text: str, max_chars: int = 4500) -> list:
    """Split text at sentence boundaries to stay under API limit."""
    sentences = text.replace("\n\n", " [PARA] ").split(". ")
    chunks, current = [], ""
    for s in sentences:
        candidate = current + s + ". "
        if len(candidate) > max_chars and current:
            chunks.append(current.replace(" [PARA] ", "\n\n").strip())
            current = s + ". "
        else:
            current = candidate
    if current:
        chunks.append(current.replace(" [PARA] ", "\n\n").strip())
    return chunks

# ── RSS feed ──────────────────────────────────────────────────────────────────

def update_rss(all_eps: list):
    from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

    rss = Element("rss", {
        "version": "2.0",
        "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"
    })
    ch = SubElement(rss, "channel")
    SubElement(ch, "title").text = PODCAST_TITLE
    SubElement(ch, "description").text = PODCAST_DESC
    SubElement(ch, "language").text = PODCAST_LANGUAGE
    SubElement(ch, "link").text = PODCAST_BASE_URL
    img = SubElement(ch, "itunes:image"); img.set("href", PODCAST_IMAGE)
    SubElement(ch, "itunes:author").text = PODCAST_AUTHOR
    SubElement(ch, "itunes:explicit").text = "false"
    owner = SubElement(ch, "itunes:owner")
    SubElement(owner, "itunes:name").text = PODCAST_AUTHOR
    SubElement(owner, "itunes:email").text = PODCAST_EMAIL
    cat = SubElement(ch, "itunes:category"); cat.set("text", "Education")

    for ep_data in reversed(all_eps):
        ep   = ep_data["episode"]
        item = SubElement(ch, "item")
        url  = f"{PODCAST_BASE_URL}/episodes/ep{ep['number']:02d}.mp3"
        SubElement(item, "title").text = f"Ep {ep['number']}: {ep['title']}"
        SubElement(item, "description").text = ep_data.get("description", "")
        SubElement(item, "pubDate").text = ep_data.get("pub_date", "")
        SubElement(item, "guid").text = url
        enc = SubElement(item, "enclosure")
        enc.set("url", url); enc.set("type", "audio/mpeg")
        enc.set("length", str(ep_data.get("file_size_bytes", 0)))
        SubElement(item, "itunes:duration").text = str(ep_data.get("duration_seconds", 1200))
        SubElement(item, "itunes:episode").text = str(ep["number"])
        SubElement(item, "itunes:episodeType").text = "full"
        SubElement(item, "itunes:explicit").text = "false"

    indent(rss, space="  ")
    from xml.etree.ElementTree import ElementTree
    with open(RSS_FILE, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        ElementTree(rss).write(f, encoding="utf-8", xml_declaration=False)
    print(f"  ✓ RSS updated: {RSS_FILE}")

# ── Main pipeline ─────────────────────────────────────────────────────────────

def run(episode_number: int = None, dry_run: bool = False):
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Pick episode
    if episode_number:
        ep = next((e for e in EPISODES if e["number"] == episode_number), None)
        if not ep:
            sys.exit(f"Episode {episode_number} not found.")
    else:
        done = {int(p.stem[2:]) for p in OUTPUT_DIR.glob("ep*.mp3") if p.stem[2:].isdigit()}
        pending = [e for e in EPISODES if e["number"] not in done]
        if not pending:
            print("✓ All episodes already generated."); return
        ep = pending[0]

    print(f"\n{'='*60}\n  Ep {ep['number']}: {ep['title']}\n{'='*60}")

    audio_path  = OUTPUT_DIR / f"ep{ep['number']:02d}.mp3"
    script_path = OUTPUT_DIR / f"ep{ep['number']:02d}_script.txt"

    # 1. Generate script
    raw    = generate_script(ep)
    secs   = parse_sections(raw)
    script_path.write_text(secs["full"], encoding="utf-8")
    print(f"  ✓ Script saved ({len(secs['full'])} chars)")

    if dry_run:
        print(f"\n[DRY RUN] Script preview:\n{secs['full'][:600]}...\n"); return

    # 2. Generate audio
    if not text_to_speech(secs["full"], audio_path):
        sys.exit("Audio generation failed.")

    # 3. Update metadata + RSS
    all_eps = json.loads(META_FILE.read_text()) if META_FILE.exists() else []
    all_eps = [e for e in all_eps if e["episode"]["number"] != ep["number"]]
    all_eps.append({
        "episode": ep,
        "duration_seconds": 1200,
        "file_size_bytes": audio_path.stat().st_size,
        "pub_date": datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000"),
        "description": secs["intro"][:250] + "..."
    })
    all_eps.sort(key=lambda x: x["episode"]["number"])
    META_FILE.write_text(json.dumps(all_eps, ensure_ascii=False, indent=2))
    update_rss(all_eps)

    print(f"\n✓ Done. Upload {audio_path} to {PODCAST_BASE_URL}/episodes/ep{ep['number']:02d}.mp3")
    print(f"  Then submit feed.xml to creators.spotify.com")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--episode", type=int)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not os.environ.get("GROQ_API_KEY"):
        sys.exit("✗ Missing GROQ_API_KEY")
    if not args.dry_run and not GOOGLE_TTS_KEY:
        sys.exit("✗ Missing GOOGLE_TTS_KEY")

    run(args.episode, args.dry_run)

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
        "prompt": """Write a 20-minute podcast script on Socrates as a model of philosophical life.

The examined life, the Socratic method, self-knowledge as a radical practice, virtue as knowledge. Explore the paradox of Socratic ignorance — how knowing that you don't know is itself a form of wisdom. Discuss the tension between Socratic humility and his absolute conviction that the unexamined life is worthless. Why did Athens kill him, and what does that tell us about the relationship between philosophy and society?

Separate sections with ---SECTION---: INTRO (600 words) / DEVELOPMENT (3,000 words) / CLOSE (400 words)."""
    },
    {
        "number": 2, "week": "W1",
        "title": "Self-Knowledge: The Most Radical Philosophical Demand",
        "prompt": """Write a 20-minute podcast script on self-knowledge as a philosophical problem.

From the Delphic oracle to Freud, the demand to 'know thyself' has haunted Western thought. But is genuine self-knowledge possible? Explore the Socratic version, the Stoic version, and the modern challenge from psychoanalysis and cognitive science — which suggest the self is largely opaque to itself. What does it mean to know yourself if the self is not a stable object? Include Montaigne's radical self-examination, Nietzsche's critique of introspection, and the Buddhist dissolution of the self altogether.

Separate sections with ---SECTION---: INTRO (600 words) / DEVELOPMENT (3,000 words) / CLOSE (400 words)."""
    },
    {
        "number": 3, "week": "W2",
        "title": "Epicurus: The Misunderstood Philosopher of Pleasure",
        "prompt": """Write a 20-minute podcast script on Epicurus and the philosophy of pleasure.

Epicurus is almost universally misread as a hedonist. Reconstruct his actual position: the careful taxonomy of pleasures, ataraxia as the highest good, the role of friendship, the argument against the fear of death. Explore the tension between Epicurean withdrawal from public life and our modern sense that engagement is a moral duty. How does Epicurus's garden community relate to later utopian experiments? What does his philosophy reveal about the relationship between desire and suffering?

Separate sections with ---SECTION---: INTRO (600 words) / DEVELOPMENT (3,000 words) / CLOSE (400 words)."""
    },
    {
        "number": 4, "week": "W2",
        "title": "The Philosophy of Enough: Simplicity as a Radical Act",
        "prompt": """Write a 20-minute podcast script on the philosophical tradition of voluntary simplicity.

From Diogenes living in a barrel to Thoreau at Walden Pond, a strand of Western philosophy has argued that civilization itself is the problem. Explore the Cynic critique of convention, Epicurean simplicity, Stoic indifference to externals, and Thoreau's experiment in deliberate living. What is the philosophical argument behind choosing less? How does this tradition relate to Buddhist non-attachment? Is voluntary simplicity a genuine philosophical position or a luxury available only to the privileged?

Separate sections with ---SECTION---: INTRO (600 words) / DEVELOPMENT (3,000 words) / CLOSE (400 words)."""
    },
    {
        "number": 5, "week": "W3",
        "title": "Epictetus: Freedom in Chains",
        "prompt": """Write a 20-minute podcast script on Epictetus and the Stoic conception of freedom.

Epictetus was a slave who became one of the most influential philosophers of the ancient world. His central insight — that freedom is interior, not exterior — is both liberating and deeply troubling. Explore the dichotomy of control in depth: what it means philosophically, its connection to Stoic physics and cosmology, and its limits. Is Stoic freedom a genuine liberation or a sophisticated form of resignation? How does it compare to existentialist freedom? What does it mean to be free when the world is unjust?

Separate sections with ---SECTION---: INTRO (600 words) / DEVELOPMENT (3,000 words) / CLOSE (400 words)."""
    },
    {
        "number": 6, "week": "W3",
        "title": "Stoic Emotions: The Philosophy of Inner Weather",
        "prompt": """Write a 20-minute podcast script on the Stoic theory of emotions.

The Stoics argued that emotions are not things that happen to us but judgments we make — and therefore within our control. Explore this radical thesis in depth: the distinction between passions and eupatheiai, the role of assent in emotional experience, and the Stoic practice of examining impressions before acting on them. How does this compare to modern psychological accounts of emotion? Is the Stoic view psychologically realistic? Explore the tension between Stoic emotional discipline and the value of genuine feeling — is a life without passion a fully human life?

Separate sections with ---SECTION---: INTRO (600 words) / DEVELOPMENT (3,000 words) / CLOSE (400 words)."""
    },
    {
        "number": 7, "week": "W4",
        "title": "Marcus Aurelius: Philosophy as a Way of Life",
        "prompt": """Write a 20-minute podcast script on Marcus Aurelius and the Meditations.

The Meditations are unique in philosophical literature: private notes never intended for publication, written by the most powerful man in the world as a discipline of self-examination. Explore what kind of text they are, how they function as a spiritual exercise, and what they reveal about Stoicism as a lived practice rather than a theoretical system. Engage with the recurring themes: impermanence, the smallness of human affairs, the unity of rational nature. What does it mean to practice philosophy in the midst of power, war and responsibility?

Separate sections with ---SECTION---: INTRO (600 words) / DEVELOPMENT (3,000 words) / CLOSE (400 words)."""
    },
    {
        "number": 8, "week": "W4",
        "title": "Seneca: On the Shortness of Life",
        "prompt": """Write a 20-minute podcast script on Seneca's philosophy of time and mortality.

Seneca's essay 'On the Shortness of Life' is one of the most urgent texts in Western philosophy. Explore its central argument — that life is not short, we simply waste it — and follow its implications into Seneca's broader philosophy of time, attention, and the good life. Examine the tension at the heart of Seneca's life: a Stoic philosopher who was also enormously wealthy and complicit in Nero's court. Does this contradiction undermine his philosophy or make it more interesting? How does memento mori function as a philosophical practice?

Separate sections with ---SECTION---: INTRO (600 words) / DEVELOPMENT (3,000 words) / CLOSE (400 words)."""
    },
    {
        "number": 9, "week": "W5",
        "title": "Nietzsche: The Death of God and the Crisis of Values",
        "prompt": """Write a 20-minute podcast script on Nietzsche's diagnosis of modernity.

The death of God is not a theological claim but a cultural diagnosis: the collapse of the metaphysical framework that gave Western civilization its values, meaning and coherence. Explore what Nietzsche means, why he thinks it is inevitable, and what he sees as its consequences — nihilism, the last man, the possibility of revaluation. Engage with the depth of the crisis he is describing: not just the loss of religion, but the loss of any ground for values whatsoever. How does this relate to our current cultural moment?

Separate sections with ---SECTION---: INTRO (600 words) / DEVELOPMENT (3,000 words) / CLOSE (400 words)."""
    },
    {
        "number": 10, "week": "W5",
        "title": "The Eternal Return: Nietzsche's Heaviest Thought",
        "prompt": """Write a 20-minute podcast script on Nietzsche's doctrine of eternal return.

Nietzsche called the eternal return his 'heaviest thought' — the idea that everything that has happened will happen again, infinitely. Explore the multiple dimensions of this idea: as a cosmological hypothesis, as a thought experiment, as an ethical criterion (amor fati), and as a response to nihilism. Why does Nietzsche think this is the most difficult idea a human being can affirm? How does it relate to his critique of resentment and his vision of the Übermensch? Engage with the philosophical objections and the profound existential challenge it poses.

Separate sections with ---SECTION---: INTRO (600 words) / DEVELOPMENT (3,000 words) / CLOSE (400 words)."""
    },
    {
        "number": 11, "week": "W6",
        "title": "Camus: The Absurd and the Question of Suicide",
        "prompt": """Write a 20-minute podcast script on Camus and the philosophy of the absurd.

Camus opens The Myth of Sisyphus with the claim that there is only one truly serious philosophical question: whether life is worth living. Explore the structure of the absurd — the collision between human desire for meaning and the universe's silence — and Camus's three responses: physical suicide, philosophical suicide (religion), and rebellion. Why does Camus reject the existentialists' leap of faith? What does it mean to live without appeal? Engage with the image of Sisyphus and why Camus insists we must imagine him happy.

Separate sections with ---SECTION---: INTRO (600 words) / DEVELOPMENT (3,000 words) / CLOSE (400 words)."""
    },
    {
        "number": 12, "week": "W7",
        "title": "Sartre: Condemned to Be Free",
        "prompt": """Write a 20-minute podcast script on Sartre's existentialism and radical freedom.

Existence precedes essence: there is no human nature, no God-given purpose, no script. We are thrown into existence and condemned to make ourselves through our choices. Explore the full weight of this position: radical freedom, anguish, bad faith, and the project of authentic existence. Engage with Sartre's analysis of bad faith in depth — the waiter who plays at being a waiter, the woman who ignores her companion's intentions. How does Sartrean freedom relate to responsibility? What are the limits of his position?

Separate sections with ---SECTION---: INTRO (600 words) / DEVELOPMENT (3,000 words) / CLOSE (400 words)."""
    },
    {
        "number": 13, "week": "W7",
        "title": "Simone de Beauvoir: Ethics, Freedom and the Other",
        "prompt": """Write a 20-minute podcast script on Simone de Beauvoir's philosophy.

De Beauvoir is often reduced to her feminism, but she was a major philosopher in her own right whose work fundamentally challenges and extends existentialism. Explore her ethics of ambiguity — the irreducible tension between freedom and situation, between self and other. How does she argue that my freedom is bound up with the freedom of others? Engage with her analysis of oppression, her critique of the serious man, and the philosophical foundations of The Second Sex. What does it mean to be 'the other'?

Separate sections with ---SECTION---: INTRO (600 words) / DEVELOPMENT (3,000 words) / CLOSE (400 words)."""
    },
    {
        "number": 14, "week": "W8",
        "title": "Heidegger: Being, Time and Authenticity",
        "prompt": """Write a 20-minute podcast script on Heidegger's analysis of human existence.

Heidegger's Being and Time is one of the most difficult and important philosophical works of the twentieth century. Make it accessible without simplifying it. Explore the key concepts: Dasein as being-in-the-world, thrownness, the They-self (das Man), anxiety as a fundamental mood, and being-toward-death. How does Heidegger's analysis of everyday inauthenticity describe something we all recognize? What does authentic existence mean for Heidegger, and is it actually achievable? Engage with the philosophical depth of his account of mortality.

Separate sections with ---SECTION---: INTRO (600 words) / DEVELOPMENT (3,000 words) / CLOSE (400 words)."""
    },
    {
        "number": 15, "week": "W9",
        "title": "Philosophy as a Way of Life: Ancient Wisdom for Modern Existence",
        "prompt": """Write a 20-minute podcast script synthesizing the philosophy of life tradition.

Pierre Hadot argued that ancient philosophy was not primarily a theoretical enterprise but a set of spiritual exercises — practices for transforming the self and living well. Use this lens to synthesize the entire series: what does each school — Socratic, Epicurean, Stoic, Nietzschean, existentialist — offer as a practice, not just a theory? What are the deep tensions between them? Is it possible to build a coherent philosophy of life from these traditions, or are they ultimately incompatible? End with an open invitation to continue the philosophical life.

Separate sections with ---SECTION---: INTRO (600 words) / DEVELOPMENT (3,000 words) / CLOSE (400 words)."""
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
                    "content": """You are a world-class podcast scriptwriter specializing in philosophy for intellectually curious adults.

AUDIENCE: University graduates aged 30-40 with an advanced intellectual background. They read widely, think deeply, and want philosophy that challenges them — not simplified summaries. They are drawn to ideas for their own sake, not for career utility.

TONE: Like a brilliant, passionate professor in an intimate seminar. Rigorous but warm. You take ideas seriously and so does your audience. No corporate language, no business analogies, no references to productivity or careers.

CONTENT APPROACH:
- Engage with the philosophical ideas themselves at an advanced level
- Draw connections between thinkers across different eras and traditions
- Include the tensions, contradictions and unresolved questions within each philosophy
- Use analogies from literature, art, science, history and everyday human experience
- Challenge the listener intellectually — don't resolve everything neatly
- Treat the listener as a peer, not a student

CRITICAL REQUIREMENTS:
- Scripts must be 4,000 words minimum. This is non-negotiable.
- INTRO: 600 words minimum. Open with a provocative question, image or paradox.
- DEVELOPMENT: 3,000 words minimum. Develop ideas fully, with depth and nuance.
- CLOSE: 400 words minimum. Leave the listener with an open question, not a neat answer.
- Separate sections with ---SECTION---
- Write only flowing prose for audio. No bullets, no headers, no markdown."""
                                },
                {
                    "role": "user",
                    "content": episode["prompt"] + "\n\nEscribe todo el guión completamente en español. Español literario, rico y natural — no una traducción del inglés. Piensa y escribe directamente en español."
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
        # Load done episodes from metadata file
        done = set()
        if META_FILE.exists():
            try:
                data = json.loads(META_FILE.read_text())
                done = {e["episode"]["number"] for e in data}
            except Exception:
                done = set()
        print(f"  Episodes already done: {done}")
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

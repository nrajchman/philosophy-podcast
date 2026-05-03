#!/usr/bin/env python3
"""
Philosophy Podcast — 100% Free Pipeline
Groq (script) -> Edge TTS (audio) -> GitHub Releases (hosting)
"""

import os
import sys
import json
import asyncio
import argparse
import requests
from pathlib import Path
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

OUTPUT_DIR = Path("./episodes")
RSS_FILE   = Path("./feed.xml")
META_FILE  = OUTPUT_DIR / "metadata.json"

PODCAST_TITLE    = "Philosophy for Life"
PODCAST_DESC     = "Un podcast de filosofía para adultos intelectualmente curiosos: estoicismo, existencialismo y los grandes pensadores aplicados a la vida moderna."
PODCAST_AUTHOR   = "Philosophy for Life"
PODCAST_EMAIL    = "n.rajchman@gmail.com"
PODCAST_BASE_URL = "https://nrajchman.github.io/philosophy-podcast/episodes"
PODCAST_IMAGE    = "https://nrajchman.github.io/philosophy-podcast/cover.jpg"
PODCAST_LANGUAGE = "es"

# ── Episode plan ──────────────────────────────────────────────────────────────
EPISODES = [
    {
        "number": 1, "week": "S1",
        "title": "Sócrates: La vida sin examen no merece vivirse",
        "prompt": """Escribe un guión de podcast de 20 minutos sobre Sócrates como modelo de vida filosófica.

Audiencia: egresados universitarios de 30-40 años con formación avanzada. Leen mucho, piensan profundamente y quieren filosofía que los desafíe — no resúmenes simplificados. Les atraen las ideas por sí mismas.

Tono: Como un profesor brillante y apasionado en un seminario íntimo. Riguroso pero cálido. Sin lenguaje corporativo, sin analogías de negocios.

Explora: la vida examinada, el método socrático, el autoconocimiento como práctica radical, la virtud como conocimiento. La paradoja de la ignorancia socrática. Por qué Atenas lo mató y qué dice eso sobre la relación entre filosofía y sociedad.

Estructura (separa con ---SECTION---):
INTRO (600 palabras mínimo): Abre con una pregunta provocadora o paradoja.
DESARROLLO (3000 palabras mínimo): Desarrolla las ideas con profundidad y matices, conexiones entre pensadores, tensiones no resueltas.
CIERRE (400 palabras mínimo): Deja al oyente con una pregunta abierta, no una respuesta definitiva.

Solo prosa fluida para audio. Sin bullets, sin títulos, sin markdown."""
    },
    {
        "number": 2, "week": "S1",
        "title": "El autoconocimiento: la demanda filosófica más radical",
        "prompt": """Escribe un guión de podcast de 20 minutos sobre el autoconocimiento como problema filosófico.

Desde el oráculo de Delfos hasta Freud, la exigencia de 'conócete a ti mismo' ha obsesionado al pensamiento occidental. ¿Es posible el autoconocimiento genuino? Explora la versión socrática, la estoica y el desafío moderno del psicoanálisis y las ciencias cognitivas. Incluye a Montaigne, la crítica de Nietzsche a la introspección y la disolución budista del yo.

Estructura (separa con ---SECTION---):
INTRO (600 palabras) / DESARROLLO (3000 palabras) / CIERRE (400 palabras).
Solo prosa para audio. Sin markdown."""
    },
    {
        "number": 3, "week": "S2",
        "title": "Epicuro: El filósofo del placer malentendido",
        "prompt": """Escribe un guión de podcast de 20 minutos sobre Epicuro y la filosofía del placer.

Epicuro es casi universalmente malinterpretado como hedonista. Reconstruye su posición real: la taxonomía de los placeres, la ataraxia como bien supremo, el papel de la amistad, el argumento contra el miedo a la muerte. Explora la tensión entre el retiro epicúreo de la vida pública y nuestra idea moderna de compromiso cívico.

Estructura (separa con ---SECTION---):
INTRO (600 palabras) / DESARROLLO (3000 palabras) / CIERRE (400 palabras).
Solo prosa para audio. Sin markdown."""
    },
    {
        "number": 4, "week": "S2",
        "title": "La filosofía de la simplicidad: vivir con menos como acto radical",
        "prompt": """Escribe un guión de podcast de 20 minutos sobre la tradición filosófica de la simplicidad voluntaria.

Desde Diógenes viviendo en un barril hasta Thoreau en Walden, una corriente del pensamiento occidental ha argumentado que la civilización misma es el problema. Explora la crítica cínica de las convenciones, la simplicidad epicúrea, la indiferencia estoica a los bienes externos y el experimento de vida deliberada de Thoreau. ¿Es la simplicidad voluntaria una posición filosófica genuina o un lujo de los privilegiados?

Estructura (separa con ---SECTION---):
INTRO (600 palabras) / DESARROLLO (3000 palabras) / CIERRE (400 palabras).
Solo prosa para audio. Sin markdown."""
    },
    {
        "number": 5, "week": "S3",
        "title": "Epicteto: La libertad en cadenas",
        "prompt": """Escribe un guión de podcast de 20 minutos sobre Epicteto y la concepción estoica de la libertad.

Epicteto fue un esclavo que se convirtió en uno de los filósofos más influyentes del mundo antiguo. Su idea central — que la libertad es interior, no exterior — es a la vez liberadora y profundamente perturbadora. Explora la dicotomía del control en profundidad, su conexión con la física y cosmología estoica, y sus límites. ¿Es la libertad estoica una liberación genuina o una forma sofisticada de resignación?

Estructura (separa con ---SECTION---):
INTRO (600 palabras) / DESARROLLO (3000 palabras) / CIERRE (400 palabras).
Solo prosa para audio. Sin markdown."""
    },
    {
        "number": 6, "week": "S3",
        "title": "Las emociones estoicas: la filosofía del clima interior",
        "prompt": """Escribe un guión de podcast de 20 minutos sobre la teoría estoica de las emociones.

Los estoicos argumentaban que las emociones no son cosas que nos suceden sino juicios que hacemos — y por tanto están bajo nuestro control. Explora esta tesis radical: la distinción entre pasiones y eupatheiai, el papel del asentimiento en la experiencia emocional. ¿Es la visión estoica psicológicamente realista? Explora la tensión entre la disciplina emocional estoica y el valor del sentimiento genuino.

Estructura (separa con ---SECTION---):
INTRO (600 palabras) / DESARROLLO (3000 palabras) / CIERRE (400 palabras).
Solo prosa para audio. Sin markdown."""
    },
    {
        "number": 7, "week": "S4",
        "title": "Marco Aurelio: la filosofía como forma de vida",
        "prompt": """Escribe un guión de podcast de 20 minutos sobre Marco Aurelio y las Meditaciones.

Las Meditaciones son únicas en la literatura filosófica: notas privadas nunca destinadas a publicarse, escritas por el hombre más poderoso del mundo como disciplina de autoexamen. Explora qué tipo de texto son, cómo funcionan como ejercicio espiritual y qué revelan sobre el estoicismo como práctica vivida. Los temas recurrentes: la impermanencia, la pequeñez de los asuntos humanos, la unidad de la naturaleza racional.

Estructura (separa con ---SECTION---):
INTRO (600 palabras) / DESARROLLO (3000 palabras) / CIERRE (400 palabras).
Solo prosa para audio. Sin markdown."""
    },
    {
        "number": 8, "week": "S4",
        "title": "Séneca: Sobre la brevedad de la vida",
        "prompt": """Escribe un guión de podcast de 20 minutos sobre la filosofía del tiempo y la mortalidad de Séneca.

El ensayo de Séneca es uno de los textos más urgentes de la filosofía occidental. Explora su argumento central — que la vida no es corta, simplemente la desperdiciamos — y sus implicaciones. Examina la tensión en el corazón de la vida de Séneca: un filósofo estoico que era enormemente rico y cómplice en la corte de Nerón. ¿Invalida esta contradicción su filosofía o la hace más interesante?

Estructura (separa con ---SECTION---):
INTRO (600 palabras) / DESARROLLO (3000 palabras) / CIERRE (400 palabras).
Solo prosa para audio. Sin markdown."""
    },
    {
        "number": 9, "week": "S5",
        "title": "Nietzsche: La muerte de Dios y la crisis de los valores",
        "prompt": """Escribe un guión de podcast de 20 minutos sobre el diagnóstico de Nietzsche de la modernidad.

La muerte de Dios no es una afirmación teológica sino un diagnóstico cultural: el colapso del marco metafísico que dio a la civilización occidental sus valores, sentido y coherencia. Explora qué quiere decir Nietzsche, por qué cree que es inevitable y cuáles ve como sus consecuencias: el nihilismo, el último hombre, la posibilidad de la transvaloración. ¿Cómo se relaciona esto con nuestro momento cultural actual?

Estructura (separa con ---SECTION---):
INTRO (600 palabras) / DESARROLLO (3000 palabras) / CIERRE (400 palabras).
Solo prosa para audio. Sin markdown."""
    },
    {
        "number": 10, "week": "S5",
        "title": "El eterno retorno: el pensamiento más pesado de Nietzsche",
        "prompt": """Escribe un guión de podcast de 20 minutos sobre la doctrina del eterno retorno de Nietzsche.

Nietzsche llamó al eterno retorno su 'pensamiento más pesado': la idea de que todo lo que ha sucedido sucederá de nuevo, infinitamente. Explora las múltiples dimensiones de esta idea: como hipótesis cosmológica, como experimento mental, como criterio ético (amor fati) y como respuesta al nihilismo. ¿Por qué Nietzsche cree que es la idea más difícil que un ser humano puede afirmar?

Estructura (separa con ---SECTION---):
INTRO (600 palabras) / DESARROLLO (3000 palabras) / CIERRE (400 palabras).
Solo prosa para audio. Sin markdown."""
    },
    {
        "number": 11, "week": "S6",
        "title": "Camus: El absurdo y la pregunta del suicidio",
        "prompt": """Escribe un guión de podcast de 20 minutos sobre Camus y la filosofía del absurdo.

Camus abre El mito de Sísifo con la afirmación de que solo hay una pregunta filosófica verdaderamente seria: si la vida merece vivirse. Explora la estructura del absurdo — la colisión entre el deseo humano de sentido y el silencio del universo — y las tres respuestas de Camus: el suicidio físico, el suicidio filosófico (la religión) y la rebelión. ¿Por qué Camus rechaza el salto de fe de los existencialistas?

Estructura (separa con ---SECTION---):
INTRO (600 palabras) / DESARROLLO (3000 palabras) / CIERRE (400 palabras).
Solo prosa para audio. Sin markdown."""
    },
    {
        "number": 12, "week": "S7",
        "title": "Sartre: Condenado a ser libre",
        "prompt": """Escribe un guión de podcast de 20 minutos sobre el existencialismo de Sartre y la libertad radical.

La existencia precede a la esencia: no hay naturaleza humana, ni propósito divino, ni guión. Somos arrojados a la existencia y condenados a hacernos a nosotros mismos a través de nuestras elecciones. Explora el peso total de esta posición: libertad radical, angustia, mala fe y el proyecto de la existencia auténtica. Analiza la mala fe en profundidad — el camarero que juega a ser camarero.

Estructura (separa con ---SECTION---):
INTRO (600 palabras) / DESARROLLO (3000 palabras) / CIERRE (400 palabras).
Solo prosa para audio. Sin markdown."""
    },
    {
        "number": 13, "week": "S7",
        "title": "Simone de Beauvoir: Ética, libertad y el otro",
        "prompt": """Escribe un guión de podcast de 20 minutos sobre la filosofía de Simone de Beauvoir.

De Beauvoir es frecuentemente reducida a su feminismo, pero fue una filósofa importante por derecho propio cuya obra desafía y extiende fundamentalmente el existencialismo. Explora su ética de la ambigüedad — la tensión irreducible entre libertad y situación, entre el yo y el otro. ¿Cómo argumenta que mi libertad está vinculada a la libertad de los demás? ¿Qué significa ser 'el otro'?

Estructura (separa con ---SECTION---):
INTRO (600 palabras) / DESARROLLO (3000 palabras) / CIERRE (400 palabras).
Solo prosa para audio. Sin markdown."""
    },
    {
        "number": 14, "week": "S8",
        "title": "Heidegger: Ser, tiempo y autenticidad",
        "prompt": """Escribe un guión de podcast de 20 minutos sobre el análisis heideggeriano de la existencia humana.

Ser y Tiempo es una de las obras filosóficas más difíciles e importantes del siglo XX. Hazla accesible sin simplificarla. Explora los conceptos clave: Dasein como ser-en-el-mundo, la facticidad, el Uno (das Man), la angustia como estado de ánimo fundamental y el ser-para-la-muerte. ¿Qué significa la existencia auténtica para Heidegger y es realmente alcanzable?

Estructura (separa con ---SECTION---):
INTRO (600 palabras) / DESARROLLO (3000 palabras) / CIERRE (400 palabras).
Solo prosa para audio. Sin markdown."""
    },
    {
        "number": 15, "week": "S9",
        "title": "La filosofía como forma de vida: síntesis final",
        "prompt": """Escribe un guión de podcast de 20 minutos sintetizando la tradición de la filosofía de vida.

Pierre Hadot argumentó que la filosofía antigua no era principalmente una empresa teórica sino un conjunto de ejercicios espirituales — prácticas para transformar el yo y vivir bien. Usa esta lente para sintetizar toda la serie: ¿qué ofrece cada escuela — socrática, epicúrea, estoica, nietzscheana, existencialista — como práctica, no solo como teoría? ¿Cuáles son las tensiones profundas entre ellas? Termina con una invitación abierta a continuar la vida filosófica.

Estructura (separa con ---SECTION---):
INTRO (600 palabras) / DESARROLLO (3000 palabras) / CIERRE (400 palabras).
Solo prosa para audio. Sin markdown."""
    },
]

# ── Script generation (Groq — free) ──────────────────────────────────────────

def generate_script(episode: dict) -> str:
    print(f"  → Generating script with Groq for: {episode['title']}")

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "max_tokens": 8192,
            "temperature": 0.8,
            "messages": [
                {
                    "role": "system",
                    "content": """Eres un guionista de podcasts de filosofía de nivel mundial.

AUDIENCIA: Egresados universitarios de 30-40 años con formación intelectual avanzada. Leen mucho, piensan profundamente y quieren filosofía que los desafíe.

TONO: Como un profesor brillante y apasionado en un seminario íntimo. Riguroso pero cálido. Sin lenguaje corporativo, sin analogías de negocios.

ENFOQUE: Involúcrate con las ideas filosóficas a un nivel avanzado. Incluye tensiones, contradicciones y preguntas no resueltas. Usa analogías de literatura, arte, ciencia e historia.

REQUISITOS CRÍTICOS:
- Mínimo 4000 palabras. Esto es innegociable.
- INTRO: mínimo 600 palabras. Abre con una pregunta provocadora o paradoja.
- DESARROLLO: mínimo 3000 palabras. Desarrolla las ideas con profundidad y matices.
- CIERRE: mínimo 400 palabras. Deja al oyente con una pregunta abierta.
- Separa secciones con ---SECTION---
- Solo prosa fluida para audio. Sin bullets, sin títulos, sin markdown."""
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
        "intro":  parts[0] if len(parts) > 0 else "",
        "body":   parts[1] if len(parts) > 1 else "",
        "outro":  parts[2] if len(parts) > 2 else "",
        "full":   "\n\n".join(parts)
    }

# ── Audio generation (Edge TTS — free, no API key needed) ────────────────────

def text_to_speech(text: str, output_path: Path) -> bool:
    print(f"  → Converting to audio with Edge TTS (es-ES-AlvaroNeural)...")

    import edge_tts

    async def generate():
        communicate = edge_tts.Communicate(text, "es-ES-AlvaroNeural")
        await communicate.save(str(output_path))

    asyncio.run(generate())

    if not output_path.exists():
        print("  ✗ Audio file not created")
        return False

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  ✓ Audio saved: {output_path} ({size_mb:.1f} MB)")
    return True

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
    img = SubElement(ch, "itunes:image")
    img.set("href", PODCAST_IMAGE)
    SubElement(ch, "itunes:author").text = PODCAST_AUTHOR
    SubElement(ch, "itunes:explicit").text = "false"
    owner = SubElement(ch, "itunes:owner")
    SubElement(owner, "itunes:name").text = PODCAST_AUTHOR
    SubElement(owner, "itunes:email").text = PODCAST_EMAIL
    cat = SubElement(ch, "itunes:category")
    cat.set("text", "Education")

    for ep_data in reversed(all_eps):
        ep   = ep_data["episode"]
        item = SubElement(ch, "item")
        url  = f"{PODCAST_BASE_URL}/ep{ep['number']:02d}.mp3"
        SubElement(item, "title").text = f"Ep {ep['number']}: {ep['title']}"
        SubElement(item, "description").text = ep_data.get("description", "")
        SubElement(item, "pubDate").text = ep_data.get("pub_date", "")
        SubElement(item, "guid").text = url
        enc = SubElement(item, "enclosure")
        enc.set("url", url)
        enc.set("type", "audio/mpeg")
        enc.set("length", str(ep_data.get("file_size_bytes", 0)))
        SubElement(item, "itunes:duration").text = str(ep_data.get("duration_seconds", 1200))
        SubElement(item, "itunes:episode").text = str(ep["number"])
        SubElement(item, "itunes:episodeType").text = "full"
        SubElement(item, "itunes:explicit").text = "false"

    indent(rss, space="  ")
    with open(RSS_FILE, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        ElementTree(rss).write(f, encoding="utf-8", xml_declaration=False)
    print(f"  ✓ RSS updated: {RSS_FILE}")

# ── Main pipeline ─────────────────────────────────────────────────────────────

def run(episode_number: int = None, dry_run: bool = False):
    OUTPUT_DIR.mkdir(exist_ok=True)

    if episode_number:
        ep = next((e for e in EPISODES if e["number"] == episode_number), None)
        if not ep:
            sys.exit(f"Episode {episode_number} not found.")
    else:
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
            print("✓ All episodes already generated.")
            return
        ep = pending[0]

    print(f"\n{'='*60}\n  Ep {ep['number']}: {ep['title']}\n{'='*60}")

    audio_path  = OUTPUT_DIR / f"ep{ep['number']:02d}.mp3"
    script_path = OUTPUT_DIR / f"ep{ep['number']:02d}_script.txt"

    raw  = generate_script(ep)
    secs = parse_sections(raw)
    script_path.write_text(secs["full"], encoding="utf-8")
    print(f"  ✓ Script saved ({len(secs['full'])} chars)")

    if dry_run:
        print(f"\n[DRY RUN] Preview:\n{secs['full'][:600]}...\n")
        return

    if not text_to_speech(secs["full"], audio_path):
        sys.exit("Audio generation failed.")

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

    print(f"\n✓ Episodio {ep['number']} completado: {audio_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--episode", type=int)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not GROQ_API_KEY:
        sys.exit("✗ Missing GROQ_API_KEY")

    run(args.episode, args.dry_run)

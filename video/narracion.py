# Genera la narración con la voz clonada (F5) línea por línea y el guion legible.
# Uso: TTS_HOST=<ip> python video/narracion.py [--solo-md] [--rehacer id_seccion:indice ...]
# Salida: video/audio/<seccion>_<nn>.wav (fuera del repo: es la voz de la autora)
import base64, json, os, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guion import SECCIONES

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
HOST = os.environ.get("TTS_HOST", "127.0.0.1")
URL = f"http://{HOST}:8191/tts"
REF = os.path.join(ROOT, "voz", "referencia_corta.wav")
REF_TEXT = os.path.join(ROOT, "voz", "referencia_corta_texto.txt")
SEED = 7


def escribir_md():
    md = ["# Guion: Landing con video IA gratis en mi RTX\n",
          "Debajo de algunas frases, en cursiva, va cómo las pronuncia la voz IA.\n"]
    for s in SECCIONES:
        md.append(f"\n## {s['titulo']}\n")
        vis = None
        for l in s["lineas"]:
            if l.get("visual") and l["visual"] != vis:
                vis = l["visual"]
                md.append(f"\n**En pantalla:** `{vis}`\n")
            md.append(f"- {l['texto']}")
            if l.get("voz") and l["voz"] != l["texto"]:
                md.append(f"  - _voz: {l['voz']}_")
    open(os.path.join(BASE, "guion.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")


def generar(solo=None):
    out = os.path.join(BASE, "audio"); os.makedirs(out, exist_ok=True)
    ref_b64 = base64.b64encode(open(REF, "rb").read()).decode()
    ref_text = open(REF_TEXT, encoding="utf-8").read().strip()
    for s in SECCIONES:
        for i, l in enumerate(s["lineas"], 1):
            key = f"{s['id']}:{i}"
            path = os.path.join(out, f"{s['id']}_{i:02d}.wav")
            if solo is not None and key not in solo:
                continue
            if solo is None and os.path.exists(path):
                continue  # ya generada
            body = json.dumps({"text": l.get("voz") or l["texto"], "ref_wav_b64": ref_b64,
                               "ref_text": ref_text, "seed": SEED}).encode()
            r = urllib.request.urlopen(urllib.request.Request(URL, body, {"Content-Type": "application/json"}), timeout=600)
            open(path, "wb").write(r.read())
            print(key, r.headers["X-Gen-Seconds"], "s", flush=True)


if __name__ == "__main__":
    escribir_md()
    if "--solo-md" in sys.argv:
        sys.exit()
    rehacer = [a for a in sys.argv[1:] if ":" in a]
    generar(set(rehacer) if "--rehacer" in sys.argv else None)

# Busca la forma de escribir cada término en inglés que mejor pronuncia la voz en español (F5-Spanish).
# Para cada línea del guion con un término: prueba variantes de escritura × semillas dentro de la frase real,
# transcribe con Whisper y puntúa si el término se reconoce y si el resto de la frase sigue intacto.
# Uso: TTS_HOST=<ip> python video/pronunciacion.py   → video/build/pronunciacion.json
import base64, difflib, json, os, re, sys, unicodedata, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guion import SECCIONES
from faster_whisper import WhisperModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = os.environ.get("TTS_HOST", "127.0.0.1")
REF_B64 = base64.b64encode(open(os.path.join(ROOT, "voz", "referencia_corta.wav"), "rb").read()).decode()
REF_TEXT = open(os.path.join(ROOT, "voz", "referencia_corta_texto.txt"), encoding="utf-8").read().strip()
OUT = os.path.join(ROOT, "video", "build", "pronunciacion"); os.makedirs(OUT, exist_ok=True)
SEEDS = (7, 11)

# término canónico → (cómo está escrito hoy en el campo voz, variantes a probar)
TERMINOS = {
    "SageAttention": ("Seich atenshon", ["Seij aténshon", "Séich-aténshon", "seichatenshon", "Sage Attention"]),
    "ComfyUI": ("Cómfi iu ai", ["Cómfi, iu ái", "Cómfi-yu-ái", "Comfi iuai", "ComfyUI"]),
    "Tailscale": ("Teil Skeil", ["Téilskeil", "Teil-esquéil", "Téil, skéil", "Tailscale"]),
    "GitHub": ("Guit Jab", ["Guítjab", "Guit-jáb", "Gitjab", "GitHub"]),
    "Hugging Face": ("Jaguin Feis", ["Jáguin féis", "Jáguinfeis", "Hugging Face"]),
    "PyTorch": ("pái torch", ["Páitorch", "pai-tórch", "PyTorch"]),
    "Wan": ("Guan", ["Uán", "Guán", "Wan"]),
    "KJNodes": ("ka jota nouds", ["kei yei nouds", "Kéi-yéi-nóuds", "KJNodes"]),
    "Triton": ("tráiton", ["Tráiton", "Tráitón", "Triton"]),
    "Windows": ("güindous", ["Uíndous", "Güíndous", "Windows"]),
    "wheel": ("güil", ["uíl", "güíl", "wheel"]),
    "Higgsfield": ("Jigsfild", ["Jígs-fild", "Jígsfild", "Higgsfield"]),
    "Claude Code": ("Clod Coud", ["Clód Cóud", "Clod-cóud", "Claude Code"]),
    "GitHub Pages": ("Guit Jab Peiyes", ["Guítjab péiches", "Gitjab peichis", "GitHub Pages"]),
    "Unsplash": ("Ansplash", ["Ánsplash", "Ansplásh", "Unsplash"]),
}


def norm(t):
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", t)


def reconoce(canon, trans):
    # Mejor coincidencia del término (sin espacios) contra cualquier ventana de la transcripción
    c = norm(canon).replace(" ", "")
    words = norm(trans).split()
    best = 0.0
    for i in range(len(words)):
        for j in range(i + 1, min(len(words), i + 4) + 1):
            best = max(best, difflib.SequenceMatcher(None, "".join(words[i:j]), c).ratio())
    return best


def similitud(a, b):
    return difflib.SequenceMatcher(None, norm(a).split(), norm(b).split()).ratio()


def tts(text, seed):
    body = json.dumps({"text": text, "ref_wav_b64": REF_B64, "ref_text": REF_TEXT, "seed": seed}).encode()
    req = urllib.request.Request(f"http://{HOST}:8191/tts", body, {"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=600).read()


def main():
    model = WhisperModel("small", device="cpu", compute_type="int8")
    results = {}
    for s in SECCIONES:
        for i, l in enumerate(s["lineas"], 1):
            voz = l.get("voz") or l["texto"]
            presentes = [(c, cur, alts) for c, (cur, alts) in TERMINOS.items() if cur in voz]
            if not presentes:
                continue
            key = f"{s['id']}:{i}"
            # Optimiza un término a la vez (codicioso), manteniendo los demás con la mejor forma encontrada
            actual = voz
            for canon, cur, alts in presentes:
                cands = []
                for forma in [cur] + alts:
                    texto_voz = actual.replace(cur, forma)
                    for seed in SEEDS:
                        p = os.path.join(OUT, f"{key.replace(':', '_')}_{len(cands):02d}.wav")
                        open(p, "wb").write(tts(texto_voz, seed))
                        trans = " ".join(x.text.strip() for x in model.transcribe(p, language="es", beam_size=5)[0])
                        # 70 % que se reconozca el término, 30 % que el resto de la frase siga completo
                        score = 0.7 * reconoce(canon, trans) + 0.3 * similitud(l["texto"], trans)
                        cands.append((score, forma, seed, trans, texto_voz))
                cands.sort(key=lambda c: -c[0])
                mejor = cands[0]
                actual = mejor[4]
                cur_score = max(c[0] for c in cands if c[1] == cur)
                print(f"{key:14} {canon:14} {cur!r} {cur_score:.2f} → {mejor[1]!r} {mejor[0]:.2f} | {mejor[3]}", flush=True)
                results.setdefault(key, {"original": voz})
                results[key].update({"voz": actual, "seed": mejor[2], "trans": mejor[3]})
                results[key].setdefault("terminos", {})[canon] = {"forma": mejor[1], "score": round(mejor[0], 3),
                                                                  "score_original": round(cur_score, 3)}
            json.dump(results, open(os.path.join(ROOT, "video", "build", "pronunciacion.json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

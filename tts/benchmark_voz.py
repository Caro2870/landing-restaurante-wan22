# Benchmark de clonación de voz: mismas frases, misma referencia, misma semilla en cada modelo.
# Uso: python tts/benchmark_voz.py voz/referencia.wav voz/referencia_texto.txt
# Requiere TTS_HOST (IP de la PC con GPU). Salida en voz/benchmark/ (fuera del repo).
import base64, json, os, sys, urllib.request

HOST = os.environ.get("TTS_HOST", "127.0.0.1")
MODELS = {"chatterbox": 8190, "f5": 8191}
SEED = 7

FRASES = [
    "Hola, en este video les muestro cómo hice una landing de restaurante que se recorre como una película.",
    "Todo corre en mi propia computadora, con una RTX 5060 Ti de dieciséis gigas, sin pagar créditos.",
    "Usé Wan dos punto dos para animar las fotos, a través de ComfyUI y conectado por Tailscale.",
    "Con SageAttention, cada clip bajó de ciento sesenta y seis a ochenta y un segundos. ¡El doble de rápido!",
    "¿Y las caras? A cuatrocientos ochenta píxeles se veían borrosas, así que las generé a setecientos veinte.",
    "La lección: si el prompt dice luces, el modelo va a dibujar luces, aunque no estén en la foto.",
]


def wav_seconds(data):
    # Lee la cabecera RIFF a mano: torchaudio guarda WAV float (formato 3), que el módulo wave no soporta
    import struct
    pos, rate, block = 12, None, None
    while pos + 8 <= len(data):
        cid, size = data[pos:pos + 4], struct.unpack("<I", data[pos + 4:pos + 8])[0]
        if cid == b"fmt ":
            _, ch, rate, _, block = struct.unpack("<HHIIH", data[pos + 8:pos + 22])
        elif cid == b"data":
            if size in (0, 0xFFFFFFFF):  # tamaño sin rellenar en streams
                size = len(data) - pos - 8
            return size / block / rate
        pos += 8 + size + (size & 1)
    raise ValueError("WAV sin bloque de datos")


def main():
    ref_path, ref_text_path = sys.argv[1], sys.argv[2]
    ref_b64 = base64.b64encode(open(ref_path, "rb").read()).decode()
    ref_text = open(ref_text_path, encoding="utf-8").read().strip()
    out = os.path.join("voz", "benchmark"); os.makedirs(out, exist_ok=True)
    results = []
    only = os.environ.get("TTS_MODELS")  # p. ej. TTS_MODELS=f5 para repetir solo uno
    for model, port in MODELS.items():
        if only and model not in only.split(","):
            continue
        url = f"http://{HOST}:{port}/tts"
        # Calentamiento: la primera llamada carga cosas en la GPU y no es representativa
        body = json.dumps({"text": "Prueba.", "ref_wav_b64": ref_b64, "ref_text": ref_text, "seed": SEED}).encode()
        urllib.request.urlopen(urllib.request.Request(url, body, {"Content-Type": "application/json"}), timeout=600).read()
        for i, text in enumerate(FRASES, 1):
            body = json.dumps({"text": text, "ref_wav_b64": ref_b64, "ref_text": ref_text, "seed": SEED}).encode()
            try:
                r = urllib.request.urlopen(urllib.request.Request(url, body, {"Content-Type": "application/json"}), timeout=600)
                data = r.read()
                gen = float(r.headers["X-Gen-Seconds"])
                dur = wav_seconds(data)
                path = os.path.join(out, f"{model}_{i:02d}.wav")
                open(path, "wb").write(data)
                results.append({"modelo": model, "frase": i, "gen_s": round(gen, 2), "audio_s": round(dur, 2),
                                "rtf": round(gen / dur, 3), "wav": path})
            except urllib.error.HTTPError as e:
                results.append({"modelo": model, "frase": i, "error": e.read().decode()[:300]})
            print(results[-1], flush=True)
    # Conserva los resultados de los modelos que no se repitieron
    path = os.path.join(out, "resultados.json")
    old = json.load(open(path, encoding="utf-8"))["resultados"] if os.path.exists(path) else []
    done = {r["modelo"] for r in results}
    merged = [r for r in old if r["modelo"] not in done] + results
    json.dump({"frases": FRASES, "resultados": merged}, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

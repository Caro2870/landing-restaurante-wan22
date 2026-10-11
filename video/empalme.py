# Genera una frase en trozos: español con F5-Spanish (8191) y términos en inglés con F5 base (8192),
# con la misma voz de referencia, y los une recortando silencios e igualando volumen.
# Uso como módulo: frase([("es", "texto"), ("en", "Sage Attention"), ("es", "...")], salida.wav)
import base64, json, os, subprocess, tempfile, urllib.request

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = os.environ.get("TTS_HOST", "127.0.0.1")
PORT = {"es": 8191, "en": 8192}
REF = os.path.join(ROOT, "voz", "referencia_corta.wav")
REF_TEXT = open(os.path.join(ROOT, "voz", "referencia_corta_texto.txt"), encoding="utf-8").read().strip()
REF_B64 = base64.b64encode(open(REF, "rb").read()).decode()


REF_SECONDS = 11.2  # duración de referencia_corta.wav; F5 cuenta fix_duration con la referencia incluida


def duracion_termino(text):
    # F5 estima la duración por letras y comprime los términos cortos; les damos un tiempo natural
    return min(2.2, max(0.8, 0.09 * len(text)))


def tts(lang, text, seed=7):
    req = {"text": text, "ref_wav_b64": REF_B64, "ref_text": REF_TEXT, "seed": seed}
    if lang == "en":
        req["fix_duration"] = REF_SECONDS + duracion_termino(text)
    body = json.dumps(req).encode()
    req = urllib.request.Request(f"http://{HOST}:{PORT[lang]}/tts", body, {"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=600).read()


def limpiar(wav_bytes, path):
    # Recorta silencio al inicio y al final, y normaliza el volumen para que los trozos empaten
    src = path + ".raw.wav"
    open(src, "wb").write(wav_bytes)
    filt = ("silenceremove=start_periods=1:start_threshold=-60dB:start_silence=0.03,"
            "areverse,silenceremove=start_periods=1:start_threshold=-60dB:start_silence=0.05,areverse,"
            "loudnorm=I=-18:TP=-2:LRA=7")
    subprocess.run([FF, "-v", "error", "-y", "-i", src, "-af", filt, "-ar", "24000", "-ac", "1",
                    "-c:a", "pcm_s16le", path], check=True)
    os.remove(src)


def frase(trozos, salida, pausa=0.07):
    with tempfile.TemporaryDirectory() as tmp:
        partes = []
        for k, (lang, text) in enumerate(trozos):
            if lang == "wav":  # trozo ya generado y limpio (p. ej. un término elegido en la búsqueda)
                partes.append(text)
                continue
            p = os.path.join(tmp, f"{k:02d}.wav")
            limpiar(tts(lang, text), p)
            partes.append(p)
        # Une con una micro pausa y fundidos cortos para que no se noten los cortes
        inputs = [arg for p in partes for arg in ("-i", p)]
        filt = [f"[{k}]afade=t=in:d=0.015,areverse,afade=t=in:d=0.02,areverse,apad=pad_dur={pausa}[a{k}]"
                for k in range(len(partes))]
        concat = "".join(f"[a{k}]" for k in range(len(partes))) + f"concat=n={len(partes)}:v=0:a=1[out]"
        subprocess.run([FF, "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt + [concat]),
                        "-map", "[out]", "-c:a", "pcm_s16le", salida], check=True)


if __name__ == "__main__":
    out = os.path.join(ROOT, "video", "build", "empalme"); os.makedirs(out, exist_ok=True)
    frase([("en", "Sage Attention"),
           ("es", "hace ese mismo cálculo con números más cortos, de ocho bits en vez de dieciséis.")],
          os.path.join(out, "sage_03.wav"))
    frase([("es", "Y en vez de activarlo para todo"), ("en", "Comfy UI"),
           ("es", "lo activo con un nodo de"), ("en", "Kay Jay Nodes"),
           ("es", "dentro del flujo. Así puedo comparar con y sin.")],
          os.path.join(out, "sage_10.wav"))
    print("ok")

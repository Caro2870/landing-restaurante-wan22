# Arma un Short vertical (1080x1920) a partir de láminas HTML, clips y la voz clonada (F5).
# Uso: TTS_HOST=<ip> python video/short.py <sage|caras|voz>   → video/out/short_<nombre>.mp4
import base64, json, os, subprocess, sys, urllib.request

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
NOMBRE = sys.argv[1] if len(sys.argv) > 1 else "sage"
B = os.path.join(BASE, "build", f"short_{NOMBRE}"); os.makedirs(B, exist_ok=True)
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1080, 1920, 30
HOST = os.environ.get("TTS_HOST", "127.0.0.1")
FONTS = "C:/Windows/Fonts"

# (lámina, texto en subtítulos, texto para la voz)
SAGE = [
    ("hook", "Mi RTX tardaba 166 segundos en cada video. Cambié una sola cosa y bajó a 81.",
     "Mi erre te equis tardaba ciento sesenta y seis segundos en cada video. Cambié una sola cosa y bajó a ochenta y uno."),
    ("nombre", "Se llama SageAttention.", "Se llama Sage Attention."),
    ("redondeo", "Hace el cálculo más pesado del modelo con números de 8 bits en vez de 16. Es como redondear.",
     "Hace el cálculo más pesado del modelo con números de ocho bits en vez de dieciséis. Es como redondear."),
    ("comparacion", "Misma foto, misma semilla. Arriba sin SageAttention, abajo con. Se ve igual, pero tarda la mitad.",
     "Misma foto, misma semilla. Arriba sin Sage Attention, abajo con. Se ve igual, pero tarda la mitad."),
    ("cta", "Cómo instalarlo sin romper nada, en el video completo de mi canal.",
     "Cómo instalarlo sin romper nada, en el video completo de mi canal."),
]
CARAS = [
    ("hook", "Le pedí a la IA que animara esta foto… y mira lo que les hizo a las caras.",
     "Le pedí a la IA que animara esta foto, y mira lo que les hizo a las caras."),
    ("p480", "A 480p, cada cara mide unos 8 píxeles. El modelo no tiene información y se las inventa.",
     "A cuatrocientos ochenta pe, cada cara mide unos ocho píxeles. El modelo no tiene información y se las inventa."),
    ("p720", "La generé de nuevo a 720p: casi el triple de píxeles por cara.",
     "La generé de nuevo a setecientos veinte pe: casi el triple de píxeles por cara."),
    ("comparacion", "Arriba 480p, abajo 720p. Ahora sí tienen ojos, nariz y boca.",
     "Arriba cuatrocientos ochenta, abajo setecientos veinte. Ahora sí tienen ojos, nariz y boca."),
    ("cta", "Todo hecho gratis en mi RTX. El paso a paso, en el video completo de mi canal.",
     "Todo hecho gratis en mi erre te equis. El paso a paso, en el video completo de mi canal."),
]
VOZ = [
    ("hook", "Esta voz no es mía.", "Esta voz no es mía."),
    ("ia", "Bueno… sí es mía. Pero la está generando una IA en mi computadora.",
     "Bueno, sí es mía. Pero la está generando una inteligencia artificial en mi computadora."),
    ("muestra", "Grabé 20 segundos con el celular y el modelo F5 aprendió cómo hablo.",
     "Grabé veinte segundos con el celular, y el modelo efe cinco aprendió cómo hablo."),
    ("velocidad", "Cada frase tarda unos 2 segundos en mi RTX. Sin internet y sin pagar nada.",
     "Cada frase tarda unos dos segundos en mi erre te equis. Sin internet y sin pagar nada."),
    ("ingles", "Lo único que no le sale: el inglés. Escucha cómo dice ComfyUI.",
     "Lo único que no le sale: el inglés. Escucha cómo dice: Cómfi iu ai."),
    ("cta", "Cómo lo hice, en el video completo de mi canal.", "Cómo lo hice, en el video completo de mi canal."),
]
# Videos que se superponen sobre algunas láminas: lámina → (filtro de ffmpeg, entradas)
CLIP480 = os.path.join(ROOT, "clips", "01.mp4"); CLIP720 = os.path.join(ROOT, "clips", "01_720p.mp4")
VIDEOS = {
    "sage": {"comparacion": ([os.path.join(ROOT, "benchmark", "A_base.mp4"), os.path.join(ROOT, "benchmark", "B_sage.mp4")],
                             "[1]scale=820:-2,fps=30[a];[2]scale=820:-2,fps=30[b];[0][a]overlay=130:445[t];[t][b]overlay=130:990")},
    "caras": {
        "hook": ([CLIP480], "[1]scale=960:-2,fps=30[a];[0][a]overlay=60:520"),
        # Mismo recorte de las mesas en los dos clips (el de 720p está a 1,5x de escala)
        "p480": ([CLIP480], "[1]crop=300:200:100:250,scale=900:600:flags=neighbor,fps=30[a];[0][a]overlay=90:470"),
        "p720": ([CLIP720], "[1]crop=450:300:150:375,scale=900:600:flags=lanczos,fps=30[a];[0][a]overlay=90:470"),
        "comparacion": ([CLIP480, CLIP720], "[1]crop=300:200:100:250,scale=780:520:flags=neighbor,fps=30[a];"
                        "[2]crop=450:300:150:375,scale=780:520:flags=lanczos,fps=30[b];[0][a]overlay=150:420[t];[t][b]overlay=150:990"),
    },
    "voz": {},
}
LINEAS = {"sage": SAGE, "caras": CARAS, "voz": VOZ}[NOMBRE]
HTML = {"sage": "short_sage.html", "caras": "short_caras.html", "voz": "short_voz.html"}[NOMBRE]
PAUSA = 0.25


def run(*a):
    subprocess.run([FF, "-v", "error", "-y", *a], check=True)


def dur(path):
    err = subprocess.run([FF, "-i", path], capture_output=True, text=True).stderr
    h, m, s = err.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def voz():
    ref = base64.b64encode(open(os.path.join(ROOT, "voz", "referencia_corta.wav"), "rb").read()).decode()
    ref_text = open(os.path.join(ROOT, "voz", "referencia_corta_texto.txt"), encoding="utf-8").read().strip()
    for k, (_, _, v) in enumerate(LINEAS):
        p = os.path.join(B, f"voz_{k}.wav")
        if os.path.exists(p):
            continue
        body = json.dumps({"text": v, "ref_wav_b64": ref, "ref_text": ref_text, "seed": 7}).encode()
        req = urllib.request.Request(f"http://{HOST}:8191/tts", body, {"Content-Type": "application/json"})
        raw = p + ".raw.wav"
        open(raw, "wb").write(urllib.request.urlopen(req, timeout=600).read())
        run("-i", raw, "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", p)
        os.remove(raw)


def laminas():
    url = "file:///" + os.path.join(BASE, HTML).replace("\\", "/")
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": H})
        for s, _, _ in LINEAS:
            pg.goto(f"{url}?s={s}"); pg.wait_for_load_state("networkidle"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
            pg.screenshot(path=os.path.join(B, f"{s}.png"))
        b.close()


ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]


def toma(lamina, d, out):
    png = os.path.join(B, f"{lamina}.png")
    if lamina in VIDEOS[NOMBRE]:
        entradas, filtro = VIDEOS[NOMBRE][lamina]
        args = ["-loop", "1", "-i", png]
        for e in entradas:
            args += ["-stream_loop", "-1", "-i", e]
        run(*args, "-t", f"{d:.3f}", "-filter_complex", filtro, *ENC, out)
    else:
        n = int(d * FPS) + 1
        run("-loop", "1", "-i", png, "-t", f"{d:.3f}", "-vf",
            f"scale={W*2}:{H*2},zoompan=z='1+0.035*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS}",
            *ENC, out)


def ts(t):
    m, s = divmod(t, 60)
    return f"0:{int(m):02d}:{s:05.2f}"


def main():
    voz(); laminas()
    t = 0.0; tomas, subs, audios = [], [], []
    for k, (lam, txt, _) in enumerate(LINEAS):
        d = dur(os.path.join(B, f"voz_{k}.wav"))
        hueco = 0.8 if k == len(LINEAS) - 1 else PAUSA
        tomas.append((lam, d + hueco)); subs.append((t, t + d, txt)); audios.append((k, hueco))
        t += d + hueco
    print(f"duración: {t:.1f}s")
    lista = []
    for k, (lam, d) in enumerate(tomas):
        out = os.path.join(B, f"toma_{k}.mp4"); toma(lam, d, out); lista.append(f"file '{out.replace(os.sep, '/')}'")
    open(os.path.join(B, "tomas.txt"), "w").write("\n".join(lista))
    run("-f", "concat", "-safe", "0", "-i", os.path.join(B, "tomas.txt"), "-c", "copy", os.path.join(B, "mudo.mp4"))
    partes = []
    for k, hueco in audios:
        p = os.path.join(B, f"a_{k}.wav"); run("-i", os.path.join(B, f"voz_{k}.wav"), "-af", f"apad=pad_dur={hueco}", p)
        partes.append(f"file '{p.replace(os.sep, '/')}'")
    open(os.path.join(B, "audio.txt"), "w").write("\n".join(partes))
    run("-f", "concat", "-safe", "0", "-i", os.path.join(B, "audio.txt"), "-af", "loudnorm=I=-14:TP=-1.5:LRA=9",
        "-ar", "48000", os.path.join(B, "voz.wav"))
    # Subtítulos grandes, a la altura segura (por encima de la interfaz de Shorts)
    ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
           "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: S,Segoe UI,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,3,18,0,2,70,150,380,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    ass += [f"Dialogue: 0,{ts(a)},{ts(b + 0.1)},S,,0,0,0,,{x}" for a, b, x in subs]
    open(os.path.join(B, "subs.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")
    out = os.path.join(BASE, "out", f"short_{NOMBRE}.mp4")
    sp = os.path.join(B, "subs.ass").replace("\\", "/").replace(":", "\\:")
    run("-i", os.path.join(B, "mudo.mp4"), "-i", os.path.join(B, "voz.wav"),
        "-vf", f"ass='{sp}':fontsdir='{FONTS.replace(':', chr(92) + ':')}'",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart", out)
    print("listo:", out)


if __name__ == "__main__":
    main()

# Arma el video final a partir del guion: una toma por bloque de líneas con el mismo visual,
# la narración con pausas, subtítulos quemados y capítulos para la descripción de YouTube.
# Uso: python video/montaje.py   → video/out/video_final.mp4 + video/out/capitulos.txt
import json, os, struct, subprocess, sys

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
sys.path.insert(0, BASE)
from guion import SECCIONES

FF = imageio_ffmpeg.get_ffmpeg_exe()
B = os.path.join(BASE, "build"); VIS = os.path.join(B, "visuales"); TOMAS = os.path.join(B, "tomas")
OUT = os.path.join(BASE, "out")
for d in (TOMAS, OUT): os.makedirs(d, exist_ok=True)
W, H, FPS = 1920, 1080, 30
PAUSA, PAUSA_SECCION, COLA = 0.35, 0.8, 1.5
BG = (13, 9, 7)
FONTS = "C:/Windows/Fonts"


def run(*args):
    subprocess.run([FF, "-v", "error", "-y", *args], check=True)


def wav_dur(path):
    d = open(path, "rb").read(); pos = 12
    while pos + 8 <= len(d):
        cid, size = d[pos:pos + 4], struct.unpack("<I", d[pos + 4:pos + 8])[0]
        if cid == b"fmt ":
            _, ch, rate, _, block = struct.unpack("<HHIIH", d[pos + 8:pos + 22])
        elif cid == b"data":
            return (len(d) - pos - 8 if size in (0, 0xFFFFFFFF) else size) / block / rate
        pos += 8 + size + (size & 1)


def vid_dur(path):
    err = subprocess.run([FF, "-i", path], capture_output=True, text=True).stderr
    h, m, s = err.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]
COVER = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"


# --- Visuales ---------------------------------------------------------------

def toma_imagen(png, dur, out, zoom=0.04):
    # Imagen fija con un acercamiento lento (Ken Burns)
    n = int(dur * FPS) + 1
    run("-loop", "1", "-i", png, "-t", f"{dur:.3f}", "-vf",
        f"scale={W*2}:{H*2},zoompan=z='1+{zoom}*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},setsar=1",
        *ENC, out)


def toma_clip(src, dur, out):
    # Clip de Wan (5 s a 16 fps): se reproduce en bucle hasta cubrir la duración
    run("-stream_loop", "-1", "-i", src, "-t", f"{dur:.3f}", "-vf", f"{COVER},fps={FPS}", *ENC, out)


OFFSETS = {}


def toma_grabacion(src, dur, out, velocidad=1.0):
    # Toma un tramo de una grabación larga; cada uso continúa donde quedó el anterior
    total = vid_dur(src)
    ini = OFFSETS.get(src, 0.0)
    need = dur * velocidad
    if ini + need > total:
        ini = max(0.0, total - need)
    OFFSETS[src] = ini + need
    run("-ss", f"{ini:.3f}", "-i", src, "-t", f"{need:.3f}", "-vf",
        f"setpts=PTS/{velocidad},{COVER},fps={FPS}", "-t", f"{dur:.3f}", *ENC, out)


def toma_comparacion(a, b, dur, out):
    # Dos videos del benchmark lado a lado, con etiqueta y tiempo de generación
    res = json.load(open(os.path.join(ROOT, "benchmark", "resultados.json")))
    nombres = {"A_base": "A · sin SageAttention", "B_sage": "B · con SageAttention", "C_3samplers": "C · 3 samplers (v1)",
               "D_sage_3s": "D · Sage + 3 samplers (v1)", "J_sage_3s_v5_neutro": "J · Sage + 3 samplers corregido"}
    fondo = os.path.join(B, f"_cmp_{a}_{b}.png")
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    f1 = ImageFont.truetype(os.path.join(FONTS, "segoeuib.ttf"), 40)
    f2 = ImageFont.truetype(os.path.join(FONTS, "segoeui.ttf"), 34)
    for k, v in enumerate((a, b)):
        x = 60 + k * 920
        d.text((x, 150), nombres.get(v, v), font=f1, fill=(246, 238, 228))
        d.text((x, 205), f"{res[v]['segundos']:.0f} s por clip", font=f2, fill=(232, 116, 59))
    img.save(fondo)
    va, vb = os.path.join(ROOT, "benchmark", f"{a}.mp4"), os.path.join(ROOT, "benchmark", f"{b}.mp4")
    run("-loop", "1", "-i", fondo, "-stream_loop", "-1", "-i", va, "-stream_loop", "-1", "-i", vb, "-t", f"{dur:.3f}",
        "-filter_complex",
        "[1]scale=880:-2,fps=30[a];[2]scale=880:-2,fps=30[b];[0][a]overlay=60:270[t];[t][b]overlay=980:270,setsar=1",
        *ENC, out)


def grilla_fotos():
    out = os.path.join(B, "_fotos.png")
    img = Image.new("RGB", (W, H), BG)
    for k in range(6):
        im = Image.open(os.path.join(ROOT, "fotos", f"0{k+1}.jpg")).resize((580, 335))
        img.paste(im, (60 + (k % 3) * 610, 90 + (k // 3) * 365))
    img.save(out); return out


def lamina_caras():
    out = os.path.join(B, "_caras.png")
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    caras = Image.open(os.path.join(ROOT, "benchmark", "benchmark_caras_480_vs_720.png"))
    caras = caras.resize((int(caras.width * 820 / caras.height), 820))
    x = (W - caras.width) // 2
    img.paste(caras, (x, 40))
    f = ImageFont.truetype(os.path.join(FONTS, "segoeuib.ttf"), 44)
    for y, t in ((60, "480p"), (470, "720p")):
        d.rounded_rectangle((x + 20, y, x + 170, y + 64), 12, fill=(0, 0, 0))
        d.text((x + 42, y + 4), t, font=f, fill=(255, 197, 154))
    img.save(out); return out


def render(visual, dur, out):
    tipo, _, arg = visual.partition(":")
    if tipo == "slide":
        toma_imagen(os.path.join(VIS, f"slide_{arg}.png"), dur, out, zoom=0.03)
    elif tipo == "imagen":
        toma_imagen({"fotos": grilla_fotos, "caras": lamina_caras}[arg](), dur, out, zoom=0.05)
    elif tipo == "clip":
        toma_clip(os.path.join(ROOT, "clips", f"{arg}.mp4"), dur, out)
    elif tipo == "landing":
        toma_grabacion(os.path.join(VIS, f"landing_{arg}.mp4"), dur, out, velocidad=1.6)
    elif tipo == "web":
        toma_grabacion(os.path.join(VIS, f"web_{arg}.mp4"), dur, out)
    elif tipo == "comparacion":
        a, b = arg.split(":")
        toma_comparacion(a, b, dur, out)
    else:
        raise ValueError(visual)


# --- Línea de tiempo -------------------------------------------------------------

def ts(t):  # tiempo para ASS
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def main():
    t = 0.0; visual = None
    tomas, subs, capitulos, audio = [], [], [], []
    for si, s in enumerate(SECCIONES):
        capitulos.append((t, s["titulo"]))
        for i, l in enumerate(s["lineas"], 1):
            wav = os.path.join(BASE, "audio", f"{s['id']}_{i:02d}.wav")
            d = wav_dur(wav)
            ultima = i == len(s["lineas"])
            hueco = PAUSA_SECCION if ultima else PAUSA
            if si == len(SECCIONES) - 1 and ultima:
                hueco = COLA
            nuevo = l.get("visual") or visual
            if nuevo != visual or not tomas:
                tomas.append({"visual": nuevo, "ini": t, "dur": 0.0})
                visual = nuevo
            tomas[-1]["dur"] += d + hueco
            subs.append((t, t + d, l["texto"]))
            audio.append((wav, hueco))
            t += d + hueco
    print(f"duración total: {t/60:.2f} min, {len(tomas)} tomas", flush=True)

    # Tomas de video
    lista = []
    for k, tm in enumerate(tomas):
        out = os.path.join(TOMAS, f"{k:03d}.mp4")
        render(tm["visual"], tm["dur"], out)
        lista.append(f"file '{out.replace(os.sep, '/')}'")
        print(f"toma {k:03d} {tm['visual']:38} {tm['dur']:6.2f}s", flush=True)
    open(os.path.join(B, "tomas.txt"), "w").write("\n".join(lista))
    run("-f", "concat", "-safe", "0", "-i", os.path.join(B, "tomas.txt"), "-c", "copy", os.path.join(B, "video_mudo.mp4"))

    # Narración con pausas
    partes = []
    for k, (wav, hueco) in enumerate(audio):
        p = os.path.join(B, "_a", f"{k:03d}.wav"); os.makedirs(os.path.dirname(p), exist_ok=True)
        run("-i", wav, "-af", f"apad=pad_dur={hueco}", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", p)
        partes.append(f"file '{p.replace(os.sep, '/')}'")
    open(os.path.join(B, "audio.txt"), "w").write("\n".join(partes))
    run("-f", "concat", "-safe", "0", "-i", os.path.join(B, "audio.txt"), "-af", "loudnorm=I=-16:TP=-1.5:LRA=9",
        "-ar", "48000", os.path.join(B, "narracion.wav"))

    # Subtítulos (ASS): abajo, sobre una franja oscura
    ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "",
           "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
           "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: Sub,Segoe UI,46,&H00E4EEF6,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,3,14,0,2,220,220,60,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for a, b, txt in subs:
        ass.append(f"Dialogue: 0,{ts(a)},{ts(b + 0.15)},Sub,,0,0,0,,{txt}")
    open(os.path.join(B, "subs.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

    final = os.path.join(OUT, "video_final.mp4")
    subs_path = os.path.join(B, "subs.ass").replace("\\", "/").replace(":", "\\:")
    run("-i", os.path.join(B, "video_mudo.mp4"), "-i", os.path.join(B, "narracion.wav"),
        "-vf", f"ass='{subs_path}':fontsdir='{FONTS.replace(':', chr(92) + ':')}'",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", final)

    cap = [f"{int(c // 60)}:{int(c % 60):02d} {n}" for c, n in capitulos]
    cap[0] = "0:00 " + capitulos[0][1]
    open(os.path.join(OUT, "capitulos.txt"), "w", encoding="utf-8").write("\n".join(cap) + "\n")
    print("listo:", final)
    print("\n".join(cap))


if __name__ == "__main__":
    main()

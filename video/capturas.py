# Exporta las láminas a PNG y graba el scroll de la landing y la página del benchmark (1920x1080).
# Uso: python video/capturas.py [slides] [landing] [web]
# Requiere el servidor local de la landing en http://localhost:5173
import os, re, shutil, subprocess, sys

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "build", "visuales"); os.makedirs(OUT, exist_ok=True)
FF = imageio_ffmpeg.get_ffmpeg_exe()
SITE = os.environ.get("SITE", "http://localhost:5173")
W, H = 1920, 1080


def slides(p):
    ids = re.findall(r'<section class="slide" id="([a-z0-9_]+)"', open(os.path.join(BASE, "slides.html"), encoding="utf-8").read())
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": W, "height": H})
    url = "file:///" + os.path.join(BASE, "slides.html").replace("\\", "/")
    for i in ids:
        page.goto(f"{url}?s={i}")
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready")
        page.screenshot(path=os.path.join(OUT, f"slide_{i}.png"))
        print("slide", i, flush=True)
    b.close()


def grabar(p, nombre, url, accion, segundos):
    # Graba la página mientras `accion(page)` la recorre; luego recorta la carga inicial y convierte a mp4
    tmp = os.path.join(OUT, "_rec"); shutil.rmtree(tmp, ignore_errors=True)
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": W, "height": H}, record_video_dir=tmp, record_video_size={"width": W, "height": H})
    page = ctx.new_page()
    page.goto(url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2500)  # que carguen los frames
    t0 = page.evaluate("performance.now()") / 1000
    accion(page)
    t1 = page.evaluate("performance.now()") / 1000
    video = page.video.path()
    ctx.close(); b.close()
    # El video arranca con la navegación; cortamos todo lo anterior a la acción
    load = t0 + 0.3
    subprocess.run([FF, "-v", "error", "-y", "-ss", f"{load:.2f}", "-i", video, "-t", f"{t1 - t0:.2f}",
                    "-vf", "fps=30", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                    os.path.join(OUT, f"{nombre}.mp4")], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print("grabado", nombre, f"{t1 - t0:.1f}s", flush=True)


def scroll_suave(page, total_s=40, hasta=None):
    # Baja por la película a velocidad constante (60 pasos por segundo)
    alto = page.evaluate("document.getElementById('film').offsetHeight - innerHeight")
    hasta = hasta or alto
    pasos = int(total_s * 60)
    for k in range(pasos + 1):
        page.evaluate(f"scrollTo(0, {hasta * k / pasos})")
        page.wait_for_timeout(1000 / 60)


def landing(p):
    grabar(p, "landing_ia", f"{SITE}/?v=ia", lambda pg: scroll_suave(pg, 42), 42)
    grabar(p, "landing_fotos", f"{SITE}/?v=fotos", lambda pg: scroll_suave(pg, 42), 42)


def web(p):
    def demo(pg):
        pg.wait_for_timeout(1200)
        pg.click("#play"); pg.wait_for_timeout(5500)
        pg.click("#mode button[data-mode=wipe]")
        box = pg.locator("#handle").bounding_box()
        pg.mouse.move(box["x"] + 1, box["y"] + box["height"] / 2); pg.mouse.down()
        for x in range(0, 500, 10):
            pg.mouse.move(box["x"] - x, box["y"] + box["height"] / 2); pg.wait_for_timeout(20)
        for x in range(-500, 400, 10):
            pg.mouse.move(box["x"] + x, box["y"] + box["height"] / 2); pg.wait_for_timeout(20)
        pg.mouse.up(); pg.wait_for_timeout(2500)
        for y in range(0, 1400, 20):
            pg.evaluate(f"scrollTo(0, {y})"); pg.wait_for_timeout(16)
        pg.wait_for_timeout(1500)
    grabar(p, "web_benchmark", f"{SITE}/benchmark.html", demo, 0)


if __name__ == "__main__":
    que = sys.argv[1:] or ["slides", "landing", "web"]
    with sync_playwright() as p:
        for q in que:
            {"slides": slides, "landing": landing, "web": web}[q](p)

# Extrae los frames de cada clip a WebP para la secuencia con scroll
import glob, os, subprocess, json
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
base = os.path.dirname(os.path.abspath(__file__))
counts = {}
for clip in sorted(glob.glob(os.path.join(base, "clips", "0*.mp4"))):
    name = os.path.splitext(os.path.basename(clip))[0]
    out = os.path.join(base, "frames", name)
    os.makedirs(out, exist_ok=True)
    for f in glob.glob(os.path.join(out, "*.webp")):
        os.remove(f)
    subprocess.run([FFMPEG, "-v", "error", "-i", clip, "-c:v", "libwebp", "-quality", "78",
                    os.path.join(out, "%03d.webp")], check=True)
    counts[name] = len(glob.glob(os.path.join(out, "*.webp")))
    print(name, counts[name], "frames")

with open(os.path.join(base, "frames", "manifest.js"), "w") as f:
    f.write("window.FRAMES = " + json.dumps(counts) + ";\n")

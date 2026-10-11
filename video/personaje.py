# Genera el personaje virtual a partir de una foto con Qwen-Image-Edit-2511 (GGUF) en ComfyUI.
# Uso: COMFY_HOST=http://<ip>:8188 python video/personaje.py <foto1,foto2,foto3> <salida_dir> <estilo|all> [seed]
# Las fotos y los resultados quedan en voz/ (fuera del repo): son de una persona real.
import json, os, sys, time, urllib.parse, urllib.request, uuid

HOST = os.environ.get("COMFY_HOST", "http://127.0.0.1:8188")

# Los rasgos concretos de la persona viven en voz/personaje/rasgos.txt (fuera del repo, es una descripción física).
# Sin ese archivo se usa una instrucción genérica.
_RASGOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "voz", "personaje", "rasgos.txt")
RASGOS = (open(_RASGOS, encoding="utf-8").read().strip() if os.path.exists(_RASGOS) else
          "the same face shape, skin tone, eyes, nose, eyebrows, any distinctive marks and hairstyle as in the photos.")

# Sin "woman"/"girl": empujan al modelo hacia un estereotipo (maquillaje, ojos de muñeca, cara afinada).
# Las imágenes de referencia son varias fotos de la misma persona: dan más información de su identidad.
BASE = ("Pictures 1, 2 and 3 are photos of the same person. Keep this person's exact identity and make the face "
        "clearly recognizable as them: " + RASGOS + " Skin tone not lighter and not darker than in the photos. "
        "Natural look without makeup, neither doll-like nor overly masculine. "
        "Neutral style: oversized dark hoodie over a black t-shirt, over-ear headphones resting around the neck. "
        "Head and shoulders, looking at the camera, calm confident half smile, relaxed tech-creator vibe. "
        "Background: a dim desk setup with a monitor showing code and soft warm orange accent light, slightly blurred.")
ESTILOS = {
    "3d": "Turn this person into a stylized 3D animated character, modern animated film look with realistic "
          "proportions, smooth shading. " + BASE + " High quality 3D render, soft studio lighting.",
    "anime": "Turn this person into an anime VTuber character illustration, clean lineart, cel shading, "
             "vibrant colors, natural eye proportions. " + BASE + " High quality anime key visual.",
    "comic": "Turn this person into a bold flat vector comic illustration, thick clean outlines, flat vibrant colors, "
             "minimal shading. " + BASE + " High quality editorial illustration.",
}


# Expresiones del personaje ya elegido. Picture 1 = el personaje; Pictures 2 y 3 = fotos reales (identidad).
PERSONAJE = ("Picture 1 shows a 3D animated character; pictures 2 and 3 are photos of the real person it is based on. "
             "Keep exactly the same character as picture 1: same 3D animated style, same face, same skin tone, same "
             "hair and distinctive facial features, same dark hoodie, black t-shirt and headphones around the neck. "
             "Upper body, plain dark charcoal background with a soft warm orange rim light. ")
EXPRESIONES = {
    "sorprendida": PERSONAJE + "New pose: very surprised and amazed, eyes wide open, mouth open in a big 'wow', "
                   "both hands raised near the cheeks.",
    "senalando": PERSONAJE + "New pose: pointing with the index finger to the left side of the image, looking at the "
                 "camera with an excited confident smile.",
    "celebrando": PERSONAJE + "New pose: celebrating, big happy smile, one fist raised in victory.",
    "pensando": PERSONAJE + "New pose: skeptical and thinking, one eyebrow raised, hand on the chin, slight smirk.",
    "pulgar": PERSONAJE + "New pose: friendly confident smile, giving a thumbs up toward the camera.",
}
# Retoques puntuales sobre una imagen ya generada (Picture 1)
RETOQUES = {
    "sin_lunar": "Remove the small dark mole from the face in picture 1, leaving smooth skin of the same tone in that spot. "
                 "Change nothing else: same character, pose, expression, hair, clothes, lighting and orange background.",
}
# Foto de perfil: cuadrada, cara centrada y fondo liso para que se lea en un círculo pequeño
EXPRESIONES_PERFIL = {
    "perfil": PERSONAJE.replace("Upper body, plain dark charcoal background with a soft warm orange rim light. ", "")
              + "Centered head and shoulders portrait for a profile picture, face filling the middle of the image, "
                "friendly confident smile looking at the camera, solid flat warm orange background (#e8743b), no objects.",
}


def upload(path):
    b = uuid.uuid4().hex
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{os.path.basename(path)}\"\r\n"
            "Content-Type: image/jpeg\r\n\r\n").encode() + open(path, "rb").read() + \
           f"\r\n--{b}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{b}--\r\n".encode()
    r = urllib.request.Request(HOST + "/upload/image", body, {"Content-Type": f"multipart/form-data; boundary={b}"})
    return json.load(urllib.request.urlopen(r))["name"]


def workflow(images, prompt, seed, prefix):
    # Referencias extra (hasta 3 en total): se cargan aparte y se pasan como image2/image3
    refs = {"image1": ["8", 0]}
    extra = {}
    for k, name in enumerate(images[1:3], 2):
        extra[str(20 + k)] = {"class_type": "LoadImage", "inputs": {"image": name}}
        extra[str(30 + k)] = {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": [str(20 + k), 0],
                              "upscale_method": "lanczos", "megapixels": 1.0, "resolution_steps": 8}}
        refs[f"image{k}"] = [str(30 + k), 0]
    return {**extra,
        "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "qwen-image-edit-2511-Q4_K_M.gguf"}},
        "2": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "strength_model": 1.0,
              "lora_name": "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors"}},
        "3": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["2", 0], "shift": 3.1}},
        "4": {"class_type": "CFGNorm", "inputs": {"model": ["3", 0], "strength": 1.0}},
        "5": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
              "type": "qwen_image", "device": "default"}},
        "6": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "7": {"class_type": "LoadImage", "inputs": {"image": images[0]}},
        "8": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["7", 0], "upscale_method": "lanczos",
              "megapixels": 1.0, "resolution_steps": 8}},
        "9": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {"clip": ["5", 0], "prompt": prompt,
              "vae": ["6", 0], **refs}},
        "10": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {"clip": ["5", 0], "prompt": "",
               "vae": ["6", 0], **refs}},
        "11": {"class_type": "VAEEncode", "inputs": {"pixels": ["8", 0], "vae": ["6", 0]}},
        "12": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "seed": seed, "steps": 4, "cfg": 1.0,
               "sampler_name": "euler", "scheduler": "simple", "positive": ["9", 0], "negative": ["10", 0],
               "latent_image": ["11", 0], "denoise": 1.0}},
        "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["6", 0]}},
        "14": {"class_type": "SaveImage", "inputs": {"images": ["13", 0], "filename_prefix": f"personaje/{prefix}"}},
    }


def run(wf, out_path):
    r = urllib.request.Request(HOST + "/prompt", json.dumps({"prompt": wf}).encode(), {"Content-Type": "application/json"})
    try:
        pid = json.load(urllib.request.urlopen(r))["prompt_id"]
    except urllib.error.HTTPError as e:
        raise SystemExit(e.read().decode()[:800])
    t0 = time.time()
    while True:
        time.sleep(2)
        h = json.load(urllib.request.urlopen(f"{HOST}/history/{pid}"))
        if pid in h:
            st = h[pid]["status"]
            if st.get("status_str") == "error":
                raise SystemExit(json.dumps(st["messages"])[-800:])
            for out in h[pid]["outputs"].values():
                for f in out.get("images", []):
                    url = (f"{HOST}/view?filename={urllib.parse.quote(f['filename'])}"
                           f"&subfolder={urllib.parse.quote(f['subfolder'])}&type={f['type']}")
                    urllib.request.urlretrieve(url, out_path)
            return time.time() - t0


if __name__ == "__main__":
    fotos, out_dir, estilo = sys.argv[1].split(","), sys.argv[2], sys.argv[3]
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 42
    os.makedirs(out_dir, exist_ok=True)
    img = [upload(f) for f in fotos]  # la primera foto define el encuadre de la salida
    PROMPTS = {**ESTILOS, **EXPRESIONES, **EXPRESIONES_PERFIL, **RETOQUES}
    grupo = {"all": list(ESTILOS), "expresiones": list(EXPRESIONES)}.get(estilo, [estilo])
    for nombre in grupo:
        p = os.path.join(out_dir, f"{nombre}_{seed}.png")
        secs = run(workflow(img, PROMPTS[nombre], seed, nombre), p)
        print(f"{nombre}: {secs:.0f}s -> {p}", flush=True)

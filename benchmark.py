# Benchmark A/B de Wan 2.2 I2V en la RTX: misma foto, mismo prompt, misma semilla.
# Uso: python -I benchmark.py fotos/01.jpg [variantes...]
import json, sys, time, uuid, os, urllib.request, urllib.parse

HOST = os.environ.get("COMFY_HOST", "http://127.0.0.1:8188")
SEED = 424242
PROMPT = ("evening exterior of a restaurant terrace, warm lights glowing, people chatting at tables under umbrellas, "
          "camera moves straight forward toward the entrance, slow zoom in, photorealistic")
NEG = "blurry, distorted, deformed faces, extra objects, text, watermark, low quality, flicker, morphing"

# Configuraciones de 3 samplers: (pasos_totales, fin_sin_lora, cfg_sin_lora, fin_high_con_lora)
THREE = {
    "v1": (6, 2, 3.5, 3),    # la primera prueba (falló)
    "v2": (8, 2, 3.5, 4),    # más pasos en total → saltos de ruido más chicos
    "v3": (6, 2, 2.0, 3),    # cfg más bajo sin LoRA
    "v4": (10, 3, 3.5, 5),   # 3 de 10 pasos sin LoRA
    "v5": (12, 4, 2.5, 6),   # más pasos y cfg moderado
}

# nombre: (ancho, alto, sage, tres_samplers)
VARIANTS = {
    "A_base":      (832, 480, False, None),
    "B_sage":      (832, 480, True,  None),
    "C_3samplers": (832, 480, False, "v1"),
    "D_sage_3s":   (832, 480, True,  "v1"),
    "E_sage_3s_v2": (832, 480, True, "v2"),
    "F_sage_3s_v3": (832, 480, True, "v3"),
    "G_sage_3s_v4": (832, 480, True, "v4"),
    "H_sage_3s_v5": (832, 480, True, "v5"),
    # Mismas configuraciones con un prompt neutro (sin "lights"): ¿el problema era el prompt?
    "I_sage_3s_v3_neutro": (832, 480, True, "v3", "neutro"),
    "J_sage_3s_v5_neutro": (832, 480, True, "v5", "neutro"),
    "K_sage_neutro":       (832, 480, True, None, "neutro"),
}

PROMPTS = {
    "neutro": ("people sitting and talking at outdoor cafe tables, a few people walking past, "
               "camera moves slowly forward, realistic, natural motion"),
}

def upload(path):
    b = uuid.uuid4().hex
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{os.path.basename(path)}\"\r\n"
            "Content-Type: image/jpeg\r\n\r\n").encode() + open(path, "rb").read() + \
           f"\r\n--{b}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{b}--\r\n".encode()
    r = urllib.request.Request(HOST + "/upload/image", body, {"Content-Type": f"multipart/form-data; boundary={b}"})
    return json.load(urllib.request.urlopen(r))["name"]

def ksampler(model, latent, cond, start, end, total, cfg, noise, leftover):
    return {"class_type": "KSamplerAdvanced", "inputs": {
        "model": model, "add_noise": "enable" if noise else "disable", "noise_seed": SEED,
        "steps": total, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple",
        "positive": [cond, 0], "negative": [cond, 1], "latent_image": latent,
        "start_at_step": start, "end_at_step": end,
        "return_with_leftover_noise": "enable" if leftover else "disable"}}

def workflow(image, w, h, sage, three, prefix, prompt=None):
    wf = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "7": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
        "8": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
        "9": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["7", 0], "text": prompt or PROMPT}},
        "10": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["7", 0], "text": NEG}},
        "11": {"class_type": "LoadImage", "inputs": {"image": image}},
        "12": {"class_type": "WanImageToVideo", "inputs": {"positive": ["9", 0], "negative": ["10", 0], "vae": ["8", 0],
               "width": w, "height": h, "length": 81, "batch_size": 1, "start_image": ["11", 0]}},
    }
    high, low = ["1", 0], ["2", 0]
    if sage:  # parche de KJNodes: SageAttention solo para este flujo
        wf["20"] = {"class_type": "PathchSageAttentionKJ", "inputs": {"model": high, "sage_attention": "auto"}}
        wf["21"] = {"class_type": "PathchSageAttentionKJ", "inputs": {"model": low, "sage_attention": "auto"}}
        high, low = ["20", 0], ["21", 0]
    wf["3"] = {"class_type": "LoraLoaderModelOnly", "inputs": {"model": high, "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors", "strength_model": 1.0}}
    wf["4"] = {"class_type": "LoraLoaderModelOnly", "inputs": {"model": low, "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors", "strength_model": 1.0}}
    wf["5"] = {"class_type": "ModelSamplingSD3", "inputs": {"model": ["3", 0], "shift": 5.0}}
    wf["6"] = {"class_type": "ModelSamplingSD3", "inputs": {"model": ["4", 0], "shift": 5.0}}
    if three:
        # Primeros pasos sin LoRA (cfg real → mejor movimiento), luego high y low con LoRA
        total, a, cfg, b = THREE[three]
        wf["22"] = {"class_type": "ModelSamplingSD3", "inputs": {"model": high, "shift": 5.0}}
        wf["13"] = ksampler(["22", 0], ["12", 2], "12", 0, a, total, cfg, True, True)
        wf["14"] = ksampler(["5", 0], ["13", 0], "12", a, b, total, 1.0, False, True)
        wf["15"] = ksampler(["6", 0], ["14", 0], "12", b, 10000, total, 1.0, False, False)
        last = "15"
    else:
        wf["13"] = ksampler(["5", 0], ["12", 2], "12", 0, 2, 4, 1.0, True, True)
        wf["14"] = ksampler(["6", 0], ["13", 0], "12", 2, 10000, 4, 1.0, False, False)
        last = "14"
    wf["16"] = {"class_type": "VAEDecode", "inputs": {"samples": [last, 0], "vae": ["8", 0]}}
    wf["17"] = {"class_type": "CreateVideo", "inputs": {"images": ["16", 0], "fps": 16.0}}
    wf["18"] = {"class_type": "SaveVideo", "inputs": {"video": ["17", 0], "filename_prefix": f"bench/{prefix}", "format": "auto", "codec": "auto"}}
    return wf

def run(wf, out_path):
    r = urllib.request.Request(HOST + "/prompt", json.dumps({"prompt": wf}).encode(), {"Content-Type": "application/json"})
    try:
        pid = json.load(urllib.request.urlopen(r))["prompt_id"]
    except urllib.error.HTTPError as e:
        return None, e.read().decode()[:500]
    t0 = None
    while True:
        time.sleep(2)
        q = json.load(urllib.request.urlopen(HOST + "/queue"))
        if t0 is None and any(item[1] == pid for item in q["queue_running"]):
            t0 = time.time()  # medimos desde que empieza a correr, no desde que entra a la cola
        h = json.load(urllib.request.urlopen(f"{HOST}/history/{pid}"))
        if pid in h:
            st = h[pid]["status"]
            if st.get("status_str") == "error":
                return None, json.dumps(st["messages"])[-500:]
            for out in h[pid]["outputs"].values():
                for k in ("images", "videos", "gifs"):
                    for f in out.get(k, []):
                        url = (f"{HOST}/view?filename={urllib.parse.quote(f['filename'])}"
                               f"&subfolder={urllib.parse.quote(f['subfolder'])}&type={f['type']}")
                        urllib.request.urlretrieve(url, out_path)
            return time.time() - (t0 or time.time()), None

if __name__ == "__main__":
    img_path = sys.argv[1]
    names = sys.argv[2:] or list(VARIANTS)
    base = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base, "benchmark"); os.makedirs(out_dir, exist_ok=True)
    image = upload(img_path)
    # Calentamiento: carga los modelos para que no cuente en la primera variante
    print("calentando...", flush=True)
    run(workflow(image, 256, 144, False, False, "warmup"), os.path.join(out_dir, "_warmup.mp4"))
    results = {}
    for n in names:
        w, h, sage, three, *extra = VARIANTS[n]
        print(f"== {n}", flush=True)
        prompt = PROMPTS[extra[0]] if extra else None
        secs, err = run(workflow(image, w, h, sage, three, n, prompt), os.path.join(out_dir, f"{n}.mp4"))
        results[n] = {"segundos": round(secs, 1) if secs else None, "error": err}
        print(results[n], flush=True)
    path = os.path.join(out_dir, "resultados.json")
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(results)
    with open(path, "w") as f:
        json.dump(old, f, indent=2)
    print(json.dumps(results, indent=2))

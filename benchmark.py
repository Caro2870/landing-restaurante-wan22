# Benchmark A/B de Wan 2.2 I2V en la RTX: misma foto, mismo prompt, misma semilla.
# Uso: python -I benchmark.py fotos/01.jpg [variantes...]
import json, sys, time, uuid, os, urllib.request, urllib.parse

HOST = os.environ.get("COMFY_HOST", "http://127.0.0.1:8188")
SEED = 424242
PROMPT = ("evening exterior of a restaurant terrace, warm lights glowing, people chatting at tables under umbrellas, "
          "camera moves straight forward toward the entrance, slow zoom in, photorealistic")
NEG = "blurry, distorted, deformed faces, extra objects, text, watermark, low quality, flicker, morphing"

# nombre: (ancho, alto, sage, tres_samplers)
VARIANTS = {
    "A_base":      (832, 480, False, False),
    "B_sage":      (832, 480, True,  False),
    "C_3samplers": (832, 480, False, True),
    "D_sage_3s":   (832, 480, True,  True),
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

def workflow(image, w, h, sage, three, prefix):
    wf = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "7": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
        "8": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
        "9": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["7", 0], "text": PROMPT}},
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
        # 2 pasos sin LoRA (cfg real → mejor movimiento), luego high y low con LoRA. 6 pasos en total.
        wf["22"] = {"class_type": "ModelSamplingSD3", "inputs": {"model": high, "shift": 5.0}}
        wf["13"] = ksampler(["22", 0], ["12", 2], "12", 0, 2, 6, 3.5, True, True)
        wf["14"] = ksampler(["5", 0], ["13", 0], "12", 2, 3, 6, 1.0, False, True)
        wf["15"] = ksampler(["6", 0], ["14", 0], "12", 3, 10000, 6, 1.0, False, False)
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
        w, h, sage, three = VARIANTS[n]
        print(f"== {n}", flush=True)
        secs, err = run(workflow(image, w, h, sage, three, n), os.path.join(out_dir, f"{n}.mp4"))
        results[n] = {"segundos": round(secs, 1) if secs else None, "error": err}
        print(results[n], flush=True)
    with open(os.path.join(out_dir, "resultados.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))

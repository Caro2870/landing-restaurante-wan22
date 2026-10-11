import json, sys, time, urllib.request, uuid, os
HOST = os.environ.get("COMFY_HOST", "http://127.0.0.1:8188")
img_path, prompt, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
length = int(sys.argv[4]) if len(sys.argv) > 4 else 81
W, H = (int(sys.argv[5]), int(sys.argv[6])) if len(sys.argv) > 6 else (832, 480)

def upload(path):
    b = uuid.uuid4().hex
    data = open(path, "rb").read()
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{os.path.basename(path)}\"\r\nContent-Type: image/png\r\n\r\n").encode() + data + \
           f"\r\n--{b}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{b}--\r\n".encode()
    r = urllib.request.Request(HOST + "/upload/image", body, {"Content-Type": f"multipart/form-data; boundary={b}"})
    return json.load(urllib.request.urlopen(r))["name"]

name = upload(img_path)
neg = "blurry, distorted, deformed faces, deformed food, extra objects, text, watermark, low quality, flicker, morphing"
seed = int(time.time())
wf = {
 "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
 "2": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
 "3": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors", "strength_model": 1.0}},
 "4": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["2", 0], "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors", "strength_model": 1.0}},
 "5": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["3", 0], "shift": 5.0}},
 "6": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["4", 0], "shift": 5.0}},
 "7": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
 "8": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
 "9": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["7", 0], "text": prompt}},
 "10": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["7", 0], "text": neg}},
 "11": {"class_type": "LoadImage", "inputs": {"image": name}},
 "12": {"class_type": "WanImageToVideo", "inputs": {"positive": ["9", 0], "negative": ["10", 0], "vae": ["8", 0], "width": W, "height": H, "length": length, "batch_size": 1, "start_image": ["11", 0]}},
 "13": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["5", 0], "add_noise": "enable", "noise_seed": seed, "steps": 4, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "positive": ["12", 0], "negative": ["12", 1], "latent_image": ["12", 2], "start_at_step": 0, "end_at_step": 2, "return_with_leftover_noise": "enable"}},
 "14": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["6", 0], "add_noise": "disable", "noise_seed": seed, "steps": 4, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "positive": ["12", 0], "negative": ["12", 1], "latent_image": ["13", 0], "start_at_step": 2, "end_at_step": 10000, "return_with_leftover_noise": "disable"}},
 "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["8", 0]}},
 "16": {"class_type": "CreateVideo", "inputs": {"images": ["15", 0], "fps": 16.0}},
 "17": {"class_type": "SaveVideo", "inputs": {"video": ["16", 0], "filename_prefix": "video/landing", "format": "auto", "codec": "auto"}},
}
# SageAttention 2.2 vía KJNodes: ~2x más rápido en la RTX 5060 Ti (ver README). WAN_SAGE=0 para desactivar.
if os.environ.get("WAN_SAGE", "1") != "0":
    wf["20"] = {"class_type": "PathchSageAttentionKJ", "inputs": {"model": ["1", 0], "sage_attention": "auto"}}
    wf["21"] = {"class_type": "PathchSageAttentionKJ", "inputs": {"model": ["2", 0], "sage_attention": "auto"}}
    wf["3"]["inputs"]["model"] = ["20", 0]
    wf["4"]["inputs"]["model"] = ["21", 0]
r = urllib.request.Request(HOST + "/prompt", json.dumps({"prompt": wf}).encode(), {"Content-Type": "application/json"})
try:
    pid = json.load(urllib.request.urlopen(r))["prompt_id"]
except urllib.error.HTTPError as e:
    print(e.read().decode()); sys.exit(1)
t0 = time.time(); print("queued", pid, flush=True)
while True:
    time.sleep(5)
    h = json.load(urllib.request.urlopen(f"{HOST}/history/{pid}"))
    if pid in h:
        st = h[pid]["status"]
        if st.get("status_str") == "error":
            print(json.dumps(st["messages"])[-2000:]); sys.exit(1)
        for out in h[pid]["outputs"].values():
            for k in ("images", "videos", "gifs"):
                for f in out.get(k, []):
                    url = f"{HOST}/view?filename={urllib.parse.quote(f['filename'])}&subfolder={urllib.parse.quote(f['subfolder'])}&type={f['type']}"
                    dst = os.path.join(out_dir, f["filename"])
                    urllib.request.urlretrieve(url, dst); print("saved", dst)
        print(f"done in {time.time()-t0:.0f}s"); break

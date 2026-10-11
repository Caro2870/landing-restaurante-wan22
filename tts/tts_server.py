# Servidor de voz para el benchmark: un modelo por proceso (cada uno en su propio venv).
# Uso:  python tts_server.py --model chatterbox --port 8190
#       python tts_server.py --model f5 --port 8191
#       python tts_server.py --model xtts --port 8192
#
# POST /tts  JSON {"text": str, "ref_wav_b64": str, "ref_text": str (opcional), "seed": int}
#  → audio/wav, con la cabecera X-Gen-Seconds (tiempo de generación)
import argparse, base64, io, json, os, tempfile, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading

import torch
import torchaudio

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True, choices=["chatterbox", "f5", "xtts"])
ap.add_argument("--port", type=int, required=True)
ap.add_argument("--host", default="0.0.0.0")
args = ap.parse_args()

LOCK = threading.Lock()  # una generación a la vez en la GPU


# --- Backends ---------------------------------------------------------------
# Si la API de alguna librería cambió, ajusta solo la función de ese backend.

def load_chatterbox():
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    model = ChatterboxMultilingualTTS.from_pretrained(device="cuda")

    def gen(text, ref_path, ref_text):
        wav = model.generate(text, language_id="es", audio_prompt_path=ref_path)
        return wav.cpu(), model.sr
    return gen


def load_f5():
    # Checkpoint de F5-TTS afinado en español (el base solo habla inglés/chino)
    from huggingface_hub import hf_hub_download
    from f5_tts.api import F5TTS
    repo = os.environ.get("F5_REPO", "jpgallegoar/F5-Spanish")
    ckpt = hf_hub_download(repo, os.environ.get("F5_CKPT", "model_1200000.safetensors"))
    vocab = hf_hub_download(repo, os.environ.get("F5_VOCAB", "vocab.txt"))
    f5 = F5TTS(ckpt_file=ckpt, vocab_file=vocab, device="cuda")

    def gen(text, ref_path, ref_text):
        wav, sr, _ = f5.infer(ref_file=ref_path, ref_text=ref_text or "", gen_text=text)
        return torch.as_tensor(wav).reshape(1, -1).float(), sr
    return gen


def load_xtts():
    from TTS.api import TTS
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cuda")

    def gen(text, ref_path, ref_text):
        wav = tts.tts(text=text, speaker_wav=ref_path, language="es")
        return torch.tensor(wav).reshape(1, -1).float(), tts.synthesizer.output_sample_rate
    return gen


GEN = {"chatterbox": load_chatterbox, "f5": load_f5, "xtts": load_xtts}[args.model]()
print(f"[{args.model}] modelo cargado, escuchando en {args.host}:{args.port}", flush=True)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"model": args.model, "ok": True}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/tts":
            self.send_error(404)
            return
        try:
            req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(base64.b64decode(req["ref_wav_b64"]))
                ref_path = f.name
            with LOCK:
                torch.manual_seed(int(req.get("seed", 0)))
                torch.cuda.synchronize()
                t0 = time.time()
                wav, sr = GEN(req["text"], ref_path, req.get("ref_text"))
                torch.cuda.synchronize()
                secs = time.time() - t0
            os.unlink(ref_path)
            buf = io.BytesIO()
            torchaudio.save(buf, wav, sr, format="wav")
            data = buf.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("X-Gen-Seconds", f"{secs:.3f}")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:  # el error vuelve al cliente para poder diagnosticarlo
            body = json.dumps({"error": repr(e)}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, fmt, *a):
        print(f"[{args.model}] " + fmt % a, flush=True)


ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()

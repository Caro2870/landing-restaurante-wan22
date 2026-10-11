# Casa Brasa: landing con video IA generado en local

Una landing de restaurante que se recorre con el scroll como una película. Es una alternativa gratuita al flujo "Claude Code + Higgsfield": los clips se generan con **Wan 2.2 Image-to-Video 14B** en una **RTX 5060 Ti de 16 GB** propia, usando ComfyUI por Tailscale, sin créditos de ningún servicio.

- Las **escenas de comida** son clips de Wan 2.2 convertidos a una secuencia de frames que se dibuja en un `<canvas>` según el scroll.
- Las **escenas con gente** usan la foto original con movimiento de cámara hecho en código, porque Wan deforma las caras pequeñas. La excepción es la portada, que usa una versión a 720p.

## Benchmark A/B: SageAttention en Wan 2.2

Misma foto, mismo prompt, misma semilla (`424242`), 832×480, 81 frames (unos 5 s a 16 fps). Hardware: RTX 5060 Ti 16 GB, Ryzen 9 7900X, 32 GB de RAM, ComfyUI 0.39 portable, PyTorch 2.14 + CUDA 13.0, modelos fp8_scaled y LoRA lightx2v de 4 pasos. El tiempo se mide desde que el trabajo empieza a ejecutarse, con los modelos ya cargados después de una ronda de calentamiento.

| Variante | Qué cambia | Tiempo | vs. A |
|---|---|---:|---:|
| **A** base | 4 pasos con LoRA lightx2v | **166 s** | — |
| **B** SageAttention | A + SageAttention 2.2 (`PathchSageAttentionKJ`, modo `auto`) | **81 s** | **2,05× más rápido** |
| C 3 samplers v1 | 6 pasos: 2 sin LoRA (cfg 3.5) + 4 con LoRA | 239 s | 0,69× · ❌ inventa luces |
| D Sage + v1 | C + SageAttention | 144 s | 1,16× · ❌ inventa luces |
| E Sage + v2 | 8 pasos: 2 sin LoRA (cfg 3.5) | 219 s | 0,76× · ❌ inventa luces |
| F Sage + v3 | 6 pasos: 2 sin LoRA (cfg 2.0) | 144 s | 1,15× · ❌ inventa un arco |
| G Sage + v4 | 10 pasos: 3 sin LoRA (cfg 3.5) | 225 s | 0,74× · ❌ inventa un arco |
| H Sage + v5 | 12 pasos: 4 sin LoRA (cfg 2.5) | 273 s | 0,61× · ✅ fiel |
| K Sage, prompt neutro | como B | 89 s | 1,87× · ✅ fiel |
| I Sage + v3, prompt neutro | como F | 144 s | 1,15× · ✅ fiel |
| J Sage + v5, prompt neutro | como H | 273 s | 0,61× · ✅ fiel |

**Comparación interactiva (videos sincronizados, cortina y lupa): [benchmark.html](https://caro2870.github.io/landing-restaurante-wan22/benchmark.html)**

![A vs B](benchmark/A_vs_B.gif)

![Primer, medio y último frame de cada variante](benchmark/comparacion.png)

**Conclusiones**

- **SageAttention reduce el tiempo a la mitad sin perder calidad visible.** La composición, la luz y el detalle quedan iguales que en A. El movimiento de la gente cambia un poco (PSNR de 22,9 dB contra A), porque la atención cuantizada lleva el muestreo por otra trayectoria, no porque se degrade. No aparecieron los frames negros que se reportan en Blackwell.
- **El 2× es mayor que el 30 a 40 % que reportan los foros.** Puede deberse a que con 16 GB la atención pesa más en el tiempo total. Es un único run por variante, así que conviene tomarlo como una estimación.
- **Los 3 samplers fallaban por la combinación de prompt y configuración, no por la técnica.** Sin la LoRA y con un cfg mayor que 1, el modelo obedece mucho más al prompt. Con "warm lights glowing" y unos pinos en la foto, terminaba decorándolos con luces navideñas (C, D y E) o agregando un arco iluminado (F y G). Con más pasos y un cfg moderado (H), o con un prompt neutro (I y J), el resultado es fiel a la foto.
- **No está claro que los 3 samplers den mejor movimiento.** Cuando funcionan, I y J no se ven claramente mejores que K, y tardan entre 1,6 y 3 veces más. Para esta foto, la configuración simple con SageAttention es la mejor relación calidad/tiempo. Con 3 samplers, conviene describir solo lo que hay en la foto y el movimiento, sin adjetivos que el modelo pueda "dibujar".
- **Con caras, la resolución pesa más que el muestreo.** A 720p las caras de la terraza se ven claramente mejor que a 480p ([comparación](benchmark/benchmark_caras_480_vs_720.png)). Sin SageAttention cuesta unas 3 veces más tiempo.

Videos completos: [A_base](benchmark/A_base.mp4) · [B_sage](benchmark/B_sage.mp4) · [C_3samplers](benchmark/C_3samplers.mp4) · [D_sage_3s](benchmark/D_sage_3s.mp4) · [H](benchmark/H_sage_3s_v5.mp4) · [K](benchmark/K_sage_neutro.mp4) · [I](benchmark/I_sage_3s_v3_neutro.mp4) · [J](benchmark/J_sage_3s_v5_neutro.mp4) · [resultados.json](benchmark/resultados.json)

## Estructura

```
index.html          landing (canvas + scroll, sin dependencias)
fotos/              fotos de entrada (Unsplash)
clips/              clips generados con Wan 2.2
frames/             frames WebP que usa la landing + manifest.js
wan_i2v.py          genera un clip: foto + prompt → ComfyUI → mp4
generar_clips.sh    genera los 6 clips
extraer_frames.py   mp4 → frames WebP (requiere imageio-ffmpeg)
benchmark.py        benchmark A/B de variantes de Wan 2.2
benchmark.html      comparación interactiva de los videos del benchmark
tts/tts_server.py   servidor de voz (Chatterbox / F5-TTS) para el benchmark de clonación
```

## Uso

```bash
export COMFY_HOST=http://<ip-de-tu-pc-con-gpu>:8188
python wan_i2v.py fotos/03.jpg "plated dish, slow cinematic push-in" clips 81
python extraer_frames.py
python -m http.server 5173   # abrir http://localhost:5173
```

El servidor de ComfyUI necesita los modelos de [Comfy-Org/Wan_2.2_ComfyUI_Repackaged](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged) (I2V high/low noise 14B fp8_scaled, umt5_xxl fp8, wan_2.1_vae y las LoRAs lightx2v de 4 pasos). Para SageAttention necesita además [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes).

## Créditos

Restaurante ficticio. Fotos de [Unsplash](https://unsplash.com) (Licencia Unsplash). Video generado con [Wan 2.2](https://github.com/Wan-Video/Wan2.2) (Apache 2.0).

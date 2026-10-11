#!/bin/bash
# Genera un clip por foto en la RTX (ComfyUI por Tailscale)
cd "$(dirname "$0")"
gen() { echo "== $1"; python -I wan_i2v.py "fotos/$1.jpg" "$2" clips 81 && mv clips/landing_*.mp4 "clips/$1.mp4"; }
gen 01 "evening exterior of a restaurant terrace, warm lights glowing, people chatting at tables under umbrellas, slow smooth cinematic dolly forward toward the entrance, gentle ambient movement, photorealistic"
gen 02 "inside a busy restaurant at night, paper lanterns softly swaying, diners and waiters moving naturally, slow cinematic camera glide forward through the dining room, warm light, photorealistic"
gen 03 "elegant plated dish on a restaurant table, candlelight flickering, wine glasses glinting, slow cinematic push-in toward the plate, shallow depth of field, photorealistic"
gen 04 "seared salmon fillet with fresh salsa in a white bowl, thin steam rising from the hot fish, sauce glistening, very slow camera push-in and slight orbit, food commercial, photorealistic"
gen 05 "glazed barbecue ribs on a wooden board, steam rising from the hot meat, glaze glistening, slow cinematic camera orbit around the board, dramatic food commercial lighting, photorealistic"
gen 06 "top-down view of friends sharing burgers and fries at a table, hands reaching for food, glasses being lifted, natural movement, slow gentle camera rise, photorealistic"
echo FIN

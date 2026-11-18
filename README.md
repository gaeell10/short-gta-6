# Short GTA 6 — 7 secretos

- `GTA6_secretos_short.mp4`: el short final (1080x1920, 30 fps, 1:21)
- `guion/guion.md`: el guion
- `build/`: script.json (texto), tts.py (voz Kokoro, voz `em_alex`), music.py (música y SFX generados), render.py (montaje)

Para regenerarlo: `python3 build/tts.py <work>/vo em_alex build/script.json`, `python3 build/music.py <work>/sfx 90` y `python3 build/render.py <clip.mp4> <work> salida.mp4`.

# Short GTA 6 — 7 secretos

- `GTA6_secretos_short.mp4`: el short final (1080x1920, 30 fps, 1:21)
- `guion/guion.md`: el guion
- `build/`: script.json (texto), tts.py (voz Kokoro, voz `em_alex`), music.py (música y SFX generados), render.py (montaje)

Para regenerarlo: `python3 build/tts.py <work>/vo em_alex build/script.json`, `python3 build/music.py <work>/sfx 90` y `python3 build/render.py <clip.mp4> <work> salida.mp4`.

## Remotion

- `remotion/`: proyecto Remotion (v4.0.546, plantilla blank). `cd remotion && npm install && npm run dev` abre el Studio; `npx remotion render` renderiza.
- Skills de agente de Remotion en `remotion/.agents/skills/` (enlazadas en `.claude/skills` para Claude Code).

## Short de prueba: Punto Nemo

- `PuntoNemo_short.mp4`: short de prueba (1080x1920, 30 fps, 41 s) hecho con Remotion.
- `nemo/script.json` (texto), `nemo/tts.py` (voz Kokoro `em_alex` + `timings.json`), `nemo/sound.py` (ambiente y SFX generados).
- Composición: `remotion/src/nemo/` (id `PuntoNemo`). Regenerar: `python3 nemo/tts.py remotion/public/nemo em_alex remotion/src/nemo/timings.json`, `python3 nemo/sound.py remotion/public/nemo 42`, y `cd remotion && npx remotion render PuntoNemo ../PuntoNemo_short.mp4`.

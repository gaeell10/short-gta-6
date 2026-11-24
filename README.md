# Short GTA 6 — 7 secretos

- `GTA6_secretos_short.mp4`: el short final (1080x1920, 30 fps, 1:21)
- `guion/guion.md`: el guion
- `build/`: script.json (texto), tts.py (voz Kokoro, voz `em_alex`), music.py (música y SFX generados), render.py (montaje)

Para regenerarlo: `python3 build/tts.py <work>/vo em_alex build/script.json`, `python3 build/music.py <work>/sfx 90` y `python3 build/render.py <clip.mp4> <work> salida.mp4`.

## Remotion

- `remotion/`: proyecto Remotion (v4.0.546, plantilla blank). `cd remotion && npm install && npm run dev` abre el Studio; `npx remotion render` renderiza.
- Skills de agente de Remotion en `remotion/.agents/skills/` (enlazadas en `.claude/skills` para Claude Code).

## Short de prueba: Punto Nemo

- `PuntoNemo_short.mp4`: short de prueba (1080x1920, 30 fps, 42 s) hecho con Remotion.
- Voz: Higgsfield `seed_audio`, voz "Juan" (speech_rate 25), una generación por frase. Frases y enlaces en `nemo/voz_juan.json`; `nemo/montar_voz.py` las une, acelera un 12 % y genera `remotion/src/nemo/timings.json`.
- `nemo/sound.py`: ambiente y SFX generados por código. `nemo/tts.py`: voz alternativa offline con Kokoro.
- Composición: `remotion/src/nemo/` (id `PuntoNemo`). Render: `cd remotion && npx remotion render PuntoNemo ../PuntoNemo_short.mp4`.

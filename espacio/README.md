# Short "7 curiosidades del espacio" (3D cartoon)

- `espacio_curiosidades_short.mp4`: video final (1080x1920, 24 fps, 1:30), voz en off alegre, sin música.
- `guion.md`: guion con tiempos.
- `build/`:
  - `script.json`: texto de la locución
  - `tts.py`: voz (Kokoro, voz `ef_dora`, velocidad 1.05)
  - `toon.py`: utilidades de Blender (materiales, contorno cartoon, mascota "Bipo")
  - `scenes.py`: las 9 escenas 3D (Venus, Saturno en la bañera, el Sol, la Luna, Marte, estrella de neutrones, playa)
  - `timeline.py`: tiempos de cada escena y cortes de cámara
  - `render_scene.py`: render con Cycles (540x960, 8 spp + denoise)
  - `edit.py`: montaje (títulos, subtítulos karaoke, rótulos, transiciones, efectos de sonido, mezcla)
  - `fonts/`: Lilita One y Fredoka (SIL OFL)

Para regenerarlo (necesita `pip install bpy==5.1.2 kokoro-onnx soundfile scipy` y los modelos de Kokoro en `/tmp/claude-0/voices`):

```
python3 build/tts.py <work>/vo ef_dora build/script.json 1.05
python3 build/render_scene.py <work>/vo/voice_meta.json <work>/frames 0 2 all &   # worker 0
python3 build/render_scene.py <work>/vo/voice_meta.json <work>/frames 1 2 all     # worker 1
python3 build/edit.py <work> espacio_curiosidades_short.mp4
```

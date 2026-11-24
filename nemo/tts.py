# Uso: python3 tts.py <dir_wav> <voz> <timings.json>
import json, re, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
k = Kokoro("/tmp/claude-0/voices/kokoro-v1.0.onnx", "/tmp/claude-0/voices/voices-v1.0.bin")
out = sys.argv[1]; voice = sys.argv[2] if len(sys.argv) > 2 else "em_alex"
segs = json.load(open(__file__.rsplit("/", 1)[0] + "/script.json"))
sr = 24000; parts = []; t = 0.0; meta = []
for s in segs:
    sents = [x.strip() for x in re.split(r'(?<=[.?!,])\s+', s["text"]) if x.strip()]
    start = t; lines = []
    for x in sents:
        a, sr = k.create(x, voice=voice, speed=1.1, lang="es")
        idx = np.where(np.abs(a) > 0.01)[0]
        a = a[max(0, idx[0]-600):idx[-1]+1200] if len(idx) else a
        lines.append({"text": x, "start": round(t, 3), "end": round(t + len(a)/sr, 3)})
        gap = 0.12 if x.endswith(",") else 0.25
        parts += [a, np.zeros(int(sr*gap), dtype=np.float32)]
        t += len(a)/sr + gap
    parts.append(np.zeros(int(sr*0.2), dtype=np.float32)); t += 0.2
    meta.append({"id": s["id"], "start": round(start, 3), "end": round(t, 3), "lines": lines})
sf.write(f"{out}/voz.wav", np.concatenate(parts), sr)
json.dump({"total": round(t, 3), "scenes": meta}, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
print("total", round(t, 2))

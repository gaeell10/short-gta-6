"""Voiceover with Kokoro (local). usage: tts.py <outdir> <voice> <script.json> [speed]"""
import json, re, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
k = Kokoro("/tmp/claude-0/voices/kokoro.onnx", "/tmp/claude-0/voices/voices.bin")
out, voice, segs = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3]))
speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.08
meta = []
for s in segs:
    sents = [x.strip() for x in re.split(r'(?<=[.?!])\s+', s["text"]) if x.strip()]
    parts, st, t, sr = [], [], 0.0, 24000
    for x in sents:
        a, sr = k.create(x, voice=voice, speed=speed, lang="es")
        idx = np.where(np.abs(a) > 0.01)[0]
        a = a[max(0, idx[0] - 600):idx[-1] + 1200] if len(idx) else a
        st.append({"text": x, "start": t, "end": t + len(a) / sr})
        parts += [a, np.zeros(int(sr * 0.22), np.float32)]
        t += len(a) / sr + 0.22
    audio = np.concatenate(parts)
    sf.write(f"{out}/{s['id']}.wav", audio, sr)
    meta.append({**s, "dur": len(audio) / sr, "sentences": st})
    print(s["id"], round(len(audio) / sr, 2))
json.dump(meta, open(f"{out}/voice_meta.json", "w"), ensure_ascii=False, indent=1)
print("total", round(sum(m["dur"] for m in meta), 2))

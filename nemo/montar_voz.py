"""Une las frases de voz (Higgsfield, voz Juan) en voz.wav y genera timings.json.
Uso: python3 montar_voz.py <carpeta_con_wavs_00..13> <voz.wav> <timings.json>"""
import json, subprocess, sys, numpy as np, soundfile as sf
from math import gcd
from scipy.signal import resample_poly
src, out_wav, out_json = sys.argv[1:4]
lines = json.load(open(__file__.rsplit("/", 1)[0] + "/voz_juan.json"))
SR = 24000; parts = []; t = 0.0; scenes = []
for i, l in enumerate(lines):
    a, sr = sf.read(f"{src}/{i:02d}.wav", dtype="float32")
    if a.ndim > 1: a = a.mean(1)
    if sr != SR:
        g = gcd(sr, SR); a = resample_poly(a, SR // g, sr // g).astype(np.float32)
    idx = np.where(np.abs(a) > 0.01)[0]
    a = a[max(0, idx[0]-480):idx[-1]+1200] if len(idx) else a
    if not scenes or scenes[-1]["id"] != l["scene"]:
        if scenes: scenes[-1]["end"] = round(t, 3)
        scenes.append({"id": l["scene"], "start": round(t, 3), "lines": []})
    text = l["text"].replace("¡", "")
    scenes[-1]["lines"].append({"text": text, "start": round(t, 3), "end": round(t + len(a)/SR, 3)})
    gap = 0.12
    parts += [a, np.zeros(int(SR*gap), np.float32)]; t += len(a)/SR + gap
scenes[-1]["end"] = round(t, 3)
v = np.concatenate(parts); v = v / np.abs(v).max() * 0.95
TEMPO = 1.12  # acelera la voz sin cambiar el tono
tmp = out_wav + ".tmp.wav"; sf.write(tmp, v, SR)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", f"atempo={TEMPO}", out_wav], check=True)
subprocess.run(["rm", tmp])
t /= TEMPO
for sc in scenes:
    sc["start"] = round(sc["start"]/TEMPO, 3); sc["end"] = round(sc["end"]/TEMPO, 3)
    for ln in sc["lines"]:
        ln["start"] = round(ln["start"]/TEMPO, 3); ln["end"] = round(ln["end"]/TEMPO, 3)
json.dump({"total": round(t, 3), "scenes": scenes}, open(out_json, "w"), ensure_ascii=False, indent=1)
print("total", round(t, 2)); [print(s["id"], s["start"]) for s in scenes]

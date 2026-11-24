"""Ambiente misterioso + SFX generados por código (sin audio con copyright).
Uso: python3 sound.py <dir_salida> <segundos>"""
import sys, numpy as np, soundfile as sf
sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/build")
from music import SR, lp, hp, bp, whoosh, boom, rng

def drone(total):
    n = int(total * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    # acorde menor grave (Re menor) con batido lento
    for f, a in [(73.42, .5), (110.0, .3), (87.31, .25), (146.83, .15), (220.0, .06)]:
        out += a * np.sin(2*np.pi*f*t + 0.3*np.sin(2*np.pi*0.07*t)) * (0.7 + 0.3*np.sin(2*np.pi*0.11*t + f))
    # ruido de océano
    sea = lp(rng.standard_normal(n), 500) * (0.5 + 0.5*np.sin(2*np.pi*0.09*t))**2 * 0.6
    out += sea
    # pulso tipo latido cada 1.1 s
    k_n = int(0.25*SR); tk = np.arange(k_n)/SR
    kick = np.sin(2*np.pi*np.cumsum(40 + 50*np.exp(-tk*25))/SR) * np.exp(-tk*14)
    for st in np.arange(0.0, total, 1.1):
        for d, g in [(0, 1.0), (0.22, 0.6)]:
            i = int((st+d)*SR); j = min(n, i+k_n)
            if i < n: out[i:j] += 0.8*g*kick[:j-i]
    fade = np.minimum(1, t/1.5) * np.minimum(1, (total - t)/2.0)
    out = out * fade
    return (out / np.abs(out).max() * 0.8).astype(np.float32)

def ping(dur=1.6):
    n = int(dur*SR); t = np.arange(n)/SR
    s = np.sin(2*np.pi*1320*t) * np.exp(-t*3) + 0.4*np.sin(2*np.pi*1980*t)*np.exp(-t*5)
    return (s*0.6).astype(np.float32)

out, total = sys.argv[1], float(sys.argv[2])
sf.write(f"{out}/ambiente.wav", drone(total), SR)
sf.write(f"{out}/whoosh.wav", whoosh(), SR)
sf.write(f"{out}/boom.wav", boom(), SR)
sf.write(f"{out}/ping.wav", ping(), SR)
print("ok")

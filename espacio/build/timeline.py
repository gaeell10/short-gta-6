"""Shared timeline: segment timing from the voiceover + camera cuts per scene."""
import json

FPS = 24
TOTAL = 90.0
VO_OFF = 0.15
CTA_EXTRA = 1.2
# camera cuts per scene: (time in voice seconds, shot index)
CUTS = {
    "hook": [(0, 0), (3.6, 1), (6.9, 2)],
    "s1": [(0, 0), (3.0, 1), (6.6, 2)],
    "s2": [(0, 0), (4.0, 1), (7.0, 0)],
    "s3": [(0, 0), (5.8, 1), (6.7, 2)],
    "s4": [(0, 0), (2.6, 2), (5.0, 1)],
    "s5": [(0, 0), (3.2, 2), (5.6, 1), (7.8, 3)],
    "s6": [(0, 0), (6.4, 1), (9.3, 2)],
    "s7": [(0, 0), (2.8, 1), (5.8, 2), (8.3, 3)],
    "cta": [(0, 0)],
}


def load(meta_path):
    meta = json.load(open(meta_path))
    pad = (TOTAL - sum(m["dur"] for m in meta) - CTA_EXTRA) / len(meta)
    segs, f0 = [], 0
    t_acc = 0.0
    for m in meta:
        dur = m["dur"] + pad + (CTA_EXTRA if m["id"] == "cta" else 0)
        t_acc += dur
        f1 = round(t_acc * FPS)
        segs.append({**m, "f0": f0, "f1": f1, "t0": f0 / FPS, "t1": f1 / FPS})
        f0 = f1
    return segs


def shot_at(sid, t):
    """t = scene-local seconds. returns (shot index, seconds since the cut)."""
    k, c0 = 0, 0.0
    for ct, sk in CUTS[sid]:
        ct = ct + VO_OFF if ct > 0 else 0.0
        if t >= ct:
            k, c0 = sk, ct
    return k, t - c0

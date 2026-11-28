"""Montaje final: frames 3D + voz + SFX + títulos + subtítulos karaoke -> MP4 vertical 1080x1920.
usage: edit.py <work dir> <out.mp4> [preview_seconds_csv]"""
import json
import math
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.signal import resample_poly

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline as TL

WORK, OUT = sys.argv[1], sys.argv[2]
PREVIEW = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None
W, H, FPS, SR = 1080, 1920, TL.FPS, 48000
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
LILITA = f"{FD}/LilitaOne-Regular.ttf"
FREDOKA = f"{FD}/Fredoka.ttf"
YELLOW, PINK, CYAN, WHITE = (255, 214, 10), (255, 77, 160), (60, 220, 255), (255, 255, 255)
INK = (40, 12, 70)
GREEN = (90, 230, 110)
SEG_COL = {"hook": YELLOW, "s1": (255, 160, 50), "s2": CYAN, "s3": (255, 190, 30), "s4": (200, 200, 220),
           "s5": (90, 170, 255), "s6": (130, 230, 255), "s7": (255, 220, 120), "cta": PINK}

segs = TL.load(f"{WORK}/vo/voice_meta.json")
NF = segs[-1]["f1"]
TOTAL = NF / FPS
for s in segs:
    s["sents"] = [{"start": s["t0"] + TL.VO_OFF + x["start"], "end": s["t0"] + TL.VO_OFF + x["end"],
                   "text": x["text"]} for x in s["sentences"]]

# karaoke chunks (2-3 words), word timing proportional to length
chunks = []
for s in segs:
    for se in s["sents"]:
        words = se["text"].split()
        wts = np.array([len(w.strip(".,¿?¡!")) + 2.0 for w in words], float)
        edges = se["start"] + np.concatenate([[0], np.cumsum(wts)]) / wts.sum() * (se["end"] - se["start"])
        i = 0
        while i < len(words):
            j = min(len(words), i + 3)
            if len(words) - j == 1:
                j += 1
            chunks.append((edges[i], edges[j], words[i:j], [(edges[q], edges[q + 1]) for q in range(i, j)]))
            i = j

# facts on screen: (seg, sentence idx, delay, kind, payload)
STICKERS = {
    "s1": [(1, 0.3, "pill", ("1 DÍA > 1 AÑO", YELLOW)), (2, 0.6, "duo", ("DÍA: 243 DÍAS", "AÑO: 225 DÍAS"))],
    "s2": [(2, 0.8, "pill", ("¡FLOTARÍA!", CYAN))],
    "s3": [(2, 1.0, "count", (1_000_000, "TIERRAS DENTRO DEL SOL")), (4, 0.6, "pill", ("LUZ: ~8 MINUTOS", YELLOW))],
    "s4": [(2, 1.2, "pill", ("MILLONES DE AÑOS", WHITE))],
    "s5": [(1, 0.8, "pill", ("ATARDECER AZUL", CYAN))],
    "s6": [(1, 2.4, "pill", ("MILES DE MILLONES DE TONELADAS", YELLOW)), (2, 0.4, "pill", ("1 CUCHARADITA = 1 MONTAÑA", PINK))],
    "s7": [(1, 1.2, "pill", ("ESTRELLAS > ARENA", YELLOW))],
}

# ---------------------------------------------------------------- drawing
_fc, _tc = {}, {}


def font(path, size, weight=None):
    k = (path, size, weight)
    if k not in _fc:
        f = ImageFont.truetype(path, size)
        if weight:
            f.set_variation_by_axes([weight, 100])
        _fc[k] = f
    return _fc[k]


def text_img(text, size, fill=WHITE, stroke=10, stroke_fill=INK, max_w=None, path=LILITA, shadow=True):
    key = (text, size, fill, stroke, stroke_fill, max_w, path, shadow)
    if key in _tc:
        return _tc[key]
    f = font(path, size)
    while max_w and f.getbbox(text, stroke_width=stroke)[2] - f.getbbox(text, stroke_width=stroke)[0] > max_w:
        size -= 4
        f = font(path, size)
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    pad = 24
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad + 10), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l, pad - t + 10), text, font=f, fill=INK + (255,), stroke_width=stroke,
                                stroke_fill=INK + (255,))
        im = Image.alpha_composite(im, sh)
    ImageDraw.Draw(im).text((pad - l, pad - t), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    _tc[key] = im
    return im


def pill(text, size, bg, fg=INK, border=INK):
    key = ("pill", text, size, bg, fg)
    if key in _tc:
        return _tc[key]
    f = font(FREDOKA, size, 700)
    l, t, r, b = f.getbbox(text)
    px, py = int(size * 0.6), int(size * 0.32)
    w, h = r - l + 2 * px, b - t + 2 * py
    im = Image.new("RGBA", (w + 12, h + 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 12, w + 5, h + 11), radius=h // 2, fill=INK)
    d.rounded_rectangle((3, 3, w + 3, h + 3), radius=h // 2, fill=bg, outline=border, width=5)
    d.text((px - l + 3, py - t + 3), text, font=f, fill=fg)
    _tc[key] = im
    return im


def paste(canvas, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def back(x):
    x = min(max(x, 0), 1)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def eout(x):
    x = min(max(x, 0), 1)
    return 1 - (1 - x) ** 3


def seg_at(t):
    for s in segs:
        if s["t0"] <= t < s["t1"]:
            return s
    return segs[-1]


# vignette + bottom shade for subtitles
yy = np.linspace(0, 1, H)[:, None]
xx = np.linspace(-1, 1, W)[None, :]
VIG = (1 - 0.28 * np.clip((xx ** 2 + ((yy - 0.5) * 2) ** 2) / 2, 0, 1))[..., None].astype(np.float32)
SHADE = np.clip((yy - 0.62) / 0.38, 0, 1) ** 1.6 * 0.45
TOPSH = np.clip((0.2 - yy) / 0.2, 0, 1) ** 1.5 * 0.35
DARK = (1 - SHADE - TOPSH)[..., None].astype(np.float32)


def load_frame(sid, f):
    p = f"{WORK}/frames/{sid}/{f:05d}.png"
    if not os.path.exists(p):
        return np.zeros((H, W, 3), np.float32) + 40
    im = Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    return np.asarray(im, np.float32)


def render(fi):
    t = fi / FPS
    s = seg_at(t)
    sid = s["id"]
    lt = t - s["t0"]
    lf = fi - s["f0"]
    a = load_frame(sid, lf)
    # zoom punch at segment start
    z = 1 + 0.10 * max(0, 1 - lt / 0.25) ** 2 if s is not segs[0] else 1.0
    if z > 1.001:
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        cw, ch = W / z, H / z
        im = im.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
        a = np.asarray(im, np.float32)
    a = a * VIG * DARK
    canvas = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    col = SEG_COL[sid]

    # ---------------- titles
    if sid == "hook":
        bob = 6 * math.sin(t * 4)
        paste(canvas, text_img("7 CURIOSIDADES", 128, YELLOW, max_w=1000), W / 2, 210 + bob,
              back(lt / 0.4), rot=2 * math.sin(t * 2.5))
        if lt > 0.3:
            paste(canvas, text_img("DEL ESPACIO", 112, WHITE, max_w=1000), W / 2, 350 - bob,
                  back((lt - 0.3) / 0.4), rot=-2 * math.sin(t * 2.5))
        if lt > 1.0:
            paste(canvas, pill("¡VAMOS DE VIAJE! 🚀".replace(" 🚀", ""), 44, PINK, WHITE), W / 2, 470,
                  back((lt - 1.0) / 0.4))
    elif s["num"]:
        n = s["num"]
        sl = eout(lt / 0.35)
        paste(canvas, pill(f"CURIOSIDAD #{n}", 46, col), W / 2 - (1 - sl) * 800, 165)
        if lt > 0.12:
            paste(canvas, text_img(s["title"], 118, WHITE, max_w=1000), W / 2, 300 + 4 * math.sin(t * 3),
                  back((lt - 0.12) / 0.4))
        d = ImageDraw.Draw(canvas)
        for i in range(7):
            x = W / 2 + (i - 3) * 50
            if i + 1 < n:
                d.ellipse((x - 11, 404, x + 11, 426), fill=GREEN, outline=INK, width=4)
            elif i + 1 == n:
                r = 17 + 3 * math.sin(t * 8)
                d.ellipse((x - r, 415 - r, x + r, 415 + r), fill=YELLOW, outline=INK, width=5)
            else:
                d.ellipse((x - 11, 404, x + 11, 426), fill=(255, 255, 255, 90), outline=INK, width=4)
    elif sid == "cta":
        b = 1 + 0.05 * math.sin(lt * 8)
        paste(canvas, text_img("¡SÍGUEME!", 150, PINK, stroke=12), W / 2, 220, back(lt / 0.4) * b,
              rot=3 * math.sin(t * 3))
        if lt > 0.25:
            paste(canvas, text_img("PARA MÁS VIAJES", 84, WHITE, max_w=1000), W / 2, 365, back((lt - 0.25) / 0.4))
            paste(canvas, text_img("POR EL ESPACIO", 84, YELLOW, max_w=1000), W / 2, 460, back((lt - 0.4) / 0.4))
        # like button
        if lt > 3.8:
            p = back((lt - 3.8) / 0.4)
            paste(canvas, pill("♥ ME GUSTA", 52, (255, 60, 90), WHITE), W / 2, 1180, p * (1 + 0.06 * math.sin(lt * 10)))

    # ---------------- stickers / counters (middle-lower area)
    for si, delay, kind, pay in STICKERS.get(sid, []):
        if si >= len(s["sents"]):
            continue
        c0 = s["sents"][si]["start"] + delay
        if t < c0:
            continue
        p = back((t - c0) / 0.4)
        wob = 2.5 * math.sin((t - c0) * 5)
        y = 1240
        if kind == "pill":
            paste(canvas, pill(pay[0], 50, pay[1]), W / 2, y, p, rot=wob)
        elif kind == "duo":
            paste(canvas, pill(pay[0], 48, (255, 170, 60)), W / 2, y - 45, p, rot=-wob)
            if t > c0 + 1.2:
                paste(canvas, pill(pay[1], 48, CYAN), W / 2, y + 60, back((t - c0 - 1.2) / 0.4), rot=wob)
        elif kind == "count":
            q = eout((t - c0) / 1.4)
            v = int(pay[0] * q)
            txt = f"{v:,}".replace(",", ".")
            sc = 1 + 0.18 * max(0, 1 - (t - c0 - 1.4) / 0.3) if t - c0 > 1.4 else 1.0
            paste(canvas, text_img(txt, 130, YELLOW, stroke=12), W / 2, y - 40, sc * min(1, p))
            paste(canvas, pill(pay[1], 40, PINK, WHITE), W / 2, y + 70, p)
    # hide stickers of previous sentences? keep: they stay until the segment ends (they are short lists)

    # ---------------- karaoke subtitles
    for c in chunks:
        if c[0] <= t < c[1] + 0.06:
            act = 0
            for i, (ws, we) in enumerate(c[3]):
                if t >= ws:
                    act = i
            ims = [text_img(w.upper(), 96, YELLOW if i == act else WHITE, stroke=11) for i, w in enumerate(c[2])]
            gap = -30
            tw = sum(im.width for im in ims) + gap * (len(ims) - 1)
            sc = min(1.0, 1020 / tw)
            pop = 1 + 0.10 * max(0, 1 - (t - c[0]) / 0.12)
            x = W / 2 - tw * sc / 2
            for i, im in enumerate(ims):
                k = sc * (pop if i == act else 1.0) * (1.06 if i == act else 1.0)
                paste(canvas, im, x + im.width * sc / 2, 1560 - (8 if i == act else 0), k)
                x += (im.width + gap) * sc
            break

    arr = np.asarray(canvas.convert("RGB"), np.float32)
    # flash at segment start
    if s is not segs[0] and lt < 0.12:
        k = 0.65 * (1 - lt / 0.12)
        arr = arr * (1 - k) + 255 * k
    # fade out the last 0.4s
    if t > TOTAL - 0.4:
        arr *= max(0, (TOTAL - t) / 0.4)
    # progress bar
    d = int(W * (fi + 1) / NF)
    arr[H - 14:, :d] = YELLOW
    arr[H - 14:, d:] *= 0.4
    return np.clip(arr, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- audio (voz + SFX, sin música)
def sfx_whoosh(d=0.45, up=True):
    n = int(d * SR)
    x = np.random.default_rng(1).standard_normal(n).astype(np.float32)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    # moving band-pass via cumulative one-pole lowpass with varying coefficient
    fc = np.linspace(500, 5000, n) if up else np.linspace(5000, 500, n)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.zeros(n, np.float32)
    prev = 0.0
    for i in range(n):
        prev = (1 - a[i]) * x[i] + a[i] * prev
        y[i] = prev
    hp = y - np.concatenate([[0], y[:-1]]) * 0.9
    return (hp * env * 0.9 / (np.abs(hp).max() + 1e-9)).astype(np.float32)


def sfx_pop(f0=900, f1=300, d=0.12):
    tt = np.arange(int(d * SR)) / SR
    f = f0 * (f1 / f0) ** (tt / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-tt * 30) * 0.8).astype(np.float32)


def sfx_ding(f=1320, d=0.9):
    tt = np.arange(int(d * SR)) / SR
    y = sum(a * np.sin(2 * np.pi * f * m * tt) for m, a in ((1, 1), (2.76, 0.4), (5.4, 0.2)))
    return (y * np.exp(-tt * 5) * 0.35).astype(np.float32)


def sfx_sparkle(d=1.0, seed=3):
    r = np.random.default_rng(seed)
    n = int(d * SR)
    y = np.zeros(n, np.float32)
    for _ in range(14):
        st = int(r.uniform(0, d - 0.15) * SR)
        g = sfx_ding(r.uniform(2000, 4200), 0.15) * r.uniform(0.3, 0.7)
        y[st:st + len(g)] += g[: n - st]
    return y


def sfx_boing(d=0.4):
    tt = np.arange(int(d * SR)) / SR
    f = 180 + 120 * np.sin(2 * np.pi * 9 * tt) * np.exp(-tt * 4)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-tt * 6) * 0.6).astype(np.float32)


def build_audio():
    n = int(TOTAL * SR) + SR
    mix = np.zeros(n, np.float32)

    def put(x, t, g=1.0):
        st = int(t * SR)
        if 0 <= st < n:
            seg = x[: n - st]
            mix[st:st + len(seg)] += seg * g

    for s in segs:
        a, sr = sf.read(f"{WORK}/vo/{s['id']}.wav", dtype="float32")
        a = resample_poly(a, SR, sr).astype(np.float32)
        a = a / (np.abs(a).max() + 1e-9) * 0.9
        put(a, s["t0"] + TL.VO_OFF, 1.0)
    wh = sfx_whoosh()
    for s in segs[1:]:
        put(wh, s["t0"] - 0.22, 0.22)
    pop = sfx_pop()
    put(pop, 0.05, 0.35)
    put(sfx_pop(1100, 400), 0.35, 0.3)
    for s in segs:
        if s["num"]:
            put(pop, s["t0"] + 0.12, 0.3)
        if s["id"] == "cta":
            put(pop, s["t0"] + 0.05, 0.35)
            put(sfx_pop(1100, 400), s["t0"] + 0.3, 0.3)
            put(sfx_ding(1568), s["t0"] + 3.85, 0.5)
        for si, delay, kind, pay in STICKERS.get(s["id"], []):
            if si < len(s["sents"]):
                c0 = s["sents"][si]["start"] + delay
                put(sfx_ding(1760 if kind == "count" else 1320), c0 + (1.4 if kind == "count" else 0), 0.45)
                if kind == "duo":
                    put(sfx_ding(1568), c0 + 1.2, 0.45)
    hook = segs[0]
    put(sfx_sparkle(1.2), hook["t0"] + TL.VO_OFF + 6.9, 0.35)  # despegamos
    put(sfx_whoosh(0.8, True), hook["t0"] + TL.VO_OFF + 7.0, 0.3)
    s4 = next(s for s in segs if s["id"] == "s4")
    for k in range(int((s4["t1"] - s4["t0"]) * 0.45) + 1):  # low-gravity hops
        put(sfx_boing(), s4["t0"] + k / 0.45 + 0.1, 0.12)
    cta = segs[-1]
    for k in range(int((cta["t1"] - cta["t0"]) * 1.2)):
        put(sfx_boing(0.3), cta["t0"] + k / 1.2, 0.07)
    put(sfx_sparkle(1.5, 7), cta["t0"] + 0.1, 0.25)
    mix = mix[: int(TOTAL * SR)]
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.95
    sf.write(f"{WORK}/mix.wav", mix, SR)


if PREVIEW:
    for ts in PREVIEW:
        Image.fromarray(render(int(ts * FPS))).save(f"{WORK}/prev_{ts:05.1f}.png")
    sys.exit()

build_audio()
ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-i", f"{WORK}/mix.wav", "-c:v", "libx264", "-preset", "medium",
                       "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
                       "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
for fi in range(NF):
    ff.stdin.write(render(fi).tobytes())
    if fi % 240 == 0:
        print("frame", fi, flush=True)
ff.stdin.close()
ff.wait()
print("done", OUT)

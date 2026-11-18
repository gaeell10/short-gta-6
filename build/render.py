"""Render the vertical GTA 6 short (1080x1920, 30fps) from the gameplay clip + voiceover + generated music."""
import json
import math
import subprocess
import sys

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.signal import resample_poly

SRC, WORK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
PREVIEW = len(sys.argv) > 4 and sys.argv[4] == "preview"

W, H, FPS, SR = 1080, 1920, 30, 44100
PX, PY, PW, PH = 30, 500, 1020, 1000  # gameplay panel
FONT_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
PINK, CYAN, YELLOW, WHITE = (255, 46, 151), (45, 226, 230), (255, 225, 77), (255, 255, 255)
CREDIT = "Gameplay: @friedtowels (TikTok)"
PAD, VO_OFF = 0.2, 0.1
GAME_MAX = 13.8  # last clean gameplay second before the death sequence

# ---------------------------------------------------------------- source
probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height", "-of", "csv=p=0", SRC], capture_output=True, text=True)
sw, sh = map(int, probe.stdout.strip().split(","))
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"fps={FPS}", "-f", "rawvideo",
                      "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
frames = np.frombuffer(raw, np.uint8).reshape(-1, sh, sw, 3)
NSRC = len(frames)
src_audio = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-ac", "1", "-ar", str(SR),
                                          "-f", "f32le", "-"], capture_output=True).stdout, np.float32)

# ---------------------------------------------------------------- timeline
meta = json.load(open(f"{WORK}/vo/voice_meta.json"))
SHOTS = {  # per sentence: (src_start, speed, zoom_from, zoom_to, cx, cy)
    "hook": [(0.0, 1.5, 1.0, 1.1, .45, .5), (8.0, 1.0, 1.3, 1.45, .5, .6), (10.0, 0.6, 1.1, 1.25, .5, .6)],
    "s1": [(4.5, 0.6, 1.0, 1.08, .65, .45), (5.8, 0.5, 1.35, 1.45, .74, .42), (6.6, 0.5, 1.15, 1.25, .72, .45)],
    "s2": [(0.0, 0.7, 1.0, 1.1, .45, .5), (1.5, 0.6, 1.3, 1.4, .5, .55), (3.0, 0.6, 1.1, 1.2, .55, .5)],
    "s3": [(9.0, 0.5, 1.3, 1.0, .5, .5), (10.5, 0.5, 1.0, 1.1, .4, .45), (12.0, 0.5, 1.2, 1.3, .6, .5)],
    "s4": [(2.0, 1.0, 1.0, 1.1, .5, .5), (4.0, 0.8, 1.25, 1.35, .55, .5), (6.0, 0.8, 1.05, 1.15, .5, .5)],
    "s5": [(6.0, 0.8, 1.0, 1.1, .5, .5), (8.0, 0.7, 1.3, 1.4, .45, .6), (10.0, 0.7, 1.1, 1.2, .5, .55)],
    "s6": [(1.0, 0.5, 1.2, 1.35, .55, .6), (2.0, 0.4, 1.5, 1.6, .55, .62), (3.0, 0.6, 1.1, 1.2, .5, .5)],
    "s7": [(11.0, 0.5, 1.0, 1.1, .5, .55), (3.0, 0.9, 1.25, 1.35, .5, .5), (9.0, 0.6, 1.1, 1.2, .5, .55),
           (12.0, 0.4, 1.3, 1.4, .5, .6)],
}
STICKERS = {"s1": "1ª PROTAGONISTA MUJER", "s2": "JASON + LUCÍA", "s3": "VICE CITY · CAYOS · PANTANOS",
            "s5": "2022 · +90 VÍDEOS", "s6": "BASADO EN HECHOS REALES"}
COUNTERS = {"s4": (90_000_000, "VISITAS EN 24 HORAS", 1, 0.0),
            "s7": (200_000_000, "COPIAS DE GTA 5 VENDIDAS", 0, 1.6)}  # value, label, sentence, delay
CLIP_SRC = (7.0, 17.0)  # real-time gameplay with original audio
CTA_SRC = 17.0

segs, t = [], 0.0
for m in meta:
    if m["id"] == "clip":
        dur = CLIP_SRC[1] - CLIP_SRC[0]
    elif m["id"] == "cta":
        dur = m["dur"] + 1.0
    else:
        dur = m["dur"] + PAD
    sents = [{"start": t + VO_OFF + s["start"], "end": t + VO_OFF + s["end"], "text": s["text"]}
             for s in m["sentences"]]
    segs.append({**m, "t0": t, "t1": t + dur, "sents": sents})
    t += dur
TOTAL = t
FACTS = [s for s in segs if s["num"]]
print(f"total {TOTAL:.2f}s, {NSRC} source frames", flush=True)

# word timings for karaoke subtitles
chunks = []  # (start, end, [words], [(wstart, wend)])
for s in segs:
    for se in s["sents"]:
        words = se["text"].split()
        wts = np.array([len(w.strip(".,¿?¡!")) + 2.5 for w in words], float)
        edges = se["start"] + np.concatenate([[0], np.cumsum(wts)]) / wts.sum() * (se["end"] - se["start"])
        for i in range(0, len(words), 3):
            j = min(len(words), i + 3)
            if len(words) - j == 1:  # avoid a lonely last word
                j += 1
            if i >= len(words):
                break
            chunks.append((edges[i], edges[j], words[i:j], [(edges[k], edges[k + 1]) for k in range(i, j)]))
            if j == len(words):
                break
# dedupe accidental overlaps from the lonely-word rule
clean = []
for c in chunks:
    if clean and c[0] < clean[-1][1] - 1e-6:
        continue
    clean.append(c)
chunks = clean

# ---------------------------------------------------------------- drawing helpers
_font_cache, _txt_cache = {}, {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def text_img(text, size, fill=WHITE, path=FONT_BLACK, stroke=8, stroke_fill=(0, 0, 0), max_w=None, shadow=True):
    key = (text, size, fill, path, stroke, stroke_fill, max_w, shadow)
    if key in _txt_cache:
        return _txt_cache[key]
    f = font(path, size)
    while max_w and f.getbbox(text, stroke_width=stroke)[2] > max_w and size > 30:
        size -= 4
        f = font(path, size)
    l, tp, r, b = f.getbbox(text, stroke_width=stroke)
    pad = 20
    im = Image.new("RGBA", (r - l + pad * 2, b - tp + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if shadow:
        sh_im = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh_im).text((pad - l + 6, pad - tp + 8), text, font=f, fill=(0, 0, 0, 170),
                                   stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        im = Image.alpha_composite(im, sh_im.filter(ImageFilter.GaussianBlur(6)))
        d = ImageDraw.Draw(im)
    d.text((pad - l, pad - tp), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    _txt_cache[key] = im
    return im


def pill(text, size, bg, fg=WHITE, path=FONT_BLACK):
    key = ("pill", text, size, bg, fg)
    if key in _txt_cache:
        return _txt_cache[key]
    f = font(path, size)
    l, tp, r, b = f.getbbox(text)
    px, py = int(size * 0.55), int(size * 0.35)
    im = Image.new("RGBA", (r - l + px * 2, b - tp + py * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=im.height // 2, fill=bg)
    d.text((px - l, py - tp), text, font=f, fill=fg)
    _txt_cache[key] = im
    return im


def paste_center(canvas, im, cx, cy, scale=1.0, alpha=1.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy()
        im.putalpha(a)
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def ease_out_back(x):
    x = min(max(x, 0), 1)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_out(x):
    x = min(max(x, 0), 1)
    return 1 - (1 - x) ** 3


# static layers
yy = np.linspace(0, 1, H)[:, None, None]
TINT = (np.array([40, 10, 70]) * (1 - yy) + np.array([90, 20, 60]) * yy).astype(np.float32)  # purple->magenta
VIG = (1 - 0.55 * np.clip(np.abs(np.linspace(-1, 1, H))[:, None] ** 2, 0, 1))[..., None].astype(np.float32)

mask = Image.new("L", (PW, PH), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, PW - 1, PH - 1), radius=36, fill=255)
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.rounded_rectangle((PX - 6, PY - 6, PX + PW + 5, PY + PH + 5), radius=42, outline=PINK + (255,), width=10)
glow = glow.filter(ImageFilter.GaussianBlur(14))
gd = ImageDraw.Draw(glow)
gd.rounded_rectangle((PX - 3, PY - 3, PX + PW + 2, PY + PH + 2), radius=39, outline=PINK + (255,), width=5)
# dark gradient at the bottom of the panel for subtitles/credit readability
shade = np.zeros((PH, PW, 4), np.uint8)
g = np.clip((np.arange(PH) - PH * 0.55) / (PH * 0.45), 0, 1) ** 1.3
shade[..., 3] = (g[:, None] * 190).astype(np.uint8)
SHADE = Image.fromarray(shade, "RGBA")
CREDIT_IM = pill(CREDIT, 26, (0, 0, 0, 150), (235, 235, 235), FONT_BOLD)

_bg_cache = {}


def background(idx):
    if idx in _bg_cache:
        return _bg_cache[idx]
    f = frames[idx]
    cw = int(sh * W / H)
    x0 = (sw - cw) // 2
    small = Image.fromarray(f[:, x0:x0 + cw]).resize((27, 48), Image.BILINEAR)
    big = np.asarray(small.resize((W, H), Image.BICUBIC), np.float32)
    out = (big * 0.42 + TINT * 0.58) * VIG
    _bg_cache[idx] = np.clip(out, 0, 255).astype(np.uint8)
    if len(_bg_cache) > 400:
        _bg_cache.pop(next(iter(_bg_cache)))
    return _bg_cache[idx]


def panel(src_t, zoom, cx, cy, effect, t):
    idx = min(NSRC - 1, max(0, int(round(src_t * FPS))))
    f = frames[idx]
    ch = sh / zoom
    cw = ch * PW / PH
    if cw > sw:
        cw = sw
        ch = cw * PH / PW
    x0 = min(max(cx * sw - cw / 2, 0), sw - cw)
    y0 = min(max(cy * sh - ch / 2, 0), sh - ch)
    im = Image.fromarray(f).resize((PW, PH), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    a = np.asarray(im, np.float32)
    # punchy grade: contrast + saturation
    m = a.mean(axis=2, keepdims=True)
    a = (a - m) * 1.25 + m
    a = (a - 128) * 1.08 + 128
    if effect == "warm":
        a *= np.array([1.07, 1.0, 0.9], np.float32)
    if effect == "glitch":
        r = np.random.default_rng(int(t * FPS))
        s = int(r.integers(6, 18))
        a[..., 0] = np.roll(a[..., 0], s, axis=1)
        a[..., 2] = np.roll(a[..., 2], -s, axis=1)
        if r.random() < 0.45:
            for _ in range(int(r.integers(2, 6))):
                y = int(r.integers(0, PH - 40))
                hgt = int(r.integers(8, 60))
                a[y:y + hgt] = np.roll(a[y:y + hgt], int(r.integers(-80, 80)), axis=1)
        a[::4] *= 0.75
        a *= np.array([0.9, 1.05, 0.95], np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), idx


def seg_at(t):
    for s in segs:
        if s["t0"] <= t < s["t1"]:
            return s
    return segs[-1]


def reflect(x, lo, hi):
    span = hi - lo
    y = (x - lo) % (2 * span)
    return lo + (y if y <= span else 2 * span - y)


# ---------------------------------------------------------------- frame renderer
def render(t):
    s = seg_at(t)
    lt = t - s["t0"]
    sid = s["id"]
    effect = {"s1": "warm", "s5": "glitch"}.get(sid, "")

    if sid == "clip":
        src_t, zoom, cx, cy = CLIP_SRC[0] + lt, 1.0, .5, .5
    elif sid == "cta":
        src_t, zoom, cx, cy = min(CTA_SRC + lt, (NSRC - 1) / FPS), 1.0 + 0.05 * lt, .5, .5
    else:
        k = 0
        for i, se in enumerate(s["sents"]):
            if t >= se["start"] - 0.05:
                k = i
        shots = SHOTS[sid]
        st0, spd, z0, z1, cx, cy = shots[k % len(shots)]
        shot_start = s["t0"] if k == 0 else s["sents"][k]["start"] - 0.05
        shot_end = s["t1"] if k == len(s["sents"]) - 1 else s["sents"][k + 1]["start"] - 0.05
        p = (t - shot_start) / max(0.1, shot_end - shot_start)
        zoom = z0 + (z1 - z0) * p
        src_t = reflect(st0 + (t - shot_start) * spd, 0.0, GAME_MAX)
        # micro punch-in on every cut inside the segment
        if k > 0:
            zoom *= 1 + 0.06 * max(0, 1 - (t - shot_start) / 0.18)

    # transition punch at segment start
    if s is not segs[0]:
        zoom *= 1 + 0.12 * max(0, 1 - lt / 0.22)

    pim, idx = panel(src_t, max(1.0, zoom), cx, cy, effect, t)
    canvas = Image.fromarray(background(idx)).convert("RGBA")
    canvas.alpha_composite(glow)
    pim = pim.convert("RGBA")
    pim.alpha_composite(SHADE)
    canvas.paste(pim, (PX, PY), mask)
    canvas.alpha_composite(CREDIT_IM, (PX + 22, PY + PH - CREDIT_IM.height - 20))

    # ---------- top: titles
    if sid == "hook":
        pop = ease_out_back(lt / 0.35)
        paste_center(canvas, text_img("7 SECRETOS", 150, YELLOW, stroke=10, max_w=1000), W / 2, 230,
                     scale=max(0.05, pop))
        pop2 = ease_out_back((lt - 0.25) / 0.35)
        if lt > 0.25:
            paste_center(canvas, text_img("DE GTA 6", 130, WHITE, stroke=10, max_w=1000), W / 2, 385,
                         scale=max(0.05, pop2))
    elif s["num"]:
        n = s["num"]
        sl = ease_out(lt / 0.3)
        paste_center(canvas, pill(f"SECRETO #{n}", 44, PINK), W / 2 - (1 - sl) * 700, 170)
        pop = ease_out_back((lt - 0.08) / 0.35)
        if lt > 0.08:
            paste_center(canvas, text_img(s["title"], 120, WHITE, stroke=9, max_w=1000), W / 2, 305,
                         scale=max(0.05, pop))
        # progress dots
        for i in range(7):
            x = W / 2 + (i - 3) * 46
            d = ImageDraw.Draw(canvas)
            if i + 1 < n:
                d.ellipse((x - 9, 427, x + 9, 445), fill=CYAN)
            elif i + 1 == n:
                d.ellipse((x - 14, 422, x + 14, 450), fill=YELLOW, outline=WHITE, width=3)
            else:
                d.ellipse((x - 9, 427, x + 9, 445), outline=(255, 255, 255, 160), width=3)
    elif sid == "clip":
        paste_center(canvas, pill("BONUS", 44, CYAN, (10, 10, 30)), W / 2, 170)
        paste_center(canvas, text_img("OJO EN LA PLAYA", 110, YELLOW, stroke=9, max_w=1000), W / 2, 305,
                     scale=max(0.05, ease_out_back(lt / 0.35)))
    elif sid == "cta":
        b = 1 + 0.04 * math.sin(lt * 7)
        paste_center(canvas, text_img("SÍGUEME", 150, PINK, stroke=10, stroke_fill=WHITE), W / 2, 230,
                     scale=ease_out_back(lt / 0.35) * b)
        if lt > 0.2:
            paste_center(canvas, text_img("PARA MÁS SECRETOS", 80, WHITE, stroke=8, max_w=1000), W / 2, 380,
                         scale=max(0.05, ease_out_back((lt - 0.2) / 0.35)))

    # ---------- stickers / counters inside panel
    if sid in STICKERS and lt > 0.4:
        a = min(1, (lt - 0.4) / 0.2)
        sp = pill(STICKERS[sid], 34, YELLOW, (15, 10, 30))
        canvas.alpha_composite(sp, (int(PX + 24 - (1 - ease_out(a)) * 300), PY + 24))
        if sid == "s5" and int(t * 4) % 2 == 0:
            canvas.alpha_composite(pill("● LEAK", 34, (230, 30, 40)), (PX + PW - 200, PY + 24))
    if sid in COUNTERS:
        val, label, sidx, delay = COUNTERS[sid]
        c0 = s["sents"][min(sidx, len(s["sents"]) - 1)]["start"] + delay
        if t >= c0:
            p = ease_out((t - c0) / 1.3)
            v = int(val * p)
            txt = f"{v:,}".replace(",", ".") + ("+" if p >= 1 else "")
            sc = 1 + 0.15 * max(0, 1 - (t - c0 - 1.3) / 0.25) if t - c0 > 1.3 else 1.0
            paste_center(canvas, text_img(txt, 120, YELLOW, stroke=10), W / 2, PY + PH * 0.42, scale=sc)
            paste_center(canvas, pill(label, 36, PINK), W / 2, PY + PH * 0.42 + 105)

    # ---------- subtitles (karaoke)
    for c in chunks:
        if c[0] <= t < c[1] + 0.08:
            active = 0
            for i, (ws, we) in enumerate(c[3]):
                if t >= ws:
                    active = i
            words = c[2]
            key_imgs = [text_img(w.upper(), 92, YELLOW if i == active else WHITE, FONT_BLACK, 9)
                        for i, w in enumerate(words)]
            gap = -22
            tw = sum(im.width for im in key_imgs) + gap * (len(key_imgs) - 1)
            sc = min(1.0, 1000 / tw) * (1 + 0.08 * max(0, 1 - (t - c[0]) / 0.12))
            x = W / 2 - tw * sc / 2
            for im in key_imgs:
                paste_center(canvas, im, x + im.width * sc / 2, PY + PH + 135, scale=sc)
                x += (im.width + gap) * sc
            break

    # ---------- flash at segment start
    arr = np.asarray(canvas.convert("RGB"), np.float32)
    if s is not segs[0] and lt < 0.15:
        a = 0.75 * (1 - lt / 0.15)
        arr = arr * (1 - a) + 255 * a
    # top progress bar
    arr[0:10, : int(W * t / TOTAL)] = PINK
    return np.clip(arr, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- audio mix
def build_audio():
    n = int(TOTAL * SR) + SR
    vo = np.zeros(n, np.float32)
    vo_env = np.zeros(n, np.float32)
    for s in segs:
        a, sr = sf.read(f"{WORK}/vo/{s['id']}.wav", dtype="float32")
        a = resample_poly(a, SR, sr).astype(np.float32)
        a = a / (np.abs(a).max() + 1e-9) * 0.92
        st = int((s["t0"] + VO_OFF) * SR)
        vo[st:st + len(a)] += a[: n - st]
        vo_env[st:st + len(a)] = 1
    music, _ = sf.read(f"{WORK}/sfx/music.wav", dtype="float32")
    music = np.pad(music, (0, max(0, n - len(music))))[:n]
    # smooth ducking envelope
    k = int(0.25 * SR)
    duck = np.convolve(vo_env, np.ones(k) / k, mode="same")
    mgain = 0.30 - 0.16 * duck
    game = np.zeros(n, np.float32)
    clip = next(s for s in segs if s["id"] == "clip")
    cta = next(s for s in segs if s["id"] == "cta")
    a0 = int(CLIP_SRC[0] * SR)
    a1 = min(len(src_audio), int((CTA_SRC + (cta["t1"] - cta["t0"])) * SR))
    piece = src_audio[a0:a1]
    st = int(clip["t0"] * SR)
    piece = piece[: n - st]
    game[st:st + len(piece)] = piece * 0.9
    # music dips under the real gameplay audio of the bonus clip
    ts = np.arange(n) / SR
    in_clip = (ts >= clip["t0"]) & (ts < clip["t1"])
    mgain[in_clip] *= 0.45
    mix = vo + music * mgain + game
    wh, _ = sf.read(f"{WORK}/sfx/whoosh.wav", dtype="float32")
    bm, _ = sf.read(f"{WORK}/sfx/boom.wav", dtype="float32")

    def add(x, at, g):
        i = max(0, int(at * SR))
        mix[i:i + len(x)] += x[: n - i] * g

    add(bm, 0.0, 0.7)
    for s in segs[1:]:
        add(wh, s["t0"] - 0.22, 0.55)
    for sid, (val, label, sidx, delay) in COUNTERS.items():
        s = next(x for x in segs if x["id"] == sid)
        add(bm, s["sents"][min(sidx, len(s["sents"]) - 1)]["start"] + delay + 1.3, 0.5)
    mix = mix[: int(TOTAL * SR)]
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)  # soft limiter
    sf.write(f"{WORK}/mix.wav", mix, SR)


build_audio()
print("audio ok", flush=True)

if PREVIEW:
    for i, tt in enumerate([0.6, 3.5] + [s["t0"] + 2.5 for s in segs[1:]]):
        Image.fromarray(render(min(tt, TOTAL - 0.05))).save(f"{WORK}/preview_{i:02d}.png")
    sys.exit(0)

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                        "-r", str(FPS), "-i", "-", "-i", f"{WORK}/mix.wav", "-c:v", "libx264", "-preset", "medium",
                        "-crf", "19", "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", "-shortest", OUT],
                       stdin=subprocess.PIPE)
nf = int(TOTAL * FPS)
for i in range(nf):
    enc.stdin.write(render(i / FPS).tobytes())
    if i % 300 == 0:
        print(f"frame {i}/{nf}", flush=True)
enc.stdin.close()
enc.wait()
print("done", OUT)

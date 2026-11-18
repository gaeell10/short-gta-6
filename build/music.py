"""Synthwave/Vice-City-style backing track + SFX, 100% generated in code (no copyrighted audio)."""
import sys
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

SR = 44100
rng = np.random.default_rng(7)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def saw(freq, n, detune=0.0):
    t = np.arange(n) / SR
    ph = (t * freq * (1 + detune)) % 1.0
    return 2 * ph - 1


def env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)
    return e


def music(total):
    bpm = 100
    beat = 60 / bpm
    n = int(total * SR)
    out = np.zeros(n + SR * 2)
    drums = np.zeros_like(out)
    # chords: Am F C G   (root, third, fifth) in Hz
    prog = [
        (110.00, [220.0, 261.63, 329.63]),
        (87.31, [174.61, 220.0, 261.63]),
        (130.81, [261.63, 329.63, 392.0]),
        (98.00, [196.0, 246.94, 293.66]),
    ]
    bar = beat * 4
    nbars = int(total / bar) + 2
    kick_n = int(0.35 * SR)
    tk = np.arange(kick_n) / SR
    kick = np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-tk * 30)) / SR) * np.exp(-tk * 9)
    sn_n = int(0.3 * SR)
    snare = bp(rng.standard_normal(sn_n), 1200, 7000) * env(sn_n, 0.001, 0.09) * 0.7
    snare += np.sin(2 * np.pi * 190 * np.arange(sn_n) / SR) * env(sn_n, 0.001, 0.05) * 0.5
    hh_n = int(0.06 * SR)
    hat = hp(rng.standard_normal(hh_n), 7000) * env(hh_n, 0.0005, 0.015) * 0.25

    pad = np.zeros_like(out)
    bass = np.zeros_like(out)
    arp = np.zeros_like(out)
    for b in range(nbars):
        root, chord = prog[b % 4]
        s0 = int(b * bar * SR)
        bn = int(bar * SR)
        if s0 >= len(out):
            break
        seg = slice(s0, min(len(out), s0 + bn))
        L = seg.stop - seg.start
        # pad: detuned saws, slow attack
        p = sum(saw(f, L, d) for f in chord for d in (-0.004, 0.004))
        pe = np.minimum(1, np.arange(L) / (0.4 * SR)) * np.minimum(1, (L - np.arange(L)) / (0.1 * SR))
        pad[seg] += p * pe
        # bass: 8th-note pulses
        for i in range(8):
            st = s0 + int(i * beat / 2 * SR)
            ln = int(beat / 2 * SR * 0.9)
            if st + ln > len(out):
                break
            f = root if i % 4 != 3 else root * 2
            bass[st:st + ln] += saw(f, ln) * env(ln, 0.003, 0.18)
        # arp: 16ths over chord tones, up an octave
        tones = [chord[0] * 2, chord[1] * 2, chord[2] * 2, chord[1] * 2]
        for i in range(16):
            st = s0 + int(i * beat / 4 * SR)
            ln = int(beat / 4 * SR * 0.8)
            if st + ln > len(out):
                break
            f = tones[i % 4]
            t = np.arange(ln) / SR
            sq = np.sign(np.sin(2 * np.pi * f * t))
            arp[st:st + ln] += sq * env(ln, 0.002, 0.06)
        # drums (start after first bar for an intro feel)
        for i in range(4):
            st = s0 + int(i * beat * SR)
            if st + kick_n < len(out):
                drums[st:st + kick_n] += kick * 0.9
            if i in (1, 3) and st + sn_n < len(out):
                drums[st:st + sn_n] += snare
            for h in range(2):
                hs = st + int(h * beat / 2 * SR)
                if hs + hh_n < len(out):
                    drums[hs:hs + hh_n] += hat * (1.0 if h else 0.6)
    pad = lp(pad, 1800) * 0.08
    bass = lp(bass, 400, 4) * 0.35
    arp = lp(arp, 3000) * 0.05
    # simple echo on arp + snare-ish space
    d = int(beat * 0.75 * SR)
    arp[d:] += arp[:-d] * 0.4
    mix = pad + bass + arp + drums * 0.55
    mix = mix[:n]
    # fade in/out
    fi = int(0.5 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)
    fo = int(2.0 * SR)
    mix[-fo:] *= np.linspace(1, 0, fo)
    return mix / (np.abs(mix).max() + 1e-9) * 0.9


def whoosh(dur=0.45):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    # sweep bandpass by chunks
    chunks = 24
    for c in range(chunks):
        a, b = c * n // chunks, (c + 1) * n // chunks
        fc = 400 + 5000 * (c / chunks) ** 1.5
        out[a:b] = bp(noise[a:b], fc * 0.6, min(fc * 1.6, 18000))
    t = np.linspace(0, 1, n)
    e = np.sin(np.pi * t) ** 2
    return out * e / (np.abs(out * e).max() + 1e-9) * 0.5


def boom(dur=1.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t * 12)) / SR) * np.exp(-t * 3.5)
    s += lp(rng.standard_normal(n), 900) * np.exp(-t * 14) * 0.6
    return s / np.abs(s).max() * 0.8


if __name__ == "__main__":
    outdir = sys.argv[1]
    total = float(sys.argv[2])
    sf.write(f"{outdir}/music.wav", music(total), SR)
    sf.write(f"{outdir}/whoosh.wav", whoosh(), SR)
    sf.write(f"{outdir}/boom.wav", boom(), SR)
    print("ok")

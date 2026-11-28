"""usage: render_scene.py <meta.json> <outdir> <worker> <nworkers> [scene ids,comma] [preview]"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import toon as T, scenes as S, timeline as TL

meta, out, wk, nw = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
only = sys.argv[5].split(",") if len(sys.argv) > 5 and sys.argv[5] != "all" else None
preview = len(sys.argv) > 6 and sys.argv[6] == "preview"
segs = TL.load(meta)
for s in segs:
    if only and s["id"] not in only:
        continue
    sid = s["id"]
    os.makedirs(f"{out}/{sid}", exist_ok=True)
    if preview:  # one frame in the middle of every cut
        cuts = [c[0] + TL.VO_OFF if c[0] else 0 for c in TL.CUTS[sid]] + [s["t1"] - s["t0"]]
        frames = [round((cuts[i] + min(1.2, (cuts[i + 1] - cuts[i]) / 2)) * TL.FPS) for i in range(len(cuts) - 1)]
    else:
        frames = [f for f in range(s["f1"] - s["f0"]) if (s["f0"] + f) % nw == wk]
    frames = [f for f in frames if not os.path.exists(f"{out}/{sid}/{f:05d}.png")]
    if not frames:
        continue
    sc = T.reset(res=(270, 480) if preview else (540, 960), samples=4 if preview else 8)
    sc.render.use_persistent_data = True
    sc.cycles.adaptive_threshold = 0.05
    if nw > 1:
        sc.render.threads_mode = "FIXED"
        sc.render.threads = max(1, (os.cpu_count() or 4) // nw)
    upd, track, n = S.BUILD[sid]()
    cam = T.camera((0, -10, 2), (0, 0, 1))
    for f in frames:
        t = f / TL.FPS
        k, tt = TL.shot_at(sid, t)
        loc, tgt, lens = track(k, tt, t)
        cam.location = loc
        T.look(cam, tgt)
        cam.data.lens = lens
        upd(t, k, tt)
        t0 = time.time()
        T.render_to(f"{out}/{sid}/{f:05d}.png")
        print(f"[{wk}] {sid} {f} {time.time()-t0:.1f}s", flush=True)

import json, re, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
k = Kokoro("/tmp/claude-0/voices/kokoro.onnx","/tmp/claude-0/voices/voices.bin")
out = sys.argv[1]; voice = sys.argv[2] if len(sys.argv)>2 else "em_alex"
segs = json.load(open(sys.argv[3]))
meta=[]
for s in segs:
    # split into sentences, synthesize each, keep timings
    sents=[x.strip() for x in re.split(r'(?<=[.?!])\s+', s["text"]) if x.strip()]
    parts=[]; st=[]; t=0; sr=24000
    for x in sents:
        say=x.replace("GTA","ge te a").replace("YouTube","Yutub").replace("Rockstar","Rocstar")
        a,sr=k.create(say,voice=voice,speed=1.12,lang="es")
        # trim silence
        idx=np.where(np.abs(a)>0.01)[0]
        a=a[max(0,idx[0]-600):idx[-1]+1200] if len(idx) else a
        st.append({"text":x,"start":t,"end":t+len(a)/sr})
        parts.append(a); gap=np.zeros(int(sr*0.18),dtype=np.float32); parts.append(gap)
        t+=len(a)/sr+0.18
    audio=np.concatenate(parts)
    sf.write(f"{out}/{s['id']}.wav",audio,sr)
    meta.append({**s,"dur":len(audio)/sr,"sentences":st})
    print(s["id"],round(len(audio)/sr,2))
json.dump(meta,open(f"{out}/voice_meta.json","w"),ensure_ascii=False,indent=1)
print("total",round(sum(m["dur"] for m in meta),2))

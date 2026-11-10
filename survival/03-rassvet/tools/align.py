"""Приблизительная пословная разметка озвучки без ASR.

Паузы в речи (silencedetect) сопоставляются с границами фраз (знаки препинания)
динамическим программированием, внутри фразы время делится по длине слов.
Выход: audio/words.json — [{"w": слово, "t": начало, "e": конец}].
"""
import json, re, subprocess, sys

wav, txt, out = sys.argv[1:4]
words = open(txt, encoding="utf-8").read().split()
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav]))
log = subprocess.run(["ffmpeg", "-i", wav, "-af", "silencedetect=n=-30dB:d=0.12", "-f", "null", "-"], capture_output=True, text=True).stderr
ts = [float(x) for x in re.findall(r"silence_(?:start|end): ([0-9.]+)", log)]
sil = list(zip(ts[::2], ts[1::2]))
# речь начинается после первой тишины в начале и кончается перед последней
start = sil[0][1] if sil and sil[0][0] < 0.05 else 0.0
end = sil[-1][0] if sil and len(ts) % 2 == 0 and sil[-1][1] > dur - 0.05 else dur
if len(ts) % 2: end = ts[-1]
sil = [s for s in sil if s[0] > start + 0.01 and s[1] < end - 0.01]

wt = [len(re.sub(r"[^\wё]", "", w)) + 1.5 for w in words]
cum = [0.0]
for x in wt: cum.append(cum[-1] + x)
# допустимые границы: после слова с пунктуацией (индекс = число слов до границы)
B = [i + 1 for i, w in enumerate(words[:-1]) if re.search(r"[.,!?:;—»]$", w) or words[i + 1] in "—"]
rate = (end - start - sum(b - a for a, b in sil)) / cum[-1]

S = len(sil)
INF = float("inf")
SKIP = 0.6
# узлы: (-1, 0) начало; (s, j) — тишина s на границе B[j]
dp = {(-1, -1): (0.0, None)}
def bpos(j): return 0 if j < 0 else B[j]
def tend(s): return start if s < 0 else sil[s][1]
for s in range(S):
    for j in range(len(B)):
        best = (INF, None)
        for sp in range(max(-1, s - 4), s):
            for (ps, pj), (c, _) in list(dp.items()):
                if ps != sp or pj >= j: continue
                span = sil[s][0] - tend(sp) - sum(b - a for a, b in sil[sp + 1:s])
                exp = (cum[B[j]] - cum[bpos(pj)]) * rate
                cc = c + (span - exp) ** 2 + SKIP * (s - sp - 1)
                if cc < best[0]: best = (cc, (ps, pj))
        if best[0] < INF: dp[(s, j)] = best
# финал: последний сегмент до end
best = (INF, None)
for (ps, pj), (c, _) in dp.items():
    span = end - tend(ps) - sum(b - a for a, b in sil[ps + 1:])
    exp = (cum[-1] - cum[bpos(pj)]) * rate
    cc = c + (span - exp) ** 2 + SKIP * (S - ps - 1)
    if cc < best[0]: best = (cc, (ps, pj))
chain, node = [], best[1]
while node != (-1, -1):
    chain.append(node); node = dp[node][1]
chain.reverse()

res = []
bounds = [(-1, -1)] + chain + [(S, len(B))]
for (s0, j0), (s1, j1) in zip(bounds, bounds[1:]):
    w0 = bpos(j0); w1 = len(words) if s1 == S else B[j1]
    t0 = tend(s0); t1 = end if s1 == S else sil[s1][0]
    inner = [x for x in sil[s0 + 1:s1]]
    speech = t1 - t0 - sum(b - a for a, b in inner)
    # время речи -> реальное время с учётом пропущенных пауз
    def real(x):
        t = t0 + x
        for a, b in inner:
            if t >= a: t += b - a
        return t
    tot = cum[w1] - cum[w0]
    for k in range(w0, w1):
        res.append({"w": words[k], "t": round(real((cum[k] - cum[w0]) / tot * speech), 3),
                    "e": round(real((cum[k + 1] - cum[w0]) / tot * speech), 3)})
json.dump({"duration": dur, "words": res}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(f"{len(res)} слов, пауз {S}, привязано {len(chain)}, речь {start:.2f}–{end:.2f}")

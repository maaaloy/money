"""Озвучка Vosk TTS (Apache 2.0) по абзацам/предложениям с таймкодами слов.

python voice_vosk.py text.txt out.wav words.json [speaker=4] [rate=0.95]
Модель: https://alphacephei.com/vosk/models/vosk-model-tts-ru-0.9-multi.zip -> /home/user/models/
Дикторы: 3 = male_0, 4 = male_1 (выбран пользователем). Ударение можно задать знаком + перед гласной: зам+ок.
"""
import json, re, sys, wave
import numpy as np
from vosk_tts import Model, Synth

txt, out, out_words = sys.argv[1:4]
SP = int(sys.argv[4]) if len(sys.argv) > 4 else 4
RATE = float(sys.argv[5]) if len(sys.argv) > 5 else 0.95
SR = 22050
s = Synth(Model(model_path="/home/user/models/vosk-model-tts-ru-0.9-multi"))
rng = np.random.default_rng(7)


def trim(a, thr=0.01):
    idx = np.where(np.abs(a) > thr)[0]
    if not len(idx):
        return a
    a = a[max(0, idx[0] - int(0.02 * SR)): idx[-1] + int(0.08 * SR)].copy()
    fo = int(0.05 * SR)
    a[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
    return a


def breath(d=0.3, amp=0.012):
    n = int(d * SR)
    f = np.fft.rfft(rng.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    f[(fr < 350) | (fr > 2600)] = 0
    b = np.fft.irfft(f, n)
    return (b / np.abs(b).max() * amp * np.sin(np.linspace(0, np.pi, n)) ** 2).astype(np.float32)


def sil(d):
    return np.zeros(int(d * SR), dtype=np.float32)


paras = [p.strip() for p in open(txt, encoding="utf-8").read().split("\n\n") if p.strip()]
chunks, words, t = [], [], 0.0
for pi, par in enumerate(paras):
    if pi:
        gap = 0.7
        chunks += [sil(gap - 0.38), breath(), sil(0.08)]
        t += gap
    sents = [x for x in re.split(r"(?<=[.!?…»])\s+(?=[«А-ЯЁA-Z])", par) if x.strip()]
    for si, sen in enumerate(sents):
        toks = sen.split()
        n = len(toks)
        rate = RATE * (0.9 if n <= 3 else 1.0)  # короткие драматичные фразы медленнее
        clean = re.sub(r'[«»"“”]', '', sen).replace('—', ',').replace('…', '.')
        a = trim(s.synth_audio(clean, speaker_id=SP, speech_rate=rate).astype(np.float32) / 32768)
        dur = len(a) / SR
        w8 = [len(re.sub(r"[^\wё]", "", w.replace("+", ""))) + 1.5 for w in toks]
        c = 0.0
        for w, k in zip(toks, w8):
            words.append({"w": w.replace("+", ""), "t": round(t + 0.03 + c / sum(w8) * (dur - 0.1), 3),
                          "e": round(t + 0.03 + (c + k) / sum(w8) * (dur - 0.1), 3)})
            c += k
        chunks.append(a); t += dur
        if si < len(sents) - 1:
            p = 0.45 if len(sents[si + 1].split()) <= 3 else 0.3
            chunks.append(sil(p)); t += p
chunks.append(sil(0.5))
audio = np.concatenate(chunks)
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
json.dump({"duration": len(audio) / SR, "words": words}, open(out_words, "w", encoding="utf-8"), ensure_ascii=False)
print(f"{len(words)} слов, {len(audio) / SR:.1f} с")

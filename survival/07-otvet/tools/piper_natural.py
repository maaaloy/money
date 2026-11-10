"""«Человечная» офлайн-озвучка Piper (ru_RU-ruslan-medium) по предложениям.

- ударения правятся прямо в фонемах (FIX), espeak ошибается в формах слов;
- каждое предложение синтезируется отдельно: мягкий вход, затухающий конец, без обрезанных согласных;
- паузы как у живого чтеца: короткие между предложениями, длинные между абзацами, тихий вдох перед абзацем;
- короткие драматичные фразы читаются медленнее;
- таймкоды слов пишутся сразу (границы предложений точные) → audio/words.json.

python3 tools/piper_natural.py <model.onnx> voiceover.txt audio/voice.wav audio/words.json   (pip install piper-tts numpy)
"""
import json, os, re, subprocess, sys, tempfile, wave
from pathlib import Path
import numpy as np
from piper import PiperVoice, SynthesisConfig

# фонемы espeak → правильное ударение (ˈ перед ударной гласной)
FIX = {
    "krˈɑju": "krajˈu",            # на краю́
    "prʌvˈoda": "prʌvʌdˈɑ",        # провода́
    "uxˈodʲitʲi": "uxʌdʲˈitʲi",    # уходи́те (повелительное)
    "mˈɑʃyn": "maʃˈyn",            # маши́н
    "tʲipʲˈerɪ^": "tʲipʲˈerʲ",     # тепе́рь
    "sʌrˈok": "sˈorʌk",            # со́рок
    "ʃtotˈo": "ʃtˈotʌ",            # что́-то
    "dvʲˈerɪ^": "dvʲˈerʲ",         # дверь
    "dvʲˈerʲɪ": "dvʲirʲˈi",        # к двери́
    "ˈokna": "ʌknˈɑ",              # окна́ (мн. ч.)
    "tʲˈen.": "tʲˈenʲ.",           # тень
    "tʲˈen ": "tʲˈenʲ ",
}

model, txt, out_wav, out_words = sys.argv[1:5]
RAW = "--raw" in sys.argv  # без обработки — для подгонки тембра в match_voice.py
LS_MUL = float(os.environ.get("LS_MUL", 1))      # общий темп (0.93 — как у Brian в ч. 3)
NOISE_W = float(os.environ.get("NOISE_W", 0.9))  # живость ритма/интонации
v = PiperVoice.load(model)
SR = v.config.sample_rate
rng = np.random.default_rng(7)

def sentences(par):
    return [s for s in re.split(r"(?<=[.!?…»])\s+(?=[«А-ЯЁA-Z])", par) if s.strip()]

def trim(a, thr=0.012, lead=0.02, tail=0.07):
    idx = np.where(np.abs(a) > thr)[0]
    if not len(idx):
        return a
    a = a[max(0, idx[0] - int(lead * SR)): idx[-1] + int(tail * SR)].copy()
    fi, fo = int(0.015 * SR), int(0.06 * SR)
    a[:fi] *= np.sin(np.linspace(0, np.pi / 2, fi)) ** 2
    a[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
    return a

def breath(d=0.32, amp=0.02):
    n = int(d * SR)
    f = np.fft.rfft(rng.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    f[(fr < 350) | (fr > 2600)] = 0
    b = np.fft.irfft(f, n)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2 * np.linspace(0.6, 1, n)
    return b / np.abs(b).max() * amp * env

def silence(d):
    return np.zeros(int(d * SR), dtype=np.float32)

paras = [p.strip() for p in Path(txt).read_text(encoding="utf-8").split("\n\n") if p.strip()]
chunks, words, t = [], [], 0.0
for pi, par in enumerate(paras):
    if pi:
        gap = 1.0 if pi == len(paras) - 1 else 0.75
        chunks += [silence(gap - 0.4), breath(), silence(0.08)]
        t += gap
    sents = sentences(par)
    for si, s in enumerate(sents):
        toks = s.split()
        n = len([w for w in toks if re.search(r"\w", w)])
        ph = " ".join("".join(x) for x in v.phonemize(s))
        for a, b in FIX.items():
            ph = ph.replace(a, b)
        ls = (1.18 if n <= 3 else 1.1 if n <= 7 else 1.04) * LS_MUL
        cfg = SynthesisConfig(length_scale=ls, noise_scale=0.72, noise_w_scale=NOISE_W)
        a = trim(v.phoneme_ids_to_audio(v.phonemes_to_ids(list(ph)), cfg).astype(np.float32))
        # слова: время делится по длине слова внутри точных границ предложения
        dur = len(a) / SR
        w8 = [len(re.sub(r"[^\wё]", "", w)) + 1.5 for w in toks]
        c = 0.0
        for w, k in zip(toks, w8):
            words.append({"w": w, "t": round(t + 0.03 + c / sum(w8) * (dur - 0.1), 3), "e": round(t + 0.03 + (c + k) / sum(w8) * (dur - 0.1), 3)})
            c += k
        chunks.append(a)
        t += dur
        if si < len(sents) - 1:
            nxt = len(sents[si + 1].split())
            p = 0.5 if nxt <= 3 else 0.34
            chunks.append(silence(p))
            t += p
chunks.append(silence(0.6))
audio = np.concatenate(chunks)
raw = Path(tempfile.mkdtemp()) / "raw.wav"
with wave.open(str(raw), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
# тон чуть ниже (длительность сохраняется), «дикторская» эквализация, компрессия, лёгкий объём
af = (f"asetrate={SR}*0.97,aresample=48000,atempo={1/0.97:.4f},highpass=f=70,equalizer=f=160:t=q:w=1:g=3,"
      "equalizer=f=3200:t=q:w=1:g=1.5,acompressor=threshold=0.1:ratio=3:attack=10:release=200,aecho=0.8:0.4:35:0.07")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", "aresample=48000" if RAW else af, out_wav], check=True)
json.dump({"duration": len(audio) / SR, "words": words}, open(out_words, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(f"{len(words)} слов, {len(audio) / SR:.1f} с")

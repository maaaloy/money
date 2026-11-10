#!/usr/bin/env python3
"""Сборка Shorts из сценария: python3 video/make.py video/stories/tp-001-chat.json
Результат: video/out/<id>.mp4

Голос: Vosk TTS male_1 + обработка (см. voice()). Запасной — Piper ruslan (story.voice = "piper").
Нужно (один раз): см. video/SETUP.md
"""
import json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = os.environ.get("TTS_PY", "/home/user/tts/bin/python3")
MODEL = ROOT / "voices" / "ru_RU-ruslan-medium.onnx"
TEMPO = 1.07
EQ = ("firequalizer=gain_entry='entry(60,6);entry(100,8);entry(160,4.8);entry(250,-1.3);entry(400,-6);"
      "entry(630,-5);entry(1000,-1.3);entry(1600,-1.5);entry(2500,-1.7);entry(4000,0.7);entry(6300,2.3);entry(9000,1)'")


def run(*a, **k):
    subprocess.run([str(x) for x in a], check=True, **k)


# Обработка «как E»: чуть ниже, плотнее, присутствие, лёгкая комната. "clean" — без неё (вариант C).
POST = {
    "E": "aresample=48000,rubberband=pitch=0.94:formant=preserved,highpass=f=70,equalizer=f=120:t=q:w=1:g=3,"
         "equalizer=f=3500:t=q:w=1.2:g=2,deesser=i=0.4,acompressor=threshold=0.1:ratio=3:attack=8:release=180,"
         "aecho=0.8:0.5:40:0.06,alimiter=limit=0.9",
    "C": "aresample=48000,highpass=f=60,alimiter=limit=0.9",
}


def voice(story, out):
    """Голос по умолчанию: Vosk male_1 (speaker 4) + обработка E. story.voice = "piper" — старый Piper."""
    txt = out / "voiceover.txt"
    txt.write_text("\n\n".join(sc["text"] for sc in story["scenes"] if sc.get("text")) + "\n", encoding="utf-8")
    raw, words = out / "raw.wav", out / "words_raw.json"
    v = out / "voice.wav"
    if story.get("voice") == "piper":
        env = dict(os.environ, LS_MUL="0.93", NOISE_W="1.05")
        run(PY, "-I", ROOT / "voice_natural.py", MODEL, txt, raw, words, "--raw", env=env, capture_output=True)
        run("ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
            f"rubberband=pitch=0.87:tempo={TEMPO}:formant=preserved,{EQ},"
            "acompressor=threshold=0.12:ratio=2.5:attack=8:release=180,alimiter=limit=0.9", "-ar", "48000", v)
        k = TEMPO
    else:
        run(PY, "-I", ROOT / "voice_vosk.py", txt, raw, words, story.get("speaker", 4), story.get("rate", 0.95),
            capture_output=True)
        run("ffmpeg", "-v", "error", "-y", "-i", raw, "-af", POST[story.get("post", "E")], "-ar", "48000", v)
        k = 1.0
    d = json.loads(words.read_text(encoding="utf-8"))
    ws = [{"w": w["w"], "start": round(w["t"] / k, 3), "end": round(w["e"] / k, 3)} for w in d["words"]]
    return v, ws, d["duration"] / k


def split_scenes(story, ws, total):
    i = 0
    spoken = [sc for sc in story["scenes"] if sc.get("text")]
    for sc in spoken:
        n = len(sc["text"].split())
        sc["words"] = ws[i:i + n]
        i += n
    for k, sc in enumerate(spoken):
        sc["start"] = 0.0 if k == 0 else round(sc["words"][0]["start"] - 0.25, 3)
    for k, sc in enumerate(spoken):
        sc["end"] = spoken[k + 1]["start"] if k + 1 < len(spoken) else round(total + 0.6, 3)
    t = spoken[-1]["end"]
    for sc in story["scenes"]:  # немые сцены (заставка в конце)
        if not sc.get("text"):
            sc["words"], sc["start"], sc["end"] = [], t, round(t + sc.get("dur", 2.5), 3)
            t = sc["end"]
    story["duration"] = max(sc["end"] for sc in story["scenes"])
    # числа в субтитрах цифрами: story.num = [["сто двенадцать", "112"], ...]
    for phrase, digits in story.get("num", []):
        toks = phrase.lower().split()
        for sc in spoken:
            w, out, j = sc["words"], [], 0
            while j < len(w):
                seg = [re.sub(r"[^\wё]", "", x["w"].lower()) for x in w[j:j + len(toks)]]
                if seg == toks:
                    tail = re.sub(r"^[\wё-]+", "", w[j + len(toks) - 1]["w"])
                    out.append(dict(w[j], show=digits + tail.rstrip(",;:."), end=w[j + len(toks) - 1]["end"]))
                    j += len(toks)
                else:
                    out.append(w[j]); j += 1
            sc["words"] = out


def sfx_list(story):
    """Звуки: стук (knocks), вибрация телефона на каждое новое сообщение, удар на страшных сценах."""
    fx = []
    for sc in story["scenes"]:
        for k in sc.get("knocks", []):
            fx.append(("knock", sc["start"] + k))
        for m in sc.get("msgs", []):
            if "at" in m and m.get("at", 0) > 0:
                fx.append(("buzz", sc["start"] + m["at"]))
        if sc.get("scare"):
            fx.append(("hit", sc["start"] + 0.05))
        if story.get("impacts") and sc.get("text") and sc["start"] > 0:
            fx.append(("thud", sc["start"]))
        if sc.get("openDoor"):
            fx.append(("creak", sc["start"] + 0.2))
    return fx


SYNTH = {
    "knock": ("0.35", "(sin(2*PI*65*t)+0.6*sin(2*PI*130*t)+0.3*(random(0)-0.5)*exp(-60*t))*exp(-22*t)", 0.9),
    "buzz": ("0.55", "sin(2*PI*175*t)*gt(sin(2*PI*3.6*t),0)*0.6", 0.35),
    "hit": ("2.2", "(sin(2*PI*42*t)+0.5*sin(2*PI*84*t)+0.4*(random(0)-0.5))*exp(-2.2*t)", 0.8),
    "thud": ("0.9", "(sin(2*PI*55*t)+0.3*(random(0)-0.5)*exp(-30*t))*exp(-5*t)", 0.35),
    "creak": ("1.4", "sin(2*PI*(310+90*sin(2*PI*1.3*t))*t)*0.35*sin(PI*t/1.4)*(0.6+0.4*sin(2*PI*23*t))", 0.25),
}


def mix(story, v, out):
    dur = story["duration"]
    inputs = ["-i", v,
              # гул: два расстроенных низких тона + бурый шум, медленно «дышит»
              "-f", "lavfi", "-t", dur, "-i",
              "aevalsrc='0.22*sin(2*PI*55*t)+0.18*sin(2*PI*55.6*t)+0.10*sin(2*PI*82.4*t)':s=48000",
              "-f", "lavfi", "-t", dur, "-i", "anoisesrc=color=brown:amplitude=0.5:r=48000"]
    filt = ["[1]volume='0.35+0.15*sin(2*PI*t/9)':eval=frame,lowpass=f=200[d]",
            "[2]lowpass=f=260,volume=0.10[n]"]
    labels = ["[0]", "[d]", "[n]"]
    for j, (kind, at) in enumerate(sfx_list(story)):
        d, expr, vol = SYNTH[kind]
        inputs += ["-f", "lavfi", "-t", d, "-i", f"aevalsrc='{expr}':s=48000"]
        filt.append(f"[{j + 3}]volume={vol},adelay={int(at * 1000)}:all=1[f{j}]")
        labels.append(f"[f{j}]")
    filt.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,"
                f"atrim=0:{dur},loudnorm=I=-14:TP=-1.5,alimiter=limit=0.95[a]")
    m = out / "mix.wav"
    run("ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt), "-map", "[a]",
        "-ar", "48000", "-ac", "2", m)
    return m


def main(story_path):
    story = json.loads(Path(story_path).read_text(encoding="utf-8"))
    out = ROOT / "out" / story["id"]
    out.mkdir(parents=True, exist_ok=True)
    v, ws, total = voice(story, out)
    split_scenes(story, ws, total)
    audio = mix(story, v, out) if story.get("ambient") else v
    tl = out / "timeline.json"
    tl.write_text(json.dumps(story, ensure_ascii=False), encoding="utf-8")
    mp4 = ROOT / "out" / f"{story['id']}.mp4"
    tpl = ROOT / story.get("template", "template_podezd2.html")
    run("node", ROOT / "render.js", tl, audio, mp4, tpl)
    print(mp4)


if __name__ == "__main__":
    main(sys.argv[1])

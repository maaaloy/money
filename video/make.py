#!/usr/bin/env python3
"""Сборка Shorts из сценария: python3 video/make.py video/stories/001-ten.json
Результат: video/out/<id>.mp4
Нужны: pip install piper-tts, ffmpeg, node + playwright, голоса в video/voices/
"""
import json, subprocess, sys, wave, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GAP = 0.35  # пауза между сценами, сек


def tts(text, voice, out):
    subprocess.run([sys.executable, "-m", "piper", "-m", str(ROOT / "voices" / f"{voice}.onnx"),
                    "-f", str(out), "--length-scale", "0.92", "--sentence-silence", "0.15"],
                   input=text.encode(), check=True, capture_output=True)
    with wave.open(str(out)) as w:
        return w.getnframes() / w.getframerate()


def word_times(text, start, dur):
    words = text.split()
    weights = [len(re.sub(r"\W", "", w)) + 2 for w in words]
    total, t, res = sum(weights), start, []
    for w, k in zip(words, weights):
        res.append({"w": w, "start": round(t, 3)})
        t += dur * k / total
    return res


def main(story_path):
    story = json.loads(Path(story_path).read_text())
    out = ROOT / "out" / story["id"]
    out.mkdir(parents=True, exist_ok=True)
    t, parts = 0.0, []
    for i, sc in enumerate(story["scenes"]):
        wav = out / f"s{i:02d}.wav"
        d = tts(sc["text"], story.get("voice", "ru_RU-dmitri-medium"), wav)
        sc["start"], sc["end"] = round(t, 3), round(t + d + GAP, 3)
        sc["words"] = word_times(sc["text"], t + 0.05, d - 0.15)
        parts.append((wav, d))
        t += d + GAP
    story["duration"] = round(t + 0.4, 3)

    # склейка озвучки с паузами
    lst = out / "concat.txt"
    sil = out / "sil.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
                    "-t", str(GAP), str(sil)], check=True)
    lst.write_text("".join(f"file '{p.name}'\nfile 'sil.wav'\n" for p, _ in parts))
    voice = out / "voice.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-af", "loudnorm=I=-14:TP=-1.5", "-ar", "44100", str(voice)], check=True)

    if story.get("ambient"):
        # тихий низкий гул + синтезированные удары в дверь (scene.knocks, сек от начала сцены)
        knocks = [sc["start"] + k for sc in story["scenes"] for k in sc.get("knocks", [])]
        inputs = ["-i", str(voice), "-f", "lavfi", "-t", str(story["duration"]),
                  "-i", "anoisesrc=color=brown:amplitude=0.5:r=44100"]
        filt = ["[1]lowpass=f=180,volume=0.10[amb]"]
        mix = ["[0]", "[amb]"]
        for j, k in enumerate(knocks):
            inputs += ["-f", "lavfi", "-t", "0.35", "-i",
                       "aevalsrc='(sin(2*PI*65*t)+0.6*sin(2*PI*130*t))*exp(-22*t)':s=44100"]
            filt.append(f"[{j + 2}]volume=0.9,adelay={int(k * 1000)}:all=1[k{j}]")
            mix.append(f"[k{j}]")
        filt.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first,alimiter=limit=0.95[a]")
        mixed = out / "mixed.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt),
                        "-map", "[a]", "-ac", "1", str(mixed)], check=True)
        voice = mixed

    tl = out / "timeline.json"
    tl.write_text(json.dumps(story, ensure_ascii=False))
    mp4 = ROOT / "out" / f"{story['id']}.mp4"
    tpl = ROOT / story.get("template", "template.html")
    subprocess.run(["node", str(ROOT / "render.js"), str(tl), str(voice), str(mp4), str(tpl)], check=True)
    print(mp4)


if __name__ == "__main__":
    main(sys.argv[1])

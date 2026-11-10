"""Сведение звука и сборка финального ролика.

Голос + музыка (приглушается под голосом) + синтезированные эффекты по таймлайну сцен.
Вход: audio/voice.wav, audio/music.wav, render/video.mp4, render/timeline.json
Выход: render/final.mp4
"""
import json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
tl = json.loads((ROOT / "render/timeline.json").read_text())
S, total = tl["scenes"], tl["total"]

SFX = {
    "alert": ("0.35*sin(2*PI*(880-220*gte(mod(t,0.5),0.25))*t)*lt(mod(t,0.25),0.2)", 1.5),
    "hit": ("0.9*sin(2*PI*(45+40*exp(-8*t))*t)*exp(-5*t)+0.15*(random(0)-0.5)*exp(-20*t)", 0.8),
    "spark": ("0.5*(random(0)-0.5)*exp(-18*t)", 0.3),
    "beep": ("0.25*sin(2*PI*1760*t)*lt(t,0.09)", 0.12),
    "ring": ("0.22*(sin(2*PI*1320*t)+sin(2*PI*1760*t))*lt(mod(t,0.1),0.05)*lt(t,0.8)", 0.9),
    "glitch": ("0.4*(random(0)-0.5)*gt(sin(2*PI*14*t),0)+0.3*sin(2*PI*120*t)*gt(sin(2*PI*9*t),0.3)", 0.9),
}
events = [("hit", s["t0"]) for s in S[1:]]
events += [("glitch", S[-1]["t0"] + 0.1)]

inputs = ["-i", str(ROOT / "render/video.mp4"), "-i", str(ROOT / "audio/voice.wav"), "-i", str(ROOT / "audio/music.wav")]
fc = [f"[2:a]volume=0.32,afade=t=in:d=2,afade=t=out:st={total - 3:.2f}:d=3,atrim=0:{total:.2f}[mus]",
      "[1:a]asplit=2[v1][vsc]",
      "[mus][vsc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[duck]"]
labels = ["[v1]", "[duck]"]
for i, (name, at) in enumerate(events):
    expr, d = SFX[name]
    fc.append(f"aevalsrc='{expr}':s=48000:d={d},adelay={int(at * 1000)}:all=1[e{i}]")
    labels.append(f"[e{i}]")
fc.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,"
          f"atrim=0:{total:.2f}[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-movflags", "+faststart", str(ROOT / "render/final.mp4")], check=True)
print("render/final.mp4 готов")

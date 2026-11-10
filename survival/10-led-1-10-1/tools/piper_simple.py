"""Офлайн нейро-озвучка Piper, когда нет кредитов на ElevenLabs.
Модель (GitHub): https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-ru_RU-ruslan-medium.tar.bz2
python3 tools/piper.py <model.onnx> voiceover.txt audio/voice.wav   (нужен pip install piper-tts)
"""
import subprocess, sys, tempfile
from pathlib import Path

model, txt, out = sys.argv[1:4]
tmp = Path(tempfile.mkdtemp())
paras = [p.strip() for p in Path(txt).read_text(encoding="utf-8").split("\n\n") if p.strip()]
lst = []
for i, p in enumerate(paras):
    subprocess.run([sys.executable, "-m", "piper", "-m", model, "--length-scale", "1.12", "-f", str(tmp / f"p{i}.wav")], input=p.encode(), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp / f"p{i}.wav"), "-af", "apad=pad_dur=0.45", "-ar", "22050", "-ac", "1",
                    str(tmp / f"g{i}.wav")], check=True)
    lst.append(f"file 'g{i}.wav'")
(tmp / "list.txt").write_text("\n".join(lst))
# чуть ниже тон, «дикторская» эквализация, мягкая компрессия, лёгкий объём
af = ("asetrate=22050*0.96,aresample=48000,atempo=1.0417,highpass=f=70,equalizer=f=160:t=q:w=1:g=3,"
      "equalizer=f=3200:t=q:w=1:g=1.5,acompressor=threshold=0.1:ratio=3:attack=10:release=200,aecho=0.8:0.4:35:0.08")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"), "-af", af, out], check=True)

"""Офлайн-озвучка через RHVoice (apt: rhvoice rhvoice-russian), когда нет кредитов на ElevenLabs.
python3 tools/rhvoice.py voiceover.txt audio/voice.wav [tmpdir]
"""
import subprocess, sys, tempfile
from pathlib import Path

txt, out = sys.argv[1:3]
tmp = Path(sys.argv[3] if len(sys.argv) > 3 else tempfile.mkdtemp())
tmp.mkdir(parents=True, exist_ok=True)
paras = [p.strip() for p in Path(txt).read_text(encoding="utf-8").split("\n\n") if p.strip()]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "0.45", str(tmp / "gap.wav")], check=True)
lst = []
for i, p in enumerate(paras):
    subprocess.run(["RHVoice-test", "-p", "aleksandr-hq", "-q", "max", "-r", "95", "-o", str(tmp / f"p{i}.wav")], input=p.encode(), check=True)
    lst += [f"file 'p{i}.wav'", "file 'gap.wav'"]
(tmp / "list.txt").write_text("\n".join(lst))
# тон −5 %, темп +8 %, «дикторская» эквализация и лёгкое эхо
af = ("asetrate=24000*0.95,aresample=48000,atempo=1.137,highpass=f=70,equalizer=f=180:t=q:w=1:g=3,"
      "equalizer=f=3500:t=q:w=1:g=2,acompressor=threshold=0.1:ratio=3:attack=10:release=200,aecho=0.8:0.5:40:0.12")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"), "-af", af, out], check=True)

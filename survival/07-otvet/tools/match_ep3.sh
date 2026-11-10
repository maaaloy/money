#!/usr/bin/env bash
# Голос финала «как в ч. 3» без кредитов ElevenLabs: Piper ruslan → тон/темп/тембр подогнаны под Brian из 03-rassvet.
# Замеры (librosa): ч. 3 — F0 96 Гц, 2.73 слова/с; ruslan — 115 Гц, 2.54. После подгонки: 96 Гц, 2.62, разница спектра 0.7 дБ.
# usage: tools/match_ep3.sh <ru_RU-ruslan-medium.onnx>   (venv с piper-tts, numpy)
set -e
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
LS_MUL=0.93 NOISE_W=1.05 python3 -I tools/piper_natural.py "$1" voiceover.txt "$tmp/raw.wav" "$tmp/words.json" --raw
EQ="firequalizer=gain_entry='entry(60,6);entry(100,8);entry(160,4.8);entry(250,-1.3);entry(400,-6);entry(630,-5);entry(1000,-1.3);entry(1600,-1.5);entry(2500,-1.7);entry(4000,0.7);entry(6300,2.3);entry(9000,1)'"
ffmpeg -v error -y -i "$tmp/raw.wav" -af "rubberband=pitch=0.87:tempo=1.07:formant=preserved,$EQ,acompressor=threshold=0.12:ratio=2.5:attack=8:release=180,alimiter=limit=0.9" -ar 48000 audio/voice.wav
python3 - "$tmp/words.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
for w in d["words"]: w["t"] = round(w["t"] / 1.07, 3); w["e"] = round(w["e"] / 1.07, 3)
d["duration"] /= 1.07
json.dump(d, open("audio/words.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
PY

#!/usr/bin/env bash
# Подготовка окружения для video/make.py (идемпотентно, можно запускать каждый раз).
set -e
cd "$(dirname "$0")"
[ -x /home/user/tts/bin/python3 ] || python3 -m venv /home/user/tts
/home/user/tts/bin/python3 -c "import piper, numpy" 2>/dev/null || /home/user/tts/bin/pip install -q piper-tts numpy
mkdir -p voices
for e in onnx onnx.json; do
  f=voices/ru_RU-ruslan-medium.$e
  [ -s "$f" ] || curl -sSL -o "$f" "https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/ruslan/medium/ru_RU-ruslan-medium.$e"
done
command -v ffmpeg >/dev/null && ffmpeg -hide_banner -filters 2>/dev/null | grep -q rubberband || echo "WARN: ffmpeg без rubberband"
/home/user/tts/bin/python3 -c "import vosk_tts" 2>/dev/null || /home/user/tts/bin/pip install -q vosk-tts
[ -d /home/user/models/vosk-model-tts-ru-0.9-multi ] || (mkdir -p /home/user/models && cd /home/user/models && curl -sSL -o v.zip https://alphacephei.com/vosk/models/vosk-model-tts-ru-0.9-multi.zip && unzip -q v.zip && rm v.zip)
node -e "require('playwright')" && echo "video setup ok"

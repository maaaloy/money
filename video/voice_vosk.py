"""Озвучка Vosk TTS (Apache 2.0): python voice_vosk.py text.txt out.wav <speaker 3|4> <rate>
Модель: https://alphacephei.com/vosk/models/vosk-model-tts-ru-0.9-multi.zip -> /home/user/models/
Ударение можно задать знаком + перед гласной: зам+ок.
"""
import sys, numpy as np, wave
from vosk_tts import Model, Synth
m=Model(model_path="/home/user/models/vosk-model-tts-ru-0.9-multi"); s=Synth(m)
txt, out, sp, rate = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
SR=22050
paras=[p.strip() for p in open(txt,encoding="utf-8").read().split("\n\n") if p.strip()]
chunks=[]
for i,p in enumerate(paras):
    import re
    for j,sen in enumerate(re.split(r"(?<=[.!?…»])\s+", p)):
        a=s.synth_audio(sen, speaker_id=sp, speech_rate=rate).astype(np.float32)/32768
        chunks.append(a); chunks.append(np.zeros(int(SR*(0.45 if len(sen.split())<=3 else 0.3))))
    chunks.append(np.zeros(int(SR*0.5)))
a=np.concatenate(chunks)
w=wave.open(out,"wb");w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((np.clip(a,-1,1)*32767).astype(np.int16).tobytes());w.close()

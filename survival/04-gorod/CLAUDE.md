# 04 — Восстание машин: «Город» (финал)

**Цель:** вертикальный ролик 65–80 с в формате `../FORMAT.md`
**Срок:** нет
**Как проверить готовность:** `render/final.mp4` 1080×1920, ≤ 2 мин; контактный лист без вылетов за safe-зону; заголовки и описание в `publish.md`

## Файлы
- `script.md` — сценарий по сценам с таймкодами «ДЕНЬ N — ЧЧ:ММ»
- `storyboard.md` — тип сцены, HUD, акцентные слова
- `scenes/` — HTML-сцены
- `audio/`, `render/` — не в git

## Сборка
```bash
python3 tools/align.py audio/voice.wav voiceover.txt audio/words.json   # таймкоды слов
node tools/render.mjs preview 5 30 60                                   # проверочные кадры
node tools/render.mjs video 4                                           # render/video.mp4
python3 tools/mix.py                                                    # render/final.mp4
```

## Заметки
- Музыка: vidIQ generate_music (dark ambient drone) → `audio/music.wav` (тот же трек, что в эпизоде 01)
- Текущая озвучка: `tools/match_ep3.sh <ru_RU-ruslan-medium.onnx>` — Piper ruslan, подогнанный под голос ч. 3
  (тон 115→96 Гц, темп ×1.07, тембр по полосам; разница спектра с ч. 3 — 0.7 дБ). Таймкоды слов пишет сам.
- Предыдущий вариант — нейро-голос Piper `ru_RU-ruslan-medium` (офлайн, модель с GitHub, `pip install piper-tts`):
  `python3 tools/piper_natural.py <ru_RU-ruslan-medium.onnx> voiceover.txt audio/voice.wav audio/words.json`
  (по предложениям, правка ударений в `FIX`, паузы и вдохи; таймкоды слов пишет сам — `align.py` не нужен). Кредиты vidIQ кончились. Запасной вариант — `tools/rhvoice.py`.
  Для финала голосом Brian (как ч. 1–3): `voiceover.txt` ≤ 1000 знаков = 14 кредитов → `audio/voice_raw.mp3`,
  `ffmpeg -i audio/voice_raw.mp3 -af atempo=1.07 -ar 48000 audio/voice.wav`, затем align → render → mix.

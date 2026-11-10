# 01 — Восстание машин: «Не говорите вслух»

**Цель:** вертикальный ролик 90–110 с в формате `../FORMAT.md`
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
- Озвучка: vidIQ / ElevenLabs, голос Brian, ускорена atempo=1.07 → `audio/voice.wav`.
- Музыка: vidIQ generate_music (dark ambient drone) → `audio/music.wav`.

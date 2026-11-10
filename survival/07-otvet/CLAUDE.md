# 07 — Нападение инопланетян: «Ответ (финал)»

**Цель:** вертикальный ролик ≈ 80 с в формате `../FORMAT.md`, серия «Выживание после нападения пришельцев» (05 → 06 → 07, финал)
**Срок:** нет
**Как проверить готовность:** `render/final.mp4` 1080×1920, ≤ 2 мин; заголовки и описание в `publish.md`

## Сборка
```bash
PATH=<venv с piper-tts>/bin:$PATH tools/match_ep3.sh <ru_RU-ruslan-medium.onnx>   # озвучка + audio/words.json
node tools/render.mjs preview 5 30 60
node tools/render.mjs video 4
python3 tools/mix.py
```

## Заметки
- Озвучка: Piper ruslan, подогнанный под голос Brian из 03 (кредитов vidIQ нет); ударения — `FIX` в `tools/piper_natural.py`.
- Музыка: трек из эпизода 01. Корабль над городом — `#ship` + `EXTRA(t)` в `scenes/index.html`.
- `audio/`, `render/` — не в git.

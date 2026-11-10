# 09 — Зомби: первые 24 часа

**Цель:** вертикальный ролик 30–40 с по сценарию на 01.11.2026 (14:50)
**Как проверить готовность:** `render/final.mp4` 1080×1920, ≤ 40 с; 5 сцен по сценарию; хук на экране 0–2 с

## Сборка
```bash
PATH=<venv с piper-tts>/bin:$PATH tools/match_ep3.sh <ru_RU-ruslan-medium.onnx>
node tools/render.mjs video 4 && python3 tools/mix.py
```
- Видео — моушн-графика вместо ИИ-клипов (кредитов vidIQ нет). Голос — Piper под Brian, ударения в `FIX`.

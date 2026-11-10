# Выживание после… — конвейер вертикальных роликов

> С выпуска 17 ролики собираются по общему шаблону: `video/template_survival.html` + сценарий `video/stories/sv-*.json` → `python3 video/make.py <json>`. Голос — Vosk (как в «Тихом подъезде»). Выпуски 01–16 ниже — архив ручного конвейера.

Канал про сценарии выживания: вертикаль 9:16, 30–110 с, закадровый голос, пословные субтитры, моушн-графика (HTML-сцены, отрисованные Playwright).
Перенесено из `opus55working-collab/claude-projects` (`youtube/shorts/`, `youtube/channel/`).

## Что здесь лежит

| Путь | Что это |
|---|---|
| `FORMAT.md` | Правила формата: структура, стиль, библиотека сцен |
| `AGENT.md` | Описание агента `survival-shorts` (положить в `.claude/agents/`, чтобы им пользоваться) |
| `channel/` | Оформление канала: `brand.html` → `avatar.png`, `banner.png`, `watermark.png` (`node shoot.cjs`), `channel.md` — название, описание, ключевые слова |
| `_episode/` | Пустой шаблон папки выпуска |
| `NN-тема/` | Выпуски: `voiceover.txt` (текст озвучки), `scenes/index.html` (все сцены), `tools/`, `publish.md` (название/описание), `CLAUDE.md`, у ранних — `script.md`, `storyboard.md` |

Инструменты в `NN-тема/tools/` (бери из самого свежего выпуска, `16-…`):

| Файл | Что делает |
|---|---|
| `piper_natural.py` | Озвучка Piper по предложениям: правка ударений (`FIX`), паузы, вдохи, пишет `audio/words.json` |
| `match_ep3.sh` | Озвучка + подгонка тона/темпа/тембра под голос Brian из ранних выпусков → `audio/voice.wav` |
| `align.py` | Пословные таймкоды по паузам (для озвучки, сделанной не через `piper_natural.py`, например из vidIQ/ElevenLabs) |
| `render.mjs` | Playwright → кадры → ffmpeg; `preview <секунды…>` — проверочные кадры, `video 4` — видео в 4 потока |
| `mix.py` | Голос + музыка с даккингом + синтезированные эффекты → `render/final.mp4` (−14 LUFS) |
| `rhvoice.py`, `piper_simple.py` | Запасные варианты озвучки |

## Что не перенесено (тяжёлое или генерируемое) и откуда взять

| Что | Где взять |
|---|---|
| Готовые ролики `*.mp4`, `render/` | Пересобираются командами ниже |
| `audio/voice.wav`, `audio/words.json` | Генерируются `match_ep3.sh` (или vidIQ → `align.py`) |
| `audio/music.wav` (фон, одинаковый во всех выпусках) | Сгенерирован в vidIQ (`generate_music`, 120 с), промпт: *«Dark cinematic ambient drone, instrumental, tense and ominous, low synth pads, subtle digital glitches and electronic pulses, slow 60 bpm heartbeat-like sub bass, sci-fi horror atmosphere, minimal and spacious, builds slowly towards the end»*. Подойдёт любой роялти-фри трек ≥ 2 мин |
| Голосовая модель Piper | https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-ru_RU-ruslan-medium.tar.bz2 (распаковать, нужен `ru_RU-ruslan-medium.onnx` + `.onnx.json`) |
| Python-пакеты | `python3 -m venv tts && tts/bin/pip install piper-tts numpy librosa` |
| Playwright + Chromium, ffmpeg (с `rubberband`) | `npm i playwright && npx playwright install chromium`, `apt install ffmpeg` |
| RHVoice (запасной голос) | `apt install rhvoice rhvoice-russian` |
| Голос Brian (выпуски 01–03) | vidIQ `voiceover_generate`, voiceId `nPczCjzI2devNBz1zQrb`, 14 кредитов за 1000 знаков |

## Как сделать новый выпуск

```bash
cp -r 16-pozhar-mnogoetazhka 17-nova-tema && cd 17-nova-tema
mkdir -p audio && cp <музыка> audio/music.wav
# 1. Текст: voiceover.txt — абзац на сцену, числа словами («сто двенадцать»)
# 2. Ударения: прогнать слова через piper.phonemize, ошибки — в FIX (tools/piper_natural.py)
PATH=<venv>/bin:$PATH tools/match_ep3.sh <ru_RU-ruslan-medium.onnx>   # audio/voice.wav + words.json
# 3. Сцены: в scenes/index.html заменить блок от «/* EP-START */» до «let CHUNKS=[];»
#    scene('первые слова абзаца', 'ЧАСЫ', {ключ:'слово озвучки'}, build, update) — по сцене на абзац,
#    в конце END(), EXTRA(t), ACC (цвета слов в субтитрах), NUM (числа цифрами)
node tools/render.mjs preview 0.5 5 10 20 30      # проверить кадры в render/preview/
node tools/render.mjs video 4 && python3 tools/mix.py
ffmpeg -i render/final.mp4 -c:v libx264 -preset slow -crf 26 -maxrate 4.5M -bufsize 9M \
  -pix_fmt yuv420p -c:a copy -movflags +faststart render/final_small.mp4
```

Проверка готовности: 1080×1920, длительность по формату, плашки не вылезают за край, субтитры читаются (контактный лист: `ffmpeg -i render/final_small.mp4 -vf "fps=1/5,scale=180:-1,tile=8x2" sheet.png`).

## Вышедшие темы

| № | Тема | Формат |
|---|---|---|
| 01–04 | Выживание после восстания машин: «Не говорите вслух», «Не отвечай», «Рассвет», «Город» (финал) | серия, 1:07–1:51 |
| 05–07 | Выживание после нападения пришельцев: «Тень», «Гул», «Ответ» (финал) | серия, 1:17–1:22 |
| 08 | Как выжить в бункере первые 72 часа | 01.11.2026, 11:50 |
| 09 | Первые 24 часа зомби-апокалипсиса | 01.11.2026, 14:50 |
| 10 | Провалился под лёд: правило 1-10-1 | 01.11.2026, 17:50 |
| 11 | Блэкаут зимой: свет пропал на неделю | 02.11.2026, 11:50 |
| 12 | Заблудился в лесу: первые 3 часа | 02.11.2026, 14:50 |
| 13 | Выживание после наводнения | 02.11.2026, 17:50 |
| 14 | Землетрясение: первые 60 секунд | 03.11.2026, 11:50 |
| 15 | Ядерная тревога: первые 24 часа | 03.11.2026, 14:50 |
| 16 | Пожар в многоэтажке | 03.11.2026, 17:50 |
| 17 | Застрял в лифте между этажами (новый шаблон, `video/stories/sv-017-lift.json`) | готов |

Названия и описания для публикации — в `publish.md` каждого выпуска.

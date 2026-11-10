#!/usr/bin/env python3
"""Раскладывает готовые ролики по дням: python3 video/package.py video/stories/tp-101-*.json ...
Результат: video/out/publish/<ДД.ММ>/<ЧЧ-ММ>_<канал>_ч<N>.mp4 + publish.txt (порядок публикаций за день).
"""
import json, shutil, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CH = {"template_podezd2.html": "Тихий подъезд", "template_survival.html": "Выживание после…"}
SHORT = {"template_podezd2.html": "podezd", "template_survival.html": "survival"}

days = defaultdict(list)
for f in sys.argv[1:]:
    d = json.loads(Path(f).read_text(encoding="utf-8"))
    for i, part in enumerate(d["parts"], 1):
        days[d["date"]].append((d["times"][i - 1], d, i, part))

for date, items in days.items():
    out = ROOT / "out" / "publish" / date
    out.mkdir(parents=True, exist_ok=True)
    lines = [f"ПУБЛИКАЦИИ НА {date}\n"]
    for time, d, i, part in sorted(items, key=lambda x: x[0]):
        src = ROOT / "out" / f"{d['id']}-p{i}.mp4"
        name = f"{date}_{time.replace(':', '-')}_{SHORT[d['template']]}_ch{i}.mp4"
        status = "OK" if src.exists() else "НЕТ ФАЙЛА"
        if src.exists():
            shutil.copy(src, out / name)
        lines += [f"=== {time} · {CH[d['template']]} · «{d['theme']}» · часть {i}/{len(d['parts'])} · {name} [{status}]",
                  f"Название: {part['title']}", f"Описание:\n{part['description']}", ""]
    (out / f"publish_{date}.txt").write_text("\n".join(lines), encoding="utf-8")
    print(out)

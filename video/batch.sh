#!/usr/bin/env bash
# Параллельный рендер: bash video/batch.sh <json>...  (все части каждой темы, 3 потока)
cd "$(dirname "$0")/.."
for f in "$@"; do n=$(python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print(len(d.get('parts',[0])))" "$f"); for p in $(seq 1 $n); do echo "$f $p"; done; done |
  xargs -P "${JOBS:-3}" -L 1 sh -c 'python3 video/make.py "$0" "$1" >/dev/null 2>&1 && echo "OK $0 $1" || echo "FAIL $0 $1"'

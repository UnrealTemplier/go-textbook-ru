#!/usr/bin/env sh
# Что браузер нарисовал на каждой странице (формулы, диаграммы, ошибки JS), Firefox
. "$(dirname "$0")/_lib.sh"
OUT="${TMPDIR:-/tmp}/go-textbook-runtime.json"
$PY engine/tools/runtime_projection.py dist --out "$OUT" && echo "Отчёт: $OUT"

#!/usr/bin/env sh
# Проверка авторской вычитки статьи относительно HEAD (путь — аргументом или по запросу)
. "$(dirname "$0")/_lib.sh"
if [ $# -gt 0 ]; then V="$1"; shift; else printf "%s: " "Путь к статье (sources/…)"; read -r V; fi
$PY book/tools/verify_editorial.py "$V" --git-ref HEAD "$@"

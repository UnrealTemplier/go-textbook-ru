#!/usr/bin/env sh
# Аудит dist/: ссылки, якоря, имена файлов, ассеты, offline, диаграммы
. "$(dirname "$0")/_lib.sh"
$PY -m engine.audit "$@"

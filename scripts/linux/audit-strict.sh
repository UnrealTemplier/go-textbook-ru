#!/usr/bin/env sh
# Аудит + предупреждения сборки как ошибки
. "$(dirname "$0")/_lib.sh"
$PY -m engine.audit --strict "$@"

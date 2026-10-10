#!/usr/bin/env sh
# Полная сборка; предупреждения сборки — ошибки
. "$(dirname "$0")/_lib.sh"
$PY -m engine.build --all --strict "$@"

#!/usr/bin/env sh
# Полная сборка сайта в dist/
. "$(dirname "$0")/_lib.sh"
$PY -m engine.build --all "$@"

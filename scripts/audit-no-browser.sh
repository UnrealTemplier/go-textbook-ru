#!/usr/bin/env sh
# Аудит без Firefox (без рантайм-разбора диаграмм)
. "$(dirname "$0")/_lib.sh"
$PY -m engine.audit --strict --no-mermaid-runtime "$@"

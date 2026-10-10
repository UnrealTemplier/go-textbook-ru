#!/usr/bin/env sh
# Перезаписать базу известных дефектов book/audit-baseline.json (после исправления ссылок или формул)
. "$(dirname "$0")/_lib.sh"
$PY -m engine.audit --katex-runtime --write-baseline

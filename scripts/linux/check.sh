#!/usr/bin/env sh
# Всё перед коммитом: строгая сборка, строгий аудит, тесты
. "$(dirname "$0")/_lib.sh"
$PY -m engine.build --all --strict && $PY -m engine.audit --strict && $PY -m unittest discover -s engine/tests -t . && $PY -m unittest discover -s book/tests

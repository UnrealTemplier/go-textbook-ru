#!/usr/bin/env sh
# Тесты ядра и книжные тесты (после пересборки dist/)
. "$(dirname "$0")/_lib.sh"
$PY -m unittest discover -s engine/tests -t . && $PY -m unittest discover -s book/tests

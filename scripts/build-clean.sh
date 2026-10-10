#!/usr/bin/env sh
# Чистая пересборка: удалить dist/ и собрать заново (убирает страницы-сироты)
. "$(dirname "$0")/_lib.sh"
rm -rf dist && $PY -m engine.build --all "$@"

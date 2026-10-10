#!/usr/bin/env sh
# Обновить engine/ из репозитория движка (ENGINE_DIR, по умолчанию ../html-textbook-engine); делает коммит
. "$(dirname "$0")/_lib.sh"
$PY -m engine.sync --from "$ENGINE_DIR" "$@"

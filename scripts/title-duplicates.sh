#!/usr/bin/env sh
# Проверить реестр двойных H1 fact-checks/title-duplicates.md (код 1, если устарел)
. "$(dirname "$0")/_lib.sh"
$PY -m engine.tools.title_duplicates --book book.toml --out fact-checks/title-duplicates.md --check

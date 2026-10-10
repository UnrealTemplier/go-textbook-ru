#!/usr/bin/env sh
# Перегенерировать реестр двойных H1
. "$(dirname "$0")/_lib.sh"
$PY -m engine.tools.title_duplicates --book book.toml --out fact-checks/title-duplicates.md

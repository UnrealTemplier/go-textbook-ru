#!/usr/bin/env sh
# Открыть dist/index.html в браузере
. "$(dirname "$0")/_lib.sh"
if command -v xdg-open >/dev/null 2>&1; then xdg-open "dist/index.html"; elif command -v open >/dev/null 2>&1; then open "dist/index.html"; else echo "Откройте dist/index.html в браузере"; fi

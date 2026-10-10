#!/usr/bin/env sh
# Полный аудит: --strict и рантайм KaTeX/Mermaid в Firefox (несколько минут)
. "$(dirname "$0")/_lib.sh"
$PY -m engine.audit --strict --katex-runtime "$@"

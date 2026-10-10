# scripts/_lib.sh — общая часть скриптов: корень репозитория и интерпретатор Python.
# Подключается командой «. "$(dirname "$0")/_lib.sh"» в начале каждого скрипта.
cd "$(dirname "$0")/.." || exit 1
if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
ENGINE_DIR="${ENGINE_DIR:-../html-textbook-engine}"

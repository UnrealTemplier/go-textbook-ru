#!/usr/bin/env sh
# Пилотная сборка: первые 15 статей модуля 1 (~1 с)
. "$(dirname "$0")/_lib.sh"
$PY -m engine.build --pilot

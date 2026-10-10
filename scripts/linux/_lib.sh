# scripts/linux/_lib.sh — общая часть скриптов: запуск двойным щелчком, корень репозитория, Python.
# Подключается командой «. "$(dirname "$0")/_lib.sh"» в начале каждого скрипта.

# Двойной щелчок в файловом менеджере запускает скрипт без терминала (ни ввод, ни вывод не на терминале).
# Тогда открываем окно терминала по умолчанию, выполняем скрипт там и оставляем окно открытым:
# после завершения появляется приглашение shell, окно закрывает пользователь.
if [ ! -t 0 ] && [ ! -t 1 ]; then
  SELF=$(readlink -f "$0")
  TERM_APP=$(sed -n 's/^TerminalApplication=//p' "$HOME/.config/kdeglobals" 2>/dev/null | head -n 1)
  HOLD='sh "$0" "$@"; rc=$?; echo; echo "Готово, код $rc. Окно можно закрыть или введите exit."; exec "${SHELL:-sh}"'
  for t in xdg-terminal-exec "$TERM_APP" x-terminal-emulator gnome-terminal konsole xterm; do
    command -v "$t" >/dev/null 2>&1 || continue
    case "$t" in
      xdg-terminal-exec) exec "$t" sh -c "$HOLD" "$SELF" "$@" ;;
      gnome-terminal) exec "$t" -- sh -c "$HOLD" "$SELF" "$@" ;;
      *) exec "$t" -e sh -c "$HOLD" "$SELF" "$@" ;;
    esac
  done
  kdialog --error "Не найден терминал по умолчанию. Запустите скрипт из терминала." 2>/dev/null
  exit 1
fi
cd "$(dirname "$0")/../.." || exit 1
if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
ENGINE_DIR="${ENGINE_DIR:-../html-textbook-engine}"

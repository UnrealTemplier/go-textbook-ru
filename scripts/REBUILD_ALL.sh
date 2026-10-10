#!/usr/bin/env sh
# REBUILD_ALL — полная проверка и пересборка go-textbook одним запуском: зависимости, чистая пересборка
# dist/ (строго), строгий аудит с рантаймом KaTeX и Mermaid в Firefox, тесты ядра и книги, реестр
# двойных H1 и сверка dist/ с закоммиченным. Двойной щелчок открывает окно терминала
# и оставляет его открытым после работы, пока вы его не закроете.
SELF=$(readlink -f "$0")

# Запуск без терминала (двойной щелчок в файловом менеджере): открываем терминал по умолчанию.
if [ ! -t 0 ] && [ ! -t 1 ]; then
  TERM_APP=$(sed -n 's/^TerminalApplication=//p' "$HOME/.config/kdeglobals" 2>/dev/null | head -n 1)
  HOLD='sh "$0"; rc=$?; echo; echo "Готово, код $rc. Окно можно закрыть или введите exit."; exec "${SHELL:-sh}"'
  for t in xdg-terminal-exec "$TERM_APP" x-terminal-emulator gnome-terminal konsole xterm; do
    command -v "$t" >/dev/null 2>&1 || continue
    case "$t" in
      xdg-terminal-exec) exec "$t" sh -c "$HOLD" "$SELF" ;;
      gnome-terminal) exec "$t" -- sh -c "$HOLD" "$SELF" ;;
      *) exec "$t" -e sh -c "$HOLD" "$SELF" ;;
    esac
  done
  kdialog --error "Не найден терминал по умолчанию. Запустите скрипт из терминала." 2>/dev/null
  exit 1
fi

cd "$(dirname "$SELF")/.." || exit 1
if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi

FAILED=0
RESULTS=""

# step "название" команда...: печатает заголовок шага, запускает команду и запоминает итог.
step() {
  name=$1
  shift
  printf '\n==== %s\n' "$name"
  if "$@"; then
    RESULTS="$RESULTS
[OK]         $name"
    return 0
  fi
  RESULTS="$RESULTS
[ОШИБКА]     $name"
  FAILED=1
  return 1
}

skip() {
  RESULTS="$RESULTS
[ПРОПУЩЕНО]  $1: $2"
}

note() {
  RESULTS="$RESULTS
[ВНИМАНИЕ]   $1"
}

build_clean() {
  rm -rf dist && $PY -m engine.build --all --strict
}

tests_all() {
  $PY -m unittest discover -s engine/tests -t . && $PY -m unittest discover -s book/tests
}

# dist/ коммитится в git: после пересборки он должен совпадать с закоммиченным.
dist_matches_head() {
  if [ -n "$(git status --porcelain -- dist 2>/dev/null)" ]; then
    note "dist/ отличается от закоммиченного: если правили sources/, закоммитьте пересобранный dist/"
  fi
  return 0
}

step "Зависимости (requirements.txt)" $PY -m pip install -q -r requirements.txt
if step "Чистая пересборка dist/ (строгая)" build_clean; then
  step "Строгий аудит и рантайм KaTeX/Mermaid в Firefox" $PY -m engine.audit --katex-runtime --strict
  step "Тесты ядра и книги" tests_all
else
  skip "Строгий аудит и рантайм KaTeX/Mermaid в Firefox" "сборка не прошла"
  skip "Тесты ядра и книги" "сборка не прошла"
fi
step "Реестр двойных H1 (fact-checks/title-duplicates.md)" \
  $PY -m engine.tools.title_duplicates --book book.toml --out fact-checks/title-duplicates.md --check
step "Сверка dist/ с закоммиченным" dist_matches_head

echo
echo "==== Итог"
printf '%s\n' "$RESULTS"
if [ "$FAILED" = 0 ]; then
  echo "Всё прошло."
else
  echo "Есть ошибки — см. вывод шагов выше."
fi
exit "$FAILED"

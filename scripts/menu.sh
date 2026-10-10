#!/usr/bin/env sh
# Меню всех команд go-textbook: выберите номер, после выполнения — снова меню.
cd "$(dirname "$0")" || exit 1
while true; do
  echo ""
  echo "go-textbook: команды"
  echo "   1. check — Всё перед коммитом: строгая сборка, строгий аудит, тесты"
  echo "   2. build — Полная сборка сайта в dist/"
  echo "   3. build-strict — Полная сборка; предупреждения сборки — ошибки"
  echo "   4. build-clean — Чистая пересборка: удалить dist/ и собрать заново (убирает страницы-сироты)"
  echo "   5. build-module — Сборка одного модуля (номер — аргументом или по запросу)"
  echo "   6. audit — Аудит dist/: ссылки, якоря, имена файлов, ассеты, offline, диаграммы"
  echo "   7. audit-strict — Аудит + предупреждения сборки как ошибки"
  echo "   8. audit-full — Полный аудит: --strict и рантайм KaTeX/Mermaid в Firefox (несколько минут)"
  echo "   9. audit-no-browser — Аудит без Firefox (без рантайм-разбора диаграмм)"
  echo "  10. runtime-projection — Что браузер нарисовал на каждой странице (формулы, диаграммы, ошибки JS), Firefox"
  echo "  11. tests — Тесты ядра и книжные тесты (после пересборки dist/)"
  echo "  12. engine-sync — Обновить engine/ из репозитория движка (ENGINE_DIR, по умолчанию ../html-textbook-engine); делает коммит"
  echo "  13. open-site — Открыть dist/index.html в браузере"
  echo "  14. audit-write-baseline — Перезаписать базу известных дефектов book/audit-baseline.json (после исправления ссылок или формул)"
  echo "  15. build-pilot — Пилотная сборка: первые 15 статей модуля 1 (~1 с)"
  echo "  16. title-duplicates — Проверить реестр двойных H1 fact-checks/title-duplicates.md (код 1, если устарел)"
  echo "  17. title-duplicates-write — Перегенерировать реестр двойных H1"
  echo "  18. verify-editorial — Проверка авторской вычитки статьи относительно HEAD (путь — аргументом или по запросу)"
  printf "Номер (Enter — выход): "
  read -r c || exit 0
  [ -z "$c" ] && exit 0
  case "$c" in
    1) sh ./check.sh ;;
    2) sh ./build.sh ;;
    3) sh ./build-strict.sh ;;
    4) sh ./build-clean.sh ;;
    5) sh ./build-module.sh ;;
    6) sh ./audit.sh ;;
    7) sh ./audit-strict.sh ;;
    8) sh ./audit-full.sh ;;
    9) sh ./audit-no-browser.sh ;;
    10) sh ./runtime-projection.sh ;;
    11) sh ./tests.sh ;;
    12) sh ./engine-sync.sh ;;
    13) sh ./open-site.sh ;;
    14) sh ./audit-write-baseline.sh ;;
    15) sh ./build-pilot.sh ;;
    16) sh ./title-duplicates.sh ;;
    17) sh ./title-duplicates-write.sh ;;
    18) sh ./verify-editorial.sh ;;
    *) echo "Нет пункта $c" ;;
  esac
  printf "\nГотово (код %s). Enter — назад в меню... " "$?"
  read -r _ || exit 0
done

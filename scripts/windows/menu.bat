@echo off
chcp 65001 >nul
set "NOPAUSE=1"
:menu
echo.
echo go-textbook: команды
echo    1. check - Всё перед коммитом: строгая сборка, строгий аудит, тесты
echo    2. build - Полная сборка сайта в dist/
echo    3. build-strict - Полная сборка; предупреждения сборки — ошибки
echo    4. build-clean - Чистая пересборка: удалить dist/ и собрать заново (убирает страницы-сироты)
echo    5. build-module - Сборка одного модуля (номер — аргументом или по запросу)
echo    6. audit - Аудит dist/: ссылки, якоря, имена файлов, ассеты, offline, диаграммы
echo    7. audit-strict - Аудит + предупреждения сборки как ошибки
echo    8. audit-full - Полный аудит: --strict и рантайм KaTeX/Mermaid в Firefox (несколько минут)
echo    9. audit-no-browser - Аудит без Firefox (без рантайм-разбора диаграмм)
echo   10. runtime-projection - Что браузер нарисовал на каждой странице (формулы, диаграммы, ошибки JS), Firefox
echo   11. tests - Тесты ядра и книжные тесты (после пересборки dist/)
echo   12. engine-sync - Обновить engine/ из репозитория движка (ENGINE_DIR, по умолчанию ../html-textbook-engine); делает коммит
echo   13. open-site - Открыть dist/index.html в браузере
echo   14. audit-write-baseline - Перезаписать базу известных дефектов book/audit-baseline.json (после исправления ссылок или формул)
echo   15. build-pilot - Пилотная сборка: первые 15 статей модуля 1 (~1 с)
echo   16. title-duplicates - Проверить реестр двойных H1 fact-checks/title-duplicates.md (код 1, если устарел)
echo   17. title-duplicates-write - Перегенерировать реестр двойных H1
echo   18. verify-editorial - Проверка авторской вычитки статьи относительно HEAD (путь — аргументом или по запросу)
set "c="
set /p "c=Номер (Enter - выход): "
if "%c%"=="" exit /b 0
if "%c%"=="1" call "%~dp0check.bat" & goto done
if "%c%"=="2" call "%~dp0build.bat" & goto done
if "%c%"=="3" call "%~dp0build-strict.bat" & goto done
if "%c%"=="4" call "%~dp0build-clean.bat" & goto done
if "%c%"=="5" call "%~dp0build-module.bat" & goto done
if "%c%"=="6" call "%~dp0audit.bat" & goto done
if "%c%"=="7" call "%~dp0audit-strict.bat" & goto done
if "%c%"=="8" call "%~dp0audit-full.bat" & goto done
if "%c%"=="9" call "%~dp0audit-no-browser.bat" & goto done
if "%c%"=="10" call "%~dp0runtime-projection.bat" & goto done
if "%c%"=="11" call "%~dp0tests.bat" & goto done
if "%c%"=="12" call "%~dp0engine-sync.bat" & goto done
if "%c%"=="13" call "%~dp0open-site.bat" & goto done
if "%c%"=="14" call "%~dp0audit-write-baseline.bat" & goto done
if "%c%"=="15" call "%~dp0build-pilot.bat" & goto done
if "%c%"=="16" call "%~dp0title-duplicates.bat" & goto done
if "%c%"=="17" call "%~dp0title-duplicates-write.bat" & goto done
if "%c%"=="18" call "%~dp0verify-editorial.bat" & goto done
echo Нет пункта %c%
:done
echo.
pause
goto menu

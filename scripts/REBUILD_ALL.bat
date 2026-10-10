@echo off
chcp 65001 >nul
title go-textbook: REBUILD_ALL
rem REBUILD_ALL - полная проверка и пересборка go-textbook одним запуском: зависимости, версия движка, чистая пересборка dist/ (строго),
rem строгий аудит с рантаймом KaTeX и Mermaid в Firefox, тесты ядра и книги, реестр двойных H1 и сверка dist/ с git.
rem Двойной щелчок оставляет окно открытым до закрытия пользователем.
cd /d "%~dp0.."
set "PY=py -3"
where py >nul 2>nul || set "PY=python"
set "FAILED=0"
set "NOTE_VER="
set "NOTE_DIST="

echo.
echo ==== 1/6 Зависимости (requirements.txt)
%PY% -m pip install -q -r requirements.txt
if errorlevel 1 (set "R1=ОШИБКА" & set "FAILED=1") else (set "R1=OK")

echo.
echo ==== 2/6 Версия движка
call :engine_version
set "R2=OK"

echo.
echo ==== 3/6 Чистая пересборка dist/ (строгая)
if exist dist rmdir /s /q dist
%PY% -m engine.build --all --strict
if errorlevel 1 (set "R3=ОШИБКА" & set "FAILED=1") else (set "R3=OK")

echo.
echo ==== 4/6 Строгий аудит и рантайм KaTeX/Mermaid в Firefox
if "%R3%"=="OK" (
  %PY% -m engine.audit --katex-runtime --strict
  if errorlevel 1 (set "R4=ОШИБКА" & set "FAILED=1") else (set "R4=OK")
) else (
  set "R4=ПРОПУЩЕНО - сборка не прошла"
)

echo.
echo ==== 5/6 Тесты ядра и книги
if "%R3%"=="OK" (
  %PY% -m unittest discover -s engine/tests -t . && %PY% -m unittest discover -s book/tests
  if errorlevel 1 (set "R5=ОШИБКА" & set "FAILED=1") else (set "R5=OK")
) else (
  set "R5=ПРОПУЩЕНО - сборка не прошла"
)

echo.
echo ==== 6/6 Реестр двойных H1 и сверка dist/ с git
%PY% -m engine.tools.title_duplicates --book book.toml --out fact-checks\title-duplicates.md --check
if errorlevel 1 (set "R6=ОШИБКА" & set "FAILED=1") else (set "R6=OK")
for /f "delims=" %%i in ('git status --porcelain -- dist 2^>nul') do set "NOTE_DIST=dist/ отличается от закоммиченного: если правили sources/, закоммитьте пересобранный dist/"

echo.
echo ==== Итог
echo   1. Зависимости: %R1%
echo   2. Версия движка: %R2%
echo   3. Чистая пересборка dist/: %R3%
echo   4. Строгий аудит и рантайм: %R4%
echo   5. Тесты ядра и книги: %R5%
echo   6. Реестр двойных H1: %R6%
if defined NOTE_VER echo   ВНИМАНИЕ: %NOTE_VER%
if defined NOTE_DIST echo   ВНИМАНИЕ: %NOTE_DIST%
if "%FAILED%"=="0" (echo Всё прошло.) else (echo Есть ошибки - см. вывод шагов выше.)

echo.
rem Двойной щелчок: окно остаётся открытым, пока его не закроет пользователь
echo %CMDCMDLINE% | find /i " /c" >nul && (echo Введите exit или закройте окно. & cmd /k)
exit /b %FAILED%

:engine_version
if not exist "..\html-textbook-engine\engine\VERSION" (
  echo Репозиторий движка ..\html-textbook-engine не найден - сверка версии пропущена.
  exit /b 0
)
set "BOOK_V="
set "ENGINE_V="
set /p BOOK_V=<engine\VERSION
set /p ENGINE_V=<..\html-textbook-engine\engine\VERSION
echo Движок в книге: %BOOK_V%; в репозитории движка: %ENGINE_V%
if not "%BOOK_V%"=="%ENGINE_V%" set "NOTE_VER=версии движка различаются: обновите engine\ через scripts\windows\engine-sync.bat"
exit /b 0

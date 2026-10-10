@echo off
chcp 65001 >nul
title go-textbook: REBUILD_ALL
rem REBUILD_ALL - полная проверка и пересборка go-textbook одним запуском: зависимости, чистая пересборка dist/ (строго),
rem строгий аудит с рантаймом KaTeX и Mermaid в Firefox, тесты ядра и книги, реестр двойных H1 и сверка dist/ с git.
rem Двойной щелчок оставляет окно открытым до закрытия пользователем.
cd /d "%~dp0.."
set "PY=py -3"
where py >nul 2>nul || set "PY=python"
set "FAILED=0"
set "NOTE="

echo.
echo ==== 1/5 Зависимости (requirements.txt)
%PY% -m pip install -q -r requirements.txt
if errorlevel 1 (set "R1=ОШИБКА" & set "FAILED=1") else (set "R1=OK")

echo.
echo ==== 2/5 Чистая пересборка dist/ (строгая)
if exist dist rmdir /s /q dist
%PY% -m engine.build --all --strict
if errorlevel 1 (set "R2=ОШИБКА" & set "FAILED=1") else (set "R2=OK")

echo.
echo ==== 3/5 Строгий аудит и рантайм KaTeX/Mermaid в Firefox
if "%R2%"=="OK" (
  %PY% -m engine.audit --katex-runtime --strict
  if errorlevel 1 (set "R3=ОШИБКА" & set "FAILED=1") else (set "R3=OK")
) else (
  set "R3=ПРОПУЩЕНО - сборка не прошла"
)

echo.
echo ==== 4/5 Тесты ядра и книги
if "%R2%"=="OK" (
  %PY% -m unittest discover -s engine/tests -t . && %PY% -m unittest discover -s book/tests
  if errorlevel 1 (set "R4=ОШИБКА" & set "FAILED=1") else (set "R4=OK")
) else (
  set "R4=ПРОПУЩЕНО - сборка не прошла"
)

echo.
echo ==== 5/5 Реестр двойных H1 и сверка dist/ с git
%PY% -m engine.tools.title_duplicates --book book.toml --out fact-checks\title-duplicates.md --check
if errorlevel 1 (set "R5=ОШИБКА" & set "FAILED=1") else (set "R5=OK")
for /f "delims=" %%i in ('git status --porcelain -- dist 2^>nul') do set "NOTE=dist/ отличается от закоммиченного: если правили sources/, закоммитьте пересобранный dist/"

echo.
echo ==== Итог
echo   1. Зависимости: %R1%
echo   2. Чистая пересборка dist/: %R2%
echo   3. Строгий аудит и рантайм: %R3%
echo   4. Тесты ядра и книги: %R4%
echo   5. Реестр двойных H1: %R5%
if defined NOTE echo   ВНИМАНИЕ: %NOTE%
if "%FAILED%"=="0" (echo Всё прошло.) else (echo Есть ошибки - см. вывод шагов выше.)

echo.
rem Двойной щелчок: окно остаётся открытым, пока его не закроет пользователь
echo %CMDCMDLINE% | find /i " /c" >nul && (echo Введите exit или закройте окно. & cmd /k)
exit /b %FAILED%

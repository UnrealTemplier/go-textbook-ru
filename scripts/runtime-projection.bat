@echo off
call "%~dp0_lib.bat"
set "RC="
rem Что браузер нарисовал на каждой странице (формулы, диаграммы, ошибки JS), Firefox
%PY% engine\tools\runtime_projection.py dist --out "%TEMP%\go-textbook-runtime.json" && echo Отчёт: %TEMP%\go-textbook-runtime.json
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

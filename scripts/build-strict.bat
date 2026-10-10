@echo off
call "%~dp0_lib.bat"
set "RC="
rem Полная сборка; предупреждения сборки — ошибки
%PY% -m engine.build --all --strict %*
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

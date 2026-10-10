@echo off
call "%~dp0_lib.bat"
set "RC="
rem Полная сборка сайта в dist/
%PY% -m engine.build --all %*
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

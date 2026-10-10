@echo off
call "%~dp0_lib.bat"
set "RC="
rem Открыть dist/index.html в браузере
start "" "dist\index.html"
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

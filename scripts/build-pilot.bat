@echo off
call "%~dp0_lib.bat"
set "RC="
rem Пилотная сборка: первые 15 статей модуля 1 (~1 с)
%PY% -m engine.build --pilot
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

@echo off
call "%~dp0_lib.bat"
set "RC="
rem Аудит + предупреждения сборки как ошибки
%PY% -m engine.audit --strict %*
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

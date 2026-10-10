@echo off
call "%~dp0_lib.bat"
set "RC="
rem Аудит без Firefox (без рантайм-разбора диаграмм)
%PY% -m engine.audit --strict --no-mermaid-runtime %*
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

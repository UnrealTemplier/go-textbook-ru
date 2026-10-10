@echo off
call "%~dp0_lib.bat"
set "RC="
rem Перезаписать базу известных дефектов book/audit-baseline.json (после исправления ссылок или формул)
%PY% -m engine.audit --katex-runtime --write-baseline
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

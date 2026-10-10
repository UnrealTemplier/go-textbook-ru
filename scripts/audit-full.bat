@echo off
call "%~dp0_lib.bat"
set "RC="
rem Полный аудит: --strict и рантайм KaTeX/Mermaid в Firefox (несколько минут)
%PY% -m engine.audit --strict --katex-runtime %*
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

@echo off
call "%~dp0_lib.bat"
set "RC="
rem Обновить engine/ из репозитория движка (ENGINE_DIR, по умолчанию ../html-textbook-engine); делает коммит
%PY% -m engine.sync --from "%ENGINE_DIR%" %*
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

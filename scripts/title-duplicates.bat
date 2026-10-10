@echo off
call "%~dp0_lib.bat"
set "RC="
rem Проверить реестр двойных H1 fact-checks/title-duplicates.md (код 1, если устарел)
%PY% -m engine.tools.title_duplicates --book book.toml --out fact-checks/title-duplicates.md --check
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

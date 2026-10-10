@echo off
call "%~dp0_lib.bat"
set "RC="
rem Перегенерировать реестр двойных H1
%PY% -m engine.tools.title_duplicates --book book.toml --out fact-checks/title-duplicates.md
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

@echo off
call "%~dp0_lib.bat"
set "RC="
rem Проверить реестр двойных H1 fact-checks/title-duplicates.md (код 1, если устарел)
%PY% -m engine.tools.title_duplicates --book book.toml --out fact-checks/title-duplicates.md --check
if not defined RC set "RC=%ERRORLEVEL%"
rem Двойной щелчок: окно остаётся открытым, пока его не закроет пользователь (cmd /k вместо pause)
if not defined NOPAUSE echo %CMDCMDLINE% | find /i " /c" >nul && (echo. & echo Введите exit или закройте окно. & cmd /k)
exit /b %RC%

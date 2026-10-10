@echo off
call "%~dp0_lib.bat"
set "RC="
rem Перезаписать базу известных дефектов book/audit-baseline.json (после исправления ссылок или формул)
%PY% -m engine.audit --katex-runtime --write-baseline
if not defined RC set "RC=%ERRORLEVEL%"
rem Двойной щелчок: окно остаётся открытым, пока его не закроет пользователь (cmd /k вместо pause)
if not defined NOPAUSE echo %CMDCMDLINE% | find /i " /c" >nul && (echo. & echo Введите exit или закройте окно. & cmd /k)
exit /b %RC%

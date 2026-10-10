@echo off
call "%~dp0_lib.bat"
set "RC="
rem Обновить engine/ из репозитория движка (ENGINE_DIR, по умолчанию ../html-textbook-engine); делает коммит
%PY% -m engine.sync --from "%ENGINE_DIR%" %*
if not defined RC set "RC=%ERRORLEVEL%"
rem Двойной щелчок: окно остаётся открытым, пока его не закроет пользователь (cmd /k вместо pause)
if not defined NOPAUSE echo %CMDCMDLINE% | find /i " /c" >nul && (echo. & echo Введите exit или закройте окно. & cmd /k)
exit /b %RC%

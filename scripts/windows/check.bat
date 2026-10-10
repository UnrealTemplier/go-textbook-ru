@echo off
call "%~dp0_lib.bat"
set "RC="
rem Всё перед коммитом: строгая сборка, строгий аудит, тесты
%PY% -m engine.build --all --strict && %PY% -m engine.audit --strict && %PY% -m unittest discover -s engine/tests -t . && %PY% -m unittest discover -s book/tests
if not defined RC set "RC=%ERRORLEVEL%"
rem Двойной щелчок: окно остаётся открытым, пока его не закроет пользователь (cmd /k вместо pause)
if not defined NOPAUSE echo %CMDCMDLINE% | find /i " /c" >nul && (echo. & echo Введите exit или закройте окно. & cmd /k)
exit /b %RC%

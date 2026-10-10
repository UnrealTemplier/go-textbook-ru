@echo off
call "%~dp0_lib.bat"
set "RC="
rem Что браузер нарисовал на каждой странице (формулы, диаграммы, ошибки JS), Firefox
%PY% engine\tools\runtime_projection.py dist --out "%TEMP%\go-textbook-runtime.json" && echo Отчёт: %TEMP%\go-textbook-runtime.json
if not defined RC set "RC=%ERRORLEVEL%"
rem Двойной щелчок: окно остаётся открытым, пока его не закроет пользователь (cmd /k вместо pause)
if not defined NOPAUSE echo %CMDCMDLINE% | find /i " /c" >nul && (echo. & echo Введите exit или закройте окно. & cmd /k)
exit /b %RC%

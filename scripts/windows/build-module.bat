@echo off
call "%~dp0_lib.bat"
set "RC="
rem Сборка одного модуля (номер — аргументом или по запросу)
set "V=%~1"
if "%V%"=="" set /p "V=Номер модуля: "
%PY% -m engine.build --module %V%
if not defined RC set "RC=%ERRORLEVEL%"
rem Двойной щелчок: окно остаётся открытым, пока его не закроет пользователь (cmd /k вместо pause)
if not defined NOPAUSE echo %CMDCMDLINE% | find /i " /c" >nul && (echo. & echo Введите exit или закройте окно. & cmd /k)
exit /b %RC%

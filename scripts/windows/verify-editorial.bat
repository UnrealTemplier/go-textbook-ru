@echo off
call "%~dp0_lib.bat"
set "RC="
rem Проверка авторской вычитки статьи относительно HEAD (путь — аргументом или по запросу)
set "V=%~1"
if "%V%"=="" set /p "V=Путь к статье (sources/...): "
%PY% book\tools\verify_editorial.py "%V%" --git-ref HEAD
if not defined RC set "RC=%ERRORLEVEL%"
rem Двойной щелчок: окно остаётся открытым, пока его не закроет пользователь (cmd /k вместо pause)
if not defined NOPAUSE echo %CMDCMDLINE% | find /i " /c" >nul && (echo. & echo Введите exit или закройте окно. & cmd /k)
exit /b %RC%

@echo off
call "%~dp0_lib.bat"
set "RC="
rem Проверка авторской вычитки статьи относительно HEAD (путь — аргументом или по запросу)
set "V=%~1"
if "%V%"=="" set /p "V=Путь к статье (sources/...): "
%PY% book\tools\verify_editorial.py "%V%" --git-ref HEAD
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

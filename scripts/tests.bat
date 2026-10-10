@echo off
call "%~dp0_lib.bat"
set "RC="
rem Тесты ядра и книжные тесты (после пересборки dist/)
%PY% -m unittest discover -s engine/tests -t . && %PY% -m unittest discover -s book/tests
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

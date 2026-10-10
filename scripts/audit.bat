@echo off
call "%~dp0_lib.bat"
set "RC="
rem Аудит dist/: ссылки, якоря, имена файлов, ассеты, offline, диаграммы
%PY% -m engine.audit %*
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

@echo off
call "%~dp0_lib.bat"
set "RC="
rem Чистая пересборка: удалить dist/ и собрать заново (убирает страницы-сироты)
if exist dist rmdir /s /q dist
%PY% -m engine.build --all %*
if not defined RC set "RC=%ERRORLEVEL%"
if not defined NOPAUSE pause
exit /b %RC%

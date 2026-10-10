@echo off
call "%~dp0_lib.bat"
set "RC="
rem Полный аудит: --strict и рантайм KaTeX/Mermaid в Firefox (несколько минут)
%PY% -m engine.audit --strict --katex-runtime %*
if not defined RC set "RC=%ERRORLEVEL%"
rem Двойной щелчок: окно остаётся открытым, пока его не закроет пользователь (cmd /k вместо pause)
if not defined NOPAUSE echo %CMDCMDLINE% | find /i " /c" >nul && (echo. & echo Введите exit или закройте окно. & cmd /k)
exit /b %RC%

@echo off
rem scripts\_lib.bat - common part: repository root and Python interpreter.
chcp 65001 >nul
cd /d "%~dp0.."
where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
if not defined ENGINE_DIR set "ENGINE_DIR=..\html-textbook-engine"

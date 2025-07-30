@echo off
chcp 65001 >nul

echo ========================================
echo PC Manufacturing Dashboard
echo ========================================

set "BASEDIR=%~dp0"
echo Execution Folder: %BASEDIR%

if exist "%BASEDIR%python-embedded\python.exe" (
    echo Using Embeddable-Python environment
    set "PYTHON_EXE=%BASEDIR%python-embedded\python.exe"
    
    set "TCL_LIBRARY=%BASEDIR%python-embedded\tcl\tcl8.6"
    set "TK_LIBRARY=%BASEDIR%python-embedded\tk"
    set "PATH=%BASEDIR%python-embedded;%BASEDIR%python-embedded\Scripts;%PATH%"
) else (
    echo Using System Python environment
    set "PYTHON_EXE=python"
)

cd /d "%BASEDIR%"

echo Starting PC Manufacturing Dashboard...
echo Data integration and dashboard startup
echo Dashboard URL: http://localhost:8502
echo Press Ctrl+C to stop
echo ------------------------------------------------------------
"%PYTHON_EXE%" app\main.py

echo.
echo Program finished
pause
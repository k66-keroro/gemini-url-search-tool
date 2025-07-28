@echo off
setlocal

REM PC製造専用ダッシュボード起動スクリプト
echo ========================================
echo 🏭 PC製造専用ダッシュボード
echo ========================================

REM スクリプトのあるフォルダを取得
set "BASEDIR=%~dp0"
echo 📁 実行フォルダ: %BASEDIR%

REM Python実行環境の確認
if exist "%BASEDIR%python-embedded\python.exe" (
    echo ✅ Embeddable-Python環境を使用
    set "PYTHON_EXE=%BASEDIR%python-embedded\python.exe"
    
    REM 環境変数の設定
    set "TCL_LIBRARY=%BASEDIR%python-embedded\tcl\tcl8.6"
    set "TK_LIBRARY=%BASEDIR%python-embedded\tk"
    set "PATH=%BASEDIR%python-embedded;%BASEDIR%python-embedded\Scripts;%PATH%"
) else (
    echo ⚠️ システムPython環境を使用
    set "PYTHON_EXE=python"
)

REM 作業ディレクトリを設定
cd /d "%BASEDIR%"

REM メインプログラムの実行
echo 🚀 プログラムを起動中...
"%PYTHON_EXE%" app\main.py

echo.
echo 👋 プログラムが終了しました
pause
endlocal
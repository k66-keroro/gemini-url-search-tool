@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Gemini URL Search Tool - Starting...
echo.

REM 仮想環境の確認
if exist "venv" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Creating...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM .envファイルの確認
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env >nul
    echo.
    echo Please edit .env file and add your GEMINI_API_KEY
    echo Then run this script again.
    pause
    exit /b 1
)

REM アプリケーション起動
echo Starting Advanced Gemini URL Search Tool with Quality Filter...
echo Open your browser and go to: http://localhost:8512
echo.
streamlit run advanced_search_with_cache.py --server.port 8512
pause
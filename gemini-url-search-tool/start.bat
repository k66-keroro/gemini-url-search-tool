@echo off
echo Gemini URL Search Tool - Starting...
echo.

REM 仮想環境の確認
if exist "venv\Scripts\activate.bat" (
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
    copy .env.example .env
    echo.
    echo Please edit .env file and add your GEMINI_API_KEY
    echo Then run this script again.
    pause
    exit /b
)

REM アプリケーション起動
echo Starting Smart Overview Detail Tool...
echo Open your browser and go to: http://localhost:8510
echo.
streamlit run smart_overview_detail.py --server.port 8510

pause
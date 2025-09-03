#!/bin/bash

echo "Gemini URL Search Tool - Starting..."
echo

# 仮想環境の確認
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# .envファイルの確認
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo
    echo "Please edit .env file and add your GEMINI_API_KEY"
    echo "Then run this script again."
    read -p "Press any key to continue..."
    exit 1
fi

# アプリケーション起動
echo "Starting Smart Overview Detail Tool..."
echo "Open your browser and go to: http://localhost:8510"
echo
streamlit run smart_overview_detail.py --server.port 8510
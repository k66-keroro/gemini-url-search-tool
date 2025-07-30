#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接ダッシュボードを起動するスクリプト
"""

import subprocess
import sys
import os
from pathlib import Path

def start_dashboard():
    """ダッシュボードを直接起動"""
    print("🚀 PC製造専用ダッシュボードを起動中...")
    print("📊 ブラウザが自動で開きます")
    print("🔗 手動でアクセスする場合: http://localhost:8506")
    print("⏹️  停止するには Ctrl+C を押してください")
    print("-" * 60)
    
    try:
        # 作業ディレクトリを設定
        os.chdir(Path(__file__).parent)
        
        # Streamlitを起動
        cmd = [sys.executable, "-m", "streamlit", "run", "app/dashboard.py", "--server.port", "8506"]
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n⏹️  ダッシュボードを停止しました")
    except Exception as e:
        print(f"❌ ダッシュボード起動エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    start_dashboard()
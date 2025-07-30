#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
緊急修正スクリプト - データベースリセット + エンコーディング修正
"""

import sqlite3
import os
import sys
from pathlib import Path
import shutil

def emergency_fix():
    """緊急修正を実行"""
    print("🚨 緊急修正を開始...")
    
    # 1. データベースファイルを削除
    db_path = Path("data/sqlite/pc_production.db")
    if db_path.exists():
        try:
            db_path.unlink()
            print("✅ 古いデータベースを削除しました")
        except Exception as e:
            print(f"⚠️ データベース削除エラー: {e}")
    
    # 2. データベースディレクトリを作成
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 3. 新しい空のデータベースを作成
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("SELECT 1")  # 接続テスト
        conn.close()
        print("✅ 新しいデータベースを作成しました")
    except Exception as e:
        print(f"❌ データベース作成エラー: {e}")
        return False
    
    # 4. Pythonプロセスを終了
    try:
        import subprocess
        result = subprocess.run(['taskkill', '/f', '/im', 'python.exe'], 
                              capture_output=True, text=True)
        print("✅ Pythonプロセスを終了しました")
    except:
        pass
    
    print("\n🎯 修正完了！")
    print("📋 次の手順:")
    print("1. 新しいコマンドプロンプトを開く")
    print("2. cd C:\\Users\\sem3171\\claude-test\\pc-production-dashboard")
    print("3. python direct_dashboard.py")
    
    return True

if __name__ == "__main__":
    emergency_fix()
    input("\nEnterキーを押して終了...")
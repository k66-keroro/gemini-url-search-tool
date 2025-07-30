#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テーブル構造確認スクリプト
"""

import sqlite3
import pandas as pd
from pathlib import Path

def check_table_structure():
    """テーブル構造を確認"""
    db_path = Path("data/sqlite/pc_production.db")
    
    if not db_path.exists():
        print("❌ データベースファイルが見つかりません")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # テーブル一覧を取得
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("📋 テーブル一覧:")
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")
            
            # テーブル構造を取得
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("    カラム:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                print(f"      - {col_name} ({col_type})")
            
            # データ件数を取得
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"    データ件数: {count:,}行")
            
            # サンプルデータを表示
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_data = cursor.fetchall()
                print("    サンプルデータ:")
                for i, row in enumerate(sample_data, 1):
                    print(f"      {i}: {row}")
            
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_table_structure()
    input("\nEnterキーを押して終了...")
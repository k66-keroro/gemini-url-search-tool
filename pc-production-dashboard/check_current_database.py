"""
現在のデータベース内容を詳細確認
"""

import sqlite3
import pandas as pd
from pathlib import Path

def check_current_database():
    """現在のデータベース内容を確認"""
    print("=" * 60)
    print("現在のデータベース内容確認")
    print("=" * 60)
    
    db_path = Path("pc-production-dashboard/data/sqlite/pc_production.db")
    
    if not db_path.exists():
        print(f"❌ データベースが見つかりません: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # テーブル一覧
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📊 テーブル一覧:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # pc_production_zm29テーブルの詳細
        if ('pc_production_zm29',) in tables:
            print(f"\n📋 pc_production_zm29テーブル:")
            
            # カラム情報
            cursor.execute("PRAGMA table_info(pc_production_zm29)")
            columns = cursor.fetchall()
            print(f"  カラム一覧:")
            for col in columns:
                print(f"    {col[1]} ({col[2]})")
            
            # データ件数
            cursor.execute("SELECT COUNT(*) FROM pc_production_zm29")
            count = cursor.fetchone()[0]
            print(f"  総件数: {count}行")
            
            # 数値データの確認
            numeric_checks = [
                ("完成数", "SELECT COUNT(*), MIN(完成数), MAX(完成数), AVG(完成数) FROM pc_production_zm29 WHERE 完成数 > 0"),
                ("単価", "SELECT COUNT(*), MIN(単価), MAX(単価), AVG(単価) FROM pc_production_zm29 WHERE 単価 > 0"),
                ("金額", "SELECT COUNT(*), MIN(金額), MAX(金額), AVG(金額) FROM pc_production_zm29 WHERE 金額 > 0")
            ]
            
            for col_name, query in numeric_checks:
                try:
                    cursor.execute(query)
                    stats = cursor.fetchone()
                    if stats and stats[0] > 0:
                        print(f"  {col_name}: 件数={stats[0]}, 最小={stats[1]}, 最大={stats[2]}, 平均={stats[3]:.2f}")
                    else:
                        print(f"  {col_name}: データなし")
                except Exception as e:
                    print(f"  {col_name}: エラー - {e}")
            
            # サンプルデータ
            print(f"\n📝 サンプルデータ（最初の3行）:")
            try:
                df = pd.read_sql_query("SELECT * FROM pc_production_zm29 LIMIT 3", conn)
                print(df.to_string())
            except Exception as e:
                print(f"サンプルデータ取得エラー: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ データベース確認エラー: {e}")

def main():
    check_current_database()

if __name__ == "__main__":
    main()
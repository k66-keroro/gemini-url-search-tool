"""
データベースをリセットして新しい構造で作り直し
"""

import sqlite3
from pathlib import Path

def reset_database():
    """データベースをリセット"""
    print("=" * 60)
    print("データベースリセット")
    print("=" * 60)
    
    db_path = Path("pc-production-dashboard/data/sqlite/pc_production.db")
    
    if not db_path.exists():
        print(f"❌ データベースが見つかりません: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 既存テーブルを削除
        cursor.execute("DROP TABLE IF EXISTS pc_production_zm29")
        print("✅ 既存テーブルを削除しました")
        
        # テーブル一覧を確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📊 残りのテーブル: {[table[0] for table in tables]}")
        
        conn.commit()
        conn.close()
        
        print("✅ データベースリセット完了")
        print("💡 次にシンプル版データローダーを実行してください")
        
    except Exception as e:
        print(f"❌ データベースリセットエラー: {e}")

def main():
    reset_database()

if __name__ == "__main__":
    main()
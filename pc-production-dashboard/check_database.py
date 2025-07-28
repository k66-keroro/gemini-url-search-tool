"""
PC製造専用ダッシュボード - データベース内容確認

統合されたデータの詳細を確認
"""

import sqlite3
import pandas as pd
from pathlib import Path

def check_database_content():
    """データベース内容の確認"""
    print("=" * 60)
    print("PC製造データベース内容確認")
    print("=" * 60)
    
    # データベースパス
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
        
        # pc_production_zm29テーブルの詳細確認
        if ('pc_production_zm29',) in tables:
            print(f"\n📋 pc_production_zm29テーブル詳細:")
            
            # カラム情報
            cursor.execute("PRAGMA table_info(pc_production_zm29)")
            columns = cursor.fetchall()
            print(f"  カラム数: {len(columns)}")
            for col in columns:
                print(f"    {col[1]} ({col[2]})")
            
            # データ件数
            cursor.execute("SELECT COUNT(*) FROM pc_production_zm29")
            count = cursor.fetchone()[0]
            print(f"  総件数: {count}行")
            
            # サンプルデータ（最初の3行）
            df = pd.read_sql_query("SELECT * FROM pc_production_zm29 LIMIT 3", conn)
            print(f"\n📝 サンプルデータ（最初の3行）:")
            print(df.to_string())
            
            # 数値カラムの統計
            numeric_columns = ['完成数', '単価', '金額', '計画数']
            for col in numeric_columns:
                if col in df.columns:
                    cursor.execute(f"SELECT MIN({col}), MAX({col}), AVG({col}), COUNT(*) FROM pc_production_zm29 WHERE {col} IS NOT NULL AND {col} != ''")
                    stats = cursor.fetchone()
                    if stats and stats[3] > 0:  # データが存在する場合
                        print(f"  {col}: 最小={stats[0]}, 最大={stats[1]}, 平均={stats[2]:.2f}, 件数={stats[3]}")
                    else:
                        print(f"  {col}: データなし")
            
            # MRP管理者別集計
            cursor.execute("SELECT MRP管理者, COUNT(*) FROM pc_production_zm29 GROUP BY MRP管理者")
            mrp_stats = cursor.fetchall()
            print(f"\n👥 MRP管理者別件数:")
            for mrp, count in mrp_stats:
                print(f"  {mrp}: {count}件")
            
            # データソース別集計
            cursor.execute("SELECT データソース, COUNT(*) FROM pc_production_zm29 GROUP BY データソース")
            source_stats = cursor.fetchall()
            print(f"\n📂 データソース別件数:")
            for source, count in source_stats:
                print(f"  {source}: {count}件")
            
            # 完成数・金額の分布確認
            print(f"\n💰 完成数・金額の分布:")
            cursor.execute("""
                SELECT 
                    COUNT(*) as 総件数,
                    COUNT(CASE WHEN 完成数 > 0 THEN 1 END) as 完成数有り,
                    COUNT(CASE WHEN 金額 > 0 THEN 1 END) as 金額有り,
                    COUNT(CASE WHEN 完成数 > 0 AND 金額 > 0 THEN 1 END) as 両方有り
                FROM pc_production_zm29
            """)
            dist_stats = cursor.fetchone()
            print(f"  総件数: {dist_stats[0]}")
            print(f"  完成数 > 0: {dist_stats[1]}件")
            print(f"  金額 > 0: {dist_stats[2]}件")
            print(f"  完成数・金額両方 > 0: {dist_stats[3]}件")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ データベース確認エラー: {e}")

def check_kansei_jisseki_structure():
    """KANSEI_JISSEKIの構造確認"""
    print(f"\n" + "=" * 60)
    print("KANSEI_JISSEKI構造確認")
    print("=" * 60)
    
    kansei_file = Path("pc-production-dashboard/data/current/KANSEI_JISSEKI.txt")
    
    if not kansei_file.exists():
        print(f"❌ KANSEI_JISSEKIファイルが見つかりません: {kansei_file}")
        return
    
    try:
        # ファイルの最初の数行を確認
        with open(kansei_file, 'r', encoding='shift_jis') as f:
            lines = f.readlines()[:10]  # 最初の10行
        
        print(f"📄 KANSEI_JISSEKI.txt 構造:")
        print(f"  ファイルサイズ: {kansei_file.stat().st_size} bytes")
        print(f"  総行数: {len(lines)}行（サンプル）")
        
        if lines:
            # ヘッダー行（1行目）
            header = lines[0].strip().split('\t')
            print(f"  カラム数: {len(header)}")
            print(f"  カラム名:")
            for i, col in enumerate(header):
                print(f"    {i+1:2d}. {col}")
            
            # データ行（2行目）のサンプル
            if len(lines) > 1:
                data_row = lines[1].strip().split('\t')
                print(f"\n📝 データサンプル（2行目）:")
                for i, (col, val) in enumerate(zip(header, data_row)):
                    print(f"    {col}: {val}")
        
    except Exception as e:
        print(f"❌ KANSEI_JISSEKI確認エラー: {e}")

def main():
    """メイン実行"""
    check_database_content()
    check_kansei_jisseki_structure()
    
    print(f"\n" + "=" * 60)
    print("🔍 問題の特定")
    print("=" * 60)
    print("1. データベースに数値データが正しく保存されているか確認")
    print("2. KANSEI_JISSEKIの実際のカラム構造を確認")
    print("3. 変換処理で数値が文字列として保存されていないか確認")
    print("4. ダッシュボードの数値変換処理を確認")

if __name__ == "__main__":
    main()
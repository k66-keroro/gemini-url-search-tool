"""
データの不整合問題を調査するスクリプト
"""

import sqlite3
import pandas as pd
from pathlib import Path

def debug_data_inconsistency():
    """データの不整合を調査"""
    print("=" * 60)
    print("データ不整合調査")
    print("=" * 60)
    
    db_path = Path('data/sqlite/pc_production.db')
    
    if not db_path.exists():
        print(f"❌ データベースが見つかりません: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    
    # 1. 指図番号50119856の詳細調査
    print("1. 指図番号50119856の詳細調査")
    query1 = """
    SELECT 
        転記日付,
        ネットワーク・指図番号,
        品目コード,
        品目テキスト,
        完成数,
        金額,
        データソース,
        MRP管理者
    FROM pc_production_zm29
    WHERE ネットワーク・指図番号 LIKE '%50119856%'
    ORDER BY 転記日付, データソース
    """
    
    df1 = pd.read_sql_query(query1, conn)
    print(f"指図番号50119856の件数: {len(df1)}件")
    if not df1.empty:
        print(df1.to_string())
    
    print("\n" + "="*60)
    
    # 2. 7月2日のデータ調査
    print("2. 7月2日のデータ調査")
    query2 = """
    SELECT 
        転記日付,
        COUNT(*) as 件数,
        SUM(完成数) as 完成数合計,
        SUM(金額) as 金額合計,
        データソース
    FROM pc_production_zm29
    WHERE 転記日付 LIKE '2025-07-02%'
    GROUP BY 転記日付, データソース
    ORDER BY 転記日付, データソース
    """
    
    df2 = pd.read_sql_query(query2, conn)
    print(f"7月2日のデータ:")
    if not df2.empty:
        print(df2.to_string())
    else:
        print("7月2日のデータが見つかりません")
    
    print("\n" + "="*60)
    
    # 3. 7月10日のデータ調査
    print("3. 7月10日のデータ調査")
    query3 = """
    SELECT 
        転記日付,
        COUNT(*) as 件数,
        SUM(完成数) as 完成数合計,
        SUM(金額) as 金額合計,
        データソース
    FROM pc_production_zm29
    WHERE 転記日付 LIKE '2025-07-10%'
    GROUP BY 転記日付, データソース
    ORDER BY 転記日付, データソース
    """
    
    df3 = pd.read_sql_query(query3, conn)
    print(f"7月10日のデータ:")
    if not df3.empty:
        print(df3.to_string())
    else:
        print("7月10日のデータが見つかりません")
    
    print("\n" + "="*60)
    
    # 4. 全体の金額・数量集計
    print("4. 全体の金額・数量集計")
    query4 = """
    SELECT 
        データソース,
        COUNT(*) as 件数,
        COUNT(DISTINCT ネットワーク・指図番号) as 品目数,
        SUM(完成数) as 完成数合計,
        SUM(金額) as 金額合計
    FROM pc_production_zm29
    WHERE MRP管理者 LIKE 'PC%'
    GROUP BY データソース
    ORDER BY データソース
    """
    
    df4 = pd.read_sql_query(query4, conn)
    print("データソース別集計:")
    if not df4.empty:
        for _, row in df4.iterrows():
            print(f"  {row['データソース']}:")
            print(f"    件数: {row['件数']:,}")
            print(f"    品目数: {row['品目数']:,}")
            print(f"    完成数合計: {row['完成数合計']:,.0f}")
            print(f"    金額合計: {row['金額合計']:,.0f}")
    
    print("\n" + "="*60)
    
    # 5. 昨日までの集計（7月28日まで）
    print("5. 昨日まで（7月28日まで）の集計")
    query5 = """
    SELECT 
        COUNT(*) as 件数,
        COUNT(DISTINCT ネットワーク・指図番号) as 品目数,
        SUM(完成数) as 完成数合計,
        SUM(金額) as 金額合計
    FROM pc_production_zm29
    WHERE MRP管理者 LIKE 'PC%'
    AND 転記日付 <= '2025-07-28'
    """
    
    df5 = pd.read_sql_query(query5, conn)
    print("昨日までの集計:")
    if not df5.empty:
        row = df5.iloc[0]
        print(f"  件数: {row['件数']:,}")
        print(f"  品目数: {row['品目数']:,}")
        print(f"  完成数合計: {row['完成数合計']:,.0f}")
        print(f"  金額合計: {row['金額合計']:,.0f}")
        print(f"  金額合計(M): {row['金額合計']/1_000_000:.1f}M")
    
    conn.close()

if __name__ == "__main__":
    debug_data_inconsistency()
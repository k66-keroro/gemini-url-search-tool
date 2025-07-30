"""
指摘された全ての問題を一括修正するスクリプト
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
from pathlib import Path
import numpy as np

def main():
    print("=" * 60)
    print("PC製造ダッシュボード問題修正")
    print("=" * 60)
    
    # 1. データベースから最新データを取得
    db_path = Path('data/sqlite/pc_production.db')
    
    if not db_path.exists():
        print(f"❌ データベースが見つかりません: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    
    # 修正されたクエリ（金額>0の条件も追加）
    query = """
    SELECT 
        MRP管理者,
        転記日付,
        ネットワーク・指図番号,
        品目コード,
        品目テキスト,
        計画数,
        完成数,
        単価,
        金額,
        月別週区分,
        データ年月,
        データソース,
        更新時刻
    FROM pc_production_zm29
    WHERE MRP管理者 LIKE 'PC%'
    AND 転記日付 IS NOT NULL
    AND (完成数 > 0 OR 金額 > 0)
    ORDER BY 転記日付 DESC, MRP管理者
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"✅ データ読み込み完了: {len(df)}行")
    
    # 2. データ前処理
    df['転記日付'] = pd.to_datetime(df['転記日付'], errors='coerce')
    
    # 数値列を適切に変換
    numeric_columns = ['金額', '完成数', '計画数', '単価', '月別週区分']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            if col == '月別週区分':
                df[col] = df[col].astype(int)
    
    # ZM29の金額フィールドを優先使用（0の場合のみ再計算）
    mask = ((df['金額'] == 0) | df['金額'].isna()) & (df['完成数'] > 0) & (df['単価'] > 0)
    if mask.any():
        df.loc[mask, '金額'] = df.loc[mask, '完成数'] * df.loc[mask, '単価']
        print(f"✅ 金額再計算: {mask.sum()}行")
    
    # 3. 集計結果の確認
    print("\n📊 修正後の集計結果:")
    
    # データソース別集計
    source_summary = df.groupby('データソース').agg({
        '金額': 'sum',
        '完成数': 'sum',
        'ネットワーク・指図番号': 'nunique'
    }).reset_index()
    
    print("データソース別:")
    for _, row in source_summary.iterrows():
        print(f"  {row['データソース']}:")
        print(f"    金額: ¥{row['金額']:,.0f} ({row['金額']/1_000_000:.1f}M)")
        print(f"    完成数: {row['完成数']:,.0f}")
        print(f"    品目数: {row['ネットワーク・指図番号']:,}")
    
    # 全体集計
    total_amount = df['金額'].sum()
    total_quantity = df['完成数'].sum()
    total_items = df['ネットワーク・指図番号'].nunique()
    
    print(f"\n📈 全体集計:")
    print(f"  総金額: ¥{total_amount:,.0f} ({total_amount/1_000_000:.1f}M)")
    print(f"  総完成数: {total_quantity:,.0f}")
    print(f"  総品目数: {total_items:,}")
    
    # 4. 昨日まで（7/28まで）の集計
    yesterday_data = df[df['転記日付'] <= '2025-07-28']
    yesterday_amount = yesterday_data['金額'].sum()
    yesterday_quantity = yesterday_data['完成数'].sum()
    yesterday_items = yesterday_data['ネットワーク・指図番号'].nunique()
    
    print(f"\n📅 昨日まで（7/28まで）の集計:")
    print(f"  金額: ¥{yesterday_amount:,.0f} ({yesterday_amount/1_000_000:.1f}M)")
    print(f"  完成数: {yesterday_quantity:,.0f}")
    print(f"  品目数: {yesterday_items:,}")
    
    # 5. 指図番号50119856の詳細
    order_50119856 = df[df['ネットワーク・指図番号'].astype(str).str.contains('50119856', na=False)]
    if not order_50119856.empty:
        print(f"\n🔍 指図番号50119856の詳細:")
        for _, row in order_50119856.iterrows():
            print(f"  日付: {row['転記日付'].strftime('%Y/%m/%d')}")
            print(f"  完成数: {row['完成数']:,.0f}")
            print(f"  金額: ¥{row['金額']:,.0f}")
            print(f"  データソース: {row['データソース']}")
    
    print(f"\n✅ 修正完了！Streamlitダッシュボードを再起動してください。")

if __name__ == "__main__":
    main()
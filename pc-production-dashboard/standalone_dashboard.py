#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立したダッシュボード起動スクリプト
"""

import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# ページ設定
st.set_page_config(
    page_title="PC製造専用ダッシュボード",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_data():
    """データベースからデータを読み込み"""
    db_path = Path("data/sqlite/pc_production.db")
    
    if not db_path.exists():
        st.error("データベースファイルが見つかりません。データ統合を先に実行してください。")
        return pd.DataFrame()
    
    try:
        conn = sqlite3.connect(str(db_path))
        
        # テーブル一覧を取得
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        if not tables:
            st.error("データテーブルが見つかりません。")
            return pd.DataFrame()
        
        # 最初のテーブルを使用
        table_name = tables[0]
        st.info(f"使用テーブル: {table_name}")
        
        # テーブル構造を確認
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        available_columns = [col[1] for col in columns_info]
        
        st.sidebar.write("📋 利用可能なカラム:")
        for col in available_columns:
            st.sidebar.write(f"  - {col}")
        
        # データ読み込み
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            st.warning("データが見つかりません。")
            return df
        
        # 日付カラムの変換（可能な場合）
        date_columns = ['転記日', '完成日', '日付', 'date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
        
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame()

def main():
    """メイン処理"""
    st.title("🏭 PC製造専用ダッシュボード")
    
    # データ読み込み
    with st.spinner("データを読み込み中..."):
        df = load_data()
    
    if df.empty:
        st.stop()
    
    # サイドバー
    st.sidebar.header("📊 フィルター設定")
    
    # 日付範囲フィルター
    min_date = df['完成日'].min().date()
    max_date = df['完成日'].max().date()
    
    date_range = st.sidebar.date_input(
        "期間選択",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_filtered = df[
            (df['完成日'].dt.date >= start_date) & 
            (df['完成日'].dt.date <= end_date)
        ]
    else:
        df_filtered = df
    
    # MRP管理者フィルター
    if 'MRP管理者' in df_filtered.columns:
        mrp_managers = ['全て'] + sorted(df_filtered['MRP管理者'].dropna().unique().tolist())
        selected_mrp = st.sidebar.selectbox("MRP管理者", mrp_managers)
        
        if selected_mrp != '全て':
            df_filtered = df_filtered[df_filtered['MRP管理者'] == selected_mrp]
    
    # メトリクス表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_amount = df_filtered['生産金額'].sum()
        st.metric(
            "総生産金額",
            f"¥{total_amount:,.0f}",
            f"({total_amount/1000000:.1f}M)"
        )
    
    with col2:
        total_items = df_filtered['品目コード'].nunique()
        st.metric("品目数", f"{total_items:,}品目")
    
    with col3:
        total_records = len(df_filtered)
        st.metric("レコード数", f"{total_records:,}件")
    
    with col4:
        if not df_filtered.empty:
            period_days = (df_filtered['完成日'].max() - df_filtered['完成日'].min()).days + 1
            st.metric("期間", f"{period_days}日")
    
    # グラフ表示
    if not df_filtered.empty:
        st.subheader("📈 日別生産金額推移")
        
        # 日別集計
        daily_summary = df_filtered.groupby([
            df_filtered['完成日'].dt.date,
            'MRP管理者' if 'MRP管理者' in df_filtered.columns else None
        ])['生産金額'].sum().reset_index()
        
        if 'MRP管理者' in daily_summary.columns:
            fig = px.bar(
                daily_summary,
                x='完成日',
                y='生産金額',
                color='MRP管理者',
                title="日別・MRP管理者別生産金額",
                labels={'生産金額': '生産金額 (円)', '完成日': '完成日'}
            )
        else:
            daily_summary_simple = df_filtered.groupby(
                df_filtered['完成日'].dt.date
            )['生産金額'].sum().reset_index()
            
            fig = px.bar(
                daily_summary_simple,
                x='完成日',
                y='生産金額',
                title="日別生産金額",
                labels={'生産金額': '生産金額 (円)', '完成日': '完成日'}
            )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # データテーブル
        st.subheader("📋 詳細データ")
        
        # 表示列の選択
        display_columns = st.multiselect(
            "表示する列を選択",
            df_filtered.columns.tolist(),
            default=['完成日', '品目コード', 'MRP管理者', '生産金額'][:4] if len(df_filtered.columns) >= 4 else df_filtered.columns.tolist()
        )
        
        if display_columns:
            st.dataframe(
                df_filtered[display_columns].head(1000),
                use_container_width=True
            )
        
        # CSV ダウンロード
        csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSVダウンロード",
            data=csv,
            file_name=f"pc_production_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
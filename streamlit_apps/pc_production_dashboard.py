"""
PC生産実績ダッシュボード - Streamlit版

既存のAccessロジックをStreamlitで再現
- 週単位、日単位での集計
- 明細データの確認
- インタラクティブなダッシュボード
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

# ページ設定
st.set_page_config(
    page_title="PC生産実績ダッシュボード",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .week-header {
        background-color: #e8f4fd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """SQLiteデータベースからデータを読み込み"""
    try:
        # データベースパス
        db_path = Path("data/sqlite/main.db")
        
        if not db_path.exists():
            st.error(f"データベースファイルが見つかりません: {db_path}")
            return None, None
        
        conn = sqlite3.connect(db_path)
        
        # ZM29テーブルからPC生産実績データを取得
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
            CAST(完成数 AS REAL) * CAST(単価 AS REAL) AS 金額
        FROM ZM29
        WHERE MRP管理者 LIKE 'PC%'
        AND 転記日付 IS NOT NULL
        AND 完成数 > 0
        ORDER BY 転記日付, MRP管理者
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            st.warning("PC生産実績データが見つかりません")
            return None, None
        
        # データ前処理
        df['転記日付'] = pd.to_datetime(df['転記日付'], errors='coerce')
        
        # 数値列を適切に変換
        numeric_columns = ['金額', '完成数', '計画数', '単価']
        for col in numeric_columns:
            if col in df.columns:
                # 文字列の場合は数値に変換
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 金額を再計算（念のため）
        if '完成数' in df.columns and '単価' in df.columns:
            df['金額'] = df['完成数'] * df['単価']
        
        # 週区分を計算（月曜日始まり）
        df['年'] = df['転記日付'].dt.year
        df['月'] = df['転記日付'].dt.month
        df['週番号'] = df['転記日付'].dt.isocalendar().week
        df['週区分'] = (df['転記日付'].dt.isocalendar().week % 4 + 1).astype(str)  # 1-4の週区分を文字列として保存
        
        # 曜日情報
        df['曜日'] = df['転記日付'].dt.day_name()
        df['平日フラグ'] = df['転記日付'].dt.weekday < 5  # 0-4が平日
        
        return df, True
        
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return None, None

def create_calendar_data(df):
    """カレンダーデータを作成（週区分付き）"""
    if df is None or df.empty:
        return pd.DataFrame()
    
    # 日付範囲を取得
    start_date = df['転記日付'].min()
    end_date = df['転記日付'].max()
    
    # 日付範囲のDataFrameを作成
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    calendar_df = pd.DataFrame({
        'DateColumn': date_range,
        '週区分': ((date_range.isocalendar().week % 4) + 1).astype(str),  # 文字列として保存
        '曜日': date_range.day_name(),
        '平日フラグ': date_range.weekday < 5
    })
    
    return calendar_df

def aggregate_daily_data(df):
    """日別集計データを作成"""
    if df is None or df.empty:
        return pd.DataFrame()
    
    # 金額列が数値型であることを確認
    df = df.copy()
    df['金額'] = pd.to_numeric(df['金額'], errors='coerce').fillna(0)
    
    # MRP管理者別の日別集計
    daily_pivot = df.pivot_table(
        index=['転記日付', '週区分'],
        columns='MRP管理者',
        values='金額',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    # 週区分を文字列型に明示的に変換（Arrowエラー対策）
    daily_pivot['週区分'] = daily_pivot['週区分'].astype(str)
    
    # 日別合計を追加
    mrp_columns = [col for col in daily_pivot.columns if col.startswith('PC')]
    if mrp_columns:
        daily_pivot['日別金額'] = daily_pivot[mrp_columns].sum(axis=1)
    else:
        daily_pivot['日別金額'] = 0
    
    # 数値列を明示的に数値型に変換
    for col in mrp_columns + ['日別金額']:
        if col in daily_pivot.columns:
            daily_pivot[col] = pd.to_numeric(daily_pivot[col], errors='coerce').fillna(0)
    
    return daily_pivot

def aggregate_weekly_data(df):
    """週別集計データを作成"""
    if df is None or df.empty:
        return pd.DataFrame()
    
    # 金額列が数値型であることを確認
    df = df.copy()
    df['金額'] = pd.to_numeric(df['金額'], errors='coerce').fillna(0)
    
    # MRP管理者別の週別集計
    weekly_pivot = df.pivot_table(
        index='週区分',
        columns='MRP管理者',
        values='金額',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    # 週別合計を追加
    mrp_columns = [col for col in weekly_pivot.columns if col.startswith('PC')]
    if mrp_columns:
        weekly_pivot['合計'] = weekly_pivot[mrp_columns].sum(axis=1)
    else:
        weekly_pivot['合計'] = 0
    
    # 週区分を文字列型に明示的に変換（Arrowエラー対策）
    weekly_pivot['週区分'] = weekly_pivot['週区分'].astype(str)
    
    # 数値列を明示的に数値型に変換
    for col in mrp_columns + ['合計']:
        if col in weekly_pivot.columns:
            weekly_pivot[col] = pd.to_numeric(weekly_pivot[col], errors='coerce').fillna(0)
    
    # 総合計行を追加
    if not weekly_pivot.empty:
        total_row = {}
        total_row['週区分'] = '合計'
        for col in mrp_columns + ['合計']:
            if col in weekly_pivot.columns:
                total_row[col] = weekly_pivot[col].sum()
        
        total_df = pd.DataFrame([total_row])
        # 週区分を文字列型に変換
        total_df['週区分'] = total_df['週区分'].astype(str)
        weekly_pivot = pd.concat([weekly_pivot, total_df], ignore_index=True)
    
    return weekly_pivot

def main():
    """メイン関数"""
    
    # ヘッダー
    st.markdown('<h1 class="main-header">📊 PC生産実績ダッシュボード</h1>', unsafe_allow_html=True)
    
    # データ読み込み
    with st.spinner('データを読み込み中...'):
        df, success = load_data()
    
    if not success or df is None:
        st.stop()
    
    # サイドバー - フィルター
    st.sidebar.header("🔍 フィルター")
    
    # 日付範囲選択
    date_range = st.sidebar.date_input(
        "日付範囲を選択",
        value=(df['転記日付'].min().date(), df['転記日付'].max().date()),
        min_value=df['転記日付'].min().date(),
        max_value=df['転記日付'].max().date()
    )
    
    # MRP管理者選択
    mrp_managers = sorted(df['MRP管理者'].unique())
    selected_mrp = st.sidebar.multiselect(
        "MRP管理者を選択",
        mrp_managers,
        default=mrp_managers
    )
    
    # データフィルタリング
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (df['転記日付'].dt.date >= start_date) & (df['転記日付'].dt.date <= end_date)
        df_filtered = df[mask]
    else:
        df_filtered = df.copy()
    
    if selected_mrp:
        df_filtered = df_filtered[df_filtered['MRP管理者'].isin(selected_mrp)]
    
    # 集計データ作成
    daily_data = aggregate_daily_data(df_filtered)
    weekly_data = aggregate_weekly_data(df_filtered)
    
    # メトリクス表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_amount = df_filtered['金額'].sum()
        if total_amount >= 1_000_000:
            st.metric("総生産金額", f"¥{total_amount/1_000_000:.1f}M")
        else:
            st.metric("総生産金額", f"¥{total_amount:,.0f}")
    
    with col2:
        total_quantity = df_filtered['完成数'].sum()
        if total_quantity >= 1000:
            st.metric("総完成数", f"{total_quantity/1000:.1f}K")
        else:
            st.metric("総完成数", f"{total_quantity:,.0f}")
    
    with col3:
        unique_items = df_filtered['品目コード'].nunique()
        st.metric("品目数", f"{unique_items:,}")
    
    with col4:
        production_days = df_filtered['転記日付'].nunique()
        st.metric("生産日数", f"{production_days}")
    
    # タブ作成
    tab1, tab2, tab3, tab4 = st.tabs(["📈 週別集計", "📅 日別集計", "📋 明細データ", "📊 分析"])
    
    with tab1:
        st.subheader("週別生産実績")
        
        if not weekly_data.empty:
            # 週別集計テーブル
            # 数値列のフォーマット用辞書を作成
            format_dict = {}
            for col in weekly_data.columns:
                if col != '週区分' and pd.api.types.is_numeric_dtype(weekly_data[col]):
                    format_dict[col] = "¥{:,.0f}"
            
            # データ型を明示的に設定してArrowエラーを回避
            display_weekly = weekly_data.copy()
            display_weekly['週区分'] = display_weekly['週区分'].astype(str)
            
            if format_dict:
                st.dataframe(
                    display_weekly.style.format(format_dict),
                    use_container_width=True
                )
            else:
                st.dataframe(display_weekly, use_container_width=True)
            
            # 週別グラフ
            if len(weekly_data) > 1:  # 合計行を除く
                weekly_chart_data = weekly_data[weekly_data['週区分'] != '合計']
                
                fig = px.bar(
                    weekly_chart_data.melt(id_vars=['週区分'], 
                                         value_vars=[col for col in weekly_chart_data.columns if col.startswith('PC')],
                                         var_name='MRP管理者', value_name='金額'),
                    x='週区分', y='金額', color='MRP管理者',
                    title="週別生産実績（MRP管理者別）",
                    labels={'金額': '生産金額 (¥)', '週区分': '週区分'}
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("日別生産実績")
        
        if not daily_data.empty:
            # 日別集計テーブル
            # 数値列のフォーマット用辞書を作成
            format_dict = {}
            for col in daily_data.columns:
                if col not in ['転記日付', '週区分'] and pd.api.types.is_numeric_dtype(daily_data[col]):
                    format_dict[col] = "¥{:,.0f}"
            
            # データ型を明示的に設定してArrowエラーを回避
            display_daily = daily_data.copy()
            display_daily['週区分'] = display_daily['週区分'].astype(str)
            
            if format_dict:
                st.dataframe(
                    display_daily.style.format(format_dict),
                    use_container_width=True
                )
            else:
                st.dataframe(display_daily, use_container_width=True)
            
            # 日別トレンドグラフ
            fig = px.line(
                daily_data, x='転記日付', y='日別金額',
                title="日別生産実績トレンド",
                labels={'日別金額': '生産金額 (¥)', '転記日付': '日付'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # MRP管理者別日別推移
            mrp_columns = [col for col in daily_data.columns if col.startswith('PC')]
            if mrp_columns:
                fig2 = go.Figure()
                for mrp in mrp_columns:
                    fig2.add_trace(go.Scatter(
                        x=daily_data['転記日付'],
                        y=daily_data[mrp],
                        mode='lines+markers',
                        name=mrp,
                        line=dict(width=2)
                    ))
                
                fig2.update_layout(
                    title="MRP管理者別日別推移",
                    xaxis_title="日付",
                    yaxis_title="生産金額 (¥)",
                    height=400
                )
                st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        st.subheader("生産実績明細")
        
        # 検索機能
        col1, col2 = st.columns(2)
        with col1:
            search_item = st.text_input("品目コード検索", placeholder="品目コードを入力...")
        with col2:
            search_text = st.text_input("品目テキスト検索", placeholder="品目テキストを入力...")
        
        # 明細データフィルタリング
        detail_df = df_filtered.copy()
        if search_item:
            detail_df = detail_df[detail_df['品目コード'].str.contains(search_item, case=False, na=False)]
        if search_text:
            detail_df = detail_df[detail_df['品目テキスト'].str.contains(search_text, case=False, na=False)]
        
        # 明細データ表示
        if not detail_df.empty:
            st.write(f"表示件数: {len(detail_df):,} 件")
            
            # 表示用データ整形
            display_df = detail_df[[
                '転記日付', 'ネットワーク・指図番号', '品目コード', '品目テキスト',
                '計画数', '完成数', '金額', 'MRP管理者', '週区分'
            ]].copy()
            
            display_df['転記日付'] = display_df['転記日付'].dt.strftime('%Y/%m/%d')
            
            # 数値フォーマット用辞書を作成
            format_dict = {}
            if '金額' in display_df.columns and pd.api.types.is_numeric_dtype(display_df['金額']):
                format_dict['金額'] = "¥{:,.0f}"
            if '計画数' in display_df.columns and pd.api.types.is_numeric_dtype(display_df['計画数']):
                format_dict['計画数'] = "{:,.0f}"
            if '完成数' in display_df.columns and pd.api.types.is_numeric_dtype(display_df['完成数']):
                format_dict['完成数'] = "{:,.0f}"
            
            # データ型を明示的に設定してArrowエラーを回避
            display_df['週区分'] = display_df['週区分'].astype(str)
            
            if format_dict:
                st.dataframe(
                    display_df.style.format(format_dict),
                    use_container_width=True,
                    height=400
                )
            else:
                st.dataframe(display_df, use_container_width=True, height=400)
            
            # CSV出力
            csv = detail_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 明細データをCSVでダウンロード",
                data=csv,
                file_name=f"pc_production_detail_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("条件に一致するデータがありません")
    
    with tab4:
        st.subheader("生産分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # MRP管理者別構成比
            mrp_summary = df_filtered.groupby('MRP管理者')['金額'].sum().reset_index()
            fig_pie = px.pie(
                mrp_summary, values='金額', names='MRP管理者',
                title="MRP管理者別生産金額構成比"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # 上位品目
            top_items = df_filtered.groupby(['品目コード', '品目テキスト'])['金額'].sum().reset_index()
            top_items = top_items.nlargest(10, '金額')
            
            fig_bar = px.bar(
                top_items, x='金額', y='品目コード',
                orientation='h',
                title="生産金額上位10品目",
                labels={'金額': '生産金額 (¥)', '品目コード': '品目コード'}
            )
            fig_bar.update_layout(height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # 週別・MRP管理者別ヒートマップ
        if not weekly_data.empty:
            heatmap_data = weekly_data[weekly_data['週区分'] != '合計'].set_index('週区分')
            mrp_cols = [col for col in heatmap_data.columns if col.startswith('PC')]
            
            if mrp_cols:
                fig_heatmap = px.imshow(
                    heatmap_data[mrp_cols].T,
                    labels=dict(x="週区分", y="MRP管理者", color="生産金額"),
                    title="週別・MRP管理者別生産実績ヒートマップ",
                    aspect="auto"
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # フッター
    st.markdown("---")
    st.markdown(
        f"**データ更新日時**: {datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')} | "
        f"**総レコード数**: {len(df):,} 件 | "
        f"**フィルター後**: {len(df_filtered):,} 件"
    )

if __name__ == "__main__":
    main()
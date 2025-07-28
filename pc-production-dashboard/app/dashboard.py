"""
PC製造専用ダッシュボード - Streamlit版

過去データ + 当日データの統合ダッシュボード
月別週区分対応版
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
    page_title="PC製造専用ダッシュボード",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f8f0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E8B57;
    }
    .data-source-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        font-weight: bold;
        margin: 0.1rem;
    }
    .historical-data {
        background-color: #E6F3FF;
        color: #0066CC;
    }
    .current-data {
        background-color: #FFE6E6;
        color: #CC0000;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_pc_production_data():
    """PC製造データを読み込み"""
    try:
        # 実行ファイルの場所を基準にパスを設定
        base_dir = Path(__file__).parent.parent
        db_path = base_dir / "data" / "sqlite" / "pc_production.db"
        
        if not db_path.exists():
            st.error(f"PC製造データベースが見つかりません: {db_path}")
            return None, None
        
        conn = sqlite3.connect(db_path)
        
        # PC製造実績データを取得
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
        AND 完成数 > 0
        ORDER BY 転記日付 DESC, MRP管理者
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            st.warning("PC製造実績データが見つかりません")
            return None, None
        
        # データ前処理
        df['転記日付'] = pd.to_datetime(df['転記日付'], errors='coerce')
        
        # 数値列を適切に変換（強制的に数値化）
        numeric_columns = ['金額', '完成数', '計画数', '単価', '月別週区分']
        for col in numeric_columns:
            if col in df.columns:
                # 文字列の場合は数値に変換、変換できない場合は0
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
        # 金額が0の場合は完成数×単価で再計算
        if '完成数' in df.columns and '単価' in df.columns:
            mask = (df['金額'] == 0) & (df['完成数'] > 0) & (df['単価'] > 0)
            df.loc[mask, '金額'] = df.loc[mask, '完成数'] * df.loc[mask, '単価']
        
        # 年月情報を追加
        df['年'] = df['転記日付'].dt.year
        df['月'] = df['転記日付'].dt.month
        df['年月'] = df['転記日付'].dt.strftime('%Y-%m')
        
        # 曜日情報
        df['曜日'] = df['転記日付'].dt.day_name()
        df['平日フラグ'] = df['転記日付'].dt.weekday < 5
        
        return df, True
        
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return None, None

def create_monthly_week_summary(df):
    """月別週区分サマリーを作成"""
    if df is None or df.empty:
        return pd.DataFrame()
    
    # 年月別・週区分別・MRP管理者別の集計
    summary = df.groupby(['年月', '月別週区分', 'MRP管理者']).agg({
        '金額': 'sum',
        '完成数': 'sum',
        '品目コード': 'nunique'
    }).reset_index()
    
    # ピボットテーブル作成（MRP管理者を列に）
    pivot_amount = summary.pivot_table(
        index=['年月', '月別週区分'],
        columns='MRP管理者',
        values='金額',
        fill_value=0
    ).reset_index()
    
    # 合計列を追加
    mrp_columns = [col for col in pivot_amount.columns if col.startswith('PC')]
    if mrp_columns:
        pivot_amount['合計'] = pivot_amount[mrp_columns].sum(axis=1)
    
    return pivot_amount

def create_data_source_summary(df):
    """データソース別サマリーを作成"""
    if df is None or df.empty:
        return pd.DataFrame()
    
    summary = df.groupby(['データソース', '年月']).agg({
        '金額': 'sum',
        '完成数': 'sum',
        '転記日付': ['min', 'max', 'count']
    }).reset_index()
    
    # カラム名を平坦化
    summary.columns = ['データソース', '年月', '金額合計', '完成数合計', '最古日付', '最新日付', 'レコード数']
    
    return summary

def main():
    """メイン関数"""
    
    # ヘッダー
    st.markdown('<h1 class="main-header">🏭 PC製造専用ダッシュボード</h1>', unsafe_allow_html=True)
    
    # データ読み込み
    with st.spinner('PC製造データを読み込み中...'):
        df, success = load_pc_production_data()
    
    if not success or df is None:
        st.stop()
    
    # データソース情報の表示
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📊 データ概要")
    with col2:
        if st.button("🔄 データ更新", help="最新データを再読み込み"):
            st.cache_data.clear()
            st.rerun()
    
    # データソース別サマリー
    data_source_summary = create_data_source_summary(df)
    if not data_source_summary.empty:
        st.dataframe(data_source_summary, use_container_width=True)
    
    # サイドバー - フィルター
    st.sidebar.header("🔍 フィルター")
    
    # 年月選択
    available_months = sorted(df['年月'].unique(), reverse=True)
    selected_months = st.sidebar.multiselect(
        "年月を選択",
        available_months,
        default=available_months[:6]  # 直近6ヶ月をデフォルト
    )
    
    # MRP管理者選択
    mrp_managers = sorted(df['MRP管理者'].unique())
    selected_mrp = st.sidebar.multiselect(
        "MRP管理者を選択",
        mrp_managers,
        default=mrp_managers
    )
    
    # データソース選択
    data_sources = df['データソース'].unique()
    selected_sources = st.sidebar.multiselect(
        "データソースを選択",
        data_sources,
        default=data_sources
    )
    
    # データフィルタリング
    df_filtered = df.copy()
    
    if selected_months:
        df_filtered = df_filtered[df_filtered['年月'].isin(selected_months)]
    
    if selected_mrp:
        df_filtered = df_filtered[df_filtered['MRP管理者'].isin(selected_mrp)]
    
    if selected_sources:
        df_filtered = df_filtered[df_filtered['データソース'].isin(selected_sources)]
    
    # 月別週区分サマリー作成
    monthly_week_summary = create_monthly_week_summary(df_filtered)
    
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 月別週区分集計", 
        "📅 日別推移", 
        "📋 明細データ", 
        "📊 分析", 
        "🔧 データ管理"
    ])
    
    with tab1:
        st.subheader("月別週区分別生産実績")
        
        if not monthly_week_summary.empty:
            # 月別週区分集計テーブル
            format_dict = {}
            for col in monthly_week_summary.columns:
                if col not in ['年月', '月別週区分'] and pd.api.types.is_numeric_dtype(monthly_week_summary[col]):
                    format_dict[col] = "¥{:,.0f}"
            
            if format_dict:
                st.dataframe(
                    monthly_week_summary.style.format(format_dict),
                    use_container_width=True
                )
            else:
                st.dataframe(monthly_week_summary, use_container_width=True)
            
            # 月別週区分グラフ
            if len(monthly_week_summary) > 0:
                # 年月-週区分の組み合わせ文字列を作成
                monthly_week_summary['年月週'] = (
                    monthly_week_summary['年月'] + '-W' + 
                    monthly_week_summary['月別週区分'].astype(str)
                )
                
                fig = px.bar(
                    monthly_week_summary.melt(
                        id_vars=['年月週'], 
                        value_vars=[col for col in monthly_week_summary.columns if col.startswith('PC')],
                        var_name='MRP管理者', 
                        value_name='金額'
                    ),
                    x='年月週', y='金額', color='MRP管理者',
                    title="月別週区分別生産実績（MRP管理者別）",
                    labels={'金額': '生産金額 (¥)', '年月週': '年月-週区分'}
                )
                fig.update_layout(height=500, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("日別生産推移")
        
        # 日別集計
        daily_data = df_filtered.groupby(['転記日付', 'データソース']).agg({
            '金額': 'sum',
            '完成数': 'sum'
        }).reset_index()
        
        if not daily_data.empty:
            # 日別推移グラフ（データソース別）
            fig = px.line(
                daily_data, x='転記日付', y='金額', color='データソース',
                title="日別生産実績推移（データソース別）",
                labels={'金額': '生産金額 (¥)', '転記日付': '日付'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # MRP管理者別日別推移
            daily_mrp = df_filtered.groupby(['転記日付', 'MRP管理者']).agg({
                '金額': 'sum'
            }).reset_index()
            
            fig2 = px.line(
                daily_mrp, x='転記日付', y='金額', color='MRP管理者',
                title="MRP管理者別日別推移",
                labels={'金額': '生産金額 (¥)', '転記日付': '日付'}
            )
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        st.subheader("生産実績明細")
        
        # 検索機能
        col1, col2, col3 = st.columns(3)
        with col1:
            search_item = st.text_input("品目コード検索", placeholder="品目コードを入力...")
        with col2:
            search_text = st.text_input("品目テキスト検索", placeholder="品目テキストを入力...")
        with col3:
            search_order = st.text_input("指図番号検索", placeholder="指図番号を入力...")
        
        # 明細データフィルタリング
        detail_df = df_filtered.copy()
        if search_item:
            detail_df = detail_df[detail_df['品目コード'].str.contains(search_item, case=False, na=False)]
        if search_text:
            detail_df = detail_df[detail_df['品目テキスト'].str.contains(search_text, case=False, na=False)]
        if search_order:
            detail_df = detail_df[detail_df['ネットワーク・指図番号'].str.contains(search_order, case=False, na=False)]
        
        # 明細データ表示
        if not detail_df.empty:
            st.write(f"表示件数: {len(detail_df):,} 件")
            
            # 表示用データ整形
            display_df = detail_df[[
                '転記日付', 'ネットワーク・指図番号', '品目コード', '品目テキスト',
                '計画数', '完成数', '金額', 'MRP管理者', '月別週区分', 'データソース'
            ]].copy()
            
            display_df['転記日付'] = display_df['転記日付'].dt.strftime('%Y/%m/%d')
            
            # データソースバッジ表示用の関数
            def format_data_source(source):
                if source == '過去データ':
                    return f'<span class="data-source-badge historical-data">{source}</span>'
                else:
                    return f'<span class="data-source-badge current-data">{source}</span>'
            
            # 数値フォーマット
            format_dict = {
                '金額': "¥{:,.0f}",
                '計画数': "{:,.0f}",
                '完成数': "{:,.0f}",
                '月別週区分': "{:.0f}"
            }
            
            st.dataframe(
                display_df.style.format(format_dict),
                use_container_width=True,
                height=400
            )
            
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
            # データソース別構成比
            source_summary = df_filtered.groupby('データソース')['金額'].sum().reset_index()
            fig_pie2 = px.pie(
                source_summary, values='金額', names='データソース',
                title="データソース別生産金額構成比"
            )
            st.plotly_chart(fig_pie2, use_container_width=True)
        
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
    
    with tab5:
        st.subheader("データ管理")
        
        # データ更新ボタン
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 全データ更新", help="サーバーから最新データを取得して統合"):
                with st.spinner("データ更新中..."):
                    try:
                        # data_loaderを実行
                        import subprocess
                        import sys
                        
                        result = subprocess.run([
                            sys.executable, "app/data_loader.py"
                        ], capture_output=True, text=True, cwd="pc-production-dashboard")
                        
                        if result.returncode == 0:
                            st.success("✅ データ更新完了")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ データ更新エラー: {result.stderr}")
                    except Exception as e:
                        st.error(f"❌ データ更新エラー: {e}")
        
        with col2:
            if st.button("📊 データ統計表示"):
                st.write("### データ統計情報")
                
                stats_info = {
                    "総レコード数": len(df),
                    "フィルター後レコード数": len(df_filtered),
                    "データ期間": f"{df['転記日付'].min().strftime('%Y/%m/%d')} ～ {df['転記日付'].max().strftime('%Y/%m/%d')}",
                    "MRP管理者数": df['MRP管理者'].nunique(),
                    "品目数": df['品目コード'].nunique(),
                    "データソース": ", ".join(df['データソース'].unique())
                }
                
                for key, value in stats_info.items():
                    st.write(f"**{key}**: {value}")
    
    # フッター
    st.markdown("---")
    
    # 最終更新時刻の表示
    if '更新時刻' in df.columns and not df['更新時刻'].isna().all():
        latest_update = df['更新時刻'].max()
        st.markdown(f"**最終データ更新**: {latest_update}")
    
    st.markdown(
        f"**表示データ**: {len(df_filtered):,} 件 / 総データ: {len(df):,} 件 | "
        f"**生成時刻**: {datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
    )

if __name__ == "__main__":
    main()
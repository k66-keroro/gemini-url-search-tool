"""
Evaluation dashboard component for displaying search performance metrics and analytics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio

from ...evaluation.evaluation_service import EvaluationService, EffectivenessReport, QueryAnalysis
from ...models.data_models import SearchMetrics, UserEvaluation, SearchFilters


class EvaluationDashboard:
    """Dashboard component for displaying evaluation metrics and analytics."""
    
    def __init__(self, evaluation_service: EvaluationService):
        """
        Initialize evaluation dashboard.
        
        Args:
            evaluation_service: EvaluationService instance
        """
        self.evaluation_service = evaluation_service
    
    def render_dashboard(self) -> None:
        """Render the complete evaluation dashboard."""
        st.title("📊 検索パフォーマンス ダッシュボード")
        
        # Date range selector
        date_range = self._render_date_range_selector()
        
        # Load data
        with st.spinner("データを読み込み中..."):
            try:
                # Get effectiveness report
                report = asyncio.run(
                    self.evaluation_service.generate_effectiveness_report(
                        date_range[0], date_range[1]
                    )
                )
                
                # Render dashboard sections
                self._render_overview_metrics(report.overall_metrics)
                self._render_search_performance_charts(report)
                self._render_query_analysis(report.query_analysis)
                self._render_improvement_suggestions(report.improvement_suggestions)
                self._render_satisfaction_trends(report.user_satisfaction_trend)
                
            except Exception as e:
                st.error(f"ダッシュボードの読み込みに失敗しました: {e}")
    
    def render_user_evaluation_form(self, content_id: int) -> Optional[UserEvaluation]:
        """
        Render user evaluation form for content.
        
        Args:
            content_id: ID of the content to evaluate
            
        Returns:
            UserEvaluation instance if submitted, None otherwise
        """
        st.subheader("📝 コンテンツ評価")
        
        with st.form(f"evaluation_form_{content_id}"):
            col1, col2 = st.columns(2)
            
            with col1:
                usefulness_rating = st.select_slider(
                    "有用性評価",
                    options=[1, 2, 3, 4, 5],
                    value=3,
                    format_func=lambda x: f"{x} {'⭐' * x}",
                    help="このコンテンツはどの程度有用でしたか？"
                )
            
            with col2:
                accuracy_rating = st.select_slider(
                    "精度評価",
                    options=[1, 2, 3, 4, 5],
                    value=3,
                    format_func=lambda x: f"{x} {'⭐' * x}",
                    help="このコンテンツの情報はどの程度正確でしたか？"
                )
            
            time_saved = st.number_input(
                "節約時間（分）",
                min_value=0,
                max_value=480,
                value=5,
                help="このツールを使用することで何分節約できましたか？"
            )
            
            feedback = st.text_area(
                "フィードバック（任意）",
                placeholder="改善点や感想をお聞かせください...",
                help="任意でフィードバックをお聞かせください"
            )
            
            submitted = st.form_submit_button("評価を送信", type="primary")
            
            if submitted:
                try:
                    evaluation = UserEvaluation(
                        content_id=content_id,
                        usefulness_rating=usefulness_rating,
                        accuracy_rating=accuracy_rating,
                        feedback=feedback if feedback.strip() else None,
                        time_saved_minutes=time_saved
                    )
                    
                    # Save evaluation
                    evaluation_id = asyncio.run(
                        self.evaluation_service.save_user_evaluation(evaluation)
                    )
                    
                    st.success("評価を保存しました！ご協力ありがとうございます。")
                    return evaluation
                    
                except Exception as e:
                    st.error(f"評価の保存に失敗しました: {e}")
        
        return None
    
    def _render_date_range_selector(self) -> Tuple[datetime, datetime]:
        """Render date range selector."""
        st.sidebar.subheader("📅 期間設定")
        
        # Preset options
        preset_options = {
            "過去7日間": 7,
            "過去30日間": 30,
            "過去90日間": 90,
            "カスタム": None
        }
        
        selected_preset = st.sidebar.selectbox(
            "期間を選択",
            options=list(preset_options.keys()),
            index=1  # Default to 30 days
        )
        
        if preset_options[selected_preset] is not None:
            # Use preset
            days = preset_options[selected_preset]
            date_to = datetime.now()
            date_from = date_to - timedelta(days=days)
        else:
            # Custom date range
            col1, col2 = st.sidebar.columns(2)
            with col1:
                date_from = st.date_input(
                    "開始日",
                    value=datetime.now() - timedelta(days=30)
                )
            with col2:
                date_to = st.date_input(
                    "終了日",
                    value=datetime.now()
                )
            
            # Convert to datetime
            date_from = datetime.combine(date_from, datetime.min.time())
            date_to = datetime.combine(date_to, datetime.max.time())
        
        return date_from, date_to
    
    def _render_overview_metrics(self, metrics: SearchMetrics) -> None:
        """Render overview metrics cards."""
        st.subheader("📈 概要メトリクス")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="総検索数",
                value=metrics.total_searches,
                help="期間内の総検索回数"
            )
        
        with col2:
            st.metric(
                label="検索成功率",
                value=f"{metrics.success_rate:.1f}%",
                delta=f"{metrics.success_rate - 80:.1f}%" if metrics.success_rate > 0 else None,
                help="結果が見つかった検索の割合"
            )
        
        with col3:
            st.metric(
                label="平均検索時間",
                value=f"{metrics.avg_search_time:.1f}秒",
                delta=f"{3.0 - metrics.avg_search_time:.1f}秒" if metrics.avg_search_time > 0 else None,
                delta_color="inverse",
                help="1回の検索にかかる平均時間"
            )
        
        with col4:
            st.metric(
                label="総節約時間",
                value=f"{metrics.time_saved_total}分",
                help="ユーザーが報告した総節約時間"
            )
        
        # Second row of metrics
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric(
                label="有用性評価",
                value=f"{metrics.avg_usefulness_rating:.1f}/5.0",
                delta=f"{metrics.avg_usefulness_rating - 3.0:.1f}" if metrics.avg_usefulness_rating > 0 else None,
                help="ユーザーによる有用性の平均評価"
            )
        
        with col6:
            st.metric(
                label="精度評価",
                value=f"{metrics.avg_accuracy_rating:.1f}/5.0",
                delta=f"{metrics.avg_accuracy_rating - 3.0:.1f}" if metrics.avg_accuracy_rating > 0 else None,
                help="ユーザーによる精度の平均評価"
            )
        
        with col7:
            st.metric(
                label="一般検索",
                value=metrics.general_searches,
                help="フリーワード検索の回数"
            )
        
        with col8:
            st.metric(
                label="部品検索",
                value=metrics.component_searches,
                help="部品仕様検索の回数"
            )
    
    def _render_search_performance_charts(self, report: EffectivenessReport) -> None:
        """Render search performance charts."""
        st.subheader("📊 検索パフォーマンス分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Search type distribution pie chart
            if report.overall_metrics.total_searches > 0:
                fig_pie = px.pie(
                    values=[
                        report.overall_metrics.general_searches,
                        report.overall_metrics.component_searches
                    ],
                    names=["一般検索", "部品検索"],
                    title="検索タイプ分布",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("検索データがありません")
        
        with col2:
            # Performance trends chart
            if report.query_analysis.query_performance_trends:
                trends_df = pd.DataFrame([
                    {"週": week, "成功率": success_rate}
                    for week, success_rate in report.query_analysis.query_performance_trends.items()
                ])
                
                fig_line = px.line(
                    trends_df,
                    x="週",
                    y="成功率",
                    title="週別検索成功率トレンド",
                    markers=True
                )
                fig_line.update_layout(yaxis_title="成功率 (%)")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("トレンドデータがありません")
    
    def _render_query_analysis(self, query_analysis: QueryAnalysis) -> None:
        """Render query analysis section."""
        st.subheader("🔍 クエリ分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**よく使用されるクエリ**")
            if query_analysis.most_common_queries:
                query_df = pd.DataFrame(
                    query_analysis.most_common_queries,
                    columns=["クエリ", "回数"]
                )
                st.dataframe(query_df, use_container_width=True)
            else:
                st.info("クエリデータがありません")
        
        with col2:
            st.write("**検索タイプ別成功率**")
            if query_analysis.most_successful_query_types:
                type_df = pd.DataFrame(
                    query_analysis.most_successful_query_types,
                    columns=["タイプ", "成功率 (%)"]
                )
                st.dataframe(type_df, use_container_width=True)
            else:
                st.info("成功率データがありません")
        
        # Average results per query
        st.metric(
            label="クエリあたりの平均結果数",
            value=f"{query_analysis.avg_results_per_query:.1f}",
            help="1つのクエリで見つかる平均結果数"
        )
    
    def _render_improvement_suggestions(self, suggestions: List[str]) -> None:
        """Render improvement suggestions."""
        st.subheader("💡 改善提案")
        
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                st.info(f"**提案 {i}:** {suggestion}")
        else:
            st.success("現在のパフォーマンスは良好です！")
    
    def _render_satisfaction_trends(self, satisfaction_trend: List[Tuple[datetime, float]]) -> None:
        """Render user satisfaction trends."""
        st.subheader("😊 ユーザー満足度トレンド")
        
        if satisfaction_trend:
            # Create DataFrame for plotting
            trend_df = pd.DataFrame(
                satisfaction_trend,
                columns=["日付", "満足度"]
            )
            
            # Create satisfaction trend chart
            fig = px.line(
                trend_df,
                x="日付",
                y="満足度",
                title="日別ユーザー満足度",
                markers=True,
                range_y=[1, 5]
            )
            
            # Add reference lines
            fig.add_hline(
                y=3.0,
                line_dash="dash",
                line_color="orange",
                annotation_text="普通 (3.0)"
            )
            fig.add_hline(
                y=4.0,
                line_dash="dash",
                line_color="green",
                annotation_text="良好 (4.0)"
            )
            
            fig.update_layout(
                yaxis_title="満足度 (1-5)",
                xaxis_title="日付"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_satisfaction = sum(score for _, score in satisfaction_trend) / len(satisfaction_trend)
                st.metric("平均満足度", f"{avg_satisfaction:.2f}/5.0")
            
            with col2:
                max_satisfaction = max(score for _, score in satisfaction_trend)
                st.metric("最高満足度", f"{max_satisfaction:.2f}/5.0")
            
            with col3:
                min_satisfaction = min(score for _, score in satisfaction_trend)
                st.metric("最低満足度", f"{min_satisfaction:.2f}/5.0")
        
        else:
            st.info("満足度データがありません。コンテンツを評価してデータを蓄積してください。")
    
    def render_detailed_analytics(self) -> None:
        """Render detailed analytics page."""
        st.title("📈 詳細分析")
        
        # Tab layout for different analytics
        tab1, tab2, tab3 = st.tabs(["検索分析", "コンテンツ分析", "ユーザー行動"])
        
        with tab1:
            self._render_search_analytics()
        
        with tab2:
            self._render_content_analytics()
        
        with tab3:
            self._render_user_behavior_analytics()
    
    def _render_search_analytics(self) -> None:
        """Render detailed search analytics."""
        st.subheader("🔍 検索詳細分析")
        
        # Time-based analysis
        st.write("**時間帯別検索パターン**")
        # This would require additional data collection
        st.info("時間帯別分析は今後の機能として実装予定です")
        
        # Search success factors
        st.write("**検索成功要因分析**")
        st.info("成功要因分析は今後の機能として実装予定です")
    
    def _render_content_analytics(self) -> None:
        """Render content analytics."""
        st.subheader("📄 コンテンツ分析")
        
        # Content type distribution
        st.write("**コンテンツタイプ分布**")
        st.info("コンテンツ分析は今後の機能として実装予定です")
        
        # Most valuable content
        st.write("**最も価値の高いコンテンツ**")
        st.info("価値分析は今後の機能として実装予定です")
    
    def _render_user_behavior_analytics(self) -> None:
        """Render user behavior analytics."""
        st.subheader("👤 ユーザー行動分析")
        
        # Usage patterns
        st.write("**使用パターン分析**")
        st.info("行動分析は今後の機能として実装予定です")
        
        # Feature adoption
        st.write("**機能採用率**")
        st.info("機能採用分析は今後の機能として実装予定です")
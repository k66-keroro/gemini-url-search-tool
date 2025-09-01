"""
Main Streamlit application for Gemini URL Search Tool
"""

import streamlit as st
import json
import os
from pathlib import Path
import sys

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from ui.components.search_interface import render_search_interface, SearchInterface
from ui.components.results_display import render_search_results
from ui.components.content_analysis_display import render_content_analysis, create_sample_content_analysis
from ui.components.evaluation_dashboard import EvaluationDashboard
from ui.components.settings_interface import render_settings_page
from evaluation.evaluation_service import EvaluationService
from models.database import DatabaseManager
from core.settings_service import SettingsService
from core.storage_service import StorageService

def load_config():
    """Load application configuration"""
    try:
        config_path = Path(__file__).parent.parent.parent / "config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load configuration: {e}")
        return {}

def run_app():
    """Main Streamlit application entry point"""
    config = load_config()
    ui_config = config.get("ui", {})
    
    # Configure Streamlit page
    st.set_page_config(
        page_title=ui_config.get("page_title", "Gemini URL Search Tool"),
        page_icon=ui_config.get("page_icon", "🔍"),
        layout=ui_config.get("layout", "wide"),
        initial_sidebar_state=ui_config.get("sidebar_state", "expanded")
    )
    
    # Navigation sidebar
    st.sidebar.title("🔍 Gemini URL Search Tool")
    page = st.sidebar.selectbox(
        "ページを選択",
        ["🔍 検索", "📊 ダッシュボード", "📈 詳細分析", "⚙️ 設定"],
        help="使用したい機能を選択してください"
    )
    
    # Main application header
    if page == "🔍 検索":
        st.title("🔍 Gemini URL Search Tool")
    elif page == "📊 ダッシュボード":
        st.title("📊 検索パフォーマンス ダッシュボード")
    elif page == "📈 詳細分析":
        st.title("📈 詳細分析")
    elif page == "⚙️ 設定":
        st.title("⚙️ 設定管理")
    
    st.markdown("---")
    
    # Check API key configuration
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key and page == "🔍 検索":
        st.error("⚠️ Gemini API key not configured")
        st.markdown("""
        Please set up your API key:
        1. Copy `.env.example` to `.env`
        2. Add your Gemini API key to the `.env` file
        3. Restart the application
        """)
        return
    
    # Handle different pages
    if page == "📊 ダッシュボード":
        render_dashboard_page()
        return
    elif page == "📈 詳細分析":
        render_detailed_analytics_page()
        return
    elif page == "⚙️ 設定":
        render_settings_page_handler()
        return
    
    # Continue with search page if API key is configured
    if not api_key:
        return
    
    # Initialize session state for search results and content analysis
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'search_in_progress' not in st.session_state:
        st.session_state.search_in_progress = False
    if 'selected_content' not in st.session_state:
        st.session_state.selected_content = None
    if 'show_content_analysis' not in st.session_state:
        st.session_state.show_content_analysis = False
    
    # Render search interface
    search_data = render_search_interface()
    
    # Handle search execution
    if search_data and not st.session_state.search_in_progress:
        st.session_state.search_in_progress = True
        
        # Display search parameters
        with st.expander("🔍 検索パラメータ"):
            st.json(search_data)
        
        # Simulate search execution (placeholder for actual implementation)
        interface = SearchInterface()
        interface.render_loading_state("検索を実行中...")
        
        # Generate more comprehensive placeholder results
        import random
        from datetime import datetime, timedelta
        
        sample_results = []
        base_titles = [
            "Python プログラミング入門ガイド",
            "React フロントエンド開発チュートリアル", 
            "機械学習の基礎概念",
            "データベース設計のベストプラクティス",
            "Web API 開発入門",
            "クラウドアーキテクチャ設計",
            "セキュリティ対策の実装方法",
            "パフォーマンス最適化テクニック"
        ]
        
        source_types = ["official", "documentation", "tutorial", "general"]
        languages = ["日本語", "英語", "多言語"]
        
        for i in range(12):  # Generate 12 sample results for pagination testing
            sample_results.append({
                "title": f"{base_titles[i % len(base_titles)]} - Part {i+1}",
                "url": f"https://example.com/result/{i+1}",
                "description": f"これは検索結果 {i+1} のサンプル説明です。実際の検索機能では、Gemini APIから取得した実際のWeb情報が表示されます。この結果は{source_types[i % len(source_types)]}タイプのコンテンツです。",
                "source_type": source_types[i % len(source_types)],
                "confidence_score": random.uniform(0.6, 0.95),
                "date_found": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
                "language": languages[i % len(languages)],
                "content_size": f"{random.randint(5, 50)}KB",
                "content_preview": f"これは結果 {i+1} のコンテンツプレビューです。実際の実装では、Webページの内容の一部が表示されます。",
                "technical_specs": {
                    "type": "sample",
                    "version": f"v{random.randint(1, 5)}.{random.randint(0, 9)}",
                    "compatibility": "All platforms"
                } if i % 3 == 0 else None
            })
        
        st.session_state.search_results = {
            "query": search_data,
            "results": sample_results
        }
        
        st.session_state.search_in_progress = False
        st.rerun()
    
    # Display search results if available
    if st.session_state.search_results:
        st.markdown("---")
        
        # Extract search query for display
        query_info = st.session_state.search_results["query"]
        if query_info["search_type"].value == "general":
            search_query = query_info["keywords"]
        else:
            search_query = f"{query_info['manufacturer']} {query_info['part_number']}"
        
        # Render search results using the new component
        result_action = render_search_results(
            results=st.session_state.search_results["results"],
            search_query=search_query,
            results_per_page=5
        )
        
        # Handle result actions
        if result_action:
            if result_action["action"] == "save":
                st.success("💾 結果が保存されました（StorageService統合後に実装）")
            elif result_action["action"] == "rate":
                st.success("⭐ 評価が記録されました（EvaluationService統合後に実装）")
            elif result_action["action"] == "analyze":
                # Trigger content analysis
                st.session_state.selected_content = result_action["data"]
                st.session_state.show_content_analysis = True
                st.rerun()
        
        # Clear results button
        st.markdown("---")
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🗑️ 検索結果をクリア", type="secondary"):
                st.session_state.search_results = None
                st.session_state.current_page = 1  # Reset pagination
                st.session_state.show_content_analysis = False
                st.session_state.selected_content = None
                st.rerun()
    
    # Display content analysis if requested
    if st.session_state.show_content_analysis and st.session_state.selected_content:
        st.markdown("---")
        
        # Create sample content analysis based on selected result
        selected_result = st.session_state.selected_content
        
        # Simulate content analysis (in real implementation, this would call ContentService)
        with st.spinner("🔍 コンテンツを分析中..."):
            import time
            time.sleep(1)  # Simulate analysis time
            
            # Create sample analysis data based on the selected result
            content_analysis = create_sample_content_analysis()
            content_analysis["url"] = selected_result.get("url", "")
            content_analysis["title"] = selected_result.get("title", "")
            
            # Customize analysis based on search type
            if st.session_state.search_results and st.session_state.search_results["query"]["search_type"].value == "component":
                # For component searches, focus on technical specifications
                query_info = st.session_state.search_results["query"]
                manufacturer = query_info.get("manufacturer", "")
                part_number = query_info.get("part_number", "")
                
                content_analysis["title"] = f"{manufacturer} {part_number} - 技術仕様"
                content_analysis["summary"] = f"{manufacturer}の{part_number}は、高性能な電子部品です。詳細な技術仕様と使用方法について説明します。"
        
        # Render content analysis
        analysis_action = render_content_analysis(content_analysis)
        
        # Handle content analysis actions
        if analysis_action:
            if analysis_action["action"] == "save":
                st.success("💾 コンテンツ分析が保存されました（StorageService統合後に実装）")
            elif analysis_action["action"] == "evaluate":
                st.success("⭐ 評価が記録されました（EvaluationService統合後に実装）")
            elif analysis_action["action"] == "reanalyze":
                st.info("🔄 再分析を実行中...（ContentService統合後に実装）")
        
        # Back to results button
        st.markdown("---")
        if st.button("⬅️ 検索結果に戻る"):
            st.session_state.show_content_analysis = False
            st.session_state.selected_content = None
            st.rerun()
    
    # Configuration display
    with st.expander("📋 Current Configuration"):
        st.json(config)


def render_dashboard_page():
    """Render the evaluation dashboard page."""
    try:
        # Initialize database and evaluation service
        db_manager = DatabaseManager()
        evaluation_service = EvaluationService(db_manager)
        
        # Create and render dashboard
        dashboard = EvaluationDashboard(evaluation_service)
        dashboard.render_dashboard()
        
    except Exception as e:
        st.error(f"ダッシュボードの初期化に失敗しました: {e}")
        st.info("データベースが初期化されていない可能性があります。検索を実行してデータを蓄積してください。")


def render_detailed_analytics_page():
    """Render the detailed analytics page."""
    try:
        # Initialize database and evaluation service
        db_manager = DatabaseManager()
        evaluation_service = EvaluationService(db_manager)
        
        # Create and render detailed analytics
        dashboard = EvaluationDashboard(evaluation_service)
        dashboard.render_detailed_analytics()
        
    except Exception as e:
        st.error(f"詳細分析の初期化に失敗しました: {e}")
        st.info("データベースが初期化されていない可能性があります。検索を実行してデータを蓄積してください。")


def render_settings_page_handler():
    """Render the settings management page."""
    try:
        # Initialize services
        config_path = Path(__file__).parent.parent.parent / "config.json"
        
        # Initialize storage service for database settings
        storage_service = None
        try:
            storage_service = StorageService()
        except Exception as e:
            st.warning(f"データベース接続に失敗しました: {e}")
            st.info("一部の設定機能が制限される可能性があります。")
        
        # Initialize settings service
        settings_service = SettingsService(
            config_path=str(config_path),
            storage_service=storage_service
        )
        
        # Render settings page
        render_settings_page(settings_service, storage_service)
        
    except Exception as e:
        st.error(f"設定ページの初期化に失敗しました: {e}")
        st.info("設定ファイルが見つからないか、破損している可能性があります。")


if __name__ == "__main__":
    run_app()
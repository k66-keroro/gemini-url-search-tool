"""
Settings interface component for the Gemini URL Search Tool.

This module provides a comprehensive settings management UI including:
- API configuration
- Search preferences
- Content processing settings
- UI customization
- Database management
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from ...core.settings_service import SettingsService
from ...core.storage_service import StorageService

logger = logging.getLogger(__name__)


class SettingsInterface:
    """
    Streamlit-based settings management interface.
    
    Provides a user-friendly interface for managing all application settings.
    """
    
    def __init__(self, settings_service: SettingsService, storage_service: Optional[StorageService] = None):
        """
        Initialize the settings interface.
        
        Args:
            settings_service: Settings management service
            storage_service: Optional storage service for additional operations
        """
        self.settings_service = settings_service
        self.storage_service = storage_service
    
    def render(self) -> None:
        """Render the complete settings interface."""
        st.title("⚙️ 設定管理")
        st.markdown("アプリケーションの設定を管理します。")
        
        # Settings tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🔑 API設定", 
            "🔍 検索設定", 
            "📄 コンテンツ設定", 
            "🎨 UI設定", 
            "💾 データベース設定",
            "🔧 システム設定"
        ])
        
        with tab1:
            self._render_api_settings()
        
        with tab2:
            self._render_search_settings()
        
        with tab3:
            self._render_content_settings()
        
        with tab4:
            self._render_ui_settings()
        
        with tab5:
            self._render_database_settings()
        
        with tab6:
            self._render_system_settings()
        
        # Settings management actions
        st.markdown("---")
        self._render_settings_actions()
    
    def _render_api_settings(self) -> None:
        """Render API configuration settings."""
        st.subheader("Gemini API 設定")
        
        api_settings = self.settings_service.get_api_settings()
        
        # API Key
        st.markdown("#### API キー")
        current_key = api_settings.api_key
        masked_key = f"{'*' * (len(current_key) - 8)}{current_key[-8:]}" if len(current_key) > 8 else current_key
        
        col1, col2 = st.columns([3, 1])
        with col1:
            new_api_key = st.text_input(
                "Gemini API キー",
                value=masked_key if current_key else "",
                type="password",
                help="Google AI Studio で取得したAPI キーを入力してください"
            )
        
        with col2:
            if st.button("🔄 更新", key="update_api_key"):
                if new_api_key and new_api_key != masked_key:
                    if self.settings_service.validate_api_key(new_api_key):
                        if self.settings_service.update_api_key(new_api_key):
                            st.success("API キーが更新されました")
                            st.rerun()
                        else:
                            st.error("API キーの更新に失敗しました")
                    else:
                        st.error("無効なAPI キー形式です")
        
        # Model Configuration
        st.markdown("#### モデル設定")
        col1, col2 = st.columns(2)
        
        with col1:
            available_models = [
                "gemini-2.0-flash-exp",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-1.0-pro"
            ]
            
            selected_models = st.multiselect(
                "使用するモデル",
                available_models,
                default=api_settings.models,
                help="フォールバック順序で選択してください"
            )
            
            if selected_models != api_settings.models:
                self.settings_service.set_setting("api.models", selected_models)
        
        with col2:
            max_retries = st.number_input(
                "最大リトライ回数",
                min_value=1,
                max_value=10,
                value=api_settings.max_retries,
                help="API エラー時の最大リトライ回数"
            )
            
            if max_retries != api_settings.max_retries:
                self.settings_service.set_setting("api.max_retries", max_retries)
        
        # Advanced API Settings
        with st.expander("詳細設定"):
            col1, col2 = st.columns(2)
            
            with col1:
                timeout = st.number_input(
                    "タイムアウト (秒)",
                    min_value=5,
                    max_value=300,
                    value=api_settings.timeout,
                    help="API リクエストのタイムアウト時間"
                )
                
                if timeout != api_settings.timeout:
                    self.settings_service.set_setting("api.timeout", timeout)
            
            with col2:
                rate_limit_delay = st.number_input(
                    "レート制限遅延 (秒)",
                    min_value=0.1,
                    max_value=10.0,
                    value=api_settings.rate_limit_delay,
                    step=0.1,
                    help="レート制限時の待機時間"
                )
                
                if rate_limit_delay != api_settings.rate_limit_delay:
                    self.settings_service.set_setting("api.rate_limit_delay", rate_limit_delay)
    
    def _render_search_settings(self) -> None:
        """Render search configuration settings."""
        st.subheader("検索設定")
        
        search_settings = self.settings_service.get_search_settings()
        
        col1, col2 = st.columns(2)
        
        with col1:
            max_results = st.number_input(
                "最大検索結果数",
                min_value=1,
                max_value=50,
                value=search_settings.max_results,
                help="一回の検索で取得する最大結果数"
            )
            
            if max_results != search_settings.max_results:
                self.settings_service.set_setting("search.max_results", max_results)
            
            default_search_type = st.selectbox(
                "デフォルト検索タイプ",
                ["general", "component"],
                index=0 if search_settings.default_search_type == "general" else 1,
                help="アプリ起動時のデフォルト検索タイプ"
            )
            
            if default_search_type != search_settings.default_search_type:
                self.settings_service.set_setting("search.default_search_type", default_search_type)
        
        with col2:
            enable_caching = st.checkbox(
                "キャッシュを有効にする",
                value=search_settings.enable_caching,
                help="検索結果のキャッシュを有効にします"
            )
            
            if enable_caching != search_settings.enable_caching:
                self.settings_service.set_setting("search.enable_caching", enable_caching)
            
            if enable_caching:
                cache_duration = st.number_input(
                    "キャッシュ保持時間 (時間)",
                    min_value=1,
                    max_value=168,  # 1 week
                    value=search_settings.cache_duration_hours,
                    help="検索結果キャッシュの保持時間"
                )
                
                if cache_duration != search_settings.cache_duration_hours:
                    self.settings_service.set_setting("search.cache_duration_hours", cache_duration)
        
        # Advanced Search Settings
        st.markdown("#### 詳細検索設定")
        col1, col2 = st.columns(2)
        
        with col1:
            enable_ranking = st.checkbox(
                "結果ランキングを有効にする",
                value=search_settings.enable_result_ranking,
                help="検索結果の関連性によるランキングを有効にします"
            )
            
            if enable_ranking != search_settings.enable_result_ranking:
                self.settings_service.set_setting("search.enable_result_ranking", enable_ranking)
        
        with col2:
            prioritize_official = st.checkbox(
                "公式ソースを優先する",
                value=search_settings.prioritize_official_sources,
                help="部品検索時に公式メーカーサイトを優先します"
            )
            
            if prioritize_official != search_settings.prioritize_official_sources:
                self.settings_service.set_setting("search.prioritize_official_sources", prioritize_official)
    
    def _render_content_settings(self) -> None:
        """Render content processing settings."""
        st.subheader("コンテンツ処理設定")
        
        content_settings = self.settings_service.get_content_settings()
        
        col1, col2 = st.columns(2)
        
        with col1:
            max_content_size = st.number_input(
                "最大コンテンツサイズ (バイト)",
                min_value=1024,
                max_value=10485760,  # 10MB
                value=content_settings.max_content_size,
                step=1024,
                help="処理する最大コンテンツサイズ"
            )
            
            if max_content_size != content_settings.max_content_size:
                self.settings_service.set_setting("content.max_content_size", max_content_size)
            
            chunk_size = st.number_input(
                "チャンクサイズ (バイト)",
                min_value=512,
                max_value=8192,
                value=content_settings.chunk_size,
                step=512,
                help="大容量コンテンツの分割サイズ"
            )
            
            if chunk_size != content_settings.chunk_size:
                self.settings_service.set_setting("content.chunk_size", chunk_size)
        
        with col2:
            summary_max_length = st.number_input(
                "要約最大長 (文字)",
                min_value=100,
                max_value=5000,
                value=content_settings.summary_max_length,
                step=100,
                help="生成する要約の最大文字数"
            )
            
            if summary_max_length != content_settings.summary_max_length:
                self.settings_service.set_setting("content.summary_max_length", summary_max_length)
            
            extraction_timeout = st.number_input(
                "抽出タイムアウト (秒)",
                min_value=10,
                max_value=300,
                value=content_settings.extraction_timeout,
                help="コンテンツ抽出の最大時間"
            )
            
            if extraction_timeout != content_settings.extraction_timeout:
                self.settings_service.set_setting("content.extraction_timeout", extraction_timeout)
        
        # Content Processing Options
        st.markdown("#### コンテンツ処理オプション")
        col1, col2 = st.columns(2)
        
        with col1:
            enable_filtering = st.checkbox(
                "コンテンツフィルタリングを有効にする",
                value=content_settings.enable_content_filtering,
                help="不適切なコンテンツのフィルタリングを有効にします"
            )
            
            if enable_filtering != content_settings.enable_content_filtering:
                self.settings_service.set_setting("content.enable_content_filtering", enable_filtering)
        
        with col2:
            auto_detect_language = st.checkbox(
                "言語自動検出を有効にする",
                value=content_settings.auto_detect_language,
                help="コンテンツの言語を自動検出します"
            )
            
            if auto_detect_language != content_settings.auto_detect_language:
                self.settings_service.set_setting("content.auto_detect_language", auto_detect_language)
    
    def _render_ui_settings(self) -> None:
        """Render UI configuration settings."""
        st.subheader("ユーザーインターフェース設定")
        
        ui_settings = self.settings_service.get_ui_settings()
        
        col1, col2 = st.columns(2)
        
        with col1:
            page_title = st.text_input(
                "ページタイトル",
                value=ui_settings.page_title,
                help="ブラウザタブに表示されるタイトル"
            )
            
            if page_title != ui_settings.page_title:
                self.settings_service.set_setting("ui.page_title", page_title)
            
            page_icon = st.text_input(
                "ページアイコン",
                value=ui_settings.page_icon,
                help="ブラウザタブに表示されるアイコン（絵文字）"
            )
            
            if page_icon != ui_settings.page_icon:
                self.settings_service.set_setting("ui.page_icon", page_icon)
            
            layout = st.selectbox(
                "レイアウト",
                ["wide", "centered"],
                index=0 if ui_settings.layout == "wide" else 1,
                help="ページレイアウトの設定"
            )
            
            if layout != ui_settings.layout:
                self.settings_service.set_setting("ui.layout", layout)
        
        with col2:
            sidebar_state = st.selectbox(
                "サイドバー初期状態",
                ["expanded", "collapsed", "auto"],
                index=["expanded", "collapsed", "auto"].index(ui_settings.sidebar_state),
                help="アプリ起動時のサイドバー状態"
            )
            
            if sidebar_state != ui_settings.sidebar_state:
                self.settings_service.set_setting("ui.sidebar_state", sidebar_state)
            
            theme = st.selectbox(
                "テーマ",
                ["auto", "light", "dark"],
                index=["auto", "light", "dark"].index(ui_settings.theme),
                help="アプリケーションのテーマ"
            )
            
            if theme != ui_settings.theme:
                self.settings_service.set_setting("ui.theme", theme)
            
            results_per_page = st.number_input(
                "ページあたりの結果数",
                min_value=5,
                max_value=50,
                value=ui_settings.results_per_page,
                help="一ページに表示する検索結果数"
            )
            
            if results_per_page != ui_settings.results_per_page:
                self.settings_service.set_setting("ui.results_per_page", results_per_page)
        
        # Advanced UI Options
        show_advanced = st.checkbox(
            "詳細オプションを表示する",
            value=ui_settings.show_advanced_options,
            help="UI に詳細オプションを表示します"
        )
        
        if show_advanced != ui_settings.show_advanced_options:
            self.settings_service.set_setting("ui.show_advanced_options", show_advanced)
    
    def _render_database_settings(self) -> None:
        """Render database configuration settings."""
        st.subheader("データベース設定")
        
        db_settings = self.settings_service.get_database_settings()
        
        col1, col2 = st.columns(2)
        
        with col1:
            db_path = st.text_input(
                "データベースパス",
                value=db_settings.path,
                help="SQLite データベースファイルのパス"
            )
            
            if db_path != db_settings.path:
                self.settings_service.set_setting("database.path", db_path)
            
            backup_enabled = st.checkbox(
                "自動バックアップを有効にする",
                value=db_settings.backup_enabled,
                help="データベースの自動バックアップを有効にします"
            )
            
            if backup_enabled != db_settings.backup_enabled:
                self.settings_service.set_setting("database.backup_enabled", backup_enabled)
        
        with col2:
            cleanup_days = st.number_input(
                "データ保持日数",
                min_value=1,
                max_value=365,
                value=db_settings.cleanup_days,
                help="古いデータを削除するまでの日数"
            )
            
            if cleanup_days != db_settings.cleanup_days:
                self.settings_service.set_setting("database.cleanup_days", cleanup_days)
            
            auto_vacuum = st.checkbox(
                "自動VACUUM を有効にする",
                value=db_settings.auto_vacuum,
                help="データベースの自動最適化を有効にします"
            )
            
            if auto_vacuum != db_settings.auto_vacuum:
                self.settings_service.set_setting("database.auto_vacuum", auto_vacuum)
        
        # Database Management Actions
        st.markdown("#### データベース管理")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 データベース最適化", help="データベースを最適化します"):
                if self.storage_service:
                    try:
                        # Perform database optimization
                        with self.storage_service.db_manager.get_connection() as conn:
                            conn.execute("VACUUM")
                        st.success("データベースが最適化されました")
                    except Exception as e:
                        st.error(f"最適化に失敗しました: {e}")
        
        with col2:
            if st.button("📊 データベース統計", help="データベースの統計情報を表示"):
                if self.storage_service:
                    try:
                        stats = self.storage_service.get_database_stats()
                        st.json(stats)
                    except Exception as e:
                        st.error(f"統計取得に失敗しました: {e}")
        
        with col3:
            if st.button("🗑️ 古いデータ削除", help="保持期間を過ぎたデータを削除"):
                if self.storage_service:
                    try:
                        deleted_count = self.storage_service.cleanup_old_data(cleanup_days)
                        st.success(f"{deleted_count} 件のデータを削除しました")
                    except Exception as e:
                        st.error(f"削除に失敗しました: {e}")
    
    def _render_system_settings(self) -> None:
        """Render system and logging settings."""
        st.subheader("システム設定")
        
        logging_settings = self.settings_service.get_logging_settings()
        
        # Logging Configuration
        st.markdown("#### ログ設定")
        col1, col2 = st.columns(2)
        
        with col1:
            log_level = st.selectbox(
                "ログレベル",
                ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(logging_settings.level),
                help="出力するログの最小レベル"
            )
            
            if log_level != logging_settings.level:
                self.settings_service.set_setting("logging.level", log_level)
            
            log_file = st.text_input(
                "ログファイルパス",
                value=logging_settings.file,
                help="ログファイルの保存パス"
            )
            
            if log_file != logging_settings.file:
                self.settings_service.set_setting("logging.file", log_file)
        
        with col2:
            max_size_mb = st.number_input(
                "最大ファイルサイズ (MB)",
                min_value=1,
                max_value=100,
                value=logging_settings.max_size_mb,
                help="ログファイルの最大サイズ"
            )
            
            if max_size_mb != logging_settings.max_size_mb:
                self.settings_service.set_setting("logging.max_size_mb", max_size_mb)
            
            backup_count = st.number_input(
                "バックアップファイル数",
                min_value=1,
                max_value=20,
                value=logging_settings.backup_count,
                help="保持するログバックアップファイル数"
            )
            
            if backup_count != logging_settings.backup_count:
                self.settings_service.set_setting("logging.backup_count", backup_count)
        
        console_output = st.checkbox(
            "コンソール出力を有効にする",
            value=logging_settings.console_output,
            help="ログをコンソールにも出力します"
        )
        
        if console_output != logging_settings.console_output:
            self.settings_service.set_setting("logging.console_output", console_output)
    
    def _render_settings_actions(self) -> None:
        """Render settings management actions."""
        st.subheader("設定管理")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 設定を保存", help="現在の設定をファイルに保存します"):
                if self.settings_service.save_settings():
                    st.success("設定が保存されました")
                else:
                    st.error("設定の保存に失敗しました")
        
        with col2:
            if st.button("🔄 設定を再読み込み", help="ファイルから設定を再読み込みします"):
                self.settings_service.load_settings()
                st.success("設定が再読み込みされました")
                st.rerun()
        
        with col3:
            if st.button("🔧 デフォルトに戻す", help="すべての設定をデフォルト値に戻します"):
                if st.session_state.get("confirm_reset", False):
                    if self.settings_service.reset_settings():
                        st.success("設定がデフォルトに戻されました")
                        st.session_state["confirm_reset"] = False
                        st.rerun()
                    else:
                        st.error("設定のリセットに失敗しました")
                else:
                    st.session_state["confirm_reset"] = True
                    st.warning("もう一度クリックして確認してください")
        
        with col4:
            # Settings Import/Export
            with st.expander("📁 インポート/エクスポート"):
                # Export settings
                if st.button("📤 設定をエクスポート"):
                    from datetime import datetime
                    export_path = f"settings_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    if self.settings_service.export_settings(export_path):
                        st.success(f"設定を {export_path} にエクスポートしました")
                    else:
                        st.error("エクスポートに失敗しました")
                
                # Import settings
                uploaded_file = st.file_uploader(
                    "設定ファイルをインポート",
                    type=['json'],
                    help="以前にエクスポートした設定ファイルを選択してください"
                )
                
                if uploaded_file is not None:
                    if st.button("📥 インポート実行"):
                        try:
                            # Save uploaded file temporarily
                            temp_path = f"temp_import_{uploaded_file.name}"
                            with open(temp_path, 'wb') as f:
                                f.write(uploaded_file.getvalue())
                            
                            # Import settings
                            if self.settings_service.import_settings(temp_path):
                                st.success("設定がインポートされました")
                                st.rerun()
                            else:
                                st.error("インポートに失敗しました")
                            
                            # Clean up temp file
                            Path(temp_path).unlink(missing_ok=True)
                            
                        except Exception as e:
                            st.error(f"インポートエラー: {e}")


def render_settings_page(settings_service: SettingsService, storage_service: Optional[StorageService] = None) -> None:
    """
    Render the settings page.
    
    Args:
        settings_service: Settings management service
        storage_service: Optional storage service
    """
    settings_interface = SettingsInterface(settings_service, storage_service)
    settings_interface.render()
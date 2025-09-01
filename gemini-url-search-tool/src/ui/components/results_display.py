"""
Search results display component for Gemini URL Search Tool
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Callable
import math
from datetime import datetime
from enum import Enum

class SortOption(Enum):
    """Sort options for search results"""
    RELEVANCE = "relevance"
    DATE = "date"
    TITLE = "title"
    SOURCE = "source"

class FilterOption(Enum):
    """Filter options for search results"""
    ALL = "all"
    OFFICIAL = "official"
    DOCUMENTATION = "documentation"
    TUTORIAL = "tutorial"

class ResultsDisplay:
    """Component for displaying and managing search results"""
    
    def __init__(self, results_per_page: int = 5):
        """Initialize results display component"""
        self.results_per_page = results_per_page
        
    def render_results_header(self, total_results: int, search_query: str) -> None:
        """Render results header with count and query info"""
        st.subheader(f"📋 検索結果 ({total_results}件)")
        
        if search_query:
            st.caption(f"検索クエリ: **{search_query}**")
        
        if total_results == 0:
            st.warning("⚠️ 検索結果が見つかりませんでした")
            st.markdown("""
            **検索のヒント:**
            - キーワードを変更してみてください
            - より一般的な用語を使用してみてください
            - スペルを確認してください
            """)
            return
    
    def render_filter_controls(self) -> Dict[str, Any]:
        """Render filter and sort controls"""
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            filter_option = st.selectbox(
                "フィルター",
                options=[
                    ("すべて", FilterOption.ALL),
                    ("公式サイト", FilterOption.OFFICIAL),
                    ("ドキュメント", FilterOption.DOCUMENTATION),
                    ("チュートリアル", FilterOption.TUTORIAL)
                ],
                format_func=lambda x: x[0],
                help="表示する結果の種類を選択"
            )
        
        with col2:
            sort_option = st.selectbox(
                "並び順",
                options=[
                    ("関連度順", SortOption.RELEVANCE),
                    ("日付順", SortOption.DATE),
                    ("タイトル順", SortOption.TITLE),
                    ("ソース順", SortOption.SOURCE)
                ],
                format_func=lambda x: x[0],
                help="結果の並び順を選択"
            )
        
        with col3:
            show_preview = st.checkbox(
                "プレビュー表示",
                value=True,
                help="結果の詳細プレビューを表示"
            )
        
        return {
            "filter": filter_option[1],
            "sort": sort_option[1],
            "show_preview": show_preview
        }
    
    def render_pagination_controls(self, total_results: int, current_page: int) -> int:
        """Render pagination controls and return selected page"""
        if total_results <= self.results_per_page:
            return current_page
        
        total_pages = math.ceil(total_results / self.results_per_page)
        
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ 最初", disabled=current_page <= 1):
                return 1
        
        with col2:
            if st.button("◀️ 前へ", disabled=current_page <= 1):
                return current_page - 1
        
        with col3:
            # Page selector
            page_options = list(range(1, total_pages + 1))
            selected_page = st.selectbox(
                f"ページ {current_page} / {total_pages}",
                options=page_options,
                index=current_page - 1,
                label_visibility="collapsed"
            )
            if selected_page != current_page:
                return selected_page
        
        with col4:
            if st.button("▶️ 次へ", disabled=current_page >= total_pages):
                return current_page + 1
        
        with col5:
            if st.button("⏭️ 最後", disabled=current_page >= total_pages):
                return total_pages
        
        return current_page
    
    def render_result_item(self, result: Dict[str, Any], index: int, show_preview: bool = True) -> Optional[str]:
        """Render individual search result item"""
        with st.container():
            # Result header
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Title with clickable link
                title = result.get("title", "無題")
                url = result.get("url", "")
                
                if url:
                    st.markdown(f"**{index}. [{title}]({url})**")
                else:
                    st.markdown(f"**{index}. {title}**")
                
                # URL display
                if url:
                    st.caption(f"🔗 {url}")
            
            with col2:
                # Source type badge
                source_type = result.get("source_type", "general")
                if source_type == "official":
                    st.success("🏢 公式")
                elif source_type == "documentation":
                    st.info("📚 ドキュメント")
                elif source_type == "tutorial":
                    st.warning("🎓 チュートリアル")
                else:
                    st.secondary("🌐 一般")
            
            # Description and preview
            if show_preview:
                description = result.get("description", "説明がありません")
                st.markdown(description)
                
                # Additional metadata
                metadata_cols = st.columns(4)
                
                with metadata_cols[0]:
                    confidence = result.get("confidence_score", 0.0)
                    st.metric("関連度", f"{confidence:.1%}")
                
                with metadata_cols[1]:
                    date_found = result.get("date_found")
                    if date_found:
                        st.caption(f"📅 {date_found}")
                
                with metadata_cols[2]:
                    language = result.get("language", "不明")
                    st.caption(f"🌐 {language}")
                
                with metadata_cols[3]:
                    content_size = result.get("content_size")
                    if content_size:
                        st.caption(f"📄 {content_size}")
            
            # Action buttons
            action_cols = st.columns([1, 1, 1, 1, 1])
            
            selected_action = None
            
            with action_cols[0]:
                if st.button("📖 詳細表示", key=f"detail_{index}"):
                    selected_action = "detail"
            
            with action_cols[1]:
                if st.button("🔍 分析", key=f"analyze_{index}"):
                    selected_action = "analyze"
            
            with action_cols[2]:
                if st.button("💾 保存", key=f"save_{index}"):
                    selected_action = "save"
            
            with action_cols[3]:
                if st.button("⭐ 評価", key=f"rate_{index}"):
                    selected_action = "rate"
            
            # Preview toggle for individual items
            if not show_preview:
                with action_cols[4]:
                    if st.button("👁️ プレビュー", key=f"preview_{index}"):
                        selected_action = "preview"
            
            st.markdown("---")
            
            return selected_action
    
    def render_result_preview_modal(self, result: Dict[str, Any]) -> None:
        """Render detailed preview modal for a result"""
        with st.expander(f"📖 詳細プレビュー: {result.get('title', '無題')}", expanded=True):
            
            # Basic information
            st.subheader("基本情報")
            info_cols = st.columns(2)
            
            with info_cols[0]:
                st.write(f"**URL:** {result.get('url', 'N/A')}")
                st.write(f"**タイトル:** {result.get('title', 'N/A')}")
                st.write(f"**言語:** {result.get('language', '不明')}")
            
            with info_cols[1]:
                st.write(f"**ソースタイプ:** {result.get('source_type', '一般')}")
                st.write(f"**関連度:** {result.get('confidence_score', 0.0):.1%}")
                st.write(f"**発見日時:** {result.get('date_found', 'N/A')}")
            
            # Description
            st.subheader("説明")
            st.write(result.get("description", "説明がありません"))
            
            # Content preview (if available)
            content_preview = result.get("content_preview")
            if content_preview:
                st.subheader("コンテンツプレビュー")
                st.text_area(
                    "プレビュー",
                    value=content_preview,
                    height=200,
                    disabled=True,
                    label_visibility="collapsed"
                )
            
            # Technical specifications (for component searches)
            tech_specs = result.get("technical_specs")
            if tech_specs:
                st.subheader("技術仕様")
                st.json(tech_specs)
    
    def render_save_dialog(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Render save dialog for a result"""
        with st.form(f"save_form_{result.get('url', 'unknown')}"):
            st.subheader("💾 結果を保存")
            
            # Save options
            save_title = st.text_input(
                "保存タイトル",
                value=result.get("title", ""),
                help="保存時に使用するタイトル"
            )
            
            category = st.selectbox(
                "カテゴリ",
                options=["一般", "技術資料", "チュートリアル", "公式ドキュメント", "その他"],
                help="結果のカテゴリを選択"
            )
            
            tags = st.text_input(
                "タグ",
                placeholder="例: Python, プログラミング, 入門",
                help="検索用のタグをカンマ区切りで入力"
            )
            
            notes = st.text_area(
                "メモ",
                placeholder="この結果に関するメモや感想を入力",
                help="個人的なメモや評価"
            )
            
            # Save button
            if st.form_submit_button("💾 保存実行", type="primary"):
                return {
                    "title": save_title,
                    "category": category,
                    "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
                    "notes": notes,
                    "url": result.get("url"),
                    "original_result": result
                }
        
        return None
    
    def render_rating_dialog(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Render rating dialog for a result"""
        with st.form(f"rating_form_{result.get('url', 'unknown')}"):
            st.subheader("⭐ 結果を評価")
            
            # Rating options
            usefulness = st.slider(
                "有用性",
                min_value=1,
                max_value=5,
                value=3,
                help="この結果がどの程度有用でしたか？"
            )
            
            accuracy = st.slider(
                "正確性",
                min_value=1,
                max_value=5,
                value=3,
                help="この結果の情報はどの程度正確でしたか？"
            )
            
            relevance = st.slider(
                "関連性",
                min_value=1,
                max_value=5,
                value=3,
                help="検索クエリとの関連性はどの程度でしたか？"
            )
            
            feedback = st.text_area(
                "フィードバック",
                placeholder="この結果に対するフィードバックや改善提案",
                help="任意でフィードバックを入力してください"
            )
            
            # Rating submission
            if st.form_submit_button("⭐ 評価を送信", type="primary"):
                return {
                    "usefulness": usefulness,
                    "accuracy": accuracy,
                    "relevance": relevance,
                    "feedback": feedback,
                    "url": result.get("url"),
                    "timestamp": datetime.now().isoformat()
                }
        
        return None
    
    def apply_filters_and_sorting(self, results: List[Dict[str, Any]], 
                                 filter_option: FilterOption, 
                                 sort_option: SortOption) -> List[Dict[str, Any]]:
        """Apply filters and sorting to results"""
        filtered_results = results.copy()
        
        # Apply filters
        if filter_option == FilterOption.OFFICIAL:
            filtered_results = [r for r in filtered_results if r.get("source_type") == "official"]
        elif filter_option == FilterOption.DOCUMENTATION:
            filtered_results = [r for r in filtered_results if r.get("source_type") == "documentation"]
        elif filter_option == FilterOption.TUTORIAL:
            filtered_results = [r for r in filtered_results if r.get("source_type") == "tutorial"]
        
        # Apply sorting
        if sort_option == SortOption.RELEVANCE:
            filtered_results.sort(key=lambda x: x.get("confidence_score", 0.0), reverse=True)
        elif sort_option == SortOption.DATE:
            filtered_results.sort(key=lambda x: x.get("date_found", ""), reverse=True)
        elif sort_option == SortOption.TITLE:
            filtered_results.sort(key=lambda x: x.get("title", "").lower())
        elif sort_option == SortOption.SOURCE:
            filtered_results.sort(key=lambda x: x.get("source_type", ""))
        
        return filtered_results

def render_search_results(results: List[Dict[str, Any]], 
                         search_query: str = "",
                         results_per_page: int = 5) -> Optional[Dict[str, Any]]:
    """Main function to render search results with all functionality"""
    
    if not results:
        st.warning("⚠️ 表示する検索結果がありません")
        return None
    
    display = ResultsDisplay(results_per_page)
    
    # Initialize session state for pagination and selection
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    if 'selected_result' not in st.session_state:
        st.session_state.selected_result = None
    if 'show_preview_modal' not in st.session_state:
        st.session_state.show_preview_modal = False
    
    # Render header
    display.render_results_header(len(results), search_query)
    
    if len(results) == 0:
        return None
    
    # Render filter and sort controls
    controls = display.render_filter_controls()
    
    # Apply filters and sorting
    filtered_results = display.apply_filters_and_sorting(
        results, controls["filter"], controls["sort"]
    )
    
    # Update results count after filtering
    if len(filtered_results) != len(results):
        st.info(f"フィルター適用後: {len(filtered_results)}件")
    
    # Pagination
    total_filtered = len(filtered_results)
    if total_filtered > 0:
        # Render pagination controls
        new_page = display.render_pagination_controls(total_filtered, st.session_state.current_page)
        if new_page != st.session_state.current_page:
            st.session_state.current_page = new_page
            st.rerun()
        
        # Calculate page bounds
        start_idx = (st.session_state.current_page - 1) * results_per_page
        end_idx = min(start_idx + results_per_page, total_filtered)
        page_results = filtered_results[start_idx:end_idx]
        
        # Render results for current page
        selected_action = None
        selected_result = None
        
        for i, result in enumerate(page_results):
            global_index = start_idx + i + 1
            action = display.render_result_item(result, global_index, controls["show_preview"])
            
            if action:
                selected_action = action
                selected_result = result
        
        # Handle selected actions
        if selected_action and selected_result:
            if selected_action == "detail":
                display.render_result_preview_modal(selected_result)
            elif selected_action == "analyze":
                return {"action": "analyze", "data": selected_result}
            elif selected_action == "save":
                save_data = display.render_save_dialog(selected_result)
                if save_data:
                    st.success("💾 結果が保存されました（実装予定）")
                    return {"action": "save", "data": save_data}
            elif selected_action == "rate":
                rating_data = display.render_rating_dialog(selected_result)
                if rating_data:
                    st.success("⭐ 評価が送信されました（実装予定）")
                    return {"action": "rate", "data": rating_data}
            elif selected_action == "preview":
                display.render_result_preview_modal(selected_result)
        
        # Render bottom pagination
        if total_filtered > results_per_page:
            st.markdown("---")
            display.render_pagination_controls(total_filtered, st.session_state.current_page)
    
    return None
"""
Search interface component for Gemini URL Search Tool
"""

import streamlit as st
from typing import Dict, Any, Optional, Tuple
from enum import Enum
import re

class SearchType(Enum):
    """Search type enumeration"""
    GENERAL = "general"
    COMPONENT = "component"

class SearchInterface:
    """Search interface component for handling user input and validation"""
    
    def __init__(self):
        """Initialize search interface"""
        self.search_type = SearchType.GENERAL
        self.query_data = {}
        
    def render_search_type_selector(self) -> SearchType:
        """Render search type selection UI"""
        st.subheader("🔍 検索タイプを選択")
        
        search_options = {
            "一般検索": SearchType.GENERAL,
            "部品仕様検索": SearchType.COMPONENT
        }
        
        selected_option = st.radio(
            "検索の種類を選択してください:",
            options=list(search_options.keys()),
            horizontal=True,
            help="一般検索: フリーワードでWeb情報を検索\n部品仕様検索: メーカー名と品番で技術仕様を検索"
        )
        
        self.search_type = search_options[selected_option]
        return self.search_type
    
    def render_general_search_form(self) -> Optional[Dict[str, Any]]:
        """Render general search form"""
        st.subheader("📝 一般検索")
        
        with st.form("general_search_form"):
            keywords = st.text_input(
                "検索キーワード",
                placeholder="例: Python プログラミング 入門",
                help="検索したいキーワードやフレーズを入力してください"
            )
            
            # Advanced options in expander
            with st.expander("🔧 詳細オプション"):
                max_results = st.slider(
                    "最大検索結果数",
                    min_value=5,
                    max_value=20,
                    value=10,
                    help="取得する検索結果の最大数"
                )
                
                language_preference = st.selectbox(
                    "言語設定",
                    options=["日本語優先", "英語優先", "言語問わず"],
                    help="検索結果の言語設定"
                )
                
                content_type = st.multiselect(
                    "コンテンツタイプ",
                    options=["記事", "ドキュメント", "チュートリアル", "公式サイト"],
                    default=["記事", "ドキュメント"],
                    help="検索対象とするコンテンツの種類"
                )
            
            submitted = st.form_submit_button(
                "🔍 検索実行",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                validation_result = self._validate_general_search(keywords)
                if validation_result["valid"]:
                    return {
                        "search_type": SearchType.GENERAL,
                        "keywords": keywords.strip(),
                        "max_results": max_results,
                        "language_preference": language_preference,
                        "content_type": content_type
                    }
                else:
                    st.error(validation_result["error"])
                    return None
        
        return None
    
    def render_component_search_form(self) -> Optional[Dict[str, Any]]:
        """Render component specification search form"""
        st.subheader("🔧 部品仕様検索")
        
        with st.form("component_search_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                manufacturer = st.text_input(
                    "メーカー名",
                    placeholder="例: Arduino, Raspberry Pi",
                    help="部品のメーカー名を入力してください"
                )
            
            with col2:
                part_number = st.text_input(
                    "品番・型番",
                    placeholder="例: UNO R3, 4 Model B",
                    help="部品の品番や型番を入力してください"
                )
            
            # Additional search parameters
            with st.expander("🔧 詳細オプション"):
                search_scope = st.selectbox(
                    "検索範囲",
                    options=["公式サイト優先", "データシート優先", "すべて"],
                    help="検索対象の優先順位"
                )
                
                specification_focus = st.multiselect(
                    "重視する仕様",
                    options=["電気特性", "機械特性", "寸法", "ピン配置", "使用例"],
                    default=["電気特性", "寸法"],
                    help="特に重視したい仕様項目"
                )
                
                include_alternatives = st.checkbox(
                    "代替品も検索",
                    value=False,
                    help="類似品や代替品も検索結果に含める"
                )
            
            submitted = st.form_submit_button(
                "🔍 仕様検索実行",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                validation_result = self._validate_component_search(manufacturer, part_number)
                if validation_result["valid"]:
                    return {
                        "search_type": SearchType.COMPONENT,
                        "manufacturer": manufacturer.strip(),
                        "part_number": part_number.strip(),
                        "search_scope": search_scope,
                        "specification_focus": specification_focus,
                        "include_alternatives": include_alternatives
                    }
                else:
                    st.error(validation_result["error"])
                    return None
        
        return None
    
    def render_loading_state(self, message: str = "検索中...") -> None:
        """Render loading state with spinner"""
        with st.spinner(message):
            # Progress bar for visual feedback
            progress_bar = st.progress(0)
            
            # Simulate progress updates (in real implementation, this would be updated by the search service)
            import time
            for i in range(100):
                time.sleep(0.01)  # Small delay for demonstration
                progress_bar.progress(i + 1)
            
            st.success("検索が完了しました！")
    
    def render_search_status(self, status: str, details: Optional[str] = None) -> None:
        """Render search status messages"""
        if status == "searching":
            st.info("🔍 検索を実行しています...")
        elif status == "processing":
            st.info("⚙️ 結果を処理しています...")
        elif status == "completed":
            st.success("✅ 検索が完了しました")
        elif status == "error":
            st.error(f"❌ エラーが発生しました: {details}")
        elif status == "no_results":
            st.warning("⚠️ 検索結果が見つかりませんでした")
        
        if details and status != "error":
            st.caption(details)
    
    def _validate_general_search(self, keywords: str) -> Dict[str, Any]:
        """Validate general search input"""
        if not keywords or not keywords.strip():
            return {
                "valid": False,
                "error": "検索キーワードを入力してください"
            }
        
        # Check minimum length
        if len(keywords.strip()) < 2:
            return {
                "valid": False,
                "error": "検索キーワードは2文字以上で入力してください"
            }
        
        # Check for potentially problematic characters
        if re.search(r'[<>"\']', keywords):
            return {
                "valid": False,
                "error": "検索キーワードに使用できない文字が含まれています"
            }
        
        return {"valid": True}
    
    def _validate_component_search(self, manufacturer: str, part_number: str) -> Dict[str, Any]:
        """Validate component search input"""
        if not manufacturer or not manufacturer.strip():
            return {
                "valid": False,
                "error": "メーカー名を入力してください"
            }
        
        if not part_number or not part_number.strip():
            return {
                "valid": False,
                "error": "品番・型番を入力してください"
            }
        
        # Check minimum lengths
        if len(manufacturer.strip()) < 2:
            return {
                "valid": False,
                "error": "メーカー名は2文字以上で入力してください"
            }
        
        if len(part_number.strip()) < 2:
            return {
                "valid": False,
                "error": "品番・型番は2文字以上で入力してください"
            }
        
        # Check for potentially problematic characters
        if re.search(r'[<>"\']', manufacturer + part_number):
            return {
                "valid": False,
                "error": "入力に使用できない文字が含まれています"
            }
        
        return {"valid": True}
    
    def render_search_history_sidebar(self) -> None:
        """Render search history in sidebar"""
        with st.sidebar:
            st.subheader("📚 検索履歴")
            
            # Placeholder for search history
            # This will be implemented when storage service is integrated
            st.info("検索履歴機能は実装予定です")
            
            # Quick search suggestions
            st.subheader("💡 検索例")
            
            general_examples = [
                "Python プログラミング 入門",
                "React フロントエンド 開発",
                "機械学習 チュートリアル"
            ]
            
            component_examples = [
                ("Arduino", "UNO R3"),
                ("Raspberry Pi", "4 Model B"),
                ("STMicroelectronics", "STM32F103")
            ]
            
            st.caption("一般検索の例:")
            for example in general_examples:
                if st.button(f"🔍 {example}", key=f"general_{example}"):
                    st.session_state.example_query = example
            
            st.caption("部品検索の例:")
            for manufacturer, part in component_examples:
                if st.button(f"🔧 {manufacturer} {part}", key=f"component_{manufacturer}_{part}"):
                    st.session_state.example_manufacturer = manufacturer
                    st.session_state.example_part = part

def render_search_interface() -> Optional[Dict[str, Any]]:
    """Main function to render the complete search interface"""
    interface = SearchInterface()
    
    # Render search type selector
    search_type = interface.render_search_type_selector()
    
    st.markdown("---")
    
    # Render appropriate search form based on type
    if search_type == SearchType.GENERAL:
        search_data = interface.render_general_search_form()
    else:
        search_data = interface.render_component_search_form()
    
    # Render sidebar with history and examples
    interface.render_search_history_sidebar()
    
    return search_data
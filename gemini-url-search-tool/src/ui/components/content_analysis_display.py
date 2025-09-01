"""
Content analysis display component for Gemini URL Search Tool
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class ContentAnalysisDisplay:
    """Component for displaying content analysis and technical specifications"""
    
    def __init__(self):
        """Initialize content analysis display component"""
        pass
    
    def render_analysis_header(self, url: str, title: str) -> None:
        """Render content analysis header"""
        st.subheader("📄 コンテンツ分析")
        
        # URL and title display
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**URL:** [{url}]({url})")
            st.markdown(f"**タイトル:** {title}")
        
        with col2:
            # Analysis timestamp
            st.caption(f"分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    def render_content_summary(self, summary: str, key_points: List[str]) -> None:
        """Render content summary section"""
        st.subheader("📝 要約")
        
        # Main summary
        with st.container():
            st.markdown("### 概要")
            st.write(summary)
        
        # Key points
        if key_points:
            st.markdown("### 主要ポイント")
            for i, point in enumerate(key_points, 1):
                st.markdown(f"**{i}.** {point}")
    
    def render_technical_specifications(self, tech_specs: Dict[str, Any]) -> None:
        """Render technical specifications in structured format"""
        if not tech_specs:
            return
        
        st.subheader("🔧 技術仕様")
        
        # Create tabs for different specification categories
        spec_categories = self._categorize_specifications(tech_specs)
        
        if len(spec_categories) > 1:
            tabs = st.tabs(list(spec_categories.keys()))
            
            for tab, (category, specs) in zip(tabs, spec_categories.items()):
                with tab:
                    self._render_spec_category(specs)
        else:
            # Single category, no tabs needed
            category_name, specs = next(iter(spec_categories.items()))
            self._render_spec_category(specs)
    
    def _categorize_specifications(self, tech_specs: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Categorize technical specifications into logical groups"""
        categories = {
            "基本仕様": {},
            "電気特性": {},
            "機械特性": {},
            "その他": {}
        }
        
        # Define keywords for categorization
        electrical_keywords = ["voltage", "current", "power", "frequency", "電圧", "電流", "電力", "周波数", "抵抗", "容量"]
        mechanical_keywords = ["dimension", "size", "weight", "material", "寸法", "サイズ", "重量", "材質", "厚さ", "幅", "高さ"]
        basic_keywords = ["model", "type", "version", "manufacturer", "モデル", "型番", "バージョン", "メーカー", "品番"]
        
        for key, value in tech_specs.items():
            key_lower = key.lower()
            
            if any(keyword in key_lower for keyword in electrical_keywords):
                categories["電気特性"][key] = value
            elif any(keyword in key_lower for keyword in mechanical_keywords):
                categories["機械特性"][key] = value
            elif any(keyword in key_lower for keyword in basic_keywords):
                categories["基本仕様"][key] = value
            else:
                categories["その他"][key] = value
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def _render_spec_category(self, specs: Dict[str, Any]) -> None:
        """Render specifications for a single category"""
        if not specs:
            st.info("この カテゴリには仕様情報がありません")
            return
        
        # Create a table-like display
        for key, value in specs.items():
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown(f"**{key}:**")
            
            with col2:
                if isinstance(value, (dict, list)):
                    # For complex data, show as JSON
                    with st.expander("詳細表示"):
                        st.json(value)
                else:
                    st.write(str(value))
    
    def render_content_metadata(self, metadata: Dict[str, Any]) -> None:
        """Render content metadata information"""
        st.subheader("ℹ️ メタデータ")
        
        # Create columns for metadata display
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("コンテンツサイズ", metadata.get("content_size", "不明"))
            st.metric("言語", metadata.get("language", "不明"))
        
        with col2:
            st.metric("コンテンツタイプ", metadata.get("content_type", "不明"))
            st.metric("分析時間", f"{metadata.get('analysis_time', 0):.2f}秒")
        
        with col3:
            st.metric("信頼度スコア", f"{metadata.get('confidence_score', 0):.1%}")
            st.metric("最終更新", metadata.get("last_updated", "不明"))
    
    def render_save_content_form(self, content_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Render form to save analyzed content"""
        st.subheader("💾 コンテンツを保存")
        
        with st.form("save_content_form"):
            # Save options
            save_title = st.text_input(
                "保存タイトル",
                value=content_data.get("title", ""),
                help="保存時に使用するタイトル"
            )
            
            category = st.selectbox(
                "カテゴリ",
                options=["技術資料", "仕様書", "チュートリアル", "ドキュメント", "その他"],
                help="コンテンツのカテゴリを選択"
            )
            
            tags = st.text_input(
                "タグ",
                placeholder="例: Arduino, 仕様書, 電子部品",
                help="検索用のタグをカンマ区切りで入力"
            )
            
            # Save options
            col1, col2 = st.columns(2)
            
            with col1:
                save_summary = st.checkbox(
                    "要約を保存",
                    value=True,
                    help="コンテンツの要約を保存"
                )
                
                save_specs = st.checkbox(
                    "技術仕様を保存",
                    value=True,
                    help="技術仕様情報を保存"
                )
            
            with col2:
                save_metadata = st.checkbox(
                    "メタデータを保存",
                    value=True,
                    help="分析メタデータを保存"
                )
                
                create_bookmark = st.checkbox(
                    "ブックマークを作成",
                    value=False,
                    help="クイックアクセス用のブックマークを作成"
                )
            
            notes = st.text_area(
                "メモ",
                placeholder="このコンテンツに関するメモや感想",
                help="個人的なメモや評価"
            )
            
            # Submit button
            if st.form_submit_button("💾 保存実行", type="primary"):
                return {
                    "title": save_title,
                    "category": category,
                    "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
                    "notes": notes,
                    "save_options": {
                        "summary": save_summary,
                        "specs": save_specs,
                        "metadata": save_metadata,
                        "bookmark": create_bookmark
                    },
                    "content_data": content_data,
                    "timestamp": datetime.now().isoformat()
                }
        
        return None
    
    def render_evaluation_form(self, content_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Render form to evaluate analyzed content"""
        st.subheader("⭐ コンテンツを評価")
        
        with st.form("evaluate_content_form"):
            # Evaluation metrics
            col1, col2 = st.columns(2)
            
            with col1:
                usefulness = st.slider(
                    "有用性",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="このコンテンツはどの程度有用でしたか？"
                )
                
                accuracy = st.slider(
                    "正確性",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="分析結果の正確性はどの程度でしたか？"
                )
            
            with col2:
                completeness = st.slider(
                    "完全性",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="必要な情報がどの程度含まれていましたか？"
                )
                
                clarity = st.slider(
                    "明確性",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="情報の表示は分かりやすかったですか？"
                )
            
            # Time saved estimation
            time_saved = st.selectbox(
                "時間短縮効果",
                options=[
                    ("なし", 0),
                    ("5分程度", 5),
                    ("15分程度", 15),
                    ("30分程度", 30),
                    ("1時間以上", 60)
                ],
                format_func=lambda x: x[0],
                help="このツールによってどの程度の時間を節約できましたか？"
            )
            
            # Feedback
            feedback = st.text_area(
                "フィードバック",
                placeholder="改善提案や感想をお聞かせください",
                help="ツールの改善に役立てるためのフィードバック"
            )
            
            # Recommendation
            would_recommend = st.radio(
                "推奨度",
                options=["強く推奨", "推奨", "どちらでもない", "推奨しない", "強く推奨しない"],
                horizontal=True,
                help="このツールを他の人に推奨しますか？"
            )
            
            # Submit evaluation
            if st.form_submit_button("⭐ 評価を送信", type="primary"):
                return {
                    "usefulness": usefulness,
                    "accuracy": accuracy,
                    "completeness": completeness,
                    "clarity": clarity,
                    "time_saved_minutes": time_saved[1],
                    "feedback": feedback,
                    "recommendation": would_recommend,
                    "url": content_data.get("url"),
                    "timestamp": datetime.now().isoformat()
                }
        
        return None
    
    def render_content_actions(self, content_data: Dict[str, Any]) -> Optional[str]:
        """Render action buttons for content"""
        st.subheader("🎯 アクション")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 保存", use_container_width=True):
                return "save"
        
        with col2:
            if st.button("⭐ 評価", use_container_width=True):
                return "evaluate"
        
        with col3:
            if st.button("🔄 再分析", use_container_width=True):
                return "reanalyze"
        
        with col4:
            if st.button("📤 共有", use_container_width=True):
                return "share"
        
        return None
    
    def render_related_content(self, related_items: List[Dict[str, Any]]) -> None:
        """Render related content suggestions"""
        if not related_items:
            return
        
        st.subheader("🔗 関連コンテンツ")
        
        for item in related_items[:3]:  # Show top 3 related items
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**[{item.get('title', '無題')}]({item.get('url', '#')})**")
                    st.caption(item.get('description', '説明なし'))
                
                with col2:
                    similarity = item.get('similarity_score', 0.0)
                    st.metric("類似度", f"{similarity:.1%}")
                
                st.markdown("---")

def render_content_analysis(content_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Main function to render complete content analysis display"""
    
    if not content_data:
        st.warning("⚠️ 表示するコンテンツ分析データがありません")
        return None
    
    display = ContentAnalysisDisplay()
    
    # Render header
    display.render_analysis_header(
        url=content_data.get("url", ""),
        title=content_data.get("title", "無題")
    )
    
    st.markdown("---")
    
    # Render content summary
    summary = content_data.get("summary", "")
    key_points = content_data.get("key_points", [])
    
    if summary or key_points:
        display.render_content_summary(summary, key_points)
        st.markdown("---")
    
    # Render technical specifications
    tech_specs = content_data.get("technical_specs", {})
    if tech_specs:
        display.render_technical_specifications(tech_specs)
        st.markdown("---")
    
    # Render metadata
    metadata = content_data.get("metadata", {})
    if metadata:
        display.render_content_metadata(metadata)
        st.markdown("---")
    
    # Render action buttons
    selected_action = display.render_content_actions(content_data)
    
    # Handle actions
    if selected_action:
        if selected_action == "save":
            save_data = display.render_save_content_form(content_data)
            if save_data:
                st.success("💾 コンテンツが保存されました")
                return {"action": "save", "data": save_data}
        
        elif selected_action == "evaluate":
            evaluation_data = display.render_evaluation_form(content_data)
            if evaluation_data:
                st.success("⭐ 評価が送信されました")
                return {"action": "evaluate", "data": evaluation_data}
        
        elif selected_action == "reanalyze":
            st.info("🔄 再分析機能は ContentService 統合後に実装されます")
            return {"action": "reanalyze", "url": content_data.get("url")}
        
        elif selected_action == "share":
            st.info("📤 共有機能は後のバージョンで実装予定です")
            return {"action": "share", "data": content_data}
    
    # Render related content (if available)
    related_content = content_data.get("related_content", [])
    if related_content:
        st.markdown("---")
        display.render_related_content(related_content)
    
    return None

def create_sample_content_analysis() -> Dict[str, Any]:
    """Create sample content analysis data for testing"""
    return {
        "url": "https://example.com/arduino-uno-specs",
        "title": "Arduino UNO R3 - 公式仕様書",
        "summary": "Arduino UNO R3は、ATmega328Pマイクロコントローラーを搭載した開発ボードです。14個のデジタル入出力ピン、6個のアナログ入力、16MHzクリスタル発振器、USB接続、電源ジャック、ICSPヘッダー、リセットボタンを備えています。",
        "key_points": [
            "ATmega328Pマイクロコントローラー搭載",
            "14個のデジタルI/Oピン（うち6個はPWM出力対応）",
            "6個のアナログ入力ピン",
            "16MHz動作クロック",
            "USB経由でのプログラミングと電源供給",
            "5V/3.3V動作電圧"
        ],
        "technical_specs": {
            "マイクロコントローラー": "ATmega328P",
            "動作電圧": "5V",
            "入力電圧（推奨）": "7-12V",
            "入力電圧（限界）": "6-20V",
            "デジタルI/Oピン": "14個（うち6個PWM出力）",
            "PWMデジタルI/Oピン": "6個",
            "アナログ入力ピン": "6個",
            "DC電流（I/Oピン）": "20mA",
            "DC電流（3.3Vピン）": "50mA",
            "フラッシュメモリ": "32KB（うち0.5KBはブートローダー）",
            "SRAM": "2KB",
            "EEPROM": "1KB",
            "クロック速度": "16MHz",
            "LED_BUILTIN": "13番ピンに接続",
            "長さ": "68.6mm",
            "幅": "53.4mm",
            "重量": "25g"
        },
        "metadata": {
            "content_size": "15.2KB",
            "language": "日本語",
            "content_type": "技術仕様書",
            "analysis_time": 2.34,
            "confidence_score": 0.92,
            "last_updated": "2024-01-15"
        },
        "related_content": [
            {
                "title": "Arduino IDE セットアップガイド",
                "url": "https://example.com/arduino-ide-setup",
                "description": "Arduino開発環境のインストールと設定方法",
                "similarity_score": 0.85
            },
            {
                "title": "Arduino プログラミング基礎",
                "url": "https://example.com/arduino-programming",
                "description": "Arduinoプログラミングの基本概念とサンプルコード",
                "similarity_score": 0.78
            }
        ]
    }
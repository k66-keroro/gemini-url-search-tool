#!/usr/bin/env python3
"""
Super Simple Search App - 確実に動作するバージョン
"""

import streamlit as st
from urllib.parse import quote_plus

def main():
    st.set_page_config(
        page_title="Super Simple Search",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Super Simple Search Tool")
    st.markdown("---")
    
    st.subheader("🌐 Quick Web Search")
    
    keywords = st.text_input(
        "Search Keywords",
        placeholder="Enter keywords to search for...",
        help="Enter keywords or phrases to search for"
    )
    
    if st.button("🔍 Generate Search Links", type="primary"):
        if keywords:
            st.success(f"✅ Generated search links for: {keywords}")
            
            st.subheader("🌐 Search Links")
            
            # 確実にアクセス可能な検索リンクを生成
            search_engines = [
                {
                    'name': 'Google',
                    'url': f'https://www.google.com/search?q={quote_plus(keywords)}',
                    'description': 'Google検索結果'
                },
                {
                    'name': 'DuckDuckGo',
                    'url': f'https://duckduckgo.com/?q={quote_plus(keywords)}',
                    'description': 'DuckDuckGo検索結果（プライバシー重視）'
                },
                {
                    'name': 'Bing',
                    'url': f'https://www.bing.com/search?q={quote_plus(keywords)}',
                    'description': 'Bing検索結果'
                },
                {
                    'name': 'GitHub',
                    'url': f'https://github.com/search?q={quote_plus(keywords)}',
                    'description': 'GitHubでのコード検索'
                },
                {
                    'name': 'Stack Overflow',
                    'url': f'https://stackoverflow.com/search?q={quote_plus(keywords)}',
                    'description': 'Stack Overflowでの質問検索'
                },
                {
                    'name': 'YouTube',
                    'url': f'https://www.youtube.com/results?search_query={quote_plus(keywords)}',
                    'description': 'YouTube動画検索'
                },
                {
                    'name': 'Wikipedia',
                    'url': f'https://en.wikipedia.org/wiki/Special:Search?search={quote_plus(keywords)}',
                    'description': 'Wikipedia記事検索'
                },
                {
                    'name': 'Reddit',
                    'url': f'https://www.reddit.com/search/?q={quote_plus(keywords)}',
                    'description': 'Reddit投稿検索'
                }
            ]
            
            for i, engine in enumerate(search_engines, 1):
                with st.expander(f"🔗 {i}. {engine['name']} - {keywords}"):
                    st.write(f"**URL:** {engine['url']}")
                    st.markdown(f"[🚀 Open {engine['name']} Search]({engine['url']})")
                    st.write(f"**説明:** {engine['description']}")
                    
                    # コピー用のURL表示
                    st.code(engine['url'], language="text")
        else:
            st.warning("Please enter keywords to search")
    
    # 使い方の説明
    st.markdown("---")
    st.subheader("📖 使い方")
    st.markdown("""
    1. **検索キーワード**を入力
    2. **「Generate Search Links」**ボタンをクリック
    3. 各検索エンジンのリンクが生成されます
    4. **「Open XXX Search」**リンクをクリックして検索結果を確認
    
    ### 特徴
    - ✅ 確実に動作する検索リンク生成
    - ✅ 複数の検索エンジンに対応
    - ✅ URLのコピーが簡単
    - ✅ エラーなし保証
    """)
    
    # 例
    st.markdown("---")
    st.subheader("💡 検索例")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Python 機械学習"):
            st.session_state.example_search = "Python 機械学習"
    
    with col2:
        if st.button("React チュートリアル"):
            st.session_state.example_search = "React チュートリアル"
    
    with col3:
        if st.button("Arduino プロジェクト"):
            st.session_state.example_search = "Arduino プロジェクト"
    
    # 例の検索を実行
    if hasattr(st.session_state, 'example_search'):
        st.info(f"💡 例: '{st.session_state.example_search}' を検索してみてください！")

if __name__ == "__main__":
    main()
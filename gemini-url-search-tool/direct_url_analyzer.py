#!/usr/bin/env python3
"""
Direct URL Analyzer - URLを直接入力してサイト内容を要約するツール
"""

import streamlit as st
import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import google.generativeai as genai
import time

# Load environment variables
load_dotenv()

def fetch_page_content(url, timeout=15):
    """ページの内容を取得してテキストを抽出"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        st.info(f"🌐 Fetching content from: {url}")
        
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        st.success(f"✅ HTTP {response.status_code} - Content fetched successfully")
        
        # HTMLを解析してテキストを抽出
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # ページタイトルを取得
        title = soup.find('title')
        page_title = title.get_text().strip() if title else "No Title"
        
        # 不要な要素を削除
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            element.decompose()
        
        # メインコンテンツを取得（優先順位付き）
        main_content = None
        for selector in ['main', 'article', '.content', '.main-content', '#content', '#main']:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # メインコンテンツが見つからない場合はbody全体を使用
        if not main_content:
            main_content = soup.find('body') or soup
        
        # テキストを取得
        text = main_content.get_text()
        
        # 空白を整理
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # 長すぎる場合は切り詰め
        if len(text) > 10000:
            text = text[:10000] + "..."
        
        return {
            'title': page_title,
            'content': text,
            'url': response.url,  # 最終的なURL（リダイレクト後）
            'status_code': response.status_code,
            'content_length': len(text)
        }
        
    except requests.exceptions.Timeout:
        return {'error': f"タイムアウト: {url} への接続がタイムアウトしました"}
    except requests.exceptions.ConnectionError:
        return {'error': f"接続エラー: {url} に接続できませんでした"}
    except requests.exceptions.HTTPError as e:
        return {'error': f"HTTPエラー: {e}"}
    except Exception as e:
        return {'error': f"予期しないエラー: {str(e)}"}

def summarize_content_with_gemini(content_data, focus_query, api_key):
    """Gemini APIを使用してコンテンツを要約"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        title = content_data.get('title', 'No Title')
        content = content_data.get('content', '')
        url = content_data.get('url', '')
        
        prompt = f"""
以下のWebページの内容を分析し、要約してください。

【ページ情報】
- タイトル: {title}
- URL: {url}
- 検索テーマ: {focus_query}

【要約の指針】
1. ページの主要な内容を把握
2. 検索テーマ「{focus_query}」に関連する情報を重点的に抽出
3. 重要なポイントを3-5個に整理
4. 技術的な詳細や数値があれば含める
5. 実用的で分かりやすい日本語で300-500文字程度

【Webページ内容】
{content[:8000]}

【要約結果】
"""
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"要約エラー: {str(e)}"

def main():
    """メインアプリケーション"""
    st.set_page_config(
        page_title="Direct URL Content Analyzer",
        page_icon="🔗",
        layout="wide"
    )
    
    st.title("🔗 Direct URL Content Analyzer")
    st.markdown("**URLを直接入力してサイト内容を取得・要約**")
    st.markdown("---")
    
    # API key check
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        st.success("✅ Gemini API key configured")
    else:
        st.error("❌ Gemini API key not found. Please set GEMINI_API_KEY in .env file")
        st.stop()
    
    # URL input
    st.subheader("🌐 URL Input")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        url = st.text_input(
            "URL",
            placeholder="https://example.com",
            help="分析したいWebページのURLを入力"
        )
    
    with col2:
        timeout = st.number_input("Timeout (seconds)", min_value=5, max_value=60, value=15)
    
    focus_query = st.text_input(
        "Focus Query (Optional)",
        placeholder="例: Python 機械学習",
        help="特定のテーマに焦点を当てたい場合は入力"
    )
    
    if st.button("🔍 Analyze URL", type="primary"):
        if url:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            with st.spinner("Fetching content..."):
                # Step 1: Fetch content
                content_data = fetch_page_content(url, timeout)
                
                if 'error' in content_data:
                    st.error(f"❌ {content_data['error']}")
                else:
                    st.success(f"✅ Content fetched: {content_data['content_length']} characters")
                    
                    # Show page info
                    st.subheader("📄 Page Information")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Title:** {content_data['title']}")
                        st.write(f"**Final URL:** {content_data['url']}")
                    
                    with col2:
                        st.write(f"**Status Code:** {content_data['status_code']}")
                        st.write(f"**Content Length:** {content_data['content_length']} chars")
                    
                    # Show content preview
                    with st.expander("📝 Content Preview"):
                        preview_text = content_data['content'][:2000]
                        if len(content_data['content']) > 2000:
                            preview_text += "..."
                        st.text_area(
                            "Raw Content (first 2000 chars)",
                            preview_text,
                            height=300
                        )
                    
                    # Step 2: Summarize with Gemini
                    with st.spinner("Generating AI summary..."):
                        summary = summarize_content_with_gemini(
                            content_data, 
                            focus_query or "general analysis", 
                            api_key
                        )
                        
                        st.subheader("🤖 AI Summary")
                        st.markdown(f"""
                        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #1f77b4;">
                        {summary}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Save to session state
                        if 'analysis_history' not in st.session_state:
                            st.session_state.analysis_history = []
                        
                        st.session_state.analysis_history.append({
                            'url': content_data['url'],
                            'title': content_data['title'],
                            'summary': summary,
                            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                            'focus_query': focus_query or "general"
                        })
        else:
            st.warning("Please enter a URL")
    
    # Analysis history
    if hasattr(st.session_state, 'analysis_history') and st.session_state.analysis_history:
        st.markdown("---")
        st.subheader("📚 Analysis History")
        
        for i, analysis in enumerate(reversed(st.session_state.analysis_history), 1):
            with st.expander(f"Analysis {i}: {analysis['title'][:50]}..."):
                st.write(f"**URL:** {analysis['url']}")
                st.write(f"**Focus:** {analysis['focus_query']}")
                st.write(f"**Time:** {analysis['timestamp']}")
                st.write(f"**Summary:** {analysis['summary']}")
    
    # Quick test URLs
    st.markdown("---")
    st.subheader("🧪 Quick Test URLs")
    
    test_urls = [
        ("Wikipedia - Python", "https://en.wikipedia.org/wiki/Python_(programming_language)"),
        ("Python.org", "https://www.python.org/"),
        ("Stack Overflow - Python", "https://stackoverflow.com/questions/tagged/python"),
        ("GitHub - Python", "https://github.com/python/cpython"),
    ]
    
    cols = st.columns(len(test_urls))
    for i, (name, test_url) in enumerate(test_urls):
        with cols[i]:
            if st.button(name, key=f"test_{i}"):
                st.session_state.test_url = test_url
                st.rerun()
    
    # Auto-fill test URL
    if hasattr(st.session_state, 'test_url'):
        st.text_input("URL", value=st.session_state.test_url, key="auto_url")
        del st.session_state.test_url
    
    # Clear history
    if st.button("🗑️ Clear History"):
        if 'analysis_history' in st.session_state:
            del st.session_state.analysis_history
        st.rerun()

if __name__ == "__main__":
    main()
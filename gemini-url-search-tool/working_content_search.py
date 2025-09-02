#!/usr/bin/env python3
"""
Working Content Search App - 実際にサイト内容を取得して要約するツール
"""

import streamlit as st
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus
import time
from bs4 import BeautifulSoup
import google.generativeai as genai

# Load environment variables
load_dotenv()

def search_duckduckgo(query, num_results=3):
    """DuckDuckGo検索"""
    try:
        url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        results = []
        
        # Related Topics から結果を取得
        if 'RelatedTopics' in data:
            for topic in data['RelatedTopics'][:num_results]:
                if isinstance(topic, dict) and 'FirstURL' in topic:
                    results.append({
                        'title': topic.get('Text', 'No Title')[:100],
                        'url': topic.get('FirstURL', ''),
                        'description': topic.get('Text', 'No description available')
                    })
        
        return results
        
    except Exception as e:
        st.error(f"Search failed: {str(e)}")
        return []

def fetch_page_content(url, timeout=10):
    """ページの内容を取得してテキストを抽出"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # HTMLを解析してテキストを抽出
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 不要な要素を削除
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # テキストを取得
        text = soup.get_text()
        
        # 空白を整理
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # 長すぎる場合は切り詰め
        if len(text) > 8000:
            text = text[:8000] + "..."
        
        return text
        
    except Exception as e:
        return f"Error fetching content: {str(e)}"

def summarize_content_with_gemini(content, query, api_key):
    """Gemini APIを使用してコンテンツを要約"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
以下のWebページの内容を、検索クエリ「{query}」に関連する部分を中心に要約してください。

【要約の指針】
1. 検索クエリに最も関連する情報を優先
2. 重要なポイントを3-5個に絞る
3. 技術的な詳細があれば含める
4. 実用的な情報を重視
5. 日本語で200-400文字程度

【Webページ内容】
{content[:6000]}

【要約】
"""
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"要約エラー: {str(e)}"

def main():
    """メインアプリケーション"""
    st.set_page_config(
        page_title="Content Search & Summary Tool",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 Content Search & Summary Tool")
    st.markdown("**検索 → 内容取得 → AI要約** の完全版")
    st.markdown("---")
    
    # API key check
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        st.success("✅ Gemini API key configured")
    else:
        st.error("❌ Gemini API key not found. Please set GEMINI_API_KEY in .env file")
        st.stop()
    
    # Search interface
    st.subheader("🔍 Step 1: Web Search")
    
    keywords = st.text_input(
        "Search Keywords",
        placeholder="例: Python 機械学習",
        help="検索したいキーワードを入力"
    )
    
    num_results = st.slider("Number of Results", 1, 5, 3)
    
    if st.button("🔍 Search", type="primary"):
        if keywords:
            with st.spinner("Searching..."):
                results = search_duckduckgo(keywords, num_results)
                
                if results:
                    st.session_state.search_results = results
                    st.session_state.search_query = keywords
                    st.success(f"✅ Found {len(results)} results")
                else:
                    st.warning("No results found")
        else:
            st.warning("Please enter keywords")
    
    # Display search results and fetch content
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.markdown("---")
        st.subheader("📄 Step 2: Content Analysis")
        
        for i, result in enumerate(st.session_state.search_results, 1):
            with st.expander(f"Result {i}: {result['title']}", expanded=True):
                st.write(f"**URL:** {result['url']}")
                st.write(f"**Description:** {result['description']}")
                
                if st.button(f"📄 Get Content & Summary", key=f"fetch_{i}"):
                    with st.spinner(f"Fetching content from {result['url']}..."):
                        # Step 1: Fetch content
                        content = fetch_page_content(result['url'])
                        
                        if content and not content.startswith("Error"):
                            st.success("✅ Content fetched successfully")
                            
                            # Show content preview
                            with st.expander("📝 Content Preview"):
                                st.text_area(
                                    "Raw Content (first 1000 chars)",
                                    content[:1000] + "..." if len(content) > 1000 else content,
                                    height=200
                                )
                            
                            # Step 2: Summarize with Gemini
                            with st.spinner("Generating AI summary..."):
                                summary = summarize_content_with_gemini(
                                    content, 
                                    st.session_state.search_query, 
                                    api_key
                                )
                                
                                st.subheader("🤖 AI Summary")
                                st.markdown(f"""
                                <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #1f77b4;">
                                {summary}
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Save to session state for comparison
                                if 'summaries' not in st.session_state:
                                    st.session_state.summaries = []
                                
                                st.session_state.summaries.append({
                                    'title': result['title'],
                                    'url': result['url'],
                                    'summary': summary
                                })
                        else:
                            st.error(f"❌ Failed to fetch content: {content}")
    
    # Summary comparison
    if hasattr(st.session_state, 'summaries') and st.session_state.summaries:
        st.markdown("---")
        st.subheader("📊 Step 3: Summary Comparison")
        
        if st.button("🔄 Generate Combined Analysis"):
            with st.spinner("Generating combined analysis..."):
                all_summaries = "\n\n".join([
                    f"【{s['title']}】\n{s['summary']}" 
                    for s in st.session_state.summaries
                ])
                
                combined_prompt = f"""
以下は検索クエリ「{st.session_state.search_query}」に関する複数のWebサイトの要約です。
これらを統合して、総合的な分析を提供してください。

【要求】
1. 共通するテーマや情報を特定
2. 各サイトの独自の情報を整理
3. 最も有用な情報源を推奨
4. さらに調べるべき点があれば提案

【各サイトの要約】
{all_summaries}

【総合分析】
"""
                
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(combined_prompt)
                    
                    st.subheader("🎯 Combined Analysis")
                    st.markdown(f"""
                    <div style="background-color: #e8f5e8; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745;">
                    {response.text}
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Combined analysis failed: {str(e)}")
        
        # Individual summaries
        st.subheader("📋 Individual Summaries")
        for i, summary_data in enumerate(st.session_state.summaries, 1):
            with st.expander(f"Summary {i}: {summary_data['title']}"):
                st.write(f"**URL:** {summary_data['url']}")
                st.write(f"**Summary:** {summary_data['summary']}")
    
    # Clear results
    if st.button("🗑️ Clear All Results"):
        for key in ['search_results', 'search_query', 'summaries']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()
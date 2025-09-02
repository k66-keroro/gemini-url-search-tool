#!/usr/bin/env python3
"""
Smart Search & Filter Tool - 検索→URL絞り込み→要約の完全版
"""

import streamlit as st
import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import google.generativeai as genai
import time
from urllib.parse import quote_plus, urlparse
import re

# Load environment variables
load_dotenv()

def search_with_google_fallback(query, num_results=10):
    """Google検索の代替として、複数の方法を試す"""
    results = []
    
    # Method 1: Wikipedia検索
    try:
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote_plus(query)}&limit=3&format=json"
        response = requests.get(wiki_url, timeout=10)
        data = response.json()
        
        if len(data) >= 4:
            titles = data[1]
            descriptions = data[2]
            urls = data[3]
            
            for i in range(min(len(titles), 3)):
                results.append({
                    'title': f"{titles[i]} - Wikipedia",
                    'url': urls[i],
                    'description': descriptions[i] if i < len(descriptions) else "Wikipedia article",
                    'source': 'Wikipedia'
                })
    except:
        pass
    
    # Method 2: GitHub検索
    try:
        github_url = f"https://api.github.com/search/repositories?q={quote_plus(query)}&sort=stars&order=desc&per_page=3"
        response = requests.get(github_url, timeout=10)
        data = response.json()
        
        if 'items' in data:
            for repo in data['items'][:3]:
                results.append({
                    'title': f"{repo['name']} - GitHub",
                    'url': repo['html_url'],
                    'description': repo.get('description', 'GitHub repository'),
                    'source': 'GitHub'
                })
    except:
        pass
    
    # Method 3: 手動で関連サイトを追加
    manual_sites = {
        'python': [
            {'title': 'Python.org - Official Site', 'url': 'https://www.python.org/', 'description': 'Official Python website'},
            {'title': 'Python Documentation', 'url': 'https://docs.python.org/3/', 'description': 'Official Python documentation'},
            {'title': 'Real Python', 'url': 'https://realpython.com/', 'description': 'Python tutorials and articles'},
        ],
        'machine learning': [
            {'title': 'Scikit-learn', 'url': 'https://scikit-learn.org/', 'description': 'Machine learning library for Python'},
            {'title': 'TensorFlow', 'url': 'https://www.tensorflow.org/', 'description': 'Open source machine learning platform'},
        ],
        'javascript': [
            {'title': 'MDN Web Docs', 'url': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript', 'description': 'JavaScript documentation'},
            {'title': 'JavaScript.info', 'url': 'https://javascript.info/', 'description': 'Modern JavaScript tutorial'},
        ]
    }
    
    query_lower = query.lower()
    for keyword, sites in manual_sites.items():
        if keyword in query_lower:
            for site in sites:
                site['source'] = 'Manual'
                results.append(site)
    
    return results[:num_results]

def filter_urls_with_ai(results, query, api_key):
    """AIを使ってURLを関連性で絞り込み"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        results_text = "\n".join([
            f"{i+1}. {r['title']} - {r['url']} - {r['description']}"
            for i, r in enumerate(results)
        ])
        
        filter_prompt = f"""
検索クエリ「{query}」に対して、以下の検索結果を関連性の高い順に並び替えて、上位5つを選んでください。

【検索結果】
{results_text}

【選択基準】
1. 検索クエリとの関連性
2. 情報の信頼性（公式サイト、有名サイト優先）
3. 内容の充実度

【回答形式】
選択した結果の番号を関連性の高い順に5つまで、理由と共に回答してください。
例: 1, 3, 5, 2, 7
理由: 1番は公式サイトで最も関連性が高い、3番は...

番号のみ:
"""
        
        response = model.generate_content(filter_prompt)
        
        # 番号を抽出
        numbers = re.findall(r'\b(\d+)\b', response.text)
        selected_indices = []
        
        for num_str in numbers[:5]:  # 上位5つまで
            try:
                idx = int(num_str) - 1  # 1-based to 0-based
                if 0 <= idx < len(results):
                    selected_indices.append(idx)
            except:
                continue
        
        # 重複を除去しつつ順序を保持
        unique_indices = []
        for idx in selected_indices:
            if idx not in unique_indices:
                unique_indices.append(idx)
        
        filtered_results = [results[i] for i in unique_indices]
        
        return filtered_results, response.text
        
    except Exception as e:
        st.warning(f"AI filtering failed: {e}. Using original results.")
        return results[:5], "AI filtering unavailable"

def fetch_page_content(url, timeout=15):
    """ページの内容を取得"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # タイトル取得
        title = soup.find('title')
        page_title = title.get_text().strip() if title else "No Title"
        
        # 不要な要素を削除
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # テキスト抽出
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        if len(text) > 8000:
            text = text[:8000] + "..."
        
        return {
            'title': page_title,
            'content': text,
            'url': response.url,
            'success': True
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'success': False
        }

def summarize_content(content_data, query, api_key):
    """コンテンツを要約"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
以下のWebページ内容を、検索クエリ「{query}」の観点から要約してください。

【ページ情報】
タイトル: {content_data['title']}
URL: {content_data['url']}

【要約指針】
1. 検索クエリに最も関連する情報を重点的に抽出
2. 重要なポイントを3-4個に整理
3. 実用的で分かりやすい日本語で200-300文字

【内容】
{content_data['content'][:6000]}

【要約】
"""
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"要約エラー: {str(e)}"

def main():
    st.set_page_config(
        page_title="Smart Search & Filter Tool",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 Smart Search & Filter Tool")
    st.markdown("**検索 → AI絞り込み → 内容要約**")
    st.markdown("---")
    
    # API key check
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        st.success("✅ Gemini API key configured")
    else:
        st.error("❌ Gemini API key not found")
        st.stop()
    
    # Step 1: Search
    st.subheader("🔍 Step 1: Search")
    
    query = st.text_input(
        "Search Query",
        placeholder="例: Python 機械学習",
        help="検索したいキーワードを入力"
    )
    
    num_results = st.slider("Initial Results", 5, 15, 10)
    
    if st.button("🔍 Search", type="primary"):
        if query:
            with st.spinner("Searching..."):
                results = search_with_google_fallback(query, num_results)
                
                if results:
                    st.session_state.search_results = results
                    st.session_state.search_query = query
                    st.success(f"✅ Found {len(results)} results")
                else:
                    st.warning("No results found")
        else:
            st.warning("Please enter a search query")
    
    # Step 2: AI Filtering
    if hasattr(st.session_state, 'search_results'):
        st.markdown("---")
        st.subheader("🎯 Step 2: AI Filtering")
        
        st.write(f"**Original Results:** {len(st.session_state.search_results)}")
        
        if st.button("🤖 Filter with AI"):
            with st.spinner("AI is filtering results..."):
                filtered_results, reasoning = filter_urls_with_ai(
                    st.session_state.search_results,
                    st.session_state.search_query,
                    api_key
                )
                
                st.session_state.filtered_results = filtered_results
                st.session_state.filter_reasoning = reasoning
                
                st.success(f"✅ Filtered to {len(filtered_results)} most relevant results")
                
                with st.expander("🧠 AI Reasoning"):
                    st.write(reasoning)
    
    # Step 3: Content Analysis
    if hasattr(st.session_state, 'filtered_results'):
        st.markdown("---")
        st.subheader("📄 Step 3: Content Analysis")
        
        for i, result in enumerate(st.session_state.filtered_results, 1):
            with st.expander(f"Result {i}: {result['title']}", expanded=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**URL:** {result['url']}")
                    st.write(f"**Description:** {result['description']}")
                    st.write(f"**Source:** {result.get('source', 'Unknown')}")
                
                with col2:
                    if st.button(f"📄 Analyze", key=f"analyze_{i}"):
                        with st.spinner(f"Analyzing content..."):
                            content_data = fetch_page_content(result['url'])
                            
                            if content_data['success']:
                                st.success("✅ Content fetched")
                                
                                summary = summarize_content(
                                    content_data,
                                    st.session_state.search_query,
                                    api_key
                                )
                                
                                st.subheader("🤖 AI Summary")
                                st.markdown(f"""
                                <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px;">
                                {summary}
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Save summary
                                if 'summaries' not in st.session_state:
                                    st.session_state.summaries = []
                                
                                st.session_state.summaries.append({
                                    'title': result['title'],
                                    'url': result['url'],
                                    'summary': summary
                                })
                            else:
                                st.error(f"❌ Failed: {content_data['error']}")
    
    # Combined Analysis
    if hasattr(st.session_state, 'summaries') and len(st.session_state.summaries) >= 2:
        st.markdown("---")
        st.subheader("🎯 Combined Analysis")
        
        if st.button("🔄 Generate Combined Summary"):
            with st.spinner("Generating combined analysis..."):
                all_summaries = "\n\n".join([
                    f"【{s['title']}】\n{s['summary']}"
                    for s in st.session_state.summaries
                ])
                
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    combined_prompt = f"""
検索クエリ「{st.session_state.search_query}」について、複数のWebサイトから得られた情報を統合分析してください。

【各サイトの要約】
{all_summaries}

【統合分析の要求】
1. 共通する重要なポイントを特定
2. 各サイト独自の有用な情報を整理
3. 最も信頼できる情報源を推奨
4. 全体的な結論と次のアクション提案

【統合分析結果】
"""
                    
                    response = model.generate_content(combined_prompt)
                    
                    st.markdown(f"""
                    <div style="background-color: #e8f5e8; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745;">
                    <h4>🎯 統合分析結果</h4>
                    {response.text}
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Combined analysis failed: {e}")
    
    # Clear all
    if st.button("🗑️ Clear All"):
        for key in ['search_results', 'filtered_results', 'summaries', 'search_query', 'filter_reasoning']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()
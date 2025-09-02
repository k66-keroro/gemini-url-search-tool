#!/usr/bin/env python3
"""
Smart Overview & Detail Tool - 概要一覧→詳細表示の理想的なUI
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

def search_with_multiple_sources(query, num_results=10):
    """複数のソースから検索結果を取得"""
    results = []
    
    # Wikipedia検索
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
                    'source': 'Wikipedia',
                    'confidence': 0.9
                })
    except:
        pass
    
    # GitHub検索
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
                    'source': 'GitHub',
                    'confidence': 0.8
                })
    except:
        pass
    
    # 手動で高品質サイトを追加
    manual_sites = {
        'python': [
            {'title': 'Python.org - Official Site', 'url': 'https://www.python.org/', 'description': 'Official Python programming language website', 'confidence': 1.0},
            {'title': 'Python Documentation', 'url': 'https://docs.python.org/3/', 'description': 'Comprehensive Python documentation', 'confidence': 1.0},
            {'title': 'Real Python Tutorials', 'url': 'https://realpython.com/', 'description': 'High-quality Python tutorials and articles', 'confidence': 0.9},
        ],
        'machine learning': [
            {'title': 'Scikit-learn', 'url': 'https://scikit-learn.org/', 'description': 'Machine learning library for Python', 'confidence': 0.9},
            {'title': 'TensorFlow', 'url': 'https://www.tensorflow.org/', 'description': 'Open source machine learning platform', 'confidence': 0.9},
        ],
        'javascript': [
            {'title': 'MDN Web Docs - JavaScript', 'url': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript', 'description': 'Comprehensive JavaScript documentation', 'confidence': 1.0},
            {'title': 'JavaScript.info', 'url': 'https://javascript.info/', 'description': 'Modern JavaScript tutorial', 'confidence': 0.9},
        ],
        'react': [
            {'title': 'React Official Docs', 'url': 'https://react.dev/', 'description': 'Official React documentation', 'confidence': 1.0},
        ]
    }
    
    query_lower = query.lower()
    for keyword, sites in manual_sites.items():
        if keyword in query_lower:
            for site in sites:
                site['source'] = 'Curated'
                results.append(site)
    
    return results[:num_results]

def generate_quick_overview(results, query, api_key):
    """各サイトの簡単な概要を一括生成"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        results_text = "\n".join([
            f"{i+1}. {r['title']} - {r['url']} - {r['description']}"
            for i, r in enumerate(results)
        ])
        
        overview_prompt = f"""
検索クエリ「{query}」に対する以下の検索結果について、各サイトの簡潔な概要を生成してください。

【検索結果】
{results_text}

【要求】
各サイトについて以下の形式で回答：
- 関連度（1-5）
- 一行概要（30文字以内）
- 期待できる内容（50文字以内）

【回答形式】
1. 関連度:4 | 概要:Python公式サイト | 内容:言語仕様、ダウンロード、チュートリアル
2. 関連度:3 | 概要:GitHub Python関連 | 内容:オープンソースプロジェクト、コード例
...

回答:
"""
        
        response = model.generate_content(overview_prompt)
        
        # レスポンスを解析して各サイトの情報を抽出
        overviews = []
        lines = response.text.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip() and ('関連度:' in line or 'relevance:' in line.lower()):
                try:
                    # 関連度を抽出
                    relevance_match = re.search(r'関連度:(\d+)', line)
                    relevance = int(relevance_match.group(1)) if relevance_match else 3
                    
                    # 概要を抽出
                    overview_match = re.search(r'概要:([^|]+)', line)
                    overview = overview_match.group(1).strip() if overview_match else "概要不明"
                    
                    # 内容を抽出
                    content_match = re.search(r'内容:(.+)', line)
                    content = content_match.group(1).strip() if content_match else "内容不明"
                    
                    if i < len(results):
                        overviews.append({
                            'relevance': relevance,
                            'overview': overview,
                            'expected_content': content
                        })
                except:
                    overviews.append({
                        'relevance': 3,
                        'overview': "AI分析中...",
                        'expected_content': "詳細分析が必要"
                    })
        
        # 結果数が足りない場合はデフォルト値で埋める
        while len(overviews) < len(results):
            overviews.append({
                'relevance': 3,
                'overview': "分析中...",
                'expected_content': "詳細分析が必要"
            })
        
        return overviews
        
    except Exception as e:
        # エラー時はデフォルト値を返す
        return [{
            'relevance': 3,
            'overview': "分析中...",
            'expected_content': "詳細分析が必要"
        } for _ in results]

def fetch_and_analyze_detailed(url, query, api_key):
    """詳細分析を実行"""
    try:
        # コンテンツ取得
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
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
        
        if len(text) > 10000:
            text = text[:10000] + "..."
        
        # 詳細分析
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        analysis_prompt = f"""
以下のWebページを検索クエリ「{query}」の観点から詳細分析してください。

【ページ情報】
タイトル: {page_title}
URL: {url}

【分析要求】
1. 要約（200文字程度）
2. 重要なポイント（3-5個）
3. 検索クエリとの関連性（1-5で評価）
4. このサイトから得られる具体的な価値
5. 次に読むべき関連情報があれば提案

【内容】
{text[:8000]}

【詳細分析結果】
"""
        
        analysis_response = model.generate_content(analysis_prompt)
        
        return {
            'success': True,
            'title': page_title,
            'url': url,
            'content_length': len(text),
            'analysis': analysis_response.text
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    st.set_page_config(
        page_title="Smart Overview & Detail Tool",
        page_icon="📋",
        layout="wide"
    )
    
    st.title("📋 Smart Overview & Detail Tool")
    st.markdown("**概要一覧 → 詳細分析の理想的なUI**")
    st.markdown("---")
    
    # API key check
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        st.success("✅ Gemini API key configured")
    else:
        st.error("❌ Gemini API key not found")
        st.stop()
    
    # Search Section
    st.subheader("🔍 Search & Overview")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Search Query",
            placeholder="例: Python 機械学習",
            help="検索したいキーワードを入力"
        )
    
    with col2:
        auto_overview = st.checkbox("Auto Overview", value=True, help="検索後に自動で概要を生成")
    
    if st.button("🔍 Search & Generate Overview", type="primary"):
        if query:
            with st.spinner("Searching and generating overviews..."):
                # Step 1: Search
                results = search_with_multiple_sources(query, 8)
                
                if results:
                    st.session_state.search_results = results
                    st.session_state.search_query = query
                    
                    # Step 2: Generate overviews
                    if auto_overview:
                        overviews = generate_quick_overview(results, query, api_key)
                        st.session_state.overviews = overviews
                    
                    st.success(f"✅ Found {len(results)} results with overviews")
                else:
                    st.warning("No results found")
        else:
            st.warning("Please enter a search query")
    
    # Results Overview Section
    if hasattr(st.session_state, 'search_results'):
        st.markdown("---")
        st.subheader("📋 Results Overview")
        
        results = st.session_state.search_results
        overviews = getattr(st.session_state, 'overviews', [])
        
        # 関連度でソート
        if overviews:
            combined = list(zip(results, overviews))
            combined.sort(key=lambda x: x[1]['relevance'], reverse=True)
            results, overviews = zip(*combined)
        
        for i, (result, overview) in enumerate(zip(results, overviews)):
            # 関連度に応じて色を変更
            relevance = overview.get('relevance', 3)
            if relevance >= 4:
                border_color = "#28a745"  # Green
            elif relevance >= 3:
                border_color = "#ffc107"  # Yellow
            else:
                border_color = "#dc3545"  # Red
            
            # カード形式で表示
            with st.container():
                st.markdown(f"""
                <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 15px; margin: 10px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <h4 style="margin: 0; color: #333;">{result['title']}</h4>
                            <p style="margin: 5px 0; color: #666; font-size: 14px;">
                                <strong>概要:</strong> {overview.get('overview', '分析中...')}
                            </p>
                            <p style="margin: 5px 0; color: #666; font-size: 14px;">
                                <strong>期待内容:</strong> {overview.get('expected_content', '詳細分析が必要')}
                            </p>
                            <p style="margin: 5px 0; color: #888; font-size: 12px;">
                                <strong>Source:</strong> {result.get('source', 'Unknown')} | 
                                <strong>関連度:</strong> {relevance}/5
                            </p>
                        </div>
                        <div style="margin-left: 20px;">
                            <a href="{result['url']}" target="_blank" style="text-decoration: none; margin-right: 10px;">🔗</a>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 詳細分析ボタン
                if st.button(f"📄 詳細分析", key=f"detail_{i}"):
                    with st.spinner("詳細分析中..."):
                        detailed_analysis = fetch_and_analyze_detailed(
                            result['url'], 
                            st.session_state.search_query, 
                            api_key
                        )
                        
                        if detailed_analysis['success']:
                            st.markdown("---")
                            st.subheader(f"🔍 詳細分析: {detailed_analysis['title']}")
                            
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.markdown(f"""
                                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                                {detailed_analysis['analysis']}
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col2:
                                st.write(f"**URL:** {detailed_analysis['url']}")
                                st.write(f"**Content Length:** {detailed_analysis['content_length']} chars")
                                st.markdown(f"[🔗 サイトを開く]({detailed_analysis['url']})")
                        else:
                            st.error(f"❌ 分析失敗: {detailed_analysis['error']}")
    
    # Clear button
    if st.button("🗑️ Clear All"):
        for key in ['search_results', 'overviews', 'search_query']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()
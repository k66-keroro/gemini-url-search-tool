#!/usr/bin/env python3
"""
Advanced Search with Cache & Filters - SQLiteキャッシュ + 環境フィルタ機能付き検索ツール
"""

import streamlit as st
import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import google.generativeai as genai
import time
from urllib.parse import quote_plus, urlparse, urljoin
import re
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
import platform
import sys

# Load environment variables
load_dotenv()

class SearchCache:
    """SQLiteを使用した検索結果キャッシュ"""
    
    def __init__(self, db_path="gemini-url-search-tool/data/search_cache.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """データベース初期化"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 検索結果キャッシュテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT UNIQUE,
                query TEXT,
                results TEXT,
                created_at TIMESTAMP,
                accessed_at TIMESTAMP
            )
        ''')
        
        # コンテンツ分析キャッシュテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_hash TEXT UNIQUE,
                url TEXT,
                title TEXT,
                analysis TEXT,
                created_at TIMESTAMP,
                accessed_at TIMESTAMP
            )
        ''')
        
        # ユーザー環境設定テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_environment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                os_name TEXT,
                python_version TEXT,
                preferences TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_query_hash(self, query, filters=None):
        """クエリのハッシュ値を生成"""
        query_data = {"query": query, "filters": filters or {}}
        return hashlib.md5(json.dumps(query_data, sort_keys=True).encode()).hexdigest()
    
    def get_url_hash(self, url):
        """URLのハッシュ値を生成"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def get_cached_search(self, query, filters=None, max_age_hours=24):
        """キャッシュされた検索結果を取得"""
        query_hash = self.get_query_hash(query, filters)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 指定時間以内のキャッシュを検索
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        cursor.execute('''
            SELECT results FROM search_cache 
            WHERE query_hash = ? AND created_at > ?
        ''', (query_hash, cutoff_time))
        
        result = cursor.fetchone()
        
        if result:
            # アクセス時間を更新
            cursor.execute('''
                UPDATE search_cache SET accessed_at = ? WHERE query_hash = ?
            ''', (datetime.now(), query_hash))
            conn.commit()
            
            conn.close()
            return json.loads(result[0])
        
        conn.close()
        return None
    
    def cache_search_results(self, query, results, filters=None):
        """検索結果をキャッシュ"""
        query_hash = self.get_query_hash(query, filters)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO search_cache 
            (query_hash, query, results, created_at, accessed_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (query_hash, query, json.dumps(results), datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_cached_analysis(self, url, max_age_hours=168):  # 1週間
        """キャッシュされたコンテンツ分析を取得"""
        url_hash = self.get_url_hash(url)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        cursor.execute('''
            SELECT title, analysis FROM content_cache 
            WHERE url_hash = ? AND created_at > ?
        ''', (url_hash, cutoff_time))
        
        result = cursor.fetchone()
        
        if result:
            # アクセス時間を更新
            cursor.execute('''
                UPDATE content_cache SET accessed_at = ? WHERE url_hash = ?
            ''', (datetime.now(), url_hash))
            conn.commit()
            
            conn.close()
            return {"title": result[0], "analysis": result[1]}
        
        conn.close()
        return None
    
    def cache_content_analysis(self, url, title, analysis):
        """コンテンツ分析をキャッシュ"""
        url_hash = self.get_url_hash(url)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO content_cache 
            (url_hash, url, title, analysis, created_at, accessed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (url_hash, url, title, analysis, datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
    
    def save_user_environment(self, os_name, python_version, preferences):
        """ユーザー環境設定を保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_environment 
            (os_name, python_version, preferences, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (os_name, python_version, json.dumps(preferences), datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_user_environment(self):
        """ユーザー環境設定を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT os_name, python_version, preferences FROM user_environment 
            ORDER BY updated_at DESC LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "os_name": result[0],
                "python_version": result[1],
                "preferences": json.loads(result[2])
            }
        return None

def get_system_info():
    """システム情報を自動取得"""
    return {
        "os_name": platform.system(),
        "os_version": platform.version(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "architecture": platform.architecture()[0]
    }

def apply_environment_filters(results, user_env):
    """環境設定に基づいて検索結果をフィルタリング"""
    if not user_env:
        return results
    
    filtered_results = []
    
    for result in results:
        score = result.get('confidence', 0.5)
        
        # OS固有の調整
        if user_env.get('os_name') == 'Windows':
            if 'windows' in result['title'].lower() or 'win' in result['title'].lower():
                score += 0.2
            elif 'linux' in result['title'].lower() or 'mac' in result['title'].lower():
                score -= 0.1
        
        # Pythonバージョン固有の調整
        python_version = user_env.get('python_version', '')
        if python_version:
            major_version = python_version.split('.')[0]
            if f'python {major_version}' in result['title'].lower() or f'python{major_version}' in result['title'].lower():
                score += 0.2
            elif 'python 2' in result['title'].lower() and major_version == '3':
                score -= 0.3
        
        # 設定された優先度に基づく調整
        preferences = user_env.get('preferences', {})
        if preferences.get('prefer_official_docs', True):
            if any(word in result['url'].lower() for word in ['docs.', 'documentation', 'official']):
                score += 0.1
        
        if preferences.get('prefer_recent_content', True):
            if any(word in result['title'].lower() for word in ['2024', '2023', 'latest', 'new']):
                score += 0.1
        
        result['confidence'] = min(1.0, max(0.0, score))
        filtered_results.append(result)
    
    # 信頼度でソート
    filtered_results.sort(key=lambda x: x['confidence'], reverse=True)
    return filtered_results

def search_with_real_urls(query, num_results=8, user_env=None):
    """実際のコンテンツURLを取得する検索（環境フィルタ付き）"""
    results = []
    
    # 環境情報をクエリに追加
    enhanced_query = query
    if user_env:
        os_name = user_env.get('os_name', '')
        python_version = user_env.get('python_version', '')
        if os_name and any(tech in query.lower() for tech in ['python', 'programming', 'development']):
            enhanced_query += f" {os_name}"
        if python_version and 'python' in query.lower():
            enhanced_query += f" python {python_version}"
    
    # Wikipedia検索
    try:
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote_plus(enhanced_query)}&limit=3&format=json"
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
    
    # GitHub検索（技術関連）
    try:
        tech_keywords = ['python', 'javascript', 'react', 'vue', 'angular', 'node', 'docker', 'kubernetes', 'aws', 'api', 'framework', 'library', 'vba', 'visual basic', 'excel', 'code', 'programming']
        if any(keyword in query.lower() for keyword in tech_keywords):
            github_url = f"https://api.github.com/search/repositories?q={quote_plus(enhanced_query)}&sort=stars&order=desc&per_page=2"
            response = requests.get(github_url, timeout=10)
            data = response.json()
            
            if 'items' in data:
                for repo in data['items'][:2]:
                    results.append({
                        'title': f"{repo['name']} - GitHub",
                        'url': repo['html_url'],
                        'description': repo.get('description', 'GitHub repository'),
                        'source': 'GitHub',
                        'confidence': 0.8
                    })
    except:
        pass
    
    # 手動厳選サイト
    manual_sites = {
        'python': [
            {'title': 'Python.org - Official Site', 'url': 'https://www.python.org/', 'description': 'Official Python programming language website', 'confidence': 1.0},
            {'title': 'Python Tutorial', 'url': 'https://docs.python.org/3/tutorial/', 'description': 'Official Python tutorial', 'confidence': 1.0},
            {'title': 'Real Python', 'url': 'https://realpython.com/', 'description': 'High-quality Python tutorials', 'confidence': 0.9},
        ],
        'vba': [
            {'title': 'Microsoft VBA Documentation', 'url': 'https://docs.microsoft.com/en-us/office/vba/', 'description': 'Official Microsoft VBA documentation', 'confidence': 1.0},
            {'title': 'Excel VBA Tutorial', 'url': 'https://www.excel-easy.com/vba.html', 'description': 'Excel VBA tutorial and examples', 'confidence': 0.9},
        ],
    }
    
    query_lower = query.lower()
    for keyword, sites in manual_sites.items():
        if keyword in query_lower:
            for site in sites:
                site['source'] = 'Curated'
                results.append(site)
    
    # 環境フィルタを適用
    if user_env:
        results = apply_environment_filters(results, user_env)
    
    return results[:num_results]

def fetch_and_analyze_content_cached(url, query, api_key, cache):
    """キャッシュ機能付きコンテンツ分析"""
    # キャッシュから取得を試行
    cached_analysis = cache.get_cached_analysis(url)
    if cached_analysis:
        st.info("📦 Using cached analysis")
        return {
            'success': True,
            'title': cached_analysis['title'],
            'url': url,
            'analysis': cached_analysis['analysis'],
            'from_cache': True
        }
    
    # 新規分析
    try:
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
        
        if len(text) > 8000:
            text = text[:8000] + "..."
        
        # Gemini分析
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        analysis_prompt = f"""
以下のWebページを検索クエリ「{query}」の観点から分析してください。

【ページ情報】
タイトル: {page_title}
URL: {url}

【分析要求】
1. 要約（200文字程度）
2. 重要なポイント（3-5個）
3. 検索クエリとの関連性（1-5で評価）
4. このページから得られる具体的な価値

【内容】
{text[:6000]}

【分析結果】
"""
        
        analysis_response = model.generate_content(analysis_prompt)
        
        # キャッシュに保存
        cache.cache_content_analysis(url, page_title, analysis_response.text)
        
        return {
            'success': True,
            'title': page_title,
            'url': url,
            'analysis': analysis_response.text,
            'from_cache': False
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    st.set_page_config(
        page_title="Advanced Search with Cache & Filters",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 Advanced Search with Cache & Filters")
    st.markdown("**SQLiteキャッシュ + 環境フィルタ機能付き検索ツール**")
    st.markdown("---")
    
    # API key check
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        st.success("✅ Gemini API key configured")
    else:
        st.error("❌ Gemini API key not found")
        st.stop()
    
    # キャッシュ初期化
    cache = SearchCache()
    
    # システム情報取得
    system_info = get_system_info()
    
    # サイドバー：環境設定
    with st.sidebar:
        st.subheader("🔧 Environment Settings")
        
        # 現在の環境情報表示
        st.write("**Current System:**")
        st.write(f"OS: {system_info['os_name']} {system_info['os_version']}")
        st.write(f"Python: {system_info['python_version']}")
        st.write(f"Architecture: {system_info['architecture']}")
        
        st.markdown("---")
        
        # ユーザー設定
        st.write("**Search Preferences:**")
        prefer_official = st.checkbox("Prefer Official Documentation", value=True)
        prefer_recent = st.checkbox("Prefer Recent Content", value=True)
        prefer_os_specific = st.checkbox("Prefer OS-Specific Results", value=True)
        
        # 環境設定を保存
        user_preferences = {
            "prefer_official_docs": prefer_official,
            "prefer_recent_content": prefer_recent,
            "prefer_os_specific": prefer_os_specific
        }
        
        if st.button("💾 Save Environment Settings"):
            cache.save_user_environment(
                system_info['os_name'],
                system_info['python_version'],
                user_preferences
            )
            st.success("Settings saved!")
    
    # メイン検索エリア
    st.subheader("🔍 Smart Search with Environment Filters")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Search Query",
            placeholder="例: Python 学習",
            help="検索したいキーワードを入力"
        )
    
    with col2:
        use_cache = st.checkbox("Use Cache", value=True, help="キャッシュを使用して高速化")
    
    if st.button("🚀 Smart Search", type="primary"):
        if query:
            # ユーザー環境設定を取得
            user_env = cache.get_user_environment()
            if not user_env:
                user_env = {
                    "os_name": system_info['os_name'],
                    "python_version": system_info['python_version'],
                    "preferences": user_preferences
                }
            
            # キャッシュから検索結果を取得
            cached_results = None
            if use_cache:
                cached_results = cache.get_cached_search(query, user_env['preferences'])
            
            if cached_results:
                st.info("📦 Using cached search results")
                results = cached_results
            else:
                with st.spinner("Searching with environment filters..."):
                    results = search_with_real_urls(query, 8, user_env)
                    
                    if use_cache and results:
                        cache.cache_search_results(query, results, user_env['preferences'])
            
            if results:
                st.session_state.search_results = results
                st.session_state.search_query = query
                st.success(f"✅ Found {len(results)} results (filtered for your environment)")
            else:
                st.warning("No results found")
        else:
            st.warning("Please enter a search query")
    
    # Results Display
    if hasattr(st.session_state, 'search_results'):
        st.markdown("---")
        st.subheader("🎯 Environment-Filtered Results")
        
        results = st.session_state.search_results
        
        for i, result in enumerate(results, 1):
            confidence = result.get('confidence', 0.5)
            if confidence >= 0.8:
                border_color = "#28a745"
            elif confidence >= 0.6:
                border_color = "#ffc107"
            else:
                border_color = "#dc3545"
            
            with st.container():
                st.markdown(f"""
                <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 15px; margin: 10px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <h4 style="margin: 0; color: #333;">{result['title']}</h4>
                            <p style="margin: 5px 0; color: #666; font-size: 14px;">
                                <strong>URL:</strong> {result['url']}
                            </p>
                            <p style="margin: 5px 0; color: #666; font-size: 14px;">
                                <strong>Description:</strong> {result['description']}
                            </p>
                            <p style="margin: 5px 0; color: #888; font-size: 12px;">
                                <strong>Source:</strong> {result.get('source', 'Unknown')} | 
                                <strong>Relevance:</strong> {confidence:.1f}/1.0
                            </p>
                        </div>
                        <div style="margin-left: 20px;">
                            <a href="{result['url']}" target="_blank" style="text-decoration: none; margin-right: 10px;">🔗</a>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 詳細分析ボタン
                if st.button(f"📄 Analyze Content", key=f"analyze_{i}"):
                    with st.spinner("Analyzing content (checking cache first)..."):
                        analysis = fetch_and_analyze_content_cached(
                            result['url'], 
                            st.session_state.search_query, 
                            api_key,
                            cache
                        )
                        
                        if analysis['success']:
                            st.markdown("---")
                            cache_indicator = "📦 (Cached)" if analysis.get('from_cache') else "🆕 (Fresh)"
                            st.subheader(f"🔍 Content Analysis {cache_indicator}: {analysis['title']}")
                            
                            st.markdown(f"""
                            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                            {analysis['analysis']}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error(f"❌ Analysis failed: {analysis['error']}")
    
    # Cache Management
    st.markdown("---")
    with st.expander("🗄️ Cache Management"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Cache Stats"):
                conn = sqlite3.connect(cache.db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM search_cache")
                search_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM content_cache")
                content_count = cursor.fetchone()[0]
                
                conn.close()
                
                st.write(f"Search Cache: {search_count} entries")
                st.write(f"Content Cache: {content_count} entries")
        
        with col2:
            if st.button("🧹 Clear Old Cache"):
                conn = sqlite3.connect(cache.db_path)
                cursor = conn.cursor()
                
                # 1週間以上古いキャッシュを削除
                cutoff_time = datetime.now() - timedelta(days=7)
                cursor.execute("DELETE FROM search_cache WHERE created_at < ?", (cutoff_time,))
                cursor.execute("DELETE FROM content_cache WHERE created_at < ?", (cutoff_time,))
                
                conn.commit()
                conn.close()
                
                st.success("Old cache cleared!")
        
        with col3:
            if st.button("🗑️ Clear All Cache"):
                conn = sqlite3.connect(cache.db_path)
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM search_cache")
                cursor.execute("DELETE FROM content_cache")
                
                conn.commit()
                conn.close()
                
                st.success("All cache cleared!")

if __name__ == "__main__":
    main()